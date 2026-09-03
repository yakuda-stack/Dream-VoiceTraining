# Installs Dream-VoiceTraining from source on Windows -- the counterpart to
# install.sh on Linux.
#
#   powershell -ExecutionPolicy Bypass -File packaging\windows\install_windows.ps1
#
# What it does:
#   - checks for Python 3.10 or newer and installs it through winget if it
#     is missing
#   - copies the program to %LOCALAPPDATA%\Programs\Dream-VoiceTraining
#   - builds its own virtual environment there and installs the requirements
#   - creates a desktop shortcut and a start menu entry, and tries the
#     taskbar
#   - writes uninstall.ps1 next to the program
#
# No administrator rights: everything stays inside the user profile.
#
# If you only want to run the program, the setup.exe or the portable build
# from the releases page is less work -- those carry their own Python and
# need none of this. This script is for running from source, so a change to
# a .py file takes effect on the next start.
#
# ASCII only and saved with a byte order mark, see pin-to-taskbar.ps1.

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $Root

function Say([string]$Text) { Write-Host ":: $Text" -ForegroundColor Cyan }
function Warn([string]$Text) { Write-Host "!! $Text" -ForegroundColor Yellow }

$AppName = "Dream-VoiceTraining"
$Target = Join-Path $env:LOCALAPPDATA "Programs\$AppName"
$MinMajor = 3
$MinMinor = 10

# --- Version aus paths.py ----------------------------------------------

$Match = Select-String -Path "paths.py" -Pattern 'APP_VERSION = "([^"]+)"'
if (-not $Match) { throw "APP_VERSION not found in paths.py. Wrong folder?" }
$Version = $Match.Matches[0].Groups[1].Value
Say "$AppName $Version"

# --- Python suchen ------------------------------------------------------

function Test-Python([string]$Exe, [string[]]$Prefix) {
    <#
      Returns the real interpreter path when it is new enough and usable.

      The answer is sys.executable, not the command that was called: "py -3"
      is a launcher, and everything after this point -- creating the virtual
      environment -- wants the interpreter itself.

      The Store build of Python is rejected on purpose: it redirects
      %LOCALAPPDATA% into a private container, and that is exactly where the
      recordings go.
    #>
    $Probe = "import sys; print(sys.version_info[0], sys.version_info[1], sys.executable)"
    try {
        $Info = & $Exe @($Prefix + @("-c", $Probe)) 2>$null
    }
    catch { return $null }
    if (-not $Info) { return $null }

    $Parts = $Info.Trim().Split(" ", 3)
    if ($Parts.Count -lt 3) { return $null }
    $Major = [int]$Parts[0]
    $Minor = [int]$Parts[1]
    $Path = $Parts[2]

    if ($Path -like "*\WindowsApps\*") {
        Warn "Ignoring the Microsoft Store Python at $Path"
        Warn "It cannot write to %LOCALAPPDATA% where the recordings live."
        return $null
    }
    if ($Major -lt $MinMajor -or ($Major -eq $MinMajor -and $Minor -lt $MinMinor)) {
        Warn "Found Python $Major.$Minor, but $MinMajor.$MinMinor or newer is needed."
        return $null
    }
    Say "Using Python $Major.$Minor at $Path"
    return $Path
}

function Find-Python() {
    # "py -3" first: the launcher picks the newest installed version, while
    # a bare "python" may be whatever landed on PATH last.
    $Candidates = @(
        @{ Exe = "py";      Prefix = @("-3") },
        @{ Exe = "python";  Prefix = @() },
        @{ Exe = "python3"; Prefix = @() }
    )
    foreach ($Candidate in $Candidates) {
        if (-not (Get-Command $Candidate.Exe -ErrorAction SilentlyContinue)) {
            continue
        }
        $Found = Test-Python $Candidate.Exe $Candidate.Prefix
        if ($Found) { return $Found }
    }
    return $null
}

$Python = Find-Python
if (-not $Python) {
    Say "No suitable Python found, installing one"
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw ("Python $MinMajor.$MinMinor or newer is missing and winget is " +
               "not available. Install Python from https://www.python.org/downloads/ " +
               "(tick 'Add python.exe to PATH') and run this script again.")
    }
    winget install --exact --id Python.Python.3.12 --scope user `
        --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        throw "winget could not install Python. Install it from python.org instead."
    }

    # winget extends PATH for new processes only, so pick up the new entry.
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "Machine")
    $Python = Find-Python
    if (-not $Python) {
        throw ("Python was installed but is still not on PATH. Open a new " +
               "PowerShell window and run this script again.")
    }
}

# --- Programmdateien kopieren -------------------------------------------

Say "Installing to $Target"
if (Test-Path $Target) {
    # The virtual environment survives, everything else is replaced: a
    # reinstall then takes seconds instead of downloading Qt again.
    Get-ChildItem $Target -Exclude "venv" | Remove-Item -Recurse -Force
} else {
    New-Item -ItemType Directory -Path $Target -Force | Out-Null
}

Copy-Item "$Root\*.py" $Target
Copy-Item "$Root\requirements.txt" $Target
foreach ($Extra in @("LICENSE", "THIRD_PARTY_NOTICES.md", "README.md", "README.de.md")) {
    if (Test-Path "$Root\$Extra") { Copy-Item "$Root\$Extra" $Target }
}
Copy-Item "$Root\packaging\dream-voicetraining.ico" $Target -ErrorAction SilentlyContinue

# Bildschirmfotos der Einfuehrung; ohne sie laeuft alles, nur ohne Bilder.
if (Test-Path "$Root\assets\intro") {
    New-Item -ItemType Directory -Path "$Target\assets\intro" -Force | Out-Null
    Copy-Item "$Root\assets\intro\*" "$Target\assets\intro"
}

# --- Umgebung anlegen ---------------------------------------------------

$Venv = Join-Path $Target "venv"
$VenvPython = Join-Path $Venv "Scripts\python.exe"
$VenvPythonW = Join-Path $Venv "Scripts\pythonw.exe"

if (-not (Test-Path $VenvPython)) {
    Say "Creating the Python environment"
    & $Python -m venv $Venv
    if (-not (Test-Path $VenvPython)) { throw "Creating the environment failed." }
}

Say "Installing dependencies (this takes a minute)"
& $VenvPython -m pip install --upgrade pip wheel --quiet
& $VenvPython -m pip install --quiet -r (Join-Path $Target "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Installing dependencies failed." }

# --- Verknuepfungen -----------------------------------------------------

function New-Shortcut([string]$Path, [string]$Description) {
    $Shell = New-Object -ComObject WScript.Shell
    $Link = $Shell.CreateShortcut($Path)
    # pythonw.exe instead of python.exe: otherwise a console window sits
    # behind the program for its whole run.
    $Link.TargetPath = $VenvPythonW
    $Link.Arguments = '"' + (Join-Path $Target "main.py") + '"'
    $Link.WorkingDirectory = $Target
    $Link.Description = $Description
    $Icon = Join-Path $Target "dream-voicetraining.ico"
    if (Test-Path $Icon) { $Link.IconLocation = $Icon }
    $Link.Save()
}

$Desktop = [Environment]::GetFolderPath("Desktop")
$StartMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
$DesktopLink = Join-Path $Desktop "$AppName.lnk"

Say "Creating shortcuts"
New-Shortcut $DesktopLink "Measure what your voice is doing"
New-Shortcut (Join-Path $StartMenu "$AppName.lnk") "Measure what your voice is doing"

& (Join-Path $PSScriptRoot "pin-to-taskbar.ps1") -Target $DesktopLink

# --- Deinstallation -----------------------------------------------------

$Uninstall = @"
# Removes Dream-VoiceTraining. Recordings and settings are left alone --
# delete them yourself if you want them gone:
#   `$env:APPDATA\$AppName
#   `$env:LOCALAPPDATA\$AppName
Remove-Item -Recurse -Force "$Target" -ErrorAction SilentlyContinue
Remove-Item -Force "$DesktopLink" -ErrorAction SilentlyContinue
Remove-Item -Force "$(Join-Path $StartMenu "$AppName.lnk")" -ErrorAction SilentlyContinue
Write-Host "Removed. Your recordings are still in `$env:LOCALAPPDATA\$AppName"
"@
Set-Content -Path (Join-Path $Target "uninstall.ps1") -Value $Uninstall -Encoding UTF8

# --- Ergebnis -----------------------------------------------------------

Say "Done."
Write-Host "   Program:    $Target"
Write-Host "   Settings:   $env:APPDATA\$AppName"
Write-Host "   Recordings: $env:LOCALAPPDATA\$AppName"
Write-Host "   Uninstall:  powershell -ExecutionPolicy Bypass -File `"$Target\uninstall.ps1`""
Say "Starting it once to check"
Start-Process -FilePath $VenvPythonW -ArgumentList ('"' + (Join-Path $Target "main.py") + '"') -WorkingDirectory $Target
