"""Start the GUI: one instance, themed, platform backend.
--uninstall [--keep-data]: no window; the Windows setup's uninstaller runs it."""

import os
import shutil
import sys

from . import config


def is_admin():
    if not config.IS_WINDOWS:
        return True
    import ctypes
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except OSError:
        return False


def uninstall_cli(argv, backend=None, log=print):
    """Remove the service (and with no --keep-data everything we downloaded or
    wrote). Returns the exit code."""
    from . import tgws
    from .backend import get_backend
    backend = backend or get_backend()
    try:
        if "--keep-data" in argv:
            backend.stop(log)
        else:
            backend.uninstall(log)
            tgws.uninstall()
            shutil.rmtree(config.USER_DIR, ignore_errors=True)
    except Exception as e:  # noqa: BLE001 - the uninstaller only needs the exit code
        log(f"ОШИБКА: {e}")
        return 1
    return 0


def main():
    if "--uninstall" in sys.argv[1:]:
        return uninstall_cli(sys.argv[1:])

    from PySide6.QtCore import Qt
    from PySide6.QtNetwork import QLocalServer, QLocalSocket
    from PySide6.QtWidgets import QApplication, QMessageBox

    from .backend import get_backend
    from .ui import theme, tray
    from .ui.window import MainWindow

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName("Zapret Hub")
    app.setDesktopFileName("zapret-hub")
    theme.apply(app)

    key = "zapret-hub-single-instance"
    sock = QLocalSocket()
    sock.connectToServer(key)
    if sock.waitForConnected(300):   # already running: bring it forward
        sock.write(b"show")
        sock.waitForBytesWritten(300)
        return 0
    if not is_admin():
        QMessageBox.critical(None, "Zapret Hub", "Запусти программу от имени администратора: "
                             "без этого Windows не даст включить обход.")
        return 1

    if not config.IS_WINDOWS and os.environ.get("APPIMAGE"):
        from .backend import linux
        try:
            linux.integrate_desktop(os.environ["APPIMAGE"])
        except OSError:
            pass   # a menu entry is a convenience; never block the start

    win = MainWindow(get_backend())
    server = QLocalServer()
    QLocalServer.removeServer(key)
    server.listen(key)
    server.newConnection.connect(lambda: (server.nextPendingConnection(), win.showNormal(), win.raise_(),
                                          win.activateWindow()))
    tray.setup(win)
    win.resize(1120, 740)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
