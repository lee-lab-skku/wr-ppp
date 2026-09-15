import datetime as dt
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wr import core, admin, skills
from wr.cli import notifications
from pypdf import PdfReader, PdfWriter


def pdf(pages=1, width=595, height=842):
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width, height)
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.storage = self.root / '보고서 원본'
        self.storage.mkdir()
        self.config = {'pdf_output': str(self.root / 'output'), 'admin_output': str(self.root / 'bundles'),
                       'admin_data': str(self.root / 'data')}
        self.source = self.storage / '보고서.pdf'
        self.source.write_bytes(pdf())
        self.rows = [['schema', 'admin-wr-plan/v1'],
                     ['entry', '1', 'a', '구성원 가', 'required', 'included', str(self.source), 'user-selected'],
                     ['candidate', 'a', 'selected', str(self.source), 'user-selected']]

    def compile(self, *args, **kwargs):
        return pdf()

    def test_week_month_boundary(self):
        self.assertEqual(core.metadata('2026-08-31'), {'report-date': '2026-08-31', 'week-label': '2026-09-W1',
                                                     'week-start': '2026-08-31', 'week-end': '2026-09-06'})
        self.assertEqual(core.metadata('2027-01-01')['week-label'], '2026-12-W5')

    def test_latex_error_summary_hides_package_noise(self):
        log = 'package line\n' * 200 + './wr-input.tex:8: LaTeX Error: broken.\nhelp\nl.8 bad\nNo pages'
        summary = core.latex_error_summary(log)
        self.assertIn('LaTeX Error: broken', summary)
        self.assertNotIn('package line', summary)

    def test_week_all_days_share_label(self):
        for day in range(365):
            date = dt.date(2026, 1, 1) + dt.timedelta(days=day)
            meta = core.metadata(date.isoformat())
            self.assertEqual(meta['week-label'], core.metadata(meta['week-start'])['week-label'])
            self.assertEqual(meta['week-label'], core.metadata(meta['week-end'])['week-label'])

    def test_invalid_dates(self):
        for date in ('2026-02-29', '2026-1-01', '2026-13-01', 'hello'):
            with self.subTest(date=date), self.assertRaises(ValueError):
                core.metadata(date)

    def test_form_escapes_special_characters(self):
        source = core.form_source({'title': 'A & B_2 50%', 'Progress': r'\input{secret}'})
        self.assertIn(r'A \& B\_2 50\%', source)
        self.assertIn(r'\textbackslash{}input\{secret\}', source)
        self.assertIn(r'\usepackage{kotex}', source)

    def test_form_preserves_inline_and_display_math(self):
        source = core.form_source({'Progress': r'결과는 $a_1 + b^2$이며 $$E=mc^2$$ 입니다.'})
        self.assertIn(r'결과는 $a_1 + b^2$이며 $$E=mc^2$$ 입니다.', source)

    def test_form_rejects_unclosed_or_unsafe_math(self):
        for value in ('$a', r'$\input{secret}$', '$$'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                core.form_source({'Progress': value})

    def test_markdown_block_and_inline_conversion(self):
        converted = core.markdown_to_latex(
            '## 실험 결과\n\n**굵게**, *기울임*, `sample_id` 및 [문서](https://example.com/a_b?q=1&x=2)\n\n'
            '- 첫 항목\n- 수식 $a_1+b^2$\n\n1. 확인\n2) 기록'
        )
        self.assertIn(r'\bfseries 실험 결과', converted)
        self.assertIn(r'\textbf{굵게}', converted)
        self.assertIn(r'\emph{기울임}', converted)
        self.assertIn(r'\texttt{sample\_id}', converted)
        self.assertIn(r'\href{https://example.com/a\_b?q=1\&x=2}{문서}', converted)
        self.assertIn(r'\begin{itemize}', converted)
        self.assertIn(r'\begin{enumerate}', converted)
        self.assertIn(r'\item 수식 $a_1+b^2$', converted)

    def test_markdown_display_math_and_hard_break(self):
        converted = core.markdown_to_latex('첫 줄  \n둘째 줄 $$E=mc^2$$\n\n$$\na_1 + b_2\n$$')
        self.assertIn('첫 줄' + r'\\', converted)
        self.assertIn(r'둘째 줄 $$E=mc^2$$', converted)
        self.assertIn('\\[\na_1 + b_2\n\\]', converted)

    def test_markdown_escapes_raw_latex_and_rejects_invalid_input(self):
        self.assertIn(r'\textbackslash{}input\{secret\}', core.markdown_to_latex(r'\input{secret}'))
        self.assertEqual(core.markdown_to_latex(r'가격은 10\$입니다'), r'가격은 10\$입니다')
        for value in ('$a', '[파일](file:///secret)', r'$\input{secret}$'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                core.markdown_to_latex(value)

    def test_word_style_formatting_and_heading_levels(self):
        converted = core.markdown_to_latex(
            '## 큰 소제목\n### 하위 제목\n#### 세부 제목\n'
            '[font=sans][size=12]**강조**[/size][/font] ++밑줄++ ~~취소선~~'
        )
        self.assertIn(r'\bfseries 큰 소제목', converted)
        self.assertIn(r'\itshape 하위 제목', converted)
        self.assertIn(r'\itshape 세부 제목', converted)
        self.assertIn(r'\textsf{{\fontsize{12pt}{14.4pt}\selectfont \textbf{강조}}}', converted)
        self.assertIn(r'\underline{밑줄}', converted)
        self.assertIn(r'\sout{취소선}', converted)

    def test_embedded_css_controls_latex_layout(self):
        css = '''<style>
        @page { size: A4; margin: 9mm 10mm 8mm 10mm; }
        body { font-size: 8.7pt; line-height: 1.18; }
        h2 { font-size: 11.3pt; line-height: 1.06; margin: 5px 0 2px 0; }
        p { margin: 1px 0 2px 0; }
        table { width: 100%; font-size: 7.9pt; margin: 2px 0 3px 0; }
        th, td { padding: 1.5px 3px; border: 1px solid #aaa; }
        </style>'''
        source = core.form_source({'Progress': css + '\n## 결과\n본문'}, allow_styles=True)
        self.assertNotIn('<style>', source)
        self.assertIn(r'\geometry{top=9mm,right=10mm,bottom=8mm,left=10mm,includefoot,footskip=4mm}', source)
        self.assertIn(r'\fontsize{8.7pt}{10.266pt}\selectfont', source)
        self.assertIn(r'\fontsize{11.3pt}{11.978pt}', source)
        self.assertIn(r'\vspace{3.75pt}', source)

    def test_user_css_is_locked_by_default_and_can_be_unlocked(self):
        value = '<style>@page { margin: 1mm; } body { font-size: 16pt; }</style>\n# 1.1 제목'
        locked = core.form_source({'Progress': value})
        unlocked = core.form_source({'Progress': value}, allow_styles=True)
        self.assertNotIn(r'\geometry{top=1mm', locked)
        self.assertNotIn(r'\fontsize{16pt}', locked)
        self.assertIn(r'\geometry{top=1mm', unlocked)
        self.assertIn(r'\fontsize{16pt}', unlocked)
        self.assertIn(r'\ReportHeading{1.1 제목}', locked)

    def test_markdown_headings_do_not_add_numbers(self):
        converted = core.markdown_to_latex('# 1.1 큰 제목\n## 1.1.1 작은 제목')
        self.assertIn(r'\ReportHeading{1.1 큰 제목}', converted)
        self.assertIn(r'\bfseries 1.1.1 작은 제목', converted)
        self.assertNotIn(r'\thereportsubsection', converted)

    def test_markdown_pipe_table_conversion(self):
        converted = core.markdown_to_latex(
            '| 항목 | 값 |\n|---|---:|\n| 평균 | 3.2 ms |\n| 최대 | **9.1 ms** |'
        )
        self.assertIn(r'\begin{tabularx}{\linewidth}{|X|X|}', converted)
        self.assertIn(r'\textbf{항목} & \textbf{값}', converted)
        self.assertIn(r'평균 & 3.2 ms', converted)
        self.assertIn(r'최대 & \textbf{9.1 ms}', converted)

    def test_markdown_image_reference_becomes_attachment_note(self):
        converted = core.markdown_to_latex('![전체 형상](/mnt/data/Image6.jpg)')
        self.assertIn(r'\textit{[그림 추가 필요: 전체 형상]}', converted)

    def test_form_table_rows(self):
        source = core.form_source({'tables': [{'caption': '표', 'rows': [['A', 'B'], ['1', '2']]}]})
        self.assertIn('A & B \\\\\n1 & 2', source)

    def test_form_rejects_unsafe_figure(self):
        with self.assertRaises(ValueError):
            core.form_source({'figures': [{'file': '../secret.pdf', 'id': 'x', 'caption': ''}]})

    def test_figures_are_inserted_at_selected_boundaries(self):
        figures = [
            {'file': f'figures/{position}.png', 'id': position, 'caption': position, 'position': position}
            for position in ('after_abstract', 'after_progress', 'after_problems', 'after_plans')
        ]
        source = core.form_source({'figures': figures})
        locations = {position: source.index('{fig:' + position + '}') for position in
                     ('after_abstract', 'after_progress', 'after_problems', 'after_plans')}
        progress = source.index(r'\begin{pppbox}{Progress}')
        problems = source.index(r'\begin{pppbox}{Problems}')
        plans = source.index(r'\begin{pppbox}{Plans}')
        self.assertLess(source.index(r'\end{reportabstract}'), locations['after_abstract'])
        self.assertLess(locations['after_abstract'], progress)
        self.assertLess(source.index(r'\end{pppbox}', progress), locations['after_progress'])
        self.assertLess(locations['after_progress'], problems)
        self.assertLess(source.index(r'\end{pppbox}', problems), locations['after_problems'])
        self.assertLess(locations['after_problems'], plans)
        self.assertGreater(locations['after_plans'], source.index(r'\end{pppbox}', plans))

    def test_legacy_figure_defaults_after_plans(self):
        source = core.form_source({'figures': [{'file': 'figures/legacy.png', 'id': 'legacy', 'caption': ''}]})
        self.assertGreater(source.index('{fig:legacy}'), source.index(r'\end{pppbox}', source.index(r'\begin{pppbox}{Plans}')))

    def test_invalid_figure_position_is_rejected(self):
        with self.assertRaises(ValueError):
            core.form_source({'figures': [{'file': 'figures/x.png', 'id': 'x', 'caption': '', 'position': 'inside'}]})

    def test_probe_actual_pdf(self):
        info = core.probe(self.storage, self.source)
        self.assertEqual(info['pages'], 1)
        self.assertEqual(info['sha256'], core.sha256(self.source))

    def test_probe_rejects_outside_root(self):
        outside = self.root / 'outside.pdf'
        outside.write_bytes(pdf())
        with self.assertRaises(ValueError):
            core.probe(self.storage, outside)

    def test_encrypted_pdf_rejected(self):
        writer = PdfWriter()
        writer.add_blank_page(100, 100)
        writer.encrypt('secret')
        writer.write(self.source)
        with self.assertRaises(ValueError):
            core.probe(self.storage, self.source)

    def test_failed_report_preserves_both_outputs(self):
        tex = self.storage / 'main.tex'
        tex.write_text('test')
        destination = Path(self.config['pdf_output']) / (self.storage.name + '.pdf')
        destination.parent.mkdir()
        destination.write_bytes(b'old-final')
        local = self.storage / destination.name
        local.write_bytes(b'old-local')
        with patch.object(core, 'compile_tex', side_effect=ValueError('build failed')):
            with self.assertRaises(ValueError):
                core.build_report(tex, self.config)
        self.assertEqual(destination.read_bytes(), b'old-final')
        self.assertEqual(local.read_bytes(), b'old-local')

    def test_locked_destination_has_actionable_error_and_preserves_file(self):
        destination = self.root / 'locked.pdf'
        destination.write_bytes(b'old')
        real_replace = os.replace
        def locked(source, target):
            if Path(target) == destination:
                raise PermissionError(5, 'Access denied')
            return real_replace(source, target)
        with patch.object(os, 'replace', side_effect=locked):
            with self.assertRaisesRegex(ValueError, 'PDF 뷰어를 닫고'):
                core.atomic_write(destination, b'new')
        self.assertEqual(destination.read_bytes(), b'old')

    def test_serial_excludes_existing_target_even_here(self):
        tex = self.storage / 'main.tex'
        tex.write_text('test')
        output = Path(self.config['pdf_output'])
        output.mkdir()
        (output / 'previous.pdf').write_bytes(pdf())
        (output / (self.storage.name + '.pdf')).write_bytes(pdf())
        with patch.object(core, 'compile_tex', self.compile):
            result = core.build_report(tex, self.config, here=True)
        self.assertEqual(result['serial'], 2)
        self.assertEqual(Path(result['pdf']).parent, self.storage)

    def test_report_no_input_mutation(self):
        tex = self.storage / 'custom name.tex'
        tex.write_text('% retained comment\nhello', encoding='utf-8')
        before = tex.read_bytes()
        with patch.object(core, 'compile_tex', self.compile):
            core.build_report(tex, self.config, serial=17, date='2026-09-04')
        self.assertEqual(before, tex.read_bytes())

    def test_duplicate_selection_rejected(self):
        self.rows.append(['entry', '2', 'b', 'B', 'required', 'included', str(self.source), 'selected'])
        with self.assertRaises(ValueError):
            admin.validate_plan(self.rows, self.storage, '2026-09-04')

    def test_missing_requires_issue(self):
        rows = [['schema', 'admin-wr-plan/v1'], ['entry', '1', 'a', 'A', 'required', 'missing', '-', 'missing-report']]
        with self.assertRaises(ValueError):
            admin.validate_plan(rows, self.storage, '2026-09-04')

    def test_future_history_rejected(self):
        self.rows.append(['history', '2026-09-W2', 'a', 'included', 'test'])
        with self.assertRaises(ValueError):
            admin.validate_plan(self.rows, self.storage, '2026-09-04')

    def test_draft_and_promotion_preserve_pages(self):
        self.source.write_bytes(pdf(2, 320, 480))
        original = self.source.read_bytes()
        with patch.object(admin, 'compile_tex', self.compile):
            result = admin.build_bundle(self.rows, self.storage, self.config, '2026-09-04', output=self.root / 'review', draft=True)
            self.assertFalse(Path(self.config['admin_output']).exists())
            final = admin.build_bundle(self.rows, self.storage, self.config, '2026-09-04', approved=True, review=result['review'])
        reader = PdfReader(final['pdf'])
        self.assertEqual(len(reader.pages), 3)
        self.assertEqual(float(reader.pages[1].mediabox.width), 320)
        self.assertEqual(self.source.read_bytes(), original)
        manifest = core.read_tsv(final['manifest'])
        entry = next(r for r in manifest if r[0] == 'entry')
        self.assertEqual(entry[9:12], ['2', '2', '3'])

    def test_changed_source_invalidates_approval(self):
        with patch.object(admin, 'compile_tex', self.compile):
            draft = admin.build_bundle(self.rows, self.storage, self.config, '2026-09-04', output=self.root / 'review', draft=True)
            self.source.write_bytes(pdf(2))
            with self.assertRaises(ValueError):
                admin.build_bundle(self.rows, self.storage, self.config, '2026-09-04', approved=True, review=draft['review'])

    def test_changed_mtime_invalidates_approval(self):
        with patch.object(admin, 'compile_tex', self.compile):
            draft = admin.build_bundle(self.rows, self.storage, self.config, '2026-09-04', output=self.root / 'review', draft=True)
            stat = self.source.stat()
            os.utime(self.source, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1000000000))
            with self.assertRaises(ValueError):
                admin.build_bundle(self.rows, self.storage, self.config, '2026-09-04', approved=True, review=draft['review'])

    def test_skill_alias_duplicate_is_rejected(self):
        with self.assertRaises(ValueError):
            skills.install(['agents', 'codex'], home=self.root)
        self.assertFalse((self.root / '.agents').exists())

    def test_skill_preflight_preserves_conflicting_files(self):
        existing = self.root / '.claude/skills/wr-wr'
        existing.parent.mkdir(parents=True)
        existing.write_text('existing')
        with self.assertRaises(ValueError):
            skills.install(['agents', 'claude'], home=self.root)
        self.assertFalse((self.root / '.agents').exists())
        self.assertEqual(existing.read_text(), 'existing')

    def test_skill_permission_failure_restores_backup(self):
        existing = self.root / '.agents/skills/wr-wr'
        existing.parent.mkdir(parents=True)
        existing.write_text('existing')
        with patch.object(Path, 'symlink_to', side_effect=PermissionError('denied')), self.assertRaises(ValueError):
            skills.install(['agents'], replace=True, home=self.root)
        self.assertEqual(existing.read_text(), 'existing')
        self.assertFalse(existing.with_name('wr-wr.backup').exists())

    def test_draft_cannot_use_final_directory(self):
        with self.assertRaises(ValueError):
            admin.build_bundle(self.rows, self.storage, self.config, '2026-09-04', output=Path(self.config['admin_output']) / 'draft', draft=True)

    def test_unknown_history_forces_review(self):
        self.rows.append(['history', '2026-08-W4', 'a', 'unknown', 'not available'])
        with self.assertRaises(ValueError):
            admin.build_bundle(self.rows, self.storage, self.config, '2026-09-04')

    def test_overlength_forces_review(self):
        self.source.write_bytes(pdf(3))
        with self.assertRaises(ValueError):
            admin.build_bundle(self.rows, self.storage, self.config, '2026-09-04')

    def test_cover_overflow_does_not_replace_final(self):
        destination = Path(self.config['admin_output']) / '2026-09-W1.pdf'
        destination.parent.mkdir()
        destination.write_bytes(b'old')
        with patch.object(admin, 'compile_tex', return_value=pdf(2)), self.assertRaises(ValueError):
            admin.build_bundle(self.rows, self.storage, self.config, '2026-09-04')
        self.assertEqual(destination.read_bytes(), b'old')

    def test_manifest_destination_conflict_preserves_pdf(self):
        destination = Path(self.config['admin_output']) / '2026-09-W1.pdf'
        destination.parent.mkdir()
        destination.write_bytes(b'old')
        record = Path(self.config['admin_data']) / 'manifests/2026-09-W1.manifest.tsv'
        record.mkdir(parents=True)
        with patch.object(admin, 'compile_tex', self.compile), self.assertRaises(ValueError):
            admin.build_bundle(self.rows, self.storage, self.config, '2026-09-04')
        self.assertEqual(destination.read_bytes(), b'old')

    def test_history_write_failure_does_not_fall_back(self):
        Path(self.config['admin_data']).write_text('not a directory')
        with patch.object(admin, 'compile_tex', self.compile), self.assertRaises(OSError):
            admin.build_bundle(self.rows, self.storage, self.config, '2026-09-04')
        self.assertFalse((Path(self.config['admin_output']) / '2026-09-W1.pdf').exists())

    def test_verified_history_and_tampered_history(self):
        with patch.object(admin, 'compile_tex', self.compile):
            result = admin.build_bundle(self.rows, self.storage, self.config, '2026-09-04')
        members = [{'id': 'a'}]
        history, issues = admin.history_rows(self.config, members, '2026-09-18')
        self.assertEqual(history[0][3], 'included')
        self.assertEqual(history[1][3], 'unknown')
        self.assertFalse(issues)
        Path(result['pdf']).write_bytes(pdf(3))
        history, issues = admin.history_rows(self.config, members, '2026-09-18')
        self.assertEqual(history[0][3], 'unknown')
        self.assertTrue(issues)

    def test_manager_round_trip_and_no_auto_selection(self):
        manager = {'schema': 1, 'storage_root': str(self.storage), 'timezone': 'Asia/Seoul',
                   'members': [{'id': 'a', 'display_name': '가', 'order': 1, 'required': True, 'search_roots': ['.']}]}
        admin.save_manager(manager, self.config)
        self.assertEqual(admin.load_manager(self.config), manager)
        self.assertEqual(admin.discover(manager)['a'], [self.source])
        plan = admin.make_plan(manager, {}, self.config, '2026-09-04')
        self.assertEqual(next(r for r in plan if r[0] == 'entry')[5], 'missing')
        self.assertTrue(any(r[0] == 'issue' and r[2] == 'first-run' for r in plan))

    def test_slack_preview_and_dedup_no_network(self):
        module = notifications()
        rows = [['schema', 'admin-wr-plan/v1'], ['entry', '1', 'a', '가', 'required', 'missing', '-', 'missing-report'],
                ['issue', 'error', 'missing-report', 'a', 'Missing']]
        with patch.object(admin, 'compile_tex', self.compile):
            result = admin.build_bundle(rows, self.storage, self.config, '2026-09-04', output=self.root / 'review', draft=True)
        payload, fingerprint = module.notice(Path(result['manifest']))
        directory = self.root / 'slack'
        directory.mkdir()
        (directory / 'slack-webhook.url').write_text('https://hooks.slack.com/services/test/test/test')
        with patch.object(module, 'post') as transport:
            module.send(directory, payload, fingerprint)
            module.send(directory, payload, fingerprint)
            self.assertEqual(transport.call_count, 1)


if __name__ == '__main__':
    unittest.main()
