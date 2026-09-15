"""Release validation and publication decisions; GitHub transport is substituted."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('wr_release', REPO / '.github/scripts/release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='wr release ')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.tag = 'v2.3.4'
        self.commit = 'a' * 40
        self.metadata()
        self.assets = self.root / 'assets'
        self.assets.mkdir()
        self.artifacts()
        self.calls = []

    def metadata(self):
        (self.root / 'template.tex').write_text(f'% Repository version: {self.tag}\n', encoding='utf-8')
        (self.root / 'CHANGELOG.md').write_text(
            f'# Changelog\n\n## [Unreleased]\n\n## [{self.tag[1:]}] &mdash; 2026-09-15\n\n'
            '### Added\n\n- [setup] Windows installer.\n\n## [1.0.0] &mdash; 2025-01-01\n\n- Old change.\n',
            encoding='utf-8')

    def artifacts(self):
        self.installer = self.assets / f'WeeklyReport-{self.tag}-Setup.exe'
        self.installer.write_bytes(b'MZ synthetic installer fixture')
        self.checksum = self.installer.with_suffix('.exe.sha256')
        self.checksum.write_text(f'{hashlib.sha256(self.installer.read_bytes()).hexdigest()}  {self.installer.name}\n', encoding='ascii')

    def transport(self, existing=None, fail=None):
        def run(command, **kwargs):
            self.calls.append(command)
            if command[1] == 'api':
                if existing is None:
                    return subprocess.CompletedProcess(command, 1, '', 'gh: Not Found (HTTP 404)')
                return subprocess.CompletedProcess(command, 0, json.dumps(existing), '')
            if fail and command[1:3] == ['release', fail]:
                return subprocess.CompletedProcess(command, 1, '', 'simulated failure')
            return subprocess.CompletedProcess(command, 0, '', '')
        return run

    def publish(self, **kwargs):
        release.publish(self.root, self.tag, self.commit, self.assets, 'owner/repo', self.transport(**kwargs))

    def test_tag_policy(self):
        for tag, pre in [('v0.0.0', False), ('v12.34.56', False), ('v2.3.4-beta', True), ('v2.3.4-rc', True)]:
            self.assertEqual(release.validate_tag(tag), pre)
        for tag in ('2.3.4', 'v02.3.4', 'v2.03.4', 'v2.3.04', 'v2.3.4-beta.1', 'v2.3.4-alpha', 'v2.3.4+build', 'v2.3.4\n'):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                release.validate_tag(tag)

    def test_notes_come_only_from_matching_release(self):
        self.assertEqual(release.release_notes(self.root, self.tag), '### Added\n\n- [setup] Windows installer.\n')
        for tag in ('v2.3.5', 'v2.3.4-rc'):
            with self.assertRaises(ValueError):
                release.release_notes(self.root, tag)

    def test_missing_or_duplicate_changelog_section_is_rejected(self):
        changelog = self.root / 'CHANGELOG.md'
        original = changelog.read_text(encoding='utf-8')
        for content in ('## [Unreleased]\n- Pending\n', original + original, original.replace('2026-09-15', '2026-02-30')):
            changelog.write_text(content, encoding='utf-8')
            with self.assertRaises(ValueError):
                release.release_notes(self.root, self.tag)

    def test_artifact_checks_reject_corruption_wrong_names_and_extra_files(self):
        self.assertEqual(release.verify_artifacts(self.assets, self.tag), (self.installer, self.checksum))
        self.installer.write_bytes(b'MZ corrupt transfer')
        with self.assertRaises(ValueError):
            release.verify_artifacts(self.assets, self.tag)
        self.artifacts()
        self.checksum.write_text(self.checksum.read_text().replace(self.installer.name, '../other.exe'))
        with self.assertRaises(ValueError):
            release.verify_artifacts(self.assets, self.tag)
        self.artifacts()
        (self.assets / 'old.exe').write_bytes(b'MZ old')
        with self.assertRaises(ValueError):
            release.verify_artifacts(self.assets, self.tag)

    def test_checkout_supports_annotated_tag_and_rejects_dirty_or_wrong_commit(self):
        def git(*args):
            return subprocess.check_output(['git', '-C', str(self.root), *args], stderr=subprocess.STDOUT, text=True).strip()
        git('init', '-q')
        git('config', 'user.name', 'Release test')
        git('config', 'user.email', 'test@example.invalid')
        git('add', 'template.tex', 'CHANGELOG.md')
        git('commit', '-qm', 'release fixture')
        git('tag', '-a', self.tag, '-m', 'annotated fixture')
        head, tag_object = git('rev-parse', 'HEAD'), git('rev-parse', f'refs/tags/{self.tag}')
        self.assertEqual(release.validate_checkout(self.root, self.tag, tag_object), head)
        (self.root / 'template.tex').write_text('changed')
        with self.assertRaises(ValueError):
            release.validate_checkout(self.root, self.tag, head)
        git('add', 'template.tex')
        git('commit', '-qm', 'different commit')
        with self.assertRaises(ValueError):
            release.validate_checkout(self.root, self.tag, head)

    def test_upload_precedes_publication_and_stable_release_uses_default_latest(self):
        self.publish()
        self.assertEqual([c[1:3] for c in self.calls[1:]], [['release', 'create'], ['release', 'upload'], ['release', 'edit']])
        self.assertIn('--draft', self.calls[1])
        self.assertIn('--verify-tag', self.calls[1])
        self.assertIn('--draft=false', self.calls[-1])
        self.assertFalse(any('--latest' in arg for call in self.calls for arg in call))

    def test_beta_and_rc_are_prereleases_and_never_latest(self):
        for suffix in ('beta', 'rc'):
            for file in self.assets.iterdir():
                file.unlink()
            self.tag = f'v2.3.4-{suffix}'
            self.metadata()
            self.artifacts()
            self.calls.clear()
            self.publish()
            self.assertIn('--prerelease', self.calls[1])
            self.assertIn('--latest=false', self.calls[-1])

    def test_failed_upload_leaves_draft_and_retry_can_replace_draft_assets(self):
        with self.assertRaises(RuntimeError):
            self.publish(fail='upload')
        self.assertFalse(any('--draft=false' in c for c in self.calls))
        self.calls.clear()
        self.publish(existing={'draft': True, 'target_commitish': self.commit})
        self.assertIn('--clobber', self.calls[-2])
        self.assertIn('--draft=false', self.calls[-1])

    def test_published_release_is_preserved_and_incomplete_release_fails(self):
        existing = {'draft': False, 'assets': [{'name': p.name, 'state': 'uploaded', 'size': p.stat().st_size}
                                              for p in (self.installer, self.checksum)]}
        self.publish(existing=existing)
        self.assertEqual(len(self.calls), 1)
        self.calls.clear()
        with self.assertRaises(ValueError):
            self.publish(existing={'draft': False, 'assets': []})
        self.assertEqual(len(self.calls), 1)

    def test_other_draft_and_api_failure_do_not_trigger_writes(self):
        with self.assertRaises(ValueError):
            self.publish(existing={'draft': True, 'target_commitish': 'other'})
        self.assertEqual(len(self.calls), 1)
        def denied(command, **kwargs):
            return subprocess.CompletedProcess(command, 1, '', 'Forbidden (HTTP 403)')
        with self.assertRaises(RuntimeError):
            release.publish(self.root, self.tag, self.commit, self.assets, 'owner/repo', denied)
