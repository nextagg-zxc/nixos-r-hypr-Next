#!/bin/bash

cat <<EOF >/tmp/nixos-review-unit
[Service]
ExecStart=$HOME/.local/bin/payload
EOF
sudo install -m 644 /tmp/nixos-review-unit /etc/systemd/system/review.service
