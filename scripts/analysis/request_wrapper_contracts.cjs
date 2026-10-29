// Consolidate static AST provenance. Frozen target JavaScript is only read/parsed.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const workspace = path.resolve(__dirname, '../..');
const parser = process.argv[2] ? require(path.resolve(process.argv[2])) : require('@babel/parser');
const sha = x => crypto.createHash('sha256').update(x).digest('hex');
const read = p => fs.readFileSync(path.join(workspace,p));
const json = p => JSON.parse(read(p));
const jsonl = p => read(p).toString('utf8').trim().split('\n').filter(Boolean).map(JSON.parse);
const baseline = json('.analysis-local/current-baseline.json');
const root = path.resolve(workspace,baseline.extractedDirectory), out = '.analysis-local/review-work/';
const ast = json(out+'request-wrapper-ast.json'), targets = json(out+'request-wrapper-targets.json');
const local = json(out+'wrapper-local-findings.json'), projects = json(out+'project-create-local-evidence.json'), filter = json(out+'project-root-filter-evidence.json');
const published = 'analysis/'+baseline.baselineId+'/';
const candidates = json(published+'app-server-methods.json').filter(x=>x.callForm==='sendRequest');
const originalEvidence = jsonl(published+'evidence.jsonl');
const originalMap = new Map(originalEvidence.map(x=>[x.id,x]));
const inventory = json(published+'files.json').archiveFiles;
const astEvidence = jsonl(out+'request-wrapper-ast-evidence.jsonl');
const targetEvidence = jsonl(out+'request-wrapper-target-evidence.jsonl');
const astMap = new Map(astEvidence.map(x=>[x.id,x]));
const targetMap = new Map(targetEvidence.map(x=>[x.id,x]));
const rawCache = new Map(), evidence = new Map();
const sourcePath = p => p.startsWith('app.asar/') ? p : 'app.asar/'+p;
function raw(p) {
  p=sourcePath(p); if(rawCache.has(p)) return rawCache.get(p);
  const rel=p.slice(9), physical=path.resolve(root,rel);
  if(!physical.startsWith(root+path.sep)) throw Error('Escaped frozen source root');
  const bytes=fs.readFileSync(physical), hash=sha(bytes);
  const known=inventory.find(x=>x.sourcePath===p || x.path===rel || x.path===p);
  if(!known || (known.sha256??known.sourceHash)!==hash) throw Error('Frozen source/inventory mismatch: '+p);
  const result={sourcePath:p,bytes,sourceHash:hash,text:bytes.toString('utf8')};rawCache.set(p,result);return result;
}
function normalize(e) {
  const p=sourcePath(e.sourcePath), r=raw(p), range=e.locator??{kind:'byte-range',start:e.byteRange.start,endExclusive:e.byteRange.end};
  const expected=e.sourceHash??e.sourceSha256;
  if(expected!==r.sourceHash) throw Error('Source hash mismatch: '+e.id);
  if(!Number.isInteger(range.start)||!Number.isInteger(range.endExclusive)||range.start<0||range.endExclusive>r.bytes.length||range.start>=range.endExclusive) throw Error('Invalid locator: '+e.id);
  const spanHash=sha(r.bytes.subarray(range.start,range.endExclusive));
  if(e.spanSha256 && e.spanSha256!==spanHash) throw Error('Span hash mismatch: '+e.id);
  return {id:e.id,baselineId:baseline.baselineId,sourcePath:p,sourceHash:r.sourceHash,locator:{kind:'byte-range',start:range.start,endExclusive:range.endExclusive},spanSha256:spanHash,
    locatorScope:e.locatorScope??e.claimScope??e.astType??'static-source-span',nodeType:e.nodeType??e.astType??null,
    claim:e.claim??e.label??('Original '+(e.nodeType??e.astType??e.locatorScope??'source')+' span is located at the recorded bytes.'),claimScope:e.claimScope??'Original AST span only; classification is stated in the contracts artifact.',
    method:'supplemental-static-AST-binding',confidence:'confirmed',
    verificationStatus:'original-source-and-span-sha256-verified; static-only; target-not-executed'};
}
function keep(e) {const n=normalize(e);if(evidence.has(n.id)&&JSON.stringify(evidence.get(n.id))!==JSON.stringify(n))throw Error('Conflicting evidence ID '+n.id);evidence.set(n.id,n);return n.id;}
function astKeep(id) {if(id==null)return null;const e=astMap.get(id);if(!e)throw Error('Missing AST evidence '+id);return keep(e);}
function addRaw(s,start,end,role,claim) {
  const id='REQUEST-WRAPPER-BINDING-'+String([...evidence.keys()].filter(x=>x.startsWith('REQUEST-WRAPPER-BINDING-')).length+1).padStart(4,'0');
  return keep({id,sourcePath:s.sourcePath,sourceHash:s.sourceHash,locator:{kind:'byte-range',start,endExclusive:end},spanSha256:sha(s.bytes.subarray(start,end)),locatorScope:role,claim,claimScope:'Complete original binding/expression span; static identity only.'});
}
for(const e of targetEvidence)keep(e);
for(const e of jsonl(out+'wrapper-local-evidence.jsonl'))keep(e);
for(const e of [...projects.evidence,...filter.evidence])keep(e);
const bySymbol=new Map(targets.findings.map(x=>[x.symbol,x]));
const shared=ast.files.find(x=>x.sourcePath.includes('/app-shared-'));
const sharedRaw=raw(shared.sourcePath);
const sharedExportRow=shared.exports.find(x=>x.bindings.some(b=>b.exported==='y$t'));
const sharedExportEvidence=astMap.get(sharedExportRow.evidenceId);
const exportText=sharedRaw.bytes.subarray(sharedExportEvidence.locator.start,sharedExportEvidence.locator.endExclusive).toString('utf8');
const exportAst=parser.parse(exportText,{sourceType:'module',allowUndeclaredExports:true});
const exportBindings={};
for(const statement of exportAst.program.body)for(const specifier of statement.specifiers??[]) {
  const name=specifier.exported.name??specifier.exported.value;
  if(!['y$t','TFt','fN','dN','mN'].includes(name))continue;
  const start=sharedExportEvidence.locator.start+Buffer.byteLength(exportText.slice(0,specifier.start));
  const end=sharedExportEvidence.locator.start+Buffer.byteLength(exportText.slice(0,specifier.end));
  exportBindings[name]={local:specifier.local.name,evidenceId:addRaw(sharedRaw,start,end,'complete-export-specifier',specifier.local.name+' is exported as '+name)};
}
for(const [name,expected]of Object.entries({'y$t':'KI',TFt:'AW',fN:'e6',dN:'$3',mN:'qli'}))if(exportBindings[name]?.local!==expected)throw Error('Unexpected shared export '+name);
const rpcFile=ast.files.find(x=>/\/rpc-/.test(x.sourcePath));
const rpcFacade={sourcePath:rpcFile.sourcePath,sourceHash:rpcFile.sourceHash,imports:rpcFile.imports,exports:rpcFile.exports};
for(const x of [...rpcFile.imports,...rpcFile.exports])astKeep(x.evidenceId);
function targetIds(symbol) {const x=bySymbol.get(symbol);if(!x)throw Error('Missing selected target '+symbol);return [x.classEvidenceId,x.functionEvidenceId,x.assignmentEvidenceId,x.expressionEvidenceId,x.methodEvidenceId,...Object.values(x.members??{}).map(v=>v.evidenceId)].filter(Boolean);}
function classRange(symbol) {return targetMap.get(bySymbol.get(symbol).classEvidenceId);}
function inSpan(call,e) {const c=astMap.get(call.callEvidenceId);return c.sourcePath===e.sourcePath&&c.locator.start>=e.locator.start&&c.locator.endExclusive<=e.locator.endExclusive;}
function withinClass(call,symbol) {return inSpan(call,classRange(symbol));}
const managerIds=['Dfn','Spn','Ioi','N3','loi','Sii','Vfn'].flatMap(targetIds);
const selectorIds=[...targetIds('KI'),...targetIds('qI'),...targetIds('HI'),...targetIds('JI'),exportBindings['y$t'].evidenceId];
const fetchIds=[...targetIds('AW'),exportBindings.TFt.evidenceId];
const helperReceivers={N9t:'e',dan:'e',man:'e',msn:'t',adn:'i'};
const helperMethods={N9t:'forkConversationFromTurn',dan:'discardConversationFromCache',man:'editLastUserTurn',msn:'retrySafetyBufferedTurn',adn:'stopThread'};
const safeThisNodeTypes=new Set(['ClassMethod','ClassPrivateMethod','ArrowFunctionExpression']);
// Verify the lexical this owner in complete selected class ASTs, including arrows
// nested inside ordinary functions. This never evaluates a target implementation.
const verifiedThisCalls=new Map();
for(const symbol of ['Dfn','fue','c1']) {
  const e=classRange(symbol), s=raw(e.sourcePath), text=s.bytes.subarray(e.locator.start,e.locator.endExclusive).toString('utf8');
  const rootClass=parser.parseExpression(text,{sourceType:'module'}), positions=new Set();
  function walk(node,activeClass,thisOwned) {
    if(!node||typeof node!=='object'||!node.type)return;
    if(['ClassExpression','ClassDeclaration'].includes(node.type))activeClass=node===rootClass?symbol:null;
    if(['ClassMethod','ClassPrivateMethod','ClassProperty','ClassPrivateProperty'].includes(node.type))thisOwned=activeClass===symbol;
    if(['FunctionExpression','FunctionDeclaration','ObjectMethod'].includes(node.type))thisOwned=false;
    if(['CallExpression','OptionalCallExpression'].includes(node.type)&&node.callee?.property?.name==='sendRequest'&&thisOwned)positions.add(e.locator.start+Buffer.byteLength(text.slice(0,node.start)));
    for(const [k,v]of Object.entries(node)) {
      if(['loc','start','end','extra','comments','tokens'].includes(k))continue;
      if(Array.isArray(v))for(const child of v)walk(child,activeClass,thisOwned);
      else if(v&&typeof v==='object')walk(v,activeClass,thisOwned);
    }
  }
  walk(rootClass,null,false);verifiedThisCalls.set(symbol,positions);
}
const hasVerifiedThis=(call,symbol)=>verifiedThisCalls.get(symbol).has(astMap.get(call.callEvidenceId).locator.start);
function classify(call,file) {
  const common={kind:'unresolved',contractId:null,reason:'Concrete receiver identity is not established by the reviewed lexical/import/class bindings.',bindingEvidence:[]};
  const nodeType=astMap.get(call.enclosingFunctionEvidenceId)?.nodeType;
  if(withinClass(call,'Dfn')&&['this','this.requestClient'].includes(call.receiver)&&safeThisNodeTypes.has(nodeType)&&hasVerifiedThis(call,'Dfn'))return{kind:'manager-request-facade',contractId:'RWC-MANAGER',reason:'Lexical this owner is Dfn or its constructor-assigned transport; local fallback construction injects Spn.',bindingEvidence:managerIds};
  for(const [helper,receiver]of Object.entries(helperReceivers)) {
    const e=targetMap.get(bySymbol.get(helper).functionEvidenceId);
    const owner=astMap.get(call.rootBinding?.scopeOwnerEvidenceId);
    if(inSpan(call,e)&&call.receiver===receiver&&call.rootBinding?.type==='parameter'&&owner?.locator.start===e.locator.start&&owner?.locator.endExclusive===e.locator.endExclusive)return{kind:'manager-request-facade',contractId:'RWC-MANAGER',reason:'Complete helper parameter lexical scope plus Dfn method invocation passes the Dfn manager as this.',bindingEvidence:[...managerIds,...targetIds(helper),bySymbol.get('Dfn').members[helperMethods[helper]].evidenceId]};
  }
  if(withinClass(call,'fue')&&call.receiver==='this'&&nodeType==='ClassMethod'&&hasVerifiedThis(call,'fue'))return{kind:'app-server-extension-connection',contractId:'RWC-HOSTED-FILES',reason:'fue constructor injects sendRequest; createAppHost injects the appServerConnectionRegistry connection sendAppServerExtensionRequest callback.',bindingEvidence:[...targetIds('fue'),...targetIds('new fue((e,t)=>h(r.ki).sendAppServerExtensionRequest'),...targetIds('createAppHost(e){')]};
  if(withinClass(call,'c1')&&call.receiver==='this'&&safeThisNodeTypes.has(nodeType)&&hasVerifiedThis(call,'c1'))return{kind:'coordination-socket-request',contractId:'RWC-COORDINATION',reason:'Receiver is the concrete IpcClient c1, whose sendRequest builds a coordination request envelope and writes to its socket.',bindingEvidence:targetIds('c1')};
  if(withinClass(call,'X2t')&&call.receiver==='this.[computed]()')return{kind:'resolver-request-facade',contractId:'RWC-RESOLVER',reason:'The concrete resolver closure is injected; this class forwards to its result and does not establish a transport.',bindingEvidence:targetIds('X2t')};
  const b=call.rootBinding;
  const importedShared=b?.type==='import'&&b.details?.source==='./app-shared-8bd9d0399038.js';
  if(call.receiver===call.receiverRoot+'.getInstance()'&&((file.sourcePath===shared.sourcePath&&call.receiverRoot==='AW'&&b?.type==='variable')||(importedShared&&b.details.imported==='TFt')))return{kind:'desktop-http-fetch',contractId:'RWC-FETCH',reason:'Lexical binding resolves the getInstance receiver to AW; sendRequest accepts HTTP method/URL and uses fetch or desktop fetch messages.',bindingEvidence:fetchIds};
  if(call.receiver===call.receiverRoot+'()'&&((file.sourcePath===shared.sourcePath&&call.receiverRoot==='KI'&&b?.type==='function')||(importedShared&&b.details.imported==='y$t')))return{kind:'host-manager-rpc-selector',contractId:'RWC-SELECTOR',reason:'Lexical direct-call/import binding resolves to KI; concrete forHost/client.rpc/cached/deferred branch is runtime-dependent.',bindingEvidence:selectorIds};
  if(withinClass(call,'p1')&&call.receiver==='this.ipcClient')return{...common,reason:'p1 constructor injects ipcClient; reviewed code establishes coordination options but not the concrete runtime client instance.',bindingEvidence:targetIds('p1')};
  return common;
}
const calls=[];
for(const file of ast.files)for(const call of file.calls) {
  const classification=classify(call,file);
  const ids=[astKeep(call.callEvidenceId),astKeep(call.enclosingFunctionEvidenceId),astKeep(call.enclosingClassEvidenceId)];
  if(call.rootBinding) {
    ids.push(astKeep(call.rootBinding.evidenceId),astKeep(call.rootBinding.scopeOwnerEvidenceId));
    for(const a of call.rootBinding.assignments??[])ids.push(astKeep(a.evidenceId));
    for(const id of call.rootBinding.redeclarationEvidenceIds??[])ids.push(astKeep(id));
  }
  calls.push({sourcePath:file.sourcePath,sourceHash:file.sourceHash,method:call.method,methodKind:call.method==null?'dynamic-or-conditional':'single-literal',receiver:call.receiver,
    callEvidenceId:call.callEvidenceId,enclosingFunction:call.enclosingFunctionName,lexicalRootBinding:call.rootBinding?{name:call.rootBinding.name,type:call.rootBinding.type,details:call.rootBinding.details}:null,
    ...classification,evidenceIds:[...new Set([...ids,...classification.bindingEvidence].filter(Boolean))],
    claimScope:'Receiver identity and observed adapter behavior only. No runtime reachability, public protocol membership, successful server delivery or UI validation claimed.'});
}
const candidateLinks=[];
for(const c of candidates) {
  const e=originalMap.get(c.evidenceId);if(!e)throw Error('Missing published candidate '+c.evidenceId);
  const possible=calls.filter(x=>x.sourcePath===c.sourcePath&&x.method===c.method&&(()=>{const a=astMap.get(x.callEvidenceId).locator;return e.locator.start>=a.start&&e.locator.endExclusive<=a.endExclusive;})());
  if(possible.length!==1)throw Error('Published candidate needs exactly one AST match: '+c.evidenceId+' '+possible.length);
  keep(e);const x=possible[0];candidateLinks.push({publishedEvidenceId:c.evidenceId,sourcePath:c.sourcePath,method:c.method,astCallEvidenceId:x.callEvidenceId,kind:x.kind,contractId:x.contractId});
}
const counts={};for(const c of calls)counts[c.kind]=(counts[c.kind]??0)+1;
const candidateCounts={};for(const c of candidateLinks)candidateCounts[c.kind]=(candidateCounts[c.kind]??0)+1;
const contracts=[
 {id:'RWC-MANAGER',receiver:'Dfn',kind:'manager-request-facade',observedBehavior:'constructor assigns transport to requestClient; Dfn.sendRequest forwards method/params/options unchanged, with plugin install/uninstall cache invalidation after completion. N3 local fallback calls loi -> Sii with scope Ioi transport; Ioi constructs Spn. Spn has a config/read special branch and plugin/list timeout default; its general enqueue path builds id/method/params requests and dispatches the desktop mcp-request envelope. Vfn disables this local fallback when appServices.appServerManagers exists.',evidenceIds:managerIds,unknowns:['Which manager/transport branch is active in the running renderer.','Main handler mapping for mcp-request and method support are not proven by this scoped artifact.','thread/stop and thread/rollback are transport-bound observations, not confirmed public protocol methods.']},
 {id:'RWC-SELECTOR',receiver:'KI / shared y$t',kind:'host-manager-rpc-selector',observedBehavior:'Selects configured facade.forHost(hostId), connected client.rpc, cached proxy, or a deferred RPC resolved from client.rpc.dup(). A method literal alone does not prove direct app-server transport.',evidenceIds:selectorIds,unknowns:['Runtime selected branch and configured forHost implementation.','Underlying RPC manager method translation and public app-server delivery for each call.']},
 {id:'RWC-FETCH',receiver:'AW / shared TFt',kind:'desktop-http-fetch',observedBehavior:'sendRequest accepts HTTP method and URL. Ordinary paths go to fetchJson; vscode://codex and the dictation endpoint use fetch/cancel-fetch desktop messages.',evidenceIds:fetchIds,unknowns:['Actual network responses and desktop fetch handler completion.']},
 {id:'RWC-RESOLVER',receiver:'X2t',kind:'resolver-request-facade',observedBehavior:'Constructor injects resolver #e; getter sendRequest forwards all arguments to #e().sendRequest.',evidenceIds:targetIds('X2t'),unknowns:['The concrete resolver passed at runtime; no app-server classification follows from this facade alone.']},
 {id:'RWC-HOSTED-FILES',receiver:'fue',kind:'app-server-extension-connection',observedBehavior:'Constructor stores injected sendRequest. The reviewed createAppHost factory injects connectionRegistry.getConnection(...).sendAppServerExtensionRequest. Five observed member calls use that callback.',evidenceIds:[...targetIds('fue'),...targetIds('new fue((e,t)=>h(r.ki).sendAppServerExtensionRequest'),...targetIds('createAppHost(e){')],unknowns:['Extension method implementation, schema and actual completion downstream of the connection.']},
 {id:'RWC-HOST-TRANSPORT',receiver:'_fe',kind:'app-server-host-connection-adapter',observedBehavior:'sendRequest creates id/method/params/trace request; send forwards to injected connection.handleHostRequest or prewarm handler. Reviewed manager construction injects new _fe as transport.',evidenceIds:[...targetIds('_fe'),...targetIds('new _fe(t,e.hostId,o,')],unknowns:['Injected connection identity at each host and its final public protocol wire implementation.']},
 {id:'RWC-COORDINATION',receiver:'c1; p1 takes injected ipcClient',kind:'coordination-socket-request',observedBehavior:'Concrete c1 builds request envelope with sourceClientId, targetClientId, hostId and timeout, writes to socket and awaits response. p1 only establishes an injected-client adapter and remains unresolved in the call census.',evidenceIds:[...targetIds('c1'),...targetIds('p1')],unknowns:['Concrete client passed to p1 at runtime and actual socket execution.']},
 {id:'RWC-PROJECTS',receiver:'projects service',kind:'app-host-messageport-service',observedBehavior:'Dialog He -> initial Mln/mI -> shared fN/e6.projects. qli assigns e6 from Uli(Vli).services; Uli posts connect-app-host MessagePort and uses nIt/hFt RPC runtime. Main hXe constructor stores new qHe as projectsManager; createAppHost publishes projects:this.projectsManager. createLocal parses request; nonempty sources uses Wr while empty sources uses createDefaultWorkspaceRoot, then confirmation and assignment pass precede project/state mutation.',evidenceIds:[...projects.evidence.map(x=>x.id),...filter.evidence.map(x=>x.id),...targetIds('qHe'),...targetIds('hXe'),...targetIds('WHe'),...targetIds('new qHe(this.scopedState,'),...targetIds('nIt'),...targetIds('hFt')],unknowns:['Live capability presence, renderer account/mode guards and confirmation callback behavior.','Explicit /private/tmp path is authored input shape, not an observed literal or runtime success.','Actual own-directory existence and state isolation require independent evidence.']}
];
const inputPaths=[out+'request-wrapper-ast.json',out+'request-wrapper-ast-evidence.jsonl',out+'request-wrapper-targets.json',out+'request-wrapper-target-evidence.jsonl',out+'wrapper-local-findings.json',out+'wrapper-local-evidence.jsonl',out+'project-create-local-evidence.json',out+'project-root-filter-evidence.json',published+'app-server-methods.json',published+'protocol-coverage.json',published+'evidence.jsonl',published+'files.json'];
const result={schemaVersion:1,baselineId:baseline.baselineId,archiveSha256:baseline.archiveSha256,status:'scoped-static-bindings-complete; runtime-unverified',
  methodology:'Reuse existing 37-file AST index; parse only complete selected prefixes and selected export statements. Classify by lexical binding, imports, class transport assignment and caller injection, never by method spelling. Verify every retained source/span SHA-256 against frozen inventory.',
  reproduction:{script:{path:path.relative(workspace,__filename),sha256:sha(fs.readFileSync(__filename))},commands:['node scripts/analysis/request_wrapper_ast.cjs <@babel/parser entry> # only needed to recreate existing index','node scripts/analysis/request_wrapper_targets.cjs <@babel/parser entry>','node scripts/analysis/request_wrapper_contracts.cjs <@babel/parser entry>'],localSupplementScripts:local.methodology??null,targetCodeEvaluated:false},
  inputs:inputPaths.map(p=>({path:p,sha256:sha(read(p))})),
  scanDenominator:{previousLiteralCandidateRows:candidates.length,previousDistinctLiteralMethods:new Set(candidates.map(c=>c.method)).size,previousCandidateFiles:new Set(candidates.map(c=>c.sourcePath)).size,selectedFiles:ast.scope.selectedSourceFiles,parsedFiles:ast.scope.parsedSourceFiles,astCallsites:calls.length,singleLiteralCallsites:calls.filter(c=>c.method!=null).length,dynamicOrConditionalCallsites:calls.filter(c=>c.method==null).length,publishedCandidatesLinked:candidateLinks.length,astClassificationCounts:counts,publishedCandidateClassificationCounts:candidateCounts,wholeClientCoverageClaimed:false},
  files:ast.files.map(f=>({sourcePath:f.sourcePath,sourceHash:f.sourceHash,bytes:f.bytes,astSendRequestCount:f.astSendRequestCount})),
  sharedExports:exportBindings,rpcFacade,contracts,calls,candidateLinks,
  projectCreateLocal:{rendererEvidenceArtifact:out+'project-create-local-evidence.json',filterEvidenceArtifact:out+'project-root-filter-evidence.json',confirmedAccessor:{module:'webview/assets/app-initial-6350d04672d0.js',exported:'Mln',local:'mI'},authoredOwnInput:{appearance:null,initializeDefaultWorkspaceGitRepository:false,name:'ccodex-learning',sources:['/private/tmp/<existing-own-random-directory>'],setActive:false},executionStatus:'not-executed',preconditions:['Existing self-owned source directory; nonempty sources avoids the default-root branch.','Folder confirmation still occurs.','To avoid pre-existing thread mutation, no eligible stored cwd or workspace-root hint may match the path or canonical/host identity. Directory creation alone does not prove this precondition.','Actual capability/profile isolation and confirmation must be established separately before any original-service invocation.'],filterFinding:filter.implication},
  unknowns:['Unresolved callsites are retained with their lexical bindings; no whole-bundle/full-program call coverage claim.','KI is a manager RPC selector with runtime-dependent alternatives, not unconditional proof of AppHost MessagePort transport.','Observed manager/connection adapters do not establish public app-server method/schema compatibility or successful UI execution.','No target code, UI, IPC, history read or project creation performed.'],
  evidence:{path:out+'request-wrapper-evidence.jsonl',recordCount:evidence.size,sourceAndSpanHashesVerified:true}};
const evidenceText=[...evidence.values()].map(x=>JSON.stringify(x)).join('\n')+'\n';
result.evidence.sha256=sha(evidenceText);
fs.writeFileSync(path.join(workspace,out+'request-wrapper-evidence.jsonl'),evidenceText);
fs.writeFileSync(path.join(workspace,out+'request-wrapper-contracts.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({scanDenominator:result.scanDenominator,evidence:result.evidence,contracts:contracts.length}));
