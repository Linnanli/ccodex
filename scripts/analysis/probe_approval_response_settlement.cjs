// Evaluate only selected, hash-checked function bodies with synthetic dependencies.
// This is a source-contract probe, not a desktop/backend acceptance run.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const vm = require('node:vm');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '../..');
const baseline = 'codex-26.1007.30912-c5b273322a83';
const work = path.join(root, '.analysis-local/approval-response-settlement-work');
const output = path.join(work, 'probe');
if (fs.existsSync(output)) throw Error('Preserve the previous probe output');
fs.mkdirSync(output, {recursive: true});
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const pins = [];
function input(relative) {
  const bytes = fs.readFileSync(path.join(root, relative));
  pins.push({path: relative, bytes: bytes.length, sha256: sha(bytes)});
  return JSON.parse(bytes);
}
const helpers = input('.analysis-local/approval-response-settlement-work/helpers/source-contracts.json');
const approval = input(`analysis/${baseline}/approval-entry-contracts.json`);
const providers = input('.analysis-local/submission-host-instance-work/shared-host-scope-bindings.json');
const manager = input('.analysis-local/task-composer-entry-work/local-manager-complete.json');
const frozen = path.join(root, '.analysis-local/baselines', baseline, 'extracted/webview/assets/app-shared-8bd9d0399038.js');
const bytes = fs.readFileSync(frozen);
assert.equal(sha(bytes), helpers.sourceHash);
assert.equal(bytes.length, helpers.sourceBytes);
const units = [];
const bodies = {};
function select(name, range, expected, origin, nodeType) {
  const body = bytes.subarray(range.start, range.endExclusive);
  assert.equal(sha(body), expected, name);
  const sourceFilename = `${String(units.length + 1).padStart(3, '0')}-${name}.txt`;
  fs.writeFileSync(path.join(output, sourceFilename), body, {flag: 'wx'});
  units.push({name, sourcePath: helpers.sourcePath, sourceHash: helpers.sourceHash,
    byteRange: range, spanSha256: expected, nodeType, origin, sourceFilename});
  bodies[name] = body.toString('utf8');
}
for (const [index, unit] of helpers.units.entries()) {
  if (unit.name === 'KI') continue; // Provider selection was already analyzed.
  select(unit.name, unit.byteRange, unit.spanHash, {input: pins[0].path, jsonPointer: `/units/${index}`}, unit.nodeType);
}
for (const name of ['V8t', 'H8t', 'U8t', 'sB', 'zB', 'Km', 'rp']) {
  const index = helpers.programBindingUses.findIndex(use => use.name === name);
  const binding = helpers.programBindingUses[index].binding;
  assert.equal(binding.scopeKind, 'Program');
  assert.equal(binding.definitions.length, 1);
  const unit = binding.definitions[0].declaration;
  select(name, unit.byteRange, unit.spanHash,
    {input: pins[0].path, jsonPointer: `/programBindingUses/${index}/binding/definitions/0/declaration`}, unit.nodeType);
}
for (const name of ['L7t', 'Z7t', 'uV', 'B8t', 'G7t', 'jj']) {
  const index = approval.selectedUnits.findIndex(unit => unit.local === name);
  const unit = approval.selectedUnits[index];
  select(name, {start: unit.locator.start, endExclusive: unit.locator.endExclusive}, unit.spanSha256,
    {input: pins[1].path, jsonPointer: `/selectedUnits/${index}`}, unit.nodeType);
}
const factoryIndex = providers.completeFunctions.findIndex(unit => unit.name === 'Sii');
const factory = providers.completeFunctions[factoryIndex];
select('Sii', factory.byteRange, factory.spanSha256,
  {input: pins[2].path, jsonPointer: `/completeFunctions/${factoryIndex}`}, factory.nodeType);
for (const name of ['constructor', 'getApprovalActionContext', 'replyWithMcpServerElicitationResponse']) {
  const index = manager.classMembers.findIndex(unit => unit.name === name);
  const unit = manager.classMembers[index];
  select(`Dfn-${name}`, unit.byteRange, unit.spanSha256,
    {input: pins[3].path, jsonPointer: `/classMembers/${index}`}, unit.nodeType);
}

// The original Sii Program binding is reused. Parsing its complete saved body
// selects the actual Dfn construction argument, without evaluating the factory.
const parserPath = path.join(root, '.analysis-local/global-state-storage-work/tooling/node_modules/@babel/parser/lib/index.js');
const parser = require(parserPath);
const ast = parser.parse(bodies.Sii, {sourceType: 'script'});
const senderCandidates = [];
function walk(node) {
  if (!node || typeof node !== 'object') return;
  if (node.type === 'NewExpression' && node.callee.type === 'Identifier' && node.callee.name === 'Dfn') {
    assert.equal(node.arguments[0].type, 'ObjectExpression');
    for (const property of node.arguments[0].properties) {
      if (property.type === 'ObjectMethod' && property.key.name === 'sendAppServerResponse') senderCandidates.push(property);
    }
  }
  for (const [key, value] of Object.entries(node)) {
    if (['loc', 'extra', 'comments'].includes(key)) continue;
    if (Array.isArray(value)) value.forEach(walk);
    else if (value && typeof value.type === 'string') walk(value);
  }
}
walk(ast.program);
assert.equal(senderCandidates.length, 1);
const sender = senderCandidates[0];
const factoryText = bodies.Sii;
const senderRange = {
  start: factory.byteRange.start + Buffer.byteLength(factoryText.slice(0, sender.start)),
  endExclusive: factory.byteRange.start + Buffer.byteLength(factoryText.slice(0, sender.end))
};
select('Sii-sendAppServerResponse', senderRange, sha(bytes.subarray(senderRange.start, senderRange.endExclusive)),
  {input: pins[2].path, jsonPointer: `/completeFunctions/${factoryIndex}`, selection: 'Dfn constructor argument ObjectMethod in complete saved factory AST'}, sender.type);

function evaluate(names, injected = {}) {
  const context = vm.createContext({...injected});
  const declarations = names.map(name => bodies[name]).join('\n');
  return vm.runInContext(`${declarations}\n({${names.join(',')}})`, context, {timeout: 1000});
}
function logger(events) {
  return {info: (...args) => events.push(['info', ...args]), error: (...args) => events.push(['error', ...args])};
}
const response = {action: 'accept'};
const request = (id, params = {}) => ({id, method: 'mcpServer/elicitation/request', params: {mode: 'form', turnId: 'turn', ...params}});
function fixture(overrides = {}) {
  const events = [];
  const requests = [request('r1')];
  const api = {
    logger: logger(events),
    getConversationRequests: () => requests,
    isMcpServerElicitationApprovalSafe: () => true,
    getStreamRole: () => ({role: 'leader'}),
    getEquivalentConnectorAuthRequests: selected => [selected],
    dispatchAppServerResponse: (...args) => events.push(['send', ...args]),
    applyMcpServerElicitationResponse: (...args) => events.push(['apply', ...args]),
    discardMcpServerElicitation: (...args) => events.push(['discard', ...args]),
    ...overrides
  };
  const fns = evaluate(['L7t', 'uV', 'jj'], {dV: (...args) => events.push(['forward-error', ...args])});
  return {events, requests, api, reply: () => fns.L7t(api, 'conversation', 'r1', response), fns};
}
const cases = [];
async function test(id, claim, run) {
  await run();
  cases.push({id, claim, passed: true, verificationKind: 'isolated-exact-source-with-synthetic-boundaries'});
}

(async () => {
  await test('AR-01', 'Missing request returns undefined without send or state effects.', () => {
    const f = fixture({getConversationRequests: () => []});
    assert.equal(f.reply(), undefined); assert.equal(f.events.length, 0);
  });
  await test('AR-02', 'Unexpected method logs and returns without sending.', () => {
    const f = fixture({getConversationRequests: () => [{...request('r1'), method: 'other'}]});
    f.reply(); assert.deepEqual(f.events.map(e => e[0]), ['error']);
  });
  await test('AR-03', 'User-verification accept is ignored on this reply path.', () => {
    const f = fixture({getConversationRequests: () => [request('r1', {mode: 'openai/userVerification'})]});
    f.reply(); assert.equal(f.events.length, 0);
  });
  await test('AR-04', 'Unsafe accept throws before sending or changing state.', () => {
    const f = fixture({isMcpServerElicitationApprovalSafe: () => false});
    assert.throws(f.reply, /Unsafe MCP/); assert.equal(f.events.length, 0);
  });
  await test('AR-05', 'Decline bypasses the accept-only safety check and applies its response.', () => {
    const f = fixture({isMcpServerElicitationApprovalSafe: () => {throw Error('must not run');}});
    assert.equal(f.fns.L7t(f.api, 'conversation', 'r1', {action: 'decline'}), undefined);
    assert.deepEqual(f.events.filter(e => ['send', 'apply'].includes(e[0])).map(e => e[0]), ['send', 'apply']);
  });
  await test('AR-06', 'Follower returns immediately; pending forwarding has no local send or state effects.', async () => {
    let reject;
    const pending = new Promise((resolve, failure) => {reject = failure;});
    const forwarded = [];
    const f = fixture({getStreamRole: () => ({role: 'follower', ownerClientId: 'owner'}),
      forwardFollowerMcpElicitation: (...args) => {forwarded.push(args); return pending;}});
    assert.equal(f.reply(), undefined);
    assert.deepEqual(forwarded, [['conversation', 'r1', response, 'owner']]);
    assert.equal(f.events.length, 0);
    reject(Error('synthetic forwarding failure')); await pending.catch(() => {}); await Promise.resolve();
    assert.deepEqual(f.events.map(e => e[0]), ['forward-error']);
  });
  await test('AR-07', 'Equivalence batch validates every accept before the first dispatch.', () => {
    const f = fixture({getEquivalentConnectorAuthRequests: () => [request('r1'), request('r2', {unsafe: true})],
      isMcpServerElicitationApprovalSafe: params => !params.unsafe});
    assert.throws(f.reply, /Unsafe MCP/); assert.equal(f.events.length, 0);
  });
  await test('AR-08', 'Equivalent requests send sequentially; selected request applies and others discard.', () => {
    const f = fixture({getEquivalentConnectorAuthRequests: () => [request('r1'), request('r2')]});
    f.reply();
    assert.deepEqual(f.events.filter(e => e[0] !== 'info').map(e => [e[0], e[0] === 'send' ? e[2].id : e[2]]),
      [['send', 'r1'], ['apply', 'r1'], ['send', 'r2'], ['discard', 'r2']]);
  });
  await test('AR-09', 'A later synchronous send failure leaves the earlier request transition applied.', () => {
    const sent = [];
    const f = fixture({getEquivalentConnectorAuthRequests: () => [request('r1'), request('r2')],
      dispatchAppServerResponse: (method, payload) => {sent.push(payload.id); if (payload.id === 'r2') throw Error('send failed');}});
    assert.throws(f.reply, /send failed/); assert.deepEqual(sent, ['r1', 'r2']);
    assert.deepEqual(f.events.filter(e => ['apply', 'discard'].includes(e[0])).map(e => e[0]), ['apply']);
  });
  await test('AR-10', 'A returned pending sender Promise is not awaited before state application.', () => {
    const never = new Promise(() => {});
    const f = fixture({dispatchAppServerResponse: () => never});
    assert.equal(f.reply(), undefined); assert.equal(f.events.filter(e => e[0] === 'apply').length, 1);
  });
  await test('AR-11', 'An asynchronously rejected sender is not converted into a reply rejection or rollback.', async () => {
    const failure = Promise.reject(Error('synthetic async send failure'));
    const observed = failure.catch(error => error.message);
    const f = fixture({dispatchAppServerResponse: () => failure});
    assert.equal(f.reply(), undefined); assert.equal(f.events.filter(e => e[0] === 'apply').length, 1);
    assert.equal(await observed, 'synthetic async send failure');
  });
  function senderWith(injected) {
    return vm.runInNewContext(`({${bodies['Sii-sendAppServerResponse']}}).sendAppServerResponse`, injected, {timeout: 1000});
  }
  await test('AR-12', 'Actual factory sender discards the Pvn return value for MCP elicitation responses.', () => {
    const calls = [], dispatch = () => {};
    const send = senderWith({t: 'host', a: dispatch, Pvn: value => {calls.push(value); return new Promise(() => {});}});
    const payload = {id: 'r1', result: response};
    assert.equal(send('mcpServer/elicitation/request', payload, 'conversation'), undefined);
    assert.equal(calls.length, 1); assert.equal(calls[0].dispatchMessageFromView, dispatch);
    assert.equal(calls[0].hostId, 'host'); assert.equal(calls[0].response, payload);
    assert.equal(calls[0].threadId, 'conversation');
  });
  await test('AR-13', 'Actual factory sender propagates synchronous downstream throws.', () => {
    const send = senderWith({t: 'host', a: () => {}, Pvn: () => {throw Error('downstream throw');}});
    assert.throws(() => send('mcpServer/elicitation/request', {}, 'conversation'), /downstream throw/);
  });
  await test('AR-14', 'The currentTime special branch dispatches mcp-response and returns undefined.', () => {
    const calls = [];
    const send = senderWith({t: 'host', a: (...args) => calls.push(args), Pvn: () => {throw Error('wrong branch');}});
    assert.equal(send('currentTime/read', {id: 'clock'}, 'conversation'), undefined);
    assert.equal(calls[0][0], 'mcp-response'); assert.equal(calls[0][1].hostId, 'host');
  });
  const projectionCalls = [];
  const stateFns = evaluate(['Z7t', 'z7t', 'q7t', 'U7t', 'cB', 'sB', 'zB', 'Km', 'rp'], {
    V7t: 'synthetic-plan-method',
    // Turn lookup and draft-array recognition are explicit synthetic boundaries.
    Z4t: (conversation, turnId, logging, options) => {
      projectionCalls.push(options);
      const turn = conversation.turns.find(turn => turn.id === turnId);
      return turn ? {turn} : null;
    }, qf: () => false, np: value => value,
    G7t: selected => [selected], B8t: () => true
  });
  function stateContext(conversation, extra = {}) {
    return stateFns.Z7t({logger: logger([]), hostId: 'host', conversations: new Map([['conversation', conversation]]),
      getStreamRole: () => ({role: 'leader'}),
      updateConversationState: (id, update) => {assert.equal(id, 'conversation'); update(conversation);}, ...extra});
  }
  await test('AR-15', 'Context forwarding awaits its IPC result and turns error envelopes into rejection.', async () => {
    const calls = [];
    const api = stateContext({requests: [], turns: []}, {ipcBridge: {request: async (...args) => {
      calls.push(args); return {resultType: 'error', error: 'owner rejected'};
    }}});
    await assert.rejects(api.forwardFollowerMcpElicitation('conversation', 'r1', response, 'owner'), /owner rejected/);
    assert.equal(calls[0][0], 'thread-follower-submit-mcp-server-elicitation-response');
    assert.equal(calls[0][1].conversationId, 'conversation'); assert.equal(calls[0][2].targetClientId, 'owner');
  });
  await test('AR-16', 'Missing IPC bridge rejects forwarding; it cannot acknowledge owner delivery.', async () => {
    const api = stateContext({requests: [], turns: []});
    await assert.rejects(api.forwardFollowerMcpElicitation('conversation', 'r1', response, 'owner'), /unavailable/);
  });
  await test('AR-17', 'Apply replaces the existing projected item and removes only its pending request.', () => {
    const conversation = {requests: [request('r1'), request('r2')], turns: [{id: 'turn', items: [{id: 'mcp-server-elicitation-r1', old: true}, {id: 'other'}]}]};
    stateContext(conversation).applyMcpServerElicitationResponse('conversation', 'r1', request('r1').params, 'accept');
    assert.deepEqual(conversation.requests.map(r => r.id), ['r2']);
    const item = conversation.turns[0].items[0];
    assert.equal(item.completed, true); assert.equal(item.action, 'accept'); assert.equal(item.old, undefined);
    assert.equal(conversation.turns[0].items.length, 2); assert.equal(projectionCalls.at(-1).synthesizeMissingTurn, false);
  });
  await test('AR-18', 'Missing turn still removes the request without synthesizing a turn.', () => {
    const conversation = {requests: [request('r1')], turns: []};
    stateContext(conversation).applyMcpServerElicitationResponse('conversation', 'r1', request('r1').params, 'accept');
    assert.equal(conversation.requests.length, 0); assert.equal(conversation.turns.length, 0);
    assert.equal(projectionCalls.at(-1).synthesizeMissingTurn, false);
  });
  await test('AR-19', 'Empty turn ID removes the request without even invoking the turn lookup.', () => {
    const before = projectionCalls.length;
    const conversation = {requests: [request('r1')], turns: []};
    stateContext(conversation).applyMcpServerElicitationResponse('conversation', 'r1', {turnId: ''}, 'decline');
    assert.equal(conversation.requests.length, 0); assert.equal(projectionCalls.length, before);
  });
  await test('AR-20', 'User-verification projection clears its challenge in the projected params.', () => {
    const params = {mode: 'openai/userVerification', turnId: 'turn', challenge: 'synthetic-secret'};
    const item = stateFns.U7t('r1', params, true, 'decline');
    assert.equal(item.params.challenge, ''); assert.equal(params.challenge, 'synthetic-secret');
    assert.equal(stateFns.U7t('r1', {turnId: null}, true, 'decline'), null);
  });
  await test('AR-21', 'Discard removes only the matching elicitation item and matching pending request.', () => {
    const conversation = {requests: [request('r1'), request('r2')], turns: [{id: 'turn', items: [
      {id: 'one', type: 'mcpServerElicitation', requestId: 'r1'},
      {id: 'two', type: 'mcpServerElicitation', requestId: 'r2'},
      {id: 'three', type: 'message', requestId: 'r1'}, {id: 'four', type: 'mcpServerElicitation'}]}]};
    stateContext(conversation).discardMcpServerElicitation('conversation', 'r1', 'turn');
    assert.deepEqual(conversation.turns[0].items.map(item => item.id), ['two', 'three', 'four']);
    assert.deepEqual(conversation.requests.map(r => r.id), ['r2']);
  });
  await test('AR-22', 'Context list lookup applies its excluded-method predicate; single lookup rejects followers.', () => {
    const conversation = {requests: [request('r1'), {...request('plan'), method: 'synthetic-plan-method'}], turns: []};
    const api = stateContext(conversation);
    assert.equal(api.getConversationRequests('conversation').length, 1);
    const follower = stateContext(conversation, {getStreamRole: () => ({role: 'follower', ownerClientId: 'owner'})});
    assert.throws(() => follower.getConversationRequest('conversation', 'r1'), /window where it was started/);
  });
  const equivalence = evaluate(['n5t']).n5t;
  const connector = {connector_id: 'connector', link_id: 'link', auth_reason: 'reason', requested_scopes: ['read', 'write', 'read']};
  await test('AR-23', 'Connector equivalence compares a set of scopes; duplicates/order and absent-vs-empty do not differ.', () => {
    assert.equal(equivalence(connector, {...connector, requested_scopes: ['write', 'read']}), true);
    assert.equal(equivalence({...connector, requested_scopes: undefined}, {...connector, requested_scopes: []}), true);
    assert.equal(equivalence(connector, {...connector, requested_scopes: ['read']}), false);
  });
  await test('AR-24', 'Connector/link/reason mismatch or any non-null connection_consent prevents equivalence.', () => {
    for (const key of ['connector_id', 'link_id', 'auth_reason']) assert.equal(equivalence(connector, {...connector, [key]: 'other'}), false);
    for (const value of [false, 0, '', {}]) assert.equal(equivalence(connector, {...connector, connection_consent: value}), false);
    assert.equal(equivalence({...connector, connection_consent: null}, connector), true);
  });
  const shape = evaluate(['H8t']).H8t;
  await test('AR-25', 'Execution-bound parameter shape requires exactly two keys and a non-blank string plan token.', () => {
    assert.equal(shape({confirmation_summary: '', plan_token: 'token'}), true);
    for (const value of [{confirmation_summary: '', plan_token: ' '}, {confirmation_summary: 1, plan_token: 'token'},
      {confirmation_summary: '', plan_token: 'token', extra: true}, {confirmation_summary: ''}]) assert.equal(shape(value), false);
  });
  await test('AR-26', 'Accept safety rejects any non-null persist value for a recognized execution-bound approval.', () => {
    const safe = evaluate(['B8t'], {z8t: () => ({approveDisabled: false, executionBound: true})}).B8t;
    for (const value of [false, true, 0, '']) assert.equal(safe({}, {action: 'accept', _meta: {persist: value}}), false);
    for (const value of [undefined, null, 'text', [], {persist: null}, {}]) assert.equal(safe({}, {_meta: value}), true);
    assert.equal(evaluate(['B8t'], {z8t: () => ({approveDisabled: true, executionBound: true})}).B8t({}, {}), false);
    assert.equal(evaluate(['B8t'], {z8t: () => null}).B8t({}, {}), true);
  });
  const result = {
    schemaVersion: 1, baselineId: baseline, recordedAtUtc: new Date().toISOString(),
    source: {path: helpers.sourcePath, bytes: bytes.length, sha256: sha(bytes)}, inputs: pins,
    parser: {path: path.relative(root, parserPath), sha256: sha(fs.readFileSync(parserPath))},
    units, cases, counts: {passed: cases.length, failed: 0, selectedUnits: units.length,
      newCompleteProgramParsesThisProbe: 0, savedHelperProgramParsesFromPreviousTurn: 1,
      selectedFactoryFragmentParses: 1, productAcceptanceRuns: 0, modelSubmissions: 0, originalClientRuns: 0},
    limits: [
      'Only exact selected function bodies execute in isolated VM contexts. No application module/factory/constructor is executed.',
      'IPC, sender transport, manager identity, schema parsers, turn lookup, draft recognition, storage and account/runtime are not real.',
      'B8t receives a synthetic recognized approval; z8t, QB and their full schema/canonicalization dependencies are source-inspected only.',
      'These cases prove local control-flow and mutation contracts under stated inputs, not delivery, backend authorization, persistence, UI success or whole-client coverage.'
    ]
  };
  fs.writeFileSync(path.join(output, 'observations.json'), JSON.stringify(result, null, 2) + '\n', {flag: 'wx'});
  process.stdout.write(JSON.stringify({passed: cases.length, selectedUnits: units.length, productAcceptanceRuns: 0}) + '\n');
})().catch(error => {
  fs.writeFileSync(path.join(output, 'failure.txt'), error.stack + '\n', {flag: 'wx'});
  process.stderr.write(error.stack + '\n'); process.exitCode = 1;
});
