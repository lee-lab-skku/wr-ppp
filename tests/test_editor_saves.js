// Exercise the actual injected bridge with controllable HTTP completions.
const assert=require('assert');
const fs=require('fs');
const vm=require('vm');
const text=fs.readFileSync('report_editor/server.py','utf8');
const code=text.slice(text.indexOf('  var localSaveTimer'),text.indexOf('  var nativeRenderAll')).replace('__REVISION__','0');
function session(){
  let requests=[];
  const c={current:'A',savedJson:null,currentEditorJson(){return JSON.stringify({title:c.current});},
    clearTimeout(){},setTimeout(){return 1;},updateSaveState(){},showToast(){},
    fetch(url,opts){return new Promise(resolve=>requests.push({payload:JSON.parse(opts.body),resolve}));}};
  vm.createContext(c);vm.runInContext(code,c);
  return {c,requests,ack(index,revision,status=200){requests[index].resolve({ok:status===200,status,json:async()=>({revision}),text:async()=> 'conflict'});}};
}
const tick=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
  const s=session(),c=s.c;
  c.localSave();const first=c.flushLocalSave();
  assert.equal(s.requests[0].payload.state.title,'A');
  c.current='B';c.localSave();const manual=c.flushLocalSave();let done=false;manual.then(()=>done=true);
  s.ack(0,1);await tick();
  assert.equal(JSON.parse(c.savedJson).title,'A');
  assert.equal(s.requests.length,2);assert.equal(s.requests[1].payload.revision,1);
  assert.equal(done,false,'manual save must wait for queued edits');
  s.ack(1,2);await Promise.all([first,manual]);
  assert.equal(JSON.parse(c.savedJson).title,'B');
  c.current='C';c.localSave();const conflict=c.flushLocalSave();s.ack(2,3,409);
  await assert.rejects(conflict);assert.equal(JSON.parse(c.savedJson).title,'B');
  await assert.rejects(c.flushLocalSave());assert.equal(s.requests.length,3,'never retry a stale revision');
  console.log('ok: serialized snapshots, pending manual save, stale conflict');
})().catch(error=>{console.error(error);process.exitCode=1;});
