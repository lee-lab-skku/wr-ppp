#Requires -Version 5.1
param(
    [string]$Compiler = '',
    [string]$Python = '',
    [switch]$SkipPackage
)
. (Join-Path $PSScriptRoot 'common.ps1')
$repoRoot = $script:WrRoot
$Python = Resolve-WrPython $Python
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
$Version = (Get-Content -LiteralPath (Join-Path $bundle '_internal\VERSION') -Raw).Trim()
if ($Version -notmatch '^v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-(beta|rc))?(-[0-9]+-g[0-9a-f]+)?(-dirty)?$') {
    throw 'Bundle version must derive from a repository SemVer tag. Rebuild the package.'
}
Invoke-WrChecked $Python @((Join-Path $PSScriptRoot 'sanitize-bundle.py'))
foreach ($required in @('WeeklyReport.exe', 'WeeklyReportCLI.exe', '_internal\weekly-report.sty', 'tex\bin\windows\xelatex.exe')) {
    if (-not (Test-Path -LiteralPath (Join-Path $bundle $required))) {
        throw "Incomplete offline bundle: $required"
    }
}
Invoke-WrChecked $Compiler @("/DAppVersion=$Version", (Join-Path $PSScriptRoot 'installer.iss'))
$installer = Join-Path $PSScriptRoot "dist\installer\WeeklyReport-$Version-Setup.exe"
$hash = (Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant()
"$hash  $(Split-Path -Leaf $installer)" | Set-Content -LiteralPath "$installer.sha256" -Encoding ASCII
Write-Host "Installer: $installer"
