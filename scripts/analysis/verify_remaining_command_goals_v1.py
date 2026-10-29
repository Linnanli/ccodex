#!/usr/bin/env python3
"""Read-only verification of frozen source ranges and a bounded review artifact.

This does not execute client code or qualify UI, native, service or build behavior.
"""
import argparse
import collections
import csv
import hashlib
import json
import pathlib
import tarfile


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=pathlib.Path, required=True)
    ap.add_argument('--artifacts', type=pathlib.Path, required=True)
    ap.add_argument('--raw', type=pathlib.Path, required=True)
    args = ap.parse_args()
    root, artifacts, raw = args.root.resolve(), args.artifacts.resolve(), args.raw.resolve()
    base = 'codex-26.1007.30912-c5b273322a83'
    out = root / 'analysis' / base
    frozen = root / '.analysis-local/baselines' / base / 'extracted'
    read = lambda p: json.loads(p.read_text())
    digest = lambda b: hashlib.sha256(b).hexdigest()
    d = read(artifacts / 'remaining-command-goals-v1.json')
    selected = read(raw / 'selected-entries.json')
    census = read(raw / 'literal-census.json')
    hits = read(raw / 'hits-by-command.json')
    legacy = read(out / 'legacy-entry-dispositions-v21.json')
    pending = [x for x in legacy['entries'] if x.get('entryKind') == 'command-metadata-instance' and not x.get('featureIds')]
    assert {x['entryId'] for x in selected} == {x['entryId'] for x in pending}
    assert len(selected) == len(pending) == len(d['records']) == 78
    ids = {x['commandId'] for x in selected}
    assert len(ids) == 78 and ids == {x['commandId'] for x in d['records']}
    assert len(d['groups']) == 34
    groupids = [c for g in d['groups'] for c in g['commandIds']]
    assert len(groupids) == 78 and set(groupids) == ids
    assert d['counts']['dispositions'] == dict(collections.Counter(x['disposition'] for x in d['records']))
    assert sum(v for k, v in d['counts']['dispositions'].items() if k.endswith('-gap')) == 20
    assert all(x['reviewCompleted'] and not x['actualRuntimeVerified'] and not x['functionalEntryFullyResolved']
               and not x['ledgerFeatureAssociationAdopted'] and x['mode'] == 'unknown' for x in d['records'])
    assert d['sourceDispositionBatchCompleted'] and not d['all78BusinessGoalsResolved']
    for k in ['currentFeatureLedgerChanged', 'fullAnalysisCompleted', 'clientImplementationStarted',
              'originalNineCompletionCriteriaChanged']:
        assert d[k] is False
    for k, v in d['counts'].items():
        if k.startswith('new'):
            assert v == 0, (k, v)

    pin_checks = 0
    pin_cache, json_cache, file_hashes = set(), {}, {}
    def pin(ref):
        nonlocal pin_checks
        p = root / ref['path']
        if not p.is_file():
            p = out / ref['path']
        key = (str(p), ref['sha256'], ref.get('jsonPointer'))
        if key in pin_cache:
            return
        assert p.is_file() and p.resolve().is_relative_to(root)
        if str(p) not in file_hashes:
            file_hashes[str(p)] = digest(p.read_bytes())
        assert p.stat().st_size == ref['bytes'] and file_hashes[str(p)] == ref['sha256']
        if 'jsonPointer' in ref:
            if str(p) not in json_cache:
                json_cache[str(p)] = read(p)
            node = json_cache[str(p)]
            for part in ref['jsonPointer'].split('/')[1:]:
                part = part.replace('~1', '/').replace('~0', '~')
                node = node[int(part)] if isinstance(node, list) else node[part]
        pin_checks += 1
        pin_cache.add(key)
    for x in d['inputs']:
        pin(x)
    for x in d['records']:
        for ref in x['candidateFeatureRefs']:
            pin(ref)

    source_cache, source_hashes, checked_ranges = {}, {}, set()
    def span(ref):
        p = ref['sourcePath']
        assert p.startswith('app.asar/')
        full = (frozen / p[len('app.asar/'):]).resolve()
        assert full.is_relative_to(frozen.resolve())
        if p not in source_cache:
            source_cache[p] = full.read_bytes()
            source_hashes[p] = digest(source_cache[p])
        buf = source_cache[p]
        assert source_hashes[p] == ref['sourceHash']
        start, end = ref['byteRange']['start'], ref['byteRange']['endExclusive']
        assert 0 <= start <= end <= len(buf)
        assert digest(buf[start:end]) == ref['spanHash']
        checked_ranges.add((p, start, end, ref['spanHash']))
        return buf[start:end]

    def walk(value):
        if isinstance(value, dict):
            if all(k in value for k in ['path','sha256','bytes']):
                pin(value)
            if all(k in value for k in ['sourcePath', 'sourceHash', 'byteRange', 'spanHash']):
                span(value)
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)

    walk(d)
    walk(selected)
    total_hits = total_nodes = total_units = 0
    expected_units = {}
    by_source = {}
    for p in census['programs']:
        data = read(raw / p['resultPath'])
        assert data['sourcePath'] == p['sourcePath'] and data['sourceHash'] == p['sourceHash']
        assert data['fullProgramParsed'] and data['parseErrors'] == 0 and data['targetCodeExecuted'] is False
        frozen_file = frozen / data['sourcePath'][len('app.asar/'):]
        if data['sourcePath'] not in source_cache:
            source_cache[data['sourcePath']] = frozen_file.read_bytes()
            source_hashes[data['sourcePath']] = digest(source_cache[data['sourcePath']])
        assert source_hashes[data['sourcePath']] == data['sourceHash']
        assert len(source_cache[data['sourcePath']]) == data['sourceBytes'] == p['sourceBytes']
        walk(data)
        by_source[p['sourcePath']] = data
        total_hits += len(data['hits'])
        total_nodes += data['nodeCount']
        total_units += len(data['sourceUnits'])
        assert p['hits'] == len(data['hits']) and p['sourceUnits'] == len(data['sourceUnits'])
        for ref in data['sourceUnits']:
            assert ref['savedPath'] not in expected_units
            expected_units[ref['savedPath']] = span(ref)
    assert len(census['programs']) == 138 and total_hits == 628 and total_nodes == 17135282 and total_units == 919
    assert len((raw / 'searched-js-files.txt').read_text().splitlines()) == 15047
    actual = {str((frozen / p[len('app.asar/'):]).resolve()) for p in by_source}
    # Search lists are repository-relative, independently of the caller cwd.
    listed = {str((root / p).resolve()) for p in (raw / 'complete-matching-files.txt').read_text().splitlines()}
    assert listed == actual
    for cmd, values in hits.items():
        assert cmd in ids
        for h in values:
            original = by_source[h['sourcePath']]['hits'][h['hitIndex']]
            assert original['commandId'] == cmd and original['literal'] == h['literal']
    assert sum(map(len, hits.values())) == total_hits
    for rec in d['records']:
        for h in rec['sourceCensusRefs']:
            assert by_source[h['sourcePath']]['hits'][h['hitIndex']]['commandId'] == rec['commandId']

    closures = {}
    for p in sorted((raw / 'closures').glob('*/source-contracts.json')):
        data = read(p)
        assert data['fullProgramParsed'] and data['parserErrors'] == 0 and data['targetCodeExecuted'] is False
        walk(data)
        closures[p.parent.name] = data
        for ref in data['selectedSourceUnits']:
            key = str(p.parent.relative_to(raw) / ref['savedPath'])
            assert key not in expected_units
            expected_units[key] = span(ref)
    assert len(closures) == 4 and len(expected_units) == 1152
    assert sum(x['nodeCount'] for x in closures.values()) == d['counts']['additionalAstNodes']
    for j in d['scopeResolvedAliasJoins']:
        primary = next(b for b in closures['app-primary']['selectedBindings'] if b['name'] == j['consumerBinding'])
        exp = next(e for e in closures['app-initial']['exports'] if e['exported'] == primary['imported']['imported'])
        expected = {'QS': 'iIc', 'py': 'Pw'}[j['consumerBinding']]
        assert exp['local'] == expected and j['export'] == exp and primary['references'] == j['programResolvedReferences']
    initial = {b['name']:span(b['declaration']).decode() for b in closures['app-initial']['selectedBindings']}
    assert initial['abc'] == 'function abc(){}' and initial['ibc'] == 'function ibc(){}'
    assert 'isActive:s' in initial['iIc'] and 'Pw(e,t,c)' in initial['iIc']
    assert 'appshot-shortcut' in initial['fIc']
    assert 'controlActive(e)' in initial['Ofc']
    assert 'realtimeVoiceRuntime?.requestRealtimeStart' in initial['kfc']

    archive = raw / 'source-units.tar.gz'
    if archive.exists():
        with tarfile.open(archive, 'r:gz') as tf:
            members = tf.getmembers()
            assert len(members) == len(expected_units)
            assert {m.name for m in members} == set(expected_units)
            for m in members:
                assert m.isfile() and tf.extractfile(m).read() == expected_units[m.name]
    else:
        for name, buf in expected_units.items():
            assert (raw / name).read_bytes() == buf

    ev = [json.loads(s) for s in (artifacts / 'remaining-command-goals-v1-evidence.jsonl').read_text().splitlines()]
    required = {'id','baselineId','claim','sourcePath','sourceHash','locator','method','confidence','verificationStatus'}
    assert len(ev) == 78 and len({x['id'] for x in ev}) == 78
    assert {x['reviewEvidenceId'] for x in d['records']} == {x['id'] for x in ev}
    for e in ev:
        assert required <= e.keys() and e['baselineId'] == base and e['confidence'] in ['inferred','unresolved']
        span(dict(sourcePath=e['sourcePath'],sourceHash=e['sourceHash'],**{k:e['locator'][k] for k in ['byteRange','spanHash']}))
        walk(e['locator']['relatedSourceRanges'])
    rows = list(csv.DictReader((artifacts / 'remaining-command-goals-v1.csv').open()))
    assert len(rows) == 78 and {x['commandId'] for x in rows} == ids
    assert len(read(out / 'feature-scope-v42.json')['features']) == 463
    receipt = dict(status='passed',qualification='Saved-source/disposition/provenance verification only; no product, native, service or build acceptance.',
        selectedCommands=78,reviewGroups=34,sourceDispositionBatchCompleted=True,allBusinessGoalsResolved=False,
        censusPrograms=138,additionalFullProgramParses=4,exactKeyHits=628,sourceUnits=1152,
        distinctFrozenSourceFiles=len(source_cache),verifiedDistinctRanges=len(checked_ranges),pinnedFileOrPointerChecks=pin_checks,
        archiveChecked=archive.exists(),currentFeatureLedgerChanged=False,newProductPasses=0)
    print(json.dumps(receipt,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
