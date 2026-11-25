echo "Install Kimi coding agent mise wrapper"

if [[ ! -f $HOME/.local/state/nixos/preinstalls-removed ]] && nixos-cmd-missing kimi; then
  nixos-mise-install npm:@moonshot-ai/kimi-code kimi
fi
