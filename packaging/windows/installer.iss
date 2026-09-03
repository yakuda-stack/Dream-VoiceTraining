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

[CustomMessages]
english.PinTask=Pin to taskbar (Windows may refuse this)
german.PinTask=An die Taskleiste anheften (Windows lehnt das eventuell ab)

[Tasks]
; Checked by default: a program without a desktop icon is one people cannot
; find again.
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "taskbarpin"; Description: "{cm:PinTask}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; One file. The spec builds onefile, so there is no program folder to copy
; and no _internal directory beside the executable.
Source: "..\..\dist\Dream-VoiceTraining.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "pin-to-taskbar.ps1"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Pinning is attempted, never required: the helper exits without an error
; when Windows refuses, so a blocked pin cannot fail the installation.
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\pin-to-taskbar.ps1"" -Target ""{app}\{#MyAppExeName}"""; Flags: runhidden; Tasks: taskbarpin
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\pin-to-taskbar.ps1"

; Recordings and settings live under %APPDATA% and %LOCALAPPDATA% and are
; deliberately left alone when uninstalling.
