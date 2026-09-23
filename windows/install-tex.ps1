#Requires -Version 5.1
param([string]$InstallRoot = '', [string]$Python = '', [switch]$PrepareDistribution,
      [string]$Repository = 'https://mirror.ctan.org/systems/texlive/tlnet')
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
# Resolve CTAN once: separate tlmgr/Python requests can otherwise select mirrors
# at different sync revisions, even for a package installed moments earlier.
if ($PrepareDistribution) {
    $indexSuffix = '/tlpkg/texlive.tlpdb.xz'
    $curl = (Get-Command curl.exe -CommandType Application -TotalCount 1 -ErrorAction Stop).Source
    $resolved = & $curl '-fsSL' '--retry' '2' '--connect-timeout' '30' '--max-time' '120' '--proto' '=https' '--proto-redir' '=https' '-o' 'NUL' '-w' '%{url_effective}' ($Repository.TrimEnd('/') + $indexSuffix)
    if ($LASTEXITCODE -ne 0) { throw 'Unable to resolve TeX repository.' }
    $resolved = [string]$resolved
    if (-not $resolved.StartsWith('https://') -or -not $resolved.EndsWith($indexSuffix)) {
        throw "Unexpected TeX repository URL: $resolved"
    }
    $Repository = $resolved.Substring(0, $resolved.Length - $indexSuffix.Length)
    Write-Host "Distribution TeX repository: $Repository"
}
# Do not change machine/user PATH or touch another TeX installation.
& $tlmgr option repository $Repository
if ($LASTEXITCODE -ne 0) { throw 'Unable to set TeX repository.' }
if ($PrepareDistribution) {
    # install skips existing packages from the daily bootstrap or a previous
    # local setup. Align those too before matching their documentation hashes.
    & $tlmgr update --self --all
    if ($LASTEXITCODE -ne 0) { throw 'TeX packages could not be updated for distribution.' }
}
# weekly-report.sty also requires mhchem, which is outside these collections.
& $tlmgr install collection-latexrecommended collection-latexextra collection-langcjk collection-langkorean collection-fontsrecommended collection-xetex mhchem
if ($LASTEXITCODE -ne 0) { throw 'TeX packages could not be installed.' }
& $tlmgr postaction install script xetex
if ($LASTEXITCODE -ne 0) { throw 'XeTeX configuration failed.' }
# Source-only use does not need redistribution preparation. Packaging always
# requires it; CI opts in here so the prepared notices travel with its cache.
if ($PrepareDistribution) {
    Invoke-WrChecked (Resolve-WrPython $Python) @((Join-Path $PSScriptRoot 'distribution_licenses.py'),
        'prepare-tex', '--tex-root', $texRoot, '--cache', (Join-Path $InstallRoot 'tex-notice-cache'),
        '--repository', $Repository)
}
Write-Host "TeX ready: $texRoot\bin\windows"
