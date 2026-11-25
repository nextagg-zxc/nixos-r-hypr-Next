#!/bin/bash
# Полное удаление Zapret Hub.
set -e
[ "$(id -u)" = 0 ] || exec sudo "$0" "$@"
[ -x /usr/lib/zapret-hub/zapret-hub-helper ] && /usr/lib/zapret-hub/zapret-hub-helper uninstall || true
systemctl disable --now zapret-hub.service 2>/dev/null || true
rm -rf /usr/lib/zapret-hub /usr/bin/zapret-hub /usr/lib/systemd/system/zapret-hub.service \
    /usr/share/polkit-1/actions/org.zaprethub.helper.policy /usr/share/applications/zapret-hub.desktop \
    /usr/share/icons/hicolor/scalable/apps/zapret-hub.svg
systemctl daemon-reload
echo "Zapret Hub удалён"
