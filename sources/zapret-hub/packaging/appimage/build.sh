#!/bin/bash
# Сборка dist/ZapretHub-x86_64.AppImage: Python 3.12 (manylinux_2_28, glibc 2.28+) + PySide6 + программа.
# Нужны: curl, ar, tar, readelf (binutils), интернет. Запуск из корня репозитория:
#   packaging/appimage/build.sh
set -euo pipefail
ROOT=$(readlink -f "$(dirname "$0")/../..")
W=$ROOT/build/appimage
CACHE=$W/cache
APPDIR=$W/AppDir
VERSION=$(sed -n 's/^VERSION = "\(.*\)"/\1/p' "$ROOT/zaprethub/__init__.py")
PYSIDE=6.12.0
PY=python3.12
UBUNTU=http://archive.ubuntu.com/ubuntu/pool

fetch() {   # url sha256 -> $CACHE/<name>
    local url=$1 sum=$2 out=$CACHE/${1##*/}
    mkdir -p "$CACHE"
    [ -f "$out" ] && echo "$sum  $out" | sha256sum -c --quiet 2>/dev/null && return
    curl -sSfL -o "$out.part" "$url"
    echo "$sum  $out.part" | sha256sum -c --quiet || { echo "ОШИБКА: контрольная сумма $url" >&2; exit 1; }
    mv "$out.part" "$out"
}

fetch https://github.com/niess/python-appimage/releases/download/python3.12/python3.12.15-cp312-cp312-manylinux_2_28_x86_64.AppImage \
    929ce69b45955bfc74af81fd65a65c3ad240593c99b3574466a94ebf0f987ebf
fetch https://github.com/AppImage/appimagetool/releases/download/1.9.1/appimagetool-x86_64.AppImage \
    ed4ce84f0d9caff66f50bcca6ff6f35aae54ce8135408b3fa33abfc3cb384eb0
# xcb-util-библиотеки, которых часто нет в Ubuntu/Mint (без libxcb-cursor0 Qt 6 не стартует под X11);
# из Ubuntu 20.04, чтобы не требовать свежую glibc. libxkbcommon-x11/libxcb-xkb не кладём: они обязаны
# совпадать по версии с системными libxkbcommon/libxcb (старая xkbcommon-x11 падает с новой xkbcommon)
DEBS="universe/x/xcb-util-cursor/libxcb-cursor0_0.1.1-4ubuntu1_amd64.deb c9b5d1ad4af57397b1bd77e0a92750e34419def134c0282a0836ae9efc07cf64
main/x/xcb-util-wm/libxcb-icccm4_0.4.1-1.1_amd64.deb 03cf5acb68f7d6bffa378f9d30e8d519ee3e5b10340df741af8c0d8bbaf5d3d4
main/x/xcb-util-image/libxcb-image0_0.4.0-1build1_amd64.deb 4002be5159fe91fcfbc6cdb68871163dbfd5c1092341bb51f26079e25b421d92
main/x/xcb-util-keysyms/libxcb-keysyms1_0.4.0-1build1_amd64.deb 6cfbd86d2e1c66d2d8d0a6a17f27f0b825fc0d595647674714a2926a616bdae6
main/x/xcb-util-renderutil/libxcb-render-util0_0.3.9-1build1_amd64.deb 5486323b1a43b8d4d1f19986fac99a25c00676cd5596926d973e4966c8f05a84
main/x/xcb-util/libxcb-util1_0.4.0-0ubuntu3_amd64.deb 83f9a455c8c6e787fcad27a84108704c7aa7669405f2af097cd25cfeeb10d82a"
while read -r path sum; do fetch "$UBUNTU/$path" "$sum"; done <<<"$DEBS"

echo "==> Python"
rm -rf "$W/py" "$APPDIR"
mkdir -p "$W/py"
chmod +x "$CACHE"/*.AppImage
(cd "$W/py" && "$CACHE/python3.12.15-cp312-cp312-manylinux_2_28_x86_64.AppImage" --appimage-extract >/dev/null)
mv "$W/py/squashfs-root" "$APPDIR"
rm -rf "$W/py" "$APPDIR"/AppRun "$APPDIR"/*.desktop "$APPDIR"/python.png "$APPDIR"/.DirIcon "$APPDIR/usr/share/tcltk" \
    "$APPDIR"/usr/lib/libtcl* "$APPDIR"/usr/lib/libtk* "$APPDIR"/usr/share/applications "$APPDIR"/usr/share/metainfo
PYBIN=$APPDIR/opt/$PY/bin/$PY
SITE=$APPDIR/opt/$PY/lib/$PY/site-packages
STDLIB=$APPDIR/opt/$PY/lib/$PY
rm -rf "$STDLIB"/{test,idlelib,tkinter,turtledemo,ensurepip,lib2to3} "$STDLIB"/lib-dynload/_tkinter* "$APPDIR/opt/$PY/include"

echo "==> PySide6 $PYSIDE"
SSL_CERT_FILE=$APPDIR/opt/_internal/certs.pem "$PYBIN" -I -m pip install --disable-pip-version-check -q \
    --no-compile "PySide6-Essentials==$PYSIDE"
"$PYBIN" -I "$ROOT/packaging/appimage/prune.py" "$SITE"
while read -r path sum; do
    deb=$CACHE/${path##*/}
    t=$(mktemp -d)
    (cd "$t" && ar x "$deb" && tar xf data.tar.*)
    cp -P "$t"/usr/lib/x86_64-linux-gnu/lib*.so.* "$SITE/PySide6/Qt/lib/"
    rm -rf "$t"
done <<<"$DEBS"

echo "==> Zapret Hub $VERSION"
A=$APPDIR/usr/lib/zapret-hub
mkdir -p "$A/packaging"
cp -r "$ROOT/zaprethub" "$A/"
cp -r "$ROOT/packaging/linux" "$A/packaging/"
cp "$ROOT/packaging/appimage/run.py" "$A/run.py"
find "$APPDIR" -name __pycache__ -prune -exec rm -rf {} +
"$PYBIN" -I -m compileall -q -j0 "$APPDIR/opt/$PY/lib" "$A/zaprethub" >/dev/null
cat >"$APPDIR/AppRun" <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/opt/python3.12/bin/python3.12" -I "$HERE/usr/lib/zapret-hub/run.py" "$@"
EOF
chmod +x "$APPDIR/AppRun"
cp "$ROOT/packaging/linux/zapret-hub.svg" "$APPDIR/zapret-hub.svg"
ln -sf zapret-hub.svg "$APPDIR/.DirIcon"
sed 's/^Exec=.*/Exec=zapret-hub/' "$ROOT/packaging/linux/zapret-hub.desktop" >"$APPDIR/zapret-hub.desktop"

echo "==> AppImage"
mkdir -p "$ROOT/dist"
OUT=$ROOT/dist/ZapretHub-$VERSION-x86_64.AppImage
ARCH=x86_64 "$CACHE/appimagetool-x86_64.AppImage" --appimage-extract-and-run --no-appstream -n "$APPDIR" "$OUT" \
    >"$W/appimagetool.log" 2>&1 || { tail -20 "$W/appimagetool.log"; exit 1; }
du -h "$OUT"
