# Builds Dream-VoiceTraining for Windows.
#
#   powershell -ExecutionPolicy Bypass -File packaging\windows\build_windows.ps1
#
# Output:
#   dist\Dream-VoiceTraining\Dream-VoiceTraining.exe          (portable)
#   dist\Dream-VoiceTraining-<version>-windows-portable.zip
#   dist\Dream-VoiceTraining-<version>-setup.exe               (needs Inno Setup)
#
# Requirements: Python 3.10+ from python.org. NOT the Microsoft Store build,
# which restricts access to %LOCALAPPDATA%. Inno Setup is optional.
#
# This file is intentionally ASCII only. Windows PowerShell 5.1 reads .ps1
# files without a byte order mark as ANSI, which mangles accented characters
# and can break parsing.

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $Root

function Say([string]$Text) { Write-Host ":: $Text" -ForegroundColor Cyan }
function Warn([string]$Text) { Write-Host "!! $Text" -ForegroundColor Yellow }

# --- Python finden -----------------------------------------------------

$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) { $PythonCmd = Get-Command py -ErrorAction SilentlyContinue }
if (-not $PythonCmd) {
    throw "Python was not found. Install Python 3.10 or newer from python.org."
}

# --- Version aus paths.py lesen ----------------------------------------

$Match = Select-String -Path "paths.py" -Pattern 'APP_VERSION = "([^"]+)"'
if (-not $Match) { throw "APP_VERSION not found in paths.py" }
$Version = $Match.Matches[0].Groups[1].Value
Say "Dream-VoiceTraining $Version"

# --- Bauumgebung -------------------------------------------------------

Say "Creating build environment"
if (-not (Test-Path ".venv-build")) {
    & $PythonCmd.Source -m venv .venv-build
}
$Py = Join-Path $Root ".venv-build\Scripts\python.exe"
if (-not (Test-Path $Py)) { throw "Virtual environment is incomplete: $Py" }

& $Py -m pip install --upgrade pip wheel --quiet
& $Py -m pip install --quiet -r requirements.txt
& $Py -m pip install --quiet pyinstaller
if ($LASTEXITCODE -ne 0) { throw "Installing dependencies failed." }

# --- Bauen -------------------------------------------------------------

Say "Removing previous output"
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

Say "Running PyInstaller"
& $Py -m PyInstaller --noconfirm --clean "packaging\windows\dream-voicetraining.spec"
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed." }

$ExePath = "dist\Dream-VoiceTraining\Dream-VoiceTraining.exe"
if (-not (Test-Path $ExePath)) { throw "No executable was produced." }

$Bytes = (Get-ChildItem -Recurse "dist\Dream-VoiceTraining" | Measure-Object -Property Length -Sum).Sum
$SizeMb = [math]::Round($Bytes / 1MB, 1)
Say "Built $ExePath ($SizeMb MB)"

Say "Creating portable archive"
$Zip = "dist\Dream-VoiceTraining-$Version-windows-portable.zip"
Compress-Archive -Path "dist\Dream-VoiceTraining\*" -DestinationPath $Zip -Force

# --- Installer (optional) ----------------------------------------------
# ${env:ProgramFiles(x86)} cannot be used inside a double quoted string,
# the parentheses end the expression early. Read it explicitly instead.

$ProgramFilesX86 = [Environment]::GetEnvironmentVariable("ProgramFiles(x86)")
$InnoCandidates = @()
if ($ProgramFilesX86) {
    $InnoCandidates += (Join-Path $ProgramFilesX86 "Inno Setup 6\ISCC.exe")
}
if ($env:ProgramFiles) {
    $InnoCandidates += (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
}
$Inno = $InnoCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($Inno) {
    Say "Building installer"
    & $Inno "/DMyAppVersion=$Version" "packaging\windows\installer.iss"
    if ($LASTEXITCODE -ne 0) { Warn "Inno Setup reported an error." }
} else {
    Warn "Inno Setup not found, built the portable version only."
    Warn "Get it from https://jrsoftware.org/isdl.php"
}

# --- Ergebnis ----------------------------------------------------------

Say "Results:"
Get-ChildItem "dist\*.zip", "dist\*.exe" -ErrorAction SilentlyContinue |
    ForEach-Object { Write-Host ("   " + $_.Name) }

Say "Test the executable before shipping:"
Write-Host "   $ExePath"
