# omacalc — калькулятор рабочего стола (Super+Shift+Q), версия 0.3.1 из upstream 4.5;
# собирается из исходников (Qt 6, qmake).
{ lib, stdenv, fetchFromGitHub, qt6 }:
stdenv.mkDerivation rec {
  pname = "omacalc";
  version = "0.3.1";
  src = fetchFromGitHub {
    owner = "omacom-io";
    repo = "omacalc";
    rev = "v${version}";
    hash = "sha256-Q1LGLTmMz8jqPGptyp8oZKr3iCM2YTR0f/NbmPY8AFQ=";
  };
  nativeBuildInputs = [ qt6.qmake qt6.wrapQtAppsHook ];
  buildInputs = [ qt6.qtbase qt6.qtdeclarative ];
  installPhase = ''
    runHook preInstall
    install -Dm755 omacalc $out/bin/omacalc
    install -Dm644 pkgbuild/omacalc.desktop $out/share/applications/omacalc.desktop
    # убран из списка приложений по просьбе; Super+Shift+Q запускает его напрямую
    echo "NoDisplay=true" >> $out/share/applications/omacalc.desktop
    install -Dm644 pkgbuild/omacalc.svg $out/share/icons/hicolor/scalable/apps/omacalc.svg
    runHook postInstall
  '';
  meta.mainProgram = "omacalc";
}
