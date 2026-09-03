; Inno Setup script for Dream-VoiceTraining.
; Called by build_windows.ps1, which passes the version in:
;   ISCC.exe /DMyAppVersion=1.0.9 installer.iss
;
; Builds a plain wizard: welcome, licence, folder, shortcut options, ready,
; install, finish. Installs machine-wide under Program Files, which needs
; administrator rights -- Windows asks for them once, at the start.
;
; Recordings and settings are never written into the install folder. They
; live under %APPDATA% and %LOCALAPPDATA% and survive both an update and an
; uninstall, which is why the uninstaller does not touch them.
;
; ASCII only, so older Inno Setup versions cannot mis-read it.

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#define MyAppName "Dream-VoiceTraining"
#define MyAppPublisher "Yakuda"
#define MyAppURL "https://github.com/yakuda-stack/Dream-VoiceTraining"
#define MyAppExeName "Dream-VoiceTraining.exe"

[Setup]
; Never change this GUID: Windows recognises an update by it, and a new one
; would leave the old version installed beside the new.
AppId={{7C1F2A64-4E3B-4C0A-9E2D-3A8B5D1F0C77}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases

; C:\Program Files\Dream-VoiceTraining on 64-bit Windows, Program Files (x86)
; on 32-bit. Writing there needs administrator rights.
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; The shortcut goes into the top level of the start menu, so there is no
; group folder to name and no page asking about one.
DisableProgramGroupPage=yes
; The welcome page is worth keeping: it is where the version is stated.
DisableWelcomePage=no
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
; PySide6 needs Windows 10 or newer; saying so now beats a broken start.
MinVersion=10.0

OutputDir=..\..\dist
OutputBaseFilename={#MyAppName}-{#MyAppVersion}-setup
SetupIconFile=..\dream-voicetraining.ico
LicenseFile=..\..\LICENSE
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes

; What Apps & features shows.
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
; Offers to close a running copy instead of failing on a locked file.
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[CustomMessages]
english.StartMenuIcon=Create a start menu entry
german.StartMenuIcon=Eintrag im Startmenue anlegen
english.ShortcutGroup=Shortcuts:
german.ShortcutGroup=Verknuepfungen:

[Tasks]
; Both asked on their own page of the wizard, both ticked: a program with no
; icon anywhere is one people cannot find again. Untick and nothing is
; created.
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:ShortcutGroup}"
Name: "startmenuicon"; Description: "{cm:StartMenuIcon}"; GroupDescription: "{cm:ShortcutGroup}"

[Files]
; One file. The spec builds onefile, so there is no program folder to copy
; and no _internal directory beside the executable.
Source: "..\..\dist\Dream-VoiceTraining.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\LICENSE"; DestDir: "{app}"; DestName: "LICENSE.txt"; Flags: ignoreversion
Source: "..\..\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; A comment gives the Windows search box something besides the file name to
; match on, so typing "voice" finds the entry.
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "Voice training: pitch, resonance, weight and voice quality"; Tasks: startmenuicon
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "Voice training: pitch, resonance, weight and voice quality"; Tasks: desktopicon
; Always there, whatever was ticked: without it an uninstall can only be
; started from the settings app.
Name: "{autoprograms}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Registry]
; Lets Win+R and a command prompt start the program by name.
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\{#MyAppExeName}"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\{#MyAppExeName}"; ValueType: string; ValueName: "Path"; ValueData: "{app}"; Flags: uninsdeletekey

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; The program writes nothing into its own folder, but a crash log or a stray
; file should not keep the folder alive after an uninstall.
Type: filesandordirs; Name: "{app}"

; Deliberately not removed on uninstall, because they are the user's work:
;   %APPDATA%\Dream-VoiceTraining        settings
;   %LOCALAPPDATA%\Dream-VoiceTraining   recordings
