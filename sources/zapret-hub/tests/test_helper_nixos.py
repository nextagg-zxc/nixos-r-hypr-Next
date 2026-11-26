"""NixOS mode (ZAPRETHUB_NIXOS / ZAPRETHUB_NFQWS / ZAPRETHUB_HELPER): autostart through a flag file,
nfqws from nixpkgs instead of downloading zapret, hosts block kept in a file the NixOS module re-applies."""
import os
import stat
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zaprethub import config, core, helper_linux, updates  # noqa: E402
from zaprethub.backend import linux  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        self.calls = []
        patches = {
            "DATA_DIR": d,
            "AUTOSTART_FLAG": os.path.join(d, "autostart"),
            "HOSTS_BLOCK_FILE": os.path.join(d, "hosts.block"),
            "HOSTS_FILE": os.path.join(d, "hosts"),
            "STATE_FILE": os.path.join(d, "state.json"),
            "VERSIONS_FILE": os.path.join(d, "versions.json"),
        }
        for k, v in patches.items():
            p = mock.patch.object(config, k, v, create=True)
            p.start()
            self.addCleanup(p.stop)
        p = mock.patch.object(helper_linux, "sh", side_effect=self.fake_sh)
        p.start()
        self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)

    def fake_sh(self, cmd, check=True, **kw):
        self.calls.append(list(cmd))
        return mock.Mock(returncode=0, stdout="", stderr="")


class Autostart(Base):
    def test_autostart_flag_nixos(self):
        with mock.patch.object(config, "NIXOS", True, create=True):
            helper_linux.set_autostart(True)
            self.assertTrue(os.path.exists(config.AUTOSTART_FLAG))
            helper_linux.set_autostart(False)
            self.assertFalse(os.path.exists(config.AUTOSTART_FLAG))
            helper_linux.set_autostart(False)  # повторно — без ошибки
        self.assertFalse([c for c in self.calls if c[:1] == ["systemctl"]])

    def test_autostart_systemctl_elsewhere(self):
        with mock.patch.object(config, "NIXOS", False, create=True):
            helper_linux.set_autostart(True)
            helper_linux.set_autostart(False)
        self.assertIn(["systemctl", "enable", helper_linux.SERVICE], self.calls)
        self.assertIn(["systemctl", "disable", helper_linux.SERVICE], self.calls)
        self.assertFalse(os.path.exists(config.AUTOSTART_FLAG))

    def test_service_stop_clears_autostart(self):
        open(config.AUTOSTART_FLAG, "w").close()
        with mock.patch.object(config, "NIXOS", True, create=True), \
                mock.patch.object(helper_linux, "fw_down"):
            helper_linux.cmd_service(mock.Mock(action="stop"))
        self.assertIn(["systemctl", "stop", helper_linux.SERVICE], self.calls)
        self.assertFalse(os.path.exists(config.AUTOSTART_FLAG))


class Fix(Base):
    def test_fix_nixos_managed_unit(self):
        # NixOS: юниты в /etc/systemd только для чтения — disable не сработает, маскируем до перезагрузки
        with mock.patch.object(config, "NIXOS", True, create=True), mock.patch.object(helper_linux, "log"):
            helper_linux.cmd_fix(mock.Mock(id="zapret_gui"))
        self.assertIn(["systemctl", "stop", "zapret-gui.service"], self.calls)
        self.assertIn(["systemctl", "mask", "--runtime", "zapret-gui.service"], self.calls)
        self.assertNotIn(["systemctl", "disable", "--now", "zapret-gui.service"], self.calls)
        self.assertIn(["nft", "delete", "table", "inet", "zapret_gui"], self.calls)

    def test_fix_regular_unit(self):
        with mock.patch.object(config, "NIXOS", False, create=True), mock.patch.object(helper_linux, "log"):
            helper_linux.cmd_fix(mock.Mock(id="zapret_gui"))
        self.assertIn(["systemctl", "disable", "--now", "zapret-gui.service"], self.calls)


class InstallFreshZapret(Base):
    """NixOS тоже качает свежий zapret (стратегии Flowseal ждут свежий nfqws); nfqws из nixpkgs —
    только запасной вариант, если скачать/подобрать не вышло."""

    def setUp(self):
        super().setUp()
        self.fallback = os.path.join(self.tmp.name, "nixpkgs-nfqws")
        with open(self.fallback, "w") as f:
            f.write("#!/bin/sh\n")
        os.chmod(self.fallback, os.stat(self.fallback).st_mode | stat.S_IXUSR)
        self.written = {}
        for k, v in {"ZAPRET_DIR": os.path.join(self.tmp.name, "zapret"),
                     "CUSTOM_DIR": os.path.join(self.tmp.name, "strategies")}.items():
            p = mock.patch.object(config, k, v)
            p.start()
            self.addCleanup(p.stop)
        for target, attr, kw in ((helper_linux, "watch_stdin", {}), (helper_linux, "event", {}),
                                 (updates, "install_flowseal", {"return_value": "1.9.0"}),
                                 (updates, "convert_builtin", {}), (updates, "setup_lists", {}),
                                 (updates, "install_targets", {}),
                                 (updates, "write_file", {"side_effect": self.fake_write})):
            p = mock.patch.object(target, attr, **kw)
            p.start()
            self.addCleanup(p.stop)

    def fake_write(self, path, text, mode=0o644):
        self.written[path] = text

    def versions(self):
        import json
        return json.loads(self.written[config.VERSIONS_FILE])

    def test_downloads_fresh_zapret_even_with_fallback(self):
        def fake_install(work, versions):
            versions["zapret"] = "v72.13"
        with mock.patch.object(config, "NFQWS_FALLBACK", self.fallback), \
                mock.patch.object(helper_linux, "install_zapret", side_effect=fake_install) as inst:
            helper_linux.cmd_install(mock.Mock())
        inst.assert_called_once()
        self.assertEqual(self.versions()["zapret"], "v72.13")

    def test_falls_back_to_nixpkgs_when_download_fails(self):
        with mock.patch.object(config, "NFQWS_FALLBACK", self.fallback), \
                mock.patch.object(helper_linux, "install_zapret", side_effect=OSError("нет сети")):
            helper_linux.cmd_install(mock.Mock())
            self.assertEqual(config.nfqws(), self.fallback)
        self.assertEqual(self.versions()["zapret"], "nixpkgs")

    def test_dies_without_any_nfqws(self):
        with mock.patch.object(config, "NFQWS_FALLBACK", ""), \
                mock.patch.object(helper_linux, "install_zapret", side_effect=OSError("нет сети")), \
                self.assertRaises(SystemExit):
            helper_linux.cmd_install(mock.Mock())

    def test_nfqws_prefers_downloaded(self):
        with mock.patch.object(config, "NFQWS_FALLBACK", self.fallback):
            self.assertEqual(config.nfqws(), self.fallback)          # скачанного ещё нет
            os.makedirs(os.path.join(config.ZAPRET_DIR, "nfq"))
            dl = os.path.join(config.ZAPRET_DIR, "nfq", "nfqws")
            with open(dl, "w") as f:
                f.write("#!/bin/sh\n")
            os.chmod(dl, 0o755)
            self.assertEqual(config.nfqws(), dl)
        with mock.patch.object(config, "NFQWS_FALLBACK", ""):
            os.remove(dl)
            self.assertEqual(config.nfqws(), dl)                     # путь по умолчанию, даже если файла нет


class Hosts(Base):
    def test_hosts_block_saved_and_removed(self):
        with open(config.HOSTS_FILE, "w") as f:
            f.write("127.0.0.1 localhost\n")
        with mock.patch.object(updates, "fetch_hosts", return_value="1.2.3.4 discord.media"):
            helper_linux.cmd_hosts(mock.Mock(action="update"))
        hosts = open(config.HOSTS_FILE).read()
        self.assertIn(core.HOSTS_BEGIN, hosts)
        self.assertIn("1.2.3.4 discord.media", hosts)
        self.assertEqual(open(config.HOSTS_BLOCK_FILE).read().strip(), "1.2.3.4 discord.media")
        helper_linux.cmd_hosts(mock.Mock(action="remove"))
        self.assertNotIn(core.HOSTS_BEGIN, open(config.HOSTS_FILE).read())
        self.assertFalse(os.path.exists(config.HOSTS_BLOCK_FILE))


    def test_hosts_restore(self):
        # NixOS после пересборки кладёт /etc/hosts заново — блок возвращается из файла
        with open(config.HOSTS_FILE, "w") as f:
            f.write("127.0.0.1 localhost\n")
        helper_linux.cmd_hosts_restore(mock.Mock())          # блока нет — hosts не трогаем
        self.assertEqual(open(config.HOSTS_FILE).read(), "127.0.0.1 localhost\n")
        with open(config.HOSTS_BLOCK_FILE, "w") as f:
            f.write("1.2.3.4 discord.media\n")
        helper_linux.cmd_hosts_restore(mock.Mock())
        helper_linux.cmd_hosts_restore(mock.Mock())          # повторно — без второго блока
        hosts = open(config.HOSTS_FILE).read()
        self.assertEqual(hosts.count(core.HOSTS_BEGIN), 1)
        self.assertTrue(hosts.startswith("127.0.0.1 localhost\n"))
        self.assertIn("1.2.3.4 discord.media", hosts)


class BackendHelperPath(unittest.TestCase):
    def test_backend_helper_env(self):
        with mock.patch.dict(os.environ, {"ZAPRETHUB_HELPER": "/x/helper"}):
            self.assertEqual(linux.LinuxBackend().prefix, ["pkexec", "/x/helper"])
        env = {k: v for k, v in os.environ.items() if k not in ("ZAPRETHUB_HELPER", "APPIMAGE")}
        with mock.patch.dict(os.environ, env, clear=True):
            prefix = linux.LinuxBackend().prefix
        self.assertEqual(prefix[0], "pkexec")
        self.assertIn(prefix[1], (linux.INSTALLED_HELPER, linux.DEV_HELPER))


class ConfigEnv(unittest.TestCase):
    def test_fallback_and_nixos_from_env(self):
        import importlib
        with mock.patch.dict(os.environ, {"ZAPRETHUB_NFQWS_FALLBACK": "/nix/store/x/bin/nfqws", "ZAPRETHUB_NIXOS": "1"}):
            c = importlib.reload(config)
            self.assertEqual(c.NFQWS_FALLBACK, "/nix/store/x/bin/nfqws")
            self.assertTrue(c.NIXOS)
        env = {k: v for k, v in os.environ.items() if k not in ("ZAPRETHUB_NFQWS_FALLBACK", "ZAPRETHUB_NIXOS")}
        with mock.patch.dict(os.environ, env, clear=True):
            c = importlib.reload(config)
            self.assertEqual(c.NFQWS_FALLBACK, "")
            self.assertTrue(c.nfqws().endswith(os.path.join("zapret", "nfq", "nfqws")))
            self.assertFalse(c.NIXOS)


if __name__ == "__main__":
    unittest.main()
