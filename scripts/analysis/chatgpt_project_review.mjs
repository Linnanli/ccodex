import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {parse} from '/private/tmp/ccodex-rea-tooling/install/node_modules/@babel/parser/lib/index.js';

// This script parses frozen JavaScript as data. It never imports or executes it.
// Semantic conclusions below are a manual review of these three complete modules.
const root = process.cwd();
const baseline = JSON.parse(fs.readFileSync(path.join(root, '.analysis-local/current-baseline.json'), 'utf8'));
if (baseline.baselineId !== 'codex-26.1007.30912-c5b273322a83') throw Error('Unexpected baseline');
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const targets = [
  ['chatgpt-project-fetch-652f0ab6af18.js', 98, '99f9924646c84a161b23688f78ab4863d41d3359ef7e95a825650615a41aa01e'],
  ['chatgpt-project-settings-dialog-8af3e5dc9374.js', 38918, '71fced71a57cb1c80bf802544ee8f2ce071788e8f18a8319798ec8434eb9b0d3'],
  ['chatgpt-project-sources-35a06ad8e3bc.js', 2522, 'a93a57c9bb1aba3db0d2b6d74d8326d95e52cb5787b76a9c7c198d8760e777e5'],
];
const artifacts = {};
for (const [id, rel] of Object.entries({guards: '.analysis-local/feature-work/route-guard-notes.json', requests: '.analysis-local/review-work/request-wrapper-contracts.json'})) {
  const raw = fs.readFileSync(path.join(root, rel));
  const data = JSON.parse(raw);
  if (data.baselineId !== baseline.baselineId) throw Error('Artifact baseline mismatch');
  artifacts[id] = {artifactPath: rel, artifactSha256: sha(raw), data};
}
let nextEvidence = 1;
const evidence = [], modules = [], runtimeExecuted = false;
const children = node => Object.entries(node).flatMap(([key, value]) => {
  if (['loc', 'start', 'end', 'extra', 'comments', 'leadingComments', 'innerComments', 'trailingComments', 'tokens', 'errors'].includes(key)) return [];
  return Array.isArray(value) ? value.filter(x => x && typeof x.type === 'string').map(x => [key, x]) : value && typeof value.type === 'string' ? [[key, value]] : [];
});
const isFunction = n => ['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression', 'ObjectMethod', 'ClassMethod', 'ClassPrivateMethod'].includes(n.type);
const expr = n => {
  if (!n) return null;
  if (n.type === 'Identifier') return n.name;
  if (n.type === 'StringLiteral' || n.type === 'NumericLiteral' || n.type === 'BooleanLiteral') return JSON.stringify(n.value);
  if (n.type === 'ThisExpression') return 'this';
  if (n.type === 'MemberExpression' || n.type === 'OptionalMemberExpression') return `${expr(n.object)}${n.computed ? `[${expr(n.property)}]` : `.${expr(n.property)}`}`;
  if (n.type === 'SequenceExpression') return n.expressions.map(expr).join(',');
  return n.type;
};
const keyName = n => n?.name ?? n?.value ?? (n?.type === 'TemplateLiteral' && n.expressions.length === 0 ? n.quasis[0].value.cooked : null);
const unwrap = n => n?.type === 'SequenceExpression' ? n.expressions.at(-1) : n;
const rootIdentifier = n => {n = unwrap(n); while (n && ['MemberExpression', 'OptionalMemberExpression'].includes(n.type)) n = n.object; return n?.type === 'Identifier' ? n.name : null;};
const shape = (n, depth = 0) => {
  if (!n) return null;
  const result = {type: n.type};
  if (['StringLiteral', 'NumericLiteral', 'BooleanLiteral'].includes(n.type)) result.value = n.value;
  if (n.type === 'TemplateLiteral' && !n.expressions.length) result.value = n.quasis[0].value.cooked;
  if (n.type === 'Identifier') result.identifier = n.name;
  if (n.type === 'ObjectExpression' && depth < 3) result.properties = n.properties.map(p => p.type === 'SpreadElement' ? {spread: shape(p.argument, depth + 1)} : {key: keyName(p.key), value: shape(p.value, depth + 1)});
  if (n.type === 'ArrayExpression' && depth < 2) result.elements = n.elements.map(x => shape(x, depth + 1));
  return result;
};

for (const [name, expectedBytes, expectedHash] of targets) {
  const absoluteSourcePath = path.join(baseline.extractedDirectory, 'webview/assets', name);
  const raw = fs.readFileSync(absoluteSourcePath), sourceHash = sha(raw), text = raw.toString('utf8');
  if (raw.length !== expectedBytes || sourceHash !== expectedHash) throw Error(`Frozen source changed: ${name}`);
  const sourcePath = `app.asar/webview/assets/${name}`;
  const ast = parse(text, {sourceType: 'module', errorRecovery: false, ranges: true});
  const offsets = new Map(), evidences = new Map(), nodes = [], scopes = [], bindingRecords = [];
  const nodeScope = new WeakMap(), parents = new WeakMap(), functionIds = new WeakMap();
  const byteOffset = offset => {if (!offsets.has(offset)) offsets.set(offset, Buffer.byteLength(text.slice(0, offset))); return offsets.get(offset);};
  const ev = (node, kind = node.type) => {
    const key = `${node.start}:${node.end}:${kind}`;
    if (!evidences.has(key)) {
      const start = byteOffset(node.start), endExclusive = byteOffset(node.end), id = `CGP-E${String(nextEvidence++).padStart(5, '0')}`;
      evidence.push({evidenceId: id, baselineId: baseline.baselineId, sourcePath, sourceHash, range: {kind: 'byte-range', start, endExclusive}, spanHash: sha(raw.subarray(start, endExclusive)), nodeType: node.type, kind});
      evidences.set(key, id);
    }
    return evidences.get(key);
  };
  const scope = (kind, parent, node) => {const s = {id: `${name}:scope-${scopes.length + 1}`, kind, parent, node, bindings: new Map()}; scopes.push(s); return s;};
  const functionScope = s => {while (s.parent && !['function', 'program'].includes(s.kind)) s = s.parent; return s;};
  const bindPattern = (pattern, s, definition, kind, extra = {}, propertyPath = []) => {
    if (!pattern) return;
    if (pattern.type === 'Identifier') {
      const b = {bindingId: `${name}:binding-${bindingRecords.length + 1}`, name: pattern.name, kind, scopeId: s.id, declarationEvidenceId: ev(definition, 'binding-definition'), identifierEvidenceId: ev(pattern, 'binding-identifier'), parameterPropertyPath: propertyPath, ...extra};
      bindingRecords.push(b); const list = s.bindings.get(pattern.name) ?? []; list.push(b); s.bindings.set(pattern.name, list); return;
    }
    if (pattern.type === 'AssignmentPattern') return bindPattern(pattern.left, s, definition, kind, extra, propertyPath);
    if (pattern.type === 'RestElement') return bindPattern(pattern.argument, s, definition, kind, extra, [...propertyPath, '*']);
    if (pattern.type === 'ObjectPattern') for (const p of pattern.properties) bindPattern(p.type === 'RestElement' ? p.argument : p.value, s, definition, kind, extra, [...propertyPath, keyName(p.key) ?? '*']);
    if (pattern.type === 'ArrayPattern') pattern.elements.forEach((p, i) => bindPattern(p, s, definition, kind, extra, [...propertyPath, i]));
  };
  const walk = (node, incoming, parent = null, parentKey = null, fn = null) => {
    parents.set(node, {node: parent, key: parentKey});
    let s = incoming;
    if (node.type === 'Program') s = scope('program', null, node);
    if (node.type === 'FunctionDeclaration' && node.id) bindPattern(node.id, incoming, node, 'function', {callableDefinitionEvidenceId: ev(node, 'complete-function')});
    if (isFunction(node)) {
      s = scope('function', incoming, node); fn = ev(node, 'complete-function'); functionIds.set(node, fn);
      if (node.type === 'FunctionExpression' && node.id) bindPattern(node.id, s, node, 'named-function-expression', {callableDefinitionEvidenceId: fn});
      node.params.forEach(p => bindPattern(p, s, p, 'parameter'));
    } else if (node.type === 'BlockStatement') s = scope('block', incoming, node);
    else if (['ForStatement', 'ForInStatement', 'ForOfStatement', 'CatchClause', 'SwitchStatement'].includes(node.type)) s = scope(node.type, incoming, node);
    nodeScope.set(node, s); nodes.push({node, fn});
    if (node.type === 'CatchClause') bindPattern(node.param, s, node.param, 'catch-parameter');
    if (node.type === 'ImportDeclaration') for (const spec of node.specifiers) bindPattern(spec.local, s, spec, 'import', {moduleSpecifier: node.source.value, importedName: keyName(spec.imported) ?? (spec.type === 'ImportDefaultSpecifier' ? 'default' : '*'), importDeclarationEvidenceId: ev(node, 'complete-import')});
    if (node.type === 'VariableDeclarator') {
      const pk = parent.kind;
      bindPattern(node.id, pk === 'var' ? functionScope(s) : s, node, `variable:${pk}`, {initializer: shape(node.init), callableDefinitionEvidenceId: isFunction(node.init ?? {}) ? ev(node.init, 'complete-function') : null, producerCallee: ['CallExpression', 'OptionalCallExpression', 'NewExpression'].includes(node.init?.type) ? expr(unwrap(node.init.callee)) : null});
    }
    for (const [key, child] of children(node)) walk(child, s, node, key, fn);
  };
  walk(ast.program, null);
  const lookup = (name, s) => {
    if (!name) return {status: 'non-identifier-root'};
    while (s) {const bs = s.bindings.get(name); if (bs?.length) return bs.length === 1 ? {status: 'lexical-bound-in-complete-module', bindingId: bs[0].bindingId} : {status: 'multiple-declarations-in-scope', bindingIds: bs.map(b => b.bindingId)}; s = s.parent;}
    return {status: 'unbound-or-global', name};
  };
  const byBinding = new Map(bindingRecords.map(b => [b.bindingId, b]));
  const imports = ast.program.body.filter(x => x.type === 'ImportDeclaration').map(n => ({moduleSpecifier: n.source.value, evidenceId: ev(n, 'complete-import'), specifiers: n.specifiers.map(s => ({localName: s.local.name, importedName: keyName(s.imported) ?? (s.type === 'ImportDefaultSpecifier' ? 'default' : '*'), evidenceId: ev(s, 'import-specifier'), binding: lookup(s.local.name, nodeScope.get(s))}))}));
  const exports = ast.program.body.filter(x => x.type.startsWith('Export')).map(n => ({type: n.type, evidenceId: ev(n, 'complete-export'), source: n.source?.value ?? null, specifiers: (n.specifiers ?? []).map(s => ({localName: keyName(s.local), exportedName: keyName(s.exported), evidenceId: ev(s, 'export-specifier'), binding: lookup(keyName(s.local), nodeScope.get(s))}))}));
  const functions = nodes.filter(x => isFunction(x.node)).map(({node: n}) => ({name: n.id?.name ?? null, type: n.type, evidenceId: ev(n, 'complete-function'), scopeId: nodeScope.get(n).id, parentFunctionEvidenceId: (() => {let p = parents.get(n)?.node; while (p && !isFunction(p)) p = parents.get(p)?.node; return p ? functionIds.get(p) : null;})(), parameters: n.params.map(shape)}));
  const calls = nodes.filter(x => ['CallExpression', 'OptionalCallExpression', 'NewExpression'].includes(x.node.type)).map(({node: n, fn}) => {
    const callee = unwrap(n.callee), name = rootIdentifier(callee), binding = lookup(name, nodeScope.get(n)), b = byBinding.get(binding.bindingId);
    return {kind: n.type, evidenceId: ev(n, 'complete-call'), enclosingFunctionEvidenceId: fn, calleeExpression: expr(callee), calleeBinding: binding, importedOrigin: b?.kind === 'import' ? {moduleSpecifier: b.moduleSpecifier, importedName: b.importedName, localName: b.name, declarationEvidenceId: b.declarationEvidenceId} : null, receiverProducer: b?.producerCallee ? {calleeExpression: b.producerCallee, bindingDefinitionEvidenceId: b.declarationEvidenceId} : null, arguments: n.arguments.map(shape), mode: 'unknown', runtimeStatus: 'unverified'};
  });
  const assignments = nodes.filter(x => x.node.type === 'AssignmentExpression' && x.node.left.type === 'Identifier').map(({node: n, fn}) => ({evidenceId: ev(n, 'complete-assignment'), name: n.left.name, binding: lookup(n.left.name, nodeScope.get(n)), valueType: n.right.type, producerCallee: ['CallExpression', 'NewExpression'].includes(n.right.type) ? expr(unwrap(n.right.callee)) : null, enclosingFunctionEvidenceId: fn}));
  const findFunction = name => {const n = nodes.find(x => x.node.type === 'FunctionDeclaration' && x.node.id.name === name)?.node; if (!n) throw Error(`Missing function ${name}`); return ev(n, 'complete-function');};
  const select = (predicate, kind) => nodes.filter(x => predicate(x.node)).map(x => ({evidenceId: ev(x.node, kind), nodeType: x.node.type, enclosingFunctionEvidenceId: x.fn}));
  const businessImportedNames = new Set(['iOn', 'oOn', 'sOn', 'fkn', '$wt', 'Ran', 'akn', 'okn', 'gkn', 'ykn', '_kn']);
  const businessCalls = calls.filter(c => businessImportedNames.has(c.importedOrigin?.importedName) || ['q.mutateAsync', 'dt.mutateAsync', 'q.retryAttachment'].includes(c.calleeExpression));
  const review = name.startsWith('chatgpt-project-settings-dialog') ? {
    componentDefinitionEvidenceId: findFunction('Pt'),
    localFoldersProperty: select(n => n.type === 'ObjectProperty' && keyName(n.key) === 'localFolders' && n.value.type === 'ConditionalExpression', 'complete-local-folders-property'),
    connectorPredicateDefinitionEvidenceId: findFunction('Lt'),
    queryEnabledProperties: select(n => n.type === 'ObjectProperty' && keyName(n.key) === 'enabled', 'complete-query-enabled-property'),
    mutationCallbacks: select(n => isFunction(n) && nodes.some(x => x.fn === functionIds.get(n) && x.node.type === 'CallExpression' && ['Ne', 'q.mutateAsync', 'dt.mutateAsync'].includes(expr(unwrap(x.node.callee)))), 'complete-project-mutation-callback'),
    keyBindingDefinitions: bindingRecords.filter(b => ['i', 'a', 'k', 's', 'L', 'R', 'q', 'dt', 'ae', 'V', 'Ne', 'Le', 'Be', 'je', 'Me', 't', 'Ke', 'D'].includes(b.name) && (b.kind === 'import' || b.scopeId === nodeScope.get(nodes.find(x => x.node.type === 'FunctionDeclaration' && x.node.id.name === 'Pt').node.body).id)),
  } : {};
  const lexicalScopes = scopes.map(s => ({scopeId: s.id, kind: s.kind, parentScopeId: s.parent?.id ?? null, completeScopeEvidenceId: ev(s.node, 'complete-lexical-scope')}));
  modules.push({name, sourcePath, absoluteSourcePath, sourceHash, bytes: raw.length, moduleEvidenceId: ev(ast.program, 'complete-module'), parser: {name: '@babel/parser', version: '8.0.4', sourceType: 'module', errorRecovery: false, wholeModule: true}, astCoverage: {programParsed: true, traversalNodes: nodes.length, functions: functions.length, calls: calls.length, imports: imports.length, importSpecifiers: imports.reduce((a, x) => a + x.specifiers.length, 0), exports: exports.length, lexicalBindings: bindingRecords.length, lexicalScopes: lexicalScopes.length}, imports, exports, functions, calls, assignments, lexicalScopes, lexicalBindings: bindingRecords, businessCalls, targetedReview: review, mode: 'unknown', runtimeStatus: 'unverified'});
}

const requestRefs = [], guardRefs = [];
const searchArtifact = (id, predicate) => {
  const found = [], data = artifacts[id].data;
  const rec = (value, pointer = '') => {
    if (value && typeof value === 'object') {
      if (predicate(value)) found.push({artifactPath: artifacts[id].artifactPath, artifactSha256: artifacts[id].artifactSha256, jsonPointer: pointer, evidenceIds: [...new Set([...(value.evidenceIds ?? []), value.evidenceId, value.definitionEvidenceId].filter(Boolean))]});
      for (const [key, child] of Object.entries(value)) rec(child, `${pointer}/${key.replaceAll('~', '~0').replaceAll('/', '~1')}`);
    }
  }; rec(data); return found;
};
requestRefs.push(...searchArtifact('requests', v => typeof v === 'object' && (['iOn', 'rOn', 'sOn', 'fkn', 'akn', 'okn', '$wt'].includes(v.exportedName) || ['iOn', 'rOn', 'sOn', 'fkn', 'akn', 'okn', '$wt'].includes(v.exportName))));
guardRefs.push(...searchArtifact('guards', v => Array.isArray(v.componentNames) && v.componentNames.some(n => ['pss', 'Dos', 'jos', 'sFs'].includes(n))));
// The existing request-wrapper inventory does not cover these three modules.
// Keep its generic wrapper contracts as unlinked references rather than inventing
// a binding from the settings import $wt to the different export TFt.
for (const pointer of ['/sharedExports/TFt', '/contracts/2', '/sharedExports/fN', '/contracts/7']) {
  let value = artifacts.requests.data;
  for (const key of pointer.slice(1).split('/')) value = value[key];
  if (!value) throw Error(`Missing existing wrapper reference ${pointer}`);
  requestRefs.push({artifactPath: artifacts.requests.artifactPath, artifactSha256: artifacts.requests.artifactSha256, jsonPointer: pointer, evidenceIds: value.evidenceIds ?? [], contractId: value.id ?? null, linkToTargetModules: 'not-established'});
}
const callerIndices = [15, 20, 24, 25, 26, 27, 28, 29, 31, 136, 138, 142, 143];
const reusedCallerEvidence = callerIndices.map(index => {
  const source = artifacts.guards.data.evidence[index];
  if (!source) throw Error(`Missing caller evidence ${index}`);
  const record = {...source}; delete record.snippet; delete record.text; delete record.sourceText;
  return {artifactPath: artifacts.guards.artifactPath, artifactSha256: artifacts.guards.artifactSha256, jsonPointer: `/evidence/${index}`, existingEvidence: record, validationLevel: 'reused-existing-artifact; frozen-caller-source-not-reread'};
});
const localModuleImportLinks = [];
for (const importer of modules) for (const imp of importer.imports) {
  const target = modules.find(m => m.name === path.basename(imp.moduleSpecifier));
  if (!target) continue;
  for (const spec of imp.specifiers) {
    const matched = target.exports.flatMap(x => x.specifiers).filter(x => x.exportedName === spec.importedName);
    if (matched.length !== 1) throw Error('Sibling module export not unique');
    localModuleImportLinks.push({status: 'immediate-import-export-boundary-confirmed', from: {sourcePath: importer.sourcePath, sourceHash: importer.sourceHash, localName: spec.localName, importEvidenceId: spec.evidenceId}, to: {sourcePath: target.sourcePath, sourceHash: target.sourceHash, exportedName: matched[0].exportedName, localName: matched[0].localName, exportEvidenceId: matched[0].evidenceId, binding: matched[0].binding}, behaviorClaim: 'Export identity only; runtime initialization and product-mode reachability are not established.'});
  }
}
const settings = modules[1];
const importBoundary = (localName, importedName, role) => {
  const b = settings.lexicalBindings.find(x => x.kind === 'import' && x.name === localName);
  if (b?.importedName !== importedName) throw Error(`Incorrect import mapping: ${localName}`);
  return {role, localName, importedName, moduleSpecifier: b.moduleSpecifier, bindingId: b.bindingId, declarationEvidenceId: b.declarationEvidenceId, callableImplementation: 'outside selected target modules; unknown', linkedUpstreamContractId: null};
};
const externalBoundaries = [importBoundary('Ne', 'iOn', 'project-save-function'), importBoundary('Le', 'oOn', 'project-source-upload-hook'), importBoundary('Be', 'sOn', 'project-source-delete-hook'), importBoundary('je', 'fkn', 'local-folders-eligibility-predicate'), importBoundary('Me', 'gkn', 'project-edit-capability'), importBoundary('t', '$wt', 'safeGet-request-facade'), importBoundary('D', 'Ran', 'project-save-data-query')];
const receiverDataflow = ['q', 'dt'].map(name => {
  const producer = name === 'q' ? 'Le' : 'Be';
  const bindings = settings.lexicalBindings.filter(x => x.name === name && x.producerCallee === producer);
  if (bindings.length !== 1) throw Error(`Ambiguous target receiver ${name}`);
  const record = bindings[0], calls = settings.calls.filter(c => c.calleeBinding.bindingId === record.bindingId && c.calleeExpression.startsWith(`${name}.`));
  const writes = settings.assignments.filter(a => a.binding.bindingId === record.bindingId);
  if (writes.length) throw Error('Receiver is reassigned; dataflow must be reviewed');
  return {receiver: name, variableBindingId: record.bindingId, variableDefinitionEvidenceId: record.declarationEvidenceId, producerImport: externalBoundaries.find(x => x.localName === producer), receiverCalls: calls.map(c => ({calleeExpression: c.calleeExpression, callEvidenceId: c.evidenceId, bindingId: c.calleeBinding.bindingId})), additionalAssignmentsWithinModule: writes.length, status: 'local-initializer-to-receiver-lexical-dataflow-confirmed', implementationClaim: 'The returned object method implementation remains outside the selected modules.'};
});
const output = {
  schemaVersion: 1, baselineId: baseline.baselineId, archiveSha256: baseline.archiveSha256,
  status: 'complete-target-module-ast; manual-mode-boundary-review',
  method: {targetCodeExecution: runtimeExecuted, wholeInitialOrSharedAstScanned: false, targetModuleCount: 3, parser: '@babel/parser 8.0.4', scopeAnalysis: 'Two-pass lexical declaration/reference indexing over each complete module, preserving duplicate declarations and unbound/global identifiers as unknown.', evidenceCoordinates: 'UTF-8 byte offsets, end exclusive; source and complete-node SHA256.', semanticNotes: 'Manual review; selected AST evidence and artifact references are reproducible by this script. No runtime values or feature entitlement were observed.'},
  reproduction: {scriptPath: 'scripts/analysis/chatgpt_project_review.mjs', scriptSha256: sha(fs.readFileSync(new URL(import.meta.url))), command: '/Users/nallylin/.nvm/versions/node/v22.23.2/bin/node scripts/analysis/chatgpt_project_review.mjs', parserModulePath: '/private/tmp/ccodex-rea-tooling/install/node_modules/@babel/parser/lib/index.js'},
  sourceArtifacts: Object.fromEntries(Object.entries(artifacts).map(([k, v]) => [k, {artifactPath: v.artifactPath, artifactSha256: v.artifactSha256, baselineId: v.data.baselineId}])),
  modules, localModuleImportLinks, externalBoundaries, receiverDataflow,
  reusedArtifactReferences: {requests: requestRefs, guards: guardRefs, callerEvidence: reusedCallerEvidence},
  existingRequestInventoryCoverage: {targetModuleFilesPresent: artifacts.requests.data.files.filter(f => modules.some(m => m.sourcePath === f.sourcePath)).length, targetModuleCallsPresent: artifacts.requests.data.calls.filter(c => modules.some(m => m.sourcePath === c.sourcePath)).length, conclusion: 'No immediate target-module callable mapping to the generic existing wrappers is established; the actual $wt, iOn, oOn, sOn and fkn exports require targeted upstream implementation review.'},
  modeBoundaryReview: [],
  unknowns: ['Complete target-module AST does not establish caller mounting, Work/Codex product mode, feature access or server behavior.', 'Import specifiers prove an immediate module/export boundary; existing upstream contract references are needed for external callable semantics.', 'Source labels, translation keys and filenames are not exclusion criteria.'],
  summary: {targetModules: modules.length, sourceBytes: modules.reduce((a, x) => a + x.bytes, 0), evidenceRecords: evidence.length, completeFunctionDefinitions: modules.reduce((a, x) => a + x.functions.length, 0), completeCalls: modules.reduce((a, x) => a + x.calls.length, 0), modeConfirmedExcludedModules: 0, runtimeVerified: 0},
};
// The manual mode notes are intentionally separate from the exhaustive AST inventory.
output.modeBoundaryReview = [
  {reviewId: 'CGP-R01', scope: 'fetch facade', classification: 'unknown; immediate-export-boundary-confirmed', sourcePath: modules[0].sourcePath, evidenceIds: [modules[0].moduleEvidenceId, ...modules[0].imports.map(x => x.evidenceId), ...modules[0].exports.map(x => x.evidenceId)], conclusion: 'The entire 98-byte module imports app-initial.akn as e and okn as t, invokes t, and re-exports e as fetchChatGptProject. There is no local request implementation or product-mode guard. The re-exported implementation must be classified using existing upstream contracts/callers.', confirmedExclude: false, mode: 'unknown', runtimeStatus: 'unverified'},
  {reviewId: 'CGP-R02', scope: 'project settings dialog', classification: 'shared-local-caller-context-candidate; upstream-mutation-implementation-unknown', sourcePath: modules[1].sourcePath, evidenceIds: [modules[1].targetedReview.componentDefinitionEvidenceId, ...modules[1].targetedReview.localFoldersProperty.map(x => x.evidenceId), ...modules[1].businessCalls.map(x => x.evidenceId)], conclusion: 'The exported Pt component binds project save to app-initial.iOn, source upload hook to oOn, deletion hook to sOn, local-folder eligibility to fkn and edit capability to gkn. The same dialog conditionally renders local-folders-section.t under s && L && je(i). Its direct safeGet requests for gizmo details and connector scopes are separate from those imported mutation implementations. A module-name based removal would discard the explicit local-folder branch; upstream local/remote mutation contracts and caller guards are required.', confirmedExclude: false, mode: 'unknown', runtimeStatus: 'unverified'},
  {reviewId: 'CGP-R03', scope: 'project settings direct queries', classification: 'request-facade-boundary-confirmed; backend-and-product-mode-unknown', sourcePath: modules[1].sourcePath, evidenceIds: [modules[1].targetedReview.componentDefinitionEvidenceId, modules[1].targetedReview.connectorPredicateDefinitionEvidenceId, ...modules[1].targetedReview.queryEnabledProperties.map(x => x.evidenceId), ...modules[1].businessCalls.filter(x => x.calleeExpression === 't.safeGet').map(x => x.evidenceId)], conclusion: 'Pt binds t to app-shared.$wt and issues safeGet for /gizmos/{gizmo_id_or_short_url} and /projects/{project_id}/connector_scopes. The details query is enabled only on advanced view when instructions or memory_scope is missing. Connector loading is enabled by Lt(project), whose complete function tests gizmo_snorlax_type == null. These predicates are data/view conditions, not independently proven Work/ChatGPT product-mode gates. The existing TFt/AW wrapper contract does not directly bind the different imported $wt facade.', confirmedExclude: false, mode: 'unknown', runtimeStatus: 'unverified'},
  {reviewId: 'CGP-R04', scope: 'source-formatting helper', classification: 'pure-data-and-rendering-support; callers-required', sourcePath: modules[2].sourcePath, evidenceIds: [modules[2].moduleEvidenceId, ...modules[2].functions.map(x => x.evidenceId), ...modules[2].exports.map(x => x.evidenceId)], conclusion: 'The entire module exports a project_save metadata parser (t/o), timestamp normalizer (n/s), initializer (r/f) and source-type message descriptor table (i/d). It contains no direct network/IPC/project mutation. The settings module imports all four exports for its source rows. Project-save field names and message labels do not establish whether local project support may be removed.', confirmedExclude: false, mode: 'unknown', runtimeStatus: 'unverified'},
];
output.modeBoundaryReview.push({reviewId: 'CGP-R05', scope: 'reused settings callers and dedicated project route', classification: 'shared-caller-context-confirmed; route-guard-does-not-generalize', artifactReferences: guardRefs, callerEvidenceReferences: reusedCallerEvidence.filter(x => [24,25,26,31,138,142,143].some(i => x.jsonPointer === `/evidence/${i}`)), conclusion: 'Existing full pss/Dos/jos evidence traces the same lazy ChatGptProjectSettingsDialog export into shared sidebar project/settings use. pss includes Work and local Codex task context; its dialog condition is ae && Omn(project), without a ChatGPT-only sidebar mode condition. In contrast, dedicated sFs project-route finally uses oZ without allowWork, hence the documented default false guard. Its earlier mapping redirects can pass chatGptProjectId through state. That route cannot be treated as the exclusive caller or exclusion boundary for shared project settings/local task handling.', confirmedExclude: false, mode: 'unknown', runtimeStatus: 'unverified', unknowns: ['Caller runtime mounting, upper sidebar visibility, feature/platform entitlement, project local/cloud mapping, and downstream mutation implementations are not established.']});
for (const [name, , expectedHash] of targets) if (sha(fs.readFileSync(path.join(baseline.extractedDirectory, 'webview/assets', name))) !== expectedHash) throw Error('Source changed during extraction');
for (const v of Object.values(artifacts)) if (sha(fs.readFileSync(path.join(root, v.artifactPath))) !== v.artifactSha256) throw Error('Input artifact changed during extraction');
const outDir = path.join(root, '.analysis-local/mode-boundary-work'); fs.mkdirSync(outDir, {recursive: true});
const evidencePath = path.join(outDir, 'project-evidence.jsonl');
const evidenceRaw = evidence.map(x => JSON.stringify(x)).join('\n') + '\n'; fs.writeFileSync(evidencePath, evidenceRaw);
output.evidence = {artifactPath: '.analysis-local/mode-boundary-work/project-evidence.jsonl', sha256: sha(evidenceRaw), records: evidence.length};
const reviewPath = path.join(outDir, 'project-review.json'); const reviewRaw = JSON.stringify(output, null, 2) + '\n'; fs.writeFileSync(reviewPath, reviewRaw);
console.log(JSON.stringify({reviewPath, reviewSha256: sha(reviewRaw), reviewBytes: Buffer.byteLength(reviewRaw), evidencePath, evidenceSha256: sha(evidenceRaw), evidenceRecords: evidence.length, summary: output.summary, modules: modules.map(m => ({name: m.name, astCoverage: m.astCoverage, businessCalls: m.businessCalls.map(c => ({callee: c.calleeExpression, origin: c.importedOrigin, evidenceId: c.evidenceId}))}))}));
