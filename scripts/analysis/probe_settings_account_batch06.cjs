// Exact frozen helper/callback replay. Synthetic receivers only; no application imports.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=process.cwd(),base='codex-26.1007.30912-c5b273322a83';
const work=path.join(root,'.analysis-local/settings-account-batch06-work');
const frozen=path.join(root,'.analysis-local/baselines',base,'extracted');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const meta=Object.fromEntries(['usage','billing','teams'].map(n=>[n,JSON.parse(fs.readFileSync(path.join(work,n,'source-contracts.json')))]));
const used=[];
function exact(page,record){
  const b=fs.readFileSync(path.join(frozen,record.sourcePath.replace(/^app.asar\//,'')));
  assert.equal(sha(b),record.sourceHash);
  const s=b.subarray(record.byteRange.start,record.byteRange.endExclusive);
  assert.equal(sha(s),record.spanHash);used.push({page,...record});return s.toString();
}
function unit(page,name,context){const u=meta[page].units.find(x=>x.name===name);assert(u);return vm.runInNewContext(`(${exact(page,u)})`,context,{timeout:1000});}
function callback(page,name,predicate,context){
  const found=meta[page].callbacks.filter(x=>x.unit===name).filter(x=>predicate(exact(page,x)));
  assert.equal(found.length,1);return vm.runInNewContext(`(${exact(page,found[0])})`,context,{timeout:1000});
}
const plain=x=>JSON.parse(JSON.stringify(x)),cases=[];
async function check(id,fn){await fn();cases.push({id,passed:true});}
class SyntheticHttpError extends Error {constructor(status){super(`synthetic-${status}`);this.status=status;}}
(async()=>{
  const history=(get)=>unit('usage','$l',{ge:{safeGet:get},i:SyntheticHttpError,ft:{FIVE_MINUTES:300000}});
  const identity={accountId:'fixture-account',userId:'fixture-user',authMethod:'chatgpt'};
  await check('HISTORY-IDENTITY-AND-RETRY',()=>{const q=history(()=>{})(identity,300);assert.equal(q.enabled,true);assert.deepEqual(plain(q.queryKey),['plan-limit-balance-history','fixture-account','fixture-user',300]);assert.equal(q.retry(0,new SyntheticHttpError(409)),true);assert.equal(q.retry(1,new SyntheticHttpError(409)),false);assert.equal(q.retry(0,new SyntheticHttpError(404)),false);assert.equal(history(()=>{})({...identity,authMethod:'apiKey'},300).enabled,false);});
  await check('HISTORY-CURSOR-ACCUMULATION',async()=>{const calls=[];const q=history(async(url,opts)=>{calls.push({url,cursor:opts.parameters.query.cursor});return calls.length===1?{points:[1],next_cursor:'fixture-cursor'}:{points:[2],next_cursor:null};})(identity,300);assert.deepEqual(plain(await q.queryFn({signal:new AbortController().signal})),{points:[1,2],next_cursor:null});assert.deepEqual(calls.map(x=>x.cursor),[undefined,'fixture-cursor']);assert(calls.every(x=>x.url==='/wham/usage/plan_limit_balance_history'));});
  await check('HISTORY-404-UNAVAILABLE',async()=>{assert.equal(await history(async()=>{throw new SyntheticHttpError(404);})(identity,300).queryFn({signal:new AbortController().signal}),null);});
  await check('HISTORY-409-PROPAGATES',async()=>{await assert.rejects(history(async()=>{throw new SyntheticHttpError(409);})(identity,300).queryFn({signal:new AbortController().signal}),e=>e.status===409);});
  await check('HISTORY-ABORT-BETWEEN-PAGES',async()=>{const c=new AbortController();let calls=0;const q=history(async()=>{calls++;c.abort();return{points:[],next_cursor:'more'};})(identity,300);await assert.rejects(q.queryFn({signal:c.signal}),e=>e.name==='AbortError');assert.equal(calls,1);});
  const mandate=unit('billing','lr',{});
  const terms={original_payment_method_id:'method',client_secret:'synthetic-secret',publishable_key:'synthetic-key',processor_entity:'processor',mandate_terms:{amount:100,currency:'USD',amount_type:'fixed',interval:'month',interval_count:1}};
  await check('MANDATE-IDENTICAL-CONSENT',()=>assert.equal(mandate(terms,plain(terms)),true));
  await check('MANDATE-CHANGED-IDENTITY-OR-TERMS',()=>{for(const key of ['original_payment_method_id','client_secret','publishable_key','processor_entity'])assert.equal(mandate(terms,{...terms,[key]:'changed'}),false);for(const key of Object.keys(terms.mandate_terms))assert.equal(mandate(terms,{...terms,mandate_terms:{...terms.mandate_terms,[key]:'changed'}}),false);});
  const reconcile=unit('billing','kr',{He:plan=>plan==='fixture-paid',Lt:plan=>`subscription:${plan}`});
  const trial={account:{plan_type:'free'},entitlement:{subscription_plan:'chatgptplus_no_payment_trial',is_eligible_for_cp:true}};
  await check('TRIAL-UNRESOLVED-VERSUS-NO-REFRESH',()=>{assert.equal(reconcile(trial,undefined),null);assert.equal(reconcile(trial,null),trial);});
  await check('TRIAL-MISMATCHED-SUBSCRIPTION',()=>assert.equal(reconcile(trial,{id:'a',entitlement:{subscription_id:'b'},last_active_subscription:{subscription_id:'a'}}),null));
  await check('TRIAL-VALID-PAID-RECONCILIATION',()=>{const active={id:'a',plan_type:'fixture-paid',entitlement:{subscription_id:'a',subscription_plan:'subscription:fixture-paid',has_active_subscription:true,is_active_subscription_gratis:false},last_active_subscription:{subscription_id:'a',purchase_origin_platform:'chatgpt_web'}};const r=reconcile(trial,active);assert.equal(r.account.plan_type,'fixture-paid');assert.equal(r.entitlement.is_eligible_for_cp,true);assert.equal(trial.account.plan_type,'free');});
  await check('TRANSACTION-QUERY-PAYLOAD',async()=>{let got;const fn=unit('billing','Vr',{Ne:x=>x,oe:{safeGet:(url,opts)=>{got={url,opts};return'fixture';}}});const q=fn('fixture-account',10,'cursor');const signal=new AbortController().signal;assert.equal(await q.queryFn({signal}),'fixture');assert.equal(got.url,'/payments/transaction-history');assert.deepEqual(plain(got.opts.parameters.query),{account_id:'fixture-account',limit:10,cursor:'cursor'});assert.equal(got.opts.signal,signal);assert.equal(q.gcTime,0);assert.equal(q.retry,false);});
  const visible=unit('teams','Mr',{});
  await check('TEAM-DEFAULT-SERVICE-USER-HIDDEN',()=>{assert.equal(visible({principal_type:'user',principal_id:'svc'},'account','svc__account'),false);assert.equal(visible({principal_type:'user',principal_id:'human'},'account','svc__account'),true);assert.equal(visible({principal_type:'group',principal_id:'svc'},'account','svc__account'),true);});
  function editor({draft=' New ',field='name',saved='Old',pending=false,error}={}){
    const effects=[],guard={current:pending};
    const context={d:draft,y:guard,i:field,S:saved,n:'fixture-account',r:{id:'fixture-team'},T:'update',o:SyntheticHttpError,
      a:{get:key=>{assert.equal(key,'update');return{mutateAsync:async value=>{effects.push(['write',plain(value)]);if(error)throw new SyntheticHttpError(error);}};}},
      s:{formatMessage:value=>typeof value==='string'?value:value.id},G:{saveError:'save-error',nameConflict:'name-conflict',saveForbidden:'forbidden'},
      g:value=>effects.push(['error',value]),f:value=>effects.push(['draft',value]),v:value=>effects.push(['pending',value])};
    return{fn:callback('teams','_r',s=>s.startsWith('async function'),context),effects,guard};
  }
  await check('TEAM-EDIT-EMPTY-NAME',async()=>{const e=editor({draft:'  '});await e.fn();assert.equal(e.effects.some(x=>x[0]==='write'),false);assert(e.effects.some(x=>x[0]==='error'));});
  await check('TEAM-EDIT-UNCHANGED-CLOSES',async()=>{const e=editor({draft:' Old '});await e.fn();assert.deepEqual(e.effects,[['draft',null],['error',null]]);});
  await check('TEAM-EDIT-TRIMMED-PAYLOAD',async()=>{const e=editor();await e.fn();assert.deepEqual(e.effects.find(x=>x[0]==='write')[1],{accountId:'fixture-account',teamId:'fixture-team',fields:{name:'New'}});assert.equal(e.guard.current,false);assert(e.effects.some(x=>x[0]==='draft'&&x[1]===null));});
  await check('TEAM-DESCRIPTION-MAY-BE-EMPTY',async()=>{const e=editor({field:'description',draft:'  '});await e.fn();assert.deepEqual(e.effects.find(x=>x[0]==='write')[1].fields,{description:''});});
  await check('TEAM-EDIT-PENDING-GUARD',async()=>{const e=editor({pending:true});await e.fn();assert.deepEqual(e.effects,[]);});
  for(const [code,expected] of [[409,'name-conflict'],[403,'forbidden'],[500,'save-error']])await check(`TEAM-EDIT-ERROR-${code}`,async()=>{const e=editor({error:code});await e.fn();assert(e.effects.some(x=>x[0]==='error'&&x[1]===expected));assert.equal(e.effects.some(x=>x[0]==='draft'),false);assert.equal(e.guard.current,false);});
  for(const last of [false,true])await check(`TEAM-${last?'LAST-MEMBER-DELETE':'MEMBER-REMOVE'}-DISPATCH`,async()=>{const effects=[];const fn=callback('teams','Fr',s=>s.startsWith('async()=>'),{r:last,n:'fixture-account',a:'fixture-team',i:{principal_id:'fixture-user'},f:false,j:'delete',k:'members',u:{get:(key,arg)=>({mutateAsync:async value=>effects.push({key,arg,value})})},l:()=>effects.push('exited')});await fn();assert.equal(effects[0].key,last?'delete':'members');assert.deepEqual(plain(effects[0].value),last?{accountId:'fixture-account',teamId:'fixture-team'}:{action:'remove',principalId:'fixture-user'});assert.equal(effects.includes('exited'),last);});
  const unique=Array.from(new Map(used.map(u=>[`${u.page}:${u.spanHash}`,u])).values());
  const result={baselineId:base,method:'Exact frozen helpers/callbacks in isolated VM with synthetic HTTP, query, editor and mutation receivers; no imports or live service execution.',sourceSelections:unique,cases,passed:cases.length,failed:0,productScenariosExecuted:0,modelSubmissionsAdded:0,originalClientRunsAdded:0,liveAccountOrFinancialWrites:0};
  fs.writeFileSync(path.join(work,'isolated-observations.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
  process.stdout.write(JSON.stringify({passed:cases.length,failed:0,productScenariosExecuted:0})+'\n');
})().catch(e=>{process.stderr.write(e.stack+'\n');process.exitCode=1;});
