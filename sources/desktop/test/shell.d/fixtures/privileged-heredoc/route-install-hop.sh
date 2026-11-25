tmp=$(mktemp)

cat >"$tmp" <<EOF
#!/bin/bash
exec "$HOME/.local/share/nixos/bin/nixos-agent" "$@"
EOF

sudo install -m 0755 "$tmp" /usr/local/bin/nixos-agent-shim
