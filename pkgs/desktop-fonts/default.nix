# Шрифт значков рабочего стола и его правила fontconfig (upstream ставит их отдельным
# пакетом настроек 4.5.0). Лежат здесь уже переименованными: файл nixos.ttf,
# семейство и глиф U+E900 «nixos», правила 50-nixos.conf (24.11).
{ stdenvNoCC }:
stdenvNoCC.mkDerivation {
  pname = "nixos-desktop-fonts";
  version = "4.5.0";
  src = ./.;
  installPhase = ''
    install -Dm644 nixos.ttf -t $out/share/fonts/truetype/nixos
    install -Dm644 50-nixos.conf -t $out/etc/fonts/conf.d
  '';
}
