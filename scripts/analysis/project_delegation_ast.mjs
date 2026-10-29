// Targeted project delegation query. Reuses the frozen-Program scope walker from resume_provider_ast.mjs; no target execution.
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


const config=JSON.parse(fs.readFileSync(process.argv[6]));
const programScope=scopes.find(x=>x.kind==='Program'),selected=new Map(),bindings=[],refs=[],exports=[],imports=[];
function select(label,node){if(node)selected.set(label,node);}
function context(label,node){
 select(label,node);
 const fn=callable(node);
 if(fn&&offset(fn.end)-offset(fn.start)<85000)select(label+'-owner',fn);
 const statement=chain(node).find(p=>['ExpressionStatement','VariableDeclaration','ReturnStatement'].includes(p.type));
 if(statement&&offset(statement.end)-offset(statement.start)<85000)select(label+'-statement',statement);
}
for(const name of [...(config.bindings||[]),...(config.definitionOnlyBindings||[])]){
 const definitions=programScope.bindings.get(name);if(!definitions)throw Error('Missing Program binding '+name);
 bindings.push({name,definitions:definitions.map(d=>({kind:d.kind,declaration:loc(d.declaration),identifier:loc(d.identifier)}))});
 for(const d of definitions)select('binding-'+name,d.declaration);
 if(config.definitionOnlyBindings?.includes(name))continue;
 for(const node of nodes){
  if(node.type!=='Identifier'||node.name!==name||!reference(node)||resolve(node)?.scope!==programScope)continue;
  const parent=parents.get(node);refs.push({name,reference:loc(node),parent:loc(parent),expression:expression(parent).slice(0,14000),binding:bindingDescription(node),owner:description(callable(node))});
  if(name!=='i')context('ref-'+name+'-'+offset(node.start),parent);
 }
}
for(const node of nodes){
 if(config.members?.includes(key(node.key))&&['ClassMethod','ObjectMethod','ObjectProperty'].includes(node.type)){
  context('member-'+key(node.key)+'-'+offset(node.start),node);
  const cls=chain(node).find(p=>['ClassDeclaration','ClassExpression'].includes(p.type));
  if(cls&&offset(cls.end)-offset(cls.start)<100000)select('class-'+offset(cls.start),cls);
 }
 if(['MemberExpression','OptionalMemberExpression'].includes(node.type)&&config.members?.includes(key(node.property))){
  const parent=parents.get(node);refs.push({member:key(node.property),reference:loc(node),parent:loc(parent),expression:expression(parent).slice(0,14000),owner:description(callable(node)),receiverBinding:node.object.type==='Identifier'?bindingDescription(node.object):null});
  context('member-use-'+key(node.property)+'-'+offset(node.start),parent);
 }
 if(node.type==='CallExpression'&&expression(node.callee)==='Object.defineProperty'&&node.arguments[0]?.name==='exports'&&config.exports?.includes(node.arguments[1]?.value)){
  select('cjs-getter-'+node.arguments[1].value,node);const returned=nodes.find(n=>n.type==='ReturnStatement'&&n.start>node.start&&n.end<node.end&&n.argument?.type==='Identifier');
  exports.push({exported:node.arguments[1].value,expression:expression(node),...loc(node),binding:returned?bindingDescription(returned.argument):null});
 }
 if(node.type==='AssignmentExpression'&&node.left.type==='MemberExpression'&&node.left.object.name==='exports'&&config.exports?.includes(key(node.left.property))){
  select('export-'+key(node.left.property),node);exports.push({exported:key(node.left.property),expression:expression(node),...loc(node)});
  if(node.right.type==='Identifier'){
   const b=resolve(node.right);for(const d of b?.definitions||[])select('export-definition-'+key(node.left.property),d.declaration);
   exports[exports.length-1].binding=bindingDescription(node.right);
  }
 }
}
for(const query of config.classMethods||[]){
 const definition=programScope.bindings.get(query.binding)?.[0]?.declaration, cls=definition?.init;
 if(cls?.type!=='ClassExpression')throw Error('Class initializer not found '+query.binding);
 for(const method of cls.body.body){const name=method.key?.type==='PrivateName'?'#'+method.key.id.name:key(method.key);if(query.names.includes(name))select('class-method-'+query.binding+'-'+name,method);}
}

// Resolve real ESM exports to their original Program declarations before inspecting delegates.
const esmTargets=[];
for (const statement of ast.program.body) {
 if(statement.type!=='ExportNamedDeclaration')continue;
 for(const spec of statement.specifiers||[]) {
  const exported=key(spec.exported);
  if(!config.exports?.includes(exported))continue;
  const resolved=resolve(spec.local);
  if(!resolved||resolved.scope!==programScope)throw Error('Export is not Program-bound '+exported);
  const entry={exported,local:spec.local.name,...loc(spec),binding:bindingDescription(spec.local)};
  exports.push(entry);select('esm-export-'+exported,spec);
  for(const d of resolved.definitions){select('esm-definition-'+exported,d.declaration);esmTargets.push({exported,node:d.declaration});}
 }
}
for(const target of esmTargets){
 for(const node of nodes){
  if(node.start<target.node.start||node.end>target.node.end)continue;
  if(node.type==='Identifier'&&reference(node)){
   refs.push({exportedOwner:target.exported,name:node.name,reference:loc(node),parent:loc(parents.get(node)),binding:bindingDescription(node),owner:description(callable(node))});
  }
  if(['CallExpression','NewExpression'].includes(node.type)){
   refs.push({exportedOwner:target.exported,call:expression(node).slice(0,14000),...loc(node),calleeBinding:node.callee.type==='Identifier'?bindingDescription(node.callee):null});
  }
 }
}
for(const node of nodes){
 if(node.type==='StringLiteral'&&config.importTargets?.includes(node.value)){
  const parent=parents.get(node);context('dialog-loader-'+offset(node.start),parent);
  let decl=chain(node).find(p=>p.type==='VariableDeclarator');
  if(decl&&offset(decl.end)-offset(decl.start)<85000)select('dialog-loader-binding-'+offset(decl.start),decl);
  refs.push({importTarget:node.value,...loc(node),owner:description(callable(node)),declaration:decl?loc(decl):null});
 }
}

fs.mkdirSync(outputDirectory,{recursive:true});const units=[];
for(const [label,node]of selected){
 const filename=String(units.length+1).padStart(3,'0')+'-'+label.replace(/[^a-zA-Z0-9_-]/g,'_')+'.txt';const location=loc(node);
 fs.writeFileSync(path.join(outputDirectory,filename),source.subarray(location.byteRange.start,location.byteRange.endExclusive),{flag:'wx'});
 units.push({label,...description(node),file:filename,ancestors:chain(node).map(p=>({name:p.id?.name??key(p.key),...loc(p)}))});
}
const result={baselineId:baseline,sourcePath,sourceHash,sourceBytes:source.length,parser:{path:parserPath,sha256:hash(fs.readFileSync(parserPath))},startedAtUtc,completedAtUtc:new Date().toISOString(),fullProgramParsed:true,nodeCount:nodes.length,scopeCount:scopes.length,parserErrors:ast.errors?.length??0,config,bindings,bindingReferences:refs,exports,units,targetCodeExecuted:false,modelSubmissionsAdded:0,originalClientRunsAdded:0,newReaRuns:0};
fs.writeFileSync(path.join(outputDirectory,'source-contracts.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({sourcePath,nodeCount:nodes.length,units:units.length,refs:refs.length,exports}));
