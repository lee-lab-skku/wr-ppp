#Requires -Version 5.1
param(
    [Parameter(Mandatory=$true)][string]$SourceRoot,
    [Parameter(Mandatory=$true)][string]$ResourceRoot
)
$ErrorActionPreference = 'Stop'
# Compare complete files after packaging/installation: existence alone cannot
# detect truncated notices or an editor copied without its embedded attribution.
foreach ($relative in @('LICENSE.txt', 'NOTICE.txt',
                         'report_editor/assets/KaTeX-LICENSE.txt', 'report_editor/assets/editor.html')) {
    $expected = Get-FileHash -LiteralPath (Join-Path $SourceRoot $relative) -Algorithm SHA256
    $actual = Get-FileHash -LiteralPath (Join-Path $ResourceRoot $relative) -Algorithm SHA256
    if ($actual.Hash -ne $expected.Hash) {
        throw "Packaged license resource differs from the selected source: $relative"
    }
}
Write-Host 'Project notices and attributed editor resources match the selected source: OK'
