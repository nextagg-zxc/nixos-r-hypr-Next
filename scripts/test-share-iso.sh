#!/usr/bin/env bash
# Проверка ISO в QEMU (UEFI, без сети): автоустановка по ответам → загрузка установленной системы → снимок экрана.
#   bash scripts/test-share-iso.sh <iso> <answers.json> <рабочая папка>
#   с сетью: SHARE_ISO_NIC="-nic user,model=virtio-net-pci" bash scripts/test-share-iso.sh …
# Установщик тот же, что в Calamares (nixos-share-install); разметка — как «стереть диск» (ESP + btrfs).
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
    -device virtio-vga -display none ${SHARE_ISO_NIC:--nic none} \
    -monitor unix:"$work/mon.sock",server,nowait "$@"
}
shot() { printf 'screendump %s\n' "$1" | socat - UNIX-CONNECT:"$work/mon.sock" >/dev/null 2>&1 || true; }

echo "1/2 установка с ISO (лог: $work/install.log)"
start=$(date +%s)
q -drive file="$work/disk.qcow2",if=virtio -drive file="$work/answers.img",if=virtio,format=raw \
  -cdrom "$iso" -boot order=d -serial file:"$work/install.log" &
qp=$!
i=0
while kill -0 $qp 2>/dev/null; do
  sleep 60; i=$((i+1)); shot "$work/install-$i.ppm"
  [ $i -lt 150 ] || { kill $qp; echo "ТАЙМАУТ установки"; exit 1; }
done
echo "установка: $(( ($(date +%s)-start)/60 )) мин"
grep -q "АВТОУСТАНОВКА: ГОТОВО" "$work/install.log" || { tail -40 "$work/install.log"; echo "УСТАНОВКА НЕ УДАЛАСЬ"; exit 1; }

echo "2/2 загрузка установленной системы"
q -drive file="$work/disk.qcow2",if=virtio -serial file:"$work/boot.log" &
qp=$!
for t in 60 120 180; do sleep 60; shot "$work/boot-$t.ppm"; done
kill $qp 2>/dev/null || true
echo "снимки: $work/boot-*.ppm"
