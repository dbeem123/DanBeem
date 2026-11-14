const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');
const root = path.resolve(__dirname, '..');
const pageSource=fs.readFileSync(path.join(root,'Assets/nors-crosswalk-page.js'),'utf8');
const pageHtml=fs.readFileSync(path.join(root,'tools/nors-crosswalk.html'),'utf8');
assert(!/\b(?:localStorage|sessionStorage)\b/.test(pageSource), 'NORS UI must not use browser storage');
assert(/connect-src\s+'self'/.test(pageHtml), 'NORS page must restrict network connections to its own origin');
assert(!/https?:\/\//i.test(pageSource), 'NORS UI source must not contain external service URLs');
const reviewData=JSON.parse(fs.readFileSync(path.join(root,'data/nors_reviewed_links.json'),'utf8'));
const accepted=reviewData.links.filter(link=>link.status==='reviewed');
const rejected=reviewData.links.filter(link=>link.status==='rejected');
const acceptedMethods=new Set(['approved Claude first-pass triage','Daniel-directed triage approved 2026-11-13']);
assert(accepted.length>0 && accepted.every(link=>link.reviewed_by==='Daniel' && link.reviewed_date==='2026-11-13' && acceptedMethods.has(link.review_method)));
assert(rejected.length>0, 'drop decisions are retained as rejected records');
const synonymData=JSON.parse(fs.readFileSync(path.join(root,'data/nors_app_search_synonyms.json'),'utf8'));
assert.equal(synonymData.label,'Approved app guidance; expands Appendix PP search terms only.');
assert.deepEqual(synonymData.rules[0].match_any_trigger,['own','my own','bedside','self']);
assert.deepEqual(synonymData.rules[0].alongside_any_medication_term,['medication','medicine','pills','meds','inhaler']);
class Node {
  constructor(name) { this.name=name; this.children=[]; this.events={}; this.textContent=''; this.value=''; this.scrolls=0; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children=[...nodes]; this.textContent=''; }
  addEventListener(type, fn) { this.events[type]=fn; }
  scrollIntoView() { this.scrolls++; }
  querySelectorAll(name) { return this.children.flatMap(x => x instanceof Node ? [...(x.name === name ? [x] : []), ...x.querySelectorAll(name)] : []); }
}
const nodes = Object.fromEntries(['source-output','load-status','nors-code','ftag-code','nors-filter','ftag-filter','run-keyword-crosswalk','keyword-text'].map(id => [id,new Node(id)]));
const document = { getElementById: id=>nodes[id], createElement: name=>new Node(name), createTextNode: text=>({textContent:text}), addEventListener: (event,fn)=>{if(event==='DOMContentLoaded') document.init=fn;} };
const seen=[];
const windowEvents={};
let currentHash='';
const location={get hash(){return currentHash;},set hash(value){currentHash=value; windowEvents.hashchange?.();}};
async function fetch(file) {
  seen.push(file);
  if (file.includes('nors_reviewed_links')) {
    const target=path.join(root, file.replace(/^\.\.\//,''));
    return {ok:true,json:async()=>JSON.parse(fs.readFileSync(target,'utf8').replace(/^\uFEFF/,''))};
  }
  const target=path.join(root, file.replace(/^\.\.\//,''));
  return {ok:true,json:async()=>JSON.parse(fs.readFileSync(target,'utf8').replace(/^\uFEFF/,''))};
}
const context={document,fetch,history:{replaceState(){}},location,window:{addEventListener:(event,fn)=>{windowEvents[event]=fn;}},URLSearchParams,console,encodeURIComponent,Map,Set};
vm.runInNewContext(fs.readFileSync(path.join(root,'Assets/nors-crosswalk-page.js'),'utf8'),context);
const walk=node=>[node.textContent||'',...(node.children||[]).flatMap(walk)];
(async()=>{
  await document.init();
  assert(seen.length>0 && seen.every(file=>!/^https?:\/\//i.test(file)), 'source reads must stay same-origin');
  assert.equal(nodes['nors-code'].children.flatMap(x=>x.children).length,60);
  assert.equal(nodes['ftag-code'].children.flatMap(x=>x.children).length,204);
  const f917group=nodes['ftag-code'].children.find(group=>group.children.some(option=>option.value==='F917'));
  assert.equal(f917group.label,'Section not verified');
  nodes['ftag-filter'].value='F917'; nodes['ftag-filter'].events.input();
  assert.equal(f917group.children.find(option=>option.value==='F917').hidden,false);
  assert.equal(f917group.children.find(option=>option.value==='F918').hidden,true);
  nodes['nors-code'].value='D09'; nodes['nors-code'].events.change(); await new Promise(resolve=>setTimeout(resolve,0));
  let text=walk(nodes['source-output']).join(' ');
  assert(text.includes('D09 The deprivation')); assert(text.includes('F554 (coded_by_reviewer)'));
  assert.equal(location.hash,'#code=D09');
  const scrollBeforeOpen=nodes['source-output'].scrolls;
  nodes['ftag-code'].value='F554'; nodes['ftag-code'].events.change(); await new Promise(resolve=>setTimeout(resolve,0));
  text=walk(nodes['source-output']).join(' '); assert(text.includes('self-administer medications')); assert(text.includes('Regulation (42 CFR)'));
  for (const code of ['F04','D01','D09']) assert(text.includes(`${code} (`), `F554 should show reviewed ${code}`);
  assert(nodes['source-output'].scrolls > scrollBeforeOpen, 'opening a tag scrolls its card into view');
  assert(text.includes('Tag header: F554 — Rev. 232'));
  assert(!text.includes('draft') && !text.includes('proposed'), 'draft and proposed records must not render');
  for (const tag of ['F622','F623','F624','F625','F626']) {
    nodes['ftag-code'].value=tag; nodes['ftag-code'].events.change(); await new Promise(resolve=>setTimeout(resolve,0));
    text=walk(nodes['source-output']).join(' ');
    assert(text.includes('C03 (coded_by_reviewer)'), `${tag} tag card should show reviewed C03`);
  }
  nodes['ftag-code'].value='F660'; nodes['ftag-code'].events.change(); await new Promise(resolve=>setTimeout(resolve,0));
  text=walk(nodes['source-output']).join(' ');
  assert(text.includes('D02 (coded_by_reviewer; weak — title-only, check)'), 'F660 tag card should show reviewed D02 with its weak title-only check label');
  assert(text.includes('weak — title-only, check'), 'F660 D02 should be visibly marked weak and title-only');
  assert(!text.includes('C03 (coded_by_reviewer)'), 'undecided F660 to C03 must stay out');
  nodes['ftag-code'].value='F646'; nodes['ftag-code'].events.change(); await new Promise(resolve=>setTimeout(resolve,0));
  text=walk(nodes['source-output']).join(' ');
  assert(text.includes('F03 (coded_by_reviewer; weak — title-only, check)'), 'approved manual F646/F03 should display as a weak checked context link');
  for (const [tag, codes] of Object.entries({F620:['C02','C03','C04'],F621:['C02','C03','C04'],F627:['C01','C04'],F628:['D02','C04','C01']})) {
    nodes['ftag-code'].value=tag; nodes['ftag-code'].events.change(); await new Promise(resolve=>setTimeout(resolve,0));
    text=walk(nodes['source-output']).join(' ');
    for (const code of codes) assert(!text.includes(`${code} (`), `${tag} must not show dropped ${code}`);
  }
  nodes['ftag-code'].value='F554'; nodes['ftag-code'].events.change(); await new Promise(resolve=>setTimeout(resolve,0));
  nodes['source-output'].querySelectorAll('button').find(button=>button.textContent.startsWith('D09 ')).events.click();
  assert(walk(nodes['source-output']).join(' ').includes('NORS D09'), 'related-code link opens its selected card');
  assert.equal(location.hash,'#code=D09');
  nodes['source-output'].querySelectorAll('button').find(button=>button.textContent.startsWith('F554 ')).events.click();
  await new Promise(resolve=>setTimeout(resolve,0));
  assert(walk(nodes['source-output']).join(' ').includes('Tag header: F554'), 'related-tag link opens its selected card');
  async function searchAndCheckFirstTag(query) {
    const scrollBefore=nodes['source-output'].scrolls;
    nodes['keyword-text'].value=query; await nodes['run-keyword-crosswalk'].events.click();
    const outputText=walk(nodes['source-output']).join(' ');
    assert(outputText.includes('NORS definitions with matching words'));
    assert(outputText.includes('Appendix PP tags with matching words'));
    const appendixHeading=nodes['source-output'].children.findIndex(child=>child.textContent==='Appendix PP tags with matching words');
    const firstTag=nodes['source-output'].children.slice(appendixHeading+1).find(child=>child.name==='div');
    assert(firstTag && walk(firstTag).join(' ').trim().startsWith('F554'), `${query} should return F554 as first Appendix PP result; got ${firstTag ? walk(firstTag).join(' ').slice(0,80) : 'none'}`);
    for (const code of ['F04','D01','D09']) assert(walk(firstTag).join(' ').includes(code), `search shows reviewed ${code} as context`);
    const norsResults=outputText.split('Appendix PP tags with matching words')[0];
    assert(!norsResults.includes('Matched: self-administer'), 'app synonym does not alter NORS matching or ranking');
    assert(nodes['source-output'].scrolls > scrollBefore, 'search scrolls results into view');
    return outputText;
  }
  text=await searchAndCheckFirstTag('keep my own medications');
  assert.equal(location.hash,'#search=keep%20my%20own%20medications');
  await searchAndCheckFirstTag('resident wants to take her own pills');
  await searchAndCheckFirstTag('can I keep my own medicine at bedside');
  currentHash='#tag=F554'; windowEvents.popstate?.(); await new Promise(resolve=>setTimeout(resolve,0));
  assert(walk(nodes['source-output']).join(' ').includes('Tag header: F554'), 'forward navigation restores the tag card');
  currentHash='#code=D09'; windowEvents.popstate?.();
  assert(walk(nodes['source-output']).join(' ').includes('NORS D09'), 'history navigation restores prior card');
  const html=fs.readFileSync(path.join(root,'tools/nors-crosswalk.html'),'utf8');
  assert(!html.includes('id="open-ftag"') && !html.includes('id="run-nors-crosswalk"'), 'selection opens without a separate button');
  assert(seen.every(x=>!x.includes('draft')));
  assert(!/\b(?:localStorage|sessionStorage)\b/.test(fs.readFileSync(path.join(root,'Assets/nors-crosswalk-page.js'),'utf8')));
  console.log('Source UI checks passed: approved triage, synonyms, result scrolling, hash navigation, and open-on-select.');
})().catch(error=>{console.error(error);process.exitCode=1;});
