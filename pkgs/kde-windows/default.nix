# KDE «как Windows» для раздаваемой системы: две свои глобальные темы Plasma (org.nixos.windows11/10,
# раскладка панели — layout.js), оформление из Fluent-kde и We10XOS-kde (тема Plasma, рамки окон,
# цвета, Kvantum, обои Fluent), иконки We10X (Win10) и Win11 (Win11), курсоры Fluent и скрипт nixos-kde-look.
# Все темы — GPL-3.0; логотипов и обоев Microsoft нет (start-here в наборах значков заменён снежинкой NixOS).
{
  lib,
  stdenvNoCC,
  fetchFromGitHub,
  makeWrapper,
  gtk3,
  kdePackages,
  xdg-user-dirs,
  coreutils,
  gnused,
  nixos-icons,
}:
let
  fluent-kde = fetchFromGitHub {
    owner = "vinceliuice";
    repo = "Fluent-kde";
    rev = "44794f29c89de994b0179aebabd2f5776c90d236";
    hash = "sha256-Ejr2wDs3tr36YN2mWSd9ZKp5e6gH/whcuhauN/2Y15I=";
  };
  we10xos-kde = fetchFromGitHub {
    owner = "yeyushengfan258";
    repo = "We10XOS-kde";
    rev = "270f0d7d3c1f0d5540109e6116d2fa891664f24b";
    hash = "sha256-EXhFazRo76BVcAEigsB5GIMOsNe27ztBDUcHv8JWXS0=";
  };
  we10x-icons = fetchFromGitHub {
    owner = "yeyushengfan258";
    repo = "We10X-icon-theme";
    rev = "0f52ff2dce554146f8f76ab2c7a5968fd773400d";
    hash = "sha256-EPhq5WCFdF76lQMGC4GhwSh9Gu9uyL8KwvLYxP8FUxs=";
  };
  # значки Windows 11 (жёлтые папки, корзина, «Этот компьютер») — для вида Win11
  win11-icons = fetchFromGitHub {
    owner = "yeyushengfan258";
    repo = "Win11-icon-theme";
    rev = "a5b460a407da143b32f19a503d7fcebb3edf2371";
    hash = "sha256-+GtOkOVSWlNTdKSs0R86LhnpbBZ21Y0ML3V8pwDUUSc=";
  };
  fluent-icons = fetchFromGitHub {
    owner = "vinceliuice";
    repo = "Fluent-icon-theme";
    rev = "c8a244f571ef8fb47812bdc9dbce76546cedce69";
    hash = "sha256-rodsZX3SK1CUVlpaXNv4uPDSZkFYgce4OUVAjxULt4E=";
  };
in
stdenvNoCC.mkDerivation {
  pname = "kde-windows";
  version = "1.0";
  src = ./.;
  nativeBuildInputs = [ makeWrapper gtk3 ];
  dontBuild = true;

  installPhase = ''
    runHook preInstall
    s=$out/share
    mkdir -p $s/plasma/look-and-feel $s/plasma/desktoptheme $s/aurorae/themes \
      $s/color-schemes $s/Kvantum $s/wallpapers $s/icons $out/bin

    # оформление Windows 11 (Fluent) и Windows 10 (We10XOS)
    cp -r ${fluent-kde}/plasma/desktoptheme/Fluent-round ${we10xos-kde}/plasma/desktoptheme/We10XOS-dark $s/plasma/desktoptheme/
    cp -r ${fluent-kde}/aurorae/Fluent-round-dark ${we10xos-kde}/aurorae/We10XOS-dark-Sharp $s/aurorae/themes/
    cp ${fluent-kde}/color-schemes/FluentDark.colors ${we10xos-kde}/color-schemes/We10XOSDark.colors $s/color-schemes/
    cp -r ${fluent-kde}/Kvantum/Fluent-round ${we10xos-kde}/Kvantum/We10XOS-dark $s/Kvantum/
    # обои без логотипов: Win11 — тёмно-синий Fluent-round-dark, Win10 — голубой Fluent
    cp -r ${fluent-kde}/wallpaper/Fluent ${fluent-kde}/wallpaper/Fluent-round-dark $s/wallpapers/
    chmod -R u+w $s

    # иконки We10X (тёмные панели) и курсоры Fluent
    cp -r ${we10x-icons} we10x && chmod -R u+w we10x
    (cd we10x && patchShebangs install.sh && bash install.sh -d $s/icons -n We10X -t default >/dev/null)
    cp -r ${win11-icons} win11 && chmod -R u+w win11
    (cd win11 && patchShebangs install.sh && bash install.sh -d $s/icons -n Win11 -t default >/dev/null)
    # варианты цветных папок ссылаются на файлы, которых в «default» нет
    # значки сторонних программ (Discord, Spotify, Steam…) — их собственные, современные: старые копии из наборов
    # убираются (монохромные -symbolic для трея остаются)
    for t in Win11 Win11-dark We10X We10X-dark; do
      [ -d $s/icons/$t/apps ] || continue
      find $s/icons/$t/apps -not -path '*/symbolic/*' -not -iname '*-symbolic*' -regextype egrep -iregex \
        '.*/(discord|spotify|steam|firefox|telegram|org\.telegram|obs|com\.obsproject|vlc|libreoffice|heroic|com\.heroicgameslauncher|org\.prismlauncher|prismlauncher|chromium|google-chrome|soundcloud|rustdesk|lutris|thunderbird|gimp)[^/]*' \
        -delete
    done
    # «Пуск» и прочие start-here — снежинка NixOS, а не логотип Windows из наборов значков
    find $s/icons -iname 'start-here*.svg' -exec cp -f --remove-destination \
      ${nixos-icons}/share/icons/hicolor/scalable/apps/nix-snowflake.svg {} \;
    find $s/icons -xtype l -delete
    cp -r ${fluent-icons}/cursors/dist $s/icons/Fluent-cursors
    chmod -R u+w $s/icons
    for t in $s/icons/*/; do [ -f "$t/index.theme" ] && gtk-update-icon-cache -q -f "$t" || true; done

    # свои глобальные темы: общая часть раскладки + раскладка темы, обои по путям в $out
    for v in 11 10; do
      d=$s/plasma/look-and-feel/org.nixos.windows$v
      cp -r lnf/windows$v $d
      chmod -R u+w $d
      js=$d/contents/layouts/org.kde.plasma.desktop-layout.js
      cat lnf/common-layout.js $js.in > $js
      rm $js.in
    done
    wp11=$(ls -d $s/wallpapers/Fluent-round-dark/contents/images/* | sort -V | tail -1)
    wp10=$(ls -d $s/wallpapers/Fluent/contents/images/* | sort -V | tail -1)
    sed -i "s|@wallpaper11@|$wp11|" $s/plasma/look-and-feel/org.nixos.windows11/contents/layouts/*.js
    sed -i "s|@wallpaper10@|$wp10|" $s/plasma/look-and-feel/org.nixos.windows10/contents/layouts/*.js

    install -m755 nixos-kde-look.sh $out/bin/nixos-kde-look
    substituteInPlace $out/bin/nixos-kde-look --replace-fail '@out@' "$out"
    # папки «Рабочий стол»… на языке системы: xdg-user-dirs нужны свои настройки и база локалей NixOS
    wrapProgram $out/bin/nixos-kde-look --prefix PATH : ${lib.makeBinPath [
      kdePackages.kconfig kdePackages.plasma-workspace xdg-user-dirs coreutils gnused
    ]} \
      --suffix XDG_CONFIG_DIRS : ${xdg-user-dirs}/etc/xdg \
      --set-default LOCALE_ARCHIVE /run/current-system/sw/lib/locale/locale-archive
    runHook postInstall
  '';

  meta = {
    description = "KDE Plasma как Windows 11/10: глобальные темы, оформление, иконки, nixos-kde-look";
    license = lib.licenses.gpl3Plus;
    platforms = lib.platforms.linux;
  };
}
