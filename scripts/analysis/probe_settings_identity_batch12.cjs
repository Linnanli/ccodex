// Exact frozen selections run with owned, in-memory service/query/UI substitutes.
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const assert = require('node:assert/strict'), crypto = require('node:crypto');
const root = path.resolve(__dirname, '../..'), base = 'codex-26.1007.30912-c5b273322a83';
const work = path.join(root, '.analysis-local/settings-identity-batch12-work');
const frozen = path.join(root, '.analysis-local/baselines', base, 'extracted');
const folders = ['agreements', 'account', 'extension', 'agreements-access'];
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
function assignment(page, name, env, result) {
  const r = metadata[page].units.find(u => u.name === name); assert(r);
  vm.runInNewContext(exact(page, r), env, {timeout: 1000}); return env[result];
}
async function check(id, run) {
  try { await run(); cases.push({id, passed: true}); }
  catch (error) { cases.push({id, passed: false, error: String(error.stack)}); }
}
const memo = {c: n => Array(n).fill(Symbol.for('react.memo_cache_sentinel'))};
const jsx = {jsx: (type, props) => ({type, props}), jsxs: (type, props) => ({type, props}), Fragment: 'fragment'};
const messages = new Proxy({}, {get: (_, key) => ({id: String(key)})});
const formatter = {formatMessage: (m, values) => m.defaultMessage === 'DELETE' ? 'DELETE' : m.id + (values ? JSON.stringify(values) : '')};
function nodes(v) {
  if (!v || typeof v !== 'object') return [];
  if (Array.isArray(v)) return v.flatMap(nodes);
  return [v, ...Object.values(v.props ?? {}).flatMap(nodes)];
}
class OwnedApiError extends Error {
  constructor(status, code, message = '{}') {super(message); this.status = status; this.errorCode = code;}
}
function agreements(options = {}) {
  const calls = [], configs = {}, client = {setQueryData: (key, fn) => calls.push(['merge', plain(key), plain(fn({other: 'kept'}))]),
    invalidateQueries: async arg => calls.push(['invalidate', plain(arg)])};
  const api = {safeGet: async (...a) => calls.push(['get', ...plain(a)]), safePost: async (...a) => calls.push(['post', ...plain(a)])};
  const env = {K: memo, q: jsx, Z: messages, S: 'Owned-Account', p: () => client, n: api,
    y: cfg => {configs.query = cfg; return {data: {workspace_baa_metadata: {}}, isPending: false, isError: false, refetch: () => calls.push(['refetch']), ...options.query};},
    w: cfg => {configs.mutation = cfg; return {mutate: () => calls.push(['mutate']), isPending: false, isError: false, ...options.mutation};},
    I: 'spinner', G: 'retry', R: Object.assign('section', {Header: 'header', Footer: 'footer'}), C: 'message', v: 'rows', f: 'row', L: 'link',
    J: 'owned-service-link', W: x => jsx.jsx('baa-link', {children: x}), U: x => x, a: 'button'};
  const tree = unit('agreements', 'H', env)({workspaceId: 'owned-A', isHipaaWorkspace: options.hipaa ?? true});
  return {calls, configs, tree};
}
function account(options = {}) {
  const calls = [], queries = [], mutations = [], states = options.states ?? [null, null, false]; let index = 0;
  const identity = {accountId: 'owned-A', userId: 'owned-U', email: 'fallback@owned.invalid', planAtLogin: 'owned-plan', ...options.identity};
  const current = options.missingUser ? null : {name: 'Original', email: 'user@owned.invalid', ...options.current};
  const env = {yn: memo, $: jsx, te: () => ({get: () => ({danger: (...a) => calls.push(['danger', ...a])})}), ne: 'scope',
    ve: () => formatter, ce: s => s, be: () => identity, _e: () => ({}), ge: () => ({invalidateQueries: async a => calls.push(['invalidate', plain(a)])}),
    Ke: () => ({data: {structure: options.structure ?? 'personal'}}), Te: {ONE_MINUTE: 60000}, fe: () => {},
    xe: cfg => {queries.push(cfg); return cfg.queryKey[0] === 'chatgpt-user-profile' ? {data: options.profile} : cfg.queryKey[0] === 'browser-chatgpt-auth' ? {data: {accessToken: 'owned-token'}, isLoading: !!options.authLoading} : {data: options.reauth ?? false};},
    se: () => ({data: current}), He: 'current-user', vn: () => {}, bn: {useState: () => {const i = index++; return [states[i], value => calls.push(['state', i, typeof value === 'function' ? value(options.draftAtSuccess) : value])];}},
    Se: cfg => {mutations.push(cfg); return {isPending: !!options.pending, mutate: value => calls.push(['mutate', value])};}, _n: () => {},
    st: async () => ({ok: true, url: 'owned-login'}), nt: () => {}, pe: () => {}, Ee: () => 'owned-login', le: 'toast', Rt: () => {},
    Re: 'title', at: {Header: 'header', Content: 'content'}, q: 'message', me: 'row', tt: 'input', l: 'button',
    un: 'username', nn: 'email', gt: 'age', z: 'rows', Ne: 'capability', xn: 'cme', qe: 'page', Dt: 'delete-dialog',
    je: arg => calls.push(['external', plain(arg)]), window: {location: {replace: url => calls.push(['replace', url])}}};
  return {tree: unit('account', 'gn', env)(), calls, queries, mutations};
}
function email(options = {}) {
  const queries = [], calls = [], states = [null, false]; let index = 0;
  const env = {an: memo, Q: jsx, te: () => ({get: () => ({})}), ne: 'scope', be: () => ({userId: 'owned-U', accountId: 'owned-A'}),
    ve: () => formatter, ue: () => () => {}, ee: () => ({state: null}), ce: x => x, _e: () => ({}),
    ge: () => ({setQueryData: () => {}}), se: () => ({data: {email: options.email ?? 'user@owned.invalid'}}), He: 'user',
    xe: cfg => {queries.push(cfg); return {data: cfg.queryKey[0] === 'change-email-eligibility' ? {eligible: options.eligible ?? true} : null};},
    rn: () => {}, on: {useState: () => [states[index++], () => {}]}, ut: () => false,
    Se: () => ({isPending: !!options.pending, mutate: () => calls.push(['local-mutate'])}),
    Be: arg => calls.push(['external', plain(arg)]), sn: messages, q: 'message', l: 'button', me: 'row', cn: 'email-modal'};
  return {tree: unit('account', 'nn', env)(), queries, calls};
}
function username(options = {}) {
  const calls = [], queries = [], keys = [];
  const env = {dn: memo, pn: jsx, fn: {useState: () => [!!options.open, v => calls.push(['open', v])]},
    G: cfg => {keys.push(plain(cfg)); return options.mutating ?? 0;}, Te: {ONE_MINUTE: 60000},
    T: {safeGet: async (...args) => {calls.push(['get', ...plain(args)]); return {profile: {username: options.username ?? '  owned  '}};}},
    xe: cfg => {queries.push(cfg); return {data: 'owned', isPending: !!options.pending, isError: !!options.error, refetch: () => calls.push(['refetch'])};},
    B: 'username-row', q: 'message', mn: 'username-modal'};
  const tree = unit('account', 'un', env)({accountId: options.accountId === undefined ? 'owned-A' : options.accountId, userId: 'owned-U'});
  return {tree, calls, queries, keys};
}
function deletion(options = {}) {
  const calls = [], refs = [], cleanups = []; let index = 0;
  const values = options.states ?? ['USER@OWNED.INVALID', ' DELETE ', false, false];
  const env = {jt: memo, Z: jsx, te: () => ({get: key => key === 'events' ? {logProductEvent: (...a) => calls.push(['event', ...plain(a)])} : {warning: x => calls.push(['warning', x])}}), ne: 'scope', ve: () => formatter,
    Mt: {useRef: value => {const ref = {current: value}; refs.push(ref); return ref;}, useState: () => {const i = index++; return [values[i], value => calls.push(['state', i, value])];}, useLayoutEffect: fn => cleanups.push(fn())},
    Qe: () => ({data: {}, isLoading: !!options.subscriptionLoading}), et: () => 'web', kt: () => options.recent ?? true,
    Se: cfg => {env.mutation = cfg; return {isPending: !!options.pending, mutate: () => calls.push(['mutate'])};},
    t: {safePost: async (...a) => calls.push(['post', ...plain(a)])}, Ct: async () => ({owned: 'risk'}),
    he: 'events', pt: 'account-event', mt: {CHATGPT_ACCOUNT_ACTION_DEACTIVATION_REQUESTED: 'deactivate'}, n: OwnedApiError, p: class Diagnostic extends Error {}, le: 'toast', At: () => 'owned error', AbortController,
    r: 'header', De: 'title', q: 'message', re: 'dialog', ie: 'form', L: 'layout', z: 'rows', oe: 'text', ye: 'actions', l: 'button', tt: 'input', me: 'row', ae: 'unused', it: x => x};
  env.Ot = unit('account', 'Ot', {Z: jsx, rt: 'external-help-link'});
  const tree = unit('account', 'Dt', env)({accessToken: options.token === undefined ? 'owned-token' : options.token,
    contactPoint: options.contact === undefined ? 'user@owned.invalid' : options.contact, contactPointKind: 'email',
    onClose: () => calls.push(['close']), onDeleted: async () => calls.push(['deleted']), onRefreshLogin: async signal => {calls.push(['refresh', signal.aborted]); return false;}});
  return {tree, calls, refs, cleanups, env};
}
function extension(options = {}) {
  const queries = [], calls = [], configs = [], prefs = {history_approval_mode: 'never_ask', full_cdp_access_enabled: true, ...options.preferences};
  const identity = {accountId: 'owned-A', userId: 'owned-U', authMethod: 'chatgpt', isLoading: false, ...options.identity};
  const settings = {revision: 7, preferences: prefs, rules: {}};
  const client = {invalidateQueries: async a => calls.push(['invalidate', plain(a)]), cancelQueries: async a => calls.push(['cancel', plain(a)]), setQueryData: (k, v) => calls.push(['set', plain(k), plain(v)])};
  const api = {safeGet: async (...a) => {calls.push(['get', ...plain(a)]); return {requirements: 'owned'};},
    safePatch: async (...a) => {calls.push(['patch', ...plain(a)]); if (options.patchFailure) throw options.patchFailure; return {revision: 8};}};
  const env = {Fe: memo, $: jsx, E: () => identity, v: () => client, a: key => key === 'account' ? {status: options.accountStatus ?? 'loaded', structure: options.structure ?? 'personal'} : key === 'selected-account' ? (options.selectedAccount ?? 'owned-A') : 'owned-U',
    ee: 'account', O: 'selected-account', ie: 'selected-user', Oe: ['browser-settings'], ke: ['browser-cloud-requirements'], ce: 'owned-skip', se: {ONE_MINUTE: 60000, FIVE_MINUTES: 300000}, g: api,
    D: cfg => {queries.push(cfg); return {data: queries.length === 1 ? settings : {requirements: options.requirements ?? null}, isPending: false, isError: !!options.queryError, isFetching: !!options.fetching};},
    we: x => ({normalized: x}), ne: cfg => {configs.push(cfg); return {mutate: arg => calls.push(['mutate', plain(arg)]), mutateAsync: async arg => calls.push(['mutateAsync', plain(arg)]), isPending: !!options.pending, error: options.error};},
    Se: () => options.extensionAllowed ?? true, xe: () => options.historyAllowed ?? true, be: () => options.neverAskAllowed ?? true,
    me: 'title', j: 'message', fe: 'error', ye: 'spinner', ve: 'page', Ee: 'site-editor', T: 'rows', _: 'row', Ae: 'dropdown', je: [{value: 'never_ask'}, {value: 'always_ask'}], Ie: messages,
    t: 'switch', Ne: () => {}, ge: 'risk-badge', w: 'risk-icon', Te: 'managed', C: 'managed-icon', n: OwnedApiError,
    o: 'owned-settings-changed', Event: class Event {constructor(type) {this.type = type;}}, window: {dispatchEvent: e => calls.push(['event', e.type])}};
  return {tree: unit('extension', 'Me', env)(), queries, calls, configs, settings};
}
function siteEditor(options = {}) {
  const calls = [], env = {V: memo, H: jsx, z: 'site-manager', B: x => x[0], De: () => {},
    W: {always_ask: 'alwaysAsk', never_ask: 'neverAsk', disabled: 'disabled'}, U: {origin: 'approval_mode', download: 'download_approval_mode', upload: 'upload_approval_mode'}, G: {default: null, allowed: 'allow', denied: 'deny'}};
  const settings = {revision: 7, preferences: options.preferences ?? {}, rules: options.rules ?? {}};
  const tree = unit('extension', 'Ee', env)({settings, enterprisePolicy: 'owned-policy', disabled: !!options.disabled, onUpdate: async arg => calls.push(plain(arg)), onWebMcpEnabledChange: 'owned-handler'});
  return {tree, calls};
}

(async () => {
  await check('AGREEMENT-ACCESS-DENIED-LOADING-ERROR-PLAN-HIPAA', () => {
    const select = assignment('agreements-access', 'assignment-f', {a: (_, fn) => fn, n: 'scope', o: 'access', l: 'account', t: 'accounts', u: x => x === 'eligible'}, 'f');
    const run = (access, accountId, query) => select({get: key => key === 'access' ? {status: access} : key === 'account' ? accountId : query});
    assert.equal(run('loading', 'owned-A', {}).status, 'loading'); assert.equal(run('allowed', null, {}).status, 'denied');
    assert.equal(run('allowed', 'owned-A', {isPending: true}).status, 'loading');
    assert.deepEqual(plain(run('allowed', 'owned-A', {isError: true})), {status: 'error', accountId: 'owned-A'});
    for (const [plan, expected] of [['other', 'denied'], ['eligible', 'allowed']]) {
      const q = {data: {account_ordering: ['x'], accounts: {x: {account: {account_id: 'owned-A', plan_type: plan, is_hipaa_compliant_workspace: true}}}}};
      const result = run('allowed', 'owned-A', q); assert.equal(result.status, expected); if (expected === 'allowed') assert.equal(result.isHipaaWorkspace, true);
    }
  });
  await check('AGREEMENT-QUERY-AND-SIGN-PAYLOADS-CACHE-SCOPE', async () => {
    const f = agreements(); await f.configs.query.queryFn({signal: 'owned-signal'}); await f.configs.mutation.mutationFn();
    assert.deepEqual(plain(f.configs.query.queryKey), ['account-agreements-metadata', 'owned-A']);
    assert.equal(f.calls[0][2].signal, 'owned-signal'); assert.equal(f.calls[0][2].parameters.path.account_id, 'owned-A');
    assert.equal(f.calls[1][1], '/quorum/workspace/{account_id}/sign_baa');
    assert.deepEqual(f.calls[1][2].additionalHeaders, {'ChatGPT-Account-ID': 'owned-A', 'Owned-Account': 'owned-A'});
    await f.configs.mutation.onSuccess({timestamp: 'owned-stamp'});
    assert.deepEqual(f.calls.slice(2), [['merge', ['account-agreements-metadata', 'owned-A'], {other: 'kept', workspace_baa_metadata: {signed: true, timestamp: 'owned-stamp'}}], ['invalidate', {queryKey: ['account-agreements-metadata', 'owned-A']}]]);
  });
  await check('AGREEMENT-UNSIGNED-HIPAA-AND-PENDING-CONTROLS', () => {
    assert.equal(nodes(agreements({hipaa: false}).tree).filter(n => n.type === 'button').length, 0);
    assert.equal(nodes(agreements({query: {data: {workspace_baa_metadata: {timestamp: 'bad-date'}}}}).tree).filter(n => n.type === 'button').length, 0);
    const explicitFalse = agreements({query: {data: {workspace_baa_metadata: {signed: false, timestamp: 'bad-date'}}}, mutation: {isPending: true}});
    const button = nodes(explicitFalse.tree).find(n => n.type === 'button'); assert.equal(button.props.disabled, true); assert.equal(button.props.loading, true);
    assert(nodes(agreements({query: {data: {workspace_baa_metadata: {signed: true, timestamp: 'bad-date'}}}}).tree).some(n => n.props?.control === 'bad-date'));
  });
  await check('AGREEMENT-LOADING-ERROR-STALE-DATA-AND-SIGN-ERROR', () => {
    assert.equal(agreements({query: {isPending: true}}).tree.type, 'spinner');
    const empty = agreements({query: {isError: true, data: null}}); assert.equal(empty.tree.type, 'retry'); empty.tree.props.onRetry(); assert.equal(empty.calls[0][0], 'refetch');
    const stale = agreements({query: {isError: true}, mutation: {isError: true}}); assert(nodes(stale.tree).some(n => n.type === 'retry')); assert(nodes(stale.tree).some(n => n.props?.role === 'alert'));
  });
  await check('ACCOUNT-NAME-PATCH-AND-NEWER-DRAFT-PRESERVATION', async () => {
    const calls = []; await unit('account', '_n', {t: {safePatch: async (...a) => calls.push(plain(a))}})('Owned');
    assert.deepEqual(calls[0], ['/accounts/users/name', {requestBody: {name: 'Owned'}}]);
    for (const [draft, expected] of [['Submitted', null], ['Newer', 'Newer']]) {
      const f = account({draftAtSuccess: draft}); await f.mutations[0].onSuccess({}, 'Submitted');
      assert.deepEqual(f.calls, [['invalidate', {queryKey: ['chatgpt-current-user']}], ['state', 0, expected]]);
    }
  });
  await check('ACCOUNT-NAME-DISABLED-AND-PROFILE-READONLY', () => {
    for (const opts of [{missingUser: true}, {pending: true}, {}]) {
      const f = account(opts); const save = nodes(f.tree).find(n => n.type === 'button' && n.props?.children?.props?.id === 'settings.chatGpt.account.save'); assert.equal(save.props.disabled, true);
    }
    const f = account({states: ['Owned', null, false], profile: {viewer_access: {can_edit: true}, profile_details: {display_name: 'Builder', username: 'owned'}}});
    assert.equal(nodes(f.tree).find(n => n.type === 'row' && n.props?.label === 'Builder').props.control, null);
    assert(nodes(f.tree).some(n => n.type === 'age')); assert(nodes(f.tree).some(n => n.type === 'capability' && n.props.name === 'chatgpt.cme'));
    assert.equal(f.queries.find(q => q.queryKey[0] === 'browser-chatgpt-auth').enabled, false);
  });
  await check('ACCOUNT-PERSONAL-DELETE-DIALOG-IDENTITY-AND-DISMISSAL', async () => {
    for (const [opts, visible] of [[{states: [null, 'owned-U:owned-A', false]}, true], [{structure: 'workspace', states: [null, 'owned-U:owned-A', false]}, false], [{states: [null, 'other:owned-A', false]}, false], [{reauth: true}, true], [{reauth: true, states: [null, null, true]}, false], [{missingUser: true, reauth: true}, false]]) {
      assert.equal(nodes(account(opts).tree).some(n => n.type === 'delete-dialog'), visible);
    }
    const f = account({reauth: true}), dialog = nodes(f.tree).find(n => n.type === 'delete-dialog');
    assert.equal(await dialog.props.onRefreshLogin({aborted: true}), false); assert.equal(f.calls.length, 0);
    assert.equal(await dialog.props.onRefreshLogin({aborted: false}), true); assert.equal(f.calls[0][1].openTarget, 'external-browser');
  });
  await check('ACCOUNT-PROFILE-READ-AND-EMAIL-ELIGIBILITY-SIGNAL', async () => {
    const calls = [], api = {safeGet: async (...a) => calls.push(plain(a))};
    await unit('account', 'vn', {t: api})(); await unit('account', 'rn', {t: api})({signal: 'owned-signal'});
    assert.deepEqual(calls, [['/profiles/me'], ['/accounts/change_email/eligibility', {signal: 'owned-signal'}]]);
  });
  await check('ACCOUNT-USERNAME-KEYS-QUERY-TRIM-EDITOR-AND-RETRY', async () => {
    const f = username({open: true}); assert.equal(await f.queries[0].queryFn({signal: 'owned-signal'}), 'owned');
    assert.deepEqual(plain(f.queries[0].queryKey), ['chatgpt-account-username', 'owned-A', 'owned-U']);
    assert.deepEqual(f.keys[0].mutationKey, plain(f.queries[0].queryKey)); assert.equal(f.calls[0][2].additionalHeaders['ChatGPT-Account-ID'], 'owned-A');
    assert.deepEqual(f.calls[0][2].expectedErrorStatuses, [403, 404]);
    assert.equal(nodes(f.tree).find(n => n.type === 'username-modal').props.initialUsername, 'owned');
    const error = username({error: true}); nodes(error.tree).find(n => n.type === 'username-row').props.onClick(); assert.deepEqual(error.calls, [['refetch']]);
    assert.equal(username({accountId: null}).queries[0].enabled, false); assert.equal(nodes(username({mutating: 1}).tree).find(n => n.type === 'username-row').props.disabled, true);
  });
  await check('ACCOUNT-EMAIL-NULL-CLIENT-USES-EXTERNAL-BRIDGE-NO-LOCAL-MODAL', () => {
    const f = email(), button = nodes(f.tree).find(n => n.type === 'button'); button.props.onClick({owned: true});
    assert.equal(f.queries.find(q => q.queryKey[0] === 'chatgpt-email-reauth').enabled, false);
    assert.equal(nodes(f.tree).some(n => n.type === 'email-modal'), false);
    assert.equal(f.calls[0][0], 'external'); assert.equal(f.calls[0][1].href, 'https://chatgpt.com/#settings/Account'); assert.equal(f.calls[0][1].openTarget, 'external-browser');
    assert.equal(nodes(email({eligible: false}).tree).some(n => n.type === 'button'), false);
    assert.equal(nodes(email({pending: true}).tree).find(n => n.type === 'button').props.disabled, true);
  });
  await check('DELETE-TOKEN-AGE-BOUNDARY-AND-MISSING-ISSUEDAT', () => {
    for (const [issuedAt, now, expected] of [[1000, 1599999, true], [1000, 1600000, false], [null, 9000000, true]]) {
      const recent = unit('account', 'kt', {A: () => issuedAt == null ? {} : {issuedAt}, Nt: 600000}); assert.equal(recent('owned-token', now), expected);
    }
  });
  await check('DELETE-REAUTH-IDENTITY-NONCE-AGE-AND-AUTH-TIME', async () => {
    const now = 2000000000000;
    for (const variant of ['seconds', 'milliseconds', 'wrong-user', 'wrong-nonce', 'expired', 'future', 'old-auth', 'aborted']) {
      const saved = {userId: variant === 'wrong-user' ? 'other' : 'owned-U', accountId: 'owned-A', requestedAtMs: now - (variant === 'expired' ? 600001 : variant === 'future' ? -1 : 2000), returnNonce: variant === 'wrong-nonce' ? 'other' : 'nonce'};
      const calls = [], env = {fe: async () => ({userId: 'owned-U', accountId: 'owned-A', accessToken: 'owned-token'}), URL, Vt: 'account_deletion_reauth', Bt: 'pending', Ht: 60000,
        Date: class extends Date {static now() {return now;}}, Ut: {parse: x => x}, Wt: {parse: x => x}, F: () => ({pwd_auth_time: variant === 'milliseconds' ? now : Math.floor((now - (variant === 'old-auth' ? 70000 : 1000)) / 1000)}), zt: () => calls.push('clear'),
        window: {location: {href: 'https://owned.invalid/?account_deletion_reauth=nonce'}, history: {state: null, replaceState: (_, __, url) => calls.push(['replace', String(url)])}, sessionStorage: {getItem: () => JSON.stringify(saved), removeItem: () => calls.push('consume')}}};
      const result = await unit('account', 'Rt', env)({userId: 'owned-U', accountId: 'owned-A', signal: {aborted: variant === 'aborted'}});
      assert.equal(result, ['seconds', 'milliseconds'].includes(variant), variant); assert.equal(calls.includes('consume'), variant !== 'aborted');
    }
  });
  await check('DELETE-RISK-HEADERS-PRIMARY-FALLBACK-AND-EMPTY', async () => {
    for (const variant of ['primary', 'fallback', 'empty']) {
      const env = {Ae: async () => {if (variant !== 'primary') throw Error('owned provider missing'); return {token: async purpose => {assert.equal(purpose, 'deactivate'); return 'owned-primary';}, timing: async () => 'owned-timing'};}, Le: 'provider', wt: 'deactivate', Ge: {sentinelToken: 'risk', timing: 'timing'}, Tt: '[1,null]',
        window: {SentinelSDK: {requirementsToken: () => variant === 'fallback' ? 'owned-fallback' : ''}}};
      const headers = plain(await unit('account', 'Ct', env)());
      if (variant === 'primary') assert.deepEqual(headers, {risk: 'owned-primary', timing: 'owned-timing'});
      else if (variant === 'fallback') assert.equal(JSON.parse(headers.risk).c, 'owned-fallback'); else assert.deepEqual(headers, {});
    }
  });
  await check('DELETE-ERROR-ORGANIZATION-OWNER-AND-GENERIC', () => {
    const errorText = unit('account', 'At', {n: OwnedApiError, Ft: 'scim', Pt: 'owner', It: {safeParse: data => ({success: true, data})}});
    assert(errorText(new OwnedApiError(403, 'scim'), formatter).endsWith('scim_managed'));
    assert(errorText(new OwnedApiError(403, 'owner', JSON.stringify({detail: {workspace_name: 'Owned'}})), formatter).includes('Owned'));
    assert(errorText(new Error('owned'), formatter).endsWith('generic'));
  });
  await check('DELETE-CONFIRMATION-KEYWORD-CONTACT-LOADING-PENDING', () => {
    for (const [opts, enabled] of [[{}, true], [{states: ['other', 'DELETE', false, false]}, false], [{states: ['USER@OWNED.INVALID', 'delete', false, false]}, false], [{subscriptionLoading: true}, false], [{pending: true}, false], [{contact: null, states: ['', 'DELETE', false, false]}, true]]) {
      const f = deletion(opts), button = nodes(f.tree).find(n => n.type === 'button' && n.props.type === 'submit'); assert.equal(button.props.disabled, !enabled);
    }
    assert.equal(nodes(deletion({recent: false}).tree).some(n => n.props?.type === 'submit'), false);
  });
  await check('DELETE-SUBMIT-RECHECKS-RECENCY-AND-PENDING', () => {
    for (const [allowed, pending, recent, expected] of [[true, false, true, 'mutate'], [true, false, false, 'stale'], [true, true, true, 'none'], [false, false, true, 'none']]) {
      const calls = [], submit = callback('account', 'Dt', s => s.includes('e.preventDefault(),D'), {D: allowed, P: {isPending: pending, mutate: () => calls.push('mutate')}, a: 'owned-token', kt: () => recent, ae: x => calls.push(x ? 'stale' : 'other')});
      submit({preventDefault() {}}); assert.equal(calls[0] ?? 'none', expected);
    }
  });
  await check('DELETE-MUTATION-ORDER-AND-CLOSE-ABORT', async () => {
    const f = deletion(); await f.env.mutation.mutationFn(); assert.deepEqual(f.calls.map(c => c[0]), ['event', 'post', 'deleted']);
    assert.deepEqual(f.calls[1], ['post', '/accounts/deactivate', {additionalHeaders: {owned: 'risk'}}]);
    const controller = new AbortController(); f.refs[1].current = controller;
    nodes(f.tree).find(n => n.type === 'button' && n.props.type === 'button').props.onClick(); assert.equal(controller.signal.aborted, true); assert.equal(f.refs[0].current, false);
  });
  await check('DELETE-STALE-ERROR-CLEARS-FIELDS-AND-REFRESHES', async () => {
    const calls = [], error = callback('account', 'Dt', s => s.includes('e instanceof n') && s.includes('m.current'), {m: {current: true}, n: OwnedApiError, p: class Diagnostic {}, ae: v => calls.push(['stale', v]), _: v => calls.push(['contact', v]), y: v => calls.push(['keyword', v]), A: async () => calls.push(['refresh']), d: {get: () => ({warning: v => calls.push(['warning', v])})}, le: 'toast', At: () => 'generic', f: formatter});
    await error(new OwnedApiError(401, 'reauth_required')); assert.deepEqual(calls, [['stale', true], ['contact', ''], ['keyword', ''], ['refresh']]);
  });
  await check('EXTENSION-IDENTITY-SKIP-AND-PERSONAL-WORKSPACE-QUERIES', async () => {
    assert.equal(extension({selectedAccount: 'other'}).queries[0].queryFn, 'owned-skip');
    assert.equal(extension({identity: {authMethod: 'pat'}}).queries[0].queryFn, 'owned-skip');
    const personal = extension(); await personal.queries[0].queryFn({signal: 'owned-signal'}); const config = await personal.queries[1].queryFn({signal: 'owned-signal'});
    assert.deepEqual(plain(config), {supportsIndependentSpeedModes: null, requirements: null}); assert.equal(personal.calls.length, 1);
    assert.deepEqual(personal.calls[0][2].expectedIdentity, {accountId: 'owned-A', userId: 'owned-U'});
    const workspace = extension({structure: 'workspace'}); await workspace.queries[1].queryFn({signal: 'owned-signal'}); assert.equal(workspace.calls[0][1], '/wham/config/bundle');
    assert.equal(workspace.queries[1].refetchOnWindowFocus, 'always'); assert.equal(workspace.queries[1].retry, false);
  });
  await check('EXTENSION-WRITE-REVISION-IDENTITY-CACHE-EVENT-ORDER', async () => {
    const f = extension(), requestBody = {expected_revision: 7, preferences: {webmcp_enabled: false}}, identity = {accountId: 'owned-A', userId: 'owned-U'};
    await f.configs[0].mutationFn({requestBody, identity});
    assert.deepEqual(f.calls.map(c => c[0]), ['cancel', 'patch', 'cancel', 'set', 'event']);
    assert.deepEqual(f.calls[1], ['patch', '/wham/browser/settings', {requestBody, expectedIdentity: identity, retry: false, expectedErrorStatuses: [400, 409, 422]}]);
    assert.deepEqual(f.calls[0][1].queryKey, ['browser-settings', 'owned-U', 'owned-A']); assert.equal(f.configs[0].retry, false);
  });
  await check('EXTENSION-FAILED-WRITE-INVALIDATES-AND-RETHROWS', async () => {
    const error = new OwnedApiError(409, 'conflict'), f = extension({patchFailure: error});
    await assert.rejects(() => f.configs[0].mutationFn({requestBody: {expected_revision: 7}, identity: {userId: 'owned-U', accountId: 'owned-A'}}), e => e === error);
    assert.deepEqual(f.calls.map(c => c[0]), ['cancel', 'patch', 'invalidate']);
    assert.equal(nodes(extension({error}).tree).filter(n => n.props?.id === 'settings.chromeExtension.conflict').length, 1);
  });
  await check('EXTENSION-ERROR-RETRY-INVALIDATES-ACCOUNT-AND-BOTH-KEYS', () => {
    const f = extension({accountStatus: 'unavailable'}), error = nodes(f.tree).find(n => n.type === 'error'); error.props.onPrimaryCtaClick();
    assert.deepEqual(f.calls.map(c => c[1].queryKey), [['accounts'], ['browser-settings', 'owned-U', 'owned-A'], ['browser-cloud-requirements', 'owned-U', 'owned-A']]);
    assert.equal(nodes(f.tree).some(n => n.type === 'site-editor'), false);
  });
  await check('EXTENSION-HISTORY-AND-CDP-POLICY-PROJECTION', () => {
    for (const [opts, history, managed, cdp] of [[{}, 'never_ask', false, true], [{neverAskAllowed: false}, 'always_ask', false, true], [{historyAllowed: false}, 'disabled', true, true], [{extensionAllowed: false}, 'disabled', true, false], [{requirements: {featureRequirements: {browser_use_full_cdp_access: false}}}, 'never_ask', false, false]]) {
      const f = extension(opts), rows = nodes(f.tree).filter(n => n.type === 'row'), controls = rows.map(n => n.props.control({}));
      assert.equal(controls[0].props.value, history); assert.equal(controls[0].props.managed, managed);
      const toggle = nodes(controls[2]).find(n => n.type === 'switch'); assert.equal(toggle.props.checked, cdp); assert.equal(toggle.props.disabled, !cdp);
      if (opts.neverAskAllowed === false) assert.equal(controls[0].props.options[0].disabled, true);
    }
  });
  await check('EXTENSION-CONTROLS-ENCODE-REVISION-AND-BOOLEAN', async () => {
    const f = extension(), rows = nodes(f.tree).filter(n => n.type === 'row'), controls = rows.map(n => n.props.control({}));
    controls[0].props.onChange('disabled'); controls[1].props.onChange(false); nodes(controls[2]).find(n => n.type === 'switch').props.onChange(false);
    assert.deepEqual(f.calls.map(c => c[1].requestBody), [{expected_revision: 7, preferences: {history_approval_mode: 'disabled'}}, {expected_revision: 7, preferences: {webmcp_enabled: false}}, {expected_revision: 7, preferences: {full_cdp_access_enabled: false}}]);
    for (const node of nodes(extension({pending: true}).tree).filter(n => n.type === 'row')) {
      assert(nodes(node.props.control({})).filter(n => ['switch', 'dropdown'].includes(n.type)).every(n => n.props.disabled));
    }
  });
  await check('EXTENSION-SITE-MANAGER-PROJECTION-CAPABILITIES', () => {
    const f = siteEditor({rules: {origin: {'owned-a': 'allow', 'owned-b': 'deny'}, full_cdp: {'owned-c': 'allow'}}, disabled: true});
    assert.deepEqual(plain(f.tree.props.originsConfig.allowedOrigins), ['owned-a']); assert.deepEqual(plain(f.tree.props.originsConfig.allowedFullCdpOrigins), ['owned-c']);
    assert.equal(f.tree.props.backend, 'chrome'); assert.equal(f.tree.props.isFullCdpAccessEnabled, false); assert.equal(f.tree.props.supportsRequiresApproval, false);
    assert.equal(f.tree.props.disabled, true); assert.equal(f.tree.props.originsConfig.webMcpEnabled, true); assert.equal(f.tree.props.originsConfig.fullCdpAccessEnabled, false);
  });
  await check('EXTENSION-DEFAULT-APPROVAL-RESOURCE-MAPPING', async () => {
    const f = siteEditor(); for (const resource of ['origin', 'download', 'upload']) await f.tree.props.onApprovalModeChange(resource, 'neverAsk');
    assert.deepEqual(f.calls, ['approval_mode', 'download_approval_mode', 'upload_approval_mode'].map(key => ({expected_revision: 7, preferences: {[key]: 'never_ask'}})));
  });
  await check('EXTENSION-SITE-RULE-WEBMCP-MAPPING-REMOVE-AND-ASK-REJECTION', async () => {
    const f = siteEditor({rules: {origin: {'owned-a': 'allow'}}});
    await f.tree.props.onSitePermissionsChange({operation: 'add', origin: 'owned-pattern', resources: ['webMcp', 'download', 'fullCdp'], nextValues: {webMcp: 'allowed', download: 'denied', fullCdp: 'allowed'}});
    assert.deepEqual(f.calls[0], {expected_revision: 7, rule_updates: [{resource: 'webmcp', pattern: 'owned-pattern', decision: 'allow'}, {resource: 'download', pattern: 'owned-pattern', decision: 'deny'}]});
    await f.tree.props.onSitePermissionsChange({operation: 'remove', origin: 'owned-a', resources: ['origin'], nextValues: {}}); assert.equal(f.calls[1].rule_updates[0].decision, null);
    await assert.rejects(() => f.tree.props.onSitePermissionsChange({operation: 'add', origin: 'owned-a', resources: ['origin'], nextValues: {origin: 'ask'}}), /not supported/);
    assert.equal(f.calls.length, 2);
  });
  await check('EXTENSION-ABSENT-DEFAULT-AND-FULL-CDP-ONLY-ARE-NOOP', async () => {
    const f = siteEditor(); await f.tree.props.onSitePermissionsChange({operation: 'remove', origin: 'absent', resources: ['origin', 'fullCdp'], nextValues: {}}); assert.equal(f.calls.length, 0);
  });
  await check('EXTENSION-PATTERN-UNICODE-LENGTH-CONTROLS-NO-URL-NORMALIZATION', () => {
    const parse = unit('extension', 'De');
    for (const input of ['', 'has space', 'line\n', 'zero\u200bwidth', 'x'.repeat(4097), '😀'.repeat(4097)]) assert.equal(parse(input), null);
    for (const input of ['x'.repeat(4096), '😀'.repeat(4096), '*.owned.invalid', 'unparsed:owned-pattern']) assert.equal(parse(input), input);
  });
  const result = {baselineId: base, method: 'exact-frozen-functions-callbacks-and-roots-in-owned-node-vm', sourceSelections: used,
    cases, passed: cases.filter(c => c.passed).length, failed: cases.filter(c => !c.passed).length,
    productScenariosExecuted: 0, modelSubmissionsAdded: 0, originalClientRunsAdded: 0, realServiceCalls: 0,
    actualLegalAcceptances: 0, actualAccountDeletions: 0, actualBrowserPolicyWrites: 0,
    qualification: 'Synthetic UI/hooks/query/cache/auth/schema/service/policy providers only. Root rendering does not mount React; policy and schema providers are fixtures. No target imports, real browser, account, SDK, credential, service or model execution.'};
  const target = process.argv[2] ?? path.join(work, 'isolated-observations.json');
  fs.writeFileSync(target, JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
  console.log(JSON.stringify({passed: result.passed, failed: result.failed, failures: cases.filter(c => !c.passed).map(c => ({id: c.id, error: c.error}))}));
  process.exitCode = result.failed ? 1 : 0;
})().catch(error => {console.error(error); process.exitCode = 1;});
