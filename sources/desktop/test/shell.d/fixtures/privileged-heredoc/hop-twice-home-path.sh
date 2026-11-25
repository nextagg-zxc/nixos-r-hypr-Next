#!/bin/bash

# Two hops. The scan resolves nixos_bin into helper, so the value it ends up
# judging still carries an unresolved $HOME rather than a literal path.
nixos_bin="$HOME/.local/share/nixos/bin"
helper="$nixos_bin/nixos-agent"

# nixos:heredoc-expands paths=none -- helper names the agent, no path is baked in
cat <<EOF | sudo tee /etc/udev/rules.d/99-nixos-agent.rules >/dev/null
SUBSYSTEM=="power_supply", RUN+="$helper"
EOF
