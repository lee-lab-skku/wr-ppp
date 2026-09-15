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
