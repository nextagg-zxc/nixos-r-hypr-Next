# «Только оболочка» (публичный репозиторий nixos-r-hypr-Next): Hyprland с конфигом автора и Quickshell-оболочка
# (бар, меню, плагины, темы, обои — вид share, без личного) поверх своей NixOS человека. Без KDE и без программ
# раздаваемой системы (Магазин, Настройка системы, Steam/Discord/Spotify, Zapret Hub).
#   nextagg.shell = { enable = true; user = "<пользователь>"; };
{ inputs, self }:
{ config, lib, pkgs, ... }:
let
  cfg = config.nextagg.shell;
in
{
  options.nextagg.shell = {
    enable = lib.mkEnableOption "оболочка nixos-r-hypr-Next (Hyprland + бар, меню, темы)";
    user = lib.mkOption {
      type = lib.types.str;
      description = "Пользователь, которому ставится рабочий стол (вид раскладывается в его домашнюю папку).";
    };
  };

  config = lib.mkIf cfg.enable {
    nextagg.desktop = { enable = true; user = cfg.user; };
    # Zapret Hub — программа, а не оболочка
    services.zapret-hub.enable = lib.mkForce false;
    nixpkgs.config.allowUnfree = lib.mkDefault true;

    home-manager = {
      useGlobalPkgs = true;
      useUserPackages = true;
      backupFileExtension = "hm-bak";
      extraSpecialArgs = { inherit inputs self; };
      sharedModules = [ self.homeManagerModules.look ];
      users.${cfg.user} = { pkgs, ... }: {
        home.stateVersion = lib.mkDefault config.system.stateVersion;
        nextagg.look = { enable = true; profile = "share"; };
        # терминал как у автора: fastfetch, atuin, pay-respects, yazi, zoxide, ble.sh (их ждёт .bashrc вида)
        home.packages = with pkgs; [ fastfetch atuin pay-respects yazi zoxide ];
        home.file.".local/share/blesh".source = "${pkgs.blesh}/share/blesh";
      };
    };
  };
}
