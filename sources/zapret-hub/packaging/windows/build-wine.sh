#!/bin/bash
# Сборка Windows-установщика на Linux через wine: dist/ZapretHub-Setup-<версия>.exe
# (Python 3.12 для Windows + PyInstaller + Inno Setup в отдельном префиксе build/wine/prefix).
# Нужны: wine, curl, интернет. Запуск из корня репозитория: packaging/windows/build-wine.sh
set -euo pipefail
ROOT=$(readlink -f "$(dirname "$0")/../..")
W=$ROOT/build/wine
CACHE=$W/cache
export WINEPREFIX=$W/prefix WINEDEBUG=-all WINEARCH=win64
VERSION=$(sed -n 's/^VERSION = "\(.*\)"/\1/p' "$ROOT/zaprethub/__init__.py")
PY='C:\Python312\python.exe'
ISCC='C:\InnoSetup\ISCC.exe'

fetch() {   # url sha256 -> $CACHE/<name>
    local url=$1 sum=$2 out=$CACHE/${1##*/}
    mkdir -p "$CACHE"
    [ -f "$out" ] && echo "$sum  $out" | sha256sum -c --quiet 2>/dev/null && return
    curl -sSfL -o "$out.part" "$url"
    echo "$sum  $out.part" | sha256sum -c --quiet || { echo "ОШИБКА: контрольная сумма $url" >&2; exit 1; }
    mv "$out.part" "$out"
}

fetch https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe \
    67b5635e80ea51072b87941312d00ec8927c4db9ba18938f7ad2d27b328b95fb
fetch https://github.com/jrsoftware/issrc/releases/download/is-7_1_0/innosetup-7.1.0-x64.exe \
    0362a383ed217d4c4239b5933866dd96d3eb2102737da92f80f6057a4b40df2f

if [ ! -f "$WINEPREFIX/drive_c/Python312/python.exe" ]; then
    echo "==> wine: Python 3.12"
    wineboot -i >/dev/null 2>&1
    wine "$CACHE/python-3.12.10-amd64.exe" /quiet InstallAllUsers=0 'TargetDir=C:\Python312' Include_test=0 \
        Include_tcltk=0 Include_launcher=0 Include_doc=0 Shortcuts=0 AssociateFiles=0
fi
if [ ! -f "$WINEPREFIX/drive_c/InnoSetup/ISCC.exe" ]; then
    echo "==> wine: Inno Setup 7.1"
    wine "$CACHE/innosetup-7.1.0-x64.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /CURRENTUSER '/DIR=C:\InnoSetup'
fi
wine "$PY" -m pip install --disable-pip-version-check -q --no-warn-script-location \
    PySide6-Essentials==6.12.0 psutil==7.2.2 pyinstaller==6.22.3

echo "==> тесты (Python для Windows)"
(cd "$ROOT" && QT_QPA_PLATFORM=offscreen wine "$PY" -m unittest discover -s tests 2>&1 | tail -3) | tee "$W/tests.log"
grep -q '^OK' "$W/tests.log" || { echo "ОШИБКА: тесты не прошли" >&2; exit 1; }

echo "==> PyInstaller"
rm -rf "$W/dist" "$W/work"
(cd "$ROOT" && wine "$PY" -m PyInstaller --noconfirm --clean --log-level WARN --distpath build/wine/dist \
    --workpath build/wine/work packaging/windows/zaprethub.spec)

echo "==> Inno Setup"
mkdir -p "$ROOT/dist"
(cd "$ROOT" && wine "$ISCC" /Q "/DAppVersion=$VERSION" "/DSrc=Z:$W/dist/ZapretHub" "/DOut=Z:$ROOT/dist" \
    packaging/windows/zaprethub.iss)
du -h "$ROOT/dist/ZapretHub-Setup-$VERSION.exe"
