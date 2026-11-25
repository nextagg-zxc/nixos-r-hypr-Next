# nixos:heredoc-expands paths=none -- the positional argument is a scalar
sudo tee /etc/nixos/example.conf <<EOF
argument=$1
command=$HOME/.local/share/nixos/bin/example
EOF
