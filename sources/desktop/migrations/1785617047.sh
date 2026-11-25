echo "Install oh-my-pi (omp) via mise wrapper"

if [[ ! -f $HOME/.local/state/nixos/preinstalls-removed ]]; then
  nixos-mise-install github:can1357/oh-my-pi omp
fi
