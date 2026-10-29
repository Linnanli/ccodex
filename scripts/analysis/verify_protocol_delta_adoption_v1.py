"""Verify exactly the saved variant decisions, source slices and isolated replay scope."""
from pathlib import Path
import hashlib
import json
import stat

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/protocol-delta-adoption-work'
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'
sha = lambda b: hashlib.sha256(b).hexdigest()
read = lambda p: json.loads(p.read_text())
pins = set()


def visit(value):
    if isinstance(value, dict):
        if {'path', 'bytes', 'sha256'} <= value.keys():
            p = ROOT / value['path']
            raw = p.read_bytes()
            assert len(raw) == value['bytes'] and sha(raw) == value['sha256'], p
            pins.add((value['path'], value['sha256']))
        for v in value.values():
            visit(v)
    elif isinstance(value, list):
        for v in value:
            visit(v)


def pointer(value, path):
    for token in path.split('/')[1:]:
        token = token.replace('~1', '/').replace('~0', '~')
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


doc = read(OUT / 'protocol-delta-adoption-v1.json')
publication = read(WORK / 'publication.json')
visit(doc)
visit(publication)
assert doc['baselineId'] == BASE and not doc['fullBackendAdoptionQualified'] and not doc['fullAnalysisCompleted']
comparison = read(ROOT / doc['comparison']['path'])
expected = {f'/comparisons/{mode}/variantContracts/{i}' for mode, part in comparison['comparisons'].items()
            for i, row in enumerate(part['variantContracts']) if row['effectiveContract']['status'] == 'different'}
assert len(expected) == 11 and {v['comparisonPointer'] for v in doc['variants']} == expected
assert len({v['id'] for v in doc['variants']}) == len(doc['variants']) == 11
decisions = {d['id']: d for d in doc['decisions']}
assert len(decisions) == 2
for variant in doc['variants']:
    row = pointer(comparison, variant['comparisonPointer'])
    assert variant['fieldDifferences'] == row['effectiveContract']['fieldDifferences']
    assert variant['method'] == row['method'] and variant['union'] == row['union']
    assert variant['id'] in decisions[variant['decisionId']]['variants']
assert len(decisions['PDA-D01']['variants']) == 10 and len(decisions['PDA-D02']['variants']) == 1
assert 'not-qualified' in decisions['PDA-D02']['status']
assert 'silently use ordinary fork' in decisions['PDA-D02']['decision']
required = {'id', 'baselineId', 'claim', 'sourcePath', 'sourceHash', 'locator', 'method', 'confidence', 'verificationStatus'}
journal = [json.loads(x) for x in (OUT / 'protocol-delta-adoption-v1-evidence.jsonl').read_text().splitlines()]
assert journal == doc['facts'] and len(journal) == 16
for fact in journal:
    assert required <= fact.keys() and fact['method'] == 'static-code' and fact['confidence'] == 'confirmed'
    p = FROZEN / fact['sourcePath'].removeprefix('app.asar/') if fact['sourceKind'] == 'frozen-JavaScript' else ROOT / fact['sourcePath']
    raw = p.read_bytes()
    assert sha(raw) == fact['sourceHash']
    locator = fact['locator']
    if locator['kind'] == 'byte-range':
        assert sha(raw[locator['start']:locator['endExclusive']]) == fact['spanHash']
    else:
        value = pointer(json.loads(raw), locator['pointer'])
        old = read(ROOT / fact['frozenCounterpart']['path'])
        previous = pointer(old, fact['frozenCounterpart']['pointer'])
        if value.get('title') == 'SubAgentActivityThreadItem':
            assert value['required'] == previous['required']
            assert not {'model', 'reasoningEffort'} & set(value['required'])
            assert value['properties']['model']['type'] == ['string', 'null']
            assert {'type': 'null'} in value['properties']['reasoningEffort']['anyOf']
            assert value.get('additionalProperties', True) is not False and previous.get('additionalProperties', True) is not False
            stripped = json.loads(json.dumps(value))
            for key in ['model', 'reasoningEffort']:
                del stripped['properties'][key]
            assert stripped == previous
        else:
            assert 'experimentalPredictionMode' not in value['properties']
            assert previous['properties']['experimentalPredictionMode']['type'] == 'boolean'
            stripped = json.loads(json.dumps(previous))
            del stripped['properties']['experimentalPredictionMode']
            assert stripped == value
assert len(doc['schemaInputs']) == 6
for item in doc['schemaInputs']:
    source = ROOT / item['pin']['path']
    public = 'public-cli-npm' in str(source)
    manifest = read(OUT / ('public-protocol-generation-npm.json' if public else 'protocol-generation.json'))
    recorded = pointer(manifest, item['manifestPointer'])
    assert recorded['sha256'] == item['pin']['sha256'] and recorded['bytes'] == item['pin']['bytes']
units = {u['label']: u for u in doc['sourceUnits']}
assert len(units) == len(doc['sourceUnits']) == 8
for u in units.values():
    raw = (FROZEN / u['sourcePath'].removeprefix('app.asar/')).read_bytes()
    s = u['byteRange']
    b = raw[s['start']:s['endExclusive']]
    assert sha(raw) == u['sourceHash'] and sha(b) == u['spanHash']
    selected = ROOT / u['selection']['path']
    assert b == selected.read_bytes() and not selected.stat().st_mode & stat.S_IWUSR
select = lambda label: (ROOT / units[label]['selection']['path']).read_text()
assert 'qtn(e,o)' in select('item-completed-case')
assert 'subagentTopology.discoverForSpawn(u,o)' in select('item-completed-case')
assert select('dispatcher-qtn').endswith(':t}')
assert 'model' not in select('subagent-display-case') and 'reasoningEffort' not in select('subagent-display-case')
assert 'experimentalPredictionMode:!0' in select('prediction-fork-argument')
assert 'fallbackToFreshThread:!1' in select('prediction-fge')
assert 'method:`thread/fork`,params:{...e,' in select('prediction-fork-sender')
replay = read(OUT / 'protocol-delta-adoption-v1-replay.json')
assert replay == read(WORK / 'replay.json')
assert len(replay['cases']) == replay['casesPassed'] == 8
assert len({x['id'] for x in replay['cases']}) == 8 and all(x['status'] == 'passed' for x in replay['cases'])
cases = {x['id']: x['observed'] for x in replay['cases']}
assert cases['PDR-01']['variants'] == 3 and len(cases['PDR-03']['rows']) == 10
assert cases['PDR-03']['payloadReferencePreserved'] and cases['PDR-08']['sameObject']
assert cases['PDR-05']['fallbackToFreshThread'] is False
assert cases['PDR-06']['helperCalls'] == cases['PDR-07']['helperCalls'] == 0
for key in ['realServiceCalls', 'modelSubmissions', 'clientLaunches', 'productScenariosExecuted']:
    assert replay[key] == 0
for r in replay['sourceInputs']:
    assert any(all(r[k] == u[k] for k in ['sourcePath', 'sourceHash', 'byteRange', 'spanHash']) for u in units.values())
state = read(OUT / 'analysis-state.json')
before = read(WORK / 'analysis-state.json.before')
assert set(state) == set(before) | {'protocolDeltaAdoption'}
for key in before:
    if key not in ['updatedAtUtc', 'pending', 'stageDecisions', 'publicProtocolComparison']:
        assert state[key] == before[key], key
assert {k: v for k, v in state['publicProtocolComparison'].items() if k != 'adoptionDecisionRefinement'} == before['publicProtocolComparison']
assert state['status'] == 'in-progress' and not state['fullAnalysisCompleted']
assert state['latestBehaviorAuthorizationState']['groupRemaining'] == 0
assert state['stageDecisions']['nextAction']['issueId'] == 'SD-06'
assert state['protocolDeltaAdoption']['result'] == publication['result']
assert state['publicProtocolComparison']['adoptionDecisionRefinement']['result'] == publication['result']
assert state['stageDecisions']['protocolDeltaAdoptionOverlay']['result'] == publication['result']
for name in ['report.md', 'gaps.md']:
    now = (OUT / name).read_text().split('\n\n', 1)
    old = (WORK / (name+'.before')).read_text().split('\n\n', 1)
    assert now[1] == old[1] and 'protocol-delta-adoption-v1.md' in now[0]
result = {'status': 'passed', 'pinsChecked': len(pins), 'schemaInputs': 6, 'differingVariants': 11, 'decisions': 2,
          'sourceFacts': len(journal), 'sourceSelections': len(units), 'isolatedSourceCasesPassed': 8,
          'scopeAndAuthorizationUnchanged': True, 'qualification': 'Selected source/schema decisions only; complete backend and successful prediction remain unverified.'}
receipt = WORK / 'verification.json'
if receipt.exists():
    assert read(receipt) == result
else:
    with receipt.open('x') as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(result, ensure_ascii=False))
