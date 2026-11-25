tmp=/tmp/nixos-generated
cat >"$tmp" <<EOF
command=$HOME/.local/share/nixos/bin/example
EOF
sudo install -m644 "${tmp}" /etc/nixos/example.conf
