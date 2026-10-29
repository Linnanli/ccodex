// Frozen first-party selections with owned inventories, accounts and in-memory services.
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const assert = require('node:assert/strict'), crypto = require('node:crypto');
const root = path.resolve(__dirname, '../..'), base = 'codex-26.1007.30912-c5b273322a83';
const work = path.join(root, '.analysis-local/settings-safety-batch13-work');
const frozen = path.join(root, '.analysis-local/baselines', base, 'extracted');
const folders = ['storage', 'security', 'parental-controls'];
const metadata = Object.fromEntries(folders.map(p => [p, JSON.parse(fs.readFileSync(path.join(work, p, 'source-contracts.json')))]));
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const buffers = new Map(), used = [], cases = [];
const plain = value => JSON.parse(JSON.stringify(value));
function exact(page, record) {
  if (!buffers.has(record.sourcePath)) {
    const b = fs.readFileSync(path.join(frozen, record.sourcePath.replace(/^app.asar\//, '')));
    assert.equal(sha(b), record.sourceHash); buffers.set(record.sourcePath, b);
  }
  const b = buffers.get(record.sourcePath).subarray(record.byteRange.start, record.byteRange.endExclusive);
  assert.equal(sha(b), record.spanHash); used.push({page, ...record}); return b.toString();
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
const jsx = {jsx: (type, props) => ({type, props}), jsxs: (type, props) => ({type, props}), Fragment: 'fragment'};
const messages = new Proxy({}, {get: (_, key) => ({id: String(key)})});
const formatter = {formatMessage: m => m.id, formatList: items => items.join(', '), locale: 'en'};
function nodes(v) {
  if (!v || typeof v !== 'object') return [];
  if (Array.isArray(v)) return v.flatMap(nodes);
  return [v, ...Object.values(v.props ?? {}).flatMap(nodes)];
}
class OwnedApiError extends Error {constructor(status, code) {super('owned'); this.status = status; this.errorCode = code;}}
const thread = (id, parentId = null, extra = {}) => ({id, parentId, updatedAt: 10, status: {type: 'idle'}, ephemeral: false, source: 'owned-source', threadSource: 'owned-desktop', ...extra});
const entry = (value, archived = true) => ({thread: value, archived});
const eligible = unit('storage', 'Le', {le: t => t.parentId, _e: s => s === 'owned-desktop'});
function cleanup(options = {}) {
  const calls = [], parent = thread('parent'), child = thread('child', 'parent'), entries = [entry(parent), entry(child)];
  const review = {entries, cutoff: 100, archivedOnly: true};
  const fresh = plain(review); options.change?.(fresh);
  const backend = {discoverSubagentDescendantSnapshot: async (...a) => {calls.push(['discover', ...plain(a)]); return {isComplete: !options.incomplete, descendantThreads: [options.active ? {...child, status: {type: 'active'}} : child]};},
    sendRequest: async (method, args) => {calls.push([method, plain(args)]); if (options.fail === method) throw Error('owned failure'); return {thread: options.changedRead ? {...thread(args.threadId), updatedAt: 11} : (args.threadId === 'parent' ? parent : child)};}};
  const run = unit('storage', 'ze', {Re: () => !options.unsupported, Ie: async () => fresh, Le: eligible, se: x => x});
  return {calls, run: () => run(backend, review, new Set(options.unselected ? [] : ['parent']), 'owned-version')};
}
function measurement(options = {}) {
  const calls = [], configs = [], query = {}, data = {status: 'ready', completedCategories: ['threads', 'subagents', 'archived'], measuredAt: 1,
    usage: {totalBytes: 10, codexHome: '/owned/synthetic-home', categories: [{category: 'threads', bytes: 10}], threadBytes: {}}, ...options.data};
  const env = {it: memo, Q: jsx, V: () => formatter, at: {useId: () => 'owned-chart'}, I: () => ({cancelQueries: async a => calls.push(['cancel', plain(a)]), setQueryData: (...a) => calls.push(['cache', ...plain(a)])}),
    re: cfg => {query.cfg = cfg; return {data, isPending: false, isError: !!options.error};}, ue: x => x, rt: unit('storage', 'rt'), de: cfg => {configs.push(cfg); return {mutate: () => calls.push(['refresh-mutation']), isPending: !!options.refreshing};},
    J: 'message', Pe: n => String(n), i: 'button', Te: 'skeleton', me: (...a) => a.join(' '), ot: {threads: 'owned-style'}, st: messages, Qe: 'cleanup'};
  const service = {read: async () => {calls.push(['read']); return data;}, refresh: async () => {calls.push(['refresh']); return data;}};
  return {tree: unit('storage', 'nt', env)({service, hostId: 'local'}), calls, configs, query};
}
function password(options = {}) {
  const calls = [], keys = {changePassword: 'change', addPassword: 'add', protection: 'protection'};
  const env = {Fa: memo, Ia: jsx, An: () => keys, rt: key => key === 'protection' ? {data: {advanced_protection_mode_enabled: !!options.protected}, isSuccess: !options.loading} : {data: {eligible: key === 'change' ? !!options.change : !!options.add}, isSuccess: !options.loading},
    vt: cfg => ({isPending: !!options.pending, isSuccess: false, mutate: value => calls.push(value)}), zn: () => {}, Pa: () => {},
    wn: {Header: 'header', Content: 'content'}, K: 'message', ot: 'login-row', Ze: 'rows', k: 'arrow', $r: 'auth-error'};
  return {tree: unit('security', 'Na', env)({accountId: 'owned-A', passkeyCount: options.passkeys, onOpenPasskeys: () => {}}), calls};
}
function securityPreferences(options = {}) {
  const calls = [], configs = [], env = {vi: memo, yi: jsx, C: () => ({query: {snapshot: () => ({invalidate: async () => calls.push(['invalidate'])})}}), D: 'scope',
    Kt: () => ({data: {accounts: [{id: 'owned-A', structure: options.structure ?? 'personal'}]}}), p: () => ({data: options.missing ? null : {enableDeviceCodeAuth: true, connectorEnforceCspInDevMode: false}}), _t: 'settings', te: () => ({get: () => options.csp ?? true}),
    vt: cfg => {configs.push(cfg); return {isPending: !!options.pending, isError: !!options.error, mutate: arg => calls.push(['mutate', plain(arg)])};}, n: {safePatch: async (...a) => calls.push(['patch', ...plain(a)])},
    wn: {Header: 'header', Content: 'content'}, Ze: 'rows', G: 'row', K: 'message', t: 'switch', _i: () => {}};
  return {tree: unit('security', 'gi', env)({accountId: 'owned-A'}), calls, configs};
}
function sessions(options = {}) {
  const calls = [], Wa = unit('security', 'Wa');
  const env = {n: 'owned-A', s: options.trusted ?? true, Wa, g: ['chatgpt-security', 'owned-A', 'sessions'], he: () => ({accountId: 'owned-A', accountUserId: 'owned-AU'}),
    l: {get: () => ({logProductEvent: (...a) => calls.push(['event', ...plain(a)])})}, be: 'events', Pt: 'logout-event', Cn: {ACCESS_LOGOUT_ACTION_LOCATION_SETTINGS_MODAL_LOG_OUT_ALL: 'settings'}, Xt: {ACCESS_LOGOUT_TYPE_USER_INITIATED: 'user'},
    jn: {safePost: async (...a) => {calls.push(['post', ...plain(a)]); if (options.fail) throw new OwnedApiError(409, 'conflict');}}, u: {invalidateQueries: async a => calls.push(['invalidate', plain(a)])}};
  return {run: callback('security', 'qa', s => s.includes('`/accounts/logout_all`'), env), calls};
}
function lockdown(options = {}) {
  const calls = []; let data = {lockdownModeEnabled: false, owned: true};
  const snapshot = {cancel: async () => calls.push(['cancel']), getData: () => data, setData: fn => {data = fn(data); calls.push(['set', plain(data)]);}, invalidate: async arg => calls.push(['invalidate', arg ? plain(arg) : null])};
  const controller = new AbortController();
  const env = {a: {query: {snapshot: () => snapshot}, get: () => ({success: () => calls.push(['success']), danger: () => calls.push(['danger']), accountId: 'owned-A', userId: 'owned-U'})}, _t: 'settings',
    x: () => !options.denied, i: {accountId: 'owned-A', userId: 'owned-U'}, Xr: 'identity', ue: 'toast', Jr: jsx, K: 'message', Lr: messages,
    Gr: unit('security', 'Gr'), Hr: unit('security', 'Hr'), Wr: () => true, Ur: () => false,
    n: {safePatch: async (...args) => {calls.push(['patch', ...plain(args)]); if (options.abort) controller.abort(); if (options.fail) throw Error('owned rejected');}}};
  const run = callback('security', 'Br', s => s.includes('async e=>') && s.includes('safePatch'), env);
  return {run: enabled => run({controller, enabled}), calls, data: () => data};
}
function family(options = {}) {
  const calls = [], values = [!!options.inviteOpen, options.invitedIdentifier]; let index = 0;
  const params = new URLSearchParams(options.member ? {member: options.member} : {});
  const env = {Q: memo, $: jsx, u: () => ({}), d: 'scope', ee: () => formatter,
    Ge: {useState: () => {const i = index++; return [values[i], value => calls.push(['state', i, value])];}}, p: () => [params, arg => calls.push(['search', String(arg)])], _: () => url => calls.push(['navigate', url]), URLSearchParams,
    S: 'redirect', be: 'back', x: 'row', j: 'message', ie: 'page', re: 'title', ye: 'help', ke: 'notices', Ue: () => {}, o: 'button',
    Ce: (...a) => calls.push(['incoming', ...plain(a)]), K: {Header: 'header', Content: 'content'}, D: 'rows', te: 'member-row', ne: 'avatar', f: 'arrow', xe: 'owner-icon', b: 'plus', oe: 'invite-dialog',
    Se: 'remove-relationship', _e: 'member-summary', se: 'invited-detail', ge: 'member-settings', He: unit('parental-controls', 'He')};
  return {tree: unit('parental-controls', 'Ve', env)({userId: 'owned-U', accountId: 'owned-A', amphoraId: options.noFamily ? undefined : 'owned-F', role: options.role ?? 'owner', members: options.members, incomingInvite: options.incoming}), calls};
}
function incoming(options = {}) {
  const env = {Q: memo, $: jsx, u: () => ({queryClient: {invalidateQueries: async () => {}}}), d: 'scope',
    de: () => ({notifications: cursor => ({queryKey: ['owned-notifications', cursor]})}), O: () => ({data: {items: options.items ?? [], cursor: options.cursor ?? null}, isPending: false, isError: false}),
    We: 'loading', J: 'retry', Ve: 'family-home', ze: 'incoming-family'};
  return unit('parental-controls', 'Re', env)({userId: 'owned-U', accountId: 'owned-A', unavailableFamilyIds: options.unavailable ?? []});
}
function notices(options = {}) {
  const calls = [], refs = [], cleanups = [], states = []; let index = 0;
  let current = true, data = {notices: [{id: 'old', recipient_type: 'teen'}, {id: 'new', recipient_type: 'parent'}]};
  const client = {cancelQueries: async arg => {calls.push(['cancel', plain(arg)]); if (options.switchBeforePost) current = false;},
    setQueryData: (key, fn) => {data = fn(data); calls.push(['cache', plain(data)]);}, invalidateQueries: arg => calls.push(['invalidate', plain(arg)])};
  const env = {Ne: memo, Z: jsx, u: () => ({}), d: 'scope', C: () => client,
    O: cfg => ({data, isPending: false, isError: false, isFetching: false}), P: {ONE_MINUTE: 60000},
    X: {useState: () => [null, value => {states.push([index, value]);}], useRef: value => {const r = {current: value}; refs.push(r); return r;}, useEffect: fn => cleanups.push(fn())},
    ue: () => current, AbortController, t: {safeGet: () => {}, safePost: async (...a) => {calls.push(['post', ...plain(a)]); if (options.fail) throw Error('owned failure'); if (options.abortInPost) refs[0].current.abort();}},
    le: 'loading', j: 'message', x: 'row', o: 'button', Ae: 'notice-group'};
  const tree = unit('parental-controls', 'ke', env)({account: {userId: 'owned-U', accountId: 'owned-A'}});
  return {tree, calls, refs, cleanups, states, data: () => data};
}
const flush = () => new Promise(resolve => setImmediate(resolve));

(async () => {
  await check('STORAGE-LOCAL-SERVICE-VERSUS-REMOTE-MANAGEMENT', () => {
    const env = {ft: memo, $: jsx, Oe: () => ({selectedHostId: 'remote'}), x: 'local', B: {deviceStorage: 'owned-service'}, De: 'title', je: 'page', ut: 'storage-body'};
    assert.equal(unit('storage', 'lt', env)().props.children.props.storageService, undefined);
    env.Oe = () => ({selectedHostId: 'local'}); assert.equal(unit('storage', 'lt', env)().props.children.props.storageService, 'owned-service');
  });
  await check('STORAGE-SCANNING-POLL-AND-COMPLETE-CATEGORY-GATE', () => {
    const poll = unit('storage', 'rt'); assert.equal(poll({state: {data: {status: 'scanning'}}}), 1000); assert.equal(poll({state: {data: {status: 'ready'}}}), false);
    assert(nodes(measurement().tree).find(n => n.type === 'cleanup').props.storage);
    for (const opts of [{error: true}, {refreshing: true}, {data: {completedCategories: ['threads']}}]) assert.equal(nodes(measurement(opts).tree).find(n => n.type === 'cleanup').props.storage, undefined);
  });
  await check('STORAGE-READ-REFRESH-CANCEL-CACHE-OWNERSHIP', async () => {
    const f = measurement(); await f.query.cfg.queryFn({signal: 'owned-signal'}); await f.configs[0].onMutate(); const data = await f.configs[0].mutationFn(); f.configs[0].onSuccess(data);
    assert.deepEqual(f.calls.map(c => c[0]), ['read', 'cancel', 'refresh', 'cache']); assert.equal(f.query.cfg.retry, false); assert.equal(f.query.cfg.refetchOnWindowFocus, false);
  });
  await check('STORAGE-ELIGIBLE-PARENT-DESCENDANTS-AND-BYTE-COVERAGE', () => {
    const entries = [entry(thread('parent')), entry(thread('child', 'parent')), entry(thread('new', null, {updatedAt: 100}))];
    const result = eligible(entries, 100, true); assert.equal(result.length, 1); assert.equal(result[0].descendants.length, 1);
    const size = unit('storage', 'Fe', {Le: eligible}); assert.equal(size({entries, cutoff: 100, archivedOnly: true}, {threadBytes: {parent: 10, child: 5}})[0].bytes, 15);
    assert.equal(size({entries, cutoff: 100, archivedOnly: true}, {threadBytes: {parent: 10}}).length, 0);
  });
  await check('STORAGE-UNSAFE-SOURCE-ACTIVE-EPHEMERAL-AND-TIME-EXCLUSIONS', () => {
    for (const extra of [{source: 'unknown'}, {source: null}, {threadSource: 'cloud_threads.create'}, {ephemeral: true}, {status: {type: 'active'}}, {updatedAt: 0}, {updatedAt: NaN}, {updatedAt: 100}]) assert.equal(eligible([entry(thread('p', null, extra))], 100, true).length, 0);
    assert.equal(eligible([entry(thread('p'), false)], 100, true).length, 0);
    assert.equal(eligible([entry(thread('p')), entry(thread('c', 'p')), entry(thread('c', 'p'))], 100, true).length, 0);
    assert.equal(eligible([entry(thread('p')), entry(thread('c', 'p', {status: {type: 'active'}}))], 100, true).length, 0);
  });
  await check('STORAGE-INVENTORY-BOTH-ARCHIVE-STATES-AND-MISSING-ID-RECOVERY', async () => {
    const calls = [], inventory = unit('storage', 'Ie', {ae: ['owned-kind']});
    const result = await inventory({sendRequest: async (method, args) => {calls.push([method, plain(args)]); return method === 'thread/list' ? {data: [thread(args.archived ? 'archived' : 'live')], nextCursor: null} : {thread: thread(args.threadId)};}}, 100, true, ['missing']);
    assert.equal(result.entries.length, 3); assert.equal(calls.filter(c => c[0] === 'thread/list').length, 2); assert(calls.filter(c => c[0] === 'thread/list').every(c => c[1].useStateDbOnly));
    assert.deepEqual(calls.find(c => c[0] === 'thread/read')[1], {threadId: 'missing', includeTurns: false});
  });
  await check('STORAGE-INVENTORY-DUPLICATES-AND-WRONG-RECOVERY-ID-REJECT', async () => {
    const inventory = unit('storage', 'Ie', {ae: []});
    await assert.rejects(() => inventory({sendRequest: async () => ({data: [thread('duplicate')], nextCursor: null})}, 100, true, []), /pagination/);
    await assert.rejects(() => inventory({sendRequest: async method => method === 'thread/list' ? {data: [], nextCursor: null} : {thread: thread('wrong')}}, 100, true, ['missing']), /recovery/);
  });
  await check('STORAGE-CLEANUP-RECHECKS-ALL-THEN-DELETES-ONLY-PARENT', async () => {
    const f = cleanup(); assert.deepEqual(plain(await f.run()), {deleted: 1, skipped: 0, failed: 0});
    assert.deepEqual(f.calls.map(c => c[0]), ['discover', 'thread/read', 'thread/read', 'thread/delete']); assert.equal(f.calls[3][1].threadId, 'parent'); assert.equal(f.calls[0][2].reconcile, false);
  });
  await check('STORAGE-CLEANUP-CHANGED-INCOMPLETE-ACTIVE-AND-FAILED-OUTCOMES', async () => {
    for (const opts of [{change: r => {r.entries[0].thread.updatedAt++;}}, {incomplete: true}, {active: true}, {changedRead: true}]) {
      const f = cleanup(opts); assert.equal((await f.run()).skipped, 1); assert.equal(f.calls.some(c => c[0] === 'thread/delete'), false);
    }
    const failure = cleanup({fail: 'thread/delete'}); assert.equal((await failure.run()).failed, 1);
    const unsupported = cleanup({unsupported: true}); await assert.rejects(unsupported.run, /descendant/); assert.equal(unsupported.calls.length, 0);
    const unselected = cleanup({unselected: true}); assert.deepEqual(plain(await unselected.run()), {deleted: 0, skipped: 0, failed: 0});
  });
  await check('STORAGE-REVIEW-CONFIRM-SUPPRESSES-DUPLICATE-SUBMIT', () => {
    const calls = [], ref = {current: false}; const confirm = callback('storage', 'We', s => s.includes('s(u,_)'), {b: ref, s: (...a) => calls.push(a), u: 'review', _: 'selected'}); confirm(); confirm(); assert.equal(calls.length, 1);
  });
  await check('STORAGE-MANAGEMENT-LINKS-PRESERVE-HOST-ID', () => {
    const calls = [], tree = unit('storage', 'dt', {ft: memo, $: jsx, A: () => url => calls.push(url), J: 'message', N: 'row', i: 'button', ne: 'rows', URLSearchParams})({hostId: 'owned remote'});
    for (const row of nodes(tree).filter(n => n.type === 'row')) row.props.control({}).props.onClick();
    assert.deepEqual(calls, ['/settings/worktrees?hostId=owned+remote', '/settings/archived-chats?hostId=owned+remote']);
  });
  await check('SECURITY-PASSWORD-ELIGIBILITY-AND-ADVANCED-PROTECTION', () => {
    const f = password({change: true, add: true}); nodes(f.tree).find(n => n.type === 'login-row').props.onClick(); assert.equal(f.calls[0], 'change');
    const add = password({add: true}); nodes(add.tree).find(n => n.type === 'login-row').props.onClick(); assert.equal(add.calls[0], 'add');
    assert.equal(password({}).tree, null); assert.equal(nodes(password({change: true, protected: true}).tree).find(n => n.type === 'login-row').props.disabled, true);
  });
  await check('SECURITY-CODEX-DEVICE-CODE-PERSONAL-GUARD-AND-CSP-FLAG', async () => {
    const f = securityPreferences(), rows = nodes(f.tree).filter(n => n.type === 'row'); assert.equal(rows.length, 2);
    rows[1].props.control({}).props.onChange(false); assert.deepEqual(f.calls[0], ['mutate', {feature: 'enable_device_code_auth', value: false}]);
    await f.configs[0].mutationFn({feature: 'enable_device_code_auth', value: false});
    assert.deepEqual(f.calls[1], ['patch', '/settings/account_user_setting', {additionalHeaders: {'ChatGPT-Account-ID': 'owned-A'}, parameters: {query: {feature: 'enable_device_code_auth', value: false}}}]); assert.equal(f.calls[2][0], 'invalidate');
    assert.equal(nodes(securityPreferences({structure: 'workspace', csp: false}).tree).filter(n => n.type === 'row').length, 0);
    assert(nodes(securityPreferences({pending: true}).tree).filter(n => n.type === 'row').every(n => n.props.control({}).props.disabled));
  });
  await check('SECURITY-TRUSTED-SIGNED-OUT-DEVICE-PREDICATE', () => {
    const predicate = unit('security', 'Wa'), good = {is_trusted_device: true, can_untrust: true, is_current_device: false, session_id: '', hashed_device_id: 'owned-hash'};
    assert.equal(predicate(good), true);
    for (const change of [{is_trusted_device: false}, {can_untrust: false}, {is_current_device: true}, {session_id: 'active'}, {hashed_device_id: ' '}]) assert.equal(predicate({...good, ...change}), false);
  });
  await check('SECURITY-REVOKE-SESSION-EXCLUDES-CURRENT-AND-EMPTY-ID', async () => {
    const f = sessions(); await f.run({session_id: 'owned-session', is_current_device: false}); assert.equal(f.calls[0][1], '/accounts/sessions/revoke'); assert.equal(f.calls[1][0], 'invalidate');
    for (const row of [{session_id: 'owned-current', is_current_device: true}, {session_id: ' '}]) {const denied = sessions(); await denied.run(row); assert.equal(denied.calls.length, 0);}
  });
  await check('SECURITY-REVOKE-TRUST-REFRESHES-EVEN-ON-CONFLICT', async () => {
    for (const fail of [false, true]) {
      const f = sessions({fail}), row = {is_trusted_device: true, can_untrust: true, is_current_device: false, session_id: '', hashed_device_id: 'owned-hash'};
      if (fail) await assert.rejects(() => f.run(row)); else await f.run(row);
      assert.equal(f.calls[0][1], '/accounts/trusted_devices/revoke'); assert.equal(f.calls[1][0], 'invalidate');
    }
  });
  await check('SECURITY-LOGOUT-ALL-CAPTURES-SNAPSHOT-AND-LOCAL-IDENTITY-GUARD', async () => {
    const f = sessions(), result = await f.run('all'); assert.equal(result.accountId, 'owned-A'); assert.equal(f.calls[1][1], '/accounts/logout_all');
    const snapshot = {accountId: 'owned-A', accountUserId: 'owned-AU', userId: 'owned-U'};
    for (const [current, expected] of [[snapshot, true], [{...snapshot, accountId: 'other'}, false], [{...snapshot, accountUserId: 'other'}, false], [{...snapshot, userId: 'other'}, false], [null, false]]) {
      const valid = unit('security', 'Ka', {Ga: x => typeof x === 'string' && x.trim().length > 0, he: () => current}); assert.equal(valid({accountId: 'owned-A', authSnapshot: snapshot}), expected);
    }
  });
  await check('SECURITY-SESSION-REVIEW-ACKNOWLEDGES-ONLY-FRESH-SUCCESS-ONCE', async () => {
    const calls = [], sent = {current: false}, mutate = () => calls.push('ack');
    const run = callback('security', 'qa', s => s.includes('M.current=!0,P.mutate'), {c: true, n: 'owned-A', d: 'owned-U', A: true, O: false, k: true, M: sent, P: {mutate}}); run(); run(); assert.deepEqual(calls, ['ack']);
    const post = []; await unit('security', 'to', {n: {safePost: async (...a) => post.push(plain(a))}})({accountId: 'owned-A', userId: 'owned-U'});
    assert.deepEqual(post[0][1].expectedIdentity, {accountId: 'owned-A', userId: 'owned-U'}); assert.equal(post[0][1].retry, false);
  });
  await check('SECURITY-ADVANCED-PROTECTION-DISABLE-RECHECKS-AUTH-AND-MOUNT', async () => {
    for (const variant of ['current', 'unmounted', 'other-account', 'stale']) {
      const calls = [], run = callback('security', 'ai', s => s.includes('`/accounts/security_settings/advanced_protection_mode/disable`'), {r: 'owned-A', ge: async () => ({accountId: variant === 'other-account' ? 'other' : 'owned-A', accessToken: 'owned'}), d: {current: variant !== 'unmounted'}, Hn: () => variant !== 'stale', u: {current: null}, AbortController,
        n: {safePost: async (...a) => calls.push(plain(a))}});
      assert.equal(await run(), variant === 'current' ? 'disabled' : variant === 'unmounted' ? 'cancelled' : 'reauth_required'); assert.equal(calls.length, variant === 'current' ? 1 : 0);
    }
  });
  await check('SECURITY-LOCKDOWN-OPTIMISTIC-ENABLE-ROLLBACK-AND-DENIED', async () => {
    const ok = lockdown(); await ok.run(true); assert.equal(ok.data().lockdownModeEnabled, true); assert.equal(ok.calls[0][0], 'cancel'); assert.equal(ok.calls[1][0], 'set'); assert.equal(ok.calls[2][0], 'patch');
    const rejected = lockdown({fail: true}); await rejected.run(true); assert.equal(rejected.data().lockdownModeEnabled, false); assert(rejected.calls.some(c => c[0] === 'danger'));
    const denied = lockdown({denied: true}); await denied.run(true); assert.equal(denied.calls.some(c => c[0] === 'patch'), false);
  });
  await check('SECURITY-PASSKEY-TOKEN-ENROLLMENT-REDIRECT-IS-DELEGATED', async () => {
    const calls = [], queries = [], env = {pi: memo, J: jsx, mi: {useEffect: fn => fn()}, rt: cfg => {queries.push(cfg); return {data: {state_token: 'owned-state'}, isError: false, refetch: () => {}};},
      jn: {safePost: async (...a) => calls.push(['post', ...plain(a)])}, _e: () => ({auth: {loginWebUrl: 'https://auth.owned.invalid/'}}), Xn: () => '/settings/security', URL, window: {location: {assign: url => calls.push(['redirect', url])}}, qn: 'loading'};
    unit('security', 'fi', env)({accountId: 'owned-A'}); await queries[0].queryFn({signal: 'owned-signal'});
    const url = new URL(calls[0][1]); assert.equal(url.pathname, '/passkey-enroll'); assert.equal(url.searchParams.get('mfa_token'), 'owned-state'); assert.equal(url.searchParams.get('redirect_path'), '/settings/security?view=passkeys');
    assert.equal(queries[0].retry, false); assert.equal(queries[0].gcTime, 0); assert.equal(calls[1][1], '/accounts/mfa/user/request_mfa_token_in_house');
  });
  await check('SECURITY-MFA-DISABLE-REQUIRES-EXISTING-FACTOR', () => {
    const env = {pi: memo, J: jsx, Qe: () => ({email: 'owned@invalid'}), An: () => ({mfa: 'factors'}), rt: () => ({data: {factors: {passkeys: [{id: 'owned-key', metadata: {factor_name: 'Owned'}}], sms: [], totp: []}}}), Un: 'disable-confirm', Ln: 'setup', fi: 'passkey-enroll'};
    const render = unit('security', 'di', env); assert.equal(render({accountId: 'owned-A', action: {action: 'disable', factor: 'passkey', factorId: 'missing'}}), null);
    assert.equal(render({accountId: 'owned-A', action: {action: 'disable', factor: 'passkey', factorId: 'owned-key'}}).props.passkeyName, 'Owned');
  });
  await check('SECURITY-PASSKEY-RENAME-TRIMS-AND-USES-FACTOR-ID', async () => {
    const calls = [], save = callback('security', 'Ba', s => s.includes('`/accounts/mfa/user/update_factor_name`'), {n: 'owned-A', r: {id: 'owned-key'}, u: '  Owned Key  ', jn: {safePost: async (...a) => calls.push(plain(a))}}); await save();
    assert.deepEqual(calls[0][1], {additionalHeaders: {'ChatGPT-Account-ID': 'owned-A'}, requestBody: {factor_id: 'owned-key', factor_name: 'Owned Key'}});
  });
  await check('SECURITY-LEGACY-DELETE-AND-MODERN-REVOKE-ARE-DISTINCT', async () => {
    const calls = [], api = {safeDelete: async (...a) => calls.push(['delete', ...plain(a)]), safePost: async (...a) => calls.push(['post', ...plain(a)])};
    await callback('security', 'la', s => s.includes('safeDelete'), {n: 'owned-A', jn: api})('legacy');
    await callback('security', 'Xi', s => s.includes('safePost'), {r: 'owned-A', n: {id: 'modern'}, jn: api})({type: 'plugins'});
    assert.equal(calls[0][1], '/client_applications/{client_id}'); assert.equal(calls[1][1], '/client_applications/{client_id}/permissions/revoke'); assert.deepEqual(calls[1][2].requestBody, {target: {type: 'plugins'}});
  });
  await check('SECURITY-PERMISSION-CONFLICT-FETCHES-FRESH-STATE', async () => {
    const calls = [], conflict = callback('security', 'Xi', s => s.includes('fetchQuery') && s.includes('status===409'), {i: OwnedApiError, g: {queryKey: ['owned-permissions']}, c: {cancelQueries: async a => calls.push(['cancel', plain(a)]), fetchQuery: async a => calls.push(['fetch', plain(a)])}, Qi: () => {}});
    await conflict(new OwnedApiError(404, 'missing')); assert.equal(calls.length, 0); await conflict(new OwnedApiError(409, 'conflict')); assert.equal(calls[1][1].staleTime, 0);
  });
  await check('SECURITY-PIN-EXPECTED-ERRORS-AND-OPERATION-IDENTITY', () => {
    const pin = unit('security', 'assignment-Nr'); assert.equal(pin.test('1234'), true);
    for (const value of ['123', '12345', '123456', '12ab', '１２３４']) assert.equal(pin.test(value), false);
    const expected = unit('security', 'Dr'); assert.equal(expected({errorCode: 'invalid_pin'}), true); assert.equal(expected({errorCode: 'pin_locked'}), true); assert.equal(expected({errorCode: 'other'}), false);
    const identity = {current: 'owned-A:owned-U'}, generation = {current: 1}, valid = callback('security', 'kr', s => s.includes('return ae.current===e.identity'), {ae: identity, oe: generation});
    const token = {identity: 'owned-A:owned-U', generation: 1}; assert.equal(valid(token), true); generation.current++; assert.equal(valid(token), false); identity.current = null; assert.equal(valid(token), false);
  });
  await check('FAMILY-ACCESS-LOADING-ERROR-DENIED-AND-IDENTITY', () => {
    for (const status of ['loading', 'error', 'denied', 'allowed']) {
      const env = {Q: memo, $: jsx, u: () => ({queryClient: {invalidateQueries: () => {}}}), d: 'scope', a: () => ({status, userId: 'owned-U', accountId: 'owned-A'}), G: 'access', Ee: 'access-state', Le: 'family'};
      const tree = unit('parental-controls', 'Ie', env)(); assert.equal(tree.type, status === 'allowed' ? 'family' : 'access-state'); if (status === 'allowed') assert.equal(tree.props.accountId, 'owned-A');
    }
  });
  await check('FAMILY-ROLE-INVITE-AND-NOTIFICATION-ENTRY-GUARDS', () => {
    const self = {user_id: 'owned-U', role: 'member_role', status: 'accepted'};
    for (const [role, members, canInvite] of [['owner', [self], true], ['child', [self], false], ['member_role', [self], true], ['member_role', [self, {user_id: 'other', status: 'accepted'}], false]]) {
      const f = family({role, members}); assert.equal(nodes(f.tree).some(n => n.type === 'button' && n.props.children?.some?.(x => x?.props?.id?.includes('add'))), canInvite);
      const notification = nodes(f.tree).find(n => n.type === 'button' && n.props.children?.props?.id === 'amphora.settings.safetyNotificationsButton'); assert.equal(!!notification, role === 'owner'); if (notification) {notification.props.onClick(); assert.deepEqual(f.calls[0], ['navigate', '/settings/notifications']);}
    }
  });
  await check('FAMILY-SELECTED-OWNER-SELF-AND-UNAVAILABLE-MEMBER', () => {
    const members = [{user_id: 'owned-U', role: 'owner', status: 'accepted'}, {user_id: 'child', role: 'child', status: 'accepted'}];
    assert(nodes(family({members, member: 'child'}).tree).some(n => n.type === 'member-settings'));
    assert.equal(nodes(family({role: 'child', members, member: 'child'}).tree).some(n => n.type === 'member-settings'), false);
    assert(nodes(family({members, member: 'missing'}).tree).some(n => n.props?.id === 'settings.chatGpt.parentalControls.memberUnavailable'));
    assert.equal(family({noFamily: true, member: 'stale'}).tree.type, 'redirect');
  });
  await check('FAMILY-INVITE-DIALOG-FORCED-ROLE-PROPS', () => {
    const owner = family({inviteOpen: true, role: 'owner', members: []}); assert.equal(nodes(owner.tree).find(n => n.type === 'invite-dialog').props.forceTeen, true);
    const alone = family({inviteOpen: true, role: 'member_role', members: [{user_id: 'owned-U', status: 'accepted'}]}); assert.equal(nodes(alone.tree).find(n => n.type === 'invite-dialog').props.forceParent, true);
  });
  await check('FAMILY-INCOMING-INVITATION-PAGINATION-AND-MALFORMED-PAYLOAD', () => {
    const next = incoming({cursor: 'next'}); assert.equal(typeof next.type, 'function'); assert.equal(next.type.name, 'Re'); assert.equal(next.props.cursor, 'next');
    assert.equal(incoming({}).type, 'family-home');
    assert.equal(incoming({items: [{notification_type: 'family-invite', payload: {}}]}).type, 'retry');
    const tree = incoming({items: [{id: 'done', notification_type: 'family-invite', reacted_to_at: 1, payload: {family_group_id: 'done'}}, {id: 'old', notification_type: 'family-invite', payload: {family_group_id: 'unavailable'}}, {id: 'good', notification_type: 'family-invite', payload: {family_group_id: 'owned-F'}}], unavailable: ['unavailable']}); assert.equal(tree.props.invitation.id, 'good');
  });
  await check('FAMILY-INCOMING-404-CONTINUES-NEXT-CANDIDATE', () => {
    const env = {Q: memo, $: jsx, u: () => ({}), d: 'scope', Te: () => null, de: () => ({members: () => ({staleTime: 1})}), O: () => ({isPending: false, isError: true, error: new OwnedApiError(404)}), n: OwnedApiError, J: 'retry', We: 'loading', Ve: 'family-home'};
    const tree = unit('parental-controls', 'ze', env)({userId: 'owned-U', accountId: 'owned-A', invitation: {id: 'owned-invite'}, amphoraId: 'owned-F', next: 'next-candidate'}); assert.equal(tree, 'next-candidate');
  });
  await check('FAMILY-NOTICE-DISMISS-CAPTURED-IDS-PRESERVES-NEWER-NOTICE', async () => {
    const f = notices(); nodes(f.tree).find(n => n.type === 'notice-group').props.onDismiss(['old']); await flush();
    assert.deepEqual(f.calls.find(c => c[0] === 'post')[2].requestBody, {notice_ids: ['old']}); assert.deepEqual(f.data().notices.map(n => n.id), ['new']);
    assert.equal(f.calls.at(-1)[1].refetchType, 'active'); assert.equal(f.refs[0].current, null);
  });
  await check('FAMILY-NOTICE-STALE-IDENTITY-ABORT-FAILURE-AND-CLEANUP', async () => {
    const switched = notices({switchBeforePost: true}); nodes(switched.tree).find(n => n.type === 'notice-group').props.onDismiss(['old']); await flush(); assert.equal(switched.calls.some(c => c[0] === 'post'), false); assert.equal(switched.calls.at(-1)[1].refetchType, 'none');
    const aborted = notices({abortInPost: true}); nodes(aborted.tree).find(n => n.type === 'notice-group').props.onDismiss(['old']); await flush(); assert.equal(aborted.calls.some(c => c[0] === 'cache'), false); assert.equal(aborted.calls.at(-1)[1].refetchType, 'none');
    const failure = notices({fail: true}); nodes(failure.tree).find(n => n.type === 'notice-group').props.onDismiss(['old']); await flush(); assert.equal(failure.calls.some(c => c[0] === 'cache'), false); assert(failure.states.some(s => JSON.stringify(s[1]) === '["old"]'));
    const cleanup = notices(), controller = new AbortController(); cleanup.refs[0].current = controller; cleanup.cleanups[0](); assert.equal(controller.signal.aborted, true); assert.equal(cleanup.calls[0][1].refetchType, 'none');
  });
  const result = {baselineId: base, method: 'exact-frozen-functions-callbacks-and-roots-in-owned-node-vm', sourceSelections: used,
    cases, passed: cases.filter(c => c.passed).length, failed: cases.filter(c => !c.passed).length,
    productScenariosExecuted: 0, modelSubmissionsAdded: 0, originalClientRunsAdded: 0, realServiceCalls: 0,
    actualFilesystemScans: 0, actualThreadDeletions: 0, actualAuthenticationChanges: 0, actualFamilyDataAccesses: 0,
    qualification: 'Owned synthetic inventories/identities/UI/query/auth/policy/service substitutes. Root rendering does not mount React. Parent/source/eligibility normalization and imported providers are fixtures. No target imports, real disk scan, credential, account/family service or model execution.'};
  fs.writeFileSync(process.argv[2] ?? path.join(work, 'isolated-observations.json'), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
  console.log(JSON.stringify({passed: result.passed, failed: result.failed, failures: cases.filter(c => !c.passed).map(c => ({id: c.id, error: c.error}))}));
  process.exitCode = result.failed ? 1 : 0;
})().catch(error => {console.error(error); process.exitCode = 1;});
