import os
import sys
import tempfile
import textwrap
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zaprethub.backend import linux  # noqa: E402

FAKE = textwrap.dedent('''
    import json, sys
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    cmd = sys.argv[1]
    if cmd == "echo-stdin":
        print("got " + sys.stdin.read().strip(), flush=True)
    elif cmd == "events":
        print("Начинаю", flush=True)
        print("@@" + json.dumps({"type": "strategy", "name": "general"}), flush=True)
        print("@@" + json.dumps({"type": "done", "ok": True}), flush=True)
    elif cmd == "fail":
        print("что-то делаю", flush=True)
        print("ОШИБКА: стратегия не прошла проверку", flush=True)
        sys.exit(1)
    elif cmd == "wait-stdin":
        print("жду", flush=True)
        sys.stdin.read()
        print("отменено", flush=True)
    elif cmd == "pkexec-dismissed":
        sys.exit(126)
''')


class ParseLine(unittest.TestCase):
    def test_event_and_log(self):
        self.assertEqual(linux.parse_helper_line('@@{"type": "done"}\n'), ("event", {"type": "done"}))
        self.assertEqual(linux.parse_helper_line("Скачиваю…\n"), ("log", "Скачиваю…"))
        self.assertEqual(linux.parse_helper_line("@@not json\n"), ("log", "@@not json"))


class Call(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.script = os.path.join(cls.tmp.name, "fake_helper.py")
        with open(cls.script, "w", encoding="utf-8") as f:
            f.write(FAKE)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def backend(self):
        return linux.LinuxBackend(prefix=[sys.executable, self.script])

    def test_stdin_is_passed(self):
        logs = []
        self.backend().call(["echo-stdin"], logs.append, stdin_text='{"a": 1}')
        self.assertEqual(logs, ['got {"a": 1}'])

    def test_events(self):
        logs, events = [], []
        self.backend().call(["events"], logs.append, on_event=events.append)
        self.assertEqual(logs, ["Начинаю"])
        self.assertEqual([e["type"] for e in events], ["strategy", "done"])

    def test_error_message_surfaces(self):
        with self.assertRaises(RuntimeError) as cm:
            self.backend().call(["fail"], lambda m: None)
        self.assertEqual(str(cm.exception), "стратегия не прошла проверку")

    def test_cancel_closes_stdin(self):
        logs, cancel = [], threading.Event()
        threading.Timer(0.3, cancel.set).start()
        self.backend().call(["wait-stdin"], logs.append, cancel=cancel)
        self.assertEqual(logs, ["жду", "отменено"])

    def test_auth_dismissed(self):
        with self.assertRaises(RuntimeError) as cm:
            self.backend().call(["pkexec-dismissed"], lambda m: None)
        self.assertIn("пароль", str(cm.exception))


class Conflicts(unittest.TestCase):
    def test_units(self):
        active = {"zapret-gui.service"}
        self.assertEqual(linux.conflicts(lambda u: u in active), ["zapret_gui"])
        self.assertEqual(linux.conflicts(lambda u: False), [])


class Launcher(unittest.TestCase):
    def test_uses_system_python(self):
        # python3 from PATH may be mise/pyenv/conda without the distro's PySide6
        path = os.path.join(os.path.dirname(__file__), "..", "packaging", "linux", "zapret-hub")
        with open(path) as f:
            lines = [l.strip() for l in f if l.strip().startswith("PY=")]
        self.assertEqual(lines, ["PY=/usr/bin/python3"])


if __name__ == "__main__":
    unittest.main()
