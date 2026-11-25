#!/usr/bin/env python3
"""Отпускает «залипшую» левую кнопку виртуального планшета OpenTabletDriver.

В режиме Absolute OTD отдаёт перо как мышь (BTN_LEFT = касание пером). Если OTD не
прислал отпускание (перо резко ушло из зоны, смена пресета, osu! закрылся с зажатым
пером), кнопка остаётся нажатой, и Hyprland перестаёт принимать левый клик настоящей
мыши (24.11: «после osu! на планшете мышка не нажимается»).

Правило: пером и мышью одновременно не работают. Если у планшета зажата левая кнопка,
а другая мышь двигается или нажимает кнопку, — пишем в устройство планшета BTN_LEFT=0.
Только стандартная библиотека; права — группа input. Устройства пересканируются
каждые 5 с (OTD при перезапуске создаёт планшет заново).
"""
import fcntl
import glob
import os
import select
import struct
import sys
import time

TABLET = "OpenTabletDriver Virtual Tablet"
# Собственные интерфейсы планшета (его HID-«мышь» шевелится вместе с пером) — не мыши.
TABLET_WORDS = ("wacom", "ctl-472", "tablet", "pen", "stylus")
EV_SYN, EV_KEY, EV_REL = 0, 1, 2
BTN_LEFT = 0x110
EVENT = struct.Struct("llHHi")
EVIOCGKEY = 0x80604518  # _IOR('E', 0x18, 96 байт битовой карты клавиш)


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def read_name(node):
    try:
        with open(f"/sys/class/input/{node}/device/name") as f:
            return f.read().strip()
    except OSError:
        return ""


def has_rel(node):
    try:
        with open(f"/sys/class/input/{node}/device/capabilities/rel") as f:
            return int(f.read().split()[-1], 16) & 0x3 != 0  # REL_X/REL_Y
    except (OSError, ValueError, IndexError):
        return False


def scan():
    tablet, mice = None, []
    for path in sorted(glob.glob("/sys/class/input/event*")):
        node = os.path.basename(path)
        name = read_name(node)
        if name == TABLET:
            tablet = f"/dev/input/{node}"
        elif has_rel(node) and not any(w in name.lower() for w in TABLET_WORDS):
            mice.append(f"/dev/input/{node}")
    return tablet, mice


def left_down(fd):
    buf = bytearray(96)
    try:
        fcntl.ioctl(fd, EVIOCGKEY, buf)
    except OSError:
        return False
    return bool(buf[BTN_LEFT // 8] & (1 << (BTN_LEFT % 8)))


def release(path):
    now = time.time()
    sec, usec = int(now), int((now % 1) * 1e6)
    fd = os.open(path, os.O_WRONLY)
    try:
        os.write(fd, EVENT.pack(sec, usec, EV_KEY, BTN_LEFT, 0) + EVENT.pack(sec, usec, EV_SYN, 0, 0))
    finally:
        os.close(fd)
    log(f"released stuck BTN_LEFT on {path}")


def main():
    opened = {}      # path -> fd
    tablet = None
    next_scan = 0.0
    while True:
        if time.time() >= next_scan:
            tablet, mice = scan()
            wanted = set(mice) | ({tablet} if tablet else set())
            for p in list(opened):
                if p not in wanted:
                    os.close(opened.pop(p))
            for p in wanted - set(opened):
                try:
                    opened[p] = os.open(p, os.O_RDONLY | os.O_NONBLOCK)
                except OSError as e:
                    log(f"cannot open {p}: {e}")
            next_scan = time.time() + 5
        if not opened:
            time.sleep(5)
            continue
        ready, _, _ = select.select(list(opened.values()), [], [], 5)
        for fd in ready:
            path = next((p for p, f in opened.items() if f == fd), None)
            try:
                data = os.read(fd, EVENT.size * 64)
            except BlockingIOError:
                continue
            except OSError:
                if path:
                    os.close(opened.pop(path))
                continue
            if path == tablet or not tablet or tablet not in opened:
                continue
            # Активность другой мыши: движение или кнопка.
            active = False
            for i in range(0, len(data) - EVENT.size + 1, EVENT.size):
                _, _, etype, code, value = EVENT.unpack_from(data, i)
                if etype == EV_REL or (etype == EV_KEY and code >= BTN_LEFT and value == 1):
                    active = True
                    break
            if active and left_down(opened[tablet]):
                try:
                    release(tablet)
                except OSError as e:
                    log(f"release failed: {e}")


if __name__ == "__main__":
    main()
