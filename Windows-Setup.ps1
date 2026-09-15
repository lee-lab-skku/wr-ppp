#Requires -Version 5.1
param([string]$Python = '')
. (Join-Path $PSScriptRoot 'windows\common.ps1')
try {
    $bootstrap = Resolve-WrPython -Python $Python -Bootstrap
    Invoke-WrChecked $bootstrap @('-c', 'import tkinter, venv, ensurepip')
    $environment = Join-Path $PSScriptRoot '.venv'
    $venvPython = Join-Path $environment 'Scripts\python.exe'
    if (Test-Path -LiteralPath $environment) {
        if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
            throw 'Existing .venv is not a Windows environment and has been preserved. Rename it before setup.'
        }
        $venvPython = Resolve-WrPython -Python $venvPython
    } else {
        Invoke-WrChecked $bootstrap @('-m', 'venv', $environment)
    }
    Invoke-WrChecked $venvPython @('-m', 'pip', 'install', '-r', (Join-Path $PSScriptRoot 'windows\requirements.txt'))
    Write-Host 'Ready. Run Start-Weekly-Report.ps1, or windows/install-tex.ps1 to prepare local TeX.'
} catch { [Console]::Error.WriteLine($_.Exception.Message); exit 1 }
