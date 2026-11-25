# Заглушка: установщик заменяет этот файл выводом nixos-generate-config (этап 10).
# Загрузчик (Limine) — modules/nixos/share-boot.nix.
{ lib, ... }:
{
  fileSystems."/" = lib.mkDefault { device = "/dev/disk/by-label/nixos"; fsType = "ext4"; };
  fileSystems."/boot" = lib.mkDefault { device = "/dev/disk/by-label/BOOT"; fsType = "vfat"; options = [ "umask=0077" ]; };
}
