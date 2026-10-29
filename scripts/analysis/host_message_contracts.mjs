#!/usr/bin/env node
// Parse the frozen release as data. No module from the target is imported/evaluated.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const flags = new Map();
for (let i=2; i<process.argv.length; i+=2) {
  if (!process.argv[i].startsWith('--') || process.argv[i+1] === undefined) throw new Error('Expected --name value arguments');
  flags.set(process.argv[i].slice(2),process.argv[i+1]);
}
const baselinePath = path.resolve(flags.get('baseline') || '.analysis-local/current-baseline.json');
const output = path.resolve(flags.get('output') || '.analysis-local/feature-work');
const parserPath = path.resolve(flags.get('parser-path') || '/private/tmp/ccodex-rea-tooling/install/node_modules/@babel/parser');
const sourceRelative = flags.get('source') || '.vite/build/main-CqEoQDOU.js';
const baseline = JSON.parse(fs.readFileSync(baselinePath,'utf8'));
const fileIndex = JSON.parse(fs.readFileSync(path.join('analysis',baseline.baselineId,'files.json'),'utf8'));
const expectedFile = fileIndex.archiveFiles.find(entry=>entry.archivePath===sourceRelative);
if (!expectedFile?.sha256) throw new Error('Source missing from frozen file manifest');
const sourcePath = path.join(baseline.extractedDirectory,sourceRelative);
const sourceBuffer = fs.readFileSync(sourcePath);
const sha = value=>crypto.createHash('sha256').update(value).digest('hex');
const sourceHash = sha(sourceBuffer);
if(sourceHash!==expectedFile.sha256) throw new Error('Frozen input hash changed');
const source = sourceBuffer.toString('utf8');
if(!Buffer.from(source,'utf8').equals(sourceBuffer)) throw new Error('Source is not lossless UTF-8');
const parser = require(parserPath);
const parserPackagePath=path.join(path.dirname(require.resolve(parserPath)), '..', 'package.json');
const parserPackage = JSON.parse(fs.readFileSync(parserPackagePath,'utf8'));
const ast = parser.parse(source,{sourceType:'unambiguous',errorRecovery:false,attachComment:false,plugins:['jsx'],allowReturnOutsideFunction:false});
if(ast.errors?.length) throw new Error('Parser returned errors');

// Babel offsets count UTF-16 code units. Evidence offsets count original UTF-8 bytes.
const byteOffsets = new Uint32Array(source.length+1);
let bytes=0;
for(let i=0;i<source.length;i++){
  byteOffsets[i]=bytes;
  const point=source.codePointAt(i);
  if(point>0xffff){byteOffsets[i+1]=bytes;bytes+=4;i++;}
  else bytes+=point<0x80?1:point<0x800?2:3;
}
byteOffsets[source.length]=bytes;
if(bytes!==sourceBuffer.length) throw new Error('UTF-8 mapping length mismatch');
const range=node=>({kind:'byte-range',start:byteOffsets[node.start],endExclusive:byteOffsets[node.end]});
const raw=node=>source.slice(node.start,node.end);
const children=node=>Object.entries(node).filter(([key])=>!['loc','comments','leadingComments','trailingComments','innerComments','tokens','errors','extra'].includes(key)).flatMap(([,value])=>Array.isArray(value)?value.filter(x=>x&&typeof x.type==='string'):value&&typeof value.type==='string'?[value]:[]);
const isFunction=node=>['FunctionDeclaration','FunctionExpression','ArrowFunctionExpression','ClassMethod','ClassPrivateMethod','ObjectMethod'].includes(node.type);
const literal=node=>{
  if(!node)return {kind:'default',value:null};
  if(node.type==='StringLiteral'||node.type==='NumericLiteral'||node.type==='BooleanLiteral')return {kind:'literal',value:node.value};
  if(node.type==='NullLiteral')return {kind:'literal',value:null};
  if(node.type==='TemplateLiteral'&&node.expressions.length===0)return {kind:'literal',value:node.quasis.map(x=>x.value.cooked??x.value.raw).join('')};
  return {kind:'computed',value:null,expression:raw(node)};
};
const nodeScopes=new WeakMap(),parents=new WeakMap(),classOwner=new WeakMap();
const rootScope={kind:'program',parent:null,bindings:new Map()};
const addBinding=(scope,name,node,kind,extra={})=>{
  const values=scope.bindings.get(name)||[];
  values.push({name,node,kind,...extra});scope.bindings.set(name,values);
};
const patternNames=node=>{
  if(!node)return [];
  if(node.type==='Identifier')return [node.name];
  if(node.type==='RestElement')return patternNames(node.argument);
  if(node.type==='AssignmentPattern')return patternNames(node.left);
  if(node.type==='ArrayPattern')return node.elements.flatMap(patternNames);
  if(node.type==='ObjectPattern')return node.properties.flatMap(p=>patternNames(p.type==='RestElement'?p.argument:p.value));
  return [];
};
const importValue=init=>{
  if(init?.type==='CallExpression'&&init.callee?.type==='Identifier'&&init.callee.name==='require'){
    const target=literal(init.arguments[0]);return target.kind==='literal'?target.value:null;
  }
  return null;
};
const classInfo=new WeakMap();
function buildScopes(node,parentScope=rootScope,parent=null,owner=null){
  if(parent)parents.set(node,parent);
  let scope=parentScope;
  if(node.type==='FunctionDeclaration'&&node.id)addBinding(parentScope,node.id.name,node,'function-declaration');
  if(node.type==='ClassDeclaration'&&node.id)addBinding(parentScope,node.id.name,node,'class-declaration');
  if(node.type==='ClassExpression'||node.type==='ClassDeclaration'){
    const declaration=parent?.type==='VariableDeclarator'?parent.id?.name:node.id?.name;
    owner={node,name:declaration||'<anonymous-class>',methods:new Map(),fields:new Map()};
    for(const member of node.body.body){
      const key=member.key?.type==='Identifier'&&!member.computed?member.key.name:literal(member.key).value;
      if(!key)continue;
      if(member.type==='ClassMethod'||member.type==='ClassPrivateMethod')owner.methods.set(key,member);
      else owner.fields.set(key,{node:member,initializer:member.value||null});
    }
    classInfo.set(node,owner);
  }
  if(isFunction(node)){
    scope={kind:'function',parent:parentScope,bindings:new Map(),node};
    if(node.type==='FunctionExpression'&&node.id)addBinding(scope,node.id.name,node,'named-function-expression');
    for(const param of node.params||[])for(const name of patternNames(param))addBinding(scope,name,param,'parameter');
  }else if(node.type==='BlockStatement'||node.type==='CatchClause'){
    scope={kind:'block',parent:parentScope,bindings:new Map(),node};
    if(node.type==='CatchClause')for(const name of patternNames(node.param))addBinding(scope,name,node.param,'catch-parameter');
  }
  nodeScopes.set(node,scope);if(owner)classOwner.set(node,owner);
  if(node.type==='VariableDeclarator'){
    const declarationKind=parent?.kind||'unknown';let bindingScope=scope;
    if(declarationKind==='var')while(bindingScope.parent&&bindingScope.kind!=='function'&&bindingScope.kind!=='program')bindingScope=bindingScope.parent;
    for(const name of patternNames(node.id))addBinding(bindingScope,name,node,declarationKind+'-declaration',{initializer:node.init,requireSpecifier:importValue(node.init)});
  }
  if(node.type==='ImportDeclaration')for(const spec of node.specifiers)addBinding(scope,spec.local.name,spec,'import',{importSpecifier:node.source.value,importedName:spec.imported?.name||spec.imported?.value||spec.type});
  // Constructor-injected receiver roots are a binding of the object, not proof of
  // its runtime method implementation. Preserve that distinction below.
  if(node.type==='AssignmentExpression'&&owner&&node.left?.type==='MemberExpression'&&node.left.object.type==='ThisExpression'&&!node.left.computed&&node.left.property.type==='Identifier'){
    const key=node.left.property.name;
    const values=owner.fields.get(key)?.assignments||[];values.push(node);
    owner.fields.set(key,{node:owner.fields.get(key)?.node||node,initializer:owner.fields.get(key)?.initializer||null,assignments:values});
  }
  for(const child of children(node))buildScopes(child,scope,node,owner);
}
buildScopes(ast.program);
const resolve=(node,name)=>{
  let scope=nodeScopes.get(node);
  while(scope){const bindings=scope.bindings.get(name);if(bindings)return bindings;scope=scope.parent;}
  return [];
};
const memberParts=node=>{
  if(node.type==='SequenceExpression')return memberParts(node.expressions.at(-1));
  if(node.type==='Identifier')return {root:{kind:'identifier',name:node.name},properties:[],computed:false};
  if(node.type==='ThisExpression')return {root:{kind:'this'},properties:[],computed:false};
  if(node.type==='MemberExpression'||node.type==='OptionalMemberExpression'){
    const root=memberParts(node.object);if(!root)return null;
    const property=!node.computed&&node.property.type==='Identifier'?node.property.name:literal(node.property).kind==='literal'?literal(node.property).value:null;
    return {...root,properties:[...root.properties,property],computed:root.computed||property===null};
  }
  return null;
};
function calleeBinding(call,owner){
  const expression=raw(call.callee),parts=memberParts(call.callee);
  if(!parts)return {expression,status:'dynamic-expression',unresolvedReason:'callee is not a fixed member/identifier chain'};
  if(parts.computed)return {expression,status:'dynamic-computed-property',root:parts.root,properties:parts.properties,unresolvedReason:'computed property requires runtime value'};
  if(parts.root.kind==='this'){
    const first=parts.properties[0];
    if(parts.properties.length===1&&owner.methods.has(first))return {expression,status:'bound-local-class-method',ownerClass:owner.name,method:first,definitionRange:range(owner.methods.get(first))};
    const field=owner.fields.get(first);
    if(field)return {expression,status:'bound-receiver-method-unresolved',ownerClass:owner.name,receiver:first,properties:parts.properties.slice(1),receiverDefinitionRange:range(field.node),receiverAssignmentRanges:(field.assignments||[]).map(range),unresolvedReason:'receiver is bound but implementation of its member was not resolved'};
    return {expression,status:'unresolved-this-member',ownerClass:owner.name,properties:parts.properties,unresolvedReason:'class member may be inherited or installed dynamically'};
  }
  const bindings=resolve(call,parts.root.name);
  if(!bindings.length){
    const knownGlobals=new Set(['Object','Array','String','Number','Boolean','Math','Date','JSON','Promise','Set','Map','WeakMap','WeakSet','Symbol','Error','TypeError','Buffer','URL','URLSearchParams','setTimeout','clearTimeout','setInterval','clearInterval','queueMicrotask','console','process','structuredClone']);
    return {expression,status:knownGlobals.has(parts.root.name)?'global-runtime-binding':'unresolved-identifier',root:parts.root,properties:parts.properties,unresolvedReason:knownGlobals.has(parts.root.name)?'global implementation is an external runtime dependency':'binding not found in lexical scopes'};
  }
  const binding=bindings.at(-1);
  const definition=range(binding.node);
  if(binding.requireSpecifier||binding.importSpecifier)return {expression,status:'bound-external-module-member',root:parts.root,properties:parts.properties,moduleSpecifier:binding.requireSpecifier||binding.importSpecifier,importedName:binding.importedName||null,definitionRange:definition,unresolvedReason:'module boundary is bound; exported method contract requires cross-module trace'};
  const callable=binding.kind==='function-declaration'||['ArrowFunctionExpression','FunctionExpression','ClassExpression'].includes(binding.initializer?.type);
  return {expression,status:callable&&!parts.properties.length?'bound-local-callable':'bound-lexical-value-member-unresolved',root:parts.root,properties:parts.properties,bindingKind:binding.kind,definitionRange:definition,multipleDefinitions:bindings.length>1,unresolvedReason:callable&&!parts.properties.length?null:'a lexical binding exists but callable/member implementation is not resolved'};
}

const targets=[];
function findTargets(node,method=null){
  const current=(node.type==='ClassMethod'||node.type==='ClassPrivateMethod')&&node.key?.name==='handleMessage'?node:method;
  if(node.type==='SwitchStatement'&&current&&raw(node.discriminant)==='t.type')targets.push({method:current,switch:node,owner:classOwner.get(current)});
  for(const child of children(node))findTargets(child,current);
}
findTargets(ast.program);
targets.sort((a,b)=>b.switch.cases.length-a.switch.cases.length);
if(!targets.length||targets[0].switch.cases.length<100)throw new Error('Did not locate central t.type dispatcher');
if(targets[1]?.switch.cases.length===targets[0].switch.cases.length)throw new Error('Ambiguous central dispatcher');
const target=targets[0];
const evidence=[],keys=new Map();
function ev(node,claim){
  const r=range(node),key=[r.start,r.endExclusive,claim].join(':');
  if(keys.has(key))return keys.get(key);
  const original=sourceBuffer.subarray(r.start,r.endExclusive);
  if(!original.equals(Buffer.from(raw(node),'utf8')))throw new Error('Evidence byte span does not match AST source');
  const id='HOST-AST-E'+String(evidence.length+1).padStart(5,'0');keys.set(key,id);
  evidence.push({id,baselineId:baseline.baselineId,claim,sourcePath:'app.asar/'+sourceRelative,sourceHash,locator:r,spanHash:sha(original),method:'supplemental-babel-ast',confidence:'confirmed',verificationStatus:'static-confirmed; runtime-unverified'});
  return id;
}
const switchEvidence=ev(target.switch,'Central main-message dispatcher switch(t.type) complete AST range');
const methodEvidence=ev(target.method,'Owner async handleMessage(e,t) complete AST range');
const unwrappedTail=statement=>statement?.type==='BlockStatement'?unwrappedTail(statement.body.at(-1)):statement;
function tailExit(statement){
  const tail=unwrappedTail(statement);
  if(!tail)return 'none';
  if(tail.type==='BreakStatement')return tail.label?'break-labeled':'break-unlabeled';
  if(tail.type==='ReturnStatement')return 'return';
  if(tail.type==='ThrowStatement')return 'throw';
  if(tail.type==='IfStatement'&&tail.alternate){const a=tailExit(tail.consequent),b=tailExit(tail.alternate);if(a!=='none'&&b!=='none')return 'both-if-branches-exit';}
  return 'none';
}
const meaningful=statement=>statement.type==='EmptyStatement'||statement.type==='BreakStatement'?false:statement.type==='BlockStatement'?statement.body.some(meaningful):true;
function walkClause(node,fn,nestedDepth=0){
  fn(node,nestedDepth);
  for(const child of children(node))walkClause(child,fn,nestedDepth+(isFunction(child)?1:0));
}
const cases=target.switch.cases.map((clause,index)=>{
  const label=literal(clause.test),calls=[],controls=[],unknowns=[];
  for(const statement of clause.consequent)walkClause(statement,(node,nestedDepth)=>{
    if(node.type==='CallExpression'||node.type==='OptionalCallExpression'||node.type==='NewExpression'){
      const binding=calleeBinding(node,target.owner);
      const entry={nodeType:node.type,...binding,range:range(node),withinNestedCallback:nestedDepth>0,optional:node.optional===true,evidenceId:ev(node,'Callsite in central dispatcher case '+String(label.value??label.expression??'default')+': '+binding.expression)};
      calls.push(entry);
      if(['dynamic-expression','dynamic-computed-property','unresolved-this-member','unresolved-identifier'].includes(binding.status))unknowns.push(entry.evidenceId);
    }
    if(nestedDepth===0&&['ReturnStatement','BreakStatement','ThrowStatement','ContinueStatement'].includes(node.type))controls.push({kind:node.type,label:node.label?.name||null,range:range(node)});
  });
  const empty=clause.consequent.length===0;
  const noop=!empty&&!clause.consequent.some(meaningful);
  const lastExit=tailExit(clause.consequent.at(-1));
  return {index,label,clauseRange:range(clause),clauseEvidenceId:ev(clause,'Complete AST case clause '+String(label.value??label.expression??'default')),
    statementTypes:clause.consequent.map(x=>x.type),ownConsequentRange:empty?null:{kind:'byte-range',start:byteOffsets[clause.consequent[0].start],endExclusive:byteOffsets[clause.consequent.at(-1).end]},
    emptyOwnHandler:empty,noOpOwnHandler:noop,topLevelTailExit:lastExit,fallthrough:empty||lastExit==='none',controlStatements:controls,calls,dynamicUnknownCallEvidenceIds:unknowns,
    mode:'unknown',modeConfidence:'unresolved',runtimeStatus:'not-verified',groupIndex:null,effectiveHandlerCaseIndex:null};
});
const groups=[];let pending=[];
for(const item of cases){
  pending.push(item);
  if(item.emptyOwnHandler&&item.index!==cases.length-1)continue;
  const groupIndex=groups.length,effective=item.emptyOwnHandler?null:item.index;
  const node={start:target.switch.cases[pending[0].index].start,end:target.switch.cases[item.index].end};
  const group={index:groupIndex,caseIndices:pending.map(x=>x.index),labels:pending.map(x=>x.label),hasSharedEmptyLabelFallthrough:pending.length>1,
    handlerCaseIndex:effective,handlerRange:item.ownConsequentRange,handlerEvidenceId:effective===null?null:ev({start:target.switch.cases[item.index].consequent[0].start,end:target.switch.cases[item.index].consequent.at(-1).end},'Complete effective handler for labels '+pending.map(x=>String(x.label.value??'default')).join(', ')),
    fullGroupRange:range(node),fullGroupEvidenceId:ev(node,'Complete consecutive-label handler group '+groupIndex),noOp:item.noOpOwnHandler||effective===null,fallsThroughAfterHandler:item.fallthrough};
  for(const member of pending){member.groupIndex=groupIndex;member.effectiveHandlerCaseIndex=effective;member.effectiveHandlerEvidenceId=group.handlerEvidenceId;member.sharedHandlerLabels=group.labels;member.effectiveHandlerNoOp=group.noOp;}
  groups.push(group);pending=[];
}
for(const item of cases){
  item.nextCaseIndex=item.fallthrough&&item.index+1<cases.length?item.index+1:null;
  // A nested unlabeled break may belong to a nested loop/switch. Keep full ranges
  // rather than asserting that every recorded break exits the outer dispatcher.
  item.controlFlowLimitations=['controlStatements exclude callback bodies; nested break ownership and all-path termination require CFG analysis'];
}
const previousPath=path.join(output,'host-message-types.json');
const previous=fs.existsSync(previousPath)?JSON.parse(fs.readFileSync(previousPath,'utf8')):[];
const oldLabels=new Set(previous.map(x=>x.type));
const labels=new Set(cases.filter(x=>x.label.kind==='literal').map(x=>x.label.value));
const nestedDispatches=[];
function findNestedDispatches(node){
  if(node.type==='SwitchStatement'&&node!==target.switch){
    let ancestor=parents.get(node);while(ancestor&&!(ancestor.type==='SwitchCase'&&parents.get(ancestor)===target.switch))ancestor=parents.get(ancestor);
    nestedDispatches.push({discriminant:raw(node.discriminant),outerCaseIndex:ancestor?target.switch.cases.indexOf(ancestor):null,range:range(node),
      labels:node.cases.map(item=>literal(item.test)),caseCount:node.cases.length,evidenceId:ev(node,'Nested sub-dispatch switch '+raw(node.discriminant)+'; not an outer t.type case')});
  }
  for(const child of children(node))findNestedDispatches(child);
}
findNestedDispatches(target.switch);
const counts=values=>values.reduce((out,value)=>(out[value]=(out[value]||0)+1,out),{});
const allCalls=cases.flatMap(x=>x.calls);
const summary={baselineId:baseline.baselineId,sourcePath:'app.asar/'+sourceRelative,sourceHash,sourceBytes:sourceBuffer.length,
  parser:{name:parserPackage.name,version:parserPackage.version,path:parserPath,packageSha256:sha(fs.readFileSync(parserPackagePath)),implementationSha256:sha(fs.readFileSync(require.resolve(parserPath))),errors:0},
  inspectedHandleMessageTypeSwitches:targets.length,selectedOwnerClass:target.owner.name,selectedMethodRange:range(target.method),selectedSwitchRange:range(target.switch),
  clauses:cases.length,literalLabels:cases.filter(x=>x.label.kind==='literal').length,distinctLiteralLabels:labels.size,computedLabels:cases.filter(x=>x.label.kind==='computed').length,defaultClauses:cases.filter(x=>x.label.kind==='default').length,
  completeClausesInventoried:cases.length,handlerGroups:groups.length,sharedEmptyLabelGroups:groups.filter(x=>x.hasSharedEmptyLabelFallthrough).length,
  ownEmptyClauses:cases.filter(x=>x.emptyOwnHandler).length,ownNoOpClauses:cases.filter(x=>x.noOpOwnHandler).length,effectiveNoOpLabelCount:cases.filter(x=>x.effectiveHandlerNoOp).length,
  nonemptyPotentialFallthroughClauses:cases.filter(x=>!x.emptyOwnHandler&&x.fallthrough).map(x=>x.index),tailExitCounts:counts(cases.map(x=>x.topLevelTailExit)),
  callsites:allCalls.length,callBindingCounts:counts(allCalls.map(x=>x.status)),callbackCallsites:allCalls.filter(x=>x.withinNestedCallback).length,
  priorLexicalCandidateLabels:oldLabels.size,lexicalOnlyLabels:[...oldLabels].filter(x=>!labels.has(x)),astOnlyLabels:[...labels].filter(x=>!oldLabels.has(x)),
  nestedSubDispatchSwitches:nestedDispatches.length,nestedSubDispatchCases:nestedDispatches.reduce((total,item)=>total+item.caseCount,0),
  modeClassifiedClauses:0,runtimeVerifiedClauses:0,evidenceRecords:evidence.length,allEvidenceByteSpansVerified:true,
  limitations:['Inventory covers the complete selected main switch, not all Electron/RPC/worker/native handlers.', 'Caller payload schemas, response envelopes, timeouts and per-feature domain semantics are not inferred from label names.', 'Bound receiver, imported namespace and lexical value are distinct from a fully resolved runtime callee.', 'Callback calls are recorded separately; callsite presence does not prove unconditional execution.', 'All labels keep mode unknown and runtime unverified; neither lexical nor AST enumeration proves functionality coverage.']};
fs.mkdirSync(output,{recursive:true});
fs.writeFileSync(path.join(output,'host-message-contracts.json'),JSON.stringify({baselineId:baseline.baselineId,sourcePath:'app.asar/'+sourceRelative,sourceHash,methodEvidenceId:methodEvidence,switchEvidenceId:switchEvidence,ownerClass:target.owner.name,cases,groups,nestedDispatches,summary},null,2)+'\n');
fs.writeFileSync(path.join(output,'host-message-contract-evidence.jsonl'),evidence.map(x=>JSON.stringify(x)).join('\n')+'\n');
fs.writeFileSync(path.join(output,'host-message-contract-summary.json'),JSON.stringify(summary,null,2)+'\n');
process.stdout.write(JSON.stringify(summary,null,2)+'\n');
