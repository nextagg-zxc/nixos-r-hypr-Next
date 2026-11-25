# A plain redirect into /etc, no sudo: the command re-execs itself as root.
cat >/etc/nixos/agent.conf <<EOF
helper=$HOME/.local/share/nixos/bin/nixos-agent
EOF
