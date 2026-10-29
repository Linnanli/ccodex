"""Independent readback of source ranges, publication hashes and state preservation."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/runtime-feature-policy-work'
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'


def read(p):
    return json.loads(p.read_text())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    result = read(OUT / 'runtime-feature-policy-contracts.json')
    pins = result['inputPins'] + result['rawPins']
    for item in pins:
        data = (ROOT / item['path']).read_bytes()
        assert len(data) == item['bytes'] and digest(data) == item['sha256'], item
    sources, spans = {}, set()

    def walk(value):
        if isinstance(value, list):
            for item in value:
                walk(item)
        if not isinstance(value, dict):
            return
        if all(key in value for key in ['sourcePath', 'sourceHash', 'byteRange', 'spanHash']):
            name = value['sourcePath']
            assert name.startswith('app.asar/')
            if name not in sources:
                sources[name] = (FROZEN / name.removeprefix('app.asar/')).read_bytes()
            data = sources[name]
            assert digest(data) == value['sourceHash']
            begin, end = value['byteRange']['start'], value['byteRange']['endExclusive']
            assert 0 <= begin <= end <= len(data)
            assert digest(data[begin:end]) == value['spanHash'], value
            spans.add((name, begin, end, value['spanHash']))
        for item in value.values():
            walk(item)

    units = 0
    for family in ['main', 'startup', 'initial', 'shared']:
        folder = OUT / 'raw/runtime-feature-policy' / family
        source = read(folder / 'source-contracts.json')
        assert source['fullProgramParsed'] and source['parserErrors'] == 0
        walk(source)
        for unit in source['units']:
            data = (folder / unit['file']).read_bytes()
            assert digest(data) == unit['spanHash']
            units += 1
    walk(result['facts'])
    assert units == result['counts']['selectedSourceUnits']
    assert len(result['facts']) == 9 and len(result['gateJoins']) == 2
    evidence = [json.loads(line) for line in (OUT / 'runtime-feature-policy-evidence.jsonl').read_text().splitlines()]
    assert evidence == result['facts']
    replay = read(OUT / 'raw/runtime-feature-policy/replay.json')
    assert replay['passed'] == 12 and replay['failed'] == 0
    assert len(replay['cases']) == 12 and all(x['status'] == 'passed' for x in replay['cases'])
    before, after = read(WORK / 'state-before.json'), read(OUT / 'analysis-state.json')
    for name in ['runtimeFeaturePolicyContracts']:
        overlay = after[name]
        for key in ['result', 'summary', 'evidence']:
            item = overlay[key]
            assert digest((ROOT / item['path']).read_bytes()) == item['sha256']
    normalized = copy.deepcopy(after)
    normalized['updatedAtUtc'] = before['updatedAtUtc']
    del normalized['runtimeFeaturePolicyContracts']
    del normalized['runtimeCapabilityDecisions']['currentFeaturePolicyOverlay']
    del normalized['stageDecisions']['runtimeFeaturePolicyOverlay']
    normalized['stageDecisions']['nextAction'] = before['stageDecisions']['nextAction']
    assert normalized == before, 'Unrelated state changed'
    assert after['latestBehaviorAuthorizationState']['groupRemaining'] == 0
    assert after['fullAnalysisCompleted'] is False
    for name in ['report.md', 'gaps.md']:
        assert (OUT / name).read_text().endswith((WORK / (name + '.before')).read_text())
    assert digest((ROOT / 'docs/reverse-engineering/analysis-plan.md').read_bytes()) == '48dd8b65348efd4a8b5634aac5341c4507c262e7b5c88e8ed9368c88eeb96db4'
    verdict = {'status': 'passed', 'pinsChecked': len(pins), 'frozenSourceFiles': len(sources),
               'distinctSourceRangesChecked': len(spans), 'selectedSourceUnitsChecked': units,
               'sourceFactsChecked': len(evidence), 'isolatedReplayCases': 12,
               'unrelatedStateAndScopeUnchanged': True, 'modelAuthorizationRemaining': 0,
               'originalPlanUnchanged': True, 'fullAnalysisCompleted': False}
    (WORK / 'independent-readback.json').write_text(json.dumps(verdict, indent=2) + '\n')
    print(json.dumps(verdict))


if __name__ == '__main__':
    main()
