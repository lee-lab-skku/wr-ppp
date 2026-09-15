#Requires -Version 5.1
# Intentionally no param block: forward Python CLI options without PowerShell binding them.
. (Join-Path $PSScriptRoot 'windows\common.ps1')
try {
    $commandArguments = @($args)
    if ($commandArguments.Count -eq 0) { $commandArguments = @('gui') }
    $python = Resolve-WrPython
    Invoke-WrNative $python (@((Join-Path $PSScriptRoot 'windows\weekly_report.py')) + $commandArguments) -AsPipeline
    exit $LASTEXITCODE
} catch { [Console]::Error.WriteLine($_.Exception.Message); exit 1 }
