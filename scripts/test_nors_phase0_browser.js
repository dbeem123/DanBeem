// Runs the Phase 0 browser harness twice in Microsoft Edge without installing dependencies.
// Start the repository's local static server first, then: node scripts/test_nors_phase0_browser.js http://127.0.0.1:8876 <edge.exe>
const assert=require('node:assert/strict');
const {spawnSync}=require('node:child_process');
const base=process.argv[2]||'http://127.0.0.1:8876';
const edge=process.argv[3]||'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
for(let run=1;run<=2;run++){
 const profile=require('node:path').resolve(`.nors-phase0-edge-profile-${process.pid}-${run}`);
 const dirs=['Roaming','Local','Home','Temp'].map(x=>require('node:path').join(profile,x));for(const dir of dirs)require('node:fs').mkdirSync(dir,{recursive:true});
 const env={...process.env,APPDATA:dirs[0],LOCALAPPDATA:dirs[1],USERPROFILE:dirs[2],TEMP:dirs[3],TMP:dirs[3]};
 const result=spawnSync(edge,['--headless=new','--disable-gpu','--disable-crash-reporter','--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update','--virtual-time-budget=30000','--dump-dom',`--user-data-dir=${require('node:path').join(profile,'EdgeData')}`,`${base}/scripts/test_nors_phase0_harness.html`],{encoding:'utf8',timeout:60000,maxBuffer:8*1024*1024,windowsHide:true,env});
 try{
  assert.equal(result.status,0,`Edge run ${run} failed: ${result.error?.message||result.stderr}`);
  assert.ok(result.stdout.includes('PASS complete: 4 pages at desktop and mobile sizes'),`Edge run ${run} did not report success. ${result.stdout.slice(-2000)} ${result.stderr}`);
  assert.ok(!result.stdout.includes('FAILURES'),`Edge run ${run} reported a failing browser assertion.`);
  console.log(`PASS Edge presentation/privacy run ${run}: 8 page-size combinations; synthetic workflow, warning, URL, CSP, request-origin and overflow checks.`);
 } finally {
  try{require('node:fs').rmSync(profile,{recursive:true,force:true});}catch{}
 }
}
