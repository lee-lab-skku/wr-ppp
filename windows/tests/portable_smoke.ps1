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
    # template.tex intentionally demonstrates three report figures. The build
    # now rejects missing report assets instead of silently printing figure
    # placeholders, so the portable smoke test must provide real files too.
    $figures = Join-Path (Split-Path -Parent $source) 'figures'
    [IO.Directory]::CreateDirectory($figures) | Out-Null
    $samplePdf = [Convert]::FromBase64String(
        'JVBERi0xLjMKJeLjz9MKMSAwIG9iago8PAovUHJvZHVjZXIgKHB5cGRmKQo+PgplbmRvYmoKMiAwIG9iago8PAovVHlwZSAvUGFnZXMKL0NvdW50IDEKL0tpZHMgWyA0IDAgUiBdCj4+CmVuZG9iagozIDAgb2JqCjw8Ci9UeXBlIC9DYXRhbG9nCi9QYWdlcyAyIDAgUgo+PgplbmRvYmoKNCAwIG9iago8PAovVHlwZSAvUGFnZQovUmVzb3VyY2VzIDw8Cj4+Ci9NZWRpYUJveCBbIDAuMCAwLjAgMTAwIDEwMCBdCi9QYXJlbnQgMiAwIFIKPj4KZW5kb2JqCnhyZWYKMCA1CjAwMDAwMDAwMDAgNjU1MzUgZiAKMDAwMDAwMDAxNSAwMDAwMCBuIAowMDAwMDAwMDU0IDAwMDAwIG4gCjAwMDAwMDAxMTMgMDAwMDAgbiAKMDAwMDAwMDE2MiAwMDAwMCBuIAp0cmFpbGVyCjw8Ci9TaXplIDUKL1Jvb3QgMyAwIFIKL0luZm8gMSAwIFIKPj4Kc3RhcnR4cmVmCjI1NgolJUVPRgo=')
    foreach ($name in @('calibration-curve.pdf', 'rare-class-errors.pdf', 'seed-variance.pdf')) {
        [IO.File]::WriteAllBytes((Join-Path $figures $name), $samplePdf)
    }
    Invoke-WrChecked $app @('setup', '--pdf-output', (Join-Path $qa 'portable-output'))
    Invoke-WrChecked $app @('preflight')
    Invoke-WrChecked $app @('self-test', '--output', (Join-Path $qa 'portable-selftest.json'))
    Invoke-WrChecked $app @('report-build', $source, '--date', '2026-09-11', '--serial', '17')
    Write-Host 'Portable EXE + bundled TeX with system-only PATH: OK'
} finally {
    $env:WR_CONFIG = $previousConfig
    $env:PATH = $previousPath
}
