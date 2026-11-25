echo "Replace GNOME Calculator with Omacalc"

nixos-pkg-add omacalc
nixos-pkg-drop gnome-calculator
