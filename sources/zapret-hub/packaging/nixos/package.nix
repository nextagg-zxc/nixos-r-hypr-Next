# Пакет Zapret Hub для NixOS.
# bin/zapret-hub — окно (PySide6 из nixpkgs); libexec/zapret-hub-helper — root-помощник (pkexec, служба)
# с ZAPRETHUB_NIXOS=1 и nfqws из nixpkgs; правило polkit указывает ровно на этот помощник.
# pkexec сбрасывает окружение и PATH, поэтому всё нужное помощнику задаёт его обёртка.
{
  lib,
  stdenv,
  python3,
  qt6,
  makeWrapper,
  zapret,
  nftables,
  systemd,
  coreutils,
  gnugrep,
  gnused,
  procps,
  util-linux,
}:
let
  version = lib.removeSuffix "\"" (lib.removePrefix "VERSION = \"" (lib.head (lib.filter (lib.hasPrefix "VERSION")
    (lib.splitString "\n" (builtins.readFile ../../zaprethub/__init__.py)))));
  guiPython = python3.withPackages (p: [ p.pyside6 p.psutil ]);
  helperPath = lib.makeBinPath [ nftables systemd coreutils gnugrep gnused procps util-linux ];
in
stdenv.mkDerivation {
  pname = "zapret-hub";
  inherit version;
  src = lib.fileset.toSource {
    root = ../..;
    fileset = lib.fileset.unions [
      (lib.fileset.fileFilter (f: !(f.hasExt "pyc")) ../../zaprethub)
      ../../packaging/linux
    ];
  };
  nativeBuildInputs = [ makeWrapper qt6.wrapQtAppsHook ];
  buildInputs = [ qt6.qtbase qt6.qtwayland qt6.qtsvg ];
  dontWrapQtApps = true;

  installPhase = ''
    runHook preInstall
    lib=$out/lib/zapret-hub
    mkdir -p $lib $out/bin $out/libexec $out/share/applications \
      $out/share/icons/hicolor/scalable/apps $out/share/polkit-1/actions
    cp -r zaprethub $lib/
    # помощник ищет пакет zaprethub рядом с собой (realpath) — кладём его в $lib
    sed '1s|.*|#!${python3}/bin/python3 -I|' packaging/linux/zapret-hub-helper > $lib/zapret-hub-helper
    chmod 755 $lib/zapret-hub-helper
    install -m644 packaging/linux/zapret-hub.desktop $out/share/applications/zapret-hub.desktop
    install -m644 packaging/linux/zapret-hub.svg $out/share/icons/hicolor/scalable/apps/zapret-hub.svg
    sed 's|/usr/lib/zapret-hub/zapret-hub-helper|'"$out"'/libexec/zapret-hub-helper|' \
      packaging/linux/org.zaprethub.helper.policy > $out/share/polkit-1/actions/org.zaprethub.helper.policy
    grep -q "$out/libexec/zapret-hub-helper" $out/share/polkit-1/actions/org.zaprethub.helper.policy
    runHook postInstall
  '';

  postFixup = ''
    makeWrapper $out/lib/zapret-hub/zapret-hub-helper $out/libexec/zapret-hub-helper \
      --set ZAPRETHUB_NIXOS 1 \
      --set ZAPRETHUB_NFQWS_FALLBACK ${zapret}/bin/nfqws \
      --prefix PATH : ${helperPath}
    makeWrapper ${guiPython}/bin/python3 $out/bin/zapret-hub \
      "''${qtWrapperArgs[@]}" \
      --chdir / \
      --set PYTHONSAFEPATH 1 \
      --set PYTHONPATH $out/lib/zapret-hub \
      --set ZAPRETHUB_NIXOS 1 \
      --set ZAPRETHUB_NFQWS_FALLBACK ${zapret}/bin/nfqws \
      --set ZAPRETHUB_HELPER $out/libexec/zapret-hub-helper \
      --add-flags "-m zaprethub"
  '';

  meta = {
    description = "Zapret Hub — обход блокировок Discord/YouTube (zapret + Flowseal) и прокси для Telegram";
    license = lib.licenses.gpl3Plus;
    mainProgram = "zapret-hub";
    platforms = lib.platforms.linux;
  };
}
