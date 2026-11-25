echo "Install basecamp (basecamp-cli) via mise wrapper"

if [[ ! -f $HOME/.local/state/nixos/preinstalls-removed ]]; then
  nixos-mise-install github:basecamp/basecamp-cli basecamp
fi
