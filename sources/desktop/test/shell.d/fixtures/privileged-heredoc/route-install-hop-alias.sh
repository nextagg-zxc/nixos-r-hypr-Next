tmp=/tmp/nixos-generated
copy=$tmp
cat >"$tmp" <<EOF
command=$HOME/.local/share/nixos/bin/example
EOF
sudo install -m644 "$copy" /etc/nixos/example.conf
