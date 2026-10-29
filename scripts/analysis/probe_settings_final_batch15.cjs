/* Exact saved functions/callbacks in owned fixtures; no application module imports. */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '../..');
const baselineId = 'codex-26.1007.30912-c5b273322a83';
const work = path.join(root, '.analysis-local/settings-final-batch15-work');
const frozen = path.join(root, '.analysis-local/baselines', baselineId, 'extracted');
const metadata = {}, sources = {}, used = [], cases = [];
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const plain = value => JSON.parse(JSON.stringify(value));
const jsx = {jsx: (type, props, key) => ({type, props, key}), jsxs: (type, props, key) => ({type, props, key}), Fragment: 'fragment'};
const memo = {c: n => Array(n).fill(Symbol.for('react.memo_cache_sentinel'))};
const formatter = {formatMessage: x => x.id ?? x.defaultMessage, formatNumber: n => `${n * 100}%`};
function nodes(tree) {
  if (!tree || typeof tree !== 'object') return [];
  if (Array.isArray(tree)) return tree.flatMap(nodes);
  return [tree, ...nodes(tree.props?.children)];
}
for (const folder of ['cloud-environments', 'personalization', 'codex-micro']) {
  const data = JSON.parse(fs.readFileSync(path.join(work, folder, 'source-contracts.json')));
  const bytes = fs.readFileSync(path.join(frozen, data.sourcePath.replace(/^app.asar\//, '')));
  assert.equal(hash(bytes), data.sourceHash); metadata[folder] = data; sources[folder] = bytes;
}
function record(folder, item) {
  const bytes = sources[folder].subarray(item.byteRange.start, item.byteRange.endExclusive);
  assert.equal(hash(bytes), item.spanHash);
  used.push({sourcePath: item.sourcePath, sourceHash: item.sourceHash, byteRange: item.byteRange, spanHash: item.spanHash});
  return bytes.toString('utf8');
}
function compile(text, env) {
  return new vm.Script(`(${text})`).runInNewContext({URLSearchParams, ...env}, {timeout: 1000});
}
function unit(folder, name, env = {}) {
  const item = metadata[folder].units.find(x => x.name === name); assert(item, name);
  const text = record(folder, item);
  assert.equal(fs.readFileSync(path.join(work, folder, item.sourceFilename), 'utf8'), text);
  return compile(text, env);
}
function callback(folder, name, predicate, env = {}) {
  const found = metadata[folder].callbacks.filter(x => x.unit === name).filter(x => {
    const t = sources[folder].subarray(x.byteRange.start, x.byteRange.endExclusive).toString('utf8'); return predicate(t);
  });
  assert.equal(found.length, 1, `${folder}/${name}: ${found.length} matching callbacks`);
  return compile(record(folder, found[0]), env);
}
async function check(id, run) {
  try {await run(); cases.push({id, passed: true});}
  catch (error) {cases.push({id, passed: false, error: error.stack});}
}
function route(tail = '', search = '', flag = false) {
  const calls = [], base = '/settings/cloud-environments';
  const env = {Z: memo, Q: jsx, l: () => ({pathname: base + tail, search}), N: () => value => calls.push(value),
    O: () => flag, Wt: e => e.length > 0, $: base, W: 'page', Nt: 'tabs', Ie: 'title', _t: 'preferences',
    Lt: 'list', X: 'breadcrumb', Jt: 'new-title', ht: 'editor', Kt: 'edit', Gt: 'detail', oe: 'redirect'};
  return {tree: unit('cloud-environments', 'Ut', env)(), calls, base};
}
function edit(query) {
  const env = {Z: memo, Q: jsx, te: (_, id) => {assert.equal(id, 'owned-E'); return query;}, at: 'query',
    $: '/settings/cloud-environments', oe: 'redirect', X: 'breadcrumb', Xt: 'edit-title', Yt: 'loading-title',
    Qe: 'loading', U: 'message', W: 'page', ht: 'editor'};
  return unit('cloud-environments', 'Kt', env)({environmentId: 'owned-E', onBack: () => {}, onRootClick: () => {}});
}
function parseHash(s) {const [pathname, search = ''] = s.split('?'); return {pathname, search};}
function buildHash(v) {return v.pathname + (v.search ? '?' + v.search : '');}
function memoryReset(options = {}) {
  const calls = [];
  const run = callback('personalization', 'Xr', s => s.startsWith('async()=>(p.kind'), {
    p: {kind: options.remote ? 'remote' : 'local'}, g: {available: !options.unavailable}, Oe: {chronicle: {}},
    M: {mutateAsync: async arg => {calls.push(['chronicle', plain(arg)]); if (options.fail) throw Error('owned reset failure');}},
    Ot: (_, host) => ({sendRequest: async (...args) => calls.push(['memory', host, ...args])}), s: {}, d: 'owned-H'});
  return {run, calls};
}

(async () => {
  await check('CLOUD-LIST-ENTRY-AND-ROW-NAVIGATION', () => {
    const f = route(); assert.equal(f.tree.type, 'list'); f.tree.props.onCreateEnvironment(); f.tree.props.onEditEnvironment('owned-E'); f.tree.props.onSelectEnvironment('owned-E');
    assert.deepEqual(f.calls, [f.base + '/new', f.base + '/owned-E/edit', f.base + '/owned-E']);
  });
  await check('CLOUD-NEW-EDITOR-NULL-BASELINE-SAVED-AND-CANCEL-ROUTES', () => {
    const f = route('/new'); const editor = nodes(f.tree).find(x => x.type === 'editor'); assert.equal(editor.props.environment, null);
    editor.props.onSaved('owned-E'); editor.props.onCancel(); assert.deepEqual(f.calls, [f.base + '/owned-E', f.base]);
  });
  await check('CLOUD-DETAIL-EDIT-AND-INVALID-PATHS', () => {
    const detail = route('/owned-E'); assert.equal(detail.tree.type, 'detail'); detail.tree.props.onEdit(); assert.equal(detail.calls[0], detail.base + '/owned-E/edit');
    const editing = route('/owned-E/edit'); assert.equal(editing.tree.type, 'edit'); assert.equal(editing.tree.props.environmentId, 'owned-E');
    for (const tail of ['/new/extra', '/owned-E/extra', '/owned-E/edit/extra']) {const f = route(tail); assert.equal(f.tree.type, 'redirect'); assert.equal(f.tree.props.replace, true);}
  });
  await check('CLOUD-PREFERENCES-ONLY-AT-GATED-ROOT', () => {
    assert(nodes(route('', '?tab=preferences', true).tree).some(x => x.type === 'preferences'));
    assert.equal(route('', '?tab=preferences', false).tree.type, 'list');
    assert.equal(route('/owned-E', '?tab=preferences', true).tree.type, 'detail');
  });
  await check('CLOUD-EDIT-REQUIRES-STRICT-BOOLEAN-WRITE-PERMISSION', () => {
    for (const value of [undefined, false, 1, 'true']) assert.equal(edit({data: {permissions: {can_write: value}}}).type, 'redirect');
    const tree = edit({data: {id: 'owned-E', label: 'Owned', permissions: {can_write: true}}});
    assert.equal(nodes(tree).find(x => x.type === 'editor').key, 'owned-E');
  });
  await check('CLOUD-EDIT-ERROR-REDIRECT-AND-PENDING-STATE', () => {
    assert.equal(edit({isError: true}).props.to, '/settings/cloud-environments/owned-E');
    assert(nodes(edit({isPending: true})).some(x => x.type === 'loading'));
  });
  await check('CLOUD-SECRET-NAMES-PRECEDENCE-AND-NULL-FILTER', () => {
    const project = unit('cloud-environments', 'xt');
    assert.deepEqual(plain(project({secrets: {OWNED_SECRET: 'not-returned'}, secrets_with_domains: [{name: 'ignored'}]})), ['OWNED_SECRET']);
    assert.deepEqual(plain(project({secrets: {}, secrets_with_domains: [{name: null}, {name: 'owned'}]})), ['owned']);
    assert.deepEqual(plain(project({})), []);
  });
  await check('CLOUD-NETWORK-AND-SHARING-UNKNOWN-BOUNDARIES', () => {
    const network = unit('cloud-environments', 'yt', {K: jsx, U: 'message'}), sharing = unit('cloud-environments', 'bt', {K: jsx, U: 'message'});
    assert.equal(network(undefined).props.defaultMessage, 'Off'); assert.equal(network('custom').props.defaultMessage, 'Custom');
    assert.equal(network('unexpected'), undefined); assert.equal(sharing('workspace').props.defaultMessage, 'Workspace'); assert.equal(sharing('unexpected'), undefined);
  });
  await check('CLOUD-MIGRATION-DRAFT-SELECTION-PRECEDES-ONBOARDING', () => {
    const calls = [], run = callback('cloud-environments', 'Ot', s => s.startsWith('()=>{let e=st('), {
      r: 'owned-store', i: 'owned-context', n: {id: 'owned-E', label: 'Owned', repos: ['R1', 'R2'], repo_map: {R1: {repository_full_name: 'owned/repo'}}}, c: {isLoading: false},
      st: (...args) => {calls.push(['draft', plain(args[2])]); return 'owned-draft';}, At: {flushSync: f => {calls.push(['flush']); f();}},
      o: (...args) => calls.push(['select', ...args]), ue: () => 'owned-revision', ct: (...args) => calls.push(['onboarding', ...args]), a: 'owned-navigate'});
    run(); assert.deepEqual(calls.map(x => x[0]), ['draft', 'flush', 'select', 'onboarding']);
    assert.deepEqual(calls[0][1].repositoryNamesById, {R1: 'owned/repo', R2: 'R2'});
  });
  await check('CLOUD-CONFIRMATION-PENDING-UI-IS-NOT-A-CALLBACK-GUARD', () => {
    for (const [name, pendingName, confirmName, closeName] of [['wt', 'i', 'o', 's'], ['Tt', 'n', 'a', 'o']]) {
      const calls = [], env = {Et: memo, q: jsx, Se: 'heading', U: 'message', M: 'text', r: 'header', u: 'button', de: 'footer', w: 'form', v: 'dialog'};
      const tree = unit('cloud-environments', name, env)({environmentName: 'Owned', isPending: true, open: true, onConfirm: () => calls.push('confirm'), onOpenChange: () => calls.push('close')});
      const all = nodes(tree), cancel = all.find(x => x.type === 'button' && x.props.type === 'button'), submit = all.find(x => x.type === 'button' && x.props.type === 'submit');
      assert.equal(cancel.props.disabled, true); assert.equal(submit.props.loading, true);
      all.find(x => x.type === 'form').props.onSubmit({preventDefault: () => calls.push('prevent')}); assert.deepEqual(calls, ['prevent', 'confirm']);
    }
  });

  await check('PERSONAL-RULES-ROUTE-PRESERVES-UNRELATED-LOCATION', () => {
    const change = unit('personalization', 'Gr', {Mt: parseHash, dt: buildHash});
    const state = {owned: true}, ordinary = change({pathname: '/settings/personalization', search: '?keep=1&instructions=codex', hash: '#old', state}, true);
    assert.equal(new URLSearchParams(ordinary.search).get('rules'), 'custom'); assert.equal(new URLSearchParams(ordinary.search).has('instructions'), false); assert.equal(ordinary.state, state); assert.equal(ordinary.hash, '');
    const nested = change({pathname: '/owned', search: '?outer=1', hash: '#settings/personalization?keep=1&rules=custom', state}, false);
    assert.equal(nested.hash, '#settings/personalization?keep=1'); assert.equal(nested.search, '?outer=1');
  });
  await check('PERSONAL-HOST-INSTRUCTIONS-CACHE-USES-SUBMITTED-HOST-AND-CONTENTS', () => {
    const calls = [], run = callback('personalization', 'wi', s => s.startsWith('(e,t)=>{a.query.setData'), {
      a: {query: {setData: (selector, arg, update) => calls.push([selector, plain(arg), plain(update({hasOverride: true}))])}}, li: 'owned-query'});
    run({path: '/owned/AGENTS.md', contents: 'server different'}, {hostId: 'owned-H', contents: 'submitted'});
    assert.deepEqual(calls[0], ['owned-query', {hostId: 'owned-H'}, {path: '/owned/AGENTS.md', contents: 'submitted', hasOverride: true}]);
  });
  await check('PERSONAL-HOST-INSTRUCTIONS-SAVE-CAPTURES-HOST', () => {
    const calls = [], run = callback('personalization', 'wi', s => s.startsWith('(e,t)=>f({hostId:'), {n: 'owned-H', f: (...args) => calls.push(plain(args))});
    run('owned contents', {owned: true}); assert.deepEqual(calls, [[{hostId: 'owned-H', contents: 'owned contents'}, {owned: true}]]);
  });
  await check('PERSONAL-ACCOUNT-CODEX-INSTRUCTIONS-LOADED-BASELINE-AND-PATCH', () => {
    for (const data of [undefined, {}, {custom_instructions: 'Owned'}]) {
      const calls = [], env = {ki: memo, X: jsx, Ti: 'editor', $n: () => ({data}), er: () => ({mutate: (...a) => calls.push(plain(a))})};
      const tree = unit('personalization', 'Ci', env)({onClose: () => {}}); assert.equal(tree.props.contents, data == null ? undefined : data.custom_instructions ?? '');
      tree.props.save('replacement', {owned: true}); assert.deepEqual(calls[0], [{custom_instructions: 'replacement'}, {owned: true}]);
    }
  });
  await check('PERSONAL-INSTRUCTION-SAVE-RECHECKS-LOADED-CHANGED-AND-PENDING', () => {
    for (const [loaded, changed, saving] of [[false, true, false], [true, false, false], [true, true, true], [true, true, false]]) {
      const calls = [], env = {w: loaded, C: changed, c: saving, S: 'owned draft', u: (...args) => calls.push(args)};
      callback('personalization', 'Ti', s => s.startsWith('()=>{w&&C&&!c&&u('), env)(); assert.equal(calls.length, loaded && changed && !saving ? 1 : 0);
    }
  });
  await check('PERSONAL-INSTRUCTION-SUCCESS-CLOSES-WHILE-ERROR-RETAINS-DRAFT', () => {
    const calls = [], env = {h: v => calls.push(['draft', v]), f: {get: () => ({success: () => calls.push(['success']), danger: () => calls.push(['error'])})}, ue: 'toast', p: formatter, d: () => calls.push(['close'])};
    callback('personalization', 'Ti', s => s.startsWith('()=>{f.get(ue).danger'), env)(); assert.deepEqual(calls, [['error']]);
    callback('personalization', 'Ti', s => s.startsWith('()=>{h(null),f.get(ue).success'), env)(); assert.deepEqual(calls.slice(1), [['draft', null], ['success'], ['close']]);
  });
  await check('PERSONAL-INSTRUCTION-BACK-PROMPTS-AND-CANCEL-DISCARDS', () => {
    for (const dirty of [false, true]) {
      const calls = [], env = {vi: memo, yi: {useState: () => [false, value => calls.push(['prompt', value])]}, It: 'button', _: 'button', bi: jsx, Ge: 'icon', nt: 'back', K: 'message', fn: 'layout', ir: 'unsaved', Re: 'toolbar'};
      const tree = unit('personalization', '_i', env)({dirty, saving: false, saveDisabled: false, onSave: () => {}, onClose: () => calls.push(['close'])});
      const layout = nodes(tree).find(x => x.type === 'layout'); layout.props.backSlot.props.onClick(); assert.equal(calls[0][0], dirty ? 'prompt' : 'close');
      nodes(layout.props.toolbarActions).find(x => x.type === 'button' && x.props.children?.props?.id?.endsWith('.cancel')).props.onClick(); assert.equal(calls.at(-1)[0], 'close');
    }
  });
  await check('PERSONAL-KEYBOARD-SAVE-RESPECTS-IME-AND-PENDING', () => {
    for (const saving of [false, true]) for (const disabled of [false, true]) for (const composing of [false, true]) {
      let saves = 0; const run = callback('personalization', '_i', s => s.startsWith('e=>{(e.metaKey||e.ctrlKey)'), {o: saving, s: disabled, u: () => saves++});
      run({metaKey: true, key: 'Enter', nativeEvent: {isComposing: composing}, preventDefault: () => {}}); assert.equal(saves, !saving && !disabled && !composing ? 1 : 0);
    }
  });
  await check('PERSONAL-MEMORY-RESET-AWAITS-LOCAL-CHRONICLE-FIRST', async () => {
    const f = memoryReset(); await f.run(); assert.deepEqual(f.calls.map(x => x[0]), ['chronicle', 'memory']); assert.deepEqual(f.calls[0][1], {scope: 'all', interval: null}); assert.equal(f.calls[1][1], 'owned-H'); assert.equal(f.calls[1][2], 'memory/reset');
  });
  await check('PERSONAL-MEMORY-RESET-FAILURE-STOPS-BACKEND-RESET', async () => {
    const f = memoryReset({fail: true}); await assert.rejects(f.run, /owned reset failure/); assert.deepEqual(f.calls.map(x => x[0]), ['chronicle']);
  });
  await check('PERSONAL-REMOTE-OR-UNAVAILABLE-CHRONICLE-USES-ONLY-HOST-RESET', async () => {
    for (const options of [{remote: true}, {unavailable: true}]) {const f = memoryReset(options); await f.run(); assert.deepEqual(f.calls.map(x => x[0]), ['memory']);}
  });
  await check('PERSONAL-TOOL-MEMORY-CHECKBOX-REVERSAL-AND-LEGACY-CLEAR', () => {
    for (const enabled of [true, false]) {
      const calls = [], env = {l: 'owned-logger', ie: {disableOnExternalContext: false}, _e: value => value,
        Cr: cfg => {assert.equal(cfg.selectedEnabled, !enabled); cfg.write();}, D: {mutateAsync: arg => calls.push(plain(arg))}};
      callback('personalization', 'Xr', s => s.startsWith('e=>{let t=!e;Cr('), env)(enabled);
      assert.deepEqual(calls[0].edits, [{keyPath: 'memories.disable_on_external_context', value: !enabled}, {keyPath: 'memories.no_memories_if_mcp_or_web_search', value: null}]);
    }
  });
  await check('PERSONAL-SYSTEM-MESSAGE-OPTIMISTIC-SNAPSHOT-AND-ROLLBACK', async () => {
    const calls = [], prior = {enabled: false, nickname: 'Owned'}, query = {cancelQueries: async x => calls.push(['cancel', plain(x)]), getQueryData: () => prior, setQueryData: (_, value) => calls.push(['cache', plain(value)])};
    const snapshot = await callback('personalization', 'Ma', s => s.startsWith('async e=>{await m.cancelQueries'), {m: query, N: ['owned', 'owned-A']})({enabled: true});
    assert.equal(snapshot, prior); assert.deepEqual(calls[1][1], {enabled: true, nickname: 'Owned'});
    callback('personalization', 'Ma', s => s.startsWith('(e,t,n)=>{m.setQueryData'), {m: query, N: ['owned', 'owned-A'], d: {get: () => ({danger: () => {}})}, ue: 'toast', p: formatter})(Error('owned'), {}, snapshot);
    assert.deepEqual(calls.at(-1)[1], prior);
  });
  await check('PERSONAL-PHOTO-UPLOAD-CAPTURES-ACCOUNT-KIND-AND-CURRENT-TAG', () => {
    const calls = [], file = {name: 'owned.png'}, run = callback('personalization', 'Ca', s => s.startsWith('e=>Zn(i,'), {i: 'owned-client', n: 'owned-A', r: 'self', g: {id: 'old'}, Zn: (...args) => calls.push(args)});
    run(file); assert.equal(calls[0][1].imageFile, file); assert.deepEqual({...calls[0][1], imageFile: 'owned'}, {accountId: 'owned-A', imageFile: 'owned', kind: 'self', imageTagId: 'old'});
  });
  await check('PERSONAL-PHOTO-DELETE-SELECTED-FACE-VERSUS-ALL-BODY', async () => {
    for (const body of [false, true]) {
      const calls = [], tags = [{id: 'one', kind: 'self'}, {id: 'two', kind: 'full_body_likeness'}, {id: 'three', kind: 'full_body_likeness'}];
      const env = {g: tags[body ? 1 : 0], v: body, d: tags, r: body ? 'full_body_likeness' : 'self', n: 'owned-A', Kn: n => ({queryKey: ['owned-images', n]}),
        a: {safeDelete: async (_, arg) => calls.push(['delete', plain(arg)])}, i: {queryClient: {cancelQueries: async () => calls.push(['cancel']), setQueryData: (_, update) => calls.push(['cache', plain(update(tags))])}}};
      await callback('personalization', 'Ca', s => s.startsWith('async()=>{let e=g==null'), env)();
      assert.equal(calls.filter(x => x[0] === 'delete').length, body ? 2 : 1); assert.equal(calls[0][1].additionalHeaders['ChatGPT-Account-ID'], 'owned-A'); assert.equal(calls.at(-1)[1].length, body ? 1 : 2);
    }
  });
  await check('PERSONAL-PHOTO-PARTIAL-DELETE-FAILURE-SKIPS-SUCCESS-CACHE-FILTER', async () => {
    const calls = [], tags = [{id: 'one', kind: 'full_body_likeness'}, {id: 'two', kind: 'full_body_likeness'}], env = {g: tags[0], v: true, d: tags, r: 'full_body_likeness', n: 'owned-A', Kn: () => ({queryKey: ['owned']}),
      a: {safeDelete: async (_, arg) => {calls.push('delete'); if (arg.parameters.path.image_tag_id === 'two') throw Error('owned partial failure');}}, i: {queryClient: {cancelQueries: () => calls.push('cancel'), setQueryData: () => calls.push('cache')}}};
    await assert.rejects(callback('personalization', 'Ca', s => s.startsWith('async()=>{let e=g==null'), env), /owned partial failure/); assert.deepEqual(calls, ['delete', 'delete']);
  });

  await check('MICRO-ROOT-REQUIRES-NATIVE-BRIDGE', () => {
    assert.equal(unit('codex-micro', 'ui', {Oi: memo, ue: {}, $: jsx, di: 'body'})(), null);
    const bridge = {owned: true}, tree = unit('codex-micro', 'ui', {Oi: memo, ue: {codexMicro: bridge}, $: jsx, di: 'body'})(); assert.equal(tree.props.codexMicro, bridge);
  });
  await check('MICRO-BRIGHTNESS-RANGE-AND-NUMERIC-CONVERSION', () => {
    const calls = [], tree = unit('codex-micro', 'fi', {Oi: memo, fe: () => formatter, X: {lightingBrightness: {id: 'brightness'}}, $: jsx, V: 'number'})({value: 50, onChange: value => calls.push(value)});
    const input = nodes(tree).find(x => x.type === 'input'); assert.deepEqual([input.props.min, input.props.max, input.props.step], [0, 100, 10]);
    input.props.onChange({currentTarget: {value: '70'}}); assert.deepEqual(calls, [70]);
  });
  await check('MICRO-SLOT-SUBMIT-PAYLOADS-AND-EMPTY-TEXT-GUARD', () => {
    for (const action of [undefined, {type: 'command', commandId: 'owned-command'}, {type: 'skill', skillName: 'Owned', skillPath: '/owned/SKILL.md'}, {type: 'composer-text', text: ''}, {type: 'composer-text', text: ' '}]) {
      const calls = [], run = callback('codex-micro', 'yi', s => s.startsWith('t=>{t.preventDefault(),(_?.type'), {_: action, l: value => calls.push(plain(value)), w: {id: 'OWNED'}, e: action?.type === 'command' ? {id: 'owned-command'} : null});
      run({preventDefault: () => {}}); assert.equal(calls.length, action?.type === 'composer-text' && action.text === '' ? 0 : 1);
      if (calls.length) {assert.equal(calls[0].keycapId, 'OWNED'); assert.equal(calls[0].commandId, action?.type === 'command' ? 'owned-command' : undefined); if (['skill', 'composer-text'].includes(action?.type)) assert.deepEqual(calls[0].action, action);}
    }
  });
  await check('MICRO-SLOT-CLOSE-WAITS-FOR-PREFERENCE-WRITE', async () => {
    const calls = []; let finish; const pending = new Promise(resolve => {finish = resolve;});
    const run = callback('codex-micro', 'di', s => s.startsWith('e=>{Be(a,je.layout,gn('), {a: 'owned-store', je: {layout: 'layout'}, A: {owned: true}, H: 'slot', gn: (...args) => {calls.push(['transform', ...args]); return 'next';}, Be: (...args) => {calls.push(['write', ...args]); return pending;}, ne: v => calls.push(['close', v])});
    run({keycapId: 'OWNED'}); assert.equal(calls.some(x => x[0] === 'close'), false); finish(); await Promise.resolve(); assert.equal(calls.at(-1)[0], 'close');
  });
  await check('MICRO-AGENT-ASSIGNMENT-CLOSES-SYNCHRONOUSLY', () => {
    const calls = [], run = callback('codex-micro', 'Jr', s => s.startsWith('function(e){Sn('), {Sn: (...args) => {calls.push(['write', ...args]); return new Promise(() => {});}, s: 'owned-store', n: 'AGENT1', o: v => calls.push(['close', v])});
    const target = {hostId: 'owned-H', threadKey: 'owned-T'}; run(target); assert.equal(calls[0][3], target); assert.deepEqual(calls.at(-1), ['close', false]); run(null); assert.equal(calls.at(-2)[3], null);
  });
  await check('MICRO-LAYOUT-CONFIRMATION-DOES-NOT-AWAIT-WRITE', () => {
    const calls = [], tree = unit('codex-micro', 'kr', {Ar: jsx, q: 'message', T: 'dialog', ee: 'form', Je: 'heading', ne: 'description', he: 'section', i: 'header', _e: 'footer', m: 'button'})({onClose: () => calls.push('close'), onConfirm: () => {calls.push('write'); return new Promise(() => {});}});
    nodes(tree).find(x => x.type === 'form').props.onSubmit({preventDefault: () => calls.push('prevent')}); assert.deepEqual(calls, ['prevent', 'write', 'close']);
  });
  await check('MICRO-REMOVE-RECHECKS-CURRENT-STORE-ELIGIBILITY', () => {
    for (const eligible of [true, false]) {let count = 0; callback('codex-micro', 'di', s => s === '()=>{a.get(Jt)&&cn(a)}', {a: {get: () => eligible}, Jt: 'eligible', cn: () => count++})(); assert.equal(count, eligible ? 1 : 0);}
  });
  await check('MICRO-ANALOG-AND-ENCODER-IMMEDIATE-LAYOUT-WRITES', () => {
    for (const [name, helper] of [['bn', 'analog'], ['fn', 'encoder']]) {
      const calls = [], env = {a: 'owned-store', je: {layout: 'layout'}, A: 'old', Be: (...args) => calls.push(['write', ...args])}; env[name] = (...args) => {calls.push([helper, ...args]); return 'next';};
      callback('codex-micro', 'di', s => s === `(e,t)=>{Be(a,je.layout,${name}(A,e,t))}`, env)('left', null); assert.deepEqual(calls.map(x => x[0]), [helper, 'write']);
    }
  });
  await check('MICRO-RECENT-CHAT-ASSIGNMENTS-RETAIN-HOST-IDENTITY', () => {
    const loaded = [{kind: 'local', hostId: 'owned-H', threadKey: 'old', updatedAt: 1, title: 'Old'}, {kind: 'remote', threadKey: 'new', updatedAt: 2, title: ' New '}, {kind: 'other', updatedAt: 3}];
    const result = unit('codex-micro', 'Hr', {Wr: {default: x => x}, mt: x => x.threadKey, Qe: () => {throw Error('unexpected search');}})({loadedResults: loaded, limit: 3, query: ''});
    assert.deepEqual(plain(result.map(x => x.assignment)), [{hostId: null, threadKey: 'new', title: 'New'}, {hostId: 'owned-H', threadKey: 'old', title: 'Old'}]);
  });
  await check('MICRO-KEYCAP-SEARCH-ALIASES-AND-SPLIT-MICROPHONE-SLOTS', () => {
    const matches = unit('codex-micro', 'Ei', {pn: e => e.aliases}); assert(matches({id: 'OWNED', aliases: ['Alias']}, ' ALI ')); assert.equal(matches({id: 'OWNED', aliases: []}, 'missing'), false);
    const label = unit('codex-micro', 'Di'); assert.equal(label({id: 'SPLIT'}), 'FORK'); assert.equal(label({id: 'BRCH'}), 'DRAFT');
    const slots = unit('codex-micro', 'li', {Pi: [{slotId: 'ONE'}, {slotId: 'ACT10_ACT11'}], Fi: [{slotId: 'ACT10'}, {slotId: 'ACT11'}]}); assert.equal(slots({separateMicrophoneKeys: true}).length, 3); assert.equal(slots({separateMicrophoneKeys: false}).length, 2);
  });
  const unique = [...new Map(used.map(r => [`${r.sourcePath}:${r.byteRange.start}:${r.byteRange.endExclusive}`, r])).values()];
  const result = {baselineId, method: 'exact-saved-frozen-functions-and-callbacks-in-owned-vm', sourceSelections: unique, cases,
    passed: cases.filter(x => x.passed).length, failed: cases.filter(x => !x.passed).length,
    productScenariosExecuted: 0, modelSubmissionsAdded: 0, originalClientRunsAdded: 0, realServiceCalls: 0, actualDeviceActions: 0,
    qualification: 'Synthetic identities, location parse/build, store/query/mutation/native/JSX substitutes. No target module bootstrap, React mount, original client, network, account mutations or hardware execution. Imported orchestration, validation, normalization, ranking, utility algorithms and durable receivers remain qualified interfaces.'};
  fs.writeFileSync(process.argv[2] ?? path.join(work, 'isolated-observations.json'), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
  console.log(JSON.stringify({passed: result.passed, failed: result.failed, selectedSourceRanges: unique.length, failures: cases.filter(x => !x.passed).map(x => ({id: x.id, error: x.error}))}));
  process.exitCode = result.failed ? 1 : 0;
})().catch(error => {console.error(error); process.exitCode = 1;});
