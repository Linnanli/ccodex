#!/usr/bin/env node
// Static, bounded AST inventory of the frozen renderer's route registrations.
// Target modules are read as UTF-8 data: never import, require, eval or run them.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url), flags = new Map();
for (let i=2;i<process.argv.length;i+=2) {
  if (!process.argv[i].startsWith('--') || process.argv[i+1]===undefined) throw new Error('Expected --name value pairs');
  flags.set(process.argv[i].slice(2),process.argv[i+1]);
}
const baselineFile=path.resolve(flags.get('baseline')||'.analysis-local/current-baseline.json');
const output=path.resolve(flags.get('output')||'.analysis-local/feature-work');
const parserPath=path.resolve(flags.get('parser-path')||'/private/tmp/ccodex-rea-tooling/install/node_modules/@babel/parser');
const baseline=JSON.parse(fs.readFileSync(baselineFile,'utf8'));
const manifest=JSON.parse(fs.readFileSync(path.join('analysis',baseline.baselineId,'files.json'),'utf8'));
const expected=new Map(manifest.archiveFiles.map(x=>[x.archivePath,x]));
const parser=require(parserPath), parserImpl=require.resolve(parserPath);
const parserPackageFile=path.join(path.dirname(parserImpl),'..','package.json');
const parserPackage=JSON.parse(fs.readFileSync(parserPackageFile,'utf8'));
const sha=value=>crypto.createHash('sha256').update(value).digest('hex');
const evidence=[], evidenceKeys=new Map(), contexts=new Map();
const scopeFiles=['webview/assets/app-initial-6350d04672d0.js','webview/assets/app-primary-6f60e9ac4103.js'];
const auxiliaryFile='webview/assets/app-shared-8bd9d0399038.js';
const ignored=new Set(['loc','comments','leadingComments','trailingComments','innerComments','tokens','errors','extra']);
const kids=node=>Object.entries(node).filter(([key])=>!ignored.has(key)).flatMap(([,v])=>Array.isArray(v)?v.filter(x=>x&&typeof x.type==='string'):v&&typeof v.type==='string'?[v]:[]);
const isFunction=n=>['FunctionDeclaration','FunctionExpression','ArrowFunctionExpression','ClassMethod','ClassPrivateMethod','ObjectMethod'].includes(n.type);
const patternNames=n=>!n?[]:n.type==='Identifier'?[n.name]:n.type==='RestElement'?patternNames(n.argument):n.type==='AssignmentPattern'?patternNames(n.left):n.type==='ArrayPattern'?n.elements.flatMap(patternNames):n.type==='ObjectPattern'?n.properties.flatMap(p=>patternNames(p.type==='RestElement'?p.argument:p.value)):[];
const keyName=p=>!p.computed&&p.key?.type==='Identifier'?p.key.name:['StringLiteral','NumericLiteral'].includes(p.key?.type)?String(p.key.value):null;
const unwrap=n=>n?.type==='SequenceExpression'?unwrap(n.expressions.at(-1)):n;
const brief=(c,n,limit=320)=>{const s=c.text.slice(n.start,n.end);return s.length<=limit?s:s.slice(0,limit)+'…';};
function walk(n,fn) {fn(n);for(const child of kids(n))walk(child,fn);}
function readContext(relative) {
  if(contexts.has(relative))return contexts.get(relative);
  const entry=expected.get(relative);if(!entry?.sha256)throw new Error('Missing frozen manifest entry: '+relative);
  const buffer=fs.readFileSync(path.join(baseline.extractedDirectory,relative));
  if(sha(buffer)!==entry.sha256)throw new Error('Frozen source changed: '+relative);
  const text=buffer.toString('utf8');if(!Buffer.from(text).equals(buffer))throw new Error('Non-lossless UTF-8 input');
  const offsets=new Uint32Array(text.length+1);let bytes=0;
  for(let i=0;i<text.length;i++){offsets[i]=bytes;const cp=text.codePointAt(i);if(cp>0xffff){offsets[i+1]=bytes;bytes+=4;i++;}else bytes+=cp<128?1:cp<2048?2:3;}
  offsets[text.length]=bytes;if(bytes!==buffer.length)throw new Error('UTF-8 mapping failed');
  console.error('Parsing frozen AST:',relative);
  const ast=parser.parse(text,{sourceType:'module',attachComment:false,errorRecovery:false,plugins:['jsx']});
  if(ast.errors?.length)throw new Error('AST parse errors');
  const c={relative,buffer,text,hash:entry.sha256,archiveByteOffset:entry.archiveByteOffset,offsets,ast,parents:new WeakMap(),scopes:new WeakMap(),allNodes:[],exports:new Map(),imports:[],bindingCounter:0};
  c.root={kind:'program',parent:null,bindings:new Map()};contexts.set(relative,c);
  const add=(scope,name,node,kind,extra={})=>{let b=scope.bindings.get(name);if(!b){b={id:relative+':B'+(++c.bindingCounter),name,scope,definitions:[],values:[],writes:[]};scope.bindings.set(name,b);}b.definitions.push({node,kind,...extra});if(extra.initializer)b.values.push({node:extra.initializer,site:node,kind:'initializer'});return b;};
  function visit(n,scope=c.root,parent=null){
    if(parent)c.parents.set(n,parent);c.allNodes.push(n);delete n.loc;delete n.extra;
    if(n.type==='FunctionDeclaration'&&n.id)add(scope,n.id.name,n,'function-declaration',{initializer:n});
    if(n.type==='ClassDeclaration'&&n.id)add(scope,n.id.name,n,'class-declaration',{initializer:n});
    if(isFunction(n)){scope={kind:'function',parent:scope,bindings:new Map()};if(n.type==='FunctionExpression'&&n.id)add(scope,n.id.name,n,'named-function-expression',{initializer:n});for(const p of n.params||[])for(const name of patternNames(p))add(scope,name,p,'parameter');}
    else if(n.type==='BlockStatement'||n.type==='CatchClause'){scope={kind:'block',parent:scope,bindings:new Map()};if(n.type==='CatchClause')for(const name of patternNames(n.param))add(scope,name,n.param,'catch-parameter');}
    c.scopes.set(n,scope);
    if(n.type==='VariableDeclarator'){let target=scope;if(parent.kind==='var')while(target.parent&&target.kind!=='function'&&target.kind!=='program')target=target.parent;for(const name of patternNames(n.id))add(target,name,n,parent.kind+'-declaration',{initializer:n.id.type==='Identifier'?n.init:null});}
    if(n.type==='ImportDeclaration')for(const s of n.specifiers){const d={node:s,kind:'import',module:n.source.value,importedName:s.imported?.name||s.imported?.value||(s.type==='ImportDefaultSpecifier'?'default':'*'),declaration:n};add(scope,s.local.name,s,'import',d);c.imports.push({local:s.local.name,...d});}
    if(n.type==='ExportNamedDeclaration')for(const s of n.specifiers)c.exports.set(s.exported.name||s.exported.value,{local:s.local?.name,node:s,module:n.source?.value||null});
    for(const child of kids(n))visit(child,scope,n);
  }
  visit(ast.program);
  for(const n of c.allNodes)if(n.type==='AssignmentExpression'&&n.left.type==='Identifier'){const b=resolve(c,n.left);if(b){b.writes.push(n);if(n.operator==='=')b.values.push({node:n.right,site:n,kind:'assignment'});}}
  console.error('Indexed frozen AST:',relative,c.allNodes.length,'nodes');
  return c;
}
function resolve(c,n){if(c.nodeBindings)return c.nodeBindings.get(n)||null;let s=c.scopes.get(n);while(s){if(s.bindings.has(n.name))return s.bindings.get(n.name);s=s.parent;}return null;}
const range=(c,n)=>({kind:'byte-range',start:c.offsets[n.start],endExclusive:c.offsets[n.end]});
function ev(c,n,claim){
  const r=range(c,n),key=c.relative+':'+r.start+':'+r.endExclusive+':'+claim;
  if(evidenceKeys.has(key))return evidenceKeys.get(key);
  const span=c.buffer.subarray(r.start,r.endExclusive);if(!span.equals(Buffer.from(c.text.slice(n.start,n.end),'utf8')))throw new Error('AST span differs from original bytes');
  const id='ROUTE-AST-E'+String(evidence.length+1).padStart(5,'0');evidenceKeys.set(key,id);
  evidence.push({id,baselineId:baseline.baselineId,claim,sourcePath:'app.asar/'+c.relative,sourceHash:c.hash,locator:r,spanHash:sha(span),method:'supplemental-babel-ast',confidence:'confirmed',verificationStatus:'static-confirmed; runtime-unverified'});return id;
}
const cite=(c,n,claim)=>({sourcePath:'app.asar/'+c.relative,sourceHash:c.hash,range:range(c,n),evidenceId:ev(c,n,claim)});
function importedTarget(c,d){if(!d.module?.startsWith('.'))return null;const relative=path.posix.normalize(path.posix.join(path.posix.dirname(c.relative),d.module));const target=contexts.get(relative);const exp=target?.exports.get(d.importedName);return exp&&exp.local?{context:target,binding:target.root.bindings.get(exp.local),exportNode:exp.node}:null;}
function bindingOrigin(c,b,seen=new Set()){
  if(!b||seen.has(b.id))return null;seen=new Set(seen);seen.add(b.id);
  const d=b.definitions.find(d=>d.kind==='import');
  if(d){const target=importedTarget(c,d);if(target){const terminal=bindingOrigin(target.context,target.binding,seen);return terminal?{...terminal,chain:[{c,d},...terminal.chain],exportNode:target.exportNode}:null;}return{context:c,binding:b,chain:[{c,d}],external:true};}
  if(b.values.length===1&&unwrap(b.values[0].node)?.type==='Identifier'){const terminal=bindingOrigin(c,resolve(c,unwrap(b.values[0].node)),seen);return terminal?{...terminal,chain:[{c,aliasBinding:b,value:b.values[0]},...terminal.chain]}:null;}
  return{context:c,binding:b,chain:[]};
}
function origin(c,n,seen=new Set()){n=unwrap(n);return n?.type==='Identifier'?bindingOrigin(c,resolve(c,n),seen):null;}
// Resolve fixed literal expressions only, using explicit lexical bindings.
// The evaluator implements a small AST grammar; it never runs target code.
const unknown=(reason,trace=[])=>({known:false,reason,trace});
const known=(value,trace=[])=>({known:true,value,trace});
const merged=(...v)=>[...new Set(v.flatMap(x=>x.trace||[]))];
function evaluate(c,n,env=new Map(),seen=new Set(),depth=0){
  if(!n)return unknown('missing expression');if(depth>40)return unknown('static expression depth limit');n=unwrap(n);
  if(['StringLiteral','NumericLiteral','BooleanLiteral'].includes(n.type))return known(n.value,[ev(c,n,'Static literal value')]);
  if(n.type==='NullLiteral')return known(null,[ev(c,n,'Static null value')]);
  if(n.type==='Identifier'){
    if(n.name==='undefined'&&!resolve(c,n))return known(undefined);
    const b=resolve(c,n);if(!b)return unknown('unbound identifier '+n.name);if(env.has(b.id))return env.get(b.id);if(seen.has(b.id))return unknown('cyclic binding '+n.name);
    const next=new Set(seen);next.add(b.id);const d=b.definitions.find(d=>d.kind==='import');
    if(d){const target=importedTarget(c,d);if(!target?.binding)return unknown('import value outside bounded source set',[ev(c,d.node,'Imported identifier '+b.name)]);return evaluateBinding(target.context,target.binding,env,next,depth+1,[ev(c,d.node,'Imported path/value binding '+b.name),ev(target.context,target.exportNode,'Exported path/value binding '+d.importedName)]);}
    return evaluateBinding(c,b,env,next,depth+1,[]);
  }
  if(n.type==='TemplateLiteral'){const vals=n.expressions.map(x=>evaluate(c,x,env,seen,depth+1));if(vals.some(x=>!x.known))return unknown('dynamic template interpolation',merged(...vals));let v='';for(let i=0;i<n.quasis.length;i++){v+=n.quasis[i].value.cooked??n.quasis[i].value.raw;if(i<vals.length)v+=String(vals[i].value);}return known(v,[...merged(...vals),ev(c,n,'Static template value')]);}
  if(n.type==='UnaryExpression'){const a=evaluate(c,n.argument,env,seen,depth+1);if(n.operator==='void')return known(undefined,[ev(c,n,'Static void expression')]);if(!a.known)return a;const operations={'!':x=>!x,'-':x=>-x,'+':x=>+x,'~':x=>~x,'typeof':x=>typeof x};return operations[n.operator]?known(operations[n.operator](a.value),a.trace):unknown('unsupported unary operator');}
  if(n.type==='ArrayExpression'){const vals=n.elements.map(x=>x?.type==='SpreadElement'?unknown('array spread'):evaluate(c,x,env,seen,depth+1));return known(vals,[ev(c,n,'Static array shape'),...merged(...vals)]);}
  if(n.type==='ObjectExpression'){const props={};let dynamic=false;for(const p of n.properties){const k=keyName(p);if(p.type!=='ObjectProperty'||k===null){dynamic=true;continue;}props[k]=evaluate(c,p.value,env,seen,depth+1);}return known({staticObjectProperties:props,dynamicProperties:dynamic},[ev(c,n,'Static object shape')]);}
  if(n.type==='MemberExpression'||n.type==='OptionalMemberExpression'){const obj=evaluate(c,n.object,env,seen,depth+1),prop=n.computed?evaluate(c,n.property,env,seen,depth+1):known(n.property.name);if(!obj.known||!prop.known)return unknown('dynamic member object/key',merged(obj,prop));if(obj.value?.staticObjectProperties){const v=obj.value.staticObjectProperties[prop.value];return v?{...v,trace:[...merged(obj,prop,v),ev(c,n,'Fixed object member lookup')]}:unknown('object member unavailable',merged(obj,prop));}if(Array.isArray(obj.value)){const v=obj.value[prop.value];if(prop.value==='length')return known(obj.value.length,obj.trace);if(v)return{...v,trace:merged(obj,prop,v)};}return unknown('non-static member value',merged(obj,prop));}
  if(n.type==='ConditionalExpression'){const t=evaluate(c,n.test,env,seen,depth+1);if(t.known){const v=evaluate(c,t.value?n.consequent:n.alternate,env,seen,depth+1);return{...v,trace:[...merged(t,v),ev(c,n.test,'Statically evaluated conditional test')]};}const a=evaluate(c,n.consequent,env,seen,depth+1),b=evaluate(c,n.alternate,env,seen,depth+1);return a.known&&b.known&&JSON.stringify(a.value)===JSON.stringify(b.value)?known(a.value,merged(t,a,b)):unknown('dynamic conditional result',merged(t,a,b));}
  if(n.type==='BinaryExpression'||n.type==='LogicalExpression'){const a=evaluate(c,n.left,env,seen,depth+1);if(n.type==='LogicalExpression'&&a.known){if(n.operator==='&&'&&!a.value||n.operator==='||'&&a.value||n.operator==='??'&&a.value!=null)return a;const b=evaluate(c,n.right,env,seen,depth+1);return{...b,trace:merged(a,b)};}const b=evaluate(c,n.right,env,seen,depth+1);if(!a.known||!b.known)return unknown('dynamic operands',merged(a,b));const op={'+':(a,b)=>a+b,'-':(a,b)=>a-b,'===':(a,b)=>a===b,'!==':(a,b)=>a!==b,'==':(a,b)=>a==b,'!=':(a,b)=>a!=b,'>':(a,b)=>a>b,'<':(a,b)=>a<b,'>=':(a,b)=>a>=b,'<=':(a,b)=>a<=b};return op[n.operator]?known(op[n.operator](a.value,b.value),merged(a,b)):unknown('unsupported binary operator',merged(a,b));}
  if(n.type==='CallExpression'&&n.callee.type==='MemberExpression'&&!n.callee.computed&&['filter','map'].includes(n.callee.property.name)){
    const input=evaluate(c,n.callee.object,env,seen,depth+1),callback=n.arguments[0];if(!input.known||!Array.isArray(input.value)||!callback||!['ArrowFunctionExpression','FunctionExpression'].includes(callback.type))return unknown('dynamic array operation',input.trace);
    if(callback.body.type==='BlockStatement')return unknown('block-bodied array callback not interpreted',input.trace);
    const vals=[];for(let i=0;i<input.value.length;i++){const local=new Map(env);for(const [j,p]of callback.params.entries())if(p.type==='Identifier'){const b=resolve(c,p);if(b)local.set(b.id,j===0?input.value[i]:j===1?known(i):unknown('array callback argument'));}const v=evaluate(c,callback.body,local,seen,depth+1);if(n.callee.property.name==='filter'){if(!v.known)return unknown('dynamic filter predicate',merged(input,v));if(v.value)vals.push(input.value[i]);}else vals.push(v);}return known(vals,[...input.trace,ev(c,n,'Bounded static array '+n.callee.property.name+' expression')]);
  }
  if(n.type==='CallExpression'&&n.arguments.length===0){const o=origin(c,n.callee),b=o?.binding,definition=b?.values.length===1?b.values[0].node:null;if(definition&&isFunction(definition)&&!definition.async&&!definition.generator&&definition.params.length===0&&definition.body.type==='BlockStatement'&&definition.body.body.length===1&&definition.body.body[0].type==='ReturnStatement'&&!seen.has(b.id)){const value=definition.body.body[0].argument;if(value?.type==='StringLiteral'||value?.type==='TemplateLiteral'&&value.expressions.length===0){const v=evaluate(o.context,value,env,new Set([...seen,b.id]),depth+1);return{...v,trace:[...v.trace,ev(o.context,definition,'Pure zero-argument fixed-return path helper '+b.name),ev(c,n,'Static AST substitution of fixed-return path helper')]};}}}
  return unknown('requires runtime value: '+n.type);
}
function evaluateBinding(c,b,env,seen,depth,trace){
  if(!b.values.length)return unknown('binding has no static initializer: '+b.name,trace);
  if(b.writes.some(n=>n.operator!=='='))return unknown('compound assignment to binding '+b.name,trace);
  const values=b.values.map(v=>{const out=evaluate(c,v.node,env,seen,depth);return{...out,trace:[...out.trace,ev(c,v.site,'Binding definition/assignment '+b.name)]};});
  if(values.some(x=>!x.known))return unknown('non-static or ambiguous binding '+b.name,[...trace,...merged(...values)]);
  if(values.some(x=>JSON.stringify(x.value)!==JSON.stringify(values[0].value)))return unknown('multiple differing binding values '+b.name,[...trace,...merged(...values)]);
  return known(values[0].value,[...trace,...merged(...values)]);
}
function dynamicImportDetails(c,values,name){
  const dynamicImports=[],dynamicImportBindings=[];
  const literalSpecifier=n=>n?.type==='StringLiteral'?n.value:n?.type==='TemplateLiteral'&&n.expressions.length===0?n.quasis.map(q=>q.value.cooked??q.value.raw).join(''):null;
  const importSpecifier=n=>n.type==='ImportExpression'?literalSpecifier(n.source):n.type==='CallExpression'&&n.callee.type==='Import'?literalSpecifier(n.arguments[0]):null;
  const moduleMetadata=specifier=>{const relative=specifier.startsWith('.')?path.posix.normalize(path.posix.join(path.posix.dirname(c.relative),specifier)):null;const f=expected.get(relative);return f?{targetSourcePath:'app.asar/'+relative,targetSourceHash:f.sha256}:{};};
  for(const value of values){const parentMap=new WeakMap();walk(value,n=>{for(const child of kids(n))parentMap.set(child,n);});walk(value,n=>{
    const specifier=importSpecifier(n);
    if(specifier!==null){dynamicImports.push({moduleSpecifier:specifier,...moduleMetadata(specifier),...cite(c,n,'Component dynamic import '+name)});let p=parentMap.get(n);if(p?.type==='AwaitExpression')p=parentMap.get(p);if(p?.type==='VariableDeclarator'&&p.id.type==='ObjectPattern')for(const prop of p.id.properties){const exportedName=keyName(prop);if(exportedName!==null)dynamicImportBindings.push({kind:'destructured-import-export',moduleSpecifiers:[specifier],exportedName,localName:prop.value.type==='Identifier'?prop.value.name:null,...cite(c,p,'Dynamic import destructured component export '+name)});}}
    if(n.type==='CallExpression'&&n.callee.type==='MemberExpression'&&!n.callee.computed&&n.callee.property.name==='then'){const cb=n.arguments[0];let body=cb&&isFunction(cb)?cb.body:null;if(body?.type==='BlockStatement'&&body.body.length===1&&body.body[0].type==='ReturnStatement')body=body.body[0].argument;if(body?.type==='MemberExpression'&&!body.computed&&body.object.type==='Identifier'&&cb.params[0]?.name===body.object.name){const imports=[];walk(n.callee.object,x=>{const target=importSpecifier(x);if(target!==null)imports.push(target);});if(imports.length)dynamicImportBindings.push({kind:'promise-selected-export',moduleSpecifiers:[...new Set(imports)],exportedName:body.property.name,...cite(c,n,'Dynamic import selected component export '+name)});}}
    if(n.type==='VariableDeclarator'&&n.id.type==='ArrayPattern'&&n.init?.type==='AwaitExpression'){const call=n.init.argument;if(call.type==='CallExpression'&&call.callee.type==='MemberExpression'&&call.callee.object.type==='Identifier'&&call.callee.object.name==='Promise'&&!call.callee.computed&&call.callee.property.name==='all'&&call.arguments[0]?.type==='ArrayExpression')for(const[index,pattern]of n.id.elements.entries()){if(pattern?.type!=='ObjectPattern'||!call.arguments[0].elements[index])continue;const imports=[];walk(call.arguments[0].elements[index],x=>{const target=importSpecifier(x);if(target!==null)imports.push(target);});for(const prop of pattern.properties){const exportedName=keyName(prop);if(exportedName!==null&&imports.length)dynamicImportBindings.push({kind:'promise-all-destructured-import-export',promiseArrayIndex:index,moduleSpecifiers:[...new Set(imports)],exportedName,localName:prop.value.type==='Identifier'?prop.value.name:null,...cite(c,n,'Promise.all selected component import export '+name)});}}}
  });}
  return{dynamicImports,dynamicImportBindings};
}
function componentBinding(c,n){
  n=unwrap(n);const item={expression:brief(c,n),nodeType:n.type};
  if(n.type==='MemberExpression')return{...item,status:'member-component',receiver:n.object.type==='Identifier'?componentBinding(c,n.object):null,member:!n.computed?n.property.name:null,mode:'unknown'};
  if(n.type!=='Identifier')return{...item,status:'dynamic-component',mode:'unknown'};
  const b=resolve(c,n);if(!b)return{...item,status:'unresolved-identifier',mode:'unknown'};
  const defs=b.definitions.map(d=>({kind:d.kind,...cite(c,d.node,'Component lexical definition '+b.name),...(d.kind==='import'?{moduleSpecifier:d.module,importedName:d.importedName}: {})}));
  const o=origin(c,n), actual=o?.binding||b, ac=o?.context||c;
  const valueDefs=actual.values.map(v=>cite(ac,v.site,'Component value/assignment '+actual.name));
  const{dynamicImports,dynamicImportBindings}=dynamicImportDetails(ac,actual.values.map(v=>v.node),actual.name);
  const aliasDefinitions=(o?.chain||[]).filter(x=>x.aliasBinding).map(x=>cite(x.c,x.value.site,'Component alias definition '+x.aliasBinding.name));
  return{...item,status:o?.external?'external-import-binding':o?.chain.some(x=>x.d)?'resolved-import-binding':'local-lexical-binding',localName:b.name,bindingId:b.id,definitions:defs,aliasDefinitions,terminal:{name:actual.name,sourcePath:'app.asar/'+ac.relative,valueDefinitions:valueDefs},dynamicImports,dynamicImportBindings,dynamicImportScanStatus:ac.compacted?'not-scanned-auxiliary-body-pruned':'static-scanned',mode:'unknown',runtimeStatus:'not-verified'};
}
const jsxInfo=n=>{if(n.type!=='CallExpression')return null;const callee=unwrap(n.callee);return callee?.type==='MemberExpression'&&!callee.computed&&['jsx','jsxs','jsxDEV','createElement'].includes(callee.property.name)&&n.arguments.length>=2?{component:n.arguments[0],props:n.arguments[1],creator:callee}:null;};
const props=n=>n?.type==='ObjectExpression'?new Map(n.properties.filter(x=>x.type==='ObjectProperty'&&keyName(x)!==null).map(x=>[keyName(x),x.value])):new Map();
function scalar(c,n,env=new Map()){if(!n)return null;const v=evaluate(c,n,env);return{expression:brief(c,n),status:v.known&&['string','number','boolean','undefined'].includes(typeof v.value)||v.known&&v.value===null?'static-resolved':'dynamic-unknown',...(v.known&&['string','number','boolean'].includes(typeof v.value)||v.known&&v.value===null?{value:v.value}:v.known&&v.value===undefined?{valueKind:'undefined'}:{}),reason:v.known?null:v.reason,evidenceIds:v.trace,initializationOrder:'not-verified'};}
function elementTree(c,n,depth=0){if(!n)return null;if(depth>18)return{status:'depth-limit',...cite(c,n,'Element tree depth-limited expression')};const j=jsxInfo(n);if(j){const p=props(j.props), scalarProps={};for(const[k,v]of p)if(k!=='children'&&k!=='element'&&k!=='fallback')scalarProps[k]=scalar(c,v);return{kind:'jsx-element',component:componentBinding(c,j.component),props:scalarProps,...cite(c,n,'Complete route element component call'),children:elementTree(c,p.get('children'),depth+1)};}if(n.type==='ArrayExpression')return{kind:'array',children:n.elements.filter(Boolean).map(x=>elementTree(c,x,depth+1))};if(n.type==='ConditionalExpression')return{kind:'conditional',test:condition(c,n.test,'element-test'),consequent:elementTree(c,n.consequent,depth+1),alternate:elementTree(c,n.alternate,depth+1)};if(n.type==='LogicalExpression')return{kind:'logical',operator:n.operator,test:condition(c,n.left,'element-logical-left'),right:elementTree(c,n.right,depth+1)};return{kind:'expression',...scalar(c,n),...cite(c,n,'Route element expression')};}
function condition(c,n,branch){return{branch,expression:brief(c,n,600),...cite(c,n,'Enclosing/element condition '+branch),staticValue:scalar(c,n),runtimeMeaning:'unknown'};}
function ancestorConditions(c,n){const result=[];let child=n,parent=c.parents.get(child);while(parent){if(parent.type==='ConditionalExpression'&&child!==parent.test)result.push(condition(c,parent.test,child===parent.consequent?'truthy':'falsy'));if(parent.type==='LogicalExpression'&&child===parent.right)result.push(condition(c,parent.left,parent.operator==='&&'?'truthy':parent.operator==='||'?'falsy':'nullish'));if(parent.type==='IfStatement'&&child!==parent.test)result.push(condition(c,parent.test,child===parent.consequent?'if-true':'if-false'));child=parent;parent=c.parents.get(parent);}return result;}
function enclosingFunction(c,n){let p=c.parents.get(n);while(p){if(isFunction(p))return{name:p.id?.name||null,...cite(c,p,'Enclosing route-construction function')};p=c.parents.get(p);}return null;}
function mapContexts(c,n){const result=[];let child=n,p=c.parents.get(child);while(p){if(isFunction(p)){const call=c.parents.get(p);if(call?.type==='CallExpression'&&call.arguments.includes(p)&&call.callee.type==='MemberExpression'&&!call.callee.computed&&call.callee.property.name==='map'){const input=evaluate(c,call.callee.object);const b=p.params[0]?.type==='Identifier'?resolve(c,p.params[0]):null;result.push({call,callback:p,binding:b,input,...cite(c,call,'Route registration array-map template'),inputExpression:brief(c,call.callee.object),staticInputCount:input.known&&Array.isArray(input.value)?input.value.length:null});}}child=p;p=c.parents.get(p);}return result;}

function refreshExisting(){
  const resultPath=path.join(output,'route-contracts.json'),evidencePath=path.join(output,'route-contract-evidence.jsonl');
  const result=JSON.parse(fs.readFileSync(resultPath,'utf8'));
  if(result.baselineId!==baseline.baselineId)throw new Error('Existing route inventory baseline mismatch');
  // A full run reaches this function with its freshly written evidence still
  // in memory. Rebuild once from disk, deduplicate exact claims, and normalize
  // references; the fragment-only refresh uses the same path.
  evidence.length=0;evidenceKeys.clear();const idMap=new Map(),originalIdClaims=new Map();
  for(const e of fs.readFileSync(evidencePath,'utf8').trim().split('\n').map(JSON.parse)){const key=e.sourcePath.replace(/^app\.asar\//,'')+':'+e.locator.start+':'+e.locator.endExclusive+':'+e.claim;if(originalIdClaims.has(e.id)&&originalIdClaims.get(e.id)!==key)throw new Error('Conflicting original evidence ID');originalIdClaims.set(e.id,key);let id=evidenceKeys.get(key);if(!id){id='ROUTE-AST-E'+String(evidence.length+1).padStart(5,'0');evidenceKeys.set(key,id);evidence.push({...e,id});}idMap.set(e.id,id);}
  function remap(value){if(!value||typeof value!=='object')return;for(const[k,v]of Object.entries(value)){if(k==='evidenceId')value[k]=idMap.get(v)||v;else if(k==='evidenceIds')value[k]=v.map(id=>idMap.get(id)||id);else if(Array.isArray(v))v.forEach(remap);else remap(v);}}
  remap(result);
  const sourceCache=new Map();
  function frozenSource(relative){if(!sourceCache.has(relative)){const buffer=fs.readFileSync(path.join(baseline.extractedDirectory,relative));const file=expected.get(relative);if(!file||sha(buffer)!==file.sha256)throw new Error('Changed/missing frozen fragment input');sourceCache.set(relative,{buffer,hash:file.sha256});}return sourceCache.get(relative);}
  const refreshed=new Map();
  for(const component of result.componentBindings){if(!scopeFiles.some(f=>component.terminal?.sourcePath==='app.asar/'+f))continue;const dynamicImports=[],dynamicImportBindings=[];
    for(const def of component.terminal.valueDefinitions){const relative=def.sourcePath.replace(/^app\.asar\//,''),s=frozenSource(relative),span=s.buffer.subarray(def.range.start,def.range.endExclusive),fragment=span.toString('utf8');if(!Buffer.from(fragment).equals(span))throw new Error('Invalid UTF-8 fragment');let ast;try{ast=parser.parse(fragment,{sourceType:'module',attachComment:false,errorRecovery:false});}catch(first){try{ast=parser.parseExpression(fragment,{attachComment:false});}catch{throw first;}}
      const offsets=new Uint32Array(fragment.length+1);let bytes=def.range.start;for(let i=0;i<fragment.length;i++){offsets[i]=bytes;const cp=fragment.codePointAt(i);if(cp>0xffff){offsets[i+1]=bytes;bytes+=4;i++;}else bytes+=cp<128?1:cp<2048?2:3;}offsets[fragment.length]=bytes;
      const c={relative,text:fragment,buffer:s.buffer,hash:s.hash,offsets};const details=dynamicImportDetails(c,[ast],component.terminal.name);dynamicImports.push(...details.dynamicImports);dynamicImportBindings.push(...details.dynamicImportBindings);
    }
    refreshed.set(component.bindingId,{dynamicImports,dynamicImportBindings,dynamicImportScanStatus:'static-scanned; frozen exact definition fragments'});
  }
  function update(value){if(!value||typeof value!=='object')return;if(value.bindingId&&refreshed.has(value.bindingId))Object.assign(value,refreshed.get(value.bindingId));for(const child of Object.values(value))if(Array.isArray(child))child.forEach(update);else update(child);}
  update(result);
  const legacyRoutesPath=path.join(output,'routes.json'),legacyEvidencePath=path.join(output,'evidence.jsonl');
  if(fs.existsSync(legacyRoutesPath)&&fs.existsSync(legacyEvidencePath)){
    const legacyBytes=fs.readFileSync(legacyRoutesPath),legacyEvBytes=fs.readFileSync(legacyEvidencePath),rows=JSON.parse(legacyBytes).filter(x=>['route-registration','computed-route-registration'].includes(x.kind)),oldEvidence=new Map(legacyEvBytes.toString('utf8').trim().split('\n').map(s=>{const e=JSON.parse(s);return[e.id,e];})),matches=[];
    for(const row of rows){const e=oldEvidence.get(row.evidenceId),span=e?.locator;const route=e&&span?result.registrations.filter(r=>r.sourcePath===e.sourcePath&&r.sourceHash===e.sourceHash&&r.range.start<=span.start&&r.range.endExclusive>=span.endExclusive).sort((a,b)=>(a.range.endExclusive-a.range.start)-(b.range.endExclusive-b.range.start))[0]:null;matches.push({legacyEvidenceId:row.evidenceId,kind:row.kind,routeId:route?.id||null});}
    const matched=new Set(matches.map(x=>x.routeId).filter(Boolean)),missing=result.registrations.filter(x=>!matched.has(x.id));
    result.legacyLexicalReconciliation={inputFiles:[{path:'routes.json',sha256:sha(legacyBytes)},{path:'evidence.jsonl',sha256:sha(legacyEvBytes)}],lexicalRouteCandidateRows:rows.length,matchedLegacyRows:matches.filter(x=>x.routeId).length,matchedDistinctASTRouteCalls:matched.size,unmatchedLegacyRows:matches.filter(x=>!x.routeId).length,ASTRouteCallsOutsideThoseCandidates:missing.length,pathBearingASTCallsOutsideThoseCandidates:missing.filter(x=>x.propsKeys.includes('path')).length,pathlessASTCallsOutsideThoseCandidates:missing.filter(x=>!x.propsKeys.includes('path')).length,matches,additionalPathCalls:missing.filter(x=>x.propsKeys.includes('path')).map(x=>({routeId:x.id,expression:x.path.expression,staticValue:x.path.value,evidenceId:x.evidenceId})),scope:'Comparison of 77 literal + 51 computed lexical candidate rows with the two-file AST denominator; it does not assign functionality or mode.'};
  }
  const notesPath=path.join(output,'route-guard-notes.json');
  if(fs.existsSync(notesPath)){const noteBuffer=fs.readFileSync(notesPath),notes=JSON.parse(noteBuffer);if(notes.baselineId!==baseline.baselineId)throw new Error('Guard notes baseline mismatch');const translated=new Map();
    for(const e of notes.evidence){const relative=e.sourcePath.replace(/^app\.asar\//,''),s=frozenSource(relative),start=e.byteRange.start,end=e.byteRange.end,expectedHash=e.sourceHash||e.sourceSha256,spanHash=e.spanHash||e.spanSha256;if(s.hash!==expectedHash||sha(s.buffer.subarray(start,end))!==spanHash)throw new Error('Guard evidence hash mismatch '+e.id);const claim='Guard semantic supplement: '+e.label,key=relative+':'+start+':'+end+':'+claim;let id=evidenceKeys.get(key);if(!id){id='ROUTE-AST-E'+String(evidence.length+1).padStart(5,'0');evidenceKeys.set(key,id);evidence.push({id,baselineId:baseline.baselineId,claim,sourcePath:'app.asar/'+relative,sourceHash:s.hash,locator:{kind:'byte-range',start,endExclusive:end},spanHash,method:'supplemental-static-guard-trace',confidence:'confirmed',verificationStatus:'static-confirmed; runtime-unverified',supplementEvidenceId:e.id});}translated.set(e.id,id);}
    result.guardReviews={sourceFile:'route-guard-notes.json',sourceHash:sha(noteBuffer),mode:'unknown',notes:notes.notes.map(n=>{const{routeContractReferences,...note}=n;return{...note,evidenceIds:n.evidenceIds.map(id=>translated.get(id)),registrationReferences:(n.routeIds||[]).map(id=>result.registrations.find(r=>r.id===id)).filter(Boolean).map(r=>({routeId:r.id,evidenceId:r.evidenceId,sourcePath:r.sourcePath,sourceHash:r.sourceHash,range:r.range}))};})};
    const getNames=element=>{const names=[];function read(n){if(!n||typeof n!=='object')return;if(n.component?.expression)names.push(n.component.expression);for(const v of Object.values(n))if(Array.isArray(v))v.forEach(read);else if(v&&typeof v==='object')read(v);}read(element);return new Set(names);};
    for(const route of result.registrations){const names=getNames(route.element);for(const a of route.ancestorElements)for(const name of getNames(a.element))names.add(name);route.guardReviewIds=notes.notes.filter(n=>n.componentNames.some(name=>names.has(name))).map(n=>n.id);}
    result.summary.guardSemanticNotes=notes.notes.length;result.summary.guardSupplementEvidenceRecords=notes.evidence.length;
  }
  result.summary.evidenceRecords=evidence.length;
  result.summary.componentDynamicImportSites=result.componentBindings.reduce((n,c)=>n+(c.dynamicImports?.length||0),0);
  result.summary.componentSelectedImportExports=result.componentBindings.reduce((n,c)=>n+(c.dynamicImportBindings?.length||0),0);
  result.fragmentSupplement={method:'Babel parse of exact frozen component-definition source spans',targetExecuted:false,scope:'only definitions already bound in the full requested-file AST',baselineId:baseline.baselineId};
  fs.writeFileSync(resultPath,JSON.stringify(result,null,2)+'\n');fs.writeFileSync(evidencePath,evidence.map(x=>JSON.stringify(x)).join('\n')+'\n');fs.writeFileSync(path.join(output,'route-contract-summary.json'),JSON.stringify(result.summary,null,2)+'\n');
  const mdPath=path.join(output,'route-contract-summary.md');let md=fs.readFileSync(mdPath,'utf8').split('\n## Static guard and component review')[0];md+='\n## Static guard and component review\n\n';md+=`Selected component imports: ${result.summary.componentDynamicImportSites} import sites and ${result.summary.componentSelectedImportExports} fixed selected exports. Evidence records after supplements: ${evidence.length}.\n\n`;
  if(result.guardReviews)md+=result.guardReviews.notes.map(n=>`- ${n.id}: ${n.conclusion} Mode: unknown; runtime unverified. Evidence: ${n.evidenceIds.join(', ')}.`).join('\n')+'\n';
  fs.writeFileSync(mdPath,md);return result.summary;
}
if(flags.get('refresh-imports')==='true'){console.log(JSON.stringify(refreshExisting(),null,2));process.exit(0);}

// Import/export proof fixes Route identity; local minified names alone are not identity.
const shared=readContext(auxiliaryFile);
const routeExport=shared.exports.get('san'), routeOrigin=bindingOrigin(shared,shared.root.bindings.get(routeExport?.local)),routeSymbol=routeOrigin?.binding?.name;
const factoryExport=shared.exports.get('man'),factoryOrigin=bindingOrigin(shared,shared.root.bindings.get(factoryExport?.local)),factorySymbol=factoryOrigin?.binding?.name;
const navigateExport=shared.exports.get('aan'),navigateOrigin=bindingOrigin(shared,shared.root.bindings.get(navigateExport?.local)),navigateSymbol=navigateOrigin?.binding?.name;
if(!routeSymbol||!factorySymbol)throw new Error('Expected Route and createRoutesFromElements exports missing');
const routeDefinition=shared.root.bindings.get(routeSymbol)?.values.find(x=>x.node.type==='FunctionDeclaration')?.node;
const factoryDefinition=shared.root.bindings.get(factorySymbol)?.values.find(x=>x.node.type==='FunctionDeclaration')?.node;
if(!routeDefinition||!factoryDefinition||!shared.text.slice(routeDefinition.start,routeDefinition.end).includes('A <Route> is only ever'))throw new Error('Route export identity proof failed');
const identityEvidence=[ev(shared,routeExport.node,'Route export identity san -> '+routeSymbol),ev(shared,routeDefinition,'Route component rejects direct rendering; complete definition'),ev(shared,factoryExport.node,'Route element conversion export man -> '+factorySymbol),ev(shared,factoryDefinition,'Complete Route-element-to-route-record conversion definition')];
for(const o of[routeOrigin,factoryOrigin,navigateOrigin])for(const step of o?.chain||[])if(step.aliasBinding)identityEvidence.push(ev(step.c,step.value.site,'Route/navigation identity alias '+step.aliasBinding.name));
// Only fixed values/exports/ranges are needed from this auxiliary bundle. Drop
// executable function bodies and unknown call argument trees in the in-memory
// AST after binding collection, retaining untouched source bytes for evidence.
// This bounds memory without altering either target source or requested ASTs.
for(const n of shared.allNodes){
  if(isFunction(n))n.body={type:'BlockStatement',start:n.body.start,end:n.body.end,body:[]};
  if(n.type==='CallExpression'&&!(n.callee.type==='MemberExpression'&&!n.callee.computed&&['map','filter'].includes(n.callee.property.name)))n.arguments=[];
}
// AST parents point to sibling-heavy initialization sequences. They are not
// needed for the auxiliary constants; drop these references as well as scopes.
const auxiliaryBindings=new WeakMap();
for(const n of shared.allNodes)if(n.type==='Identifier'){const b=resolve(shared,n);if(b){delete b.scope;auxiliaryBindings.set(n,b);}}
shared.nodeBindings=auxiliaryBindings;shared.parents=new WeakMap();shared.scopes=new WeakMap();shared.compacted=true;
shared.ast=null;shared.allNodes=[];global.gc?.();
const identity=(c,n,symbol)=>{const o=origin(c,n);return o?.context===shared&&o.binding?.name===symbol;};
const calls=[], nonRoutePathProps=[], consumers=[], navigationTargets=[], components={}, registrationByNode=new WeakMap();
for(const relative of scopeFiles){
  const c=readContext(relative);let jsxCalls=0,componentOriginUnresolved=0;
  for(const n of c.allNodes){const j=jsxInfo(n);if(!j)continue;jsxCalls++;const p=props(j.props);if(!identity(c,j.component,routeSymbol)){if(p.has('path'))nonRoutePathProps.push({sourcePath:'app.asar/'+relative,component:componentBinding(c,j.component),path:scalar(c,p.get('path')),...cite(c,n,'JSX path prop outside proven Route identity'),classification:'non-Route JSX path prop; not registration'});if(j.component.type==='Identifier'&&!resolve(c,j.component))componentOriginUnresolved++;continue;}
    const maps=mapContexts(c,n), pnode=p.get('path'), pathResolution=pnode?scalar(c,pnode):{status:'no-path',reason:p.has('index')?'index-route':'layout-route'};
    const instances=[];
    if(maps.length===1&&maps[0].binding&&maps[0].input.known&&Array.isArray(maps[0].input.value))for(const[index,value]of maps[0].input.value.entries()){const env=new Map([[maps[0].binding.id,value]]);instances.push({index,path:pnode?scalar(c,pnode,env):{status:'no-path'}});}
    const id='ROUTE-'+String(calls.length+1).padStart(4,'0');const record={id,...cite(c,n,'Complete actual Route JSX registration call'),callType:'Route-element construction',registrationStatus:'static-confirmed',componentBinding:componentBinding(c,j.component),propsKeys:[...p.keys()],hasSpreadProps:j.props.type==='ObjectExpression'&&j.props.properties.some(x=>x.type==='SpreadElement'),path:pathResolution,index:p.has('index')?scalar(c,p.get('index')):null,element:elementTree(c,p.get('element')),enclosingConditions:ancestorConditions(c,n),enclosingFunction:enclosingFunction(c,n),arrayMapTemplates:maps.map(m=>({sourcePath:m.sourcePath,sourceHash:m.sourceHash,range:m.range,evidenceId:m.evidenceId,inputExpression:m.inputExpression,staticInputCount:m.staticInputCount,parameterBinding:m.binding?.id||null,reason:m.input.known?null:m.input.reason})),staticMapInstances:instances,parentRouteIds:[],conversionConsumerIds:[],mode:'unknown',modeConfidence:'unresolved',runtimeStatus:'not-verified'};
    calls.push(record);registrationByNode.set(n,{record,c,n,props:p});
  }
  c.scanCounters={allASTNodes:c.allNodes.length,jsxCreatorCalls:jsxCalls,unboundIdentifierJSXComponents:componentOriginUnresolved};
}
// Expand only the construction expression grammar to connect Route children.
// This includes literal Fragment/array children, unique local aliases, and map
// templates. Conditions retain both alternatives without asserting reachability.
function routeRoots(c,n,seen=new Set()){
  if(!n)return[];n=unwrap(n);const r=registrationByNode.get(n);if(r)return[r];const j=jsxInfo(n);if(j)return routeRoots(c,props(j.props).get('children'),seen);
  if(n.type==='Identifier'){const b=resolve(c,n);if(!b||seen.has(b.id)||b.values.length!==1)return[];return routeRoots(c,b.values[0].node,new Set([...seen,b.id]));}
  if(n.type==='ArrayExpression')return n.elements.flatMap(x=>routeRoots(c,x,seen));
  if(n.type==='ConditionalExpression')return[...routeRoots(c,n.consequent,seen),...routeRoots(c,n.alternate,seen)];
  if(n.type==='LogicalExpression')return[...routeRoots(c,n.left,seen),...routeRoots(c,n.right,seen)];
  if(n.type==='CallExpression'&&n.callee.type==='MemberExpression'&&n.callee.property.name==='map'){const cb=n.arguments[0];return isFunction(cb)?routeRoots(c,cb.body,seen):[];}
  return[];
}
for(const c of contexts.values())if(scopeFiles.includes(c.relative))for(const n of c.allNodes){const entry=registrationByNode.get(n);if(!entry)continue;const roots=routeRoots(c,entry.props.get('children'));for(const child of roots)if(child.record.id!==entry.record.id&&!child.record.parentRouteIds.includes(entry.record.id))child.record.parentRouteIds.push(entry.record.id);}
const byId=new Map(calls.map(x=>[x.id,x]));
function descendants(r,seen=new Set()){if(seen.has(r.id))return[];const next=new Set([...seen,r.id]);return[r,...calls.filter(x=>x.parentRouteIds.includes(r.id)).flatMap(x=>descendants(x,next))];}
for(const relative of scopeFiles){const c=contexts.get(relative);for(const n of c.allNodes){
  if(n.type==='CallExpression'&&identity(c,unwrap(n.callee),factorySymbol)){const roots=routeRoots(c,n.arguments[0]),id='ROUTE-CONSUMER-'+String(consumers.length+1).padStart(3,'0');const affected=[...new Set(roots.flatMap(r=>descendants(r.record)).map(r=>r.id))];consumers.push({id,kind:'createRoutesFromElements',...cite(c,n,'Complete Route-element conversion/registration consumer'),callee:componentBinding(c,unwrap(n.callee)),inputExpression:n.arguments[0]?brief(c,n.arguments[0]):null,rootRouteIds:roots.map(x=>x.record.id),registrationIds:affected,resultAssignment:c.parents.get(n)?.type==='AssignmentExpression'&&c.parents.get(n).left.type==='Identifier'?c.parents.get(n).left.name:null,runtimeUse:'not-verified'});for(const id of affected)byId.get(id).conversionConsumerIds.push(consumers.at(-1).id);}
  const j=jsxInfo(n);if(j&&identity(c,j.component,navigateSymbol)){const p=props(j.props);navigationTargets.push({kind:'Navigate-component',...cite(c,n,'Navigation target JSX call; not route registration'),component:componentBinding(c,j.component),target:p.has('to')?scalar(c,p.get('to')):null,mode:'unknown'});}
  if(n.type==='ObjectExpression'){const p=props(n),type=p.get('type');if(type?.type==='StringLiteral'&&type.value==='navigate-to-route'&&p.has('path'))navigationTargets.push({kind:'host-message-navigate-to-route',...cite(c,n,'Explicit host navigation target message; not route registration'),target:scalar(c,p.get('path')),mode:'unknown'});}
}}
function ancestors(r,seen=new Set()){if(seen.has(r.id))return[];return r.parentRouteIds.flatMap(id=>{const p=byId.get(id);return[p,...ancestors(p,new Set([...seen,r.id]))];});}
for(const r of calls){r.ancestorRouteIds=[...new Set(ancestors(r).map(x=>x.id))];r.ancestorElements=r.ancestorRouteIds.filter(id=>byId.get(id).element).map(id=>({routeId:id,element:byId.get(id).element}));r.enclosingRouteConditions=r.ancestorRouteIds.filter(id=>byId.get(id).enclosingConditions.length).map(id=>({routeId:id,conditions:byId.get(id).enclosingConditions}));}
// Keep selected component definitions in one table for review without copying code.
function collectComponents(tree){if(!tree)return;if(tree.component?.bindingId)components[tree.component.bindingId]=tree.component;if(Array.isArray(tree.children))tree.children.forEach(collectComponents);else collectComponents(tree.children);collectComponents(tree.right);collectComponents(tree.consequent);collectComponents(tree.alternate);}
calls.forEach(r=>collectComponents(r.element));
const knownPaths=calls.filter(x=>x.path.status==='static-resolved'&&typeof x.path.value==='string');
const mapTemplates=calls.filter(x=>x.arrayMapTemplates.length), mapResolved=calls.filter(x=>x.staticMapInstances.length);
const resolvedInstances=mapResolved.flatMap(x=>x.staticMapInstances).filter(x=>x.path.status==='static-resolved');
const summary={baselineId:baseline.baselineId,requestedSourceFiles:scopeFiles.length,parsedRequestedSourceFiles:scopeFiles.length,requestedSourceParseErrors:0,actualRouteConstructionCalls:calls.length,constructionCallsByFile:Object.fromEntries(scopeFiles.map(f=>[f,calls.filter(r=>r.sourcePath==='app.asar/'+f).length])),pathBearingCalls:calls.filter(x=>x.propsKeys.includes('path')).length,indexCalls:calls.filter(x=>x.propsKeys.includes('index')).length,pathlessCalls:calls.filter(x=>!x.propsKeys.includes('path')).length,staticallyResolvedPathCalls:knownPaths.length,dynamicPathCalls:calls.filter(x=>x.path.status==='dynamic-unknown').length,mapTemplateCalls:mapTemplates.length,staticallyExpandedMapTemplateCalls:mapResolved.length,staticallyResolvedMapInstances:resolvedInstances.length,routeConversionConsumers:consumers.length,callsReachableInStaticConversionGraph:calls.filter(x=>x.conversionConsumerIds.length).length,callsOutsideStaticConversionGraph:calls.filter(x=>!x.conversionConsumerIds.length).length,nonRouteJSXPathProps:nonRoutePathProps.length,navigationTargetCandidates:navigationTargets.length,confirmedModeExclusions:0,runtimeVerifiedCalls:0,evidenceRecords:evidence.length};
const limitations=['Denominator covers actual JSX/createElement Route constructions with proven import/alias identity in exactly the two requested renderer files; it is not an asset-wide or product-wide functionality denominator.','The shared chunk is auxiliary import/export and fixed-constant evidence only; it is not added to the route-construction denominator.','Both branches of dynamic conditions and static route expressions are retained. Presence of a registration does not prove runtime reachability, entitlement, feature flag, or supported platform.','Single/equal static binding values and pure zero-argument single-return helper ASTs resolve paths without asserting that an initializer has executed. Other dynamic calls, unknown imports, mutations, destructuring, and block-bodied array callbacks remain unresolved.','Map templates count once as source constructions; expanded fixed map instances are separately counted and cannot be added to calls as a disjoint denominator.','Parent Route element components and inline enclosing conditions are recorded, but their behavior and cross-module guard semantics require separate evidence and runtime validation.','Navigate components and explicit host navigate-to-route messages are separate navigation targets. This is not a complete inventory of all navigation helpers.','No component/route is excluded by a chat/chatgpt name. All mode ownership is unknown in this generated structural inventory.','No target module was evaluated. No third-party implementation source is emitted.'];
fs.mkdirSync(output,{recursive:true});
const result={schemaVersion:1,baselineId:baseline.baselineId,method:'bounded supplemental Babel AST parse; target never executed',parser:{name:parserPackage.name,version:parserPackage.version,packageHash:sha(fs.readFileSync(parserPackageFile)),implementationHash:sha(fs.readFileSync(parserImpl))},sourceFiles:[...contexts.values()].map(c=>({sourcePath:'app.asar/'+c.relative,sourceHash:c.hash,sourceBytes:c.buffer.length,archiveByteOffset:c.archiveByteOffset,role:scopeFiles.includes(c.relative)?'registration-denominator':'auxiliary-binding-resolution',scanCounters:c.scanCounters||null})),routeIdentity:{exportName:'san',localSymbol:routeSymbol,conversionExportName:'man',conversionLocalSymbol:factorySymbol,navigationExportName:'aan',navigationLocalSymbol:navigateSymbol,evidenceIds:identityEvidence},summary,limitations,registrations:calls,conversionConsumers:consumers,componentBindings:Object.values(components),nonRoutePathProps,navigationTargets};
fs.writeFileSync(path.join(output,'route-contracts.json'),JSON.stringify(result,null,2)+'\n');
fs.writeFileSync(path.join(output,'route-contract-evidence.jsonl'),evidence.map(x=>JSON.stringify(x)).join('\n')+'\n');
fs.writeFileSync(path.join(output,'route-contract-summary.json'),JSON.stringify(summary,null,2)+'\n');
const summaryText=['# Frozen renderer Route AST inventory','',`Baseline: ${baseline.baselineId}. Static parsing only; target modules never executed.`, '',`Actual Route construction denominator: **${calls.length}/${calls.length}** complete AST calls in ${scopeFiles.length} requested files; ${summary.pathBearingCalls} path-bearing, ${summary.pathlessCalls} pathless (${summary.indexCalls} index).`, '',`Fixed path calls: ${summary.staticallyResolvedPathCalls}; dynamic path calls: ${summary.dynamicPathCalls}. Map templates: ${summary.mapTemplateCalls}; fixed expansions: ${summary.staticallyResolvedMapInstances} instances from ${summary.staticallyExpandedMapTemplateCalls} templates. These instance counts overlap the construction denominator.`, '',`Route conversion consumers: ${consumers.length}; static conversion graph covers ${summary.callsReachableInStaticConversionGraph}/${calls.length} constructions. Navigation target candidates: ${navigationTargets.length}, kept separately. Non-Route JSX path props: ${nonRoutePathProps.length}.`, '',`Runtime verified routes: 0. Confirmed mode exclusions: 0. Evidence records: ${evidence.length}; each contains source SHA-256, UTF-8 byte span, span SHA-256.`, '',...limitations.map(x=>'- '+x),'','Artifacts: route-contracts.json, route-contract-evidence.jsonl, route-contract-summary.json. Guard semantic notes, when present, are a separate static supplement and do not change this structural denominator.',''].join('\n');
fs.writeFileSync(path.join(output,'route-contract-summary.md'),summaryText);
console.log(JSON.stringify(refreshExisting(),null,2));
