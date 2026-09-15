"""Release updates against local Git remotes, with substituted Docker and time."""

import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

if os.name == 'nt':
    raise unittest.SkipTest('POSIX Git updater; run in WSL.')


REPO = Path(__file__).resolve().parents[1]


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="report update ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.publisher = self.root / "publisher"
        self.publisher.mkdir()
        self.remote = self.root / "origin.git"
        self.repo = self.root / "installation"
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.output = self.root / "output"
        self.source = self.root / "weekly source"
        self.source.mkdir()
        (self.source / "main.tex").write_text("source\n")
        self.clock = self.root / "clock"
        self.clock.write_text("1800000000")
        self.calls = self.root / "git-calls"
        self.env = dict(os.environ, PATH=f"{self.bin}:{os.environ['PATH']}",
                        GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
        self.real_git = shutil.which("git")
        self.executable("git", f"""
import os, sys, time
from pathlib import Path
args = sys.argv[1:]
if 'ls-remote' in args or 'fetch' in args:
    with open({str(self.calls)!r}, 'a') as stream:
        stream.write(('fetch' if 'fetch' in args else 'lookup') + '\\n')
    failure = os.environ.get('UPDATE_TEST_FAIL')
    if failure == 'timeout' and 'ls-remote' in args:
        time.sleep(60)
    if failure == 'lookup' and 'ls-remote' in args or failure == 'fetch' and 'fetch' in args:
        print('simulated network failure', file=sys.stderr)
        sys.exit(1)
os.execv({self.real_git!r}, [{self.real_git!r}, *args])
""")
        real_date = shutil.which("date")
        self.executable("date", f"""
import os, sys
from pathlib import Path
if sys.argv[1:] == ['+%s']:
    print(Path({str(self.clock)!r}).read_text())
else:
    os.execv({real_date!r}, [{real_date!r}, *sys.argv[1:]])
""")
        self.executable("sudo", "import os, sys\nos.execvp(sys.argv[1], sys.argv[1:])\n")
        self.executable("docker", """
import os, sys, time
from pathlib import Path
sys.stdin.buffer.read()
if os.environ.get('UPDATE_TEST_ENTERED'):
    Path(os.environ['UPDATE_TEST_ENTERED']).touch()
if os.environ.get('UPDATE_TEST_GATE'):
    while not Path(os.environ['UPDATE_TEST_GATE']).exists():
        time.sleep(.02)
sys.stdout.buffer.write(b'%PDF-1.4\\n')
sys.exit(int(os.environ.get('UPDATE_TEST_BUILD_STATUS', '0')))
""")
        for directory in ("scripts",):
            shutil.copytree(REPO / directory, self.publisher / directory)
        for filename in ("weekly-report.sty", "template.tex", ".gitignore"):
            shutil.copyfile(REPO / filename, self.publisher / filename)
        setup = self.publisher / "scripts/setup.sh"
        setup.write_text(setup.read_text().replace(
            'REPORT_BUILD_TARGET="/usr/local/bin/report-build"',
            f'REPORT_BUILD_TARGET="{self.root / "commands/report-build"}"'))
        self.git(self.publisher, "init", "-b", "main")
        self.git(self.publisher, "config", "user.name", "Update Test")
        self.git(self.publisher, "config", "user.email", "update@example.invalid")
        self.git(self.publisher, "add", ".")
        self.git(self.publisher, "commit", "-m", "base")
        self.git(self.publisher, "tag", "v1.0.0")
        self.run_command([self.real_git, "init", "--bare", str(self.remote)])
        self.git(self.publisher, "remote", "add", "origin", str(self.remote))
        self.git(self.publisher, "push", "origin", "main", "--tags")
        self.git(self.remote, "symbolic-ref", "HEAD", "refs/heads/main")
        self.run_command([self.real_git, "clone", str(self.remote), str(self.repo)])
        self.config = self.repo / ".local-config"
        self.config.write_text(
            f"PDF_OUTPUT_DIR={shlex.quote(str(self.output))}\nDOCKER_IMAGE=test-image\n")
        self.state = self.repo / ".report-update/state"
        self.lock = self.repo / ".report-update/lock"

    def executable(self, name, body):
        path = self.bin / name
        path.write_text(f"#!{sys.executable}\n{body}")
        path.chmod(0o755)

    def run_command(self, args, cwd=None, env=None, status=0):
        result = subprocess.run(args, cwd=cwd, env=env or self.env,
                                text=True, capture_output=True, timeout=45)
        self.assertEqual(result.returncode, status, result.stderr)
        return result

    def git(self, repo, *args, status=0):
        return self.run_command([self.real_git, "-C", str(repo), *args], status=status).stdout.strip()

    def setup(self, *args, status=0):
        return self.run_command(["bash", str(self.repo / "scripts/setup.sh"), *args], status=status)

    def build(self, *args, env=None, status=0):
        return self.run_command(["bash", str(self.repo / "scripts/report-build"),
                                 "--here", "--serial", "7", "--date", "2026-09-14", *args],
                                cwd=self.source, env=env, status=status)

    def publish(self, tag, annotated=False):
        (self.publisher / "weekly-report.sty").write_text(f"% release {tag}\n")
        build = self.publisher / "scripts/report-build"
        build.write_text(build.read_text() + f"\necho 'executed release {tag}' >&2\n")
        self.git(self.publisher, "add", ".")
        self.git(self.publisher, "commit", "-m", tag)
        if annotated:
            self.git(self.publisher, "tag", "-a", tag, "-m", tag)
        else:
            self.git(self.publisher, "tag", tag)
        self.git(self.publisher, "push", "origin", "main", "--tags")
        return self.git(self.publisher, "rev-parse", "HEAD")

    def advance(self, seconds):
        self.clock.write_text(str(int(self.clock.read_text()) + seconds))

    def call_count(self, kind="lookup"):
        return self.calls.read_text().splitlines().count(kind) if self.calls.exists() else 0

    def test_setup_default_preserve_disable_and_invalid_values(self):
        self.setup()
        self.assertIn("AUTO_UPDATE_CHANNEL=off", self.config.read_text())
        self.setup("--auto-update")
        self.assertIn("AUTO_UPDATE_CHANNEL=stable", self.config.read_text())
        self.setup()
        self.assertIn("AUTO_UPDATE_CHANNEL=stable", self.config.read_text())
        self.setup("--auto-update=prerelease")
        self.build()
        self.assertTrue(self.state.exists())
        self.setup("--auto-update=off")
        self.assertFalse(self.state.exists())
        self.setup("--auto-update=prerelease")
        self.build()
        self.assertEqual(self.call_count(), 2)
        before = self.config.read_bytes()
        for args in (("--auto-update=",), ("--auto-update=beta",),
                     ("--auto-update", "--auto-update=off")):
            with self.subTest(args=args):
                self.setup(*args, status=2)
                self.assertEqual(self.config.read_bytes(), before)

    def test_disabled_and_invalid_builds_do_not_check(self):
        self.build(env=dict(self.env, AUTO_UPDATE_CHANNEL="stable"))
        self.assertFalse(self.state.exists())
        self.setup("--auto-update")
        self.build("--help")
        self.build("--unknown", status=2)
        self.build("missing.tex", status=2)
        self.assertEqual(self.call_count(), 0)

    def test_stable_update_preserves_branch_and_restarts_new_build(self):
        original = self.git(self.repo, "rev-parse", "main")
        target = self.publish("v1.1.0", annotated=True)
        self.publish("v1.2.0-beta")
        self.setup("--auto-update")
        result = self.build()
        self.assertIn("updated v1.0.0 -> v1.1.0", result.stderr)
        self.assertIn("executed release v1.1.0", result.stderr)
        self.assertIn("version: v1.1.0", result.stderr)
        self.assertIn("serial : #7", result.stderr)
        self.assertEqual(self.git(self.repo, "rev-parse", "HEAD"), target)
        self.assertEqual(self.git(self.repo, "rev-parse", "main"), original)
        self.assertEqual(self.git(self.repo, "branch", "--show-current"), "")
        self.assertFalse(self.lock.exists())
        self.assertEqual(self.call_count(), 1)

    def test_no_argument_build_updates_and_uses_configured_output(self):
        target = self.publish("v1.1.0")
        self.setup("--auto-update")
        result = self.run_command(["bash", str(self.repo / "scripts/report-build")], cwd=self.source)
        self.assertEqual(self.git(self.repo, "rev-parse", "HEAD"), target)
        self.assertIn("updated v1.0.0 -> v1.1.0", result.stderr)
        self.assertEqual((self.output / "weekly source.pdf").read_bytes(), b"%PDF-1.4\n")
        self.assertFalse(self.lock.exists())

    def test_prerelease_order_invalid_tags_and_global_sort_settings(self):
        self.publish("v1.2.0-beta")
        self.publish("v1.2.0-rc")
        expected = self.publish("v1.2.0")
        for tag in ("v9.0.0-alpha", "v9.0.0-beta.1", "v9.0.0-rc.2",
                    "v01.2.0", "v9.0.0+build", "other"):
            self.publish(tag)
        self.git(self.repo, "tag", "local-only")
        self.git(self.repo, "config", "--add", "versionsort.suffix", "-rc")
        self.git(self.repo, "config", "--add", "versionsort.suffix", "-beta")
        self.setup("--auto-update=prerelease")
        self.build()
        self.assertEqual(self.git(self.repo, "rev-parse", "HEAD"), expected)

    def test_numeric_order_and_beta_rc_progression(self):
        self.publish("v1.2.0")
        target = self.publish("v1.10.0-beta")
        self.setup("--auto-update=prerelease")
        self.build()
        self.assertEqual(self.git(self.repo, "rev-parse", "HEAD"), target)
        target = self.publish("v1.10.0-rc")
        self.advance(86400)
        self.build()
        self.assertEqual(self.git(self.repo, "rev-parse", "HEAD"), target)
        self.setup("--auto-update=stable")
        self.build()
        self.assertEqual(self.git(self.repo, "rev-parse", "HEAD"), target)

    def test_cache_expiry_and_channel_change(self):
        self.setup("--auto-update")
        self.build()
        target = self.publish("v1.1.0-beta")
        self.build()
        self.advance(86399)
        self.build()
        self.assertEqual(self.call_count(), 1)
        self.advance(1)
        self.build()
        self.assertEqual(self.call_count(), 2)
        self.setup("--auto-update=prerelease")
        self.build()
        self.assertEqual(self.call_count(), 3)
        self.assertEqual(self.git(self.repo, "rev-parse", "HEAD"), target)

    def test_lookup_and_fetch_failure_retry_without_losing_pdf(self):
        self.publish("v1.1.0")
        self.setup("--auto-update")
        for failure in ("lookup", "fetch"):
            with self.subTest(failure=failure):
                self.advance(86400)
                env = dict(self.env, UPDATE_TEST_FAIL=failure)
                result = self.build(env=env)
                self.assertIn("using the current checkout", result.stderr)
                before = self.call_count()
                self.advance(3599)
                self.build(env=env)
                self.assertEqual(self.call_count(), before)
                self.advance(1)
                self.build(env=env)
                self.assertEqual(self.call_count(), before + 1)
                self.assertTrue((self.source / "weekly source.pdf").exists())

    def test_network_timeout_is_bounded_and_records_retry(self):
        self.setup("--auto-update")
        self.executable("sleep", "import time\ntime.sleep(.1)\n")
        result = self.build(env=dict(self.env, UPDATE_TEST_FAIL="timeout"))
        self.assertIn("remote lookup failed or timed out", result.stderr)
        self.assertEqual(self.state.read_text().split()[-1], "3600")
        self.assertFalse(self.lock.exists())

    def test_tracked_changes_and_local_commits_are_preserved(self):
        self.publish("v1.1.0")
        self.setup("--auto-update")
        style = self.repo / "weekly-report.sty"
        style.write_text("local work\n")
        result = self.build()
        self.assertIn("tracked changes", result.stderr)
        self.git(self.repo, "add", "weekly-report.sty")
        self.advance(86400)
        self.assertIn("tracked changes", self.build().stderr)
        self.git(self.repo, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "commit", "-m", "local work")
        before = self.git(self.repo, "rev-parse", "HEAD")
        self.advance(86400)
        result = self.build()
        self.assertIn("does not include the current commits", result.stderr)
        self.assertEqual(self.git(self.repo, "rev-parse", "HEAD"), before)
        self.assertEqual(style.read_text(), "local work\n")

    def test_local_only_release_is_not_a_candidate(self):
        self.git(self.repo, "tag", "v99.0.0")
        target = self.publish("v1.1.0")
        self.setup("--auto-update")
        self.build()
        self.assertEqual(self.git(self.repo, "rev-parse", "HEAD"), target)

    def test_conflicting_local_tag_is_not_overwritten(self):
        self.publish("v1.1.0")
        # A differently named local commit owns the remote tag's name.
        self.git(self.repo, "tag", "v1.1.0", "HEAD")
        old = self.git(self.repo, "rev-parse", "v1.1.0")
        self.setup("--auto-update")
        self.assertIn("fetch failed", self.build().stderr)
        self.assertEqual(self.git(self.repo, "rev-parse", "v1.1.0"), old)

    def test_untracked_checkout_collision_is_preserved(self):
        (self.publisher / "new-file").write_text("upstream\n")
        self.publish("v1.1.0")
        local = self.repo / "new-file"
        local.write_text("local\n")
        before = self.git(self.repo, "rev-parse", "HEAD")
        self.setup("--auto-update")
        self.assertIn("checkout failed", self.build().stderr)
        self.assertEqual(local.read_text(), "local\n")
        self.assertEqual(self.git(self.repo, "rev-parse", "HEAD"), before)

    def test_no_eligible_tags_and_unwritable_state_fall_back(self):
        self.git(self.remote, "tag", "-d", "v1.0.0")
        self.setup("--auto-update")
        self.assertIn("no eligible release", self.build().stderr)
        shutil.rmtree(self.state.parent)
        self.state.parent.write_text("not a directory")
        self.assertIn("cannot store update state", self.build().stderr)

    def test_live_lock_times_out_without_removal_or_pdf_changes(self):
        self.setup("--auto-update")
        self.lock.mkdir(parents=True)
        (self.lock / "owner").write_text(f"test-host\t{os.getpid()}\n")
        pdf = self.source / "weekly source.pdf"
        pdf.write_bytes(b"existing PDF")
        # Advance the fixed number of polling attempts without a real 30s wait.
        self.executable("sleep", "pass\n")
        self.assertIn("installation is locked", self.build(status=1).stderr)
        self.assertEqual(pdf.read_bytes(), b"existing PDF")
        self.assertTrue(self.lock.exists())
        self.assertEqual(self.call_count(), 0)

    def test_signal_releases_lock_and_stops_build_process_group(self):
        self.setup("--auto-update")
        gate = self.root / "gate"
        entered = self.root / "entered"
        process = subprocess.Popen(
            ["bash", str(self.repo / "scripts/report-build"), "--here", "--serial", "1"],
            cwd=self.source, env=dict(self.env, UPDATE_TEST_GATE=str(gate),
                                      UPDATE_TEST_ENTERED=str(entered)),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 10
            while not entered.exists() and time.monotonic() < deadline:
                time.sleep(.02)
            self.assertTrue(entered.exists())
            process.send_signal(signal.SIGTERM)
            _, error = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 143, error)
            self.assertFalse(self.lock.exists())
            self.assertFalse((self.source / "weekly source.pdf").exists())
        finally:
            gate.touch()
            if process.poll() is None:
                process.kill()
                process.communicate()

    def test_malformed_state_is_ignored_and_failed_build_releases_lock(self):
        self.setup("--auto-update")
        self.state.parent.mkdir(exist_ok=True)
        self.state.write_text("stable\t$(touch malicious)\t86400\n")
        self.build(env=dict(self.env, UPDATE_TEST_BUILD_STATUS="1"), status=1)
        self.assertEqual(self.call_count(), 1)
        self.assertFalse(self.lock.exists())

    def test_builds_serialize_and_waiter_uses_new_state(self):
        self.setup("--auto-update")
        gate = self.root / "gate"
        entered = self.root / "entered"
        command = ["bash", str(self.repo / "scripts/report-build"), "--here", "--serial", "1"]
        first = subprocess.Popen(command, cwd=self.source,
                                 env=dict(self.env, UPDATE_TEST_GATE=str(gate),
                                          UPDATE_TEST_ENTERED=str(entered)),
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        second = None
        try:
            deadline = time.monotonic() + 10
            while not entered.exists() and time.monotonic() < deadline:
                time.sleep(.02)
            self.assertTrue(entered.exists())
            target = self.publish("v1.1.0")
            self.advance(86400)
            second = subprocess.Popen(command, cwd=self.source, env=self.env,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            time.sleep(.3)
            self.assertEqual(self.call_count(), 1)
            self.assertNotEqual(self.git(self.repo, "rev-parse", "HEAD"), target)
            gate.touch()
            _, error = first.communicate(timeout=10)
            self.assertEqual(first.returncode, 0, error)
            _, error = second.communicate(timeout=10)
            self.assertEqual(second.returncode, 0, error)
            self.assertEqual(self.git(self.repo, "rev-parse", "HEAD"), target)
            self.assertEqual(self.call_count(), 2)
            self.assertFalse(self.lock.exists())
        finally:
            gate.touch()
            for process in (first, second):
                if process is not None and process.poll() is None:
                    process.kill()
                    process.communicate()


if __name__ == "__main__":
    unittest.main()
