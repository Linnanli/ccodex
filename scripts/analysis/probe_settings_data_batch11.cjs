// Frozen functions/callbacks with owned state, query and service substitutes.
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const assert = require('node:assert/strict'), crypto = require('node:crypto');
const root = path.resolve(__dirname, '../..'), base = 'codex-26.1007.30912-c5b273322a83';
const work = path.join(root, '.analysis-local/settings-data-batch11-work');
const frozen = path.join(root, '.analysis-local/baselines', base, 'extracted');
const folders = ['ads-controls', 'archived-chats', 'data-controls', 'ads-state', 'ads-availability', 'training-query'];
const metadata = Object.fromEntries(folders.map(p => [p, JSON.parse(fs.readFileSync(path.join(work, p, 'source-contracts.json')))]));
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const buffers = new Map(), used = [], cases = [];
const plain = value => JSON.parse(JSON.stringify(value));
function exact(page, record) {
  if (!buffers.has(record.sourcePath)) {
    const bytes = fs.readFileSync(path.join(frozen, record.sourcePath.replace(/^app.asar\//, '')));
    assert.equal(sha(bytes), record.sourceHash); buffers.set(record.sourcePath, bytes);
  }
  const bytes = buffers.get(record.sourcePath).subarray(record.byteRange.start, record.byteRange.endExclusive);
  assert.equal(sha(bytes), record.spanHash); used.push({page, ...record}); return bytes.toString();
}
function unit(page, name, env = {}) {
  const r = metadata[page].units.filter(u => u.name === name); assert.equal(r.length, 1, page + ':' + name);
  return vm.runInNewContext('(' + exact(page, r[0]) + ')', env, {timeout: 1000});
}
function callback(page, name, match, env = {}) {
  const r = metadata[page].callbacks.filter(c => c.unit === name).filter(c => match(exact(page, c)));
  assert.equal(r.length, 1, page + ':' + name);
  return vm.runInNewContext('(' + exact(page, r[0]) + ')', env, {timeout: 1000});
}
async function check(id, run) {
  try { await run(); cases.push({id, passed: true}); }
  catch (error) { cases.push({id, passed: false, error: String(error.stack)}); }
}
const memo = {c: n => Array(n).fill(Symbol.for('react.memo_cache_sentinel'))};
const jsx = {jsx: (type, props) => ({type, props}), jsxs: (type, props) => ({type, props})};
function nodes(v) {
  if (!v || typeof v !== 'object') return [];
  if (Array.isArray(v)) return v.flatMap(nodes);
  return [v, ...Object.values(v.props ?? {}).flatMap(nodes)];
}
function snapshot(value, name, effects) {
  return {getData: () => value, getOptions: () => ({queryKey: ['owned', name]}),
    cancel: async () => effects.push(['cancel', name]), invalidate: async () => effects.push(['invalidate', name]),
    setData(fn) { value = typeof fn === 'function' ? fn(value) : fn; effects.push(['set', name, plain(value)]); }};
}
function ads(options = {}) {
  const effects = [], values = {account: 'owned-A', identity: 'owned-I', available: true, capability: true, ...options.values};
  const data = options.noData ? null : {bazaarPersonalizationEnabled: true, bazaarPersonalizationUnavailable: false, freeAdsOptOut: false, ...options.data};
  const snapshots = {personal: snapshot(data, 'personal', effects), topics: snapshot({pages: [{preferences: ['one'], cursor: 'next'}], pageParams: [undefined]}, 'topics', effects),
    history: snapshot({pages: [{history: ['one'], cursor: 'next'}], pageParams: [undefined]}, 'history', effects)};
  const scope = {get: key => key === 'capability' ? {isCapable: values.capability} : values[key],
    query: {snapshot: key => snapshots[key]}, queryClient: {removeQueries: args => effects.push(['remove', plain(args)])}};
  const api = {safePatch: async (...args) => {effects.push(['patch', ...plain(args)]); if (options.fail) throw Error('owned failure'); options.afterPatch?.(values);},
    safeDelete: async (...args) => {effects.push(['delete', ...plain(args)]); if (options.fail) throw Error('owned failure'); options.afterPatch?.(values);}};
  const env = {v: 'identity', l: 'account', C: 'available', s: 'capability', h: 'personal', D: 'topics', E: 'history', m: 'Owned-Account', t: api,
    d: (_, key) => options.flags?.[key] ?? true, x: async () => {effects.push(['refresh']); options.afterRefresh?.(values);}};
  return {effects, values, snapshots, scope, save: unit('ads-state', 'w', env), remove: unit('ads-state', 'T', env)};
}

(async () => {
  await check('ADS-REJECTED-GUARDS-SEND-NO-PATCH', async () => {
    for (const options of [{values: {account: 'owned-B'}}, {values: {available: false}}, {noData: true},
      {data: {bazaarPersonalizationUnavailable: true}}, {flags: {'1613860123': false}, feature: 'free_ads_opt_out'}]) {
      const f = ads(options); assert.equal(await f.save(f.scope, 'owned-A', {feature: options.feature ?? 'bazaar_personalization_enabled', value: true}), false);
      assert.equal(f.effects.length, 0);
    }
  });
  await check('ADS-CONSENT-OVERRIDE-REQUIRES-CAPABILITY-AND-FLAG', async () => {
    for (const [capability, override, expected] of [[true, true, true], [false, true, false], [true, false, false]]) {
      const f = ads({values: {available: false, capability}, data: {bazaarPersonalizationUnavailable: true}, flags: {'3274900344': override}});
      assert.equal(await f.save(f.scope, 'owned-A', {feature: 'bazaar_personalization_enabled', value: true}, 'consent'), expected);
      assert.equal(f.effects.some(e => e[0] === 'patch'), expected);
    }
  });
  await check('ADS-PERSONALIZATION-SAVE-REMOVES-EXACT-TOPICS-QUERY', async () => {
    const f = ads(); assert.equal(await f.save(f.scope, 'owned-A', {feature: 'bazaar_personalization_enabled', value: false}), true);
    assert.equal(f.snapshots.personal.getData().bazaarPersonalizationEnabled, false);
    assert.deepEqual(f.effects.find(e => e[0] === 'patch'), ['patch', '/settings/account_user_setting', {parameters: {query: {feature: 'bazaar_personalization_enabled', value: false}}, additionalHeaders: {'ChatGPT-Account-ID': 'owned-A', 'Owned-Account': 'owned-A'}}]);
    assert.deepEqual(f.effects.find(e => e[0] === 'remove'), ['remove', {queryKey: ['owned', 'topics'], exact: true}]);
  });
  await check('ADS-RETURN-TO-ADS-REFRESH-AND-IDENTITY-GUARD', async () => {
    for (const changed of [false, true]) {
      const f = ads({afterRefresh: v => {if (changed) v.identity = 'owned-NEW';}});
      assert.equal(await f.save(f.scope, 'owned-A', {feature: 'free_ads_opt_out', value: false}), !changed);
      assert(f.effects.some(e => e[0] === 'refresh'));
      assert.equal(f.effects.some(e => e[0] === 'invalidate'), !changed);
    }
  });
  await check('ADS-FAILED-PATCH-DOES-NOT-MERGE-CACHE', async () => {
    const f = ads({fail: true}); assert.equal(await f.save(f.scope, 'owned-A', {feature: 'free_ads_opt_out', value: true}), false);
    assert.equal(f.snapshots.personal.getData().freeAdsOptOut, false); assert.equal(f.effects.length, 1);
  });
  await check('ADS-PROFILE-DELETE-CLEARS-ONLY-HISTORY-AND-TOPICS', async () => {
    const f = ads(); assert.equal(await f.remove(f.scope, 'owned-A'), true);
    assert.equal(f.effects[0][1], '/bazaar/profile');
    assert.deepEqual(plain(f.snapshots.history.getData()), {pages: [{history: []}], pageParams: [null]});
    assert.deepEqual(plain(f.snapshots.topics.getData()), {pages: [{preferences: []}], pageParams: [null]});
    assert.equal(f.snapshots.personal.getData().bazaarPersonalizationEnabled, true);
  });
  await check('ADS-DELETE-GUARDS-FAILURE-AND-STALE-IDENTITY', async () => {
    for (const options of [{values: {account: 'owned-B'}}, {values: {available: false}}, {fail: true}, {afterPatch: v => {v.identity = 'owned-NEW';}}]) {
      const f = ads(options); assert.equal(await f.remove(f.scope, 'owned-A'), false);
      if (options.fail) assert.equal(f.snapshots.history.getData().pages[0].history.length, 1);
      if (options.values) assert.equal(f.effects.length, 0);
    }
  });
  await check('ADS-QUERIES-KEEP-SCOPE-CURSOR-AND-TOPIC-ELIGIBILITY', async () => {
    for (const [name, key, endpoint] of [['assignment-E', 'E', '/bazaar/history'], ['assignment-D', 'D', '/bazaar/preferences']]) {
      const requests = [], context = {a: (_, fn) => fn, r: 'scope', v: 'identity', l: 'account', C: 'available', h: 'personal', m: 'Owned-Account', y: {ONE_MINUTE: 60000},
        t: {safeGet: async (...args) => requests.push(plain(args))}};
      const rec = metadata['ads-state'].units.find(u => u.name === name);
      vm.runInNewContext(exact('ads-state', rec), context, {timeout: 1000});
      const get = (data = {}) => atom => ({identity: 'owned-I', account: 'owned-A', available: true, personal: {data: {bazaarPersonalizationEnabled: true, ...data}}})[atom];
      const q = context[key]('owned-A', {get: get()}); assert.equal(q.enabled, true); assert.equal(q.retry, false);
      assert.deepEqual(plain(q.queryKey), ['chatgpt-ads', 'owned-A', 'owned-I', key === 'E' ? 'history' : 'topics']);
      await q.queryFn({pageParam: 'owned-next', signal: 'owned-signal'});
      assert.equal(requests[0][0], endpoint); assert.equal(requests[0][1].parameters.query.cursor, 'owned-next');
      assert.equal(requests[0][1].signal, 'owned-signal'); assert.equal(context[key]('owned-B', {get: get()}).enabled, false);
      if (key === 'D') assert.equal(context[key]('owned-A', {get: get({bazaarPersonalizationEnabled: false})}).enabled, false);
    }
  });
  await check('ADS-HISTORY-ROWS-ARE-READ-ONLY-AND-PROJECTIONS-DIFFER', () => {
    const render = unit('ads-controls', 'Me', {Q: jsx, O: 'row', z: 'message', D: 'date'});
    const row = render({id: 'ad', ad_data: {advertiser_brand: {name: 'Owned'}, title: 'Synthetic'}, occurred_at: '2026-01-01', action: 'opened'});
    assert.equal(row.props.control, null);
    assert.equal(unit('ads-controls', 'Pe')({history: []}), true);
    assert.equal(unit('ads-controls', 'Le')({preferences: []}), false);
  });
  await check('ARCHIVE-KEYS-ISOLATE-DURABLE-ACCOUNT', () => {
    const key = unit('archived-chats', 'Cn');
    assert.deepEqual(plain(key('durable', 'owned-A')), ['archived-threads', 'durable', 'owned-A']);
    assert.deepEqual(plain(key('local', 'owned-A')), ['archived-threads', 'local']);
  });
  await check('ARCHIVE-STREAM-USES-TYPED-BACKGROUND-LIST-AND-CURSORS', async () => {
    const calls = [], replies = [{data: ['first'], nextCursor: 'next'}, {data: ['second'], nextCursor: null}];
    const list = unit('archived-chats', 'Sn', {Xe: (_, host) => ({sendRequest: async (...args) => {calls.push([host, ...plain(args)]); return replies.shift();}}), xe: ['owned-source']});
    const pages = []; for await (const page of list('scope', 'owned-host', {throwIfAborted() {}})) pages.push(plain(page));
    assert.deepEqual(pages, [['first'], ['second']]);
    assert.equal(calls[0][1], 'thread/list'); assert.equal(calls[0][2].archived, true); assert.equal(calls[0][2].useStateDbOnly, true);
    assert.equal(calls[1][2].cursor, 'next'); assert.deepEqual(calls[0][3], {priority: 'background', source: 'thread_list'});
  });
  await check('ARCHIVE-STREAM-ABORT-AND-REPEATED-CURSOR-STOP', async () => {
    const repeating = unit('archived-chats', 'Sn', {Xe: () => ({sendRequest: async () => ({data: [], nextCursor: 'repeat'})}), xe: []});
    await assert.rejects(async () => {for await (const _ of repeating('scope', 'host', {throwIfAborted() {}})) {}}, /repeated/);
    let requests = 0;
    const aborting = unit('archived-chats', 'Sn', {Xe: () => ({sendRequest: async () => {requests++;}}), xe: []});
    await assert.rejects(async () => {for await (const _ of aborting('scope', 'host', {throwIfAborted() {throw Error('owned abort');}})) {}}, /owned abort/);
    assert.equal(requests, 0);
  });
  await check('ARCHIVE-ALL-IGNORES-VISIBLE-ID-SET-PROJECT-USES-EXPLICIT-IDS', async () => {
    const effects = [], api = {deleteAllArchivedConversations: async () => {effects.push(['all']); return ['hidden-too'];}, deleteArchivedConversation: async id => {effects.push(['single', id]); return [id];}};
    const remove = callback('archived-chats', 'wn', s => s.startsWith('async e=>e.kind===`all`?'), {Xe: (_, host) => {assert.equal(host, 'owned-host'); return api;}, D: 'scope', o: 'owned-host', Re: id => 'normalized:' + id});
    assert.deepEqual(plain(await remove({kind: 'all', threadIds: ['visible']})), ['hidden-too']);
    assert.deepEqual(effects, [['all']]); effects.length = 0;
    assert.deepEqual(plain(await remove({kind: 'project', threadIds: ['one', 'two']})), ['normalized:one', 'normalized:two']);
    assert.deepEqual(effects, [['single', 'normalized:one'], ['single', 'normalized:two']]);
    effects.length = 0; await remove({kind: 'single', thread: {id: 'three'}}); assert.deepEqual(effects, [['single', 'normalized:three']]);
  });
  await check('ARCHIVE-LOCAL-UNARCHIVE-REUSES-HOST-ADAPTER', async () => {
    const effects = [], input = {thread: {id: 'one'}, hostId: 'owned-host'};
    const restore = callback('archived-chats', 'wn', s => s.startsWith('async e=>{let{thread:t,hostId:n}=e') && s.includes('.unarchiveConversation('),
      {Xe: (_, host) => ({unarchiveConversation: async (...args) => effects.push([host, ...plain(args)])}), D: {get: () => true}, se: 'pins', Re: id => 'normalized:' + id});
    assert.equal(await restore(input), input); assert.deepEqual(effects, [['owned-host', 'normalized:one', {useAppServerPins: true}]]);
  });
  await check('ARCHIVE-CLOUD-RECOVERY-AND-ACCOUNT-UNARCHIVE-USE-DIFFERENT-APIS', async () => {
    for (const cloud of [true, false]) {
      const effects = [], restore = callback('archived-chats', 'un', s => s.startsWith('async()=>{y?await ue.safePost'),
        {y: cloud, ue: {safePost: async (...args) => effects.push(['cloud', ...plain(args)])}, Zt: async args => effects.push(['account', plain(args)]), a: 'owned-scope', n: {id: 'owned-id'}});
      await restore(); assert.equal(effects[0][0], cloud ? 'cloud' : 'account');
      if (cloud) assert.deepEqual(effects[0], ['cloud', '/wham/tasks/{task_id}/recover', {parameters: {path: {task_id: 'owned-id'}}}]);
      else assert.deepEqual(effects[0], ['account', {scope: 'owned-scope', conversationId: 'owned-id'}]);
    }
  });
  await check('ARCHIVE-CONVERSATION-DELETE-DELEGATES-WITH-CONVERSATION-ID', async () => {
    const effects = [], remove = callback('archived-chats', 'un', s => s === '()=>Gt({scope:a,conversationId:n.id})',
      {Gt: async args => effects.push(plain(args)), a: 'owned-scope', n: {id: 'owned-id'}});
    await remove(); assert.deepEqual(effects, [{scope: 'owned-scope', conversationId: 'owned-id'}]);
  });
  await check('TRAINING-ELIGIBILITY-QUERY-REQUIRES-MATCHING-WORKSPACE', async () => {
    const effects = [], factory = unit('training-query', 'a', {t: {safeGet: async (...args) => effects.push(plain(args))}, i: () => {throw Error('skip query');}});
    for (const structure of ['personal', 'workspace']) for (const matches of [false, true]) {
      const query = factory({account: {id: 'owned-A', structure}, userId: 'owned-U', settingsAccountId: matches ? 'owned-A' : 'owned-B'});
      assert.equal(query.enabled, structure === 'workspace' && matches);
      if (query.enabled) await query.queryFn();
    }
    assert.deepEqual(effects, [['/accounts/data_usage_for_training', {additionalHeaders: {'ChatGPT-Account-ID': 'owned-A'}}]]);
  });
  function training(options = {}) {
    const effects = [], data = options.missing ? null : {trainingAllowed: false, amphoraLocks: {training_allowed: options.locked === true}};
    const state = {account: options.account ?? 'owned-A'}, snap = snapshot(data, 'settings', effects);
    const scope = {get: () => state.account, query: {snapshot: () => snap}};
    const run = callback('data-controls', 'dn', s => s.startsWith('async function(e,t){e===`precise_location_allowed`'),
      {r: scope, Ae: 'settings', y: options.noReal ? null : {id: options.real ?? 'owned-A'}, h: 'owned-A', j: 'account', w: options.workspace === true,
        T: {getQueryState: () => ({status: options.queryError ? 'error' : 'success'}), getQueryData: () => ({data_usage_for_training: options.policy ?? 'permitted'})}, D: {queryKey: ['eligibility']},
        n: {safePatch: async (...args) => {effects.push(['patch', ...plain(args)]); if (options.change) state.account = 'owned-B'; if (options.fail) throw Error('owned failure');}},
        Ue: () => effects.push(['error']), b: () => effects.push(['stop-sharing'])});
    return {effects, run: () => run('training_allowed', true), snap};
  }
  await check('TRAINING-UPDATE-REJECTS-DATA-LOCK-ACCOUNT-AND-WORKSPACE-GUARDS', async () => {
    for (const options of [{missing: true}, {locked: true}, {account: 'owned-B'}, {real: 'owned-B'}, {noReal: true}, {workspace: true, queryError: true}, {workspace: true, policy: 'forbidden'}]) {
      const f = training(options); await f.run(); assert.equal(f.effects.length, 0);
    }
  });
  await check('TRAINING-UPDATE-SAVES-AND-ERROR-FEEDBACK-IS-ACCOUNT-GUARDED', async () => {
    const f = training({workspace: true}); await f.run(); assert.equal(f.snap.getData().trainingAllowed, true); assert.equal(f.effects[0][2].parameters.query.feature, 'training_allowed');
    for (const change of [false, true]) {
      const failed = training({fail: true, change}); await failed.run(); assert.equal(failed.snap.getData().trainingAllowed, false);
      assert.equal(failed.effects.some(e => e[0] === 'error'), !change);
    }
  });
  await check('ACCOUNT-BULK-ARCHIVE-DELETE-AND-ACCOUNT-SWITCH-SCOPE', async () => {
    for (const action of ['archive', 'delete']) for (const change of [false, true]) {
      const effects = [], state = {account: 'owned-A'};
      const run = callback('data-controls', 'dn', s => s.startsWith('async e=>{let t=r.get(we);await n.safePatch'),
        {r: {get: () => state.account, set: (...args) => effects.push(['set', ...plain(args)])}, we: 'account', et: 'list',
          n: {safePatch: async (...args) => {effects.push(['patch', ...plain(args)]); if (change) state.account = 'owned-B';}},
          re: (_, account) => effects.push(['invalidate-old', account]), lt: () => effects.push(['clear-derived']),
          T: {invalidateQueries: args => effects.push(['invalidate', plain(args)])}, st: 'account-archive',
          ot: async args => {effects.push(['history', plain(args)]); throw Error('owned cache failure');}, fn: unit('data-controls', 'fn')});
      await run(action); assert.equal(effects[0][1], '/conversations');
      assert.deepEqual(effects[0][2], {requestBody: action === 'archive' ? {is_archived: true} : {is_visible: false}});
      assert.equal(effects.some(e => e[0] === 'set'), !change); assert.deepEqual(effects.at(-1), ['history', {includePersisted: true}]);
    }
  });
  await check('EXPORT-REAUTH-REQUEST-AND-CANCELLED-TOKEN', async () => {
    for (const allowed of [true, false]) {
      const effects = [], exportData = unit('data-controls', 'Ft', {rt: async purpose => {effects.push(['reauth', purpose]); return {'Owned-Reauth': 'synthetic'};}, n: {safePost: async (...args) => effects.push(['post', ...plain(args)])}});
      const identity = {accountId: 'owned-A', userId: 'owned-U'};
      assert.equal(await exportData(identity, async () => allowed, () => {throw Error('unused third guard');}), allowed ? 'requested' : 'cancelled');
      assert.equal(effects[0][1], 'chatgpt_account_data_export'); assert.equal(effects.length, allowed ? 2 : 1);
      if (allowed) assert.deepEqual(effects[1], ['post', '/accounts/data_export', {additionalHeaders: {'Owned-Reauth': 'synthetic'}, expectedIdentity: identity}]);
    }
  });
  await check('CONSENT-GPC-OVERRIDES-ALL-CATEGORIES-ONLY-WHEN-ENABLED', async () => {
    for (const [flag, browserGpc] of [[false, true], [true, false], [true, true]]) {
      const effects = [], snap = snapshot({marketing: false, analytics: true, personalization: true}, 'consent', effects);
      const run = callback('data-controls', 'Rt', s => s.startsWith('async e=>{let{key:t,value:r}=e'),
        {a: {get: key => key === 'account' ? 'owned-A' : 'owned-I', query: {snapshot: () => snap}}, j: 'account', ze: 'identity', wt: 'consent', s: flag, navigator: {globalPrivacyControl: browserGpc},
          ke: 'Owned-Account', n: {safePost: async (...args) => effects.push(['post', ...plain(args)])}});
      await run({key: 'marketing', value: true}); const data = effects[0][2].requestBody.granular_consent;
      assert.deepEqual(data, flag && browserGpc ? {analytics: false, marketing: false, personalization: false} : {marketing: true});
      assert.equal(effects[0][2].additionalHeaders['ChatGPT-Account-ID'], 'owned-A');
    }
  });
  function location(options = {}) {
    const effects = [], state = {account: 'owned-A', identity: 'owned-I', user: 'owned-U', capable: true};
    const snap = snapshot({preciseLocationAllowed: false}, 'location', effects);
    snap.fetch = async () => {effects.push(['fetch']); if (options.changeOnFetch) state.account = 'owned-B'; return {preciseLocationAllowed: false, amphoraLocks: {precise_location_allowed: options.locked === true}};};
    const scope = {get: key => key === 'toast' ? {danger: () => effects.push(['error'])} : state[key], query: {snapshot: () => snap}};
    const run = callback('data-controls', 'Wt', s => s.startsWith('async function(e){let t=s.get(j)'),
      {s: scope, j: 'account', ze: 'identity', Fe: 'user', Ae: 'settings', ft: 'capable', i: false,
        n: {safePatch: async (...args) => {effects.push(['patch', ...plain(args)]); if (options.changeOnPatch) state.identity = 'owned-NEW';}}, ke: 'Owned-Account',
        Gt: unit('data-controls', 'Gt'), b: () => effects.push(['stop']), mt: async (_, ...args) => effects.push(['permission', ...args]),
        dt: {CHATGPT_PRECISE_LOCATION_ENTRY_POINT_SETTINGS: 'settings'}, gt: {CHATGPT_LOCATION_PERMISSION_INTERACTION_STATUS_ROW: 'row'}, M: 'toast', c: {formatMessage: x => x.id}});
    return {effects, run, snap};
  }
  await check('LOCATION-ENABLE-REFRESHES-AND-REJECTS-STALE-OR-LOCKED', async () => {
    for (const options of [{changeOnFetch: true}, {locked: true}]) {
      const f = location(options); await f.run(true); assert.deepEqual(f.effects, [['fetch']]);
    }
    const f = location(); await f.run(true); assert.deepEqual(f.effects.map(e => e[0]), ['fetch', 'patch', 'invalidate', 'permission']);
    assert.deepEqual(f.effects[1][2].expectedIdentity, {accountId: 'owned-A', userId: 'owned-U'});
  });
  await check('LOCATION-DISABLE-STOPS-ONLY-CURRENT-IDENTITY', async () => {
    for (const changeOnPatch of [false, true]) {
      const f = location({changeOnPatch}); await f.run(false);
      assert.equal(f.snap.getData().preciseLocationAllowed, false); assert.equal(f.effects.some(e => e[0] === 'stop'), !changeOnPatch);
      assert(!f.effects.some(e => e[0] === 'permission'));
    }
  });
  await check('WORK-NETWORK-SWITCH-LOCKS-AND-ERROR-RELOAD', () => {
    for (const options of [{}, {missing: true}, {locked: true}, {pending: true}, {error: true}]) {
      const effects = [], data = options.missing ? null : {enableFloraNetworkAccess: true, amphoraLocks: {enable_flora_network_access: !!options.locked}};
      const render = unit('data-controls', 'Zt', {Qt: memo, $t: jsx, ce: () => ({formatMessage: x => x.id}), Ae: 'settings', Ee: 'mutation',
        l: key => key === 'settings' ? {data, isError: !!options.error, refetch: () => effects.push('reload')} : {mutate: value => effects.push(value), isPending: !!options.pending, error: null},
        G: 'message', L: 'row', t: 'switch', We: 'error'});
      const rows = nodes(render()), toggle = rows.find(n => n.type === 'switch');
      assert.equal(toggle.props.disabled, Object.keys(options).length > 0);
      if (!toggle.props.disabled) {toggle.props.onChange(false); assert.deepEqual(effects, [false]);}
      if (options.error) {rows.find(n => n.type === 'error').props.onPrimaryCtaClick(); assert.deepEqual(effects, ['reload']);}
    }
  });
  await check('WORK-RESET-ENTRY-REQUIRES-LOADED-ACCOUNT-AND-WORKSPACE-FLORA', () => {
    for (const [flag, structure, flora, expected] of [[false, 'personal', true, false], [true, 'personal', false, true], [true, 'workspace', false, false], [true, 'workspace', true, true]]) {
      const render = unit('data-controls', 'an', {sn: memo, ln: jsx, ae: 'flags', Ce: 'workspace', Oe: 'account', we: 'account-id', Fe: 'user-id', on: 'reset-row',
        ne: key => key === 'flags' ? flag : {data: {features: flora ? ['flora'] : []}}, l: key => ({account: {status: 'loaded', structure}, 'account-id': 'owned-A', 'user-id': 'owned-U'})[key]});
      assert.equal(render() !== null, expected);
    }
  });
  await check('WORK-RESET-IDENTITY-NO-RETRY-AND-PENDING-CLOSE-GUARD', async () => {
    for (const pending of [false, true]) {
      const effects = []; let mutationOptions;
      const render = unit('data-controls', 'tn', {nn: memo, Q: jsx, p: () => ({get: () => ({success() {}, danger() {}})}), g: 'scope', ce: () => ({formatMessage: x => x.id}),
        n: {safePost: async (...args) => effects.push(['post', ...plain(args)])}, ke: 'Owned-Account',
        je: opts => {mutationOptions = opts; return {mutate: () => effects.push(['mutate']), isPending: pending};},
        M: 'toast', G: 'message', Be: 'title', pe: 'body', i: 'information', te: 'subtitle', u: 'button', me: 'actions', ee: 'form', v: 'dialog'});
      const result = render({accountId: 'owned-A', userId: 'owned-U', open: true, onOpenChange: value => effects.push(['close', value]), triggerContent: 'trigger'});
      assert.equal(mutationOptions.retry, false); await mutationOptions.mutationFn();
      assert.deepEqual(effects[0], ['post', '/flora/workspace/reset', {expectedIdentity: {accountId: 'owned-A', userId: 'owned-U'}, additionalHeaders: {'ChatGPT-Account-ID': 'owned-A', 'Owned-Account': 'owned-A'}, retry: false}]);
      result.props.onOpenChange(false); assert.equal(effects.some(e => e[0] === 'close'), !pending);
      nodes(result).find(n => n.type === 'form').props.onSubmit({preventDefault() {}}); assert.equal(effects.some(e => e[0] === 'mutate'), !pending);
    }
  });
  const failed = cases.filter(c => !c.passed).length;
  const sourceSelections = [...new Map(used.map(r => [r.page + ':' + r.spanHash, r])).values()];
  const result = {baselineId: base, method: 'Exact frozen functions/callbacks with synthetic account/query/host/cloud/location receivers; no target-module imports.',
    sourceSelections, cases, passed: cases.length - failed, failed, productScenariosExecuted: 0, modelSubmissionsAdded: 0, originalClientRunsAdded: 0,
    realServiceCalls: 0, actualDeletionExportOrResetRequests: 0, devicePermissionRequests: 0,
    limits: ['Selected source contracts only; not real React/provider/product acceptance', 'All account/host/cloud/query/device services are synthetic', 'No complete delegated manager or mode closure']};
  fs.writeFileSync(path.join(work, process.argv[2] ?? 'isolated-observations.json'), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
  console.log(JSON.stringify({passed: result.passed, failed, failedCases: cases.filter(c => !c.passed)}));
  if (failed) process.exitCode = 1;
})().catch(e => {console.error(e.stack); process.exitCode = 1;});
