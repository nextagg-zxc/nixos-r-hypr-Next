#!/usr/bin/env bash
# Вид KDE «как Windows» (раздаваемая система).
#   nixos-kde-look init [win11|win10]   — до первого входа в KDE: тема, клавиши, ярлыки (один раз;
#                                          повторно ничего не меняет — правки друга остаются)
#   nixos-kde-look apply win11|win10    — сменить вид у работающего Plasma (панель строится заново)
#   nixos-kde-look reset                — вернуть вид Windows, выбранный сейчас
# Выбор по умолчанию — /etc/nixos-kde/look (из choices.json установщика).
# Переменные для тестов: NIXOS_KDE_LOOK_SHARE (папка share с темами), NIXOS_KDE_APPS (где искать .desktop).
set -euo pipefail

share=${NIXOS_KDE_LOOK_SHARE:-@out@/share}
state=${XDG_STATE_HOME:-$HOME/.local/state}/nixos-kde
cfg=${XDG_CONFIG_HOME:-$HOME/.config}
apps=${NIXOS_KDE_APPS:-/etc/profiles/per-user/$USER/share/applications:/run/current-system/sw/share/applications}

usage() { sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 2; }

look_of() {
  case "${1:-}" in
    win11|win10) echo "$1" ;;
    "") cat /etc/nixos-kde/look 2>/dev/null || echo win11 ;;
    *) usage ;;
  esac
}

# [файл][группа] key=value из contents/defaults → kwriteconfig6 (kvantum — в ~/.config/Kvantum)
write_defaults() {
  local defaults=$1 file="" groups=() line key val
  local header_re='^\[([^]]+)\]\[([^]]+)\](\[([^]]+)\])?$'
  while IFS= read -r line || [ -n "$line" ]; do
    line=${line%$'\r'}
    [ -z "$line" ] && continue
    if [[ $line =~ $header_re ]]; then
      file=${BASH_REMATCH[1]}
      groups=("${BASH_REMATCH[2]}")
      [ -n "${BASH_REMATCH[4]}" ] && groups+=("${BASH_REMATCH[4]}")
      continue
    fi
    key=${line%%=*} val=${line#*=}
    if [ "$file" = kvantum ]; then
      mkdir -p "$cfg/Kvantum"
      kwriteconfig6 --file "$cfg/Kvantum/kvantum.kvconfig" --group General --key "$key" "$val"
    else
      local gargs=()
      for g in "${groups[@]}"; do gargs+=(--group "$g"); done
      kwriteconfig6 --file "$cfg/$file" "${gargs[@]}" --key "$key" "$val"
    fi
  done <"$defaults"
}

find_app() {
  local d
  IFS=: read -ra dirs <<<"$apps"
  for d in "${dirs[@]}"; do
    [ -f "$d/$1" ] && { echo "$d/$1"; return 0; }
  done
  return 1
}

shortcut() { # имя-файла содержимое
  local f="$desk/$1"
  [ -e "$f" ] && return 0
  printf '%s\n' "$2" >"$f"
  chmod +x "$f"
}

desktop_icons() {
  # папки «Рабочий стол», «Загрузки»… на языке системы
  if [ -r /etc/locale.conf ]; then set -a; . /etc/locale.conf; set +a; fi
  xdg-user-dirs-update >/dev/null 2>&1 || true
  desk=$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")
  mkdir -p "$desk"
  shortcut this-pc.desktop "[Desktop Entry]
Type=Application
Name=Этот компьютер
Name[en]=This PC
Icon=computer
Exec=dolphin --new-window /"
  shortcut home.desktop "[Desktop Entry]
Type=Link
Name=Домашняя папка
Name[en]=Home
Icon=user-home
URL=file://$HOME"
  shortcut trash.desktop "[Desktop Entry]
Type=Link
Name=Корзина
Name[en]=Trash
Icon=user-trash-full
EmptyIcon=user-trash
URL=trash:/"
  local id src
  for id in firefox.desktop org.nixos.Store.desktop steam.desktop discord.desktop spotify.desktop \
            soundcloud.desktop zapret-hub.desktop org.nixos.Settings.desktop; do
    src=$(find_app "$id") || continue
    [ -e "$desk/$id" ] && continue
    cp "$src" "$desk/$id"
    chmod u+w,+x "$desk/$id"
  done
}

keyboard() { # раскладки друга (выбраны в установщике; файл пишет share.nix), Alt+Shift — как в Windows
  local f=${NIXOS_SHARE_KEYBOARD:-/etc/nixos-share/keyboard} list
  [ -r "$f" ] || return 0
  list=$(head -1 "$f")
  [ -n "$list" ] || return 0
  kwriteconfig6 --file "$cfg/kxkbrc" --group Layout --key Use true
  kwriteconfig6 --file "$cfg/kxkbrc" --group Layout --key LayoutList "$list"
  kwriteconfig6 --file "$cfg/kxkbrc" --group Layout --key ResetOldOptions true
  kwriteconfig6 --file "$cfg/kxkbrc" --group Layout --key Options "grp:alt_shift_toggle"
}

no_gtk_sync() { # «оба рабочих стола»: тема GTK — от Hyprland/home-manager, KDE её не переписывает
  kwriteconfig6 --file "$cfg/kded6rc" --group Module-gtkconfig --key autoload false
}

shortcuts() { # клавиши Windows, которых нет в Plasma по умолчанию
  kwriteconfig6 --file "$cfg/kglobalshortcutsrc" --group services --group org.kde.krunner.desktop --key _launch "Meta+R	Alt+Space"
  kwriteconfig6 --file "$cfg/kglobalshortcutsrc" --group services --group systemsettings.desktop --key _launch "Meta+I"
  kwriteconfig6 --file "$cfg/kglobalshortcutsrc" --group services --group org.nixos.Keys.desktop --key _launch "Meta+K"
  kwriteconfig6 --file "$cfg/kglobalshortcutsrc" --group services --group org.kde.plasma-systemmonitor.desktop --key _launch "Ctrl+Shift+Esc"
  kwriteconfig6 --file "$cfg/kglobalshortcutsrc" --group services --group org.kde.spectacle.desktop \
    --key RectangularRegionScreenShot "Meta+Shift+S	Meta+Shift+Print"
  # Win+↑ — развернуть (в Plasma по умолчанию это «прилипнуть вверх»), как в Windows
  kwriteconfig6 --file "$cfg/kglobalshortcutsrc" --group kwin --key "Window Maximize" "Meta+Up	Meta+PgUp,Meta+PgUp,Maximize Window"
  kwriteconfig6 --file "$cfg/kglobalshortcutsrc" --group kwin --key "Window Quick Tile Top" "none,Meta+Up,Quick Tile Window to the Top"
}

cmd=${1:-}; shift || true
case "$cmd" in
  init)
    [ -e "$state/init-done" ] && exit 0
    look=$(look_of "${1:-}")
    lnf=org.nixos.${look/win/windows}
    write_defaults "$share/plasma/look-and-feel/$lnf/contents/defaults"
    kwriteconfig6 --file "$cfg/kdeglobals" --group KDE --key LookAndFeelPackage "$lnf"
    shortcuts
    keyboard
    no_gtk_sync
    desktop_icons
    mkdir -p "$state"
    echo "$look" >"$state/look"
    touch "$state/init-done"
    ;;
  apply|reset)
    if [ "$cmd" = reset ]; then look=$(cat "$state/look" 2>/dev/null || look_of ""); else
      [ -n "${1:-}" ] || usage; look=$(look_of "$1"); fi
    lnf=org.nixos.${look/win/windows}
    # окно ей не нужно: так работает и без графической сессии (из «Настройки системы», ssh, тестов)
    QT_QPA_PLATFORM=offscreen plasma-apply-lookandfeel --apply "$lnf" --resetLayout
    write_defaults "$share/plasma/look-and-feel/$lnf/contents/defaults"
    mkdir -p "$state"
    echo "$look" >"$state/look"
    ;;
  *) usage ;;
esac
