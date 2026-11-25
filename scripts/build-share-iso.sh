#!/usr/bin/env bash
# Собрать ISO раздаваемой NixOS:  bash scripts/build-share-iso.sh [папка для ISO, по умолчанию ~/Work/nixos-iso]
#   1) экспорт флейка (без личного) → в хранилище;  2) содержимое образа (scripts/iso-closure.py);
#   3) nix build ISO (--impure: пути из шагов 1–2);  4) проверка размера (≤ 7,4 ГиБ).
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
dest=${1:-$HOME/Work/nixos-iso}
work=$(mktemp -d /tmp/claude-1000/share-iso.XXXX)
trap 'rm -rf "$work"' EXIT

python3 "$repo/scripts/export-share-flake.py" "$work/etc-nixos"
# готовый список программ Магазина (nix search берёт ~4,6 ГБ памяти — у друга на 8 ГБ его не построить)
nixpkgs=$(nix eval --raw --impure --expr "(builtins.getFlake \"path:$work/etc-nixos\").inputs.nixpkgs.outPath")
nix --extra-experimental-features "nix-command flakes" search "path:$nixpkgs" '^' --json >"$work/etc-nixos/.store-index.json"
echo "$nixpkgs" >"$work/etc-nixos/.store-index.source"
flake=$(nix store add --name nixos-share-flake "$work/etc-nixos")
echo "флейк: $flake"
python3 "$repo/scripts/iso-closure.py" "$flake" "$work/contents.json"

export NIXOS_SHARE_ISO_FLAKE=$flake NIXOS_SHARE_ISO_CONTENTS=$work/contents.json
iso=$(nix build --impure --no-link --print-out-paths "$repo#nixosConfigurations.share-iso.config.system.build.isoImage")
f=$(ls "$iso"/iso/*.iso)
size=$(stat -c %s "$f")
awk -v f="$f" -v s="$size" 'BEGIN { printf "ISO: %s (%.2f ГиБ)\n", f, s / 1073741824 }'
mkdir -p "$dest"
# через временное имя: старый образ может быть открыт (QEMU), его нельзя переписывать на месте
cp --reflink=auto "$f" "$dest/.$(basename "$f").tmp" && chmod u+w "$dest/.$(basename "$f").tmp"
mv -f "$dest/.$(basename "$f").tmp" "$dest/$(basename "$f")"
cp "$work/contents.json" "$dest/$(basename "$f" .iso).contents.json"   # что положено в образ (для разбора)
[ "$size" -le $((74 * 1073741824 / 10)) ] || { echo "БОЛЬШЕ 7,4 ГиБ"; exit 1; }
echo "готово: $dest/$(basename "$f")"
