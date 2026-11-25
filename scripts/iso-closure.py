#!/usr/bin/env python3
"""Что положить в хранилище ISO, чтобы «готовая» установка шла без интернета.

    python3 scripts/iso-closure.py <экспорт флейка> <выход.json>

1. Собирает готовые варианты системы из экспорта (ядра × видеодрайверы, оба плеера, все дополнения) —
   тяжёлое (ядра, драйверы, программы) у друга не собирается.
2. Для «проб» (другое имя, железо, выбор — как у реального друга) смотрит граф сборки: какие производные
   пришлось бы собрать на месте и что им нужно на входе (исходники, инструменты сборки). Нужное, чего нет в
   вариантах, тоже кладётся в образ; загрузки (fixed-output) на месте недопустимы — их выходы тоже в образ.
3. Плюс исходники входов флейка (nixpkgs и др.) — чтобы вычислить конфигурацию без сети.
"""
from __future__ import annotations

import json  # noqa: I001
import subprocess
import sys
from pathlib import Path

BASE = {"user": {"name": "user", "fullName": "Пользователь"}, "desktop": "both", "kernelBuild": "ready",
        "extras": ["gaming", "obs", "telegram", "vr", "autologin"],
        "system": {"mitigationsOff": False, "virtualization": True, "iommu": True},
        "hardware": {"laptop": True, "snapshots": True, "prime": None,
                     "windowsDisks": [{"uuid": "01D9A1B2C3D4E5F6", "name": "Windows"}]}}
VARIANTS = [
    dict(BASE, kernel="cachyos", gpu="mesa", player="spotify"),
    dict(BASE, kernel="cachyos", gpu="nvidia", player="soundcloud"),
    dict(BASE, kernel="zen", gpu="nvidia", player="spotify"),
    dict(BASE, kernel="linux", gpu="nvidia", player="soundcloud"),
    # старые NVIDIA (GTX 900/1000) — не в образе (≈0,5 ГиБ сжатыми, образ не влезал в 7,4 ГиБ):
    # их драйвер установщик докачивает из кэша NixOS, если есть интернет
]
# пробы: как у друзей — своё имя, своё железо (initrd, диски), разные выборы
PROBE_HW = '''{ lib, ... }: {
  boot.initrd.availableKernelModules = [ "nvme" "xhci_pci" "ahci" "usbhid" "usb_storage" "sd_mod" "rtsx_pci_sdmmc" ];
  boot.kernelModules = [ "kvm-amd" ];
  boot.initrd.luks.devices."luks-probe" = { device = "/dev/disk/by-uuid/00000000-0000-0000-0000-000000000001";
    crypttabExtraOpts = [ "tpm2-device=auto" ]; };
  fileSystems."/" = lib.mkForce { device = "/dev/mapper/luks-probe"; fsType = "btrfs"; };
  fileSystems."/home" = { device = "/dev/mapper/luks-probe"; fsType = "btrfs"; options = [ "subvol=home" ]; };
  fileSystems."/boot" = lib.mkForce { device = "/dev/disk/by-uuid/ABCD-1234"; fsType = "vfat"; options = [ "fmask=0077" "dmask=0077" ]; };
  swapDevices = [ ];
  hardware.cpu.amd.updateMicrocode = true;
}'''
PROBES = [
    {"user": {"name": "vasya", "fullName": "Вася"}, "hostname": "vasya-pc", "timezone": "Europe/Berlin",
     "keyboard": ["us", "de"], "desktop": "hyprland", "kdeLook": "win10", "kernel": "zen", "kernelBuild": "ready",
     "gpu": "mesa", "player": "soundcloud", "extras": [], "locale": "de_DE.UTF-8",
     "system": {"mitigationsOff": True, "virtualization": False, "iommu": False},
     "hardware": {"laptop": True, "snapshots": True, "prime": None,
                  "windowsDisks": [{"uuid": "01D9A1B2C3D4E5F6", "name": "Games"}]},
     "boot": {"secureBoot": False, "windows": [{"name": "Windows", "esp": "0f1e2d3c-aaaa-bbbb-cccc-0123456789ab"}]}},
    {"user": {"name": "petya", "fullName": "Петя"}, "desktop": "kde", "kdeLook": "win11", "kernel": "cachyos",
     "kernelBuild": "ready", "gpu": "nvidia", "player": "spotify", "extras": ["autologin", "gaming"],
     "hardware": {"laptop": True, "snapshots": False,
                  "prime": {"intelBusId": "PCI:0:2:0", "nvidiaBusId": "PCI:1:0:0"}, "windowsDisks": []}},
    {"user": {"name": "kolya", "fullName": "Коля"}, "desktop": "both", "kernel": "linux", "kernelBuild": "ready",
     "gpu": "nvidia", "player": "soundcloud", "extras": ["obs", "telegram", "vr"],
     "boot": {"secureBoot": True, "windows": []}},
    # остальные сочетания «рабочий стол × видеодрайвер × ядро» и наборы дополнений (steam FHS зависит от них)
    {"user": {"name": "dima", "fullName": "Дима"}, "desktop": "kde", "kdeLook": "win11", "kernel": "zen",
     "kernelBuild": "ready", "gpu": "mesa", "player": "soundcloud", "extras": ["gaming", "autologin"],
     "hardware": {"laptop": False, "snapshots": True, "prime": None, "windowsDisks": []}},
    {"user": {"name": "sasha", "fullName": "Саша"}, "desktop": "hyprland", "kernel": "linux", "kernelBuild": "ready",
     "gpu": "nvidia", "player": "spotify", "extras": ["vr"]},
    {"user": {"name": "lena", "fullName": "Лена"}, "desktop": "both", "kernel": "cachyos", "kernelBuild": "ready",
     "gpu": "mesa", "player": "spotify", "extras": ["telegram", "obs"]},
]


# сборные производные, которые у друга почти всегда пересобираются под его выбор (набор программ, initrd,
# модули ядра, steam FHS, файлы home-manager): их сборочные входы должны быть в образе, даже если сама сборка
# у нас уже есть (иначе вход вроде getconf-glibc или net.conf не попадёт в образ — он не в замыкании системы)
import re  # noqa: E402
AGGREGATE = re.compile(r"^[a-z0-9]{32}-(system-path|etc|initrd-|linux-.*-modules(-shrunk)?|steam-.*fhsenv|steam-run|"
                       r"steam-[0-9.]+|home-manager-|hm_|users-groups|unit-|X-R|nixos-system|activat|dbus-1|"
                       r"system-units|user-units|udev-rules|kernel-modules|firmware|sane-config|fontconfig)")


# варианты с «железом друга» (LUKS + btrfs, AMD): в образ попадают initrd с cryptsetup и т. п.
HW_VARIANTS = {0, 2}


def expr(flake: Path, choices: dict, probe: bool) -> str:
    extra = f"(import {probe_file})" if probe else "{ }"
    return (f'let f = builtins.getFlake "path:{flake}"; lib = f.inputs.nixpkgs.lib; in '
            f'(f.lib.mkShareHost [ (f + "/hosts/share") {extra} '
            f'{{ nextagg.share.choices = lib.mkForce (builtins.fromJSON {json.dumps(json.dumps(choices))}); }} ]'
            f').config.system.build.toplevel')


def nix(*args: str) -> str:
    r = subprocess.run(["nix", *args], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"nix {' '.join(args[:3])}…: {r.stderr[-2000:]}")
    return r.stdout.strip()


def sp(p: str) -> str:
    return p if p.startswith("/nix/store/") else f"/nix/store/{p}"


def closure(paths: list[str]) -> set[str]:
    out = subprocess.run(["nix-store", "-qR", *paths], capture_output=True, text=True, check=True).stdout
    return set(out.split())


def main(argv: list[str]) -> int:
    global probe_file
    flake, out = Path(argv[0]).resolve(), Path(argv[1])
    probe_file = out.parent / "iso-probe-hw.nix"
    probe_file.write_text(PROBE_HW)
    tops = []
    from concurrent.futures import ThreadPoolExecutor   # вычисление Nix однопоточное — варианты и пробы параллельно
    import os
    # «не грузить ПК» (NIX_CONFIG с max-jobs = 1, например во время игры) — по одному
    workers = int(os.environ.get("ISO_CLOSURE_JOBS") or (1 if "max-jobs = 1" in os.environ.get("NIX_CONFIG", "") else 8))

    def build_variant(iv):
        i, v = iv
        print(f"вариант: {v['kernel']} + {v['gpu']} + {v['player']}", flush=True)
        return nix("build", "--impure", "--no-link", "--print-out-paths", "--expr", expr(flake, v, i in HW_VARIANTS))
    with ThreadPoolExecutor(workers) as ex:
        tops += list(ex.map(build_variant, enumerate(VARIANTS)))
    have = closure(tops)
    print(f"вариантов: {len(tops)}, путей: {len(have)}", flush=True)

    need: set[str] = set()
    to_realise: set[str] = set()
    def prepare(p):
        # собрать пробу у себя: всё общее (не зависящее от имени друга) окажется готовым и ляжет в образ;
        # смотреть — ту же пробу с другим именем: что разошлось, то друг соберёт на месте (только своё)
        nix("build", "--impure", "--no-link", "--expr", expr(flake, p, True))
        p = dict(p, user={"name": p["user"]["name"] + "x", "fullName": "Другой"}, hostname="other-pc")
        drv = nix("eval", "--impure", "--raw", "--expr", expr(flake, p, True) + ".drvPath")
        shown = json.loads(nix("derivation", "show", "-r", drv))
        shown = shown.get("derivations", shown)   # Nix ≥ 2.32: {"derivations": …, "version": …}
        return p, drv, {sp(k): v for k, v in shown.items()}
    with ThreadPoolExecutor(workers) as ex:
        prepared = list(ex.map(prepare, PROBES))
    for p, drv, graph in prepared:
        built: set[str] = set()

        def outs(d: str, names) -> list[str]:
            o = graph[d]["outputs"]
            return [sp(o[n]["path"]) for n in names if o.get(n, {}).get("path")]

        def visit(d: str, names):
            o = outs(d, names)
            if all(x in have for x in o) or d in built:
                return
            if o and all(Path(x).exists() for x in o) and not AGGREGATE.match(Path(d).name):
                # уже собрано (у нас) и не зависит от выбора друга: кладём готовым, на месте не собирать
                need.update(o)
                return
            built.add(d)
            info = graph[d]
            fixed = any("hash" in o or "method" in o for o in info["outputs"].values()) or "outputHash" in info.get("env", {})
            if fixed:   # загрузка — на месте без сети нельзя: кладём готовый результат
                to_realise.add(d)
                need.update(outs(d, info["outputs"].keys()))
                return
            inputs = info.get("inputs") or {}
            need.update(sp(s) for s in inputs.get("srcs", info.get("inputSrcs", [])))
            for idrv, spec in inputs.get("drvs", info.get("inputDrvs", {})).items():
                idrv = sp(idrv)
                inames = spec["outputs"] if isinstance(spec, dict) else spec
                if all(x in have for x in outs(idrv, inames)):
                    continue
                visit(idrv, inames)

        visit(sp(drv), ["out"])
        print(f"проба {p['user']['name']}: собрать на месте {len(built)} производных", flush=True)
        (out.parent / f"probe-{p['user']['name']}.txt").write_text("\n".join(sorted(built)) + "\n")
    if to_realise:
        subprocess.run(["nix-store", "-r", *sorted(to_realise)], check=True, capture_output=True)
    # входы флейка: исходники для вычисления без сети
    archive = json.loads(nix("flake", "archive", "--json", "--no-write-lock-file", f"path:{flake}"))

    def walk(node):
        if node.get("path"):   # у относительных входов (./sources) пути нет — они внутри флейка
            yield node["path"]
        for sub in node.get("inputs", {}).values():
            yield from walk(sub)
    inputs = set(walk(archive)) - {archive["path"]}
    extra = closure(sorted(need | inputs)) - have
    print(f"сборочных и исходников: {len(extra)} путей", flush=True)
    out.write_text(json.dumps(sorted(set(tops) | extra), indent=0) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
