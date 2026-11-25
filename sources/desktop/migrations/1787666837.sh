echo "Enable Dell XPS 13 sidecar speaker amplifiers"

if nixos-hw-dell-xps13-sidecar-amps; then
  source "$NIXOS_PATH/install/hardware/dell-xps13-sidecar-amps.sh"
  nixos-state set reboot-required
fi
