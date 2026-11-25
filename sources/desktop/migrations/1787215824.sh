echo "Install hey (hey-cli) via mise wrapper"

if [[ ! -f $HOME/.local/state/nixos/preinstalls-removed ]]; then
  nixos-mise-install github:basecamp/hey-cli hey
fi
