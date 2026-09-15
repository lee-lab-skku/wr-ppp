#Requires -Version 5.1
param([string]$Python = '', [switch]$RealBuild, [switch]$Gui, [switch]$Package)
. (Join-Path $PSScriptRoot 'common.ps1')
try {
    $Python = Resolve-WrPython $Python
    Invoke-WrChecked $Python @('-B', '-m', 'unittest', 'discover', '-s', (Join-Path $PSScriptRoot 'tests'), '-v')
    Invoke-WrChecked $Python @('-B', '-m', 'unittest', 'discover', '-s', (Join-Path $script:WrRoot 'tests'), '-v')
    if ($RealBuild) { Invoke-WrChecked $Python @((Join-Path $PSScriptRoot 'tests\real_build.py')) }
    if ($Gui) { Invoke-WrChecked $Python @((Join-Path $PSScriptRoot 'tests\gui_smoke.py')) }
    if ($Package) { & (Join-Path $PSScriptRoot 'tests\portable_smoke.ps1') }
} catch { [Console]::Error.WriteLine($_.Exception.Message); exit 1 }
