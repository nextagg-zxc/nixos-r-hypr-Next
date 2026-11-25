"""Самопроверка окна: python3 -m system_settings --selftest
Подменённый помощник (NIXOS_SETTINGS_HELPER) записывает вызовы и stdin; проверяем, что окно просит
то, что надо. Снимки разделов — $SETTINGS_SHOT-<раздел>.png. Печатает SELFTEST PASS / FAIL."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

FAKE_HELPER = r"""#!/usr/bin/env bash
log=%(log)s
{ printf 'ARGS %%s\n' "$*"; case "$1" in status|generations) ;; *) printf 'STDIN '; cat; echo ;; esac; } >>"$log"
case "$1" in
  generations) echo '[{"number": 3, "date": 1764000000, "version": "26.11.3", "current": true},
                {"number": 2, "date": 1763900000, "version": "26.11.2", "current": false}]' ;;
  status) echo '{"secureboot": {"setup_mode": false}, "luks": [{"device": "/dev/vda2", "tpm2": false}],
           "windows": [{"esp": "0f1e2d3c-aaaa-bbbb-cccc-112233445566", "device": "/dev/vda1"}]}' ;;
  secureboot-prepare) echo "Создаю ключи…"; echo '@@{"type": "secureboot", "need": "setup_mode"}'; echo '@@{"type": "done", "ok": true}' ;;
  *) echo "building..."; echo '@@{"type": "done", "ok": true}' ;;
esac
"""


def main(argv):
    root = Path(tempfile.mkdtemp(prefix="settings-selftest-"))
    (root / "etc/hosts/share").mkdir(parents=True)
    (root / "etc/hosts/share/choices.json").write_text(json.dumps({"kernel": "cachyos", "system": {"iommu": True}}))
    log = root / "calls.log"
    h = root / "helper"
    h.write_text(FAKE_HELPER % {"log": log})
    h.chmod(0o755)
    look = root / "nixos-kde-look"
    look.write_text(f"#!/usr/bin/env bash\necho \"LOOK $*\" >>{log}\n")
    look.chmod(0o755)
    (root / "etc/flake.lock").write_text(json.dumps({"nodes": {"nixpkgs": {"locked": {"rev": "aaa"}}}}))
    (root / "channel").write_text("bbb\n")
    flat = root / "flatpak"
    flat.write_text("#!/usr/bin/env bash\n[ \"$1\" = remote-ls ] && echo org.vinegarhq.Sober\nexit 0\n")
    flat.chmod(0o755)
    os.environ.update(NIXOS_SHARE_ETC=str(root / "etc"), NIXOS_SETTINGS_HELPER=str(h), NIXOS_KDE_LOOK=str(look),
                      NIXOS_UPDATE_CHANNEL_URL=(root / "channel").as_uri(), NIXOS_STORE_FLATPAK=str(flat))

    from . import ui  # задаёт версии Gtk/Adw

    from gi.repository import GLib, Gtk  # noqa: E402

    result = {"ok": False, "msg": "не дошли до конца"}

    def calls():
        return log.read_text() if log.exists() else ""

    def check(cond, msg):
        if not cond:
            raise AssertionError(msg)

    def shot(win, name):
        path = os.environ.get("SETTINGS_SHOT")
        if not path:
            return
        paintable = Gtk.WidgetPaintable(widget=win)
        snap = Gtk.Snapshot()
        paintable.snapshot(snap, win.get_width(), win.get_height())
        tex = win.get_renderer().render_texture(snap.to_node(), None)
        tex.save_to_png(f"{path}-{name}.png")

    def select(win, key):
        i = [s[0] for s in win.sections].index(key)
        win.sidebar.select_row(win.sidebar.get_row_at_index(i))

    def steps(win):
        yield
        check([s[0] for s in win.sections] == ["system", "look", "boot", "update"], f"разделы: {win.sections}")
        shot(win, "system")
        win.kernel_rows["zen"].set_active(True)
        win.sw_mitig.set_active(True)
        win.apply_btn.emit("clicked")
        for _ in range(10):
            yield
            if "STDIN" in calls():
                break
        line = [l for l in calls().splitlines() if l.startswith("STDIN")][-1]
        patch = json.loads(line[6:])
        check(patch["kernel"] == "zen" and patch["system"]["mitigationsOff"] is True, f"патч: {patch}")
        yield
        shot(win, "run")
        dlg = win.get_visible_dialog()
        if dlg:
            dlg.close_btn.emit("clicked")
        yield
        select(win, "look")
        yield
        shot(win, "look")
        win.look_btns["win10"].emit("clicked")
        for _ in range(5):
            yield
        check("LOOK apply win10" in calls(), "вид Windows 10 не применён")
        select(win, "boot")
        yield
        shot(win, "boot")
        win.find_btn.emit("clicked")
        for _ in range(8):
            yield
            if calls().count("ARGS set") >= 2:
                break
        last = [l for l in calls().splitlines() if l.startswith("STDIN")][-1]
        check(json.loads(last[6:]) == {"boot": {"windows": [{"name": "Windows",
                                                              "esp": "0f1e2d3c-aaaa-bbbb-cccc-112233445566"}]}},
              f"Windows: {last}")
        dlg = win.get_visible_dialog()
        if dlg:
            dlg.close_btn.emit("clicked")
        for _ in range(3):
            yield
        win.sb_btn.emit("clicked")
        for _ in range(6):
            yield
        check("ARGS secureboot-prepare" in calls(), "Secure Boot не вызван")
        dlg = win.get_visible_dialog()
        if dlg:
            dlg.close_btn.emit("clicked")
        for _ in range(3):
            yield
        select(win, "update")
        for _ in range(4):
            yield
        win.check_btn.emit("clicked")
        for _ in range(6):
            yield
            if "Есть обновления" in (win.upd_row.get_subtitle() or ""):
                break
        check("система" in win.upd_row.get_subtitle() and "Flathub: 1" in win.upd_row.get_subtitle(),
              f"проверка: {win.upd_row.get_subtitle()}")
        shot(win, "update")
        check(2 in win.gen_buttons and 3 not in win.gen_buttons, f"поколения: {list(win.gen_buttons)}")
        win.gen_buttons[2].emit("clicked")
        for _ in range(6):
            yield
        check("ARGS rollback 2" in calls(), "откат не вызван")
        result.update(ok=True, msg="")

    def on_window(win):
        it = steps(win)

        def tick():
            try:
                next(it)
                return True
            except StopIteration:
                pass
            except Exception as err:  # noqa: BLE001
                result.update(ok=False, msg=f"{type(err).__name__}: {err}")
            win.get_application().quit()
            return False

        GLib.timeout_add(500, tick)

    ui.make_app(on_window).run([sys.argv[0]])
    shutil.rmtree(root, ignore_errors=True)
    print("SELFTEST PASS" if result["ok"] else f"SELFTEST FAIL: {result['msg']}", flush=True)
    return 0 if result["ok"] else 1
