#!/usr/bin/env python3
"""Put a state JSON into the editor template, ready to publish as an Artifact.

Usage: build_artifact.py <state.json> [out.html]
"""
import json
import sys
from pathlib import Path

MARK = '<script id="state-json" type="application/json">'


def build(state, template_html):
    start = template_html.index(MARK) + len(MARK)
    end = template_html.index('</script>', start)
    body = json.dumps(state, ensure_ascii=False, indent=1)
    return template_html[:start] + '\n' + body + '\n' + template_html[end:]


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    tpl = Path(__file__).resolve().parent.parent / 'assets' / 'editor.html'
    html = build(json.load(open(sys.argv[1], encoding='utf-8')), tpl.read_text(encoding='utf-8'))
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(html, encoding='utf-8')
        print(f'{sys.argv[2]}: {len(html)} bytes')
    else:
        sys.stdout.write(html)
