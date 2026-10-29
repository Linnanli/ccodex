const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=process.cwd(),work=path.join(root,'.analysis-local/resume-provider-resolution-work');
const parserPath=path.join(root,'.analysis-local/global-state-storage-work/tooling/node_modules/@babel/parser/lib/index.js'),parser=require(parserPath);
const index=JSON.parse(fs.readFileSync(path.join(work,'main-01/source-contracts.json'))),unit=index.units.find(u=>u.name==='u0e');
const source=fs.readFileSync(path.join(root,'.analysis-local/baselines',index.baselineId,'extracted',index.sourcePath.slice(9))),bytes=source.subarray(unit.byteRange.start,unit.byteRange.endExclusive),text=bytes.toString('utf8');
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');if(hash(source)!==index.sourceHash||hash(bytes)!==unit.spanHash)throw Error('Input mismatch');
const ast=parser.parse(text,{sourceType:'script'}),nodes=[],parents=new WeakMap();
function walk(n,p){if(!n?.type)return;nodes.push(n);if(p)parents.set(n,p);for(const[k,v]of Object.entries(n)){if(['loc','extra','comments'].includes(k))continue;if(Array.isArray(v))for(const x of v)if(x?.type)walk(x,n);else{}else if(v?.type)walk(v,n);}}walk(ast.program,null);
function loc(n){const start=unit.byteRange.start+Buffer.byteLength(text.slice(0,n.start)),endExclusive=unit.byteRange.start+Buffer.byteLength(text.slice(0,n.end));return{sourcePath:index.sourcePath,sourceHash:index.sourceHash,byteRange:{start,endExclusive},spanHash:hash(source.subarray(start,endExclusive)),nodeType:n.type};}
const declarations=nodes.filter(n=>n.type==='VariableDeclarator'&&['z','ne'].includes(n.id.name));
if(declarations.length!==2||text.slice(declarations.find(n=>n.id.name==='z').start,declarations.find(n=>n.id.name==='z').end)!=='z=!_.app.isPackaged')throw Error('Unexpected flag declarations');
const references=nodes.filter(n=>n.type==='Identifier'&&n.name==='ne');if(references.length!==2)throw Error('Unexpected local ne uses');
const result={baselineId:index.baselineId,method:'selected complete u0e FunctionDeclaration AST, local z/ne declaration and sole reference; no target evaluation',inputUnit:unit,parserSha256:hash(fs.readFileSync(parserPath)),completeProgramParsed:false,selectedUnitParsed:true,nodeCount:nodes.length,declarations:declarations.map(n=>({name:n.id.name,expression:text.slice(n.start,n.end),...loc(n)})),references:references.map(n=>({reference:loc(n),parent:loc(parents.get(n)),expression:text.slice(parents.get(n).start,parents.get(n).end)})),modelSubmissionsAdded:0};
fs.writeFileSync(path.join(work,'startup-gate.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({nodeCount:nodes.length,declarations:result.declarations,references:result.references}));
