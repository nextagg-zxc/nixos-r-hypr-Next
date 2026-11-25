; Inno Setup script: ZapretHub-Setup-<version>.exe from the PyInstaller folder.
; iscc /DAppVersion=1.0.0 /DSrc=<path to dist\ZapretHub> /DOut=<output dir> packaging\windows\zaprethub.iss
; Uninstall runs ZapretHub.exe --uninstall [--keep-data]: the same cleanup as the app's own button
; (service, WinDivert, hosts block, C:\ProgramData\ZapretHub, TG WS Proxy).

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#ifndef Src
  #define Src "..\..\dist\ZapretHub"
#endif
#ifndef Out
  #define Out "..\..\dist"
#endif

[Setup]
AppId={{8F3C6A2E-5B1D-4E7A-9C40-2D7E1F6B9A53}
AppName=Zapret Hub
AppVersion={#AppVersion}
AppVerName=Zapret Hub {#AppVersion}
AppPublisher=Zapret Hub
VersionInfoVersion={#AppVersion}
DefaultDirName={autopf}\Zapret Hub
DisableProgramGroupPage=yes
DisableDirPage=auto
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir={#Out}
OutputBaseFilename=ZapretHub-Setup-{#AppVersion}
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\ZapretHub.exe
UninstallDisplayName=Zapret Hub
WizardStyle=modern
WizardImageFile=wizard-large-100.bmp,wizard-large-200.bmp
WizardSmallImageFile=wizard-small-100.bmp,wizard-small-200.bmp
Compression=lzma2/ultra64
SolidCompression=yes
; the app is closed in PrepareToInstall; Restart Manager would only ask about it again
CloseApplications=no

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[CustomMessages]
russian.DesktopIcon=Значок на рабочем столе
russian.LaunchApp=Запустить Zapret Hub
russian.AskRemoveData=Удалить также скачанные стратегии, свои списки сайтов и настройки?%n%nНажми «Нет», если собираешься поставить Zapret Hub снова — всё останется как было.

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIcon}"

[InstallDelete]
; a new build may drop libraries; never mix old and new ones
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "{#Src}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Zapret Hub"; Filename: "{app}\ZapretHub.exe"
Name: "{autodesktop}\Zapret Hub"; Filename: "{app}\ZapretHub.exe"; Tasks: desktopicon

[Run]
; runascurrentuser: postinstall entries run unelevated by default, and ZapretHub.exe requires admin (error 740)
Filename: "{app}\ZapretHub.exe"; Description: "{cm:LaunchApp}"; Flags: nowait postinstall skipifsilent runascurrentuser

[Code]
var
  KeepData: Boolean;

procedure CloseApp();
var
  Code: Integer;
begin
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/IM ZapretHub.exe /F', '', SW_HIDE, ewWaitUntilTerminated, Code);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  // the bypass service keeps running: it lives in C:\ProgramData\ZapretHub, not here
  CloseApp();
  Result := '';
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Code: Integer;
  Params: String;
begin
  // usUninstall comes after "remove Zapret Hub?" was confirmed, while the files are still here
  if CurUninstallStep = usUninstall then
  begin
    KeepData := SuppressibleMsgBox(CustomMessage('AskRemoveData'), mbConfirmation, MB_YESNO, IDYES) = IDNO;
    CloseApp();
    Params := '--uninstall';
    if KeepData then
      Params := Params + ' --keep-data';
    Exec(ExpandConstant('{app}\ZapretHub.exe'), Params, '', SW_HIDE, ewWaitUntilTerminated, Code);
  end;
end;
