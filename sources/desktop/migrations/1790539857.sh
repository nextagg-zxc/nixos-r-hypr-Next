echo "Install Monologue, the webcam recorder"

if [[ ! -f $HOME/.local/state/nixos/preinstalls-removed ]]; then
  nixos-pkg-add monologue
fi
