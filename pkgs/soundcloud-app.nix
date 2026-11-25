# SoundCloud отдельным окном: Chromium в режиме --app со своим профилем.
# app_id окна на Wayland Chromium задаёт сам: chrome-<адрес>-Default (--class в режиме --app
# игнорируется, проверено 24.11), поэтому окно узнаётся по PID из PID-файла; --class=soundcloud
# остаётся меткой процесса в cmdline (по ней проверяется, что PID — ещё наш Chromium).
# Chromium отдаёт MPRIS как org.mpris.MediaPlayer2.chromium.instance<PID>; обёртка делает exec,
# поэтому PID в $XDG_RUNTIME_DIR/soundcloud-app.pid — это PID самого Chromium, и меню Win+B
# узнаёт именно это окно (PlayerPick.js), а не любой другой Chromium.
# Второй запуск при открытом окне только фокусирует его: иначе Chromium передал бы работу
# живому процессу и вышел, а PID-файл указал бы на мёртвый процесс.
# Громкость: MPRIS Chromium её не меняет (Volume всегда 1.0), поэтому поток PipeWire называется
# «SoundCloud» (libpulse читает PULSE_PROP_OVERRIDE) — по этому имени меню и крутит громкость.
# Ярлык soundcloud.desktop и иконка (из Papirus, в hicolor — видна при любой теме) — в пакете.
# Для тестов: SOUNDCLOUD_APP_CHROMIUM — путь к chromium, SOUNDCLOUD_APP_URL — адрес.
{
  lib,
  runCommand,
  writeShellApplication,
  chromium,
  coreutils,
  util-linux,
  papirus-icon-theme,
}:
let
  app = writeShellApplication {
    name = "soundcloud-app";
    # hyprctl берётся из PATH сессии (версия совпадает с запущенным Hyprland); его нет — фокус пропускается.
    runtimeInputs = [
      coreutils
      util-linux
    ];
    text = ''
      chromium_bin=''${SOUNDCLOUD_APP_CHROMIUM:-${lib.getExe chromium}}
      url=''${SOUNDCLOUD_APP_URL:-https://soundcloud.com}
      run=''${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
      profile=''${XDG_DATA_HOME:-$HOME/.local/share}/soundcloud-app
      pidfile=$run/soundcloud-app.pid
      mkdir -p "$run" "$profile"

      alive() {
        local pid=$1
        [[ $pid =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null || return 1
        # Chromium склеивает свой cmdline в одну строку через пробелы — ищем слово, а не строку.
        local cmd
        cmd=$(tr '\0' ' ' 2>/dev/null <"/proc/$pid/cmdline") || return 1
        [[ " $cmd " == *" --class=soundcloud "* ]]
      }

      # Проверка и запись PID под замком: два одновременных запуска не перепишут файл друг другу.
      exec 9>"$pidfile.lock"
      flock 9
      old=$(cat "$pidfile" 2>/dev/null || true)
      if alive "$old"; then
        # Hyprland с Lua-конфигом принимает в dispatch Lua-выражение; старый синтаксис — запасной.
        if command -v hyprctl >/dev/null; then
          hyprctl dispatch "hl.dsp.focus({ window = \"pid:$old\" })" >/dev/null 2>&1 ||
            hyprctl dispatch focuswindow "pid:$old" >/dev/null 2>&1 || true
        fi
        exit 0
      fi
      echo $$ >"$pidfile"
      exec 9>&-
      export PULSE_PROP_OVERRIDE="application.name='SoundCloud' application.icon_name='soundcloud'"
      exec "$chromium_bin" \
        --app="$url" \
        --class=soundcloud \
        --user-data-dir="$profile" \
        --ozone-platform-hint=auto \
        --no-first-run \
        "$@"
    '';
  };
in
runCommand "soundcloud-app"
  {
    meta = {
      description = "SoundCloud в отдельном окне Chromium для меню Win+B";
      mainProgram = "soundcloud-app";
    };
  }
  ''
    mkdir -p $out/bin $out/share/applications $out/share/icons/hicolor/scalable/apps
    ln -s ${app}/bin/soundcloud-app $out/bin/soundcloud-app
    cp ${papirus-icon-theme}/share/icons/Papirus/64x64/apps/soundcloud.svg \
      $out/share/icons/hicolor/scalable/apps/soundcloud.svg
    cat >$out/share/applications/soundcloud.desktop <<'DESKTOP'
    [Desktop Entry]
    Type=Application
    Name=SoundCloud
    Comment=SoundCloud отдельным окном; управляется из меню Win+B
    Exec=soundcloud-app
    Icon=soundcloud
    StartupWMClass=chrome-soundcloud.com__-Default
    Categories=AudioVideo;Audio;Player;
    Keywords=soundcloud;music;музыка;
    Terminal=false
    DESKTOP
    sed -i 's/^    //' $out/share/applications/soundcloud.desktop
  ''
