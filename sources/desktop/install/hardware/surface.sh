# The Marvell Wi-Fi firmware is for x86 Surfaces only; Snapdragon Surfaces use Qualcomm Wi-Fi.
if nixos-hw-surface && nixos-hw-x86; then
  nixos-pkg-add linux-firmware-marvell
fi
