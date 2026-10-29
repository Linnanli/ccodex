// Offline replay of selected, hash-checked first-party source; no Electron or SDK loads.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {isDeepStrictEqual} = require('node:util');
const [work, output] = process.argv.slice(2);
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const loaded = {};
function unit(family, label) {
  const folder = path.join(work, family);
  const contract = loaded[family] ??= JSON.parse(fs.readFileSync(path.join(folder, 'source-contracts.json')));
  const item = contract.units.find(x => x.label === label);
  if (!item) throw Error('Missing selected unit ' + label);
  const bytes = fs.readFileSync(path.join(folder, item.file));
  assert.equal(hash(bytes), item.spanHash);
  return bytes.toString('utf8');
}
const variables = ['At', 'e$', 't$', 'lze', 'uze'];
const functions = ['n$', 'dze', 'fze', 'pze', 'r$'];
const mainCode = variables.map(n => 'var ' + unit('main', 'binding-' + n) + ';').join('\n') + '\n' + functions.map(n => unit('main', 'binding-' + n)).join('\n');
const initialCode = ['bZs', 'xZs', 'qhi'].map(n => unit('initial', 'binding-' + n)).join('\n');
function mainFixture(platform = 'win32') {
  const calls = [], values = new Map(), app = {
    setRuntimeFeatures(value) { calls.push(['features', {...value}]); },
    setLegacyChromePolicyFallbackEnabled(value) { calls.push(['legacy', value]); },
    isRuntimeFeatureEnabled(value) { return value === 'supported'; }
  };
  const state = {get: key => values.get(key), set: (key, v) => values.set(key, v), delete: key => values.delete(key)};
  const context = vm.createContext({_: {app}, l: {Pt: class {}, j: 'owner'}, process: {platform}, Error});
  vm.runInContext(mainCode + '\nglobalThis.api={uze,dze,fze,pze,r$,keys:()=>[...At],cached:()=>({...e$})};', context);
  return {app, calls, values, state, ...context.api};
}
function rendererFixture() {
  const calls = [], provider = {
    async setRuntimeFeatures(v) { calls.push(['features', {...v}]); },
    async enableLegacyChromePolicyFallback(v) { calls.push(['legacy', v]); }
  };
  const Pd = {owlFeatures: provider};
  const jsonEqual = (a, b) => isDeepStrictEqual(JSON.parse(JSON.stringify(a)), JSON.parse(JSON.stringify(b)));
  const context = vm.createContext({Pd, Yhi: {default: jsonEqual}, Jhi: {_getFullUserHash: () => 'synthetic-user-hash'}});
  vm.runInContext('var SZs=[["3646210497","OwlOpenAIGoLinks"],["3217069062","OwlRemoteSearchSuggestions"]],CZs=new WeakMap;\n' + initialCode + '\nglobalThis.api={bZs,xZs,qhi,cached:e=>CZs.has(e)};', context);
  const user = {userID: 'synthetic-user', custom: {auth_method: 'chatgpt', workspace_id: 'synthetic-account'}, customIDs: {account_id: 'synthetic-account', workspace_id: 'synthetic-account', stableID: 'synthetic-stable'}};
  let values = {user: {...user, custom: {...user.custom, account_creation_time: 1}}};
  const gates = {
    '3646210497': {value: true, details: {reason: 'LocalOverride'}},
    '3217069062': {value: false, details: {reason: 'Network:Recognized'}},
    '3384989494': {value: true, details: {reason: 'Network:Recognized'}}
  };
  const client = {getContext: () => ({user, values}), getFeatureGate: id => gates[id], dataAdapter: {getDataSync: () => ({fullUserHash: 'synthetic-user-hash', data: JSON.stringify(values)})}};
  return {Pd, calls, provider, user, gates, client, setValues: v => {values = v;}, ...context.api};
}
const cases = [];
async function check(id, claim, body) {
  try { await body(); cases.push({id, claim, status: 'passed'}); }
  catch (error) { cases.push({id, claim, status: 'failed', error: String(error.stack)}); }
}
(async () => {
  await check('RFP-01', 'Two allowed boolean keys merge across service instances; unknown/nonboolean input is ignored.', async () => {
    const f = mainFixture(), a = new f.uze(f.state), b = new f.uze(f.state);
    assert.deepEqual([...f.keys()], ['OwlOpenAIGoLinks', 'OwlRemoteSearchSuggestions']);
    await a.setRuntimeFeatures({unknown: true, OwlOpenAIGoLinks: 'true'}); assert.equal(f.calls.length, 0);
    await a.setRuntimeFeatures({OwlOpenAIGoLinks: true});
    await b.setRuntimeFeatures({OwlRemoteSearchSuggestions: false, unknown: true});
    assert.deepEqual(f.calls.at(-1), ['features', {OwlOpenAIGoLinks: true, OwlRemoteSearchSuggestions: false}]);
  });
  await check('RFP-02', 'Setter failure preserves previous cache, whereas reset failure has already cleared it.', async () => {
    const f = mainFixture(), service = new f.uze(f.state);
    await service.setRuntimeFeatures({OwlOpenAIGoLinks: true});
    f.app.setRuntimeFeatures = () => {throw Error('synthetic-provider-failure');};
    await assert.rejects(service.setRuntimeFeatures({OwlOpenAIGoLinks: false}), /synthetic-provider-failure/);
    assert.deepEqual({...f.cached()}, {OwlOpenAIGoLinks: true});
    assert.throws(() => f.dze(), /synthetic-provider-failure/); assert.deepEqual({...f.cached()}, {});
  });
  await check('RFP-03', 'Only the specified unsupported-feature Error is converted to false; missing methods propagate.', async () => {
    const f = mainFixture(), service = new f.uze(f.state);
    f.app.isRuntimeFeatureEnabled = () => {throw Error('Unsupported Owl feature: synthetic');};
    assert.equal(await service.isOwlFeatureEnabled('x'), false);
    f.app.isRuntimeFeatureEnabled = () => {throw Error('other');};
    await assert.rejects(service.isOwlFeatureEnabled('x'), /other/);
    delete f.app.isRuntimeFeatureEnabled;
    await assert.rejects(service.isOwlFeatureEnabled('x'), /not a function/);
  });
  await check('RFP-04', 'Windows enables only for matching account, then stores account/user owner.', async () => {
    const f = mainFixture(), service = new f.uze(f.state, async () => ({accountId: 'a', userId: 'u'}));
    await service.enableLegacyChromePolicyFallback('a');
    assert.deepEqual(f.calls, [['legacy', true]]); assert.deepEqual({...f.values.get('owner')}, {accountId: 'a', userId: 'u'});
    await service.enableLegacyChromePolicyFallback('b'); assert.equal(f.calls.length, 1);
  });
  await check('RFP-05', 'Empty account/non-Windows avoid auth lookup; absent native capability prevents activation.', async () => {
    for (const platform of ['darwin', 'linux']) {
      const f = mainFixture(platform), service = new f.uze(f.state, () => {throw Error('must-not-lookup');});
      await service.enableLegacyChromePolicyFallback('a'); assert.equal(f.calls.length, 0);
    }
    const f = mainFixture(), service = new f.uze(f.state, () => {throw Error('must-not-lookup');});
    await service.enableLegacyChromePolicyFallback(''); delete f.app.setLegacyChromePolicyFallbackEnabled;
    await new f.uze(f.state, async () => ({accountId: 'a', userId: 'u'})).enableLegacyChromePolicyFallback('a');
    assert.equal(f.calls.length, 0);
  });
  await check('RFP-06', 'Generation invalidates an in-flight enable after clear.', async () => {
    const f = mainFixture(); let release;
    const service = new f.uze(f.state, () => new Promise(resolve => {release = resolve;}));
    const pending = service.enableLegacyChromePolicyFallback('a'); f.fze(f.state);
    release({accountId: 'a', userId: 'u'}); await pending;
    assert.deepEqual(f.calls, [['legacy', false]]); assert.equal(f.values.has('owner'), false);
  });
  await check('RFP-07', 'Owner match preserves policy; user/account mismatch deletes owner and disables Windows policy.', async () => {
    const f = mainFixture(); f.values.set('owner', {accountId: 'a', userId: 'u'});
    f.pze(f.state, {accountId: 'a', userId: 'u'}); assert.equal(f.calls.length, 0);
    f.pze(f.state, {accountId: 'a', userId: 'other'});
    assert.equal(f.values.has('owner'), false); assert.deepEqual(f.calls, [['legacy', false]]);
  });
  await check('RFP-08', 'Renderer skips dispatch until Ready or when provider is absent.', async () => {
    const f = rendererFixture(); await f.bZs(f.client, 'Loading'); assert.equal(f.calls.length, 0);
    f.Pd.owlFeatures = undefined; await f.bZs(f.client, 'Ready'); assert.equal(f.calls.length, 0);
  });
  await check('RFP-09', 'Renderer maps local/recognized gates to exact keys and accepts recognized legacy policy.', async () => {
    const f = rendererFixture(); await f.bZs(f.client, 'Ready');
    assert.deepEqual(f.calls, [['legacy', 'synthetic-account'], ['features', {OwlOpenAIGoLinks: true, OwlRemoteSearchSuggestions: false}]]);
  });
  await check('RFP-10', 'Unrecognized feature gates are omitted; LocalOverride alone does not enable legacy policy.', async () => {
    const f = rendererFixture(); f.gates['3646210497'].details.reason = 'Network:Unrecognized';
    f.gates['3217069062'].details.reason = 'Network:Unrecognized'; f.gates['3384989494'].details.reason = 'LocalOverride';
    await f.bZs(f.client, 'Ready'); assert.equal(f.calls.length, 0);
  });
  await check('RFP-11', 'Invalid auth/account-creation input blocks legacy activation but not independent runtime-feature dispatch.', async () => {
    const f = rendererFixture(); f.setValues({user: {...f.user, custom: {...f.user.custom, account_creation_time: Infinity}}});
    await f.bZs(f.client, 'Ready'); assert.equal(f.calls.some(x => x[0] === 'legacy'), false);
    assert.equal(f.calls.some(x => x[0] === 'features'), true);
    f.user.custom.auth_method = 'apiKey'; await f.xZs(f.client, f.provider); assert.equal(f.cached(f.client), false);
  });
  await check('RFP-12', 'Cached identity permits missing evaluated user, but changed identity invalidates the cache.', async () => {
    const f = rendererFixture(); await f.xZs(f.client, f.provider); assert.equal(f.cached(f.client), true);
    f.setValues({}); await f.xZs(f.client, f.provider); assert.equal(f.calls.length, 2);
    f.user.customIDs.stableID = 'synthetic-other-stable'; await f.xZs(f.client, f.provider);
    assert.equal(f.cached(f.client), false); assert.equal(f.calls.length, 2);
  });
  const result = {cases, passed: cases.filter(x => x.status === 'passed').length, failed: cases.filter(x => x.status === 'failed').length,
    qualification: 'Selected first-party source with synthetic RPC base, state, Electron methods, gate client, equality/hash helpers; not original SDK/native behavior or product acceptance.',
    targetModulesLoaded: 0, originalClientRunsAdded: 0, modelSubmissionsAdded: 0, productScenarioPassesAdded: 0};
  fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
  console.log(JSON.stringify(result));
  if (result.failed) process.exitCode = 1;
})();
