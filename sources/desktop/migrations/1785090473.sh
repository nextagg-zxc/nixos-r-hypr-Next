echo "Repair fingerprint support left without a libfprint"

# An earlier version of this migration swapped libfprint-git for stock
# libfprint in two steps. A run that failed between them left fprintd with
# no library; finish with the driver the fingerprint setup installs now.
if nixos-pkg-present fprintd && nixos-pkg-missing libfprint && nixos-pkg-missing libfprint-git; then
  nixos-pkg-add libfprint-git
fi
