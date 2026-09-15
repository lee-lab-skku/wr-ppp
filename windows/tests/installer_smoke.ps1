#Requires -Version 5.1
param(
    [Parameter(Mandatory=$true)][string]$Installer,
    [Parameter(Mandatory=$true)][string]$ExpectedVersion
)
. (Join-Path (Split-Path -Parent $PSScriptRoot) 'common.ps1')
$Installer = (Get-Item -LiteralPath $Installer -ErrorAction Stop).FullName
$qa = Join-Path $script:WrRoot '.runtime/qa'
$installRoot = Join-Path $qa 'installed app'
$registryKey = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{F703E260-445B-4B85-A1ED-D289BDA64E64}_is1'
foreach ($hive in @('HKCU:', 'HKLM:')) {
    if (Test-Path -LiteralPath "$hive\$registryKey") {
        throw 'An existing Weekly Report installation was preserved. Run this check on a clean CI runner.'
    }
}
if (Test-Path -LiteralPath $installRoot) { throw "Existing test installation preserved: $installRoot" }
$source = Get-ChildItem -LiteralPath (Join-Path $qa 'sources') -Filter main.tex -Recurse | Select-Object -First 1
if (-not $source) { throw 'Run windows/tests/real_build.py first to prepare the Korean test report.' }
$config = Join-Path $qa 'installer-config.json'
$output = Join-Path $qa 'installer-output'
$app = Join-Path $installRoot 'WeeklyReportCLI.exe'
$uninstaller = Join-Path $installRoot 'unins000.exe'
$previousConfig, $previousPath = $env:WR_CONFIG, $env:PATH
try {
    Invoke-WrChecked $Installer @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-', '/NOICONS',
                                 '/TASKS=', "/DIR=$installRoot", "/LOG=$(Join-Path $qa 'installer.log')")
    if ((Get-Content -LiteralPath (Join-Path $installRoot '_internal/VERSION') -Raw).Trim() -ne $ExpectedVersion) {
        throw 'Installed application version does not match the release tag.'
    }
    if (-not (Test-Path -LiteralPath "HKCU:\$registryKey")) { throw 'Per-user uninstall registration is missing.' }
    $env:WR_CONFIG = $config
    $env:PATH = "$env:SystemRoot\System32;$env:SystemRoot"
    Invoke-WrChecked $app @('setup', '--pdf-output', $output)
    Invoke-WrChecked $app @('preflight')
    Invoke-WrChecked $app @('self-test', '--output', (Join-Path $qa 'installed-selftest.json'))
    Invoke-WrChecked $app @('report-build', $source.FullName, '--date', '2026-09-11', '--serial', '17')
} finally {
    $env:WR_CONFIG = $previousConfig
    $env:PATH = $previousPath
    # Inno may leave a partial installation on failure; use its own uninstaller.
    if (Test-Path -LiteralPath $uninstaller -PathType Leaf) {
        Invoke-WrChecked $uninstaller @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART',
                                      "/LOG=$(Join-Path $qa 'uninstaller.log')")
    }
}
$deadline = [DateTime]::UtcNow.AddSeconds(30)
while ((Test-Path -LiteralPath $app) -and [DateTime]::UtcNow -lt $deadline) { Start-Sleep -Milliseconds 200 }
if ((Test-Path -LiteralPath $app) -or (Test-Path -LiteralPath "HKCU:\$registryKey")) {
    throw 'Uninstallation left the application or its registration behind.'
}
if (-not (Test-Path -LiteralPath $config -PathType Leaf) -or -not (Get-ChildItem -LiteralPath $output -Filter *.pdf)) {
    throw 'Uninstallation removed user configuration or report output.'
}
Write-Host 'Installed EXE, bundled TeX and uninstall preservation: OK'
