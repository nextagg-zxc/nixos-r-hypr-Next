# Иконки, которых нет в теме рабочего стола (Yaru → hicolor) на NixOS, а ярлыки их
# просят: взяты из пакетов (docker, fluxer, claude-desktop,
# yazi, opentabletdriver, adwaita-icon-theme-legacy). Лежат в hicolor — его
# оболочка проверяет последним, так что настоящие иконки тем их перекрывают.
{ stdenvNoCC }:
stdenvNoCC.mkDerivation {
  pname = "nextagg-extra-icons";
  version = "1";
  src = ./.;
  installPhase = ''
    mkdir -p $out/share/icons
    cp -r hicolor $out/share/icons/
  '';
}
