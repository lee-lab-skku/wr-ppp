"""Adapt native Windows form persistence to the shared browser editor."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import re
import uuid

from report_editor.persistence import ConflictError, fingerprint, file_lock

from . import core
from report_editor.server import VisualEditorServer as SharedEditorServer


def values_to_state(values, week_start=''):
    """Translate the native form model to the editor's ordered flow model."""
    flow = []
    figures = list(values.get('figures', []))

    def add_figures(position):
        selected = [f for f in figures if f.get('position', 'after_plans') == position]
        used = set()
        for item in selected:
            identity = item.get('id') or uuid.uuid4().hex
            group = item.get('pair_group')
            if group and group in used:
                continue
            members = [f for f in selected if f.get('pair_group') == group] if group else [item]
            members = sorted(members, key=lambda f: f.get('pair_order', 0))
            if group and len(members) != 2:
                raise ValueError('A figure pair must contain exactly two members')
            used.add(group) if group else None
            flow.append({
                'type': 'figure', 'id': 'f' + identity,
                'heightMm': int(item.get('height_mm', 45)),
                'items': [{'path': f.get('file', ''), 'caption': f.get('caption', ''),
                           'native': deepcopy(f),
                           'prev': '/' + f.get('file', '').replace('\\', '/')}
                          for f in members],
            })

    add_figures('after_abstract')
    for box_id, key, after in (
        ('progress', 'Progress', 'after_progress'),
        ('problems', 'Problems', 'after_problems'),
        ('plans', 'Plans', 'after_plans'),
    ):
        text = values.get(key, '')
        if text.strip():
            flow.append({'type': 'block', 'boxId': box_id, 'id': 'b' + uuid.uuid4().hex, 'text': text})
        else:
            flow.append({'type': 'subsection', 'boxId': box_id, 'id': 's' + uuid.uuid4().hex,
                         'heading': key, 'nativePlaceholder': True})
        add_figures(after)
    return {'formatVersion': 2, 'capabilities': {'nativeForm': True},
            'nativeOriginal': deepcopy(values), 'title': values.get('title', ''), 'author': values.get('author', ''),
            'project': values.get('project', ''), 'weekStart': week_start,
            'abstract': values.get('abstract', ''), 'flow': flow}


def state_to_values(state, previous=None):
    """Translate supported flow while retaining native identity and extra fields."""
    if state.get('formatVersion', 1) not in (1, 2):
        raise ValueError('Unsupported editor state version')
    values = deepcopy(previous or state.get('nativeOriginal') or {})
    values.update({key: state.get(key, '') for key in ('title', 'author', 'project', 'abstract')})
    text = {'progress': [], 'problems': [], 'plans': []}
    figures, current_box = [], None
    position = 'after_abstract'
    position_for = {'progress': 'after_progress', 'problems': 'after_problems', 'plans': 'after_plans'}
    flow = state.get('flow', [])
    seen_boxes, closed_boxes = set(), set()
    for entry in flow:
        kind = entry.get('type')
        if kind in ('subsection', 'block'):
            parent = next((e for e in flow if e.get('id') == entry.get('subId')), {})
            next_box = entry.get('boxId') or parent.get('boxId') or current_box
            if next_box not in text:
                raise ValueError('Unknown report section')
            if next_box != current_box:
                if next_box in seen_boxes or (current_box and list(text).index(next_box) < list(text).index(current_box)):
                    raise ValueError('The native form preserves Progress, Problems, Plans order')
                seen_boxes.add(next_box)
            if next_box in closed_boxes:
                raise ValueError('Native figures must stay after an entire section')
            current_box = next_box
            if current_box in position_for:
                position = position_for[current_box]
            if kind == 'subsection' and not (entry.get('nativePlaceholder') and entry.get('heading') == {'progress': 'Progress', 'problems': 'Problems', 'plans': 'Plans'}[current_box]):
                text[current_box].append('## ' + entry.get('heading', ''))
            elif kind == 'block' and current_box in text:
                text[current_box].append(entry.get('text', ''))
        elif kind == 'figure':
            if current_box:
                closed_boxes.add(current_box)
            items = entry.get('items', [])
            if not 1 <= len(items) <= 2:
                raise ValueError('A figure needs one or two items')
            groups = [it.get('native', {}).get('pair_group') for it in items]
            group = ((groups[0] if groups[0] and len(set(groups)) == 1 else 'pair-' + '-'.join(str(it.get('native', {}).get('id') or it.get('editorId') or entry.get('id', 'figure')) for it in items))
                     if len(items) == 2 else None)
            for order, item in enumerate(items):
                path = str(item.get('path', '')).replace('\\', '/')
                original = deepcopy(item.get('native', {}))
                original.pop('pair_group', None)
                original.pop('pair_order', None)
                figures.append({**original, 'file': path, 'caption': item.get('caption', ''),
                                'id': original.get('id') or re.sub(r'[^A-Za-z0-9_-]', '', item.get('editorId') or entry.get('id', 'figure') + '-' + str(order)),
                                'position': position, 'height_mm': (original.get('height_mm', 45) if len(items) == 2 else int(entry.get('heightMm', 45))),
                                **({'pair_group': group, 'pair_order': order} if group else {})})
        else:
            raise ValueError('This structure cannot be represented by the native form')
    for box_id, key in (('progress', 'Progress'), ('problems', 'Problems'), ('plans', 'Plans')):
        values[key] = '\n\n'.join(part for part in text[box_id] if part.strip())
    # Preserve absent defaults, whitespace and extra fields on a no-op round trip.
    original = state.get('nativeOriginal', {})
    if original:
        baseline = values_to_state(original, state.get('weekStart', ''))
        for key in ('title', 'author', 'project', 'abstract'):
            if state.get(key, '') == baseline.get(key, ''):
                if key in original: values[key] = original[key]
                else: values.pop(key, None)
        for box, key in (('progress', 'Progress'), ('problems', 'Problems'), ('plans', 'Plans')):
            entries = [e for e in flow if e.get('boxId') == box or any(p.get('id') == e.get('subId') and p.get('boxId') == box for p in flow)]
            before = [e for e in baseline['flow'] if e.get('boxId') == box]
            if [(e['type'], e.get('text'), e.get('heading')) for e in entries] == [(e['type'], e.get('text'), e.get('heading')) for e in before]:
                if key in original: values[key] = original[key]
                else: values.pop(key, None)
        old_visual_figures = [e for e in baseline['flow'] if e['type'] == 'figure']
        new_visual_figures = [e for e in flow if e['type'] == 'figure']
        def visual_identity(entries):
            return [{k: v for k, v in e.items() if k != 'id'} for e in entries]
        if visual_identity(new_visual_figures) == visual_identity(old_visual_figures):
            figures = deepcopy(original.get('figures', []))
        old_figures = original.get('figures', [])
        for i, figure in enumerate(figures):
            old = next((f for f in old_figures if f.get('id') == figure['id']), None)
            if old:
                for key, default in (('position', 'after_plans'), ('height_mm', 45)):
                    if key not in old and figure.get(key) == default:
                        figure.pop(key, None)
    values['figures'] = figures
    if 'figures' not in original and not figures:
        values.pop('figures', None)
    return values


def save_form(form_file, values, allow_user_styles=False):
    """Validate and stage both outputs before committing authoritative JSON.

    The caller holds the form lock. JSON is authoritative if replacing the
    derived TeX fails; reopening the form can regenerate it without data loss.
    """
    form_file = Path(form_file)
    tex_file = form_file.with_suffix('.tex')
    tex = core.form_source(values, allow_user_styles)
    encoded = json.dumps(values, ensure_ascii=False, indent=2)
    staged = []
    try:
        staged.append(core.stage_write(form_file, encoded))
        staged.append(core.stage_write(tex_file, tex))
        os.replace(staged[0], form_file)
        try:
            os.replace(staged[1], tex_file)
        except OSError as error:
            raise ConflictError('작성 데이터는 저장됐지만 TeX 갱신에 실패했습니다. 폼을 다시 열고 저장하여 복구하세요.') from error
    finally:
        for file in staged:
            file.unlink(missing_ok=True)
    return fingerprint(form_file), fingerprint(tex_file)


class FormBackend:
    def __init__(self, form_file, on_save=None, allow_user_styles=False):
        self.form_file = Path(form_file).resolve()
        self.directory = self.form_file.parent
        self.on_save = on_save
        self.allow_user_styles = allow_user_styles
        self.expected = fingerprint(self.form_file)
        self.tex_expected = fingerprint(self.form_file.with_suffix('.tex'))
        self.snapshots = []

    def load(self):
        values = json.loads(self.form_file.read_text(encoding='utf-8'))
        self.snapshots.append(deepcopy(values))
        return values_to_state(values)

    def save(self, state):
        with file_lock(self.form_file):
            if fingerprint(self.form_file) != self.expected or fingerprint(self.form_file.with_suffix('.tex')) != self.tex_expected:
                raise ConflictError('작성 데이터가 다른 곳에서 변경되었습니다. 다시 여세요.')
            previous = json.loads(self.form_file.read_text(encoding='utf-8'))
            if state.get('nativeOriginal') not in self.snapshots:
                raise ConflictError('The native import snapshot changed')
            values = state_to_values(state, previous)
            self.expected, self.tex_expected = save_form(self.form_file, values, self.allow_user_styles)
        if self.on_save:
            self.on_save(values)

    def write_image(self, target, data):
        core.atomic_write(target, data)


class VisualEditorServer(SharedEditorServer):
    def __init__(self, form_file, template_file, on_save=None, allow_user_styles=False):
        super().__init__(FormBackend(form_file, on_save, allow_user_styles), template_file)
