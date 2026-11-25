"""Дописывает пункты меню для NixOS в конец nixos-menu.jsonc.

JSONC — объект { "id": {...}, ... } с комментариями. Пункты из файла
overrides вставляются перед последней закрывающей скобкой; одинаковый id
дальше по файлу переопределяет поля предыдущего (так работает nixos-menu).
"""
import sys

menu_path, extra_path = sys.argv[1], sys.argv[2]
menu = open(menu_path, encoding="utf-8").read()
extra = open(extra_path, encoding="utf-8").read().strip()

end = menu.rstrip().rfind("}")
if end < 0:
    sys.exit(f"{menu_path}: не нашёл закрывающую скобку")

head = menu[:end].rstrip()
if not head.endswith(",") and not head.endswith("{"):
    head += ","

open(menu_path, "w", encoding="utf-8").write(
    head + "\n\n  // ── NixOS (добавлено сборкой, overrides/menu-nixos.jsonc) ──\n  "
    + extra.replace("\n", "\n  ") + "\n}\n"
)
