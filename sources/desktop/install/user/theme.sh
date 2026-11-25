# Setup user theme folder and seed the default only when no theme exists yet.
mkdir -p ~/.config/nixos/themes

if [[ ! -s $HOME/.local/state/nixos/current/theme.name ]]; then
  # iso-chroot and provision-owner both run without a live session to notify.
  if [[ ${NIXOS_SETUP_CONTEXT:-runtime} != "runtime" ]]; then
    NIXOS_THEME_HEADLESS=1 nixos-theme-set "Tokyo Night"
    rm -f ~/.config/chromium/SingletonLock # otherwise archiso owns the Chromium singleton
  else
    nixos-theme-set "Tokyo Night"
  fi
fi
nixos-theme-set-pi --activate
nixos-theme-set-fcitx5 --activate

mkdir -p ~/.config/btop/themes
ln -snf "$HOME/.local/state/nixos/current/theme/btop.theme" ~/.config/btop/themes/current.theme
