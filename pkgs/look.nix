{ lib, runCommand, python3, rsync, self, extras, nixos-desktop, wallpapers, profile ? "personal" }:

# «Вид» целиком, разложенный как в домашней папке:
#   home/.config/nixos/…    (бар, меню, плагины, темы, брендинг, обои)
#   home/.config/hypr/…     (Hyprland — один hyprland.lua)
#   home/.config/{ghostty,btop,…}
#   share/icons/material-design-dark (курсоры)
# Плюс theme.name/background — какую тему и обои включить при первом входе.
runCommand (if profile == "share" then "nixos-look-share" else "nixos-look") { nativeBuildInputs = [ python3 rsync ]; } (''
  d=${../dotfiles}
  h=$out/share/nixos-look/home
  mkdir -p $h/.config $out/share/icons

  rsync -a --chmod=u+w $d/nixos $d/hypr $h/.config/
  for x in ghostty alacritty kitty foot btop fastfetch fcitx5 starship.toml xdg-terminals.list mimeapps.list; do
    [ -e $d/$x ] && rsync -a --chmod=u+w $d/$x $h/.config/
  done
  # Состояние рабочего стола, которое задаёт вид: закругления/прозрачность/blur
  # (appearance.lua), флаги hypr, настройки плагинов, редактор по умолчанию.
  [ -d $d/nixos-state ] && mkdir -p $h/.local/state/nixos && \
    rsync -a --chmod=u+w $d/nixos-state/ $h/.local/state/nixos/

  # Обои: вместо прежних (wallpaperbetter, аниме) и встроенных в тему NeoVoid —
  # набор NixOS (pkgs/wallpapers.nix) в папке обоев темы neovoid.
  rm -rf $h/.config/nixos/backgrounds/neovoid
  mkdir -p $h/.config/nixos/backgrounds/neovoid
  cp ${wallpapers}/* $h/.config/nixos/backgrounds/neovoid/

  # About рисует ASCII-снежинку fastfetch (about.txt пустой). Заставка (скринсейвер) — та же
  # снежинка NixOS из dotfiles/nixos/branding/screensaver.txt с эффектами ttfx (24.11).
  mkdir -p $h/.config/nixos/branding
  : > $h/.config/nixos/branding/about.txt

  # Курсоры — отдельно в share/icons (их ставит home.pointerCursor).
  [ -d $d/icons ] && rsync -a --chmod=u+w $d/icons/ $out/share/icons/

  rsync -a --chmod=u+w ${extras}/share/desktop-extras/plugins/ $h/.config/nixos/plugins/
  mkdir -p $h/.config/nixos/themes
  rsync -a --chmod=u+w ${extras}/share/desktop-extras/themes/ $h/.config/nixos/themes/
  # встроенные обои темы NeoVoid (одна — с надписью upstream) — убраны
  rm -f $h/.config/nixos/themes/neovoid/backgrounds/*

  # ~/.bashrc: свой из dotfiles, иначе стандартный от рабочего стола. Строки
  # `. файл` (cargo, swiftly, uv) срабатывают, только если файл есть.
  if [ -f $d/bash/bashrc ]; then
    sed -E 's|^\. (.+)$|[ -r \1 ] \&\& . \1|' $d/bash/bashrc > $h/.bashrc
  else
    cp ${nixos-desktop}/share/nixos/etc-overrides/dot.bashrc $h/.bashrc
  fi
  chmod u+w $h/.bashrc
  python3 ${./portable-paths.py} bash $h/.bashrc
  # cfg — открыть конфиг системы, rebuild — пересобрать и применить.
  cat >> $h/.bashrc <<'EOF'

if command -v nextagg-rebuild >/dev/null; then
  alias cfg='nextagg-config' rebuild='nextagg-rebuild'
fi
EOF
  [ -f $h/.config/ghostty/config ] && python3 ${./portable-paths.py} ghostty $h/.config/ghostty/config

  # Меню: твой nixos-menu.jsonc + пункты для NixOS (Packages, Update, откат).
  python3 ${./merge-menu.py} \
    $h/.config/nixos/extensions/nixos-menu.jsonc \
    ${../overrides/menu-nixos.jsonc}

  # Состояние темы раскладывается отдельно (это не конфиг, а выбор).
  mv $h/.config/nixos/theme.name $out/share/nixos-look/theme.name 2>/dev/null || echo neovoid > $out/share/nixos-look/theme.name
  mv $h/.config/nixos/background $out/share/nixos-look/background 2>/dev/null || true

  find $h -name '*.sh' -exec chmod +x {} +
  chmod +x $h/.config/hypr/scripts/* 2>/dev/null || true

  # Плагины и темы из внешних репозиториев — тоже в nixos (команды nixos-*, пути
  # ~/.config/nixos, ~/.local/state/nixos), как весь рабочий стол (pkgs/nixos-desktop.nix).
  python3 ${../scripts/rebrand.py} $out
  # и без ссылок с именем upstream в документации/комментариях (рабочий код не трогается)
  python3 ${../scripts/strip-upstream-links.py} $h/.config/nixos/plugins
  python3 ${../scripts/strip-upstream-links.py} $h/.config/nixos/themes
'' + lib.optionalString (profile == "share") ''
  # вид для друзей: без личного (плагины, меню, модули Hyprland, .bashrc)
  python3 ${../scripts/share-profile.py} $h
'')
