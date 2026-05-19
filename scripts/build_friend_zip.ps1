# Build a clean Resellix zip for friends (no logs, license, or personal data).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Staging = Join-Path $env:TEMP "resellix-friend-build"
$OutZip = Join-Path ([Environment]::GetFolderPath("Desktop")) "resellix-friend-mac.zip"
$Dest = Join-Path $Staging "resellix"

if (Test-Path $Staging) { Remove-Item $Staging -Recurse -Force }
New-Item -ItemType Directory -Path $Dest -Force | Out-Null

$ExcludeDirs = @(
    ".git", ".venv", "__pycache__", ".runtime", "node_modules"
)
$ExcludeFiles = @(
    "resellix-license-keys.txt",
    "resellix-share.zip",
    "resellix-friend-mac.zip"
)

robocopy $Root $Dest /E /NFL /NDL /NJH /NJS /NC /NS `
    /XD $($ExcludeDirs -join " ") `
    /XF @(
        "license.key", "license.meta.json", ".env", "targets.json",
        "resell.db", "resell.db-wal", "resell.db-shm",
        ".update_state.json", "startup_error.log", "trends.txt",
        "kleinanzeigen_api.pid", "*.log", "*.pyc", "*.pyo"
    ) `
    | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed with code $LASTEXITCODE" }

foreach ($name in $ExcludeFiles) {
    Get-ChildItem -Path $Dest -Recurse -Filter $name -ErrorAction SilentlyContinue |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

# Fresh empty targets for new installs
@("[]") | Set-Content -Path (Join-Path $Dest "dev\targets.json") -Encoding UTF8

# Mac quick-start (friend)
@'
RESELLIX — MAC INSTALL (from Thomas)
====================================

1. Unzip this folder to Desktop (you should see: resellix/apple/, resellix/dev/, …).

2. Install once:
   - Python 3.11+  https://www.python.org/downloads/
   - Git: open Terminal and run:  xcode-select --install

3. Terminal (first time only):
   cd ~/Desktop/resellix
   chmod +x apple/*.command

4. Start: double-click  RESELLIX-MAC-START.command  (in the resellix folder)
   First time: right-click → Open → Open
   If problems: read apple/MAC-ZUGRIFF-FIX.txt

5. First run installs packages (5–15 min). App starts on FREE plan.

6. Settings → paste the license key Thomas sent you.

UPDATES
-------
Every start checks GitHub (scrachies/resellix). You need:
  - Git installed
  - GitHub access (Thomas adds you as collaborator)
  - A license that includes Updates (Plus/Pro/Max)

Manual update: double-click apple/updateapple.command

Private use only — do not share this zip publicly.
'@ | Set-Content -Path (Join-Path $Dest "START-MAC.txt") -Encoding UTF8

if (Test-Path $OutZip) { Remove-Item $OutZip -Force }
Compress-Archive -Path $Dest -DestinationPath $OutZip -CompressionLevel Optimal

Remove-Item $Staging -Recurse -Force
Write-Host "[OK] Created: $OutZip"
$mb = [math]::Round((Get-Item $OutZip).Length / 1MB, 1)
Write-Host "     Size: ${mb} MB"
