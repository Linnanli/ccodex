#!/usr/bin/env python3
"""Verify provenance and material source boundaries, without evaluating target JS."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'
PREFIX = 'storage-feature-ownership-v1'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pointer(value, ptr):
    for part in ptr.split('/')[1:]:
        part = part.replace('~1', '/').replace('~0', '~')
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def verify(directory):
    document = json.loads((directory / (PREFIX + '.json')).read_text())
    assert document['baselineId'] == BASE
    by_id, text, source_hashes, saved_bytes = {}, {}, {}, 0
    for unit in document['sourceUnits']:
        assert unit['id'] not in by_id
        by_id[unit['id']] = unit
        p = FROZEN / unit['sourcePath'].removeprefix('app.asar/')
        raw = p.read_bytes()
        assert sha(raw) == unit['sourceHash']
        start, end = unit['byteRange']['start'], unit['byteRange']['endExclusive']
        assert 0 <= start < end <= len(raw)
        b = raw[start:end]
        assert sha(b) == unit['spanHash']
        assert (directory / unit['savedPath']).read_bytes() == b
        assert len(b) == unit['bytes']
        saved_bytes += len(b)
        text[(p.name.split('-')[0], unit['label'])] = b.decode()
        source_hashes[str(p)] = sha(raw)
    assert len({u['savedPath'].casefold() for u in by_id.values()}) == len(by_id)
    for program in document['analysisPasses']:
        p = FROZEN / program['file'] if program['file'].startswith('.vite/') else FROZEN / '.vite/build' / program['file']
        assert sha(p.read_bytes()) == program['sourceHash'] and program['parserErrors'] == 0

    refs = set()
    pointers = set()
    cache = {}

    def walk(v):
        if isinstance(v, dict):
            if 'path' in v and 'sha256' in v and 'bytes' in v:
                p = ROOT / v['path']
                if not p.exists():
                    p = OUT / v['path']
                b = p.read_bytes()
                assert sha(b) == v['sha256'] and len(b) == v['bytes'], v['path']
                refs.add(str(p))
                if 'jsonPointer' in v:
                    cache.setdefault(str(p), json.loads(b))
                    pointer(cache[str(p)], v['jsonPointer'])
                    pointers.add((str(p), v['jsonPointer']))
            for child in v.values():
                walk(child)
        elif isinstance(v, list):
            for child in v:
                walk(child)

    walk(document)
    required_evidence = {'id', 'baselineId', 'claim', 'sourcePath', 'sourceHash', 'locator', 'method', 'confidence', 'verificationStatus'}
    evidence = [json.loads(line) for line in (directory / (PREFIX + '-evidence.jsonl')).read_text().splitlines()]
    assert len({e['id'] for e in evidence}) == len(evidence)
    for e in evidence:
        assert required_evidence <= e.keys()
        assert e['baselineId'] == BASE and e['confidence'] in ['confirmed', 'inferred', 'unresolved']
        assert sha((FROZEN / e['sourcePath'].removeprefix('app.asar/')).read_bytes()) == e['sourceHash']
    fact_ids = {f['id'] for f in document['sourceFacts']}
    owner_ids = {o['id'] for o in document['ownerProposals']}
    domain_ids = {d['id'] for d in document['domains']}
    assert len(fact_ids) == 21 and len(owner_ids) == 8 and len(domain_ids) == 16
    module_fields = {'responsibility', 'environment', 'mode', 'sourceRanges', 'imports', 'exports', 'sharedState', 'sideEffects', 'thirdPartyDependencies', 'proposedPath'}
    for f in document['sourceFacts']:
        assert set(f['sourceUnitIds']) <= by_id.keys()
    for o in document['ownerProposals']:
        assert module_fields <= o.keys()
        assert set(o['sourceFactIds']) <= fact_ids and set(o['storageDomainIds']) <= domain_ids
    for link in document['featureStorageLinks']:
        assert set(link['ownerIds']) <= owner_ids and set(link['sourceFactIds']) <= fact_ids
        assert set(link['storageDomainIds']) <= domain_ids
        assert link['operationContractRefs'] and not link['completeStateAuthorityProven'] and not link['runtimeAcceptanceChanged']
        f = pointer(cache[str(ROOT / link['featureOwnershipRef']['path'])], link['featureOwnershipRef']['jsonPointer'])
        assert f['featureId'] == link['featureId'] and f['mode'] == link['mode']
    for scenario in document['additionalUnexecutedStorageScenarios']:
        assert scenario['status'].startswith('unexecuted') and set(scenario['sourceFactIds']) <= fact_ids

    checked = []

    def unit(file, label):
        return text[(file, label if label.startswith(('contains-', 'property-', 'new-', 'export-')) else 'binding-' + label)]

    def contains(name, file, label, *terms):
        s = unit(file, label)
        assert all(term in s for term in terms), (name, [term for term in terms if term not in s])
        checked.append(name)

    def ordered(name, file, label, *terms):
        s = unit(file, label)
        cursor = 0
        for term in terms:
            at = s.find(term, cursor)
            assert at >= 0, (name, term)
            cursor = at + len(term)
        checked.append(name)

    contains('project adapter uses globalState keys', 'main', 'x4', 'this.globalState.set(r.gs.LOCAL_PROJECTS', 'PROJECT_APPEARANCES')
    contains('project backend receives scopedState', 'main', 'new-NHe-9', 'new x4(this.scopedState)')
    ordered('SSH preference write precedes refresh/connect', 'main', 'fKe', 'async setRemoteConnectionAutoConnect(', 'this.appState.set(', 'await this.refreshRemoteConnectionsForHostId(', 'await this.ensureRemoteConnectionConnected(')
    contains('browser AppHost joins manager store to downloads receiver', 'main', 'contains-18c3cf7b42d6', 'getBrowserHostManager()', 'let{downloadStore:f}=u', 'downloads:new Kb(f,e,')
    ordered('download history clear then readback', 'main', 'Xwe', 'async clearHistory()', 'await this.readNativeHistory()', 'clearData({dataTypes:[`downloads`]}', 'await this.readNativeHistory()', 'Download history could not be cleared')
    assert not any(term in unit('main', 'Xwe') for term in ['rmSync', 'unlink', '.rm('])
    checked.append('selected download controller has no explicit rm/unlink call; native clearData internals remain unknown')
    ordered('TOML rename fallback can remove prior target', 'src', 'PF', 'writeFileSync', 'renameSync', 'catch', 'rmSync', 'renameSync')
    ordered('local create performs file then unchecked SQL write', 'src', 'rI', 'FF(h)', 'dF({automation:h', ')),h}')
    ordered('local delete SQL precedes filesystem removal', 'src', 'aI', 'DELETE FROM automations', 'state_cleanup_failed', 'rmSync', 'remove_failed')
    ordered('runs cleanup follows facade successful status and catches errors', 'main', 'z_e', 'r===`deleted`||r===`not_found`', 'i.Br(e)', 'catch{}')
    ordered('migration file copy and unlink outside SQL transaction', 'src', 'zF', 'copyFileSync', 'prepare(`BEGIN`)', 'dF(', 'prepare(`COMMIT`)', 'unlinkSync')
    contains('migration has explicit rollback', 'src', 'zF', 'prepare(`ROLLBACK`)')
    contains('database provider WAL fallback and migration callback', 'src', 'ea', 'PRAGMA journal_mode = WAL', 'PRAGMA synchronous = NORMAL', 'PRAGMA synchronous = FULL', 't(n)', 'n.close()')
    contains('database provider external package', 'src', 'na', 'require("better-sqlite3")')
    contains('exact database flavor names', 'src', 'Qi', 'codex.db', 'codex-dev.db', 'BUILD_FLAVOR', 'NODE_ENV')
    ordered('hosted create verifies before local cache adoption', 'main', 'ppe', 'async create(', 'await this.saveAndVerify(', 'i.Tn(')
    ordered('service save and independent readback', 'main', 'ppe', 'async saveAndVerify(', '/automations/save', '/automation/${encodeURIComponent(a.id)}', 'Saved automation could not be independently verified')
    ordered('enrollment status flush and memory rollback', 'main', 'ppe', 'async persistStatus(', 'this.globalState.update(', 'await this.globalState.flushOrThrow()', 'catch(e)', 'this.globalState.set(')
    ordered('salt reads, tries write, retains memory value', 'src', 'ZF', 'readFileSync', 'randomUUID', 'writeFileSync', 'catch{}', 'aF=t,t')
    contains('Windows state and native package roots stay distinct', 'bootstrap', 'wn', 'windows-msix-updater', 'getPackageLocalCachePath()', 'windows-updates', 'prepared.msix', 'staged-msix.json')
    ordered('Windows bytes validation precedes rename; native metadata follows', 'bootstrap', '_n', 'writeFile(o,n)', 't.sha256!=null&&r!==t.sha256', 'rename(o,a)', 'readPackageMetadata(a)', 'finally', 'rm(o,')
    ordered('Windows stage precedes state temp/rename', 'bootstrap', 'wn', 'async performCheck()', 'nativeAddon.stagePackage', 'writeFile(`${o}.tmp`', 'rename(`${o}.tmp`,o)')
    contains('Windows Store downloads remain native operations', 'bootstrap', 'Mn', 'trySilentDownloadStoreUpdates', 'trySilentDownloadAndInstallStoreUpdates')
    contains('macOS native boundary explicit', 'bootstrap', 'Kn', 'sparkle.node', 'c.checkForUpdates()', 'c.installLatestUpdate()')
    contains('Linux installed metadata and package manager boundary', 'bootstrap', 'Ze', 'Linux updates are managed by the package manager.', 'f.app.relaunch()')
    dep = document['dependencyPolicy']['selectedDependency']
    meta_bytes = (FROZEN / dep['sourcePath'].removeprefix('app.asar/')).read_bytes()
    assert sha(meta_bytes) == dep['sourceHash']
    meta = json.loads(meta_bytes)
    assert meta['name'] == dep['name'] and meta['version'] == dep['version'] == '12.11.1'
    assert not dep['generateImplementationCopy']
    assert not document['fullAnalysisCompleted'] and not document['implementationReady']
    assert not document['completeStorageDenominatorEstablished'] and not document['fullStorageIsolationProven']
    assert 'all retained features storage mapping' in document['batchClosure']['doesNotClose']
    c = document['counts']
    assert c['savedSourceUnits'] == len(by_id) == 115
    assert c['fullProgramParsePasses'] == len(document['analysisPasses']) == 18
    assert c['qualifiedFeatureLinks'] == len(document['featureStorageLinks']) == 17
    assert c['newSourceFeatureLinks'] == 11 and c['reusedAuthorityFeatureLinks'] == 6
    assert c['otherFiniteFeatureAssignmentsUnchanged'] + c['qualifiedFeatureLinks'] == 426
    for k in ['newFeatureDefinitions', 'newReaRuns', 'newClientLaunches', 'newModelSubmissions', 'newServiceCalls', 'newProductScenarioPasses', 'newClientImplementation']:
        assert c[k] == 0
    return {'status': 'passed', 'scope': 'frozen byte identity, source fact boundaries and design reference checks only; no product/native/build acceptance',
            'sourceUnits': len(by_id), 'savedSourceBytes': saved_bytes, 'frozenSourceFiles': len(source_hashes), 'evidenceRecords': len(evidence),
            'referencedFiles': len(refs), 'jsonPointers': len(pointers), 'semanticSourceChecks': checked, 'featureLinks': len(document['featureStorageLinks']),
            'fullAnalysisCompleted': False, 'newProductScenarioPasses': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, default=ROOT / '.analysis-local/storage-feature-ownership-work/publication')
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    result = verify(args.directory)
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
