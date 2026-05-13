; ──────────────────────────────────────────────────────────────────────────────
; Steel Connection Designer — Inno Setup 6 script
;
; Prerequisites:
;   1. Run PyInstaller first:  pyinstaller steel_connections.spec --noconfirm
;   2. Compile this script with Inno Setup 6 (https://jrsoftware.org/isinfo.php)
;      or run:  ISCC.exe installer\setup.iss
; ──────────────────────────────────────────────────────────────────────────────

#define AppName      "Steel Connection Designer"
#define AppVersion   "0.1.0"
#define AppPublisher "ebrahimraeyat"
#define AppURL       "https://github.com/ebrahimraeyat/steel_connections"
#define AppExeName   "SteelConnections.exe"
#define DistDir      "..\dist\SteelConnections"

[Setup]
AppId={{F3A8C2D1-4B67-4E9A-8C3F-2D5A7B1E9F04}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
; OutputDir is relative to the .iss file location (installer\)
OutputDir=..\dist
OutputBaseFilename=SteelConnectionDesigner-{#AppVersion}-Setup
SetupIconFile=icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Entire PyInstaller output folder
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}";      Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
