# Программа «Автозапуск» (GTK4 + libadwaita, Python) и обёртка autostart-run.
# bin/autostart — окно; bin/autostart-run — задержка/скрытый запуск в записях XDG autostart;
# bin/autostart-python — python с модулем autostart (посев записей home-manager, тесты).
{
  lib,
  stdenv,
  python3,
  gtk4,
  libadwaita,
  gobject-introspection,
  wrapGAppsHook4,
  makeWrapper,
  jq,
  coreutils,
  kdotool,
  papirus-icon-theme,
}:
let
  py = python3.withPackages (p: [ p.pygobject3 ]);
in
stdenv.mkDerivation {
  pname = "autostart";
  version = "1.0";
  src = lib.fileset.toSource {
    root = ./.;
    fileset = lib.fileset.unions [ ./autostart ./autostart-run ];
  };
  nativeBuildInputs = [ wrapGAppsHook4 gobject-introspection makeWrapper ];
  buildInputs = [ gtk4 libadwaita ];
  dontWrapGApps = true;
  installPhase = ''
    runHook preInstall
    mkdir -p $out/lib/autostart $out/bin $out/share/applications $out/share/icons/hicolor/scalable/apps
    cp -r autostart $out/lib/autostart/
    rm -rf $out/lib/autostart/autostart/__pycache__
    install -m755 autostart-run $out/bin/autostart-run
    cp ${papirus-icon-theme}/share/icons/Papirus/64x64/apps/session-properties.svg \
      $out/share/icons/hicolor/scalable/apps/org.nixos.Autostart.svg
    cat >$out/share/applications/org.nixos.Autostart.desktop <<'DESKTOP'
    [Desktop Entry]
    Type=Application
    Name=Автозапуск
    Comment=Что запускается при входе в систему
    Exec=autostart
    Icon=org.nixos.Autostart
    Categories=Settings;System;
    Keywords=autostart;startup;автозапуск;запуск;
    Terminal=false
    DESKTOP
    sed -i 's/^    //' $out/share/applications/org.nixos.Autostart.desktop
    runHook postInstall
  '';
  postFixup = ''
    makeWrapper ${py}/bin/python3 $out/bin/autostart "''${gappsWrapperArgs[@]}" \
      --prefix PYTHONPATH : $out/lib/autostart --add-flags "-m autostart"
    makeWrapper ${py}/bin/python3 $out/bin/autostart-python --prefix PYTHONPATH : $out/lib/autostart
    # hyprctl — из PATH сессии (версия совпадает с запущенным Hyprland)
    wrapProgram $out/bin/autostart-run --prefix PATH : ${lib.makeBinPath [ jq coreutils kdotool ]}
  '';
  meta = {
    description = "Автозапуск: что стартует при входе (XDG autostart), задержка и скрытый запуск";
    mainProgram = "autostart";
  };
}
