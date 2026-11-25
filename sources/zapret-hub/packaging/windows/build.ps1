# Build ZapretHub.exe on Windows. Run from the repo root in PowerShell:
#   powershell -ExecutionPolicy Bypass -File packaging\windows\build.ps1
# Needs Python 3.11+ (python.org). Creates .venv-win and dist\ZapretHub\.
# (ASCII only: Windows PowerShell 5.1 reads BOM-less scripts as ANSI.)
$py = if ($env:PYTHON) { $env:PYTHON } else { "py" }
function Step($what, $cmd) {
    & $cmd
    if ($LASTEXITCODE) { Write-Host "FAILED: $what (exit $LASTEXITCODE)"; exit 1 }
}
if (-not (Test-Path .venv-win)) { Step "venv" { & $py -m venv .venv-win } }
Step "pip" { .\.venv-win\Scripts\python -m pip install --disable-pip-version-check -q PySide6 psutil pyinstaller }
Step "tests" { $env:QT_QPA_PLATFORM = "offscreen"; .\.venv-win\Scripts\python -m unittest discover -s tests }
Step "pyinstaller" { .\.venv-win\Scripts\python -m PyInstaller --noconfirm --clean --log-level WARN packaging\windows\zaprethub.spec }
Compress-Archive -Force -Path dist\ZapretHub -DestinationPath dist\ZapretHub-windows.zip
Write-Host "OK: dist\ZapretHub\ZapretHub.exe, dist\ZapretHub-windows.zip"
# Installer (Inno Setup 6+): ISCC from $env:ISCC, PATH or the default install folder
$iscc = if ($env:ISCC) { $env:ISCC } else { (Get-Command iscc -ErrorAction SilentlyContinue).Source }
if (-not $iscc) { $iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" }
if (Test-Path $iscc) {
    $ver = (Select-String -Path zaprethub\__init__.py -Pattern 'VERSION = "(.*)"').Matches[0].Groups[1].Value
    Step "inno setup" { & $iscc /Q "/DAppVersion=$ver" "/DSrc=$PWD\dist\ZapretHub" "/DOut=$PWD\dist" packaging\windows\zaprethub.iss }
    Write-Host "OK: dist\ZapretHub-Setup-$ver.exe"
} else {
    Write-Host "Inno Setup not found: skipping ZapretHub-Setup.exe (choco install innosetup)"
}
