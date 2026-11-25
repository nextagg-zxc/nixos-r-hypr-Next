# Раздаваемая система: всё, что выбрал друг в установщике (choices.json, разбор — lib/choices.nix),
# и программы из Магазина (packages.json). Без личного пользователя nextagg.
# Хост: hosts/share (choices.json и packages.json лежат рядом, установщик кладёт свои).
{ inputs, self }:
{ config, lib, pkgs, ... }:
let
  choicesLib = import ../../lib/choices.nix { inherit lib; };
  cfg = config.nextagg.share;
  c = choicesLib.normalize cfg.choices;
  has = x: builtins.elem x c.extras;
  ownPkgs = config.nextagg.ownPackages;
  hyprland = c.desktop != "kde";
  kde = c.desktop != "hyprland";

  # ядро: готовое из образа (ready) или под этот процессор (native, собирается на месте)
  cachy = pkgs.callPackage "${inputs.nix-cachyos-kernel}/kernel-cachyos" { inherit inputs; };
  native = k: k.overrideAttrs (o: { makeFlags = (o.makeFlags or [ ]) ++ [ "KCFLAGS=-march=native -O2" ]; });
  kernel = {
    cachyos = if c.kernelBuild == "native"
      then cachy.linux-cachyos-latest.override { processorOpt = "native"; }
      else cachy.linux-cachyos-latest;
    zen = (if c.kernelBuild == "native" then native else lib.id) pkgs.linuxPackages_zen.kernel;
    linux = (if c.kernelBuild == "native" then native else lib.id) pkgs.linuxPackages_latest.kernel;
  }.${c.kernel};
in
{
  imports = [ ./desktop-kde-minimal.nix ./share-boot.nix ./share-extras.nix (import ./share-store.nix { inherit inputs; }) ];

  options.nextagg.share = {
    choices = lib.mkOption {
      type = lib.types.attrs;
      default = { };
      description = "Содержимое choices.json (сырое; разбирает lib/choices.nix).";
    };
    packages = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      description = "Содержимое packages.json: программы из Магазина (имена атрибутов nixpkgs).";
    };
    resolved = lib.mkOption {
      type = lib.types.attrs;
      readOnly = true;
      default = c;
      description = "choices.json после разбора (для home-manager и проверок).";
    };
  };

  config = {
    nixpkgs.config.allowUnfree = true; # Steam, Spotify, Discord, NVIDIA; Магазин — тоже несвободное

    # ── пользователь, язык, время ──
    users.users.${c.user.name} = {
      isNormalUser = true;
      description = c.user.fullName;
      extraGroups = [ "wheel" "networkmanager" "video" "audio" "input" ]
        ++ lib.optionals c.system.virtualization [ "libvirtd" "kvm" ];
    } // lib.optionalAttrs (c.user.passwordHash != null) { hashedPassword = c.user.passwordHash; };
    networking.hostName = c.hostname;
    networking.networkmanager.enable = true;
    time.timeZone = c.timezone;
    i18n.defaultLocale = c.locale;
    services.xserver.xkb = {
      layout = lib.concatStringsSep "," c.keyboard;
      options = "grp:alt_shift_toggle";
    };
    console.useXkbConfig = true;
    # раскладки друга для Hyprland: его конфиг общий для всех, а раскладки у каждого свои (вид share читает файл)
    environment.etc."nixos-share/keyboard".text = lib.concatStringsSep "," c.keyboard;

    # ── рабочий стол ──
    # уборка хранилища: тулчейн после сборки ядра/драйверов и старые поколения уходят сами
    # (установщик после «собрать» вызывает очистку сразу; «Откатить» — последние поколения остаются)
    # уборка раз в неделю: поколения старше 14 дней, но последние 5 остаются всегда (для «Откатить»)
    systemd.services.nixos-share-gc = {
      description = "Уборка старых версий системы";
      serviceConfig = { Type = "oneshot"; ExecStart = "${ownPkgs.system-settings}/libexec/nixos-share-apply gc"; Nice = 19; IOSchedulingClass = "idle"; };
    };
    systemd.timers.nixos-share-gc = {
      wantedBy = [ "timers.target" ];
      timerConfig = { OnCalendar = "weekly"; Persistent = true; RandomizedDelaySec = "1h"; };
    };
    nix.settings.auto-optimise-store = true;

    nextagg.desktop = {
      enable = hyprland;
      user = c.user.name;
      autoLogin = has "autologin";
      flakePath = "/etc/nixos";
    };
    nextagg.kdeMinimal = { enable = kde; look = c.kdeLook; };
    services.displayManager = {
      # при «оба» первый вход — в KDE (друг пересаживается с Windows), дальше SDDM помнит выбор
      defaultSession = lib.mkForce (if kde then "plasma" else "hyprland-uwsm");
      autoLogin = lib.mkIf (has "autologin") { enable = true; user = c.user.name; };
    };
    services.zapret-hub.enable = true; # всегда, при любом рабочем столе
    # связка ключей открывается паролем входа (без автовхода); при автовходе — пустая связка (home/share.nix)
    services.gnome.gnome-keyring.enable = true;
    security.pam.services.sddm.enableGnomeKeyring = true;

    # ── ядро и «Система» ──
    boot.kernelPackages = pkgs.linuxPackagesFor kernel;
    boot.kernelParams = lib.optional c.system.mitigationsOff "mitigations=off"
      ++ lib.optionals c.system.iommu [ "intel_iommu=on" "iommu=pt" ];
    virtualisation.libvirtd.enable = c.system.virtualization;
    # только x86 с KVM (весь qemu со всеми архитектурами — ~1 ГиБ в образе)
    virtualisation.libvirtd.qemu.package = pkgs.qemu_kvm;
    programs.virt-manager.enable = c.system.virtualization;

    # ── видеодрайвер ──
    hardware.graphics = {
      enable = true;
      enable32Bit = true;
      # аппаратное видео: Intel — VA-API (браузер, Discord) и QSV (запись в OBS); NVIDIA — VA-API; AMD — уже в Mesa
      extraPackages = [ pkgs.intel-media-driver pkgs.vpl-gpu-rt ]
        ++ lib.optional (c.gpu != "mesa") pkgs.nvidia-vaapi-driver;
    };
    # прошивки Wi‑Fi, Bluetooth, видеокарт AMD/Intel, звука (те же, что в живом образе — место в ISO не растёт)
    hardware.enableRedistributableFirmware = lib.mkDefault true;
    # сжатая подкачка в памяти (как у автора): раздела подкачки установщик не делает, а на 8 ГБ игры
    # и браузер упираются в память — zram сжимает её примерно втрое, без записи на диск
    zramSwap = { enable = lib.mkDefault true; memoryPercent = lib.mkDefault 100; algorithm = lib.mkDefault "zstd"; };
    services.xserver.videoDrivers = lib.mkIf (c.gpu != "mesa") [ "nvidia" ];
    hardware.nvidia = lib.mkIf (c.gpu != "mesa") {
      open = c.gpu == "nvidia"; # открытый модуль — RTX 20 и новее; legacy — GTX 900/1000
      modesetting.enable = true;
      # GTX 900/1000 (Maxwell, Pascal) — последняя поддерживающая их ветка 580
      package = if c.gpu == "nvidia-legacy" then config.boot.kernelPackages.nvidiaPackages.legacy_580
                else config.boot.kernelPackages.nvidiaPackages.stable;
    };

    # ── всегда: Steam + Millennium, Discord + Vencord ──
    programs.steam = {
      enable = true;
      package = pkgs.steam.override {
        extraPkgs = p: [ ownPkgs.millennium p.brotli.lib p.xz p.zstd ];
        extraLibraries = p: [ p.openssl ];
      };
      # Proton-GE (1,6 ГиБ) в образ не кладём: Steam сам скачивает Proton при первой игре
    };
    # Millennium ищет себя в /run/host/usr/lib(64)/millennium (как у пользователя, hosts/nextagg/gaming.nix)
    systemd.tmpfiles.rules = [
      "d /run/host 0755 root root -"
      "d /run/host/usr 0755 root root -"
      "d /run/host/usr/lib 0755 root root -"
      "L+ /run/host/usr/lib/millennium - - - - ${ownPkgs.millennium}/lib/millennium"
      "d /run/host/usr/lib64 0755 root root -"
      "L+ /run/host/usr/lib64/millennium - - - - ${ownPkgs.millennium}/lib/millennium"
    ];
    programs.firefox.enable = true;
    environment.systemPackages = [ (pkgs.discord.override { withVencord = true; }) ownPkgs.system-settings ]
      ++ lib.optionals (has "gaming") [ pkgs.mangohud ]
      # OBS без встроенного браузера (CEF, ~0,4 ГиБ образа): оверлеи-«источник браузера» — в OBS из Flathub (Магазин)
      ++ lib.optionals (has "obs") [ (pkgs.obs-studio.override { browserSupport = false; }) ]
      ++ lib.optionals (has "telegram") [ pkgs.telegram-desktop ]
      ++ choicesLib.packageList pkgs cfg.packages;
    programs.gamemode.enable = has "gaming";

    # ── домашняя папка друга (вид без личного, автозапуск, плеер) ──
    home-manager.users.${c.user.name} = import ../../home/share.nix;
  };
}
