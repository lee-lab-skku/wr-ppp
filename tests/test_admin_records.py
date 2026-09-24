"""Execution-manifest compatibility and validation before consumer side effects."""

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from admin_records import read_manifest


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'history.tsv'
        self.rows = [
            ['schema', 'admin-wr-bundle/v1'],
            ['bundle', '2026-09-04', '2026-09-W1', '2026-08-31', '2026-09-06',
             'complete', 'not-required', '2026-09-W1.pdf', 'a' * 64],
            ['entry', '1', 'a', '"구성원 A"', 'required', 'included', '자료/보고서.pdf',
             '123', 'b' * 64, '2', '2', '3', 'current'],
            ['entry', '2', 'b', 'B', 'optional', 'optional-missing', '-', '-', '-', '0', '-', '-', 'no-report'],
        ]

    def read(self):
        self.path.write_bytes(('\ufeff# comment\r\n\r\n' + '\r\n'.join('\t'.join(r) for r in self.rows)).encode())
        return read_manifest(self.path)

    def test_legacy_and_additive_records(self):
        parsed = self.read()
        self.assertEqual(parsed.bundle.pdf_name, '2026-09-W1.pdf')
        self.assertEqual(parsed.entries[0].display_name, '"구성원 A"')
        self.assertEqual(sum(entry.page_count for entry in parsed.entries), 2)
        self.rows.extend([
            ['created-at', '123'],
            ['history', '2026-08-W4', 'a', 'unknown', 'No verified record'],
            ['candidate', 'a', 'selected', '자료/보고서.pdf', '123', 'b' * 64, 'current'],
            ['issue', 'warning', 'first-run', '-', 'Review'],
        ])
        self.assertEqual(self.read().entries, parsed.entries)

    def test_swapped_filename_hash(self):
        self.rows[1][7], self.rows[1][8] = self.rows[1][8], self.rows[1][7]
        with self.assertRaisesRegex(ValueError, r':4: bundle: pdf_sha256'):
            self.read()

    def test_source_names_are_preserved_without_host_path_interpretation(self):
        self.rows[2][6] = '자료/C:notes\\report.pdf'
        self.assertEqual(self.read().entries[0].source, self.rows[2][6])

    def test_invalid_counts_ranges_and_missing_metadata(self):
        for row, column, value in [(2, 9, 'b' * 64), (2, 9, '-1'), (2, 9, '0'),
                                   (2, 11, '4'), (2, 8, 'report.pdf'), (3, 9, '1'),
                                   (3, 6, 'report.pdf'), (2, 7, 'oops')]:
            with self.subTest(column=column, value=value):
                old = self.rows[row][column]
                self.rows[row][column] = value
                with self.assertRaisesRegex(ValueError, 'entry:'):
                    self.read()
                self.rows[row][column] = old

    def test_truncated_extra_duplicate_and_empty_fields(self):
        original = list(self.rows[2])
        for replacement in [original[:-1], original + ['extra'],
                            original[:3] + [''] + original[4:]]:
            self.rows[2] = replacement
            with self.assertRaises(ValueError):
                self.read()
        self.rows[2] = original
        self.rows.append(original)
        with self.assertRaisesRegex(ValueError, 'duplicate member'):
            self.read()

    def test_invalid_bundle_and_candidate(self):
        for column, value in [(1, '2026-02-30'), (7, '../bundle.pdf'), (7, 'C:\\bundle.pdf'), (6, 'required')]:
            old = self.rows[1][column]
            self.rows[1][column] = value
            with self.assertRaises(ValueError):
                self.read()
            self.rows[1][column] = old
        self.rows.append(['candidate', 'a', 'selected', 'report.pdf', '123', 'wrong', 'current'])
        with self.assertRaisesRegex(ValueError, 'candidate: sha256'):
            self.read()


if __name__ == '__main__':
    unittest.main()
