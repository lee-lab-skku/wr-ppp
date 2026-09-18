#!/usr/bin/env python3
"""main.tex -> editor state JSON.

Inline text is kept as LaTeX verbatim; only the *structure* is converted
(pppbox -> boxes, \\ReportSubsection -> subsections, prose/lists/tables -> blocks).
The editor renders that LaTeX subset directly, so nothing has to be
translated twice and the round trip stays lossless.

Usage: tex_to_state.py <main.tex> [out.json] [--week-start YYYY-MM-DD]
"""
import json
import re
import sys

BOXES = ('progress', 'problems', 'plans')


def to_md(s):
    """LaTeX -> the editor's text. Only \\textbf becomes markdown (it round-trips)."""
    s = re.sub(r'\\textbf\{((?:[^{}]|\{[^{}]*\})*)\}', r'**\1**', s.strip())
    return re.sub(r'\s+', ' ', s).strip()


def items_of(body):
    """The \\item entries of one itemize/enumerate body."""
    body = re.sub(r'\\end\{(itemize|enumerate)\}.*$', '', body, flags=re.S)
    return [to_md(p) for p in re.split(r'\\item\s', body)[1:] if p.strip()]


def brace_split(chunk):
    """Split '<heading>}<rest>' at the brace that closes the heading."""
    depth, i = 1, 0
    while i < len(chunk) and depth:
        if chunk[i] == '{':
            depth += 1
        elif chunk[i] == '}':
            depth -= 1
        i += 1
    return chunk[:i - 1], chunk[i:]


def command_args(text, start, count):
    """Return balanced braced arguments and the first character after them."""
    args, i = [], start
    for _ in range(count):
        while i < len(text) and text[i].isspace():
            i += 1
        if i >= len(text) or text[i] != '{':
            return None, start
        depth, begin = 1, i + 1
        i += 1
        while i < len(text) and depth:
            if text[i] == '{' and (i == 0 or text[i - 1] != '\\'):
                depth += 1
            elif text[i] == '}' and (i == 0 or text[i - 1] != '\\'):
                depth -= 1
            i += 1
        if depth:
            return None, start
        args.append(text[begin:i - 1])
    return args, i


def table_md(body, caption):
    """Convert a ReportTable body to the editor's pipe-table notation."""
    body = re.sub(r'\\(?:top|mid|bottom)rule', '', body)
    rows = []
    for row in re.split(r'(?<!\\)\\\\', body):
        cells = [to_md(c) for c in re.split(r'(?<!\\)&', row)]
        if any(cells):
            rows.append(cells)
    if not rows:
        return ''
    width = max(len(row) for row in rows)
    rows = [row + [''] * (width - len(row)) for row in rows]
    lines = ['| ' + ' | '.join(row) + ' |' for row in rows]
    lines.insert(1, '| ' + ' | '.join('---' for _ in range(width)) + ' |')
    if caption.strip():
        lines.append(': ' + to_md(caption))
    return '\n'.join(lines)


def content_blocks(body):
    """Yield prose, list and ReportTable blocks in source order."""
    out, pos = [], 0
    token = re.compile(r'\\begin\{(itemize|enumerate)\}|\\ReportTable\b')

    def add_prose(text):
        text = re.sub(r'\\vspace\{[^}]*\}', '', text)
        out.extend(to_md(p) for p in re.split(r'\n\s*\n', text) if p.strip())

    while True:
        match = token.search(body, pos)
        if not match:
            add_prose(body[pos:])
            break
        add_prose(body[pos:match.start()])
        if match.group(1):
            kind = match.group(1)
            end_match = re.search(r'\\end\{' + kind + r'\}', body[match.end():])
            if not end_match:
                add_prose(body[match.start():])
                break
            end = match.end() + end_match.end()
            items = items_of(body[match.end():end])
            mark = (lambda i, item: f'{i + 1}. {item}') if kind == 'enumerate' else (lambda _i, item: '- ' + item)
            if items:
                out.append('\n'.join(mark(i, item) for i, item in enumerate(items)))
            pos = end
        else:
            args, end = command_args(body, match.end(), 4)
            if not args:
                add_prose(body[match.start():])
                break
            table = table_md(args[1], args[2])
            if table:
                out.append(table)
            pos = end
    return out


def convert(tex, week_start=''):
    flow, n = [], {'s': 0, 'b': 0, 'f': 0}

    for name, body in re.findall(r'\\begin\{pppbox\}\{(\w+)\}(.*?)\\end\{pppbox\}', tex, re.S):
        box = name.lower()
        chunks = re.split(r'\\ReportSubsection\{', body)
        if len(chunks) == 1:
            for text in content_blocks(body):
                n['b'] += 1
                flow.append({"type": "block", "boxId": box, "id": f"b{n['b']}", "text": text})
        else:
            for chunk in chunks[1:]:
                heading, rest = brace_split(chunk)
                n['s'] += 1
                sid = f"s{n['s']}"
                flow.append({"type": "subsection", "boxId": box, "id": sid, "heading": to_md(heading)})
                for text in content_blocks(rest):
                    n['b'] += 1
                    flow.append({"type": "block", "subId": sid, "id": f"b{n['b']}", "text": text})

    figs = []
    for path, cap, _label, height in re.findall(
            r'\\ReportFigure\s*\{([^}]*)\}\s*\{(.*?)\}\s*\{([^}]*)\}\s*\{([^}]*)\}', tex, re.S):
        n['f'] += 1
        figs.append({"type": "figure", "id": f"f{n['f']}",
                     "heightMm": int(re.sub(r'\D', '', height) or 40),
                     "items": [{"path": path.strip(), "caption": to_md(cap)}]})
    for p1, c1, _l1, p2, c2, _l2 in re.findall(
            r'\\ReportFigurePair\s*\{([^}]*)\}\s*\{(.*?)\}\s*\{([^}]*)\}\s*\{([^}]*)\}\s*\{(.*?)\}\s*\{([^}]*)\}',
            tex, re.S):
        n['f'] += 1
        figs.append({"type": "figure", "id": f"f{n['f']}", "heightMm": 35,
                     "items": [{"path": p1.strip(), "caption": to_md(c1)},
                               {"path": p2.strip(), "caption": to_md(c2)}]})

    # figures sit between the boxes; drop them after the Progress run, as the template does
    prog = [i for i, e in enumerate(flow)
            if e.get('boxId') == 'progress'
            or (e['type'] == 'block' and any(f['type'] == 'subsection' and f['id'] == e.get('subId')
                                             and f['boxId'] == 'progress' for f in flow))]
    if prog and figs:
        flow = flow[:prog[-1] + 1] + figs + flow[prog[-1] + 1:]
    else:
        flow += figs

    hdr = re.search(r'\\ReportHeader\s*\{(.*?)\}\s*\{(.*?)\}\s*\{(.*?)\}', tex, re.S)
    ab = re.search(r'\\begin\{reportabstract\}(.*?)\\end\{reportabstract\}', tex, re.S)
    return {"title": to_md(hdr.group(1)) if hdr else "",
            "author": hdr.group(2).strip() if hdr else "",
            "project": hdr.group(3).strip() if hdr else "",
            "weekStart": week_start,
            "abstract": to_md(ab.group(1)) if ab else "",
            "flow": flow}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    week_start = ''
    if '--week-start' in sys.argv:
        at = sys.argv.index('--week-start')
        if at + 1 >= len(sys.argv):
            sys.exit('--week-start requires YYYY-MM-DD')
        week_start = sys.argv[at + 1]
    state = convert(open(sys.argv[1], encoding='utf-8').read(), week_start)
    out = json.dumps(state, ensure_ascii=False, indent=1)
    if len(sys.argv) > 2:
        open(sys.argv[2], 'w', encoding='utf-8').write(out)
        print(f"{sys.argv[2]}: {sum(1 for e in state['flow'] if e['type']=='subsection')} subsections, "
              f"{sum(1 for e in state['flow'] if e['type']=='block')} blocks, "
              f"{sum(1 for e in state['flow'] if e['type']=='figure')} figures")
    else:
        print(out)
