// Analyze one complete frozen class without loading or executing target code.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';

const [root, baseline, output] = process.argv.slice(2);
const out = path.join(root, 'analysis', baseline);
const families = JSON.parse(fs.readFileSync(path.join(out, 'entry-family-map.json')));
const contracts = JSON.parse(fs.readFileSync(path.join(out, 'host-message-contracts.json')));
const entries = families.entries.filter(x => x.family === 'host-dispatch');
if (entries.length !== 143) throw Error('Unexpected selected dispatch denominator');
const location = entries[0].lexicalClass;
const source = fs.readFileSync(path.join(root, '.analysis-local/baselines', baseline, 'extracted', location.sourcePath.replace(/^app\.asar\//, '')));
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const fragment = source.subarray(location.byteRange.start, location.byteRange.endExclusive);
if (hash(source) !== location.sourceHash || hash(fragment) !== location.spanHash) throw Error('Frozen class identity mismatch');
const parserPath = path.join(root, '.analysis-local/global-state-storage-work/tooling/node_modules/@babel/parser/lib/index.js');
const parser = createRequire(import.meta.url)(parserPath);
const prefix = 'const SelectedOwner=';
const text = prefix + fragment.toString('utf8') + ';';
const ast = parser.parse(text, {sourceType: 'module'});
const cls = ast.program.body[0].declarations[0].init;
const method = cls.body.body.find(x => x.type === 'ClassMethod' && x.key.name === 'handleMessage');
if (!method) throw Error('Selected method missing');
const switchNode = method.body.body.find(x => x.type === 'SwitchStatement');
const expression = n => text.slice(n.start, n.end);
if (expression(switchNode.discriminant) !== 't.type') throw Error('Different dispatch switch');
function loc(n) {
  const start = location.byteRange.start + Buffer.byteLength(text.slice(prefix.length, n.start));
  const endExclusive = location.byteRange.start + Buffer.byteLength(text.slice(prefix.length, n.end));
  return {sourcePath: location.sourcePath, sourceHash: location.sourceHash,
    byteRange: {start, endExclusive}, spanHash: hash(source.subarray(start, endExclusive)), nodeType: n.type};
}
const gate = method.body.body[0];
if (gate.type !== 'IfStatement' || expression(gate.test) !== 'gR(t)' ||
    gate.consequent.body.at(-1).type !== 'ReturnStatement') throw Error('Dispatch prelude changed');
const rows = [];
const counts = {};
for (let i = 0; i < switchNode.cases.length; i++) {
  const node = switchNode.cases[i];
  if (node.test?.type !== 'TemplateLiteral' || node.test.expressions.length) throw Error('Nonliteral label');
  const label = node.test.quasis[0].value.cooked;
  let effective = i;
  while (effective < switchNode.cases.length && switchNode.cases[effective].consequent.length === 0) effective++;
  if (effective === switchNode.cases.length) throw Error('Unterminated empty label group');
  const body = switchNode.cases[effective].consequent;
  const noOp = body.length === 1 && body[0].type === 'BreakStatement' && body[0].label === null;
  const unsupported = body.length === 1 && body[0].type === 'ThrowStatement' &&
    body[0].argument.type === 'CallExpression' && expression(body[0].argument.callee) === 'Error' &&
    expression(body[0].argument).includes('is not implemented in Electron.');
  const effect = noOp ? 'selected-switch-no-op' : unsupported ? 'selected-switch-explicit-unsupported-error' : 'selected-switch-handler';
  const position = loc(node), saved = contracts.cases[i];
  if (label !== saved.label.value || position.byteRange.start !== saved.clauseRange.start ||
      position.byteRange.endExclusive !== saved.clauseRange.endExclusive ||
      effective !== saved.effectiveHandlerCaseIndex || noOp !== saved.effectiveHandlerNoOp ||
      (node.consequent.length === 0) !== saved.emptyOwnHandler) throw Error('Saved contract differs at case ' + i);
  const entry = entries.find(x => x.sourceCoordinates.byteRange.start === position.byteRange.start &&
    x.sourceCoordinates.byteRange.endExclusive === position.byteRange.endExclusive);
  if (!entry || entry.sourceCoordinates.spanHash !== position.spanHash) throw Error('Legacy entry span mismatch');
  rows.push({entryId: entry.entryId, caseIndex: i, label, ...position,
    ownStatementTypes: node.consequent.map(x => x.type), ownEmpty: node.consequent.length === 0,
    effectiveCaseIndex: effective, effectiveCase: loc(switchNode.cases[effective]), effect,
    conditionalOnPreludePredicateFalse: true, globalOperationRole: 'not-established',
    runtimeVerified: false, productMode: 'unknown'});
  counts[effect] = (counts[effect] || 0) + 1;
}
if (rows.length !== 143 || counts['selected-switch-no-op'] !== 33 ||
    counts['selected-switch-explicit-unsupported-error'] !== 6 || counts['selected-switch-handler'] !== 104) throw Error('Dispatch accounting changed');
let nodes = 0;
function walk(n) {
  if (!n || typeof n !== 'object') return;
  if (typeof n.type === 'string') nodes++;
  for (const [key, value] of Object.entries(n)) {
    if (['loc', 'extra', 'comments', 'leadingComments', 'trailingComments', 'innerComments'].includes(key)) continue;
    if (Array.isArray(value)) value.forEach(walk);
    else if (value && typeof value === 'object') walk(value);
  }
}
walk(ast.program);
const result = {schemaVersion: 1, baselineId: baseline, sourceClass: location,
  method: loc(method), switch: loc(switchNode),
  prelude: {condition: expression(gate.test), source: loc(gate),
    qualification: 'The prelude can route to an overlay manager and return before this switch. A no-op here does not prove absence or nonfunctionality elsewhere.'},
  parser: {path: parserPath, sha256: hash(fs.readFileSync(parserPath))},
  parseScope: 'one complete original ClassExpression inside a synthetic const declaration; free Program bindings are not resolved',
  rows, counts: {...counts, legacyRecordsReviewed: rows.length, ownEmptyLabels: rows.filter(x => x.ownEmpty).length,
    selectedClassParses: 1, parsedNodes: nodes, originalFullProgramsParsed: 0},
  targetCodeExecuted: false, modelSubmissionsAdded: 0, originalClientRunsAdded: 0, newReaRuns: 0};
fs.mkdirSync(output, {recursive: true});
fs.writeFileSync(path.join(output, 'source-class.txt'), fragment, {flag: 'wx'});
fs.writeFileSync(path.join(output, 'class-roles.json'), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify(result.counts));
