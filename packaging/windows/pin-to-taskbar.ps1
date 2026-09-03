# Tries to pin a file to the taskbar.
#
#   powershell -ExecutionPolicy Bypass -File pin-to-taskbar.ps1 -Target "C:\...\app.exe"
#
# Read this before trusting the result: since Windows 10 1607 Microsoft
# removed the "Pin to taskbar" verb for programs that ask for it themselves,
# and Windows 11 blocks it outright. There is no supported way to do this
# from an installer. So this script tries, reports what happened and exits
# without an error either way -- an installer must not fail over a shortcut.
#
# Exit codes: 0 pinned, 2 refused by Windows, 3 target missing.
#
# ASCII only, and saved with a byte order mark: Windows PowerShell 5.1 reads
# .ps1 files without one as ANSI, which mangles anything above ASCII.

param(
    [Parameter(Mandatory = $true)][string]$Target
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Target)) {
    Write-Host "!! Nothing to pin at $Target" -ForegroundColor Yellow
    exit 3
}

$Target = (Resolve-Path $Target).Path
$Directory = Split-Path -Parent $Target
$Leaf = Split-Path -Leaf $Target

try {
    $Shell = New-Object -ComObject Shell.Application
    $Item = $Shell.Namespace($Directory).ParseName($Leaf)

    # The verb is localised, so match on the part that survives translation
    # rather than on an English name: taskbar, Taskleiste, barre des taches.
    $Verb = $Item.Verbs() | Where-Object {
        $Name = $_.Name -replace "&", ""
        $Name -match "askbar" -or $Name -match "askleiste" -or
        $Name -match "barre des t"
    } | Select-Object -First 1

    if ($Verb) {
        $Verb.DoIt()
        Write-Host ":: Pinned to the taskbar" -ForegroundColor Cyan
        exit 0
    }
}
catch {
    # Fall through to the same message: from the outside a refusal and a
    # failure look alike, and neither is worth stopping for.
}

Write-Host "!! Windows did not offer the pin action." -ForegroundColor Yellow
Write-Host "   Microsoft blocks this for installers since Windows 10 1607."
Write-Host "   Right-click the desktop icon and pick 'Pin to taskbar'."
exit 2
