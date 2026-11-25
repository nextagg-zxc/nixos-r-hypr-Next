# Установщик раздаваемой NixOS: Calamares (штатные страницы + свои страницы выбора) и свой шаг установки.
#   calamares-nixos-share — Calamares с этими настройками (запускается в живой системе образа);
#   nixos-share-install   — тот же шаг без окна, по файлу ответов (проверка в QEMU, автоустановка).
# flake — экспорт флейка (scripts/export-share-flake.py), его установщик кладёт в /etc/nixos.
{
  lib,
  runCommand,
  python3,
  makeWrapper,
  calamares,
  calamares-nixos-extensions,
  glibcLocales,
  nixos-install-tools,
  pciutils,
  util-linux,
  nix,
  librsvg,
  papirus-icon-theme,
  flake ? null,
}:
let
  upstream = calamares-nixos-extensions;
  src = lib.fileset.toSource { root = ./.; fileset = lib.fileset.unions [ ./nixos_share ./calamares ./images ./add-images.py ./answers ]; };
  ext = runCommand "nixos-share-installer" { nativeBuildInputs = [ makeWrapper python3 librsvg ]; } ''
    mkdir -p $out/lib/nixos-share $out/etc/calamares/modules $out/lib/calamares/modules $out/share/calamares $out/bin
    cp -r ${src}/nixos_share ${src}/answers $out/lib/nixos-share/
    chmod -R u+w $out/lib/nixos-share
    substituteInPlace $out/lib/nixos-share/nixos_share/install.py \
      --replace-fail '@flake@' '${if flake == null then "/etc/nixos-share-flake" else flake}'
    cp ${src}/calamares/settings.conf $out/etc/calamares/
    cp ${src}/calamares/modules/*.conf $out/etc/calamares/modules/
    chmod -R u+w $out/etc
    substituteInPlace $out/etc/calamares/settings.conf --replace-fail '@ext@' "$out" --replace-fail '@upstream@' '${upstream}'
    substituteInPlace $out/etc/calamares/modules/locale.conf --replace-fail '@glibcLocales@' '${glibcLocales}'
    # картинки страниц выбора: снимки рабочих столов и значки
    python3 ${src}/add-images.py $out/etc/calamares/modules ${src}/images $out/share/nixos-share-installer/images \
      ${papirus-icon-theme}/share/icons/Papirus/64x64/apps
    cp -r ${src}/calamares/nixos-share $out/lib/calamares/modules/
    chmod -R u+w $out/lib/calamares
    substituteInPlace $out/lib/calamares/modules/nixos-share/main.py \
      --replace-fail '@lib@' "$out/lib/nixos-share" --replace-fail '@upstream@' '${upstream}'
    ln -s ${upstream}/share/calamares/branding $out/share/calamares/branding
    makeWrapper ${python3}/bin/python3 $out/bin/nixos-share-install \
      --prefix PYTHONPATH : $out/lib/nixos-share \
      --prefix PATH : ${lib.makeBinPath [ nixos-install-tools pciutils util-linux nix ]} \
      --add-flags "-m nixos_share"
    python3 -m py_compile $out/lib/nixos-share/nixos_share/*.py
  '';
in
ext
// {
  calamares = calamares.override {
    extraWrapperArgs = [
      "--prefix XDG_DATA_DIRS : ${ext}/share"
      "--prefix XDG_CONFIG_DIRS : ${ext}/etc"
      "--prefix PATH : ${lib.makeBinPath [ nixos-install-tools pciutils util-linux nix ]}"
      "--add-flag --xdg-config"
    ];
  };
}
