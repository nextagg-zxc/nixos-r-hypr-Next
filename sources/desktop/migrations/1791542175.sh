echo "Install Gliff, the Hyprland remote desktop over SSH"

# Gliff has no aarch64 build (install/nixos-x86_64-only.packages).
if nixos-hw-x86; then
  nixos-pkg-add gliff
fi
