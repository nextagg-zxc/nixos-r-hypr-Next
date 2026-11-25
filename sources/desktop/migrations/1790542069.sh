echo "Install Hype, the Markdown presentation app"

if [[ ! -f $HOME/.local/state/nixos/preinstalls-removed ]]; then
  nixos-pkg-add hype
fi
