import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zaprethub import __main__ as entry, config, tgws  # noqa: E402


class FakeBackend:
    def __init__(self):
        self.calls = []

    def stop(self, log):
        self.calls.append("stop")

    def uninstall(self, log):
        self.calls.append("uninstall")


class Uninstall(unittest.TestCase):
    """ZapretHub.exe --uninstall: what the Windows setup's uninstaller runs."""

    def run_cli(self, argv):
        b = FakeBackend()
        with tempfile.TemporaryDirectory() as d:
            user = os.path.join(d, "user")
            os.makedirs(user)
            with mock.patch.object(config, "USER_DIR", user), \
                    mock.patch.object(tgws, "uninstall") as tg:
                rc = entry.uninstall_cli(argv, backend=b, log=lambda m: None)
            return rc, b.calls, tg.called, os.path.exists(user)

    def test_full(self):
        rc, calls, tg, user_left = self.run_cli(["--uninstall"])
        self.assertEqual((rc, calls, tg, user_left), (0, ["uninstall"], True, False))

    def test_keep_data_only_removes_the_service(self):
        rc, calls, tg, user_left = self.run_cli(["--uninstall", "--keep-data"])
        self.assertEqual((rc, calls, tg, user_left), (0, ["stop"], False, True))

    def test_failure_is_reported_as_exit_code(self):
        b = FakeBackend()
        b.uninstall = mock.Mock(side_effect=RuntimeError("занято"))
        with mock.patch.object(tgws, "uninstall"):
            self.assertEqual(entry.uninstall_cli(["--uninstall"], backend=b, log=lambda m: None), 1)


if __name__ == "__main__":
    unittest.main()
