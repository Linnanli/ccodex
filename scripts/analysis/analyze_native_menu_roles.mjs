// Parse selected complete owners; never import or execute the target application.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';

const [root, baseline, work] = process.argv.slice(2);
const out = path.join(root, 'analysis', baseline);
const read = name => JSON.parse(fs.readFileSync(path.join(out, name)));
const family = read('entry-family-map.json');
const menu = read('menu-command-contracts.json');
const entries = family.entries.filter(x => x.family === 'native-menus');
assert.equal(entries.length, 189);
const sourcePath = entries[0].sourceCoordinates.sourcePath;
const source = fs.readFileSync(path.join(root, '.analysis-local/baselines', baseline, 'extracted', sourcePath.replace(/^app\.asar\//, '')));
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
assert.equal(hash(source), entries[0].sourceCoordinates.sourceHash);
const sourceHash = hash(source);
const parserPath = path.join(root, '.analysis-local/global-state-storage-work/tooling/node_modules/@babel/parser/lib/index.js');
const parser = createRequire(import.meta.url)(parserPath);
const skip = new Set(['loc', 'extra', 'comments', 'leadingComments', 'trailingComments', 'innerComments', 'tokens', 'errors']);
function visit(n, fn) {
  if (!n || typeof n !== 'object') return;
  if (typeof n.type === 'string') fn(n);
  for (const [k, v] of Object.entries(n)) {
    if (skip.has(k)) continue;
    if (Array.isArray(v)) v.forEach(x => visit(x, fn));
    else if (v && typeof v === 'object') visit(v, fn);
  }
}
const key = p => p.computed ? null : p.key?.name ?? p.key?.value;
const literal = n => n?.type === 'StringLiteral' || n?.type === 'BooleanLiteral' || n?.type === 'NumericLiteral'
  ? {kind: 'literal', value: n.value} : n?.type === 'TemplateLiteral' && n.expressions.length === 0
    ? {kind: 'literal', value: n.quasis[0].value.cooked} : {kind: 'dynamic'};
const index = new Map(menu.contractRecordIndex.map(x => [x.contractId, x]));
const pointer = p => p.slice(1).split('/').reduce((v, k) => v[k], menu);
const ownerMap = new Map(entries.map(x => [x.lexicalOwner.name, x.lexicalOwner]));
const owners = [];
const nodes = new Map();
let parsedNodes = 0;
for (const [name, location] of ownerMap) {
  const bytes = source.subarray(location.byteRange.start, location.byteRange.endExclusive);
  assert.equal(hash(bytes), location.spanHash);
  const prefix = location.nodeType === 'VariableDeclarator' ? 'const ' : '';
  const text = prefix + bytes.toString('utf8') + (prefix ? ';' : '');
  const ast = parser.parse(text, {sourceType: 'module'});
  const owner = prefix ? ast.program.body[0].declarations[0] : ast.program.body[0];
  assert.equal(owner.type, location.nodeType);
  const locate = n => {
    const start = location.byteRange.start + Buffer.byteLength(text.slice(prefix.length, n.start));
    const endExclusive = location.byteRange.start + Buffer.byteLength(text.slice(prefix.length, n.end));
    return {sourcePath, sourceHash, byteRange: {start, endExclusive}, spanHash: hash(source.subarray(start, endExclusive)), nodeType: n.type};
  };
  visit(owner, n => {
    parsedNodes++;
    const loc = locate(n);
    const k = loc.byteRange.start + ':' + loc.byteRange.endExclusive + ':' + n.type;
    // Shorthand properties may expose the same Identifier as both key and value.
    if (!nodes.has(k)) nodes.set(k, {node: n, loc, ownerName: name, expression: x => text.slice(x.start, x.end)});
  });
  owners.push({name, ...location, parseWrapper: prefix ? 'const <complete VariableDeclarator>;' : 'complete FunctionDeclaration'});
}
const roleCounts = {}, originCounts = {};
const rows = entries.map(entry => {
  const c = entry.sourceCoordinates;
  const types = entry.entryKind === 'application-menu-factory' ? ['FunctionDeclaration']
    : ['native-menu-api', 'application-menu-consumer'].includes(entry.entryKind)
      ? ['CallExpression', 'OptionalCallExpression', 'NewExpression'] : ['ObjectExpression'];
  const matches = types.map(type => nodes.get(c.byteRange.start + ':' + c.byteRange.endExclusive + ':' + type)).filter(Boolean);
  assert.equal(matches.length, 1, entry.entryId);
  const found = matches[0];
  assert(found, entry.entryId);
  assert.equal(found.loc.spanHash, c.spanHash);
  const ci = index.get(entry.entryId);
  assert(ci);
  assert.equal(ci.coordinates.start, c.byteRange.start);
  assert.equal(ci.coordinates.endExclusive, c.byteRange.endExclusive);
  assert.equal(ci.coordinates.sourceHash, c.sourceHash);
  const saved = pointer(ci.jsonPointer);
  const node = found.node;
  let role, shape = null;
  if (entry.entryKind === 'application-menu-factory') role = 'application-menu-assembly-factory';
  else if (entry.entryKind === 'application-menu-consumer') role = 'application-menu-factory-consumer';
  else if (entry.entryKind === 'native-menu-api') {
    assert(['CallExpression', 'OptionalCallExpression', 'NewExpression'].includes(node.type));
    role = saved.api.endsWith('buildFromTemplate') ? 'native-template-construction-call'
      : saved.api.endsWith('MenuItem') ? 'native-item-construction-call' : 'native-menu-installation-call';
  } else {
    assert.equal(node.type, 'ObjectExpression');
    const props = node.properties.filter(p => p.type !== 'SpreadElement');
    const keys = props.map(key);
    assert.deepEqual([...keys].sort(), [...saved.properties].sort());
    const get = k => props.find(p => key(p) === k);
    const click = get('click'), roleProp = get('role'), submenu = get('submenu');
    const value = roleProp ? literal(roleProp.value) : null;
    if (entry.entryKind === 'native-menu-generator-options') role = 'menu-generator-options';
    else if (roleProp && value.kind === 'dynamic') role = 'dynamic-menu-item-adapter';
    else if (click) role = 'custom-action-schema';
    else if (roleProp) role = submenu ? 'runtime-role-with-submenu' : 'runtime-role-item';
    else { assert(submenu); role = 'submenu-container'; }
    if (value?.kind === 'literal') assert.equal(value.value, saved.values.role.value);
    shape = {ownPropertyKeys: keys, spreadCount: node.properties.length - props.length,
      click: click ? {nodeType: click.type === 'ObjectMethod' ? click.type : click.value.type, expression: found.expression(click)} : null,
      runtimeRole: roleProp ? {...value, expression: found.expression(roleProp.value)} : null,
      submenu: !!submenu};
  }
  const origin = found.ownerName === 'R$e' ? 'electron-context-menu-selected-factory-candidate' : 'application-or-runtime-adapter';
  roleCounts[role] = (roleCounts[role] || 0) + 1;
  originCounts[origin] = (originCounts[origin] || 0) + 1;
  return {entryId: entry.entryId, entryKind: entry.entryKind, ...found.loc, ownerName: found.ownerName,
    contractPointer: ci.jsonPointer, primaryEvidenceId: ci.primaryEvidenceId, sourceRole: role, origin,
    shape, callbackStatus: saved.callback?.status ?? null,
    callbackCalls: saved.callback?.calls?.map(x => ({expression: x.expression, status: x.status, evidenceId: x.evidenceId})) ?? [],
    runtimeRole: saved.values?.role ?? null,
    conditions: saved.conditions ?? [], registrationUses: saved.registrationUses ?? [],
    productMode: 'unknown', actualRuntimeVerified: false, functionalEntryFullyResolved: false};
});
// Compare one upstream default-action object with the candidate bundle factory.
const upstreamPath = path.join(work, 'upstream/v4.1.2/index.js');
const upstreamBytes = fs.readFileSync(upstreamPath);
const upstreamAst = parser.parse(upstreamBytes.toString('utf8'), {sourceType: 'module'});
function defaultActions(ast) {
  const candidates = [];
  visit(ast, n => {
    if (n.type !== 'ObjectExpression') return;
    const keys = n.properties.map(key);
    if (keys.includes('learnSpelling') && keys.includes('copyVideoAddress')) candidates.push(n);
  });
  assert.equal(candidates.length, 1);
  return candidates[0];
}
function actionFingerprint(object) {
  return object.properties.map(p => {
    let item = p.value;
    if (item.type === 'CallExpression') item = item.arguments[0];
    else if (item.type === 'ArrowFunctionExpression') item = item.body;
    assert.equal(item.type, 'ObjectExpression');
    const prop = k => item.properties.find(p => key(p) === k);
    const click = prop('click');
    return {action: key(p), propertyKeys: item.properties.map(key).sort(),
      id: prop('id') ? literal(prop('id').value) : null,
      label: prop('label') ? literal(prop('label').value) : null,
      clickArity: click ? (click.type === 'ObjectMethod' ? click.params.length : click.value.params.length) : null};
  });
}
const targetOwner = owners.find(x => x.name === 'R$e');
const targetNode = nodes.get(targetOwner.byteRange.start + ':' + targetOwner.byteRange.endExclusive + ':' + targetOwner.nodeType).node;
const targetFingerprint = actionFingerprint(defaultActions(targetNode));
const referenceFingerprint = actionFingerprint(defaultActions(upstreamAst));
assert.deepEqual(targetFingerprint, referenceFingerprint);
assert.equal(targetFingerprint.length, 19);
const comparisons = {
  targetFactory: targetOwner, upstream: {path: upstreamPath, bytes: upstreamBytes.length, sha256: hash(upstreamBytes),
    url: 'https://github.com/sindresorhus/electron-context-menu/blob/v4.1.2/index.js', ref: 'v4.1.2'},
  actionFingerprint: targetFingerprint, matchedActionRecords: targetFingerprint.length,
  fingerprintFields: ['action', 'propertyKeys', 'id', 'label', 'clickArity'],
  inference: 'The declared package plus matching selected-factory action fingerprints supports external-library ownership of this factory. It does not establish exact bundled version, unmodified upstream code, or runtime equivalence.',
  actualInstalledVersion: 'unknown', modificationStatus: 'unknown', semanticEquivalenceClaimed: false,
};
assert.equal(rows.filter(x => x.origin === 'electron-context-menu-selected-factory-candidate').length, 20);
const result = {schemaVersion: 1, baselineId: baseline, sourcePath, sourceHash: hash(source), owners, rows,
  parser: {path: parserPath, sha256: hash(fs.readFileSync(parserPath))},
  parseScope: '14 complete selected lexical owners; free enclosing-Program bindings rely on the saved complete-Program entry-family contracts, not these fragment parses.',
  upstreamComparison: comparisons,
  counts: {legacyRecordsReviewed: rows.length, selectedOwnerParses: owners.length, parsedNodes,
    originalFullProgramsReparsed: 0, roleCounts, originCounts},
  targetCodeExecuted: false, newModelSubmissions: 0, newClientRuns: 0};
fs.mkdirSync(work, {recursive: true});
fs.writeFileSync(path.join(work, 'menu-roles.json'), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify(result.counts));
