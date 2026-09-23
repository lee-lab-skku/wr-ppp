"""Shared browser transport and both persistence adapters, without TeX or a GUI."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'windows'))

from report_editor import TEMPLATE
from report_editor.server import VisualEditorServer
from report_editor.state_to_tex import render
from report_editor.tex_backend import TexBackend
from wr.visual_editor import VisualEditorServer as NativeEditorServer


def sample_state():
    return {'title': 'Report', 'author': 'Author', 'project': 'Project',
            'abstract': 'Summary', 'weekStart': '2026-09-21',
            'flow': [{'type': 'block', 'id': box, 'boxId': box, 'text': 'Result.'}
                     for box in ('progress', 'problems', 'plans')]}


class EditorTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='editor test ')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.source = self.root / 'main.tex'
        self.original = render(sample_state())
        self.source.write_text(self.original, encoding='utf-8')
        self.katex_license = (TEMPLATE.parent / 'KaTeX-LICENSE.txt').read_text(encoding='utf-8')

    def start(self, server):
        url = server.start()
        self.addCleanup(server.stop)
        return url

    def post(self, url, path, data, content_type='application/json'):
        base, token = url.split('/?')
        request = Request(base + path + '?' + token, data=data,
                          headers={'Content-Type': content_type})
        return urlopen(request, timeout=5)

    def test_tex_session_saves_separate_output_and_uploads_original(self):
        backend = TexBackend(self.source, week_start='2026-09-21')
        url = self.start(VisualEditorServer(backend))
        with urlopen(url, timeout=5) as response:
            html = response.read().decode('utf-8')
        self.assertIn('2026-09-21', html)
        self.assertIn('/api/state?token=', html)
        self.assertIn('BEGIN KATEX LICENSE\n' + self.katex_license + 'END KATEX LICENSE', html)
        self.assertFalse(backend.output.exists())
        state = backend.load()
        state['title'] = 'Edited report'
        with self.post(url, '/api/state', json.dumps(state).encode()) as response:
            self.assertEqual(response.status, 204)
        self.assertIn('Edited report', backend.output.read_text(encoding='utf-8'))
        self.assertEqual(self.source.read_text(encoding='utf-8'), self.original)
        self.assertEqual(backend.load()['title'], 'Edited report')

        image = b'original-image-bytes'
        body = (b'--boundary\r\nContent-Disposition: form-data; name="image"; filename="plot.png"\r\n'
                b'Content-Type: image/png\r\n\r\n' + image + b'\r\n--boundary--\r\n')
        with self.post(url, '/api/image', body, 'multipart/form-data; boundary=boundary') as response:
            path = json.load(response)['path']
        self.assertEqual((self.root / path).read_bytes(), image)
        with urlopen(url.split('/?')[0] + '/' + path, timeout=5) as response:
            self.assertEqual(response.read(), image)

        saved = backend.output.read_bytes()
        with self.assertRaises(HTTPError) as failure:
            self.post(url, '/api/state', b'{}')
        self.assertEqual(failure.exception.code, 400)
        self.assertEqual(backend.output.read_bytes(), saved)

    def test_native_session_keeps_form_persistence_and_callback(self):
        form = self.root / 'report.wr.json'
        values = {'title': 'Native', 'author': 'Author', 'project': 'Project',
                  'abstract': 'Summary', 'Progress': 'Result.', 'Problems': 'None.',
                  'Plans': 'Next.', 'tables': [], 'figures': []}
        form.write_text(json.dumps(values), encoding='utf-8')
        saved = []
        server = NativeEditorServer(form, TEMPLATE, on_save=saved.append)
        url = self.start(server)
        with urlopen(url, timeout=5) as response:
            html = response.read().decode()
            self.assertIn('Native', html)
            self.assertIn('BEGIN KATEX LICENSE\n' + self.katex_license + 'END KATEX LICENSE', html)
        state = server.backend.load()
        state['title'] = 'Native edit'
        with self.post(url, '/api/state', json.dumps(state).encode()) as response:
            self.assertEqual(response.status, 204)
        self.assertEqual(json.loads(form.read_text(encoding='utf-8'))['title'], 'Native edit')
        self.assertIn('Native edit', form.with_suffix('.tex').read_text(encoding='utf-8'))
        self.assertEqual(saved[0]['title'], 'Native edit')

    def test_guard_and_output_checks_leave_sources_untouched(self):
        self.source.write_text(self.original.replace(r'\begin{document}',
                                                    r'\newcommand{\custom}{value}' + '\n' + r'\begin{document}'),
                               encoding='utf-8')
        before = self.source.read_bytes()
        with self.assertRaisesRegex(ValueError, 'Cannot edit'):
            TexBackend(self.source)
        self.assertEqual(self.source.read_bytes(), before)
        self.assertFalse(self.source.with_name('main.edited.tex').exists())
        with self.assertRaisesRegex(ValueError, 'already exists'):
            TexBackend(self.source, self.source)
        outside = self.root / 'other'
        outside.mkdir()
        with self.assertRaisesRegex(ValueError, 'beside the source'):
            TexBackend(self.source, outside / 'edited.tex')

    def test_native_source_entry_and_package_import_from_another_directory(self):
        result = subprocess.run([sys.executable, str(ROOT / 'windows/weekly_report.py'), '--help'],
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        script = ('import sys; sys.path.insert(0, ' + repr(str(ROOT / 'windows')) + '); '
                  'before = list(sys.path); import wr; assert sys.path == before')
        result = subprocess.run([sys.executable, '-c', script], cwd=self.root,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_entry_points_resolve_resources_from_another_directory(self):
        guard = subprocess.run([sys.executable, str(ROOT / 'scripts/check_roundtrip.py'), str(self.source)],
                               cwd=self.root, capture_output=True, text=True)
        self.assertEqual(guard.returncode, 0, guard.stderr + guard.stdout)
        help_result = subprocess.run([sys.executable, str(ROOT / 'scripts/report-edit'), '--help'],
                                     cwd=self.root, capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        state = self.root / 'state.json'
        sample = sample_state()
        sample['title'] = '</script> in a report'
        state.write_text(json.dumps(sample), encoding='utf-8')
        artifact = self.root / 'editor.html'
        exported = subprocess.run([sys.executable, str(ROOT / 'scripts/build_artifact.py'),
                                   str(state), str(artifact)], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(exported.returncode, 0, exported.stderr)
        html = artifact.read_text(encoding='utf-8')
        self.assertIn('<\\/script> in a report', html)
        self.assertIn('BEGIN KATEX LICENSE\n' + self.katex_license + 'END KATEX LICENSE', html)


if __name__ == '__main__':
    unittest.main()
