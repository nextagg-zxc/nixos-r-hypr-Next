echo "Install ori (OpenRouter's agent harness) via mise wrapper"

if [[ ! -f $HOME/.local/state/nixos/preinstalls-removed ]]; then
  nixos-mise-install github:OpenRouterLabs/ori-releases ori
fi
