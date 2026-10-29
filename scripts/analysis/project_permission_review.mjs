#!/usr/bin/env node
// One 47-byte predicate and one 70-byte complete memo expression; no target execution.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';

const root=process.cwd(), baselineId='codex-26.1007.30912-c5b273322a83';
const output=path.join(root,'.analysis-local/project-permission-work');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const parserPath='/private/tmp/ccodex-rea-tooling/install/node_modules/@babel/parser/lib/index.js';
const parser=createRequire(import.meta.url)(parserPath);
const inputPaths={baseline:'.analysis-local/current-baseline.json',project:'.analysis-local/mode-boundary-work/project-review.json','project-evidence':'.analysis-local/mode-boundary-work/project-evidence.jsonl',ast:'.analysis-local/review-work/request-wrapper-ast.json','ast-evidence':'.analysis-local/review-work/request-wrapper-ast-evidence.jsonl','prior-review':'.analysis-local/project-upstream-work/review.json','prior-evidence':'.analysis-local/project-upstream-work/evidence.jsonl','prior-manifest':'.analysis-local/project-upstream-work/frozen-manifest.json'};
const bytes=Object.fromEntries(Object.entries(inputPaths).map(([k,p])=>[k,fs.readFileSync(path.join(root,p))]));
const inputs=Object.entries(inputPaths).map(([key,p])=>({key,path:p,bytes:bytes[key].length,sha256:hash(bytes[key])}));
const documents=Object.fromEntries(Object.entries(bytes).filter(([k])=>!k.endsWith('evidence')).map(([k,b])=>[k,JSON.parse(b)]));
if(Object.values(documents).some(d=>d.baselineId!==baselineId))throw Error('Input baseline mismatch');
const sourceRoot=path.resolve(documents.baseline.extractedDirectory);
const sourceFiles=[], rawSources=new Map();
function source(sourcePath,sourceHash){
  if(rawSources.has(sourcePath))return rawSources.get(sourcePath);
  const p=path.resolve(sourceRoot,sourcePath.replace(/^app\.asar\//,''));
  if(!p.startsWith(sourceRoot+path.sep))throw Error('Outside fixed extracted root');
  const raw=fs.readFileSync(p);
  if(hash(raw)!==sourceHash)throw Error('Source hash mismatch');
  sourceFiles.push({sourcePath,sourceHash,bytes:raw.length});rawSources.set(sourcePath,raw);return raw;
}
const initial=documents.ast.files[2], settings=documents.project.modules[1];
const actualExport=initial.exports[0].bindings[6499];
if(actualExport.local!=='ymn'||actualExport.exported!=='gkn'||!initial.sourcePath.endsWith('/app-initial-6350d04672d0.js'))throw Error('Source-qualified export changed');
const initialRaw=source(initial.sourcePath,initial.sourceHash), settingsRaw=source(settings.sourcePath,settings.sourceHash);
const predicateRange={start:1978766,endExclusive:1978813}, memoRange={start:31818,endExclusive:31888};
const predicateText=initialRaw.subarray(predicateRange.start,predicateRange.endExclusive).toString();
const memoText=settingsRaw.subarray(memoRange.start,memoRange.endExclusive).toString();
if(predicateText!=='function ymn(e,t){return t===`allowed`&&e===!0}')throw Error('Predicate range changed');
if(memoText!=='n[11]!==a||n[12]!==Fe?(Re=Me(Fe,a),n[11]=a,n[12]=Fe,n[13]=Re):Re=n[13]')throw Error('Memo expression changed');
const predicateProgram=parser.parse(predicateText,{sourceType:'module',errorRecovery:false}).program;
const predicate=predicateProgram.body[0];
if(predicateProgram.body.length!==1||predicate.type!=='FunctionDeclaration'||predicate.id.name!=='ymn')throw Error('Not exactly one complete predicate');
const memo=parser.parseExpression(memoText,{errorRecovery:false});
if(memo.type!=='ConditionalExpression'||memo.start!==0||memo.end!==memoText.length)throw Error('Not a complete conditional expression');
const records=[];let sequence=0;
const reference=(key,jsonPointer)=>({key,jsonPointer});
function emit(sourcePath,sourceHash,start,endExclusive,nodeType,kind,origin,id=null){
  const raw=source(sourcePath,sourceHash), span=raw.subarray(start,endExclusive);
  if(start<0||endExclusive<=start||endExclusive>raw.length)throw Error('Invalid range');
  const spanHash=hash(span), evidenceId=id||'PPM-E'+String(++sequence).padStart(4,'0');
  const result={id:evidenceId,baselineId,claim:kind+'; exact source/span identity without runtime or product-mode inference',sourcePath,sourceHash,range:{start,endExclusive},locator:{kind:'byte-range',start,endExclusive},spanHash,spanSha256:spanHash,nodeType,kind,origin,method:origin.kind==='fresh-fragment-ast'?'Babel 8.0.4 finite complete-function/expression AST and source/span SHA256':origin.kind==='reused-frozen-evidence'?'Frozen original evidence artifact reference and source/span SHA256; no fresh large-module AST':'Exact specifier lookup within saved complete export declaration and source-qualified export AST record',confidence:'high',confidenceScope:'coordinate-identity-only',verificationStatus:'static-source-span-verified; original-module-binding-and-runtime-unverified; target-code-not-executed'};
  records.push(result);return result;
}
const byteRange=(node,text,base)=>({start:base+Buffer.byteLength(text.slice(0,node.start)),endExclusive:base+Buffer.byteLength(text.slice(0,node.end))});
function nodeEvidence(node,text,base,file,kind){const r=byteRange(node,text,base);return emit(file.sourcePath,file.sourceHash,r.start,r.endExclusive,node.type,kind,{kind:'fresh-fragment-ast'});}
function walk(value,visit){if(!value||typeof value!=='object')return;if(typeof value.type==='string')visit(value);for(const[k,v]of Object.entries(value)){if(['loc','start','end','extra','comments','tokens','errors'].includes(k))continue;if(Array.isArray(v))for(const x of v)walk(x,visit);else if(v&&typeof v==='object')walk(v,visit);}}
const predicateEvidence=nodeEvidence(predicate,predicateText,predicateRange.start,initial,'complete-permission-predicate');
const returnEvidence=nodeEvidence(predicate.body.body[0].argument,predicateText,predicateRange.start,initial,'complete-predicate-return');
const memoEvidence=nodeEvidence(memo,memoText,memoRange.start,settings,'complete-memo-conditional');
const testEvidence=nodeEvidence(memo.test,memoText,memoRange.start,settings,'complete-memo-input-comparison');
const fnCalls=[];let predicateAstNodes=0,memoAstNodes=0;
walk(predicateProgram,n=>{predicateAstNodes++;if(['CallExpression','OptionalCallExpression','NewExpression'].includes(n.type))fnCalls.push(n);});
if(fnCalls.length!==0)throw Error('Predicate unexpectedly calls helpers');
const memoCalls=[], memoAssignments=[];
walk(memo,n=>{
  memoAstNodes++;
  if(n.type==='CallExpression'){
    if(n.callee.type!=='Identifier'||n.callee.name!=='Me')throw Error('Unexpected memo callee');
    const e=nodeEvidence(n,memoText,memoRange.start,settings,'complete-memo-computation-call');
    memoCalls.push({evidenceId:e.id,range:e.range,calleeName:'Me',arguments:n.arguments.map(a=>a.name),savedBindingReference:{sourceArtifact:reference('project','/modules/1/calls/295')},calleeBindingId:settings.calls[295].calleeBinding.bindingId,candidateUpstreamFunctionEvidenceId:predicateEvidence.id,upstreamStatus:'export-alias-confirmed; full-original-module-definition-binding-unknown'});
  }
  if(n.type==='AssignmentExpression'){
    const e=nodeEvidence(n,memoText,memoRange.start,settings,'complete-memo-assignment');
    const text=node=>memoText.slice(node.start,node.end);
    memoAssignments.push({evidenceId:e.id,range:e.range,operator:n.operator,left:text(n.left),rightNodeType:n.right.type,role:n.left.type==='Identifier'?'Pt-local-Re-write':'memo-slot-write'});
  }
});
if(memoCalls.length!==1||memoAssignments.length!==5)throw Error('Unexpected finite memo denominator');
const catalogs={};
for(const key of ['project-evidence','ast-evidence','prior-evidence'])catalogs[key]=bytes[key].toString().trim().split('\n').map(line=>JSON.parse(line));
function reuse(key,id){
  const row=catalogs[key].findIndex(r=>(r.id||r.evidenceId)===id);
  if(row<0)throw Error('Original evidence missing: '+id);
  const r=catalogs[key][row], range=r.range||r.locator||r.byteRange;
  const end=typeof range.endExclusive==='number'?range.endExclusive:range.end;
  const originalHash=r.sourceHash||r.sourceSha256, expected=r.spanHash||r.spanSha256;
  const raw=source(r.sourcePath,originalHash);
  if(hash(raw.subarray(range.start,end))!==expected)throw Error('Original evidence span changed');
  const result=emit(r.sourcePath,originalHash,range.start,end,r.nodeType,'reused-complete-node',{kind:'reused-frozen-evidence',sourceArtifact:reference(key,'/'+row)},id);
  if(result.spanHash!==expected)throw Error('Reused identity changed');return r;
}
const originalExport=reuse('ast-evidence','REQUEST-WRAPPER-AST-07063');
const loc=originalExport.locator, span=initialRaw.subarray(loc.start,loc.endExclusive), literal=Buffer.from('ymn as gkn');
const offset=span.indexOf(literal);
if(offset<0||span.indexOf(literal,offset+1)!==-1)throw Error('Export specifier not unique in saved export');
const exportEvidence=emit(initial.sourcePath,initial.sourceHash,loc.start+offset,loc.start+offset+literal.length,'ExportSpecifier','exact-source-qualified-gkn-export',{kind:'export-specifier-lookup',sourceArtifact:reference('ast','/files/2/exports/0/bindings/6499')});
const reusedIds=['CGP-E00121','CGP-E00154','CGP-E00779','CGP-E00786','CGP-E00879','CGP-E00881','CGP-E00883','CGP-E01504','CGP-E01790','CGP-E01791','CGP-E01848'];
for(const id of reusedIds)reuse('project-evidence',id);
reuse('prior-evidence','PUP-E0001');
const originalCall=catalogs['project-evidence'].find(r=>r.evidenceId==='CGP-E01504');
if(originalCall.range.start!==memoCalls[0].range.start||originalCall.range.endExclusive!==memoCalls[0].range.endExclusive)throw Error('Memo call did not match saved complete-module consumer');
const bindings=[69,396,446,447,448];
if(settings.lexicalBindings[69].importedName!=='gkn'||settings.lexicalBindings[447].name!=='Re'||!settings.lexicalBindings[447].scopeId.endsWith(':scope-88'))throw Error('Saved binding identity changed');
const refs=[['ast','/files/2/exports/0/bindings/6499'],['project','/modules/1/calls/295'],...bindings.map(i=>['project','/modules/1/lexicalBindings/'+i]),['project','/modules/1/assignments/177'],['project','/modules/1/assignments/178'],['project','/modules/1/targetedReview/localFoldersProperty/0'],['prior-review','/semanticReviews/1'],['prior-manifest','/files/0']].map(([key,pointer])=>({sourceArtifact:reference(key,pointer)}));
const scripts=['scripts/analysis/project_permission_review.mjs','scripts/analysis/verify_project_permission.py'].map(p=>{const b=fs.readFileSync(path.join(root,p));return{path:p,bytes:b.length,sha256:hash(b)};});
const sourceInputs=sourceFiles.map(f=>({path:path.relative(root,path.join(sourceRoot,f.sourcePath.replace(/^app\.asar\//,''))),sourcePath:f.sourcePath,bytes:f.bytes,sha256:f.sourceHash}));
const result={schemaVersion:1,baselineId,status:'finite-permission-and-status-calculation-review; original-module-identity-and-runtime-unknown',inputs,sourceArtifacts:inputs,sourceInputs,sourceFiles,scripts,
 reproduction:{scriptPath:scripts[0].path,scriptSha256:scripts[0].sha256,parserPath,parserSha256:hash(fs.readFileSync(parserPath)),command:'/Users/nallylin/.nvm/versions/node/v22.23.2/bin/node '+scripts[0].path},
 scope:{newWholeInitialOrSharedAst:false,targetExecuted:false,uiUsed:false,credentialsRead:false,personalHistoryRead:false,networkOrMutationCalls:false,modelCalls:false,selectedFunctionDenominator:1,selectedHelperDenominator:0,predicateRange,memoRange,predicateBytes:47,memoExpressionBytes:70,predicateAstNodes,memoExpressionAstNodes:memoAstNodes,jsonlPointerConvention:'Pinned JSONL files are materialized as ordered arrays; /N points to zero-based physical record N.',allInitialDefinitionOrAssignmentDenominator:'unknown',consumerCoverage:'One saved Pt Me(Fe,a) call and one exact complete memo expression; not all gkn consumers'},
 exportContract:{sourceArtifact:reference('ast','/files/2/exports/0/bindings/6499'),sourcePath:initial.sourcePath,sourceHash:initial.sourceHash,importLocal:'Me',importedName:'gkn',exportLocal:'ymn',evidenceIds:['CGP-E00154','CGP-E01504','REQUEST-WRAPPER-AST-07063',exportEvidence.id,predicateEvidence.id],bindingStatus:'Source-qualified import and saved export alias confirmed; candidate full function has local parameter scope, original full-module definition binding remains unknown'},
 functions:[{name:'ymn',evidenceId:predicateEvidence.id,range:predicateEvidence.range,parameterNames:predicate.params.map(p=>p.name),returnEvidenceId:returnEvidence.id,calls:[],bindingBasis:'Exactly one complete FunctionDeclaration fragment with parameter-bound e/t; no helpers/calls in this complete body.',originalModuleLexicalIdentity:'unknown'}],
 consumerExpressions:[{evidenceId:memoEvidence.id,range:memoEvidence.range,testEvidenceId:testEvidence.id,nodeType:'ConditionalExpression',calls:memoCalls,assignments:memoAssignments,savedBindingReference:{sourceArtifact:reference('project','/modules/1/assignments/177')},originalLocalReBindingId:settings.lexicalBindings[447].bindingId}],references:refs,
 semanticReviews:[
  {id:'PPM-R01',scope:'Complete permission predicate candidate',evidenceIds:[predicateEvidence.id,returnEvidence.id,exportEvidence.id],facts:['ymn returns true exactly when its second parameter strictly equals allowed and its first parameter strictly equals boolean true.','The complete 47-byte function contains no helper call, network/IPC, environment/feature flag or direct chat/work/codex mode read.','The saved settings import Me is initial.gkn; the saved source-qualified initial export maps gkn to ymn.'],unknowns:['Finite function parsing does not establish original initial outer scope, all same-name declarations or later assignments. No runtime inputs were observed.'],confirmedExclude:false},
  {id:'PPM-R02',scope:'Pt permission/status arguments and memo flow',evidenceIds:[memoEvidence.id,testEvidence.id,...memoCalls.map(x=>x.evidenceId),...memoAssignments.map(x=>x.evidenceId),...reusedIds],facts:['Fe is the Pt-body local value project.gizmo.current_user_permission?.can_write; a is the projectCrudStatus prop, and the saved complete-module call binds Me(Fe,a) to Program import binding-70.','When cached n[11] differs from a OR cached n[12] differs from Fe, Pt local Re is computed by Me(Fe,a), then n[11]=a, n[12]=Fe, n[13]=Re. Otherwise the same local Re is read from n[13].','L is initialized from this local Re; it shadows the separate same-name Program import Re from initial.rOn. No link to that import is made.','On the computation branch, this candidate predicate checks can_write===true and projectCrudStatus===allowed. The cache reuse branch is a recorded read, not an independently proven unconditional equivalence.','The saved localFolders consumer additionally requires s and the separate fkn eligibility predicate, so this permission computation alone is not its complete guard.'],unknowns:['can_write and projectCrudStatus producers/values; memo n initialization and invariants; original module definition binding; mounting, remaining s/fkn conditions and runtime product mode are not established.'],confirmedExclude:false}
 ],
 summary:{selectedFunctions:1,helperFunctions:0,functionCalls:0,consumerExpressions:1,consumerCalls:1,selectedCalls:1,memoAssignments:5,newAstBytes:117,evidenceRecords:records.length,freshEvidenceRecords:records.filter(r=>r.id.startsWith('PPM-')).length,reusedEvidenceRecords:records.filter(r=>!r.id.startsWith('PPM-')).length,confirmedModeExclusions:0,runtimeVerifiedChains:0},
 limitations:['No old frozen artifact/script was changed. Only one 47-byte complete candidate function and one 70-byte complete expression were freshly parsed.','Saved source-qualified bindings and exact shared call/assignment spans support the consumer dataflow; an original full initial module binding is not inferred from a fragment.','No runtime purity, cache invariant, product-mode ownership, exclusion or complete consumer denominator is established.','Reused journals are pinned as original bytes and only referenced spans are checked; all historical input chains are not claimed verified.']};
fs.mkdirSync(output,{recursive:true});fs.writeFileSync(path.join(output,'project-permission.json'),JSON.stringify(result,null,2)+'\n');fs.writeFileSync(path.join(output,'evidence.jsonl'),records.map(r=>JSON.stringify(r)).join('\n')+'\n');
console.log(JSON.stringify({summary:result.summary,scope:result.scope,scriptSha256:scripts[0].sha256}));
