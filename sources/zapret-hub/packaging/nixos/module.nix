# services.zapret-hub: программа, служба nfqws и права pkexec для неё.
# На NixOS юниты и /etc/hosts описывает модуль, поэтому:
#  - автозапуск — файл-флаг /opt/zapret-hub/autostart (его ставит помощник), а zapret-hub-autostart
#    при загрузке запускает службу, если флаг есть (systemctl enable в /etc/systemd здесь невозможен);
#  - /etc/hosts — копия, а не ссылка в хранилище (помощник может дописать блок Flowseal), и после
#    каждой пересборки активация возвращает блок из /opt/zapret-hub/hosts.block.
{ config, lib, pkgs, ... }:
let
  cfg = config.services.zapret-hub;
  helper = "${cfg.package}/libexec/zapret-hub-helper";
in
{
  options.services.zapret-hub = {
    enable = lib.mkEnableOption "Zapret Hub (обход блокировок: zapret + стратегии Flowseal)";
    package = lib.mkOption {
      type = lib.types.package;
      default = pkgs.callPackage ./package.nix { };
      description = "Пакет Zapret Hub.";
    };
  };

  config = lib.mkIf cfg.enable {
    # окно, ярлык, иконка и действие polkit (share/polkit-1/actions попадает в профиль системы)
    environment.systemPackages = [ cfg.package ];
    security.polkit.enable = true;

    systemd.services.zapret-hub = {
      description = "Zapret Hub — обход блокировок (zapret, стратегии Flowseal)";
      after = [ "network-online.target" ];
      wants = [ "network-online.target" ];
      serviceConfig = {
        Type = "simple";
        ExecStartPre = "${helper} fw-up";
        ExecStart = "${helper} run";
        ExecStopPost = "${helper} fw-down";
        Restart = "on-failure";
        RestartSec = 3;
      };
    };

    systemd.services.zapret-hub-autostart = {
      description = "Zapret Hub: включить обход при загрузке, если он включён в программе";
      wantedBy = [ "multi-user.target" ];
      after = [ "network-online.target" ];
      wants = [ "network-online.target" ];
      unitConfig.ConditionPathExists = "/opt/zapret-hub/autostart";
      serviceConfig = {
        Type = "oneshot";
        ExecStart = "${config.systemd.package}/bin/systemctl start --no-block zapret-hub.service";
      };
    };

    environment.etc.hosts.mode = "0644";
    system.activationScripts.zapretHubHosts = lib.stringAfter [ "etc" ] ''
      if [ -s /opt/zapret-hub/hosts.block ]; then
        ${helper} hosts-restore || echo "zapret-hub: не удалось вернуть блок hosts" >&2
      fi
    '';
  };
}
