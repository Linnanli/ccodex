// Offline, bounded fixture runner. Original implementation remains in the frozen
// source files; this file contains only extraction, safety checks and test inputs.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const vm = require('node:vm');
const workspace = path.resolve(__dirname, '../..');
const options = {};
for (let i = 2; i < process.argv.length; i += 2) {
  const flag = process.argv[i];
  if (!['--parser-path', '--input-map'].includes(flag) || !process.argv[i + 1]) {
    throw new Error('Usage: node scripts/analysis/chunk_transport_fixture.cjs [--parser-path PATH] [--input-map PATH]');
  }
  options[flag] = process.argv[i + 1];
}
const parser = options['--parser-path']
  ? require(path.resolve(options['--parser-path']))
  : require('@babel/parser');
const baseline = JSON.parse(fs.readFileSync(path.join(workspace, '.analysis-local/current-baseline.json'), 'utf8'));
const outputDir = path.join(workspace, '.analysis-local/review-work');
const baselineId = baseline.baselineId;
const frozenRoot = path.resolve(workspace, baseline.extractedDirectory);
const publishedInputMap = path.join(workspace, 'analysis', baselineId, 'chunk-fixture-input-map.json');
const inputMapPath = options['--input-map']
  ? path.resolve(options['--input-map'])
  : (fs.existsSync(publishedInputMap) ? publishedInputMap : path.join(outputDir, 'chunk-fixture-input-map.json'));
const sourceMapping = JSON.parse(fs.readFileSync(inputMapPath, 'utf8'));
if (sourceMapping.baselineId !== baselineId || sourceMapping.archiveSha256 !== baseline.archiveSha256) {
  throw new Error('Input map does not match current frozen baseline; investigate the new release before extracting code');
}
if (!fs.existsSync(frozenRoot) || !fs.statSync(frozenRoot).isDirectory()) throw new Error('Frozen extracted directory is missing');
const digest = b => crypto.createHash('sha256').update(b).digest('hex');
const inputMap = [];
const buffers = new Map();
function original(evidenceId) {
  const entry = sourceMapping.sources.find(e => e.id === evidenceId);
  if (!entry) throw new Error('Missing input-map evidence ' + evidenceId);
  const rel = entry.sourcePath.replace(/^app\.asar\//, '');
  const sourceFile = path.resolve(frozenRoot, rel);
  if (!sourceFile.startsWith(frozenRoot + path.sep)) throw new Error('Source path escapes frozen directory: ' + rel);
  let b = buffers.get(rel);
  if (!b) {
    b = fs.readFileSync(sourceFile);
    if (digest(b) !== entry.sourceHash) throw new Error('Frozen hash changed: ' + rel);
    buffers.set(rel, b);
  }
  const span = b.subarray(entry.locator.start, entry.locator.endExclusive);
  if (digest(span) !== entry.spanSha256) throw new Error('Span hash changed: ' + evidenceId);
  inputMap.push({ ...entry, executionUse: 'unmodified original span, only scope wiring added' });
  return span.toString('utf8');
}

const initialization = original('REVIEW-CHUNK-E021');
inputMap[inputMap.length - 1].executionUse = 'Parsed only to locate nested complete class/assignment expressions; initializer not executed';
const initializerEvidence = sourceMapping.sources.find(e => e.id === 'REVIEW-CHUNK-E021');
const initStart = initializerEvidence.locator.start;
const initializerAst = parser.parse(initialization, { sourceType: 'script' });
const selected = {};
function findClasses(node) {
  if (!node || typeof node !== 'object') return;
  if (node.type === 'AssignmentExpression' && ['p', 'm', 'h'].includes(node.left?.name)) {
    const name = node.left.name;
    if (name === 'p' || node.right.type === 'ClassExpression') {
      const selectedNode = name === 'p' ? node : node.right;
      const start = initStart + Buffer.byteLength(initialization.slice(0, selectedNode.start));
      const endExclusive = initStart + Buffer.byteLength(initialization.slice(0, selectedNode.end));
      const span = initialization.slice(selectedNode.start, selectedNode.end);
      const saved = sourceMapping.sources.find(entry => entry.id === 'CHUNK-FIXTURE-SOURCE-' + name);
      if (!saved || saved.sourceHash !== initializerEvidence.sourceHash ||
          saved.sourcePath !== initializerEvidence.sourcePath || saved.locator.start !== start ||
          saved.locator.endExclusive !== endExclusive || saved.spanSha256 !== digest(Buffer.from(span))) {
        throw new Error('Nested complete expression differs from input map: ' + name);
      }
      selected[name] = span;
      inputMap.push({
        id: 'CHUNK-FIXTURE-SOURCE-' + name,
        baselineId,
        sourcePath: initializerEvidence.sourcePath,
        sourceHash: initializerEvidence.sourceHash,
        locator: { kind: 'byte-range', start, endExclusive },
        spanSha256: digest(Buffer.from(span)),
        symbol: name,
        locatorScope: name === 'p' ? 'complete-assignment-expression' : 'complete-class-expression',
        executionUse: 'unmodified original expression; declared within offline VM scope',
      });
    }
  }
  for (const [key, value] of Object.entries(node)) {
    if (['loc', 'start', 'end', 'extra', 'comments', 'tokens', 'leadingComments', 'trailingComments', 'innerComments'].includes(key)) continue;
    if (Array.isArray(value)) value.forEach(findClasses);
    else if (value && typeof value === 'object') findClasses(value);
  }
}
findClasses(initializerAst);
if (!selected.p || !selected.m || !selected.h) throw new Error('Receiver/assembler isolation failed');

const extractedProgram = [
  original('REVIEW-CHUNK-E001'),
  original('REVIEW-CHUNK-E002'),
  'var ' + original('REVIEW-CHUNK-E023') + ';',
  original('REVIEW-CHUNK-E024'),
  'const o = { w: ts };',
  ...['003', '004', '005', '006', '007'].map(n => original('REVIEW-CHUNK-E' + n)),
  original('REVIEW-CHUNK-E019'),
  original('REVIEW-CHUNK-E020'),
  'var p; ' + selected.p + ';',
  'var h = ' + selected.h + ';',
  'var m = ' + selected.m + ';',
].join('\n');

const prohibitedIdentifiers = new Set([
  'require', 'process', 'module', 'exports', 'eval', 'Function',
  'fetch', 'XMLHttpRequest', 'WebSocket', 'Worker', 'SharedWorker',
  'setTimeout', 'setInterval', 'setImmediate', 'queueMicrotask',
]);
const audit = { prohibitedIdentifiersFound: [], prohibitedNodesFound: [], method: 'Manual complete-span review plus AST forbidden-identifier/async/import checks; capability-free VM context', sideEffectsAllowed: 'Only internal in-memory arrays, maps, objects and receiver state', programSha256: digest(Buffer.from(extractedProgram)) };
const programAst = parser.parse(extractedProgram, { sourceType: 'script' });
function auditNode(node) {
  if (!node || typeof node !== 'object') return;
  if (node.type === 'Identifier' && prohibitedIdentifiers.has(node.name)) audit.prohibitedIdentifiersFound.push(node.name);
  if (['ImportDeclaration', 'ImportExpression', 'AwaitExpression', 'WithStatement'].includes(node.type) || node.async === true) audit.prohibitedNodesFound.push(node.type);
  for (const [key, value] of Object.entries(node)) {
    if (['loc', 'start', 'end', 'extra', 'comments', 'tokens', 'leadingComments', 'trailingComments', 'innerComments'].includes(key)) continue;
    if (Array.isArray(value)) value.forEach(auditNode);
    else if (value && typeof value === 'object') auditNode(value);
  }
}
auditNode(programAst);
if (audit.prohibitedIdentifiersFound.length || audit.prohibitedNodesFound.length) throw new Error('Pure-function audit failed');

const context = vm.createContext(Object.create(null), {
  codeGeneration: { strings: false, wasm: false },
  microtaskMode: 'afterEvaluate',
});
new vm.Script(extractedProgram, { filename: 'frozen-chunk-pure-spans.js' }).runInContext(context, { timeout: 1000 });
new vm.Script(`
function snap(value) {
  if (value === undefined) return {kind:'undefined'};
  if (value === null) return {kind:'null'};
  if (typeof value === 'string') return {kind:'string',value,utf16:Array.from({length:value.length},(_,i)=>value.charCodeAt(i))};
  if (Array.isArray(value)) return {kind:'array',items:value.map(snap)};
  if (typeof value === 'object') return {kind:'object',entries:Object.entries(value).map(([k,v])=>[snap(k),snap(v)])};
  return {kind:typeof value,value};
}
function equal(a,b) {return JSON.stringify(snap(a))===JSON.stringify(snap(b));}
function roundtrip(input,batchTargetBytes=16) {
  const frames=[...bG(input,{transferId:'fixture-transfer',batchTargetBytes})];
  const receiver=new m();
  const results=frames.map(frame=>receiver.receive(frame));
  const completed=results.filter(r=>r.type==='complete');
  return {frames,results,completed,receiver};
}
function checks(items) {return items.map(([name,pass])=>({name,pass:pass===true}));}
function logicalError(tokens,end=true) {
  const receiver=new m();receiver.receive({marker:le,kind:'start',transferId:'logical',sequence:0});
  let stage='chunk';
  try {receiver.receive({marker:le,kind:'chunk',transferId:'logical',sequence:1,tokens});
    stage='end';if(end) receiver.receive({marker:le,kind:'end',transferId:'logical',sequence:2});
    return {error:null,stage,activeTransfers:receiver.transfers.size};
  } catch(error) {return {error:{name:error.name,message:error.message},stage,activeTransfers:receiver.transfers.size};}
}
`, { filename: 'owned-fixture-helpers.js' }).runInContext(context, { timeout: 1000 });

const fixtures = [
  {
    id: 'CHUNK-F01', name: 'Ordinary object, Unicode, undefined and array roundtrip',
    body: `const input={type:'fixture',text:'A😀𠮷é🇨🇳Z',nested:{nil:null,undef:undefined,flag:false,zero:0,empty:''},list:[undefined,null,false,0,'x',{deep:true}]};
      const r=roundtrip(input,16);return {input:snap(input),output:snap(r.completed[0]?.message),frameCount:r.frames.length,checks:checks([['exact deep value including undefined',equal(input,r.completed[0]?.message)],['one completion',r.completed.length===1],['ack for every frame',r.results.every((x,i)=>x.acknowledgement?.sequence===i)],['no early completion',r.results.slice(0,-1).every(x=>x.type==='pending')],['receiver cleaned',r.receiver.transfers.size===0]])};`,
  },
  {
    id: 'CHUNK-F02', name: 'UTF-16 surrogate split in long keys and values',
    body: `const key='😀key𠮷';const text='A😀𠮷é🇨🇳'+String.fromCharCode(0xD83D)+'X'+String.fromCharCode(0xDC00)+'Z';const input={type:'fixture',[key]:text};const r=roundtrip(input,4);
      const strings=r.frames.flatMap(f=>f.tokens??[]).filter(t=>t.type==='string-chunk').map(t=>({text:t.value,utf16:Array.from({length:t.value.length},(_,i)=>t.value.charCodeAt(i))}));
      return {input:snap(input),output:snap(r.completed[0]?.message),stringChunks:strings,checks:checks([['exact Unicode and lone-surrogate units preserved',equal(input,r.completed[0]?.message)],['actual single high surrogate token',strings.some(x=>x.utf16.length===1&&x.utf16[0]>=0xD800&&x.utf16[0]<=0xDBFF)],['actual single low surrogate token',strings.some(x=>x.utf16.length===1&&x.utf16[0]>=0xDC00&&x.utf16[0]<=0xDFFF)],['all generated frames recognized',r.frames.every(l)]])};`,
  },
  {
    id: 'CHUNK-F03', name: 'Special chunked array and repeated object references',
    body: `const repeated={value:'same'};const input={type:'fixture',normal:[1,undefined],special:new $o([[1,undefined],[2,'😀']],4),a:repeated,b:repeated};const r=roundtrip(input,16);const output=r.completed[0]?.message;
      return {output:snap(output),checks:checks([['special chunks flatten',equal(output.special,[1,undefined,2,'😀'])],['ordinary array preserved',equal(output.normal,[1,undefined])],['repeated shape preserved',equal(output.a,repeated)&&equal(output.b,repeated)],['shared identity not preserved',output.a!==output.b]])};`,
  },
  {
    id: 'CHUNK-F04', name: 'Wrong sequence deletes transfer; later correct sequence cannot resume',
    body: `const r=new m();const start=r.receive({marker:le,kind:'start',transferId:'seq',sequence:0});const wrong=r.receive({marker:le,kind:'chunk',transferId:'seq',sequence:2,tokens:[{type:'value',value:'x'}]});const afterWrong=r.transfers.size;const later=r.receive({marker:le,kind:'chunk',transferId:'seq',sequence:1,tokens:[{type:'value',value:'x'}]});return {start,wrong,afterWrong,later,checks:checks([['start acknowledged',start.acknowledgement?.sequence===0],['wrong sequence has no ack',wrong.acknowledgement===null],['state deleted',afterWrong===0],['later frame cannot recover',later.type==='pending'&&later.acknowledgement===null]])};`,
  },
  {
    id: 'CHUNK-F05', name: 'Duplicate frame deletes transfer and missing-start frame has no ack',
    body: `const r=new m();const frame={marker:le,kind:'chunk',transferId:'duplicate',sequence:1,tokens:[{type:'value',value:'x'}]};r.receive({marker:le,kind:'start',transferId:'duplicate',sequence:0});const first=r.receive(frame);const duplicate=r.receive(frame);const end=r.receive({marker:le,kind:'end',transferId:'duplicate',sequence:2});const missing=new m().receive(frame);return {first,duplicate,end,missing,checks:checks([['first valid chunk acked',first.acknowledgement?.sequence===1],['duplicate unacked',duplicate.acknowledgement===null],['duplicate deleted state',r.transfers.size===0],['end cannot complete after duplicate',end.type==='pending'&&end.acknowledgement===null],['chunk without start unacked',missing.type==='pending'&&missing.acknowledgement===null]])};`,
  },
  {
    id: 'CHUNK-F06', name: 'New start clears old transfer',
    body: `const r=new m();r.receive({marker:le,kind:'start',transferId:'old',sequence:0});r.receive({marker:le,kind:'start',transferId:'new',sequence:0});const afterStart=[...r.transfers.keys()];const old=r.receive({marker:le,kind:'chunk',transferId:'old',sequence:1,tokens:[{type:'value',value:'old'}]});r.receive({marker:le,kind:'chunk',transferId:'new',sequence:1,tokens:[{type:'value',value:'new'}]});const end=r.receive({marker:le,kind:'end',transferId:'new',sequence:2});return {afterStart,old,end,checks:checks([['only new transfer exists',equal(afterStart,['new'])],['old frame unacked',old.acknowledgement===null],['new transfer completes',end.type==='complete'&&end.message==='new']])};`,
  },
  {
    id: 'CHUNK-F07', name: 'Malformed logical tokens produce actual assembler errors',
    body: `const cases=[['unmatched-container-end',[{type:'container-end'}]],['key-outside-object',[{type:'key',value:'x'}]],['object-value-without-key',[{type:'object-start'},{type:'value',value:1}]],['nested-string',[{type:'string-start',target:'value'},{type:'string-start',target:'value'}]],['string-chunk-no-start',[{type:'string-chunk',value:'x'}]],['string-end-no-start',[{type:'string-end'}]],['unfinished-container',[{type:'array-start'}]],['unfinished-string',[{type:'string-start',target:'value'}]],['multiple-roots',[{type:'value',value:1},{type:'value',value:2}]]];const actual=cases.map(([name,tokens])=>({name,...logicalError(tokens)}));return {actual,checks:checks([['each malformed case throws',actual.every(x=>x.error?.name==='Error')],['premature end deletes transfer before finish throws',actual.filter(x=>x.stage==='end').every(x=>x.activeTransfers===0)],['chunk exception leaves active transfer',actual.filter(x=>x.stage==='chunk').every(x=>x.activeTransfers===1)]])};`,
  },
  {
    id: 'CHUNK-F08', name: 'Empty transfer end and missing value field',
    body: `const empty=new m();empty.receive({marker:le,kind:'start',transferId:'empty',sequence:0});let emptyError;try{empty.receive({marker:le,kind:'end',transferId:'empty',sequence:1})}catch(e){emptyError={name:e.name,message:e.message}};const r=new m();r.receive({marker:le,kind:'start',transferId:'missing-value',sequence:0});const chunk=r.receive({marker:le,kind:'chunk',transferId:'missing-value',sequence:1,tokens:[{type:'object-start'},{type:'key',value:'type'},{type:'value',value:'fixture'},{type:'key',value:'missing'},{type:'value'},{type:'container-end'}]});const end=r.receive({marker:le,kind:'end',transferId:'missing-value',sequence:2});return {emptyError,emptyActiveTransfers:empty.transfers.size,chunk,end:{type:end.type,message:snap(end.message)},checks:checks([['empty end throws',emptyError?.name==='Error'],['empty end deletes transfer',empty.transfers.size===0],['absent value field recognized',u({type:'value'})],['missing value creates own undefined property',Object.hasOwn(end.message,'missing')&&end.message.missing===undefined]])};`,
  },
  {
    id: 'CHUNK-F09', name: 'Invalid frame shape is passthrough',
    body: `const cases=[{marker:le,kind:'chunk',transferId:'shape',sequence:1,tokens:[{type:'invalid'}]},{marker:le,kind:'start',transferId:'shape',sequence:1.5},{marker:le,kind:'start',transferId:'shape',sequence:Number.MAX_SAFE_INTEGER+1},{marker:le,kind:'other',transferId:'shape',sequence:0}];const actual=cases.map(frame=>({recognized:l(frame),result:new m().receive(frame)}));return {actual,checks:checks([['invalid shapes unrecognized',actual.every(x=>x.recognized===false)],['invalid shapes passthrough',actual.every(x=>x.result.type==='passthrough')]])};`,
  },
  {
    id: 'CHUNK-F10', name: 'Tokenization rejects cycles and unsupported primitive types',
    body: `const cyclic={type:'fixture'};cyclic.self=cyclic;const cases=[['cycle',cyclic],['bigint',1n],['function',()=>1],['symbol',Symbol('fixture')]];const actual=cases.map(([name,input])=>{try{[...bG(input,{transferId:name,batchTargetBytes:16})];return {name,error:null}}catch(e){return{name,error:{name:e.name,message:e.message}}}});return {actual,checks:checks([['all rejected',actual.every(x=>x.error?.name==='Error')],['cycle message retained',actual[0].error.message==='Chunked messages cannot contain cyclic values']])};`,
  },
  {
    id: 'CHUNK-F11', name: 'Enumerable object keys and nonplain object representation',
    body: `const input={type:'fixture',['__proto__']:{own:true},date:new Date(0),bytes:new Uint8Array([1,2])};const r=roundtrip(input,16);const out=r.completed[0]?.message;return {output:snap(out),checks:checks([['proto key is own property',Object.hasOwn(out,'__proto__')],['prototype remains ordinary',Object.getPrototypeOf(out)===Object.prototype],['date serialized as enumerable empty object',equal(out.date,{})],['typed array serialized by enumerable entries',equal(out.bytes,{'0':1,'1':2})]])};`,
  },
];

const results = [];
for (const fixture of fixtures) {
  const startedAtUtc = new Date().toISOString();
  const script = `JSON.stringify((()=>{${fixture.body}})())`;
  let actual, executionError = null;
  try {
    actual = JSON.parse(new vm.Script(script, { filename: fixture.id + '.fixture.js' }).runInContext(context, { timeout: 1000 }));
  } catch (error) {
    executionError = { name: error.name, message: error.message };
  }
  results.push({ id: fixture.id, name: fixture.name, startedAtUtc, timeoutMs: 1000,
    inputAndSteps: fixture.body, actual, executionError,
    passed: !executionError && actual.checks.every(check => check.pass),
  });
}

const mapping = { baselineId, archiveSha256: baseline.archiveSha256,
  sourceScope: 'Only original complete tokenizer/validator/generator/receiver/assembler expressions. No bundle initializer, sender class, IPC or application code is executed.',
  sources: inputMap, extractionProgramSha256: digest(Buffer.from(extractedProgram)),
  scopeWiring: ['Original variable declarators are prefixed with var and terminated with a semicolon.',
    'Original receiver m and assembler h class expressions are given local var bindings.',
    'Original unset Symbol assignment p is given a local var binding.',
    'Imported predicate is wired as const o={w:ts}, with original ts and original special-array class $o.'],
  sourceTextSaved: false, audit,
};
const summary = { baselineId, executedAtUtc: new Date().toISOString(),
  runner: { sourcePath: path.relative(workspace, __filename), sourceSha256: digest(fs.readFileSync(__filename)),
    inputMapPath: path.relative(workspace, inputMapPath), inputMapSha256: digest(fs.readFileSync(inputMapPath)) },
  nodeVersion: process.version, platform: process.platform, architecture: process.arch,
  execution: { engine: 'node:vm', contextCapabilities: 'No require/process/fs/network/IPC/timers injected; string and Wasm code generation disabled.',
    compileAndInitializeTimeoutMs: 1000, perFixtureTimeoutMs: 1000, originalClientLaunched: false,
    testInputs: 'Only synthetic owned plain objects, Unicode, arrays and deliberate malformed frames; no personal data.' },
  sourceEvidenceValidated: true, validationScope: 'pure-code-fixtures-only', uiVerified: false, ipcVerified: false,
  sourceSpans: inputMap.length, fixtureCount: results.length,
  assertionCount: results.reduce((count, result) => count + (result.actual?.checks.length ?? 0), 0),
  passedFixtures: results.filter(result => result.passed).length,
  failedFixtures: results.filter(result => !result.passed).map(result => result.id),
  limitations: ['Tests establish extracted pure-code behavior in this Node VM only; not Electron/Owl IPC delivery, renderer UI reachability or application completeness.',
    'Sender backpressure, critical priority, lifecycle loading retry and lost-ack handling are not executed by these pure-function fixtures.',
    'No public dependency equivalence, upstream modification or complete mode boundary is established.',
    'Preload shared-object cache parity and origin gate are not executed.',
    'Original code text stays in the local frozen evidence; this runner writes mapping and actual results without copying implementation source into output files.'],
};
fs.mkdirSync(outputDir, { recursive: true });
fs.writeFileSync(path.join(outputDir, 'chunk-fixture-input-map.json'), JSON.stringify(mapping, null, 2) + '\n');
fs.writeFileSync(path.join(outputDir, 'chunk-fixture-results.jsonl'), results.map(result => JSON.stringify(result)).join('\n') + '\n');
fs.writeFileSync(path.join(outputDir, 'chunk-fixture-summary.json'), JSON.stringify(summary, null, 2) + '\n');
console.log(JSON.stringify(summary));
if (summary.failedFixtures.length) process.exitCode = 1;
