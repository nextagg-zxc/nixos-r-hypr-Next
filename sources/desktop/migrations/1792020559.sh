echo "Theme the Fcitx candidate window with the current NixOS theme"

# Activation selects the theme; the refresh then renders it, since the current
# theme was staged before its template existed.
nixos-theme-set-fcitx5 --activate
nixos-theme-refresh
