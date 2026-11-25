"""Каталог Магазина: индекс nixpkgs (nix search --json), результаты Flathub, поиск, подсказка команд.
Чистый Python без GTK (tests/share/test_store_catalog.py)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

PREFIX = re.compile(r"^legacyPackages\.[^.]+\.")
ATTR = re.compile(r"^[A-Za-z_][A-Za-z0-9_+-]*(\.[A-Za-z_][A-Za-z0-9_+-]*)*$")
# библиотеки и наборы для разработчиков новичку в Магазине не нужны
LIBRARY_SETS = ("Packages.", "haskellPackages", "perlPackages", "python", "rubyPackages", "lua", "nodePackages",
                "ocamlPackages", "rPackages", "emacsPackages", "vimPlugins", "texlivePackages", "linuxKernel",
                "kdePackages.", "gnome.", "xfce.", "qt5.", "qt6.", "libsForQt5.", "coqPackages", "idrisPackages")


@dataclass
class Entry:
    attr: str          # имя атрибута nixpkgs или id приложения Flathub
    name: str
    version: str
    description: str
    source: str        # "nixpkgs" | "flathub"


def valid_attr(attr: str) -> bool:
    return bool(attr) and ".." not in attr and bool(ATTR.match(attr))


def load_index(path) -> list[Entry] | None:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    out = []
    for key, v in data.items():
        attr = PREFIX.sub("", key)
        out.append(Entry(attr, v.get("pname") or attr, v.get("version", ""), v.get("description", ""), "nixpkgs"))
    return out


def parse_flatpak_search(text: str) -> list[Entry]:
    """Вывод `flatpak search --columns=application,name,description,version`."""
    out = []
    for line in text.splitlines():
        cols = line.split("\t")
        if len(cols) >= 2 and cols[0] and "." in cols[0]:
            cols += [""] * (4 - len(cols))
            out.append(Entry(cols[0], cols[1], cols[3], cols[2], "flathub"))
    return out


def _is_library(e: Entry) -> bool:
    return e.source == "nixpkgs" and "." in e.attr and e.attr.startswith(LIBRARY_SETS)


def search(query: str, index: list[Entry] | None, flathub: list[Entry], limit: int = 60) -> list[Entry]:
    q = query.strip().casefold()
    if not q:
        return []
    scored = []
    for e in (index or []) + flathub:
        if _is_library(e):
            continue
        name, attr, desc = e.name.casefold(), e.attr.casefold(), e.description.casefold()
        if q == name or q == attr:
            s = 0
        elif name.startswith(q) or attr.startswith(q):
            s = 1
        elif q in name or q in attr:
            s = 2
        elif q in desc:
            s = 3
        else:
            continue
        scored.append((s, e.source != "flathub", len(e.name), e))
    scored.sort(key=lambda t: t[:3])
    return [t[3] for t in scored[:limit]]


def command_hint(cmd: str, index: list[Entry] | None) -> str | None:
    """Имя пакета nixpkgs, в котором, вероятно, есть команда cmd (pname или имя атрибута совпадает)."""
    if not index or not re.match(r"^[A-Za-z0-9][A-Za-z0-9_+.-]*$", cmd):
        return None
    for e in index:
        if not _is_library(e) and (e.attr == cmd or e.name == cmd):
            return e.attr
    return None
