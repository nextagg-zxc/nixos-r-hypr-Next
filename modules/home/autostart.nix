# Программа «Автозапуск» и записи автозапуска по умолчанию (раздаваемая система: Discord + плеер).
# Записи создаются при активации, только если файла ещё нет — правки друга не затираются.
# У пользователя nextagg defaults пустой: Discord и Spotify стартуют через hypr/scripts/autostart-media.sh.
{ self }:
{ config, lib, pkgs, osConfig ? { }, ... }:
let
  cfg = config.nextagg.autostart;
  pkg = (osConfig.nextagg.ownPackages or self.packages.${pkgs.stdenv.hostPlatform.system}).autostart;
  entry = lib.types.submodule {
    options = {
      id = lib.mkOption { type = lib.types.strMatching "[A-Za-z0-9._-]+\\.desktop"; };
      name = lib.mkOption { type = lib.types.str; };
      command = lib.mkOption { type = lib.types.str; description = "Exec (кавычки по спецификации desktop entry)"; };
      hidden = lib.mkOption { type = lib.types.bool; default = false; };
      delay = lib.mkOption { type = lib.types.ints.between 0 600; default = 0; };
      where = lib.mkOption { type = lib.types.enum [ "all" "hyprland" "kde" ]; default = "all"; };
      icon = lib.mkOption { type = lib.types.str; default = ""; };
    };
  };
in
{
  options.nextagg.autostart = {
    enable = lib.mkOption { type = lib.types.bool; default = true; description = "Программа «Автозапуск»"; };
    defaults = lib.mkOption { type = lib.types.listOf entry; default = [ ]; };
  };
  config = lib.mkIf cfg.enable {
    home.packages = [ pkg ];
    home.activation.autostartSeed = lib.mkIf (cfg.defaults != [ ]) (
      lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${pkg}/bin/autostart-python -m autostart --seed ${pkgs.writeText "autostart-defaults.json" (builtins.toJSON cfg.defaults)}
      ''
    );
  };
}
