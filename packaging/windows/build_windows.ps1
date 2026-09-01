# Baut Dream-VoiceTraining fuer Windows.
#
#   powershell -ExecutionPolicy Bypass -File packaging\windows\build_windows.ps1
#
# Ergebnis:
#   dist\Dream-VoiceTraining\Dream-VoiceTraining.exe      (portabel)
#   dist\Dream-VoiceTraining-<version>-setup.exe          (falls Inno Setup da ist)
#
# Voraussetzungen: Python 3.10+ aus python.org (nicht der Store, dort ist
# der Zugriff auf %LOCALAPPDATA% eingeschraenkt). Inno Setup ist optional.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $Root

function Say($text) { Write-Host ":: $text" -ForegroundColor Cyan }

$Version = (Select-String -Path "paths.py" -Pattern 'APP_VERSION = "([^"]+)"').Matches[0].Groups[1].Value
Say "Dream-VoiceTraining $Version"

Say "Bauumgebung anlegen"
if (-not (Test-Path ".venv-build")) { python -m venv .venv-build }
$Py = ".\.venv-build\Scripts\python.exe"
& $Py -m pip install --upgrade pip wheel --quiet
& $Py -m pip install --quiet -r requirements.txt
& $Py -m pip install --quiet pyinstaller

Say "Alte Ergebnisse entfernen"
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

Say "PyInstaller"
& $Py -m PyInstaller --noconfirm --clean packaging\windows\dream-voicetraining.spec

$ExePath = "dist\Dream-VoiceTraining\Dream-VoiceTraining.exe"
if (-not (Test-Path $ExePath)) { throw "EXE wurde nicht erzeugt." }
$SizeMb = [math]::Round((Get-ChildItem -Recurse "dist\Dream-VoiceTraining" |
                         Measure-Object -Property Length -Sum).Sum / 1MB, 1)
Say "fertig: $ExePath  ($SizeMb MB)"

Say "Portables ZIP"
Compress-Archive -Path "dist\Dream-VoiceTraining\*" `
                 -DestinationPath "dist\Dream-VoiceTraining-$Version-windows-portable.zip" `
                 -Force

$Inno = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (Test-Path $Inno) {
    Say "Installer bauen"
    & $Inno "/DMyAppVersion=$Version" "packaging\windows\installer.iss"
} else {
    Write-Host "!! Inno Setup nicht gefunden — nur die portable Fassung gebaut." -ForegroundColor Yellow
    Write-Host "   https://jrsoftware.org/isdl.php"
}

Say "Ergebnisse:"
Get-ChildItem dist\*.zip, dist\*.exe -ErrorAction SilentlyContinue |
    ForEach-Object { Write-Host "   $($_.Name)" }
