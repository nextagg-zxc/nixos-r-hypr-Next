import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zaprethub import config, tgws  # noqa: E402


class Links(unittest.TestCase):
    def test_url(self):
        url = tgws.proxy_url({"host": "0.0.0.0", "port": 1443, "secret": "ab" * 16})
        self.assertEqual(url, "tg://proxy?server=127.0.0.1&port=1443&secret=dd" + "ab" * 16)

    def test_dc(self):
        self.assertEqual(tgws.parse_dc_lines("4:149.154.167.220,2:1.2.3.4\n"), ["4:149.154.167.220", "2:1.2.3.4"])
        self.assertEqual(tgws.parse_dc_lines(""), [])
        with self.assertRaises(ValueError):
            tgws.parse_dc_lines("149.154.167.220")


class Platform(unittest.TestCase):
    def test_asset_and_binary_windows(self):
        with mock.patch.object(config, "IS_WINDOWS", True):
            self.assertEqual(tgws.asset_name(), "TgWsProxy_windows.exe")
            self.assertTrue(tgws.binary().endswith("TgWsProxy.exe"))

    def test_asset_and_binary_linux(self):
        with mock.patch.object(config, "IS_WINDOWS", False):
            self.assertEqual(tgws.asset_name(), "TgWsProxy_linux_amd64")
            self.assertTrue(tgws.binary().endswith(os.sep + "TgWsProxy"))

    def test_windows_running_parse(self):
        out = '"TgWsProxy.exe","4242","Console","1","40 000 K"\r\n'
        self.assertEqual(tgws.parse_tasklist(out), [4242])
        self.assertEqual(tgws.parse_tasklist("INFO: No tasks are running which match the specified criteria.\r\n"), [])


class Config(unittest.TestCase):
    def test_ensure_config_creates_secret_and_marker(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(tgws, "CONFIG_DIR_OVERRIDE", d):
            cfg = tgws.ensure_config()
            self.assertRegex(cfg["secret"], r"^[0-9a-f]{32}$")
            self.assertEqual(cfg["port"], 1443)
            self.assertTrue(os.path.exists(os.path.join(d, ".first_run_done_mtproto")))
            # its one-time IPv6 popup is replaced by a hint on our page
            self.assertTrue(os.path.exists(os.path.join(d, ".ipv6_warned")))
            with open(os.path.join(d, "config.json")) as f:
                self.assertEqual(json.load(f)["secret"], cfg["secret"])
            # keeps an existing valid secret
            self.assertEqual(tgws.ensure_config()["secret"], cfg["secret"])


if __name__ == "__main__":
    unittest.main()
