"""GUI smoke test: offscreen, fake backend. Saves a PNG per page into
ZAPRETHUB_SHOTS (if set) for eyeballing."""

import os
import sys
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from PySide6.QtCore import QCoreApplication
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
except ImportError:  # PySide6 missing: the rest of the suite still runs
    QApplication = None

from zaprethub.backend.base import Backend, Check, ConflictError, Status  # noqa: E402


class FakeBackend(Backend):
    def __init__(self, installed=True, running=False, conflicts=()):
        self.st = Status(installed=installed, running=running, strategy="general (ALT3)",
                         versions={"flowseal": "1.10.3", "zapret": "v72.13"}, conflicts=list(conflicts))
        self.calls = []

    def is_installed(self):
        return self.st.installed

    def strategies(self):
        return [("general", "builtin"), ("general (ALT)", "builtin"), ("general (ALT3)", "builtin"),
                ("мой", "custom")]

    def state(self):
        return {"strategy": self.st.strategy, "game_filter": "off", "ipset": "none", "autostart": True}

    def results(self):
        return {"general (ALT3)": {"ok": 30, "total": 30, "ping": 41}, "general": {"ok": 12, "total": 30, "ping": 60}}

    def read_user_list(self, name):
        return "example.org\n" if name == "list-general-user.txt" else ""

    def status(self):
        return self.st

    def install(self, log):
        self.calls.append("install")
        log("Скачиваю…")
        self.st.installed = True

    def start(self, log):
        self.calls.append("start")
        if self.st.conflicts:
            raise ConflictError(["flowseal_service"])
        self.st.running = True

    def stop(self, log):
        self.calls.append("stop")
        self.st.running = False

    def set_state(self, changes, log):
        self.calls.append(("set_state", changes))

    def set_autostart(self, on, log):
        self.calls.append(("autostart", on))

    def write_list(self, name, text, log):
        self.calls.append(("write_list", name, text))

    def diagnostics(self):
        return [Check("bfe", "ok", "Служба BFE работает"),
                Check("tcp_timestamps", "warn", "Выключены TCP timestamps", "Многие стратегии без них не работают.",
                      True, "Включить"),
                Check("flowseal_service", "error", "Работает служба zapret от Flowseal", "Мешает.", True, "Удалить")]

    def run_tests(self, names, on_event, cancel, timeout=4):
        self.calls.append(("tests", tuple(names)))
        for n in names:
            on_event({"type": "strategy", "name": n, "index": 0, "total": len(names)})
            on_event({"type": "strategy_done", "name": n, "ok": 10, "total": 10, "ping": 20})
        on_event({"type": "done", "cancelled": False, "best": names[0]})
        return {}


def wait_idle(win, ms=5000):
    for _ in range(ms // 20):
        QCoreApplication.processEvents()
        if not win.busy:
            return
        QTest.qWait(20)
    raise AssertionError("task did not finish")


@unittest.skipIf(QApplication is None, "PySide6 not installed")
class Smoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from zaprethub.ui import theme
        cls.app = QApplication.instance() or QApplication([])
        theme.apply(cls.app)
        cls.shots = os.environ.get("ZAPRETHUB_SHOTS") or tempfile.mkdtemp()
        cls.home = tempfile.TemporaryDirectory()
        from zaprethub import config
        from unittest import mock
        user = os.path.join(cls.home.name, "zapret-hub")
        cls.patch = mock.patch.multiple(config, USER_DIR=user, USER_SETTINGS=os.path.join(user, "settings.json"),
                                        MTPROTO_CACHE=os.path.join(user, "mtproto.json"))
        cls.patch.start()

    @classmethod
    def tearDownClass(cls):
        cls.patch.stop()
        cls.home.cleanup()

    def make(self, **kw):
        from zaprethub.ui.window import MainWindow
        win = MainWindow(FakeBackend(**kw), check_updates=False)
        win.resize(1100, 720)
        win.show()
        QCoreApplication.processEvents()
        return win

    def test_every_page_renders(self):
        win = self.make()
        for i, key in enumerate(win.page_keys()):
            win.show_page(key)
            QTest.qWait(50)
            self.assertTrue(win.grab().save(os.path.join(self.shots, f"{i}-{key}.png")))
        win.close()

    def test_standard_buttons_are_russian(self):
        from PySide6.QtWidgets import QDialogButtonBox
        from zaprethub.ui import theme
        theme.install_translations(self.app)
        box = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No | QDialogButtonBox.Cancel)
        texts = sorted(b.text().replace("&", "") for b in box.buttons())
        self.assertEqual(texts, ["Да", "Нет", "Отмена"])

    def test_opens_on_home_even_if_last_page_differs(self):
        from zaprethub import config
        os.makedirs(config.USER_DIR, exist_ok=True)
        with open(config.USER_SETTINGS, "w") as f:
            f.write('{"page": "diagnostics"}')
        win = self.make()
        self.assertIs(win.stack.currentWidget(), win.pages["home"])
        win.close()

    def test_not_installed_text_mentions_zapret(self):
        # и на NixOS программа качает свежий zapret (nfqws из nixpkgs — только запасной)
        from unittest import mock
        from zaprethub import config
        for nixos in (True, False):
            with mock.patch.object(config, "NIXOS", nixos):
                win = self.make(installed=False)
                self.assertIn("скачает zapret и стратегии Flowseal", win.pages["home"].sub.text())
                win.close()

    def test_power_installs_then_starts(self):
        win = self.make(installed=False)
        win.pages["home"].power.click()
        wait_idle(win)
        self.assertEqual(win.backend.calls[:2], ["install", "start"])
        self.assertTrue(win.backend.st.running)
        win.close()

    def test_power_stops_when_running(self):
        win = self.make(running=True)
        win.pages["home"].power.click()
        wait_idle(win)
        self.assertEqual(win.backend.calls, ["stop"])
        win.close()

    def test_recommendation_applies_best(self):
        win = self.make()
        win.pages["strategies"].apply_best()
        wait_idle(win)
        self.assertIn(("set_state", {"strategy": "general (ALT3)"}), win.backend.calls)
        win.close()

    def test_strategy_tests_report_progress(self):
        win = self.make()
        page = win.pages["strategies"]
        page.start_tests(["general", "general (ALT)"])
        wait_idle(win)
        self.assertEqual(win.backend.calls[-1], ("tests", ("general", "general (ALT)")))
        self.assertIn("general", page.result_text("general"))
        win.close()


if __name__ == "__main__":
    unittest.main()
