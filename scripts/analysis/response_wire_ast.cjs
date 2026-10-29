// Frozen-code data extraction. Never import or execute application modules.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const [root, baseline, filename, output, classNames, methodNames] = process.argv.slice(2);
if (fs.existsSync(output)) throw Error('Preserve existing extraction');
const wantedClasses = new Set(classNames.split(','));
const wantedMethods = new Set(methodNames.split(','));
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const bytes = fs.readFileSync(path.join(root, '.analysis-local/baselines', baseline, 'extracted', filename));
const sourceHash = sha(bytes);
const sourcePath = 'app.asar/' + filename;
const registry = JSON.parse(fs.readFileSync(path.join(root, 'analysis', baseline, 'files.json')));
const expected = registry.archiveFiles.find(file => file.sourcePath === sourcePath);
if (!expected || expected.sha256 !== sourceHash || expected.bytes !== bytes.length) throw Error('Frozen input mismatch');
const text = bytes.toString('utf8');
const parserPath = path.join(root, '.analysis-local/global-state-storage-work/tooling/node_modules/@babel/parser/lib/index.js');
const parser = require(parserPath);
const startedAtUtc = new Date().toISOString();
const ast = parser.parse(text, {sourceType: 'unambiguous'});
const skip = new Set(['loc', 'start', 'end', 'extra', 'comments', 'tokens', 'leadingComments', 'trailingComments', 'innerComments', 'errors']);
const functions = new Set(['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression', 'ClassMethod', 'ClassPrivateMethod', 'ObjectMethod']);
const nodes = [], parents = new WeakMap(), scopes = new WeakMap();
let scopeCount = 0;
function scope(parent, node, kind) {scopeCount++; return {parent, node, kind, bindings: new Map()};}
function bind(pattern, owner, kind, declaration) {
  if (!pattern) return;
  if (pattern.type === 'Identifier') owner.bindings.set(pattern.name, [...owner.bindings.get(pattern.name) || [], {identifier: pattern, kind, declaration}]);
  else if (pattern.type === 'AssignmentPattern') bind(pattern.left, owner, kind, declaration);
  else if (pattern.type === 'RestElement') bind(pattern.argument, owner, kind, declaration);
  else if (pattern.type === 'ArrayPattern') pattern.elements.forEach(p => bind(p, owner, kind, declaration));
  else if (pattern.type === 'ObjectPattern') pattern.properties.forEach(p => bind(p.type === 'RestElement' ? p.argument : p.value, owner, kind, declaration));
}
function build(node, parent, current) {
  nodes.push(node); if (parent) parents.set(node, parent);
  let owner = current;
  if (node.type === 'Program') owner = scope(null, node, 'Program');
  else if (functions.has(node.type)) {
    if (node.type === 'FunctionDeclaration' && node.id) bind(node.id, current, 'function', node);
    owner = scope(current, node, 'function'); node.params.forEach(p => bind(p, owner, 'parameter', p));
    if (node.type === 'FunctionExpression' && node.id) bind(node.id, owner, 'self', node);
  } else if (['ClassDeclaration', 'ClassExpression'].includes(node.type)) {
    if (node.type === 'ClassDeclaration' && node.id) bind(node.id, current, 'class', node);
    owner = scope(current, node, 'class'); if (node.id) bind(node.id, owner, 'self', node);
  } else if (['BlockStatement', 'CatchClause', 'ForStatement', 'ForInStatement', 'ForOfStatement', 'SwitchStatement', 'StaticBlock'].includes(node.type)) {
    owner = scope(current, node, node.type); if (node.type === 'CatchClause') bind(node.param, owner, 'catch', node.param);
  }
  scopes.set(node, owner);
  if (node.type === 'VariableDeclaration') {
    let target = owner;
    if (node.kind === 'var') while (!['Program', 'function'].includes(target.kind)) target = target.parent;
    node.declarations.forEach(d => bind(d.id, target, node.kind, d));
  }
  if (node.type === 'ImportDeclaration') node.specifiers.forEach(s => bind(s.local, owner, 'import', s));
  for (const [key, value] of Object.entries(node)) {
    if (skip.has(key)) continue;
    if (Array.isArray(value)) {for (const child of value) if (child && typeof child.type === 'string') build(child, node, owner);}
    else if (value && typeof value.type === 'string') build(value, node, owner);
  }
}
build(ast.program, null, null);
const deltas = [{end: 0, delta: 0}]; let delta = 0;
for (let index = 0; index < text.length;) {
  const cp = text.codePointAt(index), width = cp > 0xffff ? 2 : 1;
  if (cp > 127) {delta += (cp <= 0x7ff ? 2 : cp <= 0xffff ? 3 : 4) - width; deltas.push({end: index + width, delta});}
  index += width;
}
function offset(index) {
  let lo = 0, hi = deltas.length;
  while (lo < hi) {const mid = (lo + hi) >>> 1; if (deltas[mid].end <= index) lo = mid + 1; else hi = mid;}
  return index + deltas[lo - 1].delta;
}
const locations = new WeakMap();
function loc(node) {
  if (!locations.has(node)) {
    const start = offset(node.start), endExclusive = offset(node.end);
    locations.set(node, {sourcePath, sourceHash, byteRange: {start, endExclusive}, spanSha256: sha(bytes.subarray(start, endExclusive)), nodeType: node.type});
  }
  return locations.get(node);
}
const expr = node => node ? text.slice(node.start, node.end) : null;
const key = node => node?.type === 'Identifier' ? node.name : node?.type === 'StringLiteral' ? node.value : node?.type === 'PrivateName' ? '#' + node.id.name : null;
function resolve(identifier) {
  let owner = scopes.get(identifier);
  while (owner) {if (owner.bindings.has(identifier.name)) return {scope: owner, definitions: owner.bindings.get(identifier.name)}; owner = owner.parent;}
  return null;
}
function binding(identifier) {
  const found = resolve(identifier);
  return found ? {scopeKind: found.scope.kind, scope: loc(found.scope.node), definitions: found.definitions.map(d => ({kind: d.kind, declaration: loc(d.declaration)}))} : null;
}
function nameOfClass(node) {
  const parent = parents.get(node);
  return node.id?.name ?? (parent?.type === 'VariableDeclarator' ? key(parent.id) : parent?.type === 'AssignmentExpression' ? key(parent.left) : null);
}
const classes = nodes.filter(n => ['ClassDeclaration', 'ClassExpression'].includes(n.type));
const classIndex = classes.map(node => ({name: nameOfClass(node), ...loc(node),
  members: node.body.body.map(member => ({name: key(member.key), ...loc(member), valueType: member.value?.type ?? null}))}));
const selected = [];
for (const owner of classes) {
  const name = nameOfClass(owner);
  if (!wantedClasses.has(name)) continue;
  for (const member of owner.body.body) {
    const memberName = key(member.key);
    if (memberName === 'constructor' || wantedMethods.has(memberName) || member.type === 'ClassProperty') {
      selected.push({name: `${name}.${memberName}`, owner: name, node: member});
    }
  }
}
for (const node of nodes) {
  if (node.type === 'SwitchCase') {
    const label = node.test?.type === 'StringLiteral' ? node.test.value : node.test?.type === 'TemplateLiteral' && node.test.expressions.length === 0 ? node.test.quasis[0].value.cooked : null;
    if (label === 'mcp-response') selected.push({name: 'case-mcp-response', node});
  }
}
if (!selected.length) throw Error('No selected units');
fs.mkdirSync(output, {recursive: true});
const units = selected.map((unit, index) => {
  const location = loc(unit.node), sourceFilename = `${String(index + 1).padStart(3, '0')}-${unit.name.replaceAll('#', 'private-')}.txt`;
  fs.writeFileSync(path.join(output, sourceFilename), bytes.subarray(location.byteRange.start, location.byteRange.endExclusive));
  return {name: unit.name, owner: unit.owner ?? null, ...location, sourceFilename};
});
const uses = [];
for (const unit of selected) for (const node of nodes) {
  if (node.start < unit.node.start || node.end > unit.node.end) continue;
  if (node.type === 'CallExpression' && node.callee.type === 'Identifier') uses.push({unit: unit.name, kind: 'call', name: node.callee.name, ...loc(node), binding: binding(node.callee)});
  if (node.type === 'NewExpression' && node.callee.type === 'Identifier') uses.push({unit: unit.name, kind: 'new', name: node.callee.name, ...loc(node), binding: binding(node.callee)});
}
const declarations = nodes.filter(n => n.type === 'FunctionDeclaration' || n.type === 'VariableDeclarator').map(n => ({name: key(n.id), ...loc(n), binding: n.id?.type === 'Identifier' ? binding(n.id) : null}));
const newExpressions = nodes.filter(n => n.type === 'NewExpression').map(n => ({callee: expr(n.callee), ...loc(n), arguments: n.arguments.map(expr), binding: n.callee.type === 'Identifier' ? binding(n.callee) : n.callee.object?.type === 'Identifier' ? binding(n.callee.object) : null}));
const exportBindings = nodes.filter(n => n.type === 'CallExpression' && n.callee.type === 'MemberExpression' && n.callee.object.type === 'Identifier' && n.callee.object.name === 'Object' && key(n.callee.property) === 'defineProperty' && n.arguments[0]?.type === 'Identifier' && n.arguments[0].name === 'exports').map(n => ({exported: n.arguments[1]?.value, expression: expr(n), ...loc(n)}));
const requires = nodes.filter(n => n.type === 'CallExpression' && n.callee.type === 'Identifier' && n.callee.name === 'require' && n.arguments[0]?.type === 'StringLiteral').map(n => ({module: n.arguments[0].value, ...loc(n), parent: loc(parents.get(n))}));
const result = {schemaVersion: 1, baselineId: baseline, sourcePath, sourceHash, sourceBytes: bytes.length,
  startedAtUtc, completedAtUtc: new Date().toISOString(), fullProgramParsed: true, nodeCount: nodes.length, scopeCount,
  parser: {path: parserPath, sha256: sha(fs.readFileSync(parserPath))}, units, uses, classIndex, declarations, newExpressions, exports: exportBindings, requires,
  targetModuleExecuted: false, originalClientRuns: 0, modelSubmissions: 0};
fs.writeFileSync(path.join(output, 'source-contracts.json'), JSON.stringify(result, null, 2) + '\n');
process.stdout.write(JSON.stringify({sourcePath, selectedUnits: units.length, classes: classIndex.length, declarations: declarations.length}) + '\n');
