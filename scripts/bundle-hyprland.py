#!/usr/bin/env python3
"""Build one self-contained hyprland.lua from the desktop defaults and the
personal modules.

  bundle-hyprland.py <defaults-hypr-dir> <user-hypr-dir> <out-file>

<defaults-hypr-dir>  /usr/share/nixos/default/hypr (module prefix default.hypr)
<user-hypr-dir>      ~/.config/hypr: hyprland.lua (main) + personal modules

Every module becomes package.preload["name"] = function(...) <code> end, so
require() finds the code in this file and behaves exactly as before. Kept as
separate files on purpose (written by programs, not by hand):
  * hypr/gui-settings.lua   - written by Hypr Settings ("Apply")
  * ~/.local/state/nixos/... - theme, toggle flags, workspace layouts
"""
import os
import re
import sys

KEEP_EXTERNAL = {"gui-settings"}  # personal files loaded from disk if present


def module_files(root, prefix):
    out = []
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".lua"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), root)[:-4]
            out.append((prefix + "." + rel.replace(os.sep, ".") if prefix else rel,
                        os.path.join(dirpath, fn)))
    return sorted(out)


COMMENTED_REQUIRE = re.compile(r'^(\s*--.*?)require\("', re.M)


def preload(name, path, label):
    code = open(path, encoding="utf-8").read().rstrip("\n")
    # Commented-out require("...") lines inside inlined modules get a space
    # (require ("...")): the Rounded Corner Blur plugin un-comments any line
    # matching `-- require("hypr.appearance")` in hyprland.lua, which would
    # make the inlined appearance module require itself (C stack overflow).
    code = COMMENTED_REQUIRE.sub(r'\1require ("', code)
    bar = "-" * 76
    return (f"-- {bar}\n-- {label}\n-- {bar}\n"
            f'package.preload["{name}"] = function(...)\n{code}\nend\n')


def main(defaults, user, out):
    main_src = open(os.path.join(user, "hyprland.lua"), encoding="utf-8").read()
    boot = open(os.path.join(defaults, "bootstrap.lua"), encoding="utf-8").read().rstrip("\n")

    # drop the bootstrap dofile line from the main file: it is inlined below
    main_lines = [l for l in main_src.splitlines()
                  if not re.match(r'\s*dofile\(.*default/hypr/bootstrap\.lua"\)\s*$', l)]
    # gui-settings stays a separate generated file
    main_body = "\n".join(main_lines).replace(
        'require("hypr.gui-settings")',
        'pcall(require, "hypr.gui-settings")')

    personal = []
    for fn in sorted(os.listdir(user)):
        if not fn.endswith(".lua") or fn == "hyprland.lua":
            continue
        name = fn[:-4]
        if name in KEEP_EXTERNAL:
            continue
        # personal modules are required as "hypr.<name>"; media-toggle as is
        mod = name if re.search(rf'require\("{re.escape(name)}"\)', main_src) else "hypr." + name
        personal.append((mod, os.path.join(user, fn)))

    parts = [
        "-- " + "=" * 76,
        "-- Hyprland: the whole configuration in one file.",
        "--",
        "-- Sections:",
        "--   1. Module path and reload handling",
        "--   2. Desktop defaults (window rules, bindings, look, toggles, ...)",
        "--   3. Personal modules (monitors, input, bindings, look and feel, ...)",
        "--   4. Main: what is loaded and in which order",
        "--",
        "-- Each module is a package.preload entry, so require() takes it from this",
        "-- file. Separate on purpose (written by programs): hypr/gui-settings.lua",
        "-- (Hypr Settings) and ~/.local/state/nixos (theme, toggles, layouts).",
        "-- Display scale changes from the menu are written into section 3 (monitors).",
        "-- " + "=" * 76,
        "",
        "-- " + "=" * 76,
        "-- 1. Module path and reload handling",
        "-- " + "=" * 76,
        boot,
        "",
        "-- " + "=" * 76,
        "-- 2. Desktop defaults",
        "-- " + "=" * 76,
    ]
    for mod, path in module_files(defaults, "default.hypr"):
        if mod == "default.hypr.bootstrap":
            continue
        parts.append(preload(mod, path, mod))
    parts += ["-- " + "=" * 76, "-- 3. Personal modules", "-- " + "=" * 76]
    for mod, path in personal:
        parts.append(preload(mod, path, mod))
    parts += ["-- " + "=" * 76, "-- 4. Main", "-- " + "=" * 76, main_body.strip("\n"), ""]
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"bundle-hyprland: {out}: {len(personal)} personal + "
          f"{len(module_files(defaults, 'default.hypr')) - 1} default modules", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
