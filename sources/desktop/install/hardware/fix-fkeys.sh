# Ensure that F-keys on Apple-like keyboards (such as Lofree Flow84) are always F-keys.
# Apple Silicon is left alone: the nixos-mac package owns its keyboard mode.
conf="${NIXOS_HID_APPLE_CONF:-/etc/modprobe.d/hid_apple.conf}"
if [[ ! -f $conf ]] && ! nixos-hw-aarch64-apple; then
  sudo mkdir -p "$(dirname "$conf")"
  echo "options hid_apple fnmode=2" | sudo tee "$conf" >/dev/null
fi
