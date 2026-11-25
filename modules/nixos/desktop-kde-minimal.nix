# KDE Plasma 6 для раздаваемой системы — «как Windows 11/10» (pkgs/kde-windows).
# Вид записывается до первого входа (home/share.nix → nixos-kde-look init), поэтому друг с первой
# секунды видит панель и «Пуск» как в Windows. Выбор 11/10 — /etc/nixos-kde/look (choices.json).
{ config, lib, pkgs, ... }:
let
  cfg = config.nextagg.kdeMinimal;
  ownPkgs = config.nextagg.ownPackages;
in
{
  options.nextagg.kdeMinimal = {
    enable = lib.mkEnableOption "KDE Plasma 6 «как Windows» (раздаваемая система)";
    look = lib.mkOption {
      type = lib.types.enum [ "win11" "win10" ];
      default = "win11";
      description = "Вид при первом входе: Windows 11 или Windows 10.";
    };
  };

  config = lib.mkIf cfg.enable {
    services.desktopManager.plasma6.enable = true;
    services.displayManager.sddm = {
      enable = true;
      wayland.enable = true;
    };
    # окно приветствия Plasma не нужно: вид уже настроен, помощь — «Настройка системы»
    environment.plasma6.excludePackages = [ pkgs.kdePackages.plasma-welcome ];
    # почта/календарь KDE PIM (kmail, akonadi + MariaDB в фоне) новичку не нужны — тормозят вход
    programs.kde-pim.enable = false;
    environment.systemPackages = [
      ownPkgs.kde-windows
      pkgs.fluent-icon-theme
      pkgs.nixos-icons # снежинка на кнопке «Пуск»
      pkgs.kdePackages.qtstyleplugin-kvantum
      pkgs.xdg-user-dirs
    ];
    environment.etc."nixos-kde/look".text = cfg.look + "\n";
  };
}
