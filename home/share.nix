# Домашняя папка друга (раздаваемая система): вид без личного, плеер в фоне, автозапуск Discord и плеера.
# Что выбрано — osConfig.nextagg.share.resolved (choices.json после разбора).
{ config, lib, pkgs, osConfig, inputs, ... }:
let
  c = osConfig.nextagg.share.resolved;
  ownPkgs = osConfig.nextagg.ownPackages;
  spotify = c.player == "spotify";
in
{
  imports = [ inputs.spicetify-nix.homeManagerModules.spicetify ];

  home.username = c.user.name;
  home.homeDirectory = "/home/${c.user.name}";
  home.stateVersion = "26.05";

  # вид Hyprland без личного (при «только KDE» не раскладывается)
  nextagg.look = {
    enable = osConfig.nextagg.desktop.enable;
    profile = "share";
  };

  # терминал как у пользователя: fastfetch, atuin, pay-respects, yazi, ble.sh (блоки .bashrc вида share)
  home.packages = with pkgs; [ fastfetch atuin pay-respects yazi zoxide ]
    ++ lib.optional (!spotify) ownPkgs.soundcloud-app;
  home.file.".local/share/blesh".source = "${pkgs.blesh}/share/blesh";

  # плеер меню Win+B: spotify | soundcloud (PlayerPick.js, media-background, SUPER+W/Q)
  xdg.configFile."nixos/media-player".text = c.player + "\n";

  # автозапуск (XDG autostart): Discord обычным окном, плеер — скрытым
  nextagg.autostart.defaults = [
    { id = "discord.desktop"; name = "Discord"; command = "discord"; icon = "discord"; }
  ] ++ (if spotify
    then [ { id = "spotify.desktop"; name = "Spotify"; command = "spotify"; icon = "spotify"; hidden = true; } ]
    else [ { id = "soundcloud.desktop"; name = "SoundCloud"; command = "soundcloud-app"; icon = "soundcloud"; hidden = true; } ]);

  # выбранный плеер всегда в фоне: перезапуск скрытым, если завершился
  systemd.user.services.media-background = {
    Unit = { Description = "Keep the chosen music player running in the background for the Win+B menu"; After = [ "graphical-session.target" ]; };
    Service = {
      ExecStart = "${pkgs.writeShellApplication {
        name = "media-background";
        runtimeInputs = [ pkgs.procps pkgs.jq pkgs.hyprland pkgs.uwsm pkgs.coreutils pkgs.gnugrep ];
        text = builtins.readFile ./scripts/media-background;
      }}/bin/media-background";
      Restart = "always";
      Environment = [ "PATH=/etc/profiles/per-user/${c.user.name}/bin:/run/current-system/sw/bin" ];
    };
    Install.WantedBy = [ "graphical-session.target" ];
  };

  # Spotify с темой Spicetify StarryNight Lite и мостом очереди для меню Win+B (как у пользователя)
  programs.spicetify = lib.mkIf spotify {
    enable = true;
    theme = {
      name = "StarryNightLite";
      src = ../overrides/spicetify/StarryNightLite;
      injectCss = true;
      injectThemeJs = true;
      replaceColors = true;
      overwriteAssets = false;
    };
    colorScheme = "Base";
    wayland = true;
    enabledExtensions = [
      { src = ./spotify-queue; name = "nextagg-queue.js"; }
      { src = ./spotify-queue; name = "preload-covers.js"; }
    ];
    enabledCustomApps = [ inputs.spicetify-nix.legacyPackages.${pkgs.stdenv.hostPlatform.system}.apps.marketplace ];
  };
  systemd.user.services.spotify-queue = lib.mkIf spotify {
    Unit = { Description = "Spotify queue bridge for the Win+B menu (Spicetify nextagg-queue)"; After = [ "graphical-session.target" ]; };
    Service = {
      ExecStart = "${pkgs.python3}/bin/python3 ${./spotify-queue/bridge.py} serve";
      Restart = "always";
      Environment = [
        "NEXTAGG_FFMPEG=${pkgs.ffmpeg-headless}/bin/ffmpeg"
        "NEXTAGG_FFPROBE=${pkgs.ffmpeg-headless}/bin/ffprobe"
      ];
    };
    Install.WantedBy = [ "graphical-session.target" ];
  };

  # Автовход: связку ключей некому открыть паролем входа — без этого Discord/Spotify при первом
  # запуске просят «придумать пароль для новой связки». Создаём пустую незашифрованную связку login
  # (только если её ещё нет). Без автовхода её создаёт и открывает пароль входа (PAM SDDM).
  home.activation.autologinKeyring = lib.mkIf (builtins.elem "autologin" c.extras) (
    lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      k="$HOME/.local/share/keyrings"
      if [ ! -e "$k/login.keyring" ]; then
        run mkdir -p "$k"
        run chmod 700 "$k"
        printf '[keyring]\ndisplay-name=login\nctime=0\nmtime=0\nlock-on-idle=false\nlock-after=false\n' > "$k/login.keyring"
        run chmod 600 "$k/login.keyring"
      fi
      [ -e "$k/default" ] || echo login > "$k/default"
    ''
  );

  # KDE «как Windows»: тема, клавиши и ярлыки — до первого входа (потом не трогаем правки друга)
  home.activation.kdeWindows = lib.mkIf osConfig.nextagg.kdeMinimal.enable (
    lib.hm.dag.entryAfter [ "writeBoundary" ] (''
      run ${ownPkgs.kde-windows}/bin/nixos-kde-look init || echo "nixos-kde-look: вид KDE применится позже" >&2
    '' + lib.optionalString (builtins.elem "autologin" c.extras) ''
      # автовход: бумажник KDE некому открыть паролем — без этого Spotify/Discord просят «создать
      # бумажник». Секреты хранит уже открытая пустая связка gnome-keyring (activation autologinKeyring).
      if ! grep -qs '^Enabled=' "$HOME/.config/kwalletrc"; then
        run ${pkgs.kdePackages.kconfig}/bin/kwriteconfig6 --file "$HOME/.config/kwalletrc" --group Wallet --key Enabled false
      fi
    '')
  );

  # обновления: раз в день проверка и уведомление «Есть обновления» (без установки)
  systemd.user.services.nixos-update-check = {
    Unit.Description = "Проверка обновлений системы";
    Service = { Type = "oneshot"; ExecStart = "${ownPkgs.system-settings}/bin/nixos-settings --check-updates"; };
  };
  systemd.user.timers.nixos-update-check = {
    Unit.Description = "Проверка обновлений раз в день";
    Timer = { OnBootSec = "15min"; OnUnitActiveSec = "1d"; Persistent = true; };
    Install.WantedBy = [ "timers.target" ];
  };

  # Flathub и Roblox (Sober) — когда появится интернет: служба повторяет попытку, пока не получится
  systemd.user.services.flathub-defaults = {
    Unit.Description = "Flathub и Sober (Roblox) при первом выходе в сеть";
    Service = {
      Type = "oneshot";
      ExecStart = "${pkgs.writeShellScript "flathub-defaults" ''
        set -e
        f=${pkgs.flatpak}/bin/flatpak
        $f remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
        $f info --user org.vinegarhq.Sober >/dev/null 2>&1 || $f install --user -y --noninteractive flathub org.vinegarhq.Sober
      ''}";
      Restart = "on-failure";
      RestartSec = 300;
    };
    Install.WantedBy = [ "default.target" ];
  };

  # Millennium: ссылки в папке Steam (как у пользователя)
  home.activation.millenniumLinks = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    s="$HOME/.local/share/Steam"
    if [ -d "$s/ubuntu12_64" ]; then
      run ln -sfn /usr/lib/millennium/libmillennium_bootstrap_x86.so "$s/ubuntu12_32/libXtst.so.6"
      run ln -sfn /usr/lib/millennium/libmillennium_bootstrap_hhx64.so "$s/ubuntu12_64/libXtst.so.6"
      run ln -sfn /usr/lib/millennium/libmillennium_hhx64.so "$s/ubuntu12_64/libmillennium_hhx64.so"
      run mkdir -p "$s/steamrt64"
      run ln -sfn /run/host/usr/lib64/millennium/libmillennium_bootstrap_x64.so "$s/steamrt64/libXtst.so.6"
    fi
  '';
}
