cat <<'EOF' | sudo tee /etc/udev/rules.d/99-nixos.rules >/dev/null
SUBSYSTEM=="power_supply", RUN+="/usr/bin/nixos-powerprofiles-set $HOME"
EOF

cat <<"XML" | sudo tee /etc/nixos/agent.xml >/dev/null
<config path="$HOME/.local/share/nixos" />
XML
