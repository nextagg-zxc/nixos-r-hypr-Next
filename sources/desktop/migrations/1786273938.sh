echo "Install herdr from the NixOS package repo and seed its config"

# The package was briefly published as nixos-herdr; herdr replaces it
nixos-pkg-drop nixos-herdr
nixos-pkg-add herdr

# An earlier revision of this migration installed herdr through mise. Drop that
# install so a stale client can't shadow the packaged /usr/bin/herdr with an
# older wire protocol.
rm -f "$HOME/.local/bin/herdr"
if mise ls herdr 2>/dev/null | grep -q herdr; then
  mise unuse -g herdr &>/dev/null || true
  mise uninstall -a herdr &>/dev/null || true
fi
rm -rf "$HOME/.local/share/mise/installs/herdr" "$HOME/.local/share/mise/shims/herdr"

# Only seed. A user who already has a herdr config keeps it; nixos-refresh-herdr
# is the explicit way to take the shipped defaults.
[[ -f "$HOME/.config/herdr/config.toml" ]] || nixos-refresh-config herdr/config.toml
