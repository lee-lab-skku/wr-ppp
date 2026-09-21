"""Local browser transport shared by the TeX and native Windows form adapters.

Backends own state conversion and persistence and expose directory, load(),
save(state), and write_image(path, bytes). The server never compiles reports.
"""
from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import secrets
import threading
import uuid

from . import TEMPLATE
from .build_artifact import build

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.pdf'}


def _editor_html(template, state, token):
    html = build(state, template)
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
    def __init__(self, backend, template_file=TEMPLATE):
        self.backend = backend
        self.template_file = Path(template_file)
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
                    target = (owner.backend.directory / relative).resolve()
                    figures = (owner.backend.directory / 'figures').resolve()
                    if figures not in target.parents or not target.is_file():
                        return self._send(404)
                    return self._send(200, target.read_bytes(), mimetypes.guess_type(target.name)[0] or 'application/octet-stream')
                if not self._authorized():
                    return self._send(403)
                state = owner.backend.load()
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
                        owner.backend.save(state)
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
                    target = owner.backend.directory / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    owner.backend.write_image(target, match.group(2))
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
