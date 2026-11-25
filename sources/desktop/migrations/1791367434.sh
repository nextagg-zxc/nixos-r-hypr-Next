echo "Configure shared input-method defaults and free desktop shortcuts"

nixos-pkg-add fcitx5-mozc fcitx5-hangul fcitx5-chinese-addons fcitx5-chewing
nixos-input-method configure --defaults
