# Mesa из любого исходника (входы flake `mesa-git` — main, `mesa-stable` — релиз),
# собранная рецептом nixpkgs.
# Обновить: `nix flake update mesa-git`. Rust-крейты (subprojects/*.wrap)
# читаются из самих исходников, так что wraps.json nixpkgs не мешает.
{ lib, mesa, fetchCrate, runCommand, src, rev ? "git" }:
let
  wrapDir = "${src}/subprojects";
  wraps = lib.filter (lib.hasSuffix ".wrap") (lib.attrNames (builtins.readDir wrapDir));

  field = text: key:
    let m = builtins.match ".*\n${key} *= *([^\n]*)\n.*" ("\n" + text + "\n");
    in if m == null then null else lib.trim (builtins.head m);

  crate = file:
    let
      text = builtins.readFile "${wrapDir}/${file}";
      url = field text "source_url";
      parts = lib.splitString "/" url; # https://static.crates.io/crates/<name>/<ver>/download
    in
    if url == null || !(lib.hasInfix "crates.io" url) then null else {
      pname = lib.elemAt parts 4;
      version = lib.elemAt parts 5;
      filename = field text "source_filename";
      hash = builtins.convertHash {
        hash = field text "source_hash";
        hashAlgo = "sha256";
        toHashFormat = "sri";
      };
    };

  crates = lib.filter (c: c != null) (map crate wraps);

  packageCache = runCommand "mesa-git-rust-package-cache" { } (''
    mkdir -p $out
  '' + lib.concatMapStrings (c: ''
    ln -s ${fetchCrate { inherit (c) pname version hash; unpack = false; }} $out/${c.filename}
  '') crates);

  version = lib.trim (builtins.readFile "${src}/VERSION");
in
mesa.overrideAttrs (old: {
  version = "${version}-${rev}";
  inherit src;
  # nixpkgs сверяет GL-заголовки с mesa-gl-headers своей версии — для main это не нужно.
  postPatch = ''
    patchShebangs .
  '';
  env = old.env // { MESON_PACKAGE_CACHE_DIR = packageCache; };
  # В main опцию amdgpu-virtio заменили массивом amd-options (в 26.2 её ещё нет).
  mesonFlags =
    if lib.hasInfix "'amd-options'" (builtins.readFile "${src}/meson.options") then
      map (f: if f == "-Damdgpu-virtio=true" then "-Damd-options=use-llvm,virtio" else f) old.mesonFlags
    else old.mesonFlags;
})
