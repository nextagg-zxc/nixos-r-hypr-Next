"""Самопроверка Магазина: подменённые индекс, flatpak и root-помощник; HOME — временный.
Печатает SELFTEST PASS / FAIL; снимки — $STORE_SHOT-<шаг>.png."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path


def fixture(root: Path):
    (root / "home").mkdir()
    (root / "flake/hosts/share").mkdir(parents=True)
    (root / "flake/hosts/share/packages.json").write_text("[]")
    (root / "sysapps").mkdir()
    (root / "index.json").write_text(json.dumps({
        "legacyPackages.x86_64-linux.vlc": {"pname": "vlc", "version": "3.0.21", "description": "Cross-platform media player"},
        "legacyPackages.x86_64-linux.htop": {"pname": "htop", "version": "3.4", "description": "Interactive process viewer"}}))
    log = root / "calls.log"
    flat = root / "flatpak"
    flat.write_text(f"""#!/usr/bin/env bash
echo "FLATPAK $*" >>{log}
case "$1" in
  search) printf 'org.vinegarhq.Sober\\tSober\\tRoblox client for Linux\\t1.6\\n' ;;
  list) [ -e {root}/sober-installed ] && echo org.vinegarhq.Sober ;;
  install) touch {root}/sober-installed; d={root}/home/.local/share/flatpak/exports/share/applications; mkdir -p "$d"
           printf '[Desktop Entry]\\nType=Application\\nName=Sober\\nExec=sober\\n' >"$d/org.vinegarhq.Sober.desktop"; echo "Installing… done" ;;
esac
""")
    helper = root / "helper"
    helper.write_text(f"""#!/usr/bin/env bash
echo "HELPER $*" >>{log}
if [ "$1" = packages-add ]; then
  python3 -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); d.append(sys.argv[2]); json.dump(d,open(p,"w"))' {root}/flake/hosts/share/packages.json "$2"
  printf '[Desktop Entry]\\nType=Application\\nName=VLC\\nExec=vlc\\n' >{root}/sysapps/vlc.desktop
fi
echo "building…"; echo '@@{{"type": "done", "ok": true}}'
""")
    for f in (flat, helper):
        f.chmod(0o755)
    return log


def main(argv):
    root = Path(tempfile.mkdtemp(prefix="store-selftest-"))
    log = fixture(root)
    os.environ.update(HOME=str(root / "home"), NIXOS_STORE_INDEX=str(root / "index.json"),
                      NIXOS_STORE_FLATPAK=str(root / "flatpak"), NIXOS_SETTINGS_HELPER=str(root / "helper"),
                      NIXOS_SHARE_ETC=str(root / "flake"), NIXOS_STORE_SYSAPPS=str(root / "sysapps"),
                      XDG_CURRENT_DESKTOP="KDE")
    from . import ui  # задаёт версии Gtk/Adw

    from gi.repository import GLib, Gtk  # noqa: E402

    result = {"ok": False, "msg": "не дошли до конца"}

    def check(c, m):
        if not c:
            raise AssertionError(m)

    def shot(win, name):
        p = os.environ.get("STORE_SHOT")
        if not p:
            return
        paintable = Gtk.WidgetPaintable(widget=win)
        snap = Gtk.Snapshot()
        paintable.snapshot(snap, win.get_width(), win.get_height())
        win.get_renderer().render_texture(snap.to_node(), None).save_to_png(f"{p}-{name}.png")

    def close_dialog(win):
        d = win.get_visible_dialog()
        if d:
            d.close_btn.emit("clicked")

    def wait(cond, n=20):
        for _ in range(n):
            if cond():
                return True
            yield
        return cond()

    def steps(win):
        yield
        shot(win, "start")
        win.search.set_text("vlc")
        win.do_search()
        yield from wait(lambda: "nixpkgs:vlc" in win.rows)
        check("nixpkgs:vlc" in win.rows, f"vlc не найден: {list(win.rows)}")
        shot(win, "search")
        win.rows["nixpkgs:vlc"].emit("clicked")
        yield from wait(lambda: "HELPER packages-add vlc" in log.read_text() and win.get_visible_dialog() is not None
                        and win.get_visible_dialog().close_btn.get_sensitive())
        shot(win, "install")
        close_dialog(win)
        yield
        desk = Path(os.environ["HOME"]) / "Desktop"
        yield from wait(lambda: (desk / "vlc.desktop").exists())
        check(json.loads((root / "flake/hosts/share/packages.json").read_text()) == ["vlc"], "packages.json")
        check((desk / "vlc.desktop").exists() and os.access(desk / "vlc.desktop", os.X_OK), "нет ярлыка vlc")
        win.search.set_text("roblox")
        win.do_search()
        yield from wait(lambda: "flathub:org.vinegarhq.Sober" in win.rows)
        check("flathub:org.vinegarhq.Sober" in win.rows, "Sober не найден")
        win.rows["flathub:org.vinegarhq.Sober"].emit("clicked")
        yield from wait(lambda: "FLATPAK install" in log.read_text() and win.get_visible_dialog() is not None
                        and win.get_visible_dialog().close_btn.get_sensitive())
        close_dialog(win)
        yield from wait(lambda: (desk / "org.vinegarhq.Sober.desktop").exists())
        check((desk / "org.vinegarhq.Sober.desktop").exists(), "нет ярлыка Sober")
        win.installed_btn.set_active(True)
        yield from wait(lambda: {"nixpkgs:vlc", "flathub:org.vinegarhq.Sober"} <= set(win.rows))
        check({"nixpkgs:vlc", "flathub:org.vinegarhq.Sober"} <= set(win.rows), f"установленные: {list(win.rows)}")
        shot(win, "installed")
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
        GLib.timeout_add(300, tick)

    ui.make_app(on_window).run([sys.argv[0]])
    shutil.rmtree(root, ignore_errors=True)
    print("SELFTEST PASS" if result["ok"] else f"SELFTEST FAIL: {result['msg']}", flush=True)
    return 0 if result["ok"] else 1
