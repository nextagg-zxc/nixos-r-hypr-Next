DROP_IN=/etc/systemd/system/nixos-agent.service.d/override.conf

cat <<EOF | sudo tee "$DROP_IN" >/dev/null
[Service]
ExecStart=$NIXOS_PATH/bin/nixos-agent
EOF
