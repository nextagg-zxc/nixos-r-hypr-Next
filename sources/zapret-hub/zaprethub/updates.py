"""Flowseal releases: version check, download, unpack, convert strategies,
lay out lists. Shared by the Windows backend and the Linux root helper."""

import json
import os
import re
import shutil
import tempfile
import urllib.request
import zipfile

from . import config, core

UA = "zapret-hub"


def http_get(u, accept=None, timeout=30):
    headers = {"User-Agent": UA, "Cache-Control": "no-cache"}
    if accept:
        headers["Accept"] = accept
    return urllib.request.urlopen(urllib.request.Request(config.mirror(u), headers=headers), timeout=timeout)


def version_tuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v or ""))


def version_gt(a, b):
    """a newer than b ('v' prefixes and missing b allowed)."""
    return version_tuple(a) > version_tuple(b)


def flowseal_remote_version(timeout=8):
    with http_get(config.url("flowseal_version"), timeout=timeout) as r:
        v = r.read(64).decode("utf-8", "replace").strip()
    if not re.fullmatch(r"v?\d+(\.\d+)*", v):
        raise RuntimeError(f"странный ответ сервера версий: {v[:30]!r}")
    return v


def flowseal_zip_url(v):
    return f"https://github.com/Flowseal/zapret-discord-youtube/releases/download/{v}/zapret-discord-youtube-{v}.zip"


def flowseal_release():
    """(tag, zip url). Falls back to version.txt when the GitHub API refuses
    (60 requests/hour without a token is easy to hit behind a shared NAT)."""
    try:
        with http_get(config.url("flowseal_api"), "application/vnd.github+json", timeout=15) as r:
            rel = json.load(r)
        asset = next(a for a in rel["assets"] if a["name"].endswith(".zip"))
        return rel["tag_name"], config.mirror(asset["browser_download_url"])
    except Exception:  # noqa: BLE001
        v = flowseal_remote_version()
        return v, config.mirror(flowseal_zip_url(v))


def download(u, dest, progress=None):
    with http_get(u, timeout=60) as r, open(dest, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while chunk := r.read(256 * 1024):
            f.write(chunk)
            done += len(chunk)
            if progress and total:
                progress(done / total)


# ---------------------------------------------------------------- files

def write_file(path, text, mode=0o644):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.chmod(tmp, mode)
    os.replace(tmp, path)


def swap_dir(new, target):
    old = target + ".old"
    shutil.rmtree(old, ignore_errors=True)
    if os.path.exists(target):
        os.rename(target, old)
    os.rename(new, target)
    shutil.rmtree(old, ignore_errors=True)


def strip_top(root):
    entries = os.listdir(root)
    if len(entries) == 1 and os.path.isdir(os.path.join(root, entries[0])):
        return os.path.join(root, entries[0])
    return root


LINUX_KEEP = (".bin", ".txt", ".bat", ".backup", ".enabled")


def install_flowseal(dest_dir, log, windows=None, release=flowseal_release, download=download, progress=None):
    """Download the latest Flowseal release into dest_dir, replacing it only
    once everything is unpacked. Returns the tag. Raises RuntimeError with a
    readable message; the old dest_dir is untouched on failure."""
    windows = config.IS_WINDOWS if windows is None else windows
    parent = os.path.dirname(os.path.abspath(dest_dir))
    os.makedirs(parent, exist_ok=True)
    work = tempfile.mkdtemp(dir=parent, prefix=".dl-")
    try:
        try:
            log("Узнаю последнюю версию Flowseal…")
            tag, u = release()
            log(f"Скачиваю Flowseal {tag}…")
            zpath = os.path.join(work, "flowseal.zip")
            download(u, zpath, progress)
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"Не удалось скачать Flowseal: {e}. Проверь интернет и попробуй ещё раз.") from e
        ex = os.path.join(work, "x")
        os.mkdir(ex)
        try:
            with zipfile.ZipFile(zpath) as z:
                for m in z.infolist():
                    name = m.filename.replace("\\", "/")
                    if ".." in name.split("/") or name.startswith("/"):
                        continue
                    if not windows and not m.is_dir() and not name.endswith(LINUX_KEEP):
                        continue
                    z.extract(m, ex)
        except zipfile.BadZipFile as e:
            raise RuntimeError("Скачанный архив Flowseal повреждён — попробуй ещё раз.") from e
        src = strip_top(ex)
        if not any(fn.startswith("general") and fn.endswith(".bat") for fn in os.listdir(src)):
            raise RuntimeError("В архиве Flowseal нет стратегий general*.bat — формат релиза изменился.")
        if not windows:
            for root, dirs, files in os.walk(src):
                os.chmod(root, 0o755)
                for fn in files:
                    os.chmod(os.path.join(root, fn), 0o644)
        swap_dir(src, dest_dir)
        return tag
    finally:
        shutil.rmtree(work, ignore_errors=True)


def convert_builtin(flowseal_dir, builtin_dir, log):
    new = builtin_dir + ".new"
    shutil.rmtree(new, ignore_errors=True)
    os.makedirs(new)
    n = 0
    for fn in sorted(os.listdir(flowseal_dir)):
        if not (fn.startswith("general") and fn.endswith(".bat")):
            continue
        name = fn[:-4]
        try:
            with open(os.path.join(flowseal_dir, fn), encoding="utf-8", errors="replace") as f:
                text = core.bat_to_strategy(f.read(), f"{name} (Flowseal)")
            core.build(text, "all", "/b", "/l")   # catches unknown %VARS% now, not at start
        except ValueError as e:
            log(f"Пропускаю {fn}: {e}")
            continue
        write_file(os.path.join(new, name + ".txt"), text)
        n += 1
    swap_dir(new, builtin_dir)
    log(f"Стратегий Flowseal: {n}")
    return n


def apply_ipset_mode(lists_dir, mode, ipset_full):
    p = os.path.join(lists_dir, "ipset-all.txt")
    if mode == "any":
        write_file(p, "")
    elif mode == "loaded" and os.path.exists(ipset_full):
        shutil.copy(ipset_full, p)
    else:
        write_file(p, core.IPSET_DUMMY + "\n")


def setup_lists(flowseal_dir, lists_dir, ipset_mode, ipset_full):
    """Base lists from Flowseal (replaced), user lists created once (kept)."""
    os.makedirs(lists_dir, exist_ok=True)
    fl = os.path.join(flowseal_dir, "lists")
    for name in core.BASE_LISTS:
        p = os.path.join(fl, name)
        if os.path.exists(p):
            shutil.copy(p, os.path.join(lists_dir, name))
    for name, default in core.USER_LISTS.items():
        p = os.path.join(lists_dir, name)
        if not os.path.exists(p):
            write_file(p, default)
    if not os.path.exists(ipset_full):
        for cand in ("ipset-all.txt.backup", "ipset-all.txt"):
            p = os.path.join(fl, cand)
            if os.path.exists(p) and len(core.read_list(p)) > 1:
                shutil.copy(p, ipset_full)
                break
    apply_ipset_mode(lists_dir, ipset_mode, ipset_full)


def install_targets(flowseal_dir, targets_file):
    if not os.path.exists(targets_file):
        src = os.path.join(flowseal_dir, "utils", "targets.txt")
        if os.path.exists(src):
            shutil.copy(src, targets_file)


def fetch_ipset():
    with http_get(config.url("flowseal_ipset")) as r:
        text = r.read().decode("utf-8", "replace")
    lines = [l.strip() for l in text.splitlines() if core.CIDR_RE.match(l.strip())]
    if len(lines) < 10:
        raise RuntimeError("скачанный список IPSet подозрительно короткий, оставляю старый")
    return "\n".join(lines) + "\n"


def fetch_hosts():
    with http_get(config.url("flowseal_hosts")) as r:
        good = core.hosts_lines(r.read().decode("utf-8", "replace"))
    if not good:
        raise RuntimeError("в скачанном hosts нет записей")
    return "\n".join(good)
