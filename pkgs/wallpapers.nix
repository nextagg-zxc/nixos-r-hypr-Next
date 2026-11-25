# Набор обоев NixOS (nixos-artwork, CC-BY-SA) — тёмные, под тему neovoid.
{ runCommand, nixos-artwork }:
let
  names = [
    "binary-black" "binary-blue" "catppuccin-mocha" "catppuccin-macchiato" "dracula"
    "moonscape" "mosaic-blue" "nineish-dark-gray" "nineish-catppuccin-mocha"
    "nineish-solarized-dark" "simple-blue" "simple-dark-gray" "stripes-logo"
    "waterfall" "watersplash" "recursive" "gnome-dark"
  ];
  copy = n: let w = nixos-artwork.wallpapers.${n}; in
    ''f=${w.gnomeFilePath}; cp "$f" "$out/nixos-${n}.''${f##*.}"'';
in
runCommand "nextagg-wallpapers" { } (''
  mkdir -p $out
'' + builtins.concatStringsSep "\n" (map copy names))
