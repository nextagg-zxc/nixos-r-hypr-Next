#!/usr/bin/env python3
"""Вид для друзей: из собранного личного вида (pkgs/look.nix → share/nixos-look/home) убирается личное.
    share-profile.py <home-dir>      (правит на месте; повторный запуск ничего не меняет)
Списки личного — ниже (анти-цель дизайна раздаваемой системы: никакого личного в образе)."""
import json
import re
import shutil
import sys
from pathlib import Path

PERSONAL_PLUGINS = ["nextagg.agents", "ajazz.mouse-battery"]
# разделы меню целиком (ключ и всё, что под ним) и отдельные пункты
PERSONAL_MENU_SECTIONS = ["server", "rea", "xtool", "claude", "winsub"]
PERSONAL_MENU_KEYS = ["system.screensaver", "update.epic",
                      # инструменты автора для его ~/nixos-config (у друга флейк в /etc/nixos, хост share)
                      "packages.config", "packages.apply", "packages.save", "update.gc"]
# у друга обновление и откат — «Настройка системы» → «Обновление» (pkexec, откат на любую версию)
SHARE_MENU_ACTIONS = {"update.nixos": "uwsm-app -- nixos-settings --section update",
                      "update.rollback": "uwsm-app -- nixos-settings --section update"}
# «claude apps» у друзей — «Программы», только эти пункты
SHARED_APPS = ["autostart", "soundcloud", "zaprethub"]
# пункты «Программ», которых у пользователя нет (только у друзей)
SHARE_MENU_EXTRA = [
    '"claudeapps.help": {"icon":"' + chr(0xF02D6) + '","label":"Позвать на помощь","description":"Друг подключится к экрану (RustDesk)","aliases":["help","помощь","rustdesk"],"action":"uwsm-app -- nixos-tool help","when":"command -v nixos-tool"},',
    '"claudeapps.report": {"icon":"' + chr(0xF00E4) + '","label":"Сообщить о проблеме","description":"Журналы одним файлом для помощника","aliases":["report","bug","проблема"],"action":"uwsm-app -- nixos-tool report","when":"command -v nixos-tool"},',
    '"claudeapps.update": {"icon":"' + chr(0xF06B0) + '","label":"Обновление системы","description":"Обновить или откатить прежнюю версию","aliases":["update","обновление","откат"],"action":"uwsm-app -- nixos-settings --section update","when":"command -v nixos-settings"},',
    '"claudeapps.store": {"icon":"' + chr(0xF0110) + '","label":"Магазин","description":"Поиск и установка программ","aliases":["store","магазин","install","установить"],"action":"uwsm-app -- nixos-store","when":"command -v nixos-store"},',
    '"claudeapps.settings": {"icon":"\U000f0493","label":"Настройка системы","description":"Ядро, защита, Secure Boot, Windows в меню загрузки","aliases":["settings","настройки","secure boot"],"action":"uwsm-app -- nixos-settings","when":"command -v nixos-settings"},',
]
APPS_SECTION = {"label": "Программы", "aliases": ["programs", "apps", "программы"]}
PERSONAL_HYPR = ["hypr.monitors", "media-toggle", "hypr.osu-spotify", "hypr.deadlock", "hypr.steam-friends",
                 "hypr.autostart", "hypr.princewm"]
PERSONAL_HYPR_SCRIPTS = ["autostart-media.sh", "share-hdmi-a-3.sh", "swap-media.sh"]
# из ~/.bashrc остаются шапка (до «Add your own…») и эти блоки
BASHRC_BLOCKS = ["terminal niceties", "terminal command suggestions"]

log = []


def write_if_changed(p: Path, text: str, what: str):
    if p.read_text(encoding="utf-8") != text:
        p.write_text(text, encoding="utf-8")
        log.append(what)


def plugins(home: Path):
    for pid in PERSONAL_PLUGINS:
        d = home / ".config/nixos/plugins" / pid
        if d.exists():
            shutil.rmtree(d)
            log.append(f"плагин {pid}")


def scrub(o):
    """Убрать из JSON всё, что ссылается на личные плагины (объекты с их id и сами строки-id)."""
    if isinstance(o, dict):
        return {k: scrub(v) for k, v in o.items() if k not in PERSONAL_PLUGINS}
    if isinstance(o, list):
        return [scrub(x) for x in o
                if not (isinstance(x, dict) and x.get("id") in PERSONAL_PLUGINS) and x not in PERSONAL_PLUGINS]
    return o


def shell_json(home: Path):
    p = home / ".config/nixos/shell.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    write_if_changed(p, json.dumps(scrub(data), indent=2, ensure_ascii=False) + "\n", "shell.json")


ENTRY = re.compile(r'^(\s*)"([^"]+)":\s*(\{.*\})(,?)\s*$')


def menu_keep(key: str) -> bool:
    top = key.split(".")[0]
    if top in PERSONAL_MENU_SECTIONS or key in PERSONAL_MENU_KEYS:
        return False
    if top == "claudeapps" and key != "claudeapps":
        return key.split(".", 1)[1] in SHARED_APPS
    return True


def menu(home: Path):
    p = home / ".config/nixos/extensions/nixos-menu.jsonc"
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("//"):
            continue  # комментарии — личные пояснения
        m = ENTRY.match(line)
        if m:
            indent, key, body, comma = m.groups()
            if not menu_keep(key):
                continue
            if key in SHARE_MENU_ACTIONS:
                obj = json.loads(body)
                obj["action"] = SHARE_MENU_ACTIONS[key]
                line = f'{indent}"{key}": {json.dumps(obj, ensure_ascii=False, separators=(",", ":"))}{comma}'
                out.append(line)
                continue
            if key == "claudeapps":
                obj = json.loads(body)
                obj.update(APPS_SECTION)
                line = f'{indent}"{key}": {json.dumps(obj, ensure_ascii=False, separators=(",", ":"))}{comma}'
                out.append(line)
                for extra in SHARE_MENU_EXTRA:
                    ekey = extra.split('"')[1]
                    if not any(l.lstrip().startswith(f'"{ekey}"') for l in out):
                        out.append(indent + extra)
                continue
        out.append(line)
    text = "\n".join(out) + "\n"
    text = re.sub(r"\n{3,}", "\n\n", text)
    write_if_changed(p, text, "меню")


def hyprland(home: Path):
    p = home / ".config/hypr/hyprland.lua"
    text = p.read_text(encoding="utf-8")
    for mod in PERSONAL_HYPR:
        text = re.sub(rf'^(require\("{re.escape(mod)}"\).*)$', r"-- share: \1", text, flags=re.M)
    text = text.replace("|local\\\\.ajazz\\\\..*", "")  # окна AJAZZ в правиле прозрачности
    # планшет OTD пользователя (osu!) — у друзей его нет: строку и её комментарий убираем целиком
    text = "".join(l for l in text.splitlines(True) if "opentabletdriver" not in l.lower())
    # раскладки автора (us,ru) → раскладки друга из установщика (файл пишет modules/nixos/share.nix)
    text = text.replace('    kb_layout = "us,ru",',
                        '    kb_layout = (function() local f = io.open("/etc/nixos-share/keyboard"); '
                        'if not f then return "us,ru" end; local s = f:read("l"); f:close(); return s end)(),')
    write_if_changed(p, text, "hyprland.lua")
    x = home / ".config/hypr/xdph.conf"
    if x.exists():  # выбор экрана жёстко на HDMI-A-3 пользователя — у друзей обычный выбор
        write_if_changed(x, "".join(l for l in x.read_text(encoding="utf-8").splitlines(True)
                                    if "custom_picker_binary" not in l and "HDMI-A-3" not in l), "xdph.conf")
    for s in PERSONAL_HYPR_SCRIPTS:
        f = home / ".config/hypr/scripts" / s
        if f.exists():
            f.unlink()
            log.append(f"hypr/scripts/{s}")


def bashrc(home: Path):
    p = home / ".bashrc"
    lines = p.read_text(encoding="utf-8").splitlines()
    # алиасы cfg/rebuild на nextagg-* (дописывает pkgs/look.nix, для ~/nixos-config автора) — убрать всегда,
    # и когда .bashrc уже вычищен заранее (флейк друга из экспорта)
    if any("nextagg-rebuild" in l for l in lines):
        i = next(i for i, l in enumerate(lines) if "nextagg-rebuild" in l)
        j = next((k for k in range(i, len(lines)) if lines[k].strip() == "fi"), i)
        lines = lines[:i] + lines[j + 1:]
        while lines and not lines[-1].strip():
            lines.pop()
        write_if_changed(p, "\n".join(lines) + "\n", ".bashrc (алиасы автора)")
    try:
        head_end = next(i for i, l in enumerate(lines) if l.startswith("# Add your own"))
    except StopIteration:
        return  # уже обработан
    out = lines[:head_end]
    for name in BASHRC_BLOCKS:
        b = next(i for i, l in enumerate(lines) if l.strip() == f"# >>> {name} >>>")
        e = next(i for i, l in enumerate(lines) if l.strip() == f"# <<< {name} <<<")
        out += [""] + lines[b:e + 1]
    # хвост pkgs/look.nix (алиасы cfg/rebuild на nextagg-* для ~/nixos-config автора) другу не нужен
    # pay-respects (блок выше) ставит свой command_not_found_handle и без nix-locate пишет только ошибку —
    # у друга неизвестная команда подсказывает программу из Магазина
    out += ["", "# неизвестная команда → «есть в программе X, установите через Магазин»",
            'command -v nixos-store-hint &>/dev/null && command_not_found_handle() { nixos-store-hint "$1"; }']
    write_if_changed(p, "\n".join(out).rstrip("\n") + "\n", ".bashrc")


def misc(home: Path):
    ff = home / ".config/fastfetch/config.jsonc"   # заголовок «nextagg@nixos» вписан руками → имя друга
    if ff.exists():
        text = ff.read_text(encoding="utf-8")
        new = re.sub(r'\{ "type": "custom", "format": "(\{#1\}\{#38;2;180;190;254\})nextagg(\{#\}.*?\{#magenta\})nixos" \}',
                     r'{ "type": "title", "format": "\1{user-name}\2{host-name}" }', text)
        write_if_changed(ff, new, "fastfetch title")
    m = home / ".config/mimeapps.list"
    if m.exists():
        write_if_changed(m, "".join(l for l in m.read_text(encoding="utf-8").splitlines(True) if "claude" not in l),
                         "mimeapps.list")
    w = home / ".config/nixos/glass-weather.json"   # город пользователя — у друга свой (плагин спросит/по умолчанию)
    if w.exists():
        w.unlink()
        log.append("glass-weather.json")
    a = home / ".config/nixos/defaults/agent"
    if a.exists():
        a.unlink()
        log.append("defaults/agent")


def main():
    home = Path(sys.argv[1])
    plugins(home)
    shell_json(home)
    menu(home)
    hyprland(home)
    bashrc(home)
    misc(home)
    print("share-profile: " + (", ".join(log) if log else "без изменений"))


if __name__ == "__main__":
    main()
