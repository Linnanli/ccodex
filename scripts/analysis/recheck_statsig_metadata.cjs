#!/usr/bin/env node
// Reparse only the complete frozen statement located by the initial AST pass.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const parser=require('/private/tmp/ccodex-rea-tooling/install/node_modules/@babel/parser');
const dir=path.resolve('.analysis-local/embedded-dependency-work-v2');
const baseline=JSON.parse(fs.readFileSync('.analysis-local/current-baseline.json','utf8'));
const original=JSON.parse(fs.readFileSync(path.join(dir,'embedded-dependency-contracts.json'),'utf8'));
const inputEvidence=fs.readFileSync(path.join(dir,'evidence.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
const priorContract=original.contracts.find(c=>c.id==='bundle-hint-004');
const enclosing=inputEvidence.find(e=>e.id===priorContract.evidenceRefs[0]);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const source=fs.readFileSync(path.join(baseline.extractedDirectory,enclosing.sourcePath.replace(/^app.asar\//,'')));
if(sha(source)!==enclosing.sourceHash)throw Error('Source hash differs');
const span=source.subarray(enclosing.locator.start,enclosing.locator.endExclusive);if(sha(span)!==enclosing.spanHash)throw Error('Prior AST statement changed');
const text=span.toString('utf8');if(!Buffer.from(text).equals(span))throw Error('Lossy UTF8');
const ast=parser.parse(text,{sourceType:'module',errorRecovery:false});
if(ast.program.body.length!==1||ast.program.body[0].type!=='VariableDeclaration')throw Error('Expected one complete program variable declaration');
const producer=ast.program.body[0].declarations.find(n=>n.id.name==='Fg');if(!producer)throw Error('Fg declaration missing');
const fn=producer.init.arguments[0];if(fn.type!=='ArrowFunctionExpression'||fn.params[0]?.name!=='e')throw Error('Factory export parameter differs');
const ignored=new Set(['loc','comments','leadingComments','trailingComments','innerComments','extra','tokens','errors']);
const kids=n=>Object.entries(n).filter(([k])=>!ignored.has(k)).flatMap(([,v])=>Array.isArray(v)?v.filter(x=>x&&typeof x.type==='string'):v&&typeof v.type==='string'?[v]:[]);
const lit=n=>n?.type==='StringLiteral'?n.value:n?.type==='TemplateLiteral'&&n.expressions.length===0?n.quasis[0].value.cooked:null;
const prop=n=>n?.computed?lit(n.property||n.key):n?.property?.name||n?.key?.name||lit(n?.key);
const walk=(n,cb)=>{cb(n);for(const c of kids(n))walk(c,cb);};
const assignments=[],metadata=[];walk(fn,n=>{if(n.type==='AssignmentExpression')assignments.push(n);if(n.type==='ObjectExpression'&&n.properties.some(p=>prop(p)==='sdkVersion'&&p.value?.object?.name==='e'&&prop(p.value)==='SDK_VERSION')&&n.properties.some(p=>prop(p)==='sdkType'&&lit(p.value)==='js-mono'))metadata.push(n);});
const declarations=assignments.filter(n=>n.left.object?.name==='e'&&prop(n.left)==='SDK_VERSION'&&lit(n.right)==='3.34.0');
const providers=assignments.filter(n=>n.left.object?.name==='e'&&prop(n.left)==='StatsigMetadataProvider'&&n.right.type==='ObjectExpression'&&['get','add'].every(k=>n.right.properties.some(p=>prop(p)===k)));
const empty=assignments.filter(n=>n.left.object?.name==='e'&&prop(n.left)==='StatsigMetadataProvider'&&n.right.type==='AssignmentExpression');
if(declarations.length!==1||providers.length!==1||metadata.length!==1||empty.length!==1)throw Error('Actual provider/init/version counts differ');
function canonical(n){if(Array.isArray(n))return n.map(canonical);if(n&&typeof n==='object'){const x={};for(const k of Object.keys(n).sort())if(!ignored.has(k)&&!['start','end'].includes(k))x[k]=canonical(n[k]);return x;}return n;}
const firstPath=path.resolve('.analysis-local/embedded-dependency-work/embedded-dependency-contracts.json'),firstEvPath=path.resolve('.analysis-local/embedded-dependency-work/evidence.jsonl');
const first=JSON.parse(fs.readFileSync(firstPath,'utf8')),firstContract=first.contracts.find(c=>c.id==='statsig-metadata-renderer');
const firstEv=fs.readFileSync(firstEvPath,'utf8').trim().split('\n').map(JSON.parse).find(e=>e.id===firstContract.boundaries[0].evidenceRef);
const priorSource=fs.readFileSync(path.join(baseline.extractedDirectory,firstEv.sourcePath.replace(/^app.asar\//,'')));if(sha(priorSource)!==firstEv.sourceHash)throw Error('Renderer source differs');
const priorSpan=priorSource.subarray(firstEv.locator.start,firstEv.locator.endExclusive);if(sha(priorSpan)!==firstEv.spanHash)throw Error('Renderer production factory changed');
const oldFn=parser.parse('var '+priorSpan.toString('utf8')+';',{sourceType:'module'}).program.body[0].declarations[0].init.arguments[0];
const currentBody=JSON.stringify(canonical(fn.body)),oldBody=JSON.stringify(canonical(oldFn.body));
const evidence=[];function ev(n,claim){const start=enclosing.locator.start+Buffer.byteLength(text.slice(0,n.start)),end=enclosing.locator.start+Buffer.byteLength(text.slice(0,n.end));const b=source.subarray(start,end);if(!b.equals(Buffer.from(text.slice(n.start,n.end))))throw Error('Span mismatch');const id='EMBDEP2R-E'+String(evidence.length+1).padStart(5,'0');evidence.push({id,baselineId:baseline.baselineId,claim,sourcePath:enclosing.sourcePath,sourceHash:enclosing.sourceHash,locator:{kind:'byte-range',start,endExclusive:end},spanHash:sha(b),method:'supplemental-babel-ast-fragment-from-verified-complete-statement',confidence:'confirmed',verificationStatus:'static-confirmed; runtime-unverified'});return id;}
const versionRef=ev(declarations[0],'Metadata factory export parameter e.SDK_VERSION declares 3.34.0');
const refs=[versionRef,ev(metadata[0],'Provider sdkVersion consumes exact exported SDK_VERSION and sdkType js-mono'),ev(providers[0],'Actual StatsigMetadataProvider object has get/add interfaces'),ev(producer,'Complete emitted main metadata factory Fg'),ev(empty[0],'Provider export clearing initialization is distinct from actual provider object assignment')];
const comparison={priorArtifactSha256:sha(fs.readFileSync(firstPath)),priorContractId:firstContract.id,priorEvidenceId:firstEv.id,priorSourceHash:firstEv.sourceHash,priorSpanHash:firstEv.spanHash,comparison:'Babel AST callback body after stripping positions/comments/extra; identifiers and properties retained',bodyShapeEqual:currentBody===oldBody,currentBodyShapeSha256:sha(currentBody),rendererBodyShapeSha256:sha(oldBody),scope:'Only metadata callback; not entire SDK or upstream distribution'};
const contract={...priorContract,investigationStatus:'source-declaration-bound',sourceSelfReportConfidence:'confirmed',reason:undefined,selfReportedSdkVersion:'3.34.0',specificPackage:null,factoryBinding:'Fg',evidenceRefs:refs,versionEvidenceRef:versionRef,comparisonToRendererMetadata:comparison,correction:'Initial pass counted the export-clearing assignment and the provider object assignment together; this pass binds only the object with get/add.',supersedes:{artifactPath:path.join(dir,'embedded-dependency-contracts.json'),artifactSha256:sha(fs.readFileSync(path.join(dir,'embedded-dependency-contracts.json'))),id:priorContract.id,priorInvestigationStatus:priorContract.investigationStatus},limitations:['Metadata-body equality does not establish identical SDK implementation or unmodified upstream distribution.','Exact @oai-statsig package and mode/runtime behavior remain unresolved.']};
const result={baselineId:baseline.baselineId,generatedAtUtc:new Date().toISOString(),scope:{candidateCount:1,candidateId:'bundle-hint-004',parsedCompleteStatementBytes:span.length,fullSourceBytes:source.length,parsedFiles:1,parseErrors:0},contract,inputEvidence:{path:path.join(dir,'evidence.jsonl'),sha256:sha(fs.readFileSync(path.join(dir,'evidence.jsonl'))),evidenceId:enclosing.id,sourceHash:enclosing.sourceHash,spanHash:enclosing.spanHash},comparison};
fs.writeFileSync(path.join(dir,'statsig-recheck.json'),JSON.stringify(result,null,2)+'\n');fs.writeFileSync(path.join(dir,'statsig-recheck-evidence.jsonl'),evidence.map(e=>JSON.stringify(e)).join('\n')+'\n');console.log(JSON.stringify({scope:result.scope,evidence:evidence.length,comparison},null,2));
