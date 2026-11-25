# gamemode на NixOS: модуль nixpkgs через mkForce даёт gamemoded PATH только с pkexec, поэтому
# скрипты [custom] start/end из gamemode.ini падают с «command not found» (exit 127). Добавляем
# обычные утилиты; setuid-обёрток, кроме pkexec, по-прежнему нет. (Находка 24.11 соседней сессии.)
# Приоритет 45: хост может перекрыть своим (mkOverride 40 и выше по силе).
{ config, lib, pkgs, ... }:
{
  config = lib.mkIf config.programs.gamemode.enable {
    systemd.user.services.gamemoded.environment.PATH = lib.mkOverride 45 (lib.concatStringsSep ":" [
      "${pkgs.linkFarm "pkexec" [ { name = "pkexec"; path = "${config.security.wrapperDir}/pkexec"; } ]}"
      (lib.makeBinPath (with pkgs; [ coreutils procps util-linux gnugrep gnused gawk findutils bash systemd libnotify ]))
    ]);
  };
}
