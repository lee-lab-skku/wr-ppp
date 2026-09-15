#Requires -Version 5.1
. (Join-Path (Split-Path -Parent $PSScriptRoot) 'common.ps1')
$app = Join-Path $script:WrRoot 'windows\dist\WeeklyReport\WeeklyReportCLI.exe'
if (-not (Test-Path -LiteralPath $app -PathType Leaf)) { throw 'Run package.ps1 -IncludeTeX first.' }
$qa = Join-Path $script:WrRoot '.runtime\qa'
$previousConfig, $previousPath = $env:WR_CONFIG, $env:PATH
try {
    $env:WR_CONFIG = Join-Path $qa 'portable-config.json'
    # Exclude development Python, MSYS and installed TeX from PATH.
    $env:PATH = "$env:SystemRoot\System32;$env:SystemRoot"
    [IO.Directory]::CreateDirectory($qa) | Out-Null
    $source = Join-Path $qa 'portable-template\main.tex'
    [IO.Directory]::CreateDirectory((Split-Path -Parent $source)) | Out-Null
    Copy-Item -LiteralPath (Join-Path $script:WrRoot 'template.tex') -Destination $source
    Invoke-WrChecked $app @('setup', '--pdf-output', (Join-Path $qa 'portable-output'))
    Invoke-WrChecked $app @('preflight')
    Invoke-WrChecked $app @('self-test', '--output', (Join-Path $qa 'portable-selftest.json'))
    Invoke-WrChecked $app @('report-build', $source, '--date', '2026-09-11', '--serial', '17')
    Write-Host 'Portable EXE + bundled TeX with system-only PATH: OK'
} finally {
    $env:WR_CONFIG = $previousConfig
    $env:PATH = $previousPath
}
