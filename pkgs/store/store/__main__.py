"""python3 -m store [--selftest | hint <команда>]"""
import sys

if len(sys.argv) >= 3 and sys.argv[1] == "hint":
    # подсказка для command_not_found_handle (bash): без GTK
    import os

    from . import catalog

    idx = catalog.load_index(os.environ.get("NIXOS_STORE_INDEX") or "/var/lib/nixos-store/index.json")
    attr = catalog.command_hint(sys.argv[2], idx)
    if attr:
        print(f"Команды «{sys.argv[2]}» нет, но она есть в программе «{attr}».\n"
              f"Установить: откройте «Магазин» и найдите «{attr}».", file=sys.stderr)
    else:
        print(f"bash: {sys.argv[2]}: команда не найдена", file=sys.stderr)
    sys.exit(127)

if "--selftest" in sys.argv:
    from . import selftest

    sys.exit(selftest.main(sys.argv[1:]))

from . import ui

sys.exit(ui.main(sys.argv[:1]))
