"""Readback of source ranges, classification conservation and state isolation."""
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/codex-26.1007.30912-c5b273322a83'
WORK = ROOT / '.analysis-local/resume-provider-resolution-work'
FROZEN = ROOT / '.analysis-local/baselines/codex-26.1007.30912-c5b273322a83/extracted'
OP = 'operation:ttc:TTC-OP-thread-resume'


def read(p):
    return json.loads(p.read_text())


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pointer(value, path):
    for key in path.strip('/').split('/'):
        key = key.replace('~1', '/').replace('~0', '~')
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def main():
    result = read(OUT / 'resume-provider-resolution.json')
    cached, pins, spans = {}, set(), set()

    def data(path):
        if path not in cached:
            cached[path] = path.read_bytes()
        return cached[path]

    def pin_path(p):
        path = OUT / p['path']
        return path if path.is_file() else ROOT / p['path']

    def verify(value):
        if isinstance(value, dict):
            if {'path', 'sha256', 'bytes'} <= value.keys():
                path = pin_path(value); b = data(path)
                assert len(b) == value['bytes'] and sha(b) == value['sha256'], path
                pins.add(str(path))
            if {'sourcePath', 'sourceHash', 'byteRange', 'spanHash'} <= value.keys():
                path = FROZEN / value['sourcePath'].removeprefix('app.asar/')
                b = data(path); r = value['byteRange']
                assert sha(b) == value['sourceHash']
                assert 0 <= r['start'] < r['endExclusive'] <= len(b)
                assert sha(b[r['start']:r['endExclusive']]) == value['spanHash']
                spans.add((str(path), r['start'], r['endExclusive']))
            for item in value.values():
                verify(item)
        elif isinstance(value, list):
            for item in value:
                verify(item)

    verify(result)
    for label, u in result['sourceUnits'].items():
        p = pin_path(u['origin'])
        original = pointer(read(p), u['origin']['jsonPointer'])
        if label != 'connection-export-pn':
            for k in ['sourcePath', 'sourceHash', 'byteRange', 'spanHash']:
                assert u[k] == original[k], (label, k)
        b = data(FROZEN / u['sourcePath'].removeprefix('app.asar/'))
        assert data(pin_path(u['savedSource'])) == b[u['byteRange']['start']:u['byteRange']['endExclusive']]
    assert result['startupGate']['declarations'][0]['expression'] == 'z=!_.app.isPackaged'
    assert result['startupGate']['declarations'][1]['expression'] == 'ne=z&&process.env.CODEX_APP_SERVER_MANAGER_IN_MAIN===`1`'
    assert result['lexicalReceiverEvidence']['expression'] == 'l.resumeThread({threadId:e})'
    receiver = result['lexicalReceiverEvidence']['receiverBinding']['definitions']
    assert len(receiver) == 1
    loc = receiver[0]['declaration']; b = data(FROZEN / loc['sourcePath'].removeprefix('app.asar/'))
    assert b[loc['byteRange']['start']:loc['byteRange']['endExclusive']] == b'l=ge(t,de())'
    required = {'id', 'baselineId', 'claim', 'sourcePath', 'sourceHash', 'locator', 'method', 'confidence', 'verificationStatus'}
    facts = [json.loads(line) for line in (OUT / 'resume-provider-resolution-evidence.jsonl').read_text().splitlines()]
    assert facts == result['sourceFacts'] and len(facts) == 12
    assert all(required <= f.keys() and f['confidence'] in ['confirmed', 'inferred', 'unresolved'] for f in facts)
    for f in facts:
        u = result['sourceUnits'][f['sourceUnitIds'][0]]
        assert f['sourcePath'] == u['sourcePath'] and f['sourceHash'] == u['sourceHash']
        assert {k: f['locator'][k] for k in ['start', 'endExclusive']} == u['byteRange']

    old = read(OUT / 'feature-scope-v25.json'); new = read(OUT / 'feature-scope-v26.json')
    assert old['features'] == new['features'] and len(new['features']) == 373
    assert new['supportOperations'][:-1] == old['supportOperations']
    assert new['operationReviewQueue'] == [] and new['supportOperations'][-1]['operationId'] == OP
    assert new['supportOperations'][-1]['excludedFromProductScope'] is False
    assert new['supportOperations'][-1]['operationEquivalenceClaimed'] is False
    expected_roots = copy.deepcopy(old['rootCandidateDispositions'])
    for r in expected_roots:
        if r['operationId'] == OP:
            r['role'] = 'support'
    assert new['rootCandidateDispositions'] == expected_roots
    assert len(new['supportOperations']) == 117
    for k, v in old['counts'].items():
        if k not in ['supportOperations', 'queuedOperations', 'rootCandidateDispositionCounts', 'originalRootCandidateDispositionCounts']:
            assert new['counts'][k] == v, k
    for k in ['rootCandidateDispositionCounts', 'originalRootCandidateDispositionCounts']:
        expected = copy.deepcopy(old['counts'][k]); expected['support'] += 1; expected['pending'] -= 1
        assert new['counts'][k] == expected
    assert new['counts']['supportOperations'] == 117 and new['counts']['queuedOperations'] == 0
    changed = {'supportOperations', 'operationReviewQueue', 'rootCandidateDispositions', 'counts', 'previousScopeRef', 'resumeProviderDisposition', 'newDefinitionIds'}
    assert {k:v for k,v in old.items() if k not in changed} == {k:v for k,v in new.items() if k not in changed}
    assert (OUT / 'feature-scope-v25.csv').read_bytes() == (OUT / 'feature-scope-v26.csv').read_bytes()
    before_coverage = read(OUT / 'restoration-coverage-v16.json'); coverage = read(OUT / 'restoration-coverage-v17.json')
    changed = {'previousSnapshot', 'featureLedger', 'supportOperations', 'counts', 'resumeProviderDisposition'}
    assert {k:v for k,v in before_coverage.items() if k not in changed} == {k:v for k,v in coverage.items() if k not in changed}
    assert coverage['supportOperations'] == new['supportOperations']
    expected = copy.deepcopy(before_coverage['counts']); expected['supportOperations'] = 117
    assert coverage['counts'] == expected
    assert len(coverage['taskGroups']) == 48
    assert Counter(f['mode'] for f in new['features']) == {'unknown': 372, 'shared': 1}
    scenarios = read(OUT / 'feature-scope-v24-scenarios.json')
    assert len(scenarios['scenarios']) == 1216 and scenarios['executed'] == 0
    assert all(s.get('executionStatus', s.get('status')) == 'not-executed' for s in scenarios['scenarios'])
    ordering = read(OUT / 'restoration-current-ordering-v1.json')
    assert len(ordering['integrationGraph']) == 57
    assert before_coverage['taskGroups'] == coverage['taskGroups']

    before = read(WORK / 'state-before.json'); after = read(OUT / 'analysis-state.json')
    changed = {'updatedAtUtc', 'resumeProviderResolution', 'featureScopeCurrentView', 'restorationCoverageCurrentOverlay', 'stageDecisions', 'pending'}
    assert {k:v for k,v in before.items() if k not in changed} == {k:v for k,v in after.items() if k not in changed}
    stage_changed = {'resumeProviderOverlay', 'nextAction'}
    assert {k:v for k,v in before['stageDecisions'].items() if k not in stage_changed} == {k:v for k,v in after['stageDecisions'].items() if k not in stage_changed}
    assert after['fullAnalysisCompleted'] is False and after['status'] == 'in-progress'
    verify(after['resumeProviderResolution']); verify(after['restorationCoverageCurrentOverlay'])
    assert after['featureScopeCurrentView']['ledger']['path'] == 'feature-scope-v26.json'
    assert after['featureScopeCurrentView']['counts'] == new['counts']
    for n in ['report.md', 'gaps.md']:
        tail = (OUT / 'raw/resume-provider-resolution' / (n + '.before')).read_bytes()
        current = (OUT / n).read_bytes()
        assert current.endswith(tail) and b'resume-provider-resolution.md' in current[:-len(tail)]
    assert sha((ROOT / 'docs/reverse-engineering/analysis-plan.md').read_bytes()) == '48dd8b65348efd4a8b5634aac5341c4507c262e7b5c88e8ed9368c88eeb96db4'
    for key in ['newReaRuns', 'newModelSubmissions', 'newClientRuns', 'newTargetCodeExecutions', 'newUserFeatures', 'newProductScenarioPasses']:
        assert result['counts'][key] == 0
    assert len(result['sourceAnalysisQueries']) == 7
    assert sum(q['nodeCount'] for q in result['sourceAnalysisQueries']) == result['counts']['parsedProgramNodes']
    immutable = list((OUT / 'raw/resume-provider-resolution').rglob('*'))
    immutable += [OUT / n for n in ['resume-provider-resolution.json', 'resume-provider-resolution.md', 'resume-provider-resolution-evidence.jsonl', 'feature-scope-v26.json', 'feature-scope-v26.csv', 'restoration-coverage-v17.json']]
    assert all(p.stat().st_mode & 0o222 == 0 for p in immutable if p.is_file())
    receipt = {'result': 'passed', 'distinctPinnedFiles': len(pins), 'distinctSourceRanges': len(spans), 'savedFirstPartySelections': 55, 'facts': 12, 'featuresUnchanged': 373, 'supportOperations': 117, 'queuedOperations': 0, 'tasksUnchanged': 48, 'unexecutedScenarios': 1216, 'unrelatedStateAndAuthorizationsPreserved': True, 'fullAnalysisCompleted': False}
    with (WORK / 'independent-readback.json').open('x') as stream:
        stream.write(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
