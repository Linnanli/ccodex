// Parse frozen source as data; never import or execute a target module.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';

const [root, baseline, sourcePath, destination] = process.argv.slice(2);
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const pin = b => ({bytes:b.length,sha256:hash(b)});
const out = path.join(root,'analysis',baseline);
const ledgerBytes=fs.readFileSync(path.join(out,'functional-entry-ledger.json'));
const ledger=JSON.parse(ledgerBytes);
if(ledger.baselineId!==baseline)throw Error('Baseline mismatch');
const entries=ledger.entries.filter(e=>e.sourceCoordinates.sourcePath===sourcePath);
if(!entries.length)throw Error('No requested entries');
const rel=sourcePath.replace(/^app\.asar\//,'');
const source=fs.readFileSync(path.join(root,'.analysis-local/baselines',baseline,'extracted',rel));
const sourceHash=hash(source),text=source.toString('utf8');
for(const e of entries){
 const c=e.sourceCoordinates,r=c.byteRange;
 if(c.sourceHash!==sourceHash||r.start<0||r.endExclusive>source.length||r.start>=r.endExclusive)throw Error('Invalid source '+e.entryId);
 if(c.spanHash&&hash(source.subarray(r.start,r.endExclusive))!==c.spanHash)throw Error('Old span mismatch '+e.entryId);
}
const parserPath=path.join(root,'.analysis-local/global-state-storage-work/tooling/node_modules/@babel/parser/lib/index.js');
const parser=createRequire(import.meta.url)(parserPath);
const startedAtUtc=new Date().toISOString();
const ast=parser.parse(text,{sourceType:'unambiguous'});
// Sparse offsets avoid repeatedly encoding a multi-megabyte prefix.
const deltas=[{end:0,delta:0}];let delta=0;
for(let u=0;u<text.length;){const cp=text.codePointAt(u),w=cp>0xffff?2:1;
 if(cp>127){delta+=(cp<=0x7ff?2:cp<=0xffff?3:4)-w;deltas.push({end:u+w,delta});}u+=w;}
function byte(u){let lo=0,hi=deltas.length;while(lo<hi){const m=(lo+hi)>>>1;if(deltas[m].end<=u)lo=m+1;else hi=m;}return u+deltas[lo-1].delta;}
function char(b){let lo=0,hi=text.length;while(lo<hi){const m=(lo+hi)>>>1;if(byte(m)<b)lo=m+1;else hi=m;}if(byte(lo)!==b)throw Error('Not a UTF8 boundary');return lo;}
const requested=entries.map(e=>({entry:e,a:char(e.sourceCoordinates.byteRange.start),z:char(e.sourceCoordinates.byteRange.endExclusive),best:null,parents:null})).sort((a,b)=>a.a-b.a);
const ignored=new Set(['loc','start','end','extra','comments','tokens','leadingComments','trailingComments','innerComments','errors']);
const functionTypes=new Set(['FunctionDeclaration','FunctionExpression','ArrowFunctionExpression','ClassMethod','ClassPrivateMethod','ObjectMethod']);
const bindingTypes=new Set(['VariableDeclarator','AssignmentExpression','FunctionDeclaration','ClassDeclaration']);
const stack=[];let nodeCount=0;
function walk(n){
 nodeCount++;
 let lo=0,hi=requested.length;while(lo<hi){const m=(lo+hi)>>>1;if(requested[m].a<n.start)lo=m+1;else hi=m;}
 for(let j=lo;j<requested.length&&requested[j].a<n.end;j++){
  const q=requested[j];if(q.z<=n.end&&(!q.best||n.end-n.start<q.best.end-q.best.start)){
   q.best=n;q.parents=stack.slice();
  }
 }
 stack.push(n);
 for(const k of Object.keys(n)){
  if(ignored.has(k))continue;const v=n[k];
  if(Array.isArray(v)){for(const child of v)if(child&&typeof child.type==='string')walk(child);}
  else if(v&&typeof v.type==='string')walk(v);
 }
 stack.pop();
}
walk(ast.program);
const cache=new WeakMap();
function loc(n){if(cache.has(n))return cache.get(n);const a=byte(n.start),z=byte(n.end);
 const v={sourcePath,sourceHash,byteRange:{start:a,endExclusive:z},spanHash:hash(source.subarray(a,z)),nodeType:n.type};cache.set(n,v);return v;}
const expression=n=>text.slice(n.start,n.end);
function name(n){
 if(n.type==='VariableDeclarator')return expression(n.id);
 if(n.type==='AssignmentExpression')return expression(n.left);
 if(n.type==='ClassMethod'||n.type==='ClassPrivateMethod'||n.type==='ObjectMethod')return expression(n.key);
 return n.id?.name??null;
}
function describe(n,ancestors){
 let display=name(n);
 if(!display&&(n.type==='ArrowFunctionExpression'||n.type==='FunctionExpression')){
  const p=ancestors[ancestors.length-1];
  if(p?.type==='VariableDeclarator'&&p.init===n)display=name(p);
  if(p?.type==='AssignmentExpression'&&p.right===n)display=name(p);
  if(p?.type==='ObjectProperty'&&p.value===n)display=expression(p.key);
 }
 return {name:display,...loc(n)};
}
function guard(parent,child){
 if(parent.type==='IfStatement'&&parent.test!==child)return{kind:parent.type,branch:parent.consequent===child?'consequent':'alternate',condition:loc(parent.test),expression:expression(parent.test)};
 if(parent.type==='ConditionalExpression'&&parent.test!==child)return{kind:parent.type,branch:parent.consequent===child?'consequent':'alternate',condition:loc(parent.test),expression:expression(parent.test)};
 if(parent.type==='LogicalExpression'&&parent.right===child)return{kind:parent.type,branch:parent.operator==='&&'?'truthy-RHS':parent.operator==='||'?'falsy-RHS':'nullish-RHS',condition:loc(parent.left),expression:expression(parent.left)};
 if(parent.type==='SwitchCase'&&parent.test)return{kind:parent.type,branch:'case',condition:loc(parent.test),expression:expression(parent.test),caveat:'Lexical case membership only; preceding fallthrough may also reach it.'};
 return null;
}
const rows=requested.map(q=>{
 if(!q.best)throw Error('No enclosing node '+q.entry.entryId);
 const chain=[...q.parents,q.best];
 let fnIndex=-1;for(let j=chain.length-1;j>=0;j--)if(functionTypes.has(chain[j].type)){fnIndex=j;break;}
 const functions=chain.map((n,j)=>({n,j})).filter(x=>functionTypes.has(x.n.type));
 const bind=chain.map((n,j)=>({n,j})).find(x=>bindingTypes.has(x.n.type));
 const classNode=chain.findLast(n=>n.type==='ClassDeclaration'||n.type==='ClassExpression');
 const guards=[];
 for(let j=0;j<chain.length-1;j++){const g=guard(chain[j],chain[j+1]);if(g)guards.push({...g,completeControl:loc(chain[j]),insideNearestCallable:j>fnIndex});}
 const r=q.entry.sourceCoordinates.byteRange;
 return{entryId:q.entry.entryId,entryKind:q.entry.entryKind,
  originalSourceCoordinates:q.entry.sourceCoordinates,
  freshlyHashedSourceSpan:{sourcePath,sourceHash,byteRange:{start:r.start,endExclusive:r.endExclusive},spanHash:hash(source.subarray(r.start,r.endExclusive))},
  matchedNode:loc(q.best),exactAstRange:byte(q.best.start)===r.start&&byte(q.best.end)===r.endExclusive,
  lexicalCallable:fnIndex<0?null:describe(chain[fnIndex],chain.slice(0,fnIndex)),
  callableAncestry:functions.map(x=>describe(x.n,chain.slice(0,x.j))),
  outerBinding:bind?describe(bind.n,chain.slice(0,bind.j)):null,
  lexicalClass:classNode?describe(classNode,[]):null,
  structuralGuards:guards,
  bindingMeaning:'Lexical ownership and structural conditions; values, actual instance, mount/call sites and product mode are not established.'};
});
const result={schemaVersion:1,baselineId:baseline,sourcePath,sourceHash,sourceBytes:source.length,
 parser:{path:parserPath,...pin(fs.readFileSync(parserPath))},ledger:pin(ledgerBytes),
 startedAtUtc,completedAtUtc:new Date().toISOString(),fullProgramParsed:true,nodeCount,parserErrors:ast.errors?.length??0,
 sourceEntries:rows.length,exactAstMatches:rows.filter(r=>r.exactAstRange).length,entries:rows,
 targetCodeExecuted:false,originalClientRunsAdded:0,modelSubmissionsAdded:0,newReaRuns:0};
fs.writeFileSync(destination,JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({sourcePath,entries:rows.length,nodeCount,exactAstMatches:result.exactAstMatches,output:destination}));
