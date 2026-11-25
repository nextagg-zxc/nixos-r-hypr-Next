# Zapret Hub для NixOS: пакет, модуль (services.zapret-hub) и тест в VM.
#   nix build -f packaging/nixos test --arg pkgs 'import <nixpkgs> {}'
{ pkgs ? import <nixpkgs> { } }:
rec {
  package = pkgs.callPackage ./package.nix { };
  module = ./module.nix;
  test = import ./test.nix { inherit pkgs module; };
}
