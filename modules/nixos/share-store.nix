# Магазин раздаваемой системы: индекс программ nixpkgs (без интернета, из того же nixpkgs, что система),
# Flatpak + Flathub, подсказка в терминале для неизвестных команд.
{ inputs }:
{ config, lib, pkgs, ... }:
let
  ownPkgs = config.nextagg.ownPackages;
  nixpkgsSrc = "${inputs.nixpkgs}";
in
{
  environment.systemPackages = [ ownPkgs.store ];
  services.flatpak.enable = true;

  # индекс: nix search по всему nixpkgs берёт ~4,6 ГБ памяти и ~1,5 мин — не при загрузке (рядом с рабочим столом,
  # Discord и плеером это роняло систему по памяти), а по таймеру через 10 мин и раз в час, пока не получится;
  # и только если свободно ≥ 5 ГиБ. Первый список кладёт установщик (построен при сборке образа), так что
  # здесь он строится заново только после обновления системы (сменился nixpkgs).
  systemd.timers.nixos-store-index = {
    wantedBy = [ "timers.target" ];
    timerConfig = { OnBootSec = "10min"; OnUnitActiveSec = "1h"; };
  };
  systemd.services.nixos-store-index = {
    description = "Список программ для Магазина (nix search по nixpkgs системы)";
    after = [ "nix-daemon.socket" ];
    path = [ config.nix.package pkgs.coreutils pkgs.gawk pkgs.procps ];
    environment.HOME = "/var/lib/nixos-store";
    serviceConfig = {
      Type = "oneshot";
      StateDirectory = "nixos-store";
      Nice = 19;
      IOSchedulingClass = "idle";
      CPUSchedulingPolicy = "idle";
      MemoryHigh = "5G"; # не даёт индексу вытеснить всё остальное
    };
    script = ''
      d=/var/lib/nixos-store
      [ "$(cat $d/source 2>/dev/null)" = "${nixpkgsSrc}" ] && [ -s $d/index.json ] && exit 0
      # идёт игра (Steam/Proton, Wine, gamescope) — не мешаем, попробуем через час
      if pgrep -f 'SteamLaunch|steamapps/common' >/dev/null || pgrep -x wineserver >/dev/null || pgrep -x gamescope >/dev/null; then
        echo "идёт игра — построю список программ позже"; exit 0
      fi
      avail=$(awk '/^MemAvailable:/ {print int($2 / 1048576)}' /proc/meminfo)
      if [ "$avail" -lt "''${NIXOS_STORE_INDEX_MIN_GIB:-5}" ]; then
        echo "свободно $avail ГиБ памяти — построю список программ позже"; exit 0
      fi
      nix --extra-experimental-features "nix-command flakes" search "path:${nixpkgsSrc}" '^' --json \
        > $d/index.json.tmp
      chmod 644 $d/index.json.tmp
      mv $d/index.json.tmp $d/index.json
      echo "${nixpkgsSrc}" > $d/source
    '';
  };

  # неизвестная команда в терминале → «есть в программе X, установите через Магазин»
  programs.command-not-found.enable = false;
  programs.bash.interactiveShellInit = ''
    command_not_found_handle() { ${ownPkgs.store}/bin/nixos-store-hint "$1"; }
  '';
}
