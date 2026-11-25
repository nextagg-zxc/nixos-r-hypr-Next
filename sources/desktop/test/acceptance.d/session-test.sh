#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

# The compositor reports at least one monitor
monitors=$(hyprctl -j monitors | jq 'length')
(( monitors >= 1 )) || fail "compositor reports a monitor"
pass "compositor reports a monitor"

# The NixOS shell is running and responsive
wait_until "nixos-shell responds to ping" 60 nixos-shell shell ping

# Core shell plugins are loaded
plugins=$(nixos-shell shell listPlugins)
for plugin in \
  nixos.audio nixos.background nixos.bar nixos.bluetooth \
  nixos.clipboard nixos.emojis nixos.menu \
  nixos.monitor nixos.network nixos.notifications nixos.power \
  nixos.reminders nixos.weather; do
  [[ $plugins == *"$plugin"* ]] || fail "shell plugin is loaded: $plugin" "loaded plugins: $plugins"
  pass "shell plugin is loaded: $plugin"
done

# The bar and background are actually on screen
wait_until "bar layer is on screen" 30 layer_on_screen "nixos-bar"
wait_until "background layer is on screen" 30 layer_on_screen "nixos-background"

# Hiding parks the bar off-screen without unmapping its layer surface, and
# revealing brings that same surface back on-screen.
restore_bar_visibility() {
  nixos-toggle-bar off >/dev/null 2>&1 || true
}
trap restore_bar_visibility EXIT

nixos-toggle-bar on
wait_until "hidden bar layer stays mapped" 15 layer_present "nixos-bar"
wait_until "hidden bar layer parks off screen" 15 layer_off_screen "nixos-bar"
screenshot "success-bar-hidden"

nixos-toggle-bar off
wait_until "revealed bar layer returns on screen" 15 layer_on_screen "nixos-bar"
screenshot "success-bar-revealed"
trap - EXIT

# Audio stack is up
wait_until "pipewire is running" 30 wpctl status

# Root filesystem is btrfs as installed
[[ $(findmnt -no FSTYPE /) == "btrfs" ]] || fail "root filesystem is btrfs"
pass "root filesystem is btrfs"

# NixOS reports its version
nixos-desktop-version >/dev/null || fail "nixos-desktop-version works"
pass "nixos-desktop-version works"

# No failed units, system or user. NIXOS_ACCEPTANCE_IGNORE_UNITS can hold a
# regex of units to overlook (useful on dev machines; a fresh VM should be clean).
failed_units() {
  systemctl "$@" --failed --no-legend --plain | awk '{print $1}' |
    grep -Ev "${NIXOS_ACCEPTANCE_IGNORE_UNITS:-^$}" || true
}

failed_system=$(failed_units --system)
if [[ -n $failed_system ]]; then
  fail "no failed system units" "failed units: $failed_system"
fi
pass "no failed system units"

failed_user=$(failed_units --user)
if [[ -n $failed_user ]]; then
  fail "no failed user units" "failed units: $failed_user"
fi
pass "no failed user units"

screenshot "success-desktop"
