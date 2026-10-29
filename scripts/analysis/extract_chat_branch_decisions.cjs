// Reuses saved complete-Program identities; parses only saved selected functions.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const [root, work] = process.argv.slice(2);
const baseline = 'codex-26.1007.30912-c5b273322a83';
const out = path.join(root, 'analysis', baseline);
const original = path.join(out, 'raw/product-flow-ownership/selected-units');
const saved = JSON.parse(fs.readFileSync(path.join(original, 'contracts.json')));
const completePath = path.join(root, '.analysis-local/product-flow-ownership-work/primary-01/source-contracts.json');
const complete = JSON.parse(fs.readFileSync(completePath));
const parserPath = path.join(root, '.analysis-local/global-state-storage-work/tooling/node_modules/@babel/parser/lib/index.js');
const parser = require(parserPath);
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
if (!complete.fullProgramParsed || complete.targetCodeExecuted) throw Error('Unqualified saved Program');
if (fs.existsSync(work)) throw Error('Preserve earlier work');
fs.mkdirSync(work, {recursive: true});
fs.mkdirSync(path.join(work, 'units'));
const sourcePath = complete.sourcePath;
const frozen = fs.readFileSync(path.join(root, '.analysis-local/baselines', baseline, 'extracted', sourcePath.slice(9)));
if (hash(frozen) !== complete.sourceHash) throw Error('Frozen source changed');
const skip = new Set(['loc', 'start', 'end', 'extra', 'comments', 'leadingComments', 'trailingComments', 'innerComments']);
const units = [], fragments = [];
function select(nodes, owner, id, predicate) {
  const matches = nodes.filter(predicate);
  if (matches.length !== 1) throw Error(id + ': expected one match, got ' + matches.length);
  const node = matches[0], expression = owner.text.slice(node.start, node.end);
  const start = owner.byteRange.start + Buffer.byteLength(owner.text.slice(0, node.start));
  const endExclusive = start + Buffer.byteLength(expression);
  if (!frozen.subarray(start, endExclusive).equals(Buffer.from(expression))) throw Error('Byte coordinate mismatch');
  fragments.push({id, owner: owner.name, nodeType: node.type, sourcePath, sourceHash: hash(frozen), byteRange: {start, endExclusive}, spanHash: hash(Buffer.from(expression)), expression});
}
for (const name of ['wzt', 'Tzt', 'Ezt', 'M9', 'jRt']) {
  const metadata = saved.units.find(unit => unit.name === name);
  const bytes = fs.readFileSync(path.join(original, metadata.sourceFilename));
  if (hash(bytes) !== metadata.spanHash || !frozen.subarray(metadata.byteRange.start, metadata.byteRange.endExclusive).equals(bytes)) throw Error(name + ': source mismatch');
  const definitions = complete.programDefinitions.find(item => item.name === name)?.definitions;
  if (definitions?.length !== 1 || definitions[0].spanHash !== metadata.spanHash) throw Error(name + ': complete Program identity mismatch');
  const owner = {...metadata, text: bytes.toString('utf8')};
  fs.writeFileSync(path.join(work, 'units', metadata.sourceFilename), bytes, {flag: 'wx'});
  units.push({...metadata, completeProgramDefinition: definitions[0]});
  const ast = parser.parse(owner.text, {sourceType: 'script'}), nodes = [];
  function walk(node) {
    nodes.push(node);
    for (const [key, child] of Object.entries(node)) {
      if (skip.has(key)) continue;
      if (Array.isArray(child)) child.forEach(value => {if (value && typeof value.type === 'string') walk(value);});
      else if (child && typeof child.type === 'string') walk(child);
    }
  }
  walk(ast.program);
  const text = node => owner.text.slice(node.start, node.end);
  const literal = node => node?.type === 'TemplateLiteral' && node.expressions.length === 0 ? node.quasis[0].value.cooked : node?.type === 'StringLiteral' ? node.value : null;
  if (name === 'jRt') {
    select(nodes, owner, 'jRt:chat-temporary-footer', node => node.type === 'ConditionalExpression' && text(node.test) === 'c===`chat`&&D?.isTemporaryChat');
    select(nodes, owner, 'jRt:retained-NRt', node => node.type === 'CallExpression' && node.arguments[0]?.name === 'NRt');
  }
  if (name === 'wzt') {
    select(nodes, owner, 'wzt:chat-inline-enabled', node => node.type === 'VariableDeclarator' && node.id.name === 'ue' && text(node.init) === 'W===`chat`');
    select(nodes, owner, 'wzt:chat-inline-variant', node => node.type === 'VariableDeclarator' && node.id.name === 'de' && node.init?.type === 'ConditionalExpression' && text(node.init.test) === 'W===`chat`');
  }
  if (name === 'Tzt') {
    select(nodes, owner, 'Tzt:codex-suggestion-policy', node => node.type === 'OptionalCallExpression' && text(node.callee) === 'n?.setSuggestionTriggers');
    select(nodes, owner, 'Tzt:positive-Codex-M9', node => node.type === 'CallExpression' && node.arguments[0]?.name === 'M9');
  }
  if (name === 'Ezt') {
    select(nodes, owner, 'Ezt:mode-suggestion-policy', node => node.type === 'CallExpression' && text(node.callee) === 'n.setSuggestionTriggers');
    select(nodes, owner, 'Ezt:chat-shortcut-registration', node => node.type === 'CallExpression' && node.callee.name === 'py' && literal(node.arguments[0]) === 'switchToMode1');
    select(nodes, owner, 'Ezt:chat-shortcut-callback', node => node.type === 'ArrowFunctionExpression' && text(node.body) === 'me(`chat`)');
    select(nodes, owner, 'Ezt:mode-shortcut-eligibility', node => node.type === 'VariableDeclarator' && node.id.name === 'le' && text(node.init) === 'r&&!0');
    select(nodes, owner, 'Ezt:retained-M9', node => node.type === 'CallExpression' && node.arguments[0]?.name === 'M9');
  }
  if (name === 'M9') select(nodes, owner, 'M9:retained-jRt', node => node.type === 'CallExpression' && node.arguments[0]?.name === 'jRt');
}
const joins = complete.programBindingUses.filter(item => (item.unit === 'Tzt' || item.unit === 'Ezt') && item.name === 'M9');
if (joins.length !== 2 || joins.some(item => item.binding.definitions[0].declaration.spanHash !== units.find(unit => unit.name === 'M9').spanHash)) throw Error('Shared M9 binding join changed');
const result = {
  baselineId: baseline, recordedAtUtc: new Date().toISOString(), units, fragments, sharedM9Joins: joins,
  savedCompleteProgram: {path: path.relative(root, completePath), bytes: fs.statSync(completePath).size, sha256: hash(fs.readFileSync(completePath)), nodeCount: complete.nodeCount},
  parser: {path: parserPath, sha256: hash(fs.readFileSync(parserPath))},
  scriptSha256: hash(fs.readFileSync(__filename)),
  newFullProgramParses: 0, selectedFunctionParses: units.length,
  targetModuleBootstrapped: false, originalClientRunsAdded: 0, modelSubmissionsAdded: 0,
  limits: ['Selected-function AST supplies local branch coordinates; global identities come from the saved complete Program. No new global consumer census or runtime mode discovery.'],
};
fs.writeFileSync(path.join(work, 'branch-source.json'), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({units: units.length, fragments: fragments.length, savedLexicalJoins: joins.length, newFullProgramParses: 0}));
