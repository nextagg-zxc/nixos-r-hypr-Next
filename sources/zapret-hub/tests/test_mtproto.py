import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zaprethub import mtproto  # noqa: E402

HEX = "ee2b6eb790d613a1725557ce33b9a87b30786170692e6f7a6f6e2e7275"
SAMPLE = f"""# MTProto RU (100)
tg://proxy?server=helix.lite64.click&port=443&secret={HEX}
https://t.me/proxy?server=web-kook.mosbatbashim.info.&port=5500&secret=DDBighLLvXrFGRMCBVJdFQ
<a href="https://t.me/proxy?server=1.2.3.4&amp;port=8443&amp;secret=dd{'ab' * 16}">x</a>
tg://proxy?server=HELIX.lite64.click&port=443&secret={HEX.upper()}
tg://proxy?server=bad.port&port=70000&secret={HEX}
tg://proxy?server=bad.secret&port=443&secret=zz!
tg://proxy?server=&port=443&secret={HEX}
garbage line
"""


class Parse(unittest.TestCase):
    def test_parse_and_dedupe(self):
        ps = mtproto.parse_links(SAMPLE, "src")
        self.assertEqual([(p.server, p.port) for p in ps],
                         [("helix.lite64.click", 443), ("web-kook.mosbatbashim.info", 5500), ("1.2.3.4", 8443)])
        self.assertEqual(ps[1].secret, "DDBighLLvXrFGRMCBVJdFQ")
        self.assertEqual(ps[0].source, "src")

    def test_tg_url(self):
        p = mtproto.Proxy("1.2.3.4", 443, "dd" + "ab" * 16, "s")
        self.assertEqual(p.tg_url(), "tg://proxy?server=1.2.3.4&port=443&secret=dd" + "ab" * 16)
        self.assertEqual(p.key, "1.2.3.4:443:dd" + "ab" * 16)

    def test_kind(self):
        self.assertEqual(mtproto.Proxy("a", 1, HEX, "").kind, "Fake TLS")
        self.assertEqual(mtproto.Proxy("a", 1, "dd" + "ab" * 16, "").kind, "Secure")
        self.assertEqual(mtproto.Proxy("a", 1, "ab" * 16, "").kind, "Обычный")


class Fetch(unittest.TestCase):
    def test_fetch_all_tolerates_bad_source(self):
        def fetch(url, timeout):
            if url == "boom":
                raise OSError("connection refused")
            if url == "html":
                return "<!DOCTYPE html><title>Attention Required! | Cloudflare</title>"
            return SAMPLE
        srcs = [{"name": "A", "url": "boom"}, {"name": "B", "url": "html"}, {"name": "C", "url": "ok"}]
        proxies, errors = mtproto.fetch_all(srcs, fetch=fetch)
        self.assertEqual(len(proxies), 3)
        self.assertEqual({p.source for p in proxies}, {"C"})
        self.assertEqual(len(errors), 2)
        self.assertTrue(any("A" in e for e in errors))
        self.assertTrue(any("B" in e and "нет ни одного" in e for e in errors))

    def test_fetch_dedupes_across_sources(self):
        proxies, errors = mtproto.fetch_all([{"name": "A", "url": "1"}, {"name": "B", "url": "2"}],
                                            fetch=lambda u, t: SAMPLE)
        self.assertEqual(len(proxies), 3)
        self.assertEqual(errors, [])


class Check(unittest.TestCase):
    def test_check_all_sorts_alive_by_ping(self):
        ps = [mtproto.Proxy(h, 443, HEX, "s") for h in ("slow", "dead", "fast")]
        pings = {"slow": 300.0, "dead": None, "fast": 20.0}
        out = mtproto.check_all(ps, ping=lambda h, p, t: pings[h])
        self.assertEqual([p.server for p in out], ["fast", "slow", "dead"])
        self.assertEqual([p.alive for p in out], [True, True, False])


class StoreTest(unittest.TestCase):
    def test_roundtrip_favorites_custom(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "sub", "mtproto.json")
            s = mtproto.Store(path)
            self.assertEqual(s.proxies, [])
            self.assertEqual(len(s.sources), 4)
            p = mtproto.Proxy("1.2.3.4", 443, HEX, "s", ping=12.5, alive=True)
            s.proxies = [p]
            s.toggle_favorite(p.key)
            self.assertTrue(s.add_custom(f"tg://proxy?server=my.host&port=443&secret={HEX}"))
            self.assertFalse(s.add_custom("not a link"))
            s.save()
            s2 = mtproto.Store(path)
            self.assertEqual(s2.proxies[0].ping, 12.5)
            self.assertIn(p.key, s2.favorites)
            self.assertEqual(s2.custom[0].server, "my.host")
            self.assertEqual(s2.custom[0].source, "Свой")


if __name__ == "__main__":
    unittest.main()
