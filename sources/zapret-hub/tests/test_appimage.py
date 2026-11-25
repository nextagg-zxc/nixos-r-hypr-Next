import os
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zaprethub import helper_linux  # noqa: E402
from zaprethub.backend import linux  # noqa: E402

# Stands in for "pkexec /bin/bash install.sh --system": copies the staged
# FINGERPRINT into the "installed" root, like the real script does.
FAKE_INSTALLER = textwrap.dedent('''
    import os, shutil, sys
    sys.stdout.reconfigure(encoding="utf-8")
    script, mode, root = sys.argv[1], sys.argv[2], sys.argv[3]
    stage = os.path.dirname(os.path.dirname(os.path.dirname(script)))
    assert mode == "--system", mode
    assert os.path.isfile(os.path.join(stage, "zaprethub", "core.py"))
    assert not os.path.exists(os.path.join(stage, "zaprethub", "__pycache__"))
    os.makedirs(root, exist_ok=True)
    shutil.copy(os.path.join(stage, "FINGERPRINT"), os.path.join(root, "FINGERPRINT"))
    print("ставлю системную часть", flush=True)
''')
FAKE_HELPER = 'import sys; print("helper " + " ".join(sys.argv[1:]), flush=True)\n'


def make_bundle(root):
    for rel, text in [("zaprethub/__init__.py", "VERSION = '1'\n"), ("zaprethub/core.py", "X = 1\n"),
                      ("zaprethub/ui/window.py", "W = 1\n"),
                      ("packaging/linux/install.sh", "#!/bin/bash\n"),
                      ("packaging/linux/zapret-hub-helper", "#!/usr/bin/python3 -I\n"),
                      ("packaging/linux/zapret-hub.service", "[Service]\n"),
                      ("packaging/linux/org.zaprethub.helper.policy", "<policyconfig/>\n")]:
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        write(p, text)
    os.makedirs(os.path.join(root, "zaprethub", "__pycache__"))
    with open(os.path.join(root, "zaprethub", "__pycache__", "core.pyc"), "w") as f:
        f.write("junk")


def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class Fingerprint(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        make_bundle(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_stable(self):
        self.assertEqual(linux.fingerprint(self.root), linux.fingerprint(self.root))
        self.assertRegex(linux.fingerprint(self.root), r"^[0-9a-f]{64}$")

    def test_changes_with_helper_code_and_unit(self):
        before = linux.fingerprint(self.root)
        write(os.path.join(self.root, "zaprethub", "core.py"), "X = 2\n")
        after_code = linux.fingerprint(self.root)
        self.assertNotEqual(before, after_code)
        write(os.path.join(self.root, "packaging", "linux", "zapret-hub.service"), "[Service]\nX=1\n")
        self.assertNotEqual(after_code, linux.fingerprint(self.root))

    def test_ignores_gui_and_bytecode(self):
        # the root side never runs the GUI, so a GUI-only update needs no password
        before = linux.fingerprint(self.root)
        write(os.path.join(self.root, "zaprethub", "ui", "window.py"), "W = 2\n")
        write(os.path.join(self.root, "zaprethub", "__pycache__", "core.pyc"), "other")
        self.assertEqual(before, linux.fingerprint(self.root))


class AppImageDetect(unittest.TestCase):
    def test_only_inside_appimage(self):
        with tempfile.TemporaryDirectory() as d:
            make_bundle(d)
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("APPIMAGE", None)
                self.assertIsNone(linux.appimage_bundle(d))
            with mock.patch.dict(os.environ, {"APPIMAGE": "/home/u/ZapretHub.AppImage"}):
                self.assertEqual(linux.appimage_bundle(d), d)
                self.assertIsNone(linux.appimage_bundle(os.path.join(d, "missing")))


class SelfSetup(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.bundle = os.path.join(self.tmp.name, "bundle")
        self.installed = os.path.join(self.tmp.name, "installed")
        make_bundle(self.bundle)
        self.installer = os.path.join(self.tmp.name, "fake_installer.py")
        write(self.installer, FAKE_INSTALLER)
        self.helper = os.path.join(self.tmp.name, "fake_helper.py")
        write(self.helper, FAKE_HELPER)

    def tearDown(self):
        self.tmp.cleanup()

    def backend(self):
        # the fake installer takes the "installed" root as an extra argument after --system
        b = linux.LinuxBackend(prefix=[sys.executable, self.helper], bundle=self.bundle,
                               installed_root=self.installed, setup_prefix=[sys.executable, self.installer])
        b.setup_args = ["--system", self.installed]
        return b

    def test_first_call_installs_system_part_then_runs_helper(self):
        b, logs = self.backend(), []
        self.assertTrue(b.needs_setup())
        b.call(["install"], logs.append)
        self.assertEqual(logs, ["Ставлю системную часть: службу и права администратора для zapret",
                                "ставлю системную часть", "helper install"])
        self.assertFalse(b.needs_setup())
        # staging dir is cleaned up
        self.assertFalse([d for d in os.listdir(tempfile.gettempdir()) if d.startswith("zapret-hub-setup-")
                          and os.path.isdir(os.path.join(tempfile.gettempdir(), d, "zaprethub"))])

    def test_up_to_date_skips_setup(self):
        b, logs = self.backend(), []
        os.makedirs(self.installed)
        write(os.path.join(self.installed, "FINGERPRINT"), linux.fingerprint(self.bundle) + "\n")
        b.call(["service", "start"], logs.append)
        self.assertEqual(logs, ["helper service start"])

    def test_outdated_system_part_is_replaced(self):
        b, logs = self.backend(), []
        os.makedirs(self.installed)
        write(os.path.join(self.installed, "FINGERPRINT"), "0" * 64)
        b.call(["install"], logs.append)
        self.assertIn("ставлю системную часть", logs)

    def test_setup_that_did_not_take_is_an_error(self):
        b = self.backend()
        b.setup_args = ["--system", os.path.join(self.tmp.name, "elsewhere")]
        with self.assertRaises(RuntimeError) as cm:
            b.call(["install"], lambda m: None)
        self.assertIn("Системная часть", str(cm.exception))

    def test_diagnostics_offer_setup(self):
        b = self.backend()
        with mock.patch.object(linux, "conflicts", return_value=[]), \
                mock.patch.object(linux.subprocess, "run", return_value=mock.Mock(returncode=1, stdout="")):
            checks = {c.id: c for c in b.diagnostics()}
        self.assertEqual(checks["system"].level, "warn")
        self.assertTrue(checks["system"].fixable)

    def test_classic_install_has_no_setup(self):
        b = linux.LinuxBackend(prefix=[sys.executable, self.helper])
        self.assertFalse(b.needs_setup())


class DesktopEntry(unittest.TestCase):
    def test_points_at_the_appimage(self):
        with tempfile.TemporaryDirectory() as home:
            linux.integrate_desktop("/home/u/Apps/Zapret Hub.AppImage", home)
            with open(os.path.join(home, "applications", "zapret-hub.desktop"), encoding="utf-8") as f:
                text = f.read()
            self.assertIn('Exec="/home/u/Apps/Zapret Hub.AppImage"\n', text)
            self.assertTrue(os.path.isfile(os.path.join(home, "icons", "hicolor", "scalable", "apps",
                                                        "zapret-hub.svg")))
            linux.remove_desktop(home)
            self.assertFalse(os.path.exists(os.path.join(home, "applications", "zapret-hub.desktop")))


class HelperUninstallSystem(unittest.TestCase):
    def test_removes_system_files(self):
        with tempfile.TemporaryDirectory() as d:
            unit, lib = os.path.join(d, "zapret-hub.service"), os.path.join(d, "lib")
            write(unit, "x")
            os.makedirs(lib)
            calls = []
            with mock.patch.object(helper_linux, "SYSTEM_FILES", [unit, lib]), \
                    mock.patch.object(helper_linux, "sh", lambda cmd, check=True, **kw: calls.append(cmd)), \
                    mock.patch.object(helper_linux, "fw_down", lambda: None), \
                    mock.patch.object(helper_linux.config, "HOSTS_FILE", os.path.join(d, "hosts")), \
                    mock.patch.object(helper_linux.config, "DATA_DIR", os.path.join(d, "data")), \
                    mock.patch.object(helper_linux, "log", lambda m: None):
                helper_linux.cmd_uninstall(mock.Mock(system=True))
            self.assertFalse(os.path.exists(unit))
            self.assertFalse(os.path.exists(lib))
            self.assertIn(["systemctl", "daemon-reload"], calls)


if __name__ == "__main__":
    unittest.main()
