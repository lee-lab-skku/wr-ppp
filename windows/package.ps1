#Requires -Version 5.1
param([string]$Python = '', [switch]$IncludeTeX)
. (Join-Path $PSScriptRoot 'common.ps1')
$Python = Resolve-WrPython $Python
$version = Get-WrVersion
$texSource = Join-Path $script:WrRoot '.runtime\TinyTeX'
if ($IncludeTeX -and -not (Test-Path -LiteralPath (Join-Path $texSource 'bin\windows\xelatex.exe') -PathType Leaf)) {
    throw 'Run install-tex.ps1 first.'
}
Push-Location -LiteralPath $PSScriptRoot
try {
    Invoke-WrChecked $Python @('-m', 'pip', 'install', 'pyinstaller==6.21.0', '-r', 'requirements.txt')
    if ($IncludeTeX) {
        Invoke-WrChecked $Python @((Join-Path $PSScriptRoot 'distribution_licenses.py'), 'prepare-tex',
            '--tex-root', $texSource, '--cache', (Join-Path $script:WrRoot '.runtime/tex-notice-cache'))
    }
    Invoke-WrChecked $Python @('-m', 'PyInstaller', '--noconfirm', 'WeeklyReport.spec')
    $version | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'dist\WeeklyReport\_internal\VERSION') -Encoding ASCII
    if ($IncludeTeX) {
        $texDestination = Join-Path $PSScriptRoot 'dist\WeeklyReport\tex'
        [IO.Directory]::CreateDirectory($texDestination) | Out-Null
        foreach ($item in Get-ChildItem -LiteralPath $texSource) {
            Copy-Item -LiteralPath $item.FullName -Destination $texDestination -Recurse -Force
        }
        Invoke-WrChecked $Python @((Join-Path $PSScriptRoot 'sanitize-bundle.py'))
    }
    Invoke-WrChecked $Python @((Join-Path $PSScriptRoot 'distribution_licenses.py'), 'check',
        '--bundle', (Join-Path $PSScriptRoot 'dist/WeeklyReport'))
    Write-Host 'Distribute the whole windows/dist/WeeklyReport folder. Use -IncludeTeX for an offline bundle.'
} finally { Pop-Location }
