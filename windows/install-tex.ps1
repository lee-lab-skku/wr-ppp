#Requires -Version 5.1
param([string]$InstallRoot = '')
. (Join-Path $PSScriptRoot 'common.ps1')
if (-not $InstallRoot) { $InstallRoot = Join-Path $script:WrRoot '.runtime' }
$InstallRoot = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($InstallRoot)
$texRoot = Join-Path $InstallRoot 'TinyTeX'
$tlmgr = Join-Path $texRoot 'bin\windows\tlmgr.bat'
if (-not (Test-Path -LiteralPath $tlmgr)) {
    if (Test-Path -LiteralPath $texRoot) { throw "Existing incomplete installation preserved: $texRoot" }
    [IO.Directory]::CreateDirectory($InstallRoot) | Out-Null
    $archive = Join-Path $InstallRoot 'TinyTeX-1-windows.exe'
    Invoke-WrChecked (Get-Command curl.exe -CommandType Application -TotalCount 1 -ErrorAction Stop).Source @('-fL', '--retry', '2', '-o', $archive, 'https://github.com/rstudio/tinytex-releases/releases/download/daily/TinyTeX-1-windows.exe')
    $extraction = Start-Process -FilePath $archive -ArgumentList '-y' -WorkingDirectory $InstallRoot -WindowStyle Hidden -Wait -PassThru
    if ($extraction.ExitCode -ne 0) { throw 'TinyTeX extraction failed.' }
}
# Do not change machine/user PATH or touch another TeX installation.
& $tlmgr option repository 'https://mirror.ctan.org/systems/texlive/tlnet'
if ($LASTEXITCODE -ne 0) { throw 'Unable to set TeX repository.' }
# weekly-report.sty also requires mhchem, which is outside these collections.
& $tlmgr install collection-latexrecommended collection-latexextra collection-langcjk collection-langkorean collection-fontsrecommended collection-xetex mhchem
if ($LASTEXITCODE -ne 0) { throw 'TeX packages could not be installed.' }
& $tlmgr postaction install script xetex
if ($LASTEXITCODE -ne 0) { throw 'XeTeX configuration failed.' }
Write-Host "TeX ready: $texRoot\bin\windows"
