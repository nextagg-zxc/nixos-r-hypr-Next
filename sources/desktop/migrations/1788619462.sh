echo "Hand Hermes Desktop the NixOS theme as a skin"

# Only the app NixOS installed under Install > AI follows the theme by itself.
# A Hermes the user set up some other way keeps whatever skin they chose.
nixos-pkg-present hermes-desktop || exit 0

# The same hand-over a fresh install does. A Hermes that is not ready or refuses
# the write is reported and done with there; only NixOS's own failures return.
nixos-theme-set-hermes --activate
