"""Boundary and failure contracts using isolated files and substituted commands."""

import hashlib
import io
import os
from pathlib import Path
import runpy
import shlex
import shutil
import signal
import subprocess
import tarfile
import time
import unittest

import test_admin_workflow as admin
import test_report_build as report


class ReportSafetyTests(unittest.TestCase):
    setUp = report.ReportSerialTests.setUp

    def run_build(self, *args):
        return subprocess.run(
            [str(self.repo / 'scripts/report-build'), *args], cwd=self.source,
            env=dict(os.environ, PATH=f'{self.bin}:{os.environ["PATH"]}'),
            capture_output=True, text=True, timeout=10)

    def fail_docker(self):
        (self.bin / 'docker').write_text('#!/bin/sh\ncat >/dev/null\nexit 17\n')

    def test_here_failure_preserves_pdf(self):
        pdf = self.source / (self.source.name + '.pdf')
        pdf.write_bytes(b'previous')
        self.fail_docker()
        self.assertNotEqual(self.run_build('--here').returncode, 0)
        self.assertEqual(pdf.read_bytes(), b'previous')

    def test_output_alias_of_source_preserves_pdf_on_failure(self):
        alias = self.root / 'alias'
        alias.symlink_to(self.source, target_is_directory=True)
        (self.repo / '.local-config').write_text(
            f'PDF_OUTPUT_DIR={shlex.quote(str(alias))}\nDOCKER_IMAGE=test-image\n')
        pdf = self.source / (self.source.name + '.pdf')
        pdf.write_bytes(b'previous')
        self.fail_docker()
        self.assertNotEqual(self.run_build().returncode, 0)
        self.assertEqual(pdf.read_bytes(), b'previous')

    def test_empty_output_is_rejected_without_replacement(self):
        pdf = self.output / (self.source.name + '.pdf')
        pdf.write_bytes(b'previous')
        (self.bin / 'docker').write_text('#!/bin/sh\ncat >/dev/null\n')
        result = self.run_build()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(pdf.read_bytes(), b'previous')

    def test_success_preserves_unselected_local_pdf(self):
        pdf = self.source / (self.source.name + '.pdf')
        pdf.write_bytes(b'local review')
        self.assertEqual(self.run_build().returncode, 0)
        self.assertEqual(pdf.read_bytes(), b'local review')

    def test_existing_pdf_remains_available_during_build(self):
        pdf = self.source / (self.source.name + '.pdf')
        pdf.write_bytes(b'previous')
        snapshot = self.root / 'snapshot'
        admin.executable(self.bin / 'docker', f'''
import sys
from pathlib import Path
sys.stdin.buffer.read()
pdf = Path({str(pdf)!r})
Path({str(snapshot)!r}).write_bytes(pdf.read_bytes() if pdf.exists() else b'MISSING')
sys.stdout.buffer.write(b'%PDF-1.4\\nnew')
''')
        self.assertEqual(self.run_build('--here').returncode, 0)
        self.assertEqual(snapshot.read_bytes(), b'previous')
        self.assertEqual(pdf.read_bytes(), b'%PDF-1.4\nnew')
        self.assertEqual(self.run_build('--here').returncode, 0)
        self.assertEqual(snapshot.read_bytes(), b'%PDF-1.4\nnew')

    def test_replacement_is_staged_beside_destination_and_touched(self):
        log = self.root / 'publish-events'
        for name in ('mv', 'touch'):
            real = shutil.which(name)
            admin.executable(self.bin / name, f'''
import os, sys
from pathlib import Path
with Path({str(log)!r}).open('a') as out:
    out.write({name!r} + '\\t' + '\\t'.join(sys.argv[1:]) + '\\n')
os.execv({real!r}, [{real!r}, *sys.argv[1:]])
''')
        pdf = self.output / (self.source.name + '.pdf')
        for _ in range(2):
            self.assertEqual(self.run_build().returncode, 0)
        events = [line.split('\t') for line in log.read_text().splitlines()]
        moves = [e for e in events if e[0] == 'mv' and e[-1] == str(pdf)]
        self.assertEqual(len(moves), 2)
        self.assertTrue(all(Path(e[-2]).parent == self.output for e in moves))
        self.assertEqual(len([e for e in events if e[0] == 'touch' and e[-1] == str(pdf)]), 2)

    def test_bad_date_and_missing_source_do_not_change_pdf(self):
        pdf = self.output / (self.source.name + '.pdf')
        pdf.write_bytes(b'previous')
        for args in (('--date', '2026-02-29'), ('missing.tex',), ('--serial', '0')):
            self.assertEqual(self.run_build(*args).returncode, 2)
            self.assertEqual(pdf.read_bytes(), b'previous')


class SetupSafetyTests(unittest.TestCase):
    setUp = admin.AdminPathTests.setUp

    def run_setup(self, *args):
        return subprocess.run([str(self.repo / 'scripts/setup.sh'), *args],
                              env=self.env, capture_output=True, text=True, timeout=10)

    @unittest.expectedFailure
    def test_unknown_option_does_not_change_config(self):
        before = self.config.read_bytes()
        self.assertEqual(self.run_setup('--typo').returncode, 2)
        self.assertEqual(self.config.read_bytes(), before)

    @unittest.expectedFailure
    def test_help_does_not_change_config(self):
        before = self.config.read_bytes()
        result = self.run_setup('--help')
        self.assertEqual(result.returncode, 0)
        self.assertIn('Usage:', result.stdout + result.stderr)
        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse((self.root / 'commands').exists())

    @unittest.expectedFailure
    def test_parent_conflict_is_detected_before_mutation(self):
        parent = self.root / 'skill-links/.agents'
        parent.mkdir(parents=True)
        (parent / 'skills').write_text('existing file')
        before = self.config.read_bytes()
        self.assertNotEqual(self.run_setup('--skills=agents', 'new-image').returncode, 0)
        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse((self.root / 'commands').exists())

    @unittest.expectedFailure
    def test_admin_output_uses_same_path_rules_as_reader(self):
        before = self.config.read_bytes()
        for value in (str(self.root / 'one/../two'), str(self.root / 'a\tb')):
            result = self.run_setup('--admin', '--skills=agents', f'--admin-output={value}')
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(self.config.read_bytes(), before)

    @unittest.expectedFailure
    def test_failed_link_install_restores_config_and_previous_links(self):
        command = self.root / 'commands/report-build'
        command.parent.mkdir()
        command.write_text('previous command')
        before = self.config.read_bytes()
        real_ln = shutil.which('ln')
        admin.executable(self.bin / 'ln', f'''
import os, sys
if '/.agents/' in sys.argv[-1]:
    sys.exit(19)
os.execv({real_ln!r}, [{real_ln!r}, *sys.argv[1:]])
''')
        result = self.run_setup('--skills=agents', '--replace-existing', 'new-image')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse(command.is_symlink())
        self.assertEqual(command.read_text(), 'previous command')


class BundleConcurrencyTests(unittest.TestCase):
    setUp = admin.BundleTests.setUp

    def test_concurrent_publications_keep_pdf_and_manifest_together(self):
        entered, release, waiting = (self.root / p for p in ('entered', 'release', 'waiting'))
        real_mv, real_sleep = shutil.which('mv'), shutil.which('sleep')
        admin.executable(self.bin / 'mv', f'''
import os, subprocess, sys, time
from pathlib import Path
result = subprocess.run([{real_mv!r}, *sys.argv[1:]])
if result.returncode == 0 and os.environ.get('REVIEW_ROLE') == 'A' and sys.argv[-1].endswith('2026-09-W1.pdf'):
    Path({str(entered)!r}).touch()
    deadline = time.monotonic() + 10
    while not Path({str(release)!r}).exists() and time.monotonic() < deadline:
        time.sleep(.01)
sys.exit(result.returncode)
''')
        admin.executable(self.bin / 'sleep', f'''
import os, sys
from pathlib import Path
if os.environ.get('REVIEW_ROLE') == 'B': Path({str(waiting)!r}).touch()
os.execv({real_sleep!r}, [{real_sleep!r}, *sys.argv[1:]])
''')
        command = [str(self.builder), '--storage-root', str(self.storage),
                   '--plan', str(self.plan), '--date', '2026-09-04']
        a = subprocess.Popen(command, env=dict(self.env, REVIEW_ROLE='A'),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        b = None
        try:
            deadline = time.monotonic() + 10
            while not entered.exists() and a.poll() is None and time.monotonic() < deadline:
                time.sleep(.01)
            self.assertTrue(entered.exists())
            self.plan.write_text(self.clean_plan.replace('\t구성원 가\t', '\tSecond run\t'))
            b = subprocess.Popen(command, env=dict(self.env, REVIEW_ROLE='B'),
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            while not waiting.exists() and b.poll() is None and time.monotonic() < deadline:
                time.sleep(.01)
            release.touch()
            a_out, a_err = a.communicate(timeout=10)
            b_out, b_err = b.communicate(timeout=10)
            self.assertEqual(a.returncode, 0, a_err)
            self.assertEqual(b.returncode, 0, b_err)
            pdf, manifest = map(Path, b_out.splitlines())
            bundle = next(r.split('\t') for r in manifest.read_text().splitlines() if r.startswith('bundle\t'))
            self.assertEqual(hashlib.sha256(pdf.read_bytes()).hexdigest(), bundle[8])
        finally:
            release.touch()
            for process in (a, b):
                if process is not None and process.poll() is None:
                    process.kill()
                    process.communicate()

    def prepare_final(self):
        result = admin.BundleTests.build(self)
        return [Path(p) for p in result.stdout.splitlines()]

    def command(self):
        return [str(self.builder), '--storage-root', str(self.storage),
                '--plan', str(self.plan), '--date', '2026-09-04']

    def test_active_lock_times_out_without_replacing_outputs(self):
        paths = self.prepare_final()
        before = [p.read_bytes() for p in paths]
        lock = self.output / '.2026-09-W1.pdf.publish.lock'
        lock.mkdir(); (lock / 'owner').write_text('other-host\t123\n')
        admin.executable(self.bin / 'sleep', 'pass\n')
        result = subprocess.run(self.command(), env=self.env, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('publication is locked', result.stderr)
        self.assertEqual([p.read_bytes() for p in paths], before)
        self.assertEqual((lock / 'owner').read_text(), 'other-host\t123\n')

    def test_signal_releases_only_acquired_locks(self):
        paths = self.prepare_final()
        acquired = self.output / '.2026-09-W1.pdf.publish.lock'
        occupied = paths[1].parent / '.2026-09-W1.manifest.tsv.publish.lock'
        occupied.mkdir(); (occupied / 'owner').write_text('other-host\t123\n')
        waiting = self.root / 'waiting'
        admin.executable(self.bin / 'sleep', f"from pathlib import Path\nimport time\nPath({str(waiting)!r}).touch()\ntime.sleep(.05)\n")
        process = subprocess.Popen(self.command(), env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 10
            while not waiting.exists() and process.poll() is None and time.monotonic() < deadline:
                time.sleep(.01)
            self.assertTrue(waiting.exists())
            process.send_signal(signal.SIGTERM)
            _, error = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 143, error)
            self.assertFalse(acquired.exists())
            self.assertTrue(occupied.exists())
        finally:
            if process.poll() is None: process.kill(); process.communicate()

    def test_changed_source_while_waiting_is_rejected(self):
        paths = self.prepare_final()
        before = [p.read_bytes() for p in paths]
        occupied = paths[1].parent / '.2026-09-W1.manifest.tsv.publish.lock'
        occupied.mkdir()
        admin.executable(self.bin / 'sleep', f"from pathlib import Path\nPath({str(self.source)!r}).write_bytes(b'changed')\nPath({str(occupied)!r}).rmdir()\n")
        result = subprocess.run(self.command(), env=self.env, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Selected source changed', result.stderr)
        self.assertEqual([p.read_bytes() for p in paths], before)
        self.assertFalse(list(self.output.glob('*.lock')))

    def test_refresh_failure_still_writes_matching_record(self):
        admin.executable(self.bin / 'touch', 'import sys\nsys.exit(1)\n')
        result = subprocess.run(self.command(), env=self.env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 3, result.stderr)
        pdf, manifest = map(Path, result.stdout.splitlines())
        row = next(r.split('\t') for r in manifest.read_text().splitlines() if r.startswith('bundle\t'))
        self.assertEqual(hashlib.sha256(pdf.read_bytes()).hexdigest(), row[8])


class ProbeAndResolverTests(unittest.TestCase):
    setUp = admin.BundleTests.setUp

    def test_resolver_entrypoints_follow_links_from_another_directory(self):
        for relative in ('scripts/resolve-repo-root', 'skills/wr-wr/scripts/resolve-repo-root',
                         'skills/admin-wr/scripts/resolve-repo-root'):
            result = subprocess.run([str(self.repo / relative)], cwd=self.root,
                                    capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout.strip(), str(self.repo))

    def probe(self, mode):
        admin.executable(self.bin / 'docker', '''
import io, os, sys, tarfile
from pathlib import Path
if sys.argv[1] in ('info', 'image') or 'missing=0' in sys.argv[-1]: sys.exit(0)
sys.stdin.buffer.read()
mode = os.environ['PROBE_MODE']
if mode == 'runtime': sys.exit(17)
files = {'status.tsv': b'pdfinfo\\t0\\npdftotext\\t0\\n',
         'pdfinfo.txt': b'Pages: 2\\nEncrypted: no\\n', 'text.txt': b'Report text'}
if mode == 'damaged': files['status.tsv'] = b'pdfinfo\\t1\\npdftotext\\t0\\n'
if mode == 'encrypted': files['pdfinfo.txt'] = b'Pages: 2\\nEncrypted: yes\\n'
if mode == 'text-failure': files['status.tsv'] = b'pdfinfo\\t0\\npdftotext\\t1\\n'
if mode == 'empty-text': files['text.txt'] = b''
if mode == 'changed': Path(os.environ['PROBE_SOURCE']).write_bytes(b'changed source')
with tarfile.open(fileobj=sys.stdout.buffer, mode='w|') as archive:
    for name, content in files.items():
        entry = tarfile.TarInfo(name); entry.size = len(content)
        archive.addfile(entry, io.BytesIO(content))
''')
        return subprocess.run([str(self.repo / 'scripts/probe-report'), '--storage-root',
                               str(self.storage), '--file', str(self.source)],
                              env=dict(self.env, PROBE_MODE=mode, PROBE_SOURCE=str(self.source)),
                              text=True, capture_output=True, timeout=10)

    def test_probe_success_and_failure_statuses(self):
        for mode, status in (('good', 0), ('damaged', 20), ('encrypted', 21),
                             ('text-failure', 20), ('empty-text', 0), ('runtime', 15), ('changed', 22)):
            with self.subTest(mode=mode):
                result = self.probe(mode)
                self.assertEqual(result.returncode, status, result.stderr)
                if mode == 'good': self.assertIn('pages\t2', result.stdout)
                if mode == 'empty-text': self.assertIn('text-status\tempty', result.stdout)


class MetadataTests(unittest.TestCase):
    def test_calendar_boundaries(self):
        for day, label, start, end in (
            ('2020-12-31', '2020-12-W5', '2020-12-28', '2021-01-03'),
            ('2021-01-01', '2020-12-W5', '2020-12-28', '2021-01-03'),
            ('2024-02-29', '2024-02-W5', '2024-02-26', '2024-03-03'),
            ('2026-08-31', '2026-09-W1', '2026-08-31', '2026-09-06')):
            with self.subTest(day=day):
                result = subprocess.run([str(admin.REPO / 'scripts/report-metadata.sh'), '--date', day],
                                        check=True, capture_output=True, text=True)
                rows = dict(line.split('\t') for line in result.stdout.splitlines())
                self.assertEqual((rows['week-label'], rows['week-start'], rows['week-end']), (label, start, end))


class LiteralManifestTests(unittest.TestCase):
    setUp = admin.BundleTests.setUp
    build = admin.BundleTests.build

    @unittest.expectedFailure
    def test_builder_and_notification_preserve_literal_quotes(self):
        name = '"Alice"'
        self.plan.write_text('schema\tadmin-wr-plan/v1\n'
                             f'entry\t1\ta\t{name}\trequired\tmissing\t-\tmissing-report\n'
                             'issue\terror\tmissing-report\ta\tNo report\n')
        result = self.build('--draft', '--output-dir', str(self.review))
        manifest = Path(result.stdout.splitlines()[1])
        notice = runpy.run_path(str(admin.REPO / 'scripts/notify-held'))['notice']
        payload, _ = notice(manifest)
        self.assertIn('• ' + name, payload['blocks'][0]['text']['text'])


class PdfPublisherTests(unittest.TestCase):
    setUp = report.ReportSerialTests.setUp

    def publish(self):
        return subprocess.run([str(self.repo / 'scripts/publish-pdf'), str(self.source_pdf), str(self.target_pdf)],
                              env=dict(os.environ, PATH=f'{self.bin}:{os.environ["PATH"]}'),
                              capture_output=True, text=True, timeout=10)

    def prepare(self):
        self.source_pdf = self.root / 'new.pdf'
        self.source_pdf.write_bytes(b'%PDF-1.4\nnew content')
        self.target_pdf = self.output / 'target.pdf'
        self.target_pdf.write_bytes(b'%PDF-1.4\nprevious')

    def test_invalid_bytes_and_copy_failure_preserve_target(self):
        self.prepare()
        before = self.target_pdf.read_bytes()
        self.source_pdf.write_bytes(b'not PDF')
        self.assertNotEqual(self.publish().returncode, 0)
        self.assertEqual(self.target_pdf.read_bytes(), before)
        self.source_pdf.write_bytes(b'%PDF-1.4\nnew')
        admin.executable(self.bin / 'cp', 'import sys\nfrom pathlib import Path\nPath(sys.argv[-1]).write_bytes(b"partial")\nsys.exit(1)\n')
        self.assertNotEqual(self.publish().returncode, 0)
        self.assertEqual(self.target_pdf.read_bytes(), before)
        self.assertFalse(list(self.output.glob('.report-pdf.*')))

    def test_directory_rejected_and_file_symlink_replaced_without_following(self):
        self.prepare()
        self.target_pdf.unlink()
        self.target_pdf.mkdir()
        self.assertNotEqual(self.publish().returncode, 0)
        self.assertFalse(list(self.target_pdf.iterdir()))
        self.target_pdf.rmdir()
        other = self.root / 'other.pdf'
        other.write_bytes(b'other content')
        self.target_pdf.symlink_to(other)
        self.assertEqual(self.publish().returncode, 0)
        self.assertFalse(self.target_pdf.is_symlink())
        self.assertEqual(other.read_bytes(), b'other content')

    def test_touch_failure_reports_already_replaced(self):
        self.prepare()
        admin.executable(self.bin / 'touch', 'import sys\nsys.exit(1)\n')
        result = self.publish()
        self.assertEqual(result.returncode, 3)
        self.assertIn('PDF was replaced', result.stderr)
        self.assertEqual(self.target_pdf.read_bytes(), self.source_pdf.read_bytes())

    @unittest.skipUnless(os.name == 'posix' and Path('/proc/sys/fs/inotify').exists(), 'Linux inotify check')
    def test_repeated_publication_emits_changes_without_target_deletion(self):
        import ctypes
        import struct
        self.prepare()
        libc = ctypes.CDLL(None, use_errno=True)
        fd = libc.inotify_init1(os.O_NONBLOCK)
        self.assertGreaterEqual(fd, 0)
        try:
            # Watch the containing directory as VS Code's filesystem service does.
            watch = libc.inotify_add_watch(fd, os.fsencode(self.output), 0x00000FFF)
            self.assertGreaterEqual(watch, 0)
            self.assertEqual(self.publish().returncode, 0)
            self.assertEqual(self.publish().returncode, 0)
            raw = os.read(fd, 65536)
            offset, events = 0, []
            while offset < len(raw):
                _, mask, _, size = struct.unpack_from('iIII', raw, offset)
                name = raw[offset + 16:offset + 16 + size].rstrip(b'\0')
                offset += 16 + size
                if name == b'target.pdf': events.append(mask)
            self.assertFalse(any(mask & 0x200 for mask in events))  # IN_DELETE
            self.assertGreaterEqual(sum(bool(mask & 0x80) for mask in events), 2)  # IN_MOVED_TO
            self.assertTrue(any(mask & 0x4 for mask in events))  # IN_ATTRIB (touch)
        finally:
            os.close(fd)
