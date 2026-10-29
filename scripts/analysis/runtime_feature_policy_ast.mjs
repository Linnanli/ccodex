// Bounded lexical binding query over four frozen whole Programs. No target module loads.
// Scope walk derived from scripts/analysis/runtime_boundary_ast.mjs.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
const [root,baseline,relative,outputDirectory]=process.argv.slice(2);
const sourcePath='app.asar/'+relative;
const inventory=JSON.parse(fs.readFileSync(path.join(root,'analysis',baseline,'files.json')));
const input=inventory.archiveFiles.find(x=>x.sourcePath===sourcePath);
if(!input)throw Error('Source not in fixed inventory');
const source=fs.readFileSync(path.join(root,'.analysis-local/baselines',baseline,'extracted',relative));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const sourceHash=hash(source),text=source.toString('utf8');
if(input.sha256!==sourceHash||input.bytes!==source.length)throw Error('Frozen source mismatch');
const parserPath=path.join(root,'.analysis-local/global-state-storage-work/tooling/node_modules/@babel/parser/lib/index.js');
const parser=createRequire(import.meta.url)(parserPath),startedAtUtc=new Date().toISOString();
const ast=parser.parse(text,{sourceType:'unambiguous'});
const skip = new Set(['loc','start','end','extra','comments','tokens','leadingComments','trailingComments','innerComments','errors']);
const functionTypes = new Set(['FunctionDeclaration','FunctionExpression','ArrowFunctionExpression','ClassMethod','ClassPrivateMethod','ObjectMethod']);
const nodes = [], scopes = [], parents = new WeakMap(), scopeAt = new WeakMap();
function scope(parent, node, kind) { const v = {parent,node,kind,bindings:new Map()}; scopes.push(v); return v; }
function bind(pattern, owner, kind, declaration) {
  if (!pattern) return;
  if (pattern.type === 'Identifier') { owner.bindings.set(pattern.name, [...(owner.bindings.get(pattern.name)||[]), {identifier:pattern,kind,declaration}]); return; }
  if (pattern.type === 'AssignmentPattern') bind(pattern.left, owner, kind, declaration);
  else if (pattern.type === 'RestElement') bind(pattern.argument, owner, kind, declaration);
  else if (pattern.type === 'ArrayPattern') for (const p of pattern.elements) bind(p, owner, kind, declaration);
  else if (pattern.type === 'ObjectPattern') for (const p of pattern.properties) bind(p.type === 'RestElement' ? p.argument : p.value, owner, kind, declaration);
}
function build(node, parent, current) {
  nodes.push(node); if (parent) parents.set(node, parent); let owner = current;
  if (node.type === 'Program') owner = scope(null, node, 'Program');
  else if (functionTypes.has(node.type)) {
    if (node.type === 'FunctionDeclaration' && node.id) bind(node.id, current, 'function', node);
    owner = scope(current, node, 'function'); for (const p of node.params) bind(p, owner, 'parameter', p);
    if (node.type === 'FunctionExpression' && node.id) bind(node.id, owner, 'function-self', node);
  } else if (node.type === 'ClassDeclaration' || node.type === 'ClassExpression') {
    if (node.type === 'ClassDeclaration' && node.id) bind(node.id, current, 'class', node);
    owner = scope(current, node, 'class'); if (node.id) bind(node.id, owner, 'class-self', node);
  } else if (['BlockStatement','CatchClause','ForStatement','ForInStatement','ForOfStatement','SwitchStatement','StaticBlock'].includes(node.type)) {
    owner = scope(current, node, node.type); if (node.type === 'CatchClause') bind(node.param, owner, 'catch', node.param);
  }
  scopeAt.set(node, owner);
  if (node.type === 'VariableDeclaration') for (const d of node.declarations) {
    let target = owner; if (node.kind === 'var') while (!['Program','function'].includes(target.kind)) target = target.parent;
    bind(d.id, target, node.kind, d);
  }
  if (node.type === 'ImportDeclaration') for (const d of node.specifiers) bind(d.local, owner, 'import', d);
  for (const k of Object.keys(node)) {
    if (skip.has(k)) continue; const v = node[k];
    if (Array.isArray(v)) { for (const n of v) if (n && typeof n.type === 'string') build(n, node, owner); }
    else if (v && typeof v.type === 'string') build(v, node, owner);
  }
}
build(ast.program, null, null);
function resolve(identifier) {
  let owner = scopeAt.get(identifier);
  while (owner) { if (owner.bindings.has(identifier.name)) return {scope:owner,definitions:owner.bindings.get(identifier.name)}; owner = owner.parent; }
  return null;
}
const deltas = [{end:0,delta:0}]; let delta = 0;
for (let i=0; i<text.length;) {
  const cp=text.codePointAt(i), width=cp>0xffff?2:1;
  if (cp>127) { delta+=(cp<=0x7ff?2:cp<=0xffff?3:4)-width; deltas.push({end:i+width,delta}); } i+=width;
}
function offset(i) { let lo=0,hi=deltas.length; while(lo<hi) {const m=(lo+hi)>>>1;if(deltas[m].end<=i)lo=m+1;else hi=m;} return i+deltas[lo-1].delta; }
const locations = new WeakMap();
function loc(node) {
  if(locations.has(node))return locations.get(node);
  const start=offset(node.start),endExclusive=offset(node.end);
  const value={sourcePath,sourceHash,byteRange:{start,endExclusive},spanHash:hash(source.subarray(start,endExclusive)),nodeType:node.type};locations.set(node,value);return value;
}
const expression = node => text.slice(node.start,node.end);
const key = node => node?.type==='Identifier'?node.name:node?.type==='StringLiteral'?node.value:null;
function reference(node) {
  const p=parents.get(node); if(!p)return false;
  if(['ImportSpecifier','ImportDefaultSpecifier','ImportNamespaceSpecifier'].includes(p.type))return false;
  if(p.type==='ExportSpecifier'&&p.local!==node)return false;
  if(['MemberExpression','OptionalMemberExpression'].includes(p.type)&&p.property===node&&!p.computed)return false;
  if(['ObjectProperty','ObjectMethod','ClassMethod'].includes(p.type)&&p.key===node&&!p.computed&&!p.shorthand)return false;
  const binding=resolve(node);return !!binding&&!binding.definitions.some(d=>d.identifier===node);
}
function chain(node) {const a=[];let p=parents.get(node);while(p){a.push(p);p=parents.get(p);}return a;}
function callable(node) {return chain(node).find(p=>functionTypes.has(p.type));}
function description(node) {return node?{name:node.id?.name??key(node.key),...loc(node)}:null;}
function structuralConditions(node) {
  const result=[];let child=node,p=parents.get(child);
  while(p&&!functionTypes.has(p.type)) {
    if(['IfStatement','ConditionalExpression'].includes(p.type)&&p.test!==child)result.push({type:p.type,branch:p.consequent===child?'consequent':'alternate',test:loc(p.test),expression:expression(p.test)});
    if(p.type==='LogicalExpression'&&p.right===child)result.push({type:p.type,operator:p.operator,test:loc(p.left),expression:expression(p.left)});
    child=p;p=parents.get(p);
  }
  return result;
}
function bindingDescription(identifier) {
  const r=resolve(identifier);return r?{scopeKind:r.scope.kind,scope:loc(r.scope.node),definitions:r.definitions.map(d=>({kind:d.kind,declaration:loc(d.declaration)}))}:null;
}

const family=relative.includes('main-')?'main':relative.includes('startup-requirements')?'startup':relative.includes('app-initial')?'initial':'shared';
const queries={main:['At','e$','t$','lze','uze','n$','dze','fze','pze','r$','l','_'],startup:['ft','Sr'],initial:['bZs','xZs','wZs','SZs','CZs','Pd','qhi','Bhe','l'],shared:['wAt','TAt','EAt']};
const programScope=scopes.find(x=>x.kind==='Program'), selected=new Map(),bindings=[],refs=[],exports=[],imports=[],assignments=[];
function select(name,node){if(node)selected.set(name,node);}
function selectLocalContext(name,node){
  select(name,node);
  const fn=callable(node);
  if(fn&&offset(fn.end)-offset(fn.start)<24000)select(name+'-owner',fn);
  const st=chain(node).find(p=>['ExpressionStatement','VariableDeclaration','ReturnStatement'].includes(p.type));
  if(st&&offset(st.end)-offset(st.start)<12000)select(name+'-statement',st);
}
for(const name of queries[family]){
 const definitions=programScope.bindings.get(name);
 if(!definitions)throw Error('Missing Program binding '+name);
 const target=definitions.map(x=>x.declaration);
 bindings.push({name,scopeKind:'Program',definitions:definitions.map(d=>({kind:d.kind,declaration:loc(d.declaration),identifier:loc(d.identifier)}))});
 for(const d of definitions)select('binding-'+name,d.declaration);
 for(const node of nodes){
  if(node.type!=='Identifier'||node.name!==name||!reference(node))continue;
  const resolved=resolve(node);
  if(resolved?.scope!==programScope)continue;
  const parent=parents.get(node),directCall=['CallExpression','OptionalCallExpression','NewExpression'].includes(parent.type)&&parent.callee===node;
  // Avoid enumerating generic Electron/requirements aliases: only relevant selected calls use them.
  if(family==='main'&&['l','_'].includes(name))continue;
  if(family==='initial'&&['l','Pd'].includes(name)&&!expression(parent).includes('owlFeatures')&&name==='Pd')continue;
  refs.push({name,reference:loc(node),parent:loc(parent),parentExpression:expression(parent).slice(0,3000),directCall,bindingScope:'Program',enclosingFunction:description(callable(node)),conditions:structuralConditions(node)});
  if(directCall||['AssignmentExpression','UpdateExpression','MemberExpression','OptionalMemberExpression','ForOfStatement'].includes(parent.type))selectLocalContext('reference-'+name+'-'+offset(node.start),parent);
  if(parent.type==='ExportSpecifier')exports.push({name,exported:key(parent.exported),...loc(parent)});
  if(parent.type==='AssignmentExpression'&&parent.left===node)assignments.push({name,expression:expression(parent),...loc(parent)});
 }
}
for(const node of nodes){
 if(node.type==='ImportDeclaration')for(const s of node.specifiers){
  if(queries[family].includes(s.local.name))imports.push({local:s.local.name,imported:key(s.imported),module:node.source.value,...loc(s),moduleSource:loc(node.source)});
 }
 if(family==='startup'&&node.type==='CallExpression'&&expression(node.callee)==='Object.defineProperty'&&node.arguments[0]?.name==='exports'&&['Pt','j'].includes(node.arguments[1]?.value)){
  select('cjs-export-'+node.arguments[1].value,node);
  exports.push({exported:node.arguments[1].value,expression:expression(node),...loc(node)});
 }
}
// Follow the reset callback's local binding once, to its auth event registrations.
if(family==='main'){
 const resetRefs=refs.filter(r=>r.name==='fze'&&r.directCall);
 for(const rr of resetRefs){
  const call=nodes.find(n=>n.type==='CallExpression'&&loc(n).byteRange.start===rr.parent.byteRange.start);
  const fn=callable(call),d=fn&&parents.get(fn);
  if(d?.type!=='VariableDeclarator'||d.id.type!=='Identifier')continue;
  const resolution=resolve(d.id);select('reset-callback-declaration',d);
  for(const n of nodes){
   if(n.type!=='Identifier'||n.name!==d.id.name||!reference(n)||resolve(n)?.scope!==resolution?.scope)continue;
   const p=parents.get(n);refs.push({name:'reset-callback-local-'+d.id.name,reference:loc(n),parent:loc(p),parentExpression:expression(p).slice(0,6000),bindingScope:'local-verified',enclosingFunction:description(callable(n))});
   selectLocalContext('reset-callback-consumer-'+offset(n.start),p);
  }
 }
}
fs.mkdirSync(outputDirectory,{recursive:true});
const units=[];
for(const [label,node]of selected){
 const filename=String(units.length+1).padStart(3,'0')+'-'+label.replace(/[^a-zA-Z0-9_-]/g,'_')+'.txt';
 const location=loc(node);fs.writeFileSync(path.join(outputDirectory,filename),source.subarray(location.byteRange.start,location.byteRange.endExclusive),{flag:'wx'});
 units.push({label,...description(node),file:filename,ancestors:chain(node).map(p=>({name:p.id?.name??key(p.key),...loc(p)}))});
}
const result={baselineId:baseline,sourcePath,sourceHash,sourceBytes:source.length,parser:{path:parserPath,sha256:hash(fs.readFileSync(parserPath))},startedAtUtc,completedAtUtc:new Date().toISOString(),fullProgramParsed:true,nodeCount:nodes.length,scopeCount:scopes.length,parserErrors:ast.errors?.length??0,queries:queries[family],bindings,bindingReferences:refs,imports,exports,assignments,units,targetCodeExecuted:false,modelSubmissionsAdded:0,originalClientRunsAdded:0,newReaRuns:0};
fs.writeFileSync(path.join(outputDirectory,'source-contracts.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({family,sourcePath,nodeCount:nodes.length,units:units.length,refs:refs.length,imports,exports,assignments}));
