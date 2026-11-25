"""Установка раздаваемой системы на смонтированный корень: флейк в /etc/nixos, железо, choices.json,
nixos-install. Общая часть для модуля Calamares (main.py) и для запуска без окна:

    nixos-share-install --answers ответы.json --root /mnt [--partitions разделы.json]

ответы.json — те же ключи, что в глобальном хранилище Calamares (username, packagechooser_kernel, …).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from . import logic

FLAKE = os.environ.get("NIXOS_SHARE_FLAKE_SRC", "@flake@")      # экспорт флейка в хранилище образа
ESP_TYPE = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"


def _out(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def online() -> bool:
    import socket
    try:
        socket.create_connection(("cache.nixos.org", 443), timeout=5).close()
        return True
    except OSError:
        return False


def setup_mode() -> bool:
    """Прошивка в Setup Mode — ключи Secure Boot можно записать сразу при установке."""
    for f in Path("/sys/firmware/efi/efivars").glob("SetupMode-*"):
        try:
            return f.read_bytes()[-1:] == b"\x01"
        except OSError:
            return False
    return False


def detect_hardware(partitions: list[dict], log=print) -> dict:
    lspci = _out(["lspci", "-Dnn"])
    lsblk = json.loads(_out(["lsblk", "-J", "-o", "NAME,FSTYPE,UUID,LABEL,PARTUUID,PARTTYPE,PATH,MOUNTPOINT"])
                       or '{"blockdevices": []}')
    esps = []
    for p in logic._parts(lsblk):
        if (p.get("parttype") or "").lower() != ESP_TYPE or not p.get("partuuid") or p.get("mountpoint"):
            continue
        d = tempfile.mkdtemp(prefix="esp-")
        if subprocess.run(["mount", "-o", "ro", p["path"], d], capture_output=True).returncode == 0:
            try:
                esps += logic.windows_esps([(p["partuuid"], Path(d))])
            finally:
                subprocess.run(["umount", d], capture_output=True)
        os.rmdir(d)
    hw = {
        "gpu": logic.detect_gpu(lspci),
        "prime": logic.detect_prime(lspci),
        "laptop": any(Path("/sys/class/power_supply").glob("BAT*")),
        "snapshots": logic.is_btrfs_root(partitions),
        "windowsDisks": logic.windows_disks(lsblk),
        "windows": esps[:1],
        "setupMode": setup_mode(),
    }
    log(f"железо: {json.dumps(hw, ensure_ascii=False)}")
    return hw


def copy_flake(root: Path):
    dest = root / "etc/nixos"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(FLAKE, dest, symlinks=True)
    for dirpath, dirs, files in os.walk(dest):   # из хранилища всё только для чтения
        for x in dirs + files:
            p = Path(dirpath) / x
            if not p.is_symlink():
                p.chmod(p.stat().st_mode | 0o200)


def hardware_config(root: Path, partitions: list[dict]):
    text = subprocess.run(["nixos-generate-config", "--root", str(root), "--show-hardware-config"],
                          capture_output=True, text=True, check=True).stdout
    (root / "etc/nixos/hosts/share/hardware-configuration.nix").write_text(
        logic.fix_hardware_config(text, partitions), encoding="utf-8")


def _run(cmd: list[str], log, progress, progress_parser) -> tuple[bool, list[str]]:
    log("$ " + " ".join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    out = []

    def err_reader():
        for line in proc.stderr:
            line = line.rstrip("\n")
            if progress_parser and progress_parser.handle(line):
                progress(progress_parser.fraction)
                for m in progress_parser.log_messages:
                    log(m)
                progress_parser.log_messages.clear()
            else:
                log(line)
    import threading
    t = threading.Thread(target=err_reader, daemon=True)
    t.start()
    for line in proc.stdout:
        out.append(line.rstrip("\n"))
        log(out[-1])
    t.join()
    return proc.wait() == 0, out


def run_install(root: Path, offline: bool, progress=lambda f: None, log=print, progress_parser=None) -> bool:
    ok, out = _run(logic.build_command(str(root), offline), log, lambda f: progress(0.8 * f), progress_parser)
    system = next((l for l in reversed(out) if l.startswith("/nix/store/")), None)
    if not ok or not system:
        return False
    log("Копирую систему на диск и ставлю загрузчик…")
    ok, _ = _run(logic.install_command(str(root), system), log, lambda f: None, None)
    progress(1.0)
    return ok


def place_store_index(root: Path):
    """Готовый список программ Магазина (построен при сборке образа) → /var/lib/nixos-store новой системы."""
    src = Path(root) / "etc/nixos/.store-index.json"
    if not src.exists():
        return
    d = Path(root) / "var/lib/nixos-store"
    d.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), d / "index.json")
    marker = Path(root) / "etc/nixos/.store-index.source"
    if marker.exists():
        shutil.move(str(marker), d / "source")
    for f in d.iterdir():
        f.chmod(0o644)


def install(gs: dict, root: str, partitions: list[dict], progress=lambda f: None, log=print,
            progress_parser=None) -> str | None:
    """None — получилось, иначе текст ошибки для окна."""
    root = Path(root)
    progress(0.02)
    log("Копирую настройки системы в /etc/nixos…")
    copy_flake(root)
    hw = detect_hardware(partitions, log)
    try:
        choices = logic.choices_from_answers(gs, hw)
    except ValueError as e:
        return str(e)
    share = root / "etc/nixos/hosts/share"
    (share / "choices.json").write_text(json.dumps(choices, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        hardware_config(root, partitions)
    except subprocess.CalledProcessError as e:
        return f"nixos-generate-config: {e.stderr[-500:]}"
    progress(0.05)
    native = choices["kernelBuild"] == "native"
    offline = logic.offline_install(choices["kernelBuild"], online())
    log("Устанавливаю систему (" + ("сборка ядра на этом компьютере — это долго" if native else
                                    "без интернета" if offline else "недостающее — из интернета") + ")…")
    if not run_install(root, offline=offline, progress=lambda f: progress(0.05 + 0.9 * f), log=log,
                       progress_parser=progress_parser):
        return logic.failure_message(offline)
    if native:
        # тулчейн и промежуточные файлы сборки ядра/драйвера больше не нужны
        log("Убираю файлы сборки…")
        subprocess.run(["nixos-enter", "--root", str(root), "--", "nix-collect-garbage"], capture_output=True)
    place_store_index(root)
    progress(1.0)
    return None


def main(argv: list[str]) -> int:
    if "--answers" not in argv or "--root" not in argv:
        print(__doc__, file=sys.stderr)
        return 2
    gs = json.loads(Path(argv[argv.index("--answers") + 1]).read_text(encoding="utf-8"))
    parts = json.loads(Path(argv[argv.index("--partitions") + 1]).read_text()) if "--partitions" in argv else []
    err = install(gs, argv[argv.index("--root") + 1], parts, log=lambda m: print(m, flush=True))
    if err:
        print(f"ОШИБКА: {err}", file=sys.stderr)
        return 1
    print("УСТАНОВЛЕНО", flush=True)
    return 0
