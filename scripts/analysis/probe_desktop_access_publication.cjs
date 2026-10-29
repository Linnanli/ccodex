// Execute pinned source units with owned state and hook substitutes only.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const baselineId = 'codex-26.1007.30912-c5b273322a83';
const work = path.join(root, '.analysis-local/desktop-access-publication-work');
const out = path.join(root, 'analysis', baselineId);
const frozen = path.join(root, '.analysis-local/baselines', baselineId, 'extracted');
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const readJson = p => JSON.parse(fs.readFileSync(p));
const plain = x => JSON.parse(JSON.stringify(x));
const selections = ['initial', 'shared'].map(name => ({name, metadata: readJson(path.join(work, name, 'source-contracts.json'))}));
const sourceSelections = [];
const buffers = new Map();
function span(unit) {
  const relative = unit.sourcePath.replace(/^app\.asar\//, '');
  if (!buffers.has(relative)) buffers.set(relative, fs.readFileSync(path.join(frozen, relative)));
  const input = buffers.get(relative);
  assert.equal(hash(input), unit.sourceHash);
  const r = unit.byteRange;
  const value = input.subarray(r.start, r.endExclusive);
  assert.equal(hash(value), unit.spanHash);
  return value.toString('utf8');
}
for (const selected of selections) {
  for (const unit of selected.metadata.units) {
    assert.equal(span(unit), fs.readFileSync(path.join(work, selected.name, unit.sourceFilename), 'utf8'));
    sourceSelections.push({selection: selected.name, kind: 'unit', ...unit});
  }
}
const unit = name => {
  const match = selections.flatMap(s => s.metadata.units).filter(u => u.name === name);
  assert.equal(match.length, 1);
  return span(match[0]);
};
const callbacks = selections[0].metadata.callbacks;
function callback(label, predicate) {
  const found = callbacks.filter(c => c.unit === 'SHs' && predicate(span(c)));
  assert.equal(found.length, 1, label);
  sourceSelections.push({selection: 'initial', kind: 'callback', label, ...found[0]});
  return span(found[0]);
}
const publication = callback('publish-access-inputs', s => s.includes('zne(o,') && s.includes('o.set(Gr,'));
const cleanup = callback('unmount-access-inputs', s => s.startsWith('()=>()=>') && s.includes('o.set(Gr,wHs)'));
const previous = readJson(path.join(out, 'settings-mode-boundary-contracts.json'));
const previousEG = previous.selectedUnits.filter(u => u.name === 'assignment-EG');
assert.equal(previousEG.length, 1);
sourceSelections.push({selection: 'reused-settings-mode-boundary', kind: 'unit', ...previousEG[0]});
const evaluate = (code, env) => vm.runInNewContext('(' + code + ')', env, {timeout: 1000});
const cases = [];
function check(id, run) {
  try { const observed = run(); cases.push({id, passed: true, observed}); }
  catch (error) { cases.push({id, passed: false, error: String(error.stack)}); }
}

for (const authMethod of ['chatgpt', 'chatgptAuthTokens', 'personalAccessToken', 'copilot', null]) {
  check('AUTH-PROVIDER:' + authMethod, () => {
    const queryCalls = [], listeners = [];
    const data = {accountId: 'owned-A', userId: 'owned-U', hasChatGptToken: true, plan: 'owned-plan'};
    const auth = {authMethod, isLoading: authMethod === null, accountId: 'owned-A', userId: 'owned-U', hasChatGptToken: true, email: 'owned@example.invalid', requiresAuth: true};
    const jsx = (type, props) => ({type, props});
    const env = {DUs: {c: n => Array(n).fill(Symbol('empty'))}, G: () => false, bRr: 'disabled-token', Cje: () => 'scope',
      BYe: () => auth, as: 'auth-source', OUe: config => {queryCalls.push(config); return {data, isError: false, isLoading: false, refetch() { throw Error('unexpected refetch'); }};},
      xs: (...args) => listeners.push(args[0]), Q6: {jsx, jsxs: jsx, Fragment: 'fragment'},
      SHs: 'account-access-publisher', uHs: 'account-query-diagnostic', _1e: {Provider: 'auth-provider'}};
    const result = evaluate(unit('EUs'), env)({children: 'owned-child'});
    const publisher = result.props.children[1].props.children;
    const enabled = authMethod === 'chatgpt' || authMethod === 'chatgptAuthTokens';
    assert.equal(publisher.type, 'account-access-publisher');
    assert.equal(publisher.props.auth.authMethod, authMethod);
    assert.equal(publisher.props.accountInfo, enabled ? data : undefined);
    assert.equal(queryCalls.length, 1);
    assert.equal(queryCalls[0].enabled, enabled);
    assert.equal(result.props.children[2], 'owned-child');
    return {accountPublisherConstructed: true, accountQueryEnabled: enabled, authMethod};
  });
}

function stateFixture(options = {}) {
  const mutations = [], invalidations = [];
  const identity = {accountId: 'owned-A', authenticatedAccountId: 'owned-A', userId: 'owned-U', accountUserId: 'owned-AU'};
  const saved = {accountId: 'owned-A', userId: 'owned-U', accountUserId: 'owned-AU', accessToken: 'synthetic-token'};
  const values = new Map([['chat-input', {...identity, ...options.previous}], ['saved-profile', options.saved === undefined ? saved : options.saved]]);
  const selectorEnv = {J: (_, fn) => fn, X: 'scope', wG: 'saved-profile', TG: 'chat-input'};
  vm.runInNewContext(span(previousEG[0]), selectorEnv, {timeout: 1000});
  const scope = {get(key) { return key === 'saved-eligibility' ? selectorEnv.EG({get: k => values.get(k)}) : values.get(key); },
    set(key, value) { values.set(key, value); mutations.push({key, value: plain(value)}); }};
  const env = {TG: 'chat-input', wG: 'saved-profile', EG: 'saved-eligibility', wO: (_, fn) => fn(),
    Zxn: (_, accountId, userId) => invalidations.push({accountId, userId})};
  return {scope, values, mutations, invalidations, publish: evaluate(unit('yTn'), env)};
}
function publish(options = {}) {
  const f = stateFixture(options);
  const a = {isLoading: false, authMethod: 'chatgpt', accountId: 'owned-A', userId: 'owned-U', hasChatGptToken: true, requiresAuth: true, email: 'owned@example.invalid', ...options.auth};
  const n = options.noAccountInfo ? undefined : {accountId: 'owned-A', userId: 'owned-U', plan: 'owned-plan', windowsJumpListEpoch: 3};
  const T = options.noServerAccount ? undefined : {account_id: 'owned-A', account_user_id: 'owned-AU', plan_type: 'owned-plan', structure: 'personal', ...options.server};
  const p = a.authMethod === 'chatgpt' && !!a.hasChatGptToken && a.accountId != null;
  const env = {a, n, T, p, S: options.pending === true, C: options.pending ? 'pending' : 'success', i: false, E: false,
    l: a.accountId ?? n?.accountId ?? null, u: n?.accountId === a.accountId ? n?.userId ?? null : null,
    o: f.scope, f: {account_user_id: 'owned-AU'}, Lh: 'http-account', Xl: 'old-profile', Gr: 'codex-input', Aea: 'display-identity', zne: f.publish};
  evaluate(publication, env)();
  return f;
}

for (const authMethod of ['chatgpt', 'chatgptAuthTokens', 'personalAccessToken', 'copilot']) {
  check('PUBLISH:' + authMethod, () => {
    const f = publish({auth: {authMethod}, noAccountInfo: !authMethod.startsWith('chatgpt'), noServerAccount: !authMethod.startsWith('chatgpt')});
    assert.equal(f.values.get('chat-input').supportedSurface, true);
    assert.equal(f.values.get('codex-input').supportedSurface, true);
    assert.equal(f.values.get('codex-input').workCloudSupportedSurface, true);
    assert.equal(f.values.get('http-account'), authMethod.startsWith('chatgpt') ? 'owned-A' : null);
    return {chatSurface: true, codexSurface: true, httpAccount: f.values.get('http-account')};
  });
}
check('PUBLISH:loading-does-not-publish-http-account', () => {
  const f = publish({auth: {isLoading: true}, noServerAccount: true});
  assert.equal(f.values.get('http-account'), null);
  assert.equal(f.values.get('chat-input').authLoading, true);
  assert.equal(f.values.get('chat-input').accountLoading, false);
});
check('PUBLISH:account-mismatch-is-preserved', () => {
  const f = publish({server: {account_id: 'owned-B'}});
  assert.equal(f.values.get('chat-input').accountId, 'owned-B');
  assert.equal(f.values.get('chat-input').authenticatedAccountId, 'owned-A');
});
check('PUBLISH:pending-profile-retains-matching-account-user', () => {
  const f = publish({pending: true, server: {account_user_id: null}});
  assert.equal(f.values.get('chat-input').accountUserId, 'owned-AU');
  assert.ok(f.values.get('saved-profile'));
});
check('PUBLISH:pending-profile-rejects-other-identity', () => {
  const f = publish({pending: true, saved: {accountId: 'owned-B', userId: 'owned-U', accountUserId: 'other-AU', accessToken: 'synthetic-token'}, server: {account_user_id: null}});
  assert.equal(f.values.get('chat-input').accountUserId, null);
  assert.equal(f.values.get('saved-profile'), null);
});
check('PUBLISH:changed-identity-invalidates-old-profile', () => {
  const f = publish({previous: {authenticatedAccountId: 'owned-OLD', userId: 'owned-OLD-U'}});
  assert.deepEqual(f.invalidations, [{accountId: 'owned-OLD', userId: 'owned-OLD-U'}]);
});
check('PUBLISH:unchanged-identity-does-not-invalidate', () => {
  assert.deepEqual(publish().invalidations, []);
});

const accessInputs = [
  ['surface-loading', {supportedSurface: null}, 'loading'],
  ['unsupported-surface', {supportedSurface: false}, 'unsupported-surface'],
  ['auth-loading', {authLoading: true, authMethod: null}, 'loading'],
  ['account-loading', {accountLoading: true, accountId: null}, 'loading'],
  ['missing-account', {accountId: null}, 'missing-account'],
  ['account-mismatch', {accountId: 'owned-B'}, 'account-mismatch'],
  ['token-auth-is-distinct', {authMethod: 'chatgptAuthTokens'}, 'not-chatgpt-auth'],
  ['api-auth-is-distinct', {authMethod: 'personalAccessToken'}, 'not-chatgpt-auth'],
  ['matching-chatgpt-auth', {}, 'allowed'],
  ['unsupported-plan', {plan: 'unsupported-owned-plan'}, 'unsupported-plan'],
];
for (const [name, changes, expected] of accessInputs) {
  check('ACCESS:' + name, () => {
    const input = {supportedSurface: true, authLoading: false, authMethod: 'chatgpt', accountLoading: false, accountId: 'owned-A', authenticatedAccountId: 'owned-A', plan: 'owned-plan', ...changes};
    const result = plain(evaluate(unit('xbn'), {Sbn: plan => plan === 'owned-plan'})(input));
    assert.equal(result.reason ?? result.status, expected);
    return result;
  });
}
for (const hasIdentity of [true, false]) {
  check('CLEANUP:' + (hasIdentity ? 'previous-identity' : 'no-identity'), () => {
    const f = stateFixture({previous: {authenticatedAccountId: hasIdentity ? 'owned-A' : null}});
    const dispose = evaluate(cleanup, {o: f.scope, xg: 'chat-input', Gr: 'codex-input', Xl: 'old-profile', Lh: 'http-account',
      Pc: (_, fn) => fn(), wHs: {fixtureDefault: 'codex'}, CHs: {fixtureDefault: 'chat'},
      dAe: (_, accountId, userId) => f.invalidations.push({accountId, userId})})();
    assert.equal(f.mutations.length, 0);
    dispose();
    assert.equal(f.values.get('http-account'), null);
    assert.equal(f.values.get('codex-input').fixtureDefault, 'codex');
    assert.equal(f.values.get('chat-input').fixtureDefault, 'chat');
    assert.equal(f.invalidations.length, hasIdentity ? 1 : 0);
  });
}
const result = {baselineId, method: 'Exact frozen source functions/callbacks in isolated Node VM with synthetic hooks, state, batches and effects.',
  sourceSelections, cases, passed: cases.filter(x => x.passed).length, failed: cases.filter(x => !x.passed).length,
  fullOriginalProgramsParsed: 2, productScenariosExecuted: 0, originalClientRunsAdded: 0, modelSubmissionsAdded: 0, realServiceCalls: 0,
  limits: ['No real React mount or bootstrap execution', 'Batch/state/query/hooks and supported-plan predicate are owned substitutes', 'No actual account access or product-mode observation', 'Surface booleans are input publication, not an authorization grant']};
const destination = process.argv[2];
assert.ok(destination, 'output path required');
fs.writeFileSync(destination, JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({passed: result.passed, failed: result.failed, failures: cases.filter(x => !x.passed)}));
process.exitCode = result.failed ? 1 : 0;
