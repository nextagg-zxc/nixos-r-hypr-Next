"""Pure logic shared by both platforms: strategy format, Flowseal .bat
conversion, argument building, ports, nftables rules, lists, test targets."""

import json
import re
import shlex

QNUM = 201
NFT_TABLE = "zapret_hub"
DESYNC_MARK = 0x40000000
HOSTS_BEGIN = "# >>> zapret-hub >>>"
HOSTS_END = "# <<< zapret-hub <<<"

# Lists the user edits; base lists come from Flowseal and are replaced on update.
USER_LISTS = {
    "list-general-user.txt": "domain.example.abc\n",
    "list-exclude-user.txt": "domain.example.abc\n",
    "ipset-exclude-user.txt": "203.0.113.113/32\n",
}
BASE_LISTS = ["list-general.txt", "list-google.txt", "list-exclude.txt", "ipset-exclude.txt"]
IPSET_DUMMY = "203.0.113.113/32"

GAME_FILTER_MODES = ("off", "tcp", "udp", "all")
GAME_RANGE = "1024-65535"
GAME_OFF_PORT = "12"   # Flowseal's "nothing" port when the game filter is off
IPSET_MODES = ("none", "any", "loaded")

DEFAULT_STATE = {"strategy": "general", "game_filter": "off", "ipset": "none", "autostart": True}

NAME_RE = re.compile(r"^[\w][\w .()+\-]{0,63}$")
DOMAIN_RE = re.compile(r"^\^?(?:[a-z0-9_](?:[a-z0-9_\-]{0,61}[a-z0-9_])?\.)*[a-z0-9\-]{1,63}$")
CIDR_RE = re.compile(r"^[0-9a-fA-F:.]+(?:/\d{1,3})?$")
PLACEHOLDER_RE = re.compile(r"%\w+%")

# Options that only exist in winws (WinDivert / Windows network filters).
WINDOWS_ONLY_PREFIXES = ("--wf-", "--nlm-filter", "--ssid-filter")


def valid_name(name):
    return bool(name) and bool(NAME_RE.match(name)) and name not in (".", "..")


# ---------------------------------------------------------------- state

def load_state(path):
    state = dict(DEFAULT_STATE)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            state.update({k: v for k, v in data.items() if k in DEFAULT_STATE})
    except (OSError, ValueError):
        pass
    if state["game_filter"] not in GAME_FILTER_MODES:
        state["game_filter"] = "off"
    if state["ipset"] not in IPSET_MODES:
        state["ipset"] = "none"
    if not isinstance(state["autostart"], bool):
        state["autostart"] = True
    return state


def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {} if default is None else default


# ---------------------------------------------------------------- strategies

def list_strategies(builtin_dir, custom_dir):
    """[(name, kind)] with kind 'builtin' or 'custom'; custom shadows builtin."""
    import os
    found = {}
    for kind, d in (("builtin", builtin_dir), ("custom", custom_dir)):
        try:
            names = os.listdir(d)
        except OSError:
            continue
        for fn in names:
            if fn.endswith(".txt"):
                found[fn[:-4]] = kind
    return sorted(found.items(), key=lambda kv: strategy_sort_key(kv[0]))


def strategy_sort_key(name):
    # general, general (ALT), general (ALT2) ... general (ALT10): natural order,
    # a suffix without a number counts as 1
    name = re.sub(r"([A-Za-z])\)", r"\g<1>1)", name)
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def strategy_path(name, builtin_dir, custom_dir):
    import os
    custom = os.path.join(custom_dir, name + ".txt")
    if os.path.exists(custom):
        return custom
    return os.path.join(builtin_dir, name + ".txt")


def bat_to_strategy(bat_text, title=""):
    """Convert a Flowseal general*.bat into the strategy text format:
    one profile per line, placeholders (%BIN%, %LISTS%, %GameFilterTCP%...)
    kept so the file stays portable."""
    lines = bat_text.splitlines()
    start = next((i for i, l in enumerate(lines) if "winws.exe" in l), None)
    if start is None:
        raise ValueError("в .bat не найден запуск winws.exe")
    first = lines[start]
    cmd = first[first.index("winws.exe") + len("winws.exe"):].lstrip('"')
    i = start
    parts = []
    while True:
        cur = cmd if i == start else lines[i]
        stripped = cur.rstrip()
        if stripped.endswith("^"):
            parts.append(stripped[:-1])
            i += 1
            if i >= len(lines):
                break
            continue
        parts.append(stripped)
        break
    joined = " ".join(parts).replace("^!", "!")
    tokens = shlex.split(joined)
    globals_, profiles = split_profiles(tokens)
    out = []
    if title:
        out.append(f"# {title}")
    if globals_:
        out.append(join_tokens(globals_))
    out.extend(join_tokens(p) for p in profiles)
    return "\n".join(out) + "\n"


def join_tokens(tokens):
    return " ".join(shlex.quote(t) for t in tokens)


def split_profiles(tokens):
    """Split a flat token list into (global --wf-* tokens, [profile tokens])."""
    globals_, profiles, cur = [], [], []
    for t in tokens:
        if t.startswith(WINDOWS_ONLY_PREFIXES):
            globals_.append(t)
        elif t == "--new":
            if cur:
                profiles.append(cur)
            cur = []
        else:
            cur.append(t)
    if cur:
        profiles.append(cur)
    return globals_, profiles


def parse_strategy_text(text):
    """Strategy text -> (global tokens, [profiles]). Each non-comment line is a
    profile; a line may also hold several profiles separated by --new."""
    globals_, profiles = [], []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        g, p = split_profiles(shlex.split(line, comments=True))
        globals_ += g
        profiles += p
    return globals_, profiles


def game_ports(mode):
    tcp = GAME_RANGE if mode in ("tcp", "all") else GAME_OFF_PORT
    udp = GAME_RANGE if mode in ("udp", "all") else GAME_OFF_PORT
    return tcp, udp


def _dir_prefix(d):
    sep = "\\" if "\\" in d else "/"
    return d.rstrip("/\\") + sep


def expand_placeholders(token, game_mode, bin_dir, lists_dir):
    tcp, udp = game_ports(game_mode)
    out = (token.replace("%BIN%", _dir_prefix(bin_dir))
                .replace("%LISTS%", _dir_prefix(lists_dir))
                .replace("%GameFilterTCP%", tcp)
                .replace("%GameFilterUDP%", udp)
                .replace("%GameFilter%", tcp))
    m = PLACEHOLDER_RE.search(out)
    if m:
        raise ValueError(f"в стратегии неизвестная переменная {m.group(0)} — обнови программу")
    return out


def build(text, game_mode, bin_dir, lists_dir, keep_wf=False):
    """Strategy text -> (args, tcp port spec, udp port spec). keep_wf puts the
    --wf-* filters first in args (winws); nfqws gets them via nftables."""
    globals_, profiles = parse_strategy_text(text)
    exp = lambda t: expand_placeholders(t, game_mode, bin_dir, lists_dir)  # noqa: E731
    tcp, udp, wf = [], [], []
    for g in globals_:
        g = exp(g)
        wf.append(g)
        key, _, val = g.partition("=")
        if key == "--wf-tcp":
            tcp.append(val)
        elif key == "--wf-udp":
            udp.append(val)
    if not profiles:
        raise ValueError("в стратегии нет ни одного профиля")
    args = list(wf) if keep_wf else []
    for n, prof in enumerate(profiles):
        if n:
            args.append("--new")
        args += [exp(t) for t in prof]
    tcp_spec = ",".join(tcp) or ports_from_filters(profiles, "--filter-tcp", game_mode)
    udp_spec = ",".join(udp) or ports_from_filters(profiles, "--filter-udp", game_mode)
    return args, tcp_spec, udp_spec


def ports_from_filters(profiles, opt, game_mode):
    """Fallback for hand-written strategies without --wf-*: union of the
    profiles' --filter-tcp / --filter-udp ports."""
    specs = []
    tcp, udp = game_ports(game_mode)
    for prof in profiles:
        for t in prof:
            if t.startswith(opt + "="):
                v = (t.split("=", 1)[1].replace("%GameFilterTCP%", tcp)
                     .replace("%GameFilterUDP%", udp).replace("%GameFilter%", tcp))
                if v != "*" and not v.startswith("~"):
                    specs.append(v)
    return ",".join(specs)


def merge_ports(spec):
    """'80,443,1024-65535,2053' -> [(80,80),(443,443),(1024,65535)] merged."""
    ranges = []
    for part in spec.replace(" ", "").split(","):
        if not part:
            continue
        lo, _, hi = part.partition("-")
        try:
            lo = int(lo)
            hi = int(hi) if hi else lo
        except ValueError:
            raise ValueError(f"неверный порт: {part}") from None
        if not (0 < lo <= hi <= 65535):
            raise ValueError(f"неверный порт: {part}")
        ranges.append((lo, hi))
    ranges.sort()
    merged = []
    for lo, hi in ranges:
        if merged and lo <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
        else:
            merged.append((lo, hi))
    return merged


def render_ports(ranges):
    return ", ".join(str(lo) if lo == hi else f"{lo}-{hi}" for lo, hi in ranges)


LOCAL4 = "0.0.0.0/8, 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.168.0.0/16, 224.0.0.0/3"
LOCAL6 = "::1, fc00::/7, fe80::/10, ff00::/8"


def nft_ruleset(tcp_spec, udp_spec, pkt_out=9, pkt_in=3):
    """Ruleset modelled on zapret's own nft.sh: queue the first packets of
    outgoing connections to nfqws, skip packets nfqws generated itself."""
    tcp = merge_ports(tcp_spec) if tcp_spec else []
    udp = merge_ports(udp_spec) if udp_spec else []
    mark = f"meta mark and {DESYNC_MARK:#x} == 0"
    q = f"queue num {QNUM} bypass"
    out = [f"table inet {NFT_TABLE}", f"delete table inet {NFT_TABLE}", f"table inet {NFT_TABLE} {{"]
    out += ["  chain postrouting {",
            "    type filter hook postrouting priority 99; policy accept;",
            f"    ip daddr {{ {LOCAL4} }} return",
            f"    ip6 daddr {{ {LOCAL6} }} return"]
    if tcp:
        out.append(f"    {mark} tcp dport {{ {render_ports(tcp)} }} ct original packets 1-{pkt_out} {q}")
    if udp:
        out.append(f"    {mark} udp dport {{ {render_ports(udp)} }} ct original packets 1-{pkt_out} {q}")
    out.append("  }")
    out += ["  chain prerouting {",
            "    type filter hook prerouting priority -99; policy accept;",
            f"    ip saddr {{ {LOCAL4} }} return",
            f"    ip6 saddr {{ {LOCAL6} }} return"]
    if tcp:
        out.append(f"    tcp sport {{ {render_ports(tcp)} }} ct reply packets 1-{pkt_in} {q}")
    out.append("  }")
    out += ["  chain predefrag {",
            "    type filter hook output priority -401; policy accept;",
            f"    meta mark and {DESYNC_MARK:#x} != 0 jump predefrag_nfqws",
            "  }",
            "  chain predefrag_nfqws {",
            "    ip frag-off & 0x1fff != 0 notrack",
            "    exthdr frag exists notrack",
            "    tcp flags ! syn,rst,ack notrack",
            "  }",
            "}"]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- lists

def normalize_list_entry(raw, ip=False):
    """User input -> list entry, or None if invalid. Accepts pasted URLs."""
    s = raw.strip().lower()
    if not s or s.startswith("#"):
        return None
    if ip:
        return s if CIDR_RE.match(s) else None
    s = re.sub(r"^[a-z][a-z0-9+.\-]*://", "", s)
    s = s.split("/", 1)[0].split("?", 1)[0].split(":", 1)[0].strip(".")
    if s.startswith("*."):
        s = s[2:]
    try:
        s = s.encode("idna").decode("ascii") if not s.startswith("^") else s
    except UnicodeError:
        return None
    return s if DOMAIN_RE.match(s) else None


def split_entries(text):
    return [p for p in re.split(r"[\s,;]+", text) if p]


def clean_list(name, text):
    """User list text -> file content: valid unique entries, or Flowseal's
    placeholder (winws/nfqws dislike empty lists)."""
    ip = name.startswith("ipset")
    entries = []
    for raw in split_entries(text):
        e = normalize_list_entry(raw, ip=ip)
        if e and e not in entries:
            entries.append(e)
    if not entries:
        return USER_LISTS[name]
    return "\n".join(entries) + "\n"


def read_list(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return [l.strip() for l in f if l.strip() and not l.lstrip().startswith("#")]
    except OSError:
        return []


# ---------------------------------------------------------------- tests

def parse_targets(text):
    """Flowseal targets.txt -> [{'name','url','ping'}]."""
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r'^(\w+)\s*=\s*"?([^"]+)"?\s*$', line)
        if not m:
            continue
        name, val = m.group(1), m.group(2).strip()
        if val.upper().startswith("PING:"):
            out.append({"name": name, "url": None, "ping": val[5:].strip()})
        else:
            host = re.sub(r"^https?://", "", val).split("/", 1)[0]
            out.append({"name": name, "url": val, "ping": host})
    return out


def format_targets(targets):
    lines = ["# Цели для тестов Zapret Hub (формат Flowseal targets.txt)"]
    for t in targets:
        val = t["url"] if t["url"] else f"PING:{t['ping']}"
        lines.append(f'{t["name"]} = "{val}"')
    return "\n".join(lines) + "\n"


def hosts_block_replace(hosts_text, block):
    """Replace (or append / remove when block is empty) our marked block."""
    pat = re.compile(re.escape(HOSTS_BEGIN) + r".*?" + re.escape(HOSTS_END) + r"\n?", re.S)
    text = pat.sub("", hosts_text)
    if block.strip():
        if text and not text.endswith("\n"):
            text += "\n"
        text += f"{HOSTS_BEGIN}\n{block.strip()}\n{HOSTS_END}\n"
    return text


def hosts_lines(raw):
    """Keep only 'IP host [host...]' lines from a downloaded hosts file."""
    return [l.strip() for l in raw.splitlines()
            if re.match(r"^[0-9a-fA-F:.]+\s+[\w.\-]+(\s+[\w.\-]+)*$", l.strip())]
