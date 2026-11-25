# The catalog entry holds a real newline, not a literal \n: the card renders the
# body as it arrives, and elides past three lines.
nixos-notification-send -u critical -g  "$(nixos-i18n firstRun.keybindingsTitle)" \
  "$(nixos-i18n firstRun.keybindingsBody)" \
  --exec nixos-menu-keybindings
