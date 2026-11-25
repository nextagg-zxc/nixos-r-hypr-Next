# PyInstaller spec: one-folder build of ZapretHub.exe that always asks for admin.
# Build on Windows from the repo root:  pyinstaller packaging/windows/zaprethub.spec
import os

root = os.path.abspath(os.path.join(SPECPATH, "..", ".."))
assets = os.path.join(root, "zaprethub", "ui", "assets")

a = Analysis(
    [os.path.join(SPECPATH, "launch.py")],
    pathex=[root],
    datas=[(assets, "zaprethub/ui/assets")],
    hiddenimports=["psutil", "zaprethub.backend.windows"],
    excludes=["tkinter", "PySide6.QtWebEngineCore", "PySide6.QtQml", "PySide6.QtQuick", "PySide6.Qt3DCore",
              "PySide6.QtMultimedia", "PySide6.QtPdf", "PySide6.QtCharts", "PySide6.QtDataVisualization"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="ZapretHub",
    icon=os.path.join(SPECPATH, "icon.ico"),
    console=False,
    uac_admin=True,
    version=os.path.join(SPECPATH, "version.txt"),
)
coll = COLLECT(exe, a.binaries, a.datas, name="ZapretHub")
