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


const expected=process.argv[6];
const exported=nodes.filter(n=>n.type==='ExportSpecifier'&&key(n.exported)===expected);
if(exported.length!==1)throw Error('Expected one named component export: '+expected);
const spec=exported[0],binding=resolve(spec.local);
if(!binding||binding.definitions.length!==1)throw Error('Ambiguous exported component');
const definition=binding.definitions[0].declaration;
let rootNode=definition;
if(definition.type==='VariableDeclarator'&&definition.init&&functionTypes.has(definition.init.type))rootNode=definition.init;
function value(node){
 if(node.type==='StringLiteral')return node.value;
 if(node.type==='TemplateLiteral'&&node.expressions.length===0)return node.quasis[0].value.cooked;
 return null;
}
const navigationProps=[],routeLiterals=[],rootCalls=[],returns=[];
for(const n of nodes){
 if(n.start>=rootNode.start&&n.end<=rootNode.end){
  if(n.type==='ObjectProperty'&&['to','href'].includes(key(n.key)))navigationProps.push({property:key(n.key),literal:value(n.value),expression:expression(n.value),...loc(n),nearestFunction:description(callable(n)),conditions:structuralConditions(n)});
  if(n.type==='CallExpression'&&n.callee.type==='Identifier'&&callable(n)===rootNode){
   const r=resolve(n.callee);
   rootCalls.push({callee:n.callee.name,...loc(n),binding:r&&r.definitions.length===1?bindingDescription(n.callee):null});
  }
  if(n.type==='ReturnStatement'&&callable(n)===rootNode)returns.push({...loc(n),expression:n.argument?expression(n.argument):null,conditions:structuralConditions(n)});
 }
 const v=value(n);if(v?.startsWith('/settings/')||v==='/profile')routeLiterals.push({value:v,...loc(n),nearestFunction:description(callable(n))});
}
const imports=ast.program.body.filter(n=>n.type==='ImportDeclaration').map(n=>({module:n.source.value,specifiers:n.specifiers.map(s=>({local:s.local.name,imported:s.type==='ImportSpecifier'?key(s.imported):s.type})),...loc(n)}));
fs.mkdirSync(outputDirectory);
const location=loc(rootNode),sourceFilename='exported-component.txt';
fs.writeFileSync(path.join(outputDirectory,sourceFilename),source.subarray(location.byteRange.start,location.byteRange.endExclusive),{flag:'wx'});
const result={baselineId:baseline,sourcePath,sourceHash,sourceBytes:source.length,fullProgramParsed:true,nodeCount:nodes.length,scopeCount:scopes.length,parser:{path:parserPath,sha256:hash(fs.readFileSync(parserPath))},expectedExport:expected,exportSpecifier:loc(spec),exportBinding:bindingDescription(spec.local),component:{...location,sourceFilename},navigationProps,routeLiterals,rootCalls,rootReturns:returns,imports,targetCodeExecuted:false,originalClientRunsAdded:0,modelSubmissionsAdded:0,qualification:'A named export and syntactic calls/props are source evidence; component mounting, branch outcomes and user operation identity remain separate.'};
fs.writeFileSync(path.join(outputDirectory,'source-contracts.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({sourcePath,export:expected,nodeType:rootNode.type,nodes:nodes.length,navigationProps:navigationProps.length}));
