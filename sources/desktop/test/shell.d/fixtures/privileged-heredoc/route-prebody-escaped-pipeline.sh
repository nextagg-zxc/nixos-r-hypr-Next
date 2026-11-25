#!/bin/bash

cat <<EOF | \
  sudo tee /etc/nixos/review.conf
ExecStart=$HOME/.local/bin/payload
EOF
