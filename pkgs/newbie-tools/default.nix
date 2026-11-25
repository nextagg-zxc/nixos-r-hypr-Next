# Малые программы раздаваемой системы: запуск .exe/.msi/AppImage двойным кликом, шпаргалка клавиш (KDE),
# «Сообщить о проблеме», «Позвать на помощь» (RustDesk со своим сервером пользователя на Oracle).
{
  lib,
  stdenvNoCC,
  python3,
  gtk4,
  libadwaita,
  gobject-introspection,
  wrapGAppsHook4,
  makeWrapper,
  papirus-icon-theme,
  rustdeskHost ? "",
  rustdeskKey ? "",
}:
let
  py = python3.withPackages (p: [ p.pygobject3 ]);
  desktop = id: name: comment: exec: icon: extra: ''
    cp ${papirus-icon-theme}/share/icons/Papirus/64x64/apps/${icon}.svg $out/share/icons/hicolor/scalable/apps/${id}.svg
    cat >$out/share/applications/${id}.desktop <<DESKTOP
    [Desktop Entry]
    Type=Application
    Name=${name}
    Comment=${comment}
    Exec=${exec}
    Icon=${id}
    Terminal=false
    ${extra}
    DESKTOP
    sed -i 's/^    //' $out/share/applications/${id}.desktop
  '';
in
stdenvNoCC.mkDerivation {
  pname = "newbie-tools";
  version = "1.0";
  src = lib.fileset.toSource { root = ./.; fileset = ./newbie; };
  nativeBuildInputs = [ wrapGAppsHook4 gobject-introspection makeWrapper ];
  buildInputs = [ gtk4 libadwaita ];
  dontWrapGApps = true;
  installPhase = ''
    runHook preInstall
    mkdir -p $out/lib/newbie $out/bin $out/share/applications $out/share/icons/hicolor/scalable/apps
    cp -r newbie $out/lib/newbie/
    rm -rf $out/lib/newbie/newbie/__pycache__
    substituteInPlace $out/lib/newbie/newbie/apps.py \
      --replace-fail '@rustdesk_host@' '${rustdeskHost}' --replace-fail '@rustdesk_key@' '${rustdeskKey}'
    ${desktop "org.nixos.RunExe" "Запуск программы Windows" "Запуск .exe и AppImage" "nixos-tool exe %f" "wine"
      "NoDisplay=true\n    MimeType=application/x-ms-dos-executable;application/x-msdownload;application/x-msi;application/vnd.microsoft.portable-executable;application/x-ms-shortcut;application/vnd.appimage;application/x-iso9660-appimage;"}
    ${desktop "org.nixos.Keys" "Горячие клавиши" "Шпаргалка клавиш" "nixos-tool keys" "preferences-desktop-keyboard-shortcuts" "Categories=Utility;\n    OnlyShowIn=KDE;"}
    ${desktop "org.nixos.Report" "Сообщить о проблеме" "Собрать журналы в один файл для помощника" "nixos-tool report" "bug-buddy" "Categories=System;Utility;"}
    ${desktop "org.nixos.Help" "Позвать на помощь" "Удалённая помощь: друг подключится к экрану (RustDesk)" "nixos-tool help" "rustdesk" "Categories=Network;RemoteAccess;"}
    runHook postInstall
  '';
  postFixup = ''
    makeWrapper ${py}/bin/python3 $out/bin/nixos-tool "''${gappsWrapperArgs[@]}" \
      --prefix PYTHONPATH : $out/lib/newbie --add-flags "-m newbie"
  '';
  meta = { description = "Малые программы раздаваемой системы"; mainProgram = "nixos-tool"; };
}
