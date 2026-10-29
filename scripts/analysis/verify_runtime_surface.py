"""Independent readback of publication pins, source ranges and unchanged scope."""
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE='codex-26.1007.30912-c5b273322a83'
OUT=ROOT/'analysis'/BASE
WORK=ROOT/'.analysis-local/runtime-surface-disposition-work'


def read(p):return json.loads(p.read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


if __name__=='__main__':
    result=read(OUT/'runtime-surface-disposition.json')
    comparison=read(OUT/result['comparison']['path'])
    pins=result['inputPins']+result['rawPins']
    for p in pins:
        target=ROOT/p['path'];assert target.stat().st_size==p['bytes'] and digest(target)==p['sha256'],p['path']
    assert len(comparison['rows'])==229
    assert sum(x['callSiteCount']for x in comparison['rows'])==1242
    assert Counter(x['status']for x in comparison['rows'])=={
        'declared-in-types-and-api-json':189,'declared-in-types-only':23,'absent-from-both-fixed-descriptions':17}
    assert all(x['publicTypes'].get('callable') or x['publicTypes'].get('constructor')for x in comparison['rows'] if x['publicTypes']['found'])
    dts=(WORK/'attempt-02/electron.d.ts').read_bytes()
    ranges=set()
    def check_range(r):
        assert 0<=r['start']<r['endExclusive']<=len(dts)
        assert hashlib.sha256(dts[r['start']:r['endExclusive']]).hexdigest()==r['sha256']
        ranges.add((r['start'],r['endExclusive']))
    api=read(WORK/'attempt-02/electron-api.json')
    def pointer(value,p):
        for key in p.strip('/').split('/'):
            value=value[int(key)]if isinstance(value,list)else value[key]
        return value
    pointer_count=0
    for row in comparison['rows']:
        for step in row['publicTypes']['chain']:
            if 'range'in step:check_range(step['range'])
            for r in step.get('ranges',[]):check_range(r)
        for r in row['publicTypes'].get('nodes',[]):check_range(r)
        if row['publicTypes'].get('searchedDeclaration'):check_range(row['publicTypes']['searchedDeclaration'])
        for step in row['publicJson'].get('chain',[]):
            node=pointer(api,step['pointer']);assert isinstance(node,dict)and node.get('name');pointer_count+=1
        if row['publicJson'].get('pointer'):
            node=pointer(api,row['publicJson']['pointer'])
            if row['publicJson']['found']:assert node is not None
            pointer_count+=1
        if row['javascriptFunctionBind']:assert row['normalizedApi']+'.bind'==row['canonicalApi']
    source=read(OUT/'raw/runtime-surface-disposition/selected-source.json')
    frozen_ranges=set()
    for unit in source['selectedUnits']:
        frozen=ROOT/'.analysis-local/baselines'/BASE/'extracted'/unit['sourcePath'].removeprefix('app.asar/')
        body=frozen.read_bytes();assert hashlib.sha256(body).hexdigest()==unit['sourceHash']
        selected=body[unit['locator']['start']:unit['locator']['endExclusive']]
        assert hashlib.sha256(selected).hexdigest()==unit['sha256']
        published=OUT/'raw/runtime-surface-disposition/selected-firstparty'/Path(unit['path']).name
        assert selected==published.read_bytes()
        frozen_ranges.add((unit['sourcePath'],unit['locator']['start'],unit['locator']['endExclusive']))
    facts=[json.loads(x)for x in (OUT/'runtime-surface-disposition-evidence.jsonl').read_text().splitlines()]
    assert len(facts)==17 and facts==result['facts']
    required={'id','baselineId','claim','sourcePath','sourceHash','locator','method','confidence','verificationStatus'}
    for fact in facts:
        assert required<=fact.keys() and fact['confidence']in {'confirmed','inferred','unresolved'}
        observation=read(OUT/fact['runtimeObservation']['path'])
        item=pointer(observation,fact['runtimeObservation']['pointer'])
        assert item['canonicalApi']in fact['claim']and item['type']=='undefined'and item['invoked']is False
    attempt=read(OUT/'raw/runtime-surface-disposition/comparison-attempt-01/surface-comparison.json')
    prior={x['canonicalApi']for x in attempt['rows']if not x['publicTypes']['found']}
    current={x['canonicalApi']for x in comparison['rows']if not x['publicTypes']['found']}
    assert prior-current=={'electron.app.dock.downloadFinished','electron.app.dock.setIcon','electron.app.dock.setIcon.bind','electron.app.dock.setMenu'}
    probe=read(OUT/'raw/runtime-surface-disposition/probe-01/observation.json')
    receipt=read(OUT/'raw/runtime-surface-disposition/probe-01/receipt.json')
    assert probe['complete'] and probe['ownedWindowDestroyed'] and probe['windowLoadedUrl']==''
    assert receipt['timedOut']and receipt['exitCode']==-9 and receipt['ownedProcessCheck']=={'exitCode':0,'matchingProcesses':[]}
    assert len(probe['controls'])==6 and all(x['type']=='function'for x in probe['controls'])
    before=read(WORK/'state-before.json');after=read(OUT/'analysis-state.json')
    reduced=copy.deepcopy(after)
    reduced.pop('runtimeSurfaceDisposition')
    reduced['runtimeCapabilityDecisions'].pop('currentSurfaceOverlay')
    reduced['stageDecisions'].pop('runtimeSurfaceOverlay')
    reduced['stageDecisions']['nextAction']=before['stageDecisions']['nextAction']
    reduced['updatedAtUtc']=before['updatedAtUtc']
    assert reduced==before,'unrelated state modified'
    assert digest(ROOT/'docs/reverse-engineering/analysis-plan.md')=='48dd8b65348efd4a8b5634aac5341c4507c262e7b5c88e8ed9368c88eeb96db4'
    assert after['latestBehaviorAuthorizationState']['groupRemaining']==0
    assert read(OUT/'restoration-coverage-v16.json')['counts']==result['currentProductScope']
    assert not result['fullRuntimeRouteSelected'] and not result['fullAnalysisCompleted']
    check={'passed':True,'pinsChecked':len(pins),'distinctPublicDeclarationRanges':len(ranges),
      'publicJsonPointersChecked':pointer_count,'selectedFrozenRanges':len(frozen_ranges),'facts':len(facts),
      'comparisonFalsePositivesRemoved':4,'propertyReadings':17,'positiveControls':6,
      'probeShutdownFailurePreserved':True,'originalPlanUnchanged':True,'unrelatedStatePreserved':True,
      'productCountsUnchanged':True,'fullAnalysisCompleted':False}
    (WORK/'independent-readback.json').write_text(json.dumps(check,indent=2)+'\n')
    print(json.dumps(check))
