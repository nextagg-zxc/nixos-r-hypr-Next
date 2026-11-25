echo "Install Gliff on aarch64, now that NixOS's repositories build it there"

if nixos-hw-aarch64; then
  nixos-pkg-add gliff
fi
