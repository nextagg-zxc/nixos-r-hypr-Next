"""Site checks in plain Python, the same on Windows and Linux. Mirrors
Flowseal's test (curl --http1.1 / --tlsv1.2 / --tlsv1.3): a check passes when
the server answered with any HTTP status."""

import http.client
import socket
import ssl
import time
import urllib.parse

LABELS = ("HTTP", "TLS1.2", "TLS1.3")


def _context(version=None):
    ctx = ssl.create_default_context()
    if version:
        ctx.minimum_version = ctx.maximum_version = version
    return ctx


def _request(u, timeout, ctx):
    p = urllib.parse.urlsplit(u)
    host = p.hostname
    if p.scheme == "https":
        conn = http.client.HTTPSConnection(host, p.port or 443, timeout=timeout, context=ctx)
    else:
        conn = http.client.HTTPConnection(host, p.port or 80, timeout=timeout)
    try:
        conn.request("HEAD", p.path or "/", headers={"User-Agent": "Mozilla/5.0 zapret-hub", "Connection": "close"})
        conn.getresponse().read()
    finally:
        conn.close()


def _classify(exc):
    if exc is None:
        return "OK"
    if isinstance(exc, socket.gaierror):
        return "DNS"
    if isinstance(exc, ssl.SSLCertVerificationError):
        return "SSL"
    if isinstance(exc, ssl.SSLError) and any(s in str(exc).upper() for s in
                                              ("UNSUPPORTED_PROTOCOL", "NO_PROTOCOLS_AVAILABLE", "VERSION")):
        return "UNSUP"
    return "ERROR"


def _one(u, timeout, version):
    try:
        _request(u, timeout, _context(version))
        return "OK"
    except Exception as e:  # noqa: BLE001 - any failure is a result, not a crash
        return _classify(e)


def check_site(u, timeout=4):
    """{'HTTP': s} for http:// URLs, {'HTTP','TLS1.2','TLS1.3'} for https://;
    s is OK | ERROR | UNSUP | SSL | DNS."""
    res = {"HTTP": _one(u, timeout, None)}
    if u.startswith("https://"):
        if res["HTTP"] == "DNS":   # no point trying TLS variants on a name that does not resolve
            res["TLS1.2"] = res["TLS1.3"] = "DNS"
        else:
            res["TLS1.2"] = _one(u, timeout, ssl.TLSVersion.TLSv1_2)
            res["TLS1.3"] = _one(u, timeout, ssl.TLSVersion.TLSv1_3)
    return res


def tcp_ping(host, port=443, timeout=2):
    """TCP connect time in ms, or None. Works without admin rights (no ICMP)."""
    t = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return round((time.perf_counter() - t) * 1000, 1)
    except OSError:
        return None


def check_target(t, timeout=4, ping_port=443):
    """Target {'name','url','ping'} -> {'name', HTTP/TLS statuses, 'ping'}."""
    res = {"name": t["name"]}
    if t.get("url"):
        res.update(check_site(t["url"], timeout))
    if t.get("ping"):
        res["ping"] = tcp_ping(t["ping"], ping_port, min(timeout, 3))
    return res


def score(res):
    keys = [k for k in LABELS if k in res]
    return sum(1 for k in keys if res[k] == "OK"), len(keys)
