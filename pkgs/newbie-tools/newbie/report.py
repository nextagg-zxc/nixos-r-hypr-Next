"""«Сообщить о проблеме»: журналы и сведения о компьютере одним архивом, без личного. Без GTK."""
from __future__ import annotations

import datetime
import getpass
import io
import json
import os
import subprocess
import tarfile
from pathlib import Path

from . import logic

COMMANDS = [
    ("journal-this-boot.txt", ["journalctl", "-b", "-p", "warning", "--no-pager", "-n", "3000"]),
    ("journal-previous-boot.txt", ["journalctl", "-b", "-1", "-p", "warning", "--no-pager", "-n", "2000"]),
    ("crashes.txt", ["coredumpctl", "list", "--no-pager"]),
    ("pci.txt", ["lspci", "-nnk"]),
    ("usb.txt", ["lsusb"]),
    ("system.txt", ["fastfetch", "--pipe", "--logo", "none"]),
    ("version.txt", ["nixos-version"]),
    ("disks.txt", ["lsblk", "-o", "NAME,SIZE,FSTYPE,MOUNTPOINT"]),
]


def collect_report(note: str, out_dir: Path) -> Path:
    user = getpass.getuser()
    try:
        ssids = subprocess.run(["nmcli", "-t", "-f", "NAME", "connection", "show"], capture_output=True,
                               text=True, timeout=10).stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        ssids = []
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    out = out_dir / f"problem-report-{stamp}.tar.gz"
    with tarfile.open(out, "w:gz") as tar:
        def add(name, text):
            data = logic.redact(text, user, ssids).encode()
            ti = tarfile.TarInfo(f"problem-report-{stamp}/{name}")
            ti.size = len(data)
            tar.addfile(ti, io.BytesIO(data))
        add("что-случилось.txt", note or "(не описано)")
        for name, cmd in COMMANDS:
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                add(name, r.stdout + r.stderr)
            except (OSError, subprocess.SubprocessError) as e:
                add(name, f"не удалось: {e}")
        choices = Path(os.environ.get("NIXOS_SHARE_ETC", "/etc/nixos")) / "hosts/share/choices.json"
        if choices.exists():
            c = json.loads(choices.read_text())
            c.get("user", {}).pop("passwordHash", None)
            add("choices.json", json.dumps(c, ensure_ascii=False, indent=1))
    return out


