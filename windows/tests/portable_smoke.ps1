#Requires -Version 5.1
. (Join-Path (Split-Path -Parent $PSScriptRoot) 'common.ps1')
$app = Join-Path $script:WrRoot 'windows\dist\WeeklyReport\WeeklyReportCLI.exe'
if (-not (Test-Path -LiteralPath $app -PathType Leaf)) { throw 'Run package.ps1 -IncludeTeX first.' }
& (Join-Path $PSScriptRoot 'check_license_files.ps1') -SourceRoot $script:WrRoot `
    -ResourceRoot (Join-Path (Split-Path -Parent $app) '_internal')
Invoke-WrChecked (Resolve-WrPython) @((Join-Path $script:WrRoot 'windows/distribution_licenses.py'),
    'check', '--bundle', (Split-Path -Parent $app), '--require-tex')
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
    # Supply real images for the template's three figures so this check covers
    # asset staging and rendering rather than only the placeholder path.
    # Use PNG here: a blank-page PDF is readable by pypdf but is not a valid
    # image XObject for every xdvipdfmx version bundled with TinyTeX.
    $figures = Join-Path (Split-Path -Parent $source) 'figures'
    [IO.Directory]::CreateDirectory($figures) | Out-Null
    $samplePng = [Convert]::FromBase64String(
        'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAIAAAD8GO2jAAAAKklEQVR4nGMwStlCU8QwasGoBaMWjFowasGoBaMWjFowasGoBaMWDBULAFj+KEw5vBFUAAAAAElFTkSuQmCC')
    $template = [IO.File]::ReadAllText($source)
    foreach ($stem in @('calibration-curve', 'rare-class-errors', 'seed-variance')) {
        [IO.File]::WriteAllBytes((Join-Path $figures ($stem + '.png')), $samplePng)
        $template = $template.Replace(('figures/' + $stem + '.pdf'), ('figures/' + $stem + '.png'))
    }
    [IO.File]::WriteAllText($source, $template, (New-Object Text.UTF8Encoding($false)))
    Invoke-WrChecked $app @('setup', '--pdf-output', (Join-Path $qa 'portable-output'))
    Invoke-WrChecked $app @('preflight')
    Invoke-WrChecked $app @('self-test', '--output', (Join-Path $qa 'portable-selftest.json'))
    Invoke-WrChecked $app @('report-build', $source, '--date', '2026-09-11', '--serial', '17')
    Write-Host 'Portable EXE + bundled TeX with system-only PATH: OK'
} finally {
    $env:WR_CONFIG = $previousConfig
    $env:PATH = $previousPath
}
