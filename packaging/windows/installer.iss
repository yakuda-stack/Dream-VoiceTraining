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

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\Dream-VoiceTraining\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

; Recordings and settings live under %APPDATA% and %LOCALAPPDATA% and are
; deliberately left alone when uninstalling.
