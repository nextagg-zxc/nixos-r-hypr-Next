import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zaprethub import config, core  # noqa: E402

BAT = r'''@echo off
cd /d "%~dp0"
set "BIN=%~dp0bin\"
start "zapret: %~n0" /min "%BIN%winws.exe" --wf-tcp=80,443,%GameFilterTCP% --wf-udp=443,50000-50100,%GameFilterUDP% ^
--filter-udp=443 --hostlist="%LISTS%list-general.txt" --dpi-desync=fake --dpi-desync-fake-quic="%BIN%quic_initial_www_google_com.bin" --new ^
--filter-tcp=443 --dpi-desync=fake --dpi-desync-fake-tls=^! --dpi-desync-fake-tls-mod=rnd --new ^
--filter-tcp=%GameFilterTCP% --dpi-desync=multisplit --dpi-desync-cutoff=n3
'''


class BatConversion(unittest.TestCase):
    def test_profiles_and_globals(self):
        text = core.bat_to_strategy(BAT, "general")
        g, profiles = core.parse_strategy_text(text)
        self.assertEqual(g, ["--wf-tcp=80,443,%GameFilterTCP%", "--wf-udp=443,50000-50100,%GameFilterUDP%"])
        self.assertEqual(len(profiles), 3)
        self.assertIn("--dpi-desync-fake-tls=!", profiles[1])
        self.assertIn("--dpi-desync-fake-quic=%BIN%quic_initial_www_google_com.bin", profiles[0])

    def test_build_game_off(self):
        args, tcp, udp = core.build(core.bat_to_strategy(BAT), "off", "/b", "/l")
        self.assertEqual(args.count("--new"), 2)
        self.assertIn("--hostlist=/l/list-general.txt", args)
        self.assertIn("--dpi-desync-fake-quic=/b/quic_initial_www_google_com.bin", args)
        self.assertIn("--filter-tcp=12", args)
        self.assertNotIn("--wf-tcp=80,443,12", args)
        self.assertEqual(tcp, "80,443,12")
        self.assertEqual(udp, "443,50000-50100,12")

    def test_build_game_all(self):
        _, tcp, udp = core.build(core.bat_to_strategy(BAT), "all", "/b", "/l")
        self.assertEqual(core.render_ports(core.merge_ports(tcp)), "80, 443, 1024-65535")
        self.assertEqual(core.render_ports(core.merge_ports(udp)), "443, 1024-65535")

    def test_keep_wf(self):
        args, _, _ = core.build(core.bat_to_strategy(BAT), "off", "/b", "/l", keep_wf=True)
        self.assertEqual(args[:2], ["--wf-tcp=80,443,12", "--wf-udp=443,50000-50100,12"])

    def test_windows_paths(self):
        args, _, _ = core.build(core.bat_to_strategy(BAT), "off", "C:\\Z\\bin", "C:\\Z\\lists\\", keep_wf=True)
        self.assertIn("--hostlist=C:\\Z\\lists\\list-general.txt", args)
        self.assertIn("--dpi-desync-fake-quic=C:\\Z\\bin\\quic_initial_www_google_com.bin", args)

    def test_unknown_placeholder_raises(self):
        with self.assertRaises(ValueError) as cm:
            core.build("--filter-tcp=%Foo% --dpi-desync=fake\n", "off", "/b", "/l")
        self.assertIn("%Foo%", str(cm.exception))

    def test_handwritten_without_wf(self):
        _, tcp, udp = core.build("--filter-tcp=80,443 --dpi-desync=fake --new --filter-udp=443 --dpi-desync=fake\n",
                                 "off", "/b", "/l")
        self.assertEqual(tcp, "80,443")
        self.assertEqual(udp, "443")

    def test_no_winws(self):
        with self.assertRaises(ValueError):
            core.bat_to_strategy("echo hi")

    def test_empty_strategy(self):
        with self.assertRaises(ValueError):
            core.build("# only a comment\n", "off", "/b", "/l")


class Strategies(unittest.TestCase):
    def test_list_custom_shadows_and_natural_order(self):
        with tempfile.TemporaryDirectory() as d:
            b, c = os.path.join(d, "b"), os.path.join(d, "c")
            os.makedirs(b)
            os.makedirs(c)
            for n in ("general", "general (ALT10)", "general (ALT2)", "general (ALT)"):
                open(os.path.join(b, n + ".txt"), "w").close()
            open(os.path.join(c, "general (ALT2).txt"), "w").close()
            self.assertEqual(core.list_strategies(b, c), [
                ("general", "builtin"), ("general (ALT)", "builtin"),
                ("general (ALT2)", "custom"), ("general (ALT10)", "builtin")])

    def test_state_defaults_and_validation(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "state.json")
            self.assertEqual(core.load_state(p), core.DEFAULT_STATE)
            with open(p, "w") as f:
                f.write('{"strategy": "x", "game_filter": "bogus", "ipset": "any", "autostart": "yes", "junk": 1}')
            self.assertEqual(core.load_state(p), {"strategy": "x", "game_filter": "off", "ipset": "any",
                                                  "autostart": True})
            with open(p, "w") as f:
                f.write('{"autostart": false}')
            self.assertFalse(core.load_state(p)["autostart"])


class Ports(unittest.TestCase):
    def test_merge(self):
        self.assertEqual(core.merge_ports("443,80,2053,1024-65535,8443"), [(80, 80), (443, 443), (1024, 65535)])
        self.assertEqual(core.merge_ports("1-5,6-9"), [(1, 9)])

    def test_bad(self):
        with self.assertRaises(ValueError):
            core.merge_ports("0")
        with self.assertRaises(ValueError):
            core.merge_ports("70000")

    def test_ruleset(self):
        rs = core.nft_ruleset("80,443", "443,50000-50100")
        self.assertIn("table inet zapret_hub {", rs)
        self.assertIn("tcp dport { 80, 443 } ct original packets 1-9 queue num 201 bypass", rs)
        self.assertIn("udp dport { 443, 50000-50100 }", rs)
        self.assertIn("tcp sport { 80, 443 } ct reply packets 1-3", rs)


class Lists(unittest.TestCase):
    def test_normalize(self):
        n = core.normalize_list_entry
        self.assertEqual(n("https://www.YouTube.com/watch?v=1"), "www.youtube.com")
        self.assertEqual(n("*.discord.gg"), "discord.gg")
        self.assertEqual(n("^dns.google"), "^dns.google")
        self.assertEqual(n("кто.рф"), "xn--j1ail.xn--p1ai")
        self.assertIsNone(n("bad domain"))
        self.assertIsNone(n("a/b", ip=True))
        self.assertEqual(n("1.2.3.0/24", ip=True), "1.2.3.0/24")

    def test_clean_list_keeps_placeholder(self):
        self.assertEqual(core.clean_list("list-general-user.txt", "  \n!!! ???\n"), "domain.example.abc\n")
        self.assertEqual(core.clean_list("list-general-user.txt", "YouTube.com\nyoutube.com\nx.org"),
                         "youtube.com\nx.org\n")
        self.assertEqual(core.clean_list("ipset-exclude-user.txt", "10.0.0.0/8 junk"), "10.0.0.0/8\n")


class Targets(unittest.TestCase):
    def test_roundtrip(self):
        t = core.parse_targets('# c\nYT = "https://www.youtube.com"\nDNS = "PING:1.1.1.1"\n')
        self.assertEqual(t[0], {"name": "YT", "url": "https://www.youtube.com", "ping": "www.youtube.com"})
        self.assertEqual(t[1], {"name": "DNS", "url": None, "ping": "1.1.1.1"})
        self.assertEqual(core.parse_targets(core.format_targets(t)), t)


class Hosts(unittest.TestCase):
    def test_block(self):
        h = "127.0.0.1 localhost\n"
        h2 = core.hosts_block_replace(h, "1.2.3.4 a.b")
        self.assertIn(core.HOSTS_BEGIN, h2)
        self.assertEqual(core.hosts_block_replace(h2, "5.6.7.8 c.d").count(core.HOSTS_BEGIN), 1)
        self.assertEqual(core.hosts_block_replace(h2, ""), h)


class Config(unittest.TestCase):
    def test_mirror_override(self):
        old = os.environ.get("ZAPRETHUB_MIRROR")
        try:
            os.environ["ZAPRETHUB_MIRROR"] = "http://10.0.0.1:8000"
            self.assertEqual(config.url("flowseal_version"),
                             "http://10.0.0.1:8000/raw/Flowseal/zapret-discord-youtube/main/.service/version.txt")
            self.assertEqual(config.url("flowseal_api"),
                             "http://10.0.0.1:8000/api/repos/Flowseal/zapret-discord-youtube/releases/latest")
        finally:
            if old is None:
                os.environ.pop("ZAPRETHUB_MIRROR", None)
            else:
                os.environ["ZAPRETHUB_MIRROR"] = old
        self.assertTrue(config.url("flowseal_version").startswith("https://raw.githubusercontent.com/"))


if __name__ == "__main__":
    unittest.main()
