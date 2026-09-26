"""Lossless source-backed editing, without executing or expanding TeX.

The source is an immutable tape: editable spans and protected spans cover every
character exactly once. Export replaces only changed fields. Unknown syntax is
kept on that tape, never silently interpreted as editable prose.
"""
from copy import deepcopy
import difflib
import re

from .tex_to_state import to_md, content_blocks, table_md

COMMAND = re.compile(r'\\(?:[A-Za-z@]+\*?|[^\r\n])')
SAFE_INLINE = set(('textbf textit emph texttt textrm textsf textsc underline '
                   'cref Cref crefrange Crefrange cpageref Cpageref label '
                   'SI si num qty unit numrange qtyrange SIrange ce '
                   'frac dfrac tfrac sqrt mathcal mathrm mathbf mathit mathsf '
                   'left right sum prod int lambda alpha beta gamma delta '
                   'theta sigma mu pi rho phi omega Delta Sigma Omega '
                   'le leq ge geq neq approx times cdot pm infty '
                   'uparrow downarrow lVert rVert lvert rvert percent '
                   'metre meter second micro milli nano degreeCelsius '
                   'per kilogram gram kelvin hertz mol litre liter '
                   'mathrm operatorname vec hat bar dot ddot overline '
                   'quad qquad hspace ref eqref').split())


def command_at(text, pos):
    match = COMMAND.match(text, pos)
    return (match.group()[1:], match.end()) if match else ('', pos + 1)


def trivia_end(text, pos):
    while pos < len(text):
        if text[pos].isspace():
            pos += 1
        elif text[pos] == '%':
            end = text.find('\n', pos)
            pos = len(text) if end < 0 else end + 1
        else:
            break
    return pos


def argument(text, pos):
    """Read one balanced braced argument, respecting comments and escapes."""
    pos = trivia_end(text, pos)
    if pos >= len(text) or text[pos] != '{':
        raise ValueError('Expected a braced argument')
    start, depth, pos = pos + 1, 1, pos + 1
    while pos < len(text):
        if text[pos] == '%':
            end = text.find('\n', pos)
            pos = len(text) if end < 0 else end + 1
            continue
        if text[pos] == '\\':
            _, pos = command_at(text, pos)
            continue
        if text[pos] == '{':
            depth += 1
        elif text[pos] == '}':
            depth -= 1
            if not depth:
                return (start, pos), pos + 1
        pos += 1
    raise ValueError('Unclosed argument')


def arguments(text, pos, count):
    spans = []
    for _ in range(count):
        span, pos = argument(text, pos)
        spans.append(span)
    return spans, pos


def environment(text, start):
    """Return opening/body/closing boundaries; verbatim bodies are opaque."""
    _, at = command_at(text, start)
    span, opening = argument(text, at)
    name = text[slice(*span)]
    if name in ('verbatim', 'verbatim*', 'lstlisting', 'minted'):
        match = re.search(r'\\end\{' + re.escape(name) + r'\}', text[opening:])
        if not match:
            raise ValueError('Unclosed verbatim environment')
        return name, opening, opening + match.start(), opening + match.end()
    stack, at = [name], opening
    while at < len(text):
        if text[at] == '%':
            at = trivia_end(text, at)
            continue
        if text[at] != '\\':
            at += 1
            continue
        cmd, end = command_at(text, at)
        if cmd == 'verb':
            if end < len(text):
                delim = text[end]
                finish = text.find(delim, end + 1)
                if finish < 0:
                    raise ValueError('Unclosed verbatim command')
                at = finish + 1
                continue
        if cmd in ('begin', 'end'):
            arg, finish = argument(text, end)
            env = text[slice(*arg)]
            if cmd == 'begin':
                if env in ('verbatim', 'verbatim*', 'lstlisting', 'minted'):
                    _, _, _, at = environment(text, at)
                    continue
                stack.append(env)
            else:
                if not stack or stack.pop() != env:
                    raise ValueError('Mismatched environment')
                if not stack:
                    return name, opening, at, finish
            at = finish
        else:
            at = end
    raise ValueError('Unclosed environment')


def safe_text(text):
    """Only expose syntax whose text editor conversion is unambiguous."""
    depth, at = 0, 0
    while at < len(text):
        char = text[at]
        if char == '%':
            return False
        if char == '\\':
            cmd, at = command_at(text, at)
            if cmd not in SAFE_INLINE and cmd not in ('%', '&', '_', '#', '$', '{', '}', ' ', ',', ';', '!', '[', ']', '(', ')', '\\'):
                return False
            continue
        depth += (char == '{') - (char == '}')
        if depth < 0:
            return False
        at += 1
    return depth == 0


def table_cells(body, offset):
    masked = re.sub(r'\\(?:top|mid|bottom)rule\b', lambda m: ' ' * len(m.group()), body)
    cells, row_start = [], 0
    for stop in list(re.finditer(r'(?<!\\)\\\\', masked)) + [None]:
        row_end = stop.start() if stop else len(masked)
        row = masked[row_start:row_end]
        if row.strip():
            spans, cell_start = [], row_start
            for split in list(re.finditer(r'(?<!\\)&', row)) + [None]:
                cell_end = row_start + split.start() if split else row_end
                part = masked[cell_start:cell_end]
                left = cell_start + len(part) - len(part.lstrip())
                right = cell_end - len(part) + len(part.rstrip())
                spans.append((offset + left, offset + max(left, right)))
                cell_start = cell_end + 1
            cells.append(spans)
        row_start = stop.end() if stop else len(masked)
    return cells


def reference_tokens(source):
    """Collect literal labels/references, excluding comments and verbatim text."""
    labels, references, at = [], set(), 0
    while at < len(source):
        if source[at] == '%':
            at = trivia_end(source, at)
            continue
        if source[at] != '\\':
            at += 1
            continue
        command, end = command_at(source, at)
        command = command.rstrip('*')
        try:
            if command == 'begin':
                span, _ = argument(source, end)
                if source[slice(*span)] in ('verbatim', 'verbatim*', 'lstlisting', 'minted'):
                    at = environment(source, at)[3]
                    continue
            if command == 'verb' and end < len(source):
                finish = source.find(source[end], end + 1)
                at = len(source) if finish < 0 else finish + 1
                continue
            if command in ('label', 'ref', 'eqref', 'cref', 'Cref', 'crefrange', 'Crefrange', 'cpageref', 'Cpageref'):
                spans, end = arguments(source, end, 2 if command.lower() == 'crefrange' else 1)
                for span in spans:
                    value = source[slice(*span)]
                    if command == 'label': labels.append(value)
                    else: references.update(v.strip() for v in value.split(','))
        except ValueError:
            pass
        at = end
    return labels, references


def has_comment(text):
    at = 0
    while at < len(text):
        if text[at] == '%':
            return True
        if text[at] == '\\':
            _, at = command_at(text, at)
        else:
            at += 1
    return False


def parse(source, week_start=''):
    """Return editor state plus a private span index covering the original."""
    state = {'formatVersion': 2, 'title': '', 'author': '', 'project': '',
             'abstract': '', 'weekStart': week_start, 'flow': [],
             'preservation': {'version': 1, 'source': source},
             'capabilities': {'sourcePreservation': True}}
    records = {}

    def add(start, end, entry, fields=None):
        if start == end:
            return
        entry = dict(entry, id='src' + str(start))
        if entry['type'] != 'opaque' and has_comment(source[start:end]):
            entry['structureLocked'] = True
        state['flow'].append(entry)
        records[entry['id']] = {'start': start, 'end': end, 'base': deepcopy(entry), 'fields': fields or {}}

    def raw(start, end, owner=None, hidden=False, kind='raw'):
        if start == end:
            return
        text = source[start:end]
        add(start, end, {'type': 'opaque', 'text': text, 'hidden': hidden or not text.strip(),
                         'protected': bool(text.strip()), 'role': kind,
                         'reason': '원문 보존 · 읽기 전용', **(owner or {})})

    def scan(start, end, box=None):
        pos, owner = start, ({'boxId': box} if box else {})
        while pos < end:
            begin = pos
            if source[pos].isspace() or source[pos] == '%':
                pos = min(trivia_end(source, pos), end)
                raw(begin, pos, owner, hidden=True)
                continue
            if source[pos] == '\\':
                cmd, after = command_at(source, pos)
                try:
                    if cmd == 'ReportHeader' and not box:
                        spans, pos = arguments(source, after, 3)
                        if any(not safe_text(source[slice(*s)]) for s in spans):
                            raise ValueError('Protected header')
                        for key, span in zip(('title', 'author', 'project'), spans):
                            state[key] = to_md(source[slice(*span)])
                        add(begin, pos, {'type': 'opaque', 'hidden': True, 'protected': True, 'role': 'header', 'text': source[begin:pos]}, dict(zip(('title', 'author', 'project'), spans)))
                        continue
                    if cmd == 'begin':
                        name, opening, closing, finish = environment(source, begin)
                        if finish > end:
                            raise ValueError('Crossing environment')
                        if name == 'pppbox' and not box:
                            label, body = argument(source, opening)
                            box_name = source[slice(*label)].lower()
                            if box_name not in ('progress', 'problems', 'plans'):
                                raise ValueError('Unknown box')
                            raw(begin, body, hidden=True, kind='box-open')
                            scan(body, closing, box_name)
                            raw(closing, finish, hidden=True, kind='box-close')
                        elif name == 'reportabstract' and not box and safe_text(source[opening:closing]):
                            state['abstract'] = to_md(source[opening:closing])
                            add(begin, finish, {'type': 'opaque', 'hidden': True, 'protected': True, 'role': 'abstract', 'text': source[begin:finish]}, {'abstract': (opening, closing)})
                        elif name in ('itemize', 'enumerate') and box:
                            body = source[opening:closing]
                            stripped = re.sub(r'\\item\b', '', body)
                            if (not safe_text(stripped) or '\\begin' in body or body[:body.find('\\item')].strip()
                                    or re.search(r'\\item\b(?:\s*\[|(?!\s))', body)):
                                raise ValueError('Complex list')
                            blocks = content_blocks(source[begin:finish])
                            if len(blocks) != 1:
                                raise ValueError('Complex list')
                            add(begin, finish, {'type': 'block', 'text': blocks[0], **owner}, {'text': (begin, finish)})
                        else:
                            raw(begin, finish, owner)
                        pos = finish
                        continue
                    if cmd == 'ReportSubsection' and box:
                        spans, pos = arguments(source, after, 1)
                        if not safe_text(source[slice(*spans[0])]):
                            raise ValueError('Complex heading')
                        add(begin, pos, {'type': 'subsection', 'heading': to_md(source[slice(*spans[0])]), 'boxId': box}, {'heading': spans[0]})
                        owner = {'subId': 'src' + str(begin)}
                        continue
                    if cmd in ('ReportFigure', 'ReportFigurePair') and not box:
                        spans, pos = arguments(source, after, 4 if cmd == 'ReportFigure' else 6)
                        values = [source[slice(*s)] for s in spans]
                        if not all(safe_text(v) for v in values):
                            raise ValueError('Complex figure')
                        height = 35 if cmd.endswith('Pair') else values[3]
                        if isinstance(height, str) and not re.fullmatch(r'\s*\d+(?:\.\d+)?mm\s*', height):
                            raise ValueError('Non-millimetre figure size')
                        items = [{'path': values[i], 'caption': to_md(values[i+1]), 'label': values[i+2], 'sourceItem': f'{begin}:{i}'} for i in range(0, 6 if cmd.endswith('Pair') else 3, 3)]
                        fields = {f'{i//3}.{key}': spans[i+j] for i in range(0, 6 if cmd.endswith('Pair') else 3, 3) for j, key in enumerate(('path', 'caption', 'label'))}
                        if cmd == 'ReportFigure':
                            fields['heightMm'] = spans[3]
                        add(begin, pos, {'type': 'figure', 'items': items, 'heightMm': float(str(height).replace('mm', ''))}, fields)
                        continue
                    if cmd == 'ReportTable' and box:
                        spans, pos = arguments(source, after, 4)
                        cols, body, caption, label = [source[slice(*s)] for s in spans]
                        cleaned = re.sub(r'\\(?:top|mid|bottom)rule\b', '', body)
                        if not re.fullmatch(r'\s*[LCRlcr](?:\s+[LCRlcr])*\s*', cols) or not safe_text(cleaned) or not safe_text(caption):
                            raise ValueError('Complex table')
                        text = table_md(body, caption)
                        cells = [r for r in re.split(r'(?<!\\)\\\\', cleaned) if r.strip()]
                        if any(len(re.split(r'(?<!\\)&', r)) != len(cols.split()) for r in cells) or any('|' in r for r in cells):
                            raise ValueError('Ambiguous table')
                        add(begin, pos, {'type': 'block', 'text': text, 'table': {'columns': cols, 'label': label}, **owner}, {'tableBody': spans[1], 'tableCaption': spans[2], 'tableCells': table_cells(body, spans[1][0])})
                        continue
                    if cmd == 'clearpage' and not box:
                        pos = after
                        add(begin, pos, {'type': 'pagebreak', **owner})
                        continue
                    if cmd in ('vspace', 'vfill'):
                        pos = arguments(source, after, 1)[1] if cmd == 'vspace' else after
                        raw(begin, pos, owner, hidden=True)
                        continue
                except ValueError:
                    # Consume a whole recognizable construct when possible; if its
                    # boundaries are unknowable, protect the rest of this container.
                    if cmd == 'begin':
                        try:
                            pos = environment(source, begin)[3]
                        except ValueError:
                            pos = end
                    elif pos <= begin:
                        pos = end
                    raw(begin, min(pos, end), owner)
                    continue
            # Paragraph boundaries are never whitespace-normalized in storage.
            match = re.search(r'\r?\n[ \t]*\r?\n|(?=\\(?:ReportSubsection|ReportTable|ReportFigure|begin|end)\b)', source[pos+1:end])
            pos = pos + 1 + match.start() if match else end
            text = source[begin:pos]
            trimmed = len(text) - len(text.rstrip())
            stop = pos - trimmed
            if box and safe_text(source[begin:stop]):
                add(begin, stop, {'type': 'block', 'text': to_md(source[begin:stop]), **owner}, {'text': (begin, stop)})
            else:
                raw(begin, stop, owner)
            raw(stop, pos, owner, hidden=True)

    # Recognize the document only at lexical top level; macro bodies are opaque.
    at, doc = 0, None
    while at < len(source):
        if source[at] == '%':
            at = trivia_end(source, at)
        elif source[at] == '{':
            try:
                _, at = argument(source, at)
            except ValueError:
                break
        elif source[at] == '\\':
            cmd, after = command_at(source, at)
            if cmd == 'begin':
                try:
                    name, opening, closing, end = environment(source, at)
                    if name == 'document':
                        doc = opening, closing, end
                        break
                    at = end
                except ValueError:
                    break
            else:
                at = after
        else:
            at += 1
    if doc:
        opening, closing, end = doc
        raw(0, opening, hidden=True, kind='preamble')
        scan(opening, closing)
        raw(closing, len(source), hidden=True, kind='epilogue')
    else:
        raw(0, len(source), kind='document')
    state['capabilities']['documentReadOnly'] = not bool(doc)
    state['capabilities']['lockedFields'] = [key for key in ('title', 'author', 'project', 'abstract') if sum(key in r['fields'] for r in records.values()) != 1]
    return state, records


def import_source(source, week_start=''):
    return parse(source, week_start)[0]


def preserve_spacing(old, new):
    """Keep untouched token runs and their original whitespace during text edits."""
    before = list(re.finditer(r'\S+', old))
    after = list(re.finditer(r'\S+', new))
    matcher = difflib.SequenceMatcher(None, [m.group() for m in before],
                                    [m.group() for m in after], autojunk=False)
    operations = matcher.get_opcodes()
    if all(op[0] == 'equal' for op in operations) or re.search(r'\n[ \t]*\n', new):
        return new
    edits = []
    for kind, a, b, c, d in operations:
        if kind == 'equal':
            continue
        start = before[a].start() if a < len(before) else len(old)
        end = before[b-1].end() if b > a else start
        value = new[after[c].start():after[d-1].end()] if d > c else ''
        if a == b:
            if start and not old[start-1].isspace(): value = ' ' + value
            if start < len(old) and not old[start].isspace(): value += ' '
        edits.append((start, end, value))
    for start, end, value in reversed(edits):
        old = old[:start] + value + old[end:]
    return old


def _semantic(entry):
    result = deepcopy(entry)
    for item in result.get('items', []):
        item.pop('prev', None)
        item.pop('dim', None)
        item.pop('editorId', None)
    return result


def export_source(state):
    """Export edits, refusing tampered protected spans or ambiguous operations."""
    from .state_to_tex import block_tex, md_inline
    preservation = state.get('preservation', {})
    if preservation.get('version') != 1:
        raise ValueError('Unsupported source preservation version')
    source = preservation['source']
    original, records = parse(source)
    flow = state['flow']
    ids = [e.get('id') for e in flow]
    if len(ids) != len(set(ids)) or None in ids:
        raise ValueError('Every source node needs a unique ID')
    for key in original['capabilities']['lockedFields']:
        if state.get(key, '') != original[key]:
            raise ValueError(f'{key} is read-only')
    old_protected = [e['id'] for e in original['flow'] if e.get('protected')]
    if [e['id'] for e in flow if e.get('protected')] != old_protected:
        raise ValueError('Protected source cannot be deleted or reordered')
    # A protected construct is a structural barrier. Moving across one could
    # change a macro's scope or detach comments from their research content.
    old_region, region, old_items = {}, 0, {}
    for e in original['flow']:
        if e.get('protected'):
            region += 1
        old_region[e['id']] = region
        for it in e.get('items', []):
            old_items[it['sourceItem']] = (it, region)
    region, pieces, seen_items = 0, [], set()
    active_box, in_document = None, False
    for identity, record in records.items():
        if record['base'].get('structureLocked') and identity not in ids:
            raise ValueError('Cannot delete source containing comments')
    labels = set(reference_tokens(source)[0])
    for e in original['flow']:
        labels.update(it['label'] for it in e.get('items', []))
        if e.get('table'):
            labels.add(e['table']['label'])
    def new_label(identity):
        base = 'fig:editor-' + re.sub(r'[^A-Za-z0-9_-]', '', identity)
        label, n = base, 1
        while label in labels:
            label, n = base + '-' + str(n), n + 1
        labels.add(label)
        return label
    for entry in flow:
        record = records.get(entry['id'])
        if entry.get('role') == 'preamble':
            in_document = True
        elif entry.get('role') == 'epilogue':
            in_document = False
        if entry['type'] != 'opaque' and not in_document:
            raise ValueError('Content must remain inside the document')
        if entry.get('role') == 'box-open':
            match = re.search(r'\\begin\{pppbox\}\s*\{([^}]+)\}', entry['text'])
            active_box = match.group(1).lower() if match else None
        elif entry.get('role') == 'box-close':
            active_box = None
        if entry['type'] in ('figure', 'pagebreak') and active_box:
            raise ValueError('Figures and page breaks must remain outside report boxes')
        if entry['type'] in ('subsection', 'block'):
            parent = next((e for e in flow if e['id'] == entry.get('subId')), None)
            box = entry.get('boxId') or (parent or {}).get('boxId')
            if not active_box or box != active_box:
                raise ValueError('Content must stay inside its owning report box')
        base = record['base'] if record else None
        if entry.get('protected'):
            region += 1
        if base and entry.get('type') != base['type']:
            raise ValueError('Source node type cannot be changed')
        if base and base.get('protected') and entry != base:
            raise ValueError('Protected source is read-only')
        if base and base.get('protected') is not True and old_region[entry['id']] != region and source[record['start']:record['end']].strip():
            raise ValueError('Cannot move content across protected source')
        if entry['type'] == 'figure':
            for i, item in enumerate(entry.get('items', [])):
                identity = item.get('sourceItem')
                if identity:
                    if identity in seen_items or identity not in old_items:
                        raise ValueError('Invalid figure identity')
                    seen_items.add(identity)
                    old, item_region = old_items[identity]
                    if item.get('label') != old['label'] or item_region != region:
                        raise ValueError('Preserve figure labels and protected boundaries')
                elif not item.get('label'):
                    item['label'] = new_label(entry['id'] + '-' + str(i))
        if base and _semantic(entry) == base:
            text = source[record['start']:record['end']]
            edits = []
            for key, span in record['fields'].items():
                if key in ('title', 'author', 'project', 'abstract') and state.get(key, '') != original[key]:
                    if not safe_text(state.get(key, '')):
                        raise ValueError('Unsupported header or abstract syntax')
                    edits.append((span[0], span[1], md_inline(state.get(key, ''))))
            for start, end, value in sorted(edits, reverse=True):
                value = preserve_spacing(source[start:end], value)
                text = text[:start-record['start']] + value + text[end-record['start']:]
            pieces.append(text)
            continue
        if entry['type'] == 'opaque':
            if not base or entry != base:
                raise ValueError('Read-only source was modified')
            pieces.append(entry['text'])
            continue
        if base:
            for key in ('boxId', 'subId', 'table'):
                if entry.get(key) != base.get(key):
                    raise ValueError('Preserve source ownership and table format')
        edits = []
        if entry['type'] == 'block' and base and base.get('table'):
            lines = entry['text'].splitlines()
            if not safe_text(entry['text']):
                raise ValueError('Unsupported table syntax')
            rows = [line.strip() for line in lines if line.strip().startswith('|')]
            width = len(base['table']['columns'].split())
            if not rows or any(len(line.strip('|').split('|')) != width for line in rows):
                raise ValueError('Keep the table column count; edit complex tables in LaTeX')
            body = block_tex(entry['text'])
            spans, _ = arguments(body, len('\\ReportTable'), 4)
            new_cells = table_cells(body[slice(*spans[1])], spans[1][0])
            old_cells = record['fields']['tableCells']
            if len(new_cells) == len(old_cells):
                for old_row, new_row in zip(old_cells, new_cells):
                    for old_span, new_span in zip(old_row, new_row):
                        value = body[slice(*new_span)]
                        if to_md(source[slice(*old_span)]) != to_md(value):
                            edits.append((*old_span, value))
            else:
                edits.append((*record['fields']['tableBody'], body[slice(*spans[1])]))
            cap = record['fields']['tableCaption']
            value = body[slice(*spans[2])]
            if to_md(source[slice(*cap)]) != to_md(value):
                edits.append((*cap, value))
        elif entry['type'] in ('block', 'subsection') and base:
            key = 'text' if entry['type'] == 'block' else 'heading'
            if not safe_text(entry[key]):
                raise ValueError('Unsupported syntax: edit this content in LaTeX')
            if key == 'text' and re.search(r'(?m)^[ \t]+(?:[-*]|\d+\.)\s', entry[key]):
                raise ValueError('Nested lists must be edited in LaTeX')
            edits.append((*record['fields'][key], block_tex(entry[key]) if key == 'text' else md_inline(entry[key])))
        elif entry['type'] == 'figure':
            items = entry.get('items', [])
            if any(not safe_text(str(it.get(k, ''))) for it in items for k in ('path', 'caption', 'label')):
                raise ValueError('Unsupported figure syntax')
            if not 0 < float(entry.get('heightMm', 40)) <= 120:
                raise ValueError('Figure height must be positive and at most 120 mm')
            if not 1 <= len(items) <= 2:
                raise ValueError('A figure needs one or two items')
            same_items = base and [i.get('sourceItem') for i in items] == [i.get('sourceItem') for i in base['items']]
            if base and base.get('structureLocked') and not same_items:
                raise ValueError('Cannot split or merge figures containing comments')
            if same_items:
                for i, item in enumerate(items):
                    for key in ('path', 'caption'):
                        if item[key] != base['items'][i][key]:
                            edits.append((*record['fields'][f'{i}.{key}'], md_inline(item[key]) if key == 'caption' else item[key]))
                if len(items) == 1 and entry.get('heightMm') != base.get('heightMm'):
                    edits.append((*record['fields']['heightMm'], str(entry['heightMm']) + 'mm'))
            else:
                args = ['{' + (md_inline(it[k]) if k == 'caption' else it[k]) + '}' for it in items for k in ('path', 'caption', 'label')]
                value = '\\ReportFigure' + ('Pair' if len(items) == 2 else '') + '\n    ' + '\n    '.join(args)
                if len(items) == 1:
                    value += '\n    {' + str(entry.get('heightMm', 40)) + 'mm}'
                pieces.append(value + '\n')
                continue
        elif not base and entry['type'] in ('block', 'subsection', 'pagebreak'):
            if re.search(r'(?m)^[ \t]+(?:[-*]|\d+\.)\s', entry.get('text', '')):
                raise ValueError('Nested lists must be edited in LaTeX')
            if not safe_text(entry.get('text', entry.get('heading', ''))):
                raise ValueError('Unsupported new content syntax')
            value = (block_tex(entry['text'], 'editor-' + re.sub(r'[^A-Za-z0-9_-]', '', entry['id']) + '-') if entry['type'] == 'block' else
                     '\\ReportSubsection{' + md_inline(entry['heading']) + '}' if entry['type'] == 'subsection' else '\\clearpage')
            pieces.append('\n' + value + '\n')
            continue
        else:
            raise ValueError('Unsupported source operation')
        text = source[record['start']:record['end']]
        for start, end, value in sorted(edits, reverse=True):
            if '\r\n' in source:
                value = value.replace('\r\n', '\n').replace('\n', '\r\n')
            value = preserve_spacing(source[start:end], value)
            text = text[:start-record['start']] + value + text[end-record['start']:]
        pieces.append(text)
    # Removing a referenced label would leave a document that appears to save
    # successfully but no longer points to its evidence. Existing unresolved
    # external references are not treated as newly introduced failures.
    result = ''.join(pieces)
    literal_labels, references = reference_tokens(result)
    reparsed, _ = parse(result)
    defined = literal_labels
    defined += [it['label'] for e in reparsed['flow'] for it in e.get('items', [])]
    defined += [e['table']['label'] for e in reparsed['flow'] if e.get('table')]
    original_definitions = reference_tokens(source)[0]
    original_definitions += [it['label'] for e in original['flow'] for it in e.get('items', [])]
    original_definitions += [e['table']['label'] for e in original['flow'] if e.get('table')]
    for label in references & labels:
        if label not in defined:
            raise ValueError('Cannot remove referenced label: ' + label)
    for label in set(defined):
        if defined.count(label) > max(1, original_definitions.count(label)):
            raise ValueError('Duplicate label: ' + label)
    return result
