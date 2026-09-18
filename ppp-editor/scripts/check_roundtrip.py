#!/usr/bin/env python3
"""Refuse to edit a report the editor cannot hold without losing something.

tex -> state -> tex, then compare against the original. Anything the importer
does not understand simply disappears from the state, and would disappear from
main.tex the moment the edited artifact is written back. This is the gate that
turns that silent loss into a refusal.

Usage: check_roundtrip.py <main.tex> [--min 0.99]
Exit:  0 = safe to edit, 1 = would lose content
"""
import difflib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

# constructs the state model has no room for; each one is content that would vanish
UNSUPPORTED = [
    (r'\\newcommand\{', 'a \\newcommand definition'),
    (r'\\renewcommand\{', 'a \\renewcommand (e.g. an overridden \\ReportWeekLabel)'),
    (r'\\begin\{figure\}', 'a hand-written figure environment (use \\ReportFigure/\\ReportFigurePair)'),
    (r'\\begin\{minipage\}', 'a minipage'),
    (r'\\clearpage', 'a \\clearpage outside the flow (an appendix or forced break)'),
    (r'\\begin\{tabular', 'a raw tabular (use \\ReportTable)'),
    (r'\\section\{|\\subsection\{', 'a \\section/\\subsection'),
]


def normalise(text):
    return re.sub(r'\s+', ' ', text).strip()


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    floor = 0.99
    for a in sys.argv[2:]:
        if a.startswith('--min'):
            floor = float(a.split('=', 1)[1] if '=' in a else sys.argv[sys.argv.index(a) + 1])

    original = src.read_text(encoding='utf-8')
    preamble, _, body = original.partition(r'\begin{document}')

    found = [why for pat, why in UNSUPPORTED if re.search(pat, body)]
    # the exporter emits a fixed preamble, so anything declared in this one is lost too
    for pat, why in ((r'\\newcommand\{', 'a \\newcommand in the preamble'),
                     (r'\\renewcommand\{', 'a \\renewcommand in the preamble '
                                           '(e.g. an overridden \\ReportWeekLabel)')):
        if re.search(pat, preamble):
            found.append(why)
    for pkg in re.findall(r'\\usepackage\{([^}]*)\}', preamble):
        if pkg not in ('weekly-report', 'siunitx'):
            found.append(f'\\usepackage{{{pkg}}} (the exporter only emits weekly-report + siunitx)')

    with tempfile.TemporaryDirectory() as tmp:
        state, back = Path(tmp) / 'state.json', Path(tmp) / 'back.tex'
        for cmd in ([sys.executable, HERE / 'tex_to_state.py', src, state],
                    [sys.executable, HERE / 'state_to_tex.py', state, back]):
            r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
            if r.returncode:
                print('FAIL: conversion errored\n' + r.stderr)
                return 1
        ratio = difflib.SequenceMatcher(None, normalise(body),
                                        normalise(back.read_text(encoding='utf-8')
                                                  .split(r'\begin{document}', 1)[-1])).ratio()

    print(f'round-trip fidelity: {ratio*100:.1f}%  (floor {floor*100:.0f}%)')
    for why in found:
        print('  unsupported:', why)
    if ratio >= floor and not found:
        print('safe to edit')
        return 0
    print('\nNOT safe to edit: writing the artifact back would drop the content above.')
    print('Either keep this report in plain LaTeX, or lift the unsupported parts out first.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
