// Execute previously selected source units with synthetic receivers only.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const baselineId = 'codex-26.1007.30912-c5b273322a83';
const out = path.join(root, 'analysis', baselineId);
const selected = path.join(out, 'raw/runtime-decisions/source-01/main-CqEoQDOU');
const metadata = JSON.parse(fs.readFileSync(path.join(selected, 'source-contracts.json')));
const frozen = fs.readFileSync(path.join(root, '.analysis-local/baselines', baselineId, 'extracted/.vite/build/main-CqEoQDOU.js'));
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
assert.equal(sha(frozen), metadata.sourceHash);
const units = [0, 1, 10].map(index => {
  const unit = metadata.units[index];
  const bytes = fs.readFileSync(path.join(selected, unit.sourceFilename));
  assert.equal(sha(bytes), unit.spanHash);
  assert.deepEqual(bytes, frozen.subarray(unit.byteRange.start, unit.byteRange.endExclusive));
  return { ...unit, metadataIndex: index, code: bytes.toString('utf8') };
});
const cases = [];
function check(id, claim, fn) {
  try { fn(); cases.push({ id, claim, passed: true }); }
  catch (error) { cases.push({ id, claim, passed: false, error: String(error.stack) }); }
}
function fixture() {
  const owner = { id: 'owned-window' };
  const result = { calls: [], messages: [], materialized: [] };
  const target = {
    id: 42, isDestroyed: () => false,
    _createWebViewAdoptionLease: value => { result.calls.push(['lease', value]); return 'synthetic-lease'; },
    close: () => result.calls.push(['close']), destroy: () => result.calls.push(['destroy']),
    once: (event, listener) => result.calls.push(['once', event]),
    removeListener: () => {},
  };
  const source = {
    id: 41, isDestroyed: () => false, canGoBack: () => true, canGoForward: () => true,
    clone: (...args) => { result.calls.push(['clone', args]); return target; },
  };
  const page = { view: { webContents: source }, title: 'Synthetic page', url: 'https://fixture.invalid/a',
    pendingUrl: 'https://fixture.invalid/pending', serializedPageState: { title: 'Synthetic serialized', url: 'https://fixture.invalid/a' },
    errorPagesByUrl: new Map([['https://fixture.invalid/error', { code: -1 }]]) };
  const windowState = { owner, pendingAdoptedWebviewsByWebContentsId: new Map() };
  const host = {
    getCurrentPageCommandContext: () => ({ page, windowState }),
    admitBrowserTab: reason => { result.calls.push(['admit', reason]); return true; },
    ensureThreadStateForCommand: () => ({ threadId: 'fixture-thread' }),
    materializeThreadPageState: (window, thread, state) => {
      const created = { errorPagesByUrl: null }; result.materialized.push({ window, thread, state, created }); return created;
    },
    windowManager: { sendMessageToWebContents: (recipient, message) => result.messages.push({ recipient, message }) },
  };
  const context = vm.createContext({
    Map, Error, structuredClone, g: { Gt: id => `browser-${id}` },
    crypto: { randomUUID: () => 'synthetic-id' }, lV: value => value,
  });
  vm.runInContext(units[0].code + '\n' + units[1].code, context);
  const cloneTab = vm.runInContext('({' + units[2].code + '}).cloneTab', context);
  const run = navigation => cloneTab.call(host, owner, {
    active: true, browserHostDisplayName: 'Fixture', browserTabId: 'source-tab',
    conversationId: 'fixture-thread', cwd: '/synthetic', navigation,
  });
  return { owner, result, target, source, page, windowState, host, run };
}
check('BC-01', 'A different command owner cannot initiate cloning.', () => {
  const f = fixture(); f.windowState.owner = {}; f.run('reload');
  assert.equal(f.result.calls.length, 0); assert.equal(f.result.messages.length, 0);
});
for (const [id, navigation, permission] of [['BC-02', 'back', 'canGoBack'], ['BC-03', 'forward', 'canGoForward']]) {
  check(id, `${navigation} requires source navigation availability before cloning.`, () => {
    const f = fixture(); f.source[permission] = () => false; f.run(navigation);
    assert.equal(f.result.calls.length, 0); assert.equal(f.result.messages.length, 0);
  });
}
check('BC-04', 'Admission rejection leaves the source and destination message stream unchanged.', () => {
  const f = fixture(); f.host.admitBrowserTab = () => false; f.run('reload');
  assert.equal(f.result.calls.length, 0); assert.equal(f.result.messages.length, 0);
});
check('BC-05', 'A live clone has a new identity, pending route and deferred history action; no direct JS-heap read occurs in this caller.', () => {
  const f = fixture();
  Object.defineProperty(f.source, 'heap', { get() { throw Error('caller must not assume heap access'); } });
  f.run('back');
  const { message } = f.result.messages[0];
  assert.equal(message.adoptedWebContentsId, 42); assert.notEqual(message.adoptedWebContentsId, f.source.id);
  assert.equal(message.adoptionLease, 'synthetic-lease'); assert.equal(message.initialUrl, f.page.url);
  assert.equal(message.insertToRightOfTabId, 'source-tab');
  const pending = f.windowState.pendingAdoptedWebviewsByWebContentsId.get(42);
  assert.equal(pending.initialHistoryNavigation.navigation, 'back');
  assert.equal(pending.route.conversationId, 'fixture-thread');
  assert.notEqual(pending.initialHistoryNavigation.errorPagesByUrl, f.page.errorPagesByUrl);
  assert.equal(pending.initialHistoryNavigation.errorPagesByUrl.size, 1);
  assert.equal(f.result.calls.find(x => x[0] === 'clone')[1].length, 0);
  assert.equal(f.result.materialized.length, 0);
});
check('BC-06', 'An already destroyed clone is not announced or leased.', () => {
  const f = fixture(); f.target.isDestroyed = () => true; f.run('reload');
  assert.equal(f.result.messages.length, 0); assert.equal(f.windowState.pendingAdoptedWebviewsByWebContentsId.size, 0);
});
check('BC-07', 'A clone without adoption capability is closed and raises the original failure.', () => {
  const f = fixture(); delete f.target._createWebViewAdoptionLease;
  assert.throws(() => f.run('reload'), /cannot be adopted/);
  assert.equal(f.result.calls.filter(x => x[0] === 'close').length, 1);
  assert.equal(f.result.messages.length, 0);
});
check('BC-08', 'An empty adoption lease destroys the destination and leaves no pending identity.', () => {
  const f = fixture(); f.target._createWebViewAdoptionLease = () => '';
  assert.throws(() => f.run('reload'), /lease is empty/);
  assert.equal(f.result.calls.filter(x => x[0] === 'destroy').length, 1);
  assert.equal(f.result.messages.length, 0); assert.equal(f.windowState.pendingAdoptedWebviewsByWebContentsId.size, 0);
});
check('BC-09', 'Only reload may materialize a source with no live WebContents, copying the saved snapshot.', () => {
  const f = fixture(); f.page.view.webContents = null; f.run('reload');
  const materialized = f.result.materialized[0];
  assert.equal(materialized.state.kind, 'cold-restore');
  assert.notEqual(materialized.state.snapshot, f.page.serializedPageState);
  assert.equal(materialized.state.snapshot.url, f.page.serializedPageState.url);
  assert.notEqual(materialized.created.errorPagesByUrl, f.page.errorPagesByUrl);
  assert.equal(f.result.messages[0].message.adoptionLease, undefined);
  assert.equal(f.result.calls.filter(x => x[0] === 'clone').length, 0);
});
check('BC-10', 'Back on an absent live source cannot silently take the reload/cold-restore path.', () => {
  const f = fixture(); f.page.view.webContents = null; f.run('back');
  assert.equal(f.result.materialized.length, 0); assert.equal(f.result.messages.length, 0);
});
check('BC-11', 'Absent serialized state selects a fresh page using the pending URL.', () => {
  const f = fixture(); f.page.view.webContents = null; f.page.serializedPageState = null; f.run('reload');
  assert.equal(f.result.materialized[0].state.kind, 'fresh');
  assert.equal(f.result.materialized[0].state.page.url, f.page.pendingUrl);
});
check('BC-12', 'A transferred source window owns the pending lease and receives the destination announcement.', () => {
  const f = fixture(); const destination = { owner: { id: 'owned-destination' }, pendingAdoptedWebviewsByWebContentsId: new Map() };
  f.windowState.tabSourceWindow = destination; f.run('forward');
  assert.equal(f.result.messages[0].recipient, destination.owner);
  assert.equal(destination.pendingAdoptedWebviewsByWebContentsId.size, 1);
  assert.equal(f.windowState.pendingAdoptedWebviewsByWebContentsId.size, 0);
});
const result = {
  baselineId, method: 'Previously selected exact source in Node VM; synthetic native clone/lease/host receivers.',
  selectedSourceUnits: units.map(({ code, ...unit }) => unit), cases,
  passed: cases.filter(x => x.passed).length, failed: cases.filter(x => !x.passed).length,
  newProgramParses: 0, nativeCloneBehaviorsVerified: 0, productScenarioPassesAdded: 0,
  modelSubmissionsAdded: 0, originalClientRunsAdded: 0, realServiceCalls: 0,
  limitation: 'These observations constrain first-party orchestration. The synthetic clone supplies no evidence about Owl native clone state or public-runtime equivalence.',
};
const directory = path.join(root, '.analysis-local/browser-clone-route-work');
fs.mkdirSync(directory, { recursive: true });
fs.writeFileSync(path.join(directory, 'isolated-observations.json'), JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
process.stdout.write(JSON.stringify({ passed: result.passed, failed: result.failed }) + '\n');
if (result.failed) process.exitCode = 1;
