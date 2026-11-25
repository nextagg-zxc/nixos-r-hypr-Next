"""Strategy test loop shared by the Windows backend and the Linux helper:
start a strategy, check every target, stop, score. Events are dicts:
strategy / strategy_error / target / strategy_done / done."""

import concurrent.futures
import time

from . import probe
from .backend.base import best_strategy


def run(names, start, stop, targets, emit, cancel, timeout=4, check=probe.check_target):
    results = {}
    cancelled = False
    for i, name in enumerate(names):
        if cancel.is_set():
            cancelled = True
            break
        emit({"type": "strategy", "name": name, "index": i, "total": len(names)})
        try:
            start(name)
        except Exception as e:  # noqa: BLE001 - a broken strategy is a result
            results[name] = {"error": str(e), "at": time.time()}
            emit({"type": "strategy_error", "name": name, "error": str(e)})
            continue
        rows = []
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
                for res in ex.map(lambda t: check(t, timeout), targets):
                    rows.append(res)
                    emit({"type": "target", "strategy": name, **res})
        finally:
            stop()
        ok = sum(probe.score(r)[0] for r in rows)
        total = sum(probe.score(r)[1] for r in rows)
        pings = [r["ping"] for r in rows if r.get("ping")]
        results[name] = {"ok": ok, "total": total, "ping": round(sum(pings) / len(pings)) if pings else None,
                         "at": time.time()}
        emit({"type": "strategy_done", "name": name, **results[name]})
    else:
        cancelled = cancel.is_set() and len(results) < len(names)
    emit({"type": "done", "cancelled": cancelled, "best": best_strategy(results)})
    return results


def merge(old, new):
    out = dict(old or {})
    out.update(new)
    return out
