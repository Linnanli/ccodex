// Frozen source snippets; every receiver, file reference and account is synthetic.
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const assert = require('node:assert/strict'), crypto = require('node:crypto');
const root = process.cwd(), base = 'codex-26.1007.30912-c5b273322a83';
const work = path.join(root, '.analysis-local/settings-debug-pets-import-batch10-work');
const frozen = path.join(root, '.analysis-local/baselines', base, 'extracted');
const pages = ['debug', 'pets', 'import', 'import-actions', 'import-setup'];
const metadata = Object.fromEntries(pages.map(page => [page, JSON.parse(fs.readFileSync(path.join(work, page, 'source-contracts.json')))]));
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
  const records = metadata[page].callbacks.filter(value => value.unit === name).filter(value => match(exact(page, value)));
  assert.equal(records.length, 1, `${page}:${name}`);
  return vm.runInNewContext(`(${exact(page, records[0])})`, context, {timeout: 1000});
}
async function check(id, run) {
  try {await run(); cases.push({id, passed: true});}
  catch (error) {cases.push({id, passed: false, error: String(error.stack)});}
}
const memo = {c: size => Array(size).fill(Symbol.for('react.memo_cache_sentinel'))};
const jsx = {jsx: (type, props) => ({type, props}), jsxs: (type, props) => ({type, props})};
function nodes(value) {
  if (!value || typeof value !== 'object') return [];
  if (Array.isArray(value)) return value.flatMap(nodes);
  return [value, ...Object.values(value.props ?? {}).flatMap(nodes)];
}

(async () => {
  await check('DEBUG-CHROME-GATE-DOES-NOT-REMOVE-GPU-GROUP', () => {
    for (const gate of [true, false]) {
      const calls = [];
      const render = unit('debug', 'P', {L: memo, R: jsx, d: {allowDebugMenu: env => {calls.push(env); return gate;}},
        O: 'page', E: 'title', F: 'chrome', I: 'gpu'});
      const types = nodes(render()).map(row => row.type);
      assert.equal(types.includes('chrome'), gate); assert(types.includes('gpu')); assert.deepEqual(calls, ['prod']);
    }
  });
  await check('DEBUG-EXACT-SIX-GPU-KEYS-AND-SETTER-PAYLOADS', () => {
    const keys = ['disableScrollFadeMask', 'disableScrollFadeMaskAnimation', 'disableBackdropBlur',
      'disableCssMotion', 'disableSquircles', 'forceOpaqueRendererBackground'];
    const effects = [];
    const render = unit('debug', 'I', {L: memo, R: jsx, i: () => 'scope', a: 'scope-atom',
      m: () => ({formatMessage: message => message.id}), r: () => Object.fromEntries(keys.map(key => [key, false])), A: 'gpu-state',
      N: Object.assign('section', {Header: 'header', Content: 'content'}), y: 'message', _: 'list', u: 'row', t: 'switch',
      j: (...args) => effects.push(args)});
    const switches = nodes(render()).filter(row => row.type === 'switch'); assert.equal(switches.length, 6);
    switches.forEach(row => row.props.onChange(true));
    assert.deepEqual(effects, keys.map(key => ['scope', key, true]));
  });
  await check('DEBUG-CHROME-PREFERENCE-IS-INDEPENDENT-FROM-URL-OPENING', () => {
    const effects = [];
    callback('debug', 'F', text => text === 'e=>{S(n,p.debugChromePagesEnabled,e)}',
      {S: (...args) => effects.push(args), n: 'scope', p: {debugChromePagesEnabled: 'chrome-pref'}})(true);
    assert.deepEqual(effects, [['scope', 'chrome-pref', true]]);
  });
  function selectPet(visible, selected = 'one') {
    const effects = [];
    return {effects, run: callback('pets', 'ir', text => text.startsWith('e=>{w&&e.id===S.id||'),
      {w: visible, S: {id: selected}, C: id => effects.push(['selected', id]), Be: (_, key, value) => effects.push([key, value]),
        p: 'scope', k: {petVisible: 'visible'}, N: (_, avatar) => effects.push(['event', avatar.id]),
        Te: {CODEX_AVATAR_OVERLAY_ACTION_PET_SELECTED: 'selected-event'}})};
  }
  await check('PETS-SELECTION-NOOP-AND-HIDDEN-SELECTION-REENABLE', () => {
    const same = selectPet(true); same.run({id: 'one'}); assert.equal(same.effects.length, 0);
    const hidden = selectPet(false); hidden.run({id: 'one'});
    assert.deepEqual(hidden.effects, [['selected', 'one'], ['visible', true], ['event', 'one']]);
    const other = selectPet(true); other.run({id: 'two'});
    assert.deepEqual(other.effects, [['selected', 'two'], ['event', 'two']]);
  });
  await check('PETS-NONE-HIDES-ARTWORK-WITHOUT-CHANGING-SELECTION', () => {
    for (const visible of [true, false]) {
      const writes = [];
      callback('pets', 'ir', text => text === '()=>{w&&Be(p,k.petVisible,!1)}',
        {w: visible, Be: (...args) => writes.push(args), p: 'scope', k: {petVisible: 'visible'}})();
      assert.deepEqual(writes, visible ? [['scope', 'visible', false]] : []);
    }
  });
  await check('PETS-SIZE-NUMERIC-WRITE-AND-DEFAULT-RESET', () => {
    const writes = [], context = {Be: (_, key, value) => writes.push([key, value]), p: 'scope', k: {petSize: {id: 'size', default: 144}}};
    callback('pets', 'ir', text => text === 'e=>{Be(p,k.petSize,Number(e.currentTarget.value))}', context)({currentTarget: {value: '224'}});
    callback('pets', 'ir', text => text === '()=>{Be(p,k.petSize,k.petSize.default)}', context)();
    assert.equal(writes[0][1], 224); assert.equal(writes[1][1], 144);
  });
  await check('PETS-OVERLAY-REQUEST-USES-SAVED-AVATAR-FALLBACK', () => {
    const effects = [];
    const fn = callback('pets', 'fr', text => text.startsWith('()=>{n.get(ce).logProductEvent'), {
      n: {get: () => ({logProductEvent: (_, payload) => effects.push(['event', payload])})}, ce: 'telemetry', t: 'event',
      gt: value => value, r: false, Te: {CODEX_AVATAR_OVERLAY_ACTION_OPEN_REQUESTED: 'open'},
      Je: () => null, k: {selectedAvatarId: 'avatar'}, lt: [{id: 'default'}],
      j: {CODEX_AVATAR_OVERLAY_SOURCE_SETTINGS: 'settings'}, F: {dispatchMessage: (...args) => effects.push(['dispatch', ...args])}});
    fn(); assert.equal(effects[0][1].selectedAvatar.id, 'default');
    assert.deepEqual(plain(effects[1]), ['dispatch', 'avatar-overlay-open', {}]);
  });
  function prepareSkill({install = {success: true, destination: '/owned/skill'}, enabled = true} = {}) {
    const effects = [];
    const run = unit('pets', 'In', {D: async (...args) => {effects.push(['install', ...args]); return install;},
      L: 'owned-host', Rn: 'skills/.curated/hatch-pet', Ln: 'hatch-pet', Nt: (...parts) => parts.join('/'),
      Ue: () => ({sendRequest: async (...args) => {effects.push(['request', ...args]); return {effectiveEnabled: enabled};}}),
      C: value => {effects.push(['reference', value]); return 'skill-ref';}, Error});
    return {effects, run: () => run({scope: 'scope', forceReloadSkills: async () => effects.push(['reload']), skillStatsigOverride: 'override'})};
  }
  await check('PETS-SKILL-PREPARATION-INSTALL-ENABLE-RELOAD-ORDER', async () => {
    const probe = prepareSkill(); assert.equal(await probe.run(), 'skill-ref');
    assert.deepEqual(probe.effects.map(row => row[0]), ['install', 'request', 'reload', 'reference']);
    assert.equal(probe.effects[0][2].params.forceReinstall, true);
    assert.deepEqual(plain(probe.effects[1]), ['request', 'skills/config/write', {enabled: true, path: '/owned/skill/SKILL.md'}]);
  });
  await check('PETS-SKILL-PREPARATION-FAILURES-STOP-BEFORE-PREFILL', async () => {
    for (const options of [{install: {success: false, error: 'owned failure'}}, {install: {success: true}}, {enabled: false}]) {
      const probe = prepareSkill(options); await assert.rejects(probe.run());
      assert(!probe.effects.some(row => row[0] === 'reference' || row[0] === 'reload'));
    }
  });
  await check('PETS-CREATE-AND-UPGRADE-PREPARE-TEXT-ONLY', async () => {
    const effects = [];
    const prompt = unit('pets', 'Pn', {jt: value => {effects.push(value); return 'plugin-prefill';}, In: async () => 'skill-ref'});
    assert.equal(await prompt({pluginId: 'owned-plugin', pluginDisplayName: 'Owned'}), 'plugin-prefill');
    assert.match(await prompt({scope: 'owned'}), /^skill-ref create/);
    assert.equal(effects[0].pluginId, 'owned-plugin');
    const names = [];
    const upgrade = unit('pets', 'Fn', {In: async () => 'skill-ref', Ie: (name, dir) => {names.push([name, dir]); return 'pet-ref';}});
    assert.match(await upgrade({petName: 'One\r\nTwo', petDirectoryPath: '/owned/pet'}), /upgrade.*pet-ref/);
    assert.deepEqual(names, [['One Two', '/owned/pet']]);
  });
  await check('PETS-INSTALLED-PLUGIN-MUST-HAVE-ALLOWED-MARKETPLACE', () => {
    const eligible = unit('pets', 'Hn');
    assert.equal(eligible({marketplaceName: 'openai-curated-remote', plugin: {installed: true, name: 'work-pets'}}), true);
    assert.equal(eligible({marketplaceName: 'other', plugin: {installed: true, name: 'work-pets'}}), false);
    assert.equal(eligible({marketplaceName: 'openai-curated', plugin: {installed: false, name: 'work-pets'}}), false);
  });
  await check('IMPORT-TARGET-ROUTES-ENCODE-SEARCH-AND-REUSE-MANAGERS', () => {
    const routes = [];
    const target = unit('import', 'xn', {k: 'owned-host', Se: value => {routes.push(value); return '/owned/plugin';}});
    assert.equal(target('COMMANDS', 'name', 'a & b'), '/skills?search=a%20%26%20b');
    assert.equal(target('MCP_SERVER_CONFIG', 'name'), '/settings/mcp-settings?search=name');
    assert.equal(target('PLUGINS', 'name', 'plugin-id'), '/owned/plugin');
    assert.deepEqual(plain(routes), [{hostId: 'owned-host', pluginId: 'plugin-id'}]);
    assert.equal(target('MEMORY', 'name'), null);
  });
  await check('IMPORT-SYNC-TOGGLE-ERROR-IS-SEPARATE-FROM-CATEGORY-WRITE', async () => {
    const effects = [];
    const toggle = callback('import', 'Jn', text => text === 'e=>{M(!1),Ie(i,h.syncEnabled,e).catch(()=>{M(!0)})}',
      {M: value => effects.push(['error', value]), i: 'scope', h: {syncEnabled: 'enabled'},
        Ie: async (_, key, value) => {effects.push(['write', key, value]); throw Error('synthetic');}});
    toggle(true); await Promise.resolve();
    assert.deepEqual(effects, [['error', false], ['write', 'enabled', true], ['error', true]]);
  });
  await check('IMPORT-CATEGORY-SUBMIT-REQUIRES-SELECTION-AND-NOT-PENDING', async () => {
    for (const [selected, pending, expected] of [[true, false, 1], [false, false, 0], [true, true, 0]]) {
      const effects = [];
      callback('import', 'Un', text => text === 'e=>{e.preventDefault(),C&&!o&&(h(!1),u(f).catch(()=>{h(!0)}))}',
        {C: selected, o: pending, h: value => effects.push(['error', value]), f: {SESSIONS: true},
          u: async value => {effects.push(['save', plain(value)]); throw Error('synthetic');}})({preventDefault() {}});
      await Promise.resolve(); assert.equal(effects.filter(row => row[0] === 'save').length, expected);
      if (expected) assert.deepEqual(effects.at(-1), ['error', true]);
    }
  });
  await check('IMPORT-CATEGORY-SAVE-CLOSES-ONLY-ON-SUCCESS-AND-RELEASES-PENDING', async () => {
    for (const fail of [false, true]) {
      const effects = [];
      const save = callback('import', 'Jn', text => text.startsWith('e=>(O(!0),Ie(i,h.syncItemTypes,e).then('), {
        O: value => effects.push(['pending', value]), E: value => effects.push(['open', value]), i: 'scope', h: {syncItemTypes: 'types'},
        Ie: async (_, key, value) => {effects.push(['write', key, value]); if (fail) throw Error('synthetic');}});
      if (fail) await assert.rejects(save('all')); else await save('all');
      assert.deepEqual(effects.at(-1), ['pending', false]);
      assert.equal(effects.some(row => row[0] === 'open'), !fail);
    }
  });
  await check('IMPORT-SETUP-READINESS-RETAINS-ERROR-RETRY-AND-COMPLETE-DATA', () => {
    const classify = unit('import-setup', 'oe', {U: value => ({classified: value})});
    const pending = {status: 'loading'}; assert.equal(classify({inputsResult: pending, pluginDirectory: {}}), pending);
    const ready = classify({inputsResult: {status: 'ready', data: {kind: 'complete', setup: {appsRequiringConnection: []}}}, pluginDirectory: {}});
    assert.deepEqual(plain(ready), {status: 'ready', data: {appsRequiringConnection: []}});
    let retries = 0;
    const failed = classify({inputsResult: {status: 'ready', data: {kind: 'plugin-directory'}},
      pluginDirectory: {errorMessage: 'synthetic', refetch: () => retries++}});
    assert.equal(failed.status, 'error'); failed.retry(); assert.equal(retries, 1);
  });
  await check('IMPORT-SETUP-CLASSIFICATION-ACCESS-INSTALLED-AND-PLUGIN-DEDUP', () => {
    const classify = unit('import-setup', 'U', {N: ({apps}) => apps, W: (app, plugin) => plugin.appId === app.id,
      o: market => market === 'owned-market', R: (app, plugin) => plugin.appId === app.id, Map, Set});
    const apps = [{id: 'accessible'}, {id: 'missing'}, {id: 'installed'}, {id: 'new'}, {id: 'new-again'}];
    const plugins = [{marketplaceName: 'owned-market', appId: 'installed', plugin: {id: 'installed-p', installed: true}},
      {marketplaceName: 'owned-market', appId: 'new', plugin: {id: 'same-p'}},
      {marketplaceName: 'owned-market', appId: 'new-again', plugin: {id: 'same-p'}}];
    const result = classify({candidates: [], directoryApps: apps, plugins, runtimeApps: [{id: 'accessible', isAccessible: true}], useCanonicalAppIds: true});
    assert.deepEqual(plain(result.appsRequiringConnection), [{id: 'missing'}, {id: 'installed'}]);
    assert.equal(result.importedPlugins.length, 1); assert.equal(result.importedPlugins[0].plugin.plugin.id, 'same-p');
  });
  function oauth({fail = false, deferred = false} = {}) {
    const urls = new Map(), effects = []; let resolve;
    const request = deferred ? new Promise(done => {resolve = done;}) : Promise.resolve({authorizationUrl: 'https://owned.invalid/oauth'});
    const context = {O: {current: urls}, g: 'scope', i: 'host',
      ne: () => ({sendRequest: async (...args) => {effects.push(['request', ...args]); if (fail) throw Error('synthetic'); return request;}}),
      J: value => effects.push(['open', value]), o: {error: () => effects.push(['error'])}};
    const run = callback('import-actions', 'We', text => text.startsWith('async e=>{let t=O.current.get(e)'), context);
    return {run, urls, effects, resolve};
  }
  await check('IMPORT-MCP-OAUTH-SUPPRESSES-INFLIGHT-AND-REOPENS-KNOWN-URL', async () => {
    const probe = oauth({deferred: true}); const pending = probe.run('server'); await probe.run('server');
    assert.equal(probe.effects.length, 1); assert.equal(probe.urls.get('server'), null);
    probe.resolve({authorizationUrl: 'https://owned.invalid/oauth'}); await pending; await probe.run('server');
    assert.equal(probe.effects.filter(row => row[0] === 'request').length, 1);
    assert.equal(probe.effects.filter(row => row[0] === 'open').length, 2);
    assert.equal(probe.effects[0][1], 'mcpServer/oauth/login');
  });
  await check('IMPORT-MCP-OAUTH-REQUEST-FAILURE-ALLOWS-RETRY', async () => {
    const probe = oauth({fail: true}); await probe.run('server'); assert.equal(probe.urls.has('server'), false);
    await probe.run('server'); assert.equal(probe.effects.filter(row => row[0] === 'request').length, 2);
    assert.equal(probe.effects.filter(row => row[0] === 'open').length, 0);
  });
  await check('IMPORT-MCP-OAUTH-COMPLETION-INVALIDATES-ONLY-KNOWN-SERVER', () => {
    const urls = new Map([['server', 'https://owned.invalid/oauth']]), effects = [];
    const complete = callback('import-actions', 'We', text => text.startsWith('()=>{if(C==null||!O.current.has(C.name))return;'), {
      C: {name: 'server', success: true}, O: {current: urls}, v: {invalidateQueries: value => effects.push(value)}, j: ['mcp'], i: 'host'});
    complete(); assert.equal(urls.size, 0); assert.deepEqual(plain(effects), [{queryKey: ['mcp', 'host']}]);
  });
  await check('IMPORT-POSTSETUP-RETRY-ROUTES-TO-ITS-OWN-QUERY-FAMILIES', () => {
    const effects = [];
    const retry = callback('import-actions', 'We', text => text.startsWith('e=>{switch(e){case`apps`:'), {
      f: () => effects.push('apps'), c: () => effects.push('history'), r: true, p: () => effects.push('mcp')});
    retry('apps'); retry('mcps'); retry('hooks');
    assert.deepEqual(effects, ['apps', 'history', 'mcp', 'history']);
  });
  await check('IMPORT-CONNECTION-DIALOG-CLOSE-CLEARS-CONNECTING-APP', () => {
    let cleared = 0;
    const change = callback('import', 'rr', text => text === 'e=>{e||x()}', {x: () => cleared++});
    change(true); assert.equal(cleared, 0); change(false); assert.equal(cleared, 1);
  });
  const sourceSelections = [...new Map(used.map(record => [`${record.page}:${record.spanHash}`, record])).values()];
  const failed = cases.filter(value => !value.passed).length;
  const result = {baselineId: base, method: 'Frozen control render/callback/pure-function replay with synthetic preferences, catalogs, skill, OAuth and query receivers; no target module imports.',
    sourceSelections, cases, passed: cases.length - failed, failed, productScenariosExecuted: 0, modelSubmissionsAdded: 0,
    originalClientRunsAdded: 0, realServiceCalls: 0, personalResourceReads: 0, realImportRuns: 0, realPluginOrSkillInstalls: 0};
  fs.writeFileSync(path.join(work, 'isolated-observations.json'), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
  process.stdout.write(JSON.stringify({passed: result.passed, failed, failedCases: cases.filter(value => !value.passed), productScenariosExecuted: 0}) + '\n');
  if (failed) process.exitCode = 1;
})().catch(error => {process.stderr.write(error.stack + '\n'); process.exitCode = 1;});
