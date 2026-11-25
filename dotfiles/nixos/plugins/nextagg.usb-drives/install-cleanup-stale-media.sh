#!/usr/bin/env bash
# Ставит автоочистку висячих монтирований в /run/media (btrfs-флешка после
# выдёргивания остаётся смонтированной как «<missing disk>») и сразу чистит текущие.
# Запуск: sudo bash install-cleanup-stale-media.sh
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "Нужен sudo" >&2; exit 1; }

cat > /usr/local/bin/cleanup-stale-media <<'EOF'
#!/usr/bin/env bash
# Размонтирует в /run/media всё, у чего исчезло блочное устройство.
while read -r -a f; do
    for ((i = 6; i < ${#f[@]}; i++)); do [ "${f[i]}" = "-" ] && break; done
    target=$(printf '%b' "${f[4]}")
    src=$(printf '%b' "${f[i+2]}")
    case "$target" in /run/media/*) ;; *) continue ;; esac
    [[ "$src" == /dev/* && -b "$src" ]] && continue
    echo "stale: $target ($src)"
    umount -l "$target" && rmdir "$target" 2>/dev/null || true
done < <(tac /proc/self/mountinfo)
EOF
chmod 755 /usr/local/bin/cleanup-stale-media

cat > /etc/systemd/system/cleanup-stale-media.service <<'EOF'
[Unit]
Description=Unmount stale removable media in /run/media

[Service]
Type=oneshot
ExecStartPre=/usr/bin/sleep 1
ExecStart=/usr/local/bin/cleanup-stale-media
EOF

# udevd работает с PrivateMounts — сам umount сделать не может, поэтому через systemd
cat > /etc/udev/rules.d/99-cleanup-stale-media.rules <<'EOF'
ACTION=="remove", SUBSYSTEM=="block", ENV{ID_BUS}=="usb", RUN+="/usr/bin/systemctl --no-block start cleanup-stale-media.service"
EOF

systemctl daemon-reload
udevadm control --reload
/usr/local/bin/cleanup-stale-media
echo "Готово."
