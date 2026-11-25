#!/usr/bin/env bash
# Проверка ISO в QEMU (UEFI, без сети): автоустановка по ответам → загрузка установленной системы → снимок экрана.
#   bash scripts/test-share-iso.sh <iso> <answers.json> <рабочая папка>
#   с сетью: SHARE_ISO_NIC="-nic user,model=virtio-net-pci" bash scripts/test-share-iso.sh …
#   «обычный ПК»: SHARE_ISO_REALPC=1 — ISO и ответы на USB-флешках, диск NVMe, сетевая Intel (без выхода наружу), обычная видеокарта
# Установщик тот же, что в Calamares (nixos-share-install); разметка — как «стереть диск» (ESP + btrfs).
# shellcheck disable=SC2054  # запятые — внутри аргументов QEMU
set -euo pipefail
iso=$1 answers=$2 work=$3
mkdir -p "$work"
ovmf=$(nix build --no-link --print-out-paths nixpkgs#OVMF.fd)
cp "$ovmf/FV/OVMF_VARS.fd" "$work/vars.fd"; chmod u+w "$work/vars.fd"
rm -f "$work/disk.qcow2" "$work/answers.img"
qemu-img create -f qcow2 "$work/disk.qcow2" 80G >/dev/null
truncate -s 8M "$work/answers.img"
mkfs.vfat -n SHAREAUTO "$work/answers.img" >/dev/null
mcopy -i "$work/answers.img" "$answers" ::answers.json

q() {  # общие параметры: KVM, UEFI, virtio, без сети; exec — чтобы kill $! попадал в сам QEMU
  exec qemu-system-x86_64 -enable-kvm -machine q35 -cpu host -smp "${SHARE_ISO_SMP:-4}" -m 8G \
    -drive if=pflash,format=raw,readonly=on,file="$ovmf/FV/OVMF_CODE.fd" \
    -drive if=pflash,format=raw,file="$work/vars.fd" \
    "${hw[@]}" -display none \
    -monitor unix:"$work/mon.sock",server,nowait "$@"
}
if [ -n "${SHARE_ISO_REALPC:-}" ]; then
  hw=(-vga std -device qemu-xhci,id=xhci -netdev user,id=n0,restrict=on -device e1000e,netdev=n0)
  disk=(-drive if=none,id=nv,file="$work/disk.qcow2" -device nvme,serial=realpc,drive=nv)
  media=(-drive if=none,id=ans,file="$work/answers.img",format=raw -device usb-storage,bus=xhci.0,drive=ans
         -drive if=none,id=stick,file="$iso",format=raw,readonly=on -device usb-storage,bus=xhci.0,drive=stick,bootindex=0)
else
  read -ra nic <<<"${SHARE_ISO_NIC:--nic none}"
  hw=(-device virtio-vga "${nic[@]}")
  disk=(-drive file="$work/disk.qcow2",if=virtio)
  media=(-drive file="$work/answers.img",if=virtio,format=raw -cdrom "$iso" -boot order=d)
fi
shot() { printf 'screendump %s\n' "$1" | socat - UNIX-CONNECT:"$work/mon.sock" >/dev/null 2>&1 || true; }

echo "1/2 установка с ISO (лог: $work/install.log)"
start=$(date +%s)
q "${disk[@]}" "${media[@]}" -serial file:"$work/install.log" &
qp=$!
i=0
while kill -0 $qp 2>/dev/null; do
  sleep 60; i=$((i+1)); shot "$work/install-$i.ppm"
  [ $i -lt 150 ] || { kill $qp; echo "ТАЙМАУТ установки"; exit 1; }
done
echo "установка: $(( ($(date +%s)-start)/60 )) мин"
grep -q "АВТОУСТАНОВКА: ГОТОВО" "$work/install.log" || { tail -40 "$work/install.log"; echo "УСТАНОВКА НЕ УДАЛАСЬ"; exit 1; }

echo "2/2 загрузка установленной системы"
q "${disk[@]}" -serial file:"$work/boot.log" &
qp=$!
for t in 60 120 180; do sleep 60; shot "$work/boot-$t.ppm"; done
kill $qp 2>/dev/null || true
echo "снимки: $work/boot-*.ppm"
