// Frozen pure functions/callbacks; every receiver and dataset is synthetic.
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const assert = require('node:assert/strict'), crypto = require('node:crypto');
const root = process.cwd(), base = 'codex-26.1007.30912-c5b273322a83';
const work = path.join(root, '.analysis-local/settings-history-batch08-work');
const frozen = path.join(root, '.analysis-local/baselines', base, 'extracted');
const meta = Object.fromEntries(['browser-use', 'chronicle', 'voice'].map(page =>
  [page, JSON.parse(fs.readFileSync(path.join(work, page, 'source-contracts.json')))]));
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const plain = value => JSON.parse(JSON.stringify(value));
const used = [], cases = [];
function exact(page, record) {
  const bytes = fs.readFileSync(path.join(frozen, record.sourcePath.replace(/^app.asar\//, '')));
  assert.equal(sha(bytes), record.sourceHash);
  const span = bytes.subarray(record.byteRange.start, record.byteRange.endExclusive);
  assert.equal(sha(span), record.spanHash); used.push({page, ...record}); return span.toString();
}
function unit(page, name, context = {}) {
  const record = meta[page].units.find(item => item.name === name); assert(record, name);
  return vm.runInNewContext(`(${exact(page, record)})`, context, {timeout: 1000});
}
function callback(page, name, match, context = {}) {
  const records = meta[page].callbacks.filter(item => item.unit === name)
    .filter(item => match(exact(page, item)));
  assert.equal(records.length, 1, name);
  return vm.runInNewContext(`(${exact(page, records[0])})`, context, {timeout: 1000});
}
async function check(id, fn) { await fn(); cases.push({id, passed: true}); }

(async () => {
  const classify = unit('browser-use', 'ea', {URL});
  await check('BROWSER-PRIVILEGED-SETTINGS-URL-CLASSIFICATION', () => {
    assert.equal(classify('chrome://settings/content/siteDetails?site=https://example.test'), 'siteDetails');
    assert.equal(classify('chrome://settings/cookies'), 'cookies');
    assert.equal(classify('chrome://settings/handlers'), 'handlers');
    assert.equal(classify('https://settings/content/siteDetails'), null);
    assert.equal(classify('chrome://other/content/siteDetails'), null);
    assert.equal(classify('not a URL'), null);
  });
  await check('BROWSER-SITE-DETAILS-INITIAL-HISTORY', () => {
    const initial = unit('browser-use', 'Yi', {ea: classify, Ze: 'chrome://settings/content'});
    assert.deepEqual(plain(initial('siteSettings', 'chrome://settings/content/siteDetails')), {
      entries: ['chrome://settings/content', 'chrome://settings/content/siteDetails'], index: 1, preferHistoryControls: true});
    assert.deepEqual(plain(initial('extensions', 'chrome://extensions')), {
      entries: ['chrome://extensions'], index: 0, preferHistoryControls: false});
  });
  const navigate = unit('browser-use', 'Xi');
  await check('BROWSER-NAVIGATION-BRANCH-TRUNCATES-FORWARD-HISTORY', () => {
    assert.deepEqual(plain(navigate({entries: ['a', 'b', 'c'], index: 1, preferHistoryControls: true}, 'd')), {
      entries: ['a', 'b', 'd'], index: 2, preferHistoryControls: true});
  });
  await check('BROWSER-NAVIGATION-REUSES-EXISTING-ENTRY', () => {
    const history = {entries: ['a', 'b', 'c'], index: 2, preferHistoryControls: true};
    assert.equal(navigate(history, 'a').index, 0);
    assert.equal(navigate(history, 'c'), history);
  });
  await check('BROWSER-PREFER-SYNTHETIC-HISTORY-CONTROLS', () => {
    const controls = unit('browser-use', 'qi');
    assert.deepEqual(plain(controls({canGoBack: true, canGoForward: true}, {
      entries: ['a', 'b'], index: 0, preferHistoryControls: true})), {canGoBack: false, canGoForward: true});
  });
  const removeKey = unit('browser-use', 'Mr'), rowKey = unit('browser-use', 'jr');
  await check('BROWSER-ROW-IDENTITY-DIFFERS-FROM-REMOVAL-IDENTITY', () => {
    const visit = {url: 'https://example.test', visitTime: '2026-01-03T12:00:00Z'};
    assert.equal(removeKey(visit), removeKey({...visit, isActorVisit: true}));
    assert.notEqual(rowKey(visit), rowKey({...visit, isActorVisit: true}));
  });
  await check('BROWSER-DOWNLOAD-MERGE-FILTERS-LIVE-AND-RETAINS-FILE-STATE', () => {
    const merge = unit('browser-use', 'Qr', {ni: new Set(['started', 'in_progress', 'paused'])});
    const saved = {capturedAtMs: 10, unacknowledgedIds: ['saved'], downloads: [
      {id: 'saved', status: 'paused', fileExists: false, filename: 'test.txt', url: 'https://example.test', startedAtMs: 1}]};
    const live = {capturedAtMs: 20, downloads: [
      {id: 'saved', status: 'completed', fileExists: true, startedAtMs: 2},
      {id: 'new', status: 'in_progress', filename: 'TEST.bin', url: 'https://example.test', startedAtMs: 5},
      {id: 'done', status: 'completed', filename: 'test.bin', url: 'https://example.test', startedAtMs: 6},
      {id: 'other', status: 'paused', filename: 'other.bin', url: 'https://other.invalid', startedAtMs: 8}]};
    const result = plain(merge(saved, live, 'TEST'));
    assert.deepEqual(result.downloads.map(item => item.id), ['new', 'saved']);
    assert.equal(result.downloads[1].fileExists, false);
    assert.equal(result.downloads[1].status, 'completed');
    assert.equal(result.capturedAtMs, 20); assert.deepEqual(result.unacknowledgedIds, ['saved']);
    assert.equal(merge(saved, null, ''), saved);
  });
  function historyRemoval({pending = false, allowed = true, fail = false} = {}) {
    const effects = [], visit = {url: 'https://example.test', visitTime: '2026-01-03T12:00:00Z'};
    let selected = new Set([rowKey(visit), rowKey({...visit, isActorVisit: true})]);
    const fn = callback('browser-use', 'Gr', text => text.startsWith('async e=>{!v&&z'), {
      v: pending, z: allowed, y: value => effects.push(['pending', value]),
      N: {removeEntries: async entries => {effects.push(['remove', plain(entries)]); if (fail) throw Error('synthetic');}},
      _: update => {selected = update(selected);}, x: [visit, {...visit, isActorVisit: true}], Mr: removeKey, jr: rowKey,
      t: {queryClient: {invalidateQueries: async query => effects.push(['invalidate', plain(query)])}},
      n: {}, Jr: () => effects.push(['error'])});
    return {run: entries => fn(entries ?? [visit]), effects, selected: () => selected};
  }
  await check('BROWSER-HISTORY-REMOVAL-GUARDS', async () => {
    for (const options of [{pending: true}, {allowed: false}]) {
      const probe = historyRemoval(options); await probe.run(); assert.deepEqual(probe.effects, []);
    }
    const probe = historyRemoval(); await probe.run([]); assert.deepEqual(probe.effects, []);
  });
  await check('BROWSER-HISTORY-REMOVAL-CLEARS-ACTOR-VARIANTS', async () => {
    const probe = historyRemoval(); await probe.run(); assert.equal(probe.selected().size, 0);
    assert(probe.effects.some(effect => effect[0] === 'invalidate'));
    assert.deepEqual(probe.effects.at(-1), ['pending', false]);
  });
  await check('BROWSER-HISTORY-FAILURE-RELEASES-PENDING', async () => {
    const probe = historyRemoval({fail: true}); await probe.run();
    assert.equal(probe.selected().size, 2); assert(probe.effects.some(effect => effect[0] === 'error'));
    assert.equal(probe.effects.some(effect => effect[0] === 'invalidate'), false);
    assert.deepEqual(probe.effects.at(-1), ['pending', false]);
  });
  await check('CHRONICLE-GROUPS-LOCAL-TODAY-YESTERDAY-DATE', () => {
    const sameDay = unit('chronicle', 'vn');
    const group = unit('chronicle', '_n', {vn: sameDay});
    const now = new Date(2026, 9, 24, 12), stamp = day => new Date(2026, 9, day, 12).getTime();
    const result = group([24, 24, 23, 20].map((day, id) => ({id, interval: {startMs: stamp(day)}})), now);
    assert.deepEqual(plain(result.map(item => item.label.kind)), ['today', 'yesterday', 'date']);
    assert.equal(result[0].items.length, 2);
  });
  function clearChronicle({request = {scope: 'last_hour', interval: null}, pending = false} = {}) {
    const effects = [];
    const fn = callback('chronicle', 'kn', text => text.startsWith('e=>{e.preventDefault(),i!=null'), {
      i: request, o: {isPending: pending, mutate: (payload, options) => {effects.push(['mutate', plain(payload)]); options.onSuccess();}},
      n: open => effects.push(['open', open])});
    return {run: () => fn({preventDefault: () => effects.push(['preventDefault'])}), effects};
  }
  await check('CHRONICLE-NULL-AND-PENDING-CLEAR-GUARDS', () => {
    for (const options of [{request: null}, {pending: true}]) {
      const probe = clearChronicle(options); probe.run();
      assert.equal(probe.effects.some(effect => effect[0] === 'mutate'), false);
    }
  });
  await check('CHRONICLE-CLEAR-SCOPE-AND-SUCCESS-CLOSE', () => {
    const probe = clearChronicle(); probe.run();
    assert.deepEqual(probe.effects.find(effect => effect[0] === 'mutate')[1], {scope: 'last_hour', interval: null});
    assert.deepEqual(probe.effects.at(-1), ['open', false]);
  });
  await check('VOICE-DEVICE-ENUMERATION-FILTER', async () => {
    const list = unit('voice', 'On', {navigator: {mediaDevices: {enumerateDevices: async () => [
      {kind: 'audioinput', deviceId: 'default'}, {kind: 'audioinput', deviceId: ''},
      {kind: 'audiooutput', deviceId: 'speaker'}, {kind: 'videoinput', deviceId: 'camera'},
      {kind: 'audioinput', deviceId: 'owned-input'}]}}});
    assert.deepEqual(plain(await list()).map(item => item.deviceId), ['owned-input']);
    assert.deepEqual(plain(await unit('voice', 'On')()), []);
  });
  function microphone({refreshFail = false, permissionDenied = false} = {}) {
    const effects = [], stop = unit('voice', 'Tn'), ignore = unit('voice', 'En');
    const fn = callback('voice', 'wn', text => text.startsWith('async function(){await fe.systemPermissions'), {
      fe: {systemPermissions: {requestMicrophoneAccess: async () => effects.push('permission')}},
      navigator: {mediaDevices: {getUserMedia: async () => {effects.push('media'); if (permissionDenied) throw Error('denied');
        return {getTracks: () => [{stop: () => effects.push('stop')}]};}}},
      o: {refetch: async () => {effects.push('refresh'); if (refreshFail) throw Error('refresh');}}, En: ignore, Tn: stop});
    return {run: fn, effects};
  }
  await check('VOICE-MICROPHONE-STOPS-TRACKS-AFTER-REFRESH', async () => {
    const probe = microphone(); await probe.run(); assert.deepEqual(probe.effects, ['permission', 'media', 'refresh', 'stop']);
  });
  await check('VOICE-MICROPHONE-STOPS-TRACKS-ON-REFRESH-FAILURE', async () => {
    const probe = microphone({refreshFail: true}); await assert.rejects(probe.run(), /refresh/);
    assert.equal(probe.effects.at(-1), 'stop');
  });
  await check('VOICE-MICROPHONE-DENIAL-STILL-REFRESHES-NO-TRACK', async () => {
    const probe = microphone({permissionDenied: true}); await probe.run();
    assert.deepEqual(probe.effects, ['permission', 'media', 'refresh']);
  });
  await check('VOICE-SCREEN-ENABLE-REQUIRES-PERMISSION-CALLBACK', () => {
    const effects = []; let consent;
    const fn = callback('voice', 'en', text => text.startsWith('e=>{if(!e)'), {
      n: 'scope', an: {screenContextEnabled: 'screen'},
      Re: (...args) => effects.push(args), kt: (_, callback) => {consent = callback;}});
    fn(true); assert.deepEqual(effects, []); consent(); assert.deepEqual(effects, [['scope', 'screen', true]]);
    fn(false); assert.deepEqual(effects.at(-1), ['scope', 'screen', false]);
  });
  function language({account = 'owned-account', fail = false} = {}) {
    const effects = [];
    const fn = callback('voice', 'assignment-ln', text => text.startsWith('async t=>{let n=e.get(ee)'), {
      ee: 'account', jt: ['voice'], e: {get: () => account, query: {snapshot: () => ({invalidate: async () => effects.push('account-invalidate')})},
        queryClient: {invalidateQueries: async query => effects.push(['voice-invalidate', plain(query)])}}, Me: 'settings',
      i: {safePatch: async (url, options) => {effects.push(['patch', url, plain(options)]); if (fail) throw Error('synthetic');}}});
    return {run: () => fn('auto'), effects};
  }
  await check('VOICE-LANGUAGE-ACCOUNT-PATCH-AND-INVALIDATION', async () => {
    const probe = language(); await probe.run(); const patch = probe.effects[0];
    assert.equal(patch[1], '/settings/account_user_setting');
    assert.deepEqual(patch[2].parameters.query, {feature: 'voice_main_language', value: 'auto'});
    assert.deepEqual(patch[2].additionalHeaders, {'ChatGPT-Account-ID': 'owned-account'});
    assert.equal(probe.effects.length, 3);
    const noAccount = language({account: null}); await noAccount.run(); assert.equal(noAccount.effects[0][2].additionalHeaders, undefined);
  });
  await check('VOICE-LANGUAGE-FAILURE-DOES-NOT-INVALIDATE-AS-SUCCESS', async () => {
    const probe = language({fail: true}); await assert.rejects(probe.run(), /synthetic/); assert.equal(probe.effects.length, 1);
  });
  function dictionary({fail = false} = {}) {
    const effects = [];
    const fn = callback('voice', 'Mn', text => text.startsWith('async function(e){let n=e.map(In).filter(Fn)'), {
      In: unit('voice', 'In'), Fn: unit('voice', 'Fn'), t: 'scope', ae: {dictationDictionary: 'dictionary'},
      Re: async (_, key, values) => {effects.push(['write', key, plain(values)]); if (fail) throw Error('synthetic');},
      o: value => effects.push(['draft', value])});
    return {run: () => fn([' one ', '', '  ', 'one', ' two']), effects};
  }
  await check('VOICE-DICTIONARY-TRIMS-FILTERS-PRESERVES-DUPLICATES', async () => {
    const probe = dictionary(); await probe.run();
    assert.deepEqual(probe.effects, [['write', 'dictionary', ['one', 'one', 'two']], ['draft', null]]);
  });
  await check('VOICE-DICTIONARY-FAILED-SAVE-PRESERVES-DRAFT', async () => {
    const probe = dictionary({fail: true}); await assert.rejects(probe.run(), /synthetic/); assert.equal(probe.effects.length, 1);
  });
  const sourceSelections = [...new Map(used.map(record => [`${record.page}:${record.spanHash}`, record])).values()];
  fs.writeFileSync(path.join(work, 'isolated-observations.json'), JSON.stringify({baselineId: base,
    method: 'Exact frozen pure functions/callbacks with synthetic records, device/permission/media/query/preference receivers; no target imports or real services.',
    sourceSelections, cases, passed: cases.length, failed: 0, productScenariosExecuted: 0,
    modelSubmissionsAdded: 0, originalClientRunsAdded: 0, realHistoryReads: 0, realMediaCalls: 0}, null, 2) + '\n', {flag: 'wx'});
  process.stdout.write(JSON.stringify({passed: cases.length, failed: 0, productScenariosExecuted: 0}) + '\n');
})().catch(error => {process.stderr.write(error.stack + '\n'); process.exitCode = 1;});
