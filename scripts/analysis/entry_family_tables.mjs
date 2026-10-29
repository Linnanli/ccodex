// Resolve the settings resource table in its complete original Program.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
const root=process.cwd(),baseline='codex-26.1007.30912-c5b273322a83';
const sourcePath='app.asar/webview/assets/use-visible-settings-sections-2fe9342ddfa1.js';
const file=path.join(root,'.analysis-local/baselines',baseline,'extracted',sourcePath.replace('app.asar/',''));
const b=fs.readFileSync(file),text=b.toString(),hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const parserPath=path.join(root,'.analysis-local/global-state-storage-work/tooling/node_modules/@babel/parser/lib/index.js');
const parser=createRequire(import.meta.url)(parserPath),startedAtUtc=new Date().toISOString();
const ast=parser.parse(text,{sourceType:'module'}),nodes=[],parents=new WeakMap();
const skip=new Set(['loc','start','end','extra','comments','tokens','leadingComments','trailingComments','innerComments','errors']);
function walk(n,p){nodes.push(n);if(p)parents.set(n,p);for(const k of Object.keys(n)){
 if(skip.has(k))continue;const v=n[k];if(Array.isArray(v)){for(const c of v)if(c&&typeof c.type==='string')walk(c,n);}else if(v&&typeof v.type==='string')walk(v,n);
}}
walk(ast.program,null);
function loc(n){const a=Buffer.byteLength(text.slice(0,n.start)),z=Buffer.byteLength(text.slice(0,n.end));return{sourcePath,sourceHash:hash(b),byteRange:{start:a,endExclusive:z},spanHash:hash(b.subarray(a,z)),nodeType:n.type};}
const exact=(predicate,label)=>{const found=nodes.filter(predicate);if(found.length!==1)throw Error(label+' '+found.length);return found[0];};
const declaration=exact(n=>n.type==='VariableDeclarator'&&n.id.type==='Identifier'&&n.id.name==='ua','declaration');
if(parents.get(parents.get(declaration))!==ast.program)throw Error('ua declaration must be Program-owned');
const assignment=exact(n=>n.type==='AssignmentExpression'&&n.left.type==='Identifier'&&n.left.name==='ua','assignment');
if(assignment.right.type!=='ObjectExpression')throw Error('Not a resource table');
const consumer=exact(n=>n.type==='FunctionDeclaration'&&n.id.name==='la','consumer');
if(parents.get(consumer)!==ast.program||consumer.params.some(p=>p.type!=='Identifier'||p.name==='ua'))throw Error('Unexpected la scope');
const uses=nodes.filter(n=>n.type==='Identifier'&&n.name==='ua');
if(uses.length!==3)throw Error('Additional ua binding/reference requires review');
const lookup=exact(n=>n.type==='MemberExpression'&&n.object.type==='Identifier'&&n.object.name==='ua','lookup');
if(!lookup.computed||lookup.property.type!=='Identifier'||lookup.property.name!==consumer.params[0].name)throw Error('Unexpected key source');
let ancestor=lookup;while(ancestor&&ancestor!==consumer)ancestor=parents.get(ancestor);if(!ancestor)throw Error('Lookup not in consumer');
const ledger=JSON.parse(fs.readFileSync(path.join(root,'analysis',baseline,'functional-entry-ledger.json')));
const candidates=ledger.entries.filter(e=>e.entryKind==='settings-section-lexical-candidate');
const properties=assignment.right.properties.map(p=>({key:p.key.type==='Identifier'?p.key.name:p.key.value,node:p}));
if(properties.length!==53||candidates.length!==53)throw Error('Unexpected table denominator');
const relations=candidates.map(e=>{
 const r=e.sourceCoordinates.byteRange;
 const matches=properties.filter(p=>{const s=loc(p.node);return s.byteRange.start<=r.start&&s.byteRange.endExclusive>=r.endExclusive;});
 if(matches.length!==1||matches[0].key!==e.displayLabel)throw Error('Entry not in table '+e.entryId);
 const prop=matches[0].node;
 if(prop.value.type!=='ObjectExpression')throw Error('Non-object descriptor');
 const fields=prop.value.properties.map(x=>x.key.name??x.key.value);
 if(!fields.includes('component')||fields.some(x=>!['component','commandAsset','navigation'].includes(x)))throw Error('Unexpected resource descriptor fields');
 return{entryId:e.entryId,key:matches[0].key,property:loc(prop),fields,
  role:'settings-icon-and-navigation-resource-descriptor',isSettingsPanelRegistration:false,
  explanation:'The candidate span is a property of ua; la looks up ua by its key and returns resource descriptor objects. No settings action or panel mounting is established by this registration.'};
});
const exported=nodes.filter(n=>n.type==='ExportSpecifier'&&n.local.name==='la').map(n=>({exported:n.exported.name??n.exported.value,source:loc(n)}));
const result={schemaVersion:1,baselineId:baseline,sourcePath,sourceHash:hash(b),sourceBytes:b.length,
 fullProgramParsed:true,nodeCount:nodes.length,parserErrors:ast.errors?.length??0,
 parser:{path:parserPath,sha256:hash(fs.readFileSync(parserPath))},startedAtUtc,completedAtUtc:new Date().toISOString(),
 declaration:loc(declaration),assignment:loc(assignment),consumer:loc(consumer),lookup:loc(lookup),exports:exported,
 relations,confirmedSettingsPanelsAdded:0,modeClassificationsAdded:0,
 targetCodeExecuted:false,originalClientRunsAdded:0,modelSubmissionsAdded:0,newReaRuns:0};
const dest=path.join(root,'.analysis-local/entry-family-work/settings-table.json');
fs.writeFileSync(dest,JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({settingsCandidates:relations.length,resourceDescriptors:relations.length,settingsPanelsAdded:0,nodeCount:nodes.length,output:dest}));
