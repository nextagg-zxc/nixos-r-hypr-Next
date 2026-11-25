import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zaprethub.backend import base, windows  # noqa: E402

EXE = r"C:\ProgramData\ZapretHub\flowseal\bin\winws.exe"


def svc(name, status="running", display=None, pid=0):
    return {"name": name, "display_name": display or name, "status": status, "pid": pid}


def snapshot(**kw):
    snap = {"services": [svc("BFE")], "processes": [], "proxy": (False, ""), "tcp_timestamps": True,
            "doh": True, "hosts": "127.0.0.1 localhost\n", "windivert_files": True}
    snap.update(kw)
    return snap


def by_id(checks):
    return {c.id: c for c in checks}


class ServiceCmd(unittest.TestCase):
    def test_service_cmd(self):
        self.assertEqual(windows.service_cmd(EXE, ["--wf-tcp=80", "--new"]),
                         '"C:\\ProgramData\\ZapretHub\\flowseal\\bin\\winws.exe" --wf-tcp=80 --new')

    def test_service_cmd_rejects_spaces(self):
        with self.assertRaises(ValueError):
            windows.service_cmd(EXE, ["--hostlist=C:\\My Lists\\a.txt"])
        with self.assertRaises(ValueError):
            windows.service_cmd(EXE, ['--x="y"'])

    def test_service_cmd_rejects_shell_chars(self):
        for bad in ("--x=a&calc", "--x=%PATH%", "--x=a|b", "--x=a^b", "--x=<y>"):
            with self.assertRaises(ValueError, msg=bad):
                windows.service_cmd(EXE, [bad])
        windows.service_cmd(EXE, ["--dpi-desync-fake-tls=!", "--filter-tcp=~80", "--ipset=@C:\\a_b+c.txt"])

    def test_run_never_uses_shell(self):
        from unittest import mock
        with mock.patch.object(windows.subprocess, "run") as r:
            r.return_value = mock.Mock(returncode=0, stdout=b"", stderr=b"")
            windows.WinSys().run('sc create ZapretHub binPath= "x"')
            windows.WinSys().run(["sc", "query"])
        self.assertTrue(all(c.kwargs.get("shell", False) is False for c in r.call_args_list))

    def test_sc_create_line(self):
        line = windows.sc_create_line('"C:\\a\\winws.exe" --x=1', auto=True)
        self.assertEqual(line, 'sc create ZapretHub binPath= "\\"C:\\a\\winws.exe\\" --x=1" '
                               'DisplayName= "Zapret Hub" start= auto')
        self.assertIn("start= demand", windows.sc_create_line("x", auto=False))


class Conflicts(unittest.TestCase):
    def test_conflicts_detected(self):
        snap = snapshot(services=[svc("BFE"), svc("zapret"), svc("GoodbyeDPI"), svc("ZapretHub", pid=100)],
                        processes=[(100, "winws.exe"), (200, "winws.exe")])
        ids = [c for c in windows.conflicts(snap)]
        self.assertEqual(ids, ["flowseal_service", "goodbyedpi", "stray_winws"])

    def test_our_winws_is_not_a_conflict(self):
        snap = snapshot(services=[svc("ZapretHub", pid=100), svc("WinDivert")], processes=[(100, "winws.exe")])
        self.assertEqual(windows.conflicts(snap), [])

    def test_stale_windivert(self):
        snap = snapshot(services=[svc("WinDivert")], processes=[])
        self.assertEqual(windows.conflicts(snap), ["windivert_stale"])

    def test_stopped_flowseal_service_is_fine(self):
        snap = snapshot(services=[svc("zapret", status="stopped")])
        self.assertEqual(windows.conflicts(snap), [])


class Diagnostics(unittest.TestCase):
    def test_all_good(self):
        checks = windows.evaluate(snapshot())
        self.assertTrue(all(c.level == "ok" for c in checks), [c for c in checks if c.level != "ok"])

    def test_not_installed_is_not_reported_as_missing_windivert(self):
        c = by_id(windows.evaluate(snapshot(installed=False, windivert_files=False)))
        self.assertNotIn("windivert_files", c)
        self.assertEqual((c["installed"].level, c["installed"].fixable), ("warn", True))

    def test_problems(self):
        snap = snapshot(services=[svc("Killer Network Service"), svc("NordVPN Service", display="NordVPN")],
                        processes=[(5, "AdguardSvc.exe")], proxy=(True, "127.0.0.1:8080"),
                        tcp_timestamps=False, doh=False, hosts="1.2.3.4 youtube.com\n", windivert_files=False)
        c = by_id(windows.evaluate(snap))
        self.assertEqual((c["bfe"].level, c["bfe"].fixable), ("error", True))
        self.assertEqual((c["tcp_timestamps"].level, c["tcp_timestamps"].fixable), ("warn", True))
        self.assertEqual(c["proxy"].level, "warn")
        self.assertIn("127.0.0.1:8080", c["proxy"].detail)
        self.assertEqual(c["killer"].level, "error")
        self.assertEqual(c["adguard"].level, "error")
        self.assertEqual(c["vpn"].level, "warn")
        self.assertIn("NordVPN", c["vpn"].detail)
        self.assertEqual(c["doh"].level, "warn")
        self.assertEqual(c["hosts"].level, "warn")
        self.assertEqual(c["windivert_files"].level, "error")


class FakeSys:
    def __init__(self, services, processes=()):
        self._services, self._processes, self.cmds = services, list(processes), []

    def services(self):
        return self._services

    def processes(self):
        return self._processes

    def run(self, cmd):
        self.cmds.append(cmd)
        return 0, ""

    def snapshot(self, full=True):
        return snapshot(services=self._services, processes=self._processes)

    def sddl(self, path):
        return TRUSTED

    def create_secure_dir(self, path):
        pass


TRUSTED = "O:BAG:SYD:PAI(A;OICI;FA;;;BA)(A;OICI;FA;;;SY)(A;OICI;0x1200a9;;;BU)"


class Sddl(unittest.TestCase):
    def test_ours_is_trusted(self):
        self.assertTrue(windows.sddl_trusted(TRUSTED))
        self.assertTrue(windows.sddl_trusted("O:SYD:P(A;OICIID;FA;;;SY)(A;OICIID;FA;;;BA)(A;OICIID;FR;;;BU)"))

    def test_untrusted(self):
        bad = [
            "",                                                               # unknown
            "O:S-1-5-21-1-2-3-1001D:PAI(A;OICI;FA;;;BA)",                     # user owner
            "O:BAD:AI(A;OICI;FA;;;BA)(A;OICI;FA;;;SY)",                       # inherits from ProgramData
            "O:BAD:P(A;OICI;FA;;;BA)(A;OICI;0x1301bf;;;BU)",                  # users can modify
            "O:BAD:P(A;OICI;FA;;;BA)(A;OICIIO;FA;;;CO)",                      # creator owner full
            "O:BAD:P(A;OICI;FA;;;BA)(A;;FA;;;S-1-5-21-1-2-3-1001)",           # a user SID
        ]
        for sd in bad:
            self.assertFalse(windows.sddl_trusted(sd), sd)


class DirSys(FakeSys):
    """Fake with a real temp dir: sddl() answers per path, create makes the dir."""

    def __init__(self, sddl):
        super().__init__([svc("BFE")])
        self._sddl, self.created = sddl, []

    def sddl(self, path):
        return self._sddl if os.path.isdir(path) else ""

    def create_secure_dir(self, path):
        os.mkdir(path)
        self.created.append(path)
        self._sddl = TRUSTED


class DataDirTrust(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.data = os.path.join(self.tmp.name, "ZapretHub")

    def tearDown(self):
        self.tmp.cleanup()

    def plant(self):
        os.makedirs(os.path.join(self.data, "flowseal", "bin"))
        p = os.path.join(self.data, "flowseal", "bin", "winws.exe")
        open(p, "w").close()
        return p

    def backend(self, sddl):
        from unittest import mock
        fs = DirSys(sddl)
        b = windows.WindowsBackend(fs)
        patch = mock.patch.multiple(windows.config, DATA_DIR=self.data)
        patch.start()
        self.addCleanup(patch.stop)
        return b, fs

    def test_untrusted_dir_is_replaced_before_install(self):
        from unittest import mock
        planted = self.plant()
        b, fs = self.backend("O:S-1-5-21-1-2-3-1001D:AI(A;OICI;FA;;;S-1-5-21-1-2-3-1001)")
        with mock.patch.object(windows.updates, "install_flowseal", side_effect=RuntimeError("stop")):
            with self.assertRaises(RuntimeError):
                b.install(lambda m: None)
        self.assertFalse(os.path.exists(planted))
        self.assertEqual(fs.created, [self.data])
        self.assertEqual(os.listdir(self.tmp.name), ["ZapretHub"])

    def test_start_never_runs_from_untrusted_dir(self):
        planted = self.plant()
        b, fs = self.backend("O:BAD:AI(A;OICI;FA;;;BA)(A;OICIIO;FA;;;CO)")
        b.is_installed = lambda: os.path.exists(planted)
        with self.assertRaises(RuntimeError):
            b.start(lambda m: None)
        self.assertFalse(os.path.exists(planted))
        self.assertFalse(any("create" in str(c) for c in fs.cmds))

    def test_trusted_dir_is_kept(self):
        planted = self.plant()
        b, fs = self.backend(TRUSTED)
        b.secure(lambda m: None)
        self.assertTrue(os.path.exists(planted))
        self.assertEqual(fs.created, [])

    def test_secure_rechecks_after_dir_removed(self):
        import shutil
        b, fs = self.backend("")
        b.secure(lambda m: None)
        shutil.rmtree(self.data)
        fs._sddl = ""
        b.secure(lambda m: None)
        self.assertEqual(fs.created, [self.data, self.data])

    def test_final_check_rejects_junction(self):
        from unittest import mock
        b, fs = self.backend("")
        with mock.patch.object(windows, "is_link", side_effect=lambda p: os.path.isdir(p)):
            with self.assertRaises(RuntimeError):
                b.secure(lambda m: None)

    def test_failed_acl_query_never_wipes_data(self):
        planted = self.plant()
        b, fs = self.backend(TRUSTED)
        fs.sddl = lambda path: None          # PowerShell missing / blocked
        with self.assertRaises(RuntimeError):
            b.secure(lambda m: None)
        self.assertTrue(os.path.exists(planted))

    def test_bad_strategy_change_is_not_saved(self):
        import json
        b, fs = self.backend(TRUSTED)
        b.secure(lambda m: None)
        from unittest import mock
        builtin, custom = os.path.join(self.data, "strategies-builtin"), os.path.join(self.data, "strategies")
        os.makedirs(builtin)
        os.makedirs(custom)
        with open(os.path.join(builtin, "general.txt"), "w") as f:
            f.write("--wf-tcp=443 --filter-tcp=443 --dpi-desync=fake\n")
        with open(os.path.join(custom, "broken.txt"), "w") as f:
            f.write("--filter-tcp=%Nope% --dpi-desync=fake\n")
        state = os.path.join(self.data, "state.json")
        with mock.patch.multiple(windows.config, BUILTIN_DIR=builtin, CUSTOM_DIR=custom, STATE_FILE=state):
            with self.assertRaises(RuntimeError):
                b.set_state({"strategy": "broken"}, lambda m: None)
            saved = json.load(open(state)) if os.path.exists(state) else {"strategy": "general"}
        self.assertEqual(saved["strategy"], "general")

    def test_missing_dir_is_created_secure(self):
        b, fs = self.backend("")
        b.secure(lambda m: None)
        self.assertEqual(fs.created, [self.data])


class Start(unittest.TestCase):
    def test_start_refuses_with_flowseal_running(self):
        fs = FakeSys([svc("BFE"), svc("zapret", pid=7)], [(7, "winws.exe")])
        b = windows.WindowsBackend(fs)
        b.is_installed = lambda: True
        with self.assertRaises(base.ConflictError) as cm:
            b.start(lambda m: None)
        self.assertEqual(cm.exception.ids, ["flowseal_service"])
        self.assertFalse(any("create" in str(c) for c in fs.cmds))


class WinSysServices(unittest.TestCase):
    def test_service_with_huge_config_is_still_listed(self):
        """psutil's as_dict() calls QueryServiceConfigW, which fails with
        WinError 1734 for our ~10 KB binPath; status and pid must still work."""
        import types
        from unittest import mock

        class Svc:
            def __init__(self, name, status, pid):
                self._n, self._s, self._p = name, status, pid

            def name(self):
                return self._n

            def display_name(self):
                return self._n + " display"

            def status(self):
                return self._s

            def pid(self):
                return self._p

            def as_dict(self):
                raise OSError(1734, "array bounds are invalid")

        fake = types.SimpleNamespace(win_service_iter=lambda: [Svc("ZapretHub", "running", 42), Svc("BFE", "running", 7)])
        with mock.patch.dict(sys.modules, {"psutil": fake}):
            got = windows.WinSys().services()
        self.assertEqual(got[0], {"name": "ZapretHub", "display_name": "ZapretHub display", "status": "running",
                                  "pid": 42})
        self.assertEqual(len(got), 2)


class Recommend(unittest.TestCase):
    def test_best_strategy(self):
        res = {"general": {"ok": 20, "total": 30, "ping": 40},
               "general (ALT)": {"ok": 30, "total": 30, "ping": 90},
               "general (ALT2)": {"ok": 30, "total": 30, "ping": 50},
               "broken": {"error": "не запустилась"}}
        self.assertEqual(base.best_strategy(res), "general (ALT2)")
        self.assertIsNone(base.best_strategy({}))
        self.assertIsNone(base.best_strategy({"x": {"ok": 0, "total": 30}}))


if __name__ == "__main__":
    unittest.main()
