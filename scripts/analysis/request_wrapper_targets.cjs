// Parse selected complete frozen class/function prefixes as data. Never evaluate target code.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const workspace = path.resolve(__dirname, '../..');
const parser = process.argv[2] ? require(path.resolve(process.argv[2])) : require('@babel/parser');
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
const baseline = JSON.parse(fs.readFileSync(path.join(workspace, '.analysis-local/current-baseline.json'), 'utf8'));
const root = path.resolve(workspace, baseline.extractedDirectory);
const evidence = [], findings = [];
function source(rel) {
  const bytes = fs.readFileSync(path.join(root, rel));
  return { rel, bytes, text: bytes.toString('utf8'), sourceHash: sha(bytes) };
}
function prefix(s, start, accepted = ['ClassExpression','FunctionExpression','ArrowFunctionExpression']) {
  let error;
  for (const max of [100000, 250000, 500000]) {
    const value = s.text.slice(start, start + max);
    let ast;
    try { ast = parser.parseExpression(value, { sourceType: 'module' }); }
    catch (caught) {
      error = caught;
      if (Number.isInteger(caught.pos) && caught.pos > 0) {
        try { ast = parser.parseExpression(value.slice(0, caught.pos), { sourceType: 'module' }); } catch {}
      }
    }
    if (ast) {
      while (ast.type === 'SequenceExpression') ast = ast.expressions[0];
      if (accepted.includes(ast.type)) return { ast, base: start };
    }
  }
  throw Error('Cannot isolate complete prefix at ' + s.rel + ':' + start + ': ' + error?.message);
}
function add(s, node, base, role, claim, claimScope) {
  const start = Buffer.byteLength(s.text.slice(0, base + node.start)), endExclusive = Buffer.byteLength(s.text.slice(0, base + node.end));
  const existing = evidence.find(e => e.sourcePath === 'app.asar/' + s.rel && e.locator.start === start && e.locator.endExclusive === endExclusive && e.locatorScope === role);
  if (existing) return existing.id;
  const id = 'REQUEST-WRAPPER-TARGET-' + String(evidence.length + 1).padStart(4, '0');
  evidence.push({ id, baselineId: baseline.baselineId, sourcePath: 'app.asar/' + s.rel, sourceHash: s.sourceHash,
    locator: { kind: 'byte-range', start, endExclusive }, spanSha256: sha(s.bytes.subarray(start, endExclusive)), locatorScope: role,
    claim, claimScope, verificationStatus: 'static-prefix-AST-verified; target-code-not-executed' });
  return id;
}
const key = node => node?.name ?? node?.value ?? (node?.type === 'PrivateName' ? '#' + node.id.name : null);
function classAnchor(s, name, methods) {
  const match = new RegExp('\\b' + name + '=class(?:\\s|\\{)').exec(s.text);
  if (!match) throw Error('Missing class binding ' + name);
  const start = match.index + name.length + 1, p = prefix(s, start);
  const record = { symbol: name, sourcePath: 'app.asar/' + s.rel,
    classEvidenceId: add(s,p.ast,p.base,'complete-class-expression','Complete class bound to ' + name,'Static class shape only; runtime instance/mode needs caller binding'), members: {} };
  for (const member of p.ast.body.body) if (methods.includes(key(member.key))) record.members[key(member.key)] = {
    evidenceId: add(s,member,p.base,'complete-class-member','Complete ' + name + '.' + key(member.key),'Member semantics only; injected receiver identity may remain unresolved') };
  findings.push(record); return { ...p, record };
}
function functionAnchor(s, name) {
  const match = new RegExp('(?:async\\s+)?function ' + name.replace(/\$/g,'\\$') + '\\(').exec(s.text);
  if (!match) throw Error('Missing function ' + name);
  const p = prefix(s,match.index);
  const record = { symbol:name, sourcePath:'app.asar/'+s.rel, functionEvidenceId:add(s,p.ast,p.base,'complete-function','Complete '+name+' function','Static function only; call binding separately reviewed') };
  findings.push(record); return p;
}
function assignmentAnchor(s, name) {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = new RegExp('(?<![\\w$])' + escaped + '=').exec(s.text);
  if (!match) throw Error('Missing assignment ' + name);
  const p = prefix(s, match.index, ['AssignmentExpression']);
  if (p.ast.left.type !== 'Identifier' || p.ast.left.name !== name) throw Error('Unexpected assignment binding');
  const record = { symbol: name, sourcePath: 'app.asar/' + s.rel,
    assignmentEvidenceId: add(s,p.ast,p.base,'complete-assignment-expression','Complete initializer assignment for ' + name,'Exact named assignment only; callers and runtime branch separately reviewed') };
  findings.push(record); return p;
}
function expressionAnchor(s, marker, role) {
  const start = s.text.indexOf(marker);
  if (start < 0) throw Error('Missing expression marker ' + marker);
  const p = prefix(s,start,['NewExpression','CallExpression','AssignmentExpression','MemberExpression']);
  const record = { symbol: marker, sourcePath: 'app.asar/' + s.rel,
    expressionEvidenceId: add(s,p.ast,p.base,role,'Complete selected expression beginning ' + marker,'Only the selected expression; enclosing callback inputs may remain unresolved') };
  findings.push(record); return p;
}
function methodAnchor(s, marker) {
  const start = s.text.indexOf(marker);
  if (start < 0) throw Error('Missing method marker ' + marker);
  const wrapped = { ...s, text: 'function ' + s.text.slice(start) };
  const p = prefix(wrapped,0,['FunctionExpression']);
  const end = start + p.ast.end - 9;
  const exact = s.text.slice(start,end);
  const checked = parser.parseExpression('class {' + exact + '}',{sourceType:'module'});
  if (checked.body.body.length !== 1 || checked.body.body[0].type !== 'ClassMethod') throw Error('Expected exactly one complete class method');
  const record = { symbol:marker, sourcePath:'app.asar/'+s.rel,
    methodEvidenceId:add(s,{start:0,end:end-start},start,'complete-class-method','Complete original '+marker+' method; isolated wrapper is parsed but never evaluated','Method body and lexical callbacks only; no runtime service creation performed') };
  findings.push(record); return {ast:checked.body.body[0],base:start-7,record};
}
const shared = source('webview/assets/app-shared-8bd9d0399038.js');
classAnchor(shared,'Dfn',['constructor','sendRequest','discardConversationFromCache','forkConversationFromTurn','editLastUserTurn','retrySafetyBufferedTurn','stopThread']);
classAnchor(shared,'Spn',['constructor','sendRequest','enqueueRequest','createRequest','dispatchRequest','sendAppServerExtensionRequest']);
classAnchor(shared,'X2t',['constructor','sendRequest','readSerializedConfig']);
classAnchor(shared,'AW',['constructor','sendRequest','getInstance']);
for (const name of ['KI','N9t','dan','man','msn','adn','Uli','qli']) functionAnchor(shared,name);
const main = source('.vite/build/main-CqEoQDOU.js');
classAnchor(main,'_fe',['constructor','sendRequest','createRequest','send','sendAppServerExtensionRequest']);
classAnchor(main,'fue',['constructor','getRoot','getMetadata','readDirectory','readFile']);
const localStart = main.text.indexOf('async createLocal(');
const classMatches = [...main.text.slice(0,localStart).matchAll(/\b([A-Za-z_$][\w$]*)=class(?:\s|\{)/g)];
const projectsName = classMatches.at(-1)?.[1];
if (!projectsName) throw Error('Project service class not found');
classAnchor(main,projectsName,['constructor','createLocal','createDefaultWorkspaceRoot','confirmProjectFolders']);
// Additional narrow bindings: existing evidence IDs above remain stable.
for (const name of ['loi','Sii']) functionAnchor(shared,name);
for (const name of ['Ioi','N3','nIt']) assignmentAnchor(shared,name);
for (const name of ['hFt']) functionAnchor(shared,name);
expressionAnchor(main,'new fue((e,t)=>h(r.ki).sendAppServerExtensionRequest','complete-service-instantiation');
expressionAnchor(main,'new _fe(t,e.hostId,o,','complete-transport-instantiation');
const src = source('.vite/build/src-BJv5Mk7n.js');
classAnchor(src,'c1',['constructor','sendRequest','connect']);
functionAnchor(shared,'Vfn');
for (const name of ['qI','HI','JI']) assignmentAnchor(shared,name);
assignmentAnchor(main,'WHe');
expressionAnchor(main,'new qHe(this.scopedState,','complete-project-service-instantiation');
methodAnchor(main,'createAppHost(e){');
classAnchor(main,'hXe',['constructor','createAppHost']);
classAnchor(src,'p1',['constructor','getIdeContext','findThreadOwner','requestThreadFollower']);
const sourceRecords = [shared,main,src].map(s=>({sourcePath:'app.asar/'+s.rel,sourceHash:s.sourceHash,bytes:s.bytes.length}));
const result = { baselineId:baseline.baselineId, archiveSha256:baseline.archiveSha256,
  method:'Targeted prefix AST parses for complete classes/functions; metadata only, no target evaluation or whole bundle reparse',
  script:{ path:path.relative(workspace,__filename), sha256:sha(fs.readFileSync(__filename)) },
  scope:{ sourceFiles:sourceRecords.length, selectedClassesOrFunctions:findings.length, selectedClassFunctionPrefixes:findings.map(x=>x.symbol), fullBundleScan:false }, sources:sourceRecords, findings,
  limitations:['Class/function isolation does not resolve all injected callbacks, mode guards or runtime branches.', 'No UI, IPC, app-server or project creation performed.'] };
const out = path.join(workspace,'.analysis-local/review-work'); fs.mkdirSync(out,{recursive:true});
fs.writeFileSync(path.join(out,'request-wrapper-targets.json'),JSON.stringify(result,null,2)+'\n');
fs.writeFileSync(path.join(out,'request-wrapper-target-evidence.jsonl'),evidence.map(x=>JSON.stringify(x)).join('\n')+'\n');
console.log(JSON.stringify({scope:result.scope,evidenceCount:evidence.length}));
