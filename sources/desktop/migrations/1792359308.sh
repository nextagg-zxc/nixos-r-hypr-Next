echo "Let Chromium use the cameras of Snapdragon laptops through PipeWire"

if nixos-hw-aarch64-qualcomm; then
  source "$NIXOS_PATH/install/hardware/qualcomm/camera.sh"
  nixos-install-camera

  echo "Log out and back in to load the PipeWire camera backend."
fi
