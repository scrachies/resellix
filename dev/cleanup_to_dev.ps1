# Run with Resellix CLOSED. Leaves: dev, windows, apple, IMPORTANT-README.md, .gitignore
$Root = Split-Path $PSScriptRoot -Parent
$Dev = $PSScriptRoot
$Keep = @('dev','windows','apple','README-EN.txt','README-DE.txt','.git','.gitignore')

$RootApp = Join-Path $Root 'app'
$DevApp = Join-Path $Dev 'app'
if (Test-Path $RootApp) {
    New-Item -ItemType Directory -Path $DevApp -Force | Out-Null
    robocopy $RootApp $DevApp /E /XO /NFL /NDL /NJH /NJS | Out-Null
    Remove-Item $RootApp -Recurse -Force -ErrorAction SilentlyContinue
}

Get-ChildItem $Root -Force | ForEach-Object {
    if ($Keep -contains $_.Name) { return }
    $dest = Join-Path $Dev $_.Name
    if ($_.PSIsContainer) {
        New-Item -ItemType Directory -Path $dest -Force -ErrorAction SilentlyContinue | Out-Null
        robocopy $_.FullName $dest /E /NFL /NDL /NJH /NJS | Out-Null
        Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
    } else {
        Move-Item $_.FullName $dest -Force -ErrorAction SilentlyContinue
    }
}
Write-Host "Done."
