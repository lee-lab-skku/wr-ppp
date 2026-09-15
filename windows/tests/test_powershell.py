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
        self.env = dict(os.environ, PYTHONUTF8='1', PIP_DISABLE_PIP_VERSION_CHECK='1', PIP_NO_INDEX='1')

    def run_ps(self, shell, script, *args):
        return subprocess.run([shell, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script), *args],
                              cwd=self.root.parent, env=self.env, capture_output=True, encoding='utf-8', timeout=90)

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
                self.env['WR_TEST_EXIT'] = '7'
                result = self.run_ps(shell, caller)
                self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
                received, config, cwd = json.loads(result.stdout)
                self.assertEqual(received, arguments)
                self.assertEqual(config, self.env['WR_CONFIG'])
                self.assertEqual(Path(cwd), self.root.parent)
                self.env.pop('WR_TEST_EXIT')

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
