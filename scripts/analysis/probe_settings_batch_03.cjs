// Execute saved first-party functions with synthetic hooks and services only.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const work = path.resolve(__dirname, '../../.analysis-local/settings-operation-batch-03');
const output = path.join(work, 'isolated-observations.json');
assert(!fs.existsSync(output));
const observations = [], loaded = [];
const clone = x => JSON.parse(JSON.stringify(x));
function source(folder, name) {
  const d = JSON.parse(fs.readFileSync(path.join(work, folder, 'source-contracts.json')));
  const u = d.units.find(x => x.name === name); assert(u, name);
  const b = fs.readFileSync(path.join(work, folder, u.sourceFilename));
  assert.equal(crypto.createHash('sha256').update(b).digest('hex'), u.spanHash);
  loaded.push({folder, ...u}); return b.toString('utf8');
}
function context(folder, names, globals) {
  const c = vm.createContext(globals);
  for (const n of names) vm.runInContext(source(folder, n), c);
  return c;
}
function hooks() {
  const slots = []; let cursor = 0;
  return {slots, reset() {cursor = 0;}, useState(v) {const i = cursor++; if (!(i in slots)) slots[i] = v;
    return [slots[i], x => {slots[i] = typeof x === 'function' ? x(slots[i]) : x;}];},
    useRef(v) {const i = cursor++; if (!(i in slots)) slots[i] = {current: v}; return slots[i];}, useId: () => 'fixture-id'};
}
const compiler = {c: n => Array(n).fill(Symbol.for('react.memo_cache_sentinel'))};
const jsx = {Fragment: 'fragment', jsx: (type, props) => ({type, props}), jsxs: (type, props) => ({type, props})};
const message = x => x?.id ?? 'fixture-label';
function nodes(v) {return Array.isArray(v) ? v.flatMap(nodes) : v && typeof v === 'object' ? [v, ...nodes(v.props?.children)] : [];}
async function drain() {for (let i = 0; i < 25; i++) await Promise.resolve();}
async function test(caseId, scope, run) {const observed = await run(); observations.push({caseId, scope, passed: true, observed});}

async function main() {
  const pure = context('general-appearance-01', ['ka', 'Aa', 'Ga'], {});
  await test('theme-hex-normalization', 'original-ka-Aa', () => {
    assert.equal(pure.ka('abc 123!!'), '#ABC123'); assert.equal(pure.Aa('#ABC123'), '#abc123');
    assert.equal(pure.Aa('#ABC'), null); assert.equal(pure.ka(''), '#');
    return {validSixDigitLowercased: true, partialNotCommitted: true};
  });
  await test('theme-monospace-filter', 'original-Ga', () => {
    assert.equal(pure.Ga({faces: [{isMonospaced: true}, {isMonospaced: false}]}, true), false);
    assert.equal(pure.Ga({faces: [{isMonospaced: true}]}, true), true);
    assert.equal(pure.Ga({faces: [{isMonospaced: false}]}, false), true);
    return {allFacesRequiredForMonospace: true};
  });
  await test('appearance-mode-nonoptimistic', 'original-dc-with-settings-and-JSX-substitutes', () => {
    const events = [], c = context('general-appearance-01', ['dc'], {Q: compiler, $: jsx, N: () => 'owner', P: 'store',
      L: () => ({formatMessage: message}), R: () => null, Xt: {theme: {key: 'appearanceTheme'}},
      V: (...args) => events.push(clone(args)), J: {theme: {id: 'theme'}},
      Fc: ['system', 'light', 'dark'].map(id => ({id, label: {id}})), xc: 'mode-option'});
    const tree = c.dc(), choices = nodes(tree).filter(x => x.type === 'mode-option');
    assert.equal(choices[0].props.selected, true); choices[2].props.onSelect();
    assert.deepEqual(events, [['owner', {key: 'appearanceTheme'}, 'dark', {optimistic: false}]]);
    return {fallback: 'system', writeOption: {optimistic: false}};
  });
  function numeric(name, value) {
    const events = [], h = hooks(), descriptor = {key: name, schema: {safeParse: n => ({success: Number.isFinite(n) && n >= 8 && n <= 40})}};
    const c = context('general-appearance-01', [name], {Q: compiler, kc: h, $: jsx, N: () => 'owner', P: 'store',
      L: () => ({formatMessage: message}), R: () => value, Xt: {sansFontSize: descriptor, codeFontSize: descriptor},
      V: (...a) => events.push(clone(a)), J: {uiFontSize: {}, codeFontSize: {}}, B: 'msg', I: 'row', Jr: 'input',
      bt: {sans: {min: 8, max: 40}, code: {min: 8, max: 40}}});
    return {events, input: c[name]().props.control.props.children[0].props.children};
  }
  for (const name of ['Cc', 'wc']) {
    await test(`appearance-${name}-numeric-commit`, 'original-numeric-handler-with-explicit-schema-substitute', () => {
      const {input, events} = numeric(name, 14); let target = {value: '16px'};
      input.props.onBlur({currentTarget: target}); assert.equal(target.value, '16'); assert.equal(events[0][2], 16);
      target = {value: 'bad'}; input.props.onBlur({currentTarget: target}); assert.equal(target.value, '14');
      target = {value: '14'}; input.props.onBlur({currentTarget: target}); assert.equal(events.length, 1);
      return {parseFloatPrefixAccepted: true, invalidRestored: true, unchangedSkipped: true, rangeSchemaSubstituted: true};
    });
  }
  await test('appearance-reset-partial-failure', 'original-Jo-with-settings-and-theme-hook-substitutes', async () => {
    const events = [], h = hooks(), owner = {get: k => k === 'changed' ? [{key: 'one', default: 1}, {key: 'two', default: 2}] : {danger: () => events.push('toast')}};
    const c = context('general-appearance-01', ['Jo', 'Yo'], {Xo: compiler, Zo: h, Qo: jsx, N: () => owner, P: 'store',
      L: () => ({formatMessage: message}), p: () => true, es: 'has-changes', $o: 'changed', Be: 'toast',
      qr: variant => ({hasAdvancedThemeChanges: true, resetAdvancedThemeSettings: async () => {events.push(variant); if (variant === 'dark') throw Error('fixture');}}),
      V: async (_, d) => events.push(d.key), _: 'button', B: 'message'});
    c.Jo({separateModes: true, onResetSeparateModes: () => events.push('presentation-reset')}).props.onClick();
    await drain(); assert.deepEqual(events, ['presentation-reset', 'one', 'two', 'light', 'dark', 'toast']);
    assert.equal(h.slots[0], false); return {allWritesAttempted: true, partialFailureToast: true, busyReleased: true};
  });
  function themeDialog(options = {}) {
    const events = [], h = hooks(), owner = {get: () => ({success: () => events.push('success'), danger: () => events.push('danger')})};
    const api = {canImportThemeString: s => s === 'valid', codeThemes: [], exportThemeString: () => 'export-fixture', fonts: {},
      importThemeString: async s => {events.push(['import', s]); if (options.reject) throw Error('fixture');}, selectedCodeTheme: {id: 'fixture'},
      setCodeThemeId: async () => {}, setAccountAccent: async () => {}, setFontsPatch: x => events.push(['fonts', clone(x)]),
      setThemePatch: x => events.push(['theme', clone(x)]), theme: {accent: '#123456', surface: '#ffffff', ink: '#000000', contrast: 50}};
    const c = context('general-appearance-01', ['Xa'], {lo: compiler, X: jsx, uo: h, N: () => owner, P: 'store',
      L: () => ({formatMessage: message}), J: {}, qr: () => api, co: () => 'Light', so: () => 'Light',
      Ve: async () => {events.push('copy'); return !options.copyFalse;}, Be: 'toast',
      Qa: 'section', $a: 'import-dialog', d: 'tooltip', _: 'button', mt: 'import-icon', vn: 'copy-icon', eo: 'preset',
      I: 'row', Fa: 'accent', Ta: 'color', Wa: 'font', oo: 'contrast', B: 'message', n: 'toggle', Za() {}});
    const render = section => {h.reset(); return c.Xa({section: section || 'visual', variant: 'light', showVariantTitle: false, showTranslucentSidebarToggle: true});};
    return {events, h, render, dialog: tree => nodes(tree.props.headerControl).find(x => x.type === 'import-dialog')};
  }
  for (const reject of [false, true]) await test(`theme-import-${reject ? 'failure' : 'success'}`, 'original-Xa-import-with-theme-service-substitute', async () => {
    const f = themeDialog({reject}); let tree = f.render(); f.dialog(tree).props.onOpenChange(true); f.dialog(tree).props.onValueChange(' valid ');
    tree = f.render(); f.dialog(tree).props.onSubmit(); await drain();
    assert.deepEqual(f.events, [['import', 'valid'], reject ? 'danger' : 'success']);
    assert.equal(f.h.slots[0], reject); assert.equal(f.h.slots[1], reject ? ' valid ' : '');
    return {dialogOpen: f.h.slots[0], draftRetained: reject};
  });
  await test('theme-import-cancel-and-empty', 'original-Xa-import-presentation', async () => {
    const f = themeDialog(); let tree = f.render(); f.dialog(tree).props.onValueChange('draft'); f.dialog(tree).props.onOpenChange(false);
    assert.equal(f.h.slots[1], ''); tree = f.render(); f.dialog(tree).props.onSubmit(); await drain();
    assert.deepEqual(f.events, ['danger']); return {cancelClearsDraft: true, emptyNotSubmitted: true};
  });
  await test('theme-copy-and-color-font-patches', 'original-Xa-with-clipboard-and-theme-substitutes', async () => {
    const f = themeDialog({copyFalse: true}), tree = f.render();
    const copy = nodes(tree.props.headerControl).find(x => x.type === 'button' && x.props.onClick); copy.props.onClick(); await drain();
    assert.deepEqual(f.events, ['copy']);
    const controls = nodes(tree).filter(x => x.type === 'row').map(x => x.props.control);
    controls.find(x => x.type === 'accent').props.onCustomColorChange('#abcdef');
    controls.find(x => x.type === 'font').props.onChange('fixture-font', {family: 'Fixture'});
    assert.deepEqual(f.events.slice(1), [['theme', {accent: '#abcdef', accentSource: 'custom'}], ['fonts', {ui: 'fixture-font', uiFace: {family: 'Fixture'}}]]);
    return {clipboardFalseNoSuccessToast: true, customAccentSourceSet: true, fontFacePreserved: true};
  });
  for (const absent of [true, false]) await test(`appshot-host-${absent ? 'absent' : 'forward'}`, 'original-ve-with-host-adapter-substitute', async () => {
    const events = [], c = context('appshots-01', ['ve'], {C: absent ? {} : {appshot: {setHotkey: async v => {events.push(v); return {success: true};}}}});
    if (absent) await assert.rejects(c.ve({hotkey: 'DoubleShift'}), /unavailable/);
    else {await c.ve({hotkey: null}); await c.ve({hotkey: 'DoubleShift'}); assert.deepEqual(events, [null, 'DoubleShift']);}
    return {hostAbsent: absent, forwarded: events};
  });
  function hotkey(options = {}) {
    const events = [], h = hooks(); let configured = options.configured ?? 'DoubleShift';
    const owner = {query: {setData: (_, state) => events.push(['state', clone(state)])}};
    const mutation = {isPending: !!options.pending, mutateAsync: async input => {
      events.push(['mutate', clone(input)]); if (options.throw) throw Error('host-fixture');
      const result = {success: !options.failure, error: options.failure ? 'rejected' : undefined, state: {configuredHotkey: input.hotkey}};
      config.onSuccess(result); return result;
    }}; let config;
    const c = context('appshots-01', ['_e'], {Y: compiler, be: h, X: jsx, a: () => owner, s: 'store',
      T: () => ({formatMessage: message}), i: key => key === 'capability' ? true : {data: {configuredHotkey: configured, supported: true}},
      se: 'capability', re: 'state', ee: () => ({platform: options.platform || 'windows'}), v: () => key => events.push(['refresh', key]),
      N: x => {config = x; return mutation;}, ve: () => {}, J: 'keymap', O: (...a) => events.push(['analytics', clone(a[2])]), c: 'event',
      Z: {doubleAlt: {id: 'alt'}, doubleShift: {id: 'shift'}}, xe: [], W: x => x,
      y: 'row', o: 'menu', j: {Section: 'section', Item: 'item'}, z: 'check', ie: 'trigger', M: 'message', ye: 'description'});
    const render = () => {h.reset(); return c._e();};
    return {events, h, render, items: tree => nodes(tree.props.control).filter(x => x.type === 'item')};
  }
  for (const kind of ['success', 'failure', 'throw']) await test(`appshot-hotkey-${kind}`, 'original-_e-handler-with-mutation-lifecycle-substitute', async () => {
    const f = hotkey({failure: kind === 'failure', throw: kind === 'throw'}); f.items(f.render())[0].props.onSelect(); await drain();
    assert.equal(f.h.slots[0], kind === 'success' ? null : kind === 'throw' ? 'Error: host-fixture' : 'rejected');
    assert.equal(f.events.some(x => x[0] === 'analytics'), kind === 'success');
    return {kind, inlineError: f.h.slots[0], analyticsOnSuccessOnly: true, queryLifecycleSubstituted: true};
  });
  await test('appshot-hotkey-same-and-disable', 'original-_e-menu-callbacks', async () => {
    const f = hotkey(); const items = f.items(f.render()); items[1].props.onSelect(); await drain(); assert.equal(f.events.length, 0);
    items[2].props.onSelect(); await drain(); assert.deepEqual(f.events[0], ['mutate', {hotkey: null}]);
    return {sameHotkeySkipped: true, disableForwardsNull: true};
  });
  const notificationPure = context('notifications-01', ['Ze', 'nt'], {});
  await test('notification-immutable-category-channel-patch', 'original-Ze', () => {
    const input = {settings: [{category: 'tasks', options: [{channel: 'email', enabled: false}, {channel: 'push', enabled: true}]}, {category: 'other', options: []}]};
    const result = notificationPure.Ze(input, {category: 'tasks', channel: 'email'}, true);
    assert.equal(input.settings[0].options[0].enabled, false); assert.equal(result.settings[0].options[0].enabled, true);
    assert.equal(result.settings[1], input.settings[1]); return {unmatchedCategoryIdentityRetained: true, originalNotMutated: true};
  });
  await test('notification-contact-channel-filter', 'original-nt', () => {
    assert.equal(notificationPure.nt('email', false, true), false); assert.equal(notificationPure.nt('sms', true, false), false);
    assert.equal(notificationPure.nt('push', false, false), true); return {emailAndSmsRequireContacts: true, otherChannelsAllowed: true};
  });
  await test('notification-page-capability-guard', 'original-ct-with-atom-substitute', () => {
    const c = context('notifications-01', ['ct'], {dt: compiler, $: jsx, s: () => false, c: 'capability', Ce: 'title', De: 'page'});
    assert.equal(c.ct().props.children, null); return {capabilityFalseNoAccountSettingsChildren: true, selectedProductModeNotInferred: true};
  });
  function account() {
    const h = hooks(), events = [], effect = []; let config, data = {settings: [{category: 'tasks', options: [{channel: 'email', enabled: false}]}]};
    const client = {cancelQueries: async () => events.push('cancel'), getQueryData: () => data,
      setQueryData: (_, f) => {data = f(data); events.push(['cache', data.settings[0].options[0].enabled]);}, invalidateQueries: x => events.push(['invalidate', clone(x)])};
    const store = {get: k => k === 'account' ? 'a' : k === 'user' ? 'u' : {danger: () => events.push('toast')}};
    const c = context('notifications-01', ['Ye', 'Ze'], {Z: compiler, Q: jsx, at: {...h, useEffect: f => effect.push(f())},
      ee: () => store, te: 'store', ie: () => ({formatMessage: message}), re: () => client, ot: 'account-notifications',
      n: {}, P: () => ({data, isPending: true}), ve: {ONE_MINUTE: 60000}, v: 'toast', de: x => {config = x; return {mutate() {}};}, Xe() {}, rt: 'loading', F: 'account', ge: 'user'});
    c.Ye({accountId: 'a', userId: 'u'});
    const request = enabled => ({accountId: 'a', userId: 'u', category: 'tasks', channel: 'email', enabled, controller: new AbortController()});
    return {config, events, request, effect, current: () => data.settings[0].options[0].enabled};
  }
  await test('notification-stale-success-and-current-rollback', 'original-Ye-mutation-callbacks-with-query-substitute', async () => {
    const f = account(), a = f.request(true), b = f.request(false), ca = await f.config.onMutate(a), cb = await f.config.onMutate(b);
    f.config.onSuccess({settings: [{category: 'tasks', options: [{channel: 'email', enabled: true}]}]}, a, ca);
    assert.equal(f.current(), false); f.config.onError(Error('fixture'), b, cb); assert.equal(f.current(), true);
    return {oldSuccessIgnored: true, latestFailureRestoresPreviousOptimisticValue: true};
  });
  await test('notification-stale-error-toasts-without-rollback', 'original-Ye-mutation-callbacks', async () => {
    const f = account(), a = f.request(true), b = f.request(false), ca = await f.config.onMutate(a); await f.config.onMutate(b);
    f.config.onError(Error('fixture'), a, ca); assert.equal(f.current(), false); assert.equal(f.events.filter(x => x === 'toast').length, 1);
    return {staleErrorStillToasts: true, latestCacheNotRolledBack: true};
  });
  await test('notification-aborted-error-silent', 'original-Ye-abort-check', async () => {
    const f = account(), a = f.request(true), ca = await f.config.onMutate(a); a.controller.abort(); f.config.onError(Error('fixture'), a, ca);
    assert.equal(f.current(), true); assert.equal(f.events.includes('toast'), false); return {abortSuppressesRollbackAndToast: true};
  });
  await test('notification-patch-preaborted-no-request', 'original-Xe-with-network-substitute', async () => {
    const events = [], c = context('notifications-01', ['Xe'], {n: {safePatch: (...a) => events.push(a)}}), controller = new AbortController(); controller.abort();
    assert.throws(() => c.Xe({controller})); assert.equal(events.length, 0); return {networkRequests: 0};
  });
  await test('notification-system-settings-optional-host', 'original-ut-with-host-substitute', async () => {
    const c = context('notifications-desktop-01', ['ut'], {E: {}}); assert.equal(await c.ut(), undefined);
    let called = 0; c.E.systemPermissions = {openNotificationSettings: async () => called++}; await c.ut(); assert.equal(called, 1);
    return {missingHostNoop: true, presentHostCalled: true};
  });
  function themeProvider(options = {}) {
    const events = [], initial = {codeThemeId: 'base', theme: {accent: '#123456', contrast: 50, opaqueWindows: false, fonts: {ui: 'UI', content: 'Content', code: 'Code'}}};
    let pending = null, writes = 0;
    const state = {pendingSnapshot$: 'pending', pendingWriteCount: 0, themeWriteQueue: Promise.resolve(), committedSnapshot: initial,
      editRevision: 0, accentEditRevision: 0, hasPartialThemeSettingsWrite: false, getSnapshot: () => pending ?? state.committedSnapshot};
    const owner = {get: k => k === 'state' ? state : k === 'system' ? {data: {isSystemBackdropSupported: true}} : null,
      set: (_, v) => {pending = v;}, queryClient: {cancelQueries: async () => events.push('cancel')}};
    const c = context('theme-provider-01', ['G1s'], {a0s: compiler, Di: () => owner, q: 'store',
      t0s: () => ({chromeThemeSetting: 'chrome', codeThemeSetting: 'code'}), sp: key => key === 'chrome' ? initial.theme : 'base',
      G: k => k === 'system' ? {data: {isSystemBackdropSupported: true}} : null, aq: 'accent', Gm: 'system',
      KJ: value => value ?? {contrast: 0, opaqueWindows: false, fonts: {}}, Cya: () => [], Sya: id => ({id}),
      ao: () => ({pendingSnapshot$: 'pending'}), C8: 'state', Ree() {},
      jHt: (promise, callback) => promise.finally(callback), Io: x => [x], Qi: () => events.push('refresh'),
      Kf: async (key, value) => {writes++; events.push([key, clone(value)]); if (options.failAt?.includes(writes)) throw Error('write-fixture');},
      X1s() {}, Y1s() {}, J1s() {}, q1s() {}, K1s() {}, Z1s() {}, aFe: () => null, Q1s() {},
      mLe: () => ({accountId: 'synthetic'}), n0s: (theme, patch) => ({...theme, ...patch, fonts: {...theme.fonts, ...patch.fonts}}),
      e0s: () => ({codeThemeId: 'imported', theme: {...initial.theme, accent: '#abcdef'}}), r0s: () => 'export',
      mba: options.preset ?? (async () => ({accent: '#abcdef'}))});
    return {api: c.G1s('light'), events, state, pending: () => pending};
  }
  for (const rollbackFailure of [false, true]) await test(`theme-pair-write-rollback-${rollbackFailure ? 'failure' : 'success'}`, 'original-G1s-queue-and-compensation-with-transport-finalizer-substitutes', async () => {
    const f = themeProvider({failAt: rollbackFailure ? [2, 3] : [2]}); await assert.rejects(f.api.importThemeString('fixture'), /write-fixture/);
    assert.deepEqual(f.events.filter(Array.isArray).map(x => x[0]), ['chrome', 'code', 'chrome']);
    assert.equal(f.state.hasPartialThemeSettingsWrite, rollbackFailure); assert.equal(f.state.pendingWriteCount, 0); assert.equal(f.pending(), null);
    return {compensationAttempted: true, partialFlag: f.state.hasPartialThemeSettingsWrite, pendingReleased: true, finalizerSubstituted: true};
  });
  await test('theme-queue-continues-after-failure', 'original-G1s-per-variant-queue-with-transport-substitute', async () => {
    const f = themeProvider({failAt: [2]});
    const a = f.api.importThemeString('one'), b = f.api.importThemeString('two'); await assert.rejects(a); await b;
    assert.deepEqual(f.events.filter(Array.isArray).map(x => x[0]), ['chrome', 'code', 'chrome', 'chrome', 'code']);
    assert.equal(f.state.committedSnapshot.codeThemeId, 'imported'); assert.equal(f.state.pendingWriteCount, 0);
    return {laterWriteCompleted: true, committed: 'imported'};
  });
  await test('theme-stale-preset-load-suppressed', 'original-G1s-edit-revision-with-preset-loader-substitute', async () => {
    let resolve; const deferred = new Promise(r => {resolve = r;}); const f = themeProvider({preset: () => deferred});
    const loading = f.api.setCodeThemeId('slow'); f.api.setThemePatch({contrast: 80}); await f.state.themeWriteQueue;
    resolve({accent: '#abcdef'}); await loading;
    assert.deepEqual(f.events.filter(Array.isArray).map(x => x[0]), ['chrome']);
    assert.equal(f.state.committedSnapshot.theme.contrast, 80); return {newerEditPreserved: true, stalePresetPairNotWritten: true};
  });
  fs.writeFileSync(output, JSON.stringify({baselineId: 'codex-26.1007.30912-c5b273322a83',
    scope: 'Saved source functions with synthetic fixtures; no original-client, OS, personal-data, model, real storage or real network operations.',
    loadedSourceUnits: loaded, observations, counts: {isolatedSourceCases: observations.length, passed: observations.length, productScenariosExecuted: 0},
    substitutes: ['React hooks/compiler cache/JSX', 'query and mutation lifecycle', 'settings schemas and writers', 'theme/clipboard/font services', 'host hotkey/permissions', 'account/query/network adapters'],
    modelSubmissionsAdded: 0, originalClientRunsAdded: 0}, null, 2) + '\n', {flag: 'wx'});
  console.log(JSON.stringify({passed: observations.length, productScenariosExecuted: 0, output}));
}
main().catch(e => {console.error(e.stack); process.exitCode = 1;});
