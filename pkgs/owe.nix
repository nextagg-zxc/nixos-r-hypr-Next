{ lib, stdenv, src, meson, ninja, pkg-config, wayland, wayland-scanner, wayland-protocols,
  libGL, libepoxy, mpv-unwrapped, ffmpeg, systemdLibs, makeWrapper, socat, python3 }:

# owe — движок обоев рабочего стола (картинки, gif, mp4), демон owed.
# Исходник переименовывается как весь рабочий стол: пути ~/.local/state/nixos,
# команды nixos-theme-bg-* (scripts/rebrand.py).
stdenv.mkDerivation {
  pname = "owe";
  version = "0.2.13";
  inherit src;

  nativeBuildInputs = [ meson ninja pkg-config wayland-scanner makeWrapper python3 ];
  buildInputs = [ wayland wayland-protocols libGL libepoxy mpv-unwrapped ffmpeg systemdLibs ];

  # Тесты собираются вместе с программой; при установке они не нужны.
  mesonFlags = [ "-Dwerror=false" ];

  postPatch = ''
    python3 ${../scripts/rebrand.py} .
  '';
  doCheck = false;

  postInstall = ''
    for b in $out/bin/*; do
      wrapProgram "$b" --prefix PATH : ${lib.makeBinPath [ socat ]}
    done
  '';

  meta = {
    description = "High-performance wallpaper engine";
    homepage = "https://github.com/omacom/owe";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
    mainProgram = "owe";
  };
}
