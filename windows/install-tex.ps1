param([string]$InstallRoot = '')
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $InstallRoot) { $InstallRoot = Join-Path $repoRoot '.runtime' }
$InstallRoot = [IO.Path]::GetFullPath($InstallRoot)
New-Item -ItemType Directory -Path $InstallRoot -Force | Out-Null
$texRoot = Join-Path $InstallRoot 'TinyTeX'
$tlmgr = Join-Path $texRoot 'bin\windows\tlmgr.bat'
if (-not (Test-Path -LiteralPath $tlmgr)) {
    if (Test-Path -LiteralPath $texRoot) { throw "Existing incomplete installation preserved: $texRoot" }
    $archive = Join-Path $InstallRoot 'TinyTeX-1-windows.exe'
    & curl.exe -fL --retry 2 -o $archive 'https://github.com/rstudio/tinytex-releases/releases/download/daily/TinyTeX-1-windows.exe'
    if ($LASTEXITCODE -ne 0) { throw 'TinyTeX download failed.' }
    $extraction = Start-Process -FilePath $archive -ArgumentList '-y' -WorkingDirectory $InstallRoot -WindowStyle Hidden -Wait -PassThru
    if ($extraction.ExitCode -ne 0) { throw 'TinyTeX extraction failed.' }
}
# Do not change machine/user PATH or touch another TeX installation.
& $tlmgr option repository 'https://mirror.ctan.org/systems/texlive/tlnet'
if ($LASTEXITCODE -ne 0) { throw 'Unable to set TeX repository.' }
& $tlmgr install collection-latexrecommended collection-latexextra collection-langcjk collection-langkorean collection-fontsrecommended collection-xetex
if ($LASTEXITCODE -ne 0) { throw 'TeX packages could not be installed.' }
& $tlmgr postaction install script xetex
if ($LASTEXITCODE -ne 0) { throw 'XeTeX configuration failed.' }
Write-Host "TeX ready: $texRoot\bin\windows"
