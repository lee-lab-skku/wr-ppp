from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import secrets
import threading
import uuid

from . import core


STATE_MARK = '<script id="state-json" type="application/json">'
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.pdf'}


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


def _editor_html(template, state, token):
    start = template.index(STATE_MARK) + len(STATE_MARK)
    end = template.index('</script>', start)
    state_json = json.dumps(state, ensure_ascii=False).replace('</', '<\\/')
    html = template[:start] + '\n' + state_json + '\n' + template[end:]
    bridge = r'''
  var localSaveTimer = null;
  function localSave(payload){
    clearTimeout(localSaveTimer);
    var body=payload || JSON.stringify(STATE);
    localSaveTimer = setTimeout(function(){
      fetch('/api/state?token=__TOKEN__', {method:'POST', headers:{'Content-Type':'application/json'},
        body:body}).then(function(r){
          if(!r.ok) throw new Error('save');
          if(!payload) savedJson=JSON.stringify(STATE);
          lastSavedLabel='자동 저장됨';
          updateSaveState();
        }).catch(function(){ showToast('자동 저장 실패'); });
    }, 300);
  }
  var nativeRenderAll = renderAll;
  renderAll = function(){ nativeRenderAll(); localSave(); };
  document.addEventListener('input', function(ev){
    var ta=ev.target;
    if(ta.dataset && ta.dataset.hybridEdit === '1'){
      var t=fieldTarget(+ta.dataset.flowIdx, ta.dataset.editorField);
      if(t.obj && t.prop){
        var old=t.obj[t.prop];
        t.obj[t.prop]=ta.value;
        var live=JSON.stringify(STATE);
        t.obj[t.prop]=old;
        localSave(live);
      }
    }
  });
  var nativeStartEdit = startEdit;
  startEdit = function(el){
    var field=el.dataset.editable, idx=el.dataset.flowIdx;
    nativeStartEdit(el);
    var ta=document.activeElement;
    if(ta && ta.dataset.hybridEdit === '1'){ ta.dataset.editorField=field; ta.dataset.flowIdx=idx; }
  };
  var nativeAttachImage = attachImage;
  attachImage = function(idx, itemIdx, file){
    var data=new FormData(); data.append('image', file);
    fetch('/api/image?token=__TOKEN__', {method:'POST', body:data}).then(function(r){
      if(!r.ok) throw new Error('upload'); return r.json();
    }).then(function(result){
      makePreview(file, function(preview){
        var item=STATE.flow[idx] && STATE.flow[idx].items[itemIdx];
        if(!item || !preview) return;
        snapshot();
        item.prev=preview.preview;
        item.dim={w:preview.w,h:preview.h};
        item.path=result.path;
        renderAll();
      });
    }).catch(function(){ showToast('이미지 원본 저장 실패'); });
  };
  window.claude={use:async function(){return {publish:async function(){
    var r=await fetch('/api/state?token=__TOKEN__',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(STATE)});
    if(!r.ok) throw new Error('local-save-failed');
  }}}};
'''.replace('__TOKEN__', token)
    return html.replace('  renderAll();\n})();', bridge + '\n  renderAll();\n})();')


class VisualEditorServer:
    def __init__(self, form_file, template_file, on_save=None, allow_user_styles=False):
        self.form_file = Path(form_file).resolve()
        self.template_file = Path(template_file)
        self.on_save = on_save
        self.allow_user_styles = allow_user_styles
        self.token = secrets.token_urlsafe(24)
        self.httpd = None

    def start(self):
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def _authorized(self):
                return ('token=' + owner.token) in self.path

            def _send(self, status, body=b'', content_type='text/plain; charset=utf-8'):
                self.send_response(status)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path.startswith('/figures/'):
                    relative = self.path.split('?', 1)[0].lstrip('/')
                    target = (owner.form_file.parent / relative).resolve()
                    figures = (owner.form_file.parent / 'figures').resolve()
                    if figures not in target.parents or not target.is_file():
                        return self._send(404)
                    return self._send(200, target.read_bytes(), mimetypes.guess_type(target.name)[0] or 'application/octet-stream')
                if not self._authorized():
                    return self._send(403)
                values = json.loads(owner.form_file.read_text(encoding='utf-8'))
                state = values_to_state(values)
                html = _editor_html(owner.template_file.read_text(encoding='utf-8'), state, owner.token)
                self._send(200, html.encode('utf-8'), 'text/html; charset=utf-8')

            def do_POST(self):
                if not self._authorized():
                    return self._send(403)
                length = int(self.headers.get('Content-Length', '0'))
                if length > 25 * 1024 * 1024:
                    return self._send(413)
                body = self.rfile.read(length)
                if self.path.startswith('/api/state'):
                    try:
                        state = json.loads(body.decode('utf-8'))
                        previous = json.loads(owner.form_file.read_text(encoding='utf-8'))
                        values = state_to_values(state, previous)
                        core.atomic_write(owner.form_file, json.dumps(values, ensure_ascii=False, indent=2))
                        core.atomic_write(owner.form_file.with_suffix('.tex'),
                                          core.form_source(values, owner.allow_user_styles))
                        if owner.on_save:
                            owner.on_save(values)
                    except Exception as error:
                        return self._send(400, str(error).encode('utf-8'))
                    return self._send(204)
                if self.path.startswith('/api/image'):
                    match = re.search(br'filename="([^"]+)"\r\nContent-Type:[^\r]*\r\n\r\n(.*)\r\n--', body, re.DOTALL)
                    if not match:
                        return self._send(400)
                    name = match.group(1).decode('utf-8', 'replace')
                    suffix = Path(name).suffix.lower()
                    if suffix not in IMAGE_EXTENSIONS:
                        return self._send(415)
                    relative = 'figures/' + uuid.uuid4().hex + suffix
                    target = owner.form_file.parent / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    core.atomic_write(target, match.group(2))
                    payload = json.dumps({'path': relative}).encode('utf-8')
                    return self._send(200, payload, 'application/json')
                self._send(404)

        self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        port = self.httpd.server_address[1]
        return f'http://127.0.0.1:{port}/?token={self.token}'

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
