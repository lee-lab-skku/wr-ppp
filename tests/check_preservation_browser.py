"""Real browser check of source-backed editing, autosave and undo/redo."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from report_editor import TEMPLATE
from report_editor.server import VisualEditorServer
from report_editor.tex_backend import TexBackend

EXPOSE = '''
  window.__sourceTest={state:function(){return STATE;}, dirty:function(){return isDirty();},
    flush:function(){return flushLocalSave();},render:function(){renderAll();}};
'''
HARNESS = r'''
<script>
window.addEventListener('load',function(){setTimeout(async function(){
 var result={};
 try{
  var api=window.__sourceTest;
  await api.flush();
  result.hasProtectedSource=!!document.getElementById('preservedSource');
  result.hasTitle=!!document.querySelector('[data-editable="title"]');
  var title=document.querySelector('[data-editable="title"]'); title.click();
  var ta=document.activeElement; result.editOpened=ta.tagName==='TEXTAREA';
  ta.value='Browser preservation check'; ta.dispatchEvent(new Event('input',{bubbles:true}));
  result.liveInputDirty=api.dirty();
  await api.flush(); result.liveInputSaved=!api.dirty();
  ta.blur(); await api.flush();
  document.dispatchEvent(new KeyboardEvent('keydown',{key:'z',ctrlKey:true,bubbles:true,cancelable:true}));
  await api.flush(); result.undo=api.state().title!=='Browser preservation check';
  document.dispatchEvent(new KeyboardEvent('keydown',{key:'z',ctrlKey:true,shiftKey:true,bubbles:true,cancelable:true}));
  await api.flush(); result.redo=api.state().title==='Browser preservation check';
  result.originalLabels=api.state().flow.filter(e=>e.type==='figure').flatMap(e=>e.items.map(i=>i.label)).join(',')===
    'fig:calibration-curve,fig:rare-class-errors,fig:seed-variance';
  document.getElementById('saveBtn').click(); await api.flush();
  var json=JSON.parse(document.getElementById('state-json').textContent);
  result.exportHasSource=typeof json.preservation.source==='string' && json.preservation.source.includes('% This is an adaptable example');
 }catch(error){result.error=String(error);}
 var out=document.createElement('pre');out.id='RESULT';out.textContent='@@'+JSON.stringify(result)+'@@';document.body.appendChild(out);
},300);});
</script>
'''


def main():
    chrome = os.environ.get('WR_BROWSER') or next((shutil.which(c) for c in ('google-chrome', 'chromium', 'chromium-browser') if shutil.which(c)), None)
    edge = Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')) / 'Microsoft/Edge/Application/msedge.exe'
    chrome = chrome or (str(edge) if edge.is_file() else None)
    if not chrome:
        print('skip: no Chrome/Chromium/Edge')
        return 1 if os.environ.get('WR_REQUIRE_BROWSER') else 0
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / 'main.tex'
        original = (ROOT / 'template.tex').read_bytes()
        source.write_bytes(original)
        template = root / 'editor.html'
        html = TEMPLATE.read_text(encoding='utf-8').replace('  renderAll();\n})();', EXPOSE + '  renderAll();\n})();')
        template.write_text(html + HARNESS, encoding='utf-8')
        backend = TexBackend(source)
        server = VisualEditorServer(backend, template)
        try:
            url = server.start()
            result = subprocess.run([chrome, '--headless', '--disable-gpu', '--no-sandbox',
                                     '--user-data-dir=' + str(root / 'profile'),
                                     '--virtual-time-budget=15000', '--dump-dom', url],
                                    capture_output=True, text=True, encoding='utf-8', timeout=90)
            match = re.search(r'@@(\{.*?\})@@', result.stdout, re.S)
            if not match:
                print('FAIL: browser produced no result', result.stderr[-2000:])
                return 1
            checks = json.loads(match.group(1))
            for name, value in checks.items():
                print(('ok: ' if value is True else 'FAIL: ') + name + ': ' + str(value))
            actual = backend.output.read_bytes()
            expected = original.replace(b'Calibration-Aware Classification in the Low-Data Regime', b'Browser preservation check')
            checks['exactEditedSource'] = actual == expected
            print('exactEditedSource:', checks['exactEditedSource'])
            return 0 if checks and all(v is True for v in checks.values()) else 1
        finally:
            server.stop()


if __name__ == '__main__':
    sys.exit(main())
