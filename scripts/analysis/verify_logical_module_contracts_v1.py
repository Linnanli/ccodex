"""Read back the finite owner contract publication; never execute target code."""
from pathlib import Path
import hashlib
import json
import stat

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/logical-module-contracts-v1-work'
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
cache, checked_pins, checked_pointers = {}, set(), set()


def read(p):
    p = Path(p)
    if p not in cache:
        cache[p] = json.loads(p.read_text())
    return cache[p]


def at(value, pointer):
    for part in pointer[1:].split('/') if pointer else []:
        part = part.replace('~1', '/').replace('~0', '~')
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def visit(value):
    if isinstance(value, dict):
        if {'path', 'bytes', 'sha256'} <= value.keys():
            p = ROOT / value['path']
            raw = p.read_bytes()
            assert len(raw) == value['bytes'] and sha(raw) == value['sha256'], p
            checked_pins.add((value['path'], value['sha256']))
            if 'jsonPointer' in value:
                at(read(p), value['jsonPointer'])
                checked_pointers.add((value['path'], value['jsonPointer']))
        for child in value.values():
            visit(child)
    elif isinstance(value, list):
        for child in value:
            visit(child)


publication = read(WORK / 'publication.json')
visit(publication)
doc = read(OUT / 'logical-module-contracts-v1.json')
visit(doc)
assert doc['baselineId'] == BASE
assert doc['fullAnalysisCompleted'] is False and doc['implementationReady'] is False
old = read(OUT / 'logical-module-ownership-v1.json')
catalog = read(OUT / 'logical-module-inventory-v1.json')
owner_lookup = {x['ownerId']: x for x in old['responsibilityOwners']}
proposal_lookup = {x['id']: x for x in catalog['records']}
rows = doc['records']
assert len(rows) == len(owner_lookup) == 37
assert {r['ownerId'] for r in rows} == owner_lookup.keys()
assert sum(len(r['proposalIds']) for r in rows) == 38
assert doc['requiredFields'] == catalog['requiredFields']
assert len(doc['requiredFields']) == 10
units = {u['id']: u for u in doc['sourceUnits']}
assert len(units) == len(doc['sourceUnits'])
source_files = {}
for u in units.values():
    if u['sourcePath'] not in source_files:
        source_files[u['sourcePath']] = (FROZEN / u['sourcePath'].removeprefix('app.asar/')).read_bytes()
    raw = source_files[u['sourcePath']]
    span = u['byteRange']
    assert sha(raw) == u['sourceHash']
    assert sha(raw[span['start']:span['endExclusive']]) == u['spanHash']
    for origin in u['inheritedOrigins']:
        inherited = at(read(ROOT / origin['path']), origin['jsonPointer'])
        assert inherited['sourcePath'] == u['sourcePath'] and inherited['sourceHash'] == u['sourceHash']
        assert inherited['byteRange'] == span and inherited['verifiedSpanHash'] == u['spanHash']
all_used = set()
for r in rows:
    o = owner_lookup[r['ownerId']]
    assert r['proposalIds'] == o['memberProposalIds']
    assert all(field in r and r[field] for field in doc['requiredFields'])
    assert set(r['sourceRanges']) <= units.keys()
    all_used.update(r['sourceRanges'])
    actual_spans = {(units[u]['sourcePath'], units[u]['byteRange']['start'], units[u]['byteRange']['endExclusive']) for u in r['sourceRanges']}
    expected_spans = {(s['sourcePath'], s['byteRange']['start'], s['byteRange']['endExclusive'])
                      for pid in r['proposalIds'] for s in proposal_lookup[pid]['sourceRanges']}
    assert actual_spans == expected_spans
    assert r['mode']['value'] == 'unknown' and r['mode']['disposition'] == 'retain'
    assert not r['imports']['exactEsmImportClosure'] and not r['exports']['completeConsumerClosure']
    assert not r['thirdPartyDependencies']['generateVendorImplementation']
    assert not r['thirdPartyDependencies']['exactDependencyClosure']
    assert not r['runtimeValidated'] and not r['clientImplementationGenerated']
    assert not r['completeSourcePartitionProven'] and not r['taskOwnership']['allConsumersAssigned']
    assert r['taskOwnership']['foundation'] == o['primaryFoundationTask']
    assert r['taskOwnership']['conditionalConsumerJoins'] == o['consumerTaskJoins']
    for link in r['thirdPartyDependencies']['namedPackageLinks']:
        inherited = at(read(ROOT / link['versionAndInvestigation']['path']), link['versionAndInvestigation']['jsonPointer'])
        assert inherited['name'] == link['name'] and inherited['dependencyId'] == link['dependencyId']
        assert not link['acceptedExactDependency']
assert all_used == units.keys()
lookup = {r['ownerId']: r for r in rows}
assert len(lookup['LM-PROVIDER-host-rpc-selector']['proposalIds']) == 2
assert lookup['LM-BOUNDARY-STRUCT-RWC-FETCH']['proposedPath']['values'] == ['packages/desktop-http-client/src/desktop-fetch.ts']
assert lookup['LM-APPHOST-AH-M06']['proposedPath']['values'] == ['apps/desktop/src/main/http/desktop-fetch.ts']
assert len(lookup['LM-BOUNDARY-STRUCT-RWC-PROJECTS']['proposedPath']['values']) == 3
assert 'currentLocalDelegateDecision' in lookup['LM-BOUNDARY-STRUCT-RWC-PROJECTS']['taskOwnership']
changed = [r for r in rows if r['proposedPath']['values'] != owner_lookup[r['ownerId']]['proposedPaths']]
assert len(changed) == 7
assert all(r['proposedPath']['values'][0].startswith('apps/desktop/src/') for r in changed)

correction = read(OUT / 'selected-evidence-schema-normalization-v1.json')
visit(correction)
required = {'id', 'baselineId', 'claim', 'sourcePath', 'sourceHash', 'locator', 'method', 'confidence', 'verificationStatus'}
normalizations = [
    ('unmatched', [json.loads(x) for x in (OUT / 'request-entry-unmatched-review-evidence.jsonl').read_text().splitlines()]),
    ('mainReceiver', read(OUT / 'mode-persistence-receiver.json')['records']),
]
total = 0
for kind, original in normalizations:
    normalized = [json.loads(x) for x in (ROOT / correction[kind]['effectiveEvidence']['path']).read_text().splitlines()]
    assert len(original) == len(normalized) == correction[kind]['count']
    for before, after in zip(original, normalized):
        assert required <= after.keys()
        assert after['baselineId'] == BASE and after['confidence'] in {'confirmed', 'inferred', 'unresolved'}
        assert (after['id'], after['claim'], after['sourcePath']) == (before['id'], before['claim'], before['sourcePath'])
        assert after['sourceHash'] == before.get('sourceHash', before.get('sourceSha256'))
        assert after['locator'] == before.get('locator', before.get('byteRange'))
        raw = (FROZEN / after['sourcePath'].removeprefix('app.asar/')).read_bytes()
        span = after['locator']
        assert sha(raw) == after['sourceHash']
        assert sha(raw[span['start']:span['endExclusive']]) == before['spanSha256']
        assert after['confidence'] == ('inferred' if kind == 'unmatched' else before['confidence'])
    total += len(normalized)
assert total == 50
facts = [json.loads(x) for x in (OUT / 'logical-module-contracts-v1-evidence.jsonl').read_text().splitlines()]
assert len(facts) == 37 and {f['id'] for f in facts} == {r['evidenceId'] for r in rows}
for f in facts:
    assert required <= f.keys() and f['confidence'] == 'inferred' and f['method'] == 'inference'
    assert sha((ROOT / f['sourcePath']).read_bytes()) == f['sourceHash']
    at(read(ROOT / f['sourcePath']), f['locator']['jsonPointer'])

state = read(OUT / 'analysis-state.json')
before_state = read(WORK / 'analysis-state.json.before')
for key in ['latestBehaviorAuthorizationState', 'featureScopeCurrentView', 'restorationCoverage', 'currentRestorationOrdering']:
    assert state[key] == before_state[key], key
assert state['fullAnalysisCompleted'] is False and state['status'] == 'in-progress'
assert state['stageDecisions']['nextAction']['issueId'] == 'SD-02'
assert 'input-shape' in state['stageDecisions']['nextAction']['question']
for name in ['report.md', 'gaps.md']:
    assert (OUT / name).read_text().split('\n\n', 1)[1] == (WORK / (name + '.before')).read_text().split('\n\n', 1)[1]
for item in [*publication.values(), correction['unmatched']['effectiveEvidence'], correction['mainReceiver']['effectiveEvidence']]:
    if isinstance(item, dict) and 'path' in item:
        assert not (ROOT / item['path']).stat().st_mode & stat.S_IWUSR
assert doc['counts']['uniqueInheritedSourceUnits'] == len(units)
assert doc['counts']['sourceFilesIdentityChecked'] == len(source_files)
receipt = {'status': 'passed', 'pinsChecked': len(checked_pins), 'jsonPointersChecked': len(checked_pointers),
           'responsibilityOwners': 37, 'requiredFieldsPerOwner': 10, 'inheritedSourceUnitsChecked': len(units),
           'legacyRecordsNormalized': 50, 'modeAndAuthorizationScopeUnchanged': True,
           'qualification': 'Readback of finite saved contracts, source identities and normalized evidence; no target-runtime or full-client acceptance.'}
with (WORK / 'verification.json').open('x') as handle:
    json.dump(receipt, handle, ensure_ascii=False, indent=2)
    handle.write('\n')
print(json.dumps(receipt, ensure_ascii=False))
