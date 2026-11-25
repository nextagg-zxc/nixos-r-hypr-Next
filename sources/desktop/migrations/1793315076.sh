echo "Load NixOS's shell setup on Apple Silicon"

# nixos-settings skipped every etc-override on Apple Silicon, including the
# /etc/skel/.bashrc that sources default/bash/rc, so Mac accounts were created
# with Arch's stock ~/.bashrc and none of NixOS's aliases, functions or env.
if ! nixos-hw-aarch64-apple; then
  exit 0
fi

bashrc="$HOME/.bashrc"

# A bashrc that already loads NixOS's, or one kept in a dotfiles repo, is the
# user's own to keep.
if [[ -L $bashrc ]] || { [[ -f $bashrc ]] && grep -q 'default/bash/rc' "$bashrc"; }; then
  exit 0
fi

# Back up under a name nothing else holds, so an earlier ~/.bashrc.bak survives.
if [[ -f $bashrc ]]; then
  backup=$(mktemp "$bashrc.bak.XXXXXX")
  cp -a "$bashrc" "$backup"
  echo "Your previous ~/.bashrc is saved as ~${backup#"$HOME"}"
fi

cp -f "$NIXOS_PATH/default/bashrc" "$bashrc"
