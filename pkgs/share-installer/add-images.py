"""Картинки страниц выбора: снимок рабочего стола (@файл из images/) или значок Papirus → PNG.
python3 add-images.py <папка conf> <images> <куда класть png> <Papirus 64x64/apps>"""
import json
import re
import subprocess
import sys
from pathlib import Path

confs, images, out, papirus = map(Path, sys.argv[1:5])
out.mkdir(parents=True, exist_ok=True)
for page, items in json.loads((images / "icons.json").read_text()).items():
    conf = confs / f"packagechooser-{page}.conf"
    text = conf.read_text()
    for item, src in items.items():
        if src.startswith("@") and (images / src[1:]).exists():
            dst = out / src[1:]
            dst.write_bytes((images / src[1:]).read_bytes())
        else:
            icon = "preferences-desktop-theme" if src.startswith("@") else src
            dst = out / f"{page}-{item or 'none'}.png"
            subprocess.run(["rsvg-convert", "-w", "256", "-h", "256", "-o", str(dst), str(papirus / f"{icon}.svg")],
                           check=True)
        idtext = re.escape(item) if item else '""'   # пустой id — «ничего не выбрано»
        text, n = re.subn(rf'(\n    - id: {idtext}\n)', rf'\1      screenshot: "{dst}"\n', text)
        assert n == 1, (page, item)
    conf.write_text(text)
