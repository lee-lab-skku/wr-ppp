"""Exercise real PowerShell processes and argument boundaries without network access."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SHELLS = [p for p in (shutil.which('powershell.exe'), shutil.which('pwsh.exe')) if p]


@unittest.skipUnless(os.name == 'nt' and SHELLS, 'Requires native Windows PowerShell')
class PowerShellTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / '한글 repo [test] & space'
        (self.root / 'windows').mkdir(parents=True)
        for name in ('Windows-Setup.ps1', 'Start-Weekly-Report.ps1', 'windows/common.ps1'):
            shutil.copyfile(ROOT / name, self.root / name)
        (self.root / 'windows/requirements.txt').write_text('', encoding='utf-8')
        self.env = dict(os.environ, PYTHONUTF8='1', PIP_DISABLE_PIP_VERSION_CHECK='1', PIP_NO_INDEX='1', WR_TEST_EXIT='0')

    def run_ps(self, shell, script, *args, extra_env=None):
        return subprocess.run([shell, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script), *args],
                              cwd=self.root.parent, env={**self.env, **(extra_env or {})},
                              capture_output=True, encoding='utf-8', timeout=90)

    def test_license_files_reject_missing_or_changed_packaged_content(self):
        resources = self.root / 'installed app [test]' / '_internal'
        names = ('LICENSE.txt', 'NOTICE.txt', 'report_editor/assets/KaTeX-LICENSE.txt',
                 'report_editor/assets/editor.html')
        for name in names:
            source, target = self.root / name, resources / name
            source.parent.mkdir(parents=True, exist_ok=True)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, source)
            shutil.copyfile(source, target)
        checker = ROOT / 'windows/tests/check_license_files.ps1'
        for shell in SHELLS:
            with self.subTest(shell=shell, case='complete'):
                result = self.run_ps(shell, checker, '-SourceRoot', str(self.root),
                                     '-ResourceRoot', str(resources))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for name in names:
                target = resources / name
                original = target.read_bytes()
                for case in ('modified', 'missing'):
                    with self.subTest(shell=shell, file=name, case=case):
                        if case == 'modified':
                            target.write_bytes(b'!' + original[1:])
                        else:
                            target.unlink()
                        result = self.run_ps(shell, checker, '-SourceRoot', str(self.root),
                                             '-ResourceRoot', str(resources))
                        self.assertNotEqual(result.returncode, 0, result.stdout)
                        target.write_bytes(original)

    def test_setup_repeat_launch_arguments_and_config(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                setup = self.root / 'Windows-Setup.ps1'
                for _ in range(2):
                    result = self.run_ps(shell, setup, '-Python', sys._base_executable)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                entry = self.root / 'windows/weekly_report.py'
                entry.write_text('import sys, json, os\nprint(json.dumps([sys.argv[1:], os.getenv("WR_CONFIG"), os.getcwd()]))\n'
                                 'sys.exit(int(os.getenv("WR_TEST_EXIT", "0")))\n', encoding='utf-8')
                self.env['WR_CONFIG'] = str(self.root / '설정 [x].json')
                result = self.run_ps(shell, self.root / 'Start-Weekly-Report.ps1')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)[0], ['gui'])
                arguments = ['report-build', '', '한글 & [x]', 'quote"value', 'C:\\trailing\\', '\\\\server\\share\\folder with spaces']
                literal = ', '.join("'" + value.replace("'", "''") + "'" for value in arguments)
                caller = self.root / 'invoke.ps1'
                caller.write_text("$forward = @(" + literal + ")\n"
                                  "$captured = & (Join-Path $PSScriptRoot 'Start-Weekly-Report.ps1') @forward\n"
                                  "$code = $LASTEXITCODE\nif ($null -eq $captured) { exit 98 }\n"
                                  "Write-Output $captured\nexit $code\n", encoding='utf-8-sig')
                result = self.run_ps(shell, caller, extra_env={'WR_TEST_EXIT': '7'})
                self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
                received, config, cwd = json.loads(result.stdout)
                self.assertEqual(received, arguments)
                self.assertEqual(config, self.env['WR_CONFIG'])
                # Hosted Windows TEMP may use an 8.3 alias that os.getcwd expands.
                self.assertTrue(Path(cwd).samefile(self.root.parent), (cwd, self.root.parent))

    def test_incompatible_environment_and_missing_runtime_are_preserved(self):
        environment = self.root / '.venv'
        environment.mkdir()
        marker = environment / 'keep'
        marker.write_text('preserve', encoding='utf-8')
        for shell in SHELLS:
            result = self.run_ps(shell, self.root / 'Windows-Setup.ps1', '-Python', sys._base_executable)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(marker.read_text(), 'preserve')
            result = self.run_ps(shell, self.root / 'Start-Weekly-Report.ps1', 'preflight')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Windows-Setup.ps1', result.stderr)

    def test_dependency_tools_select_one_executable_from_duplicate_path_entries(self):
        curl = Path(os.environ['SystemRoot']) / 'System32/curl.exe'
        python = Path(sys._base_executable)
        # Repeated entries also trigger Get-Command's multi-application result,
        # without depending on a second installed curl or Python distribution.
        self.env['PATH'] = os.pathsep.join([str(curl.parent), str(python.parent)] * 2 + [self.env['PATH']])
        for name in ('windows/install-tex.ps1', '.github/scripts/prepare-inno.ps1'):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        common = self.root / 'windows/common.ps1'
        original = common.read_text(encoding='utf-8')
        # Stop at the first download boundary; never fetch or install test dependencies.
        common.write_text(original + '\nfunction Invoke-WrChecked {\n'
                          'param([string]$FilePath, [string[]]$Arguments)\n'
                          '[Console]::Out.WriteLine($FilePath)\nexit 0\n}\n', encoding='utf-8')
        for shell in SHELLS:
            for name in ('windows/install-tex.ps1', '.github/scripts/prepare-inno.ps1'):
                with self.subTest(shell=shell, script=name):
                    result = self.run_ps(shell, self.root / name)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertTrue(Path(result.stdout.strip()).samefile(curl), result.stdout)
        common.write_text(original, encoding='utf-8')
        probe = self.root / 'tool-probe.ps1'
        probe.write_text(". (Join-Path $PSScriptRoot 'windows/common.ps1')\n"
                         "try {\nResolve-WrPython -Python python.exe\n"
                         "Invoke-WrChecked (Get-Command curl.exe -CommandType Application -TotalCount 1).Source @('--version')\n"
                         "} catch { [Console]::Error.WriteLine($_.Exception.Message); exit 1 }\n", encoding='ascii')
        for shell in SHELLS:
            with self.subTest(shell=shell):
                result = self.run_ps(shell, probe)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(Path(result.stdout.splitlines()[0]).samefile(python), result.stdout)
                self.assertIn('curl ', result.stdout)

    def test_tex_distribution_uses_one_mirror_and_stops_on_setup_failures(self):
        shutil.copyfile(ROOT / 'windows/install-tex.ps1', self.root / 'windows/install-tex.ps1')
        bin_dir = self.root / '.runtime/TinyTeX/bin/windows'
        bin_dir.mkdir(parents=True)
        (bin_dir / 'tlmgr.bat').write_text(
            '@echo off\necho %*>>"%WR_TEST_TLMGR_LOG%"\n'
            'if "%1"=="update" exit /b %WR_TEST_UPDATE_EXIT%\nexit /b 0\n', encoding='ascii')
        # Substitute only external dependencies; execute the real orchestration
        # in PowerShell, including native exit handling and argument forwarding.
        (self.root / 'curl-stub.ps1').write_text(
            "$args | ConvertTo-Json | Set-Content -LiteralPath $env:WR_TEST_CURL_LOG\n"
            'Write-Output $env:WR_TEST_MIRROR\nexit ([int]$env:WR_TEST_CURL_EXIT)\n', encoding='ascii')
        with (self.root / 'windows/common.ps1').open('a', encoding='utf-8') as common:
            common.write("\nfunction Get-Command {\n"
                         "param($Name, $CommandType, $TotalCount, $ErrorAction)\n"
                         "if ($Name -ne 'curl.exe') { throw 'Unexpected executable lookup' }\n"
                         "[pscustomobject]@{ Source = (Join-Path $script:WrRoot 'curl-stub.ps1') }\n}\n"
                         "function Resolve-WrPython { param($Python) 'python-fixture' }\n"
                         "function Invoke-WrChecked { param($FilePath, $Arguments)\n"
                         "$Arguments | ConvertTo-Json | Set-Content -LiteralPath $env:WR_TEST_PREPARE_LOG\n}\n")
        tlmgr_log = self.root / 'tlmgr.log'
        curl_log = self.root / 'curl.json'
        prepare_log = self.root / 'prepare.json'
        mirror = 'https://mirror.example.invalid/tlnet'
        env = {'WR_TEST_TLMGR_LOG': str(tlmgr_log), 'WR_TEST_CURL_LOG': str(curl_log),
               'WR_TEST_PREPARE_LOG': str(prepare_log), 'WR_TEST_MIRROR': mirror + '/tlpkg/texlive.tlpdb.xz'}
        for shell in SHELLS:
            for mode in ('source', 'distribution', 'curl-failure', 'update-failure'):
                with self.subTest(shell=shell, mode=mode):
                    for log in (tlmgr_log, curl_log, prepare_log):
                        log.unlink(missing_ok=True)
                    env.update(WR_TEST_CURL_EXIT='7' if mode == 'curl-failure' else '0',
                               WR_TEST_UPDATE_EXIT='9' if mode == 'update-failure' else '0')
                    flags = [] if mode == 'source' else ['-PrepareDistribution']
                    result = self.run_ps(shell, self.root / 'windows/install-tex.ps1', *flags, extra_env=env)
                    if mode == 'curl-failure':
                        self.assertNotEqual(result.returncode, 0, result.stdout)
                        self.assertFalse(tlmgr_log.exists())
                        self.assertFalse(prepare_log.exists())
                        continue
                    calls = tlmgr_log.read_text().splitlines()
                    if mode == 'update-failure':
                        self.assertNotEqual(result.returncode, 0, result.stdout)
                        self.assertEqual(calls, ['option repository ' + mirror, 'update --self --all'])
                        self.assertFalse(prepare_log.exists())
                        continue
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    if mode == 'source':
                        self.assertFalse(curl_log.exists())
                        self.assertFalse(prepare_log.exists())
                        self.assertEqual(len(calls), 3)
                    else:
                        self.assertEqual(calls[:2], ['option repository ' + mirror, 'update --self --all'])
                        self.assertTrue(calls[2].startswith('install collection-'))
                        self.assertEqual(calls[3], 'postaction install script xetex')
                        args = json.loads(prepare_log.read_text(encoding='utf-8-sig'))
                        self.assertEqual(args[args.index('--repository') + 1], mirror)
                        self.assertEqual(args[1], 'prepare-tex')

    def test_release_version_uses_triggering_tag_and_rejects_dirty_checkout(self):
        def git(*args):
            return subprocess.check_output(['git', '-C', str(self.root), *args], stderr=subprocess.STDOUT, text=True).strip()
        git('init', '-q')
        git('config', 'user.name', 'PowerShell release test')
        git('config', 'user.email', 'test@example.invalid')
        git('add', '.')
        git('commit', '-qm', 'fixture')
        git('tag', 'v2.3.4-beta')
        git('tag', 'v2.3.4-rc')
        script = self.root / 'version.ps1'
        script.write_text(". (Join-Path $PSScriptRoot 'windows/common.ps1')\n"
                          "try { Get-WrVersion } catch { [Console]::Error.WriteLine($_.Exception.Message); exit 1 }\n",
                          encoding='ascii')
        self.env.update(GITHUB_ACTIONS='true', GITHUB_REF_TYPE='tag', GITHUB_REF_NAME='v2.3.4-beta')
        for shell in SHELLS:
            result = self.run_ps(shell, script)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), 'v2.3.4-beta')
        (self.root / 'windows/requirements.txt').write_text('changed', encoding='utf-8')
        for shell in SHELLS:
            self.assertNotEqual(self.run_ps(shell, script).returncode, 0)
