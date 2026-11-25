"""Логика установщика без Calamares: ответы страниц → choices.json, поиск железа, hardware-configuration.nix."""
from __future__ import annotations

import re
from pathlib import Path

ENUMS = {
    "desktop": ("hyprland", "kde", "both"), "kdeLook": ("win11", "win10"), "kernel": ("cachyos", "zen", "linux"),
    "kernelBuild": ("ready", "native"), "gpu": ("mesa", "nvidia", "nvidia-legacy"), "player": ("spotify", "soundcloud"),
}
EXTRAS = ("gaming", "obs", "telegram", "vr")
USERNAME = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")


def _pick(gs: dict, key: str) -> list[str]:
    v = gs.get(f"packagechooser_{key}") or ""
    if isinstance(v, (list, tuple)):
        return [str(x) for x in v if x]
    return [x.strip() for x in str(v).split(",") if x.strip()]


def _one(gs: dict, key: str, enum: str, default: str) -> str:
    v = _pick(gs, key)
    return v[0] if v and v[0] in ENUMS[enum] else default


def choices_from_answers(gs: dict, hw: dict) -> dict:
    """gs — глобальное хранилище Calamares (словарь), hw — найденное железо (detect_* ниже)."""
    name = gs.get("username") or ""
    if not USERNAME.match(name):
        raise ValueError(f"имя пользователя «{name}»: латиница в нижнем регистре, цифры, _ и -")
    lang = ((gs.get("localeConf") or {}).get("LANG") or "ru_RU.UTF-8").split("/")[0]
    region, zone = gs.get("locationRegion"), gs.get("locationZone")
    layout = (gs.get("keyboardLayout") or "us").strip()
    keyboard = ["us"] if layout == "us" else ["us", layout]
    gpu = _pick(gs, "gpu")
    gpu = gpu[0] if gpu and gpu[0] in ENUMS["gpu"] else hw.get("gpu", "mesa")
    extras = [e for e in _pick(gs, "extras") if e in EXTRAS]
    if gs.get("autoLoginUser"):
        extras.append("autologin")
    system = set(_pick(gs, "system"))
    return {
        "user": {"name": name, "fullName": gs.get("fullname") or name},
        "hostname": gs.get("hostname") or "nixos",
        "locale": lang,
        "timezone": f"{region}/{zone}" if region and zone else "Europe/Moscow",
        "keyboard": keyboard,
        "desktop": _one(gs, "desktop", "desktop", "both"),
        "kdeLook": _one(gs, "kdelook", "kdeLook", "win11"),
        "kernel": _one(gs, "kernel", "kernel", "cachyos"),
        "kernelBuild": _one(gs, "kernelbuild", "kernelBuild", "ready"),
        "gpu": gpu,
        "player": _one(gs, "player", "player", "spotify"),
        "extras": extras,
        # на странице — только отключающие пункты: по умолчанию всё рекомендуемое включено
        "system": {"mitigationsOff": "mitigationsOff" in system, "virtualization": "noVirtualization" not in system,
                   "iommu": "noIommu" not in system},
        "boot": {"secureBoot": "secureboot" in _pick(gs, "security") and bool(hw.get("setupMode")), "windows": hw.get("windows", [])},
        "hardware": {"laptop": bool(hw.get("laptop")), "prime": hw.get("prime"),
                     "snapshots": bool(hw.get("snapshots")), "windowsDisks": hw.get("windowsDisks", [])},
    }


# ── железо ──
_PCI = re.compile(r"^(?:[0-9a-f]{4}:)?([0-9a-f]{2}):([0-9a-f]{2})\.([0-7]) (VGA compatible controller|3D controller|"
                  r"Display controller) \[03[0-9a-f]{2}\]: (.*)$", re.I | re.M)


def _gpus(lspci: str) -> list[tuple[str, str, int]]:
    """[(вендор, PCI:b:d:f, код устройства)] — по выводу `lspci -Dnn`."""
    out = []
    for m in _PCI.finditer(lspci):
        bus = f"PCI:{int(m.group(1), 16)}:{int(m.group(2), 16)}:{int(m.group(3))}"
        ids = re.search(r"\[([0-9a-f]{4}):([0-9a-f]{4})\]", m.group(5))
        vendor = {"10de": "nvidia", "8086": "intel", "1002": "amd"}.get(ids.group(1) if ids else "", "other")
        out.append((vendor, bus, int(ids.group(2), 16) if ids else 0))
    return out


# NVIDIA: открытые модули ядра (open = true) — только Turing (коды устройств с 0x1e00) и новее
TURING_FIRST_DEVICE = 0x1E00


def detect_gpu(lspci: str) -> str:
    nv = [dev for v, _, dev in _gpus(lspci) if v == "nvidia"]
    if not nv:
        return "mesa"
    return "nvidia" if max(nv) >= TURING_FIRST_DEVICE else "nvidia-legacy"


def detect_prime(lspci: str) -> dict | None:
    """Ноутбук/ПК с двумя видеокартами (встроенная + NVIDIA) → шины для PRIME, иначе None."""
    g = _gpus(lspci)
    nv = [b for v, b, _ in g if v == "nvidia"]
    igpu = [(v, b) for v, b, _ in g if v in ("intel", "amd")]
    if not nv or not igpu:
        return None
    v, b = igpu[0]
    return {("intelBusId" if v == "intel" else "amdgpuBusId"): b, "nvidiaBusId": nv[0]}


def _parts(lsblk: dict):
    for dev in lsblk.get("blockdevices", []):
        yield dev
        yield from _parts({"blockdevices": dev.get("children") or []})


def windows_disks(lsblk: dict) -> list[dict]:
    """Разделы NTFS (кроме служебного Recovery) → папки /mnt/<имя> (lsblk -J -o NAME,FSTYPE,UUID,LABEL)."""
    out, used = [], set()
    for p in _parts(lsblk):
        if p.get("fstype") != "ntfs" or not re.fullmatch(r"[0-9A-Fa-f]{16}", p.get("uuid") or ""):
            continue
        label = (p.get("label") or "").strip()
        if label.lower() in ("recovery", "восстановить", "winre", "system reserved", "зарезервировано системой"):
            continue
        name = label if re.fullmatch(r"[A-Za-z0-9_-]{1,32}", label) else f"Disk{len(out) + 1}"
        base, n = name, 2
        while name in used:
            name, n = f"{base}-{n}", n + 1
        used.add(name)
        out.append({"uuid": p["uuid"], "name": name})
    return out


def windows_esps(mounted: list[tuple[str, Path]]) -> list[dict]:
    """[(PARTUUID, где смонтирован раздел EFI)] → пункты Windows для загрузчика."""
    return [{"name": "Windows", "esp": partuuid.lower()} for partuuid, root in mounted
            if (Path(root) / "EFI/Microsoft/Boot/bootmgfw.efi").is_file()]


def is_btrfs_root(partitions: list[dict]) -> bool:
    return any(p.get("mountPoint") == "/" and p.get("fs") == "btrfs" for p in partitions)


# ── hardware-configuration.nix ──
_SUBVOLS = {"/home": "home", "/nix": "nix"}   # как в mount.conf Calamares (корень — верхний уровень btrfs)


def fix_hardware_config(text: str, partitions: list[dict]) -> str:
    """Диск LUKS открывается TPM2, если его привязали («Настройка системы»), иначе — паролем, как обычно;
    подтома btrfs — как их создал Calamares (nixos-generate-config пишет точки монтирования)."""
    for dev in re.findall(r'boot\.initrd\.luks\.devices\."([^"]+)"\.device = ', text):
        line = f'  boot.initrd.luks.devices."{dev}".crypttabExtraOpts = [ "tpm2-device=auto" ];'
        if line not in text:
            text = re.sub(rf'(boot\.initrd\.luks\.devices\."{re.escape(dev)}"\.device = [^;]*;\n)', rf"\g<1>{line}\n",
                          text, count=1)
    if is_btrfs_root(partitions):
        for mp, sub in _SUBVOLS.items():   # в пределах блока fileSystems."<точка>" = { … };
            text = re.sub(rf'fileSystems\."{re.escape(mp)}"\s*=\s*\{{.*?\}};',
                          lambda m: re.sub(r'"subvol=[^"]*"', f'"subvol={sub}"', m.group(0)), text, flags=re.S)
    return text


def offline_install(kernel_build: str, online: bool) -> bool:
    """Только из образа (без сети) — когда «готовое» и интернета нет. С интернетом то, чего нет в образе
    (например, драйвер старых NVIDIA), докачивается из кэша NixOS; «собрать» всегда с сетью."""
    return kernel_build == "ready" and not online


def failure_message(offline: bool) -> str:
    if offline:
        return ("Без интернета эту сборку поставить не удалось: для выбранного не всё есть на флешке. "
                "Подключите интернет (Wi‑Fi или кабель) и запустите установку снова — недостающее скачается само.")
    return "Установка не удалась — подробности в журнале (кнопка «Показать журнал»)."


def build_command(root: str, offline: bool) -> list[str]:
    """Собрать систему в хранилище живого образа: тяжёлое там уже есть, на месте — только своё (имя, файлы)."""
    cmd = ["nix", "--extra-experimental-features", "nix-command flakes", "build", "--no-link", "--print-out-paths",
           f"{root}/etc/nixos#nixosConfigurations.share.config.system.build.toplevel",
           "--log-format", "internal-json", "-v"]
    if offline:   # «готовое» без сети: только из образа
        cmd += ["--option", "substituters", ""]
    return cmd


def install_command(root: str, system: str) -> list[str]:
    """Готовую систему — на диск (nixos-install копирует замыкание, ставит загрузчик, активирует)."""
    return ["nixos-install", "--system", system, "--root", root, "--no-root-passwd", "--no-channel-copy"]
