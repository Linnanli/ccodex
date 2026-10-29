// Execute only the saved pure URL helpers, never the client or its providers.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const base = 'codex-26.1007.30912-c5b273322a83';
const out = path.join(root, 'analysis', base);
const input = path.join(out, 'raw/settings-feature-entry-conditions/usage-routes');
const destination = path.join(root, '.analysis-local/settings-section-disposition-work/usage-helper-observations.json');
assert(!fs.existsSync(destination));
const contracts = JSON.parse(fs.readFileSync(path.join(input, 'source-contracts.json')));
const hash = data => crypto.createHash('sha256').update(data).digest('hex');
const names = ['MNs', 'PNs', 'assignment-FNs'];
const pieces = names.map(name => {
  const unit = contracts.units.find(x => x.selection === name);
  assert(unit);
  const bytes = fs.readFileSync(path.join(input, unit.sourceFilename));
  assert.equal(hash(bytes), unit.spanHash);
  return {name, text: bytes.toString('utf8'), source: unit};
});
const context = vm.createContext({URLSearchParams});
vm.runInContext('var FNs;\n' + pieces.map(x => x.text).join('\n'), context, {timeout: 1000});
const reviews = JSON.parse(fs.readFileSync(path.join(out, 'settings-mode-boundary-contracts.json'))).settingsSectionReviews;
const usage = new Set(['usage', 'analytics', 'consumer-view', 'usage-code-review']);
const observations = reviews.map(row => {
  const actual = context.MNs(row.slug), expected = usage.has(row.slug);
  assert.equal(actual, expected);
  return {kind: 'usage-section-match', slug: row.slug, actual, expected, passed: true};
});
const cases = [
  {slug: 'analytics', search: '?tab=old&x=a%20b&x=c', expected: '/settings/usage?tab=analytics&x=a+b&x=c'},
  {slug: 'usage-code-review', search: '?x=1', expected: '/settings/usage?x=1&tab=code-review'},
  {slug: 'consumer-view', search: '', expected: '/settings/usage?tab=consumer-view'},
  {slug: 'usage', search: '?x=a%20b', expected: '/settings/usage?x=a+b&tab=overview'},
  {slug: 'general-settings', search: '?tab=old&x=a%20b', expected: '/settings/general-settings?tab=old&x=a%20b'},
  {slug: 'unknown', search: '', expected: '/settings/unknown'},
  {slug: 'analytics', omitSearch: true, expected: '/settings/usage?tab=analytics'},
];
for (const item of cases) {
  const actual = item.omitSearch ? context.PNs(item.slug) : context.PNs(item.slug, item.search);
  assert.equal(actual, item.expected);
  observations.push({kind: 'query-normalization', ...item, actual, passed: true});
}
const result = {
  baselineId: base, runtime: {node: process.versions.node, platform: process.platform, arch: process.arch},
  sourceContract: {path: path.relative(out, path.join(input, 'source-contracts.json')), sha256: hash(fs.readFileSync(path.join(input, 'source-contracts.json')))},
  selectedSourceUnits: pieces.map(x => x.source), observations,
  counts: {isolatedHelperCases: observations.length, passed: observations.length, productScenariosExecuted: 0},
  targetCodeExecuted: true, executionScope: 'MNs, PNs and the literal FNs assignment only',
  originalClientRunsAdded: 0, modelSubmissionsAdded: 0, mockReactUsed: false,
  qualification: 'These are actual executions of extracted pure helpers in an isolated VM. They do not establish React mounting, account/provider values or client behavior acceptance.',
};
fs.writeFileSync(destination, JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify(result.counts));
