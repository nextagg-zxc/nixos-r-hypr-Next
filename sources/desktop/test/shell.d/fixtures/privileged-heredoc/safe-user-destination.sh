mkdir -p ~/.config/nixos

cat >~/.config/nixos/agent.conf <<EOF
helper=$HOME/.local/share/nixos/bin/nixos-agent
EOF

cat >"$HOME/.local/bin/nixos-shim" <<EOF
exec "$NIXOS_PATH/bin/nixos-agent" "$@"
EOF
