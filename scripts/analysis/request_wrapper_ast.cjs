// Static-only provenance scan. Target JavaScript is parsed, never evaluated.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const workspace = path.resolve(__dirname, '../..');
const parserPath = process.argv[2];
const parser = parserPath ? require(path.resolve(parserPath)) : require('@babel/parser');
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const baseline = JSON.parse(fs.readFileSync(path.join(workspace, '.analysis-local/current-baseline.json'), 'utf8'));
const root = path.resolve(workspace, baseline.extractedDirectory);
const published = path.join(workspace, 'analysis', baseline.baselineId);
const candidates = JSON.parse(fs.readFileSync(path.join(published, 'app-server-methods.json'), 'utf8'));
const inventory = JSON.parse(fs.readFileSync(path.join(published, 'files.json'), 'utf8'));
const inventoryFiles = inventory.archiveFiles;
const selected = new Set(candidates.filter(c => c.callForm === 'sendRequest').map(c => c.sourcePath));
for (const name of fs.readdirSync(path.join(root, 'webview/assets'))) {
  if (/^(rpc-|app-main-|app-initial-|local-conversation|pending-local-conversation).*\.js$/.test(name)) selected.add('app.asar/webview/assets/' + name);
}
const outputDir = path.join(workspace, '.analysis-local/review-work');
const evidence = [], files = [], failures = [];
const skipKeys = new Set(['loc','start','end','extra','comments','tokens','leadingComments','trailingComments','innerComments','errors']);
const functionTypes = new Set(['FunctionDeclaration','FunctionExpression','ArrowFunctionExpression','ObjectMethod','ClassMethod','ClassPrivateMethod']);
const classTypes = new Set(['ClassDeclaration','ClassExpression']);
const propertyName = node => node?.type === 'Identifier' ? node.name : node?.type === 'StringLiteral' ? node.value : null;
function expression(node) {
  if (!node) return null;
  if (node.type === 'Identifier') return node.name;
  if (node.type === 'ThisExpression') return 'this';
  if (node.type === 'Super') return 'super';
  if (node.type === 'MemberExpression' || node.type === 'OptionalMemberExpression') return expression(node.object) + '.' + (propertyName(node.property) ?? '[computed]');
  if (node.type === 'CallExpression' || node.type === 'OptionalCallExpression') return expression(node.callee) + '()';
  if (node.type === 'NewExpression') return 'new ' + expression(node.callee) + '()';
  if (node.type === 'AwaitExpression') return 'await ' + expression(node.argument);
  return '[' + node.type + ']';
}
function patternNames(node, result = []) {
  if (!node) return result;
  if (node.type === 'Identifier') result.push(node.name);
  else if (node.type === 'RestElement') patternNames(node.argument, result);
  else if (node.type === 'AssignmentPattern') patternNames(node.left, result);
  else if (node.type === 'ObjectPattern') for (const p of node.properties) patternNames(p.type === 'RestElement' ? p.argument : p.value, result);
  else if (node.type === 'ArrayPattern') for (const p of node.elements) patternNames(p, result);
  return result;
}
for (const sourcePath of [...selected].sort()) {
  const rel = sourcePath.replace(/^app\.asar\//, '');
  try {
    const physical = path.resolve(root, rel);
    if (!physical.startsWith(root + path.sep)) throw new Error('Escaped frozen root');
    const bytes = fs.readFileSync(physical), sourceHash = sha(bytes), text = bytes.toString('utf8');
    const byteOffsets = new Uint32Array(text.length + 1);
    for (let i = 0, offset = 0; i < text.length;) {
      byteOffsets[i] = offset;
      const unit = text.charCodeAt(i);
      if (unit >= 0xD800 && unit <= 0xDBFF && i + 1 < text.length && text.charCodeAt(i + 1) >= 0xDC00 && text.charCodeAt(i + 1) <= 0xDFFF) {
        byteOffsets[i + 1] = offset + 3; offset += 4; i += 2;
      } else { offset += unit < 0x80 ? 1 : unit < 0x800 ? 2 : 3; i += 1; }
      byteOffsets[i] = offset;
    }
    const recorded = inventoryFiles.find(row => row.sourcePath === sourcePath || row.path === rel || row.path === sourcePath);
    const expectedHash = recorded?.sha256 || recorded?.sourceHash;
    if (expectedHash && expectedHash !== sourceHash) throw new Error('Inventory source hash differs');
    const ast = parser.parse(text, { sourceType: 'unambiguous', plugins: ['jsx'], allowReturnOutsideFunction: true });
    const parents = new WeakMap(), scopes = new WeakMap(), nodes = [], scopeList = [];
    const newScope = (type, parent, owner) => { const s = { id: scopeList.length, type, parent, owner, bindings: new Map() }; scopeList.push(s); return s; };
    const register = (scope, name, node, type, details = {}) => {
      const prior = scope.bindings.get(name);
      if (prior) { prior.redeclarations.push(node); return prior; }
      const binding = { name, node, type, scope, details, redeclarations: [] };
      scope.bindings.set(name, binding); return binding;
    };
    function walk(node, parent, parentScope) {
      if (!node || typeof node !== 'object' || !node.type) return;
      parents.set(node, parent); nodes.push(node);
      let scope = parentScope;
      if (node.type === 'Program') scope = newScope('program', null, node);
      else if (functionTypes.has(node.type)) {
        if (node.type === 'FunctionDeclaration' && node.id) register(parentScope, node.id.name, node, 'function');
        scope = newScope('function', parentScope, node);
        if (node.id) register(scope, node.id.name, node, 'function-self');
        for (const param of node.params) for (const name of patternNames(param)) register(scope, name, param, 'parameter');
      } else if (classTypes.has(node.type)) {
        if (node.type === 'ClassDeclaration' && node.id) register(parentScope, node.id.name, node, 'class');
        scope = newScope('class', parentScope, node);
        if (node.id) register(scope, node.id.name, node, 'class-self');
      } else if (node.type === 'BlockStatement' || node.type === 'CatchClause') {
        scope = newScope('block', parentScope, node);
        if (node.type === 'CatchClause') for (const name of patternNames(node.param)) register(scope, name, node.param, 'catch-parameter');
      }
      scopes.set(node, scope);
      if (node.type === 'VariableDeclaration') {
        let target = scope;
        if (node.kind === 'var') while (target.parent && !['function','program'].includes(target.type)) target = target.parent;
        for (const decl of node.declarations) for (const name of patternNames(decl.id)) register(target, name, decl, 'variable', { kind: node.kind, initializer: expression(decl.init) });
      }
      if (node.type === 'ImportDeclaration') for (const spec of node.specifiers) register(scope, spec.local.name, spec, 'import', { source: node.source.value, imported: spec.type === 'ImportSpecifier' ? propertyName(spec.imported) : spec.type });
      for (const [key, value] of Object.entries(node)) {
        if (skipKeys.has(key)) continue;
        if (Array.isArray(value)) for (const child of value) walk(child, node, scope);
        else if (value && typeof value === 'object') walk(value, node, scope);
      }
    }
    walk(ast.program, null, null);
    const evidenceKeys = new Map();
    function span(node, role) {
      if (!node) return null;
      const start = byteOffsets[node.start], endExclusive = byteOffsets[node.end];
      const key = start + ':' + endExclusive + ':' + role;
      if (evidenceKeys.has(key)) return evidenceKeys.get(key);
      const id = 'REQUEST-WRAPPER-AST-' + String(evidence.length + 1).padStart(5, '0');
      evidence.push({ id, baselineId: baseline.baselineId, sourcePath, sourceHash,
        locator: { kind: 'byte-range', start, endExclusive }, spanSha256: sha(bytes.subarray(start, endExclusive)),
        locatorScope: role, nodeType: node.type, verificationStatus: 'static-locator-confirmed; target-code-not-executed',
        claimScope: 'Complete AST node locator only; receiver identity requires reviewed binding/assignment chain.' });
      evidenceKeys.set(key, id); return id;
    }
    function ancestors(node, types) { let p = parents.get(node); while (p && !types.has(p.type)) p = parents.get(p); return p; }
    function binding(name, node) { let scope = scopes.get(node); while (scope) { if (scope.bindings.has(name)) return scope.bindings.get(name); scope = scope.parent; } return null; }
    function receiverRoot(node) { while (node && ['MemberExpression','OptionalMemberExpression','CallExpression','OptionalCallExpression','AwaitExpression'].includes(node.type)) node = node.type === 'AwaitExpression' ? node.argument : node.type.endsWith('CallExpression') ? node.callee : node.object; return node; }
    const imports = nodes.filter(n => n.type === 'ImportDeclaration').map(n => ({ source: n.source.value, evidenceId: span(n, 'complete-import-declaration'), bindings: n.specifiers.map(s => ({ local: s.local.name, imported: s.type === 'ImportSpecifier' ? propertyName(s.imported) : s.type })) }));
    const exports = nodes.filter(n => ['ExportNamedDeclaration','ExportDefaultDeclaration'].includes(n.type)).map(n => ({ source: n.source?.value ?? null, evidenceId: span(n, 'complete-export-declaration'), bindings: n.specifiers?.map(s => ({ local: propertyName(s.local), exported: propertyName(s.exported) })) ?? [], declared: n.declaration?.id?.name ?? null }));
    const assignmentsByName = new Map();
    for (const node of nodes) if (node.type === 'AssignmentExpression' && node.left.type === 'Identifier') {
      const list = assignmentsByName.get(node.left.name) ?? [];
      list.push(node); assignmentsByName.set(node.left.name, list);
    }
    const calls = [];
    for (const node of nodes) {
      if (!['CallExpression','OptionalCallExpression'].includes(node.type)) continue;
      const callee = node.callee;
      if (!['MemberExpression','OptionalMemberExpression'].includes(callee?.type) || propertyName(callee.property) !== 'sendRequest') continue;
      const first = node.arguments[0];
      const method = first?.type === 'StringLiteral' ? first.value : first?.type === 'TemplateLiteral' && first.expressions.length === 0 ? first.quasis[0].value.cooked : null;
      const rootNode = receiverRoot(callee.object), bound = rootNode?.type === 'Identifier' ? binding(rootNode.name, node) : null;
      const enclosing = ancestors(node, functionTypes), ownerClass = ancestors(node, classTypes);
      const assignments = bound ? (assignmentsByName.get(bound.name) ?? []).filter(n => binding(bound.name, n) === bound).map(n => ({ rhs: expression(n.right), evidenceId: span(n, 'complete-assignment-expression') })) : [];
      calls.push({ method, receiver: expression(callee.object), receiverRoot: expression(rootNode),
        callEvidenceId: span(node, 'complete-call-expression'), enclosingFunctionEvidenceId: span(enclosing, 'complete-enclosing-function'),
        enclosingFunctionName: enclosing?.id?.name ?? propertyName(enclosing?.key), enclosingClassEvidenceId: span(ownerClass, 'complete-enclosing-class'), enclosingClassName: ownerClass?.id?.name ?? null,
        rootBinding: bound ? { name: bound.name, type: bound.type, details: bound.details, evidenceId: span(bound.node, 'complete-lexical-binding'), scopeOwnerEvidenceId: span(bound.scope.owner, 'complete-binding-scope-owner'), assignments,
          redeclarationEvidenceIds: bound.redeclarations.map(n => span(n, 'complete-binding-redeclaration')) } : null });
    }
    const definitions = nodes.filter(n => (['ClassMethod','ObjectMethod'].includes(n.type) && propertyName(n.key) === 'sendRequest') || (n.type === 'AssignmentExpression' && ['MemberExpression','OptionalMemberExpression'].includes(n.left.type) && propertyName(n.left.property) === 'sendRequest')).map(n => ({ nodeType: n.type, evidenceId: span(n, 'complete-sendRequest-definition'), ownerClassName: ancestors(n, classTypes)?.id?.name ?? null, ownerClassEvidenceId: span(ancestors(n, classTypes), 'complete-enclosing-class') }));
    const importedPropertyAssignments = nodes.filter(n => n.type === 'AssignmentExpression' && n.left.type === 'MemberExpression' && n.left.object.type === 'ThisExpression').map(n => ({ property: propertyName(n.left.property), rhs: expression(n.right), evidenceId: span(n, 'complete-this-property-assignment'), enclosingFunctionEvidenceId: span(ancestors(n, functionTypes), 'complete-enclosing-function'), ownerClassName: ancestors(n, classTypes)?.id?.name ?? null }));
    files.push({ sourcePath, sourceHash, bytes: bytes.length, inventoryHashVerified: !!expectedHash, literalCandidateCount: candidates.filter(c => c.callForm === 'sendRequest' && c.sourcePath === sourcePath).length,
      astSendRequestCount: calls.length, astLiteralMethodCount: calls.filter(c => c.method !== null).length,
      imports, exports, calls, sendRequestDefinitions: definitions, thisPropertyAssignments: importedPropertyAssignments });
    process.stdout.write(JSON.stringify({ parsedSource: sourcePath, astCalls: calls.length }) + '\n');
  } catch (error) { failures.push({ sourcePath, name: error.name, message: error.message }); }
}
const result = { baselineId: baseline.baselineId, archiveSha256: baseline.archiveSha256, generatedAtUtc: new Date().toISOString(),
  method: 'Babel static parse plus own lexical scopes/import exports/class/property-assignment locators; no target code evaluated',
  script: { path: path.relative(workspace, __filename), sha256: sha(fs.readFileSync(__filename)), parserPathSupplied: !!parserPath, parserFileSha256: parserPath ? sha(fs.readFileSync(path.resolve(parserPath))) : null },
  scope: { previousLiteralSendRequestCandidates: candidates.filter(c => c.callForm === 'sendRequest').length, previousDistinctLiteralMethods: new Set(candidates.filter(c => c.callForm === 'sendRequest').map(c => c.method)).size,
    previousCandidateSourceFiles: new Set(candidates.filter(c => c.callForm === 'sendRequest').map(c => c.sourcePath)).size, selectedSourceFiles: selected.size, parsedSourceFiles: files.length,
    astSendRequestCalls: files.reduce((n,f) => n + f.astSendRequestCount,0), astLiteralMethodCalls: files.reduce((n,f) => n + f.astLiteralMethodCount,0),
    selection: 'All published sendRequest candidate files plus rpc/app-main/app-initial/local-conversation/pending-local-conversation assets; not all archive members or all dynamic request paths' },
  failures, files, limitations: ['Lexical locators are evidence, not automatic receiver identity classification.', 'Cross-module, dynamic dispatch, callbacks, mutation, inheritance and dependency injection need reviewed chains.', 'No UI, IPC or app-server execution or feature coverage inferred.'] };
fs.mkdirSync(outputDir, { recursive: true });
fs.writeFileSync(path.join(outputDir, 'request-wrapper-ast.json'), JSON.stringify(result, null, 2) + '\n');
fs.writeFileSync(path.join(outputDir, 'request-wrapper-ast-evidence.jsonl'), evidence.map(e => JSON.stringify(e)).join('\n') + '\n');
console.log(JSON.stringify({ ...result.scope, evidenceCount: evidence.length, failures }));
