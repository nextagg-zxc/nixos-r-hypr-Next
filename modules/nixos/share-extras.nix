# Раздаваемая система — то, что новичок с Windows ищет в первый день (решения пользователя 25.11):
# офис и шрифты для документов, VLC, архивы, Epic/GOG (Heroic), Minecraft (Prism), геймпады, принтеры и
# сканеры, диски Windows в проводнике, ноутбуки (PRIME, энергосбережение), снимки домашней папки, VR.
{ config, lib, pkgs, ... }:
let
  c = config.nextagg.share.resolved;
  hw = c.hardware;
  ownPkgs = config.nextagg.ownPackages;
  exeTypes = [ "application/x-ms-dos-executable" "application/x-msdownload" "application/x-msi"
               "application/vnd.microsoft.portable-executable" "application/vnd.appimage" "application/x-iso9660-appimage" ];
  vr = builtins.elem "vr" c.extras;
  prime = if hw.prime == null then { } else hw.prime; # модульная система смотрит в mkIf и при ложном условии
in
{
  environment.systemPackages = with pkgs; [
    libreoffice-fresh hunspell hunspellDicts.ru_RU hunspellDicts.en_US
    vlc
    kdePackages.ark p7zip unrar
    heroic # Epic Games / GOG / Amazon — нативный клиент, без песочницы
    # Minecraft; нужную Java Prism скачивает сам — встроенные JDK 8/17/21/25 — это 1,8 ГиБ образа
    (prismlauncher.override { jdks = [ jdk21 ]; }) # Vivecraft для VR ставится в нём как мод
    ntfs3g
    # программы Windows и AppImage двойным кликом (окно «Как запустить?»), удалённая помощь, отчёт
    ownPkgs.newbie-tools wineWow64Packages.stable winetricks umu-launcher rustdesk-flutter
  ] ++ lib.optionals hw.snapshots [ btrfs-assistant ]
    ++ lib.optionals vr [ wayvr ];

  programs.appimage = { enable = true; binfmt = true; };
  # OCR скриншотов: русский, английский, немецкий (все языки — 1 ГиБ)
  nextagg.tesseract = pkgs.tesseract.override { enableLanguages = [ "eng" "rus" "deu" ]; };
  # чтение с экрана (голоса mbrola, ~0,7 ГиБ) друзьям не нужно; обои Plasma — свои (Fluent)
  services.speechd.enable = lib.mkForce false;
  environment.plasma6.excludePackages = [ pkgs.kdePackages.plasma-workspace-wallpapers ];
  xdg.mime.defaultApplications = lib.genAttrs exeTypes (_: "org.nixos.RunExe.desktop");

  # шрифты, с которыми документы Word/Excel выглядят как в Windows (Arial, Times New Roman…)
  fonts.packages = with pkgs; [ corefonts vista-fonts liberation_ttf ];

  # геймпады: Xbox (Bluetooth — xpadneo, свисток — xone), PlayStation/8BitDo — ядро + steam-hardware
  hardware.bluetooth.enable = true;
  hardware.xpadneo.enable = true;
  hardware.xone.enable = true;
  hardware.steam-hardware.enable = true;
  # графический планшет (osu!, рисование): OpenTabletDriver — служба и программа настройки; настроек автора нет
  hardware.opentabletdriver.enable = true;
  services.udev.packages = [ pkgs.game-devices-udev-rules ];

  # принтеры и сканеры: CUPS с драйверами, поиск сетевых по Avahi, SANE + сетевые сканеры (eSCL/WSD)
  services.printing = {
    enable = true;
    drivers = with pkgs; [ gutenprint hplip cups-filters ];
  };
  services.avahi = {
    enable = true;
    nssmdns4 = true;
    openFirewall = true;
  };
  hardware.sane = {
    enable = true;
    extraBackends = [ pkgs.sane-airscan ];
  };

  # диски Windows: NTFS (ntfs3) видны в проводнике; найденные установщиком — в /mnt/<имя> для игр Steam
  boot.supportedFilesystems = [ "ntfs" ];
  services.udisks2.enable = true;
  fileSystems = lib.listToAttrs (map (d: lib.nameValuePair "/mnt/${d.name}" {
    device = "/dev/disk/by-uuid/${d.uuid}";
    fsType = "ntfs3";
    options = [ "nofail" "uid=1000" "gid=100" "windows_names" "x-gvfs-show" "x-systemd.device-timeout=5s" ];
  }) hw.windowsDisks);

  # ноутбук: профили питания, яркость, NVIDIA + Intel/AMD — PRIME offload (игры — `nvidia-offload`)
  services.power-profiles-daemon.enable = lib.mkIf hw.laptop true;
  services.upower.enable = lib.mkIf hw.laptop true;
  hardware.nvidia.prime = lib.mkIf (hw.prime != null && c.gpu != "mesa") ({
    offload = { enable = true; enableOffloadCmd = true; };
    nvidiaBusId = prime.nvidiaBusId or "";
  } // lib.optionalAttrs ((prime.intelBusId or null) != null) { intelBusId = prime.intelBusId; }
    // lib.optionalAttrs ((prime.amdgpuBusId or null) != null) { amdgpuBusId = prime.amdgpuBusId; });

  # снимки домашней папки (btrfs): «вернуть вчерашнюю версию файла» — Btrfs Assistant
  services.snapper.configs = lib.mkIf hw.snapshots {
    home = {
      SUBVOLUME = "/home";
      ALLOW_USERS = [ c.user.name ];
      TIMELINE_CREATE = true;
      TIMELINE_CLEANUP = true;
      TIMELINE_LIMIT_HOURLY = 8;
      TIMELINE_LIMIT_DAILY = 7;
      TIMELINE_LIMIT_WEEKLY = 4;
      TIMELINE_LIMIT_MONTHLY = 0;
      TIMELINE_LIMIT_YEARLY = 0;
    };
  };

  # VR: Quest/Pico без провода — WiVRn (и ALVR), Index/Vive — SteamVR из Steam; рабочий стол в VR — wayvr
  services.wivrn = lib.mkIf vr {
    enable = true;
    openFirewall = true; # активный рантайм OpenXR WiVRn выбирает сам
  };
  programs.alvr = lib.mkIf vr {
    enable = true;
    openFirewall = true;
  };
}
