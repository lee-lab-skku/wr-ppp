#!/usr/bin/env python3
"""Headless-Chrome behaviour checks for the editor.

Every assertion here exists because the behaviour it covers broke at least
once during development: drag that silently did nothing, edit boxes that
never closed, figure pairs that stretched past their fixed height, bold runs
torn apart by inline math.

Usage: run_tests.py [path/to/editor.html]
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDITOR = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / 'assets' / 'editor.html'

HARNESS = r"""
<script>
var OUT = {};
window.onerror = function(m,u,l){ OUT.jsError = m + ' @' + l; };
function rc(el){ var r = el.getBoundingClientRect(); return {x:r.left+Math.min(30,r.width/2), y:r.top+r.height/2}; }
function press(el, x, y){
  ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(t){
    var C = t.indexOf('pointer')===0 ? PointerEvent : MouseEvent;
    var i = {bubbles:true,cancelable:true,clientX:x,clientY:y,button:0,view:window};
    if(C===PointerEvent){ i.pointerId=1; i.pointerType='mouse'; i.isPrimary=true; }
    el.dispatchEvent(new C(t,i));
  });
}
function drag(handle, target){
  var a = rc(handle), b = rc(target);
  function m(t,x,y){ document.dispatchEvent(new MouseEvent(t,{bubbles:true,cancelable:true,clientX:x,clientY:y,button:0,buttons:1,view:window})); }
  handle.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,cancelable:true,clientX:a.x,clientY:a.y,button:0,buttons:1,view:window}));
  m('mousemove', a.x, a.y+8); m('mousemove', b.x, b.y); m('mouseup', b.x, b.y);
}
function key(k, opt){
  var i = {key:k, bubbles:true, cancelable:true};
  for(var x in (opt||{})) i[x] = opt[x];
  (document.activeElement||document.body).dispatchEvent(new KeyboardEvent('keydown', i));
}
function subs(){ return Array.prototype.map.call(document.querySelectorAll('.subsec-block'), function(s){
  return s.querySelector('.subsec-heading').textContent.trim().slice(0,10); }).join('|'); }
function figShape(){ return Array.prototype.map.call(document.querySelectorAll('.fig-block'), function(b){
  return b.querySelectorAll('.fig-col').length; }).join(','); }

window.addEventListener('load', function(){ setTimeout(function(){
  // --- inline rendering ------------------------------------------------
  var probe = document.createElement('div');
  probe.innerHTML = window.__inlineMd('\\textbf{a $+34\\%$ b} \\texttt{x.py} \\qty{50}{ms} \\num{1.71} \\qtyrange{10}{25}{\\micro\\meter} $D_p=\\qty{41.8}{\\micro\\meter}$ ``q\'\'');
  OUT.inlineBold  = !!probe.querySelector('b');
  OUT.inlineCode  = !!probe.querySelector('code');
  OUT.inlineMath  = !!probe.querySelector('.katex');
  // siunitx binds number and unit with a non-breaking space, as \qty does
  OUT.inlineUnit  = probe.textContent.replace(/ /g,' ').indexOf('50 ms') >= 0;
  OUT.inlineSi    = probe.textContent.replace(/ /g,' ').indexOf('1.71') >= 0 &&
                    probe.textContent.replace(/ /g,' ').indexOf('10–25 µm') >= 0 &&
                    probe.textContent.indexOf('41.8') >= 0;
  OUT.inlineQuote = probe.textContent.indexOf('“') >= 0;

  // --- view modes ------------------------------------------------------
  OUT.hybridPages = document.querySelectorAll('.page').length;
  key('e', {ctrlKey:true});
  OUT.renderedPages = document.querySelectorAll('.page').length;
  OUT.renderedNoHandles = document.querySelectorAll('.drag-handle').length === 0;
  key('e', {ctrlKey:true});
  key('s', {altKey:true});
  OUT.rawTextareas = document.querySelectorAll('textarea.edit-src').length;
  key('s', {altKey:true});

  // --- hybrid edit opens and closes ------------------------------------
  var f = document.querySelector('.cblock-body[data-editable]');
  var p = rc(f); press(f, p.x, p.y);
  OUT.editorOpened = document.querySelectorAll('textarea.edit-src').length;
  var pg = document.querySelector('.page'), r = pg.getBoundingClientRect();
  press(pg, r.left+8, r.top+8);
  OUT.editorClosed = document.querySelectorAll('textarea.edit-src').length;

  // --- drag: a nudge must not relocate the block -----------------------
  var before = subs();
  var h = document.querySelectorAll('.subsec-block')[0].querySelector('.subsec-headrow .drag-handle');
  var a = rc(h);
  h.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,cancelable:true,clientX:a.x,clientY:a.y,button:0,buttons:1,view:window}));
  document.dispatchEvent(new MouseEvent('mousemove',{bubbles:true,cancelable:true,clientX:a.x+6,clientY:a.y+10,button:0,buttons:1,view:window}));
  OUT.nudgeShowsHome = !!document.querySelector('.gap.home');
  document.dispatchEvent(new MouseEvent('mouseup',{bubbles:true,cancelable:true,clientX:a.x+6,clientY:a.y+10,button:0,buttons:1,view:window}));
  OUT.nudgeKeptOrder = subs() === before;

  // --- drag: a real move reorders --------------------------------------
  var anchors = document.querySelectorAll('.gap[data-gap-scope="box:progress"]');
  if(anchors.length){
    drag(document.querySelectorAll('.subsec-block')[0].querySelector('.subsec-headrow .drag-handle'),
         anchors[anchors.length-1]);
  }
  OUT.realMoveReordered = subs() !== before;

  // --- a subsection may not leave its box ------------------------------
  var firstBox = (document.querySelectorAll('.subsec-block')[0].closest('.box-wrap'));
  var allAnchors = document.querySelectorAll('.gap');
  drag(document.querySelectorAll('.subsec-block')[0].querySelector('.subsec-headrow .drag-handle'),
       allAnchors[allAnchors.length-1]);
  OUT.stillSameBoxCount = document.querySelectorAll('.box-wrap:not(.abstract-box)').length;

  // --- figures: split a pair, then merge back ---------------------------
  OUT.figShapeStart = figShape();
  var pair = Array.prototype.filter.call(document.querySelectorAll('.fig-block'), function(b){
    return b.querySelectorAll('.fig-col').length === 2; })[0];
  if(pair){
    var outside = document.querySelectorAll('.gap[data-gap-scope="outside"]');
    drag(pair.querySelectorAll('.fig-col')[1].querySelector('.drag-handle'), outside[outside.length-1]);
  }
  OUT.figShapeAfterSplit = figShape();

  // --- the abstract exists and the title is editable --------------------
  OUT.hasAbstract = !!document.querySelector('.abstract-box');
  OUT.titleEditable = !!document.querySelector('[data-editable="title"]');

  var d = document.createElement('div');
  d.id = 'RESULT';
  d.textContent = '@@' + JSON.stringify(OUT) + '@@';
  document.body.appendChild(d);
}, 900); });
</script>
"""

CHECKS = [
    ('no JS errors',                  lambda o: 'jsError' not in o),
    ('inline \\textbf renders',       lambda o: o['inlineBold']),
    ('inline \\texttt renders',       lambda o: o['inlineCode']),
    ('bold spanning $math$ survives', lambda o: o['inlineBold'] and o['inlineMath']),
    ('\\qty unit renders',            lambda o: o['inlineUnit']),
    ('siunitx variants render',       lambda o: o['inlineSi']),
    ('LaTeX quotes render',           lambda o: o['inlineQuote']),
    ('rendered view paginates',       lambda o: o['renderedPages'] >= o['hybridPages']),
    ('hybrid view is continuous',     lambda o: o['hybridPages'] == 1),
    ('rendered view hides handles',   lambda o: o['renderedNoHandles']),
    ('raw view shows source boxes',   lambda o: o['rawTextareas'] > 0),
    ('click opens an editor',         lambda o: o['editorOpened'] == 1),
    ('click away closes it',          lambda o: o['editorClosed'] == 0),
    ('a nudge targets home',          lambda o: o['nudgeShowsHome']),
    ('a nudge does not move it',      lambda o: o['nudgeKeptOrder']),
    ('a real drag reorders',          lambda o: o['realMoveReordered']),
    ('subsection stays in its box',   lambda o: o['stillSameBoxCount'] == 3),
    ('figure pair splits',            lambda o: o['figShapeAfterSplit'] != o['figShapeStart']),
    ('abstract block present',        lambda o: o['hasAbstract']),
    ('title is editable',             lambda o: o['titleEditable']),
]


def main():
    chrome = next((c for c in ('google-chrome', 'chromium', 'chromium-browser') if shutil.which(c)), None)
    if not chrome:
        print('skip: no Chrome/Chromium on PATH')
        return 0

    html = EDITOR.read_text(encoding='utf-8')
    html = html.replace('  renderAll();\n})();', '  window.__inlineMd = inlineMd;\n  renderAll();\n})();')
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / 'harness.html'
        page.write_text('<!doctype html><html><head><meta charset="utf-8"></head><body>'
                        + html + HARNESS + '</body></html>', encoding='utf-8')
        dom = subprocess.run([chrome, '--headless', '--disable-gpu', '--no-sandbox',
                              '--window-size=1400,1800', '--virtual-time-budget=7000',
                              '--dump-dom', page.as_uri()],
                             capture_output=True, text=True, timeout=180).stdout

    m = re.search(r'@@(\{.*?\})@@', dom, re.S)
    if not m:
        print('FAIL: the harness produced no result (page did not finish loading)')
        return 1
    out = json.loads(m.group(1))

    failed = 0
    for label, check in CHECKS:
        try:
            ok = bool(check(out))
        except Exception as exc:                      # a missing key is a failure too
            ok = False
            label += f'  ({exc})'
        print(('  ok   ' if ok else '  FAIL ') + label)
        failed += not ok
    if 'jsError' in out:
        print('  js error:', out['jsError'])
    print(f"\n{len(CHECKS)-failed}/{len(CHECKS)} passed")
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
