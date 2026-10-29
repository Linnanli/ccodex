// Full-Program import and lexical-call analysis. Target modules are never evaluated.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';

const [root, baseline, candidateIndex, outputDirectory] = process.argv.slice(2);
const parent=JSON.parse(fs.readFileSync(path.join(root,'analysis',baseline,'command-registration-contracts.json')));
const candidate=parent.lexicalImporterCandidates[Number(candidateIndex)];
if(!candidate)throw Error('Unknown candidate');
const sourcePath=candidate.sourcePath;
const source=fs.readFileSync(path.join(root,'.analysis-local/baselines',baseline,'extracted',sourcePath.replace(/^app\.asar\//,'')));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex'),sourceHash=hash(source),text=source.toString('utf8');
if(sourceHash!==candidate.sourceHash)throw Error('Frozen source mismatch');
const parserPath=path.join(root,'.analysis-local/global-state-storage-work/tooling/node_modules/@babel/parser/lib/index.js');
const parser=createRequire(import.meta.url)(parserPath),startedAtUtc=new Date().toISOString();
const ast=parser.parse(text,{sourceType:'module'});
const skip=new Set(['loc','start','end','extra','comments','tokens','leadingComments','trailingComments','innerComments','errors']);
const functionTypes=new Set(['FunctionDeclaration','FunctionExpression','ArrowFunctionExpression','ClassMethod','ClassPrivateMethod','ObjectMethod']);
const nodes=[],scopes=[],parents=new WeakMap(),scopeAt=new WeakMap();
function scope(parent,node,kind){const value={id:scopes.length,parent,node,kind,bindings:new Map()};scopes.push(value);return value;}
function bind(pattern,owner,kind,declaration){
 if(!pattern)return;
 if(pattern.type==='Identifier'){owner.bindings.set(pattern.name,[...(owner.bindings.get(pattern.name)||[]),{identifier:pattern,kind,declaration}]);return;}
 if(pattern.type==='AssignmentPattern')bind(pattern.left,owner,kind,declaration);
 else if(pattern.type==='RestElement')bind(pattern.argument,owner,kind,declaration);
 else if(pattern.type==='ArrayPattern')for(const p of pattern.elements)bind(p,owner,kind,declaration);
 else if(pattern.type==='ObjectPattern')for(const p of pattern.properties)bind(p.type==='RestElement'?p.argument:p.value,owner,kind,declaration);
}
function build(node,parent,current){
 nodes.push(node);if(parent)parents.set(node,parent);let owner=current;
 if(node.type==='Program')owner=scope(null,node,'Program');
 else if(functionTypes.has(node.type)){
  if(node.type==='FunctionDeclaration'&&node.id)bind(node.id,current,'function',node);
  owner=scope(current,node,'function');for(const p of node.params)bind(p,owner,'parameter',p);
  if(node.type==='FunctionExpression'&&node.id)bind(node.id,owner,'function-self',node);
 }else if(node.type==='ClassDeclaration'||node.type==='ClassExpression'){
  if(node.type==='ClassDeclaration'&&node.id)bind(node.id,current,'class',node);
  owner=scope(current,node,'class');if(node.id)bind(node.id,owner,'class-self',node);
 }else if(['BlockStatement','CatchClause','ForStatement','ForInStatement','ForOfStatement','SwitchStatement','StaticBlock'].includes(node.type)){
  owner=scope(current,node,node.type);if(node.type==='CatchClause')bind(node.param,owner,'catch',node.param);
 }
 scopeAt.set(node,owner);
 if(node.type==='VariableDeclaration')for(const d of node.declarations){let target=owner;if(node.kind==='var')while(!['Program','function'].includes(target.kind))target=target.parent;bind(d.id,target,node.kind,d);}
 if(node.type==='ImportDeclaration')for(const d of node.specifiers)bind(d.local,owner,'import',d);
 for(const k of Object.keys(node)){
  if(skip.has(k))continue;const v=node[k];
  if(Array.isArray(v)){for(const n of v)if(n&&typeof n.type==='string')build(n,node,owner);}
  else if(v&&typeof v.type==='string')build(v,node,owner);
 }
}
build(ast.program,null,null);
function resolve(identifier){let owner=scopeAt.get(identifier);while(owner){if(owner.bindings.has(identifier.name))return{scope:owner,definitions:owner.bindings.get(identifier.name)};owner=owner.parent;}return null;}
const deltas=[{end:0,delta:0}];let delta=0;
for(let i=0;i<text.length;){const cp=text.codePointAt(i),width=cp>0xffff?2:1;if(cp>127){delta+=(cp<=0x7ff?2:cp<=0xffff?3:4)-width;deltas.push({end:i+width,delta});}i+=width;}
function offset(i){let lo=0,hi=deltas.length;while(lo<hi){const m=(lo+hi)>>>1;if(deltas[m].end<=i)lo=m+1;else hi=m;}return i+deltas[lo-1].delta;}
const locations=new WeakMap();
function loc(node){if(locations.has(node))return locations.get(node);const start=offset(node.start),endExclusive=offset(node.end);
 const value={sourcePath,sourceHash,byteRange:{start,endExclusive},spanHash:hash(source.subarray(start,endExclusive)),nodeType:node.type};locations.set(node,value);return value;}
const expression=node=>text.slice(node.start,node.end);
const key=node=>node?.type==='Identifier'?node.name:node?.type==='StringLiteral'?node.value:null;
function enclosingFunction(node){let p=parents.get(node);while(p&&!functionTypes.has(p.type))p=parents.get(p);return p;}
function describeFunction(node){return node?{name:node.id?.name??key(node.key),...loc(node)}:null;}
function reference(node){
 const p=parents.get(node);if(!p)return false;
 if(['ImportSpecifier','ImportDefaultSpecifier','ImportNamespaceSpecifier'].includes(p.type))return false;
 if(p.type==='ExportSpecifier'&&p.local!==node)return false;
 if(['MemberExpression','OptionalMemberExpression'].includes(p.type)&&p.property===node&&!p.computed)return false;
 if(['ObjectProperty','ObjectMethod','ClassMethod'].includes(p.type)&&p.key===node&&!p.computed&&!p.shorthand)return false;
 const binding=resolve(node);return !!binding&&!binding.definitions.some(d=>d.identifier===node);
}
const imported=[];
for(const declaration of ast.program.body){
 if(declaration.type!=='ImportDeclaration'||declaration.source.value!=='./app-initial-6350d04672d0.js')continue;
 for(const specifier of declaration.specifiers){
  if(specifier.type!=='ImportSpecifier'||key(specifier.imported)!=='IBn')continue;
  const binding=scopes[0].bindings.get(specifier.local.name);
  if(binding?.length!==1||binding[0].declaration!==specifier)throw Error('Ambiguous import');
  imported.push({localName:specifier.local.name,imported:'IBn',module:declaration.source.value,
   specifier:loc(specifier),moduleLiteral:loc(declaration.source),declaration:loc(declaration)});
 }
}
if(imported.length!==1||imported[0].localName!==candidate.localNameCandidate)throw Error('Discovery/import disagreement');
const localName=imported[0].localName;
function target(node){if(node?.type!=='Identifier'||node.name!==localName)return false;
 const binding=resolve(node);return binding?.scope===scopes[0]&&binding.definitions.length===1&&binding.definitions[0].kind==='import';}
function calleeIdentifier(node){
 if(target(node))return node;
 if(node?.type==='SequenceExpression'&&node.expressions.slice(0,-1).every(n=>n.type==='NumericLiteral'&&n.value===0)&&target(node.expressions.at(-1)))return node.expressions.at(-1);
 return null;
}
function argument(node){
 const value={expression:expression(node),...loc(node)};
 if(node.type==='Identifier'){
  const binding=resolve(node);
  if(binding?.definitions.length===1)value.binding={kind:binding.definitions[0].kind,scopeKind:binding.scope.kind,declaration:loc(binding.definitions[0].declaration)};
 }
 if(node.type==='ObjectExpression')value.properties=node.properties.map(p=>({kind:p.type,key:key(p.key),...loc(p)}));
 return value;
}
function conditions(call){
 const result=[];let child=call,p=parents.get(child);
 while(p&&!functionTypes.has(p.type)){
  let item=null;
  if(['IfStatement','ConditionalExpression'].includes(p.type)&&p.test!==child)item={kind:p.type,branch:p.consequent===child?'consequent':'alternate',expression:expression(p.test),test:loc(p.test),completeControl:loc(p)};
  if(p.type==='LogicalExpression'&&p.right===child)item={kind:p.type,branch:p.operator==='&&'?'truthy-RHS':p.operator==='||'?'falsy-RHS':'nullish-RHS',expression:expression(p.left),test:loc(p.left),completeControl:loc(p)};
  if(item)result.push(item);child=p;p=parents.get(p);
 }
 return result;
}
fs.mkdirSync(outputDirectory);
const calls=[],used=new Set();
for(const node of nodes){
 if(!['CallExpression','OptionalCallExpression'].includes(node.type))continue;
 const identifier=calleeIdentifier(node.callee);if(!identifier)continue;used.add(identifier);
 const command=node.arguments[0];
 const commandId=command?.type==='StringLiteral'?command.value:command?.type==='TemplateLiteral'&&command.expressions.length===0?command.quasis[0].value.cooked:null;
 const number=String(calls.length+1).padStart(3,'0'),filename=number+'-registration.txt';
 const location=loc(node);fs.writeFileSync(path.join(outputDirectory,filename),source.subarray(location.byteRange.start,location.byteRange.endExclusive),{flag:'wx'});
 calls.push({call:location,calleeReference:loc(identifier),importSpecifier:imported[0].specifier,
  commandId,arguments:node.arguments.map(argument),enclosingFunction:describeFunction(enclosingFunction(node)),
  structuralConditionsWithinCallable:conditions(node),sourceFilename:filename,actualMountOrDispatchVerified:false});
}
const otherReferences=[],shadowedReferences=[];
for(const node of nodes){
 if(node.type!=='Identifier'||node.name!==localName||!reference(node))continue;
 if(!target(node)){shadowedReferences.push(loc(node));continue;}
 if(used.has(node))continue;
 otherReferences.push({reference:loc(node),parent:loc(parents.get(node)),enclosingFunction:describeFunction(enclosingFunction(node)),
  expression:expression(parents.get(node)),status:'binding-confirmed-use-outside-direct-call; value-flow-review-pending'});
}
const exports=[];
for(const node of nodes){
 if(node.type==='ExportSpecifier'&&target(node.local))exports.push({exported:key(node.exported),reference:loc(node)});
}
const result={schemaVersion:1,baselineId:baseline,candidateIndex:Number(candidateIndex),sourcePath,sourceHash,sourceBytes:source.length,
 startedAtUtc,completedAtUtc:new Date().toISOString(),parser:{path:parserPath,sha256:hash(fs.readFileSync(parserPath))},
 fullProgramParsed:true,nodeCount:nodes.length,scopeCount:scopes.length,parserErrors:ast.errors?.length??0,
 confirmedImports:imported,directCalls:calls,otherReferences,localReexports:exports,
 sameSpellingReferencesExcludedByBinding:shadowedReferences.length,
 scope:'All direct Identifier and zero-prefix SequenceExpression calls to the selected imported binding in this original Program; indirect aliases/dynamic imports not resolved.',
 targetCodeExecuted:false,originalClientRunsAdded:0,modelSubmissionsAdded:0,newReaRuns:0};
fs.writeFileSync(path.join(outputDirectory,'source-contracts.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({sourcePath,nodeCount:nodes.length,imports:imported.length,calls:calls.length,dynamicIds:calls.filter(c=>c.commandId===null).length,
 otherReferences:otherReferences.length,shadowedReferencesExcluded:shadowedReferences.length}));
