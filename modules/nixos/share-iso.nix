# Загрузочный ISO раздаваемой NixOS: живая система KDE, установщик Calamares запускается сам.
# В хранилище образа — готовые варианты системы (ядра × видеодрайверы, оба плеера, все дополнения) и всё,
# что нужно, чтобы собрать мелкие файлы конфигурации на месте: «готовая» установка идёт без интернета.
# Что класть, считает scripts/build-share-iso.sh (экспорт флейка + scripts/iso-closure.py) и передаёт
# через переменные окружения — поэтому образ собирается с --impure:
#   NIXOS_SHARE_ISO_FLAKE     — экспорт флейка в хранилище (его установщик кладёт в /etc/nixos)
#   NIXOS_SHARE_ISO_CONTENTS  — JSON-список путей хранилища для образа
# Проверка без окна (QEMU): второй диск с меткой SHAREAUTO и answers.json (ключи как у Calamares) —
# разметить /dev/vda, поставить, выключить. Без такого диска служба ничего не делает.
{ config, lib, pkgs, modulesPath, ... }:
let
  env = n: builtins.getEnv n;
  flakeSrc = if env "NIXOS_SHARE_ISO_FLAKE" == "" then null else builtins.storePath (env "NIXOS_SHARE_ISO_FLAKE");
  contents = if env "NIXOS_SHARE_ISO_CONTENTS" == "" then [ ]
             else map builtins.storePath (lib.importJSON (env "NIXOS_SHARE_ISO_CONTENTS"));
  installer = pkgs.callPackage ../../pkgs/share-installer { flake = flakeSrc; };
  autostart = pkgs.makeAutostartItem { name = "calamares"; package = installer.calamares; };
  autoinstall = pkgs.writeShellScript "share-autoinstall" ''
    set -euo pipefail
    export PATH=${lib.makeBinPath (with pkgs; [ coreutils util-linux gptfdisk dosfstools btrfs-progs systemd ])}:/run/wrappers/bin:/run/current-system/sw/bin:$PATH
    # стирает диск — только в виртуалке (на живом ПК ничего не делает, даже с флешкой SHAREAUTO)
    systemd-detect-virt --vm -q || exit 0
    for _ in $(seq 20); do [ -e /dev/disk/by-label/SHAREAUTO ] && break; sleep 1; done
    [ -e /dev/disk/by-label/SHAREAUTO ] || exit 0
    exec > >(tee /dev/console >/dev/ttyS0 2>/dev/null) 2>&1   # и на экран, и в последовательный порт (QEMU)
    mkdir -p /run/shareauto
    mount -o ro /dev/disk/by-label/SHAREAUTO /run/shareauto
    echo "АВТОУСТАНОВКА: $(cat /run/shareauto/answers.json)"
    disk=/dev/vda
    sgdisk -Z "$disk"
    sgdisk -n1:0:+1G -t1:ef00 -c1:EFI -n2:0:0 -t2:8300 -c2:root "$disk"
    udevadm settle
    mkfs.vfat -F32 -n EFI ''${disk}1
    mkfs.btrfs -f -L nixos ''${disk}2
    mount ''${disk}2 /mnt
    btrfs subvolume create /mnt/home
    btrfs subvolume create /mnt/nix
    umount /mnt
    mount ''${disk}2 /mnt
    mkdir -p /mnt/home /mnt/nix /mnt/boot
    mount -o subvol=home ''${disk}2 /mnt/home
    mount -o subvol=nix ''${disk}2 /mnt/nix
    mount -o fmask=0077,dmask=0077 ''${disk}1 /mnt/boot
    echo '[{"mountPoint": "/", "fs": "btrfs"}]' >/tmp/parts.json
    if ${installer}/bin/nixos-share-install --answers /run/shareauto/answers.json \
         --root /mnt --partitions /tmp/parts.json; then
      echo "friend:parol123" | chpasswd --root /mnt
      echo "АВТОУСТАНОВКА: ГОТОВО"
    else
      echo "АВТОУСТАНОВКА: ОШИБКА"
    fi
    sync
    umount -R /mnt || true
    systemctl poweroff
  '';
in
{
  imports = [ "${modulesPath}/installer/cd-dvd/installation-cd-graphical-base.nix" ];

  isoImage.edition = "share";
  # только UEFI: в режиме Legacy BIOS Calamares стёр бы диск, а загрузчик (Limine, EFI) поставить не смог бы
  isoImage.makeBiosBootable = false;
  isoImage.volumeID = "NIXOS_SHARE";
  image.baseName = lib.mkForce "nixos-share-${config.system.nixos.label}-${pkgs.stdenv.hostPlatform.system}";
  # xz сжимает плотнее zstd (образ должен влезть на флешку «8 ГБ»: ≤ 7,4 ГиБ); BCJ x86 — для программ
  # (блоки 1 МиБ make-squashfs ставит сам)
  isoImage.squashfsCompression = "xz -Xdict-size 100% -Xbcj x86";
  isoImage.storeContents = contents ++ lib.optional (flakeSrc != null) flakeSrc;

  # живая система: KDE, вход сам, установщик открывается сам (и ярлык на рабочем столе)
  services.desktopManager.plasma6 = { enable = true; enableQt5Integration = false; };
  services.displayManager = {
    sddm = { enable = true; wayland.enable = true; };
    autoLogin = { enable = true; user = "nixos"; };
    defaultSession = "plasma";
  };
  environment.plasma6.excludePackages = [ pkgs.kdePackages.plasma-workspace-wallpapers ];
  programs.kde-pim.enable = false;
  services.speechd.enable = lib.mkForce false;
  security.polkit.enablePkexecWrapper = true;
  programs.partition-manager.enable = true;
  environment.systemPackages = [ installer installer.calamares autostart pkgs.glibcLocales ];
  i18n.defaultLocale = "ru_RU.UTF-8";
  i18n.supportedLocales = [ "all" ];
  systemd.tmpfiles.settings."10-installer-desktop" = {
    "/home/nixos/Desktop".d = { user = "nixos"; group = "users"; mode = "0755"; };
    "/home/nixos/Desktop/calamares.desktop"."L+".argument = "${installer.calamares}/share/applications/calamares.desktop";
  };
  nix.settings.experimental-features = [ "nix-command" "flakes" ];

  # проверка без окна (QEMU): диск SHAREAUTO с answers.json
  systemd.services.share-autoinstall = {
    description = "Автоустановка для проверки (диск SHAREAUTO)";
    wantedBy = [ "multi-user.target" ];
    after = [ "multi-user.target" ];
    serviceConfig = { Type = "oneshot"; ExecStart = autoinstall; StandardOutput = "journal+console"; };
  };
}
