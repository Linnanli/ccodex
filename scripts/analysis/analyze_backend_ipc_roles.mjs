// Frozen-source call/IPC ownership review. This file never loads target modules.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const [root, baseline, work] = process.argv.slice(2);
const out = path.join(root, 'analysis', baseline);
const read = p => JSON.parse(fs.readFileSync(path.join(out, p)));
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const families = read('entry-family-map.json');
const entries = families.entries.filter(x => ['backend-calls', 'ipc-channels'].includes(x.family));
assert.equal(entries.length, 141);
const parserPath = path.join(root, '.analysis-local/global-state-storage-work/tooling/node_modules/@babel/parser/lib/index.js');
const parser = createRequire(import.meta.url)(parserPath);
const cache = new Map(), sources = new Map();
function sourceFor(p, sha) {
  if (!sources.has(p)) sources.set(p, fs.readFileSync(path.join(root, '.analysis-local/baselines', baseline, 'extracted', p.replace(/^app\.asar\//, ''))));
  const b = sources.get(p); assert.equal(hash(b), sha); return b;
}
function rawFor(e) {
  const p = e.astRef.path;
  if (!cache.has(p)) cache.set(p, read(p));
  return cache.get(p).entries[Number(e.astRef.jsonPointer.split('/').at(-1))];
}
const skip = new Set(['loc', 'start', 'end', 'extra', 'comments', 'tokens', 'leadingComments', 'trailingComments', 'innerComments', 'errors']);
const functionTypes = new Set(['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression', 'ClassMethod', 'ClassPrivateMethod', 'ObjectMethod']);
const key = n => n?.type === 'Identifier' ? n.name : n?.type === 'StringLiteral' ? n.value : n?.type === 'PrivateName' ? '#' + n.id.name : null;
const staticLiteral = n => n?.type === 'StringLiteral' ? n.value : n?.type === 'TemplateLiteral' && !n.expressions.length ? n.quasis[0].value.cooked : null;
function parseUnit(location, whole = false) {
  const source = sourceFor(location.sourcePath, location.sourceHash);
  const start = whole ? 0 : location.byteRange.start, end = whole ? source.length : location.byteRange.endExclusive;
  const bytes = source.subarray(start, end);
  if (!whole) assert.equal(hash(bytes), location.spanHash);
  const prefix = !whole && location.nodeType === 'VariableDeclarator' ? 'const ' : '';
  const text = prefix + bytes.toString('utf8') + (prefix ? ';' : '');
  const ast = parser.parse(text, {sourceType: 'unambiguous'});
  const owner = whole ? ast.program : prefix ? ast.program.body[0].declarations[0] : ast.program.body[0];
  if (!whole) assert.equal(owner.type, location.nodeType);
  const nodes = [], parents = new WeakMap(), scopeAt = new WeakMap();
  function scope(parent, node, kind) {return {parent, node, kind, bindings: new Map()};}
  function bind(n, s, kind, declaration, propertyPath = []) {
    if (!n) return;
    if (n.type === 'Identifier') s.bindings.set(n.name, [...(s.bindings.get(n.name) || []), {identifier: n, kind, declaration, propertyPath}]);
    else if (n.type === 'AssignmentPattern') bind(n.left, s, kind, declaration, propertyPath);
    else if (n.type === 'RestElement') bind(n.argument, s, kind, declaration, [...propertyPath, '<rest>']);
    else if (n.type === 'ObjectPattern') for (const p of n.properties) {
      if (p.type === 'RestElement') bind(p.argument, s, kind, declaration, [...propertyPath, '<rest>']);
      else bind(p.value, s, kind, declaration, [...propertyPath, p.computed ? '<computed>' : key(p.key)]);
    }
    else if (n.type === 'ArrayPattern') n.elements.forEach((p, i) => bind(p, s, kind, declaration, [...propertyPath, i]));
  }
  function build(n, parent, current) {
    nodes.push(n); if (parent) parents.set(n, parent); let s = current;
    if (n.type === 'Program') s = scope(null, n, 'Program');
    else if (functionTypes.has(n.type)) {
      if (n.type === 'FunctionDeclaration' && n.id) bind(n.id, current, 'function', n);
      s = scope(current, n, 'function');
      for (const p of n.params) bind(p, s, 'parameter', p);
      if (n.type === 'FunctionExpression' && n.id) bind(n.id, s, 'function-self', n);
    } else if (['ClassDeclaration', 'ClassExpression'].includes(n.type)) {
      if (n.type === 'ClassDeclaration' && n.id) bind(n.id, current, 'class', n);
      s = scope(current, n, 'class'); if (n.id) bind(n.id, s, 'class-self', n);
    } else if (['BlockStatement', 'CatchClause', 'ForStatement', 'ForInStatement', 'ForOfStatement', 'SwitchStatement', 'StaticBlock'].includes(n.type)) {
      s = scope(current, n, n.type); if (n.type === 'CatchClause') bind(n.param, s, 'catch', n.param);
    }
    scopeAt.set(n, s);
    if (n.type === 'VariableDeclaration') for (const d of n.declarations) {
      let target = s; if (n.kind === 'var') while (!['Program', 'function'].includes(target.kind)) target = target.parent;
      bind(d.id, target, n.kind, d);
    }
    if (n.type === 'ImportDeclaration') for (const d of n.specifiers) bind(d.local, s, 'import', d);
    for (const [k, v] of Object.entries(n)) {
      if (skip.has(k)) continue;
      if (Array.isArray(v)) v.forEach(x => {if (x && typeof x.type === 'string') build(x, n, s);});
      else if (v && typeof v.type === 'string') build(v, n, s);
    }
  }
  // Include the wrapper Program so selected variable declarations have a binding owner.
  build(ast.program, null, null);
  const deltas = [{end: 0, delta: 0}]; let delta = 0;
  for (let i = 0; i < text.length;) {
    const cp = text.codePointAt(i), width = cp > 0xffff ? 2 : 1;
    if (cp > 127) {delta += (cp <= 0x7ff ? 2 : cp <= 0xffff ? 3 : 4) - width; deltas.push({end: i + width, delta});}
    i += width;
  }
  function offset(i) {let lo = 0, hi = deltas.length; while (lo < hi) {const m = (lo + hi) >>> 1; if (deltas[m].end <= i) lo = m + 1; else hi = m;} return start + i + deltas[lo - 1].delta - prefix.length;}
  function loc(n) {const a = offset(n.start), b = offset(n.end); return {sourcePath: location.sourcePath, sourceHash: location.sourceHash, byteRange: {start: a, endExclusive: b}, spanHash: hash(source.subarray(a, b)), nodeType: n.type};}
  const expression = n => text.slice(n.start, n.end);
  function ancestry(n) {const result = []; let p = parents.get(n); while (p) {result.push(p); p = parents.get(p);} return result;}
  function resolve(n) {let s = scopeAt.get(n); while (s) {if (s.bindings.has(n.name)) return {scope: s, definitions: s.bindings.get(n.name)}; s = s.parent;} return null;}
  function origin(n, depth = 0, seen = new Set()) {
    if (!n || depth > 4) return {kind: 'depth-limit'};
    if (n.type === 'Identifier') {
      const r = resolve(n);
      if (!r) return {kind: 'enclosing-program-binding-unresolved', name: n.name};
      return {kind: 'lexical-binding', name: n.name, definitions: r.definitions.map(d => ({kind: d.kind, propertyPath: d.propertyPath, declaration: loc(d.declaration),
        initializer: d.declaration.init ? expression(d.declaration.init) : null,
        origin: d.declaration.init && !seen.has(d.declaration) ? origin(d.declaration.init, depth + 1, new Set([...seen, d.declaration])) : null})),
        qualification: 'Lexical declarations/initializers only; runtime reassignment and actual instance are not established.'};
    }
    if (['MemberExpression', 'OptionalMemberExpression'].includes(n.type)) return {kind: 'member-access', property: n.computed ? expression(n.property) : key(n.property), computed: n.computed, object: origin(n.object, depth + 1, seen)};
    if (n.type === 'ThisExpression') {
      const chain = ancestry(n), fn = chain.find(p => functionTypes.has(p.type) && p.type !== 'ArrowFunctionExpression');
      const cls = chain.find(p => ['ClassExpression', 'ClassDeclaration'].includes(p.type));
      return {kind: 'this-reference', classSource: cls && ['ClassMethod', 'ClassPrivateMethod'].includes(fn?.type) ? loc(cls) : null, thisBindingProvenForClass: !!cls && ['ClassMethod', 'ClassPrivateMethod'].includes(fn?.type)};
    }
    if (['CallExpression', 'OptionalCallExpression', 'NewExpression'].includes(n.type)) return {kind: 'call-result', callee: expression(n.callee), call: loc(n), calleeOrigin: origin(n.callee, depth + 1, seen)};
    return {kind: 'expression', nodeType: n.type, expression: expression(n)};
  }
  return {location: {...location, byteRange: {start, endExclusive: end}, spanHash: hash(bytes)}, whole, nodes, loc, expression, parents, ancestry, resolve, origin, owner};
}
const units = new Map();
function ownerKey(x) {return x.sourcePath + ':' + x.byteRange.start + ':' + x.byteRange.endExclusive;}
// Complete IPC source Programs resolve declaration aliases and their actual API uses.
for (const e of entries.filter(x => x.family === 'ipc-channels' && !x.sourceCoordinates.sourcePath.endsWith('/main-CqEoQDOU.js'))) {
  const p = e.sourceCoordinates.sourcePath;
  if (!units.has(p)) units.set(p, parseUnit({...e.lexicalOwner, name: p.split('/').at(-1)}, true));
}
for (const e of entries) {
  if (e.family === 'ipc-channels' && !e.sourceCoordinates.sourcePath.endsWith('/main-CqEoQDOU.js')) continue;
  const k = ownerKey(e.lexicalOwner);
  if (!units.has(k)) units.set(k, parseUnit(e.lexicalOwner));
}
function unitFor(e) {return units.get(e.sourceCoordinates.sourcePath) ?? units.get(ownerKey(e.lexicalOwner));}
const backendRows = [], ipcRows = [], ipcUses = [];
for (const e of entries) {
  const unit = unitFor(e), raw = rawFor(e), saved = raw.matchedNode;
  const found = unit.nodes.filter(n => n.type === saved.nodeType && unit.loc(n).byteRange.start === saved.byteRange.start && unit.loc(n).byteRange.endExclusive === saved.byteRange.endExclusive);
  assert.equal(found.length, 1, e.entryId);
  const n = found[0], actual = unit.loc(n);
  assert.equal(actual.spanHash, saved.spanHash);
  const original = e.sourceCoordinates, source = sources.get(original.sourcePath);
  assert.equal(hash(source.subarray(original.byteRange.start, original.byteRange.endExclusive)), original.spanHash);
  if (e.family === 'backend-calls') {
    assert.equal(n.type, 'CallExpression'); assert.equal(key(n.callee.property), 'sendAppServerRequest');
    assert.equal(staticLiteral(n.arguments[0]), e.displayLabel);
    const cls = unit.ancestry(n).find(p => ['ClassExpression', 'ClassDeclaration'].includes(p.type));
    const self = n.callee.object.type === 'ThisExpression' && cls;
    const method = self ? cls.body.body.find(p => p.type === 'ClassMethod' && key(p.key) === 'sendAppServerRequest') : null;
    const objectArg = n.arguments[1]?.type === 'ObjectExpression' ? n.arguments[1] : null;
    backendRows.push({entryId: e.entryId, originalSource: original, call: actual, expression: unit.expression(n),
      method: e.displayLabel, receiver: unit.expression(n.callee.object), receiverOrigin: unit.origin(n.callee.object),
      localMethodDefinition: method ? unit.loc(method) : null,
      sourceRole: method ? 'same-class-app-server-request-port-call' : 'injected-or-derived-app-server-request-port-call',
      arguments: n.arguments.map(x => ({...unit.loc(x), expression: unit.expression(x)})),
      directObjectParameterKeys: objectArg ? objectArg.properties.map(p => p.type === 'SpreadElement' ? '<spread>' : key(p.key)) : null,
      structuralGuards: raw.structuralGuards, sourceMode: 'unknown', actualReceiverInstanceVerified: false,
      actualServiceAcceptanceVerified: false, completeFunctionalMapping: false});
  } else {
    const parent = unit.parents.get(n);
    const declaring = parent?.type === 'VariableDeclarator' && parent.init === n;
    const builder = n.type === 'TemplateLiteral' && n.expressions.length > 0;
    const comparison = parent?.type === 'BinaryExpression';
    const ancestors = unit.ancestry(n);
    const eventRegistration = comparison ? ancestors.find(p => p.type === 'CallExpression' && key(p.callee.property) === 'on' && staticLiteral(p.arguments[0]) === 'ipc-message-sync') : null;
    if (comparison) assert(eventRegistration);
    if (!declaring && !builder && !comparison) assert(parent?.type === 'CallExpression' && parent.arguments.includes(n));
    ipcRows.push({entryId: e.entryId, originalSource: original, matchedNode: actual,
      channel: e.displayLabel, sourceRole: declaring ? 'channel-name-declaration' : builder ? 'parameterized-channel-name-builder' : comparison ? 'channel-discriminator-in-event-handler' : 'channel-argument-in-call',
      eventHandler: eventRegistration ? {registration: unit.loc(eventRegistration), callee: unit.expression(eventRegistration.callee),
        comparison: {...unit.loc(parent), expression: unit.expression(parent)},
        discriminatedValueOrigin: unit.origin(parent.left === n ? parent.right : parent.left),
        branch: unit.loc(ancestors.find(p => p.type === 'IfStatement'))} : null,
      owner: e.lexicalOwner, structuralGuards: raw.structuralGuards, sourceMode: 'unknown', actualRuntimeVerified: false});
  }
}
function channelArgument(n, u, depth = 0) {
  if (!n || depth > 3) return null;
  if (staticLiteral(n)?.startsWith('codex_desktop:')) return {channel: staticLiteral(n), declaration: u.loc(n), parameterized: false};
  if (n.type === 'TemplateLiteral' && n.quasis[0].value.cooked.startsWith('codex_desktop:')) return {channel: u.expression(n).slice(1, -1), declaration: u.loc(n), parameterized: true};
  if (n.type === 'Identifier') {
    const r = u.resolve(n); if (r?.definitions.length !== 1) return null;
    return channelArgument(r.definitions[0].declaration.init, u, depth + 1);
  }
  if (n.type === 'CallExpression' && n.callee.type === 'Identifier') {
    const r = u.resolve(n.callee); if (r?.definitions.length !== 1) return null;
    const fn = r.definitions[0].declaration;
    if (fn.type !== 'FunctionDeclaration' || fn.body.body.length !== 1 || fn.body.body[0].type !== 'ReturnStatement') return null;
    return channelArgument(fn.body.body[0].argument, u, depth + 1);
  }
  return null;
}
for (const u of units.values()) {
  // Main review is limited to ICe. Backend owners are not an IPC caller census.
  if (!u.whole && u.location.name !== 'ICe') continue;
  for (const n of u.nodes) {
    if (!['CallExpression', 'OptionalCallExpression'].includes(n.type)) continue;
    const callee = n.callee;
    if (!['MemberExpression', 'OptionalMemberExpression'].includes(callee.type)) continue;
    const verb = key(callee.property);
    if (!['send', 'sendSync', 'invoke', 'postMessage', 'on', 'once', 'removeListener', 'handle'].includes(verb)) continue;
    const channel = channelArgument(n.arguments[0], u);
    if (!channel) continue;
    ipcUses.push({...channel, source: u.loc(n), callee: u.expression(callee), verb,
      receiverOrigin: u.origin(callee.object), arguments: n.arguments.slice(1).map(a => ({source: u.loc(a), expression: u.expression(a)})),
      owner: u.ancestry(n).find(p => functionTypes.has(p.type)) ? u.loc(u.ancestry(n).find(p => functionTypes.has(p.type))) : null,
      scope: u.whole ? 'complete-selected-Program' : 'complete-ICe-function', actualDeliveryVerified: false});
  }
}
for (const row of ipcRows) row.useIndices = ipcUses.map((u, i) => u.declaration.sourcePath === row.matchedNode.sourcePath && u.declaration.byteRange.start === row.matchedNode.byteRange.start && u.declaration.byteRange.endExclusive === row.matchedNode.byteRange.endExclusive ? i : -1).filter(i => i >= 0);
const mBUnit = [...units.values()].find(u => u.location.name === 'mB');
const mBClass = mBUnit.owner.init;
const selectedMethods = ['sendAppServerRequest', 'sendInternalRequest', 'routeIncomingMessage', 'routeResponse', 'ensureReady', 'constructor'];
const portMethods = mBClass.body.body.filter(n => n.type === 'ClassMethod' && selectedMethods.includes(key(n.key))).map(n => ({name: key(n.key), source: mBUnit.loc(n), expression: mBUnit.expression(n)}));
assert.equal(portMethods.length, selectedMethods.length);
const count = rows => Object.fromEntries(rows.reduce((m, r) => m.set(r.sourceRole, (m.get(r.sourceRole) ?? 0) + 1), new Map()));
const result = {schemaVersion: 1, baselineId: baseline, recordedAtUtc: new Date().toISOString(),
  parser: {path: parserPath, sha256: hash(fs.readFileSync(parserPath))},
  sourceUnits: [...units.values()].map(u => ({...u.location, wholeProgramParsed: u.whole, parsedNodes: u.nodes.length})),
  backendRows, ipcRows, ipcUses, portMethods,
  counts: {backendRecords: backendRows.length, distinctBackendMethods: new Set(backendRows.map(x => x.method)).size,
    backendRoleCounts: count(backendRows), ipcRecords: ipcRows.length, ipcSourceRoleCounts: count(ipcRows),
    selectedIpcUses: ipcUses.length, completeOriginalPrograms: [...units.values()].filter(u => u.whole).length,
    selectedCompleteOwnerParses: [...units.values()].filter(u => !u.whole).length},
  limitations: ['Selected-owner lexical bindings do not identify free enclosing-Program values or actual running instances.',
    'IPC uses cover four complete source Programs and ICe only; other main handlers must use saved qualified contracts or remain unknown.',
    'An API named sendAppServerRequest and a schema method match do not prove actual provider identity, service support or behavior.'],
  targetCodeExecuted: false, newModelSubmissions: 0, newClientRuns: 0};
fs.mkdirSync(work, {recursive: true});
fs.writeFileSync(path.join(work, 'backend-ipc-roles.json'), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify(result.counts));
