# Загрузка раздаваемой системы: Limine (штатный модуль nixpkgs) — «NixOS», предыдущие поколения и
# Windows; тихая красивая загрузка (Plymouth bgrt — логотип производителя и кружок, как у Windows);
# initrd на systemd — диск LUKS открывается через TPM2, если он привязан в «Настройке системы».
# Secure Boot — по выбору (choices.boot.secureBoot): Limine подписан ключами sbctl; ключи создаются
# сами и записываются в прошивку вместе с ключами Microsoft, если она в Setup Mode (мастер — в
# «Настройке системы»). По умолчанию выключено: свои ключи, не записанные в прошивку, загрузку сломали бы.
{ config, lib, pkgs, ... }:
let
  c = config.nextagg.share.resolved;
  windowsEntries = lib.concatMapStrings (w: ''
    /${w.name}
      protocol: efi
      path: guid(${w.esp}):/EFI/Microsoft/Boot/bootmgfw.efi
  '') c.boot.windows;
in
{
  boot.loader.limine = {
    enable = true;
    efiSupport = true;
    maxGenerations = 8;
    extraEntries = windowsEntries;
    secureBoot = lib.mkIf c.boot.secureBoot {
      enable = true;
      autoGenerateKeys = true;
      autoEnrollKeys.enable = true; # --microsoft --firmware-builtin: Windows и античиты работают
    };
  };
  boot.loader.efi.canTouchEfiVariables = lib.mkDefault true;
  # рядом с Windows часы BIOS — в местном времени, как у неё (иначе время «уезжает» при каждой смене ОС)
  time.hardwareClockInLocalTime = lib.mkDefault (c.boot.windows != [ ] || c.hardware.windowsDisks != [ ]);
  boot.loader.timeout = lib.mkDefault 3;

  # initrd (в nixpkgs только на systemd): TPM2-разблокировка LUKS (systemd-cryptenroll, PCR 7)
  boot.initrd.systemd.tpm2.enable = true;
  security.tpm2.enable = true;
  environment.systemPackages = [ pkgs.sbctl pkgs.efibootmgr ];

  # тихо и красиво: без текста ядра, логотип производителя (bgrt) с кружком
  boot.plymouth = {
    enable = true;
    theme = "bgrt";
  };
  boot.consoleLogLevel = lib.mkDefault 3;
  boot.kernelParams = [ "quiet" "splash" "loglevel=3" "rd.udev.log_level=3" "udev.log_level=3" ];
}
