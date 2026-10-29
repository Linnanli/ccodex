// Reuse saved Program bindings; parse only exact selected functions and small wrappers.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';

const root=process.cwd(), baseline='codex-26.1007.30912-c5b273322a83';
const work=path.join(root,'.analysis-local/product-flow-ownership-work');
const out=path.join(work,'selected-units');
if(fs.existsSync(out))throw Error('Preserve existing extraction');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const parserPath=path.join(root,'.analysis-local/global-state-storage-work/tooling/node_modules/@babel/parser/lib/index.js');
const parser=createRequire(import.meta.url)(parserPath);
const primary=JSON.parse(fs.readFileSync(path.join(work,'primary-01/source-contracts.json')));
const initial=JSON.parse(fs.readFileSync(path.join(root,'.analysis-local/submission-host-instance-work/initial-host-scope-bindings.json')));
const frozen=path.join(root,'.analysis-local/baselines',baseline,'extracted');
const sourceCache=new Map(), units=[], fragments=[];
function bytes(sourcePath,expected){
 if(!sourceCache.has(sourcePath)){
  const b=fs.readFileSync(path.join(frozen,sourcePath.replace(/^app.asar\//,'')));
  if(hash(b)!==expected)throw Error('Source identity mismatch '+sourcePath);
  sourceCache.set(sourcePath,b);
 }
 return sourceCache.get(sourcePath);
}
function add(name,loc){
 const sourcePath=loc.sourcePath??'app.asar/webview/assets/app-initial-6350d04672d0.js';
 const sourceHash=loc.sourceHash??loc.source?.sha256;
 const {start,endExclusive}=loc.byteRange;
 const source=bytes(sourcePath,sourceHash),b=source.subarray(start,endExclusive);
 if(hash(b)!==(loc.spanHash??loc.spanSha256))throw Error('Span mismatch '+name);
 const text=b.toString('utf8'), ast=parser.parse(text,{sourceType:'module'});
 const u={name,sourcePath,sourceHash,byteRange:{start,endExclusive},spanHash:hash(b),bytes:b.length,sourceFilename:name+'.txt',fragmentParsed:true};
 units.push(u);
 function walk(n,parents=[]){
  if(!n||typeof n.type!=='string')return;
  const owner=parents.findLast(p=>['FunctionDeclaration','FunctionExpression','ArrowFunctionExpression'].includes(p.type));
  const ownerName=owner?.id?.name??null;
  const wantedDeclaration=n.type==='VariableDeclarator'&&['Qt','er','ht','pt','vr','mt','U','W','ne','R','z','B'].includes(n.id?.name);
  const wantedCallback=n.type==='AssignmentExpression'&&n.left.type==='Identifier'&&n.left.name==='Nr'&&n.right.type==='ArrowFunctionExpression';
  if(wantedDeclaration||wantedCallback){
   const target=wantedCallback?n.right:n;
   const a=start+Buffer.byteLength(text.slice(0,target.start)),z=start+Buffer.byteLength(text.slice(0,target.end));
   fragments.push({id:name+':'+(wantedCallback?'Nr':n.id.name),owner:ownerName,nodeType:target.type,sourcePath,sourceHash,byteRange:{start:a,endExclusive:z},spanHash:hash(source.subarray(a,z)),expression:text.slice(target.start,target.end)});
  }
  for(const [k,v]of Object.entries(n)){
   if(['loc','start','end','extra','comments','tokens','leadingComments','trailingComments','innerComments'].includes(k))continue;
   if(Array.isArray(v)){for(const c of v)if(c&&typeof c.type==='string')walk(c,[...parents,n]);}
   else if(v&&typeof v.type==='string')walk(v,[...parents,n]);
  }
 }
 walk(ast.program);
 return b;
}
fs.mkdirSync(out,{recursive:true});
for(const name of ['wzt','Tzt','Ezt','M9','jRt','NRt','VIt','$X']){
 const row=primary.programDefinitions.find(x=>x.name===name);
 if(row?.definitions.length!==1)throw Error('Nonunique Program definition '+name);
 fs.writeFileSync(path.join(out,name+'.txt'),add(name,row.definitions[0]),{flag:'wx'});
}
for(const name of ['dFs','kJa','cPt','iPt','vS']){
 const row=initial.programBindings.find(x=>x.name===name);
 if(row?.declarations.length!==1)throw Error('Nonunique saved Program binding '+name);
 fs.writeFileSync(path.join(out,name+'.txt'),add(name,row.declarations[0].declaration),{flag:'wx'});
}
const home=fs.readFileSync(path.join(frozen,'webview/assets/home-composer-route-db001185da2b.js'));
parser.parse(home.toString('utf8'),{sourceType:'module'});
units.push({name:'home-wrapper',sourcePath:'app.asar/webview/assets/home-composer-route-db001185da2b.js',sourceHash:hash(home),byteRange:{start:0,endExclusive:home.length},spanHash:hash(home),bytes:home.length,sourceFilename:'home-wrapper.txt',fragmentParsed:true});
fs.writeFileSync(path.join(out,'home-wrapper.txt'),home,{flag:'wx'});
const selectedImports=primary.imports.flatMap(i=>i.specifiers.filter(s=>['Dbe','ik','NT','JAe','gg','yf'].includes(s.local)).map(s=>({module:i.module,...s,importDeclaration:{sourcePath:i.sourcePath,sourceHash:i.sourceHash,byteRange:i.byteRange,spanHash:i.spanHash}})));
const exportT=primary.programExports.filter(x=>x.exported==='t');
if(exportT.length!==1||exportT[0].local!=='wzt')throw Error('Home export identity changed');
fs.writeFileSync(path.join(out,'contracts.json'),JSON.stringify({baselineId:baseline,parser:{path:parserPath,sha256:hash(fs.readFileSync(parserPath))},method:'Saved complete-Program lexical declarations plus exact-function parses; initial/ shared Programs not reparsed.',units,fragments,selectedImports,homeExport:exportT[0],primaryFullProgramParseRef:'../primary-01/source-contracts.json',targetModuleEvaluated:false,originalClientRunsAdded:0,modelSubmissionsAdded:0,fullAnalysisCompleted:false},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({units:units.length,bytes:units.reduce((s,u)=>s+u.bytes,0),fragments:fragments.map(f=>f.id),out}));
