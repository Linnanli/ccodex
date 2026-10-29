/* Selected first-party helper replay with synthetic cache/RPC/origin functions. */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const work = path.join(process.argv[2], '.analysis-local/environment-extension-reconciliation');
const c = JSON.parse(fs.readFileSync(path.join(work, 'source-contracts.json')));
const plain = v => JSON.parse(JSON.stringify(v));
const calls = [], cases = [];
const empty = {config:{},origins:{},layers:[]};
const ctx = vm.createContext({structuredClone, Yq:['layered'], qq:['mcp-config'], Xq:['mcp-status'],
  EW:{FIVE_MINUTES:300000}, dMn:empty,
  Wq:async(...a)=>{calls.push(['load',a]);if(ctx.failLoad)throw Error('synthetic read error');return ctx.reply;},
  zf:{error:()=>calls.push(['log'])},
  oMn:v=>v.mcp_servers,
  iMn:v=>{calls.push(['target',plain(v)]);return {filePath:'/synthetic/config.toml'};},
  aMn:v=>{calls.push(['origins',plain(v)]);return {s:{name:{type:'project'}}};},
  eMn:(servers,key,value)=>servers==null||servers[key]==null?null:{...servers,[key]:{...servers[key],enabled:value}}
});
for(const u of c.units){
  const b=fs.readFileSync(path.join(work,u.sourceFilename));
  assert.equal(crypto.createHash('sha256').update(b).digest('hex'),u.spanHash);
  vm.runInContext(b.toString(),ctx,{timeout:1000});
}
async function check(id,f){await f();cases.push({id,status:'passed',scope:'isolated-source-replay'});}
(async()=>{
  const cached={config:{mcp_servers:{cached:{command:'synthetic'}}}};
  let cache=cached, opts;
  const query={fetchQuery:async o=>{opts=o;return o.queryFn();},getQueryData:k=>{assert.deepEqual(plain(k),['layered','h','/p']);return cache;}};
  ctx.reply={config:{mcp_servers:{live:{command:'synthetic'}}}};
  await check('MCP-READ-01',async()=>{assert.equal(await ctx.Hjn({},query,'h','/p'),ctx.reply);assert.deepEqual(plain(opts.queryKey),['layered','h','/p']);assert.equal(opts.staleTime,300000);assert.equal(calls.at(-1)[1][4],true);});
  await check('MCP-READ-02',async()=>{ctx.failLoad=true;assert.equal(await ctx.Hjn({},query,'h','/p'),cached);});
  await check('MCP-READ-03',async()=>{cache=undefined;assert.equal(await ctx.Hjn({},query,'h','/p'),empty);});
  await check('MCP-READ-04',()=>{calls.length=0;const servers={s:{command:'synthetic'}};const r=ctx.Rjn({config:{mcp_servers:servers},origins:{o:1},layers:['layer']});assert.equal(r.servers,servers);assert.deepEqual(calls.map(x=>x[0]),['target','origins']);assert.equal(calls[0][1].keyPath,'mcp_servers');assert.deepEqual(calls[1][1].probeFields,['enabled','command','url']);});
  await check('MCP-INVALIDATE-01',async()=>{const seen=[];await ctx.Qjn('h',async k=>seen.push(plain(k)));assert.deepEqual(seen,[['layered','h'],['mcp-config','h'],['mcp-status','h']]);});
  await check('MCP-INVALIDATE-02',async()=>{const seen=[];await assert.rejects(ctx.Qjn('h',async k=>{seen.push(plain(k));throw Error('synthetic');}),/synthetic/);assert.deepEqual(seen,[['layered','h']]);});
  await check('MCP-SNAPSHOT-01',()=>{const r=ctx.Zjn({getQueriesData:()=>[[['a'],null],[['b'],undefined],[['c'],false],[['d'],{x:1}]]},[]);assert.deepEqual(plain(r),[[['c'],false],[['d'],{x:1}]]);});
  await check('MCP-OPTIMISTIC-01',()=>{const old={config:{mcpServers:{s:{enabled:true}},other:{x:1}},origins:{o:1}};const r=ctx.$jn(old,'s',false);assert.equal(r.config.mcpServers.s.enabled,false);assert.equal(old.config.mcpServers.s.enabled,true);assert.notEqual(r.config,old.config);assert.notEqual(r.config.other,old.config.other);assert.equal(r.origins,old.origins);});
  await check('MCP-OPTIMISTIC-02',()=>{const old={config:{mcp_servers:{s:{enabled:true}},mcpServers:{legacy:{}}}};const r=ctx.$jn(old,'s',false);assert.equal(r.config.mcp_servers.s.enabled,false);assert.deepEqual(plain(r.config.mcpServers),{legacy:{}});});
  await check('MCP-OPTIMISTIC-03',()=>{const old={config:{mcp_servers:{s:{}}}};assert.equal(ctx.$jn(old,'absent',false),old);});
  const result={baselineId:c.baselineId,cases,passed:cases.length,failed:0,sourceSelection:c,
    qualification:'Synthetic Wq, caches, config normalization, write-target/origin helpers and eMn; their real implementations and live receiver are not proved.',
    productScenariosExecuted:0,modelSubmissionsAdded:0,originalClientRunsAdded:0,actualConfigurationWrites:0};
  fs.writeFileSync(path.join(work,'isolated-observations.json'),JSON.stringify(result,null,2)+'\n');
  process.stdout.write(JSON.stringify({passed:cases.length,failed:0,productScenariosExecuted:0})+'\n');
})().catch(e=>{process.stderr.write(e.stack+'\n');process.exitCode=1;});
