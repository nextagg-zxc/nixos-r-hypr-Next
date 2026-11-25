echo "Apply the NVIDIA video driver fix on hybrid laptops"

if nixos-hw-nvidia && ! nixos-hw-nvidia-display; then
  # Hyprland applies env at startup. Reloading the updated defaults cannot
  # clear the old overrides inherited by the compositor and its applications.
  nixos-state set reboot-required
  echo "Reboot to stop forcing NVIDIA VA-API/GLX drivers on the integrated GPU."
fi
