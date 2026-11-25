#!/usr/bin/env bash
# Берёт последний (не бета) релиз Millennium с GitHub и пишет release.json рядом.
# Вызывается из nextagg-update (scripts/update.d/millennium).
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
api=https://api.github.com/repos/SteamClientHomebrew/Millennium/releases/latest
tag=$(curl -fsSL "$api" | python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"])')
asset="millennium-${tag}-linux-x86_64.tar.gz"
url="https://github.com/SteamClientHomebrew/Millennium/releases/download/${tag}/${asset}"
hex=$(curl -fsSL "${url%.tar.gz}.sha256" | awk '{print $1}')
sri=$(python3 -c "import base64,sys; print(\"sha256-\"+base64.b64encode(bytes.fromhex(sys.argv[1])).decode())" "$hex")
new=$(printf '{\n  "version": "%s",\n  "url": "%s",\n  "hash": "%s"\n}\n' "${tag#v}" "$url" "$sri")
if [ "$new" != "$(cat "$here/release.json" 2>/dev/null)" ]; then
  printf '%s' "$new" > "$here/release.json"
  echo "Millennium → ${tag}"
else
  echo "Millennium ${tag} — уже последний"
fi
