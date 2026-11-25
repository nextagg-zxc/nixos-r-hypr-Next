#!/usr/bin/env bash
# Последний релиз mise (статическая musl-сборка) → release.json. Зовётся из nextagg-update.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
tag=$(curl -fsSL https://api.github.com/repos/jdx/mise/releases/latest | python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"])')
url="https://github.com/jdx/mise/releases/download/${tag}/mise-${tag}-linux-x64-musl.tar.gz"
hash=$(nix --extra-experimental-features nix-command store prefetch-file --json "$url" | python3 -c 'import json,sys; print(json.load(sys.stdin)["hash"])')
printf '{\n  "version": "%s",\n  "url": "%s",\n  "hash": "%s"\n}\n' "${tag#v}" "$url" "$hash" > "$here/release.json"
echo "mise → ${tag}"
