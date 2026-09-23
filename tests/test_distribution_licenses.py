"""Notice collection and artifact checks using local package/archive fixtures."""
import hashlib
from importlib import util
import io
import json
import lzma
from pathlib import Path
import shutil
import tarfile
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = util.spec_from_file_location('distribution_licenses', ROOT / 'windows/distribution_licenses.py')
licenses = util.module_from_spec(SPEC)
SPEC.loader.exec_module(licenses)


class Distribution:
    def __init__(self, root, name):
        self.root, self.version = root, '1.2.3'
        self.files = [Path(f'{name}-1.2.3.dist-info/licenses/LICENSE')]
        path = root / self.files[0]
        path.parent.mkdir(parents=True)
        path.write_bytes((name + ' full original notice\r\n').encode())

    def locate_file(self, path):
        return self.root / path


class DistributionLicenseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / '한글 bundle [test]'
        self.root.mkdir()
        self.tex = self.root / 'tex'
        (self.tex / 'tlpkg').mkdir(parents=True)
        (self.tex / 'LICENSE.TL').write_bytes(b'TeX Live terms\r\n')
        (self.tex / 'LICENSE.CTAN').write_bytes(b'CTAN terms\n')
        self.cache = self.root / 'download-cache'

    def runtime(self):
        python = self.root / 'python'
        python.mkdir()
        (python / 'LICENSE.txt').write_bytes(b'Combined Python and incorporated-software terms\r\n')
        distributions = {name: Distribution(self.root / 'packages', name)
                         for name in ('pypdf', 'tzdata', 'pyinstaller')}
        hook = self.root / 'pyi_rth__tkinter.py'
        hook.write_bytes(b'# Copyright: example\n# Apache-2.0\npass\n')
        staging = self.root / 'staging'
        toc = licenses.collect_runtime(staging, [('tkinter', str(hook), 'PYSOURCE')], python, distributions)
        for name, source, _kind in toc:
            target = self.root / '_internal' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        return distributions

    def tex_fixture(self, members=None, relocated=True):
        members = members or {'doc/fonts/example/COPYING': b'Full license\r\n',
                              'doc/fonts/example/README.md': b'Copyright and provenance\n',
                              'doc/fonts/example/manual.pdf': b'Unneeded manual'}
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode='w:xz') as archive:
            for name, content in members.items():
                info = tarfile.TarInfo(name)
                info.size = len(content)
                archive.addfile(info, io.BytesIO(content))
        self.archive = data.getvalue()
        checksum = hashlib.sha512(self.archive).hexdigest()
        self.installed = f'name example\nrevision 123\ndoccontainerchecksum {checksum}\n'
        self.remote = self.installed + ('relocated 1\n' if relocated else '') + 'docfiles size=1\n'
        self.remote += ''.join(' ' + ('RELOC/' if relocated else '') + name + '\n' for name in members)
        (self.tex / 'tlpkg/texlive.tlpdb').write_text(self.installed, encoding='utf-8')
        self.requests = []

    def fetch(self, url):
        self.requests.append(url)
        if url.endswith('texlive.tlpdb.xz'):
            return lzma.compress(self.remote.encode())
        self.assertTrue(url.endswith('/archive/example.doc.tar.xz'))
        return self.archive

    def prepare(self):
        licenses.prepare_tex(self.tex, self.cache, fetch=self.fetch)

    def complete(self):
        self.runtime()
        self.tex_fixture()
        self.prepare()
        shutil.copyfile(ROOT / 'windows/TeX-NOTICE.txt', self.tex / 'README.WeeklyReport.txt')

    def test_runtime_copies_selected_interpreter_distribution_and_hook_bytes(self):
        self.runtime()
        shutil.rmtree(self.tex)
        licenses.verify_distribution(self.root)
        copied = self.root / '_internal/licenses/python/LICENSE.txt'
        self.assertEqual(copied.read_bytes(), (self.root / 'python/LICENSE.txt').read_bytes())
        hook = self.root / '_internal/licenses/pyinstaller/runtime-hooks/pyi_rth__tkinter.py'
        self.assertEqual(hook.read_bytes(), (self.root / hook.name).read_bytes())

    def test_runtime_missing_licenses_fail_instead_of_using_project_license(self):
        distributions = self.runtime()
        for name in distributions:
            with self.subTest(component=name):
                saved = distributions[name].files
                distributions[name].files = []
                with self.assertRaisesRegex(ValueError, 'No installed license'):
                    licenses.collect_runtime(self.root / 'retry', [], self.root / 'python', distributions)
                distributions[name].files = saved
        (self.root / 'python/LICENSE.txt').unlink()
        with self.assertRaisesRegex(ValueError, 'Required runtime notice'):
            licenses.collect_runtime(self.root / 'retry', [], self.root / 'python', distributions)

    def test_tex_recovers_only_notices_without_changing_install_options(self):
        self.tex_fixture()
        before = (self.tex / 'tlpkg/texlive.tlpdb').read_bytes()
        self.prepare()
        files = list((self.tex / licenses.TEX_NOTICES / 'files').rglob('*'))
        self.assertEqual(sorted(p.name for p in files if p.is_file()), ['COPYING', 'README.md'])
        self.assertEqual((self.tex / 'tlpkg/texlive.tlpdb').read_bytes(), before)
        self.assertFalse((self.tex / 'texmf-dist/doc').exists())
        self.assertEqual((self.tex / licenses.TEX_NOTICES / 'files/example/doc/fonts/example/COPYING').read_bytes(),
                         b'Full license\r\n')

    def test_prepared_cache_is_offline_and_bound_to_metadata_and_notices(self):
        self.tex_fixture()
        self.prepare()
        def no_network(_url):
            self.fail('A valid prepared tree must not require the live repository')
        licenses.prepare_tex(self.tex, self.cache, fetch=no_network)
        path = self.tex / licenses.TEX_NOTICES / 'files/example/doc/fonts/example/COPYING'
        path.write_bytes(b'Changed')
        with self.assertRaisesRegex(ValueError, 'Missing or changed'):
            licenses.prepare_tex(self.tex, self.cache, fetch=no_network)

    def test_mismatched_live_repository_does_not_replace_cached_tree(self):
        self.tex_fixture()
        self.prepare()
        original = (self.tex / licenses.TEX_NOTICES / 'manifest.json').read_bytes()
        (self.tex / 'tlpkg/texlive.tlpdb').write_text(self.installed + '\n', encoding='utf-8')
        self.remote = self.remote.replace('doccontainerchecksum ', 'ignored-checksum ')
        with self.assertRaisesRegex(ValueError, 'no longer matches'):
            self.prepare()
        self.assertEqual((self.tex / licenses.TEX_NOTICES / 'manifest.json').read_bytes(), original)

    def test_corrupt_archive_is_rejected_before_notices_are_published(self):
        self.tex_fixture()
        self.archive += b'corruption'
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            self.prepare()
        self.assertFalse((self.tex / licenses.TEX_NOTICES).exists())

    def test_repository_mismatch_preflight_reports_versions_before_any_archive_download(self):
        self.tex_fixture()
        installed = self.installed + '\nname z-later\nrevision 100\ndoccontainerchecksum ' + 'a' * 128 + '\n'
        self.remote += '\nname z-later\nrevision 101\ndoccontainerchecksum ' + 'b' * 128 + '\n'
        (self.tex / 'tlpkg/texlive.tlpdb').write_text(installed, encoding='utf-8')
        with self.assertRaises(ValueError) as raised:
            self.prepare()
        message = str(raised.exception)
        for detail in ('z-later', "revision ['100']", "revision ['101']", 'a' * 128, 'b' * 128,
                       'https://mirror.ctan.org', '-PrepareDistribution'):
            self.assertIn(detail, message)
        self.assertEqual(len(self.requests), 1)
        self.assertTrue(self.requests[0].endswith('texlive.tlpdb.xz'))
        self.assertFalse(self.cache.exists())
        self.assertFalse((self.tex / licenses.TEX_NOTICES).exists())

    def test_indexed_notice_missing_from_archive_fails_closed(self):
        self.tex_fixture()
        self.remote += ' RELOC/doc/fonts/example/NOTICE.txt\n'
        with self.assertRaisesRegex(ValueError, 'lacks indexed notices'):
            self.prepare()
        self.assertFalse((self.tex / licenses.TEX_NOTICES).exists())

    def test_preexisting_archive_cache_is_verified(self):
        self.tex_fixture()
        checksum = hashlib.sha512(self.archive).hexdigest()
        self.cache.mkdir()
        (self.cache / (checksum + '.tar.xz')).write_bytes(b'bad cache')
        with self.assertRaisesRegex(ValueError, 'Cached TeX documentation checksum'):
            self.prepare()

    def test_archive_paths_cannot_escape_even_with_valid_container_hash(self):
        self.tex_fixture({'../COPYING': b'outside'})
        with self.assertRaisesRegex(ValueError, 'Unsafe notice path'):
            self.prepare()
        self.assertFalse((self.root / 'COPYING').exists())

    def test_recorded_native_payload_hash_detects_replacement(self):
        distributions = self.runtime()
        binary = self.root / '_internal/python313.dll'
        binary.write_bytes(b'Fixture DLL')
        output = self.root / '_internal/licenses'
        licenses.collect_runtime(output, [], self.root / 'python', distributions,
                                 [('python313.dll', str(binary), 'BINARY')])
        shutil.rmtree(self.tex)
        licenses.verify_distribution(self.root)
        binary.write_bytes(b'Other bytes')
        with self.assertRaisesRegex(ValueError, 'python313.dll'):
            licenses.verify_distribution(self.root)

    def test_offline_artifact_requires_tex_inventory(self):
        self.runtime()
        shutil.rmtree(self.tex)
        with self.assertRaises(FileNotFoundError):
            licenses.verify_distribution(self.root, require_tex=True)

    def test_sanitization_preserves_collected_notices_and_records_modifications(self):
        spec = util.spec_from_file_location('sanitize', ROOT / 'windows/sanitize-bundle.py')
        sanitizer = util.module_from_spec(spec)
        spec.loader.exec_module(sanitizer)
        windows = self.root / 'windows'
        tex = windows / 'dist/WeeklyReport/tex'
        notices = tex / licenses.TEX_NOTICES
        notices.mkdir(parents=True)
        # An upstream legal file can have a suffix otherwise removed by cleanup.
        (tex / 'README.log').write_bytes(b'Keep this upstream notice')
        (tex / 'build.log').write_bytes(b'Remove generated log')
        (notices / 'COPYING.log').write_bytes(b'Keep collected terms')
        licenses.write_json(notices / 'manifest.json', {'files': {'README.log': licenses.digest(tex / 'README.log')}})
        shutil.copyfile(ROOT / 'windows/TeX-NOTICE.txt', windows / 'TeX-NOTICE.txt')
        with mock.patch.object(sanitizer, '__file__', str(windows / 'sanitize-bundle.py')):
            sanitizer.sanitize(tex.parent)
        self.assertFalse((tex / 'build.log').exists())
        self.assertEqual((tex / 'README.log').read_bytes(), b'Keep this upstream notice')
        self.assertEqual((notices / 'COPYING.log').read_bytes(), b'Keep collected terms')
        self.assertEqual((tex / 'README.WeeklyReport.txt').read_bytes(), (windows / 'TeX-NOTICE.txt').read_bytes())

    def test_manifest_paths_cannot_escape_distribution_on_either_platform(self):
        for value in ('../LICENSE', '/LICENSE', 'C:/LICENSE', 'a\\LICENSE', 'a/../LICENSE', 'a./LICENSE'):
            with self.subTest(path=value), self.assertRaises(ValueError):
                licenses.verify_files(self.root, {value: 'unused'})

    def test_unrelocated_documentation_and_installed_notices(self):
        self.tex_fixture({'README': b'Upstream readme'}, relocated=False)
        (self.tex / 'COPYING').write_bytes(b'Already installed terms')
        (self.tex / 'tlpkg/texlive.tlpdb').write_text(self.installed + 'runfiles size=1\n COPYING\n', encoding='utf-8')
        self.prepare()
        manifest = json.loads((self.tex / licenses.TEX_NOTICES / 'manifest.json').read_text())
        self.assertIn('COPYING', manifest['files'])
        self.assertIn(licenses.TEX_NOTICES + '/files/example/README', manifest['files'])

    def test_artifact_checks_reject_removed_and_changed_legal_files(self):
        self.complete()
        licenses.verify_distribution(self.root, require_tex=True)
        targets = ['_internal/licenses/python/LICENSE.txt', '_internal/licenses/pypdf/licenses/LICENSE',
                   '_internal/licenses/pyinstaller/runtime-hooks/pyi_rth__tkinter.py',
                   'tex/README.WeeklyReport.txt', 'tex/tlpkg/texlive.tlpdb',
                   'tex/tlpkg/wr-licenses/files/example/doc/fonts/example/COPYING']
        for name in targets:
            path = self.root / name
            saved = path.read_bytes()
            for missing in (False, True):
                with self.subTest(path=name, missing=missing):
                    if missing:
                        path.unlink()
                    else:
                        path.write_bytes(b'!' + saved[1:])
                    with self.assertRaises((ValueError, FileNotFoundError)):
                        licenses.verify_distribution(self.root, require_tex=True)
                    path.write_bytes(saved)


if __name__ == '__main__':
    unittest.main()
