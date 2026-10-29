#!/usr/bin/env node
// Finite static review. Only one 1.6KB initial fragment is newly parsed.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';

const root=process.cwd(), baselineId='codex-26.1007.30912-c5b273322a83';
const out=path.join(root,'.analysis-local/project-upstream-work');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const require=createRequire(import.meta.url);
const parserPath='/private/tmp/ccodex-rea-tooling/install/node_modules/@babel/parser/lib/index.js';
const parser=require(parserPath);
const inputPaths={
  baseline:'.analysis-local/current-baseline.json',
  project:'.analysis-local/mode-boundary-work/project-review.json',
  'project-evidence':'.analysis-local/mode-boundary-work/project-evidence.jsonl',
  guards:'.analysis-local/feature-work/route-guard-notes.json',
  ast:'.analysis-local/review-work/request-wrapper-ast.json',
  'ast-evidence':'.analysis-local/review-work/request-wrapper-ast-evidence.jsonl',
};
const inputBytes=Object.fromEntries(Object.entries(inputPaths).map(([k,p])=>[k,fs.readFileSync(path.join(root,p))]));
const inputs=Object.entries(inputPaths).map(([key,p])=>({key,path:p,bytes:inputBytes[key].length,sha256:sha(inputBytes[key])}));
const docs=Object.fromEntries(Object.entries(inputBytes).filter(([k])=>!k.endsWith('evidence')).map(([k,b])=>[k,JSON.parse(b)]));
if(docs.baseline.baselineId!==baselineId||docs.project.baselineId!==baselineId||docs.ast.baselineId!==baselineId)throw Error('Baseline mismatch');
const sourceRoot=path.resolve(docs.baseline.extractedDirectory);
const sourceFiles=[], sourceBytes=new Map();
function getSource(sourcePath,sourceHash){
  const rel=sourcePath.replace(/^app\.asar\//,'');
  const p=path.resolve(sourceRoot,rel);
  if(!p.startsWith(sourceRoot+path.sep))throw Error('Outside frozen source root');
  if(!sourceBytes.has(sourcePath)){
    const b=fs.readFileSync(p);
    if(sha(b)!==sourceHash)throw Error('Frozen source hash mismatch');
    sourceBytes.set(sourcePath,b);sourceFiles.push({sourcePath,sourceHash,bytes:b.length});
  }
  return sourceBytes.get(sourcePath);
}
const initial=docs.ast.files[2];
const savedExport=initial.exports[0].bindings[6312];
if(initial.sourcePath!=='app.asar/webview/assets/app-initial-6350d04672d0.js'||savedExport.local!=='Emn'||savedExport.exported!=='fkn')throw Error('Saved actual export changed');
const raw=getSource(initial.sourcePath,initial.sourceHash);
const selected=['Emn','vO','yO','bO','xmn','xO'];
const start=1977943;
if(raw.subarray(start,start+12).toString()!=='function vO(')throw Error('Fragment start drift');
const stop=raw.indexOf(Buffer.from('function SO('),1979470);
if(stop<1979470||stop-start>2000)throw Error('Fragment bound drift');
const fragment=raw.subarray(start,stop).toString('utf8');
const program=parser.parse(fragment,{sourceType:'module',errorRecovery:false}).program;
const topFunctions=program.body.filter(n=>n.type==='FunctionDeclaration');
const byteOffset=i=>start+Buffer.byteLength(fragment.slice(0,i),'utf8');
const textOf=n=>fragment.slice(n.start,n.end);
const records=[];
let seq=0;
function add(sourcePath,sourceHash,start,end,nodeType,kind,origin){
  const bytes=getSource(sourcePath,sourceHash);
  const span=bytes.subarray(start,end);
  if(start<0||end<=start||end>bytes.length)throw Error('Bad evidence range');
  span.toString('utf8');
  const id='PUP-E'+String(++seq).padStart(4,'0');
  const r={id,baselineId,sourcePath,sourceHash,range:{start,endExclusive:end},spanHash:sha(span),nodeType,kind,origin};
  records.push(r);return r;
}
function addNode(n,kind){return add(initial.sourcePath,initial.sourceHash,byteOffset(n.start),byteOffset(n.end),n.type,kind,{kind:'fresh-fragment-ast'});}
const fragmentEvidence=add(initial.sourcePath,initial.sourceHash,start,stop,'Program','complete-contiguous-fragment',{kind:'fresh-fragment-ast'});
const functions=selected.map(name=>{
  const matches=topFunctions.filter(n=>n.id.name===name);
  if(matches.length!==1)throw Error('Selected complete function missing or ambiguous');
  const n=matches[0], e=addNode(n,'complete-selected-function');
  return {name,evidenceId:e.id,range:e.range,parameterNames:n.params.map(p=>p.name),calls:[],_node:n};
});
function walk(n,fn){if(!n||typeof n!=='object')return;if(typeof n.type==='string')fn(n);for(const [k,v]of Object.entries(n)){if(['loc','start','end','extra','comments','tokens','errors'].includes(k))continue;if(Array.isArray(v))for(const x of v)walk(x,fn);else if(v&&typeof v==='object')walk(v,fn);}}
let astNodes=0;walk(program,()=>astNodes++);
for(const f of functions){
  walk(f._node,n=>{
    if(!['CallExpression','OptionalCallExpression','NewExpression'].includes(n.type))return;
    const e=addNode(n,'complete-selected-call');
    const callee=n.callee, direct=callee.type==='Identifier'?functions.find(x=>x.name===callee.name):null;
    f.calls.push({evidenceId:e.id,range:e.range,calleeKind:callee.type,calleeName:callee.type==='Identifier'?callee.name:textOf(callee),argumentCount:n.arguments.length,
      localFragmentBinding:direct?{status:'bound-to-top-level-function-in-complete-fragment',targetFunctionEvidenceId:direct.evidenceId,originalModuleScope:'unknown'}:{status:'member-or-external-implementation-unknown',targetFunctionEvidenceId:null,originalModuleScope:'unknown'}});
  });
  delete f._node;
}
const ref=(key,jsonPointer)=>({key,jsonPointer});
const projectRows=inputBytes['project-evidence'].toString().trim().split('\n').map(l=>JSON.parse(l));
const astRows=inputBytes['ast-evidence'].toString().trim().split('\n').map(l=>JSON.parse(l));
const projectCatalog=new Map(projectRows.map(r=>[r.evidenceId,r]));
const astCatalog=new Map(astRows.map(r=>[r.id||r.evidenceId,r]));
function reuse(record,key,pointer){
  const loc=record.range||record.locator||record.byteRange;
  const end=typeof loc.endExclusive==='number'?loc.endExclusive:loc.end;
  const hash=record.sourceHash||record.sourceSha256;
  const sourcePath=record.sourcePath.startsWith('app.asar/')?record.sourcePath:'app.asar/'+record.sourcePath;
  const b=getSource(sourcePath,hash);
  const expected=record.spanHash||record.spanSha256;
  if(sha(b.subarray(loc.start,end))!==expected)throw Error('Saved evidence span mismatch');
  const id=record.id||record.evidenceId;
  if(records.some(x=>x.id===id))return id;
  records.push({id,baselineId,sourcePath,sourceHash:hash,range:{start:loc.start,endExclusive:end},spanHash:expected,nodeType:record.nodeType,kind:'reused-complete-node',origin:{kind:'reused-frozen-evidence',sourceArtifact:ref(key,pointer)}});return id;
}
const oldExport=astCatalog.get('REQUEST-WRAPPER-AST-07063');
reuse(oldExport,'ast-evidence','/'+astRows.findIndex(r=>(r.id||r.evidenceId)==='REQUEST-WRAPPER-AST-07063'));
const exportLoc=oldExport.locator;
const exportSpan=raw.subarray(exportLoc.start,exportLoc.endExclusive);
const alias=Buffer.from('Emn as fkn');
const aliasStart=exportSpan.indexOf(alias);
if(aliasStart<0||exportSpan.indexOf(alias,aliasStart+1)!==-1)throw Error('Actual export specifier lookup ambiguous');
const exportEvidence=add(initial.sourcePath,initial.sourceHash,exportLoc.start+aliasStart,exportLoc.start+aliasStart+alias.length,'ExportSpecifier','exact-specifier-with-saved-AST-binding',{kind:'export-specifier-lookup',sourceArtifact:ref('ast','/files/2/exports/0/bindings/6312')});
const savedIds=['CGP-E00121','CGP-E00152','CGP-E00153','CGP-E00154','CGP-E00031','CGP-E00779','CGP-E00786','CGP-E00792','CGP-E00879','CGP-E00881','CGP-E00883','CGP-E01504','CGP-E01565','CGP-E01790','CGP-E01791','CGP-E01848'];
for(const id of savedIds)reuse(projectCatalog.get(id),'project-evidence','/'+projectRows.findIndex(r=>r.evidenceId===id));
const guardIds=['RG-025','RG-026','RG-027','RG-032','RG-139','RG-143'];
for(const id of guardIds){const i=docs.guards.evidence.findIndex(x=>x.id===id);reuse(docs.guards.evidence[i],'guards','/evidence/'+i);}
const semanticReviews=[
 {id:'PUP-R01',scope:'Six complete predicates/helpers',classification:'data-eligibility-predicate; product-mode-unknown',evidenceIds:[fragmentEvidence.id,...functions.map(x=>x.evidenceId)],facts:[
  'Emn returns bO(project) && xO(project) === open-default.',
  'vO accepts a string-like id only when its optional startsWith(g-p-) call returns true; yO checks string gizmo.id, string gizmo.display.name, and absent sharing or array sharing.subjects.',
  'bO requires yO, vO, absent/null first_party_project_type, null gizmo_snorlax_type, share_recipient=private, hasSharingSubjects !== true, and no sharing.subjects.',
  'xO requires a non-null project and a memory_scope property in gizmo; xmn maps project_v2 to project-only and every other value to open-default. Missing memory_scope yields undefined and fails Emn.',
  'The six complete function bodies contain no network/IPC calls or direct chat/work/codex mode/feature-flag/environment reads.'],unknowns:[
  'Member methods may have caller-controlled implementations; this is ordinary source structure rather than a runtime purity proof.',
  'The original enclosing lexical scope and possible later assignments to these helper identifiers are not established by the finite fragment. Saved AST proves Emn as fkn export identity, while the exact original-module definition binding remains limited.',
  'ID prefix and gizmo data fields do not establish ChatGPT-exclusive product ownership, server origin, Codex visibility or complete caller denominator.'],confirmedExclude:false},
 {id:'PUP-R02',scope:'Preserved settings localFolders consumer',classification:'complete-module-binding-reused; outer-gates-unknown',sourceArtifact:ref('project','/modeBoundaryReview/1'),evidenceIds:['CGP-E00779','CGP-E00152','CGP-E01565','CGP-E01848','CGP-E00786','CGP-E00792','CGP-E00031','CGP-E00879','CGP-E00881','CGP-E00883','CGP-E00154','CGP-E01504','CGP-E01790','CGP-E01791'],facts:[
  'The complete localFolders property uses s && L && je(i), with i bound to the project prop and je bound to initial.fkn in the saved complete-module AST.',
  's is the local result of c(rt), c imported from shared.Ban. Its implementation and runtime value are outside this chain.',
  'L is initialized from the Pt-body local Re (binding-448), assigned Me(Fe,a) or the memo cache n[13]. Me is imported initial.gkn; Fe is the Pt-body local project field, and a is projectCrudStatus.',
  'Pt-body Re shadows the Program import Re from initial.rOn. Connecting L to rOn by spelling would be incorrect.',
  'The localFolders branch renders imported at from local-folders-section.t with disabled/onSavingChange/projectId/projectName; that downstream implementation is not reviewed here.'],unknowns:['gkn implementation, c(rt) implementation, memo values, entitlement/platform gates, mounting and runtime reachability remain unknown.'],confirmedExclude:false},
 {id:'PUP-R03',scope:'Existing shared settings caller and dedicated route guards',classification:'inherited-static-context; not-exclusive-caller-proof',sourceArtifact:ref('guards','/notes/8'),evidenceIds:guardIds,facts:[
  'Frozen pss/Dos/jos notes trace the same lazy settings export into sidebar settings that also carries Work and local task context; this finite predicate review does not establish that all contexts can satisfy the localFolders branch.',
  'The dedicated sFs project route has its own mapping/redirect and default oZ.allowWork=false boundary. It cannot replace the shared settings caller or classify the localFolders predicate as removable.'],unknowns:['Complete callers, original outer lexical scope and actual mode/flag/data values remain unknown.'],confirmedExclude:false}
];
const refs=[
 ['ast','/files/2/exports/0/bindings/6312'],['ast','/files/2/exports/0/evidenceId'],
 ['project','/modules/1/calls/356'],['project','/modules/1/lexicalBindings/68'],['project','/modules/1/lexicalBindings/395'],['project','/modules/1/lexicalBindings/398'],['project','/modules/1/lexicalBindings/8'],['project','/modules/1/lexicalBindings/446'],['project','/modules/1/lexicalBindings/447'],['project','/modules/1/lexicalBindings/448'],['project','/modules/1/lexicalBindings/69'],['project','/modules/1/calls/295'],['project','/modules/1/assignments/177'],['project','/modules/1/assignments/178'],['project','/modules/1/targetedReview/localFoldersProperty/0'],['guards','/notes/8'],['guards','/notes/10']
].map(([key,pointer])=>({sourceArtifact:ref(key,pointer)}));
const scriptPath='scripts/analysis/project_upstream_review.mjs';
const scripts=[scriptPath,'scripts/analysis/verify_project_upstream.py'].map(p=>{const b=fs.readFileSync(path.join(root,p));return{path:p,bytes:b.length,sha256:sha(b)};});
const sourceInputs=sourceFiles.map(f=>({path:path.relative(root,path.join(sourceRoot,f.sourcePath.replace(/^app\.asar\//,''))),sourcePath:f.sourcePath,bytes:f.bytes,sha256:f.sourceHash}));
const result={schemaVersion:1,baselineId,status:'finite-fragment-static-review; original-module-scope-and-runtime-unknown',inputs,sourceInputs,scripts,sourceFiles,
 reproduction:{scriptPath,scriptSha256:sha(fs.readFileSync(path.join(root,scriptPath))),command:'/Users/nallylin/.nvm/versions/node/v22.23.2/bin/node '+scriptPath,parserPath,parserSha256:sha(fs.readFileSync(parserPath))},
 scope:{selectedChain:'settings.je -> initial.fkn -> local Emn candidate and five direct/transitive predicate helpers',jsonlPointerConvention:'JSONL is materialized as an ordered array of records; sourceArtifact.jsonPointer /N points to zero-based record N. No synthetic alias object is used.',newWholeLargeBundleAst:false,targetExecuted:false,uiUsed:false,authRead:false,personalHistoryRead:false,modelCalls:false,fragment:{range:{start,endExclusive:stop},bytes:stop-start,evidenceId:fragmentEvidence.id,completeProgramFragment:true,totalTopLevelFunctionDeclarations:topFunctions.length,astNodes},selectedFunctionDenominator:6,allInitialFunctionDenominator:'unknown',consumerCoverage:'One saved localFolders property and its saved lexical references; not all fkn consumers'},
 exportContract:{importLocal:'je',importedName:'fkn',exportLocal:'Emn',sourceArtifact:ref('ast','/files/2/exports/0/bindings/6312'),evidenceIds:['CGP-E00152','CGP-E01565',exportEvidence.id,'REQUEST-WRAPPER-AST-07063'],identityStatus:'saved-complete-module-export-alias-confirmed; candidate-definition-fragment-bound',originalModuleDefinitionScope:'unknown'},
 functions,references:refs,semanticReviews,
 summary:{selectedFunctions:functions.length,selectedCalls:functions.reduce((a,f)=>a+f.calls.length,0),fragmentBytes:stop-start,evidenceRecords:records.length,freshEvidenceRecords:records.filter(r=>r.id.startsWith('PUP-')).length,reusedEvidenceRecords:records.filter(r=>!r.id.startsWith('PUP-')).length,confirmedModeExclusions:0,runtimeVerifiedChains:0},
 limitations:['No full initial/shared AST was newly scanned; saved indexes do not include a complete original-module definition binding for Emn.','A fragment Program proves local helper bindings inside that fragment, not the original full-module lexical context or reassignment denominator.','Old journals are checked only for referenced spans; no claim that all historical producer pins or all rows were independently validated.','Semantic reviews are manual and use exact complete selected nodes plus saved complete-module consumers; identity/range extraction is reproducible.']};
for(const record of records){
  record.claim=record.kind+'; exact source node/span identity only, without runtime or product-mode inference';
  record.locator={kind:'byte-range',start:record.range.start,endExclusive:record.range.endExclusive};
  record.spanSha256=record.spanHash;
  record.method=record.origin.kind==='fresh-fragment-ast'?'Babel 8.0.4 finite complete-fragment AST plus source/byte-range SHA256':record.origin.kind==='reused-frozen-evidence'?'Frozen source-artifact reference plus source/byte-range SHA256; no fresh AST for reused nodes':'Exact specifier byte lookup within saved complete export declaration and saved AST binding';
  record.confidence='high-for-coordinate-identity';
  record.verificationStatus='static-source-span-verified; runtime-unverified; target-code-not-executed';
}
fs.mkdirSync(out,{recursive:true});
fs.writeFileSync(path.join(out,'review.json'),JSON.stringify(result,null,2)+'\n');
fs.writeFileSync(path.join(out,'evidence.jsonl'),records.map(r=>JSON.stringify(r)).join('\n')+'\n');
console.log(JSON.stringify({summary:result.summary,fragment:result.scope.fragment,scriptSha256:result.reproduction.scriptSha256}));
