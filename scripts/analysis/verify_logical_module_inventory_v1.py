#!/usr/bin/env python3
"""Read back the published view without importing or running its producer."""
import collections
import csv
import hashlib
import json
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/logical-module-inventory-v1-work'
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'
hash_bytes = lambda b: hashlib.sha256(b).hexdigest()


def read(p):
    return json.loads(Path(p).read_text())


def resolve(value, ptr):
    if ptr == '':
        return value
    assert ptr.startswith('/')
    for token in ptr[1:].split('/'):
        key = token.replace('~1', '/').replace('~0', '~')
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


pin_checks = set()
pointer_checks = set()


def check_ref(r):
    path = ROOT / r['path']
    b = path.read_bytes()
    assert len(b) == r['bytes'] and hash_bytes(b) == r['sha256'], path
    pin_checks.add((r['path'], r['sha256']))
    if 'jsonPointer' in r:
        resolve(json.loads(b), r['jsonPointer'])
        pointer_checks.add((r['path'], r['jsonPointer']))


publication = read(WORK / 'publication.json')
for k in ['catalog', 'summary', 'csv', 'evidence', 'producer']:
    check_ref(publication[k])
for k in ['catalog', 'summary', 'csv', 'evidence']:
    assert stat.S_IMODE((ROOT / publication[k]['path']).stat().st_mode) == 0o444
catalog = read(ROOT / publication['catalog']['path'])
assert catalog['baselineId'] == BASE
assert catalog['fullAnalysisCompleted'] is False and catalog['implementationReady'] is False
for p in catalog['inputPins'] + [catalog['plan']]:
    check_ref(p)


def walk_refs(v):
    if isinstance(v, dict):
        if all(k in v for k in ['path', 'bytes', 'sha256']):
            check_ref(v)
        for x in v.values():
            walk_refs(x)
    elif isinstance(v, list):
        for x in v:
            walk_refs(x)


walk_refs(catalog)
rows = catalog['records']
assert len(rows) == 38 and len({r['id'] for r in rows}) == 38
assert dict(collections.Counter(r['originFamily'] for r in rows)) == {
    'BOUNDARY': 11, 'APPHOST': 8, 'SOURCE': 6, 'PROVIDER': 5,
    'CONTEXT': 1, 'RUNTIME': 3, 'SETTINGS': 4,
}
assert len(catalog['requiredFields']) == 10
file_bytes = {}
span_keys = set()
row_span_count = 0
published = read(OUT / 'modules.json')
published_by_path = {m['sourcePath']: m for m in published}
for r in rows:
    assert all(k in r and r[k] is not None for k in catalog['requiredFields'])
    assert r['mode']['value'] == 'unknown' and r['mode']['disposition'] == 'retain'
    assert r['runtimeValidated'] is False and r['clientImplementationGenerated'] is False
    assert r['imports']['completeLogicalImportClosure'] is False
    assert r['exports']['completeConsumerClosure'] is False
    assert r['exports']['proposedEsmExports'] is None
    assert r['sharedState']['completeOwnershipClosure'] is False
    assert r['sideEffects']['completeEffectClosure'] is False
    assert r['thirdPartyDependencies']['implementationRecovery'] is False
    assert r['thirdPartyDependencies']['exactModuleDependencyClosure'] is False
    assert r['featureTaskOwnership']['taskIds'] is None
    assert r['featureTaskOwnership']['featureIds'] is None
    for env in r['environment']['sourceFiles']:
        if env['sourcePath'] in published_by_path:
            assert env['publishedFileEnvironment'] == published_by_path[env['sourcePath']]['environment']
    for s in r['sourceRanges'] + r['sourceMetadataRefs']:
        path = s['sourcePath']
        if path not in file_bytes:
            file_bytes[path] = (FROZEN / path.removeprefix('app.asar/')).read_bytes()
        b = file_bytes[path]
        assert hash_bytes(b) == s['sourceHash']
        origin_data = resolve(read(ROOT / s['origin']['path']), s['origin']['jsonPointer'])
        # Every published locator must be contained in its cited saved metadata.
        def find_locator(v):
            if isinstance(v, dict):
                if 'start' in v and 'endExclusive' in v:
                    if 'byteRange' in s and (v['start'], v['endExclusive']) == (s['byteRange']['start'], s['byteRange']['endExclusive']):
                        return True
                if 'byteStart' in v and 'byteEnd' in v and 'byteRange' in s:
                    if (v['byteStart'], v['byteEnd']) == (s['byteRange']['start'], s['byteRange']['endExclusive']):
                        return True
                if 'metadataLocator' in s and v == s['metadataLocator']:
                    return True
                return any(find_locator(x) for x in v.values())
            if isinstance(v, list):
                return any(find_locator(x) for x in v)
            return False
        assert find_locator(origin_data), (r['id'], s)
        if 'byteRange' not in s:
            continue
        start, end = s['byteRange']['start'], s['byteRange']['endExclusive']
        assert 0 <= start < end <= len(b)
        digest = hash_bytes(b[start:end])
        assert digest == s['verifiedSpanHash']
        assert s['inheritedSpanHash'] in [None, digest]
        span_keys.add((path, start, end))
        row_span_count += 1

# Recompute overlap pairs, without trusting the producer's pair list.
expected_pairs = set()
for i, a in enumerate(rows):
    for b in rows[i + 1:]:
        if any(x['sourcePath'] == y['sourcePath'] and
               max(x['byteRange']['start'], y['byteRange']['start']) < min(x['byteRange']['endExclusive'], y['byteRange']['endExclusive'])
               for x in a['sourceRanges'] for y in b['sourceRanges']):
            expected_pairs.add((a['id'], b['id']))
actual_pairs = {(x['left'], x['right']) for x in catalog['sourceOverlapReviews']}
assert actual_pairs == expected_pairs and len(actual_pairs) == 19
assert catalog['counts']['sourceFilesIdentityChecked'] == len(file_bytes) == 13
assert catalog['counts']['recordSourceRangesIdentityChecked'] == row_span_count == 272
for k, v in catalog['counts'].items():
    if k.startswith('new'):
        assert v == 0

ev = [json.loads(line) for line in (ROOT / publication['evidence']['path']).read_text().splitlines()]
assert len(ev) == 38
required_evidence = {'id', 'baselineId', 'claim', 'sourcePath', 'sourceHash', 'locator', 'method', 'confidence', 'verificationStatus'}
for item in ev:
    assert required_evidence <= item.keys()
    assert item['confidence'] == 'inferred' and item['baselineId'] == BASE
    assert hash_bytes((ROOT / item['sourcePath']).read_bytes()) == item['sourceHash']
    resolve(read(ROOT / item['sourcePath']), item['locator']['jsonPointer'])
csv_rows = list(csv.DictReader((ROOT / publication['csv']['path']).open()))
assert [r['id'] for r in csv_rows] == [r['id'] for r in rows]

before = read(WORK / 'state-before.json')
after = read(OUT / 'analysis-state.json')
assert after['logicalModuleInventory']['catalog'] == publication['catalog']
assert after['fullAnalysisCompleted'] is False and after['status'] == 'in-progress'
assert after['stageDecisions']['nextAction'] == catalog['nextAction']
comparison = json.loads(json.dumps(after))
del comparison['logicalModuleInventory']
comparison['updatedAtUtc'] = before['updatedAtUtc']
comparison['stageDecisions']['nextAction'] = before['stageDecisions']['nextAction']
assert comparison == before, 'Unrelated state changed'
assert after['latestBehaviorAuthorizationState']['groupRemaining'] == 0
coverage = read(OUT / 'restoration-coverage-v17.json')
assert len(coverage['features']) == 373 and len(coverage['taskGroups']) == 48
scenarios = read(OUT / 'feature-scope-v24-scenarios.json')
assert catalog['publishedFileInventory']['records'] == len(published) == 438
receipt = {'status': 'passed', 'baselineId': BASE, 'distinctPinnedFiles': len(pin_checks),
           'distinctJsonPointers': len(pointer_checks), 'proposalRecords': 38, 'proposalFamilies': 7,
           'sourceFilesIdentityChecked': len(file_bytes), 'recordSourceRangesChecked': row_span_count,
           'distinctSourceRangesChecked': len(span_keys), 'sourceOverlapPairsRecomputed': len(actual_pairs),
           'evidenceRecordsChecked': len(ev), 'publishedFilesUnchanged': 438,
           'featuresUnchanged': 373, 'restorationTasksUnchanged': 48,
           'unrelatedStateAndAuthorizationPreserved': True, 'fullAnalysisCompleted': False,
           'qualification': 'Artifact identity/locator/schema/accounting checks only; no new source semantics, runtime behavior, model request or independent client rebuild verified.'}
(WORK / 'independent-readback.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(receipt, ensure_ascii=False))
