echo "Install Signed, the PDF signing app"

if [[ ! -f $HOME/.local/state/nixos/preinstalls-removed ]]; then
  nixos-pkg-add signed
fi
