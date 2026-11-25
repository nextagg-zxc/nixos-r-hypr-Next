sudo dd status=none of=/etc/nixos/boot.conf <<EOF
cmdline=$boot_params
EOF
