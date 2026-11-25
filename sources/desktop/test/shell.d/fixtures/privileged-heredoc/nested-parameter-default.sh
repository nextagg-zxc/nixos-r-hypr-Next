#!/bin/bash

# nixos:heredoc-expands paths=none -- review regression fixture
sudo tee /etc/nixos/review.conf >/dev/null <<EOF
ExecStart=${target:-$HOME/.local/bin/payload}
EOF
