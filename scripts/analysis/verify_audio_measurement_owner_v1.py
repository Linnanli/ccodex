"""Read back source claims, source joins, isolated behavior and authorized state delta."""
from pathlib import Path
import hashlib
import json
import stat

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/audio-measurement-owner-work'
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'
sha = lambda b: hashlib.sha256(b).hexdigest()
read = lambda p: json.loads(p.read_text())
pins = set()


def visit(value):
    if isinstance(value, dict):
        if {'path', 'bytes', 'sha256'} <= value.keys():
            p = ROOT / value['path']
            b = p.read_bytes()
            assert len(b) == value['bytes'] and sha(b) == value['sha256'], p
            pins.add((value['path'], value['sha256']))
        for item in value.values():
            visit(item)
    elif isinstance(value, list):
        for item in value:
            visit(item)


doc = read(OUT / 'audio-measurement-owner-v1.json')
publication = read(WORK / 'publication.json')
visit(doc)
visit(publication)
assert doc['baselineId'] == BASE and not doc['fullAnalysisCompleted'] and not doc['fullRuntimeRouteSelected']
units = {x['id']: x for x in doc['sourceUnits']}
assert len(units) == len(doc['sourceUnits']) == 44
files = {}
by_label = {}
for u in units.values():
    raw = files.setdefault(u['sourcePath'], (FROZEN / u['sourcePath'].removeprefix('app.asar/')).read_bytes())
    s = u['byteRange']
    b = raw[s['start']:s['endExclusive']]
    assert sha(raw) == u['sourceHash'] and sha(b) == u['spanHash']
    assert b == (ROOT / u['selection']['path']).read_bytes()
    assert not (ROOT / u['selection']['path']).stat().st_mode & stat.S_IWUSR
    for label in u['labels']:
        by_label[(u['sourcePath'], label)] = b.decode()
assert len(files) == doc['counts']['distinctCompletePrograms'] == 3


def selected(kind, label):
    prefix = {'main': 'app.asar/.vite/build/main-', 'shared': 'app.asar/webview/assets/app-shared-',
              'initial': 'app.asar/webview/assets/app-initial-'}[kind]
    return next(v for (p, lab), v in by_label.items() if p.startswith(prefix) and lab == label)


assert selected('main', 'binding-_') == '_=require("electron")'
assert selected('main', 'property-microphoneDiagnostics-3331688') == 'microphoneDiagnostics:new vIe'
assert selected('main', 'property-histogramCollector-3333052') == 'histogramCollector:jNe()'
assert 'constructor(){super(),gIe()}' in selected('main', 'binding-vIe')
assert 'dZ=!0' in selected('main', 'binding-gIe') and 'whenReady().then(hZ)' in selected('main', 'binding-gIe')
assert 'Media.AudioSystem.GetDeviceDescription.Result' in selected('main', 'binding-uZ')
assert 'configureMeasurementCollection([uZ])' in selected('main', 'binding-hZ')
assert 'pZ+=e.count' in selected('main', 'binding-_Ie') and 'fZ+=e.count' in selected('main', 'binding-_Ie')
assert 'counter_discontinuity' in selected('main', 'binding-_Ie')
assert 'this.app.on(`child-process-gone`,this.onChildProcessGone)' in selected('main', 'audio-service-register')
assert 't.type===`Utility`&&t.serviceName===`audio.mojom.AudioService`&&vle(t)' in selected('main', 'audio-service-onChildProcessGone')
assert selected('shared', 'export-fN') == 'e6 as fN'
assert selected('initial', 'import-Pd') == 'fN as Pd'
assert selected('initial', 'import-uh') == 's$t as uh'
assert selected('shared', 'export-s$t') == 'JL as s$t'
assert 'Pd.microphoneDiagnostics' in selected('initial', 'binding-Gia')
assert 'Math.random()<.01&&Gia' in selected('initial', 'Gia-caller-5350443')
assert 't.name===`NotFoundError`||t.name===`DevicesNotFoundError`' in selected('initial', 'Gia-caller-5350443')
assert 'onDiagnostic:e=>{}' in selected('initial', 'media-setup-analytics')
assert 'qia=2e3' in selected('initial', 'binding-Jia')
assert 'structuredClone(n)' in selected('shared', 'binding-Gli') and 'finally{t.d()}' in selected('shared', 'binding-Gli')
assert 'e[Symbol.dispose]?.()' in selected('shared', 'binding-JL')
for join in doc['sourceJoins']:
    assert set(join['unitIds']) <= units.keys()
assert len(doc['sourceJoins']) == 4
witness = doc['lexicalWitnesses']
assert len(witness['initial']['PdDeclarationsAllScopes']) == 1
assert witness['initial']['PdDeclarationsAllScopes'][0]['type'] == 'ImportSpecifier'
assert any(x['exported'] == 'fN' and x['local'] == 'e6' for x in witness['shared']['exports'])
assert len([x for x in witness['initial']['selectedCalls'] if x.get('callee') == 'Gia']) == 2
required = {'id', 'baselineId', 'claim', 'sourcePath', 'sourceHash', 'locator', 'method', 'confidence', 'verificationStatus'}
journal = [json.loads(line) for line in (OUT / 'audio-measurement-owner-v1-evidence.jsonl').read_text().splitlines()]
assert journal == doc['facts'] and len(journal) == 16
for fact in journal:
    assert required <= fact.keys() and fact['confidence'] == 'confirmed' and fact['method'] == 'static-code'
    b = files[fact['sourcePath']]
    s = fact['locator']
    assert sha(b) == fact['sourceHash'] and sha(b[s['start']:s['endExclusive']]) == fact['spanHash']
replay = read(OUT / 'audio-measurement-owner-v1-replay.json')
assert replay == read(WORK / 'replay.json')
assert len(replay['cases']) == replay['casesPassed'] == 22
assert all(x['status'] == 'passed' for x in replay['cases'])
assert len({x['id'] for x in replay['cases']}) == 22
observed = {x['id']: x['observed'] for x in replay['cases']}
assert observed['AMR-04']['deliveredReplyCount'] == 6 and observed['AMR-04']['droppedReplyCount'] == 4
assert observed['AMR-06']['reset']['generation'] == 2 and observed['AMR-06']['ready']['deliveredReplyCount'] == 0
assert observed['AMR-11']['configureSettlesBeforeNative'] and observed['AMR-11']['collectAwaitsNative']
assert observed['AMR-14']['result']['nested']['count'] == 3 and observed['AMR-14']['disposed'] == 1
assert observed['AMR-19']['delayMs'] == 2000 and observed['AMR-19']['result']['status'] == 'timed_out'
assert observed['AMR-20']['disposed'] == 1 and observed['AMR-20']['diagnostic']['browser']['value']['requestedDevicePresent']
for k in ['realNativeCalls', 'originalClientRuns', 'modelSubmissions', 'productScenariosExecuted']:
    assert replay[k] == 0
for replay_unit in replay['sourceInputs']:
    assert any(replay_unit['sourcePath'] == x['sourcePath'] and replay_unit['byteRange'] == x['byteRange'] and replay_unit['spanHash'] == x['spanHash'] for x in units.values())
primary = read(OUT / 'audio-measurement-primary-review-v1.json')
assert primary['frozenSourceFactCountAdded'] == 0 and len(primary['sources']) == 2
assert 'no immutable commit' in primary['sources'][0]['retrieval']
assert doc['decision']['resolutionBuckets']['notReopenedByMissingRuntime']
assert not doc['decision']['consumerOwnership']['completeConsumerCensus']
before = read(WORK / 'analysis-state.json.before')
state = read(OUT / 'analysis-state.json')
for k in ['latestBehaviorAuthorizationState', 'featureScopeCurrentView', 'restorationCoverage', 'currentRestorationOrdering', 'logicalModuleContracts', 'inputShapeOwner']:
    assert state[k] == before[k], k
for k in before:
    if k not in ['updatedAtUtc', 'pending', 'stageDecisions', 'runtimeAdoptionMatrix', 'runtimeSurfaceDisposition']:
        assert state[k] == before[k], k
assert state['status'] == 'in-progress' and not state['fullAnalysisCompleted']
assert 'RAM-04' in state['stageDecisions']['nextAction']['question']
assert state['audioMeasurementOwner']['result'] == publication['result']
assert all(state[k]['audioMeasurementOwnerRefinement']['result'] == publication['result'] for k in ['runtimeAdoptionMatrix', 'runtimeSurfaceDisposition'])
assert state['stageDecisions']['audioMeasurementOwnerOverlay']['result'] == publication['result']
for name in ['report.md', 'gaps.md']:
    now = (OUT / name).read_text().split('\n\n', 1)
    old = (WORK / (name + '.before')).read_text().split('\n\n', 1)
    assert now[1] == old[1] and 'audio-measurement-owner-v1.md' in now[0]
result = {'status': 'passed', 'pinsChecked': len(pins), 'frozenSourceFiles': len(files), 'frozenSourceUnitsChecked': len(units),
          'sourceFacts': len(journal), 'sourceJoins': 4, 'isolatedSourceCasesPassed': 22, 'scopeAndAuthorizationUnchanged': True,
          'qualification': 'Selected source and isolated behavior only; no native provider, live RPC or full product acceptance.'}
with (WORK / 'verification.json').open('x') as handle:
    handle.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False))
