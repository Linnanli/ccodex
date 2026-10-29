"""Publish a scoped settings batch using explicit evidence and preservation checks.

Usage: python3 scripts/analysis/publish_settings_batch.py settings_history_batch08_specs
"""
import collections
import copy
import csv
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
BASE='codex-26.1007.30912-c5b273322a83'
OUT=ROOT/'analysis'/BASE
FROZEN=ROOT/'.analysis-local/baselines'/BASE/'extracted'
read=lambda p:json.loads(p.read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')

def retained_boundary_links(state, prefix=''):
    overlay=state['analysisMilestones'].get('currentScopeOverlay',{})
    links=[]
    plan=state['stageDecisions'].get('latestConsolidation',{}).get('plan') or state['analysisMilestones'].get('plan')
    if plan is not None:links.append(f"[当前统一实施计划]({prefix}{plan['path']})")
    decision_summary=state['stageDecisions'].get('summary')
    if decision_summary:links.append(f"[当前分析关闭条件]({prefix}{decision_summary['path']})")
    for key,label in [('modeOwnershipOverlay','归档共享模式证据'),('legacyEntryDispositionOverlay','旧入口逐ID处置')]:
        record=state['featureScopeCurrentView'].get(key)
        if record:links.append(f"[{label}]({prefix}{record['path']})")
    for key,label in [('productFlowOwnershipOverlay','首页分流与共享提交边界'),
                      ('runtimeFeasibilityOverlay','原生浏览器运行时对照'),
                      ('browserCloneRouteOverlay','浏览器克隆合同'),
                      ('publicHistoryDuplicateOverlay','公开历史复制实测及失败属性'),
                      ('accountAccessPublicationOverlay','共享账户访问与模式剥离边界')]:
        summary=overlay.get(key,{}).get('summary')
        if summary is not None:links.append(f"[{label}]({prefix}{summary['path']})")
    return '其他当前恢复决定：'+'、'.join(links)+'；继续作为对应模块的恢复依据。\n\n' if links else ''

def publish(module):
    cfg=module.configuration();specs=module.specifications()
    number=cfg['number'];tag=f'{number:02}';prefix=f'settings-operation-batch-{tag}'
    old_version=cfg['previousScope'];version=old_version+1;old_cv=cfg['previousCoverage'];cv=old_cv+1
    work=ROOT/'.analysis-local'/cfg['work'];stage=work/'deliverables';raw=stage/'raw'/prefix
    names=[prefix+'.json',prefix+'.md',f'feature-scope-v{version}.json',f'feature-scope-v{version}.csv',
           f'feature-scope-v{version}-scenarios.json',f'restoration-coverage-v{cv}.json']
    assert not stage.exists() and not any((OUT/n).exists() for n in names)
    before=read(OUT/'analysis-state.json');assert before['updatedAtUtc']==cfg['expectedState']
    current_plan=(before['stageDecisions'].get('latestConsolidation',{}).get('plan') or before['analysisMilestones']['plan'])['path']
    old_path=OUT/f'feature-scope-v{old_version}.json';old_scenario_path=OUT/before['featureScopeCurrentView']['scenarios']['path']
    old_coverage_path=OUT/f'restoration-coverage-v{old_cv}.json'
    assert old_path.name==before['featureScopeCurrentView']['ledger']['path']
    assert old_coverage_path.name==before['restorationCoverage']['path']
    old=read(old_path);old_scenarios=read(old_scenario_path);old_coverage=read(old_coverage_path)
    obs=read(work/'isolated-observations.json');assert obs['failed']==0 and obs['passed']==len(obs['cases'])
    assert obs['productScenariosExecuted']==obs['modelSubmissionsAdded']==obs['originalClientRunsAdded']==0
    raw.mkdir(parents=True);write(raw/'analysis-state-before.json',before)
    for folder in cfg['selections']:shutil.copytree(work/folder,raw/folder)
    shutil.copyfile(work/'isolated-observations.json',raw/'isolated-observations.json')
    for name in cfg['scriptFiles']+['settings_operations_ast.mjs','publish_settings_batch.py']:
        shutil.copyfile(ROOT/'scripts/analysis'/name,raw/name)
    for attempt in cfg.get('priorProbeAttempts',[]):
        for key in ['observations','probeScript']:shutil.copyfile(work/attempt[key],raw/attempt[key])
    for name in cfg.get('executionArtifacts',[]):shutil.copyfile(work/name,raw/name)
    for p in [ROOT/'README.md',OUT/'report.md',OUT/'gaps.md']:shutil.copyfile(p,raw/(p.name+'.before'))
    def pin(p):
        b=p.read_bytes()
        try:name=str(p.relative_to(stage))
        except ValueError:name=str(p.relative_to(OUT))
        return dict(path=name,bytes=len(b),sha256=sha(b))
    def ref(p,pointer):return dict(**pin(p),jsonPointer=pointer)
    folders={name:raw/name for name in cfg['selections']};metadata={name:read(p/'source-contracts.json') for name,p in folders.items()}
    cached_sources={};verified_units=set()
    def span(record):
        name=record['sourcePath']
        if name not in cached_sources:cached_sources[name]=(FROZEN/name.removeprefix('app.asar/')).read_bytes()
        b=cached_sources[name];r=record['byteRange']
        assert sha(b)==record['sourceHash'] and sha(b[r['start']:r['endExclusive']])==record['spanHash']
    def unit(folder,name):
        p=folders[folder]/'source-contracts.json';d=metadata[folder]
        matches=[(i,u) for i,u in enumerate(d['units']) if u['name']==name];assert len(matches)==1,(folder,name)
        i,u=matches[0];span(u);assert sha((p.parent/u['sourceFilename']).read_bytes())==u['spanHash']
        verified_units.add((folder,name));return ref(p,f'/units/{i}')
    for folder,d in metadata.items():
        assert d['fullProgramParsed'] and not d['targetCodeExecuted']
        for u in d['units']:unit(folder,u['name'])
    for selected in obs['sourceSelections']:span(selected)
    write(raw/'selection-qualification.json',{'completeProgramSelections':len(metadata),'sourceUnits':len(verified_units),
        'parser':'Existing fixed full-Program AST selector with explicit500-unit cap; no target modules evaluated.',
        'failedSelectionAttempts':0,'previousGoalTurnClassification':cfg.get('previousGoalTurnClassification','progress: prior batch published and independently read back'),
        'priorProbeAttempts':[{**attempt,'observations':pin(raw/attempt['observations']),
            'probeScript':pin(raw/attempt['probeScript'])} for attempt in cfg.get('priorProbeAttempts',[])],
        'scope':'Same-Program lexical closure; imported implementations and all actual service receivers remain explicit boundaries.'})
    dispositions=read(OUT/'settings-section-dispositions.json');visibility=read(OUT/'settings-mode-boundary-contracts.json')
    entries=[]
    for slug,page,task in cfg['entries']:
        i,row=next((i,r) for i,r in enumerate(dispositions['entries']) if r['slug']==slug)
        review=next(r for r in visibility['settingsSectionReviews'] if r['slug']==slug)
        entries.append({'slug':slug,'page':page,'taskId':task,'surfaceId':row['entryId'],'factoryId':row['factoryId'],
            'factoryRef':row['factoryRef'],'routeInstanceRef':ref(OUT/'settings-registry-contracts.json',f"/routeInstances/{row['savedSettingsRouteInstance']}"),
            'staticRouteInstance':row['savedSettingsRouteInstance'],'accessFamily':row['accessFamily'],
            'availableInReducedHostList':review['availableInReducedList'],
            'priorDispositionRef':ref(OUT/'settings-section-dispositions.json',f'/entries/{i}'),
            'outerConditionRef':row['outerEntryConditionRef'],'visibilityRef':row['visibilityRef'],'sectionRef':row['sectionRef'],
            'conditions':['Preserve outer host/access/loading/error/redirect precedence and every operation-specific identity/account/flag/eligibility guard.',
                'Actual account/user/platform/flag values and selected product mode remain unobserved.'],
            'mode':'unknown','actualMountObserved':False,'confirmedExclusion':False,
            'scopeQualification':'Finite local controls and explicitly retained imported/delegated families; not full-page/service/mode closure.'})
    n=len(specs);m=len(cfg['mechanisms']);previous_n=len(old['features']);previous_m=len(old['supportOperations']);previous_s=len(old_scenarios['scenarios'])
    assert set(s['pageIndex'] for s in specs)==set(range(len(entries)))
    support_ids=[f'operation:settings-batch-{tag}:SUPPORT-{i+1:03}' for i in range(m)]
    cp=stage/names[0];operations=[]
    for i,s in enumerate(specs):
        assert len(s['acceptance'])==3
        operations.append({'operationId':f'operation:settings-batch-{tag}:OP-{i+1:03}',
            'featureId':f'FSC-{previous_n+i+1:04}',**{k:s[k] for k in ['pageIndex','name','effect','failureAndCancellation']},
            'trigger':'Use the source-defined control under the pinned account/user/host/flag/eligibility conditions.',
            'guard':entries[s['pageIndex']]['conditions'],'sourceRefs':[unit(*u) for u in s['units']],
            'supportOperationIds':[support_ids[j] for j in s['support']],
            'method':'static-source-contract;qualified-isolated-helper-and-callback-replay',
            'verificationStatus':'source-contract;product-scenarios-not-executed','completeChainProven':False})
    mechanisms=[{'operationId':support_ids[i],'name':name,'claim':claim,'sourceRefs':[unit(*u) for u in sources],
        'featureIds':[o['featureId'] for o in operations if support_ids[i] in o['supportOperationIds']],
        'qualification':'Support mechanism; actual injected receiver, authorization, durable effects and full consumer closure remain unproved.'}
        for i,(name,claim,sources) in enumerate(cfg['mechanisms'])]
    known_features={f['featureId'] for f in old['features']}
    shared=[]
    for item in cfg.get('sharedGoalConsumers',[]):
        assert set(item['featureIds'])<=known_features
        assert item['pageIndex'] in range(len(entries))
        shared.append({**{k:v for k,v in item.items() if k!='units'},
            'sourceRefs':[unit(*u) for u in item['units']],
            'completeEntryEquivalenceProven':False,'productAcceptanceExecuted':False})
    counts={'newCatalogPageSurfaces':len(entries),'userGoals':n,'supportOperations':m,
        'newProductScenarioSpecifications':n*3,'newlyPublishedCompleteProgramSelections':len(metadata),
        'newIsolatedSourceCasesPassed':obs['passed'],'productScenariosExecuted':0,'modelSubmissionsAdded':0,
        'originalClientRunsAdded':0,'confirmedChatGptExclusionsAdded':0}
    contract={'schemaVersion':'settings-operation-batch/1','baselineId':BASE,'recordedAtUtc':datetime.now(timezone.utc).isoformat(),
        'scope':cfg['title'],'entries':entries,'operationContracts':operations,'mechanisms':mechanisms,'sharedGoalConsumers':shared,
        'knownGapsByPage':cfg['gaps'],'isolatedObservation':pin(raw/'isolated-observations.json'),
        'selectionQualification':pin(raw/'selection-qualification.json'),
        'modeDecision':{'status':'retain-pending-mode-review','confirmedExclusion':False,'reason':cfg['modeReason']},
        'dependencyBoundary':{'thirdPartyImplementationGenerated':False,'keepFirstParty':cfg['firstParty'],
            'externalize':cfg['externalize'],'versionAuthority':'Existing dependency-import/embedded inventories; no versions inferred from aliases.'},
        'moduleDecisions':[{'taskId':e['taskId'],'page':e['page'],'proposalOnly':True,'decision':cfg['decisions'][i]} for i,e in enumerate(entries)],
        'counts':counts,'fullAnalysisCompleted':False,'clientImplementationStarted':False}
    write(cp,contract)
    scope=copy.deepcopy(old);scenario=copy.deepcopy(old_scenarios);added=[];new_scenarios=[]
    for i,o in enumerate(operations):
        opref=ref(cp,f'/operationContracts/{i}');entryref=ref(cp,f"/entries/{o['pageIndex']}");ids=[]
        for j,expect in enumerate(specs[i]['acceptance']):
            sid=f"{o['featureId']}:SB{tag}-OP-{i+1:03}:{j+1}";ids.append(sid)
            new_scenarios.append({'scenarioId':sid,'featureId':o['featureId'],'operationId':o['operationId'],
                'kind':['behavior-and-guards','failure-and-cancellation','consumer-and-persistence'][j],
                'preconditions':{'pageEntryRef':entryref,'actualValuesObserved':False},'trigger':o['trigger'],
                'expectedEffect':expect,'sourceRef':opref,'executionStatus':'not-executed','runtimeObservationRefs':[],
                'sourceQualification':f'Product specification; {obs["passed"]} synthetic helper/callback cases do not execute this scenario.',
                'authorization':'Specification only; no live account/provider/credential reads or writes, model submissions or original client runs.'})
        added.append({'featureId':o['featureId'],'baselineId':BASE,'name':o['name'],'page':entries[o['pageIndex']]['page'],
            'definitionStatus':'author-reviewed-scoped-user-goal','granularityRationale':'One parameterized user goal; field/retry/cancel variants stay attached and imported implementations remain qualified.',
            'operationMembers':[{'operationId':o['operationId'],'operationType':'settings-control-goal','trigger':o['trigger'],'operationRef':opref}],
            'supportOperationIds':o['supportOperationIds'],'sourceRefs':[opref,entryref],'chain':o['effect'],'conditions':o['guard'],
            'boundaries':[o['failureAndCancellation']],'mode':'unknown','modeEvidence':contract['modeDecision'],
            'retentionStatus':'retain-pending-mode-review','sourceSpecificationStatus':'static-control-and-qualified-service-contract',
            'runtimeStatus':'not-observed-for-this-feature','isolatedObservationRef':contract['isolatedObservation'],
            'completeChainProven':False,'scenarioIds':ids,'knownGaps':cfg['gaps'][o['pageIndex']]+['Actual selected-mode/shared closure and end-to-end acceptance.'],
            'implementationAcceptance':specs[i]['acceptance']})
    scope.update(purpose=cfg['title']+'; complete denominator and live/mode/delegated closure remain open.',
        previousScopeRef=pin(old_path),previousScenarioRef=pin(old_scenario_path),newDefinitionIds=[f['featureId'] for f in added])
    scope['features']+=added
    for i,s in enumerate(mechanisms):
        scope['supportOperations'].append({'operationId':s['operationId'],'operationRef':ref(cp,f'/mechanisms/{i}'),
            'catalogNamespace':f'settings-batch-{tag}','featureIds':s['featureIds'],'classificationConfidence':'confirmed',
            'excludedFromProductScope':False,'operationEquivalenceClaimed':False,'actualUiChainObserved':False,
            'status':'supporting-mechanism','supportKind':s['name'],'reason':s['qualification'],'supportDoesNotExhaustConsumers':True})
    scope['rootCandidateDispositions'] += [{'operationId':o['operationId'],'role':'user','childOperationIds':[]} for o in operations]
    scope['rootCandidateDispositions'] += [{'operationId':s['operationId'],'role':'support','childOperationIds':[]} for s in mechanisms]
    for i,e in enumerate(entries):
        ids=[f['featureId'] for f in added if f['page']==e['page']];index=len(scope['pageContainerRelations'])
        scope['pageContainerRelations'].append({'page':e['page'],'legacyEntryId':'ROUTE-0152',
            'supportInstancePointer':f"/registrations/151/staticMapInstances/{e['staticRouteInstance']}",
            'factoryContractId':e['factoryId'],'featureIds':ids,'relation':'conditional-route-container-to-factory-to-controls',
            'confidence':'confirmed-static-association','sourceRefs':[e['routeInstanceRef'],e['factoryRef'],ref(cp,f'/entries/{i}')],
            'conditions':e['conditions'],'actualMountObserved':False,'sameOperationClaimed':False,'entryCompletelyResolved':False})
        for fid in ids:scope['legacyFeatureRelations'].append({'featureId':fid,'status':'conditional-container-association',
            'entryIds':['ROUTE-0152'],'pageRelationIndices':[index],'completeEntryEquivalenceProven':False,
            'remainingWork':'Actual receiver/host/mode/persistence and cross-entry equivalence remain open.'})
    scope['legacyEntryCoverage']['mappingUpdates'][0]['featureIds']+=scope['newDefinitionIds']
    c=scope['counts']
    for key,delta in {'scopedFeatureDefinitions':n,'assignedUserOperations':n,'supportOperations':m,
        'allKnownOperationCandidatesAccountedFor':n+m,'normalizedBehaviorLeaves':n+m,'unexecutedScenarioSpecifications':n*3,
        'featuresConditionallyAssociatedWithLegacyContainers':n,'additionalDiscoveredRootCandidates':n+m}.items():c[key]+=delta
    c['rootCandidateDispositionCounts']=dict(collections.Counter(r['role'] for r in scope['rootCandidateDispositions']));c['modeCounts']['unknown']+=n
    scope['legacyEntryCoverage']['qualification']=f"{c['featuresConditionallyAssociatedWithLegacyContainers']} conditional definitions; no additional legacy entry fully resolved."
    if 'dispositionRef' in scope['legacyEntryCoverage']:
        scope['legacyEntryCoverage']['qualification'] += (
            ' Source-role dispositions are recorded separately; metadata/resource roles and '
            'registration-callee identity do not close functional mappings.')
    scenario.update(previousSnapshotRef=pin(old_scenario_path),scenarios=old_scenarios['scenarios']+new_scenarios,count=c['unexecutedScenarioSpecifications'])
    sp=stage/names[2];scp=stage/names[4];write(sp,scope);write(scp,scenario)
    with (stage/names[3]).open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['featureId','name','mode','operationCount','runtimeStatus','completeChainProven']);writer.writeheader()
        for item in scope['features']:writer.writerow({k:len(item['operationMembers']) if k=='operationCount' else item[k] for k in writer.fieldnames})
    coverage=copy.deepcopy(old_coverage)
    coverage.update(recordedAtUtc=datetime.now(timezone.utc).isoformat(),previousSnapshot=pin(old_coverage_path),featureLedger=pin(sp),scenarioLedger=pin(scp))
    coverage.setdefault('sharedGoalConsumerRelations',[]).extend(
        {**consumer,'sourceContractRef':ref(cp,f'/sharedGoalConsumers/{i}')}
        for i,consumer in enumerate(shared))
    for i,f in enumerate(coverage['features']):f['featureRef']=ref(sp,f'/features/{i}')
    groups=[]
    for i,e in enumerate(entries):
        g={'taskId':e['taskId'],'name':e['page'],'featureIds':[f['featureId'] for f in added if f['page']==e['page']],
            'primaryModule':'apps/desktop/src/renderer/features/'+cfg['modules'][i],'consumerModules':cfg['consumers'][i],
            'dependsOn':['W03','W05','W07'],'evidence':[pin(cp)],'externalDependencies':cfg['dependencies'][i],
            'sourceDesignCanProceed':True,'implementationStarted':False,
            'productAcceptancePrerequisites':['Actual host/account/user/flag/eligibility conditions','Effective receiver and authorization',
                'Feature-specific failure/cancellation/refresh and durable state','Mode/shared/delegated closure'],
            'userGoalLedgerStatus':'finite-goals-mapped-integration-gaps-retained','sourceReceiverGaps':cfg['gaps'][i],
            'origin':f'Current coverage extension; published plan snapshot {current_plan} retained.'}
        groups.append(g)
        if shared:g['sharedFeatureConsumers']=[fid for consumer in shared if consumer['pageIndex']==i for fid in consumer['featureIds']]
    coverage['taskGroups']+=groups
    for i,f in enumerate(added,previous_n):
        g=groups[operations[i-previous_n]['pageIndex']]
        coverage['features'].append({'featureId':f['featureId'],'name':f['name'],'taskId':g['taskId'],'module':g['primaryModule'],
            'consumerModules':g['consumerModules'],'featureRef':ref(sp,f'/features/{i}'),
            'operationIds':[x['operationId'] for x in f['operationMembers']],'supportOperationIds':f['supportOperationIds'],
            'scenarioIds':f['scenarioIds'],'externalDependencies':g['externalDependencies'],'evidence':[pin(cp)],
            **{k:f[k] for k in ['mode','retentionStatus','completeChainProven','runtimeStatus','knownGaps','implementationAcceptance']},
            'readiness':'bounded-source-design-with-explicit-integration-gaps','implementationStarted':False})
    for i,s in enumerate(coverage['supportOperations']):s['sourceRef']=ref(sp,f'/supportOperations/{i}')
    for i,s in enumerate(mechanisms,previous_m):coverage['supportOperations'].append({'operationId':s['operationId'],
        'sourceRef':ref(sp,f'/supportOperations/{i}'),'consumerFeatureIds':s['featureIds'],
        'taskIds':sorted({f['taskId'] for f in coverage['features'] if f['featureId'] in s['featureIds']}),'disposition':'support-consumer-links-preserved'})
    unresolved=coverage['unresolvedScope'];slugs={e['slug'] for e in entries}
    assert sum(e['slug'] in slugs for e in unresolved['pendingSettingsPages'])==len(entries)
    unresolved['pendingSettingsPages']=[e for e in unresolved['pendingSettingsPages'] if e['slug'] not in slugs]
    unresolved['scopedPagesStillHaveLiveIntegrationGaps'] += [{'slug':e['slug'],'taskId':e['taskId'],'gaps':cfg['gaps'][i]} for i,e in enumerate(entries)]
    unresolved[f'deferredControlFamiliesBatch{tag}']=[{'slug':e['slug'],'families':cfg['gaps'][i][0],'sourceContractRef':ref(cp,f'/entries/{i}')} for i,e in enumerate(entries)]
    for key,pointer in [('associationBacklogRef','/retainedAssociationBacklog'),('pendingOperationQueueRef','/operationReviewQueue'),('crossFeatureOverlapRef','/crossFeatureOverlapReviews')]:unresolved[key]=ref(sp,pointer)
    total=previous_n+n;total_s=previous_s+n*3;pending=len(unresolved['pendingSettingsPages']);tasks=len(coverage['taskGroups'])
    coverage['counts'].update(finiteFeatureDefinitions=total,userOperations=c['assignedUserOperations'],supportOperations=previous_m+m,
        productScenarioSpecifications=total_s,owningTaskGroupsWithFiniteDefinitions=tasks,pendingSettingsPages=pending)
    coverage['counts']['modeCounts']=copy.deepcopy(c['modeCounts'])
    cvp=stage/names[5];write(cvp,coverage)
    pages='、'.join(e['page'] for e in entries);rows='\n'.join(f"| {e['page']} | {sum(o['pageIndex']==i for o in operations)} | {cfg['decisions'][i]} |" for i,e in enumerate(entries))
    points='\n\n'.join(cfg['summaryPoints'])
    summary=f'''# {cfg['title']}

本批交付{n}项有限操作目标、{m}项支撑机制与{n*3}条待执行产品规格，接入[恢复覆盖表v{cv}]({names[5]})的{entries[0]['taskId']}至{entries[-1]['taskId']}。[功能台账v{version}]({names[2]})现有{total}项定义、{c['assignedUserOperations']}项用户操作、{previous_m+m}项支撑及{total_s}条未执行规格。[现有实施计划]({current_plan})保留为排程基线，本批任务由最新覆盖表扩展，没有另写计划版本。

| 页面 | 本批目标 | 模块恢复决定 |
| --- | --- | --- |
{rows}

{points}

{obs['passed']}项精确源码helper/回调隔离用例通过；{cfg['probeDescription']}。{len(verified_units)}个已选择源码单元的冻结文件与字节范围核验通过。

{cfg['modeSummary']} 模块路径是恢复归属提案，客户端源码尚未生成。

45个设置容器中{45-pending}个已有局部合同，{pending}个待展开。{cfg['boundarySummary']} 局部缺口不作为其他静态盘点的全局前置条件，完整分析尚未完成。
'''
    (stage/names[1]).write_text(summary)
    profile={'contracts':pin(cp),'summary':pin(stage/names[1]),'counts':counts,'featureSnapshot':pin(sp),
        'scenarioSnapshot':pin(scp),'restorationCoverage':pin(cvp),'fullAnalysisCompleted':False}
    state=copy.deepcopy(before);state['updatedAtUtc']=datetime.now(timezone.utc).isoformat();state[f'settingsOperationBatch{tag}']=profile
    state['featureScopeCurrentView'].update(snapshotVersion=version,scope=f'Finite{total} definitions; complete denominator unknown.',ledger=pin(sp),csv=pin(stage/names[3]),
        scenarios=pin(scp),counts=c,previousLedger=pin(old_path),reconciliationKind=f'settings-batch-{tag}-bounded-controls',reconciliationArtifact=pin(cp),
        **{f'settingsOperationBatch{tag}Overlay':pin(cp)},settingsSectionDispositionOverlayQualification=f'{45-pending} scoped containers;{pending} pending. Imported/mode/live acceptance retained.')
    state['restorationCoverage']={**pin(cvp),'scope':f'All{total} definitions,{total_s} unexecuted specifications; complete denominator unknown.'}
    pagecov=state['settingsOperationCoverage'];pagecov['pageSurfacesWithScopedControlContracts'] += [e['page'] for e in entries]
    pagecov.update(remainingPageContainers=pending,latestReconciliation=pin(cp))
    state['analysisMilestones']['currentScopeOverlay']={**before['analysisMilestones'].get('currentScopeOverlay',{}),
        'coverage':pin(cvp),'featureLedger':pin(sp),'scenarioLedger':pin(scp),
        'originalTaskIdsPreserved':True,'additionalTaskIds':[g['taskId'] for g in coverage['taskGroups'][16:]],
        'qualification':'Published implementation-plan snapshot retained; latest coverage extends bounded ownership without claiming implementation.'}
    stage_state=state['stageDecisions'];stage_state['latestSubstep']=profile
    stage_state['counts'].update(currentFeatureDefinitions=total,currentRootOperationCandidates=len(scope['rootCandidateDispositions']),currentUnexecutedScenarios=total_s)
    stage_state['counts']['modeCounts']=copy.deepcopy(c['modeCounts'])
    stage_state['currentScopeOverlay']={**before['stageDecisions'].get('currentScopeOverlay',{}),
        'featureLedger':pin(sp),'scenarioLedger':pin(scp),'restorationCoverage':pin(cvp),
        'pendingSettingsOperationContainers':pending,'originalNineCriteriaStatusChanged':False,'priorStageDocumentSnapshot':'analysis-stage-decisions-v2.md'}
    next_pages=[e['slug'] for e in unresolved['pendingSettingsPages'][:3]]
    stage_state['nextAction']={'issueId':'SD-01/SD-06','completedSubstep':f'{pages}:{n} goals,{m} support,{n*3} specifications;{obs["passed"]} isolated cases passed.',
        'fixedInput':f'Saved dispositions and current v{version}/v{cv};next pending containers:'+','.join(next_pages),
        'question':'Which remaining entry families have finite operations, shared consumers or proven mode-only disposition?',
        'closure':'Publish bounded operations/delegated dispositions and ownership; do not repeat settled page selections or source probes.',
        'deferredDedicatedVerification':cfg['nextQualification']}
    if cfg.get('nextAction') is not None:
        stage_state['nextAction']=copy.deepcopy(cfg['nextAction'])
    assert state['latestBehaviorAuthorizationState']==before['latestBehaviorAuthorizationState'] and state['buildInputDispositions']==before['buildInputDispositions']
    for key,value in before['analysisMilestones'].get('currentScopeOverlay',{}).items():
        if key.endswith('Overlay'):
            assert state['analysisMilestones']['currentScopeOverlay'][key]==value
    for key,value in before['stageDecisions'].items():
        if key.endswith('Overlay') and key!='currentScopeOverlay':assert state['stageDecisions'][key]==value
    assert not state['fullAnalysisCompleted'];write(stage/'analysis-state.json',state)
    assert scope['features'][:previous_n]==old['features'] and scope['supportOperations'][:previous_m]==old['supportOperations']
    assert scenario['scenarios'][:previous_s]==old_scenarios['scenarios']
    for key in ['retainedAssociationBacklog','operationReviewQueue','operationContainers','crossFeatureOverlapReviews']:assert scope[key]==old[key]
    assert coverage['taskGroups'][:len(old_coverage['taskGroups'])]==old_coverage['taskGroups']
    prior_shared=old_coverage.get('sharedGoalConsumerRelations',[])
    assert coverage.get('sharedGoalConsumerRelations',[])[:len(prior_shared)]==prior_shared
    assert len(scope['features'])==total and sum(len(f['operationMembers']) for f in scope['features'])==c['assignedUserOperations']
    assert len(scope['supportOperations'])==previous_m+m and len(scenario['scenarios'])==total_s
    assert len({s['scenarioId'] for s in scenario['scenarios']})==total_s
    assert all(s.get('executionStatus',s.get('status'))=='not-executed' for s in scenario['scenarios'])
    assert len({f['featureId'] for f in coverage['features']})==total and sum(len(g['featureIds']) for g in coverage['taskGroups'])==total
    assert {f['featureId'] for f in coverage['features']}=={f['featureId'] for f in scope['features']}
    assert {s for f in coverage['features'] for s in f['scenarioIds']}=={s['scenarioId'] for s in scenario['scenarios']}
    assert all(not f['implementationStarted'] for f in coverage['features'])
    checked=set();parsed={};pointers=0
    def verify(value):
        nonlocal pointers
        if isinstance(value,list):
            for v in value:verify(v)
        elif isinstance(value,dict):
            if {'path','bytes','sha256'}<=value.keys():
                name=value['path'];p=stage/name
                if not p.exists():p=OUT/name
                b=p.read_bytes();assert len(b)==value['bytes'] and sha(b)==value['sha256'],name;checked.add(name)
                if 'jsonPointer' in value:
                    if name not in parsed:parsed[name]=json.loads(b)
                    x=parsed[name]
                    for token in value['jsonPointer'].lstrip('/').split('/') if value['jsonPointer'] else []:
                        token=token.replace('~1','/').replace('~0','~');x=x[int(token)] if isinstance(x,list) else x[token]
                    pointers+=1
            for v in value.values():verify(v)
    for v in [contract,scope,scenario,coverage,profile,state['featureScopeCurrentView'],state['stageDecisions'],state['analysisMilestones']['currentScopeOverlay']]:verify(v)
    validation={'priorFeaturesSupportScenariosAndTaskGroupsPreserved':True,'originalQueuesAndSharedConsumersPreserved':True,
        'finiteFeatures':total,'unexecutedSpecifications':total_s,'owningTaskGroups':tasks,'newFiniteGoals':n,'newSupport':m,
        'newIsolatedCasesPassed':obs['passed'],'sourceUnitsVerified':len(verified_units),'uniquePinnedFilesVerified':len(checked),
        'additionalSharedGoalConsumers':len(shared),
        'jsonPointersVerified':pointers,'pendingSettingsContainers':pending,'delegatedFamiliesRetained':True,
        'modelSubmissionsAdded':0,'originalClientRunsAdded':0,'newProductScenarioPasses':0,'clientImplementationStarted':False,'fullAnalysisCompleted':False}
    write(raw/'validation.json',validation)
    lead=f'''当前以[状态文件](analysis-state.json)和[{cfg['title']}]({names[1]})为准。[台账v{version}]({names[2]})含{total}项有限定义、{c['assignedUserOperations']}项用户操作、{previous_m+m}项支撑与{total_s}条未执行规格，接到[恢复覆盖表v{cv}]({names[5]})的T01至{entries[-1]['taskId']}。45个设置容器中{45-pending}个已有局部合同、{pending}个待展开；完整产品分母仍未知。

本批新增{n}项有限目标、{m}项支撑、{n*3}条规格，{obs['passed']}项精确源码隔离用例通过；{cfg['reportFacts']} 委托服务、模式与持久化缺口保留在对应任务；原九项标准仍为4项资料/范围义务有交付、5项部分完成。客户端实现尚未开始。以下旧数量与下一行动为历史记录。

'''
    docs={}
    for name in ['report.md','gaps.md']:
        text=(OUT/name).read_text();start=text.index('[阶段决定表]');docs[OUT/name]=text.split('\n\n',1)[0]+'\n\n'+lead+retained_boundary_links(state)+text[start:]
    text=(ROOT/'README.md').read_text();start=text.index('以下专项记录保留各自历史范围；')
    docs[ROOT/'README.md']=f'''# ccodex

当前为逆向分析阶段。[{cfg['title']}](analysis/{BASE}/{names[1]})新增{n}项有限目标、{m}项支撑与{n*3}条待执行规格，{obs['passed']}项源码隔离用例通过。

[台账v{version}](analysis/{BASE}/{names[2]})现有{total}项有限定义、{total_s}条未执行规格，接到[恢复覆盖表v{cv}](analysis/{BASE}/{names[5]})的T01至{entries[-1]['taskId']}。45个设置容器中{45-pending}个已有局部合同、{pending}个待展开；委托实现、模式、真实服务、持久化与独立运行时仍待验证，客户端实现尚未开始。

- [当前分析状态与下一行动](analysis/{BASE}/analysis-state.json)
- [实施计划v7（原任务结构与历史数量）](analysis/{BASE}/implementation-plan-v7.md)
- [30条缺失构建输入的处理方案](analysis/{BASE}/build-input-dispositions-v1.json)

'''+retained_boundary_links(state,f'analysis/{BASE}/')+text[start:]
    docs[ROOT/'README.md']=docs[ROOT/'README.md'].replace(f'当前功能台账为v{old_version}',f'当前功能台账为v{version}')
    assert read(OUT/'analysis-state.json')==before
    for p in stage.rglob('*'):
        if p.is_file() and p.name!='analysis-state.json':
            target=OUT/p.relative_to(stage);assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(p,target);assert sha(p.read_bytes())==sha(target.read_bytes());target.chmod(0o444)
    for p,text in docs.items():p.write_text(text)
    temp=OUT/'analysis-state.json.tmp';write(temp,state);os.replace(temp,OUT/'analysis-state.json')
    write(work/'publication.json',{'published':names,'updatedAtUtc':state['updatedAtUtc'],'validation':validation,'goalStillActive':True})
    print(json.dumps({'published':names,'counts':counts,'validation':validation,'nextPages':next_pages},ensure_ascii=False))

if __name__=='__main__':publish(importlib.import_module(sys.argv[1]))
