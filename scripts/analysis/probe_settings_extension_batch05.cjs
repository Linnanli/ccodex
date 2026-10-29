// Execute selected frozen helper bodies with synthetic state only. No application imports.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const root = process.cwd();
const work = path.join(root, '.analysis-local/settings-extension-batch05-work');
const selected = path.join(work, 'connections');
const metadata = JSON.parse(fs.readFileSync(path.join(selected, 'source-contracts.json')));
const names = ['Ms', 'Ns', 'Ps', 'Fs', 'cs', 'js', 'us'];
const units = names.map(name => metadata.units.find(u => u.name === name));
const source = units.map(u => {
  const b = fs.readFileSync(path.join(selected, u.sourceFilename));
  assert.equal(crypto.createHash('sha256').update(b).digest('hex'), u.spanHash);
  return b.toString('utf8');
}).join('\n');
const context = vm.createContext({URLSearchParams, _e: 'state', j: 'error'});
vm.runInContext(source, context, {timeout: 1000});
const rows = [];
const plain = value => JSON.parse(JSON.stringify(value));
async function check(id, fn) {
  await fn(); rows.push({id, passed: true});
}
(async () => {
  await check('ROUTE-ALIASES', () => assert.deepEqual(['computer','devices','ssh','wsl'].map(context.Ms), ['control-this-mac','access-other-devices','ssh','wsl']));
  await check('ROUTE-UNKNOWN', () => { for (const x of [undefined,null,'','other']) assert.equal(context.Ms(x), null); });
  await check('ROUTE-PATHS', () => assert.deepEqual(['control-this-mac','access-other-devices','ssh','wsl'].map(context.Ns), ['/settings/connections/computer','/settings/connections/devices','/settings/connections/ssh','/settings/connections/wsl']));
  await check('SSH-NAME-TRIM', () => assert.equal(context.Ps({routeAction:'add',routeSlug:'ssh',search:'?name=%20fixture%20&alias=other'}), 'fixture'));
  await check('SSH-ALIAS-FALLBACK', () => assert.equal(context.Ps({routeAction:'add',routeSlug:'ssh',search:'?alias=%20fixture%20'}), 'fixture'));
  await check('SSH-BLANK-NAME-BLOCKS-ALIAS', () => assert.equal(context.Ps({routeAction:'add',routeSlug:'ssh',search:'?name=%20&alias=fixture'}), null));
  await check('SSH-NONADD-GUARD', () => { for(const [routeSlug,routeAction] of [['wsl','add'],['ssh',undefined],['ssh','edit']]) assert.equal(context.Ps({routeSlug,routeAction,search:'?name=fixture'}),null); });
  await check('REMOTE-ONLINE-FIRST', () => assert.deepEqual(plain(context.Fs([{displayName:'A',online:false},{displayName:'Z',online:true}])).map(x=>x.displayName),['Z','A']));
  await check('REMOTE-LASTSEEN-AND-NONMUTATION', () => { const input=[{displayName:'A',online:false,lastSeenAt:null},{displayName:'B',online:false,lastSeenAt:'2026-01-01'},{displayName:'C',online:false,lastSeenAt:'2026-02-01'}]; assert.deepEqual(plain(context.Fs(input)).map(x=>x.displayName),['C','B','A']);assert.equal(input[0].displayName,'A'); });
  await check('REMOTE-ONLINE-NAME-ORDER', () => assert.deepEqual(plain(context.Fs([{displayName:'Z',online:true,lastSeenAt:'2026-02-01'},{displayName:'A',online:true,lastSeenAt:'2026-01-01'}])).map(x=>x.displayName),['A','Z']));
  await check('REMOTE-AUTH-SETUP-GUARD', () => { for(const [authorized,authRequired,show,expected] of [[false,false,true,true],[true,false,true,false],[false,true,true,false],[false,false,false,false]]) assert.equal(context.cs({remoteControlConnectionsAuthorized:authorized,remoteControlConnectionsAuthRequired:authRequired,showRemoteControlConnectionsSection:show}),expected); });
  await check('SSH-WAIT-PREABORT', async () => {const c=new AbortController();c.abort();let watched=false;assert.equal(await context.us({watch(){watched=true;}},'fixture',c.signal,()=>{}),false);assert.equal(watched,false);});
  await check('SSH-WAIT-CONNECTED-CLEANUP', async () => {const c=new AbortController();let callback,stopped=0;const p=context.us({watch(fn){callback=fn;return()=>stopped++;}},'fixture',c.signal,()=>{});callback({get:key=>key==='state'?'connected':null});assert.equal(await p,true);assert.equal(stopped,1);});
  await check('SSH-WAIT-LOGIN-THEN-ABORT', async () => {const c=new AbortController();let callback,stopped=0,login=0;const p=context.us({watch(fn){callback=fn;return()=>stopped++;}},'fixture',c.signal,()=>login++);callback({get:key=>key==='error'?{code:'login-required'}:'error'});c.abort();assert.equal(await p,false);assert.equal(login,1);assert.equal(stopped,1);});
  const result={baselineId:metadata.baselineId,sourceUnits:units,method:'Exact selected helper bodies in isolated VM with synthetic route/connection/watch state; all imported and native receivers excluded.',cases:rows,passed:rows.length,failed:0,productScenariosExecuted:0,modelSubmissionsAdded:0,originalClientRunsAdded:0,livePreferencesChanged:0};
  fs.writeFileSync(path.join(work,'isolated-observations.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
  process.stdout.write(JSON.stringify({passed:rows.length,failed:0,productScenariosExecuted:0})+'\n');
})().catch(error=>{process.stderr.write(error.stack+'\n');process.exitCode=1;});
