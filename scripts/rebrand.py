#!/usr/bin/env python3
"""Rebrand the upstream desktop to NixOS for a whole directory tree, in place.

Used at build time (pkgs/nixos-desktop.nix, pkgs/look.nix, pkgs/owe.nix,
pkgs/desktop-fonts) and on sources in dotfiles/.

  rebrand.py <dir>      rewrite text files and rename paths under <dir>
  rebrand.py --text     filter stdin -> stdout (one string/file)

Rules:
  * URLs stay intact, so links keep working.
  * <upstream>-version -> nixos-desktop-version (NixOS already has nixos-version).
  * upper/Capitalized/lower upstream name -> NIXOS / NixOS / nixos (code, paths, text).
  * Symlink targets are rewritten too; binary files are left alone.
"""
import os
import re
import sys

URL_RE = re.compile(r"https?://[^\s\"'<>)\]}`]*")
OLD = "om" + "archy"  # upstream name, spelled in parts
VERSION_RE = re.compile(OLD + r"-version(?![-\w])")
CASES = [(OLD.upper(), "NIXOS"), (OLD.capitalize(), "NixOS"), (OLD, "nixos")]


def rename_text(s: str) -> str:
    keep = []

    def stash(m):
        keep.append(m.group(0))
        return f"\x00{len(keep) - 1}\x00"

    s = URL_RE.sub(stash, s)
    s = VERSION_RE.sub("nixos-desktop-version", s)
    for a, b in CASES:
        s = s.replace(a, b)
    return re.sub(r"\x00(\d+)\x00", lambda m: keep[int(m.group(1))], s)


def rename_name(name: str) -> str:
    if name == OLD + "-version":
        return "nixos-desktop-version"
    for a, b in CASES:
        name = name.replace(a, b)
    return name


def is_text(data: bytes) -> bool:
    if b"\x00" in data[:8192]:
        return False
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def process_tree(root: str) -> None:
    changed = renamed = 0
    # bottom-up so renaming a directory does not invalidate paths below it
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            if os.path.islink(p):
                t = os.readlink(p)
                nt = rename_text(t)
                if nt != t:
                    os.unlink(p)
                    os.symlink(nt, p)
                    changed += 1
            else:
                with open(p, "rb") as f:
                    data = f.read()
                if b"marchy" in data or b"MARCHY" in data:
                    if is_text(data):
                        new = rename_text(data.decode("utf-8")).encode("utf-8")
                        if new != data:
                            mode = os.stat(p).st_mode
                            with open(p, "wb") as f:
                                f.write(new)
                            os.chmod(p, mode)
                            changed += 1
            nn = rename_name(fn)
            if nn != fn:
                q = os.path.join(dirpath, nn)
                if os.path.lexists(q):
                    raise SystemExit(f"rename collision: {p} -> {q}")
                os.rename(p, q)
                renamed += 1
        for dn in dirnames:
            p = os.path.join(dirpath, dn)
            if os.path.islink(p):
                t = os.readlink(p)
                nt = rename_text(t)
                if nt != t:
                    os.unlink(p)
                    os.symlink(nt, p)
                    changed += 1
            nn = rename_name(dn)
            if nn != dn:
                q = os.path.join(dirpath, nn)
                if os.path.lexists(q):
                    raise SystemExit(f"rename collision: {p} -> {q}")
                os.rename(p, q)
                renamed += 1
    print(f"rebrand: {root}: {changed} files rewritten, {renamed} paths renamed",
          file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--text":
        sys.stdout.write(rename_text(sys.stdin.read()))
    elif len(sys.argv) == 2 and os.path.isdir(sys.argv[1]):
        process_tree(sys.argv[1])
    else:
        sys.exit(__doc__)
