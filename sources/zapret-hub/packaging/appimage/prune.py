"""Trim PySide6-Essentials to what Zapret Hub loads: the Python modules it
imports, the Qt plugins a desktop needs, and the Qt libraries those pull in
(followed through ELF NEEDED with readelf). Usage: prune.py <site-packages>"""

import os
import re
import shutil
import subprocess
import sys

MODULES = ["QtCore", "QtGui", "QtWidgets", "QtSvg", "QtNetwork"]
PLUGIN_DIRS = ["platforms", "platforminputcontexts", "platformthemes", "imageformats", "iconengines",
               "xcbglintegrations", "wayland-shell-integration", "wayland-decoration-client",
               "wayland-graphics-integration-client"]
PLATFORMS = re.compile(r"libq(xcb|wayland|offscreen)")
KEEP_TOP = {"__init__.py", "_config.py", "_git_pyside_version.py", "support", "Qt", "py.typed"}


def needed(path):
    out = subprocess.run(["readelf", "-d", path], capture_output=True, text=True).stdout
    return re.findall(r"\(NEEDED\)\s+Shared library: \[(.+?)\]", out)


def main(site):
    pyside = os.path.join(site, "PySide6")
    qt = os.path.join(pyside, "Qt")
    lib = os.path.join(qt, "lib")
    plugins = os.path.join(qt, "plugins")

    for name in os.listdir(plugins):
        if name not in PLUGIN_DIRS:
            shutil.rmtree(os.path.join(plugins, name))
    for name in os.listdir(os.path.join(plugins, "platforms")):
        if not PLATFORMS.match(name):
            os.remove(os.path.join(plugins, "platforms", name))

    roots = []
    for name in os.listdir(pyside):
        p = os.path.join(pyside, name)
        mod = name.split(".")[0]
        if mod in MODULES and name.endswith(".so") or name.startswith("libpyside6"):
            roots.append(p)
        elif name in KEEP_TOP or mod in MODULES:
            continue
        elif os.path.isdir(p):
            shutil.rmtree(p)
        else:
            os.remove(p)
    for d, _, names in os.walk(plugins):
        roots += [os.path.join(d, n) for n in names if n.endswith(".so")]

    libs = set(os.listdir(lib))
    keep, todo = set(), list(roots)
    while todo:
        for so in needed(todo.pop()):
            if so in libs and so not in keep:
                keep.add(so)
                todo.append(os.path.join(lib, so))
    for name in libs - keep:
        if not name.startswith("libxcb"):
            os.remove(os.path.join(lib, name))
    for name in os.listdir(qt):
        if name not in ("lib", "plugins"):
            p = os.path.join(qt, name)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    for name in ("pip", "build", "pyproject_hooks", "packaging", "certifi", "sitecustomize.py", "README.txt"):
        for p in [os.path.join(site, name)] + [os.path.join(site, n) for n in os.listdir(site)
                                               if n.startswith(name + "-") and n.endswith(".dist-info")]:
            if os.path.isdir(p):
                shutil.rmtree(p)
            elif os.path.exists(p):
                os.remove(p)
    print(f"Qt libraries kept: {len(keep)} of {len(libs)}")


if __name__ == "__main__":
    main(sys.argv[1])
