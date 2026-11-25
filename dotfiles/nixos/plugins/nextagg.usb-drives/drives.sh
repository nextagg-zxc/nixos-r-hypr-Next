#!/usr/bin/env bash
# Хелпер виджета «Флешки»:
#   drives.sh list        — JSON-массив файловых систем на USB-накопителях
#   drives.sh open DEV    — смонтировать (если нужно) и открыть в Files
#   drives.sh eject DISK  — размонтировать все разделы диска и обесточить его

# Диски, которые виджет не показывает (серийники, `lsblk -o NAME,SERIAL`):
#   CVLY636503T0256J — Intel SSD 256G в USB-боксе со второй системой (Win11)
HIDDEN_SERIALS='["CVLY636503T0256J"]'

notify() { notify-send -a "Флешки" -i drive-removable-media "$@"; }

case "$1" in
list)
    lsblk -J -l -b -o PATH,PKNAME,TYPE,LABEL,SIZE,FSTYPE,MOUNTPOINT,TRAN,MODEL,VENDOR,SERIAL |
    jq -c --argjson hidden "$HIDDEN_SERIALS" '.blockdevices as $all
        | [ $all[]
            | select(.size > 0 and .fstype != null)
            | select(.type == "part" or .type == "disk")
            | select(.fstype != "crypto_LUKS" and .fstype != "swap")
            | (if .type == "part" then .pkname else (.path | ltrimstr("/dev/")) end) as $dname
            | ($all[] | select(.path == "/dev/" + $dname)) as $disk
            | select($disk.tran == "usb")   # у разделов TRAN пустой — смотрим на диск
            | select(($disk.serial // "") as $s | $hidden | index($s) | not)
            | { dev: .path, disk: $disk.path, label: (.label // ""),
                model: ((($disk.vendor // "") + " " + ($disk.model // "")) | gsub("^ +| +$"; "") | gsub("  +"; " ")),
                size: .size, fstype: .fstype, mount: (.mountpoint // "") } ]
        # извлечённые (без носителя), но ещё не вынутые из порта
        + [ $all[]
            | select(.tran == "usb" and .type == "disk" and .size == 0)
            | select((.serial // "") as $s | $hidden | index($s) | not)
            | { dev: .path, disk: .path, label: "",
                model: (((.vendor // "") + " " + (.model // "")) | gsub("^ +| +$"; "") | gsub("  +"; " ")),
                size: 0, fstype: "", mount: "", ejected: true } ]'
    ;;
open)
    dev=$2
    mp=$(findmnt -n -o TARGET -S "$dev" | head -1)
    if [ -z "$mp" ]; then
        if ! err=$(udisksctl mount -b "$dev" --no-user-interaction 2>&1); then
            notify "Не удалось открыть $dev" "$err"; exit 1
        fi
        mp=$(findmnt -n -o TARGET -S "$dev" | head -1)
    fi
    [ -n "$mp" ] && exec nautilus --new-window "$mp"
    ;;
eject)
    disk=$2
    sync
    for part in $(lsblk -ln -o PATH,MOUNTPOINT "$disk" | awk 'NF == 2 { print $1 }'); do
        if ! err=$(udisksctl unmount -b "$part" --no-user-interaction 2>&1); then
            users=$(fuser -vm "$(findmnt -n -o TARGET -S "$part" | head -1)" 2>&1 | awk 'NR > 2 { print $NF }' | sort -u | paste -sd ', ')
            notify -u critical "Флешка занята" "${users:+Используют: $users\n}$err"
            exit 1
        fi
    done
    if err=$(udisksctl power-off -b "$disk" --no-user-interaction 2>&1); then
        notify "Флешку можно вынимать"
    else
        notify "Флешка размонтирована" "Отключить питание не удалось, но вынимать уже безопасно.\n$err"
    fi
    ;;
esac
