param(
    [ValidatePattern('^\d+\.\d+\.\d+$')][string]$Version = '0.1.0',
    [string]$Compiler = '',
    [string]$Python = '',
    [switch]$SkipPackage
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $Compiler) {
    $candidates = @(
        (Join-Path $repoRoot '.windows-deps\inno\ISCC.exe'),
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    )
    $Compiler = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $Compiler -or -not (Test-Path -LiteralPath $Compiler)) {
    throw 'Install Inno Setup 6 or pass -Compiler <path to ISCC.exe>.'
}
if (-not $SkipPackage) {
    & (Join-Path $PSScriptRoot 'package.ps1') -Python $Python -IncludeTeX
}
$bundle = Join-Path $PSScriptRoot 'dist\WeeklyReport'
if (-not $Python) {
    $Python = Join-Path $repoRoot '.venv\Scripts\python.exe'
}
& $Python (Join-Path $PSScriptRoot 'sanitize-bundle.py')
if ($LASTEXITCODE -ne 0) { throw 'Bundle privacy cleanup failed.' }
foreach ($required in @('WeeklyReport.exe', 'WeeklyReportCLI.exe', '_internal\weekly-report.sty', 'tex\bin\windows\xelatex.exe')) {
    if (-not (Test-Path -LiteralPath (Join-Path $bundle $required))) {
        throw "Incomplete offline bundle: $required"
    }
}
& $Compiler "/DAppVersion=$Version" (Join-Path $PSScriptRoot 'installer.iss')
if ($LASTEXITCODE -ne 0) { throw 'Installer compilation failed.' }
$installer = Join-Path $PSScriptRoot "dist\installer\WeeklyReport-$Version-Setup.exe"
$hash = (Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant()
"$hash  $(Split-Path -Leaf $installer)" | Set-Content -LiteralPath "$installer.sha256" -Encoding ASCII
Write-Host "Installer: $installer"
