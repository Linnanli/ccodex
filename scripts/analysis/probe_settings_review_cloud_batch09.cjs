// Exact frozen callbacks with owned synthetic receivers. No target imports/services.
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const assert = require('node:assert/strict'), crypto = require('node:crypto');
const root = process.cwd(), base = 'codex-26.1007.30912-c5b273322a83';
const work = path.join(root, '.analysis-local/settings-review-cloud-batch09-work');
const frozen = path.join(root, '.analysis-local/baselines', base, 'extracted');
const pages = ['code-review', 'codex-cloud', 'cloud-preferences', 'code-review-access'];
const metadata = Object.fromEntries(pages.map(page => [page,
  JSON.parse(fs.readFileSync(path.join(work, page, 'source-contracts.json')))]));
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const plain = value => JSON.parse(JSON.stringify(value));
const used = [], cases = [];
function exact(page, record) {
  const bytes = fs.readFileSync(path.join(frozen, record.sourcePath.replace(/^app.asar\//, '')));
  assert.equal(sha(bytes), record.sourceHash);
  const span = bytes.subarray(record.byteRange.start, record.byteRange.endExclusive);
  assert.equal(sha(span), record.spanHash); used.push({page, ...record}); return span.toString();
}
function unit(page, name, context = {}) {
  const record = metadata[page].units.find(value => value.name === name); assert(record, name);
  return vm.runInNewContext(`(${exact(page, record)})`, context, {timeout: 1000});
}
function callback(page, name, match, context = {}) {
  const records = metadata[page].callbacks.filter(value => value.unit === name)
    .filter(value => match(exact(page, value)));
  assert.equal(records.length, 1, `${page}:${name}`);
  return vm.runInNewContext(`(${exact(page, records[0])})`, context, {timeout: 1000});
}
async function check(id, run) {
  try { await run(); cases.push({id, passed: true}); }
  catch (error) { cases.push({id, passed: false, error: String(error.stack)}); }
}
class HttpError extends Error { constructor(status) { super(`HTTP ${status}`); this.status = status; } }

(async () => {
  const normalize = unit('code-review', 'It', {URL});
  await check('REVIEW-GITHUB-NORMALIZATION-AND-NON-VALIDATING-HOST', () => {
    assert.equal(normalize('https://github.com/Org/Repo.git', 'github'), 'org/repo');
    assert.equal(normalize('www.github.com/Org/Repo/pull/3', 'github'), 'org/repo');
    assert.equal(normalize('https://other.example/Org/Repo', 'github'), 'org/repo');
    assert.equal(normalize('single-segment', 'github'), null);
  });
  await check('REVIEW-GITLAB-NESTED-PATH-AND-UI-SUFFIX', () => {
    assert.equal(normalize('https://gitlab.com/Group/Sub/Repo/-/merge_requests/2', 'gitlab'), 'Group/Sub/Repo');
    assert.equal(normalize('Group/Sub/Repo.git', 'gitlab'), 'Group/Sub/Repo');
    assert.equal(normalize('https://[invalid/', 'github'), null);
  });
  const instructions = unit('code-review', 'an', {URL});
  await check('REVIEW-INSTRUCTIONS-PROVIDER-AND-ENCODED-BRANCH', () => {
    assert.equal(instructions({id: 'github-x', clone_url: 'https://github.com/a/r.git', default_branch: 'feature/x'}),
      'https://github.com/a/r/blob/feature%2Fx/AGENTS.md');
    assert.equal(instructions({id: 'gitlab-x', clone_url: 'https://git.example/g/sub/r.git', default_branch: 'main'}),
      'https://git.example/g/sub/r/-/blob/main/AGENTS.md');
    for (const clone_url of ['ssh://git.example/a/r', 'invalid'])
      assert.equal(instructions({clone_url, default_branch: 'main'}), null);
    assert.equal(instructions({clone_url: 'https://git.example/a/r'}), null);
  });
  function repositoryQuery(params, responses) {
    const requests = [];
    const factory = unit('code-review', 'assignment-zt', {F: (_, fn) => fn, p: 'scope',
      ce: 'account', Lt: 8, Te: {FIVE_MINUTES: 300000}, It: normalize, n: HttpError,
      L: {safeGet: async (url, options) => {requests.push([url, plain(options)]);
        const response = responses[requests.length - 1]; if (response instanceof Error) throw response;
        assert(response !== undefined); return response;}}});
    return {query: factory(params, {get: () => 'owned-account'}), requests};
  }
  await check('REVIEW-GITLAB-EMPTY-SEARCH-LIST-RECEIVER', async () => {
    const probe = repositoryQuery({provider: 'gitlab', search: '  ', nextToken: 't', connectorId: 'c'}, [{repo_review_settings: []}]);
    await probe.query.queryFn();
    assert.deepEqual(probe.requests, [['/wham/settings/code_review', {parameters: {query: {
      provider: 'gitlab', next_token: 't', connector_id: 'c', per_page: 8}}}]]);
  });
  await check('REVIEW-DIRECT-ARCHIVED-RESULT-DOES-NOT-SEARCH', async () => {
    const probe = repositoryQuery({provider: 'github', search: 'Org/Repo', connectorId: 'c'}, [{repository: {archived: true}}]);
    assert.deepEqual(plain(await probe.query.queryFn()), {repo_review_settings: [], next_token: null});
    assert.equal(probe.requests.length, 1);
    assert.equal(probe.requests[0][1].parameters.path.repo_id, 'github-org/repo');
  });
  await check('REVIEW-EXPECTED-DIRECT-ERRORS-FALL-BACK-TO-SEARCH', async () => {
    for (const status of [400, 403, 404]) {
      const probe = repositoryQuery({provider: 'github', search: 'Org/Repo', connectorId: 'c'},
        [new HttpError(status), {repo_review_settings: Array.from({length: 8}, (_, id) => ({id}))}]);
      assert.equal((await probe.query.queryFn()).next_token, '2');
      assert.equal(probe.requests[1][1].parameters.query.query, 'Org/Repo archived:false');
    }
  });
  await check('REVIEW-UNEXPECTED-DIRECT-ERROR-IS-NOT-HIDDEN', async () => {
    const probe = repositoryQuery({provider: 'github', search: 'a/b'}, [new HttpError(500)]);
    await assert.rejects(probe.query.queryFn(), /HTTP 500/); assert.equal(probe.requests.length, 1);
  });
  await check('REVIEW-GITHUB-PAGINATION-CAP-AND-SHORT-PAGE', async () => {
    const full = Array.from({length: 8}, () => ({}));
    for (const [page, rows, next] of [['124', full, '125'], ['125', full, null], ['2', [], null]]) {
      const probe = repositoryQuery({provider: 'github', search: 'x', nextToken: page}, [{repo_review_settings: rows}]);
      assert.equal((await probe.query.queryFn()).next_token, next);
    }
  });
  function connectors({changeIdentity = false, abort = false} = {}) {
    let current = 'a'; const calls = [];
    const factory = unit('code-review', 'assignment-Rt', {F: (_, fn) => fn, p: 'scope', ce: 'a', we: 'u',
      Te: {FIVE_MINUTES: 300000}, Ee: async () => [
        {id: 'disabled', status: 'DISABLED_BY_ADMIN'}, {id: 'admin', labels: {admin_only_connector: 'true'}},
        {id: 'linked'}, {id: 'not-linked'}], nt: params => ({queryKey: ['links', params]})});
    const query = factory('github', {get: key => key === 'a' ? 'a' : 'u',
      scope: {get: key => key === 'a' ? current : 'u'}});
    return {query, calls, run: () => query.queryFn({client: {fetchQuery: async options => {
      calls.push(plain(options)); if (changeIdentity) current = 'other'; return [{connector_id: 'linked'}];}},
      signal: {throwIfAborted() {if (abort) throw Error('synthetic abort');}}})};
  }
  await check('REVIEW-CONNECTORS-ELIGIBILITY-AND-LINK-INTERSECTION', async () => {
    const probe = connectors(); assert.deepEqual(plain(await probe.run()), [{id: 'linked'}]);
    assert.equal(probe.calls[0].queryKey[1].productSku, 'CODEX');
    assert.equal(probe.calls[0].queryKey[1].linkRefreshStrategy, 'NONE');
  });
  await check('REVIEW-CONNECTORS-ABORT-AND-STALE-IDENTITY', async () => {
    const abort = connectors({abort: true}); await assert.rejects(abort.run(), /synthetic abort/); assert.equal(abort.calls.length, 0);
    await assert.rejects(connectors({changeIdentity: true}).run(), /Account changed/);
  });
  await check('REVIEW-PATCH-SINGLE-RECORD-AND-CONFLICT-REFRESH', async () => {
    const effects = [];
    const factory = unit('code-review', 'assignment-Vt', {_: (_, fn) => fn, p: 'scope', n: HttpError, Bt: 'detail',
      L: {safePatch: async (url, body) => effects.push(['patch', url, plain(body)])}});
    const q = factory('repo', {scope: {queryClient: {invalidateQueries: async key => effects.push(['all', plain(key)])},
      query: {invalidate: async (...args) => effects.push(['detail', ...args])}}});
    await q.mutationFn({repository: 'repo', authorize_funding: true}); await q.onSuccess();
    await q.onError(new HttpError(403)); assert.equal(effects.length, 2);
    await q.onError(new HttpError(409));
    assert.deepEqual(effects[0], ['patch', '/wham/settings/code_review', {
      expectedErrorStatuses: [400, 403, 409], requestBody: {repo_review_settings: [{repository: 'repo', authorize_funding: true}]}}]);
    assert.deepEqual(effects[2], ['detail', 'detail', 'repo']);
  });
  await check('REVIEW-USER-PREFERENCES-HAVE-A-SEPARATE-HTTP-RECEIVER', async () => {
    const effects = [], api = {safeGet: async (...args) => effects.push(['get', ...args]),
      safePatch: async (...args) => effects.push(['patch', ...args])};
    const get = unit('cloud-preferences', 'y', {a: api});
    const patch = unit('cloud-preferences', 'C', {a: api});
    await get({signal: 'synthetic-signal'}); await patch({security_review: {preference: 'always'}});
    assert.deepEqual(plain(effects), [['get', '/wham/settings/user', {signal: 'synthetic-signal'}],
      ['patch', '/wham/settings/user', {requestBody: {security_review: {preference: 'always'}}}]]);
    assert.deepEqual(plain(unit('cloud-preferences', '_')('owned-user')), ['cloud-user-preferences', 'owned-user']);
  });
  await check('REVIEW-PATH-SUBMIT-TRIM-AND-DISABLED-DIRTY-GUARD', () => {
    for (const [disabled, dirty, count] of [[false, true, 1], [true, true, 0], [false, false, 0]]) {
      const values = [];
      const fn = callback('code-review', 'gn', text => text.startsWith('e=>{e.preventDefault(),!r&&m&&o(u.trim())}'),
        {r: disabled, m: dirty, o: value => values.push(value), u: ' docs/model.md '});
      fn({preventDefault() {}}); assert.equal(values.length, count);
      if (count) assert.equal(values[0], 'docs/model.md');
    }
  });
  function deletion({receiver = true, beforeMismatch = false, switchDuringCancel = false, reject = false} = {}) {
    let account = beforeMismatch ? 'other' : 'a'; const effects = [];
    const context = {le: receiver ? {environmentConfigs: {delete: async payload => {
      effects.push(['delete', plain(payload)]); if (reject) throw Error('synthetic unavailable'); return {ok: true};}}} : null,
      r: 'a', a: 'u', o: {id: 'config'}, q: 'account', Y: 'user', n: 'selected', ht: 'selected-config', Wt: 'catalog',
      vn: unit('codex-cloud', 'vn'), bt: () => effects.push(['clear-selection']), s: () => effects.push(['close']),
      S: key => effects.push(['family', plain(key)])};
    context.c = {get: key => key === 'account' ? account : key === 'user' ? 'u' : key === 'selected' ? 'thread' : {id: 'config'},
      query: {cancel: async () => {effects.push(['cancel']); if (switchDuringCancel) account = 'other';},
        setData: (_, update) => effects.push(['data', plain(update([{id: 'config'}, {id: 'keep'}]))]),
        invalidate: async () => effects.push(['invalidate'])}, queryClient: {
        cancelQueries: async key => effects.push(['cancel-query', plain(key)]),
        removeQueries: key => effects.push(['remove-query', plain(key)]),
        resetQueries: async key => effects.push(['reset-query', plain(key)])}};
    return {effects,
      mutate: callback('codex-cloud', '_n', text => text.startsWith('async()=>{let e=le?.environmentConfigs'), context),
      success: callback('codex-cloud', '_n', text => text.startsWith('async e=>{if(e.ok&&c.get(q)'), context)};
  }
  await check('CLOUD-DELETE-UNAVAILABLE-AND-AUTHENTICATION-GUARDS', async () => {
    const noReceiver = deletion({receiver: false}); assert.equal((await noReceiver.mutate()).error, 'unavailable');
    const changed = deletion({beforeMismatch: true}); assert.equal((await changed.mutate()).error, 'authentication');
    assert.equal(noReceiver.effects.length + changed.effects.length, 0);
    const rejected = deletion({reject: true}); assert.equal((await rejected.mutate()).error, 'unavailable');
  });
  await check('CLOUD-DELETE-SUCCESS-RECONCILES-ONLY-CONFIG-CACHES', async () => {
    const probe = deletion(); await probe.success(await probe.mutate());
    assert.deepEqual(probe.effects[0], ['delete', {accountId: 'a', userId: 'u', configId: 'config', method: 'DELETE'}]);
    assert(probe.effects.some(row => row[0] === 'clear-selection'));
    assert.deepEqual(probe.effects.find(row => row[0] === 'data')[1], [{id: 'keep'}]);
    assert.equal(probe.effects.filter(row => row[0] === 'family').length, 3);
    assert.equal(probe.effects.filter(row => row[0] === 'close').length, 1);
  });
  await check('CLOUD-DELETE-RECHECKS-IDENTITY-AFTER-CANCEL', async () => {
    const probe = deletion({switchDuringCancel: true}); await probe.success({ok: true});
    assert.equal(probe.effects.length, 3); assert(probe.effects.every(row => row[0].startsWith('cancel')));
    const failed = deletion(); await failed.success({ok: false}); assert.equal(failed.effects.length, 0);
  });
  await check('CLOUD-DELETE-PENDING-AND-TERMINAL-SUBMIT-GUARD', () => {
    for (const [pending, terminal, expected] of [[false, false, 1], [true, false, 0], [false, true, 0]]) {
      let count = 0;
      callback('codex-cloud', '_n', text => text === 'e=>{e.preventDefault(),!p&&!v&&h()}',
        {p: pending, v: terminal, h: () => count++})({preventDefault() {}}); assert.equal(count, expected);
    }
  });
  const Uncertain = unit('codex-cloud', 'assignment-xn', {Error});
  const NotFound = unit('codex-cloud', 'assignment-Sn', {Error});
  function draft({response = {ok: true, data: {thread_id: 'owned-thread', draft_id: 'draft', environment_id: 'env'}},
    changeAfter = false, permission = true, available = true, loading = false, titleFail = false} = {}) {
    let account = 'a'; const effects = [];
    const context = {w: (_, fn) => fn, x: 'scope', Error, xn: Uncertain, Sn: NotFound,
      Ie: 'auth', q: 'account', Y: 'user', Me: 'enabled', ne: 'rbac', xt: 'names', de: 'intl',
      Pe: () => ({u: value => value, e: null, d() {effects.push(['dispose']); if (this.e) throw this.e;}}),
      Ct: () => permission, le: available ? {environmentConfigs: {createDraft: async payload => {
        effects.push(['post', plain(payload)]); if (changeAfter) account = 'other'; return response;}}} : null,
      he: () => 'host', Le: () => ({setThreadTitle: async (...args) => {effects.push(['title', ...args]); if (titleFail) throw Error('title');}}),
      Oe: id => id, V: (scope, fn) => fn(scope),
      it: (_, thread, data) => effects.push(['metadata', thread, plain(data)]), Xe: () => {}, ce: () => {},
      we: () => 'environment', f: {warning: () => effects.push(['warning'])}};
    const scope = {get: key => key === 'auth' ? {authLoading: loading} : key === 'account' ? account : key === 'user' ? 'u' :
      key === 'enabled' ? true : key === 'names' ? {repo: 'Owned/Repo'} : key === 'intl' ?
      {formatMessage: (_, values) => `Edit ${values.environmentName}`} : {}};
    const factory = unit('codex-cloud', 'assignment-Cn', context);
    const mutation = factory({accountId: 'a', userId: 'u', configId: 'config'}, {scope});
    return {effects, mutation, run: () => mutation.mutationFn({id: 'config', name: 'Owned', repositories: [{repositoryId: 'repo'}]})};
  }
  await check('CLOUD-DRAFT-SUCCESS-METADATA-AND-NONFATAL-TITLE-FAILURE', async () => {
    const probe = draft({titleFail: true}); assert.equal(await probe.run(), 'owned-thread'); await Promise.resolve();
    assert.equal(probe.mutation.retry, false);
    assert.deepEqual(probe.effects[0], ['post', {accountId: 'a', userId: 'u', configId: 'config', method: 'POST'}]);
    assert.equal(probe.effects.find(row => row[0] === 'metadata')[2].repositoryNamesById.repo, 'Owned/Repo');
    assert(probe.effects.some(row => row[0] === 'warning')); assert(probe.effects.some(row => row[0] === 'dispose'));
  });
  await check('CLOUD-DRAFT-AUTHENTICATION-PERMISSION-AND-RECEIVER-GUARDS', async () => {
    for (const [options, message] of [[{loading: true}, 'authentication'], [{permission: false}, 'permission'], [{available: false}, 'unavailable']]) {
      const probe = draft(options); await assert.rejects(probe.run(), new RegExp(message));
      assert.equal(probe.effects.filter(row => row[0] === 'post').length, 0);
    }
    const changed = draft({changeAfter: true}); await assert.rejects(changed.run(), /authentication/);
    assert.equal(changed.effects.filter(row => row[0] === 'metadata').length, 0);
  });
  await check('CLOUD-DRAFT-UNCERTAIN-RESPONSES-DIFFER-FROM-NOT-FOUND', async () => {
    for (const response of [null, {ok: false, error: 'unavailable'}, {ok: false, error: 'invalid-response'},
      {ok: false, error: 'authentication'}, {ok: false, error: 'http', status: 500}])
      await assert.rejects(draft({response}).run(), error => error instanceof Uncertain);
    await assert.rejects(draft({response: {ok: false, error: 'http', status: 404}}).run(), error => error instanceof NotFound);
    await assert.rejects(draft({response: {ok: true, data: {}}}).run(), /invalid-response/);
  });
  function save({readonly = false, mismatch = false, vpnPending = false, vpnResult = {id: 'vpn'}, changes = {name: 'New'}} = {}) {
    const effects = [];
    const fn = callback('codex-cloud', 'On', text => text.startsWith('async()=>{if(b)throw Error(`permission`)'), {
      Error, b: readonly, o: {get: key => key === 'account' ? (mismatch ? 'other' : 'a') : 'u'},
      q: 'account', Y: 'user', r: {accountId: 'a', userId: 'u'}, P: {pending: vpnPending},
      I: {current: {save: async () => {effects.push(['vpn']); return vpnResult;}}}, g: {id: 'current'}, w: changes,
      T: 'panel', v: () => {}, E: () => {}, lt: async (_, payload) => {effects.push(['save', plain(payload)]); return payload.config;}});
    return {run: fn, effects};
  }
  await check('CLOUD-EDITOR-SAVE-PERMISSION-IDENTITY-AND-VPN-GUARDS', async () => {
    for (const [options, message] of [[{readonly: true}, 'permission'], [{mismatch: true}, 'authentication'],
      [{vpnPending: true, vpnResult: null}, 'unavailable']]) {
      const probe = save(options); await assert.rejects(probe.run(), new RegExp(message));
      assert.equal(probe.effects.filter(row => row[0] === 'save').length, 0);
    }
    const probe = save({vpnPending: true}); assert.equal((await probe.run()).id, 'vpn');
    assert.deepEqual(probe.effects.map(row => row[0]), ['vpn', 'save']);
  });
  await check('CLOUD-EDITOR-NO-NORMALIZED-CHANGE-SKIPS-CONFIG-WRITE', async () => {
    const probe = save({changes: null}); assert.equal((await probe.run()).id, 'current'); assert.equal(probe.effects.length, 0);
  });
  await check('CLOUD-SECRET-METADATA-BLANKS-VALUES-AND-PRESERVES-TARGET', () => {
    const row = unit('codex-cloud', 'Fn');
    const env = row({name: 'TOKEN', source: 'environment', value: 'never-copy', target: {environment_variable: 'TOKEN', allowed_domains: ['one', 'two']}}, 3);
    assert.equal(env.value, ''); assert.equal(env.isMissing, true);
    assert.deepEqual(plain(env.injectionTarget), {type: 'environment_variable', name: 'TOKEN', domain: 'one, two'});
    const header = row({id: 'server', name: 'API', source: 'user_provided', value: 'never-copy',
      target: {http_header: {header_name: 'X-API', allowed_domains: ['owned.example']}}}, 4);
    assert.equal(header.value, ''); assert.equal(header.serverId, 'server');
    assert.deepEqual(plain(header.injectionTarget), {type: 'http_header', name: 'X-API', domain: 'owned.example'});
    assert.deepEqual(plain(unit('codex-cloud', 'kn')({name: ' TOKEN '})), ['TOKEN']);
    assert.deepEqual(plain(unit('codex-cloud', 'kn')({name: '  '})), []);
  });
  const sourceSelections = [...new Map(used.map(record => [`${record.page}:${record.spanHash}`, record])).values()];
  const failed = cases.filter(value => !value.passed).length;
  const result = {baselineId: base,
    method: 'Exact frozen pure functions, query/mutation factories and callbacks; all accounts/configs/repositories and HTTP/runtime receivers are synthetic.',
    sourceSelections, cases, passed: cases.length - failed, failed, productScenariosExecuted: 0,
    modelSubmissionsAdded: 0, originalClientRunsAdded: 0, realServiceCalls: 0, personalCredentialReads: 0};
  fs.writeFileSync(path.join(work, 'isolated-observations.json'), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
  process.stdout.write(JSON.stringify({passed: result.passed, failed, failedCases: cases.filter(value => !value.passed), productScenariosExecuted: 0}) + '\n');
  if (failed) process.exitCode = 1;
})().catch(error => {process.stderr.write(error.stack + '\n'); process.exitCode = 1;});
