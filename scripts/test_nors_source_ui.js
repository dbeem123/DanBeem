const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');
const root = path.resolve(__dirname, '..');
class Node {
  constructor(name) { this.name=name; this.children=[]; this.events={}; this.textContent=''; this.value=''; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children=[...nodes]; this.textContent=''; }
  addEventListener(type, fn) { this.events[type]=fn; }
  querySelectorAll(name) { return this.children.flatMap(x => x instanceof Node ? [...(x.name === name ? [x] : []), ...x.querySelectorAll(name)] : []); }
}
const nodes = Object.fromEntries(['source-output','load-status','nors-code','ftag-code','nors-filter','ftag-filter','run-nors-crosswalk','open-ftag','run-keyword-crosswalk','keyword-text'].map(id => [id,new Node(id)]));
const document = { getElementById: id=>nodes[id], createElement: name=>new Node(name), createTextNode: text=>({textContent:text}), addEventListener: (event,fn)=>{if(event==='DOMContentLoaded') document.init=fn;} };
const seen=[];
async function fetch(file) {
  seen.push(file);
  if (file.includes('nors_reviewed_links')) return {ok:true,json:async()=>({links:[{status:'draft',basis:'coded_by_reviewer',reviewer:'Daniel',reviewed_date:'2026-11-13',nors_code:'D09',f_tag:'F554'},{status:'reviewed',basis:'keyword_match',reviewer:'Daniel',reviewed_date:'2026-11-13',nors_code:'D09',f_tag:'F554'},{status:'reviewed',basis:'coded_by_reviewer',reviewer:'Daniel',reviewed_date:'2026-11-13',nors_code:'D09',f_tag:'F555',nors_authority_id:'nors-table2-d09',nors_excerpt:'D09 The deprivation',appendix_passage_id:'appendix-pp-f555-p2',appendix_excerpt:'Choice of Attending Physician'}]})};
  const target=path.join(root, file.replace(/^\.\.\//,''));
  return {ok:true,json:async()=>JSON.parse(fs.readFileSync(target,'utf8').replace(/^\uFEFF/,''))};
}
const context={document,fetch,history:{replaceState(){}},location:{hash:''},URLSearchParams,console,encodeURIComponent,Map,Set};
vm.runInNewContext(fs.readFileSync(path.join(root,'Assets/nors-crosswalk-page.js'),'utf8'),context);
const walk=node=>[node.textContent||'',...(node.children||[]).flatMap(walk)];
(async()=>{
  await document.init();
  assert.equal(nodes['nors-code'].children.flatMap(x=>x.children).length,60);
  assert.equal(nodes['ftag-code'].children.flatMap(x=>x.children).length,204);
  const f917group=nodes['ftag-code'].children.find(group=>group.children.some(option=>option.value==='F917'));
  assert.equal(f917group.label,'Section not verified');
  nodes['ftag-filter'].value='F917'; nodes['ftag-filter'].events.input();
  assert.equal(f917group.children.find(option=>option.value==='F917').hidden,false);
  assert.equal(f917group.children.find(option=>option.value==='F918').hidden,true);
  nodes['nors-code'].value='D09'; nodes['run-nors-crosswalk'].events.click();
  let text=walk(nodes['source-output']).join(' ');
  assert(text.includes('D09 The deprivation')); assert(text.includes('F555 (coded_by_reviewer)')); assert(!text.includes('F554 (coded_by_reviewer)'));
  nodes['ftag-code'].value='F554'; await nodes['open-ftag'].events.click();
  text=walk(nodes['source-output']).join(' '); assert(text.includes('self-administer medications')); assert(text.includes('Regulation (42 CFR)')); assert(!text.includes('D09 (coded_by_reviewer)'));
  nodes['keyword-text'].value='medications'; await nodes['run-keyword-crosswalk'].events.click();
  text=walk(nodes['source-output']).join(' '); assert(text.includes('NORS definitions with matching words')); assert(text.includes('Appendix PP tags with matching words')); assert(seen.every(x=>!x.includes('draft')));
  console.log('Source UI checks passed: 60 codes, 204 tags, provenance filter, F554 and source search.');
})().catch(error=>{console.error(error);process.exitCode=1;});
