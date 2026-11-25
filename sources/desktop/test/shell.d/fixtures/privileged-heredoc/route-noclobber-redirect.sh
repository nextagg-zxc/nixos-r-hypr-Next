# `>|` is a plain redirect with noclobber overridden, not a redirect into a pipe.
cat >|/etc/nixos/agent.conf <<EOF
helper=$HOME/.local/share/nixos/bin/nixos-agent
EOF
