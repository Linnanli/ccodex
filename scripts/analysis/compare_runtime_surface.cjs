'use strict';
// Compare saved source contracts with fixed public descriptions, without executing target code.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const root = path.resolve(__dirname, '../..');
const work = path.join(root, '.analysis-local/runtime-surface-disposition-work');
const input = path.join(work, 'attempt-02');
const out = path.join(root, 'analysis/codex-26.1007.30912-c5b273322a83');
const parserPath = path.join(root, '.analysis-local/settings-entry-callers-work/tooling/node_modules/@babel/parser/lib/index.js');
const parser = require(parserPath);
const hash = data => crypto.createHash('sha256').update(data).digest('hex');
const read = p => JSON.parse(fs.readFileSync(p, 'utf8'));
const pin = p => ({path:path.relative(root,p),bytes:fs.statSync(p).size,sha256:hash(fs.readFileSync(p))});
const dtsPath = path.join(input, 'electron.d.ts');
const dts = fs.readFileSync(dtsPath, 'utf8');
const api = read(path.join(input, 'electron-api.json'));
const contracts = read(path.join(out, 'runtime-api-contracts.json'));
const evidence = new Map(fs.readFileSync(path.join(out, 'runtime-api-evidence.jsonl'),'utf8').trim().split('\n').map(x=>{const e=JSON.parse(x);return[e.id,e];}));
const ast = parser.parse(dts,{sourceType:'module',plugins:['typescript']});
const namespace = ast.program.body.find(n=>n.type==='TSModuleDeclaration' && n.id.name==='Electron');
if (!namespace || ast.errors.length) throw new Error('public declaration namespace/parse failed');
const declarations = new Map(), values = new Map();
const name = n => n?.name || (n?.type==='TSQualifiedName' ? name(n.left)+'.'+name(n.right) :
  n?.type==='MemberExpression' && !n.computed ? name(n.object)+'.'+name(n.property) : null);
function typeRef(n) {
  if(n?.type==='TSUnionType') {
    const refs=n.types.filter(x=>!['TSUndefinedKeyword','TSNullKeyword'].includes(x.type));
    if(refs.length===1) {const ref=typeRef(refs[0]);return ref?{...ref,nullable:true}:null;}
    return null;
  }
  if (n?.type==='TSTypeReference') return {type:name(n.typeName),static:false};
  if (n?.type==='TSTypeQuery') return {type:name(n.exprName),static:true};
  return null;
}
for (let n of namespace.body.body) {
  if(n.type==='ExportNamedDeclaration') n=n.declaration;
  if (!n) continue;
  if (['ClassDeclaration','TSInterfaceDeclaration'].includes(n.type)) declarations.set(n.id.name,n);
  if(n.type==='VariableDeclaration') for (const d of n.declarations) values.set(d.id.name,{node:d,...typeRef(d.id.typeAnnotation?.typeAnnotation)});
}
function parents(n) {
  return [n.superClass,...(n.extends||[]).map(x=>x.expression)].filter(Boolean).map(name);
}
function member(type,key,isStatic,seen=new Set()) {
  if(seen.has(type)) throw new Error('declaration inheritance cycle');
  seen.add(type);
  const n=declarations.get(type);
  if(!n) return null;
  const own=n.body.body.filter(x=>name(x.key)===key && (n.type==='TSInterfaceDeclaration' || !!x.static===isStatic));
  if(own.length) return {type,members:own,inheritance:[type]};
  for(const p of parents(n)) {
    const found=member(p,key,isStatic,new Set(seen));
    if(found) return {...found,inheritance:[type,...found.inheritance]};
  }
  return null;
}
const publicRange = n => ({kind:'utf8-byte-range',start:Buffer.byteLength(dts.slice(0,n.start)),endExclusive:Buffer.byteLength(dts.slice(0,n.end)),sha256:hash(dts.slice(n.start,n.end))});
function resolveTypes(canonical) {
  const parts=canonical.replace(/^electron\./,'').split('.');
  const first=parts.shift();
  const instance=first.endsWith('#instance');
  let current=instance ? {type:first.replace(/#instance$/,''),static:false} : values.get(first) || {type:first,static:true};
  const chain=[];
  if(current.node)chain.push({kind:'value-declaration',type:current.type,range:publicRange(current.node)});
  if(!parts.length) {
    const n=declarations.get(current.type);
    return {found:!!n,type:current.type,constructor:true,chain,nodes:n?[publicRange(n)]:[]};
  }
  for(let i=0;i<parts.length;i++) {
    const found=member(current.type,parts[i],current.static);
    if(!found) return {found:false,missingMember:parts[i],receiverType:current.type,static:!!current.static,chain,
      searchedDeclaration:declarations.has(current.type)?publicRange(declarations.get(current.type)):null,
      externalOrOtherBases:declarations.has(current.type)?parents(declarations.get(current.type)).filter(x=>!declarations.has(x)):[]};
    chain.push({kind:'member',key:parts[i],receiverType:current.type,declaringType:found.type,inheritance:found.inheritance,ranges:found.members.map(publicRange)});
    if(i===parts.length-1)return {found:true,chain,callable:found.members.some(n=>['TSMethodSignature','TSDeclareMethod','ClassMethod'].includes(n.type))};
    current=typeRef(found.members[0].typeAnnotation?.typeAnnotation);
    if(current?.nullable) chain[chain.length-1].nullable=true;
    if(!current)return {found:false,unsupportedPropertyType:parts[i],chain};
  }
}
const byName=new Map(api.map((x,i)=>[x.name,{data:x,index:i}]));
function jsonMember(type,key,isStatic,seen=new Set()) {
  if(seen.has(type))throw new Error('public JSON inheritance cycle');
  seen.add(type);const item=byName.get(type);if(!item)return null;
  const list=item.data.type==='Module'?['methods','properties']:isStatic?['staticMethods','staticProperties']:['instanceMethods','instanceProperties'];
  for(const group of list)for(let i=0;i<(item.data[group]||[]).length;i++)if(item.data[group][i].name===key)return {data:item.data[group][i],pointer:`/${item.index}/${group}/${i}`,group,type};
  if(item.data.extends)return jsonMember(item.data.extends,key,isStatic,seen);
  return null;
}
function resolveJson(canonical) {
  const parts=canonical.replace(/^electron\./,'').split('.'),first=parts.shift();
  let type=first.replace(/#instance$/,''),isStatic=!first.endsWith('#instance');
  const chain=[];
  if(!byName.has(type) && values.has(type)) {const v=values.get(type);type=v.type;isStatic=v.static;}
  if(!parts.length) {const item=byName.get(type);return{found:!!item?.data.constructorMethod,pointer:item?`/${item.index}/constructorMethod`:null};}
  for(let i=0;i<parts.length;i++) {
    const f=jsonMember(type,parts[i],isStatic);if(!f)return {found:false,receiverType:type,missingMember:parts[i],chain};
    chain.push({pointer:f.pointer,declaringType:f.type,group:f.group,platformTags:f.data.additionalTags||[]});
    if(i===parts.length-1)return{found:true,chain,signature:f.data.signature||null};
    type=f.data.type;isStatic=false;
    if(Array.isArray(type)) {
      const alternatives=type.filter(x=>!['undefined','null'].includes(x.type));
      if(alternatives.length===1) {type=alternatives[0].type;chain[chain.length-1].nullable=true;}
    }
    if(typeof type!=='string')return{found:false,unsupportedPropertyType:true,chain};
  }
}
const sourceBytes=new Map();
for(const s of contracts.sourceInputs) {
  const p=path.join(root,'.analysis-local/baselines',contracts.baselineId,'extracted',s.sourcePath.replace(/^app.asar\//,''));
  const bytes=fs.readFileSync(p);if(hash(bytes)!==s.sourceHash)throw new Error('frozen source changed '+s.sourcePath);
  sourceBytes.set(s.sourcePath,bytes);
}
let checked=0;
for(const c of contracts.callSites) {
  const e=evidence.get(c.evidenceId),b=sourceBytes.get(e.sourcePath);
  if(hash(b.subarray(e.locator.start,e.locator.endExclusive))!==e.spanSha256)throw new Error('source span changed '+e.id);
  checked++;
}
const rows=contracts.apiContracts.map(c=>{
  const normalized=c.canonicalApi.replace(/\.bind$/,''),bind=normalized!==c.canonicalApi;
  const types=resolveTypes(normalized),json=resolveJson(normalized);
  const status=types.found?(json.found?'declared-in-types-and-api-json':'declared-in-types-only'):(json.found?'declared-in-api-json-only':'absent-from-both-fixed-descriptions');
  return {id:c.id,canonicalApi:c.canonicalApi,normalizedApi:normalized,javascriptFunctionBind:bind,status,callSiteCount:c.callSiteCount,callSiteIds:c.callSiteIds,evidenceIds:c.evidenceIds,publicTypes:types,publicJson:json,
    confidence:'confirmed',verificationStatus:'static-description-comparison; runtime-and-argument-compatibility-unverified'};
});
const counts={};for(const x of rows)counts[x.status]=(counts[x.status]||0)+1;
const result={schemaVersion:1,baselineId:contracts.baselineId,recordedAtUtc:new Date().toISOString(),
  inputs:[pin(dtsPath),pin(path.join(input,'electron-api.json')),pin(path.join(out,'runtime-api-contracts.json')),pin(path.join(out,'runtime-api-evidence.jsonl')),pin(parserPath),pin(__filename)],
  counts:{paths:rows.length,callSites:checked,javascriptBindPaths:rows.filter(x=>x.javascriptFunctionBind).length,
    javascriptBindCallSites:rows.filter(x=>x.javascriptFunctionBind).reduce((n,x)=>n+x.callSiteCount,0),...counts},rows,
  limits:['Fixed saved 10-file runtime-source selection only; 4293 unresolved name candidates and 34 budget-limited expressions remain outside this resolved-path comparison.',
    'Declaration presence proves a public named surface, not matching options, callbacks, platform support, runtime behavior or Owl equivalence.',
    'Absence from these two release descriptions is bounded documentary absence; it does not prove all versions lack a method, rule out first-party augmentation, or establish a private implementation source.',
    'The four priority capability groups are not a complete custom-runtime denominator.']};
fs.writeFileSync(path.join(work,'surface-comparison.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result.counts));
for(const x of rows.filter(x=>!x.publicTypes.found))console.log(x.canonicalApi,x.status,JSON.stringify(x.publicTypes));
