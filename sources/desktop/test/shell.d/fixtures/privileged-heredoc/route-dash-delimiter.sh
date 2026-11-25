if true; then
  cat <<-EOF | sudo tee /etc/nixos/indented.conf >/dev/null
	helper=$HOME/.local/share/nixos/bin/nixos-agent
	EOF
fi
