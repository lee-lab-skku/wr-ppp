"""Release validation and publication decisions; GitHub transport is substituted."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
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
        self.published_notes = []

    def metadata(self):
        self.notice = '## Bundled third-party sources\n\nFixture source-access directions.'
        notice = self.root / 'windows/RELEASE-NOTICE.md'
        notice.parent.mkdir(exist_ok=True)
        notice.write_text(self.notice + '\n', encoding='utf-8')
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
            if '--notes-file' in command:
                self.published_notes.append(Path(command[command.index('--notes-file') + 1]).read_text(encoding='utf-8'))
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
        self.assertEqual(release.release_notes(self.root, self.tag),
                         '### Added\n\n- [setup] Windows installer.\n\n' + self.notice + '\n')
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

    def staged_metadata(self, stable='- [build] Stable fix.', rc='- [build] RC fix.',
                        beta='- [setup] Beta feature.'):
        """Use non-stage order to ensure selection depends on versions, not proximity."""
        sections = [('Unreleased', '- Pending change.'), ('2.3.4-beta', beta),
                    ('2.3.5-rc', '- Future change.'), ('2.3.4', stable),
                    ('2.3.3-rc', '- Older change.'), ('2.3.4-rc', rc)]
        (self.root / 'template.tex').write_text(f'% Repository version: {self.tag}\n', encoding='utf-8')
        (self.root / 'CHANGELOG.md').write_text('\n\n'.join(
            f'## [{version}] &mdash; 2026-09-15\n\n### Changed\n\n{body}'
            for version, body in sections if body is not None) + '\n', encoding='utf-8')

    def test_stable_notes_collect_only_same_version_stages_in_order(self):
        self.staged_metadata(beta='- [setup] Beta feature.\n  Continuation with `code`.')
        notes = release.release_notes(self.root, self.tag)
        self.assertEqual(notes, '''## 2.3.4 &mdash; 2026-09-15

### Changed

- [build] Stable fix.

## 2.3.4-rc &mdash; 2026-09-15

### Changed

- [build] RC fix.

## 2.3.4-beta &mdash; 2026-09-15

### Changed

- [setup] Beta feature.
  Continuation with `code`.
''' + '\n' + self.notice + '\n')

    def test_notice_comes_once_from_selected_checkout_for_every_release_stage(self):
        notice_path = self.root / 'windows/RELEASE-NOTICE.md'
        for stage in ('', '-rc', '-beta'):
            with self.subTest(stage=stage):
                self.tag = 'v2.3.4' + stage
                self.staged_metadata()
                # Distinct checkout content must replace, not inherit, another
                # release's notice even when collecting its prerelease changes.
                notice = self.notice + '\nSource revision for ' + self.tag
                notice_path.write_bytes((notice + '\n').replace('\n', '\r\n').encode('utf-8'))
                notes = release.release_notes(self.root, self.tag)
                self.assertEqual(notes.count('## Bundled third-party sources'), 1)
                self.assertTrue(notes.endswith(notice + '\n'))

    def test_missing_or_empty_notice_prevents_publication(self):
        notice = self.root / 'windows/RELEASE-NOTICE.md'
        for content in (None, '', ' \r\n\t'):
            with self.subTest(content=content):
                if content is None:
                    notice.unlink()
                else:
                    notice.write_text(content, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'RELEASE-NOTICE'):
                    self.publish()
                self.assertEqual(self.calls, [])

    def test_stable_notes_allow_missing_prerelease_stages(self):
        for rc, beta in ((None, '- Beta.'), ('- RC.', None), (None, None)):
            with self.subTest(rc=rc, beta=beta):
                self.staged_metadata(rc=rc, beta=beta)
                notes = release.release_notes(self.root, self.tag)
                self.assertIn('Stable fix.', notes)
                self.assertEqual('- RC.' in notes, rc is not None)
                self.assertEqual('- Beta.' in notes, beta is not None)

    def test_stable_promotion_can_have_no_new_changes_but_requires_target_section(self):
        self.staged_metadata(stable='')
        notes = release.release_notes(self.root, self.tag)
        self.assertIn('RC fix.', notes)
        self.assertIn('Beta feature.', notes)
        for stable, rc, beta in ((None, '- RC.', '- Beta.'), ('', '', ''), ('', None, None)):
            with self.subTest(stable=stable, rc=rc, beta=beta):
                self.staged_metadata(stable=stable, rc=rc, beta=beta)
                with self.assertRaises(ValueError):
                    release.release_notes(self.root, self.tag)

    def test_prerelease_notes_remain_incremental(self):
        for stage, expected in (('rc', 'RC fix.'), ('beta', 'Beta feature.')):
            with self.subTest(stage=stage):
                self.tag = f'v2.3.4-{stage}'
                self.staged_metadata()
                notes = release.release_notes(self.root, self.tag)
                self.assertIn(expected, notes)
                for excluded in ('Stable fix.', 'Pending change.', 'Future change.', 'Older change.',
                                 'Beta feature.' if stage == 'rc' else 'RC fix.'):
                    self.assertNotIn(excluded, notes)

    def test_empty_prerelease_cannot_borrow_changes_from_other_stages(self):
        self.tag = 'v2.3.4-rc'
        self.staged_metadata(rc='')
        with self.assertRaises(ValueError):
            release.release_notes(self.root, self.tag)

    def test_selected_prerelease_sections_require_unique_valid_dates(self):
        for stage in ('rc', 'beta'):
            for invalid in ('duplicate', '2026-02-30', 'undated'):
                with self.subTest(stage=stage, invalid=invalid):
                    self.staged_metadata()
                    path = self.root / 'CHANGELOG.md'
                    text = path.read_text(encoding='utf-8')
                    heading = f'## [2.3.4-{stage}] &mdash; 2026-09-15'
                    if invalid == 'duplicate':
                        text += '\n' + heading + '\n\n- Duplicate.\n'
                    else:
                        text = text.replace(heading, f'## [2.3.4-{stage}]' +
                                            (f' &mdash; {invalid}' if invalid != 'undated' else ''))
                    path.write_text(text, encoding='utf-8')
                    with self.assertRaises(ValueError):
                        self.publish()
                    self.assertEqual(self.calls, [])

    def test_aggregated_notes_reach_new_and_resumed_release_drafts(self):
        self.staged_metadata()
        original = (self.root / 'CHANGELOG.md').read_bytes()
        for existing in (None, {'draft': True, 'target_commitish': self.commit}):
            with self.subTest(existing=existing):
                self.publish(existing=existing)
                notes = self.published_notes[-1]
                self.assertIn('Stable fix.', notes)
                self.assertIn('RC fix.', notes)
                self.assertIn('Beta feature.', notes)
                self.assertNotIn('Pending change.', notes)
                self.assertEqual(notes, release.release_notes(self.root, self.tag))
                self.assertEqual(notes.count(self.notice), 1)
                self.assertEqual((self.root / 'CHANGELOG.md').read_bytes(), original)

    def test_prepare_command_accepts_promotion_with_only_prerelease_changes(self):
        self.staged_metadata(stable='')
        script = self.root / '.github/scripts/release.py'
        script.parent.mkdir(parents=True)
        script.write_bytes((REPO / '.github/scripts/release.py').read_bytes())
        def git(*args):
            return subprocess.check_output(['git', '-C', str(self.root), *args],
                                           stderr=subprocess.STDOUT, text=True).strip()
        git('init', '-q')
        git('config', 'user.name', 'Release test')
        git('config', 'user.email', 'test@example.invalid')
        git('add', 'template.tex', 'CHANGELOG.md', '.github/scripts/release.py', 'windows/RELEASE-NOTICE.md')
        git('commit', '-qm', 'promotion fixture')
        git('tag', '-a', self.tag, '-m', 'promotion fixture')
        commit = git('rev-parse', 'HEAD')
        output = self.root / 'github-output'
        result = subprocess.run([sys.executable, '-B', str(script), 'prepare', '--tag', self.tag,
                                 '--expected-commit', commit, '--github-output', str(output)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_text(encoding='utf-8'), f'commit={commit}\n')

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

    def test_development_artifacts_are_verified_but_cannot_be_published(self):
        for file in self.assets.iterdir():
            file.unlink()
        self.tag = 'v2.3.4-rc-12-gabcdef0'
        self.artifacts()
        self.assertEqual(release.verify_artifacts(self.assets, self.tag, development=True),
                         (self.installer, self.checksum))
        with self.assertRaises(ValueError):
            release.verify_artifacts(self.assets, self.tag)
        with self.assertRaises(ValueError):
            self.publish()
        self.assertEqual(self.calls, [])
        self.installer.write_bytes(b'MZ corrupt development build')
        with self.assertRaises(ValueError):
            release.verify_artifacts(self.assets, self.tag, development=True)

    def test_development_versions_reject_dirty_untagged_and_unsafe_names(self):
        for version in ('abcdef0', 'v2.3.4-dirty', 'v2.3.4-1-gabcdef0-dirty',
                        'v2.3.4-beta.1', '../v2.3.4', 'v2.3.4\n'):
            with self.subTest(version=version), self.assertRaises(ValueError):
                release.verify_artifacts(self.assets, version, development=True)

    def test_development_version_option_cannot_prepare_or_publish(self):
        for command in ('prepare', 'publish'):
            result = subprocess.run(
                [sys.executable, str(REPO / '.github/scripts/release.py'),
                 command, '--version', 'v2.3.4-1-gabcdef0'],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('--tag is required', result.stderr)

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
