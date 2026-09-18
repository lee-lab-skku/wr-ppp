#!/usr/bin/env python3
"""Fail if the editor's page model has drifted from weekly-report.sty.

The preview is only trustworthy because it hardcodes the same numbers the
class file uses. Those numbers live in another repo (lee-lab-skku/wr-ppp),
so this check is what stops the two from quietly diverging.

Usage: verify_geometry.py [path/to/weekly-report.sty] [path/to/editor.html]
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_STY = Path.home() / 'lee-lab-skku' / 'wr-ppp' / 'weekly-report.sty'
DEFAULT_HTML = HERE.parent / 'assets' / 'editor.html'


def check(sty_path, html_path):
    sty = Path(sty_path).read_text(encoding='utf-8')
    html = Path(html_path).read_text(encoding='utf-8')
    fails = []

    def want(label, pattern, text, expected):
        m = re.search(pattern, text)
        got = m.group(1) if m else None
        if got != expected:
            fails.append(f'{label}: expected {expected!r}, found {got!r}')

    # --- what the class file declares -------------------------------------
    want('sty geometry top', r'top=(\d+)mm', sty, '15')
    want('sty geometry left', r'left=(\d+)mm', sty, '18')
    want('sty pppbox arc', r'pppbox.*?arc=([\d.]+)mm', sty.replace('\n', ' '), '1.5')
    want('sty pppbox boxrule', r'pppbox.*?boxrule=([\d.]+)pt', sty.replace('\n', ' '), '0.8')
    want('sty pppbox left pad', r'pppbox.*?left=(\d+)mm', sty.replace('\n', ' '), '3')
    want('sty figure pair height', r'ReportFigurePair.*?\{(\d+)mm\}', sty.replace('\n', ' '), '35')

    # --- what the editor assumes ------------------------------------------
    if not re.search(r'--content-w:\d+px', html):
        fails.append('editor: --content-w (the zoom basis) is missing')
    want('editor page width', r'width:calc\(var\(--mm\) \* (\d+)\)', html, '210')
    want('editor page height', r'min-height:calc\(var\(--mm\) \* (\d+)\)', html, '297')
    want('editor side margin', r'padding:calc\(var\(--mm\) \* \d+\) calc\(var\(--mm\) \* (\d+)\)', html, '18')
    want('editor top margin', r'padding:calc\(var\(--mm\) \* (\d+)\)', html, '15')
    want('editor body font', r'font-size:calc\(var\(--pt\) \* (\d+)\)', html, '10')
    want('editor box rule', r'border-left:calc\(var\(--pt\)\*([\d.]+)\) solid #26466e', html, '.8')
    want('editor box arc', r'border-radius:calc\(var\(--mm\)\*([\d.]+)\)', html, '1.5')
    want('editor pair height', r'var pair = e\.items\.length > 1;[\s\S]{0,200}?\? (\d+) :', html, '35')
    want('editor mm basis', r'--mm:calc\(var\(--content-w\) / (\d+)\)', html, '174')   # 210 - 2*18

    return fails


if __name__ == '__main__':
    sty = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_STY
    html = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_HTML
    if not Path(sty).exists():
        print(f'skip: {sty} not found (wr-ppp not installed here)')
        sys.exit(0)
    problems = check(sty, html)
    if problems:
        print('GEOMETRY DRIFT:')
        for p in problems:
            print('  -', p)
        sys.exit(1)
    print('geometry ok: editor matches weekly-report.sty')
