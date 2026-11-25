#!/usr/bin/env python3
"""Мост между расширением Spicetify nextagg-queue и меню Win+B (24.11).

  bridge.py serve            — служба: WebSocket 127.0.0.1:47823 для расширения в Spotify,
                               очередь → $XDG_CACHE_HOME/nextagg/spotify-queue.json (читает меню),
                               команды меню — Unix-сокет $XDG_RUNTIME_DIR/nextagg-spotify-queue.sock
  bridge.py play <uid> <uri> — попросить Spotify включить трек из очереди
  bridge.py heart            — поставить/снять «в любимых» у текущего трека

Только стандартная библиотека (+ ffmpeg/ffprobe из $NEXTAGG_FFMPEG/$NEXTAGG_FFPROBE). Данные от
расширения проверяются и обрезаются: это текст для меню, ссылки на обложки — только CDN Spotify
(i.scdn.co, mosaic.scdn.co, *.spotifycdn.com) или файлы, которые мост сделал сам.

Локальные файлы Spotify (spotify:local:…): обложка встроена в сам файл, MPRIS её не отдаёт.
Мост находит файл (путь от расширения или по названию среди файлов из local-files.bnk Spotify),
достаёт картинку ffmpeg'ом в $XDG_CACHE_HOME/nextagg/spotify-covers/ и отдаёт меню file://-ссылку.
Если в файле картинки нет — берёт cover/folder.jpg|png из той же папки.
"""
import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import socket
import glob
import re
import struct
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

PORT = 47823
GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
CACHE = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
STATE = os.path.join(CACHE, "nextagg", "spotify-queue.json")
SOCK = os.path.join(os.environ.get("XDG_RUNTIME_DIR") or "/tmp", "nextagg-spotify-queue.sock")
MAX_MSG = 1 << 20
COVERS = os.path.join(CACHE, "nextagg", "spotify-covers")
HOME = os.path.realpath(os.path.expanduser("~"))
AUDIO = (".mp3", ".flac", ".m4a", ".mp4", ".ogg", ".opus", ".wav", ".aac", ".wma")
FFMPEG = os.environ.get("NEXTAGG_FFMPEG") or "ffmpeg"
FFPROBE = os.environ.get("NEXTAGG_FFPROBE") or "ffprobe"
cover_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="spotify-cover")
library_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="spotify-library-cover")
cover_lock = threading.RLock()
cover_jobs = {}
cover_failures = {}
LIBRARY = os.path.join(CACHE, "nextagg", "spotify-cover-library.json")
COVER_STATUS = os.path.join(CACHE, "nextagg", "spotify-cover-status.json")
library_images = {}
library_scan = {"state": "waiting"}
status_written = 0

clients = set()
last = {"connected": False, "current": None, "next": [], "prev": [], "liked": False}


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def s(v, n=300):
    return str(v or "")[:n]


IMG_HOSTS = ("https://i.scdn.co/", "https://mosaic.scdn.co/", "https://image-cdn-ak.spotifycdn.com/",
             "https://image-cdn-fa.spotifycdn.com/", "https://seed-mix-image.spotifycdn.com/")


def img(u):
    u = s(u, 300)
    return u if u.startswith(IMG_HOSTS) else ""


class CoverRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not img(newurl):
            raise ValueError("cover redirect outside Spotify CDN")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def remote_cover(url):
    """Persist a CDN cover before the menu needs it; failures retain the original URL."""
    url = img(url)
    if not url:
        return ""
    out = os.path.join(COVERS, "remote-" + hashlib.sha256(url.encode()).hexdigest() + ".jpg")
    if os.path.isfile(out) and os.path.getsize(out) > 0:
        return "file://" + out
    if time.monotonic() - cover_failures.get(url, -60) < 60:
        return url
    os.makedirs(COVERS, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="cover-", suffix=".tmp", dir=COVERS)
    os.close(fd)
    try:
        opener = urllib.request.build_opener(CoverRedirect)
        request = urllib.request.Request(url, headers={"User-Agent": "nextagg-spotify-cover/1"})
        with opener.open(request, timeout=4) as response:
            if response.headers.get_content_type() not in ("image/jpeg", "image/png", "image/webp"):
                raise ValueError("unsupported cover content type")
            data = response.read(2 * 1024 * 1024 + 1)
        if not data or len(data) > 2 * 1024 * 1024:
            raise ValueError("invalid cover size")
        with open(tmp, "wb") as output:
            output.write(data)
        os.replace(tmp, out)
        return "file://" + out
    except (OSError, ValueError, urllib.error.URLError):
        cover_failures[url] = time.monotonic()
        return url
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass


def write_cover_status(force=False):
    global status_written
    with cover_lock:
        now = time.monotonic()
        pending = sum(not task.done() for task in cover_jobs.values())
        if not force and pending and now - status_written < 1:
            return
        os.makedirs(os.path.dirname(COVER_STATUS), exist_ok=True)
        report = dict(library_scan, known_tracks=len(library_images),
                      stored_images=len(glob.glob(os.path.join(COVERS, "remote-*.jpg"))),
                      pending_images=pending, failed_images=len(cover_failures))
        tmp = COVER_STATUS + ".tmp"
        with open(tmp, "w") as output:
            json.dump(report, output, ensure_ascii=False)
        os.replace(tmp, COVER_STATUS)
        status_written = now


def cached_cover(url, wait=False, bulk=False):
    """Deduplicate current/next-track downloads without blocking the WebSocket loop."""
    url = img(url)
    if not url:
        return ""
    with cover_lock:
        future = cover_jobs.get(url)
        # A playing track must not wait behind the full library's background queue.
        if wait and future is not None and not future.running() and not future.done():
            if future.cancel():
                future = None
        if future is None or (future.done() and future.result() == url):
            future = (library_pool if bulk else cover_pool).submit(remote_cover, url)
            cover_jobs[url] = future
            future.add_done_callback(lambda _: write_cover_status())
        # Completed jobs need no permanent in-memory cache; the files are authoritative.
        for key in list(cover_jobs):
            if key != url and cover_jobs[key].done():
                del cover_jobs[key]
    if future.done():
        return future.result()
    if wait:
        # Текущий трек ждём недолго: дольше — блокировать WebSocket всех клиентов.
        try:
            return future.result(timeout=1.5)
        except TimeoutError:
            return url
    return url


def cover_library(message):
    """Read-only library catalogue supplied by the user's Spotify extension."""
    items = message.get("items") or []
    if not isinstance(items, list):
        return
    for item in items[:500]:
        if not isinstance(item, dict):
            continue
        uri, image = s(item.get("uri"), 600), img(item.get("image"))
        if uri.startswith("spotify:local:"):
            resolved = track(item)
            if resolved and resolved["image"]:
                library_images[uri] = resolved["image"]
            continue
        if uri.startswith(("spotify:track:", "spotify:episode:")) and image:
            library_images[uri] = image
            cached_cover(image, bulk=True)
    with cover_lock:
        library_scan.update(state=s(message.get("state"), 40) or "scanning",
                            scope=s(message.get("scope"), 200),
                            scanned_tracks=message.get("scanned_tracks", 0),
                            scanned_playlists=message.get("scanned_playlists", 0),
                            errors=(message.get("errors") or [])[:20])
        os.makedirs(os.path.dirname(LIBRARY), exist_ok=True)
        tmp = LIBRARY + ".tmp"
        with open(tmp, "w") as output:
            json.dump(library_images, output, ensure_ascii=False)
        os.replace(tmp, LIBRARY)
        write_cover_status(force=True)


def audio_file(p):
    """Путь годится, только если это существующий аудиофайл внутри домашней папки."""
    try:
        r = os.path.realpath(p)
    except (TypeError, ValueError):
        return ""
    if not r.startswith(HOME + "/") or not r.lower().endswith(AUDIO) or not os.path.isfile(r):
        return ""
    return r


bank_cache = {"key": None, "files": []}
tags_cache = {}


def bank_files():
    """Аудиофайлы, которые Spotify знает как локальные (пути в local-files.bnk)."""
    banks = glob.glob(os.path.expanduser("~/.config/spotify/Users/*/local-files.bnk"))
    try:
        key = tuple((b, os.stat(b).st_mtime) for b in banks)
    except OSError:
        key = None
    if key == bank_cache["key"]:
        return bank_cache["files"]
    files = []
    for b in banks:
        try:
            data = open(b, "rb").read()
        except OSError:
            continue
        # записи идут подряд с байтом длины перед каждой, поэтому режем по началу домашней
        # папки и берём самый длинный префикс, который оканчивается аудиорасширением и существует
        prefix = (HOME + "/").encode()
        for chunk in data.split(prefix)[1:]:
            chunk = re.split(rb"[\x00-\x1f]", chunk, maxsplit=1)[0].decode("utf-8", "ignore")
            for m in reversed(list(re.finditer(r"\.(?:" + "|".join(e[1:] for e in AUDIO) + ")", chunk, re.I))):
                p = audio_file(HOME + "/" + chunk[:m.end()])
                if p:
                    if p not in files:
                        files.append(p)
                    break
    bank_cache.update(key=key, files=files)
    return files


def tags(p):
    """(title, artist) из тегов файла; без тегов Spotify показывает имя файла."""
    try:
        st = os.stat(p)
    except OSError:
        return ("", "")
    key = (p, st.st_mtime)
    if key in tags_cache:
        return tags_cache[key]
    title = artist = ""
    try:
        out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format_tags=title,artist",
                              "-of", "json", p], capture_output=True, timeout=10).stdout
        t = {k.lower(): v for k, v in (json.loads(out or b"{}").get("format", {}).get("tags") or {}).items()}
        title, artist = str(t.get("title") or ""), str(t.get("artist") or "")
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    if not title:
        title = os.path.splitext(os.path.basename(p))[0]
    tags_cache[key] = (title, artist)
    return tags_cache[key]


def find_local(uri, title, hint):
    p = audio_file(hint) if hint else ""
    if p:
        return p
    # spotify:local:<artist>:<album>:<title>:<секунды>, части в URL-кодировке (+ = пробел)
    parts = [urllib.parse.unquote_plus(x) for x in uri.split(":")[2:]]
    want = (title or (parts[2] if len(parts) > 2 else "")).strip().lower()
    if not want:
        return ""
    for f in bank_files():
        t, _ = tags(f)
        if t.strip().lower() == want or os.path.splitext(os.path.basename(f))[0].lower() == want:
            return f
    return ""


def local_cover(path):
    """file://-ссылка на обложку локального файла (кэшируется по пути и времени изменения)."""
    try:
        st = os.stat(path)
    except OSError:
        return ""
    name = hashlib.sha1(f"{path}\0{st.st_mtime_ns}".encode()).hexdigest() + ".png"
    out = os.path.join(COVERS, name)
    if os.path.isfile(out):
        return "file://" + out
    os.makedirs(COVERS, exist_ok=True)
    tmp = out + ".tmp.png"
    try:
        r = subprocess.run([FFMPEG, "-v", "error", "-y", "-i", path, "-an", "-map", "0:v:0", "-frames:v", "1",
                            "-vf", "scale=640:640:force_original_aspect_ratio=decrease", tmp],
                           capture_output=True, timeout=20)
        if r.returncode == 0 and os.path.getsize(tmp) > 0:
            os.replace(tmp, out)
            return "file://" + out
    except (OSError, subprocess.SubprocessError):
        pass
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    d = os.path.dirname(path)
    for n in ("cover", "folder", "Cover", "Folder", "front", "album"):
        for ext in (".jpg", ".jpeg", ".png"):
            c = os.path.join(d, n + ext)
            if os.path.isfile(c):
                return "file://" + c
    return ""


def track(t, resolve_cover=True):
    if not isinstance(t, dict):
        return None
    uri = s(t.get("uri"), 600)
    local = uri.startswith("spotify:local:")
    if not (uri.startswith("spotify:track:") or uri.startswith("spotify:episode:") or local):
        return None
    out = {
        "uri": uri,
        "uid": s(t.get("uid"), 80),
        "title": s(t.get("title")),
        "artist": s(t.get("artist")),
        "image": "" if local else img(t.get("image")),
    }
    if local and resolve_cover:
        f = find_local(uri, out["title"], s(t.get("localfile"), 2000))
        out["image"] = local_cover(f) if f else ""
    elif not local:
        saved = library_images.get(uri)
        if saved:
            filename = os.path.join(COVERS, "remote-" + hashlib.sha256(saved.encode()).hexdigest() + ".jpg")
            if os.path.isfile(filename):
                out["image"] = "file://" + filename
    return out


written = None
state_lock = threading.RLock()


def write_state():
    # Пишем только при изменении: меню следит за файлом и перечитывает его на каждую запись,
    # а расширение шлёт снимок каждые 5 с.
    global written
    with state_lock:
        data = json.dumps(dict(last, connected=bool(clients)), ensure_ascii=False, sort_keys=True)
        if data == written and os.path.exists(STATE):
            return
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        tmp = STATE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(data)
        os.replace(tmp, STATE)
        written = data


def on_message(text):
    try:
        m = json.loads(text)
    except ValueError:
        return
    if not isinstance(m, dict):
        return
    if m.get("type") == "cover-library":
        cover_library(m)
        return
    if m.get("type") != "queue":
        return
    snapshot(m)
    write_state()


def snapshot(m):
    last["current"] = track(m.get("current"))
    # Publish the current track before inspecting the rest of the queue.
    if last["current"] and last["current"]["image"].startswith("https://"):
        last["current"]["image"] = cached_cover(last["current"]["image"], wait=True)
    write_state()
    last["next"] = [x for x in (track(t, resolve_cover=i < 3) for i, t in enumerate((m.get("next") or [])[:100])) if x]
    last["prev"] = [x for x in (track(t, resolve_cover=False) for t in (m.get("prev") or [])[-50:]) if x]
    for item in last["next"][:3]:
        if item["image"].startswith("https://"):
            item["image"] = cached_cover(item["image"])
    last["liked"] = m.get("liked") is True


async def read_frame(reader):
    h = await reader.readexactly(2)
    fin_op, ln = h[0], h[1]
    op = fin_op & 0x0F
    masked = ln & 0x80
    ln &= 0x7F
    if ln == 126:
        ln = struct.unpack("!H", await reader.readexactly(2))[0]
    elif ln == 127:
        ln = struct.unpack("!Q", await reader.readexactly(8))[0]
    if ln > MAX_MSG:
        raise ValueError("frame too big")
    mask = await reader.readexactly(4) if masked else b"\0\0\0\0"
    data = bytearray(await reader.readexactly(ln))
    for i in range(ln):
        data[i] ^= mask[i % 4]
    return op, bytes(data)


def frame(op, payload):
    n = len(payload)
    if n < 126:
        head = struct.pack("!BB", 0x80 | op, n)
    elif n < 65536:
        head = struct.pack("!BBH", 0x80 | op, 126, n)
    else:
        head = struct.pack("!BBQ", 0x80 | op, 127, n)
    return head + payload


async def ws_client(reader, writer):
    try:
        req = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), 5)
    except Exception:
        writer.close()
        return
    if len(req) > 16384:
        writer.close()
        return
    lines = req.decode("latin-1").split("\r\n")
    headers = {}
    for l in lines[1:]:
        if ":" in l:
            k, v = l.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    origin = headers.get("origin", "")
    key = headers.get("sec-websocket-key", "")
    # Только сам Spotify (xpui): сайты в браузере сюда не подключатся.
    if not lines[0].startswith("GET ") or "websocket" not in headers.get("upgrade", "").lower() \
            or not key or "spotify" not in origin.lower():
        log(f"rejected connection (origin={origin!r})")
        writer.write(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n")
        await writer.drain()
        writer.close()
        return
    accept = base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()
    writer.write(("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                  f"Sec-WebSocket-Accept: {accept}\r\n\r\n").encode())
    await writer.drain()
    clients.add(writer)
    log(f"spotify connected (origin={origin})")
    write_state()
    try:
        while True:
            op, data = await read_frame(reader)
            if op == 1:
                # ffmpeg/ffprobe для локальных файлов — в отдельном потоке, чтобы не держать сокеты
                await asyncio.to_thread(on_message, data.decode("utf-8", "replace"))
            elif op == 9:
                writer.write(frame(10, data))
                await writer.drain()
            elif op == 8:
                break
    except (asyncio.IncompleteReadError, ConnectionError, ValueError):
        pass
    finally:
        clients.discard(writer)
        writer.close()
        log("spotify disconnected")
        write_state()


async def cmd_client(reader, writer):
    try:
        line = await asyncio.wait_for(reader.readline(), 5)
        m = json.loads(line or b"{}")
        if isinstance(m, dict) and m.get("cmd") in ("play", "refresh", "heart"):
            out = {"cmd": m["cmd"], "uid": s(m.get("uid"), 80), "uri": s(m.get("uri"), 600)}
            for w in list(clients):
                w.write(frame(1, json.dumps(out).encode()))
                await w.drain()
            writer.write(b"ok\n" if clients else b"no-spotify\n")
    except Exception as e:
        writer.write(f"error {e}\n".encode())
    finally:
        await writer.drain()
        writer.close()


async def serve():
    try:
        with open(LIBRARY) as source:
            stored = json.load(source)
        if isinstance(stored, dict):
            library_images.update({s(k, 600): v for k, v in stored.items()
                                   if img(v) or (isinstance(v, str) and v.startswith("file://" + COVERS + "/") and os.path.isfile(v[7:]))})
    except (OSError, ValueError):
        pass
    write_cover_status(force=True)
    write_state()
    ws = await asyncio.start_server(ws_client, "127.0.0.1", PORT)
    try:
        os.unlink(SOCK)
    except FileNotFoundError:
        pass
    cmd = await asyncio.start_unix_server(cmd_client, SOCK)
    os.chmod(SOCK, 0o600)
    log(f"listening ws://127.0.0.1:{PORT}, {SOCK}")
    async with ws, cmd:
        await asyncio.gather(ws.serve_forever(), cmd.serve_forever())


def send_cmd(obj):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as c:
        c.settimeout(3)
        c.connect(SOCK)
        c.sendall((json.dumps(obj) + "\n").encode())
        print(c.recv(200).decode().strip())


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "serve":
        asyncio.run(serve())
    elif len(sys.argv) == 4 and sys.argv[1] == "play":
        send_cmd({"cmd": "play", "uid": sys.argv[2], "uri": sys.argv[3]})
    elif len(sys.argv) == 2 and sys.argv[1] == "heart":
        send_cmd({"cmd": "heart"})
    elif len(sys.argv) == 2 and sys.argv[1] == "refresh":
        send_cmd({"cmd": "refresh"})
    else:
        sys.exit(__doc__)
