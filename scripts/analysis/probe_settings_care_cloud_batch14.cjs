// Execute selected frozen functions only, with owned in-memory identities and adapters.
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const assert = require('node:assert/strict'), crypto = require('node:crypto');
const root = path.resolve(__dirname, '../..'), base = 'codex-26.1007.30912-c5b273322a83';
const work = path.join(root, '.analysis-local/settings-care-cloud-batch14-work');
const frozen = path.join(root, '.analysis-local/baselines', base, 'extracted');
const folders = ['trusted-contact', 'safety', 'cloud-settings', 'trusted-client', 'cloud-provider', 'study-legacy'];
const metadata = Object.fromEntries(folders.map(p => [p, JSON.parse(fs.readFileSync(path.join(work, p, 'source-contracts.json')))]));
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const buffers = new Map(), used = [], cases = [], plain = v => JSON.parse(JSON.stringify(v));
function exact(page, record) {
  if (!buffers.has(record.sourcePath)) {const b = fs.readFileSync(path.join(frozen, record.sourcePath.replace(/^app.asar\//, ''))); assert.equal(sha(b), record.sourceHash); buffers.set(record.sourcePath, b);}
  const b = buffers.get(record.sourcePath).subarray(record.byteRange.start, record.byteRange.endExclusive);
  assert.equal(sha(b), record.spanHash); used.push({page, ...record}); return b.toString();
}
function unit(page, name, env = {}) {const r = metadata[page].units.filter(u => u.name === name); assert.equal(r.length, 1, page + ':' + name); return vm.runInNewContext('(' + exact(page, r[0]) + ')', env, {timeout: 1000});}
function callback(page, name, match, env = {}) {const r = metadata[page].callbacks.filter(c => c.unit === name).filter(c => match(exact(page, c))); assert.equal(r.length, 1, page + ':' + name); return vm.runInNewContext('(' + exact(page, r[0]) + ')', env, {timeout: 1000});}
async function check(id, run) {try {await run(); cases.push({id, passed: true});} catch (e) {cases.push({id, passed: false, error: String(e.stack)});}}
const memo = {c: n => Array(n).fill(Symbol.for('react.memo_cache_sentinel'))};
const jsx = {jsx: (type, props) => ({type, props}), jsxs: (type, props) => ({type, props}), Fragment: 'fragment'};
const messages = new Proxy({}, {get: (_, key) => ({id: String(key)})});
const enums = new Proxy({}, {get: (_, key) => String(key)});
const formatter = {formatMessage: m => m.id, formatDate: () => 'owned-day'};
function nodes(v) {if (!v || typeof v !== 'object') return []; if (Array.isArray(v)) return v.flatMap(nodes); return [v, ...Object.values(v.props ?? {}).flatMap(nodes)];}
class OwnedApiError extends Error {constructor(status, code) {super('owned failure'); this.status = status; this.errorCode = code;}}
const weeks = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];
const legacy = unit('study-legacy', 'i', {n: weeks}), study = unit('safety', 'je', {Ce: legacy});
const replace = unit('cloud-provider', 'E'), validate = unit('cloud-provider', 'w', {E: replace}), preview = unit('cloud-provider', 'T', {E: replace});
const tags = [{value: '{feature}', char_count: 8, example: 'owned-feature'}, {value: '{user}', char_count: 4, example: 'owned-user'}];
function form(options = {}) {
  const calls = [], ref = {current: false}; let resolve;
  const promise = new Promise(r => {resolve = r;});
  const run = callback('trusted-contact', 'Ke', s => s.includes('et.test(g.trim())'), {et: unit('trusted-contact', 'assignment-et'), f: options.name ?? ' Owned Contact ', g: options.email ?? ' contact@owned.invalid ', m: options.phone ?? ' ', v: options.consent ?? true, o: !!options.pending, S: ref, x: value => calls.push(['invalid', value]), a: value => {calls.push(['submit', plain(value)]); return promise;}});
  return {run: () => run({preventDefault: () => {}}), calls, ref, resolve};
}
function invitationSuccess(current) {
  const calls = [], env = {E: {list: {queryKey: ['trusted-contact', 'owned-U', 'owned-A', 'list']}}, N: {data: {contacts: [{trusted_contact_id: 'same', name: 'old'}, {trusted_contact_id: 'other'}]}},
    v: {setQueryData: (...a) => calls.push(['cache', ...plain(a)]), invalidateQueries: async a => calls.push(['invalidate', plain(a)])}, ce: {current: current ? 2 : 3}, B: a => calls.push(['contact', plain(a)]), F: value => calls.push(['dialog', value]), W: value => calls.push(['step', value]), q: enums, d: () => calls.push(['invited'])};
  return {run: callback('trusted-contact', 'it', s => s.startsWith('async(e,t)=>') && s.includes('setQueryData'), env), calls};
}
function schedule(options = {}) {
  const calls = []; let identity = {status: options.denied ? 'denied' : 'allowed', accountId: 'owned-A', userId: 'owned-U'}, watcher;
  const state = {eligibleNowOrBefore: !options.ineligible, quietHours: {status: options.unsupportedState ? 'unsupported' : 'loaded', managedByParent: !!options.managed}, studyHoursSchedule: {enabled: false, blocks: []}, hasRecurringStudyHours: false};
  const ref = {current: options.concurrent ? new AbortController() : null}, draft = {enabled: true, blocks: [{id: 'owned-B', days: ['mon'], start_time: '22:00', end_time: '07:00'}]};
  const snapshot = {invalidate: async a => calls.push(['invalidate', plain(a)]), cancel: async () => calls.push(['cancel'])};
  const provider = {get: key => key === 'identity' ? identity : {isError: !!options.refetchError}, query: {getData: () => state, snapshot: () => snapshot}, watch: fn => {watcher = fn; return () => calls.push(['unwatch']);}};
  const env = {k: value => calls.push(['attempt', value]), j: ref, z: options.dirty ?? true, B: options.validation ?? null, F: !!options.unsupported, d: provider, _e: 'identity', ne: 'state', r: options.kind ?? 'quiet', _: draft, je: study,
    D: value => calls.push(['error', value]), T: value => calls.push(['retain', value]), w: value => calls.push(['pending', value]), s: () => calls.push(['close']), AbortController, Fe: unit('safety', 'Fe'), Ie: unit('safety', 'Ie', {r: OwnedApiError}),
    n: {safePatch: async (...args) => {calls.push(['patch', ...plain(args)]); if (options.switchIdentity) {identity = {...identity, userId: 'other'}; watcher(provider);} if (options.abort) ref.current.abort(); if (options.failure) throw options.failure;}}};
  return {run: callback('safety', 'Pe', s => s.startsWith('async()=>') && s.includes('safePatch'), env), calls, ref, draft};
}
function cloud(options = {}) {
  const calls = [], pref = {branch_format: options.baseline ?? 'codex/{feature}', git_diff_mode: 'unified'}, config = {branch_format_max_length: 100, branch_format_special_values: tags};
  const mutation = {isPending: !!options.pending, mutate: (...a) => calls.push(['mutate', ...a])};
  const env = {L: memo, z: jsx, r: () => ({get: () => ({success: value => calls.push(['success', value]), danger: (...a) => calls.push(['danger', ...plain(a)])})}), i: 'scope', p: () => formatter,
    A: () => ({data: options.loading ? null : pref, isError: !!options.error, isFetching: false, refetch: () => calls.push(['retry-pref'])}), j: () => ({data: config, isError: false, isFetching: false, refetch: () => calls.push(['retry-config'])}), te: () => mutation,
    R: {useState: () => [options.draft ?? null, value => calls.push(['draft', plain(value)])]}, M: validate, ne: preview, ae: unit('cloud-settings', 'ae', {z: jsx, h: 'message'}), ie: unit('cloud-settings', 'ie'), k: {Content: 'content'}, ee: 'rows', d: 'row', b: 'diff-selector', h: 'message', D: 'input', n: 'save', c: 'toast', re: 'retry', O: 'loading'};
  return {tree: unit('cloud-settings', 'I', env)(), calls};
}

(async () => {
  await check('CONTACT-ACCESS-IDENTITY-AND-ERROR-RETRY', () => {
    for (const status of ['allowed', 'denied', 'loading', 'error']) {
      const calls = [], env = {ft: memo, Q: jsx, f: () => ({queryClient: {invalidateQueries: a => calls.push(plain(a))}}), p: 'scope', o: () => ({status, userId: 'owned-U', accountId: 'owned-A'}), xe: 'access', fe: 'title', V: 'message', $: messages, ge: 'page', s: 'button', it: 'contact-body'};
      const tree = unit('trusted-contact', 'nt', env)();
      if (status === 'allowed') {assert.equal(tree.type, 'contact-body'); assert.equal(tree.props.accountId, 'owned-A');}
      else if (status === 'error') {nodes(tree).find(n => n.type === 'button').props.onClick(); assert.deepEqual(calls, [{queryKey: ['accounts', 'check']}]);}
      else assert.equal(tree, null);
    }
  });
  await check('CONTACT-COUNTRY-AND-EXPECTED-DESTINATION-ERRORS', () => {
    const normalized = unit('trusted-contact', 'lt', {ut: unit('trusted-contact', 'ut', {ht: new Set(['US', 'KR', 'DE'])})});
    assert.equal(normalized(' kr '), 'KR'); assert.equal(normalized('unknown'), 'US'); assert.equal(normalized(null), 'US');
    const expected = unit('trusted-contact', 'st'); assert(expected({status: 400, errorCode: 'trusted-contacts-blocked-email'})); assert(expected({status: 400, errorCode: 'trusted-contacts-blocked-phone-number'})); assert.equal(expected({status: 500, errorCode: 'trusted-contacts-blocked-email'}), false);
  });
  await check('CONTACT-QUERIES-KEYS-HEADERS-SIGNALS-AND-NO-RETRY', async () => {
    const calls = [], headers = unit('trusted-client', 'a', {r: 'X-Owned-Account'});
    const queries = unit('trusted-client', 's', {a: headers, t: {safeGet: async (...a) => {calls.push(plain(a)); return {enabled: true, contacts: []};}}})('owned-U', 'owned-A');
    assert.deepEqual(plain(queries.list.queryKey), ['trusted-contact', 'owned-U', 'owned-A', 'list']); assert.equal(queries.list.retry, false); assert.equal(queries.enabled.staleTime, 30000);
    assert.equal(await queries.enabled.queryFn({signal: 'owned-signal'}), true); await queries.list.queryFn({signal: 'owned-signal'});
    assert.equal(calls[0][0], '/trusted_contact/enabled'); assert.equal(calls[1][1].signal, 'owned-signal'); assert.deepEqual(calls[1][1].additionalHeaders, {'ChatGPT-Account-ID': 'owned-A', 'X-Owned-Account': 'owned-A'});
  });
  await check('CONTACT-CONSENT-EMAIL-AND-PENDING-SUBMIT-GUARDS', () => {
    for (const options of [{name: ' '}, {email: 'invalid'}, {consent: false}, {pending: true}]) {const f = form(options); f.run(); assert.equal(f.calls.some(c => c[0] === 'submit'), false);}
  });
  await check('CONTACT-FORM-TRIM-OPTIONAL-PHONE-AND-SINGLE-INFLIGHT', async () => {
    const f = form(); f.run(); f.run(); assert.equal(f.calls.filter(c => c[0] === 'submit').length, 1); assert.deepEqual(f.calls.find(c => c[0] === 'submit')[1], {name: 'Owned Contact', email: 'contact@owned.invalid', phone_number: null, relationship: null});
    assert(f.ref.current); f.resolve(); await Promise.resolve(); assert.equal(f.ref.current, false);
  });
  await check('CONTACT-POST-CAPTURED-ACCOUNT-AND-EXPECTED-ERROR-PREDICATE', async () => {
    const calls = [], headers = {'ChatGPT-Account-ID': 'owned-A'}, st = unit('trusted-contact', 'st');
    await callback('trusted-contact', 'it', s => s.includes('safePost(`/trusted_contact`'), {t: {safePost: async (...a) => calls.push(a)}, H: headers, st})({payload: {name: 'Owned'}});
    assert.equal(calls[0][1].additionalHeaders, headers); assert.deepEqual(plain(calls[0][1].requestBody), {name: 'Owned'}); assert.equal(calls[0][1].isExpectedError, st);
  });
  await check('CONTACT-CURRENT-EPOCH-UPDATES-DIALOG-AND-DEDUPLICATES-CACHE', async () => {
    const f = invitationSuccess(true); await f.run({trusted_contact_id: 'same', name: 'Server name'}, {payload: {name: 'Draft', email: 'owned@invalid'}, epoch: 2});
    assert.deepEqual(f.calls[0][2].contacts.map(c => c.trusted_contact_id), ['same', 'other']); assert.equal(f.calls.find(c => c[0] === 'dialog')[1], 'success'); assert(f.calls.some(c => c[0] === 'invited')); assert.equal(f.calls.at(-1)[0], 'invalidate');
  });
  await check('CONTACT-STALE-EPOCH-RECONCILES-CACHE-WITHOUT-NEW-DIALOG', async () => {
    const f = invitationSuccess(false); await f.run({trusted_contact_id: 'same'}, {payload: {name: 'Draft'}, epoch: 2}); assert.deepEqual(f.calls.map(c => c[0]), ['cache', 'invalidate']);
  });
  await check('CONTACT-BLOCKED-DESTINATION-AND-STALE-ERROR-DISPOSITION', () => {
    for (const current of [true, false]) {
      const calls = [], env = {ce: {current: current ? 1 : 2}, n: OwnedApiError, B: value => calls.push(['payload', plain(value)]), F: value => calls.push(['dialog', value]), W: () => {}, q: enums, g: {get: () => ({danger: () => calls.push(['danger'])})}, S: 'toast', _: formatter, $: messages};
      callback('trusted-contact', 'it', s => s.includes('i===ce.current') && s.includes('instanceof n'), env)(new OwnedApiError(400, 'trusted-contacts-blocked-email'), {payload: {name: 'Owned'}, epoch: 1}); assert.equal(calls.some(c => c[1] === 'unavailable'), current); assert.equal(calls.some(c => c[0] === 'danger'), false);
    }
  });
  await check('CONTACT-RESEND-EMAIL-NORMALIZATION-AND-SELECTED-ID', async () => {
    const calls = [], payload = unit('trusted-client', 'o'), run = callback('trusted-contact', 'it', s => s.includes('safePut'), {Le: payload, _: formatter, $: messages, H: {'ChatGPT-Account-ID': 'owned-A'}, t: {safePut: async (...a) => calls.push(plain(a))}});
    assert.equal(payload({name: 'Owned'}, 'fallback'), null); assert.throws(() => run({trusted_contact_id: 'missing'}), /email/);
    await run({trusted_contact_id: 'owned-C', name: ' ', email: ' owned@invalid ', phone_number: '+123', relationship: 'owned'}); assert.equal(calls[0][1].parameters.path.trusted_contact_id, 'owned-C'); assert.deepEqual(calls[0][1].requestBody, {name: 'fallback', email: 'owned@invalid', phone_number: '+123', relationship: 'owned'});
  });
  await check('CONTACT-REMOVAL-CONFIRMATION-AND-SELECTED-DELETE', async () => {
    for (const pending of [true, false]) {let count = 0; callback('trusted-contact', 'Xe', s => s.includes('e.preventDefault(),a||c()'), {a: pending, c: () => count++})({preventDefault: () => {}}); assert.equal(count, pending ? 0 : 1);}
    const calls = []; await callback('trusted-contact', 'it', s => s.includes('safeDelete'), {H: {'ChatGPT-Account-ID': 'owned-A'}, t: {safeDelete: async (...a) => calls.push(plain(a))}})({trusted_contact_id: 'owned-C'}); assert.equal(calls[0][1].parameters.path.trusted_contact_id, 'owned-C');
  });
  await check('CONTACT-PERSONAL-NOTE-COMPOSITION-BRIDGE-AND-FALLBACK', () => {
    for (const handled of [true, false]) {
      const calls = [], env = {J: memo, X: jsx, ie: () => ({formatMessage: m => m.id + ' & owned text'}), Z: messages, r: 'header', U: 'title', V: 'message', ne: 'description', s: 'button', F: 'footer', te: 'content', ee: 'dialog', Ye: () => {}, pe: arg => {calls.push(['bridge', arg.href]); return handled;}, window: {location: {assign: value => calls.push(['assign', value])}}};
      const render = unit('trusted-contact', 'Je', env), tree = render({kind: 'success', open: true, contact: {name: 'Owned', email: 'owned+contact@invalid'}, onClose: () => {}});
      nodes(tree).find(n => n.props?.['data-testid'] === 'trusted-contact-invite-success-personal-note').props.onClick({}); assert(calls[0][1].startsWith('mailto:owned%2Bcontact%40invalid?subject=')); assert(calls[0][1].includes('%26')); assert.equal(calls.length, handled ? 1 : 2);
      assert.equal(nodes(render({kind: 'unavailable', contact: {email: 'owned@invalid'}})).some(n => n.props?.['data-testid'] === 'trusted-contact-invite-success-personal-note'), false);
    }
  });
  await check('SAFETY-ACCESS-STATUS-RENDERING', () => {
    for (const status of ['allowed', 'denied', 'loading', 'error']) {const env = {He: memo, $: jsx, u: () => ({queryClient: {invalidateQueries: () => {}}}), p: 'scope', o: () => ({status, accountId: 'owned-A', userId: 'owned-U'}), _e: 'access', Ve: 'denied', Be: 'loading-error', ze: 'body'}; const tree = unit('safety', 'Re', env)(); assert.equal(tree.type, status === 'allowed' ? 'body' : status === 'denied' ? 'denied' : 'loading-error'); if (status === 'error') assert.equal(tree.props.isError, true);}
  });
  await check('SAFETY-STUDY-UNSUPPORTED-PARENT-LOCK-AND-LEGACY-PROJECTION', () => {
    assert.equal(study(null, true, true, {}).status, 'unsupported'); const projected = study(null, false, true, {default_to_study_mode: true}); assert.equal(projected.managedByParent, true); assert.equal(projected.schedule.blocks[0].start_time, '00:00'); assert.equal(projected.schedule.blocks[0].end_time, '23:59'); assert.deepEqual(plain(projected.schedule.blocks[0].days), weeks);
  });
  await check('SAFETY-LEGACY-UPDATE-PRESERVES-EXISTING-BLOCKS', () => {
    const calls = [], adapter = unit('study-legacy', 'a', {i: legacy, t: (schedule, action) => {calls.push(action.type); return {...schedule, blocks: [{...schedule.blocks[0], ...action.update}]};}, crypto: {randomUUID: () => 'owned-uuid'}}), existing = {enabled: false, blocks: [{id: 'existing'}]};
    const next = adapter(existing, {type: 'update_block', update: {start_time: '10:00'}}); assert.equal(next.blocks[0].id, 'web-study-hours-owned-uuid'); assert.equal(next.blocks[0].start_time, '10:00'); assert.equal(next.blocks[1].id, 'existing'); assert.equal(next.enabled, true); assert.equal(adapter(existing, {type: 'remove_block'}), existing);
  });
  await check('SAFETY-SAVE-RECHECKS-ELIGIBILITY-LOCKS-AND-INFLIGHT', async () => {
    for (const options of [{dirty: false}, {validation: 'invalid'}, {unsupported: true}, {concurrent: true}, {denied: true}, {ineligible: true}, {managed: true}, {unsupportedState: true}]) {const f = schedule(options); await f.run(); assert.equal(f.calls.some(c => c[0] === 'patch'), false);}
  });
  await check('SAFETY-QUIET-AND-STUDY-WRITES-CAPTURED-ACCOUNT-AND-READBACK', async () => {
    for (const kind of ['quiet', 'study']) {const f = schedule({kind}); await f.run(); const call = f.calls.find(c => c[0] === 'patch'); assert.equal(call[2].additionalHeaders['ChatGPT-Account-ID'], 'owned-A'); assert.equal(call[2].parameters.query.feature, kind === 'quiet' ? 'quiet_hours_schedule' : 'study_hours_schedule'); assert.deepEqual(JSON.parse(call[2].parameters.query.value), f.draft); assert.deepEqual(f.calls.filter(c => ['invalidate', 'cancel', 'close'].includes(c[0])).map(c => c[0]), ['invalidate', 'cancel', 'invalidate', 'close']); assert.equal(f.calls.at(-1)[0], 'unwatch');}
  });
  await check('SAFETY-SWITCH-OR-ABORT-CANNOT-CLOSE-THE-EDITOR', async () => {
    for (const options of [{switchIdentity: true}, {abort: true}]) {const f = schedule(options); await f.run(); assert.equal(f.calls.some(c => c[0] === 'close'), false); assert.equal(f.ref.current, null); assert(f.calls.some(c => c[0] === 'unwatch'));}
  });
  await check('SAFETY-LOCKED-DENIED-SAVE-AND-REFETCH-ERRORS-PRESERVE-DRAFT', async () => {
    for (const [failure, expected] of [[new OwnedApiError(403, 'feature-locked-by-owner'), 'locked'], [new OwnedApiError(403, 'other'), 'denied'], [new Error('owned failure'), 'save']]) {const f = schedule({failure}); await f.run(); assert(f.calls.some(c => c[0] === 'error' && c[1] === expected)); assert(f.calls.some(c => c[0] === 'retain' && c[1] === true)); assert.equal(f.calls.some(c => c[0] === 'close'), false);}
    const refetch = schedule({refetchError: true}); await refetch.run(); assert(refetch.calls.some(c => c[0] === 'error' && c[1] === 'save'));
  });
  await check('SAFETY-UNMOUNT-ABORTS-AND-BACK-ASKS-ABOUT-UNSAVED-EDITS', () => {
    const controller = new AbortController(); callback('safety', 'Pe', s => s.includes('()=>()=>{j.current?.abort()}'), {j: {current: controller}})()(); assert(controller.signal.aborted);
    for (const dirty of [true, false]) {const calls = []; callback('safety', 'Pe', s => s.includes('z?te(!0):s()'), {z: dirty, te: value => calls.push(['confirm', value]), s: () => calls.push(['close'])})(); assert.equal(calls[0][0], dirty ? 'confirm' : 'close');}
  });
  await check('SAFETY-WEEKDAY-DONE-ONLY-APPLIES-CHANGED-SELECTION', () => {
    for (const [draft, expected] of [[['mon'], 0], [['mon', 'tue'], 1]]) {const calls = []; callback('safety', 'Ee', s => s.startsWith('()=>{(l.length!==n.length'), {l: draft, n: ['mon'], i: value => calls.push(plain(value))})(); assert.equal(calls.length, expected);}
  });
  await check('SAFETY-BLOCK-UI-RESPECTS-CAPACITY-AND-REDUCER-BOUNDARY', () => {
    for (const count of [11, 12]) {const env = {U: memo, G: jsx, A: () => formatter, d: (schedule, action) => schedule, t: 'switch', R: 'message', N: 'rows', O: 'row', he: 'input', Ee: 'weekdays', c: 'button', ve: {Content: 'content'}}; const tree = unit('safety', 'Te', env)({schedule: {enabled: true, blocks: Array.from({length: count}, (_, i) => ({id: String(i), days: ['mon'], start_time: '22:00', end_time: '07:00'}))}, description: 'owned', disabled: false, createBlock: () => ({}), onChange: () => {}}); const add = nodes(tree).find(n => n.type === 'button' && n.props.children?.props?.id === 'settings.recurringSchedule.add'); assert.equal(add.props.disabled, count === 12);}
  });
  await check('CLOUD-QUERIES-IDENTITY-KEYS-NO-RETRY-AND-SIGNAL-DIFFERENCE', async () => {
    const calls = [], api = {safeGet: async (...a) => {calls.push(plain(a)); return {};}};
    const env = {D: memo, u: () => ({userId: 'owned-U', accountId: 'owned-A'}), _: unit('cloud-provider', '_'), g: unit('cloud-provider', 'g'), d: cfg => cfg, h: {FIVE_MINUTES: 300000}, y: unit('cloud-provider', 'y', {a: api}), x: unit('cloud-provider', 'x', {a: api})};
    const preferences = unit('cloud-provider', 'v', env)(), config = unit('cloud-provider', 'b', env)(); assert.deepEqual(plain(preferences.queryKey), ['cloud-user-preferences', 'owned-U']); assert.deepEqual(plain(config.queryKey), ['cloud-preferences-config', 'owned-A', 'owned-U']); assert.equal(preferences.retry, false); assert.equal(config.staleTime, 300000); await preferences.queryFn({signal: 'owned-signal'}); await config.queryFn({signal: 'unused'}); assert.equal(calls[0][1].signal, 'owned-signal'); assert.equal(calls[1].length, 1);
    env.u = () => ({userId: null, accountId: null}); assert.equal(unit('cloud-provider', 'v', env)().enabled, false); assert.equal(unit('cloud-provider', 'b', env)().enabled, false);
  });
  await check('CLOUD-WRITER-USES-CAPTURED-CACHE-CONTEXT-AND-SERVER-RESPONSE', async () => {
    const calls = [], env = {D: memo, u: () => ({userId: 'owned-U'}), _: unit('cloud-provider', '_'), o: () => ({setQueryData: (...a) => calls.push(['cache', ...plain(a)])}), n: key => calls.push(['instructions', plain(key)]), p: cfg => cfg, C: unit('cloud-provider', 'C', {a: {safePatch: async (...a) => {calls.push(['patch', ...plain(a)]); return {git_diff_mode: 'split'};}}})};
    const cfg = unit('cloud-provider', 'S', env)(), context = cfg.onMutate(); const server = await cfg.mutationFn({git_diff_mode: 'split'}); cfg.onSuccess(server, {git_diff_mode: 'split'}, context); assert.deepEqual(calls[1], ['cache', ['cloud-user-preferences', 'owned-U'], {git_diff_mode: 'split'}]); cfg.onSuccess(server, {custom_instructions: ''}, context); assert.equal(calls.at(-1)[0], 'instructions'); const count = calls.length; cfg.onSuccess(server, {}, undefined); assert.equal(calls.length, count);
  });
  await check('CLOUD-BRANCH-VALIDATION-ERRORS-AND-PREVIEW', () => {
    for (const [value, max, expected] of [['codex/{feature', 100, 'bracket-mismatch'], ['codex/plain', 100, 'missing-pattern'], ['codex/{missing}', 100, 'invalid-pattern'], ['codex/{feature}', 5, 'too-long'], ['/{feature}', 100, 'leading-slash'], ['codex/{feature} space', 100, 'invalid-characters'], ['codex/{feature}-{user}', 100, null]]) assert.equal(validate(value, max, tags), expected);
    assert.equal(preview('{feature}/{feature}/{user}', tags), 'owned-feature/owned-feature/owned-user'); assert.equal(validate('codex//{feature}.lock', 100, tags), null);
  });
  await check('CLOUD-DRAFT-BASELINE-VALIDITY-AND-PENDING-CONTROL-BOUNDARIES', () => {
    const current = cloud({draft: {baseline: 'codex/{feature}', value: 'owned/{feature}'}}); assert.equal(nodes(current.tree).find(n => n.type === 'input').props.value, 'owned/{feature}'); assert.equal(nodes(current.tree).find(n => n.type === 'save').props.disabled, false);
    const stale = cloud({baseline: 'server/{feature}', draft: {baseline: 'codex/{feature}', value: 'owned/{feature}'}}); assert.equal(nodes(stale.tree).find(n => n.type === 'input').props.value, 'server/{feature}');
    const invalid = cloud({draft: {baseline: 'codex/{feature}', value: 'no-placeholder'}}); assert.equal(nodes(invalid.tree).find(n => n.type === 'save').props.disabled, true);
    const pending = cloud({pending: true, draft: {baseline: 'codex/{feature}', value: 'owned/{feature}'}}); assert.equal(nodes(pending.tree).find(n => n.type === 'input').props.disabled, true); const save = nodes(pending.tree).find(n => n.type === 'save'); assert.equal(save.props.disabled, false); assert.equal(save.props.loading, true); assert(nodes(pending.tree).find(n => n.type === 'diff-selector').props.options.every(o => o.disabled));
  });
  await check('CLOUD-DIFF-BRANCH-SAVE-PAYLOADS-AND-ERROR-RETRY', () => {
    const f = cloud({draft: {baseline: 'codex/{feature}', value: 'owned/{feature}'}}); nodes(f.tree).find(n => n.type === 'diff-selector').props.onSelect('split'); nodes(f.tree).find(n => n.type === 'save').props.onClick(); assert.deepEqual(plain(f.calls.filter(c => c[0] === 'mutate').map(c => c[1])), [{git_diff_mode: 'split'}, {branch_format: 'owned/{feature}'}]);
    f.calls.find(c => c[0] === 'mutate')[2].onError(); assert(f.calls.some(c => c[0] === 'danger'));
    const error = cloud({error: true}); assert.equal(error.tree.type, 'retry'); error.tree.props.onRetry(); assert.deepEqual(error.calls.map(c => c[0]), ['retry-pref', 'retry-config']); assert.equal(cloud({loading: true}).tree.type, 'loading');
  });
  const result = {baselineId: base, method: 'exact-frozen-functions-callbacks-and-roots-in-owned-node-vm', sourceSelections: used, cases,
    passed: cases.filter(c => c.passed).length, failed: cases.filter(c => !c.passed).length,
    productScenariosExecuted: 0, modelSubmissionsAdded: 0, originalClientRunsAdded: 0, realServiceCalls: 0, actualInvitations: 0, actualEmailsSent: 0, actualAccountChanges: 0,
    qualification: 'Owned synthetic accounts/contacts/schedules/config and query/state/UI/service/URL substitutes. No React mount, target module imports or real service execution. Imported schedule reducers/validators, country allowlist, routing-header name and enforcement remain qualified provider fixtures.'};
  fs.writeFileSync(process.argv[2] ?? path.join(work, 'isolated-observations.json'), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
  console.log(JSON.stringify({passed: result.passed, failed: result.failed, failures: cases.filter(c => !c.passed).map(c => ({id: c.id, error: c.error}))})); process.exitCode = result.failed ? 1 : 0;
})().catch(e => {console.error(e); process.exitCode = 1;});
