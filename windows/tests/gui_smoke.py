"""Creates the native UI briefly, without sending messages or opening PDFs."""
import os
from pathlib import Path
import sys
import tempfile
import tkinter as tk

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wr.gui import App

with tempfile.TemporaryDirectory() as temp:
    os.environ['WR_CONFIG'] = str(Path(temp) / 'config.json')
    root = tk.Tk()
    root.withdraw()
    app = App(root)
    root.update()
    assert len(app.texts) == 5
    assert len(app.settings) == 4
    app.fields['title'].set('한글 보고서 & test')
    app.form_file = Path(temp) / 'report.wr.json'
    app.texts['Progress'].insert('1.0', '## 변환 확인\n\n- **완료**')
    app.preview_latex()
    assert r'\bfseries 변환 확인' in app.texts['LaTeX'].get('1.0', 'end-1c')
    assert r'\item \textbf{완료}' in app.texts['LaTeX'].get('1.0', 'end-1c')
    assert app.editor_tabs.index(app.editor_tabs.select()) == 4
    source = app.save_report()
    assert source.is_file()
    assert r'한글 보고서 \& test' in source.read_text(encoding='utf-8')
    assert app.form_file.is_file()
    original = Path(temp) / 'existing.tex'
    original.write_text('original LaTeX', encoding='utf-8')
    app.source, app.form_file = original, None
    app.texts['LaTeX'].delete('1.0', 'end')
    try:
        app.save_report()
        raise AssertionError('empty original source was overwritten')
    except ValueError as error:
        assert '빈 내용' in str(error)
    assert original.read_text(encoding='utf-8') == 'original LaTeX'
    root.destroy()
    print('Native Tk UI creation, form editing and save: OK')
