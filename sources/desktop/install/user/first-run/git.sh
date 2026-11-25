# An upgrade, or a run of nixos-setup-git, can have set the identity already.
if [[ -z $(git config --global user.name) || -z $(git config --global user.email) ]]; then
  nixos-notification-send -u critical -g  "$(nixos-i18n firstRun.gitTitle)" "$(nixos-i18n firstRun.gitBody)" \
    --exec nixos-launch-floating-terminal-with-presentation nixos-setup-git
fi
