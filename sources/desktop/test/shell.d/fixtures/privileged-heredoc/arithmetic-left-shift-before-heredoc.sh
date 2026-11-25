mask=$((1 << bits))

cat >/etc/nixos/agent.conf <<EOF
helper=$HOME/.local/share/nixos/bin/nixos-agent
EOF
