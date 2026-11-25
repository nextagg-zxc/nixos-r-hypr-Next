# «Магазин» раздаваемой системы: поиск и установка из nixpkgs (через root-помощник «Настройки системы»:
# packages.json + пересборка) и Flathub (flatpak --user). nixos-store-hint — подсказка для bash.
{
  lib,
  stdenvNoCC,
  python3,
  gtk4,
  libadwaita,
  gobject-introspection,
  wrapGAppsHook4,
  makeWrapper,
  xdg-user-dirs,
  papirus-icon-theme,
  system-settings,
}:
let
  py = python3.withPackages (p: [ p.pygobject3 ]);
in
stdenvNoCC.mkDerivation {
  pname = "store";
  version = "1.0";
  src = lib.fileset.toSource { root = ./.; fileset = ./store; };
  nativeBuildInputs = [ wrapGAppsHook4 gobject-introspection makeWrapper ];
  buildInputs = [ gtk4 libadwaita ];
  dontWrapGApps = true;
  installPhase = ''
    runHook preInstall
    mkdir -p $out/lib/store $out/bin $out/share/applications $out/share/icons/hicolor/scalable/apps
    cp -r store $out/lib/store/
    rm -rf $out/lib/store/store/__pycache__
    substituteInPlace $out/lib/store/store/ui.py --replace-fail '@helper@' "${system-settings}/libexec/nixos-share-apply"
    cp ${papirus-icon-theme}/share/icons/Papirus/64x64/apps/system-software-install.svg \
      $out/share/icons/hicolor/scalable/apps/org.nixos.Store.svg
    cat >$out/share/applications/org.nixos.Store.desktop <<'DESKTOP'
    [Desktop Entry]
    Type=Application
    Name=Магазин
    Comment=Поиск и установка программ (NixOS и Flathub)
    Exec=nixos-store
    Icon=org.nixos.Store
    Categories=System;PackageManager;
    Keywords=store;install;apps;магазин;установить;программы;
    Terminal=false
    DESKTOP
    sed -i 's/^    //' $out/share/applications/org.nixos.Store.desktop
    runHook postInstall
  '';
  postFixup = ''
    makeWrapper ${py}/bin/python3 $out/bin/nixos-store "''${gappsWrapperArgs[@]}" \
      --prefix PYTHONPATH : $out/lib/store --prefix PATH : ${lib.makeBinPath [ xdg-user-dirs ]} \
      --add-flags "-m store"
    makeWrapper ${python3}/bin/python3 $out/bin/nixos-store-hint \
      --prefix PYTHONPATH : $out/lib/store --add-flags "-m store hint"
  '';
  meta = { description = "Магазин программ раздаваемой системы"; mainProgram = "nixos-store"; };
}
