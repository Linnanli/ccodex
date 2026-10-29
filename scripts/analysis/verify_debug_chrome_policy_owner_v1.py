"""Read back selected source, source joins, fixtures and the allowed publication delta."""
from pathlib import Path
import hashlib
import json
import stat

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/debug-chrome-policy-owner-work'
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
read = lambda p: json.loads(p.read_text())
pins = set()


def visit(value):
    if isinstance(value, dict):
        if {'path', 'bytes', 'sha256'} <= value.keys():
            p = ROOT / value['path']
            raw = p.read_bytes()
            assert len(raw) == value['bytes'] and sha(raw) == value['sha256'], p
            pins.add((value['path'], value['sha256']))
        for x in value.values():
            visit(x)
    elif isinstance(value, list):
        for x in value:
            visit(x)


doc = read(OUT / 'debug-chrome-policy-owner-v1.json')
publication = read(WORK / 'publication.json')
visit(doc)
visit(publication)
assert doc['baselineId'] == BASE and not doc['fullAnalysisCompleted'] and not doc['fullRuntimeRouteSelected']
units = {x['id']: x for x in doc['sourceUnits']}
assert len(units) == len(doc['sourceUnits']) == 63
files, selected = {}, {}
for u in units.values():
    raw = files.setdefault(u['sourcePath'], (FROZEN / u['sourcePath'].removeprefix('app.asar/')).read_bytes())
    s = u['byteRange']
    span = raw[s['start']:s['endExclusive']]
    assert sha(raw) == u['sourceHash'] and sha(span) == u['spanHash']
    p = ROOT / u['selection']['path']
    assert span == p.read_bytes() and not p.stat().st_mode & stat.S_IWUSR
    for label in u['labels']:
        assert (u['kind'], label) not in selected
        selected[(u['kind'], label)] = span.decode()
assert len(files) == doc['counts']['distinctCompletePrograms'] == 6
assert sum(x['selection']['bytes'] for x in units.values()) == doc['counts']['sourceBytesIncludingOverlappingContext']
s = lambda kind, label: selected[(kind, label)]
assert s('main', 'binding-_') == '_=require("electron")'
assert s('main', 'binding-p') == 'p=require("./build-flavor-CYXpoCFI.js")'
assert s('main', 'binding-r') == 'r=require("./src-CP7XXlpZ.js")'
assert s('main', 'binding-g') == 'g=require("./bootstrap-CooIJpZm.js")'
assert 'default:!1' in s('shared', 'preference-debugChromePagesEnabled')
assert 'key:f.DEBUG_CHROME_PAGES_ENABLED' in s('shared', 'preference-debugChromePagesEnabled')
assert 'agentAccess:`hidden`' in s('shared', 'preference-debugChromePagesEnabled')
assert s('shared', 'binding-Hi') == 'Hi=[L.Dev,L.Agent,L.Nightly,L.InternalAlpha]'
assert 'allowDebugMenu(e){return R.isInternal(e)}' in s('shared', 'binding-R')
flavor = s('flavor', 'binding-m')
assert 'process.env.BUILD_FLAVOR' in flavor and 'process.env.NODE_ENV===`production`?' in flavor
assert 'defaulting to prod in production runtime`),m.Prod)' in flavor
assert 'defaulting to dev in non-production runtime`),m.Dev)' in flavor
assert 'JSON.parse' in s('flavor', 'binding-o') and 'catch' not in s('flavor', 'binding-o')
assert 'if(aE)return aE' in s('bootstrap', 'binding-oE') and 'm=e??l.t.resolve()' in s('bootstrap', 'binding-oE')
assert s('bootstrap', 'context-factory-call-458121') == 'oE($)'
assert s('bootstrap', 'export-I') == 'exports.I=oE'
assert s('main', 'startup-e') == 'e=g.I()'
assert s('main', 'startup-j') == 'j=p.t.allowDebugMenu(o)'
assert s('main', 'startup-le') == 'le=j&&V.settingsStore.getEffective(r.J.debugChromePagesEnabled.key)===!0'
startup = s('main', 'binding-u0e')
positions = [startup.index(x) for x in ['await _.app.whenReady()', 'V=await g.U(', 'await Moe(', 'await V.settingsStore.captureInitialFollowUpQueueMode()', 'await joe(', 'let le=', '_.app.setDebugChromePagesEnabled(le)', 'uf(le)']]
assert positions == sorted(positions)
global_set = s('main', 'method-setGlobalStateValue')
positions = [global_set.index(x) for x in ['_.app.setDebugChromePagesEnabled(e)', 'uf(e)', 'this.globalState.set(r.gs.DEBUG_CHROME_PAGES_ENABLED,e)', 'this.windowManager.sendMessageToAllWindows']]
assert positions == sorted(positions)
assert 'type:`global-state-updated`,keys:[e]' in global_set
assert s('main', 'method-setConfigurationValue') == 'setConfigurationValue(e,t){this.globalState.set(e,t),this.applySettingSideEffects(e,t)}'
assert s('main', 'settings-adapter-write') == 'async write(e,t){this.store.set(e,t),this.afterWrite(e,this.store.get(e))}'
assert 'this.applySettingSideEffects(e,t)' in s('main', 'settings-adapter-injection')
assert 'await this.settings.write(e,r.F(e,t))' in s('main', 'method-setSettingValue')
assert 't===!0&&p.t.allowDebugMenu(p.t.resolve())' in s('main', 'method-applySettingSideEffects')
native = doc['lexicalWitnesses']['main']['selectedNativeCalls']
assert len(native) == 3 and all(x['tryAncestors'] == [] for x in native)
assert 'await e()}catch(r)' in s('bootstrap', 'ready-startup-callback')
assert 'Desktop bootstrap failed to start the main app' in s('bootstrap', 'ready-startup-callback')
assert s('main', 'binding-lf') == 'lf=!1'
assert s('main', 'binding-uf') == 'function uf(e){lf=e}'
assert s('main', 'binding-df') == 'function df(){return lf}'
assert 'o==null||df()?!1:' in s('main', 'binding-Ake')
assert 'r.ii(e.url)!=null&&!df()' in s('main', 'flag-consumer-1533856')
assert 'isRestrictedBrowserNavigation' in s('main', 'flag-consumer-1533856')
assert s('shared', 'binding-Oa') == 'Oa=new Map([[`downloads`,ma],[`history`,va]])'
assert 'return n==null?null:`${n}${t.search}`' in s('shared', 'binding-ka')
assert s('renderer', 'flavor-import-source') == '"./app-shared-8bd9d0399038.js"'
assert s('renderer', 'flavor-import') == 'aen as d' and s('rendererShared', 'export-aen') == 'FM as aen'
assert 'allowDebugMenu(e){return FM.isInternal(e)}' in s('rendererShared', 'binding-IM')
assert 'd.allowDebugMenu(`prod`)' in s('renderer', 'binding-P')
assert 'chrome-untrusted://' in s('renderer', 'binding-F')
for join in doc['sourceJoins']:
    assert set(join['unitIds']) <= units.keys()
assert len(doc['sourceJoins']) == 4
required = {'id', 'baselineId', 'claim', 'sourcePath', 'sourceHash', 'locator', 'method', 'confidence', 'verificationStatus'}
journal = [json.loads(x) for x in (OUT / 'debug-chrome-policy-owner-v1-evidence.jsonl').read_text().splitlines()]
assert journal == doc['facts'] and len(journal) == 17
for fact in journal:
    assert required <= fact.keys() and fact['method'] == 'static-code' and fact['confidence'] == 'confirmed'
    raw = files[fact['sourcePath']]
    s0 = fact['locator']
    assert sha(raw) == fact['sourceHash'] and sha(raw[s0['start']:s0['endExclusive']]) == fact['spanHash']
replay = read(OUT / 'debug-chrome-policy-owner-v1-replay.json')
assert replay == read(WORK / 'replay.json')
assert len(replay['cases']) == replay['casesPassed'] == 15
assert len({x['id'] for x in replay['cases']}) == 15 and all(x['status'] == 'passed' for x in replay['cases'])
observed = {x['id']: x['observed'] for x in replay['cases']}
assert observed['DPR-05']['matrixRows'] == 30
assert observed['DPR-06']['broadcasts'] == [] and not observed['DPR-06']['stored']
assert observed['DPR-07']['flag'] and not observed['DPR-07']['stored']
assert observed['DPR-08']['stored'] and not observed['DPR-08']['flag']
assert observed['DPR-09']['stored'] and not observed['DPR-09']['flag']
assert not observed['DPR-15']['chromePreferenceRow'] and observed['DPR-15']['gpuGroup']
for key in ['originalClientRuns', 'modelSubmissions', 'realNativeCalls', 'productScenariosExecuted']:
    assert replay[key] == 0
for row in replay['sourceInputs']:
    assert any(all(row[k] == u[k] for k in ['sourcePath', 'byteRange', 'spanHash']) for u in units.values())
before = read(WORK / 'analysis-state.json.before')
state = read(OUT / 'analysis-state.json')
for key in before:
    if key not in ['updatedAtUtc', 'pending', 'stageDecisions', 'runtimeAdoptionMatrix', 'runtimeSurfaceDisposition']:
        assert state[key] == before[key], key
assert state['status'] == 'in-progress' and not state['fullAnalysisCompleted']
assert state['latestBehaviorAuthorizationState']['groupRemaining'] == 0
assert state['stageDecisions']['nextAction']['issueId'] == 'SD-03'
assert state['debugChromePolicyOwner']['result'] == publication['result']
assert all(state[k]['debugChromePolicyOwnerRefinement']['result'] == publication['result'] for k in ['runtimeAdoptionMatrix', 'runtimeSurfaceDisposition'])
assert state['stageDecisions']['debugChromePolicyOwnerOverlay']['result'] == publication['result']
for name in ['report.md', 'gaps.md']:
    now = (OUT / name).read_text().split('\n\n', 1)
    old = (WORK / (name + '.before')).read_text().split('\n\n', 1)
    assert now[1] == old[1] and 'debug-chrome-policy-owner-v1.md' in now[0]
result = {'status': 'passed', 'pinsChecked': len(pins), 'sourceFiles': len(files), 'sourceUnits': len(units),
          'sourceFacts': len(journal), 'sourceJoins': 4, 'isolatedSourceCasesPassed': 15, 'scopeAndAuthorizationUnchanged': True,
          'qualification': 'Selected JS source and isolated contracts only; no native policy or complete product acceptance.'}
with (WORK / 'verification.json').open('x') as f:
    f.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False))
