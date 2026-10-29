"""Publish settings goals and source decisions without changing old snapshots."""
import collections
import copy
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
from settings_extension_batch05_specs import specifications

ROOT=Path(__file__).resolve().parents[2]
BASE='codex-26.1007.30912-c5b273322a83'
OUT=ROOT/'analysis'/BASE
WORK=ROOT/'.analysis-local/settings-extension-batch05-work'
FROZEN=ROOT/'.analysis-local/baselines'/BASE/'extracted'
STAGE=WORK/'deliverables'
RAW=STAGE/'raw/settings-operation-batch-05'
NAMES=['settings-operation-batch-05.json','settings-operation-batch-05.md',
       'feature-scope-v12.json','feature-scope-v12.csv','feature-scope-v12-scenarios.json',
       'restoration-coverage-v3.json']
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
    assert before['updatedAtUtc']=='2026-10-24T08:26:02.536210+00:00'
    old=read(OUT/'feature-scope-v11.json');old_scenarios=read(OUT/'feature-scope-v11-scenarios.json')
    assert len(old['features'])==120 and len(old_scenarios['scenarios'])==457
    obs=read(WORK/'isolated-observations.json');assert obs['passed']==14 and obs['failed']==0
    RAW.mkdir(parents=True)
    write(RAW/'analysis-state-before.json',before)
    for folder in ['skills','connections','skills-data','skill-card','skills-tab','initial-selected']:
        shutil.copytree(WORK/folder,RAW/folder)
    shutil.copyfile(WORK/'isolated-observations.json',RAW/'isolated-observations.json')
    for filename in ['settings_operations_ast.mjs','probe_settings_extension_batch05.cjs',
                     'settings_extension_batch05_specs.py','publish_settings_extension_batch05.py']:
        shutil.copyfile(ROOT/'scripts/analysis'/filename,RAW/filename)
    for p in [ROOT/'README.md',OUT/'report.md',OUT/'gaps.md']:
        shutil.copyfile(p,RAW/(p.name+'.before'))
    write(RAW/'selection-attempts.json',{
        'successfulNewFullProgramParses':5,'failedFullProgramSelectionAttempts':1,
        'failedAttempt':{'source':'remote-connections-settings-5fcec56d1e17.js',
            'result':'Unexpected local closure expansion at default200 selected units; no output artifact or target execution.',
            'resolution':'Reran with explicit500-unit cap; selected closure and all source ranges are preserved. Failed attempt is not a complete selection.'},
        'reuse':['Previously published plugin manager complete Program selection',
                 'Six initial functions extracted from existing complete Program binding locators; unique frozen export clauses checked'],
        'targetApplicationModulesExecuted':False,'productScenariosExecuted':0,'modelSubmissionsAdded':0})
    folders={name:RAW/name for name in ['skills','connections','skills-data','skill-card','skills-tab','initial-selected']}
    folders['plugins']=OUT/'raw/restoration-plan-v7/mcp-content-01'
    metadata={k:read(p/'source-contracts.json') for k,p in folders.items()}
    source_cache={};verified_units=set()
    def unit(folder,name):
        p=folders[folder]/'source-contracts.json';d=metadata[folder]
        i,u=next((i,u) for i,u in enumerate(d['units']) if u['name']==name)
        if u['sourcePath'] not in source_cache:
            source_cache[u['sourcePath']]=(FROZEN/u['sourcePath'].removeprefix('app.asar/')).read_bytes()
        b=source_cache[u['sourcePath']];r=u['byteRange']
        assert sha(b)==u['sourceHash'] and sha(b[r['start']:r['endExclusive']])==u['spanHash']
        assert sha((p.parent/u['sourceFilename']).read_bytes())==u['spanHash']
        verified_units.add((folder,name))
        return ref(p,f'/units/{i}')
    # Validate every newly selected source unit, including nested local components.
    for folder,d in metadata.items():
        if folder!='plugins':
            for u in d['units']:unit(folder,u['name'])
    dispositions=read(OUT/'settings-section-dispositions.json')
    visibility=read(OUT/'settings-mode-boundary-contracts.json')
    entries=[]
    for slug,page,task in [('plugins-settings','Plugins','T17'),('skills-settings','Skills','T18'),('connections','Connections','T19')]:
        i,row=next((i,r) for i,r in enumerate(dispositions['entries']) if r['slug']==slug)
        review=next(r for r in visibility['settingsSectionReviews'] if r['slug']==slug)
        entries.append({'slug':slug,'page':page,'taskId':task,'surfaceId':row['entryId'],'factoryId':row['factoryId'],
            'factoryRef':row['factoryRef'],'routeInstanceRef':ref(OUT/'settings-registry-contracts.json',f"/routeInstances/{row['savedSettingsRouteInstance']}"),
            'staticRouteInstance':row['savedSettingsRouteInstance'],'accessFamily':row['accessFamily'],
            'availableInReducedHostList':review['availableInReducedList'],
            'priorDispositionRef':ref(OUT/'settings-section-dispositions.json',f'/entries/{i}'),
            'outerConditionRef':row['outerEntryConditionRef'],'visibilityRef':row['visibilityRef'],'sectionRef':row['sectionRef'],
            'conditions':['Preserve outer host/access/loading/error/redirect precedence and all selected source guards.',
                'Actual host/account/platform/feature-flag values and selected product mode remain unobserved.'],
            'mode':'unknown','actualMountObserved':False,'confirmedExclusion':False,
            'scopeQualification':'Finite scoped control goals and explicit delegated families; not exhaustive page, shared-consumer or live-product closure.'})
    specs=specifications();assert collections.Counter(s['pageIndex'] for s in specs)=={0:16,1:9,2:19}
    contract_path=STAGE/NAMES[0]
    support_ids=[f'operation:settings-batch-05:SUPPORT-{i+1:03}' for i in range(5)]
    operations=[]
    for i,s in enumerate(specs):
        operations.append({'operationId':f'operation:settings-batch-05:OP-{i+1:03}',
            'featureId':f'FSC-{121+i:04}',**{k:s[k] for k in ['pageIndex','name','effect','failureAndCancellation']},
            'trigger':'Use the source-defined control under the pinned page/host/flag/account/eligibility conditions.',
            'guard':entries[s['pageIndex']]['conditions'],'sourceRefs':[unit(*u) for u in s['units']],
            'supportOperationIds':[support_ids[n] for n in s['support']],
            'method':'static-source-contract;qualified-helper-replay-only',
            'verificationStatus':'source-contract;product-scenarios-not-executed','completeChainProven':False})
    mechanisms=[]
    for i,(name,claim,sources) in enumerate([
        ('Host, route and extension availability','Resolve source-specific host/tab/account/availability conditions and shared consumers without converting route containers into complete features.',[('plugins','Qa'),('skills','Bt'),('skills','Vt'),('connections','fs')]),
        ('Plugin mutation and share coordination','Keep account-backed HTTP, remote-source HTTP and config writes separate; preserve account guards, cache rollback, partial upgrade errors and resumable marketplace removal.',[('initial-selected','Tkn'),('initial-selected','Okn'),('initial-selected','Mkn'),('plugins','Qa'),('plugins','Ka')]),
        ('Skill loading, generation and refresh','Host/root eligibility, installed matching, stale-install generation guard, raw file read and distinct name/path config addressing.',[('skills-data','q'),('skills-data','G'),('skill-card','Ge'),('skill-card','qe')]),
        ('Connection state and SSH registration','Full-list SSH save, host state watch, stale-response guard, deep-link registration/reuse and abort cleanup; actual native/network receivers retained.',[('connections','fs'),('connections','Ps'),('connections','ls'),('connections','us')]),
        ('Remote-control authorization and pairing','Separate allowed-host preference, runtime enable, claim, MFA, device list, waiting and revocation; preserve partial effects between awaited operations.',[('connections','Hi'),('connections','lo'),('connections','So'),('connections','Ii'),('connections','ki')])]):
        mechanisms.append({'operationId':support_ids[i],'name':name,'claim':claim,'sourceRefs':[unit(*u) for u in sources],
            'featureIds':[o['featureId'] for o in operations if support_ids[i] in o['supportOperationIds']],
            'qualification':'Supporting mechanism; live injected receiver identity, durable effects and full consumer closure remain unproved.'})
    gaps=[['Extension add menu and lazy plugin detail implementation remain explicit imported/deferred control families.',
           'Actual install/share/app OAuth/list/config/marketplace receivers, account transitions and durable effects.'],
          ['Modern creation/menu, suggestion activation and installed/recommended provider internals remain separate retained boundaries.',
           'Actual skills/config/write, install/remove/read/clipboard/composer receivers and refresh subscribers.'],
          ['SSH editor draft validation/normalization, setup/MFA/manual-claim adapters and runtime receiver identity remain retained boundaries.',
           'Actual SSH/WSL/network/pairing/native power effects, credential/session cleanup and durable host/project state.']]
    shared=[{'pageIndex':0,'featureIds':[f'FSC-{i:04}' for i in range(115,121)],
            'relation':'MCP tab in shared manager reuses existing finite goals; no new operation root.',
            'sourceRefs':[unit('plugins','go'),unit('plugins','Qa')], 'completeEntryEquivalenceProven':False},
        {'pageIndex':0,'featureIds':[o['featureId'] for o in operations if o['pageIndex']==1 and o['name'] in ['浏览和搜索所选宿主的技能','启用或停用已安装技能','卸载可移除的技能','打开技能文件或在文件管理器中定位','复制技能的原始 Markdown','用已启用技能预填一个新任务']],
         'relation':'Shared skill cards/list are additional conditional consumers of the same defined skill goals; page presentation/query equivalence remains unproved.',
         'sourceRefs':[unit('plugins','Qa'),unit('skills-tab','Te'),unit('skill-card','Ge')], 'completeEntryEquivalenceProven':False}]
    counts={'newCatalogPageSurfaces':3,'userGoals':len(operations),'supportOperations':len(mechanisms),
        'newProductScenarioSpecifications':len(operations)*3,'successfulNewFullProgramParses':5,
        'failedFullProgramSelectionAttempts':1,'reusedFullProgramSelections':1,'reusedInitialBindingSelections':6,
        'newIsolatedSourceCasesPassed':14,'productScenariosExecuted':0,'modelSubmissionsAdded':0,
        'originalClientRunsAdded':0,'confirmedChatGptExclusionsAdded':0}
    contract={'schemaVersion':'settings-operation-batch/1','baselineId':BASE,'recordedAtUtc':datetime.now(timezone.utc).isoformat(),
        'scope':'Plugins, Skills and Connections finite source goals; shared MCP/card consumers reused and receiver/deferred families preserved.',
        'entries':entries,'operationContracts':operations,'mechanisms':mechanisms,'sharedGoalConsumers':shared,
        'knownGapsByPage':gaps,'isolatedObservation':pin(RAW/'isolated-observations.json'),
        'selectionQualification':pin(RAW/'selection-attempts.json'),
        'modeDecision':{'status':'retain-pending-mode-review','confirmedExclusion':False,
            'reason':'Codex/ChatGPT subtitle and ChatGPT account/auth wording do not establish complete product-mode/shared-consumer closure.'},
        'dependencyBoundary':{'thirdPartyImplementationGenerated':False,
            'keepFirstParty':['host/tab/mode conditions','plugin account/config/share/cache policies','skill install generation/name-path/refresh policy',
                             'SSH list/state/registration/abort policy','remote-control authorization/pairing/MFA and partial-effect policy'],
            'externalize':['React/compiler/query/UI/DI packages','path/utility dependencies','filesystem/clipboard/browser/composer adapters',
                           'app-server config/skill/plugin/marketplace services','SSH/WSL transports and remote-control/native power runtime'],
            'versionAuthority':'Existing dependency-import and embedded-dependency inventories; no version inferred from minified aliases.'},
        'moduleDecisions':[{'taskId':e['taskId'],'page':e['page'],'proposalOnly':True,
            'decision':d} for e,d in zip(entries,[
                'Restore extension manager orchestration plus plugin/app/marketplace adapters; retain shared skills/MCP modules rather than copying their implementations.',
                'Restore both source-defined page branches, shared skill cards and host-scoped data/refresh policy; imported dependencies remain packages/adapters.',
                'Separate connection editor/registration/state orchestration from SSH/WSL/remote-control transport, pairing and native power adapters.'])],
        'notSeparateFeatures':['field editing and dialog expansion within a goal','per-goal retry/cancel gestures','labels/counts/analytics',
            'MCP goals already FSC-0115..0120','shared skill-card consumers already defined in this batch'],
        'counts':counts,'fullAnalysisCompleted':False,'clientImplementationStarted':False}
    write(contract_path,contract)
    scope=copy.deepcopy(old);scenario=copy.deepcopy(old_scenarios)
    added=[];new_scenarios=[]
    for i,o in enumerate(operations):
        opref=ref(contract_path,f'/operationContracts/{i}');entryref=ref(contract_path,f"/entries/{o['pageIndex']}")
        ids=[]
        for j,expect in enumerate(specs[i]['acceptance']):
            sid=f"{o['featureId']}:SB05-OP-{i+1:03}:{j+1}";ids.append(sid)
            new_scenarios.append({'scenarioId':sid,'featureId':o['featureId'],'operationId':o['operationId'],
                'kind':['behavior-and-guards','failure-and-cancellation','consumer-and-persistence'][j],
                'preconditions':{'pageEntryRef':entryref,'actualValuesObserved':False},'trigger':o['trigger'],
                'expectedEffect':expect,'sourceRef':opref,'executionStatus':'not-executed','runtimeObservationRefs':[],
                'sourceQualification':'Product specification. Fourteen isolated helper cases do not execute this scenario.',
                'authorization':'Specification only; no live host/config/files/account/OAuth/pairing/restart/model action performed.'})
        added.append({'featureId':o['featureId'],'baselineId':BASE,'name':o['name'],'page':entries[o['pageIndex']]['page'],
            'definitionStatus':'author-reviewed-scoped-user-goal',
            'granularityRationale':'One parameterized user goal; source branches, field variants, retry and cancel remain attached. Global cross-entry equivalence is not presumed.',
            'operationMembers':[{'operationId':o['operationId'],'operationType':'settings-control-goal','trigger':o['trigger'],'operationRef':opref}],
            'supportOperationIds':o['supportOperationIds'],'sourceRefs':[opref,entryref],'chain':o['effect'],'conditions':o['guard'],
            'boundaries':[o['failureAndCancellation']],'mode':'unknown','modeEvidence':contract['modeDecision'],
            'retentionStatus':'retain-pending-mode-review','sourceSpecificationStatus':'static-control-and-qualified-service-contract',
            'runtimeStatus':'not-observed-for-this-feature','isolatedObservationRef':contract['isolatedObservation'],
            'completeChainProven':False,'scenarioIds':ids,'knownGaps':gaps[o['pageIndex']]+['Actual selected-mode/shared closure and end-to-end acceptance.'],
            'implementationAcceptance':specs[i]['acceptance']})
    scope['features']+=added;scope['newDefinitionIds']=[f['featureId'] for f in added]
    scope['purpose']='Finite user goals including Plugins/Skills/Connections; full client denominator, imported controls and global equivalence remain open.'
    scope['previousScopeRef']=pin(OUT/'feature-scope-v11.json');scope['previousScenarioRef']=pin(OUT/'feature-scope-v11-scenarios.json')
    for i,m in enumerate(mechanisms):
        scope['supportOperations'].append({'operationId':m['operationId'],'operationRef':ref(contract_path,f'/mechanisms/{i}'),
            'catalogNamespace':'settings-batch-05','featureIds':m['featureIds'],'classificationConfidence':'confirmed',
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
            'confidence':'confirmed-static-association','sourceRefs':[e['routeInstanceRef'],e['factoryRef'],ref(contract_path,f'/entries/{i}')],
            'conditions':e['conditions'],'actualMountObserved':False,'sameOperationClaimed':False,'entryCompletelyResolved':False})
        for fid in ids:
            prior=next((x for x in scope['legacyFeatureRelations'] if x['featureId']==fid),None)
            if prior:prior['pageRelationIndices'].append(index)
            else:scope['legacyFeatureRelations'].append({'featureId':fid,'status':'conditional-container-association',
                'entryIds':['ROUTE-0152'],'pageRelationIndices':[index],'completeEntryEquivalenceProven':False,
                'remainingWork':'Actual host, receiver, mode, persistence and cross-entry equivalence remain open.'})
    link=next(o for o in operations if o['name']=='通过 SSH 深链登记连接或远程项目')
    scope['crossFeatureOverlapReviews'].append({'id':'SB05-SSH-PROJECT-ADD-OVERLAP','featureId':link['featureId'],
        'operationId':link['operationId'],'status':'pending','candidateFamily':'SSH/WSL/environment project-add entries',
        'candidateFeatureIds':['FSC-0045','FSC-0105'],'equivalenceClaimed':False,
        'sourceRef':ref(contract_path,f"/operationContracts/{operations.index(link)}"),
        'reason':'Source-specific SSH deep-link behavior is bounded; common project registration/receiver identity has not been proved.'})
    scope['legacyEntryCoverage']['mappingUpdates'][0]['featureIds']+=scope['newDefinitionIds']
    c=scope['counts'];n=len(operations);m=len(mechanisms)
    for key,delta in {'scopedFeatureDefinitions':n,'assignedUserOperations':n,'supportOperations':m,
        'allKnownOperationCandidatesAccountedFor':n+m,'normalizedBehaviorLeaves':n+m,
        'unexecutedScenarioSpecifications':n*3,'featuresConditionallyAssociatedWithLegacyContainers':n,
        'additionalDiscoveredRootCandidates':n+m,'additionalCrossFeatureOverlapReviewsPending':1}.items():c[key]+=delta
    c['rootCandidateDispositionCounts']=dict(collections.Counter(r['role'] for r in scope['rootCandidateDispositions']))
    c['modeCounts']['unknown']+=n
    scope['legacyEntryCoverage']['qualification']=f"{c['featuresConditionallyAssociatedWithLegacyContainers']} definitions conditionally associated with a route template; no additional legacy entry fully resolved."
    scenario.update(previousSnapshotRef=pin(OUT/'feature-scope-v11-scenarios.json'),scenarios=old_scenarios['scenarios']+new_scenarios,count=c['unexecutedScenarioSpecifications'])
    scope_path=STAGE/'feature-scope-v12.json';scenario_path=STAGE/'feature-scope-v12-scenarios.json'
    write(scope_path,scope);write(scenario_path,scenario)
    with (STAGE/'feature-scope-v12.csv').open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['featureId','name','mode','operationCount','runtimeStatus','completeChainProven']);w.writeheader()
        for item in scope['features']:w.writerow({k:len(item['operationMembers']) if k=='operationCount' else item[k] for k in w.fieldnames})
    coverage=copy.deepcopy(read(OUT/'restoration-coverage-v2.json'))
    coverage.update(recordedAtUtc=datetime.now(timezone.utc).isoformat(),previousSnapshot=pin(OUT/'restoration-coverage-v2.json'),
        featureLedger=pin(scope_path),scenarioLedger=pin(scenario_path))
    for i,f in enumerate(coverage['features']):f['featureRef']=ref(scope_path,f'/features/{i}')
    groups=[]
    for i,(e,module,consumers,deps) in enumerate(zip(entries,
        ['extensions','skills','connections'],
        [['skills','mcp','backend-adapter/plugins','host/external-browser','host/clipboard'],
         ['extensions/shared-manager','backend-adapter/skills','host/files','host/clipboard','composer'],
         ['host/remote-connections','backend-adapter/remote-control','projects/registration','host/power']],
        [['query/UI/DI packages','config/plugin/marketplace APIs','app lifecycle and OAuth adapters'],
         ['query/UI packages','skill install/remove/config APIs','file/clipboard/composer adapters'],
         ['query/UI packages','SSH/WSL transports','remote-control/MFA/pairing services','native power runtime']])):
        group={'taskId':e['taskId'],'name':e['page'],'featureIds':[f['featureId'] for f in added if f['page']==e['page']],
            'primaryModule':f'apps/desktop/src/renderer/features/{module}','consumerModules':consumers,
            'dependsOn':['W03','W05','W07'],'evidence':[pin(contract_path)],'externalDependencies':deps,
            'sourceDesignCanProceed':True,'implementationStarted':False,
            'productAcceptancePrerequisites':['Actual host/account/platform/flag conditions','Effective receiver and side effects',
                'Feature-specific failure/cancel/restart','Mode and shared-dependency closure'],
            'userGoalLedgerStatus':'finite-goals-mapped-live-integration-gaps-retained','sourceReceiverGaps':gaps[i],
            'origin':'Current coverage extension; original implementation-plan-v7 task snapshot is unchanged.'}
        groups.append(group)
    coverage['taskGroups']+=groups
    for i,f in enumerate(added,120):
        g=groups[operations[i-120]['pageIndex']]
        coverage['features'].append({'featureId':f['featureId'],'name':f['name'],'taskId':g['taskId'],'module':g['primaryModule'],
            'consumerModules':g['consumerModules'],'featureRef':ref(scope_path,f'/features/{i}'),
            'operationIds':[x['operationId'] for x in f['operationMembers']],'supportOperationIds':f['supportOperationIds'],
            'scenarioIds':f['scenarioIds'],'externalDependencies':g['externalDependencies'],'evidence':[pin(contract_path)],
            **{k:f[k] for k in ['mode','retentionStatus','completeChainProven','runtimeStatus','knownGaps','implementationAcceptance']},
            'readiness':'bounded-source-design-with-explicit-integration-gaps','implementationStarted':False})
    for i,s in enumerate(coverage['supportOperations']):s['sourceRef']=ref(scope_path,f'/supportOperations/{i}')
    for i,s in enumerate(mechanisms,31):
        coverage['supportOperations'].append({'operationId':s['operationId'],'sourceRef':ref(scope_path,f'/supportOperations/{i}'),
            'consumerFeatureIds':s['featureIds'],'taskIds':sorted({f['taskId'] for f in coverage['features'] if f['featureId'] in s['featureIds']}),
            'disposition':'support-consumer-links-preserved'})
    unresolved=coverage['unresolvedScope'];slugs={e['slug'] for e in entries}
    pending=unresolved['pendingSettingsPages'];assert sum(e['slug'] in slugs for e in pending)==3
    unresolved['pendingSettingsPages']=[e for e in pending if e['slug'] not in slugs]
    unresolved['scopedPagesStillHaveLiveIntegrationGaps'] += [{'slug':e['slug'],'taskId':e['taskId'],'gaps':gaps[i]} for i,e in enumerate(entries)]
    unresolved['deferredControlFamiliesBatch05']=[{'slug':e['slug'],'families':gaps[i][0],'sourceContractRef':ref(contract_path,f'/entries/{i}')} for i,e in enumerate(entries)]
    unresolved['associationBacklogRef']=ref(scope_path,'/retainedAssociationBacklog')
    unresolved['pendingOperationQueueRef']=ref(scope_path,'/operationReviewQueue')
    unresolved['crossFeatureOverlapRef']=ref(scope_path,'/crossFeatureOverlapReviews')
    coverage['sharedGoalConsumerRelations']=[dict(s,sourceContractRef=pin(contract_path)) for s in shared]
    coverage['counts'].update(finiteFeatureDefinitions=len(scope['features']),userOperations=c['assignedUserOperations'],
        supportOperations=len(scope['supportOperations']),productScenarioSpecifications=len(scenario['scenarios']),
        owningTaskGroupsWithFiniteDefinitions=len(coverage['taskGroups']),pendingSettingsPages=len(unresolved['pendingSettingsPages']))
    coverage_path=STAGE/'restoration-coverage-v3.json';write(coverage_path,coverage)
    summary='''# 插件、技能与连接设置：功能归属和恢复决定

本批交付44项有限用户目标、5项支撑机制和132条待执行产品规格。[功能台账v12](feature-scope-v12.json)现有164项定义、168项用户操作、36项支撑及589条未执行规格；[恢复覆盖表v3](restoration-coverage-v3.json)新增T17至T19任务组。原实施计划v7及T01至T16保持历史快照，没有另写一版计划。

| 页面 | 本批目标 | 恢复决定 |
| --- | --- | --- |
| Plugins | 16项：浏览、目录跳转、详情、安装、启停、卸载、分享链接/对象/版本、任务预填、应用工具/认证/启停、刷新、市场升级/移除 | 保留共享管理器；MCP复用FSC-0115至0120，技能复用本批技能目标。账号宿主HTTP、远程来源HTTP和本地配置写入保持分支。市场移除保留串行进度与失败续作，不能编造整体回滚。 |
| Skills | 9项：浏览、刷新、推荐安装、启停、卸载、打开文件、复制Markdown、任务预填、创建技能预填 | 保留新旧页面分支、共享卡片与宿主数据层。安装结果受generation约束；技能启停按name/path寻址，原始Markdown来自文件读取。预填不代表模型提交。 |
| Connections | 19项：浏览/刷新、SSH编辑/导入/移除、连接启停、认证/退出、SSH深链项目登记、远程授权/添加/改名/删除、宿主开放/配对、本机设置/开放/撤销与保持唤醒 | 分开列表配置、连接状态、项目登记和远程控制适配。授权列表写入后启用失败、项目登记后取消等可能留下部分效果；取消不等于回滚。 |

14项精确源码helper隔离回放通过，核对路由别名、SSH name/alias边界、在线/lastSeen排序与输入保留、授权显示条件、等待连接时的登录/取消及订阅清理。没有执行原应用模块、真实产品场景、模型请求、个人配置写入、OAuth或设备配对。连接模块首次选择超过默认200-unit上限，调整为显式500后成功；失败尝试单列，未算完整分析。

45个设置容器中16个已有局部操作合同，29个尚待展开。这个数字只表示操作合同覆盖；三个页面的扩展添加菜单、lazy详情、现代技能菜单/建议、SSH草稿校验、设置/MFA/配对适配等委托边界仍在合同及覆盖表中，不构成页面全量完成声明。SSH项目深链与旧WSL/环境添加入口存在关联待比对，未假定全局唯一或等价。

第三方实现不生成；React、query、UI、DI、path和utility沿用依赖清单引入。宿主选择、账号检查、缓存、技能generation、SSH登记/取消、MFA与部分失败策略作为第一方恢复；实际服务、文件/剪贴板/浏览器、SSH/WSL和原生电源能力保留独立适配与验收。出现ChatGPT账户或文案不作为删除共享功能的依据，确认模式排除仍为0。

本批收束这三个入口的有限目标与模块归属，不再追完其所有真实服务作为全局前置条件。下一批按剩余页面的已保存入口继续展开；局部委托控制、模式、真实接收和持久化缺口留在对应覆盖项中。完整分析和客户端实现尚未完成。
'''
    (STAGE/'settings-operation-batch-05.md').write_text(summary)
    profile={'contracts':pin(contract_path),'summary':pin(STAGE/'settings-operation-batch-05.md'),'counts':counts,
        'featureSnapshot':pin(scope_path),'scenarioSnapshot':pin(scenario_path),'restorationCoverage':pin(coverage_path),
        'fullAnalysisCompleted':False}
    state=copy.deepcopy(before);state['updatedAtUtc']=datetime.now(timezone.utc).isoformat();state['settingsOperationBatch05']=profile
    view=state['featureScopeCurrentView'];view.update(snapshotVersion=12,
        scope='Finite164 definitions,168 user operations; complete denominator unknown.',ledger=pin(scope_path),
        csv=pin(STAGE/'feature-scope-v12.csv'),scenarios=pin(scenario_path),counts=c,previousLedger=pin(OUT/'feature-scope-v11.json'),
        reconciliationKind='plugins-skills-connections-control-goals',reconciliationArtifact=pin(contract_path),settingsOperationBatch05Overlay=pin(contract_path),
        settingsSectionDispositionOverlayQualification='Original pending-page snapshot is qualified by scoped batches;29 page containers still await definitions and scoped pages retain delegated families.')
    state['restorationCoverage']={**pin(coverage_path),'scope':'All164 definitions,168 user operations,36 support and589 unexecuted specifications; full denominator unknown.'}
    pagecov=state['settingsOperationCoverage'];pagecov['pageSurfacesWithScopedControlContracts'] += [e['page'] for e in entries]
    pagecov['remainingPageContainers']=29;pagecov['latestReconciliation']=pin(contract_path)
    state['analysisMilestones']['currentScopeOverlay']={'coverage':pin(coverage_path),'featureLedger':pin(scope_path),
        'scenarioLedger':pin(scenario_path),'originalTaskIdsPreserved':True,'additionalTaskIds':['T17','T18','T19'],
        'qualification':'Original v7 plan/milestones remain historical; current coverage adds three bounded source-design task groups.'}
    stage=state['stageDecisions'];stage['latestSubstep']=profile
    stage['counts'].update(currentFeatureDefinitions=164,currentRootOperationCandidates=203,currentUnexecutedScenarios=589)
    stage['currentScopeOverlay']={'featureLedger':pin(scope_path),'scenarioLedger':pin(scenario_path),
        'restorationCoverage':pin(coverage_path),'pendingSettingsOperationContainers':29,
        'originalNineCriteriaStatusChanged':False,'priorStageDocumentSnapshot':'analysis-stage-decisions-v2.md'}
    next_pages=[e['slug'] for e in unresolved['pendingSettingsPages'][:3]]
    stage['nextAction']={'issueId':'SD-01/SD-06','completedSubstep':'Three settings entries reconciled into44 goals,5 support,132 specifications and T17..T19 coverage;14 helper cases passed.',
        'fixedInput':'Saved settings dispositions and current v12/v3 ledgers;next pending containers:'+','.join(next_pages),
        'question':'Which bounded operations and receiver/dependency decisions belong to the next pending page containers?',
        'closure':'Publish finite operations or explicit shared/delegated dispositions and update current coverage; do not repeat settled approval or these three root selections.',
        'deferredDedicatedVerification':'Plugin/skill/connection imported controls, actual account/native/services, mode closure and durable acceptance stay with their owning task; no additional model authorization remains.'}
    assert state['latestBehaviorAuthorizationState']==before['latestBehaviorAuthorizationState']
    assert state['buildInputDispositions']==before['buildInputDispositions'] and not state['fullAnalysisCompleted']
    write(STAGE/'analysis-state.json',state)
    # Preservation, unique ownership and acceptance-accounting checks.
    assert scope['features'][:120]==old['features']
    assert scope['supportOperations'][:31]==old['supportOperations']
    assert scenario['scenarios'][:457]==old_scenarios['scenarios']
    for key in ['retainedAssociationBacklog','operationReviewQueue','operationContainers']:
        assert scope[key]==old[key]
    assert len(scope['features'])==164 and sum(len(f['operationMembers']) for f in scope['features'])==168
    assert len(scope['supportOperations'])==36 and len(scope['rootCandidateDispositions'])==203
    assert len(scenario['scenarios'])==589 and len({s['scenarioId'] for s in scenario['scenarios']})==589
    assert all(s.get('executionStatus',s.get('status'))=='not-executed' for s in scenario['scenarios'])
    assert len(coverage['taskGroups'])==19 and sum(len(g['featureIds']) for g in coverage['taskGroups'])==164
    assert {f['featureId'] for f in coverage['features']}=={f['featureId'] for f in scope['features']}
    assert {s for f in coverage['features'] for s in f['scenarioIds']}=={s['scenarioId'] for s in scenario['scenarios']}
    assert len({f['featureId'] for f in coverage['features']})==164
    assert len(unresolved['pendingSettingsPages'])==29 and len(pagecov['pageSurfacesWithScopedControlContracts'])==16
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
    validation={'old120Features31Support457ScenariosPreserved':True,'originalQueuesPreserved':True,
        'all164Features589ScenariosMapped':True,'oldT01T16PreservedAdditionalT17T19':True,
        'newFiniteGoals':44,'newSupport':5,'newProductSpecifications':132,'newIsolatedCasesPassed':14,
        'sourceUnitsVerified':len(verified_units),'uniquePinnedFilesVerified':len(checked),'jsonPointersVerified':pointers,
        'pendingSettingsContainers':29,'unexpandedImportedControlFamiliesRetained':True,
        'modelSubmissionsAdded':0,'originalClientRunsAdded':0,'newProductScenarioPasses':0,
        'clientImplementationStarted':False,'fullAnalysisCompleted':False}
    write(RAW/'validation.json',validation)
    lead='''当前以[状态文件](analysis-state.json)和[插件、技能、连接归属结果](settings-operation-batch-05.md)为准。[台账v12](feature-scope-v12.json)含164项有限定义、168项用户操作、36项支撑与589条未执行产品规格；全部接到[恢复覆盖表v3](restoration-coverage-v3.json)的T01至T19。45个设置容器中16个已有局部操作合同，29个待展开；已覆盖入口的导入控制族、实际接收、模式与持久化缺口仍保留，不代表全页完成率。

本批新增44项目标、5项支撑、132条规格和14项隔离helper通过；真实产品通过数、模型请求和原客户端运行均未增加。MCP/共享技能目标复用，第三方实现不生成。九项原标准仍为4项资料/范围义务有交付、5项部分完成；完整功能分母、模式剥离、独立运行时和完整行为验收尚未完成。下一批继续剩余设置入口，已收束审批及本批根选择不重复调查。以下旧批次数量及“下一项”均为历史记录。

'''
    docs={}
    for name in ['report.md','gaps.md']:
        text=(OUT/name).read_text();start=text.index('[阶段决定表]')
        docs[OUT/name]=text.split('\n\n',1)[0]+'\n\n'+lead+text[start:]
    text=(ROOT/'README.md').read_text();start=text.index('以下专项记录保留各自历史范围；')
    docs[ROOT/'README.md']='''# ccodex

当前为逆向分析阶段。[插件、技能与连接设置](analysis/'''+BASE+'''/settings-operation-batch-05.md)已落实44项目标、5项支撑与132条待执行规格，14项隔离helper通过。

[台账v12](analysis/'''+BASE+'''/feature-scope-v12.json)现有164项有限定义、589条未执行规格，已接到[恢复覆盖表v3](analysis/'''+BASE+'''/restoration-coverage-v3.json)的T01至T19。45个设置容器中16个已有局部合同、29个待展开；委托控制、模式、真实服务和独立运行时仍待完成，客户端实现尚未开始。

- [当前分析状态与下一行动](analysis/'''+BASE+'''/analysis-state.json)
- [实施计划v7（原任务结构与历史数量）](analysis/'''+BASE+'''/implementation-plan-v7.md)
- [30条缺失构建输入的处理方案](analysis/'''+BASE+'''/build-input-dispositions-v1.json)

'''+text[start:]
    docs[ROOT/'README.md']=docs[ROOT/'README.md'].replace('当前功能台账为v11','当前功能台账为v12')
    assert read(OUT/'analysis-state.json')==before
    for p in STAGE.rglob('*'):
        if p.is_file() and p.name!='analysis-state.json':
            target=OUT/p.relative_to(STAGE);assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(p,target);assert sha(p.read_bytes())==sha(target.read_bytes());target.chmod(0o444)
    for p,text in docs.items():p.write_text(text)
    temp=OUT/'analysis-state.json.tmp';write(temp,state);os.replace(temp,OUT/'analysis-state.json')
    write(WORK/'publication.json',{'published':NAMES,'updatedAtUtc':state['updatedAtUtc'],'validation':validation,
        'goalStillActive':True,'rawArtifactsImmutable':True})
    print(json.dumps({'published':NAMES,'counts':counts,'validation':validation,'nextPages':next_pages},ensure_ascii=False))

if __name__=='__main__':publish()
