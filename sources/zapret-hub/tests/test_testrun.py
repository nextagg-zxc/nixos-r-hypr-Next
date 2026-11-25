import os
import sys
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zaprethub import testrun  # noqa: E402

TARGETS = [{"name": "a", "url": "https://a", "ping": "a"}, {"name": "b", "url": "https://b", "ping": "b"}]


class Run(unittest.TestCase):
    def test_runs_each_strategy_and_scores(self):
        calls, events = [], []
        current = {}

        def start(name):
            if name == "bad":
                raise RuntimeError("winws завершился")
            current["s"] = name
            calls.append(("start", name))

        def stop():
            calls.append(("stop", current.get("s")))

        def check(t, timeout):
            ok = "OK" if current["s"] == "good" else "ERROR"
            return {"name": t["name"], "HTTP": ok, "TLS1.2": ok, "TLS1.3": "OK", "ping": 10.0}

        res = testrun.run(["good", "bad", "meh"], start, stop, TARGETS, events.append, threading.Event(),
                          check=check)
        self.assertEqual(res["good"], {"ok": 6, "total": 6, "ping": 10, "at": res["good"]["at"]})
        self.assertEqual(res["meh"]["ok"], 2)
        self.assertEqual(res["bad"]["error"], "winws завершился")
        self.assertEqual([c for c in calls if c[0] == "start"], [("start", "good"), ("start", "meh")])
        types = [e["type"] for e in events]
        self.assertEqual(types.count("strategy"), 3)
        self.assertEqual(types.count("target"), 4)
        self.assertEqual(types.count("strategy_error"), 1)
        self.assertEqual(types[-1], "done")
        self.assertEqual(events[-1]["best"], "good")

    def test_cancel_stops_early(self):
        cancel = threading.Event()
        events = []

        def start(name):
            cancel.set()

        res = testrun.run(["x", "y"], start, lambda: None, TARGETS, events.append, cancel,
                          check=lambda t, to: {"name": t["name"], "HTTP": "OK"})
        self.assertEqual(list(res), ["x"])
        self.assertTrue(events[-1]["cancelled"])

    def test_merge_results(self):
        old = {"a": {"ok": 1, "total": 2}, "b": {"ok": 2, "total": 2}}
        self.assertEqual(testrun.merge(old, {"a": {"ok": 2, "total": 2}}),
                         {"a": {"ok": 2, "total": 2}, "b": {"ok": 2, "total": 2}})


if __name__ == "__main__":
    unittest.main()
