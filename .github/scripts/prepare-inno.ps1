#Requires -Version 5.1
# Pinned official portable compiler; do not depend on the runner's installed version.
. (Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) 'windows/common.ps1')
$destination = Join-Path $script:WrRoot '.windows-deps/inno'
$compiler = Join-Path $destination 'ISCC.exe'
if (Test-Path -LiteralPath $compiler -PathType Leaf) {
    if ((Get-Item -LiteralPath $compiler).VersionInfo.FileVersion -notmatch '^6\.7\.3(?:\.|$)') {
        throw 'Existing Inno Setup differs from pinned 6.7.3 and was preserved.'
    }
    return
}
if (Test-Path -LiteralPath $destination) { throw "Incomplete compiler directory preserved: $destination" }
$archive = Join-Path $script:WrRoot '.windows-deps/innosetup-6.7.3.exe'
[IO.Directory]::CreateDirectory((Split-Path -Parent $archive)) | Out-Null
Invoke-WrChecked (Get-Command curl.exe -CommandType Application).Source @(
    '-fL', '--retry', '2', '-o', $archive,
    'https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/innosetup-6.7.3.exe'
)
$expected = '9c73c3bae7ed48d44112a0f48e66742c00090bdb5bef71d9d3c056c66e97b732'
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
    throw 'Official Inno Setup installer checksum mismatch.'
}
Invoke-WrChecked $archive @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-', '/CURRENTUSER',
                          '/PORTABLE=1', '/NOICONS', '/TASKS=', "/DIR=$destination")
if (-not (Test-Path -LiteralPath $compiler -PathType Leaf)) { throw 'Inno Setup compiler was not installed.' }
