# Shared Windows automation; dot-source from an entry point. PowerShell 5.1+.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:WrRoot = Split-Path -Parent $PSScriptRoot

function Resolve-WrPython {
    param([string]$Python = '', [switch]$Bootstrap)
    if ($Python) {
        if (Test-Path -LiteralPath $Python -PathType Leaf) { $candidate = (Get-Item -LiteralPath $Python).FullName }
        else { $candidate = (Get-Command $Python -CommandType Application -TotalCount 1 -ErrorAction Stop).Source }
    } elseif (Test-Path -LiteralPath (Join-Path $script:WrRoot '.venv\Scripts\python.exe') -PathType Leaf) {
        $candidate = Join-Path $script:WrRoot '.venv\Scripts\python.exe'
    } elseif (Test-Path -LiteralPath (Join-Path $script:WrRoot '.venv\bin\python.exe') -PathType Leaf) {
        # MSYS/MinGW Python creates the POSIX venv layout while still reporting
        # sys.platform == win32 and supporting tkinter. Keep it usable when a
        # standard Windows Python installation is not available.
        $candidate = Join-Path $script:WrRoot '.venv\bin\python.exe'
    } elseif ($Bootstrap) {
        $launcher = Get-Command py.exe -CommandType Application -TotalCount 1 -ErrorAction SilentlyContinue
        if ($launcher) {
            $candidate = & $launcher.Source -3 -c 'import sys; print(sys.executable)'
            if ($LASTEXITCODE -ne 0) { throw 'Python launcher failed. Pass -Python <python.exe>.' }
        } else {
            $candidate = (Get-Command python.exe -CommandType Application -TotalCount 1 -ErrorAction Stop).Source
        }
    } else {
        throw 'Run Windows-Setup.ps1 first, or pass -Python <python.exe>.'
    }
    $candidate = (Get-Item -LiteralPath $candidate -ErrorAction Stop).FullName
    if ([IO.Path]::GetExtension($candidate) -ne '.exe') { throw 'Use a native Windows python.exe.' }
    $probe = Invoke-WrNative $candidate @('-c', 'import sys; assert sys.platform == "win32" and sys.version_info >= (3, 11)')
    if ($probe -ne 0) { throw 'Windows Python 3.11 or newer is required.' }
    return $candidate
}

function Invoke-WrNative {
    param([Parameter(Mandatory=$true)][string]$FilePath, [string[]]$Arguments = @(), [switch]$AsPipeline)
    # ProcessStartInfo avoids PowerShell 5.1 dropping empty arguments or literal quotes.
    # Quote using the Windows C runtime convention, including trailing backslashes.
    $quoted = foreach ($argument in $Arguments) {
        '"' + ([regex]::Replace([regex]::Replace($argument, '(\\*)"', '$1$1\"'), '(\\+)$', '$1$1')) + '"'
    }
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $FilePath
    $info.Arguments = $quoted -join ' '
    $info.WorkingDirectory = (Get-Location).ProviderPath
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $info.StandardOutputEncoding = [Text.Encoding]::UTF8
    $info.StandardErrorEncoding = [Text.Encoding]::UTF8
    if ($null -ne $info.EnvironmentVariables) { $info.EnvironmentVariables['PYTHONUTF8'] = '1' }
    $process = [Diagnostics.Process]::Start($info)
    try {
        # Drain both pipes concurrently, displaying prompts even without a newline.
        # Hidden terminal input (for example Slack configuration) must remain usable.
        $outBuffer = New-Object char[] 4096
        $errBuffer = New-Object char[] 4096
        if ($AsPipeline) { $stdout = $process.StandardOutput.ReadLineAsync() }
        else { $stdout = $process.StandardOutput.ReadAsync($outBuffer, 0, $outBuffer.Length) }
        $stderr = $process.StandardError.ReadAsync($errBuffer, 0, $errBuffer.Length)
        while ($null -ne $stdout -or $null -ne $stderr) {
            if ($null -ne $stdout -and $stdout.IsCompleted) {
                if ($AsPipeline) {
                    $line = $stdout.GetAwaiter().GetResult()
                    if ($null -eq $line) { $stdout = $null } else {
                        Write-Output $line
                        $stdout = $process.StandardOutput.ReadLineAsync()
                    }
                } else {
                    $count = $stdout.GetAwaiter().GetResult()
                    if ($count -eq 0) { $stdout = $null } else {
                        [Console]::Out.Write($outBuffer, 0, $count)
                        $stdout = $process.StandardOutput.ReadAsync($outBuffer, 0, $outBuffer.Length)
                    }
                }
            }
            if ($null -ne $stderr -and $stderr.IsCompleted) {
                $count = $stderr.GetAwaiter().GetResult()
                if ($count -eq 0) { $stderr = $null } else {
                    [Console]::Error.Write($errBuffer, 0, $count)
                    $stderr = $process.StandardError.ReadAsync($errBuffer, 0, $errBuffer.Length)
                }
            }
            if ($null -ne $stdout -or $null -ne $stderr) { Start-Sleep -Milliseconds 10 }
        }
        $process.WaitForExit()
        $global:LASTEXITCODE = $process.ExitCode
        if (-not $AsPipeline) { return $process.ExitCode }
    } finally { $process.Dispose() }
}

function Invoke-WrChecked {
    param([string]$FilePath, [string[]]$Arguments = @())
    $code = Invoke-WrNative -FilePath $FilePath -Arguments $Arguments
    if ($code -ne 0) { throw "Command failed with exit code ${code}: $FilePath" }
}

function Get-WrVersion {
    Push-Location -LiteralPath $script:WrRoot
    try {
        if ($env:GITHUB_ACTIONS -eq 'true' -and $env:GITHUB_REF_TYPE -eq 'tag') {
            # Several tags can refer to the same commit. CI must package the
            # triggering tag, not whichever tag git describe happens to choose.
            $tag = $env:GITHUB_REF_NAME
            if ($tag -notmatch '^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-(beta|rc))?$') {
                throw 'Invalid release tag.'
            }
            $tagCommit = & git rev-parse --verify "refs/tags/${tag}^{commit}"
            if ($LASTEXITCODE -ne 0) { throw 'Release tag is missing from the checkout.' }
            $headCommit = & git rev-parse HEAD
            if ($LASTEXITCODE -ne 0 -or $tagCommit -ne $headCommit) { throw 'Release tag does not match HEAD.' }
            $dirty = & git status --porcelain --untracked-files=no
            if ($LASTEXITCODE -ne 0 -or $dirty) { throw 'Release packaging requires a clean tracked checkout.' }
            return $tag
        }
        $version = & git describe --tags --match 'v[0-9]*' --dirty --always
        if ($LASTEXITCODE -ne 0 -or -not $version) { throw 'Cannot determine checkout version; build from a Git checkout.' }
        return $version
    } finally { Pop-Location }
}
