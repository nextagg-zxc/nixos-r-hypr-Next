#!/usr/bin/env python3
"""Root-помощник «Настройки системы» (раздаваемая система). Запускается через pkexec.
Вывод: строки журнала и события '@@{json}'.

  set                    stdin: JSON-патч choices.json → проверка → запись → nixos-rebuild switch
                         (неудачная сборка — прежний choices.json возвращается)
  secureboot-prepare     ключи sbctl; если прошивка в Setup Mode — записать их с ключами Microsoft и
                         включить подпись загрузки; иначе — только ключи и событие need=setup_mode
  tpm2-enroll <dev>      stdin: пароль диска; привязка LUKS к TPM2 (PCR 7), старая привязка заменяется
  tpm2-wipe <dev>        убрать привязку к TPM2
  status                 JSON: Secure Boot (sbctl), LUKS-устройства с TPM2, найденные Windows
  packages-add <attr>    Магазин: программа из nixpkgs в packages.json (имя проверяется по индексу) + сборка
  packages-remove <attr> убрать программу из packages.json + сборка
  update                 «Обновление системы»: свежие входы флейка (nixpkgs…) + сборка; не собралось — прежний flake.lock
  generations            JSON: поколения системы (номер, дата, версия, текущее)
  rollback <N>           переключиться на поколение N («Откатить»)
  gc                     уборка (раз в неделю): поколения старше 14 дней, но не последние 5 и не текущее; потом сборка мусора

Для тестов (только когда запущено не через pkexec): NIXOS_SHARE_ETC, NIXOS_SHARE_ENUMS,
NIXOS_SHARE_REBUILD, NIXOS_SHARE_SBCTL_KEYS.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

TRUSTED = os.environ.get("PKEXEC_UID") is None  # под pkexec переменные-подмены не принимаются
ETC = (TRUSTED and os.environ.get("NIXOS_SHARE_ETC")) or "/etc/nixos"
ENUMS_FILE = (TRUSTED and os.environ.get("NIXOS_SHARE_ENUMS")) or "@enums@"
REBUILD = (TRUSTED and os.environ.get("NIXOS_SHARE_REBUILD")) or None
SBCTL_KEYS = (TRUSTED and os.environ.get("NIXOS_SHARE_SBCTL_KEYS")) or "/var/lib/sbctl/keys"
STORE_INDEX = (TRUSTED and os.environ.get("NIXOS_SHARE_STORE_INDEX")) or "/var/lib/nixos-store/index.json"
PACKAGES = os.path.join(ETC, "hosts", "share", "packages.json")
FLAKE_UPDATE = (TRUSTED and os.environ.get("NIXOS_SHARE_FLAKE_UPDATE")) or None
SWITCH_GEN = (TRUSTED and os.environ.get("NIXOS_SHARE_SWITCH_GEN")) or None
GC_DELETE = (TRUSTED and os.environ.get("NIXOS_SHARE_GC_DELETE")) or None
PROFILES = (TRUSTED and os.environ.get("NIXOS_SHARE_PROFILES")) or "/nix/var/nix/profiles"
# сетевые входы флейка, которые обновляются (свои исходники — path:, они приходят с образом)
UPDATE_INPUTS = ["nixpkgs", "home-manager", "nix-cachyos-kernel", "spicetify-nix"]
ATTR = re.compile(r"^[A-Za-z_][A-Za-z0-9_+-]*(\.[A-Za-z_][A-Za-z0-9_+-]*)*$")
# ETC — корень флейка системы (/etc/nixos); выбор друга — рядом с хостом share
CHOICES = os.path.join(ETC, "hosts", "share", "choices.json")

GUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
USER = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")


def log(msg):
    print(msg, flush=True)


def event(**kw):
    print("@@" + json.dumps(kw, ensure_ascii=False), flush=True)


def die(msg, code=1):
    log(f"ОШИБКА: {msg}")
    event(type="done", ok=False, error=msg)
    sys.exit(code)


def load_enums():
    with open(ENUMS_FILE, encoding="utf-8") as f:
        return json.load(f)


def validate(c, enums):
    """Те же правила, что lib/choices.nix (списки значений — из него же, enums.json)."""
    top = {"user", "hostname", "locale", "timezone", "keyboard", "desktop", "kdeLook", "kernel", "kernelBuild",
           "gpu", "player", "extras", "system", "boot", "hardware"}
    if not isinstance(c, dict):
        raise ValueError("choices.json должен быть объектом")
    extra = set(c) - top
    if extra:
        raise ValueError(f"неизвестное поле {', '.join(sorted(extra))}")
    for k in ("desktop", "kdeLook", "kernel", "kernelBuild", "gpu", "player"):
        if k in c and c[k] not in enums[k]:
            raise ValueError(f"{k} = {c[k]!r}, допустимо: {', '.join(enums[k])}")
    if "extras" in c:
        if not isinstance(c["extras"], list) or any(x not in enums["extras"] for x in c["extras"]):
            raise ValueError("extras: недопустимое значение")
    u = c.get("user", {})
    if not isinstance(u, dict) or set(u) - {"name", "fullName", "passwordHash"}:
        raise ValueError("user: неизвестное поле")
    if "name" in u and (not USER.match(str(u["name"])) or u["name"] == "root"):
        raise ValueError("user.name недопустим")
    s = c.get("system", {})
    if not isinstance(s, dict) or set(s) - {"mitigationsOff", "virtualization", "iommu"}:
        raise ValueError("system: неизвестное поле")
    if any(not isinstance(v, bool) for v in s.values()):
        raise ValueError("system: значения — true/false")
    b = c.get("boot", {})
    if not isinstance(b, dict) or set(b) - {"secureBoot", "windows"}:
        raise ValueError("boot: неизвестное поле")
    if "secureBoot" in b and not isinstance(b["secureBoot"], bool):
        raise ValueError("boot.secureBoot — true/false")
    for w in b.get("windows", []):
        if not isinstance(w, dict) or set(w) - {"name", "esp"} or not GUID.match(str(w.get("esp", ""))):
            raise ValueError("boot.windows: нужен PARTUUID раздела EFI")
        if "name" in w and (not isinstance(w["name"], str) or not 0 < len(w["name"]) <= 40
                            or any(ch in w["name"] for ch in "\n/:")):
            raise ValueError("boot.windows[].name недопустимо")
    h = c.get("hardware", {})   # пишет установщик (найденное железо); подробно проверяет lib/choices.nix
    if not isinstance(h, dict) or set(h) - {"laptop", "prime", "snapshots", "windowsDisks"}:
        raise ValueError("hardware: неизвестное поле")
    if any(not isinstance(h[k], bool) for k in ("laptop", "snapshots") if k in h):
        raise ValueError("hardware: laptop/snapshots — true/false")
    if h.get("prime") is not None and (not isinstance(h["prime"], dict)
                                       or set(h["prime"]) - {"nvidiaBusId", "intelBusId", "amdgpuBusId"}):
        raise ValueError("hardware.prime недопустимо")
    if not isinstance(h.get("windowsDisks", []), list):
        raise ValueError("hardware.windowsDisks — список")
    for k in ("hostname", "locale", "timezone"):
        if k in c and not (isinstance(c[k], str) and re.match(r"^[A-Za-z0-9_./+-]{1,64}$", c[k])):
            raise ValueError(f"{k} недопустимо")


def merge(base, patch):
    """Патч поверх текущих настроек: вложенные user/system/boot сливаются, остальное заменяется."""
    out = dict(base)
    for k, v in patch.items():
        if k in ("user", "system", "boot") and isinstance(v, dict) and isinstance(out.get(k, {}), dict):
            out[k] = {**out.get(k, {}), **v}
        else:
            out[k] = v
    return out


def read_choices():
    try:
        with open(CHOICES, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def write_atomic(path, text):
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".choices-")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def rebuild():
    cmd = [REBUILD] if REBUILD else ["nixos-rebuild", "switch", "--flake", f"{ETC}#share"]
    log("Пересобираю систему (несколько минут)…")
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
    for line in p.stdout:
        log(line.rstrip("\n"))
    return p.wait() == 0


def apply_patch(patch):
    enums = load_enums()
    before = read_choices()
    new = merge(before, patch)
    try:
        validate(new, enums)
    except ValueError as e:
        die(str(e))
    backup = CHOICES + ".prev"
    if os.path.exists(CHOICES):
        shutil.copy2(CHOICES, backup)
    write_atomic(CHOICES, json.dumps(new, indent=2, ensure_ascii=False) + "\n")
    if not rebuild():
        if os.path.exists(backup):
            os.replace(backup, CHOICES)
        die("сборка не удалась — настройки возвращены как были")
    event(type="done", ok=True)


def cmd_set():
    try:
        patch = json.loads(sys.stdin.read(1024 * 1024) or "{}")
    except ValueError:
        die("запрос — не JSON")
    if not isinstance(patch, dict):
        die("запрос должен быть объектом")
    apply_patch(patch)


def sb_status():
    try:
        out = subprocess.run(["sbctl", "status", "--json"], capture_output=True, text=True).stdout
        return json.loads(out or "{}")
    except (OSError, ValueError):
        return {}


def cmd_secureboot_prepare():
    st = sb_status()
    ours = bool(st.get("installed"))  # наши ключи записаны в прошивку
    if st.get("secure_boot") and not ours:
        die("Secure Boot уже включён в BIOS с чужими ключами. Выключите Secure Boot в BIOS (или включите "
            "Setup Mode / «Удалить ключи»), затем повторите.")
    if not os.path.isdir(SBCTL_KEYS):
        log("Создаю ключи Secure Boot…")
        subprocess.run(["sbctl", "create-keys"], check=False)
    if st.get("setup_mode"):
        log("Прошивка в Setup Mode — записываю ключи вместе с ключами Microsoft…")
        r = subprocess.run(["sbctl", "enroll-keys", "--microsoft", "--firmware-builtin"])
        if r.returncode:
            die("не удалось записать ключи в прошивку")
        apply_patch({"boot": {"secureBoot": True}})
        event(type="secureboot", next="enable_in_bios")
        return
    if ours:
        apply_patch({"boot": {"secureBoot": True}})
        return
    event(type="secureboot", need="setup_mode")
    log("Ключи готовы. Включите в BIOS Setup Mode (или «Удалить ключи Secure Boot») и повторите.")
    event(type="done", ok=True)


def luks_device(dev):
    if not re.match(r"^/dev/[A-Za-z0-9/_.-]+$", dev) or ".." in dev:
        die("недопустимое устройство")
    if subprocess.run(["cryptsetup", "isLuks", dev]).returncode != 0:
        die(f"{dev} — не зашифрованный диск LUKS")
    return dev


def cmd_tpm2(action, dev):
    dev = luks_device(dev)
    if action == "enroll":
        password = sys.stdin.readline().rstrip("\n")
        if not password:
            die("нужен пароль диска")
        env = dict(os.environ, PASSWORD=password)
        r = subprocess.run(["systemd-cryptenroll", "--tpm2-device=auto", "--tpm2-pcrs=7", "--wipe-slot=tpm2", dev],
                           env=env, capture_output=True, text=True)
        if r.returncode:
            die("не удалось привязать TPM2 (неверный пароль или нет TPM)")
        log("Диск привязан к TPM2: при включённом Secure Boot пароль спрашиваться не будет")
    else:
        r = subprocess.run(["systemd-cryptenroll", "--wipe-slot=tpm2", dev], capture_output=True, text=True)
        if r.returncode:
            die("не удалось убрать привязку TPM2")
        log("Привязка к TPM2 убрана — диск снова открывается паролем")
    event(type="done", ok=True)


def cmd_status():
    st = {"secureboot": sb_status(), "luks": [], "windows": []}
    try:
        lsblk = json.loads(subprocess.run(["lsblk", "-J", "-p", "-o", "NAME,FSTYPE,PARTUUID,PARTTYPENAME,MOUNTPOINT"],
                                          capture_output=True, text=True).stdout)
    except (OSError, ValueError):
        lsblk = {"blockdevices": []}

    def walk(nodes):
        for n in nodes or []:
            yield n
            yield from walk(n.get("children"))
    for n in walk(lsblk.get("blockdevices")):
        if n.get("fstype") == "crypto_LUKS":
            dump = subprocess.run(["cryptsetup", "luksDump", n["name"]], capture_output=True, text=True).stdout
            st["luks"].append({"device": n["name"], "tpm2": "systemd-tpm2" in dump})
        if n.get("fstype") == "vfat" and n.get("partuuid"):
            mp = n.get("mountpoint")
            found = False
            if mp:
                found = os.path.exists(os.path.join(mp, "EFI/Microsoft/Boot/bootmgfw.efi"))
            else:
                with tempfile.TemporaryDirectory() as d:
                    if subprocess.run(["mount", "-o", "ro", n["name"], d], capture_output=True).returncode == 0:
                        found = os.path.exists(os.path.join(d, "EFI/Microsoft/Boot/bootmgfw.efi"))
                        subprocess.run(["umount", d])
            if found:
                st["windows"].append({"esp": n["partuuid"].lower(), "device": n["name"]})
    print(json.dumps(st, ensure_ascii=False))


def read_packages():
    try:
        with open(PACKAGES, encoding="utf-8") as f:
            data = json.load(f)
        return [x for x in data if isinstance(x, str)]
    except (OSError, ValueError):
        return []


def known_attr(attr):
    """Есть ли такой пакет в индексе Магазина (nix search --json)."""
    if not attr or ".." in attr or not ATTR.match(attr):
        return False
    try:
        with open(STORE_INDEX, encoding="utf-8") as f:
            index = json.load(f)
    except (OSError, ValueError):
        die("список программ ещё готовится — попробуйте через пару минут")
    return any(k.split(".", 2)[-1] == attr for k in index)


def cmd_packages(action, attr):
    if not known_attr(attr):
        die(f"нет такой программы: {attr!r}")
    pkgs = read_packages()
    if action == "add" and attr in pkgs or action == "remove" and attr not in pkgs:
        log("Уже сделано — пересборка не нужна")
        event(type="done", ok=True, unchanged=True)
        return
    new = pkgs + [attr] if action == "add" else [p for p in pkgs if p != attr]
    backup = PACKAGES + ".prev"
    if os.path.exists(PACKAGES):
        shutil.copy2(PACKAGES, backup)
    write_atomic(PACKAGES, json.dumps(sorted(set(new)), indent=2) + "\n")
    if not rebuild():
        if os.path.exists(backup):
            os.replace(backup, PACKAGES)
        die("сборка не удалась — список программ возвращён как был")
    log(("Установлено: " if action == "add" else "Удалено: ") + attr)
    event(type="done", ok=True)


def cmd_update():
    lock = os.path.join(ETC, "flake.lock")
    backup = lock + ".prev"
    if os.path.exists(lock):
        shutil.copy2(lock, backup)
    log("Скачиваю свежие версии программ…")
    cmd = [FLAKE_UPDATE] if FLAKE_UPDATE else ["nix", "--extra-experimental-features", "nix-command flakes",
                                              "flake", "update", "--flake", ETC, *UPDATE_INPUTS]
    if subprocess.run(cmd).returncode != 0:
        if os.path.exists(backup):
            os.replace(backup, lock)
        die("не удалось скачать обновления — проверьте интернет")
    if not rebuild():
        if os.path.exists(backup):
            os.replace(backup, lock)
        die("новая версия не собралась — система осталась прежней")
    subprocess.run(["systemctl", "start", "--no-block", "nixos-store-index.service"])
    log("Система обновлена. Если что-то не так — «Откатить» вернёт прежнюю.")
    event(type="done", ok=True)


def generations():
    out = []
    try:
        names = os.listdir(PROFILES)
    except OSError:
        return out
    current = os.readlink(os.path.join(PROFILES, "system")) if os.path.islink(os.path.join(PROFILES, "system")) else ""
    for n in names:
        m = re.match(r"^system-(\d+)-link$", n)
        if not m:
            continue
        path = os.path.join(PROFILES, n)
        try:
            with open(os.path.join(path, "nixos-version"), encoding="utf-8") as f:
                version = f.read().strip()
        except OSError:
            version = ""
        out.append({"number": int(m.group(1)), "date": int(os.lstat(path).st_mtime), "version": version,
                    "current": n == os.path.basename(current)})
    return sorted(out, key=lambda g: -g["number"])


def gc_plan(gens: list, now: float, keep: int = 5, days: int = 14) -> list:
    """Номера поколений на удаление: старше days дней, кроме последних keep и текущего."""
    last = {g["number"] for g in sorted(gens, key=lambda g: -g["number"])[:keep]}
    return sorted(g["number"] for g in gens
                  if g["number"] not in last and not g["current"] and now - g["date"] > days * 86400)


def cmd_gc():
    import time
    doomed = gc_plan(generations(), time.time())
    if doomed:
        nums = [str(n) for n in doomed]
        cmd = [GC_DELETE, *nums] if GC_DELETE else [
            "nix-env", "-p", f"{PROFILES}/system", "--delete-generations", *nums]
        if subprocess.run(cmd).returncode != 0:
            die("не удалось удалить старые поколения")
    if not GC_DELETE:
        subprocess.run(["nix-store", "--gc"])
    log(f"Уборка: удалено поколений {len(doomed)}")


def cmd_rollback(arg):
    if not re.match(r"^\d+$", arg) or not any(g["number"] == int(arg) for g in generations()):
        die("нет такого поколения")
    log(f"Переключаюсь на поколение {arg}…")
    cmd = [SWITCH_GEN, arg] if SWITCH_GEN else [
        "sh", "-c", f'nix-env -p {PROFILES}/system --switch-generation {int(arg)} && '
                    f'{PROFILES}/system/bin/switch-to-configuration switch']
    if subprocess.run(cmd).returncode != 0:
        die("не удалось переключиться")
    log("Готово. Перезагрузите компьютер, чтобы точно всё вернулось.")
    event(type="done", ok=True)


def main():
    a = sys.argv[1:]
    if a == ["set"]:
        cmd_set()
    elif a == ["secureboot-prepare"]:
        cmd_secureboot_prepare()
    elif len(a) == 2 and a[0] in ("tpm2-enroll", "tpm2-wipe"):
        cmd_tpm2(a[0][5:], a[1])
    elif len(a) == 2 and a[0] in ("packages-add", "packages-remove"):
        cmd_packages(a[0][9:], a[1])
    elif a == ["update"]:
        cmd_update()
    elif a == ["generations"]:
        print(json.dumps(generations(), ensure_ascii=False))
    elif a == ["gc"]:
        cmd_gc()
    elif len(a) == 2 and a[0] == "rollback":
        cmd_rollback(a[1])
    elif a == ["status"]:
        cmd_status()
    else:
        log("usage: nixos-share-apply set | secureboot-prepare | tpm2-enroll DEV | tpm2-wipe DEV | status |"
            " packages-add ATTR | packages-remove ATTR")
        sys.exit(2)


if __name__ == "__main__":
    main()
