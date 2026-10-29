// Full original Programs are parsed; no target module is evaluated.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';

const [root, baseline, filename, outputDirectory] = process.argv.slice(2);
if(fs.existsSync(outputDirectory))throw Error('Output exists; preserve earlier results');
fs.mkdirSync(path.dirname(outputDirectory),{recursive:true});
const registry = JSON.parse(fs.readFileSync(path.join(root,'analysis',baseline,'files.json')));
const sourcePath='app.asar/'+filename;
const input=registry.archiveFiles.find(x=>x.sourcePath===sourcePath);
if(!input)throw Error('Unregistered source');
const source=fs.readFileSync(path.join(root,'.analysis-local/baselines',baseline,'extracted',filename));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const sourceHash=hash(source),text=source.toString('utf8');
if(input.sha256!==sourceHash||input.bytes!==source.length)throw Error('Frozen source mismatch');
const parserPath = path.join(root, '.analysis-local/global-state-storage-work/tooling/node_modules/@babel/parser/lib/index.js');
const parser = createRequire(import.meta.url)(parserPath), startedAtUtc = new Date().toISOString();
const ast = parser.parse(text, {sourceType: 'unambiguous'});
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


const local=filename.includes('/git-settings-');
const selected=new Map(),exports=[];
let ownerClass=null;
if(local){
 const rootFunction=nodes.find(n=>n.type==='FunctionDeclaration'&&n.id?.name==='Ne');
 if(!rootFunction)throw Error('Missing GitSettings root');selected.set('Ne',rootFunction);
 for(const [name,fn]of selected){
  for(const id of nodes){
   if(id.type!=='Identifier'||id.start<fn.start||id.end>fn.end||!reference(id))continue;
   const r=resolve(id);if(!r||r.scope.kind!=='Program'||r.definitions.length!==1)continue;
   const d=r.definitions[0].declaration;if(d.type==='FunctionDeclaration')selected.set(d.id.name,d);
  }
  if(selected.size>50)throw Error('Unexpected local dependency expansion');
 }
}else if(filename.includes('/main-')){
 const classes=nodes.filter(n=>['ClassDeclaration','ClassExpression'].includes(n.type)&&n.body.body.some(m=>m.type==='ClassMethod'&&key(m.key)==='setSettingValue')&&n.body.body.some(m=>m.type==='ClassMethod'&&key(m.key)==='getSettingsStore'));
 if(classes.length!==1)throw Error('Ambiguous settings receiver class');ownerClass=classes[0];
 const methods=new Set(['getSettingValue','getSettingValues','getConfiguredSettingValues','setSettingValue','getSettingsStore']);
 for(const n of nodes){
  if(!chain(n).includes(ownerClass))continue;
  if(n.type==='ClassMethod'&&methods.has(key(n.key)))selected.set('method-'+key(n.key),n);
  if(n.type==='ObjectProperty'&&['get-setting','get-settings','set-setting'].includes(key(n.key)))selected.set('handler-'+key(n.key),n);
  if(n.type==='AssignmentExpression'&&n.left.type==='MemberExpression'&&n.left.object.type==='ThisExpression'&&['settings','settingsStore'].includes(key(n.left.property)))selected.set('assignment-'+key(n.left.property)+'-'+n.start,n);
 }
 if(!selected.has('method-setSettingValue')||!selected.has('handler-set-setting'))throw Error('Incomplete receiver selection');
}else{
 const wanted=new Set(process.argv[6].split(','));
 for(const spec of nodes){
  if(spec.type!=='ExportSpecifier'||!wanted.has(key(spec.exported)))continue;
  const r=resolve(spec.local);if(!r||r.definitions.length!==1||r.scope.kind!=='Program')throw Error('Ambiguous exported provider');
  const d=r.definitions[0].declaration;selected.set(spec.local.name,d);
  exports.push({exported:key(spec.exported),local:spec.local.name,...loc(spec),binding:bindingDescription(spec.local)});
 }
 if(exports.length!==wanted.size)throw Error('Missing provider export');
 for(const name of (process.argv[7]??'').split(',').filter(Boolean)){
  const candidates=nodes.filter(n=>(n.type==='FunctionDeclaration'||n.type==='VariableDeclarator')&&n.id?.name===name);
  const found=candidates.filter(n=>{const r=resolve(n.id);return r?.scope.kind==='Program'&&r.definitions.length===1;});
  if(found.length!==1)throw Error('Missing explicit provider local: '+name);selected.set(name,found[0]);
 }
 for(const [name,node]of [...selected]){
  if(node.type!=='VariableDeclarator'||node.init)continue;
  const writes=nodes.filter(n=>n.type==='AssignmentExpression'&&n.left.type==='Identifier'&&resolve(n.left)?.definitions[0]?.declaration===node);
  if(writes.length!==1)throw Error('Ambiguous provider table write: '+name);
  selected.set('assignment-'+name,writes[0]);
 }
}
const uses=[],callbacks=[],calls=[],properties=[];
for(const [name,unit]of selected){
 for(const n of nodes){
  if(n.start<unit.start||n.end>unit.end)continue;
  if(n.type==='Identifier'&&reference(n)){
   const r=resolve(n);if(r?.scope.kind==='Program'&&r.definitions.length===1)uses.push({unit:name,name:n.name,...loc(n),binding:bindingDescription(n)});
  }
  if(n.type==='ArrowFunctionExpression'||n.type==='FunctionExpression')callbacks.push({unit:name,...loc(n),expression:expression(n),conditions:structuralConditions(n)});
  if(n.type==='CallExpression'&&n.callee.type==='Identifier')calls.push({unit:name,callee:n.callee.name,...loc(n),arguments:n.arguments.map(expression),binding:bindingDescription(n.callee)});
  if(n.type==='MemberExpression'&&n.object.type==='Identifier'&&['E','y'].includes(n.object.name)&&resolve(n.object)?.scope.kind==='Program')properties.push({unit:name,object:n.object.name,property:key(n.property),...loc(n),binding:bindingDescription(n.object)});
 }
}
fs.mkdirSync(outputDirectory);
const units=[];
for(const [name,node]of selected){
 const location=loc(node),sourceFilename=String(units.length+1).padStart(3,'0')+'-'+name+'.txt';
 fs.writeFileSync(path.join(outputDirectory,sourceFilename),source.subarray(location.byteRange.start,location.byteRange.endExclusive),{flag:'wx'});
 units.push({name,...location,sourceFilename});
}
const imports=ast.program.body.filter(n=>n.type==='ImportDeclaration').map(n=>({module:n.source.value,specifiers:n.specifiers.map(s=>({local:s.local.name,imported:s.type==='ImportSpecifier'?key(s.imported):s.type})),...loc(n)}));
const result={baselineId:baseline,sourcePath,sourceHash,sourceBytes:source.length,fullProgramParsed:true,nodeCount:nodes.length,scopeCount:scopes.length,parser:{path:parserPath,sha256:hash(fs.readFileSync(parserPath))},units,exports,ownerClass:ownerClass?description(ownerClass):null,programBindingUses:uses,callbacks,calls,descriptorProperties:properties,imports,targetCodeExecuted:false,originalClientRunsAdded:0,modelSubmissionsAdded:0};
fs.writeFileSync(path.join(outputDirectory,'source-contracts.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({sourcePath,units:units.map(x=>x.name),callbacks:callbacks.length,calls:calls.length}));
