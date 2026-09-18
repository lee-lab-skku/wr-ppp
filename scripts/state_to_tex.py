#!/usr/bin/env python3
"""editor state JSON -> main.tex (weekly-report.sty).

Transcription only, and deliberately so: the wording was already settled in
the editor, so re-writing it through a model would only introduce drift.
Judgement calls - build diagnosis, page-layout pitfalls, content review -
stay with the wr-wr skill.

Usage: state_to_tex.py <state.json> [out.tex]
"""
import json
import re
import sys

BOX_LABEL = {'progress': 'Progress', 'problems': 'Problems', 'plans': 'Plans'}
BOX_ORDER = ('progress', 'problems', 'plans')


def md_inline(s):
    """The editor's only markdown shortcut is **bold**; everything else is already LaTeX."""
    return re.sub(r'\*\*((?:[^*]|\*(?!\*))+)\*\*', r'\\textbf{\1}', s or '')


def block_tex(text):
    lines = (text or '').split('\n')
    out, i = [], 0
    while i < len(lines):
        if re.match(r'^\s*[-*]\s+', lines[i]):
            out.append('\\begin{itemize}')
            while i < len(lines) and re.match(r'^\s*[-*]\s+', lines[i]):
                out.append('    \\item ' + md_inline(re.sub(r'^\s*[-*]\s+', '', lines[i])))
                i += 1
            out.append('\\end{itemize}')
            continue
        if re.match(r'^\s*\d+\.\s+', lines[i]):
            out.append('\\begin{enumerate}')
            while i < len(lines) and re.match(r'^\s*\d+\.\s+', lines[i]):
                out.append('    \\item ' + md_inline(re.sub(r'^\s*\d+\.\s+', '', lines[i])))
                i += 1
            out.append('\\end{enumerate}')
            continue
        if lines[i].strip().startswith('|'):
            rows, i = _table_rows(lines, i)
            caption = ''
            if i < len(lines) and lines[i].strip().startswith(': '):
                caption = md_inline(lines[i].strip()[2:])
                i += 1
            out += _table_tex(rows, caption, len(out))
            continue
        if lines[i].strip():
            para = []
            while i < len(lines) and lines[i].strip() and not re.match(r'^\s*([-*]|\d+\.)\s+|^\s*\|', lines[i]):
                para.append(lines[i])
                i += 1
            out.append(md_inline(' '.join(para)))
        else:
            i += 1
    return '\n'.join(out)


def _table_rows(lines, i):
    rows = []
    while i < len(lines) and lines[i].strip().startswith('|'):
        rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
        i += 1
    return rows, i


def _table_tex(rows, caption, seq):
    if not rows:
        return []
    header, body = rows[0], rows[1:]
    if len(rows) > 1 and set(''.join(rows[1])) <= set('-: '):
        body = rows[2:]
    cols = 'L' + ' C' * (len(header) - 1)
    inner = ['        \\toprule',
             '        ' + ' & '.join(md_inline(c) for c in header) + r' \\',
             '        \\midrule']
    inner += ['        ' + ' & '.join(md_inline(c) for c in r) + r' \\' for r in body]
    inner.append('        \\bottomrule')
    return ['\\ReportTable', '    {' + cols + '}', '    {', '\n'.join(inner), '    }',
            '    {' + caption + '}', '    {tab:t' + str(seq) + '}']


def render(state):
    body, cur = [], None
    for idx, e in enumerate(state['flow']):
        box = e.get('boxId') if e['type'] in ('subsection', 'block') else None
        if box and box != cur:
            if cur:
                body += ['\\end{pppbox}', '', '\\vspace{2mm}', '']
            body += ['\\begin{pppbox}{' + BOX_LABEL[box] + '}', '']
            cur = box
        if e['type'] == 'subsection':
            body += ['\\ReportSubsection{' + md_inline(e['heading']) + '}', '']
        elif e['type'] == 'block':
            body += [block_tex(e['text']), '']
        elif e['type'] == 'pagebreak':
            body += ['\\clearpage', '']
        elif e['type'] == 'figure':
            if cur:
                body += ['\\end{pppbox}', '', '\\vspace{2mm}', '']
                cur = None
            items = e.get('items', [])
            if len(items) >= 2:                       # \ReportFigurePair: height is fixed at 35mm
                a, b = items[0], items[1]
                body += ['\\ReportFigurePair',
                         '    {' + a['path'] + '}', '    {' + md_inline(a.get('caption', '')) + '}',
                         '    {fig:a' + str(idx) + '}',
                         '    {' + b['path'] + '}', '    {' + md_inline(b.get('caption', '')) + '}',
                         '    {fig:b' + str(idx) + '}', '']
            elif items:
                it = items[0]
                body += ['\\ReportFigure', '    {' + it['path'] + '}',
                         '    {' + md_inline(it.get('caption', '')) + '}',
                         '    {fig:' + str(idx) + '}',
                         '    {' + str(e.get('heightMm', 40)) + 'mm}', '']
    if cur:
        body += ['\\end{pppbox}', '']

    abstract = ('\\begin{reportabstract}\n\n' + md_inline(state.get('abstract', '')) +
                '\n\n\\end{reportabstract}\n\n\\vspace{3mm}\n\n') if state.get('abstract', '').strip() else ''
    return ('\\documentclass[10pt,a4paper]{article}\n'
            '\\usepackage{weekly-report}\n\\usepackage{siunitx}\n'
            '\\sisetup{group-separator={,},group-minimum-digits=4}\n\n'
            '\\begin{document}\n\n'
            '\\ReportHeader\n    {' + md_inline(state['title']) + '}\n'
            '    {' + state.get('author', '') + '}\n    {' + state.get('project', '') + '}\n\n'
            + abstract + '\n'.join(body) + '\n\\vfill\n\n\\end{document}\n')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    tex = render(json.load(open(sys.argv[1], encoding='utf-8')))
    if len(sys.argv) > 2:
        open(sys.argv[2], 'w', encoding='utf-8').write(tex)
        print(f'{sys.argv[2]}: {len(tex)} chars')
    else:
        print(tex)
