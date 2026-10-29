// Execute saved application functions with synthetic providers and a deterministic clock.
// No application, network, credential, filesystem-store or automation service is loaded.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const work = path.join(root, '.analysis-local/git-settings-contract-work');
const destination = path.join(work, 'isolated-observations-02.json');
assert(!fs.existsSync(destination));
const hash = data => crypto.createHash('sha256').update(data).digest('hex');
const records = [];
const loaded = [];
const clone = value => value == null ? value : JSON.parse(JSON.stringify(value));
function source(folder, name) {
  const contracts = JSON.parse(fs.readFileSync(path.join(work, folder, 'source-contracts.json')));
  const unit = contracts.units.find(x => x.name === name);
  assert(unit, name);
  const bytes = fs.readFileSync(path.join(work, folder, unit.sourceFilename));
  assert.equal(hash(bytes), unit.spanHash);
  loaded.push({folder, name, ...unit});
  return bytes.toString('utf8');
}
async function test(id, scope, run) {
  const result = await run();
  records.push({caseId: id, scope, passed: true, observed: result});
}
const writerSource = source('shared-01', 'rAn');
const setterSource = source('shared-01', 'oAn');
const readerSource = source('shared-01', 'aAn');
function settingContext(options = {}) {
  const events = [], initial = {configuredValues: {fixture: 'old'}, values: {fixture: 'old', other: 1}};
  let data = clone(initial);
  const snapshot = {
    queryKey: ['fixture-settings'],
    cancel() { events.push(['cancel']); return options.cancelReject ? Promise.reject(Error('cancel-fixture')) : Promise.resolve(); },
    getData() { return data; },
    setData(value) { data = value; events.push(['cache', clone(value)]); },
    async invalidate() { events.push(['invalidate']); if (options.invalidateReject) throw Error('invalidate-fixture'); },
  };
  const context = vm.createContext({VK: 'fixture-query', GG: key => events.push(['notify', clone(key)]),
    async oAn(setting, value) { events.push(['write', setting.key, value]); if (options.writeReject) throw Error('write-fixture'); if (options.concurrentData) data = clone(options.concurrentData); }});
  vm.runInContext(writerSource, context);
  return {events, initial, snapshot, context, data: () => clone(data), owner: {query: {snapshot: () => snapshot}}};
}
async function main() {
  await test('writer-optimistic-success', 'saved-rAn', async () => {
    const x = settingContext(); await x.context.rAn(x.owner, {key: 'fixture'}, 'new');
    assert.deepEqual(x.events.map(x => x[0]), ['cancel', 'cache', 'write', 'invalidate', 'notify']);
    assert.equal(x.data().values.fixture, 'new'); return x.events;
  });
  await test('writer-optimistic-rollback', 'saved-rAn', async () => {
    const x = settingContext({writeReject: true}); await assert.rejects(x.context.rAn(x.owner, {key: 'fixture'}, 'new'), /write-fixture/);
    assert.deepEqual(x.data(), x.initial); assert.deepEqual(x.events.map(x => x[0]), ['cancel', 'cache', 'write', 'cache', 'invalidate', 'notify']); return x.events;
  });
  await test('writer-nonoptimistic-merges-current-cache', 'saved-rAn', async () => {
    const x = settingContext({concurrentData: {configuredValues: {other: 7}, values: {other: 7}}});
    await x.context.rAn(x.owner, {key: 'fixture'}, 'new', {optimistic: false});
    assert.deepEqual(x.data(), {configuredValues: {other: 7, fixture: 'new'}, values: {other: 7, fixture: 'new'}});
    assert.deepEqual(x.events.map(x => x[0]), ['cancel', 'write', 'cache', 'invalidate', 'notify']); return x.events;
  });
  await test('writer-cancel-provider-rejection-before-try', 'saved-rAn-injected-provider-failure', async () => {
    const x = settingContext({cancelReject: true}); await assert.rejects(x.context.rAn(x.owner, {key: 'fixture'}, 'new'), /cancel-fixture/);
    assert.equal(x.data().values.fixture, 'new'); assert.deepEqual(x.events.map(x => x[0]), ['cancel', 'cache']);
    return {events: x.events, qualification: 'An injected cancel rejection; actual query-provider rejection behavior is unverified.'};
  });
  await test('writer-invalidate-rejection-skips-notify', 'saved-rAn-injected-provider-failure', async () => {
    const x = settingContext({invalidateReject: true}); await assert.rejects(x.context.rAn(x.owner, {key: 'fixture'}, 'new'), /invalidate-fixture/);
    assert.equal(x.data().values.fixture, 'new'); assert(!x.events.some(x => x[0] === 'notify')); return x.events;
  });
  for (const host of [true, false]) {
    await test('settings-service-' + (host ? 'host' : 'fallback'), 'saved-oAn-aAn', async () => {
      const events = [];
      const context = vm.createContext({e6: host ? {settings: {
        async write(key, value) { events.push(['host-write', key, value]); },
        async read(key) { events.push(['host-read', key]); return {effective: 'effective-fixture'}; },
      }} : undefined, async $G(method, body) { events.push([method, clone(body)]); return {value: null}; }});
      vm.runInContext(setterSource + '\n' + readerSource, context);
      await context.oAn({key: 'fixture'}, 'new'); const value = await context.aAn({key: 'fixture', default: 'default-fixture'});
      assert.equal(value, host ? 'effective-fixture' : 'default-fixture');
      assert.equal(events[0][0], host ? 'host-write' : 'set-setting'); return {events, value};
    });
  }

  const watcherSource = ['v', 'b', 'C', 'assignment-D', 'assignment-T'].map(x => source('watcher-02', x)).join('\n');
  const classifierSource = source('classifier-01', 'F9n');
  const bounded = JSON.parse(fs.readFileSync(path.join(work, 'supplemental-units.json'))).units.find(x => x.name === 'gM');
  const heartbeatSource = fs.readFileSync(path.join(work, 'shared-01', bounded.sourceFilename));
  assert.equal(hash(heartbeatSource), bounded.spanHash); loaded.push(bounded);
  function watcherContext(items, options = {}) {
    const events = [], context = vm.createContext({
      async a(method, request) {
        events.push([method, clone(request)]);
        if (method === 'list-automations') return {items};
        if (options.updateReject) throw Error('update-fixture');
        return {item: options.invalidItem ? {kind: 'cron'} : {...request.params, kind: 'heartbeat'}};
      },
    });
    vm.runInContext(heartbeatSource + '\nvar Aoe=gM,r=gM;\n' + classifierSource + '\nvar f=F9n,D,T;\n' + watcherSource, context);
    return {context, events};
  }
  const marker = 'This is a heartbeat turn. Continue automatically fixing this pull request.';
  const item = (id, status = 'ACTIVE', kind = 'heartbeat', hasMarker = true) => ({id, status, kind,
    name: 'synthetic watcher', targetThreadId: 'owned-fixture-thread', model: null, reasoningEffort: null, rrule: 'fixture-rule',
    prompt: '## Pull request fix automation:\nSynthetic header\n' + (hasMarker ? marker + '\n' : '') + 'old synthetic body'});
  await test('watcher-selection-and-payload', 'saved-v-b-C-F9n-gM', async () => {
    const x = watcherContext([item('active'), item('paused', 'PAUSED'), item('cron', 'ACTIVE', 'cron'), item('no-marker', 'ACTIVE', 'heartbeat', false)]);
    const result = await x.context.v({autoMerge: false, instructions: '  synthetic instructions  '});
    assert.equal(result.length, 1); const updates = x.events.filter(x => x[0] === 'automation-update'); assert.equal(updates.length, 1);
    const p = updates[0][1].params; assert.equal(p.id, 'active'); assert.equal(p.status, 'ACTIVE'); assert.equal(p.targetThreadId, 'owned-fixture-thread');
    assert(p.prompt.startsWith('## Pull request fix automation:\nSynthetic header\n' + marker));
    assert(p.prompt.endsWith('synthetic instructions')); assert(!p.prompt.includes('old synthetic body')); return {updates: updates.length, retainedFields: Object.keys(p), promptPrefixPreserved: true, customInstructionsTrimmed: true};
  });
  await test('watcher-identical-prompt-no-write', 'saved-v-b-C', async () => {
    const first = watcherContext([item('active')]); await first.context.v({autoMerge: true, instructions: ''});
    const updated = first.events.find(x => x[0] === 'automation-update')[1].params;
    const x = watcherContext([updated]); const result = await x.context.v({autoMerge: true, instructions: ''});
    assert.equal(result.length, 0); assert.deepEqual(x.events.map(x => x[0]), ['list-automations']); return x.events;
  });
  await test('watcher-update-failure', 'saved-v-b', async () => {
    const x = watcherContext([item('active')], {updateReject: true}); await assert.rejects(x.context.v({autoMerge: false, instructions: ''}), /update-fixture/);
    return x.events.map(x => x[0]);
  });
  await test('watcher-invalid-response-kind', 'saved-v-b', async () => {
    const x = watcherContext([item('active')], {invalidItem: true}); await assert.rejects(x.context.v({autoMerge: false, instructions: ''}), /could not be updated/);
    return x.events.map(x => x[0]);
  });

  const mainUnits = JSON.parse(fs.readFileSync(path.join(work, 'main-01/materialized-providers.json'))).units;
  const storeUnit = mainUnits.find(x => x.name === 'AL');
  const storeBytes = fs.readFileSync(path.join(work, 'main-01', storeUnit.sourceFilename));
  assert.equal(hash(storeBytes), storeUnit.spanHash); loaded.push(storeUnit);
  function storeHarness() {
    const events = [], values = {};
    const store = {set(key, value) { values[key] = value; events.push(['set', key, value]); }, get: key => values[key], async flush() { events.push(['flush']); }};
    const context = vm.createContext({sL: class {async readForAgent() { return {settings: {...values}, effectiveSettings: {...values}}; }}, DL: class {dispose() {}},
      r: {M: key => ({key, agentAccess: key === 'git-commit-instructions' ? 'read-only' : 'read-write'}), F: (key, value) => value},
    });
    vm.runInContext('var AL;\n' + storeBytes + '\n', context);
    const instance = new context.AL(store, (key, value) => events.push(['afterWrite', key, value]));
    return {events, values, instance};
  }
  await test('store-ui-write-does-not-await-flush', 'saved-AL-substituted-store', async () => {
    const x = storeHarness(); await x.instance.write('git-commit-instructions', 'synthetic');
    assert.deepEqual(x.events.map(x => x[0]), ['set', 'afterWrite']); return {events: x.events, durableFileIOExercised: false};
  });
  await test('store-agent-write-rejects-read-only-key', 'saved-AL-substituted-store-and-descriptors', async () => {
    const x = storeHarness(); await assert.rejects(x.instance.writeForAgent({'git-commit-instructions': 'synthetic'}), /cannot be written by Codex/);
    assert.equal(x.events.length, 0); return {events: []};
  });
  await test('store-agent-write-explicitly-flushes', 'saved-AL-substituted-store-and-descriptors', async () => {
    const x = storeHarness(); await x.instance.writeForAgent({'git-branch-prefix': 'synthetic/'});
    assert.deepEqual(x.events.map(x => x[0]), ['set', 'afterWrite', 'flush']); return {events: x.events, schemaCastingSubstituted: true};
  });

  // A small hook lifecycle substitute exercises the saved autosave component;
  // it supplies dependency behavior explicitly and does not run React/TanStack.
  const autosaveSource = source('local-01', 'me');
  function autosaveHarness(savedValue = 'base') {
    const slots = [], effects = [], pendingEffects = [], timers = new Map(), mutations = [], keys = [], notices = [], saves = [], onSaved = [];
    let cursor = 0, now = 0, nextTimer = 1;
    const timerApi = {setTimeout(fn, delay) { const id = nextTimer++; timers.set(id, {fn, at: now + delay}); return id; }, clearTimeout(id) { timers.delete(id); }};
    const hooks = {
      useState(initial) { const i = cursor++; if (!(i in slots)) slots[i] = initial; return [slots[i], value => { slots[i] = typeof value === 'function' ? value(slots[i]) : value; }]; },
      useRef(value) { const i = cursor++; if (!(i in slots)) slots[i] = {current: value}; return slots[i]; },
      useEffectEvent(fn) { const i = cursor++; if (!(i in slots)) slots[i] = {fn, stable: (...args) => slots[i].fn(...args)}; slots[i].fn = fn; return slots[i].stable; },
      useEffect(fn, deps) { const i = cursor++; const prior = effects[i]; if (!prior || deps.some((x, j) => !Object.is(x, prior.deps[j]))) pendingEffects.push({i, fn, deps}); },
    };
    const context = vm.createContext({ge: {c: n => Array(n).fill(Symbol.for('react.memo_cache_sentinel'))}, G: hooks,
      s: () => ({get: () => ({danger: text => notices.push(text)})}), c: {}, g: {}, ee: () => ({formatMessage: x => x.id}),
      window: timerApi, _e: 3000, ve: 3000, ce: x => keys.push(x), he: 'instructions-control', K: {jsx: (type, props) => ({type, props})},
      ne(config) {
        const i = cursor++; if (!(i in slots)) slots[i] = {isPending: false, mutate: value => mutations.push({value, owner: slots[i], config: slots[i].config})};
        slots[i].config = config; return slots[i];
      },
    });
    vm.runInContext(autosaveSource, context);
    const props = {savedValue, saveScope: 'fixture', save: async value => saves.push(value), onSaved: value => onSaved.push(value)};
    let rendered;
    function render() {
      cursor = 0; rendered = context.me(props);
      while (pendingEffects.length) { const x = pendingEffects.shift(); effects[x.i]?.cleanup?.(); effects[x.i] = {deps: x.deps, cleanup: x.fn()}; }
      return rendered.props;
    }
    function advance(ms) {
      const end = now + ms;
      while (true) { const next = [...timers].filter(([, x]) => x.at <= end).sort((a, b) => a[1].at - b[1].at)[0]; if (!next) break; now = next[1].at; timers.delete(next[0]); next[1].fn(); }
      now = end;
    }
    function unmount() { for (const effect of effects) effect?.cleanup?.(); }
    async function success(index) { const m = mutations[index]; await m.config.mutationFn(m.value); m.config.onSuccess(undefined, m.value); }
    function failure(index) { const m = mutations[index]; m.config.onError(Error('fixture'), m.value); }
    return {render, advance, unmount, success, failure, mutations, keys, notices, saves, onSaved, props};
  }
  await test('autosave-delay-and-no-duplicate-flush', 'saved-me-substituted-hooks', () => {
    const h = autosaveHarness(); h.render().onChange('edited'); assert.equal(h.render().actionState, 'dirty'); h.advance(2999); assert.equal(h.mutations.length, 0);
    h.advance(1); assert.equal(h.mutations.length, 1); h.unmount(); assert.equal(h.mutations.length, 1); return {delayMs: 3000, mutations: h.mutations.length};
  });
  await test('autosave-revert-before-save', 'saved-me-substituted-hooks', () => {
    const h = autosaveHarness(); h.render().onChange('edited'); h.render().onChange('base'); assert.equal(h.render().actionState, 'idle'); h.advance(3000); assert.equal(h.mutations.length, 0); return {mutations: 0};
  });
  await test('autosave-failed-snapshot-needs-explicit-retry', 'saved-me-substituted-hooks', () => {
    const h = autosaveHarness(); h.render().onChange('edited'); h.render(); h.advance(3000); h.failure(0); h.unmount(); assert.equal(h.mutations.length, 1);
    h.render().onSave(); assert.equal(h.mutations.length, 2); assert.equal(h.notices.length, 1); return {automaticMutations: 1, afterExplicitRetry: 2, errorNotices: 1};
  });
  await test('autosave-unmount-flushes-new-draft', 'saved-me-substituted-hooks', () => {
    const h = autosaveHarness(); h.render().onChange('edited'); h.render(); h.unmount(); assert.equal(h.mutations.length, 1); return {mutations: 1, value: h.mutations[0].value.value};
  });
  await test('autosave-old-success-preserves-newer-draft', 'saved-me-substituted-hooks', async () => {
    const h = autosaveHarness(); h.render().onChange('old-draft'); h.render(); h.advance(3000); h.render().onChange('new-draft'); h.render(); await h.success(0);
    const p = h.render(); assert.equal(p.currentValue, 'new-draft'); assert.equal(p.actionState, 'dirty'); assert.deepEqual(h.onSaved, ['old-draft']); return {currentValue: p.currentValue, state: p.actionState, callbackValues: h.onSaved};
  });
  await test('autosave-pending-explicit-save-guard', 'saved-me-substituted-hooks', () => {
    const h = autosaveHarness(); h.render().onChange('first'); h.render(); h.advance(3000); h.mutations[0].owner.isPending = true;
    let p = h.render(); p.onChange('second'); p = h.render(); p.onSave(); assert.equal(h.mutations.length, 1); assert.equal(h.keys.at(-1).enabled, false);
    h.advance(3000); assert.equal(h.mutations.length, 2); return {explicitSaveSuppressed: true, automaticSubmissionOfNewSnapshot: true, mutationScopeProviderNotExecuted: true};
  });
  await test('autosave-success-feedback-timeout', 'saved-me-substituted-hooks', async () => {
    const h = autosaveHarness(); h.render().onChange('edited'); h.render(); h.advance(3000); await h.success(0); h.props.savedValue = 'edited'; assert.equal(h.render().actionState, 'saved');
    h.advance(3000); assert.equal(h.render().actionState, 'idle'); return {savedFeedbackMs: 3000};
  });
  const result = {
    baselineId: 'codex-26.1007.30912-c5b273322a83', runtime: {node: process.versions.node, platform: process.platform, arch: process.arch},
    loadedSourceUnits: loaded, observations: records,
    counts: {isolatedSourceCases: records.length, passed: records.length, productScenariosExecuted: 0},
    substitutions: ['query snapshot and settings providers', 'automation list/update request', 'React hooks/JSX lifecycle substitute', 'mutation-hook delivery and pending state', 'deterministic timer', 'notification sinks', 'main store, base reader and descriptor/schema facade'],
    qualifications: ['Original saved function bodies run; the client, React and TanStack implementations do not.', 'The original heartbeat kind predicate is bounded and source-checked; original F9n/gM predicates check selection and update response kind.', 'Injected provider failures are conditional source behavior, not proof that real providers can produce those failures.', 'No real preferences, automations, threads, credentials, services or files are changed.'],
    targetCodeExecuted: true, originalClientRunsAdded: 0, modelSubmissionsAdded: 0,
  };
  fs.writeFileSync(destination, JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
  console.log(JSON.stringify(result.counts));
}
main().catch(error => { process.stderr.write(String(error.stack) + '\n'); process.exitCode = 1; });
