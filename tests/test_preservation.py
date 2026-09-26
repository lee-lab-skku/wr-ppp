"""Source invariants: a preview must not quietly rewrite the report."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'windows'))
from report_editor.preservation import import_source, export_source
from report_editor.check_roundtrip import assess
from report_editor.tex_backend import TexBackend
from report_editor.persistence import ConflictError
from wr.visual_editor import values_to_state, state_to_values, FormBackend


class PreservationTests(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / 'template.tex').read_bytes().decode('utf-8')

    def test_template_noop_and_encoding(self):
        lf_source = self.source.replace('\r\n', '\n')
        for newline, bom in [('\n', ''), ('\r\n', ''), ('\n', '\ufeff'), ('\r\n', '\ufeff')]:
            source = bom + lf_source.replace('\n', newline)
            with self.subTest(newline=repr(newline), bom=bool(bom)):
                state = import_source(source)
                self.assertEqual(export_source(json.loads(json.dumps(state))), source)
                self.assertEqual(assess(source), (1.0, []))
                self.assertEqual([it['label'] for e in state['flow'] for it in e.get('items', [])],
                                 ['fig:calibration-curve', 'fig:rare-class-errors', 'fig:seed-variance'])

    def test_each_field_changes_only_its_span(self):
        for old, new in [('Calibration-Aware Classification in the Low-Data Regime', 'New title'),
                         ('A moderate calibration penalty improved macro F1', 'A modest penalty improved macro F1'),
                         ('71.4', '71.5'),
                         ('Calibration curves for the baseline and revised loss.', 'A revised caption.')]:
            state = import_source(self.source)
            if old in state['title']:
                state['title'] = state['title'].replace(old, new)
            else:
                for entry in state['flow']:
                    if entry['type'] == 'block' and old in entry['text']:
                        entry['text'] = entry['text'].replace(old, new)
                    for item in entry.get('items', []):
                        item['caption'] = item['caption'].replace(old, new)
            self.assertEqual(export_source(state), self.source.replace(old, new))

    def test_preamble_and_unsupported_body_are_preserved_and_protected(self):
        source = self.source.replace(r'\begin{document}', r'\usepackage[draft]{graphicx}' + '\n' + r'\newcommand \metric {Accuracy}' + '\n' + r'\begin{document}')
        source = source.replace('A moderate calibration penalty', r'\custom{nested {value}} A moderate calibration penalty', 1)
        state = import_source(source)
        self.assertEqual(export_source(state), source)
        opaque = next(e for e in state['flow'] if e['type'] == 'opaque' and r'\custom' in e.get('text', ''))
        opaque['text'] += 'changed'
        with self.assertRaisesRegex(ValueError, 'read-only'):
            export_source(state)

    def test_opaque_comments_do_not_become_body_text(self):
        state = import_source(self.source)
        self.assertFalse(any('% Use a comparison table' in e.get('text', '') for e in state['flow'] if e['type'] == 'block'))
        entry = next(e for e in state['flow'] if e.get('protected') and '% Use a comparison' in e.get('text', ''))
        state['flow'].remove(entry)
        with self.assertRaisesRegex(ValueError, 'Protected'):
            export_source(state)

    def test_table_column_change_and_label_tampering_are_rejected(self):
        state = import_source(self.source)
        entry = next(e for e in state['flow'] if e.get('table'))
        entry['text'] = '| X |\n| --- |\n| Y |'
        with self.assertRaisesRegex(ValueError, 'column count'):
            export_source(state)
        state = import_source(self.source)
        figure = next(e for e in state['flow'] if e['type'] == 'figure')
        figure['items'][0]['label'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'labels'):
            export_source(state)

    def test_referenced_figure_cannot_be_deleted(self):
        state = import_source(self.source)
        state['flow'] = [e for e in state['flow'] if e['type'] != 'figure']
        with self.assertRaisesRegex(ValueError, 'referenced label'):
            export_source(state)

    def test_figure_pair_split_keeps_identities(self):
        state = import_source(self.source)
        index = next(i for i,e in enumerate(state['flow']) if e['type'] == 'figure')
        figure = state['flow'][index]
        other = deepcopy(figure)
        other['id'] = 'newFigure'
        other['items'] = [figure['items'].pop()]
        state['flow'].insert(index + 1, other)
        result = export_source(state)
        self.assertIn('{fig:calibration-curve}', result)
        self.assertIn('{fig:rare-class-errors}', result)
        self.assertNotIn('\\ReportFigurePair', result)
        self.assertEqual(export_source(import_source(result)), result)

    def test_unknown_environment_and_malformed_input(self):
        for raw in [r'\begin{unknown}a {b} \end{unknown}',
                    r'\begin{verbatim}\end{document} % x\end{verbatim}',
                    r'\begin{unknown}unterminated']:
            source = self.source.replace(r'\begin{pppbox}{Progress}', raw + '\n' + r'\begin{pppbox}{Progress}')
            self.assertEqual(export_source(import_source(source)), source)

    def test_output_and_source_external_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'main.tex'
            path.write_bytes(self.source.encode())
            backend = TexBackend(path)
            state = backend.load()
            backend.output.write_text('external')
            with self.assertRaises(ConflictError):
                backend.save(state)
            self.assertEqual(backend.output.read_text(), 'external')
            backend.output.unlink()
            path.write_text('changed source')
            with self.assertRaises(ConflictError):
                backend.save(state)

    def test_native_roundtrip_keeps_custom_ids_and_extra_fields(self):
        values = {'title': 'Report', 'Progress': '  paragraph\n\n', 'other': {'x': 1},
                  'figures': [{'file': 'figures/a.png', 'id': 'customID', 'caption': 'A', 'other': 3},
                              {'file': 'figures/b.png', 'id': 'b', 'caption': 'B', 'position': 'after_progress', 'pair_group': 'pair', 'pair_order': 0, 'height_mm': 48},
                              {'file': 'figures/c.png', 'id': 'c', 'caption': 'C', 'position': 'after_progress', 'pair_group': 'pair', 'pair_order': 1, 'height_mm': 48}],
                  'tables': [{'caption': 'Original', 'rows': [['X']]}]}
        restored = state_to_values(values_to_state(values), values)
        # Form serialization orders pictures by their actual placement, preserving
        # the order within each placement and each picture's complete metadata.
        self.assertEqual({e['id']:e for e in restored['figures']}, {e['id']:e for e in values['figures']})
        self.assertEqual(restored['other'], values['other'])
        self.assertEqual(restored['Progress'], values['Progress'])
        self.assertEqual(restored['tables'], values['tables'])
        state = values_to_state(values)
        state['flow'].append({'type': 'pagebreak'})
        with self.assertRaisesRegex(ValueError, 'cannot be represented'):
            state_to_values(state, values)

    def test_native_validation_precedes_any_write_and_external_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'a.wr.json'
            original = json.dumps({'title': 'A', 'figures': []})
            path.write_text(original)
            backend = FormBackend(path)
            state = backend.load()
            with patch('wr.visual_editor.core.form_source', side_effect=ValueError('invalid')):
                with self.assertRaises(ValueError):
                    backend.save(state)
            self.assertEqual(path.read_text(), original)
            path.write_text('{"title":"external"}')
            with self.assertRaises(ConflictError):
                backend.save(state)

    def test_existing_nested_lists_and_page_breaks_are_read_only(self):
        for content in (r'\clearpage', r'\begin{itemize}\item A\begin{itemize}\item B\end{itemize}\end{itemize}',
                        r'\begin{itemize}\item[Special] A\item B\end{itemize}',
                        r'\begin{itemize}Introduction\item A\end{itemize}'):
            source = r'\begin{document}\begin{pppbox}{Progress}' + content + r'\end{pppbox}\end{document}'
            state = import_source(source)
            self.assertEqual(export_source(state), source)
            self.assertTrue(any(e['type'] == 'opaque' and content in e.get('text', '') for e in state['flow']))

    def test_edited_paragraph_break_is_not_silently_flattened(self):
        source = r'\begin{document}\begin{pppbox}{Progress}First sentence. Second sentence.\end{pppbox}\end{document}'
        state = import_source(source)
        block = next(e for e in state['flow'] if e['type'] == 'block')
        block['text'] = 'First sentence.\n\nSecond sentence.'
        self.assertIn('First sentence.\n\nSecond sentence.', export_source(state))

    def test_native_new_figure_identity_is_stable_across_saves(self):
        values = {'title': 'A', 'Progress': 'Result'}
        state = values_to_state(values)
        state['flow'].append({'type': 'figure', 'id': 'newFigure', 'heightMm': 40,
                              'items': [{'path': 'figures/a.png', 'caption': 'A', 'editorId': 'persistentA'}]})
        first = state_to_values(state, values)
        second = state_to_values(state, first)
        self.assertEqual(first['figures'], second['figures'])

    def test_figure_comments_survive_caption_edit_and_block_split(self):
        # Exercise both checkout styles on every host; byte reads retain CRLF.
        lf_source = self.source.replace('\r\n', '\n')
        for newline in ('\n', '\r\n'):
            with self.subTest(newline=repr(newline)):
                source = lf_source.replace('\n', newline)
                marker = '\\ReportFigurePair' + newline
                self.assertIn(marker, source)
                source = source.replace(marker, '\\ReportFigurePair % paired evidence' + newline, 1)
                state = import_source(source)
                figure = next(e for e in state['flow'] if e['type'] == 'figure')
                self.assertTrue(figure.get('structureLocked'))
                figure['items'][0]['caption'] = 'New caption'
                result = export_source(state)
                self.assertEqual(result, source.replace('Calibration curves for the baseline and revised loss.', 'New caption'))
                figure['items'].pop()
                with self.assertRaisesRegex(ValueError, 'comments'):
                    export_source(state)

    def test_native_partial_failure_reports_json_as_authoritative(self):
        import os
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'a.wr.json'
            path.write_text(json.dumps({'title': 'Before'}))
            backend = FormBackend(path)
            state = backend.load()
            state['title'] = 'After'
            replace = os.replace
            def fail_tex(source, target):
                if Path(target).suffix == '.tex':
                    raise PermissionError('open file')
                return replace(source, target)
            with patch('wr.visual_editor.os.replace', side_effect=fail_tex):
                with self.assertRaises(ConflictError):
                    backend.save(state)
            self.assertEqual(json.loads(path.read_text())['title'], 'After')
            reopened = FormBackend(path)
            reopened.save(reopened.load())
            self.assertIn('After', path.with_suffix('.tex').read_text())



if __name__ == '__main__':
    unittest.main()
