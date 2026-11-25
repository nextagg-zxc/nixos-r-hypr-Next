echo "Install the Dell XPS 13 Panther Lake speaker firmware"

if nixos-hw-dell-xps13-dx13260-ptl; then
  source "$NIXOS_PATH/install/hardware/dell-xps13-ptl-speaker-firmware.sh"
  nixos-state set reboot-required
fi
