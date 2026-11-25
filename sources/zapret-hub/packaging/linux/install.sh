#!/bin/bash
# Установка Zapret Hub на Linux (Arch, Debian/Ubuntu, Fedora).
# Запускать из распакованной папки: sudo ./packaging/linux/install.sh  (или ./install.sh из архива)
# --system: только то, что работает от root (helper, служба, polkit), без интерфейса и PySide6;
#           так AppImage ставит свою системную часть.
set -e
cd "$(dirname "$(readlink -f "$0")")"
SRC=..; [ -d ../../zaprethub ] && SRC=../..; [ -d ./zaprethub ] && SRC=.
SRC=$(readlink -f "$SRC")
[ "$(id -u)" = 0 ] || exec sudo "$0" "$@"
gui=1; [ "$1" = --system ] && gui=0

need_venv=0
if command -v pacman >/dev/null; then
    echo "==> Arch: ставлю зависимости"
    pkgs="python nftables polkit libayatana-appindicator"; [ $gui = 1 ] && pkgs="$pkgs pyside6"
    pacman -S --needed --noconfirm $pkgs
elif command -v apt-get >/dev/null; then
    echo "==> Debian/Ubuntu: ставлю зависимости"
    apt-get update
    apt-get install -y python3 nftables policykit-1 2>/dev/null || apt-get install -y python3 nftables polkitd pkexec
    apt-get install -y libayatana-appindicator3-1 || true
    [ $gui = 0 ] || apt-get install -y python3-pyside6.qtwidgets python3-pyside6.qtgui python3-pyside6.qtcore \
        python3-pyside6.qtsvg python3-pyside6.qtnetwork 2>/dev/null || need_venv=1
elif command -v dnf >/dev/null; then
    echo "==> Fedora: ставлю зависимости"
    dnf install -y python3 nftables polkit libayatana-appindicator-gtk3 || true
    [ $gui = 0 ] || dnf install -y python3-pyside6 || need_venv=1
else
    echo "Не знаю этот дистрибутив. Нужны: python3, nftables, polkit (и PySide6 для интерфейса)." >&2
    [ $gui = 0 ] || /usr/bin/python3 -c 'import PySide6' 2>/dev/null || need_venv=1
fi
[ -x /usr/bin/python3 ] || { echo "ОШИБКА: нет /usr/bin/python3 — установи пакет python3" >&2; exit 1; }

echo "==> Копирую программу в /usr/lib/zapret-hub"
rm -rf /usr/lib/zapret-hub/zaprethub
mkdir -p /usr/lib/zapret-hub
cp -r "$SRC/zaprethub" /usr/lib/zapret-hub/
find /usr/lib/zapret-hub/zaprethub -name __pycache__ -prune -exec rm -rf {} +
chmod -R u=rwX,go=rX /usr/lib/zapret-hub
L="$SRC/packaging/linux"; [ -d "$L" ] || L=.
install -Dm755 "$L/zapret-hub-helper" /usr/lib/zapret-hub/zapret-hub-helper
install -Dm644 "$L/zapret-hub.service" /usr/lib/systemd/system/zapret-hub.service
install -Dm644 "$L/org.zaprethub.helper.policy" /usr/share/polkit-1/actions/org.zaprethub.helper.policy
if [ $gui = 1 ]; then
    install -Dm755 "$L/zapret-hub" /usr/bin/zapret-hub
    install -Dm644 "$L/zapret-hub.desktop" /usr/share/applications/zapret-hub.desktop
    install -Dm644 "$L/zapret-hub.svg" /usr/share/icons/hicolor/scalable/apps/zapret-hub.svg
fi
# отпечаток системной части: по нему AppImage понимает, что её надо обновить
if [ -f "$SRC/FINGERPRINT" ]; then install -m644 "$SRC/FINGERPRINT" /usr/lib/zapret-hub/FINGERPRINT
else rm -f /usr/lib/zapret-hub/FINGERPRINT; fi

if [ "$need_venv" = 1 ]; then
    echo "==> PySide6 нет в репозитории — ставлю в /usr/lib/zapret-hub/venv"
    command -v apt-get >/dev/null && apt-get install -y python3-venv python3-pip || true
    /usr/bin/python3 -m venv /usr/lib/zapret-hub/venv
    /usr/lib/zapret-hub/venv/bin/pip install --upgrade pip PySide6
fi

systemctl daemon-reload
systemctl try-restart zapret-hub.service 2>/dev/null || true   # если обход был включён — уже с новым кодом
if [ $gui = 1 ]; then
    gtk-update-icon-cache -q /usr/share/icons/hicolor 2>/dev/null || true
    echo
    echo "Готово. Открой «Zapret Hub» в меню приложений или командой: zapret-hub"
else
    echo "Системная часть установлена"
fi
