{ lib, stdenvNoCC, src, bash, python3, perl, gnused, imagemagick, nixos-icons }:

# Рабочий стол (upstream 4.5.0: Hyprland + шелл на Quickshell, меню, темы) под NixOS:
#  - сразу после копирования всё дерево переименовано в nixos (scripts/rebrand.py):
#    команды nixos-*, /usr/share/nixos, NIXOS_PATH, «NixOS» в текстах;
#  - shebang'и #!/bin/bash → bash из Nix (на NixOS нет /bin/bash);
#  - /usr/bin/python3 → python3 из Nix;
#  - скрипты чужого пакетного менеджера остаются, но в меню вместо них свои пункты
#    (overrides/menu-nixos.jsonc).
# /usr/share/nixos — ссылка на этот пакет (modules/nixos/desktop.nix).
stdenvNoCC.mkDerivation {
  pname = "nixos-desktop";
  version = "4.5.0";
  inherit src;

  # Поиск Win+B: на главном экране только установленные приложения; спрятанные
  # подменю (Install, Setup, …) не протекают в поиск (24.11, по просьбе).
  patches = [ ../patches/menu-search-apps-only.patch ../patches/qconsole-reserved.patch ];

  buildInputs = [ bash python3 perl ];
  nativeBuildInputs = [ gnused imagemagick ];

  dontConfigure = true;
  dontBuild = true;

  installPhase = ''
    runHook preInstall

    share=$out/share/nixos
    mkdir -p $share $out/bin
    cp -r applications bin config default install migrations shell themes \
      icon.png icon.txt logo.svg logo.txt version $share/
    [ -d etc ] && cp -r etc $share/etc-overrides || true
    chmod -R u+w $share

    # Всё дерево → NixOS (имена файлов, команды, тексты); ссылки на сайты не трогаются,
    # <upstream>-version → nixos-desktop-version (nixos-version уже есть в NixOS).
    python3 ${../scripts/rebrand.py} $out

    # В апстриме файл version отстал (4.0.0.alpha); fastfetch и About читают его.
    echo "4.5.0" > $share/version
    chmod +x $share/bin/*

    # Привилегированные помощники сбрасывают PATH на /usr/bin:/bin — на NixOS
    # там пусто, поэтому добавляем системный профиль.
    grep -rlZ '/usr/bin:/usr/sbin:/bin:/sbin' $share/bin | xargs -0 -r sed -i \
      's|/usr/bin:/usr/sbin:/bin:/sbin|/usr/bin:/usr/sbin:/bin:/sbin:/run/current-system/sw/bin|g'

    # `nixos update`, уведомление «Update System» и индикатор обновлений
    # обновляют flake (nextagg-update).
    cat > $share/bin/nixos-update <<'EOF'
    #!/usr/bin/env bash
    # NixOS: обновление через flake (modules/nixos/desktop.nix → nextagg-update).
    exec nextagg-update "$@"
    EOF
    chmod +x $share/bin/nixos-update

    # Скринсейвер: ttfx здесь — Python-версия (tte), 120 кадров/с на весь экран зря греет CPU.
    substituteInPlace $share/bin/nixos-screensaver --replace-fail '--frame-rate 120' '--frame-rate 60'

    substituteInPlace $share/shell/Commons/InputMethodState.qml \
      --replace-quiet /usr/bin/python3 ${python3}/bin/python3

    for f in $share/bin/*; do
      ln -s "$f" $out/bin/
    done

    # Встроенные темы (catppuccin, tokyo-night, …) не нужны: остаются только
    # свои из ~/.config/nixos/themes (neovoid, drac, purple-moon, …).
    rm -rf $share/themes
    mkdir -p $share/themes
    # и меню выбора тем (двойной клик правой кнопкой по рабочему столу) — убрано
    substituteInPlace $share/shell/plugins/background/Background.qml \
      --replace-fail 'if (mouse.button === Qt.RightButton) root.openThemeSwitcher()' 'if (mouse.button === Qt.RightButton) return'

    # Без имени рабочего стола в интерфейсе (меню, шпаргалка Super+K, панели):
    # «NixOS menu» → «Menu», «Меню NixOS» → «Меню» и т.д. (ru и en).
    find $share/default/i18n/en $share/default/i18n/ru $share/default/hypr -type f \( -name '*.json' -o -name '*.lua' \) -print0 |
      xargs -0 sed -i \
        -e 's/NixOS menu/Menu/g; s/NixOS Menu/Menu/g' \
        -e 's/Pending NixOS Updates/Pending Updates/g; s/Pending NixOS Migrations/Pending Migrations/g' \
        -e 's/Меню NixOS/Меню/g; s/меню NixOS/меню/g' \
        -e 's/Ожидающие обновления NixOS/Ожидающие обновления/g; s/Ожидающие миграции NixOS/Ожидающие миграции/g'

    # Весь конфиг Hyprland — один ~/.config/hypr/hyprland.lua (scripts/bundle-hyprland.py):
    # масштаб монитора из меню и clamshell правят правила hl.monitor прямо в нём.
    sed -i 's|/.config/hypr/monitors.lua|/.config/hypr/hyprland.lua|' \
      $share/bin/nixos-hyprland-monitor-scaling $share/bin/nixos-hyprland-monitor-clamshell

    # ── Ни надписей, ни ASCII-логотипов upstream ──
    # ASCII-логотипы (logo.txt/icon.txt) пустые; картинки-логотипы → снежинка NixOS
    # на холсте того же размера (экран входа SDDM и Plymouth не сдвигаются).
    # глиф-логотип upstream (U+E900 шрифта значков) в кнопке меню → снежинка NixOS (Nerd Font)
    grep -rlZ 'ue900' $share/shell | xargs -0 -r sed -i 's/\\ue900/\\uf313/g'
    : > $share/logo.txt
    : > $share/icon.txt
    icons=${nixos-icons}/share/icons/hicolor
    for f in $share/default/sddm/nixos/logo.png $share/default/plymouth/logo.png; do
      magick -size 800x188 xc:none \( $icons/256x256/apps/nix-snowflake-white.png -resize 188x188 \) \
        -gravity center -composite $f
    done
    magick $icons/256x256/apps/nix-snowflake-white.png -resize 300x300 $share/icon.png
    cp $icons/scalable/apps/nix-snowflake-white.svg $share/logo.svg

    # Сетка приложений дока (Apps, Win+Alt+Space): звёздное небо как в меню Win+B и
    # затемнение остальных мониторов.
    python3 ${../scripts/dock-patches.py} $share/shell/plugins/dock \
      ${../dotfiles/nixos/plugins/nextagg.menu/Starfield.qml}

    runHook postInstall
  '';

  # patchShebangs в fixup проходит весь $out, включая default/ и install/.

  meta = {
    description = "Hyprland + Quickshell desktop (shell, menus, themes) packaged for NixOS";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
  };
}
