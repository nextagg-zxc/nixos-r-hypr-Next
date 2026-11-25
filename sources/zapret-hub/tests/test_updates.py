import os
import sys
import tempfile
import unittest
import urllib.error
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zaprethub import updates  # noqa: E402

GOOD_BAT = ('@echo off\nstart "zapret" /min "%BIN%winws.exe" --wf-tcp=80,443 ^\n'
            '--filter-tcp=443 --hostlist="%LISTS%list-general.txt" --dpi-desync=fake\n')


def read(path):
    with open(path) as f:
        return f.read()


def make_zip(path, top="zapret-discord-youtube-9.9.9"):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(f"{top}/general.bat", GOOD_BAT)
        z.writestr(f"{top}/general (BROKEN).bat", "@echo off\necho nothing here\n")
        z.writestr(f"{top}/service.bat", "@echo off\n")
        z.writestr(f"{top}/bin/winws.exe", b"MZ")
        z.writestr(f"{top}/bin/quic_initial_www_google_com.bin", b"\x00")
        z.writestr(f"{top}/lists/list-general.txt", "discord.com\n")
        z.writestr(f"{top}/lists/ipset-all.txt", "1.1.1.0/24\n2.2.2.0/24\n")
        z.writestr(f"{top}/utils/targets.txt", 'YT = "https://www.youtube.com"\n')
        z.writestr("../evil.txt", "x")


class Versions(unittest.TestCase):
    def test_version_gt(self):
        self.assertTrue(updates.version_gt("1.10.10", "1.10.9"))
        self.assertTrue(updates.version_gt("v1.11.0", "1.10.3"))
        self.assertFalse(updates.version_gt("1.10.3", "1.10.3"))
        self.assertFalse(updates.version_gt("1.9", "1.10.3"))
        self.assertTrue(updates.version_gt("1.10.3", None))

    def test_zip_url_fallback(self):
        self.assertEqual(updates.flowseal_zip_url("1.10.3"),
                         "https://github.com/Flowseal/zapret-discord-youtube/releases/download/1.10.3/"
                         "zapret-discord-youtube-1.10.3.zip")


class Install(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name
        self.zip = os.path.join(self.d, "src.zip")
        make_zip(self.zip)
        self.logs = []

    def tearDown(self):
        self.tmp.cleanup()

    def fake_download(self, url, dest, progress=None):
        with open(self.zip, "rb") as s, open(dest, "wb") as f:
            f.write(s.read())

    def test_install_windows_keeps_exe(self):
        dest = os.path.join(self.d, "flowseal")
        tag = updates.install_flowseal(dest, self.logs.append, windows=True,
                                       release=lambda: ("9.9.9", "u"), download=self.fake_download)
        self.assertEqual(tag, "9.9.9")
        self.assertTrue(os.path.exists(os.path.join(dest, "bin", "winws.exe")))
        self.assertTrue(os.path.exists(os.path.join(dest, "general.bat")))
        self.assertFalse(os.path.exists(os.path.join(self.d, "evil.txt")))

    def test_install_linux_skips_exe(self):
        dest = os.path.join(self.d, "flowseal")
        updates.install_flowseal(dest, self.logs.append, windows=False,
                                 release=lambda: ("9.9.9", "u"), download=self.fake_download)
        self.assertFalse(os.path.exists(os.path.join(dest, "bin", "winws.exe")))
        self.assertTrue(os.path.exists(os.path.join(dest, "bin", "quic_initial_www_google_com.bin")))

    def test_update_failure_keeps_old(self):
        dest = os.path.join(self.d, "flowseal")
        os.makedirs(dest)
        with open(os.path.join(dest, "general.bat"), "w") as f:
            f.write("old")

        def boom(url, dest_, progress=None):
            raise urllib.error.URLError("no route")
        with self.assertRaises(RuntimeError) as cm:
            updates.install_flowseal(dest, self.logs.append, windows=True,
                                     release=lambda: ("9.9.9", "u"), download=boom)
        self.assertIn("интернет", str(cm.exception))
        with open(os.path.join(dest, "general.bat")) as f:
            self.assertEqual(f.read(), "old")
        self.assertEqual(sorted(os.listdir(self.d)), ["flowseal", "src.zip"])

    def test_update_skips_bad_bat(self):
        dest = os.path.join(self.d, "flowseal")
        updates.install_flowseal(dest, self.logs.append, windows=True,
                                 release=lambda: ("9.9.9", "u"), download=self.fake_download)
        builtin = os.path.join(self.d, "builtin")
        n = updates.convert_builtin(dest, builtin, self.logs.append)
        self.assertEqual(n, 1)
        self.assertEqual(os.listdir(builtin), ["general.txt"])
        self.assertTrue(any("Пропускаю" in l and "BROKEN" in l for l in self.logs))

    def test_setup_lists_keeps_user_lists(self):
        dest = os.path.join(self.d, "flowseal")
        updates.install_flowseal(dest, self.logs.append, windows=True,
                                 release=lambda: ("9.9.9", "u"), download=self.fake_download)
        lists = os.path.join(self.d, "lists")
        os.makedirs(lists)
        with open(os.path.join(lists, "list-general-user.txt"), "w") as f:
            f.write("mine.example\n")
        full = os.path.join(lists, "ipset-all.full.txt")
        updates.setup_lists(dest, lists, "none", full)
        with open(os.path.join(lists, "list-general-user.txt")) as f:
            self.assertEqual(f.read(), "mine.example\n")
        with open(os.path.join(lists, "list-general.txt")) as f:
            self.assertEqual(f.read(), "discord.com\n")
        with open(os.path.join(lists, "ipset-all.txt")) as f:
            self.assertEqual(f.read(), "203.0.113.113/32\n")
        self.assertTrue(os.path.exists(os.path.join(lists, "ipset-exclude-user.txt")))
        self.assertEqual(read(full), "1.1.1.0/24\n2.2.2.0/24\n")
        updates.apply_ipset_mode(lists, "any", full)
        self.assertEqual(read(os.path.join(lists, "ipset-all.txt")), "")
        updates.apply_ipset_mode(lists, "loaded", full)
        self.assertEqual(read(os.path.join(lists, "ipset-all.txt")), "1.1.1.0/24\n2.2.2.0/24\n")


if __name__ == "__main__":
    unittest.main()
