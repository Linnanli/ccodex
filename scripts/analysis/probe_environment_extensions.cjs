/* Isolated replay of selected frozen first-party units. No host, filesystem,
 * account, model or backend requests are issued by the replayed units. */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const root = process.argv[2];
const work = path.join(root, '.analysis-local/settings-operation-batch-04');
const loaded = [];
function source(dir, name) {
  const d = path.join(work, dir);
  const contract = JSON.parse(fs.readFileSync(path.join(d, 'source-contracts.json')));
  const unit = contract.units.find(u => u.name === name);
  assert(unit, `${dir}:${name}`);
  const data = fs.readFileSync(path.join(d, unit.sourceFilename));
  assert.equal(crypto.createHash('sha256').update(data).digest('hex'), unit.spanHash);
  loaded.push({ directory: dir, name, ...unit });
  return data.toString();
}
function context(extra = {}) { return vm.createContext({ URLSearchParams, ...extra }); }
function evaluate(ctx, dir, names) {
  for (const name of names) vm.runInContext(source(dir, name), ctx, { timeout: 1000 });
}
const plain = v => JSON.parse(JSON.stringify(v));
const results = [];
async function check(id, fn) {
  await fn();
  results.push({ id, status: 'passed', scope: 'isolated-source-replay' });
}
(async () => {
  const hooks = context();
  evaluate(hooks, 'hooks-model-01', ['o','c','u','a','t','i','s','p','x','S','m','g','h','d','b','_','v','y','assignment-C','assignment-w']);
  const hook = (key, extra = {}) => ({ key, eventName: 'SessionStart', source: 'user', enabled: true, trustStatus: 'trusted', ...extra });
  await check('HOOK-MODEL-01', () => assert.equal(hooks.u(hook('x', { trustStatus: 'modified' })), true));
  await check('HOOK-MODEL-02', () => assert.equal(hooks.x(hook('x', { trustStatus: 'managed', enabled: false })), true));
  await check('HOOK-MODEL-03', () => assert.equal(hooks.x(hook('x', { trustStatus: 'untrusted' })), false));
  await check('HOOK-MODEL-04', () => assert.equal(hooks.d('cloudManagedConfig'), 'admin'));
  await check('HOOK-MODEL-05', () => assert.deepEqual(plain(hooks.i(['/z','/a','/z'], ['/b','/b'], '/x')), ['/b','/a','/z','/x']));
  await check('HOOK-MODEL-06', () => assert.deepEqual(plain(hooks.s({source:null,projectRoot:'/p',projectRoots:['/p']})), {source:'project',projectRoot:'/p'}));
  await check('HOOK-MODEL-07', () => assert.equal(hooks.s({source:'project',projectRoot:'/p',projectRoots:[]}), null));
  await check('HOOK-MODEL-08', () => assert.deepEqual(plain(hooks.s({source:'plugin',pluginId:'__unknown__'})), {source:'plugin',pluginId:null}));
  await check('HOOK-MODEL-09', () => assert.deepEqual(plain(hooks.a({hooks:[hook('a'),hook('b',{trustStatus:'untrusted'})],warnings:['w'],errors:[{}]})), {issueCount:2,needsReview:1}));
  await check('HOOK-MODEL-10', () => assert.deepEqual(plain(hooks.v([hook('x'),hook('x',{enabled:false})])).map(h => h.enabled), [true]));
  await check('HOOK-MODEL-11', () => assert.equal(hooks.y([{path:'p',message:'m'},{path:'p',message:'m'}]).length, 1));
  await check('HOOK-MODEL-12', () => assert.deepEqual(plain(hooks.o([{cwd:'/p',hooks:[hook('a',{source:'project'}),hook('b',{source:'user'})],warnings:[],errors:[]}])).map(e=>e.id), ['user','project']));
  const route = context(); evaluate(route, 'hooks-route-01', ['i']);
  await check('HOOK-ROUTE-01', () => { const p = new URLSearchParams('keep=1&hostId=old&pluginId=old&source=plugin&projectRoot=old');route.i(p,'h',null);assert.equal(p.toString(),'keep=1'); });
  await check('HOOK-ROUTE-02', () => { const p = new URLSearchParams('keep=1');route.i(p,'h',{source:'plugin',pluginId:null});assert.equal(p.get('pluginId'),'__unknown__');assert.equal(p.get('hostId'),'h'); });
  await check('HOOK-ROUTE-03', () => { const p = new URLSearchParams();route.i(p,'h',{source:'project',projectRoot:'/p'});assert.equal(p.get('projectRoot'),'/p');assert.equal(p.has('pluginId'),false); });
  let requests = [], invalidations = [];
  const provider = context({ q:{}, scope:{}, Cqt:['hooks'], Qg:{FIVE_MINUTES:300000},
    Ba:(_,f)=>(h)=>f(h,{scope:{}}), kl:(_,f)=>f,
    jg:(_,h)=>({sendRequest:async(method,params)=>{requests.push({h,method,params:plain(params)});return {status: provider.replyStatus ?? 'ok'};}}),
    Qi:k=>invalidations.push(['broadcast',plain(k)]), xqt:()=>false, Sqt:e=>e });
  evaluate(provider,'hooks-provider-01',['bqt','assignment-Tqt','assignment-wqt','assignment-Eqt']);
  await check('HOOK-PROVIDER-01', async()=> { const q = provider.wqt({hostId:'h',cwds:[]},{scope:{}});assert.equal(q.enabled,false);assert.throws(()=>q.queryFn(),/Cannot list hooks/); });
  await check('HOOK-PROVIDER-02', async()=> { await provider.wqt({hostId:'h',cwds:['/p']},{scope:{}}).queryFn();assert.deepEqual(requests.at(-1),{h:'h',method:'hooks/list',params:{cwds:['/p']}}); });
  await check('HOOK-PROVIDER-03', async()=> { await provider.Eqt('h').mutationFn([{key:'a.b"c',enabled:false,trustedHash:'hash'}]);const r=requests.at(-1);assert.equal(r.method,'config/batchWrite');assert.deepEqual(r.params.edits.map(e=>e.keyPath),['hooks.state."a.b\\"c".enabled','hooks.state."a.b\\"c".trusted_hash']);assert.equal(r.params.reloadUserConfig,true);assert.equal(r.params.expectedVersion,null); });
  await check('HOOK-PROVIDER-04', async()=> {provider.replyStatus='okOverridden';await assert.rejects(provider.Eqt('h').mutationFn([{key:'k',enabled:true}]),/overridden/);provider.replyStatus='ok';});
  await check('HOOK-PROVIDER-05', ()=> { const writes=[];provider.Eqt('h').onError(null,[],{previousResponses:[[['k'],{old:1}]]},{client:{setQueryData:(...a)=>writes.push(plain(a))}});assert.deepEqual(writes,[[['k'],{old:1}]]); });
  await check('HOOK-PROVIDER-06',async()=> { await provider.bqt({invalidateQueries:async o=>{assert.equal(o.predicate({queryKey:['hooks','h',['/p']]}),true);assert.equal(o.predicate({queryKey:['hooks','other']}),false);invalidations.push(['invalidate']);}},'h',{broadcast:true,refetchType:'none'});assert.deepEqual(invalidations.slice(-2),[['invalidate'],['broadcast',['hooks']]]); });
  let effects = [], response = {type:'success',configPath:'/new'}, selection = true;
  const env = context({fe:{localEnvironments:{saveConfig:async p=>{effects.push(['save',plain(p)]);return response;}}},je:async(...args)=>{effects.push(['invalidate',args.slice(1)]);},ot:()=> 'SYNTHETIC_TOML'});
  evaluate(env,'local-editor-01',['it','Rt','gt','ht','J']);
  const draft={name:' env ',actions:[]};
  const save=()=>env.ht({configPath:'/old',draft,expectedRevision:'rev1',hostId:'h',queryClient:{},selectEnvironment:async p=>{effects.push(['select',p]);return selection;},version:1,workspaceRoot:'/p'});
  await check('ENV-01',()=>assert.equal(env.it('  ',[]).missingName,true));
  await check('ENV-02',()=>assert.deepEqual(plain(env.it('a',[{id:'blank',name:'',command:''},{id:'bad',name:'x',command:''}])).incompleteActionIds,['bad']));
  await check('ENV-03',()=>assert.equal(env.Rt({isSaving:true,isSelectionReady:false,readError:true,validation:{}}),'saving'));
  await check('ENV-04',()=>assert.equal(env.Rt({isSaving:false,isSelectionReady:false,selectionError:true,validation:{}}),'project-error'));
  await check('ENV-05',async()=>{assert.equal(await env.gt({codexWorktree:true,configPath:'p',gitRoot:null,selectForWorktree:()=>{throw Error('unexpected');}}),false);});
  await check('ENV-06',async()=>{let got;assert.equal(await env.gt({codexWorktree:false,configPath:'p',selectForWorkspace:p=>got=p}),true);assert.equal(got,'p');});
  await check('ENV-07',async()=>{effects=[];assert.equal((await save()).type,'success');assert.deepEqual(effects.map(e=>e[0]),['save','invalidate','select']);assert.equal(effects[0][1].expectedRevision,'rev1');});
  await check('ENV-08',async()=>{selection=false;assert.equal((await save()).type,'selection-failed');selection=true;});
  await check('ENV-09',async()=>{response={type:'conflict',configPath:'/new'};effects=[];assert.equal((await save()).type,'conflict');assert.deepEqual(effects.map(e=>e[0]),['save','invalidate']);response={type:'success',configPath:'/new'};});
  await check('ENV-10',async()=>{const before=effects.length;assert.equal((await env.ht({draft:{name:'',actions:[]}})).type,'invalid');assert.equal(effects.length,before);});
  await check('ENV-11',()=>assert.equal(env.J('a\r\nb'),"'''\na\nb'''"));
  const mcp = context();evaluate(mcp,'mcp-content-01',['Sa','aa','oa','sa','ca']);
  await check('MCP-01',()=>assert.equal(mcp.Sa(' A !! B ',['a_-_b','a_-_b-2']),'a_-_b-3'));
  await check('MCP-02',()=>assert.equal(mcp.Sa('你好',[]),'-'));
  await check('MCP-02b',()=>assert.equal(mcp.Sa('   ',[]),'custom-server'));
  await check('MCP-03',()=>{const d=mcp.aa({command:'run',args:[' a ',''],env:{K:'V'},startup_timeout_sec:10},'key');const c=plain(mcp.oa(d));assert.equal(c.startup_timeout_sec,10);assert.deepEqual(c.args,['a']);assert.equal(c.command,'run');assert.equal('url' in c,false);});
  await check('MCP-04',()=>{const d=mcp.aa({url:'https://fixture.invalid/mcp',oauth:{client_id:'synthetic'},enabled:false},'http');const c=plain(mcp.oa(d));assert.deepEqual(c.oauth,{client_id:'synthetic'});assert.equal(c.enabled,false);assert.equal('command' in c,false);});
  await check('MCP-05',()=>assert.deepEqual(plain(mcp.ca([{key:' K ',value:' first '},{key:'K',value:'last'},{key:'',value:'v'}])),{K:'last'}));
  let sent=[];
  const query={};
  const mcpProvider=context({Kq:{c:n=>Array(n).fill(Symbol.for('react.memo_cache_sentinel'))},X:{},hA:()=>({}),JG:()=>async()=>{},LP:()=>query,GP:o=>o,Yjn:()=>{},Qjn:async()=>{},qq:['mcp-config'],Yq:['config'],zf:{info:()=>{},error:()=>{}},KI:(_,h)=>({sendRequest:async(method,params)=>{sent.push({h,method,params:plain(params)});return{};}})});
  evaluate(mcpProvider,'mcp-provider-01',['Jjn','Xjn']);
  await check('MCP-PROVIDER-01',async()=>{await mcpProvider.Jjn({hostId:'h'}).mutationFn({filePath:'/fixture/config.toml',key:'server',value:{command:'run'}});assert.deepEqual(sent.at(-1),{h:'h',method:'config/batchWrite',params:{edits:[{keyPath:'mcp_servers.server',value:{command:'run'},mergeStrategy:'replace'}],filePath:'/fixture/config.toml',expectedVersion:null}});});
  await check('MCP-PROVIDER-02',async()=>{await mcpProvider.Xjn({hostId:'h'}).mutationFn({key:'server',enabled:false});assert.deepEqual(sent.at(-1).params,{keyPath:'mcp_servers.server.enabled',value:false,mergeStrategy:'upsert',filePath:null,expectedVersion:null});});
  await check('MCP-PROVIDER-03',async()=>{await mcpProvider.Jjn({hostId:'h'}).mutationFn({filePath:'/fixture/config.toml',key:'server',value:null});assert.equal(sent.at(-1).params.edits[0].value,null);});
  const output={baselineId:'codex-26.1007.30912-c5b273322a83',cases:results,passed:results.length,failed:0,loadedUnits:loaded,boundaries:'Original saved first-party units replayed with synthetic query, serializer, host and RPC substitutes. No real configuration files, OAuth, hooks or processes executed.',actualProductScenariosExecuted:0,modelSubmissionsAdded:0,originalClientRunsAdded:0};
  fs.writeFileSync(path.join(work,'isolated-observations.json'),JSON.stringify(output,null,2)+'\n');
  process.stdout.write(JSON.stringify({passed:results.length,failed:0,actualProductScenariosExecuted:0})+'\n');
})().catch(e=>{process.stderr.write(e.stack+'\n');process.exitCode=1;});
