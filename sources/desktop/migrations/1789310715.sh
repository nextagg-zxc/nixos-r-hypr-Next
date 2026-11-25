echo "Install cf (Cloudflare CLI) via mise wrapper"

if [[ ! -f $HOME/.local/state/nixos/preinstalls-removed ]]; then
  nixos-mise-install npm:cf cf
fi
