"""Adapt native Windows form persistence to the shared browser editor."""
from __future__ import annotations

import json
from pathlib import Path
import re
import uuid

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
            members = sorted(members, key=lambda f: f.get('pair_order', 0))[:2]
            used.add(group) if group else None
            flow.append({
                'type': 'figure', 'id': 'f' + identity,
                'heightMm': int(item.get('height_mm', 45)),
                'items': [{'path': f.get('file', ''), 'caption': f.get('caption', ''),
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
                         'heading': key})
        add_figures(after)
    return {'title': values.get('title', ''), 'author': values.get('author', ''),
            'project': values.get('project', ''), 'weekStart': week_start,
            'abstract': values.get('abstract', ''), 'flow': flow}


def state_to_values(state, previous=None):
    """Translate editor state back to the native form without losing tables."""
    values = dict(previous or {})
    values.update({key: state.get(key, '') for key in ('title', 'author', 'project', 'abstract')})
    text = {'progress': [], 'problems': [], 'plans': []}
    figures, current_box = [], None
    position = 'after_abstract'
    position_for = {'progress': 'after_progress', 'problems': 'after_problems', 'plans': 'after_plans'}
    for entry in state.get('flow', []):
        kind = entry.get('type')
        if kind in ('subsection', 'block'):
            current_box = entry.get('boxId') or current_box
            if current_box in position_for:
                position = position_for[current_box]
            if kind == 'subsection' and entry.get('heading') not in ('Progress', 'Problems', 'Plans'):
                text[current_box].append('## ' + entry.get('heading', ''))
            elif kind == 'block' and current_box in text:
                text[current_box].append(entry.get('text', ''))
        elif kind == 'figure':
            items = entry.get('items', [])[:2]
            group = uuid.uuid4().hex if len(items) == 2 else None
            for order, item in enumerate(items):
                path = str(item.get('path', '')).replace('\\', '/')
                figures.append({'file': path, 'caption': item.get('caption', ''),
                                'id': re.sub(r'[^A-Za-z0-9_-]', '', Path(path).stem) or uuid.uuid4().hex,
                                'position': position, 'height_mm': int(entry.get('heightMm', 45)),
                                **({'pair_group': group, 'pair_order': order} if group else {})})
    for box_id, key in (('progress', 'Progress'), ('problems', 'Problems'), ('plans', 'Plans')):
        values[key] = '\n\n'.join(part for part in text[box_id] if part.strip())
    values['figures'] = figures
    return values


class FormBackend:
    def __init__(self, form_file, on_save=None, allow_user_styles=False):
        self.form_file = Path(form_file).resolve()
        self.directory = self.form_file.parent
        self.on_save = on_save
        self.allow_user_styles = allow_user_styles

    def load(self):
        return values_to_state(json.loads(self.form_file.read_text(encoding='utf-8')))

    def save(self, state):
        previous = json.loads(self.form_file.read_text(encoding='utf-8'))
        values = state_to_values(state, previous)
        core.atomic_write(self.form_file, json.dumps(values, ensure_ascii=False, indent=2))
        core.atomic_write(self.form_file.with_suffix('.tex'),
                          core.form_source(values, self.allow_user_styles))
        if self.on_save:
            self.on_save(values)

    def write_image(self, target, data):
        core.atomic_write(target, data)


class VisualEditorServer(SharedEditorServer):
    def __init__(self, form_file, template_file, on_save=None, allow_user_styles=False):
        super().__init__(FormBackend(form_file, on_save, allow_user_styles), template_file)
