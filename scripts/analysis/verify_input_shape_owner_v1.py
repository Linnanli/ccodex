"""Verify the saved input-shape source, lexical witnesses, replay and bounded state delta."""
from pathlib import Path
import hashlib
import json
import stat

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/input-shape-owner-work'
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
cache, pins, pointers = {}, set(), set()


def read(p):
    p = Path(p)
    if p not in cache:
        cache[p] = json.loads(p.read_text())
    return cache[p]


def at(value, pointer):
    for token in pointer[1:].split('/') if pointer else []:
        token = token.replace('~1', '/').replace('~0', '~')
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def visit(value):
    if isinstance(value, dict):
        if {'path', 'bytes', 'sha256'} <= value.keys():
            p = ROOT / value['path']
            raw = p.read_bytes()
            assert len(raw) == value['bytes'] and sha(raw) == value['sha256'], p
            pins.add((value['path'], value['sha256']))
            if 'jsonPointer' in value:
                at(read(p), value['jsonPointer'])
                pointers.add((value['path'], value['jsonPointer']))
        for item in value.values():
            visit(item)
    elif isinstance(value, list):
        for item in value:
            visit(item)


publication = read(WORK / 'publication.json')
doc = read(OUT / 'input-shape-owner-v1.json')
visit(publication)
visit(doc)
assert doc['baselineId'] == BASE and not doc['fullAnalysisCompleted'] and not doc['fullRuntimeRouteSelected']
units = {u['id']: u for u in doc['sourceUnits']}
assert len(units) == len(doc['sourceUnits']) == 32
by_label, files = {}, {}
for u in units.values():
    if u['sourcePath'] not in files:
        files[u['sourcePath']] = (FROZEN / u['sourcePath'].removeprefix('app.asar/')).read_bytes()
    raw = files[u['sourcePath']]
    span = u['byteRange']
    selected = raw[span['start']:span['endExclusive']]
    assert sha(raw) == u['sourceHash'] and sha(selected) == u['spanHash']
    assert selected == (ROOT / u['selection']['path']).read_bytes()
    assert not (ROOT / u['selection']['path']).stat().st_mode & stat.S_IWUSR
    for label in u['labels']:
        by_label[label] = (u, selected.decode())
assert len(files) == 2
assert by_label['member-supportsInputShape'][0]['nodeType'] == 'ClassProperty'
assert by_label['member-supportsInputShape'][1] == 'supportsInputShape=_.BrowserWindow.isInputShapeSupported();'
assert by_label['owner-instance-2'][1] == 'new Uce(z,c,x)'
assert by_label['provider-manager-binding'][1] == 't=K5(this.options,e)'
assert by_label['new-xpe'][1] == 'new xpe(t,e)'
assert 'this.origin.id,e,t' in by_label['xpe-setPointerRegions'][1]
assert 'r.webContents.id!==e' in by_label['Uce-setPointerRegions'][1]
assert 'e.setInputShape(this.inputShape.map' in by_label['Uce-applyInputShape'][1]
assert 'process.platform===`win32`' in by_label['Uce-applyPointerInteractivityPolicy'][1]
assert by_label['binding-Li-307704'][1] == 'Li=On.avatarOverlay'
assert by_label['On-provider-specifier'][1] == 'fN as On'
assert by_label['On-provider-module'][1] == '"./app-shared-8bd9d0399038.js"'
assert 'Li.setPointerRegions(e,t)' in by_label['pointer-regions-publisher'][1]
for join in doc['sourceJoins']:
    assert set(join['units']) <= units.keys()
first_binding = doc['sourceJoins'][0]['bindingProof']
assert len(first_binding) == 2 and first_binding[0]['parentType'] == 'VariableDeclarator' and first_binding[1]['parentType'] == 'NewExpression'
binding = doc['sourceJoins'][2]['bindingProof']
local = next(x for x in binding if x['declaration']['text'].startswith('On='))
target = next(x for x in binding if x['declaration']['text'] == 'Li=On.avatarOverlay')
assert local['functionScopes'][0]['name'] == 'Zg' and target['functionScopes'][0]['name'] == 'Sv'
assert local['functionScopes'][0]['byteRange']['endExclusive'] < target['functionScopes'][0]['byteRange']['start']
required = {'id', 'baselineId', 'claim', 'sourcePath', 'sourceHash', 'locator', 'method', 'confidence', 'verificationStatus'}
journal = [json.loads(x) for x in (OUT / 'input-shape-owner-v1-evidence.jsonl').read_text().splitlines()]
assert journal == doc['facts'] and len(journal) == 10
for fact in journal:
    assert required <= fact.keys() and fact['confidence'] == 'confirmed' and fact['method'] == 'static-code'
    raw = files[fact['sourcePath']]
    span = fact['locator']
    assert sha(raw) == fact['sourceHash'] and sha(raw[span['start']:span['endExclusive']]) == fact['spanHash']
replay = read(OUT / 'input-shape-owner-v1-replay.json')
assert replay == read(WORK / 'replay.json')
assert len(replay['cases']) == replay['casesPassed'] == 16
assert all(x['status'] == 'passed' for x in replay['cases'])
assert replay['realNativeCalls'] == replay['originalClientRuns'] == replay['modelSubmissions'] == replay['productScenariosExecuted'] == 0
state = read(OUT / 'analysis-state.json')
before = read(WORK / 'analysis-state.json.before')
for key in ['latestBehaviorAuthorizationState', 'featureScopeCurrentView', 'restorationCoverage', 'currentRestorationOrdering', 'logicalModuleContracts']:
    assert state[key] == before[key], key
assert not state['fullAnalysisCompleted'] and state['status'] == 'in-progress'
assert state['stageDecisions']['nextAction']['issueId'] == 'SD-02'
assert 'measurement' in state['stageDecisions']['nextAction']['question']
for name in ['report.md', 'gaps.md']:
    assert (OUT / name).read_text().split('\n\n', 1)[1] == (WORK / (name + '.before')).read_text().split('\n\n', 1)[1]
assert doc['priorEvidenceRefinement']['publicPropertyAbsenceObservationChanged'] is False
assert doc['decision']['fullRuntimeRouteAccepted'] is False
receipt = {'status': 'passed', 'pinsChecked': len(pins), 'jsonPointersChecked': len(pointers),
           'frozenSourceUnitsChecked': 32, 'sourceFacts': 10, 'sourceJoins': 3,
           'isolatedSourceCasesPassed': 16, 'scopeAndAuthorizationUnchanged': True,
           'qualification': 'Selected source and replay evidence only; no target-native or full-product behavior acceptance.'}
with (WORK / 'verification.json').open('x') as handle:
    json.dump(receipt, handle, ensure_ascii=False, indent=2)
    handle.write('\n')
print(json.dumps(receipt, ensure_ascii=False))
