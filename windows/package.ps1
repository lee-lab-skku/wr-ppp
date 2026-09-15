param([string]$Python = "", [switch]$IncludeTeX)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $Python) { $Python = Join-Path $repoRoot '.venv\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $Python)) { throw 'Run Windows-Setup.cmd using python.org CPython first.' }
Push-Location $PSScriptRoot
try {
    & $Python -m pip install 'pyinstaller==6.21.0' -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    & $Python -m PyInstaller --noconfirm WeeklyReport.spec
    if ($LASTEXITCODE -ne 0) { throw 'Packaging failed.' }
    if ($IncludeTeX) {
        $texSource = Join-Path $repoRoot '.runtime\TinyTeX'
        if (-not (Test-Path -LiteralPath (Join-Path $texSource 'bin\windows\xelatex.exe'))) { throw 'Run install-tex.ps1 first.' }
        $texDestination = Join-Path $PSScriptRoot 'dist\WeeklyReport\tex'
        New-Item -ItemType Directory -Force -Path $texDestination | Out-Null
        Get-ChildItem -LiteralPath $texSource | Copy-Item -Destination $texDestination -Recurse -Force
    }
    Write-Host 'Distribute the whole windows/dist/WeeklyReport folder. Use -IncludeTeX for an offline bundle.'
} finally { Pop-Location }
