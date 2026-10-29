// Exact saved functions in synthetic React/store/controller fixtures.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto'), vm = require('node:vm');
const assert = require('node:assert/strict');
const [root, work, outputName = 'probe-attempt-01.json'] = process.argv.slice(2);
const source = JSON.parse(fs.readFileSync(path.join(work, 'branch-source.json')));
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
function unit(name) {
  const record = source.units.find(unit => unit.name === name);
  const bytes = fs.readFileSync(path.join(work, 'units', record.sourceFilename));
  assert.equal(hash(bytes), record.spanHash);
  return bytes.toString('utf8');
}
function fragment(name) { return source.fragments.find(item => item.id === name).expression; }
const results = [];
const plain = value => JSON.parse(JSON.stringify(value));
function check(id, owners, test) {
  try { test(); results.push({id, owners, status: 'passed'}); }
  catch (error) { results.push({id, owners, status: 'failed', error: String(error.stack || error)}); }
}
const jsx = {Fragment: 'Fragment', jsx: (type, props) => ({type, props}), jsxs: (type, props) => ({type, props})};
const cache = {c: count => Array(count).fill(Symbol.for('react.memo_cache_sentinel'))};
function treeNodes(root) {
  const nodes = [];
  function walk(value) {
    if (Array.isArray(value)) return value.forEach(walk);
    if (!value || typeof value !== 'object') return;
    if (value.type) nodes.push(value);
    walk(value.props?.children);
  }
  walk(root); return nodes;
}
function jRtFixture(mode, temporary, removeFooter = false) {
  const context = {
    Symbol, N9: cache, F9: jsx,
    $It: () => undefined, $Pt: () => undefined,
    VIt: () => ({isTemporaryChat: temporary, composerProps: {}, fileDropTarget: {kind: 'chatgpt', disabled: false}}),
    q: () => undefined, Da: () => false,
    P9: {useSyncExternalStore: (subscribe, snapshot) => snapshot()},
    FLt: 'FLt', iO: 'iO', mv: 'mv', IRt: () => false, MRt: () => {},
    NRt: 'NRt', ELt: 'ELt', l5: {Surface: 'surface'}, r7: 'drop-target', TRt: 'layout', hIt: 'home-layout', CFt: 'temporary-chat-footer',
  };
  vm.createContext(context);
  let text = unit('jRt');
  if (removeFooter) {
    const expression = fragment('jRt:chat-temporary-footer');
    assert.equal(text.split(expression).length, 2);
    text = text.replace(expression, 'null');
  }
  return vm.runInContext('(' + text + ')', context, {timeout: 1000})({homeComposerMode: mode});
}
for (const mode of [undefined, 'work', 'chat', 'unclassified-fixture']) {
  for (const temporary of [false, true]) {
    check('footer mode=' + mode + ' temporary=' + temporary, ['jRt'], () => {
      const tree = jRtFixture(mode, temporary);
      const nodes = treeNodes(tree);
      assert.equal(nodes.filter(node => node.type === 'temporary-chat-footer').length, mode === 'chat' && temporary ? 1 : 0);
      assert.equal(nodes.filter(node => node.type === 'NRt').length, 1);
      assert.equal(nodes.find(node => node.type === 'NRt').props.homeComposerMode, mode);
    });
  }
}
for (const mode of [undefined, 'work']) {
  for (const temporary of [false, true]) {
    check('derived footer omission preserves selected retained tree mode=' + mode + ' temporary=' + temporary, ['jRt'], () => {
      assert.deepEqual(plain(jRtFixture(mode, temporary, true)), plain(jRtFixture(mode, temporary)));
    });
  }
}
function suggestionFixture(mode, canSwitch = true, withController = true) {
  const effects = [], registrations = [], changes = [];
  const store = {get: key => key === 'ga' ? {} : key === 'UE' ? 'fixture draft' : undefined};
  const controller = withController ? {
    setSuggestionTriggers: (triggers, options) => effects.push({triggers, options}),
    cancelPendingSubmit: () => changes.push('cancelPendingSubmit'),
    getPersistedText: () => 'fixture draft',
  } : null;
  const context = {
    Symbol, URLSearchParams, Y9: cache, Z9: jsx,
    X9: {useState: value => [value, () => {}], useRef: value => ({current: value}), useLayoutEffect: effect => effect()},
    ir: () => store, ic: 'ic', J: 'J', gm: () => ({accountId: 'fixture-account', userId: 'fixture-user'}),
    ii: () => () => true, Ta: () => ({}), Da: () => true,
    q: key => key === 'oh' ? {status: 'loaded', structure: {}} : key === 'ga' ? {} : undefined,
    oh: 'oh', mv: 'mv', Azt: 'Azt', gne: 'gne', ga: 'ga', Qh: 'Qh', UE: 'UE',
    Q: key => key === 'Po' ? {isLoading: false, isCapable: false} : false,
    tzt: 'tzt', Po: 'Po', fp: () => ({formatMessage: value => value.id}), QO: () => () => {},
    Dt: () => ({hash: '', pathname: '/', search: '', state: null}), NO: () => null, Ol: () => () => {},
    ezt: () => false, Wg: search => new URLSearchParams(search).get('temporary-chat') === 'true', kzt: 'chat-triggers', Q9: 'retained-triggers',
    py: (id, callback, options) => registrations.push({id, callback, options}),
    HFt: 'header', M9: 'M9', vFt: 'mode-picker', H5: 'upgrade', DFt: 'chat-seat-prompt',
    Qx: () => {},
    Em: () => {}, Xi: 'Xi', BRt: 'BRt',
    RRt: {CHATGPT_CHAT_MODE_PICKER_SURFACE_TOGGLE: 'surface'},
    zRt: {CHATGPT_CHAT_MODE_PICKER_UI_EVENT_TYPE_MODE_CLICKED: 'clicked'},
    V9: {CHATGPT_CHAT_MODE_PICKER_MODE_WORK: 'work', CHATGPT_CHAT_MODE_PICKER_MODE_CHAT: 'chat'},
    gk: 'gk', XT: 'XT', GE: 'GE', wm: 'wm', Gg: 'Gg',
    $C: () => {}, QRt: () => {}, Qb: () => {}, LRt: () => {},
  };
  vm.createContext(context);
  const tree = vm.runInContext('(' + unit('Ezt') + ')', context, {timeout: 1000})({
    composerController: controller, mode, canSwitchMode: canSwitch,
    workModeAllowed: true, workModeLoading: false,
    onModeChange: (next, trigger) => changes.push(['onModeChange', next, trigger]),
  });
  return {tree, effects, registrations, changes};
}
for (const mode of ['chat', 'work', undefined]) {
  check('shared entry suggestion policy mode=' + mode, ['Ezt'], () => {
    const fixture = suggestionFixture(mode);
    assert.equal(fixture.effects.length, 1);
    const effect = fixture.effects[0];
    assert.equal(effect.triggers, mode === 'chat' ? 'chat-triggers' : 'retained-triggers');
    assert.equal(effect.options.enableInlineSystemHints, mode === 'chat');
    assert.equal(effect.options.variant, mode === 'chat' ? 'chatgpt' : undefined);
    assert.equal(treeNodes(fixture.tree).find(node => node.type === 'M9').props.homeComposerMode, mode);
  });
}
check('shared entry without controller has no suggestion effect', ['Ezt'], () => {
  assert.equal(suggestionFixture('work', true, false).effects.length, 0);
});
for (const mode of ['work', 'chat']) {
  for (const canSwitch of [false, true]) {
    check('Chat shortcut mode=' + mode + ' canSwitch=' + canSwitch, ['Ezt'], () => {
      const fixture = suggestionFixture(mode, canSwitch);
      const registration = fixture.registrations.find(item => item.id === 'switchToMode1');
      assert.equal(registration.options.enabled, canSwitch);
      assert(fixture.registrations.some(item => item.id === 'switchToMode2'));
      assert(fixture.registrations.some(item => item.id === 'newTask'));
      if (mode === 'work' && canSwitch) {
        registration.callback();
        assert.deepEqual(fixture.changes.at(-1), ['onModeChange', 'chat', 'mode_picker']);
      }
    });
  }
}
for (const withController of [false, true]) {
  check('Codex entry retains M9 and disables Chat hints controller=' + withController, ['Tzt'], () => {
    const effects = [];
    const controller = withController ? {setSuggestionTriggers: (triggers, options) => effects.push({triggers, options})} : null;
    const context = {Symbol, Y9: cache, Z9: jsx, X9: {useLayoutEffect: effect => effect()}, q: () => ({}), ga: 'ga', Qh: 'Qh', Q9: 'retained-triggers', HFt: 'header', M9: 'M9'};
    vm.createContext(context);
    const tree = vm.runInContext('(' + unit('Tzt') + ')', context, {timeout: 1000})({composerController: controller, preservePendingInput: true});
    const composer = treeNodes(tree).find(node => node.type === 'M9');
    assert.equal(composer.props.isCodexHome, true);
    assert.equal(composer.props.preservePendingInput, true);
    assert.equal(effects.length, withController ? 1 : 0);
    if (withController) {
      assert.equal(effects[0].triggers, 'retained-triggers');
      assert.equal(effects[0].options.enableInlineSystemHints, false);
      assert.equal(effects[0].options.variant, undefined);
    }
  });
}
for (const mode of ['work', 'chat', undefined]) {
  check('initial suggestion options mode=' + mode, ['wzt'], () => {
    const context = {W: mode}; vm.createContext(context);
    const result = vm.runInContext('(()=>{let ' + fragment('wzt:chat-inline-enabled') + ';let ' + fragment('wzt:chat-inline-variant') + ';return {enabled:ue,variant:de}})()', context);
    assert.equal(result.enabled, mode === 'chat');
    assert.equal(result.variant, mode === 'chat' ? 'chatgpt' : undefined);
  });
}
const output = {
  baselineId: source.baselineId, recordedAtUtc: new Date().toISOString(),
  sourceContractsSha256: hash(fs.readFileSync(path.join(work, 'branch-source.json'))), scriptSha256: hash(fs.readFileSync(__filename)),
  results, counts: {cases: results.length, passed: results.filter(item => item.status === 'passed').length, failed: results.filter(item => item.status === 'failed').length},
  limits: ['Original selected functions and two exact local declarators use synthetic dependency values; no actual React mount or provider/service effects.', 'Four explicitly labeled derived-footer cases replace only that conditional with null in VM memory and compare synthetic retained output trees; they do not establish complete-client deletion safety.', 'No original module bootstrap, account data, setting write, model submission or product scenario pass.'],
};
fs.writeFileSync(path.join(work, outputName), JSON.stringify(output, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({counts: output.counts, failures: results.filter(item => item.status === 'failed')}));
process.exitCode = output.counts.failed ? 1 : 0;
