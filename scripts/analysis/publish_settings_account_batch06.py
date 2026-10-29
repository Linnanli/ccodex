"""Publish bounded account-page operations and preserve every prior scope record."""
import collections
import copy
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
from settings_account_batch06_specs import specifications

ROOT=Path(__file__).resolve().parents[2]
BASE='codex-26.1007.30912-c5b273322a83'
OUT=ROOT/'analysis'/BASE
WORK=ROOT/'.analysis-local/settings-account-batch06-work'
FROZEN=ROOT/'.analysis-local/baselines'/BASE/'extracted'
STAGE=WORK/'deliverables'
RAW=STAGE/'raw/settings-operation-batch-06'
NAMES=['settings-operation-batch-06.json','settings-operation-batch-06.md',
       'feature-scope-v13.json','feature-scope-v13.csv','feature-scope-v13-scenarios.json',
       'restoration-coverage-v4.json']
read=lambda p:json.loads(p.read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def pin(p):
    b=p.read_bytes()
    try:name=str(p.relative_to(STAGE))
    except ValueError:name=str(p.relative_to(OUT))
    return dict(path=name,bytes=len(b),sha256=sha(b))
def ref(p,pointer):return dict(**pin(p),jsonPointer=pointer)

def publish():
    assert not STAGE.exists() and not any((OUT/n).exists() for n in NAMES)
    before=read(OUT/'analysis-state.json')
    assert before['updatedAtUtc']=='2026-10-24T08:49:28.344332+00:00'
    old=read(OUT/'feature-scope-v12.json');old_scenarios=read(OUT/'feature-scope-v12-scenarios.json')
    old_coverage=read(OUT/'restoration-coverage-v3.json')
    assert len(old['features'])==164 and len(old_scenarios['scenarios'])==589
    obs=read(WORK/'isolated-observations.json');assert obs['passed']==22 and obs['failed']==0
    RAW.mkdir(parents=True)
    write(RAW/'analysis-state-before.json',before)
    for folder in ['usage','billing','teams']:shutil.copytree(WORK/folder,RAW/folder)
    shutil.copyfile(WORK/'isolated-observations.json',RAW/'isolated-observations.json')
    for name in ['settings_operations_ast.mjs','settings_account_batch06_specs.py',
                 'probe_settings_account_batch06.cjs','publish_settings_account_batch06.py']:
        shutil.copyfile(ROOT/'scripts/analysis'/name,RAW/name)
    for p in [ROOT/'README.md',OUT/'report.md',OUT/'gaps.md']:shutil.copyfile(p,RAW/(p.name+'.before'))
    write(RAW/'selection-qualification.json',{
        'newlyPublishedCompleteProgramSelections':3,'selectionFolders':['usage','billing','teams'],
        'selectionMethod':'Existing unpublished exact-Program selections prepared before the status-explanation turn; reused without reparsing.',
        'newFullProgramParsesThisPublicationTurn':0,'failedSelectionAttemptsInThisBatch':0,
        'explicitSelectionUnitCap':500,'previousGoalTurnClassification':'no-progress: status explanation only',
        'targetApplicationModulesExecuted':False,'thirdPartyBodiesExecuted':False,'modelSubmissionsAdded':0})
    folders={name:RAW/name for name in ['usage','billing','teams']}
    metadata={name:read(p/'source-contracts.json') for name,p in folders.items()}
    source_cache={};verified_units=set()
    def span(record):
        name=record['sourcePath']
        if name not in source_cache:source_cache[name]=(FROZEN/name.removeprefix('app.asar/')).read_bytes()
        b=source_cache[name];r=record['byteRange']
        assert sha(b)==record['sourceHash'] and sha(b[r['start']:r['endExclusive']])==record['spanHash']
    def unit(folder,name):
        d=metadata[folder];p=folders[folder]/'source-contracts.json'
        matches=[(i,u) for i,u in enumerate(d['units']) if u['name']==name];assert len(matches)==1
        i,u=matches[0];span(u)
        assert sha((p.parent/u['sourceFilename']).read_bytes())==u['spanHash']
        verified_units.add((folder,name));return ref(p,f'/units/{i}')
    for folder,d in metadata.items():
        assert d['fullProgramParsed'] and not d['targetCodeExecuted']
        for u in d['units']:unit(folder,u['name'])
    for selected in obs['sourceSelections']:span(selected)
    dispositions=read(OUT/'settings-section-dispositions.json')
    visibility=read(OUT/'settings-mode-boundary-contracts.json')
    entries=[]
    for slug,page,task in [('usage','Usage','T20'),('billing','Billing','T21'),('teams','Teams','T22')]:
        i,row=next((i,r) for i,r in enumerate(dispositions['entries']) if r['slug']==slug)
        review=next(r for r in visibility['settingsSectionReviews'] if r['slug']==slug)
        entries.append({'slug':slug,'page':page,'taskId':task,'surfaceId':row['entryId'],'factoryId':row['factoryId'],
            'factoryRef':row['factoryRef'],'routeInstanceRef':ref(OUT/'settings-registry-contracts.json',f"/routeInstances/{row['savedSettingsRouteInstance']}"),
            'staticRouteInstance':row['savedSettingsRouteInstance'],'accessFamily':row['accessFamily'],
            'availableInReducedHostList':review['availableInReducedList'],
            'priorDispositionRef':ref(OUT/'settings-section-dispositions.json',f'/entries/{i}'),
            'outerConditionRef':row['outerEntryConditionRef'],'visibilityRef':row['visibilityRef'],'sectionRef':row['sectionRef'],
            'conditions':['Preserve outer host/access/loading/error/redirect precedence and all operation-specific account/plan/role/flag guards.',
                'Actual host/account/plan/role/feature-flag values and selected product mode remain unobserved.'],
            'mode':'unknown','actualMountObserved':False,'confirmedExclusion':False,
            'scopeQualification':'Finite local controls and explicit delegated families; not whole-page/service/mode closure.'})
    specs=specifications();assert collections.Counter(s['pageIndex'] for s in specs)=={0:10,1:11,2:13}
    cp=STAGE/NAMES[0]
    support_ids=[f'operation:settings-batch-06:SUPPORT-{i+1:03}' for i in range(5)]
    operations=[]
    for i,s in enumerate(specs):
        operations.append({'operationId':f'operation:settings-batch-06:OP-{i+1:03}','featureId':f'FSC-{165+i:04}',
            **{k:s[k] for k in ['pageIndex','name','effect','failureAndCancellation']},
            'trigger':'Use the source-defined control under the pinned host/account/plan/role/flag/eligibility conditions.',
            'guard':entries[s['pageIndex']]['conditions'],'sourceRefs':[unit(*u) for u in s['units']],
            'supportOperationIds':[support_ids[n] for n in s['support']],
            'method':'static-source-contract;qualified-isolated-helper-and-callback-replay',
            'verificationStatus':'source-contract;product-scenarios-not-executed','completeChainProven':False})
    mechanisms=[]
    for i,(name,claim,sources) in enumerate([
        ('Usage eligibility, polling and query identity','Preserve mounted/hidden selection, plan branches, account-scoped pagination and reset history; availability errors are not zero balances.', [('usage','id'),('usage','Nu'),('usage','$l'),('usage','hc'),('usage','kc')]),
        ('Credits, auto reload and reset coordination','Separate local policy/drafts, checkout handoff, subscription APIs, payment eligibility, reset controller and preference enforcement.', [('usage','mu'),('usage','gs'),('usage','qc'),('usage','tl')]),
        ('Personal billing and financial service adapters','Preserve account/session/trial conditions, fresh mandate consent, secure/payment forms, deletion dependency rechecks and account-scoped cache refresh.', [('billing','Xr'),('billing','Zr'),('billing','kr'),('billing','cr'),('billing','lr'),('billing','mr'),('billing','Vr')]),
        ('Team routes, membership and mutation dispatch','Preserve account/team identity, source UI permissions, creation recheck, inline save, owner transfer, last-member delete and imported lifecycle dialogs.', [('teams','Br'),('teams','Vr'),('teams','Hr'),('teams','jr'),('teams','_r'),('teams','Fr'),('teams','Tr')]),
        ('Team activity search and bounded pagination','Keep loaded-history search distinct from complete-history search and bound each older-page search batch to five.', [('teams','An'),('teams','gn'),('teams','assignment-xn')])]):
        mechanisms.append({'operationId':support_ids[i],'name':name,'claim':claim,'sourceRefs':[unit(*u) for u in sources],
            'featureIds':[o['featureId'] for o in operations if support_ids[i] in o['supportOperationIds']],
            'qualification':'Support mechanism; injected receiver identity, backend authorization, durable effects and complete consumer closure remain unproved.'})
    gaps=[
        ['Lazy analytics/consumer-view/usage-code-review subpages, enterprise request-policy editor, auto-reload validators/payment forms and app credit-preference control remain retained delegated families.',
         'Actual account/plan/usage/checkout/subscription/payment/reset/preference receivers, mode visibility, live rendering and durable effects.'],
        ['Plan/cadence/store/retention/cancellation workflows, secure billing/tax forms, shared payment add/edit and bank/Stripe provider remain retained delegated families.',
         'Actual financial/account services, current mode visibility, authorization, payment/cache refresh, redirect handling and persistent subscription/profile/payment state.'],
        ['Team setup/create, avatar, invite/join/delete dialogs and shared resource/task/space implementations remain retained delegated families; compiled service-account tab body is null.',
         'Actual team/member/activity providers, account/role/flag values, backend authorization, shared-connection effects, mode closure and durable membership/identity state.']]
    shared=[{'pageIndex':0,'featureIds':[o['featureId'] for o in operations if o['pageIndex']==1 and o['name'] in ['添加或编辑已保存的付款方式','打开订阅管理或续费方案流程']],
        'relation':'Usage delegates to shared pricing/payment workflows also consumed by Billing. Preserve common adapters; exact entry equivalence and full implementation remain unproved.',
        'sourceRefs':[unit('usage','gs'),unit('usage','Qs'),unit('billing','mr'),unit('billing','br')],
        'completeEntryEquivalenceProven':False}]
    counts={'newCatalogPageSurfaces':3,'userGoals':34,'supportOperations':5,'newProductScenarioSpecifications':102,
        'newlyPublishedCompleteProgramSelections':3,'newFullProgramParsesThisPublicationTurn':0,
        'newIsolatedSourceCasesPassed':22,'productScenariosExecuted':0,'modelSubmissionsAdded':0,
        'originalClientRunsAdded':0,'confirmedChatGptExclusionsAdded':0}
    contract={'schemaVersion':'settings-operation-batch/1','baselineId':BASE,'recordedAtUtc':datetime.now(timezone.utc).isoformat(),
        'scope':'Usage, Billing and Teams finite controls, explicit lifecycle handoffs and retained delegated families.',
        'entries':entries,'operationContracts':operations,'mechanisms':mechanisms,'sharedGoalConsumers':shared,'knownGapsByPage':gaps,
        'isolatedObservation':pin(RAW/'isolated-observations.json'),'selectionQualification':pin(RAW/'selection-qualification.json'),
        'modeDecision':{'status':'retain-pending-mode-review','confirmedExclusion':False,
            'reason':'Usage explicitly contains Work/Codex shared credits and Codex resets. Personal billing uses account/session guards and a chatGpt access family, while payments/pricing have shared consumers. Teams role/route predicates do not establish product mode. No full-family exclusion is justified.'},
        'dependencyBoundary':{'thirdPartyImplementationGenerated':False,
            'keepFirstParty':['route/account/plan/role/flag policy','usage polling and history aggregation','auto-reload/discount/reset coordination',
                'mandate fresh-consent comparison and redirect cleanup','payment deletion dependency rechecks','team role/last-member/update/search policy'],
            'externalize':['React/compiler/query/UI/DI/chart packages','secure-form/tax/Stripe/payment provider libraries',
                'account/subscription/usage/payment APIs','browser/clipboard/preference adapters','team/member/activity/resource APIs'],
            'versionAuthority':'Existing dependency-import and embedded-dependency inventories; no new version inferred from aliases.'},
        'moduleDecisions':[{'taskId':e['taskId'],'page':e['page'],'proposalOnly':True,'decision':d} for e,d in zip(entries,[
            'Separate usage overview/history, shared credits/auto-reload orchestration and Codex reset preference/redemption. Keep delegated panels explicit; use external chart/query packages and shared financial adapters.',
            'Separate personal account entitlement/session presentation from shared billing/payment/mandate adapters and provider forms. Keep fresh-consent and deletion safety policy in first-party source; defer live financial verification locally.',
            'Separate team navigation/presentation, membership/update/ownership policy and activity search from account-scoped service adapters and shared lifecycle/resource dialogs. Preserve last-member deletion as a distinct confirmed consequence.'])],
        'notSeparateFeatures':['labels/analytics/field edits/retry within a goal','each pagination cursor or historical row',
            'lazy dialog internals beyond their reviewed handoff','service-account tab editor absent in the compiled body'],
        'counts':counts,'fullAnalysisCompleted':False,'clientImplementationStarted':False}
    write(cp,contract)
    scope=copy.deepcopy(old);scenario=copy.deepcopy(old_scenarios);added=[];new_scenarios=[]
    for i,o in enumerate(operations):
        opref=ref(cp,f'/operationContracts/{i}');entryref=ref(cp,f"/entries/{o['pageIndex']}");ids=[]
        for j,expect in enumerate(specs[i]['acceptance']):
            sid=f"{o['featureId']}:SB06-OP-{i+1:03}:{j+1}";ids.append(sid)
            new_scenarios.append({'scenarioId':sid,'featureId':o['featureId'],'operationId':o['operationId'],
                'kind':['behavior-and-guards','failure-and-cancellation','consumer-and-persistence'][j],
                'preconditions':{'pageEntryRef':entryref,'actualValuesObserved':False},'trigger':o['trigger'],
                'expectedEffect':expect,'sourceRef':opref,'executionStatus':'not-executed','runtimeObservationRefs':[],
                'sourceQualification':'Product specification. Twenty-two isolated helper/callback cases do not execute this scenario.',
                'authorization':'Specification only; no live account/team/financial writes, model requests or original client runs performed.'})
        added.append({'featureId':o['featureId'],'baselineId':BASE,'name':o['name'],'page':entries[o['pageIndex']]['page'],
            'definitionStatus':'author-reviewed-scoped-user-goal',
            'granularityRationale':'One bounded user goal or explicitly named workflow handoff; field variants/retry stay attached, delegated internals are not claimed completed.',
            'operationMembers':[{'operationId':o['operationId'],'operationType':'settings-control-goal','trigger':o['trigger'],'operationRef':opref}],
            'supportOperationIds':o['supportOperationIds'],'sourceRefs':[opref,entryref],'chain':o['effect'],'conditions':o['guard'],
            'boundaries':[o['failureAndCancellation']],'mode':'unknown','modeEvidence':contract['modeDecision'],
            'retentionStatus':'retain-pending-mode-review','sourceSpecificationStatus':'static-control-and-qualified-service-contract',
            'runtimeStatus':'not-observed-for-this-feature','isolatedObservationRef':contract['isolatedObservation'],
            'completeChainProven':False,'scenarioIds':ids,'knownGaps':gaps[o['pageIndex']]+['Actual selected-mode/shared closure and end-to-end acceptance.'],
            'implementationAcceptance':specs[i]['acceptance']})
    scope['features']+=added;scope['newDefinitionIds']=[f['featureId'] for f in added]
    scope['purpose']='Finite user goals including Usage/Billing/Teams; full denominator, delegated implementations and mode closure remain open.'
    scope['previousScopeRef']=pin(OUT/'feature-scope-v12.json');scope['previousScenarioRef']=pin(OUT/'feature-scope-v12-scenarios.json')
    for i,m in enumerate(mechanisms):
        scope['supportOperations'].append({'operationId':m['operationId'],'operationRef':ref(cp,f'/mechanisms/{i}'),
            'catalogNamespace':'settings-batch-06','featureIds':m['featureIds'],'classificationConfidence':'confirmed',
            'excludedFromProductScope':False,'operationEquivalenceClaimed':False,'actualUiChainObserved':False,
            'status':'supporting-mechanism','supportKind':m['name'],'reason':m['qualification'],'supportDoesNotExhaustConsumers':True})
    scope['rootCandidateDispositions'] += [{'operationId':o['operationId'],'role':'user','childOperationIds':[]} for o in operations]
    scope['rootCandidateDispositions'] += [{'operationId':m['operationId'],'role':'support','childOperationIds':[]} for m in mechanisms]
    for i,e in enumerate(entries):
        ids=[f['featureId'] for f in added if f['page']==e['page']]
        ids+=list(dict.fromkeys(fid for s in shared if s['pageIndex']==i for fid in s['featureIds']))
        index=len(scope['pageContainerRelations'])
        scope['pageContainerRelations'].append({'page':e['page'],'legacyEntryId':'ROUTE-0152',
            'supportInstancePointer':f"/registrations/151/staticMapInstances/{e['staticRouteInstance']}",
            'factoryContractId':e['factoryId'],'featureIds':ids,'relation':'conditional-route-container-to-factory-to-controls',
            'confidence':'confirmed-static-association','sourceRefs':[e['routeInstanceRef'],e['factoryRef'],ref(cp,f'/entries/{i}')],
            'conditions':e['conditions'],'actualMountObserved':False,'sameOperationClaimed':False,'entryCompletelyResolved':False})
        for fid in ids:
            prior=next((x for x in scope['legacyFeatureRelations'] if x['featureId']==fid),None)
            if prior:prior['pageRelationIndices'].append(index)
            else:scope['legacyFeatureRelations'].append({'featureId':fid,'status':'conditional-container-association',
                'entryIds':['ROUTE-0152'],'pageRelationIndices':[index],'completeEntryEquivalenceProven':False,
                'remainingWork':'Actual host, receiver, mode, persistence and cross-entry equivalence remain open.'})
    scope['legacyEntryCoverage']['mappingUpdates'][0]['featureIds']+=scope['newDefinitionIds']
    c=scope['counts']
    for key,delta in {'scopedFeatureDefinitions':34,'assignedUserOperations':34,'supportOperations':5,
        'allKnownOperationCandidatesAccountedFor':39,'normalizedBehaviorLeaves':39,'unexecutedScenarioSpecifications':102,
        'featuresConditionallyAssociatedWithLegacyContainers':34,'additionalDiscoveredRootCandidates':39}.items():c[key]+=delta
    c['rootCandidateDispositionCounts']=dict(collections.Counter(r['role'] for r in scope['rootCandidateDispositions']))
    c['modeCounts']['unknown']+=34
    scope['legacyEntryCoverage']['qualification']=f"{c['featuresConditionallyAssociatedWithLegacyContainers']} definitions conditionally associated with a route template; no additional legacy entry fully resolved."
    scenario.update(previousSnapshotRef=pin(OUT/'feature-scope-v12-scenarios.json'),scenarios=old_scenarios['scenarios']+new_scenarios,count=c['unexecutedScenarioSpecifications'])
    sp=STAGE/'feature-scope-v13.json';scp=STAGE/'feature-scope-v13-scenarios.json'
    write(sp,scope);write(scp,scenario)
    with (STAGE/'feature-scope-v13.csv').open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['featureId','name','mode','operationCount','runtimeStatus','completeChainProven']);w.writeheader()
        for item in scope['features']:w.writerow({k:len(item['operationMembers']) if k=='operationCount' else item[k] for k in w.fieldnames})
    coverage=copy.deepcopy(old_coverage)
    coverage.update(recordedAtUtc=datetime.now(timezone.utc).isoformat(),previousSnapshot=pin(OUT/'restoration-coverage-v3.json'),featureLedger=pin(sp),scenarioLedger=pin(scp))
    for i,f in enumerate(coverage['features']):f['featureRef']=ref(sp,f'/features/{i}')
    groups=[]
    for i,(e,module,consumers,deps) in enumerate(zip(entries,['usage','billing','teams'],
        [['billing/shared-financial','backend-adapter/usage','host/preferences','pricing','charts'],
         ['usage/shared-credits','backend-adapter/billing','host/external-browser','secure-forms'],
         ['backend-adapter/teams','shared-resources','team-lifecycle-dialogs','host/clipboard']],
        [['React/query/UI/chart packages','usage/subscription/reset APIs','preference/checkout/browser adapters'],
         ['React/query/UI/secure-form/tax packages','Stripe/provider interfaces','account/payment/subscription APIs'],
         ['React/query/UI packages','team/member/activity APIs','shared-resource/lifecycle/clipboard adapters']])):
        group={'taskId':e['taskId'],'name':e['page'],'featureIds':[f['featureId'] for f in added if f['page']==e['page']],
            'primaryModule':f'apps/desktop/src/renderer/features/{module}','consumerModules':consumers,'dependsOn':['W03','W05','W07'],
            'evidence':[pin(cp)],'externalDependencies':deps,'sourceDesignCanProceed':True,'implementationStarted':False,
            'productAcceptancePrerequisites':['Actual host/account/plan/role/flag conditions','Effective receiver and authorization',
                'Feature-specific failure/cancel/refresh and persistent effects','Mode and shared-dependency closure'],
            'userGoalLedgerStatus':'finite-goals-and-explicit-handoffs-mapped-integration-gaps-retained','sourceReceiverGaps':gaps[i],
            'origin':'Current coverage extension; original implementation-plan-v7 snapshot unchanged.'}
        groups.append(group)
    coverage['taskGroups']+=groups
    for i,f in enumerate(added,164):
        g=groups[operations[i-164]['pageIndex']]
        coverage['features'].append({'featureId':f['featureId'],'name':f['name'],'taskId':g['taskId'],'module':g['primaryModule'],
            'consumerModules':g['consumerModules'],'featureRef':ref(sp,f'/features/{i}'),
            'operationIds':[x['operationId'] for x in f['operationMembers']],'supportOperationIds':f['supportOperationIds'],
            'scenarioIds':f['scenarioIds'],'externalDependencies':g['externalDependencies'],'evidence':[pin(cp)],
            **{k:f[k] for k in ['mode','retentionStatus','completeChainProven','runtimeStatus','knownGaps','implementationAcceptance']},
            'readiness':'bounded-source-design-with-explicit-integration-gaps','implementationStarted':False})
    for i,s in enumerate(coverage['supportOperations']):s['sourceRef']=ref(sp,f'/supportOperations/{i}')
    for i,s in enumerate(mechanisms,36):
        coverage['supportOperations'].append({'operationId':s['operationId'],'sourceRef':ref(sp,f'/supportOperations/{i}'),
            'consumerFeatureIds':s['featureIds'],'taskIds':sorted({f['taskId'] for f in coverage['features'] if f['featureId'] in s['featureIds']}),
            'disposition':'support-consumer-links-preserved'})
    unresolved=coverage['unresolvedScope'];slugs={e['slug'] for e in entries}
    assert sum(e['slug'] in slugs for e in unresolved['pendingSettingsPages'])==3
    unresolved['pendingSettingsPages']=[e for e in unresolved['pendingSettingsPages'] if e['slug'] not in slugs]
    unresolved['scopedPagesStillHaveLiveIntegrationGaps'] += [{'slug':e['slug'],'taskId':e['taskId'],'gaps':gaps[i]} for i,e in enumerate(entries)]
    unresolved['deferredControlFamiliesBatch06']=[{'slug':e['slug'],'families':gaps[i][0],'sourceContractRef':ref(cp,f'/entries/{i}')} for i,e in enumerate(entries)]
    for key,pointer in [('associationBacklogRef','/retainedAssociationBacklog'),('pendingOperationQueueRef','/operationReviewQueue'),('crossFeatureOverlapRef','/crossFeatureOverlapReviews')]:unresolved[key]=ref(sp,pointer)
    coverage.setdefault('sharedGoalConsumerRelations',[]).extend(dict(s,sourceContractRef=pin(cp)) for s in shared)
    coverage['counts'].update(finiteFeatureDefinitions=198,userOperations=202,supportOperations=41,productScenarioSpecifications=691,
        owningTaskGroupsWithFiniteDefinitions=22,pendingSettingsPages=26)
    cvp=STAGE/'restoration-coverage-v4.json';write(cvp,coverage)
    summary='''# Usage、Billing 与 Teams：操作归属和恢复边界

本批收束34项有限操作目标与5项支撑机制，新增102条待执行产品规格，接到[恢复覆盖表v4](restoration-coverage-v4.json)的T20至T22。[功能台账v13](feature-scope-v13.json)共198项定义、202项用户操作、41项支撑和691条未执行规格。原计划v7保留，不再新增实施计划版本。

| 页面 | 已定义目标 | 恢复决定 |
| --- | --- | --- |
| Usage | 10项：面板与概要、额度历史、申请提高额度、购买入口、自动充值、方案入口、应用额度比例、Codex重置偏好、使用重置、重置历史 | 分开用量数据、共享额度/自动充值、Codex重置协调及服务适配。隐藏面板仍挂载，仅选中面板轮询。404历史不可用、409一次重试、分页取消与聚合缺口不能当作零额度。 |
| Billing | 11项：订阅状态、方案管理入口、周期付款授权、余额与兑换入口、交易与发票、账单/税号资料、添加/编辑付款、默认付款、备用开关、移除付款、取消流程入口 | 保留个人账户/会话/试用刷新条件；共享财务适配器独立于展示页面。付款授权前重新比对条款和付款身份；移除付款前重新获取默认及自动充值依赖。 |
| Teams | 13项：列表、创建入口、面板/资源筛选、名称/描述、头像、成员搜索、邀请入口、加入链接、加入确认、退出/移除、所有权转移、删除、活动历史 | 分开页面路由、成员与更新策略、历史搜索和服务/共享对话框。所有者有其他成员时需先转移再退出；最后一名成员的确认会删除团队。活动搜索只覆盖已加载历史，每次向前搜索最多五页。 |

22项精确源码helper/回调隔离用例通过：历史身份/分页/404/409/取消、授权条款变化、试用订阅协调、交易查询参数、服务账户成员过滤、字段保存校验/重复请求/403/409及最后成员删除分发。接收器为合成替身，没有运行原应用模块或真实账户、财务、团队服务，没有新增模型请求。607个已选择源码单元的文件及字节范围均核验；复用三个准备好的完整Program选择，没有再次解析大包。

模式决定仍为保留待核：Usage源码明确包含Work/Codex共享额度和Codex重置；Billing个人账户与chatGpt访问族不能证明支付/方案依赖均为独占；Teams角色及路由条件也不等于产品模式。确认排除数仍为0，不依据名称删除共享功能。

第三方实现不生成。React、query、UI、chart及secure-form/tax/Stripe供应商能力沿现有依赖清单或适配器引入；第一方保留账户/角色条件、轮询、授权条款核对、付款依赖重查、最后成员删除、重置和历史协调策略。上述模块路径都是恢复归属提案，尚未生成客户端源码。

45个设置容器中19个已有局部合同、26个待展开。Usage的三个lazy子页面、企业申请策略编辑、充值校验/付款表单与应用额度偏好；Billing的方案周期/挽留/取消和供应商表单；Teams的创建/头像/邀请/加入/删除及资源实现，均在覆盖表保留为委托边界。进入流程不算完成其内部业务；编译后的service-account面板体为null，不编造编辑器。

本批关闭三个根入口的有限操作定义与模块归属，真实接收、模式、权限、持久化和委托内部实现留在对应任务中，不再作为其他静态盘点的全局前置条件。完整分析与实际客户端验收仍未完成。
'''
    (STAGE/NAMES[1]).write_text(summary)
    profile={'contracts':pin(cp),'summary':pin(STAGE/NAMES[1]),'counts':counts,'featureSnapshot':pin(sp),
        'scenarioSnapshot':pin(scp),'restorationCoverage':pin(cvp),'fullAnalysisCompleted':False}
    state=copy.deepcopy(before);state['updatedAtUtc']=datetime.now(timezone.utc).isoformat();state['settingsOperationBatch06']=profile
    state['featureScopeCurrentView'].update(snapshotVersion=13,scope='Finite198 definitions,202 user operations; complete denominator unknown.',
        ledger=pin(sp),csv=pin(STAGE/'feature-scope-v13.csv'),scenarios=pin(scp),counts=c,previousLedger=pin(OUT/'feature-scope-v12.json'),
        reconciliationKind='usage-billing-teams-bounded-control-goals',reconciliationArtifact=pin(cp),settingsOperationBatch06Overlay=pin(cp),
        settingsSectionDispositionOverlayQualification='Current scoped batches cover19 page containers;26 await definitions. Delegated internals and live/mode acceptance remain explicit.')
    state['restorationCoverage']={**pin(cvp),'scope':'All198 definitions,202 user operations,41 support and691 unexecuted specifications; complete denominator unknown.'}
    pagecov=state['settingsOperationCoverage'];pagecov['pageSurfacesWithScopedControlContracts'] += [e['page'] for e in entries]
    pagecov.update(remainingPageContainers=26,latestReconciliation=pin(cp))
    state['analysisMilestones']['currentScopeOverlay']={'coverage':pin(cvp),'featureLedger':pin(sp),'scenarioLedger':pin(scp),
        'originalTaskIdsPreserved':True,'additionalTaskIds':[f'T{i}' for i in range(17,23)],
        'qualification':'Original v7 task snapshot remains historical; current coverage adds bounded source-design ownership without claiming implementation.'}
    stage=state['stageDecisions'];stage['latestSubstep']=profile
    stage['counts'].update(currentFeatureDefinitions=198,currentRootOperationCandidates=242,currentUnexecutedScenarios=691)
    stage['currentScopeOverlay']={'featureLedger':pin(sp),'scenarioLedger':pin(scp),'restorationCoverage':pin(cvp),
        'pendingSettingsOperationContainers':26,'originalNineCriteriaStatusChanged':False,'priorStageDocumentSnapshot':'analysis-stage-decisions-v2.md'}
    next_pages=[e['slug'] for e in unresolved['pendingSettingsPages'][:3]]
    stage['nextAction']={'issueId':'SD-01/SD-06','completedSubstep':'Usage/Billing/Teams:34 bounded goals,5 support,102 specifications,T20..T22;22 isolated cases passed.',
        'fixedInput':'Saved dispositions and current v13/v4 ledgers;next pending containers:'+','.join(next_pages),
        'question':'Which remaining entry families have finite operations, shared consumers or a proven mode-only disposition?',
        'closure':'Publish bounded operations/delegated dispositions and ownership; do not reselect settled page roots or repeat financial/team source probes.',
        'deferredDedicatedVerification':'Actual account/financial/team services, delegated lifecycle forms, modes and persistence stay local; no additional model authorization remains.'}
    assert state['latestBehaviorAuthorizationState']==before['latestBehaviorAuthorizationState']
    assert state['buildInputDispositions']==before['buildInputDispositions'] and not state['fullAnalysisCompleted']
    write(STAGE/'analysis-state.json',state)
    assert scope['features'][:164]==old['features'] and scope['supportOperations'][:36]==old['supportOperations']
    assert scenario['scenarios'][:589]==old_scenarios['scenarios']
    for key in ['retainedAssociationBacklog','operationReviewQueue','operationContainers','crossFeatureOverlapReviews']:assert scope[key]==old[key]
    assert coverage['taskGroups'][:19]==old_coverage['taskGroups']
    assert coverage['sharedGoalConsumerRelations'][:len(old_coverage['sharedGoalConsumerRelations'])]==old_coverage['sharedGoalConsumerRelations']
    assert len(scope['features'])==198 and sum(len(f['operationMembers']) for f in scope['features'])==202
    assert len(scope['supportOperations'])==41 and len(scope['rootCandidateDispositions'])==242
    assert len(scenario['scenarios'])==691 and len({s['scenarioId'] for s in scenario['scenarios']})==691
    assert all(s.get('executionStatus',s.get('status'))=='not-executed' for s in scenario['scenarios'])
    assert len(coverage['taskGroups'])==22 and sum(len(g['featureIds']) for g in coverage['taskGroups'])==198
    assert len({f['featureId'] for f in coverage['features']})==198
    assert {f['featureId'] for f in coverage['features']}=={f['featureId'] for f in scope['features']}
    assert {s for f in coverage['features'] for s in f['scenarioIds']}=={s['scenarioId'] for s in scenario['scenarios']}
    assert len(unresolved['pendingSettingsPages'])==26 and len(pagecov['pageSurfacesWithScopedControlContracts'])==19
    assert all(not f['implementationStarted'] for f in coverage['features'])
    checked=set();parsed={};pointers=0
    def verify(value):
        nonlocal pointers
        if isinstance(value,list):
            for v in value:verify(v)
        elif isinstance(value,dict):
            if {'path','bytes','sha256'}<=value.keys():
                name=value['path'];p=STAGE/name
                if not p.exists():p=OUT/name
                b=p.read_bytes();assert len(b)==value['bytes'] and sha(b)==value['sha256'],name
                checked.add(name)
                if 'jsonPointer' in value:
                    if name not in parsed:parsed[name]=json.loads(b)
                    x=parsed[name]
                    for token in value['jsonPointer'].lstrip('/').split('/') if value['jsonPointer'] else []:
                        token=token.replace('~1','/').replace('~0','~');x=x[int(token)] if isinstance(x,list) else x[token]
                    pointers+=1
            for v in value.values():verify(v)
    for v in [contract,scope,scenario,coverage,profile,state['featureScopeCurrentView'],state['stageDecisions']]:verify(v)
    validation={'old164Features36Support589ScenariosPreserved':True,'oldT01T19AndSharedConsumersPreserved':True,
        'all198Features691ScenariosMapped':True,'originalQueuesPreserved':True,'newFiniteGoals':34,'newSupport':5,
        'newProductSpecifications':102,'newIsolatedCasesPassed':22,'sourceUnitsVerified':len(verified_units),
        'uniquePinnedFilesVerified':len(checked),'jsonPointersVerified':pointers,'pendingSettingsContainers':26,
        'delegatedFamiliesRetained':True,'modelSubmissionsAdded':0,'originalClientRunsAdded':0,'newProductScenarioPasses':0,
        'clientImplementationStarted':False,'fullAnalysisCompleted':False}
    write(RAW/'validation.json',validation)
    lead='''当前以[状态文件](analysis-state.json)和[Usage、Billing、Teams操作归属](settings-operation-batch-06.md)为准。[台账v13](feature-scope-v13.json)含198项有限定义、202项用户操作、41项支撑与691条未执行规格；全部接到[恢复覆盖表v4](restoration-coverage-v4.json)的T01至T22。45个设置容器中19个已有局部合同、26个待展开；全页覆盖率和完整产品分母仍未知。

本批新增34项有限目标、5项支撑、102条规格，22项精确源码隔离用例通过；真实账户/财务/团队服务、产品验收与模型请求未增加。明确共享财务适配、付款授权条款重查、付款删除依赖重查与最后成员删除分支。lazy页面、生命周期/供应商表单、模式与持久化缺口留在对应任务，不作其他源码盘点的全局前置。原九项标准仍为4项资料/范围义务有交付、5项部分完成，客户端实现尚未开始。以下旧数量与下一行动为历史记录。

'''
    docs={}
    for name in ['report.md','gaps.md']:
        text=(OUT/name).read_text();start=text.index('[阶段决定表]')
        docs[OUT/name]=text.split('\n\n',1)[0]+'\n\n'+lead+text[start:]
    text=(ROOT/'README.md').read_text();start=text.index('以下专项记录保留各自历史范围；')
    docs[ROOT/'README.md']='''# ccodex

当前为逆向分析阶段。[Usage、Billing与Teams操作归属](analysis/'''+BASE+'''/settings-operation-batch-06.md)新增34项有限目标、5项支撑与102条待执行规格，22项源码隔离用例通过。

[台账v13](analysis/'''+BASE+'''/feature-scope-v13.json)现有198项有限定义、691条未执行规格，接到[恢复覆盖表v4](analysis/'''+BASE+'''/restoration-coverage-v4.json)的T01至T22。45个设置容器中19个已有局部合同、26个待展开；委托内部实现、模式、真实服务、持久化与独立运行时仍待验证，客户端实现尚未开始。

- [当前分析状态与下一行动](analysis/'''+BASE+'''/analysis-state.json)
- [实施计划v7（原任务结构与历史数量）](analysis/'''+BASE+'''/implementation-plan-v7.md)
- [30条缺失构建输入的处理方案](analysis/'''+BASE+'''/build-input-dispositions-v1.json)

'''+text[start:]
    docs[ROOT/'README.md']=docs[ROOT/'README.md'].replace('当前功能台账为v12','当前功能台账为v13')
    assert read(OUT/'analysis-state.json')==before
    for p in STAGE.rglob('*'):
        if p.is_file() and p.name!='analysis-state.json':
            target=OUT/p.relative_to(STAGE);assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(p,target);assert sha(p.read_bytes())==sha(target.read_bytes());target.chmod(0o444)
    for p,text in docs.items():p.write_text(text)
    temp=OUT/'analysis-state.json.tmp';write(temp,state);os.replace(temp,OUT/'analysis-state.json')
    write(WORK/'publication.json',{'published':NAMES,'updatedAtUtc':state['updatedAtUtc'],'validation':validation,'goalStillActive':True})
    print(json.dumps({'published':NAMES,'counts':counts,'validation':validation,'nextPages':next_pages},ensure_ascii=False))

if __name__=='__main__':publish()
