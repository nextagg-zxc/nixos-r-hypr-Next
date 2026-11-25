echo "List NixOS's aarch64 repository ahead of Arch Linux ARM's on the N1x"

# default/pacman/aarch64/pacman-edge.conf puts [nixos] first so NixOS's builds
# (its NVIDIA driver among them) win over Arch Linux ARM's. Installs from
# earlier N1x images list it last, where an Arch Linux ARM update could replace
# them. Move the [nixos] section in place so other edits to the file survive.
if ! nixos-hw-aarch64-n1x; then
  exit 0
fi

conf=/etc/pacman.conf
first_repo=$(grep -E '^\[[^]]+\]' "$conf" | grep -vx '\[options\]' | head -1)

if [[ $first_repo == "[nixos]" ]] || ! grep -qx '\[nixos\]' "$conf"; then
  exit 0
fi

reordered=$(mktemp)
awk '
  # Split the file into the [nixos] section and everything else, then print
  # the section again just before the first repository after [options].
  /^\[[^]]+\]/ { in_nixos = ($0 == "[nixos]") }
  in_nixos { nixos = nixos $0 "\n"; next }
  { rest[++n] = $0 }
  END {
    sub(/\n+$/, "\n", nixos)
    for (i = 1; i <= n; i++) {
      if (!placed && rest[i] ~ /^\[[^]]+\]/ && rest[i] != "[options]") {
        printf "%s\n", nixos
        placed = 1
      }
      print rest[i]
    }
  }
' "$conf" >"$reordered"

sudo cp -f "$conf" "$conf.bak"
sudo install -m644 "$reordered" "$conf"
rm -f "$reordered"
