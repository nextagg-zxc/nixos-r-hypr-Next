# Millennium (плагины и темы клиента Steam, https://steambrew.app) — готовая
# сборка из релизов GitHub (release.json, обновляет update.sh при nextagg-update).
# Клиент Steam грузит её через симлинки ubuntu12_{32,64}/libXtst.so.6 →
# /usr/lib/millennium/…, поэтому библиотеки лежат в lib/millennium и попадают в
# /usr/lib/millennium внутри FHS-окружения Steam (programs.steam.package).
{ lib, stdenvNoCC, fetchurl, perl }:
let
  release = lib.importJSON ./release.json;
in
stdenvNoCC.mkDerivation {
  pname = "millennium";
  inherit (release) version;
  src = fetchurl { inherit (release) url hash; };
  sourceRoot = ".";
  nativeBuildInputs = [ perl ];
  dontBuild = true;
  dontFixup = true; # грузятся внутри FHS Steam, где /usr/lib — обычный
  # Millennium ищет свои библиотеки по /usr/lib/millennium, а внутри контейнера
  # SteamRT3 — по /run/host/usr/lib/millennium. В FHS-окружении Steam на NixOS
  # /usr/lib — абсолютная ссылка на /usr/lib64, и в контейнере она уводит в
  # рантайм, где Millennium нет. Поэтому путь в бинарниках заменён на настоящий
  # каталог той же длины: /usr/lib64/mlnm/lib (lib/mlnm/lib в пакете).
  installPhase = ''
    for f in usr/lib/millennium/*; do
      perl -0777 -pi -e 's|/usr/lib/millennium|/usr/lib64/mlnm/lib|g' "$f"
    done
    install -Dm755 usr/lib/millennium/* -t $out/lib/millennium
    install -Dm755 usr/lib/millennium/* -t $out/lib/mlnm/lib
  '';
}
