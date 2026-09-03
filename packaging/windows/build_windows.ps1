# Builds Dream-VoiceTraining for Windows.
#
#   powershell -ExecutionPolicy Bypass -File packaging\windows\build_windows.ps1
#
# Output:
#   dist\Dream-VoiceTraining-<version>-Portable.exe   one file, runs anywhere
#   dist\Dream-VoiceTraining-<version>-setup.exe      needs Inno Setup
#   dist\Dream-VoiceTraining.exe                      what the setup packs
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

# The spec builds two single files straight into dist, no program folder.
# This step used to look for dist\Dream-VoiceTraining\Dream-VoiceTraining.exe
# and failed after the switch to onefile even though the build had worked.
$ExePath = "dist\Dream-VoiceTraining.exe"
$PortableBuilt = "dist\Dream-VoiceTraining-Portable.exe"
foreach ($Needed in @($ExePath, $PortableBuilt)) {
    if (-not (Test-Path $Needed)) {
        throw "PyInstaller produced no $Needed. Check the output above."
    }
    $SizeMb = [math]::Round((Get-Item $Needed).Length / 1MB, 1)
    Say "Built $Needed ($SizeMb MB)"
}

# No archive: the portable build is one self-contained file. Unpacking a ZIP
# to get at a single EXE is a step for nothing.
Say "Naming the portable build"
$Portable = "dist\Dream-VoiceTraining-$Version-Portable.exe"
Move-Item -Force $PortableBuilt $Portable
# paths.py stores next to the EXE when the file name contains "portable";
# the version in the middle does not disturb that.
Say "Ready: $Portable"

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
Get-ChildItem "dist\*.exe" -ErrorAction SilentlyContinue |
    ForEach-Object { Write-Host ("   " + $_.Name) }

Say "Test both before shipping:"
Write-Host "   $ExePath"
Write-Host "   $Portable"
