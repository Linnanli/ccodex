// Exact frozen function/method probes; all host/IPC/backend boundaries are synthetic.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const baseline = 'codex-26.1007.30912-c5b273322a83';
const work = path.join(root, '.analysis-local/approval-response-wire-work');
const out = path.join(work, 'probe');
if (fs.existsSync(out)) throw Error('Preserve previous probe');
fs.mkdirSync(out);
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const sources = {}, programs = {}, pins = [], units = [], body = {};
for (const [key, folder] of Object.entries({shared: 'shared-program', main: 'main-program', connection: 'connection-program'})) {
  const file = path.join(work, folder, 'source-contracts.json');
  const raw = fs.readFileSync(file), program = JSON.parse(raw);
  pins.push({path: path.relative(root, file), bytes: raw.length, sha256: sha(raw)});
  programs[key] = program;
  const bytes = fs.readFileSync(path.join(root, '.analysis-local/baselines', baseline, 'extracted', program.sourcePath.replace(/^app\.asar\//, '')));
  assert.equal(sha(bytes), program.sourceHash);
  sources[key] = bytes;
}
function select(key, name, locator, pointer) {
  const bytes = sources[key], range = locator.byteRange;
  const selected = bytes.subarray(range.start, range.endExclusive);
  assert.equal(sha(selected), locator.spanSha256 ?? locator.spanHash);
  const sourceFilename = `${String(units.length + 1).padStart(3, '0')}-${name}.txt`;
  fs.writeFileSync(path.join(out, sourceFilename), selected);
  units.push({name, sourcePath: programs[key].sourcePath, sourceHash: programs[key].sourceHash,
    byteRange: range, spanSha256: sha(selected), nodeType: locator.nodeType,
    origin: {input: pins[{shared: 0, main: 1, connection: 2}[key]].path, jsonPointer: pointer}, sourceFilename});
  body[name] = selected.toString('utf8');
}
function unit(key, name) {
  const index = programs[key].units.findIndex(unit => unit.name === name);
  assert.ok(index >= 0, name); select(key, name, programs[key].units[index], `/units/${index}`);
}
function member(key, className, name) {
  const classes = programs[key].classIndex;
  const classIndex = classes.findIndex(c => c.name === className);
  assert.ok(classIndex >= 0, className);
  const index = classes[classIndex].members.findIndex(m => m.name === name);
  assert.ok(index >= 0, name);
  select(key, `${className}.${name}`, classes[classIndex].members[index], `/classIndex/${classIndex}/members/${index}`);
}
function declaration(key, name) {
  const candidates = programs[key].declarations.map((d, index) => ({d, index})).filter(x => x.d.name === name && x.d.binding.scopeKind === 'Program');
  assert.equal(candidates.length, 1, name);
  select(key, name, candidates[0].d, `/declarations/${candidates[0].index}`);
}
unit('shared', 'Pvn');
const dispatcherPath = `analysis/${baseline}/host-message-contracts.json`;
const dispatcherBytes = fs.readFileSync(path.join(root, dispatcherPath));
const dispatcher = JSON.parse(dispatcherBytes);
pins.push({path: dispatcherPath, bytes: dispatcherBytes.length, sha256: sha(dispatcherBytes)});
const caseIndex = dispatcher.cases.findIndex(item => item.label.value === 'mcp-response');
assert.ok(caseIndex >= 0);
const caseRange = dispatcher.cases[caseIndex].clauseRange;
select('main', 'case-mcp-response', {byteRange: {start: caseRange.start, endExclusive: caseRange.endExclusive},
  spanSha256: sha(sources.main.subarray(caseRange.start, caseRange.endExclusive)), nodeType: 'SwitchCase'}, `/cases/${caseIndex}`);
units.at(-1).origin.input = dispatcherPath;
for (const name of ['MMe.getAppServerConnection', 'MMe.constructor', 'tee.getConnection', 'tee.getMaybeConnection', 'Uv.route']) unit('main', name);
for (const name of ['constructor', 'createAppServerConnection', 'handleMessage']) member('main', 'hXe', name);
declaration('main', 'Wv');
for (const name of ['mB.handleClientResponse', 'mB.constructor', 'MR.sendMessage', 'MR.constructor']) unit('connection', name);
for (const name of ['$L', 'eR', 'kR']) declaration('connection', name);
const exportedIndex = programs.connection.exports.findIndex(e => e.exported === 'pn' && e.expression.includes('return mB}'));
assert.ok(exportedIndex >= 0);
select('connection', 'export-pn-mB', programs.connection.exports[exportedIndex], `/exports/${exportedIndex}`);

function compileFunction(name, injected) {
  return vm.runInNewContext(`${body[name]};${name}`, injected, {timeout: 1000});
}
function compileMethod(name, injected = {}) {
  const method = name.split('.').at(-1);
  return vm.runInNewContext(`({${body[name]}}).${method}`, injected, {timeout: 1000});
}
const response = {id: 'synthetic-request', result: {action: 'accept', content: null, _meta: null}};
const cases = [];
async function test(id, claim, run) {await run(); cases.push({id, claim, passed: true});}
function mainHandler(injected) {
  return vm.runInNewContext(`(async function(e,t){switch(t.type){${body['case-mcp-response']}}})`, injected, {timeout: 1000});
}
function deliveryFixture(options = {}) {
  const sent = [], remembered = [], encoded = [];
  const connection = {send: value => {sent.push(value);}};
  const injected = {Buffer, o: {M: Error}, tL: () => false,
    n: {sa: (...args) => {encoded.push(args); return 'synthetic-durable-envelope';}}};
  const helpers = vm.runInNewContext(`${body.$L}\n${body.eR}\n${body.kR}\n({$L,eR,kR})`, injected, {timeout: 1000});
  const send = compileMethod('MR.sendMessage', {...injected, ...helpers});
  const receiver = {
    options: {getConnection: () => connection, hostId: 'local', hostKind: 'local', transportKind: 'stdio',
      sharedThreadIds: new Set(), getThreadAccess: () => 'private',
      logger: {debug() {}, trace() {}}, ...options},
    outgoingMessageSizeTracker: {track: () => []},
    rememberSharedThread: (...args) => remembered.push(args)
  };
  return {send: (...args) => send.call(receiver, ...args), sent, remembered, encoded, connection, receiver};
}
function connectionFixture(overrides = {}) {
  const events = [];
  const respond = compileMethod('mB.handleClientResponse', {n: {xs: value => value}, o: {Jt: () => 'current-trace'}});
  const receiver = {
    userVerification: {remove: id => events.push(['verification', id])},
    turnCwds: {observeClientResponse: payload => events.push(['cwd', payload])},
    requestUserInputAutoResolution: {stopTrackingRequest: id => events.push(['auto', id])},
    logger: {trace: () => events.push(['log'])}, ensureReady: async () => {},
    broadcastFatalError: error => events.push(['fatal', error]),
    messageDelivery: {sendMessage: (...args) => events.push(['send', ...args])}, ...overrides
  };
  return {events, receiver, respond: (...args) => respond.call(receiver, ...args)};
}
(async () => {
  await test('AW-01', 'Untraced Pvn envelope contains host/thread/response and omits requestMethod/trace.', () => {
    const messages = [], fn = compileFunction('Pvn', {n6: () => null});
    assert.equal(fn({dispatchMessageFromView: (...args) => messages.push(args), hostId: 'host', threadId: 'thread', method: 'mcpServer/elicitation/request', response}), undefined);
    assert.equal(messages[0][0], 'mcp-response'); assert.equal(messages[0][1].response, response);
    assert.deepEqual(Object.keys(messages[0][1]).sort(), ['hostId', 'response', 'threadId']);
  });
  await test('AW-02', 'Traced Pvn carries method/trace and finishes after synchronous dispatch, without waiting its Promise.', () => {
    const events = [], fn = compileFunction('Pvn', {n6: args => {events.push(['trace', args]); return {trace: 'trace', finish: error => events.push(['finish', error])};}});
    const messages = [];
    fn({dispatchMessageFromView: (...args) => {messages.push(args); return new Promise(() => {});}, hostId: 'host', threadId: 'thread', method: 'mcpServer/elicitation/request', response});
    assert.equal(events[0][1].childName, 'approval.response'); assert.equal(messages[0][1].requestMethod, 'mcpServer/elicitation/request');
    assert.equal(messages[0][1].trace, 'trace'); assert.equal(events.at(-1)[0], 'finish');
  });
  await test('AW-03', 'Pvn classifies the two dynamic tool methods separately and reports synchronous dispatch failure.', () => {
    for (const method of ['item/tool/call', 'item/tool/requestOptionPicker']) {
      const records = [], fn = compileFunction('Pvn', {n6: args => {records.push(args); return {trace: {}, finish: error => records.push(error)};}});
      assert.throws(() => fn({dispatchMessageFromView: () => {throw Error('dispatch failure');}, hostId: 'host', method, response}), /dispatch failure/);
      assert.equal(records[0].childName, 'tool.response'); assert.equal(records.at(-1).message, 'dispatch failure');
    }
  });
  const logging = {xY: () => ({debug() {}})};
  await test('AW-04', 'A dynamic response router hit prevents app-server connection lookup.', async () => {
    const handle = mainHandler(logging);
    await handle.call({dynamicAppToolResponses: {route: () => true}, getAppServerConnection() {throw Error('must not lookup');}}, {id: 1}, {type: 'mcp-response', hostId: 'host', response});
  });
  await test('AW-05', 'Main routes a non-dynamic response by hostId and forwards response plus threadId.', async () => {
    const calls = [], handle = mainHandler(logging);
    await handle.call({dynamicAppToolResponses: {route: () => false}, getAppServerConnection: host => {
      calls.push(host); return {handleClientResponse: async (...args) => calls.push(args)};
    }}, {id: 1}, {type: 'mcp-response', hostId: 'host', threadId: 'thread', response});
    assert.equal(calls[0], 'host'); assert.deepEqual(calls[1], [response, 'thread']);
  });
  await test('AW-06', 'Main uses its tracing wrapper only when both trace and requestMethod are present.', async () => {
    let wrappers = 0;
    const handle = mainHandler({...logging, c: {rn: async (options, callback) => {wrappers++; assert.equal(options.trace, 'trace'); return callback();}}});
    const receiver = {dynamicAppToolResponses: {route: () => false}, getAppServerConnection: () => ({handleClientResponse: async () => {}})};
    for (const extra of [{trace: 'trace'}, {requestMethod: 'method'}, {trace: 'trace', requestMethod: 'method'}]) await handle.call(receiver, {id: 1}, {type: 'mcp-response', response, ...extra});
    assert.equal(wrappers, 1);
  });
  await test('AW-07', 'Main awaits the connection handler and propagates its rejection.', async () => {
    const handle = mainHandler(logging), receiver = {dynamicAppToolResponses: {route: () => false}, getAppServerConnection: () => ({handleClientResponse: async () => {throw Error('connection failed');}})};
    await assert.rejects(handle.call(receiver, {id: 1}, {type: 'mcp-response', response}), /connection failed/);
  });
  await test('AW-08', 'The actual registry getter throws for a missing host and returns the stored object otherwise.', () => {
    const get = compileMethod('tee.getConnection'), maybe = compileMethod('tee.getMaybeConnection');
    const connection = {}, receiver = {connections: new Map([['host', connection]]), getMaybeConnection: maybe};
    assert.equal(get.call(receiver, 'host'), connection); assert.throws(() => get.call(receiver, 'missing'), /not found/);
  });
  await test('AW-09', 'Dynamic router returns false on no pending ID; a hit is removed before resolving/rejecting.', () => {
    const normalize = compileFunction('Wv', {}), pending = new Map(), results = [];
    const route = compileMethod('Uv.route', {Wv: normalize, r: {mr: {safeParse: result => ({success: true, data: result})}}});
    assert.equal(route.call({pending}, response), false);
    pending.set(normalize(response.id), {resolve: result => {assert.equal(pending.size, 0); results.push(result);}});
    assert.equal(route.call({pending}, response), true); assert.equal(results[0], response.result);
    pending.set(normalize(response.id), {reject: error => results.push(error.message)});
    assert.equal(route.call({pending}, {id: response.id, error: {message: 'dynamic error'}}), true);
    assert.equal(results.at(-1), 'dynamic error'); assert.equal(pending.size, 0);
  });
  await test('AW-10', 'Ready failure follows pre-send tracking cleanup, broadcasts fatal error and fulfills without send.', async () => {
    const f = connectionFixture({ensureReady: async () => {throw Error('not ready');}});
    assert.equal(await f.respond(response, 'thread'), undefined);
    assert.deepEqual(f.events.map(e => e[0]), ['verification', 'cwd', 'auto', 'log', 'fatal']);
    assert.match(f.events.at(-1)[1], /not ready/);
  });
  await test('AW-11', 'A false admission callback suppresses sending after readiness.', async () => {
    const f = connectionFixture(); await f.respond(response, 'thread', () => false);
    assert.equal(f.events.some(e => e[0] === 'send'), false);
  });
  await test('AW-12', 'Connection overwrites response trace with current context and passes thread context separately.', async () => {
    const f = connectionFixture(); await f.respond({...response, trace: 'old-trace'}, 'thread');
    const sent = f.events.find(e => e[0] === 'send'); assert.equal(sent[1].trace, 'current-trace');
    assert.equal(sent[2], undefined); assert.equal(sent[3], 'thread');
  });
  await test('AW-13', 'Connection fulfillment does not await a Promise returned by delivery.', async () => {
    const f = connectionFixture({messageDelivery: {sendMessage: () => new Promise(() => {})}});
    assert.equal(await f.respond(response, 'thread'), undefined);
  });
  await test('AW-14', 'A synchronous delivery throw becomes a rejected connection handler Promise.', async () => {
    const f = connectionFixture({messageDelivery: {sendMessage: () => {throw Error('write failed');}}});
    await assert.rejects(f.respond(response, 'thread'), /write failed/);
  });
  await test('AW-15', 'Ordinary-host delivery JSON-serializes the response, without copying host/thread wrapper fields.', () => {
    const f = deliveryFixture(); assert.equal(f.send(response, undefined, 'thread'), undefined);
    assert.deepEqual(JSON.parse(f.sent[0]), response); assert.equal(f.remembered[0][0], response);
  });
  await test('AW-16', 'Response transformation occurs before ordinary-host serialization.', () => {
    const f = deliveryFixture({transformOutgoingMessage: message => ({...message, transformed: true})});
    f.send(response); assert.equal(JSON.parse(f.sent[0]).transformed, true);
  });
  await test('AW-17', 'Missing transport connection and synchronous send failure throw.', () => {
    const missing = deliveryFixture({getConnection: () => null}); assert.throws(() => missing.send(response), /not available/);
    const failure = deliveryFixture(); failure.connection.send = () => {throw Error('synthetic transport throw');};
    assert.throws(() => failure.send(response), /synthetic transport throw/);
  });
  await test('AW-18', 'Delivery ignores a pending return value from transport.send.', () => {
    const f = deliveryFixture(); f.connection.send = () => new Promise(() => {});
    assert.equal(f.send(response), undefined);
  });
  await test('AW-19', 'Durable shared delivery adds thread routing fields and uses its separate encoder.', () => {
    const f = deliveryFixture({hostId: 'durable', sharedThreadIds: new Set(['thread'])});
    f.send(response, undefined, 'thread'); assert.equal(f.sent[0], 'synthetic-durable-envelope');
    assert.equal(f.encoded[0][0].threadId, 'thread'); assert.equal(f.encoded[0][0].threadAccess, 'shared');
  });
  await test('AW-20', 'Composed main/connection/delivery methods emit one ordinary-host response string.', async () => {
    const delivery = deliveryFixture(), connection = connectionFixture({messageDelivery: {sendMessage: delivery.send}});
    const handle = mainHandler(logging);
    await handle.call({dynamicAppToolResponses: {route: () => false}, getAppServerConnection: () => ({handleClientResponse: connection.respond})}, {id: 1}, {type: 'mcp-response', hostId: 'local', threadId: 'thread', response});
    assert.equal(delivery.sent.length, 1); assert.equal(JSON.parse(delivery.sent[0]).id, response.id);
    assert.equal(JSON.parse(delivery.sent[0]).trace, 'current-trace');
  });
  const result = {schemaVersion: 1, baselineId: baseline, recordedAtUtc: new Date().toISOString(), inputs: pins,
    units, cases, counts: {selectedUnits: units.length, isolatedCasesPassed: cases.length,
      productAcceptanceRuns: 0, originalClientRuns: 0, modelSubmissions: 0},
    limits: ['No target module, app constructor, actual IPC, host/account or backend was executed.',
      'Tracing, logging, URL/schema classification, connection readiness, dynamic response schema, turn tracking and durable encoding are synthetic boundaries.',
      'Registry construction/export joins are source evidence; actual receiver identity and delivery remain unobserved.',
      'JSON output here ends at transport.send; actual framing/write acceptance, backend authorization and approval resolution are not proven.']};
  fs.writeFileSync(path.join(out, 'observations.json'), JSON.stringify(result, null, 2) + '\n');
  process.stdout.write(JSON.stringify(result.counts) + '\n');
})().catch(error => {fs.writeFileSync(path.join(out, 'failure.txt'), error.stack); process.stderr.write(error.stack + '\n'); process.exitCode = 1;});
