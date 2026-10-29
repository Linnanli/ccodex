// Original saved functions, synthetic services and hook state only; no client or real data access.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const work = path.resolve(__dirname, '../../.analysis-local/settings-operation-batch-02');
const destination = path.join(work, 'isolated-observations.json');
assert(!fs.existsSync(destination));
const loaded = [], observations = [];
const clone = x => JSON.parse(JSON.stringify(x));
const hash = x => crypto.createHash('sha256').update(x).digest('hex');
function source(folder, name) {
  const j = JSON.parse(fs.readFileSync(path.join(work, folder, 'source-contracts.json')));
  const u = j.units.find(x => x.name === name); assert(u, name);
  const b = fs.readFileSync(path.join(work, folder, u.sourceFilename)); assert.equal(hash(b), u.spanHash);
  loaded.push({folder, ...u}); return b.toString('utf8');
}
async function test(caseId, scope, run) { observations.push({caseId, scope, passed: true, observed: await run()}); }
function deferred() { let resolve, reject; const promise = new Promise((a, b) => {resolve = a; reject = b;}); return {promise, resolve, reject}; }
async function drain() { for (let i = 0; i < 12; i++) await Promise.resolve(); }
function nodes(x) {
  if (Array.isArray(x)) return x.flatMap(nodes);
  if (!x || typeof x !== 'object') return [];
  return [x, ...nodes(x.props?.children), ...nodes(x.props?.control)];
}
function hooks() {
  const slots = []; let cursor = 0;
  return {reset() {cursor = 0;}, slots,
    useState(initial) {const i = cursor++; if (!(i in slots)) slots[i] = initial; return [slots[i], v => {slots[i] = typeof v === 'function' ? v(slots[i]) : v;}];},
    useRef(initial) {const i = cursor++; if (!(i in slots)) slots[i] = {current: initial}; return slots[i];},
  };
}
const jsx = {Fragment: 'fragment', jsx: (type, props) => ({type, props}), jsxs: (type, props) => ({type, props})};
const compiler = {c: n => Array(n).fill(Symbol.for('react.memo_cache_sentinel'))};

async function main() {
  const pure = vm.createContext({He: x => x.replace(/\\/g, '/'), D: x => x.toLowerCase(), Ct: x => x.split('/.git/')[0]});
  for (const n of ['mn', 'An', 'pn', 'Tn']) vm.runInContext(source('worktrees-01', n), pure);
  await test('worktree-path-boundary', 'original-mn-with-normalizer-substitute', () => {
    assert.equal(pure.mn('/repo/wt/nested/', '/repo/wt/'), true); assert.equal(pure.mn('/repo/wt-two', '/repo/wt'), false);
    return {descendant: true, siblingPrefix: false, pathNormalizerSubstituted: true};
  });
  await test('worktree-exclude-local-environment-roots', 'original-An-mn', () => {
    const result = pure.An([{dir: '/a/one'}, {dir: '/b/two'}, {dir: '/a/one-other'}], ['/a/one']);
    assert.deepEqual(clone(result), [{dir: '/b/two'}, {dir: '/a/one-other'}]); return clone(result);
  });
  await test('worktree-links-deduplicate-native-and-attached', 'original-pn-with-key-substitute', () => {
    const result = pure.pn([{dir: '/wt'}], [{id: 'a', cwd: '/wt/sub', attachedWorktreeRoots: ['/wt']}, {id: 'a', cwd: '/wt'}, {id: 'b', cwd: '/else', attachedWorktreeRoots: ['/wt']}]);
    assert.deepEqual(clone(result.get('/wt')).map(x => x.id), ['a', 'b']); return {ids: ['a', 'b']};
  });
  await test('worktree-visible-pinned-or-nonsubagent', 'original-Tn', () => {
    assert.equal(pure.Tn({isPinned: true, isSubagent: true}), true); assert.equal(pure.Tn({isPinned: false, isSubagent: true}), false);
    assert.equal(pure.Tn({isPinned: false, isSubagent: false}), true); return {pinnedSubagentVisible: true, unpinnedSubagentVisible: false};
  });
  const deleteSource = source('worktrees-01', 'gn');
  function deletion(options = {}) {
    const events = [], blocker = options.blocker, state = {pending: !!options.pending};
    const context = vm.createContext({vn: 'pending', W: 'notices', q: 'pin-policy',
      _n: jsx, X: 'message', c: x => x.message, f: {error: () => events.push(['log-error'])}, Ot: x => ['worktrees', x],
      async sn() {events.push(['read-pins']); return options.pinned ? [{cwd: '/wt/sub'}] : [];},
      le: (roots, cwd) => roots.some(r => cwd === r || cwd.startsWith(r + '/')) ? roots[0] : null,
      et: () => ({async archiveConversation(id, params) {events.push(['archive', id, clone(params)]); if (options.archiveReject) throw Error('archive-fixture'); if (blocker) await blocker.promise;}}),
      async M(method, payload) {events.push([method, clone(payload)]); if (options.deleteReject) throw Error('delete-fixture');},
    });
    vm.runInContext(deleteSource, context);
    const owner = {get: key => key === 'pending' ? state.pending : key === 'pin-policy' ? 'synthetic' : Object.fromEntries(['success', 'danger', 'warning'].map(k => [k, () => events.push([k])])),
      set(key, value, v) {state.pending = v; events.push(['pending', v]);}, queryClient: {async invalidateQueries(x) {events.push(['invalidate', clone(x)]); if (options.invalidateReject) throw Error('invalidate-fixture');}}};
    return {events, state, run: () => context.gn(owner, {hostId: 'fixture-host', worktree: '/wt'}, [{id: 'a'}, {id: 'b'}])};
  }
  await test('delete-worktree-pending-suppression', 'original-gn-synthetic-services', async () => {const x = deletion({pending: true}); await x.run(); assert.equal(x.events.length, 0); return {requests: 0};});
  await test('delete-worktree-rechecks-pins', 'original-gn-synthetic-services', async () => {
    const x = deletion({pinned: true}); await x.run(); assert.deepEqual(x.events.map(x => x[0]), ['pending', 'read-pins', 'warning', 'pending']); assert.equal(x.state.pending, false); return x.events;
  });
  await test('delete-worktree-archives-before-targeted-delete', 'original-gn-synthetic-services', async () => {
    const gate = deferred(), x = deletion({blocker: gate}); const running = x.run(); await drain();
    assert.equal(x.events.filter(x => x[0] === 'archive').length, 2); assert(!x.events.some(x => x[0] === 'worktree-delete'));
    gate.resolve(); await running; assert.deepEqual(x.events.map(x => x[0]), ['pending', 'read-pins', 'archive', 'archive', 'worktree-delete', 'invalidate', 'success', 'pending']);
    assert(x.events.filter(x => x[0] === 'archive').every(x => x[2].cleanupWorktree === false)); return x.events;
  });
  for (const [id, option] of [['archive-error', 'archiveReject'], ['delete-error', 'deleteReject'], ['invalidate-error', 'invalidateReject']]) {
    await test('delete-worktree-' + id, 'original-gn-synthetic-services', async () => {
      const x = deletion({[option]: true}); await x.run(); assert.equal(x.state.pending, false); assert(x.events.some(x => x[0] === 'danger')); assert(!x.events.some(x => x[0] === 'success'));
      if (option === 'archiveReject') assert(!x.events.some(x => x[0] === 'worktree-delete'));
      return {events: x.events, noCompensationObservedInSelectedFunction: true};
    });
  }
  const listSource = source('worktrees-01', 'cn');
  for (const repeat of [false, true]) await test(repeat ? 'worktree-list-repeated-cursor-error' : 'worktree-list-pagination', 'original-cn-synthetic-rpc', async () => {
    const calls = [], pages = repeat ? [{data: [{id: 'a'}], nextCursor: 'same'}, {data: [], nextCursor: 'same'}] : [{data: [{id: 'a'}], nextCursor: 'next'}, {data: [{id: 'b'}], nextCursor: null}];
    const context = vm.createContext({et: () => ({async sendRequest(method, params, metadata) {calls.push([method, clone(params), clone(metadata)]); return pages.shift();}})}); vm.runInContext(listSource, context);
    if (repeat) await assert.rejects(context.cn({}, 'host', ['synthetic']), /repeated/); else assert.deepEqual(clone(await context.cn({}, 'host', ['synthetic'])).map(x => x.id), ['a', 'b']);
    assert.equal(calls.length, 2); assert.equal(calls[1][1].cursor, repeat ? 'same' : 'next'); return calls;
  });

  const cleanupSource = source('worktrees-01', 'Jt');
  function cleanup(options = {}) {
    const state = hooks(), mutations = [], notices = [], saved = {autoCleanupEnabled: options.enabled ?? true, keepCount: 15};
    const descriptors = {upstreamRefreshMode: {key: 'upstream'}, autoCleanupEnabled: {key: 'cleanup', default: true}, keepCount: {key: 'keep', default: 15}};
    const context = vm.createContext({Xt: compiler, Zt: state, Q: jsx, X: 'message', L: descriptors, kt: {}, S: {}, W: {}, de: 'row', Et: 'input', r: 'toggle', Yt: 'confirm-disable',
      b: () => ({get: () => Object.fromEntries(['success', 'danger'].map(k => [k, text => notices.push([k, text])]))}), ye: () => ({formatMessage: x => x.id}),
      ke: () => 'never', re: () => saved, Ze: async () => {}, Nt: async () => {},
      qe(config) {const index = mutations.length; const m = {isPending: false, config, calls: [], mutate: value => m.calls.push(value)}; mutations.push(m); return m;}});
    vm.runInContext(cleanupSource, context);
    function render() {state.reset(); mutations.length = 0; const tree = context.Jt({hostId: 'synthetic'}); return {tree, input: nodes(tree).find(x => x.type === 'input'), toggles: nodes(tree).filter(x => x.type === 'toggle'), dialog: nodes(tree).find(x => x.type === 'confirm-disable')};}
    return {render, mutations, notices, saved};
  }
  for (const [value, expected] of [['', null], ['bad', null], ['15', null], ['0', 1], ['-3', 1], ['2.9', 2], ['3garbage', 3], [' 4 ', 4]]) {
    await test('cleanup-keep-count-' + (value || 'empty'), 'original-Jt-substituted-hooks-and-mutation', () => {
      const x = cleanup(); x.render().input.props.onChange({target: {value}}); const view = x.render(); view.input.props.onBlur();
      assert.deepEqual(x.mutations[2].calls, expected == null ? [] : [expected]); return {draft: value, submitted: expected, parseIntBehavior: true};
    });
  }
  await test('cleanup-disabled-limit-is-inert', 'original-Jt-substituted-hooks', () => {
    const x = cleanup({enabled: false}), view = x.render(); assert.equal(view.input.props.disabled, true); view.input.props.onChange({target: {value: '2'}}); x.render().input.props.onBlur(); assert.equal(x.mutations[2].calls.length, 0); return {disabled: true, mutations: 0};
  });
  await test('cleanup-disable-requires-confirmation', 'original-Jt-substituted-hooks', () => {
    const x = cleanup(); x.render().toggles[1].props.onChange(false); let view = x.render(); assert.equal(view.dialog.props.open, true); assert.equal(x.mutations[1].calls.length, 0);
    view.dialog.props.onOpenChange(false); assert.equal(x.render().dialog.props.open, false);
    x.render().toggles[1].props.onChange(false); view = x.render(); view.dialog.props.onConfirm(); assert.deepEqual(x.mutations[1].calls, [false]); return {cancelWrites: 0, confirmedValue: false};
  });

  const serialSource = source('initial-01', 'O7s');
  function serializer(options = {}) {
    const events = [], values = {}, first = options.first, keys = new WeakMap(); let n = 0;
    const context = vm.createContext({k7s: keys, cbe: {preferredViewers: {}}, async ac() {events.push(['read']); return {...values};}, async mg(owner, descriptor, next) {events.push(['write', clone(next)]); if (++n === 1 && first) await first.promise; Object.assign(values, next);}});
    vm.runInContext(serialSource, context); return {events, values, context, owner: {queryClient: {}}};
  }
  await test('preferred-viewers-serializes-and-preserves-other-keys', 'original-O7s-synthetic-setting-read-write', async () => {
    const gate = deferred(), x = serializer({first: gate}); const a = x.context.O7s(x.owner, 'a', 'viewer-a'), b = x.context.O7s(x.owner, 'b', 'viewer-b');
    await drain(); assert.equal(x.events.filter(x => x[0] === 'write').length, 1); gate.resolve(); await Promise.all([a, b]); assert.deepEqual(x.values, {a: 'viewer-a', b: 'viewer-b'}); return x.events;
  });
  await test('preferred-viewers-queue-continues-after-failure', 'original-O7s-synthetic-setting-read-write', async () => {
    const gate = deferred(), x = serializer({first: gate}); const a = x.context.O7s(x.owner, 'a', 'viewer-a'); const rejected = assert.rejects(a, /fixture/); const b = x.context.O7s(x.owner, 'b', 'viewer-b');
    await drain(); gate.reject(Error('fixture')); await rejected; await b; assert.deepEqual(x.values, {b: 'viewer-b'}); return x.events;
  });
  const rowSource = source('file-handlers-01', 'ue');
  function viewerRow() {
    const state = hooks(), requests = [], prefs = {}, options = [{server: 's', title: 'A'}, {server: 's', title: 'B'}];
    const context = vm.createContext({X: compiler, Z: state, Q: jsx, i: () => ({}), o: {}, _: () => prefs, m: {preferredViewers: {}},
      re: () => 'host.ext', te: () => options, Y: (a, b) => a.title.localeCompare(b.title), ie: (a,b,c,d,selected) => options.find(x => x.title === selected), z: x => x.title,
      a: 'menu', ee: 'trigger', b: {RadioGroup: 'group', RadioItem: 'option'}, B: 'icon', h: 'row', x: 'message', U: 'error',
      N(owner, key, value) {const gate = deferred(); requests.push({key, value, gate}); return gate.promise;}});
    vm.runInContext(rowSource, context);
    function render() {state.reset(); const tree = context.ue({hostId: 'host', extension: 'ext', catalog: options}); const menu = tree.props.control({}); return {tree, select: value => nodes(menu).find(x => x.type === 'option' && x.props.value === value).props.onSelect()};}
    return {render, requests};
  }
  await test('file-viewer-old-failure-does-not-override-new-selection', 'original-ue-substituted-hooks-and-resolvers', async () => {
    const x = viewerRow(); x.render().select('A'); x.render().select('B'); x.requests[0].gate.reject(Error('old-fixture')); await drain();
    let view = x.render(); assert.equal(view.tree.props.description, undefined); assert.equal(view.tree.props.control({}).props.children.props.value, 'B');
    x.requests[1].gate.resolve(); await drain(); assert.equal(x.render().tree.props.description, undefined); return {oldFailureIgnored: true, newerSelectionRetainedUntilItsCompletion: true};
  });
  await test('file-viewer-current-failure-shows-row-error', 'original-ue-substituted-hooks-and-resolvers', async () => {
    const x = viewerRow(); x.render().select('A'); x.requests[0].gate.reject(Error('current-fixture')); await drain(); assert.equal(x.render().tree.props.description.type, 'error'); return {rowError: true};
  });
  const normalization = vm.createContext({}); vm.runInContext(source('file-handlers-01', 'ce'), normalization); vm.runInContext(source('keyboard-01', 'Zt'), normalization);
  await test('file-extension-normalization', 'original-ce', () => {assert.equal(normalization.ce(' ...TsX '), 'tsx'); assert.equal(normalization.ce('...'), ''); return {normalized: 'tsx', emptyFilteredByPage: true};});
  await test('shortcut-search-sequence-boundary', 'original-Zt', () => {assert.equal(normalization.Zt('Ctrl+K Ctrl+C', 'Ctrl+K'), true); assert.equal(normalization.Zt('Ctrl+Key', 'Ctrl+K'), false); return {wholeStrokePrefix: true, characterPrefix: false};});
  const conflict = vm.createContext({p: x => x.split(' '), E: x => x.toLowerCase()}); vm.runInContext(source('command-row-01', 'Te'), conflict);
  await test('shortcut-prefix-conflict-both-directions', 'original-Te-with-parser-label-substitutes', () => {
    assert.equal(conflict.Te('Ctrl+K', 'Ctrl+K Ctrl+C', false), true); assert.equal(conflict.Te('Ctrl+K Ctrl+C', 'Ctrl+K', false), true); assert.equal(conflict.Te('Ctrl+K Ctrl+A', 'Ctrl+K Ctrl+B', false), false); return {prefixConflictsInBothDirections: true, divergentSecondStroke: false};
  });
  const result = {baselineId: 'codex-26.1007.30912-c5b273322a83', runtime: {node: process.versions.node, platform: process.platform, arch: process.arch},
    loadedSourceUnits: loaded, observations, counts: {isolatedSourceCases: observations.length, passed: observations.length, productScenariosExecuted: 0},
    substitutions: ['hooks and compiler cache recomputation', 'JSX nodes', 'query/mutation providers and delivery', 'path normalization/key helpers', 'catalog/viewer selection resolvers', 'settings/RPC/thread/pin/deletion/notification services', 'accelerator parsing/display'],
    qualifications: ['Original selected function bodies only; no React, client, actual query scheduling, real data store or service implementation runs.', 'No actual worktree, thread, preference, automation, credential or model task is read or changed.', 'Failure and concurrency cases are synthetic dependency outcomes, not actual service compatibility or durable recovery proof.'],
    originalClientRunsAdded: 0, modelSubmissionsAdded: 0, actualProductScenariosExecuted: 0};
  fs.writeFileSync(destination, JSON.stringify(result, null, 2) + '\n', {flag: 'wx'}); console.log(JSON.stringify(result.counts));
}
main().catch(error => {process.stderr.write(error.stack + '\n'); process.exitCode = 1;});
