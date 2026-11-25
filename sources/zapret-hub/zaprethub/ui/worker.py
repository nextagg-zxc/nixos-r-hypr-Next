"""Run blocking work off the GUI thread. The function gets log(str) and
emit(dict) callables; results come back through Qt signals on the GUI thread."""

import threading
import traceback

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class Signals(QObject):
    log = Signal(str)
    event = Signal(dict)
    done = Signal(object)
    failed = Signal(object)


class Worker(QRunnable):
    def __init__(self, fn):
        super().__init__()
        self.fn = fn
        self.signals = Signals()
        self.cancel = threading.Event()

    def run(self):
        try:
            res = self.fn(self.signals.log.emit, self.signals.event.emit)
        except Exception as e:  # noqa: BLE001 - shown to the user as text
            e.trace = traceback.format_exc()
            self.signals.failed.emit(e)
        else:
            self.signals.done.emit(res)


_keep = set()   # QRunnable signal objects must outlive the slot calls


def start(fn, on_done=None, on_failed=None, on_log=None, on_event=None):
    w = Worker(fn)
    _keep.add(w.signals)
    if on_log:
        w.signals.log.connect(on_log)
    if on_event:
        w.signals.event.connect(on_event)

    def finish(slot):
        def f(x):
            _keep.discard(w.signals)
            if slot:
                slot(x)
        return f
    w.signals.done.connect(finish(on_done))
    w.signals.failed.connect(finish(on_failed))
    w.setAutoDelete(True)
    QThreadPool.globalInstance().start(w)
    return w
