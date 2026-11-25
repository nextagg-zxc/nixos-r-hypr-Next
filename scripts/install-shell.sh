#!/usr/bin/env bash
# Оболочка nixos-r-hypr-Next на свою NixOS одной командой:
#   nix --extra-experimental-features 'nix-command flakes' run github:nextagg-zxc/nixos-r-hypr-Next#install
# В /etc/nixos рядом с вашей configuration.nix (она не меняется) появляется flake.nix, который добавляет к ней
# Hyprland и оболочку (бар, меню, темы) для вашего пользователя. Привычное «sudo nixos-rebuild switch» дальше
# само берёт этот флейк — оболочка не пропадёт при обновлениях. Прежняя система остаётся в меню загрузчика.
# Убрать оболочку: sudo rm /etc/nixos/flake.nix /etc/nixos/flake.lock && sudo nixos-rebuild switch
set -euo pipefail

REPO=${NIXOS_HYPR_REPO:-github:nextagg-zxc/nixos-r-hypr-Next}
SRC=${NIXOS_HYPR_SRC:-/etc/nixos}
USER_NAME=${NIXOS_HYPR_USER:-${SUDO_USER:-$(id -un)}}
HOST=${NIXOS_HYPR_HOST:-$(hostname)}
SUDO=sudo; [ "$(id -u)" = 0 ] && SUDO=
[ -n "${NIXOS_HYPR_DRY:-}" ] && SUDO=

say() { printf '\033[1;35m»\033[0m %s\n' "$*"; }
die() { printf '\033[1;31mОшибка:\033[0m %s\n' "$*" >&2; exit 1; }

[ -e /etc/NIXOS ] || [ -n "${NIXOS_HYPR_DRY:-}" ] || die "это не NixOS (нужна установленная NixOS; для «с нуля» — ISO)"
[ "$USER_NAME" != root ] || die "запустите от своего пользователя (не root) — оболочка ставится ему"
[[ $USER_NAME =~ ^[a-z_][a-z0-9_-]*$ ]] || die "странное имя пользователя: $USER_NAME"
if [ -e "$SRC/flake.nix" ]; then
  cat >&2 <<EOF
Ваша $SRC — уже флейк, его установщик не трогает. Подключите оболочку сами:
  inputs.nixos-r-hypr-Next.url = "$REPO";
  # в modules вашей nixosConfiguration:
  nixos-r-hypr-Next.nixosModules.shell
  { nextagg.shell = { enable = true; user = "$USER_NAME"; }; }
(nixpkgs лучше взять тот же: inputs.nixpkgs.follows = "nixos-r-hypr-Next/nixpkgs")
EOF
  exit 1
fi
[ -f "$SRC/configuration.nix" ] || die "нет $SRC/configuration.nix"

say "Поставлю Hyprland и оболочку (бар, меню, темы) пользователю $USER_NAME на $HOST."
say "В $SRC добавлю flake.nix (ваша configuration.nix не меняется); дальше обычный nixos-rebuild switch — уже с оболочкой."
if [ -z "${NIXOS_HYPR_YES:-}" ]; then
  read -rp "Продолжить? [y/N] " a
  [[ $a == [yYдД]* ]] || exit 0
fi

tmp=$(mktemp)
cat >"$tmp" <<EOF
# Добавлено установщиком nixos-r-hypr-Next: ваша configuration.nix + Hyprland и оболочка для $USER_NAME.
# Обычное «sudo nixos-rebuild switch» берёт этот флейк сам. Обновить оболочку и систему:
#   sudo nix flake update --flake /etc/nixos && sudo nixos-rebuild switch
# Убрать оболочку: удалить этот flake.nix и flake.lock, затем sudo nixos-rebuild switch.
{
  inputs.nixos-r-hypr-Next.url = "$REPO";
  outputs = { nixos-r-hypr-Next, ... }: {
    nixosConfigurations."$HOST" = nixos-r-hypr-Next.lib.mkShellHost [
      ./configuration.nix
      { nextagg.shell = { enable = true; user = "$USER_NAME"; }; }
    ];
  };
}
EOF
$SUDO install -m 644 "$tmp" "$SRC/flake.nix"
rm -f "$tmp"
# /etc/nixos в git — флейк видит только файлы из индекса
if [ -d "$SRC/.git" ]; then
  $SUDO git -C "$SRC" add flake.nix
fi

if [ -n "${NIXOS_HYPR_DRY:-}" ]; then
  say "Пробный запуск: флейк в $SRC, пересборка пропущена."
  exit 0
fi
say "Собираю систему (первый раз — несколько минут, качает пакеты)…"
$SUDO nixos-rebuild switch --flake "$SRC#$HOST"
say "Готово. Выйдите из сеанса и выберите при входе «Hyprland (uwsm)». Меню — Win+B."
