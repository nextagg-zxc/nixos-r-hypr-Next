"""Жёсткие /home/<пользователь>/ в dotfiles → пути, работающие у любого пользователя.

bashrc: '/home/x/a' и "/home/x/a" → "$HOME/a";
ghostty: config-file = "/home/x/.config/ghostty/f" → config-file = f (относительно конфига).
"""
import re, sys

kind, path = sys.argv[1], sys.argv[2]
s = open(path, encoding="utf-8").read()
if kind == "bash":
    s = re.sub(r"'/home/[^/'\"]+/([^']*)'", r'"$HOME/\1"', s)
    s = re.sub(r"/home/[^/'\"\s]+/", "$HOME/", s)
elif kind == "ghostty":
    s = re.sub(r'config-file\s*=\s*"?/home/[^/]+/\.config/ghostty/([^"\n]+)"?', r"config-file = \1", s)
open(path, "w", encoding="utf-8").write(s)
