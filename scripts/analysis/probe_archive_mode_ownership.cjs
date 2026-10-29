// Replays selected frozen first-party functions with synthetic data and adapters.
// No application module, real account, filesystem provider, or service is loaded.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const vm = require('node:vm');
const assert = require('node:assert/strict');

const root = process.argv[2];
const baseline = 'codex-26.1007.30912-c5b273322a83';
const work = path.join(root, '.analysis-local/mode-ownership-reconciliation-work');
const selected = path.join(work, 'archive-provider');
const metadata = JSON.parse(fs.readFileSync(path.join(selected, 'source-contracts.json')));
const source = fs.readFileSync(path.join(root, '.analysis-local/baselines', baseline,
  'extracted', metadata.sourcePath.replace(/^app\.asar\//, '')));
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
assert.equal(hash(source), metadata.sourceHash);
const sourceReferences = [];
function readUnit(reference, name) {
  const {start, endExclusive} = reference.byteRange;
  const bytes = source.subarray(start, endExclusive);
  assert.equal(hash(bytes), reference.spanHash);
  sourceReferences.push({name, ...reference});
  return bytes.toString('utf8');
}
const units = metadata.units.flatMap(unit => {
  const text = readUnit(unit, unit.name);
  // xPr is static evidence only; its module import is outside this VM replay.
  return unit.name === 'xPr' ? [] : [text];
});
// These complete helpers are selected by the existing full-Program binding links.
for (const name of ['N4o', 'M4o']) {
  const use = metadata.programBindingUses.find(use => use.unit === 'O4o' && use.name === name);
  assert.equal(use.binding.scopeKind, 'Program');
  assert.equal(use.binding.definitions.length, 1);
  units.push(readUnit(use.binding.definitions[0].declaration, name));
}
const context = vm.createContext({
  // Imported title/path formatting and state/query/service adapters are substitutes.
  Gs: value => value,
  SKo: value => value ?? null,
  km: value => value,
  as: 'local',
  L4o: 'special:automations',
  Date, Set, Map, Number, Promise,
});
vm.runInContext(units.join('\n'), context);
const cases = [];
async function check(name, action) {
  try { await action(); cases.push({name, status:'passed'}); }
  catch (error) { cases.push({name, status:'failed', error:String(error.stack ?? error)}); }
}
const plain = value => JSON.parse(JSON.stringify(value));
const accountChat = {id:'synthetic-chat', title:' Chat ', create_time:'2026-01-01T00:00:00Z', update_time:'2026-01-02T00:00:00Z', conversation_origin:null};
const workConversation = {...accountChat, id:'synthetic-work', title:' Work ', conversation_origin:'tpp'};
const cloudTask = {id:'synthetic-cloud', title:' Cloud ', created_at:1, updated_at:2, archived:true};
const localThread = {id:'synthetic-local', name:' Local ', preview:'Fallback', createdAt:3, updatedAt:4};

(async () => {
  await check('same projector preserves account chat, work conversation, cloud task and local identities', () => {
    const rows = context.O4o({chatGptConversations:[accountChat, workConversation], cloudTasks:[cloudTask], localThreads:[localThread]});
    assert.equal(rows.length,4);
    assert.deepEqual(plain(rows.map(row => row.kind)), ['cloud','cloud','local','cloud']);
    assert.equal(rows[0].task,accountChat);
    assert.equal(rows[1].task,workConversation);
    assert.equal(rows[2].thread,localThread);
    assert.equal(rows[3].task,cloudTask);
  });
  await check('normalizer accepts empty sources without inventing a row', () => {
    assert.deepEqual(plain(context.O4o({})),[]);
  });
  await check('durable thread preserves backend identity and host instead of becoming an account conversation', () => {
    const [row] = context.O4o({localThreads:[localThread], localHostId:'durable'});
    assert.equal(row.kind,'local'); assert.equal(row.hostId,'durable'); assert.equal(row.thread,localThread);
  });
  await check('finite timestamp fallback and title projection remain source behavior', () => {
    const [row] = context.O4o({localThreads:[{...localThread,name:' ',updatedAt:NaN}]});
    assert.equal(row.title,'Fallback'); assert.equal(row.updatedAt,3);
  });
  await check('account and local rows can preserve the same explicit local-project grouping', () => {
    const project={projectId:'synthetic-project',projectKind:'local',groupId:'group-1',label:'Fixture',path:'/fixture'};
    const rows=context.O4o({chatGptConversations:[{...accountChat,gizmo_id:project.projectId}],
      localThreads:[{...localThread,cwd:'/fixture'}],projects:[project]});
    assert.deepEqual(plain(rows.map(row=>row.projectGroupId)),['group-1','group-1']);
  });
  await check('chat-only archive query explicitly excludes tpp origin', async () => {
    let captured;
    context.Wgn=async (...args)=>{captured=args;return {offset:0,limit:20,total:25,items:[]};};
    const signal={fixture:true}; const scope={fixture:true};
    const value=await context.iPr(scope,{includeWorkCloud:false,limit:20,offset:0},signal);
    assert.equal(captured[0],scope); assert.equal(captured[1].exclude_conversation_origin,'tpp');
    assert.equal(captured[1].is_archived,true); assert.equal(captured[2],signal); assert.equal(value.nextOffset,20);
  });
  await check('including work cloud removes the origin exclusion and respects last page', async () => {
    let captured;
    context.Wgn=async (...args)=>{captured=args;return {offset:20,limit:20,total:25,items:[workConversation]};};
    const value=await context.iPr({}, {includeWorkCloud:true,limit:20,offset:20},{});
    assert.equal(captured[1].exclude_conversation_origin,undefined);
    assert.equal(value.nextOffset,null); assert.equal(value.page.items[0],workConversation);
  });
  await check('account archive query propagates provider rejection', async () => {
    const failure=new Error('synthetic query failure');context.Wgn=async()=>{throw failure;};
    await assert.rejects(context.iPr({}, {includeWorkCloud:true,limit:20,offset:0},{}),error=>error===failure);
  });
  function prepareMutation(shouldReject) {
    const events=[];
    Object.assign(context,{kk:id=>events.push(['invalidate-id',id]),
      Ae:{safePatch:async (url,options)=>{events.push(['patch',url,plain(options)]);if(shouldReject)throw new Error('synthetic patch failure');}},
      tA:'conversation-snapshot',Wz:(...args)=>events.push(['refresh',args[1],args[2]]),
      Qz:'archive-key',Yk:'account-key',LO:'collection-key',Jk:()=>true,Kk:()=>['pin-key']});
    const scope={query:{snapshot:(key,id)=>({setData:update=>events.push(['snapshot',id,update({is_archived:true}).is_archived])})},
      queryClient:{cancelQueries:options=>events.push(['cancel',options.queryKey]),invalidateQueries:async options=>events.push(['invalidate',!!options.predicate,options.queryKey??null])}};
    return {events,scope};
  }
  await check('account unarchive uses captured ID and refreshes collections after successful patch', async () => {
    const {events,scope}=prepareMutation(false);await context.SPr({scope,conversationId:workConversation.id});
    const patch=events.find(event=>event[0]==='patch');
    assert.equal(patch[2].parameters.path.conversation_id,workConversation.id);
    assert.equal(patch[2].requestBody.is_archived,false);
    assert.equal(events.filter(event=>event[0]==='invalidate').length,5);
    assert(events.some(event=>event[0]==='snapshot'&&event[2]===false));
  });
  await check('failed unarchive still invalidates ID but never reports cache success', async () => {
    const {events,scope}=prepareMutation(true);
    await assert.rejects(context.SPr({scope,conversationId:accountChat.id}),/synthetic patch failure/);
    assert.equal(events.filter(event=>event[0]==='invalidate-id').length,2);
    assert.equal(events.filter(event=>event[0]==='snapshot'||event[0]==='invalidate').length,0);
  });
  const report={baselineId:baseline,recordedAtUtc:new Date().toISOString(),
    kind:'isolated-frozen-source-replay',sourceReferences,cases,
    counts:{passed:cases.filter(value=>value.status==='passed').length,failed:cases.filter(value=>value.status==='failed').length},
    executedFunctionNames:['O4o','iPr','SPr','N4o','M4o'],staticOnlyFunctionNames:['xPr'],
    substitutions:['title and path formatting','account query','HTTP mutation','query cache/state'],
    targetModuleEvaluated:false,originalClientRunsAdded:0,realServiceCalls:0,modelSubmissionsAdded:0,productScenarioPassesAdded:0};
  fs.writeFileSync(path.join(work,'isolated-observations.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({counts:report.counts,cases:cases.filter(value=>value.status==='failed')}));
  if(report.counts.failed)process.exitCode=1;
})();
