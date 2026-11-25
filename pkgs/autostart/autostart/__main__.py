"""python3 -m autostart [--selftest | --seed <defaults.json>]"""
import sys

if "--seed" in sys.argv:
    # Посев записей по умолчанию (home-manager при активации): только недостающие. Без GTK.
    import json
    import os
    from pathlib import Path

    from . import model

    path = sys.argv[sys.argv.index("--seed") + 1]
    home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    created = model.seed(json.loads(Path(path).read_text(encoding="utf-8")), home)
    for c in created:
        print(f"autostart: добавлено {c}")
    sys.exit(0)

if "--selftest" in sys.argv:
    from . import selftest

    sys.exit(selftest.main(sys.argv[1:]))

from . import ui

sys.exit(ui.main(sys.argv[:1]))
