// Replays selected original functions with synthetic providers; never boots the app.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const vm = require('node:vm');
const assert = require('node:assert/strict');

const [root, work] = process.argv.slice(2);
const directory = path.join(work, 'editor');
const contracts = JSON.parse(fs.readFileSync(path.join(directory, 'source-contracts.json')));
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const results = [];
function unit(name) {
  const entry = contracts.units.find(item => item.name === name);
  assert(entry, name);
  const bytes = fs.readFileSync(path.join(directory, entry.sourceFilename));
  assert.equal(sha(bytes), entry.spanHash);
  const original = fs.readFileSync(path.join(root, '.analysis-local/baselines', contracts.baselineId, 'extracted', entry.sourcePath.slice(9)));
  assert.equal(sha(original), entry.sourceHash);
  assert(bytes.equals(original.subarray(entry.byteRange.start, entry.byteRange.endExclusive)));
  return {entry, text: bytes.toString('utf8')};
}
function run(name, sourceNames, check) {
  try {
    check();
    results.push({name, status: 'passed', sourceUnits: sourceNames.map(name => unit(name).entry)});
  } catch (error) {
    results.push({name, status: 'failed', error: String(error.stack || error), sourceUnits: sourceNames.map(name => unit(name).entry)});
  }
}
const plain = value => JSON.parse(JSON.stringify(value));
function fixture(options = {}) {
  const records = [];
  const symbol = Symbol.for('react.memo_cache_sentinel');
  let stateIndex = 0;
  const context = {
    Symbol,
    kt: {c: size => Array(size).fill(symbol)},
    $: {Fragment: 'fragment', jsx: (type, props) => ({type, props}), jsxs: (type, props) => ({type, props})},
    Q: {
      useId: () => 'synthetic-id',
      useState: initial => {
        const index = stateIndex++;
        return [initial, value => records.push(['state', index, value])];
      },
      useImperativeHandle: (ref, create) => { ref.current = create(); },
    },
    l: () => ({get: () => ({success: value => records.push(['success', value]), danger: value => records.push(['error', value])})}),
    d: 'store', C: 'notifications',
    ae: () => ({formatMessage: value => value.id}),
    ve: () => options.query || {data: []},
    r: class ApiError extends Error { constructor(status) { super('synthetic'); this.status = status; } },
    de: () => ({planAtLogin: 'synthetic-plan'}),
    pe: () => false, ne: () => false,
    De: 'machines', ge: 'create', Ee: 'update',
    s: key => key === 'machines' ? {data: options.machines || [], isPending: false} : {
      isPending: !!options.pending,
      mutate: (input, callbacks) => { context.mutation = {kind: key, input, callbacks}; records.push(['mutation', key]); },
    },
    ee: () => false,
    Oe: (...args) => { records.push(['defaults', ...args]); return {label: 'Fixture'}; },
    _e: (...args) => { context.validationArguments = args; return options.valid !== false; },
    be: value => ({syntheticCreateSerializerInput: value}),
    ye: (value, environment) => ({syntheticUpdateSerializerInput: value, environment}),
    ze: spec => {
      context.formSpec = spec;
      const form = {store: {}, Subscribe: 'subscribe', Field: 'field', reset: value => records.push(['reset', value]), handleSubmit: () => records.push(['handleSubmit'])};
      return form;
    },
    Re: () => !!options.dirty,
    je: (...args) => records.push(['dirtyRegistry', ...args]),
    Ot: value => !value.isDefaultValue,
    Dt: value => value.values,
    j: 'message', Ge: 'unsaved-dialog', Tt: 'create-editor', Et: 'shared-editor',
    He: () => ({data: {preferred_github_connector_id: 'preferred-fixture'}}),
    records,
  };
  vm.createContext(context);
  const evaluate = name => vm.runInContext('(' + unit(name).text + ')', context, {timeout: 1000});
  const ref = {};
  const props = {
    ref,
    environment: options.environment ?? null,
    requestContext: options.requestContext,
    onCancel: () => records.push(['cancel']),
    onSaved: (...args) => records.push(['saved', ...args]),
  };
  return {context, evaluate, props, ref, records, mount: () => evaluate('Et')(props)};
}

for (const environment of [null, undefined, {id: 'synthetic-env'}]) {
  run('wrapper dispatch ' + String(environment?.id ?? environment), ['wt'], () => {
    const f = fixture(); f.props.environment = environment;
    const output = f.evaluate('wt')(f.props);
    assert.equal(output.type, environment == null ? 'create-editor' : 'shared-editor');
    assert.equal(output.props.requestContext, f.props.requestContext);
    if (environment != null) assert.equal(output.props.preferredConnectorId, null);
  });
}
for (const connector of [undefined, 'initial-fixture']) {
  run('new environment connector precedence ' + String(connector), ['Tt'], () => {
    const f = fixture();
    f.props.initialRepository = connector ? {githubConnectorId: connector} : undefined;
    const result = f.evaluate('Tt')(f.props);
    assert.equal(result.props.preferredConnectorId, connector || 'preferred-fixture');
    assert.equal(result.props.environment, null);
  });
}
run('validation failure prevents both mutations', ['Et'], () => {
  const f = fixture({valid: false}); f.mount(); f.context.formSpec.onSubmit({value: {label: 'Fixture'}});
  assert.equal(f.context.mutation, undefined);
});
run('new environment waits for duplicate-name query', ['Et'], () => {
  const f = fixture({query: {data: undefined}}); f.mount(); f.context.formSpec.onSubmit({value: {label: 'Fixture'}});
  assert.equal(f.context.mutation, undefined);
});
run('existing unchanged trimmed name may submit before names query', ['Et'], () => {
  const environment = {id: 'fixture-env', label: 'Fixture', machine_id: 'existing-machine'};
  const f = fixture({environment, query: {data: undefined}}); f.mount();
  f.context.formSpec.onSubmit({value: {label: ' Fixture ', machineId: 'existing-machine'}});
  assert.equal(f.context.mutation.kind, 'update');
  assert.equal(f.context.validationArguments[2], 'existing-machine');
});
run('existing changed name waits for names query', ['Et'], () => {
  const f = fixture({environment: {id: 'fixture-env', label: 'Old'}, query: {data: undefined}}); f.mount();
  f.context.formSpec.onSubmit({value: {label: 'New'}}); assert.equal(f.context.mutation, undefined);
});
run('query HTTP 404 counts as names ready', ['Et'], () => {
  const f = fixture(); f.context.ve = () => ({error: new f.context.r(404)}); f.mount();
  f.context.formSpec.onSubmit({value: {label: 'Fixture'}}); assert.equal(f.context.mutation.kind, 'create');
});
run('other query errors do not count as names ready', ['Et'], () => {
  const f = fixture(); f.context.ve = () => ({error: new f.context.r(500)}); f.mount();
  f.context.formSpec.onSubmit({value: {label: 'Fixture'}}); assert.equal(f.context.mutation, undefined);
});
for (const environment of [null, {id: 'fixture-env', label: 'Fixture'}]) {
  run('request context and serializer boundary ' + (environment ? 'update' : 'create'), ['Et'], () => {
    const requestContext = {signal: {aborted: false}, fixtureOnly: true};
    const f = fixture({environment, requestContext}); f.mount();
    const value = {label: 'Fixture', machineId: 'm1'};
    f.context.formSpec.onSubmit({value});
    const mutation = f.context.mutation;
    assert.equal(mutation.kind, environment ? 'update' : 'create');
    assert.equal(mutation.input.requestContext, requestContext);
    if (environment) {
      assert.equal(mutation.input.environmentId, environment.id);
      assert.equal(mutation.input.requestBody.syntheticUpdateSerializerInput, value);
      assert.equal(mutation.input.requestBody.environment, environment);
    } else assert.equal(mutation.input.requestBody.syntheticCreateSerializerInput, value);
  });
}
run('selected machine membership is forwarded to validation', ['Et'], () => {
  const f = fixture({machines: [{id: 'm1'}]}); f.mount();
  f.context.formSpec.onSubmit({value: {label: 'Fixture', machineId: 'm1'}});
  assert.equal(f.context.validationArguments[1], true);
});
run('create success orders notification reset and saved callback', ['Et'], () => {
  const f = fixture(); f.mount(); const value = {label: 'Fixture'};
  f.context.formSpec.onSubmit({value}); const start = f.records.length;
  f.context.mutation.callbacks.onSuccess({id: 'new-fixture'});
  assert.deepEqual(f.records.slice(start).map(row => row[0]), ['success', 'reset', 'saved']);
  assert.deepEqual(f.records.at(-1), ['saved', 'new-fixture', value]);
});
run('update success keeps original environment id', ['Et'], () => {
  const f = fixture({environment: {id: 'fixture-env', label: 'Fixture'}}); f.mount();
  const value = {label: 'Fixture'}; f.context.formSpec.onSubmit({value}); f.context.mutation.callbacks.onSuccess();
  assert.deepEqual(f.records.at(-1), ['saved', 'fixture-env', value]);
});
run('aborted context suppresses success and error callbacks', ['Et'], () => {
  const signal = {aborted: false}; const f = fixture({requestContext: {signal}}); f.mount();
  f.context.formSpec.onSubmit({value: {label: 'Fixture'}}); signal.aborted = true;
  const start = f.records.length; f.context.mutation.callbacks.onSuccess({id: 'x'}); f.context.mutation.callbacks.onError();
  assert.equal(f.records.length, start);
});
run('already aborted context has no local submission guard', ['Et'], () => {
  const f = fixture({requestContext: {signal: {aborted: true}}}); f.mount();
  f.context.formSpec.onSubmit({value: {label: 'Fixture'}}); assert.equal(f.context.mutation.kind, 'create');
});
run('error notifies without reset or saved callback', ['Et'], () => {
  const f = fixture(); f.mount(); f.context.formSpec.onSubmit({value: {label: 'Fixture'}});
  const start = f.records.length; f.context.mutation.callbacks.onError();
  assert.deepEqual(f.records.slice(start).map(row => row[0]), ['error']);
});
for (const [pending, dirty, expected] of [[false, false, 'cancel'], [false, true, 'state'], [true, false, undefined], [true, true, undefined]]) {
  run('requestClose pending=' + pending + ' dirty=' + dirty, ['Et'], () => {
    const f = fixture({pending, dirty}); f.mount(); const start = f.records.length;
    f.ref.current.requestClose();
    assert.deepEqual(f.records.slice(start).map(row => row[0]), expected ? [expected] : []);
    if (dirty && !pending) assert.deepEqual(f.records.at(-1), ['state', 0, true]);
  });
}
run('form submit delegates to form library after preventDefault', ['Et'], () => {
  const f = fixture(); const result = f.mount();
  const form = result.props.children[0]; const start = f.records.length;
  form.props.onSubmit({preventDefault: () => f.records.push(['preventDefault'])});
  assert.deepEqual(f.records.slice(start).map(row => row[0]), ['preventDefault', 'handleSubmit']);
});
for (const [name, input, expected] of [
  ['comments and export', '# comment\n; comment\nexport API_KEY=fixture', [{key: 'API_KEY', value: 'fixture'}]],
  ['quoted hash', 'KEY="fixture#value" # comment', [{key: 'KEY', value: 'fixture#value'}]],
  ['unquoted hash comment', 'KEY=fixture # comment', [{key: 'KEY', value: 'fixture'}]],
  ['malformed line rejects whole paste', 'KEY=fixture\nmalformed', []],
  ['unclosed quote rejects paste', 'KEY="fixture', []],
  ['empty value retained', 'KEY=', [{key: 'KEY', value: ''}]],
]) {
  run('dotenv paste ' + name, ['$e'], () => {
    const f = fixture(); assert.deepEqual(plain(f.evaluate('$e')(input)), expected);
  });
}
const output = {
  baselineId: contracts.baselineId,
  createdAtUtc: new Date().toISOString(),
  sourceContractsSha256: sha(fs.readFileSync(path.join(directory, 'source-contracts.json'))),
  scriptSha256: sha(fs.readFileSync(__filename)),
  counts: {cases: results.length, passed: results.filter(row => row.status === 'passed').length, failed: results.filter(row => row.status === 'failed').length},
  results,
  limits: [
    'Form library, validation, defaults, serialization, query and mutation implementations are synthetic providers.',
    'Replay verifies local forwarding and control flow, not actual validation rules, wire payload, backend cancellation, account state or persistence.',
    'No target module initialization, original client run, network/service call, model submission or product scenario pass.',
  ],
};
const outputPath = path.join(work, 'probe-attempt-01.json');
fs.writeFileSync(outputPath, JSON.stringify(output, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({outputPath, counts: output.counts, failures: results.filter(row => row.status === 'failed')}));
process.exitCode = output.counts.failed ? 1 : 0;
