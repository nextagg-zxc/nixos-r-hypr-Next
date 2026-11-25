# Set default XCompose that is triggered with Shift + CapsLock
tee ~/.XCompose >/dev/null <<EOF
# Run nixos-restart-xcompose to apply changes

# Include fast emoji access
include "/usr/share/nixos/default/xcompose"

# Identification
<Multi_key> <space> <n> : "$NIXOS_USER_NAME"
<Multi_key> <space> <e> : "$NIXOS_USER_EMAIL"
EOF
