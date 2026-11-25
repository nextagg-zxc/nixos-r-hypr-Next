"""python3 -m system_settings [--selftest | --section <раздел> | --check-updates]"""
import os
import sys

if "--check-updates" in sys.argv:
    # ежедневная проверка (таймер пользователя): уведомление, если есть обновления. Без GTK-окна.
    import subprocess

    from .ui import check_updates

    r = check_updates()
    if r["online"] and (r["system"] or r["flatpaks"]):
        subprocess.run(["notify-send", "-a", "Обновление системы", "-i", "software-update-available",
                        "Есть обновления", "Откройте «Обновление системы», чтобы установить."])
    sys.exit(0)

if "--section" in sys.argv:
    os.environ["NIXOS_SETTINGS_SECTION"] = sys.argv[sys.argv.index("--section") + 1]

if "--selftest" in sys.argv:
    from . import selftest

    sys.exit(selftest.main(sys.argv[1:]))

from . import ui

sys.exit(ui.main(sys.argv[:1]))
