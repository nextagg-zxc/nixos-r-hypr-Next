#!/usr/bin/env python3
"""Убрать из плагинов и тем ссылки с именем upstream, не трогая работающий код.

  strip-upstream-links.py <dir>

  * README*.md — удаляются (это документация, в работе не участвуют);
  * остальные *.md (лицензии и т.п.) — такие ссылки заменяются на «(upstream)»;
  * manifest.json — поля homepage/repository/url с такой ссылкой становятся пустыми;
  * строки-комментарии (//, #, --, /*, *, <!--) — ссылка заменяется на «(upstream)».
  Ссылки в работающем коде (например @import url(...)) остаются как есть.
"""
import json
import os
import re
import sys

OLD = "om" + "archy"
URL = re.compile(r"https?://[^\s\"'<>)\]}`]*" + OLD + r"[^\s\"'<>)\]}`]*", re.I)
COMMENT = re.compile(r"^\s*(//|#|--|/\*|\*|<!--)")


def main(root):
    removed = rewritten = 0
    for dirpath, _, files in os.walk(root):
        for fn in files:
            p = os.path.join(dirpath, fn)
            if os.path.islink(p):
                continue
            if fn.lower().startswith("readme") and fn.lower().endswith(".md"):
                os.remove(p)
                removed += 1
                continue
            try:
                s = open(p, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            if OLD not in s.lower():
                continue
            if fn == "manifest.json":
                try:
                    d = json.loads(s)
                except ValueError:
                    continue
                for k in ("homepage", "repository", "url"):
                    if isinstance(d.get(k), str) and URL.search(d[k]):
                        d[k] = ""
                new = json.dumps(d, indent=2, ensure_ascii=False) + "\n"
            elif fn.lower().endswith(".md"):
                new = URL.sub("(upstream)", s)
            else:
                new = "".join(URL.sub("(upstream)", l) if COMMENT.match(l) else l
                              for l in s.splitlines(keepends=True))
            if new != s:
                mode = os.stat(p).st_mode
                with open(p, "w", encoding="utf-8") as f:
                    f.write(new)
                os.chmod(p, mode)
                rewritten += 1
    print(f"strip-upstream-links: {root}: {removed} README removed, {rewritten} files rewritten",
          file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        sys.exit(__doc__)
    main(sys.argv[1])
