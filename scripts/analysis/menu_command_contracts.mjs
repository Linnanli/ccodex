#!/usr/bin/env node
// Frozen JavaScript is parsed as data; this script never imports target modules.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url), flags=new Map();
for(let k=2;k<process.argv.length;k+=2){if(!process.argv[k+1])throw Error('Expected --flag value');flags.set(process.argv[k].slice(2),process.argv[k+1]);}
const output=path.resolve(flags.get('output')||'.analysis-local/entry-work');
const baseline=JSON.parse(fs.readFileSync(flags.get('baseline')||'.analysis-local/current-baseline.json','utf8'));
const manifest=JSON.parse(fs.readFileSync(path.join('analysis',baseline.baselineId,'files.json'),'utf8'));
const parserPath=flags.get('parser-path')||'/private/tmp/ccodex-rea-tooling/install/node_modules/@babel/parser';
const parser=require(parserPath), sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const sources=[], evidence=[], evKeys=new Map();
const isFn=n=>n&&['FunctionDeclaration','FunctionExpression','ArrowFunctionExpression','ClassMethod','ClassPrivateMethod','ObjectMethod'].includes(n.type);
const childKeys=n=>Object.entries(n).filter(([k])=>!['loc','extra','comments','leadingComments','trailingComments','innerComments','tokens','errors'].includes(k));
const children=n=>childKeys(n).flatMap(([,v])=>Array.isArray(v)?v.filter(x=>x&&typeof x.type==='string'):v&&typeof v.type==='string'?[v]:[]);
const names=n=>!n?[]:n.type==='Identifier'?[{name:n.name,member:[]}]:n.type==='AssignmentPattern'?names(n.left):n.type==='RestElement'?names(n.argument):n.type==='ArrayPattern'?n.elements.flatMap(names):n.type==='ObjectPattern'?n.properties.flatMap(p=>names(p.type==='RestElement'?p.argument:p.value).map(x=>({...x,member:[p.key?.name??p.key?.value,...x.member]}))):[];
function load(relative,fragmentRanges=null){
 const expected=manifest.archiveFiles.find(x=>x.archivePath===relative),buf=fs.readFileSync(path.join(baseline.extractedDirectory,relative));
 if(!expected||sha(buf)!==expected.sha256)throw Error('Frozen source hash mismatch: '+relative);
 const text=buf.toString('utf8');if(!Buffer.from(text).equals(buf))throw Error('Lossless UTF8 required');
 const offsets=new Uint32Array(text.length+1);let bytes=0;for(let i=0;i<text.length;i++){offsets[i]=bytes;const cp=text.codePointAt(i);if(cp>0xffff){offsets[++i]=bytes;bytes+=4;}else bytes+=cp<128?1:cp<2048?2:3;}offsets[text.length]=bytes;
 const parseOptions={sourceType:'unambiguous',attachComment:false,errorRecovery:false,plugins:['jsx']};
 const asts=fragmentRanges?fragmentRanges.map(r=>{const base=buf.subarray(0,r.start).toString('utf8').length,end=buf.subarray(0,r.end).toString('utf8').length;const ast=parser.parse(text.slice(base,end),parseOptions);function adjust(n){n.start+=base;n.end+=base;for(const ch of children(n))adjust(ch);}adjust(ast.program);return ast;}):[parser.parse(text,parseOptions)];
 const ast=asts[0];
 const c={relative,buf,text,offsets,hash:expected.sha256,archiveByteOffset:expected.archiveByteOffset,ast,fragmentRanges,nodes:[],parent:new WeakMap(),scope:new WeakMap(),owner:new WeakMap(),exports:new Map()};
 c.raw=n=>text.slice(n.start,n.end);c.range=n=>({kind:'byte-range',start:offsets[n.start],endExclusive:offsets[n.end]});
 c.root={kind:'program',parent:null,bindings:new Map()};
 function add(s,name,b){const l=s.bindings.get(name)||[];l.push(b);s.bindings.set(name,l);}
 function walk(n,s=c.root,p=null,owner=null){
  c.nodes.push(n);if(p)c.parent.set(n,p);
  if(n.type==='FunctionDeclaration'&&n.id)add(s,n.id.name,{node:n,kind:'function',callable:n,name:n.id.name});
  if(n.type==='ClassDeclaration'&&n.id)add(s,n.id.name,{node:n,kind:'class',value:n,name:n.id.name});
  if(n.type==='ClassDeclaration'||n.type==='ClassExpression'){owner={node:n,name:n.id?.name||p?.id?.name||'<anonymous>',methods:new Map(),fields:new Map()};for(const m of n.body.body){let k=m.computed?m.key?.value:m.key?.name??m.key?.id?.name;if(k!=null){if(isFn(m))owner.methods.set(k,m);else owner.fields.set(k,m);}}}
  if(isFn(n)){s={kind:'function',parent:s,bindings:new Map(),node:n};if(n.type==='FunctionExpression'&&n.id)add(s,n.id.name,{node:n,kind:'function',callable:n,name:n.id.name});for(const arg of n.params||[])for(const v of names(arg))add(s,v.name,{node:arg,kind:'parameter',member:v.member,name:v.name});}
  else if(n.type==='BlockStatement'||n.type==='CatchClause'){s={kind:'block',parent:s,bindings:new Map(),node:n};if(n.type==='CatchClause')for(const v of names(n.param))add(s,v.name,{node:n.param,kind:'catch',name:v.name});}
  c.scope.set(n,s);if(owner)c.owner.set(n,owner);
  if(n.type==='VariableDeclarator'){let bs=s;if(p?.kind==='var')while(bs.parent&&!['function','program'].includes(bs.kind))bs=bs.parent;for(const v of names(n.id))add(bs,v.name,{node:n,kind:'variable',value:n.init,member:v.member,name:v.name,callable:isFn(n.init)?n.init:null});}
  if(n.type==='ImportDeclaration')for(const sp of n.specifiers)add(s,sp.local.name,{node:sp,kind:'import',module:n.source.value,imported:sp.imported?.name||sp.type,name:sp.local.name});
  for(const ch of children(n))walk(ch,s,n,owner);
 }
 for(const part of asts)walk(part.program,{kind:'program',parent:null,bindings:new Map()});
 c.resolve=(n,name)=>{let s=c.scope.get(n);while(s){const b=s.bindings.get(name);if(b)return b.at(-1);s=s.parent;}return null;};
 for(const n of c.nodes){if(n.type==='CallExpression'&&c.raw(n.callee)==='Object.defineProperty'&&n.arguments[0]?.name==='exports'&&n.arguments[1]?.type==='StringLiteral'){const get=n.arguments[2]?.properties?.find(p=>p.key?.name==='get');const ret=get?.value?.body?.body?.find(x=>x.type==='ReturnStatement')?.argument;if(ret?.type==='Identifier')c.exports.set(n.arguments[1].value,{node:n,binding:c.resolve(ret,ret.name)});}}
 sources.push(c);return c;
}
function ev(c,n,kind){
 const r=c.range(n),key=[c.relative,r.start,r.endExclusive,kind].join(':');if(evKeys.has(key))return evKeys.get(key);
 const bytes=c.buf.subarray(r.start,r.endExclusive);if(!bytes.equals(Buffer.from(c.raw(n))))throw Error('AST span mismatch');
 const id='ENTRY-AST-E'+String(evidence.length+1).padStart(5,'0');evKeys.set(key,id);
 evidence.push({id,baselineId:baseline.baselineId,claim:kind,sourcePath:'app.asar/'+c.relative,sourceHash:c.hash,locator:r,spanHash:sha(bytes),method:'supplemental-babel-ast',confidence:'confirmed',verificationStatus:'static-confirmed; runtime-unverified'});return id;
}
const key=p=>p.computed?(p.key?.type==='StringLiteral'?p.key.value:null):p.key?.name??p.key?.value;
const props=n=>n?.type==='ObjectExpression'?new Map(n.properties.filter(p=>p.type==='ObjectProperty'||p.type==='ObjectMethod').map(p=>[key(p),p])):new Map();
function lit(n){if(!n)return{kind:'missing'};if(['StringLiteral','NumericLiteral','BooleanLiteral'].includes(n.type))return{kind:'literal',value:n.value};if(n.type==='NullLiteral')return{kind:'literal',value:null};if(n.type==='TemplateLiteral'&&!n.expressions.length)return{kind:'literal',value:n.quasis.map(q=>q.value.cooked??q.value.raw).join('')};return{kind:'dynamic'};}
const valueProp=(n,k)=>{const p=props(n).get(k);return p?.type==='ObjectMethod'?p:p?.value;};
function parts(n){if(n?.type==='SequenceExpression')return parts(n.expressions.at(-1));if(n?.type==='Identifier')return{root:n.name,members:[]};if(n?.type==='ThisExpression')return{root:'this',members:[]};if(['MemberExpression','OptionalMemberExpression'].includes(n?.type)){const b=parts(n.object),k=n.computed?lit(n.property).value:n.property.name;if(b)return{...b,members:[...b.members,k]};}return null;}
const nearest=(c,n,predicate)=>{let x=n;while(x){if(predicate(x))return x;x=c.parent.get(x);}return null;};
const literalOverrides=new Map();
function constant(c,n,seen=new Set()){
 const l=lit(n);if(l.kind!=='dynamic')return l;if(!n||seen.has(n))return l;seen.add(n);
 if(n.type==='UnaryExpression'&&n.operator==='!'){const v=constant(c,n.argument,seen);if(v.kind==='literal')return{kind:'literal',value:!v.value};}
 if(n.type==='Identifier'){const b=c.resolve(n,n.name);if(literalOverrides.has(b))return{kind:'literal',value:literalOverrides.get(b)};if(b?.value)return constant(c,b.value,seen);}
 if(n.type==='TemplateLiteral'){const values=n.expressions.map(x=>constant(c,x,new Set(seen)));if(values.every(v=>v.kind==='literal'&&['string','number','boolean'].includes(typeof v.value)))return{kind:'literal',value:n.quasis.map((q,i)=>(q.value.cooked??q.value.raw)+(i<values.length?String(values[i].value):'')).join('')};}
 const p=parts(n);if(p&&p.root!=='this'&&p.members.length){let v=c.resolve(n,p.root)?.value;for(const k of p.members)v=valueProp(v,k);if(v)return constant(c,v,seen);}
 return l;
}
function moduleOf(c,b,seen=new Set()){
 if(!b||seen.has(b))return null;seen.add(b);if(b.module)return b.module;
 const n=b.value;if(n?.type==='CallExpression'&&n.callee?.name==='require')return lit(n.arguments[0]).value;
 if(n?.type==='CallExpression')for(const a of n.arguments||[])if(a.type==='Identifier'){const m=moduleOf(c,c.resolve(a,a.name),seen);if(m)return m;}
 if(n?.type==='Identifier')return moduleOf(c,c.resolve(n,n.name),seen);return null;
}
function describe(c,n){const l=constant(c,n),p=parts(n);return{...l,...l.kind==='dynamic'?{expression:c.raw(n).slice(0,700)}:{},...p&&p.root!=='this'?{sourceBinding:bindingRecord(c,c.resolve(n,p.root)),propertyPath:p.members}:{},evidenceId:n?ev(c,n,'Complete value expression'):null};}
function bindingRecord(c,b){if(!b)return{status:'unbound'};return{status:'lexical-bound',name:b.name,kind:b.kind,parameterPropertyPath:b.member||[],moduleSpecifier:moduleOf(c,b),definitionEvidenceId:ev(c,b.node,'Lexical binding definition')};}
function conditions(c,node,stop=null){const out=[];let child=node;for(let p=c.parent.get(child);p&&p!==stop;child=p,p=c.parent.get(p)){
  let test=null,branch=null;
  if(p.type==='IfStatement'){test=p.test;branch=child===p.consequent?'consequent':child===p.alternate?'alternate':null;}
  if(p.type==='ConditionalExpression'){test=p.test;branch=child===p.consequent?'consequent':child===p.alternate?'alternate':null;}
  if(p.type==='LogicalExpression'&&child===p.right){test=p.left;branch=p.operator==='&&'?'truthy-RHS':p.operator==='||'?'falsy-RHS':'nullish-RHS';}
  if(test&&branch)out.push({kind:p.type,branch,expression:c.raw(test).slice(0,1200),conditionEvidenceId:ev(c,test,'Enclosing condition'),completeControlEvidenceId:ev(c,p,'Complete enclosing control expression')});
  if(p.type==='SwitchCase')out.push({kind:'SwitchCase',branch:describe(c,p.test),completeControlEvidenceId:ev(c,p,'Enclosing switch case')});
  if(['ForOfStatement','ForInStatement','ForStatement','WhileStatement','DoWhileStatement'].includes(p.type))out.push({kind:p.type,iteration:'runtime-unknown',completeControlEvidenceId:ev(c,p,'Enclosing registration loop')});
 }return out;
}
function callable(c,n,seen=new Set()){
 if(isFn(n))return{c,node:n,status:'inline-callable'};
 if(!n||seen.has(n))return null;seen.add(n);
 if(n.type==='Identifier'){const b=c.resolve(n,n.name);if(b?.callable)return{c,node:b.callable,status:'bound-local-callable',binding:b};if(b?.value)return callable(c,b.value,seen);}
 const p=parts(n);if(p?.root==='this'&&p.members.length===1){const own=c.owner.get(n),m=own?.methods.get(p.members[0])||own?.fields.get(p.members[0])?.value;if(isFn(m))return{c,node:m,status:'bound-local-class-callable',owner:own.name};}
 if(p&&p.root!=='this'&&p.members.length){const b=c.resolve(n,p.root),mod=moduleOf(c,b),relative=mod?.startsWith('.')?path.posix.normalize(path.posix.join(path.posix.dirname(c.relative),mod)):null,target=sources.find(x=>x.relative===relative),exported=target?.exports.get(p.members[0]);if(exported?.binding?.callable&&p.members.length===1)return{c:target,node:exported.binding.callable,status:'bound-imported-callable',binding:exported.binding,importEvidenceId:ev(c,b.node,'Bound imported namespace'),exportEvidenceId:ev(target,exported.node,'Export getter binding')};
  if(b?.value?.type==='ObjectExpression'){const prop=valueProp(b.value,p.members[0]);return callable(c,prop,seen);}
 }
 return null;
}
function callee(c,call){const p=parts(call.callee),b=p&&p.root!=='this'?c.resolve(call,p.root):null,fn=callable(c,call.callee);return{expression:c.raw(call.callee),status:fn?.status||(!p?'dynamic-callee':b?'bound-receiver-or-value-unresolved':p.root==='this'?'this-member-unresolved':'global-or-unresolved'),receiver:p,rootBinding:bindingRecord(c,b),...fn?{callableDefinitionEvidenceId:ev(fn.c,fn.node,'Bound callable complete definition'),importEvidenceId:fn.importEvidenceId,exportEvidenceId:fn.exportEvidenceId}:{}};}
function visit(n,fn,skipFunctions=false,root=n){fn(n);for(const ch of children(n))if(!(skipFunctions&&isFn(ch)&&ch!==root))visit(ch,fn,skipFunctions,root);}
function allCalls(n){const a=[];visit(n,x=>{if(['CallExpression','OptionalCallExpression','NewExpression'].includes(x.type))a.push(x);},true);return a;}
function callbackContract(c,n,depth=0,seen=new Set()){
 const fn=callable(c,n);if(!fn)return{status:'handler-unresolved',expression:n?c.raw(n).slice(0,800):null,binding:n?.type==='Identifier'?bindingRecord(c,c.resolve(n,n.name)):null};
 const id=fn.c.relative+':'+fn.node.start;if(seen.has(id))return{status:'recursive-bound-callable',definitionEvidenceId:ev(fn.c,fn.node,'Bound callback complete definition')};
 const nextSeen=new Set(seen);nextSeen.add(id);
 const calls=allCalls(fn.node).map(call=>{
  const p=parts(call.callee),b=p&&p.root!=='this'?fn.c.resolve(call,p.root):null,module=moduleOf(fn.c,b),bound=callee(fn.c,call);
  const result={...bound,evidenceId:ev(fn.c,call,'Call within bound callback'),conditions:conditions(fn.c,call,fn.node),arguments:call.arguments.map(x=>describe(fn.c,x))};
  if(module==='electron')result.boundary={kind:'native-electron-api',method:p.members.join('.'),status:'static-call-bound; runtime-unverified'};
  if(['sendMessageToWindow','sendMessageToWebContents','sendMessageToAllRegisteredWindows'].includes(p?.members.at(-1))){
   const expected=b?.kind==='parameter'&&b.member?.[0]==='windowManager';
   result.boundary={kind:'host-to-renderer-message',status:expected?'destructured-windowManager-parameter-call':'receiver-implementation-unresolved',receiverBinding:bindingRecord(fn.c,b),payloads:call.arguments.filter(a=>a.type==='ObjectExpression').map(a=>({type:describe(fn.c,valueProp(a,'type')),id:describe(fn.c,valueProp(a,'id')),completePayloadEvidenceId:ev(fn.c,a,'Complete cross-process payload')}))};
  }
  const local=callable(fn.c,call.callee);if(local&&depth<5)result.calleeTrace=callbackContract(fn.c,call.callee,depth+1,nextSeen);else if(local)result.traceLimit='maximum five local-call edges';
  return result;
 });
 return{status:fn.status,definitionEvidenceId:ev(fn.c,fn.node,'Bound callback complete definition'),ownerClass:fn.owner||null,importEvidenceId:fn.importEvidenceId,exportEvidenceId:fn.exportEvidenceId,calls,mode:'unknown',runtimeStatus:'unverified'};
}
const main=load('.vite/build/main-CqEoQDOU.js');
const metadata=load('.vite/build/src-BJv5Mk7n.js');
const nativeMenuCalls=main.nodes.filter(n=>['CallExpression','OptionalCallExpression','NewExpression'].includes(n.type)&&parts(n.callee)?.members.some(x=>['buildFromTemplate','setApplicationMenu','MenuItem','setMenu','setContextMenu','popUpContextMenu'].includes(x))&&moduleOf(main,main.resolve(n,parts(n.callee).root))==='electron');
const applicationInstall=nativeMenuCalls.filter(n=>parts(n.callee).members.at(-1)==='setApplicationMenu');
if(applicationInstall.length!==1)throw Error('Expected exactly one bound application menu installer');
const applicationFactory=nearest(main,applicationInstall[0],isFn);
const applicationBuild=nativeMenuCalls.filter(n=>parts(n.callee).members.at(-1)==='buildFromTemplate'&&nearest(main,n,isFn)===applicationFactory);
if(applicationBuild.length!==1)throw Error('Application factory build binding ambiguous');
const registryExport=metadata.exports.get('zt');if(!registryExport?.binding?.value)throw Error('Command metadata export binding missing');
const registry=registryExport.binding.value, registryEvidence=ev(metadata,registry,'Complete bound command metadata registry initializer');
const commands=[],commandSeen=new Set(),registrySources=[];
function registryWalk(n,kind=null,seen=new Set()){
 if(!n||seen.has(n))return;seen.add(n);
 if(n.type==='Identifier'){const b=metadata.resolve(n,n.name);if(b?.value){registrySources.push({binding:bindingRecord(metadata,b),kind});registryWalk(b.value,kind,seen);}return;}
 if(n.type==='ArrayExpression'){for(const e of n.elements)registryWalk(e,kind,seen);return;}
 if(n.type==='SpreadElement'){registryWalk(n.argument,kind,seen);return;}
 if(n.type==='CallExpression'){
  if(n.callee?.type==='MemberExpression'&&n.callee.property?.name==='map'&&n.callee.object?.type==='ArrayExpression'&&n.arguments[0]?.type==='ArrowFunctionExpression'&&n.arguments[0].body.type==='ObjectExpression'){
   const callback=n.arguments[0],parameter=callback.params[0];if(parameter?.type!=='Identifier')throw Error('Unresolved finite metadata map parameter');const b=metadata.resolve(parameter,parameter.name),values=n.callee.object.elements.map(x=>constant(metadata,x));if(values.some(x=>x.kind!=='literal'))throw Error('Dynamic metadata map input');
   registrySources.push({finiteMapEvidenceId:ev(metadata,n,'Complete finite metadata schema map'),sourceArrayEvidenceId:ev(metadata,n.callee.object,'Finite metadata map input array'),callbackEvidenceId:ev(metadata,callback,'Finite metadata schema producer'),parameterBinding:bindingRecord(metadata,b),instanceCount:values.length,kind});
   for(const v of values){literalOverrides.set(b,v.value);registryWalk(callback.body,kind,new Set(seen));}literalOverrides.delete(b);return;
  }
  const f=callable(metadata,n.callee);const sourceShape=f&&f.c===metadata&&f.node.body?.type==='BlockStatement'&&f.node.body.body.length===1&&f.node.body.body[0].type==='ReturnStatement'&&f.node.body.body[0].argument?.type==='CallExpression'&&f.node.body.body[0].argument.callee?.property?.name==='map';
  if(!sourceShape)throw Error('Unhandled registry construction call '+metadata.raw(n.callee));
  const callback=f.node.body.body[0].argument.arguments[0];const returned=callback?.body;if(returned?.type!=='ObjectExpression'||!valueProp(returned,'kind'))throw Error('Registry map kind transformer must be rechecked');
  registrySources.push({callEvidenceId:ev(metadata,n,'Registry kind transformer call'),transformerEvidenceId:ev(metadata,f.node,'Bound metadata kind transformer'),kind:lit(n.arguments[1]).value||null});
  registryWalk(n.arguments[0],lit(n.arguments[1]).value||null,seen);return;
 }
 if(n.type==='ObjectExpression'&&constant(metadata,valueProp(n,'id')).kind==='literal'){
  const id=constant(metadata,valueProp(n,'id')).value,identity=n.start+':'+id;if(commandSeen.has(identity))return;commandSeen.add(identity);
  const data={id,idValue:describe(metadata,valueProp(n,'id')),kind,definitionEvidenceId:ev(metadata,n,'Complete command metadata schema'),properties:[...props(n).keys()],requiredAccess:describe(metadata,valueProp(n,'requiredAccess')),shortcutScope:describe(metadata,valueProp(n,'shortcutScope')),commandMenu:describe(metadata,valueProp(n,'commandMenu')),electron:null,browser:null,handler:'metadata-only; actual consumer binding required',mode:'unknown',runtimeStatus:'unverified'};
  for(const platform of ['electron','browser']){const v=valueProp(n,platform);if(v)data[platform]={definitionEvidenceId:ev(metadata,v,'Complete '+platform+' command metadata'),defaultKeybindings:[],platformDefaultKeybindings:[],menuTitle:describe(metadata,valueProp(v,'menuTitle')),menuTitleIntlId:describe(metadata,valueProp(v,'menuTitleIntlId'))};if(v)visit(v,x=>{if(x.type==='ObjectExpression'&&valueProp(x,'key')){const row={key:describe(metadata,valueProp(x,'key')),when:describe(metadata,valueProp(x,'when')),definitionEvidenceId:ev(metadata,x,'Complete default keybinding schema'),conditions:conditions(metadata,x,n)};data[platform].defaultKeybindings.push(row);}});}
  commands.push(data);return;
 }
 throw Error('Unhandled registry AST '+n.type+' '+metadata.raw(n).slice(0,450));
}
registryWalk(registry);
const commandById=new Map(commands.map(x=>[x.id,x]));
const linkedMetadataExports=['zt','At','Ft','Pt','Mt','Ot','St','wt','xt'].map(name=>{const x=metadata.exports.get(name);return{name,exportEvidenceId:x?ev(metadata,x.node,'Command consumer export getter '+name):null,binding:x?bindingRecord(metadata,x.binding):null,definitionEvidenceId:x?.binding?.callable?ev(metadata,x.binding.callable,'Bound command metadata consumer '+name):null};});
const applicationConsumers=main.nodes.filter(n=>n.type==='CallExpression'&&callable(main,n.callee)?.node===applicationFactory).map(n=>({callEvidenceId:ev(main,n,'Application menu factory consumer complete call'),enclosingFactoryEvidenceId:ev(main,nearest(main,n,isFn),'Application menu install consumer closure'),arguments:n.arguments.map(a=>describe(main,a)),injectedValues:n.arguments[0]?.type==='ObjectExpression'?n.arguments[0].properties.filter(p=>p.type==='ObjectProperty').map(p=>({property:key(p),value:describe(main,p.value),binding:p.value.type==='Identifier'?bindingRecord(main,main.resolve(p.value,p.value.name)):null,...callable(main,p.value)?{callback:callbackContract(main,p.value)}:{}})):[],conditions:conditions(main,n),mode:'unknown'}));
// Only actual bound native registration expressions are counted. Generated
// menus and runtime arrays keep an unknown runtime item count.
const registrations=nativeMenuCalls.map((n,i)=>({index:i,api:parts(n.callee).members.join('.'),callEvidenceId:ev(main,n,'Complete bound native menu registration call'),callee:callee(main,n),arguments:n.arguments.map(a=>describe(main,a)),conditions:conditions(main,n),enclosingFactoryEvidenceId:nearest(main,n,isFn)?ev(main,nearest(main,n,isFn),'Complete native menu factory/callback scope'):null,ownerClass:main.owner.get(n)?.name||null,runtimeItemCount:'unknown',mode:'unknown',runtimeStatus:'unverified'}));
const menuFactories=new Map([[applicationFactory,'application-menu']]);
for(const call of nativeMenuCalls){if(parts(call.callee).members.at(-1)==='buildFromTemplate'){const f=nearest(main,call,isFn);if(f)menuFactories.set(f,f===applicationFactory?'application-menu':'native-menu-construction-scope');}}
// Attach helpers through binding identity, not shared minified names. Limit
// the helper closure to calls returning template-like schemas and a known
// trace menu item; arbitrary user-facing callback implementation is separate.
const schemaFields=n=>n?.type==='ObjectExpression'&&['click','role','submenu'].some(k=>props(n).has(k));
for(const root of [...menuFactories.keys()])for(const call of allCalls(root)){const f=callable(main,call.callee);if(f?.c===main){let templates=false;visit(f.node,x=>{if(schemaFields(x))templates=true;},true);if(templates&&f.node!==root)menuFactories.set(f.node,'bound-menu-template-helper');}}
// Dock/tray factories build from parameters/this methods; follow class method
// bindings to getNativeTrayMenuItems/refreshMenu and then bound schema helpers.
for(const root of [...menuFactories.keys()]){const own=main.owner.get(root);if(own){for(const method of own.methods.values()){let hasSchema=false;visit(method,x=>{if(schemaFields(x))hasSchema=true;},true);if(hasSchema)menuFactories.set(method,'bound-owning-class-menu-schema');}}}
for(const root of [...menuFactories.keys()])for(const call of allCalls(root)){const f=callable(main,call.callee);if(f?.c===main){let templates=false;visit(f.node,x=>{if(schemaFields(x))templates=true;});if(templates)menuFactories.set(f.node,'bound-menu-template-helper');}}
const nativeMenuItems=[],itemSeen=new Set();
const itemRowsByNode=new Map();
for(const [factory,scopeKind] of menuFactories){
 visit(factory,n=>{
  if(!schemaFields(n)||itemSeen.has(n))return;
  // Objects passed to map-generating helpers are generator parameters rather
  // than complete item constructions; record their distinct source denominator.
  itemSeen.add(n);const parent=main.parent.get(n),isGeneratorInput=parent?.type==='CallExpression'&&parent.arguments.includes(n)&&parent.callee?.type==='Identifier'&&callable(main,parent.callee)?.node!==factory;
  const item={index:nativeMenuItems.length,scopeKind,constructionKind:isGeneratorInput?'bound-template-generator-options':'item-schema-construction',completeItemEvidenceId:ev(main,n,'Complete native menu item/generator schema'),factoryEvidenceId:ev(main,factory,'Menu construction lexical scope'),conditions:conditions(main,n,factory),properties:[...props(n).keys()],values:{},spreadMetadataBindings:[],callback:null,mode:'unknown',runtimeStatus:'unverified'};
  for(const k of ['id','label','role','type','accelerator','acceleratorWorksWhenHidden','registerAccelerator','visible','enabled','submenu'])if(valueProp(n,k))item.values[k]=describe(main,valueProp(n,k));
  for(const sp of n.properties.filter(p=>p.type==='SpreadElement')){const p=sp.argument;const cal=p.type==='CallExpression'?callable(main,p.callee):null;const info={spreadEvidenceId:ev(main,sp,'Complete menu item metadata spread'),expression:main.raw(p).slice(0,800),calleeBinding:p.type==='CallExpression'?callee(main,p):null};
   if(cal?.c===main){const metadataCalls=allCalls(cal.node).filter(call=>moduleOf(main,main.resolve(call,parts(call.callee)?.root))==='./src-BJv5Mk7n.js');info.boundProducerDefinitionEvidenceId=ev(main,cal.node,'Bound menu metadata producer');info.metadataConsumerCalls=metadataCalls.map(call=>({evidenceId:ev(main,call,'Bound command metadata consumer call'),callee:callee(main,call)}));if(metadataCalls.some(call=>parts(call.callee)?.members.at(-1)==='Pt')){const id=lit(p.arguments[0]);info.commandId=id;if(id.kind==='literal'){info.commandMetadataEvidenceId=commandById.get(id.value)?.definitionEvidenceId||null;info.shortcutIndex=describe(main,p.arguments[1]);}}}
   item.spreadMetadataBindings.push(info);
  }
  const click=valueProp(n,'click');if(click)item.callback=callbackContract(main,click);
  nativeMenuItems.push(item);itemRowsByNode.set(n,item);
 });
}
// Registration dataflow follows lexical binding identities, template helper
// returns, map callbacks, array mutations and object submenu assignments. Both
// branches are retained, with the actual construction/insertion conditions.
const mutations=new Map();
function mutationFor(b,n){if(!b)return;const a=mutations.get(b)||[];a.push(n);mutations.set(b,a);}
for(const n of main.nodes){
 if(n.type==='CallExpression'){const p=parts(n.callee);if(p?.members.length===1&&['push','unshift','splice'].includes(p.members[0]))mutationFor(main.resolve(n,p.root),n);}
 if(n.type==='AssignmentExpression'&&parts(n.left)?.members.length){const p=parts(n.left);mutationFor(main.resolve(n,p.root),n);}
}
function reachRegistration(n,registration,env=new Map(),memberPath=[],chain=[],seen=new Set(),depth=0){
 if(!n)return;if(depth>40){registration.dynamicUnknowns.push({reason:'dataflow-depth-limit',evidenceId:ev(main,n,'Dataflow trace limit expression')});return;}
 const visitKey=n.start+':'+memberPath.join('.');if(seen.has(visitKey))return;const next=new Set(seen);next.add(visitKey);
 const step={evidenceId:ev(main,n,'Menu registration dataflow expression'),conditions:conditions(main,n)};
 const steps=[...chain,step];
 const recur=(x,members=[],e=env)=>reachRegistration(x,registration,e,members,steps,next,depth+1);
 if(n.type==='Identifier'){
  const b=main.resolve(n,n.name),value=env.get(b)||b?.value;
  if(value)recur(value,[...(b?.member||[]),...memberPath]);
  else registration.dynamicUnknowns.push({reason:'identifier value unavailable',binding:bindingRecord(main,b),evidenceId:step.evidenceId});
  for(const mutation of mutations.get(b)||[]){
   const mstep={evidenceId:ev(main,mutation,'Actual menu array/property mutation'),conditions:conditions(main,mutation)};
   if(mutation.type==='CallExpression')for(const a of mutation.arguments)reachRegistration(a,registration,env,[],[...steps,mstep],next,depth+1);
   else if(parts(mutation.left)?.members.at(-1)==='submenu')reachRegistration(mutation.right,registration,env,[],[...steps,mstep],next,depth+1);
  }return;
 }
 if(n.type==='ObjectExpression'){
  if(memberPath.length){recur(valueProp(n,memberPath[0]),memberPath.slice(1));return;}
  const row=itemRowsByNode.get(n);if(row){row.registrationUses??=[];row.registrationUses.push({registrationIndex:registration.index,dataflow:steps});registration.reachableItemSchemaIndices.push(row.index);}
  for(const p of n.properties){if(p.type==='SpreadElement')recur(p.argument);else if(key(p)==='submenu'||!schemaFields(n))recur(p.value||p);}
  return;
 }
 if(n.type==='ArrayExpression'){for(const el of n.elements)recur(el,memberPath);return;}
 if(n.type==='SpreadElement'){recur(n.argument,memberPath);return;}
 if(n.type==='ConditionalExpression'){recur(n.consequent,memberPath);recur(n.alternate,memberPath);return;}
 if(n.type==='LogicalExpression'){recur(n.left,memberPath);recur(n.right,memberPath);return;}
 if(n.type==='SequenceExpression'){recur(n.expressions.at(-1),memberPath);return;}
 if(n.type==='MemberExpression'||n.type==='OptionalMemberExpression'){
  const k=n.computed?constant(main,n.property).value:n.property.name;if(k!=null)recur(n.object,[k,...memberPath]);else registration.dynamicUnknowns.push({reason:'computed menu member',evidenceId:step.evidenceId});return;
 }
 if(n.type==='CallExpression'||n.type==='OptionalCallExpression'||n.type==='NewExpression'){
  const f=callable(main,n.callee);if(f?.c===main){
   const e=new Map(env);for(let i=0;i<(f.node.params||[]).length;i++)for(const v of names(f.node.params[i])){const b=main.resolve(f.node.params[i],v.name);if(b&&n.arguments[i])e.set(b,n.arguments[i]);}
   const producer={evidenceId:ev(main,f.node,'Bound menu dataflow producer definition'),conditions:conditions(main,n)};
   if(f.node.body?.type!=='BlockStatement')reachRegistration(f.node.body,registration,e,memberPath,[...steps,producer],next,depth+1);
   else visit(f.node.body,x=>{if(x.type==='ReturnStatement'&&x.argument)reachRegistration(x.argument,registration,e,memberPath,[...steps,producer],next,depth+1);},true);
  }else{
   const p=parts(n.callee);if(p?.members.at(-1)==='buildFromTemplate'||p?.members.at(-1)==='MenuItem'){for(const a of n.arguments)recur(a,memberPath);}
   else if(['map','flatMap','flat','filter','concat'].includes(p?.members.at(-1))){
    const callback=n.arguments.find(isFn);if(callback){const producer={evidenceId:ev(main,callback,'Generated menu collection callback'),conditions:conditions(main,n),runtimeInstanceCount:'unknown'};if(callback.body.type==='BlockStatement')visit(callback.body,x=>{if(x.type==='ReturnStatement')reachRegistration(x.argument,registration,env,memberPath,[...steps,producer],next,depth+1);},true);else reachRegistration(callback.body,registration,env,memberPath,[...steps,producer],next,depth+1);}
    if(n.callee.object)recur(n.callee.object,memberPath);if(p.members.at(-1)==='concat')for(const a of n.arguments)recur(a,memberPath);
   }else registration.dynamicUnknowns.push({reason:'dynamic/external template producer',callee:callee(main,n),evidenceId:step.evidenceId});
  }return;
 }
 if(!['StringLiteral','NumericLiteral','BooleanLiteral','NullLiteral','TemplateLiteral','UnaryExpression'].includes(n.type))registration.dynamicUnknowns.push({reason:'unhandled template value '+n.type,evidenceId:step.evidenceId});
}
for(let i=0;i<nativeMenuCalls.length;i++){
 const row=registrations[i];row.reachableItemSchemaIndices=[];row.dynamicUnknowns=[];
 for(const arg of nativeMenuCalls[i].arguments)reachRegistration(arg,row);
 row.reachableItemSchemaIndices=[...new Set(row.reachableItemSchemaIndices)];
}
for(const row of nativeMenuItems){row.registrationUses??=[];row.registrationReachability=row.registrationUses.length?'bound-source-dataflow':'construction-scope-only; registration-instance-unresolved';}
const globalRegisterCalls=main.nodes.filter(n=>n.type==='CallExpression'&&parts(n.callee)?.members.join('.')==='globalShortcut.register'&&moduleOf(main,main.resolve(n,parts(n.callee).root))==='electron');
if(globalRegisterCalls.length!==1)throw Error('Expected one actual globalShortcut.register call');
const globalRegisterFn=nearest(main,globalRegisterCalls[0],isFn),globalRegisterConsumers=main.nodes.filter(n=>n.type==='CallExpression'&&callable(main,n.callee)?.node===globalRegisterFn);
const globalWrappers=new Set(globalRegisterConsumers.map(n=>nearest(main,n,isFn)).filter(f=>f&&f!==globalRegisterFn));
const globalRegistrationWrappers=new Set([...globalWrappers].filter(f=>(f.params||[]).length>0));
const globalWrapperConsumerCalls=main.nodes.filter(n=>n.type==='CallExpression'&&globalRegistrationWrappers.has(callable(main,n.callee)?.node));
const globalReregistrationTriggers=main.nodes.filter(n=>n.type==='CallExpression'&&globalWrappers.has(callable(main,n.callee)?.node)&&!globalRegistrationWrappers.has(callable(main,n.callee)?.node));
const globalShortcuts={nativeRegistration:{callEvidenceId:ev(main,globalRegisterCalls[0],'Complete OS-global shortcut registration call'),wrapperEvidenceId:ev(main,globalRegisterFn,'Complete bound OS-global registration function'),callback:callbackContract(main,globalRegisterCalls[0].arguments[1])},directWrapperConsumers:globalRegisterConsumers.map(n=>({callEvidenceId:ev(main,n,'Bound global registration wrapper consumer'),callee:callee(main,n),conditions:conditions(main,n)})),wrappers:[...globalWrappers].map(f=>({name:f.id?.name||null,role:globalRegistrationWrappers.has(f)?'registration-wrapper':'resume-or-keyboard-layout-reregistration',definitionEvidenceId:ev(main,f,'Complete higher global shortcut wrapper'),consumerCount:globalWrapperConsumerCalls.filter(n=>callable(main,n.callee)?.node===f).length})),reregistrationTriggers:globalReregistrationTriggers.map(n=>({callEvidenceId:ev(main,n,'Global shortcut reregistration trigger'),callee:callee(main,n),conditions:conditions(main,n)})),registrations:globalWrapperConsumerCalls.map((n,index)=>({index,callEvidenceId:ev(main,n,'Complete higher global shortcut wrapper registration consumer'),callee:callee(main,n),hotkey:describe(main,n.arguments[0]),callbackOptions:n.arguments[1]?describe(main,n.arguments[1]):null,handlers:n.arguments[1]?.type==='ObjectExpression'?['onPressed','onReleased','onCancelled'].filter(k=>valueProp(n.arguments[1],k)).map(k=>({kind:k,handler:callbackContract(main,valueProp(n.arguments[1],k))})):[],ownership:describe(main,n.arguments[2]),conditions:conditions(main,n),ownerClass:main.owner.get(n)?.name||null,mode:'unknown',runtimeStatus:'unverified'}))};
// Event registration receiver is separately bound, since webContents is often
// injected and not the imported electron namespace itself.
const keyEventRegistrations=main.nodes.filter(n=>n.type==='CallExpression'&&parts(n.callee)?.members.at(-1)==='on'&&lit(n.arguments[0]).value==='before-input-event').map((n,index)=>({index,event:'before-input-event',callEvidenceId:ev(main,n,'Complete before-input-event registration'),callee:callee(main,n),handler:callbackContract(main,n.arguments[1]),conditions:conditions(main,n),ownerClass:main.owner.get(n)?.name||null,receiverStatus:'binding-recorded; runtime object identity unverified',mode:'unknown',runtimeStatus:'unverified'}));
const registryPolicyFunctions=['Ft','At','Pt','Mt','St'].map(x=>metadata.exports.get(x)?.binding?.callable).filter(Boolean).map(f=>({definitionEvidenceId:ev(metadata,f,'Complete command selection/access/keymap policy'),calls:allCalls(f).map(n=>({callEvidenceId:ev(metadata,n,'Command policy bound call'),callee:callee(metadata,n)}))}));
const rendererReviewInputs=[],rendererReviews=[];
function addReviewedNotes(name){
 const p=path.join(output,name);if(!fs.existsSync(p))return null;
 const buf=fs.readFileSync(p),j=JSON.parse(buf.toString('utf8'));if(j.baselineId!==baseline.baselineId)throw Error('Reviewed renderer baseline mismatch');
 const refs=new Map();for(const x of j.evidence||[]){
  const relative=x.sourcePath.replace(/^app\.asar\//,''),expected=manifest.archiveFiles.find(y=>y.archivePath===relative),original=fs.readFileSync(path.join(baseline.extractedDirectory,relative));
  const r=x.byteRange;if(!expected||sha(original)!==expected.sha256||x.sourceSha256!==expected.sha256||sha(original.subarray(r.start,r.end))!==x.spanSha256)throw Error('Renderer review span/hash mismatch '+x.id);
  const id='ENTRY-AST-E'+String(evidence.length+1).padStart(5,'0');refs.set(x.id,id);evidence.push({id,baselineId:baseline.baselineId,claim:x.label,sourcePath:'app.asar/'+relative,sourceHash:expected.sha256,locator:{kind:'byte-range',start:r.start,endExclusive:r.end},spanHash:x.spanSha256,method:'supplemental-babel-fragment-ast-and-static-review',confidence:'confirmed',verificationStatus:'original-byte-span-confirmed; lexical/semantic confidence preserved in renderer review'});
 }
 function remap(value){if(typeof value==='string')return refs.get(value)||value;if(Array.isArray(value))return value.map(remap);if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).filter(([k])=>!['evidence','snippet'].includes(k)).map(([k,v])=>[k,remap(v)]));return value;}
 const review=remap(j);rendererReviewInputs.push({name,sha256:sha(buf),evidenceRecords:refs.size});rendererReviews.push(review);return j;
}
const rendererNotes=addReviewedNotes('renderer-command-notes.json');
addReviewedNotes('renderer-command-bridge-helper.json');
const rendererHookContracts=[];
if(rendererNotes){
 const selected=(rendererNotes.registrationConsumers||[]).map(x=>({name:x.functionName,evidenceId:x.definitionEvidenceId}));
 const hostReceiver=(rendererNotes.functions||[]).find(x=>x.name==='Fsc');if(hostReceiver&&!selected.some(x=>x.name==='Fsc'))selected.push({name:'Fsc',evidenceId:hostReceiver.evidenceId});
 const byId=new Map(rendererNotes.evidence.map(x=>[x.id,x]));
 const grouped=new Map();for(const item of selected){const e=byId.get(item.evidenceId);if(!e)throw Error('Selected renderer hook evidence missing');const a=grouped.get(e.sourcePath)||[];a.push({...item,e});grouped.set(e.sourcePath,a);}
 for(const [relative,list] of grouped){
  const c=load(relative,list.map(x=>x.e.byteRange));
  for(const item of list){const f=c.nodes.find(n=>isFn(n)&&c.range(n).start===item.e.byteRange.start&&c.range(n).endExclusive===item.e.byteRange.end);if(!f)throw Error('Selected renderer function fragment exact AST mismatch');
   const calls=allCalls(f).filter(n=>['Pw','xs'].includes(parts(n.callee)?.root)).map(n=>({callEvidenceId:ev(c,n,'Complete selected renderer command/message registration call'),callee:callee(c,n),registryBindingStatus:'callee outside independent function fragment; candidate registry link is separately reviewed, original enclosing-source binding remains unknown',arguments:n.arguments.map(a=>describe(c,a)),conditions:conditions(c,n,f),handler:callbackContract(c,n.arguments[1]),mode:'unknown',runtimeStatus:'unverified'}));
   rendererHookContracts.push({name:item.name,definitionEvidenceId:ev(c,f,'Complete selected renderer hook AST scope'),scopeStatus:'complete function; original enclosing program/import bindings outside fragment are unknown',calls,localCallBindings:allCalls(f).filter(n=>!['Pw','xs'].includes(parts(n.callee)?.root)).map(n=>({callEvidenceId:ev(c,n,'Call in selected renderer hook scope'),callee:callee(c,n)}))});
  }
 }
}
const summary={baselineId:baseline.baselineId,sourceFiles:sources.map(c=>({sourcePath:'app.asar/'+c.relative,sha256:c.hash,sourceBytes:c.buf.length,astNodes:c.nodes.length,scope:c.fragmentRanges?'independent-selected-function-fragments':'complete-source',parsedSourceBytes:c.fragmentRanges?c.fragmentRanges.reduce((sum,r)=>sum+r.end-r.start,0):c.buf.length,fragmentRanges:c.fragmentRanges||null,archiveByteOffset:c.archiveByteOffset,parserErrors:0})),parser:{name:'@babel/parser',version:JSON.parse(fs.readFileSync(path.join(path.dirname(require.resolve(parserPath)),'../package.json'),'utf8')).version,implementationSha256:sha(fs.readFileSync(require.resolve(parserPath)))},applicationMenuFactories:1,applicationFactoryConsumers:applicationConsumers.length,nativeMenuApiCalls:registrations.length,nativeBuildFromTemplateCalls:nativeMenuCalls.filter(n=>parts(n.callee).members.at(-1)==='buildFromTemplate').length,nativeMenuItemConstructorCalls:nativeMenuCalls.filter(n=>parts(n.callee).members.at(-1)==='MenuItem').length,menuConstructionLexicalScopes:menuFactories.size,nativeItemSchemaConstructionSites:nativeMenuItems.filter(x=>x.constructionKind==='item-schema-construction').length,nativeTemplateGeneratorOptionSites:nativeMenuItems.filter(x=>x.constructionKind!=='item-schema-construction').length,metadataCommandSchemaSites:new Set(commands.map(x=>x.definitionEvidenceId)).size,metadataCommandInstances:commands.length,finiteMetadataMaps:registrySources.filter(x=>x.finiteMapEvidenceId).map(x=>({sourceEvidenceId:x.finiteMapEvidenceId,instanceCount:x.instanceCount})),distinctMetadataCommandIds:new Set(commands.map(x=>x.id)).size,commandKinds:commands.reduce((o,x)=>(o[x.kind]=(o[x.kind]||0)+1,o),{}),osGlobalNativeRegistrationCalls:globalRegisterCalls.length,osGlobalDirectWrapperConsumers:globalRegisterConsumers.length,osGlobalHigherWrapperConsumerCalls:globalWrapperConsumerCalls.length,osGlobalReregistrationTriggerCalls:globalReregistrationTriggers.length,beforeInputEventRegistrations:keyEventRegistrations.length,rendererReviewInputs,rendererSelectedHookScopes:rendererHookContracts.length,rendererSelectedCommandRegistrations:rendererHookContracts.reduce((n,x)=>n+x.calls.filter(c=>c.callee.receiver?.root==='Pw').length,0),rendererSelectedMessageSubscriptions:rendererHookContracts.reduce((n,x)=>n+x.calls.filter(c=>c.callee.receiver?.root==='xs').length,0),rendererWholeSourceRegistrationCoverage:'unknown',modeClassifiedEntries:0,runtimeVerifiedEntries:0,evidenceRecords:evidence.length,denominatorDefinitions:{metadataCommandSchemaSites:'Distinct command object source spans reachable from the bound exported metadata registry initializer, including finite-map callback schema spans; metadata is not a handler registration.',metadataCommandInstances:'Statically resolved metadata instances: fixed ID schemas plus finite literal array/map/template expansions, preserving shared source spans; not runtime registrations.',nativeMenuApiCalls:'AST native Menu API and MenuItem expressions with electron require binding in complete frozen main; a call may construct/install/mutate a menu and is not a runtime item count.',nativeItemSchemaConstructionSites:'Distinct literal interactive/container item schema object expressions with click, role or submenu properties in bound native menu construction scopes and schema-producing helpers; generated map instances and platform/feature filters are not expanded.',nativeTemplateGeneratorOptionSites:'Distinct object inputs passed to bound template-generating local helpers, separate from their output schema objects.',osGlobalHigherWrapperConsumerCalls:'Calls to lexical wrappers which themselves call the one native globalShortcut.register wrapper; runtime loops/keymap values remain dynamic.',beforeInputEventRegistrations:'Complete main AST .on(before-input-event, handler) calls, not unique shortcuts or all renderer key handlers.'},limitations:['Renderer review supplements preserve their complete-program fragment proof versus original full-source binding unknowns; selected hook registrations are a separate partial denominator.', 'No target code was executed and no UI/account/history/model was accessed.','Conditional source branches are recorded; feature values, entitlement, platform-specific runtime registration and final item counts remain unknown.','Schemas sharing command IDs are linked only through the bound metadata producer/registry, not by unrelated string matches.','Some native context menus accept dynamic renderer/native payloads and their item instances cannot be enumerated statically.','Bound callbacks are traced at most five local-call edges; injected receivers, dynamically installed/inherited methods, Promise continuations and external modules remain explicit unknowns.','Metadata includes multiple command kinds and products; neither chat names nor requiredAccess values justify deleting functionality.','Separator-only schemas are present in registration arguments and dataflow evidence but are excluded from the interactive/container schema denominator.', 'All native API call expressions with an electron namespace binding in main are inventoried, but schema helper traversal is a bounded source denominator, not proof of complete application feature coverage.']};
const result={baselineId:baseline.baselineId,applicationMenu:{factoryEvidenceId:ev(main,applicationFactory,'Complete application menu factory'),buildEvidenceId:ev(main,applicationBuild[0],'Complete application menu construction'),installEvidenceId:ev(main,applicationInstall[0],'Complete application menu installation'),consumers:applicationConsumers},metadataRegistry:{registryEvidenceId:registryEvidence,exportEvidenceId:ev(metadata,registryExport.node,'Bound command registry export getter'),sources:registrySources,exports:linkedMetadataExports,policies:registryPolicyFunctions,commands},nativeMenuRegistrations:registrations,nativeMenuItems,globalShortcuts,keyEventRegistrations,rendererReviews,rendererHookContracts,summary};
const evidenceById=new Map(evidence.map(e=>[e.id,e])),contractRecordIndex=[];
function stamp(record,evidenceKey,kind,pointer,instance=''){
 const e=evidenceById.get(record[evidenceKey]);if(!e)throw Error('Contract stable ID evidence missing: '+pointer);
 const coordinates={baselineId:baseline.baselineId,kind,sourcePath:e.sourcePath,sourceHash:e.sourceHash,start:e.locator.start,endExclusive:e.locator.endExclusive,instance};
 const contractId=kind+':'+sha(JSON.stringify(coordinates)).slice(0,24);record.contractId=contractId;
 contractRecordIndex.push({contractId,kind,jsonPointer:pointer,primaryEvidenceKey:evidenceKey,primaryEvidenceId:e.id,coordinates});
}
stamp(result.applicationMenu,'factoryEvidenceId','application-menu-factory','/applicationMenu');
applicationConsumers.forEach((x,i)=>stamp(x,'callEvidenceId','application-menu-consumer','/applicationMenu/consumers/'+i));
commands.forEach((x,i)=>stamp(x,'definitionEvidenceId','command-metadata-instance','/metadataRegistry/commands/'+i,x.id));
registrations.forEach((x,i)=>stamp(x,'callEvidenceId','native-menu-api','/nativeMenuRegistrations/'+i));
nativeMenuItems.forEach((x,i)=>stamp(x,'completeItemEvidenceId',x.constructionKind==='item-schema-construction'?'native-menu-schema':'native-menu-generator-options','/nativeMenuItems/'+i));
stamp(globalShortcuts.nativeRegistration,'callEvidenceId','os-global-native-registration','/globalShortcuts/nativeRegistration');
globalShortcuts.registrations.forEach((x,i)=>stamp(x,'callEvidenceId','os-global-wrapper-consumer','/globalShortcuts/registrations/'+i));
keyEventRegistrations.forEach((x,i)=>stamp(x,'callEvidenceId','before-input-event-registration','/keyEventRegistrations/'+i));
rendererHookContracts.forEach((x,i)=>{stamp(x,'definitionEvidenceId','renderer-hook-scope','/rendererHookContracts/'+i);x.calls.forEach((y,j)=>stamp(y,'callEvidenceId',y.callee.receiver?.root==='Pw'?'renderer-command-registration-candidate':'renderer-message-subscription-candidate','/rendererHookContracts/'+i+'/calls/'+j));});
if(new Set(contractRecordIndex.map(x=>x.contractId)).size!==contractRecordIndex.length)throw Error('Duplicate stable contract IDs');
result.contractRecordIndex=contractRecordIndex;
summary.contractRecords=contractRecordIndex.length;
summary.stableIdBasis='contractId: contract kind plus first 24 hex SHA256 of baselineId, kind, original sourcePath/sourceHash, complete primary byte span and explicit finite-map instance ID. Stable within this frozen baseline and parser/review inputs; not a cross-version feature ID.';
summary.evidenceReferenceConvention='Every ...EvidenceId and ...EvidenceIds value resolves to menu-command-evidence.jsonl.id; nested argument/binding/dataflow/condition/callback/calleeTrace/review evidence is retained. contractRecordIndex gives primaryEvidenceKey and JSON pointer for each stamped record.';
// Build final counts after all root evidence records were added.
summary.evidenceRecords=evidence.length;
fs.mkdirSync(output,{recursive:true});
fs.writeFileSync(path.join(output,'menu-command-contracts.json'),JSON.stringify(result,null,2)+'\n');
fs.writeFileSync(path.join(output,'menu-command-evidence.jsonl'),evidence.map(x=>JSON.stringify(x)).join('\n')+'\n');
fs.writeFileSync(path.join(output,'menu-command-summary.json'),JSON.stringify(summary,null,2)+'\n');
fs.writeFileSync(path.join(output,'menu-command-summary.md'),`# Menu, command and shortcut AST contracts\n\nFrozen baseline: ${baseline.baselineId}. All mode/runtime conclusions remain unknown.\n\n- Application menu factories: 1; bound consumers: ${applicationConsumers.length}.\n- Native Menu API expressions: ${registrations.length}; item schema sites: ${summary.nativeItemSchemaConstructionSites}; separate generator option sites: ${summary.nativeTemplateGeneratorOptionSites}.\n- Exported metadata schema source sites: ${summary.metadataCommandSchemaSites}; finite expansion instances: ${commands.length}; distinct IDs: ${summary.distinctMetadataCommandIds}. These are metadata, not handler registrations.\n- Native OS-global register calls: 1; direct wrapper consumers: ${globalRegisterConsumers.length}; higher wrapper consumers: ${globalWrapperConsumerCalls.length}.\n- before-input-event registrations in main: ${keyEventRegistrations.length}.\n- Selected renderer hook AST scopes: ${rendererHookContracts.length}; original full-program bindings outside fragments remain unknown.
- Evidence records: ${evidence.length}; complete original UTF-8 byte spans and SHA-256.\n\n${summary.limitations.map(x=>'- '+x).join('\n')}\n`);
process.stdout.write(JSON.stringify(summary,null,2)+'\n');
