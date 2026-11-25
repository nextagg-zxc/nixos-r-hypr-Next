# mise: официальная статическая сборка, свежее nixpkgs.
# Им пользуются твои обёртки ~/.local/share/mise/command-wrappers (claude, codex, grok)
# и shims через /usr/bin/mise. Обновляет update.sh при nextagg-update.
{ lib, stdenvNoCC, fetchurl }:
let release = lib.importJSON ./release.json; in
stdenvNoCC.mkDerivation {
  pname = "mise-bin";
  inherit (release) version;
  src = fetchurl { inherit (release) url hash; };
  installPhase = "install -Dm755 bin/mise $out/bin/mise";
  meta.mainProgram = "mise";
}
