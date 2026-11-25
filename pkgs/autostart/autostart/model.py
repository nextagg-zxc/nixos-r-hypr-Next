"""Записи автозапуска: файлы XDG autostart (~/.config/autostart/*.desktop).

uwsm/systemd-xdg-autostart-generator превращает каждую запись в юнит app-<id>@autostart.service.
Задержка и скрытый запуск — обёртка autostart-run в Exec:
    Exec=autostart-run <задержка> <имя|0> -- <команда…>
где имя — special-воркспейс Hyprland (в KDE окно сворачивается), 0 — не прятать.
Системные записи (/etc/xdg/autostart) не трогаем: правим копией-перекрытием в ~/.config/autostart.
Чистый Python без GTK — проверяется pytest (tests/autostart/test_model.py).
"""
from __future__ import annotations

import configparser
import io
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

SECTION = "Desktop Entry"
OUR_DESKTOPS = ("Hyprland", "KDE")
FIELD_CODES = {"%f", "%F", "%u", "%U", "%d", "%D", "%n", "%N", "%i", "%c", "%k", "%v", "%m"}
RESERVED = set(" \t\n\"'\\><~|&;$*?#()`")

Where = Literal["all", "hyprland", "kde"]


@dataclass
class Entry:
    id: str
    name: str
    command: str
    enabled: bool
    hidden: bool
    delay: int
    icon: str
    source: Literal["user", "system"]
    path: Path | None
    where: Where = "all"
    # системный файл с тем же id (для перекрытий); у чисто пользовательских — None
    system_path: Path | None = field(default=None, repr=False)

    @property
    def slug(self) -> str:
        return self.id[:-len(".desktop")] if self.id.endswith(".desktop") else self.id


# ── Exec: кавычки по спецификации desktop entry ──

def exec_quote(args: list[str]) -> str:
    out = []
    for a in args:
        if a and not (set(a) & RESERVED):
            out.append(a)
        else:
            out.append('"' + re.sub(r'(["`$\\])', r"\\\1", a) + '"')
    return " ".join(out)


def exec_split(value: str) -> list[str]:
    args: list[str] = []
    cur: list[str] = []
    have = False
    i, n = 0, len(value)
    while i < n:
        ch = value[i]
        if ch in " \t\n":
            if have:
                args.append("".join(cur))
                cur, have = [], False
            i += 1
        elif ch == '"':
            have = True
            i += 1
            while i < n and value[i] != '"':
                if value[i] == "\\" and i + 1 < n:
                    i += 1
                cur.append(value[i])
                i += 1
            i += 1
        else:
            have = True
            cur.append(ch)
            i += 1
    if have:
        args.append("".join(cur))
    return args


def app_command(exec_value: str) -> str:
    """Exec приложения → команда для автозапуска: без кодов полей (%U, %f, %i…)."""
    return exec_quote([a for a in exec_split(exec_value) if a not in FIELD_CODES])


# строковое экранирование значений desktop-файла (\\ \n \t \r \s) — только для Exec
def _unescape(v: str) -> str:
    return re.sub(r"\\([\\nstr])", lambda m: {"\\": "\\", "n": "\n", "s": " ", "t": "\t", "r": "\r"}[m.group(1)], v)


def _escape(v: str) -> str:
    return v.replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")


# ── чтение/запись desktop-файлов ──

def _parser() -> configparser.ConfigParser:
    cp = configparser.ConfigParser(interpolation=None, strict=False, delimiters=("=",),
                                   comment_prefixes=("#",), inline_comment_prefixes=None,
                                   empty_lines_in_values=False, default_section="\0none")
    cp.optionxform = str  # type: ignore[assignment]
    return cp


def _read(path: Path) -> configparser.ConfigParser | None:
    cp = _parser()
    try:
        cp.read_string(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, configparser.Error):
        return None
    if not cp.has_section(SECTION):
        return None
    return cp


def _dump(cp: configparser.ConfigParser) -> str:
    buf = io.StringIO()
    cp.write(buf, space_around_delimiters=False)
    return buf.getvalue().rstrip("\n") + "\n"


def _as_dict(cp: configparser.ConfigParser) -> dict[str, dict[str, str]]:
    return {s: dict(cp[s]) for s in cp.sections()}


def _list(v: str) -> list[str]:
    return [x for x in v.split(";") if x]


def _truthy(v: str | None) -> bool:
    return (v or "").strip().lower() == "true"


def _locale_name(d: configparser.SectionProxy) -> str:
    lang = os.environ.get("LC_ALL") or os.environ.get("LC_MESSAGES") or os.environ.get("LANG") or ""
    lang = lang.split(".")[0].split("@")[0]
    for key in (f"Name[{lang}]", f"Name[{lang.split('_')[0]}]", "Name"):
        if lang and key in d or key == "Name":
            v = d.get(key)
            if v:
                return v
    return ""


def _applies(d: configparser.SectionProxy) -> bool:
    only = _list(d.get("OnlyShowIn", ""))
    if only and not set(only) & set(OUR_DESKTOPS):
        return False
    return not set(OUR_DESKTOPS) <= set(_list(d.get("NotShowIn", "")))


def _where(d: configparser.SectionProxy) -> Where:
    only = _list(d.get("OnlyShowIn", ""))
    if only == ["Hyprland"]:
        return "hyprland"
    if only == ["KDE"]:
        return "kde"
    return "all"


def _parse_exec(raw: str) -> tuple[str, int, bool]:
    value = _unescape(raw)
    args = exec_split(value)
    if len(args) >= 4 and Path(args[0]).name == "autostart-run" and args[3] == "--":
        try:
            delay = max(0, int(args[1]))
        except ValueError:
            delay = 0
        return exec_quote(args[4:]), delay, args[2] != "0"
    return value, 0, False


def _entry(id_: str, cp: configparser.ConfigParser, source: str, path: Path,
           system_path: Path | None) -> Entry | None:
    d = cp[SECTION]
    if d.get("Type", "Application") != "Application" or "Exec" not in d or not _applies(d):
        return None
    command, delay, hidden = _parse_exec(d["Exec"])
    enabled = not _truthy(d.get("Hidden")) and d.get("X-GNOME-Autostart-enabled", "true").strip().lower() != "false"
    return Entry(id=id_, name=_locale_name(d) or id_, command=command, enabled=enabled, hidden=hidden,
                 delay=delay, icon=d.get("Icon", ""), source=source, path=path,  # type: ignore[arg-type]
                 where=_where(d), system_path=system_path)


def _system_file(id_: str, config_dirs: list[Path]) -> Path | None:
    for d in config_dirs:
        p = d / "autostart" / id_
        if p.is_file():
            return p
    return None


def load_entries(config_home: Path, config_dirs: list[Path]) -> list[Entry]:
    ids: set[str] = set()
    for d in [config_home, *config_dirs]:
        ad = d / "autostart"
        if ad.is_dir():
            ids |= {p.name for p in ad.glob("*.desktop") if p.is_file()}
    out = []
    for id_ in ids:
        sys_path = _system_file(id_, config_dirs)
        user = config_home / "autostart" / id_
        path = user if user.is_file() else sys_path
        if path is None:
            continue
        cp = _read(path)
        if cp is None:
            continue
        e = _entry(id_, cp, "system" if sys_path else "user", path, sys_path)
        if e:
            out.append(e)
    return sorted(out, key=lambda e: (e.name.casefold(), e.id))


def _build(e: Entry, base: configparser.ConfigParser | None) -> configparser.ConfigParser:
    cp = _parser()
    if base is not None:
        cp.read_dict(_as_dict(base))
    if not cp.has_section(SECTION):
        cp.add_section(SECTION)
    d = cp[SECTION]
    d.setdefault("Type", "Application")
    if base is None:
        d["Name"] = e.name
        if e.icon:
            d["Icon"] = e.icon
    if e.delay > 0 or e.hidden:
        args = ["autostart-run", str(int(e.delay)), e.slug if e.hidden else "0", "--", *exec_split(e.command)]
        d["Exec"] = _escape(exec_quote(args))
    else:
        d["Exec"] = _escape(e.command)
    for key, val, default in (("X-Autostart-Delay", str(int(e.delay)), "0"),
                              ("X-Autostart-Hidden", "true" if e.hidden else "false", "false")):
        if val == default:
            d.pop(key, None)
        else:
            d[key] = val
    if e.enabled:
        d.pop("Hidden", None)
        if d.get("X-GNOME-Autostart-enabled", "").strip().lower() == "false":
            d.pop("X-GNOME-Autostart-enabled")
    else:
        d["Hidden"] = "true"
    if e.where == "hyprland":
        d["OnlyShowIn"] = "Hyprland;"
    elif e.where == "kde":
        d["OnlyShowIn"] = "KDE;"
    elif _where(d) != "all":
        d.pop("OnlyShowIn", None)
    return cp


def save_entry(e: Entry, config_home: Path) -> Path:
    target = config_home / "autostart" / e.id
    sys_path = e.system_path
    sys_cp = _read(sys_path) if sys_path else None
    base = _read(target) if target.is_file() else sys_cp
    new = _build(e, base)
    if sys_cp is not None:
        # то, что стало бы из системного файла без перекрытия, — сравниваем без него
        if _as_dict(_build(e, sys_cp)) == _as_dict(sys_cp) and _as_dict(new) == _as_dict(sys_cp):
            target.unlink(missing_ok=True)
            e.path = sys_path
            return sys_path  # type: ignore[return-value]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_dump(new), encoding="utf-8")
    e.path = target
    return target


def remove_entry(e: Entry, config_home: Path) -> None:
    if e.source != "user":
        raise ValueError("системную запись можно только выключить")
    (config_home / "autostart" / e.id).unlink(missing_ok=True)


def list_apps(data_dirs: list[Path]) -> list[Entry]:
    seen: dict[str, Entry] = {}
    for d in data_dirs:
        ad = d / "applications"
        if not ad.is_dir():
            continue
        for p in sorted(ad.rglob("*.desktop")):
            id_ = str(p.relative_to(ad)).replace(os.sep, "-")
            if id_ in seen:
                continue
            cp = _read(p)
            if cp is None:
                continue
            s = cp[SECTION]
            if s.get("Type") != "Application" or "Exec" not in s or _truthy(s.get("NoDisplay")) or _truthy(s.get("Hidden")):
                continue
            seen[id_] = Entry(id=id_, name=_locale_name(s) or id_, command=app_command(_unescape(s["Exec"])),
                              enabled=True, hidden=False, delay=0, icon=s.get("Icon", ""), source="user", path=None)
    return sorted(seen.values(), key=lambda e: (e.name.casefold(), e.id))


TRANSLIT = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
                    ["a", "b", "v", "g", "d", "e", "e", "zh", "z", "i", "y", "k", "l", "m", "n", "o", "p", "r",
                     "s", "t", "u", "f", "kh", "ts", "ch", "sh", "shch", "", "y", "", "e", "yu", "ya"]))


def entry_from_command(name: str, command: str, taken: set[str]) -> Entry:
    s = "".join(TRANSLIT.get(c, c) for c in name.lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "custom"
    id_, n = f"{s}.desktop", 2
    while id_ in taken:
        id_, n = f"{s}-{n}.desktop", n + 1
    return Entry(id=id_, name=name, command=command, enabled=True, hidden=False, delay=0,
                 icon="", source="user", path=None)


def seed(defaults: list[dict], config_home: Path) -> list[str]:
    created = []
    for d in defaults:
        id_ = d["id"]
        if (config_home / "autostart" / id_).exists():
            continue
        e = Entry(id=id_, name=d.get("name", id_), command=d["command"], enabled=True,
                  hidden=bool(d.get("hidden", False)), delay=int(d.get("delay", 0)),
                  icon=d.get("icon", ""), source="user", path=None, where=d.get("where", "all"))
        save_entry(e, config_home)
        created.append(id_)
    return created
