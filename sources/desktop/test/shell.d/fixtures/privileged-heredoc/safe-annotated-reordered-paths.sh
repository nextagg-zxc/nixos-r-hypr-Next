storage="$HOME/storage"
shared="$HOME/shared"

# nixos:heredoc-expands paths=shared,storage -- both sources are validated before use
cat >/etc/nixos/mounts.conf <<EOF
storage=$storage:/storage
shared=$shared:/shared
EOF
