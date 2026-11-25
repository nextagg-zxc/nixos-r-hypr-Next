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


class InstallWithNixpkgsNfqws(Base):
    def test_install_skips_zapret_with_nixpkgs_nfqws(self):
        nfqws = os.path.join(self.tmp.name, "nfqws")
        with open(nfqws, "w") as f:
            f.write("#!/bin/sh\n")
        os.chmod(nfqws, os.stat(nfqws).st_mode | stat.S_IXUSR)
        written = {}

        def fake_write(path, text, mode=0o644):
            written[path] = text

        boom = mock.Mock(side_effect=AssertionError("install_zapret не должен вызываться"))
        with mock.patch.dict(os.environ, {"ZAPRETHUB_NFQWS": nfqws}), \
                mock.patch.object(config, "NFQWS", nfqws), \
                mock.patch.object(helper_linux, "install_zapret", boom), \
                mock.patch.object(helper_linux, "watch_stdin"), \
                mock.patch.object(helper_linux, "event"), \
                mock.patch.object(updates, "install_flowseal", return_value="1.9.0"), \
                mock.patch.object(updates, "convert_builtin"), \
                mock.patch.object(updates, "setup_lists"), \
                mock.patch.object(updates, "install_targets"), \
                mock.patch.object(updates, "write_file", side_effect=fake_write), \
                mock.patch.object(config, "CUSTOM_DIR", os.path.join(self.tmp.name, "strategies")):
            helper_linux.cmd_install(mock.Mock())
        boom.assert_not_called()
        import json
        self.assertEqual(json.loads(written[config.VERSIONS_FILE])["zapret"], "nixpkgs")


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
    def test_nfqws_and_nixos_from_env(self):
        import importlib
        with mock.patch.dict(os.environ, {"ZAPRETHUB_NFQWS": "/nix/store/x/bin/nfqws", "ZAPRETHUB_NIXOS": "1"}):
            c = importlib.reload(config)
            self.assertEqual(c.NFQWS, "/nix/store/x/bin/nfqws")
            self.assertTrue(c.NIXOS)
        env = {k: v for k, v in os.environ.items() if k not in ("ZAPRETHUB_NFQWS", "ZAPRETHUB_NIXOS")}
        with mock.patch.dict(os.environ, env, clear=True):
            c = importlib.reload(config)
            self.assertTrue(c.NFQWS.endswith(os.path.join("zapret", "nfq", "nfqws")))
            self.assertFalse(c.NIXOS)


if __name__ == "__main__":
    unittest.main()
