#!/usr/bin/env bash
# Забирает внешний вид с живой системы в dotfiles/ (рядом со скриптом).
# Запускай после правок через GUI (hypr-settings,
# перетаскивание виджетов на баре, смена темы), потом git diff → commit.
#
# Копируется только своё: бэкапы *.bak* / *.save*, кэш, сокеты и сторонние
# плагины/темы с GitHub (они подключены входами flake.nix) пропускаются.
set -euo pipefail

repo=$(cd "$(dirname "$0")/.." && pwd)
dst="$repo/dotfiles"
cfg="${XDG_CONFIG_HOME:-$HOME/.config}"

# Сторонние плагины и темы: берутся из flake.nix (inputs), сюда не копируются.
third_party_plugins=(
  0xfanko.advanced-clipboard custom.rounded-corner-blur
  io.github.aaronshahriari.omatube io.github.iampoul.hackernews
  io.github.jburchel.jarvis jmthomas00.vantage ngnk.glass-weather
  nixos-resizeable.resizeable org.lsong.window-switcher sky.lofi
  sys-monitor whimsy
)

excludes=(
  --exclude='*.bak*' --exclude='*.save*' --exclude='*.sock'
  --exclude='*.log' --exclude='.git' --exclude='__pycache__'
)

copy() { # copy <src> <dst> [rsync args...]
  local src=$1 to=$2
  shift 2
  [ -e "$src" ] || { echo "нет $src — пропуск"; return 0; }
  mkdir -p "$(dirname "$to")"
  rsync -a --delete "${excludes[@]}" "$@" "$src" "$to"
}

plugin_excludes=()
for p in "${third_party_plugins[@]}"; do plugin_excludes+=(--exclude="/$p"); done

# NixOS: бар, меню, плагины, брендинг, обои.
copy "$cfg/nixos/plugins/" "$dst/nixos/plugins/" "${plugin_excludes[@]}"
copy "$cfg/nixos/extensions/" "$dst/nixos/extensions/"
copy "$cfg/nixos/branding/" "$dst/nixos/branding/"
copy "$cfg/nixos/backgrounds/" "$dst/nixos/backgrounds/"
copy "$cfg/nixos/defaults/" "$dst/nixos/defaults/"
for f in shell.json shell.toml glass-weather.json; do
  copy "$cfg/nixos/$f" "$dst/nixos/$f"
done

# Hyprland (lua-конфиги и скрипты).
copy "$cfg/hypr/" "$dst/hypr/" --exclude='lslfs*'

# Терминалы, промпт, fastfetch, btop, ввод.
copy "$cfg/ghostty/" "$dst/ghostty/"
for f in alacritty/alacritty.toml kitty/kitty.conf foot/foot.ini starship.toml btop/btop.conf xdg-terminals.list mimeapps.list; do
  copy "$cfg/$f" "$dst/$f"
done
copy "$cfg/btop/themes/" "$dst/btop/themes/"
copy "$cfg/fastfetch/" "$dst/fastfetch/"
copy "$cfg/fcitx5/" "$dst/fcitx5/" --exclude='cached_layouts'

# Bash: fastfetch, atuin, yazi, ble.sh и свои алиасы.
copy "$HOME/.bashrc" "$dst/bash/bashrc"
copy "$HOME/.XCompose" "$dst/XCompose"

# Курсоры Material Design (собраны build-xcursor.py).
copy "$HOME/.local/share/icons/material-design-dark/" "$dst/icons/material-design-dark/"

# Состояние NixOS, которое задаёт вид (закругления, прозрачность, blur —
# панель Appearance; флаги hypr; настройки плагинов; редактор по умолчанию).
st="$HOME/.local/state/nixos"
for f in appearance.lua toggles/hypr/flags.lua settings/ defaults/; do
  [ -e "$st/$f" ] && copy "$st/$f" "$dst/nixos-state/$f"
done

# Текущая тема и обои NixOS.
state="$HOME/.local/state/nixos/current"
if [ -f "$state/theme.name" ]; then
  cp "$state/theme.name" "$dst/nixos/theme.name"
fi
if [ -L "$state/background" ]; then
  readlink "$state/background" | sed "s|^$HOME/|~/|" > "$dst/nixos/background"
fi

echo "Готово: $dst"
