; Inno Setup script for Dream-VoiceTraining.
; Called by build_windows.ps1, which passes the version in.
; ASCII only, so older Inno Setup versions cannot mis-read it.

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#define MyAppName "Dream-VoiceTraining"
#define MyAppPublisher "Yakuda"
#define MyAppURL "https://github.com/yakuda-stack/Dream-VoiceTraining"
#define MyAppExeName "Dream-VoiceTraining.exe"

[Setup]
AppId={{7C1F2A64-4E3B-4C0A-9E2D-3A8B5D1F0C77}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; No group folder to click through: the entry goes straight into Programs,
; which is the folder Windows Search reads for the start menu.
DisableProgramGroupPage=yes
; Install without administrator rights: everything lands in the user
; profile and nobody has to click away an elevation prompt.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\..\dist
OutputBaseFilename={#MyAppName}-{#MyAppVersion}-setup
SetupIconFile=..\dream-voicetraining.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
LicenseFile=..\..\LICENSE

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
; Checked by default: a program without a desktop icon is one people cannot
; find again.
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; One file. The spec builds onefile, so there is no program folder to copy
; and no _internal directory beside the executable.
Source: "..\..\dist\Dream-VoiceTraining.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; {autoprograms} instead of {group}: the shortcut sits at the top level of the
; start menu, so typing "dream" or "voice" into the Windows search box finds
; it. A comment gives the search something besides the file name to match.
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "Voice training: pitch, resonance, weight and voice quality"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Comment: "Voice training: pitch, resonance, weight and voice quality"

[Registry]
; Lets Win+R and a command prompt start the program by name.
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\{#MyAppExeName}"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\{#MyAppExeName}"; ValueType: string; ValueName: "Path"; ValueData: "{app}"; Flags: uninsdeletekey

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent


; Recordings and settings live under %APPDATA% and %LOCALAPPDATA% and are
; deliberately left alone when uninstalling.
