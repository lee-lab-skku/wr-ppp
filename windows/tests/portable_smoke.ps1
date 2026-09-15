$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$app = Join-Path $repoRoot 'windows\dist\WeeklyReport\WeeklyReportCLI.exe'
$qa = Join-Path $repoRoot '.runtime\qa'
$env:WR_CONFIG = Join-Path $qa 'portable-config.json'
# Exclude the development Python, MSYS and any existing TeX from PATH.
$env:PATH = "$env:SystemRoot\System32;$env:SystemRoot"
& $app setup --pdf-output (Join-Path $qa 'portable-output')
if ($LASTEXITCODE -ne 0) { throw 'Packaged configuration failed.' }
& $app preflight
if ($LASTEXITCODE -ne 0) { throw 'Packaged preflight failed.' }
& $app self-test --output (Join-Path $qa 'portable-selftest.json')
if ($LASTEXITCODE -ne 0) { throw 'Packaged GUI/library test failed.' }
$source = Get-ChildItem -LiteralPath (Join-Path $qa 'sources') -Filter main.tex -Recurse | Select-Object -First 1
& $app report-build $source.FullName --date 2026-09-11 --serial 17
if ($LASTEXITCODE -ne 0) { throw 'Packaged TeX build failed.' }
Write-Host 'Portable EXE + bundled TeX with system-only PATH: OK'
