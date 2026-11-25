# Snapdragon cameras run through libcamera, which apps reach through
# PipeWire's libcamera backend.

if nixos-hw-aarch64-qualcomm; then
  nixos-pkg-add pipewire-libcamera
fi
