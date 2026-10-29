"""Publish scoped candidate metadata; third-party implementations stay local."""
import base64
import hashlib
import json
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
LOCAL = WORKSPACE / '.analysis-local/capnweb-upstream-candidate-work'
RPC = WORKSPACE / '.analysis-local/submission-rpc-dependency-work'
OUT = WORKSPACE / 'analysis' / BASELINE


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write(name, raw):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == raw, name
    else:
        path.write_bytes(raw)
    path.chmod(0o444)


def main():
    selections = [(LOCAL, name) for name in ('registry.json', 'package.json', 'fetch-result.json',
        'extraction.json', 'candidate-api.json', 'candidate-api-v2.json',
        'registry.json.receipt.json', 'upstream.tgz.receipt.json')]
    selections += [(RPC, 'interfaces.json'), (RPC, 'unit-inspection.json')]
    inputs = {(directory.name, name): (directory / name).read_bytes() for directory, name in selections}
    metadata = json.loads(inputs[(LOCAL.name, 'registry.json')])
    package = json.loads(inputs[(LOCAL.name, 'package.json')])
    api = json.loads(inputs[(LOCAL.name, 'candidate-api-v2.json')])
    interfaces = json.loads(inputs[(RPC.name, 'interfaces.json')])
    target = json.loads(inputs[(RPC.name, 'unit-inspection.json')])
    assert metadata['name'] == package['name'] == 'capnweb'
    assert metadata['version'] == package['version'] == api['version'] == '0.11.1'
    assert interfaces['baselineId'] == target['baselineId'] == BASELINE
    archive = (LOCAL / 'upstream.tgz').read_bytes()
    assert hashlib.sha1(archive).hexdigest() == metadata['dist']['shasum']
    assert metadata['dist']['integrity'] == 'sha512-' + base64.b64encode(hashlib.sha512(archive).digest()).decode()
    assert pin((LOCAL / 'index.js').read_bytes()) == {key: api['source'][key] for key in ('bytes', 'sha256')}
    assert api['upstreamExecuted'] is False and api['targetExecuted'] is False
    copies = []
    for directory, name in selections:
        raw = inputs[(directory.name, name)]
        published = 'raw/capnweb-upstream-candidate/' + ('target-' if directory == RPC else '') + name
        write(published, raw)
        copies.append({'original': str(directory / name), 'published': published, **pin(raw),
                       'role': 'exact-consumed-metadata-snapshot',
                       'reviewStatus': 'root-authored; independent candidate review pending'})
    def ref(directory, name, pointer):
        raw = inputs[(directory.name, name)]
        return {'sourcePath': str(directory / name), 'sourceHash': pin(raw)['sha256'],
                'locator': {'jsonPointer': pointer}, 'role': 'upstream-candidate' if directory == LOCAL else 'saved-target-projection'}
    records = []
    def record(claim, sources, method='package-metadata', confidence='confirmed'):
        result = {'id': f'CAPNWEB-CANDIDATE-{len(records)+1:03d}', 'baselineId': BASELINE,
            'claim': claim, 'sourcePath': [s['sourcePath'] for s in sources],
            'sourceHash': [s['sourceHash'] for s in sources], 'locator': [s['locator'] for s in sources],
            'method': method, 'confidence': confidence,
            'verificationStatus': 'candidate-or-saved-metadata-only; no-runtime-equivalence', 'sources': sources}
        records.append(result)
        return result['id']
    record('Official npm capnweb 0.11.1 archive passes declared SHA-512 SRI and SHA-1; this does not identify the baseline installed version.', [ref(LOCAL, 'registry.json', '/dist'), ref(LOCAL, 'fetch-result.json', '/archive')])
    record('Published package declares MIT and the Cloudflare capnweb repository.', [ref(LOCAL, 'package.json', '/license'), ref(LOCAL, 'package.json', '/repository')])
    record('npm metadata gitHead is 20fe0fb488d9238ac69b05776287999b24e4e3e8; its commit tree has not been independently inspected.', [ref(LOCAL, 'registry.json', '/gitHead')])
    record('Root-only package exports select default ESM/CJS, workerd and bun entries; no separate public deep subpath is declared.', [ref(LOCAL, 'package.json', '/exports')])
    record('Default ESM candidate has 16 named exports, including RpcStub, RpcTarget, RpcPromise, RpcSession and newMessagePortRpcSession.', [ref(LOCAL, 'candidate-api-v2.json', '/exports')], 'static-code')
    pairs = [('aF', 'RpcStub', ['constructor', 'dup', 'onRpcBroken', 'map', 'toString']),
             ('oF', 'RpcPromise', ['constructor', 'then', 'catch', 'finally', 'toString']),
             ('BFt', 'RpcSession', ['constructor', 'getRemoteMain', 'getStats', 'drain']),
             ('VFt', 'MessagePortTransport', ['constructor', 'send', 'receive', 'abort'])]
    comparisons = []
    for baseline_label, candidate_label, names in pairs:
        ti = next(i for i, u in enumerate(target['units']) if u['label'] == baseline_label)
        ci = next(i for i, u in enumerate(api['selectedUnits']) if u['label'] == candidate_label)
        tu, cu = target['units'][ti], api['selectedUnits'][ci]
        members = []
        for name in names:
            tm = next(m for m in tu['methods'] if m['name'] == name)
            cm = next(m for m in cu['methods'] if m['name'] == name)
            assert len(tm['params']) == len(cm['params'])
            members.append({'name': name, 'parameterCount': len(tm['params']),
                'target': {'byteRange': tm['byteRange'], 'spanSha256': tm['spanSha256']},
                'candidate': {'byteRange': cm['byteRange'], 'spanSha256': cm['spanSha256']},
                'matches': 'name-and-parameter-count-only', 'operationEquivalent': 'unknown'})
        eid = record(f'{baseline_label} → {candidate_label} is an inferred candidate mapping; {len(names)} selected member names and parameter counts match only.',
            [ref(RPC, 'unit-inspection.json', f'/units/{ti}'), ref(LOCAL, 'candidate-api-v2.json', f'/selectedUnits/{ci}')], 'inference', 'inferred')
        comparisons.append({'targetLabel': baseline_label, 'candidateLabel': candidate_label,
                            'evidenceId': eid, 'members': members})
    ti = next(i for i, u in enumerate(target['units']) if u['label'] == 'hFt')
    ci = next(i for i, u in enumerate(api['selectedUnits']) if u['label'] == 'newMessagePortRpcSession')
    tcalls = target['units'][ti]['calls']; ccalls = api['selectedUnits'][ci]['calls']
    assert sorted(len(c['arguments']) for c in tcalls) == sorted(len(c['arguments']) for c in ccalls) == [0, 1, 3]
    assert sorted(c['callee'].get('name', c['callee'].get('property', {}).get('name')) for c in tcalls) == ['BFt', 'VFt', 'getRemoteMain']
    assert sorted(c['callee'] for c in ccalls) == ['MessagePortTransport', 'NewExpression.getRemoteMain', 'RpcSession$1']
    record('hFt and candidate newMessagePortRpcSession each construct a transport, construct a session and obtain remote main; constructor argument counts are 1/3 and getRemoteMain is 0. Mapping remains inferred.',
        [ref(RPC, 'unit-inspection.json', f'/units/{ti}'), ref(LOCAL, 'candidate-api-v2.json', f'/selectedUnits/{ci}')], 'inference', 'inferred')
    ci = next(i for i, u in enumerate(api['selectedUnits']) if u['label'] == 'RpcTarget')
    assert api['selectedUnits'][ci]['runtimeCondition']['test'] == 'workersModule'
    record('Default ESM RpcTarget initializer is conditional: workersModule.RpcTarget or an empty local class. Package runtime context must be preserved.', [ref(LOCAL, 'candidate-api-v2.json', f'/selectedUnits/{ci}')], 'static-code')
    record('Official default ESM source map contains 10 sourcesContent entries; this is upstream candidate coverage, not recovered application source maps.', [ref(LOCAL, 'extraction.json', '/sourceMap')])
    record('Actual baseline installed lock, full target-to-upstream equivalence, modifications, other embedded versions and transport runtime compatibility remain unverified.', [ref(RPC, 'interfaces.json', '/independentImportDecision'), ref(LOCAL, 'candidate-api-v2.json', '/limits')], 'inference', 'unresolved')
    record('Use normal capnweb root imports as a candidate. Keep application manager/coordinator adapters and scope/host/lifecycle ownership first-party; do not generate capnweb implementation copies.', [ref(LOCAL, 'package.json', '/exports'), ref(RPC, 'interfaces.json', '/proposedOwnedAdapter')], 'inference', 'inferred')
    result = {'schemaVersion': 'capnweb-upstream-candidate/1', 'baselineId': BASELINE,
        'status': 'scoped-official-candidate; independent-review-pending', 'versionCandidate': '0.11.1',
        'package': {'name': package['name'], 'version': package['version'], 'exports': package['exports'], 'license': package['license'],
                    'gitHeadMetadata': metadata.get('gitHead'), 'archive': pin(archive)},
        'records': records, 'interfaceComparisons': comparisons,
        'counts': {'records': len(records), 'interfaceGroups': len(comparisons), 'memberShapes': sum(len(c['members']) for c in comparisons),
                   'factoryCallShapes': 3, 'candidateWholeProgramsParsed': 1, 'candidateSelectedRepairUnits': 6},
        'provenance': copies, 'globalRecordsAdded': 0, 'runtimeRunsAdded': 0,
        'installedVersion': 'unknown', 'fullEquivalence': 'unknown', 'modifiedStatus': 'unknown', 'mode': 'unknown',
        'limits': ['18 matching name/declared-parameter-count shapes do not establish operations, wire encoding or receiver equivalence.',
                   'Pre-review target metadata is pinned exactly as consumed; later owner revisions need explicit delta review.',
                   'No original client, package implementation, source-map contents or tarball is published.']}
    write('capnweb-upstream-candidate.json', encode(result))
    write('capnweb-upstream-candidate-evidence.jsonl', b''.join((json.dumps(r, ensure_ascii=False)+'\n').encode() for r in records))
    assert len(records) == 14 and result['counts']['memberShapes'] == 18
    print(json.dumps({'status': 'scoped-candidate-published', **result['counts'], 'runtimeRunsAdded': 0}))


if __name__ == '__main__':
    main()
