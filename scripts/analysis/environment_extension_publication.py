"""Publish the finite environment/hooks/MCP reconciliation and current coverage."""
from reconcile_environment_extensions import ROOT, BASE, OUT, WORK, FROZEN, read, sha, write
import collections
import copy
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil

STAGE = WORK / 'deliverables'
RAW = STAGE / 'raw/settings-operation-batch-04'
NAMES = ['settings-operation-batch-04.json', 'settings-operation-batch-04.md',
         'feature-scope-v11.json', 'feature-scope-v11.csv', 'feature-scope-v11-scenarios.json',
         'restoration-coverage-v2.json']
PRIOR = OUT / 'raw/restoration-plan-v7'


def pin(p):
    b = p.read_bytes()
    try: name = str(p.relative_to(STAGE))
    except ValueError: name = str(p.relative_to(OUT))
    return {'path': name, 'bytes': len(b), 'sha256': sha(b)}


def ref(p, pointer): return {**pin(p), 'jsonPointer': pointer}


def unit(folder, name):
    p = PRIOR / folder / 'source-contracts.json'
    x = read(p)
    i, u = next((i, u) for i, u in enumerate(x['units']) if u['name'] == name)
    b = (FROZEN / u['sourcePath'].removeprefix('app.asar/')).read_bytes()
    r = u['byteRange']
    assert sha(b) == u['sourceHash'] and sha(b[r['start']:r['endExclusive']]) == u['spanHash']
    assert sha((p.parent / u['sourceFilename']).read_bytes()) == u['spanHash']
    return ref(p, f'/units/{i}')


def newunit(name):
    p = RAW / 'source-contracts.json'
    x = read(p)
    return ref(p, f"/units/{next(i for i,u in enumerate(x['units']) if u['name']==name)}")


def specifications():
    s = []
    def add(page, name, units, effect, failure, checks, support=()):
        assert len(checks) == 3
        s.append(dict(pageIndex=page, name=name, units=units, effect=effect,
                      failureAndCancellation=failure, acceptance=checks, support=list(support)))
    env = 'operation:settings-batch-04:SUPPORT-001'
    hooks = 'operation:settings-batch-04:SUPPORT-002'
    mcp = 'operation:settings-batch-04:SUPPORT-003'
    oauth = 'operation:settings-batch-04:SUPPORT-004'
    add(0, '浏览项目及其本地或继承的环境配置', [('local-content-01','Ut'),('local-content-01','Ft'),('local-content-01','Tt')],
        'Choose project/config path and read its summary. Project and inherited configurations remain distinct; opening a row changes page selection, not active-environment storage. Host/project/config loading, read/parse errors and retry are distinct. Workflow and ordinary settings navigation differ.',
        'Unknown project roots are rejected unless workflow/config-path context permits them. Retry refetches sources/config; selection/navigation alone issues no save. Read failure does not prove absence.',
        ['Browse project and inherited configurations with selected host, route/config/workflow context and source-defined loading states.',
         'Fail project/source/config reads and parse separately; verify retry, missing versus invalid config and stale data display.',
         'Verify the actual read receiver and reopening behavior; merely opening a row must not activate or execute its scripts.'])
    add(0, '从环境页面添加项目', [('local-content-01','Ut'),('local-content-01','Nt')],
        'Add project delegates to local Ke(scope) or remote qe({hostId}); this entry does not implement project registration itself.',
        'Dialog cancellation, remote/local registration and persistence remain delegated. Potential overlap with other project-add entries is retained for reconciliation.',
        ['Trigger Add project under local and remote hosts and observe the correct delegated flow.',
         'Cancel or fail the delegated flow; the environment page must not invent a registered project or write a configuration.',
         'Verify registration, root refresh and reopening against the real project subsystem; compare cross-entry equivalence before merging IDs.'])
    add(0, '新建或修改并保存本地环境配置', [('local-content-01','Ut'),('local-content-01','Ft'),('local-editor-01','Ft'),('local-editor-01','Dt'),('local-editor-01','wt'),('local-editor-01','ht'),('local-editor-01','gt'),('local-editor-01','ot')],
        'One draft/save goal includes name, default/per-platform setup and cleanup scripts, and action name/command/icon/platform add/remove fields. Save sends raw TOML plus expectedRevision. Revision-null creation optionally activates after save: workspace callback or worktree scoped config write. Existing revision editing does not automatically reselect. onSaved returns to the calling view/workflow.',
        'Capture initial draft/revision once; guard saving/read/project/dirty/name/incomplete actions. Blank action rows are discarded. Conflict differs from save rejection and saved-but-selection-failed; the latter keeps the saved file. SimpleSetup requires nonblank setup and is a reused editor variant. Back/field edits do not save.',
        ['Create and edit with all script/action fields, guard precedence and simple/full variants; inspect exact raw/version/revision/host/path payload.',
         'Fail save, invalidation and activation separately; distinguish conflict, retryable rejection and selection-failed without undoing a saved file or claiming script execution.',
         'Verify real revision-conflict handling, durable file readback, new workspace/worktree selection and actual setup/action consumers after reopening.'], [env])
    add(0, '发生环境保存冲突后丢弃草稿并重新读取', [('local-content-01','Ut'),('local-editor-01','Ft')],
        'Conflict changes the Save action to Discard edits. Source refetch starts, config refetch is awaited, and a nonerror data result increments the editor key so captured initial draft/revision are rebuilt.',
        'Failed config refetch does not increment the key. This is explicit discard, distinct from ordinary back navigation; source refresh itself is not awaited in the selected callback.',
        ['Produce a revision conflict and invoke Discard edits; inspect warning and the source/config refetch sequence.',
         'Fail or return no config data; verify no successful remount or new save is claimed.',
         'On successful reload, verify editor draft/revision match the actual on-disk configuration and a subsequent save uses the new revision.'], [env])
    add(1, '按来源与项目浏览 Hooks', [('hooks-01','Jt'),('hooks-01','Ot'),('hooks-model-01','o'),('hooks-route-01','i')],
        'Resolve selected host and project roots; query hooks/list only for nonempty roots. Group plugin/user/admin/project/sessionFlags/unknown sources. Source selection is URL state; mismatched host parameter switches host before query invalidation.',
        'Root loading, no roots, query failure, pending and empty results are separate. Selection of an absent project root is rejected. Managed source normalization is not selected-product-mode classification.',
        ['Browse source groups under local/remote roots, host URL changes and valid/invalid source selection.',
         'Test empty roots, loading, load error and duplicate hook/source data without silently enabling a broader query.',
         'Verify actual hooks/list receiver, enabled-plugin inputs and route restoration; listing must not execute a hook.'], [hooks])
    add(1, '重新加载当前项目的 Hooks', [('hooks-01','Jt'),('hooks-01','Ot')],
        'Manual reload refetches hooks, then on isSuccess awaits host invalidation with broadcast:true/refetchType:none and shows success.',
        'Disabled for no roots, initial loading or refreshing. Failed refetch does not show success. Shared broadcast and query error handling remain external.',
        ['Reload with valid roots and verify one refetch followed by host-scoped broadcast invalidation.',
         'Fail refetch and invalidation independently; do not invent a success toast or overwrite a different host.',
         'Change a controlled configuration and verify live reload reflects it without executing hook commands.'], [hooks])
    add(1, '查看 Hook 定义、事件和配置问题', [('hooks-01','gt'),('hooks-01','yt'),('hooks-rows-01','z'),('hooks-rows-01','V')],
        'Open a source detail dialog, group by event, expand a hook and inspect command/prompt/agent/MCP-tool-specific fields plus warnings/errors. Plugin title can delegate to plugin detail.',
        'Dialog and row expansion are local state; closing does not mutate trust or enabled values. Load/empty/error and issues expansion remain visible conditions.',
        ['Inspect each hook type and event-specific details, issues and source/plugin title navigation.',
         'Exercise missing fields, errors, loading and closing; no review or toggle write may occur merely from inspection.',
         'Compare displayed values with real source/list response and confirm plugin navigation preserves the selected host.'])
    add(1, '信任单个新增或已修改的 Hook', [('hooks-01','Jt'),('hooks-rows-01','z')],
        'Trust invokes mutation with key and trustedHash:currentHash. A review-needed row has a disabled unchecked enable switch; trusting is a distinct write.',
        'Managed hooks are always on and are not ordinary trust/toggle targets. Layer override can prevent effective trust despite a write response; provider throws for okOverridden and restores cache.',
        ['Trust untrusted/modified hooks with exact key/currentHash and observe subsequent enabled/trust state.',
         'Return okOverridden or reject write; verify source-defined error boundary and cache rollback without presenting effective approval.',
         'Verify real config reload, unchanged/changed hashes and trust state after reopening; no actual hook execution is authorized by this specification.'], [hooks])
    add(1, '信任当前来源中全部待审核的 Hooks', [('hooks-01','gt'),('hooks-01','vt'),('hooks-01','_t')],
        'Trust all filters unmanaged review-needed hooks in the open source, maps key/currentHash edits and submits one batch. Button requires an open, nonloading, nonerror source and nonempty review set.',
        'Pending disables bulk action. Managed/already trusted hooks are omitted. Override has a dedicated explanation; other errors show generic bulk-trust failure.',
        ['Verify eligible set and one batch request across mixed trust/managed states.',
         'Fail/override batch and verify disabled/pending state, rollback and distinct error text.',
         'Verify real layer precedence and reloaded hashes for each eligible hook; batch submission alone does not prove effective trust.'], [hooks])
    add(1, '启用或停用已信任的 Hook', [('hooks-01','Jt'),('hooks-rows-01','z')],
        'An eligible row writes key/enabled independently from trusted_hash. Managed hooks show always-on disabled controls; review-needed hooks cannot use the enable switch.',
        'Optimistic query responses are host scoped and rolled back on error; settled reload/broadcast follows. Individual row UI does not establish a universal pending/error display.',
        ['Toggle trusted unmanaged hooks and verify exact JSON-quoted state key and boolean.',
         'Reject or override write; verify rollback and both managed/review-needed controls remain disabled.',
         'Verify actual effective enabled state after config reload/reopen and distinguish preference state from hook execution.'], [hooks])
    add(1, '打开本地 Hook 的来源配置文件', [('hooks-rows-01','z')],
        'Local unmanaged rows call the open-file adapter with sourcePath, hostId and project cwd only for project sources. Remote and managed rows omit this action.',
        'File opening is delegated; the selected callback does not establish native editor choice, missing-file feedback or successful opening.',
        ['Open user/project hook source and inspect path/host/cwd adapter arguments.',
         'Verify remote/managed visibility and adapter missing-file/rejection behavior without claiming a successful open.',
         'Use a controlled source file to verify the actual editor integration and correct project context.'])
    add(2, '浏览和搜索已配置或插件提供的 MCP 服务', [('mcp-01','d'),('mcp-content-01','go'),('mcp-content-01','ha'),('mcp-content-01','Ca'),('mcp-provider-01','Ljn')],
        'MCP settings enters shared manager with manageOnly:true and initial MCP tab. Configured and plugin-provided servers/status are separate; hide internal/alias-duplicate and pending-uninstalled entries, search case-insensitively. Layer origins determine project read-only controls. Config read failure may return cached layered response or dMn fallback.',
        'Configured read and auth status loading differ. A stale/default fallback does not prove a successful fresh read. Shared plugin/skill/app/marketplace tabs remain separate scope; the chunk cannot be deleted wholesale.',
        ['Browse/search both server groups, aliases, internal entries, selected host/workspace and origin-based read-only controls.',
         'Fail configuration/status reads with and without cache; verify fallback provenance and avoid treating stale/default data as confirmed absence.',
         'Verify actual layered configuration, write-target/origin helpers, status receiver and reopened list under real host initialization.'], [mcp])
    add(2, '添加或修改自定义 MCP 服务配置', [('mcp-content-01','ha'),('mcp-content-01','na'),('mcp-content-01','aa'),('mcp-content-01','oa'),('mcp-content-01','Sa'),('mcp-provider-01','Jjn')],
        'One create/edit draft supports stdio or streamable_http fields. New keys normalize/deduplicate label; existing edit keeps key. Preserve base timeouts/tool lists and transport-specific auth/oauth/environment/header fields. Save replaces mcp_servers.<key> in chosen writable config, then marks restart pending and closes.',
        'Require nonblank label and command/URL plus dirty UI state; pending/error kept locally. Existing transport cannot switch without uninstall. Missing write target throws. Back discards draft without writing. expectedVersion:null does not provide optimistic concurrency.',
        ['Create and edit both transports, duplicate/non-ASCII keys, env/header rows and preserved base fields; inspect chosen file and replace payload.',
         'Exercise incomplete/unchanged draft, read-only project origin, missing target, save rejection and Back; no failed save may close as successful.',
         'Verify real config readback and app-server reload with command/URL/auth behavior; saved configuration alone is not a running connection.'], [mcp])
    add(2, '移除自定义 MCP 服务', [('mcp-content-01','ha'),('mcp-content-01','na'),('mcp-provider-01','Jjn')],
        'Existing editor Uninstall writes value:null at the same config key/file, hides key/display aliases while restart is pending and closes on success.',
        'Failure remains in editor and clears pending; project-origin edit is disabled before entry. Actual process teardown happens at a separate receiver/restart boundary.',
        ['Uninstall existing service and verify replace-null payload plus alias hiding.',
         'Reject write or remove write target; verify inline error, retained editor and unchanged successful-state claims.',
         'Verify config deletion and post-initialization list/process state; hidden row alone is not proof of process teardown.'], [mcp])
    add(2, '启用或停用 MCP 服务', [('mcp-content-01','ha'),('mcp-content-01','Ca'),('mcp-provider-01','Xjn')],
        'Eligible configured server toggle upserts mcp_servers.<key>.enabled using default config file. Optimistically update host config caches, preserve snapshots and mark restart pending only after mutation success.',
        'Project-origin controls disabled. Provider logs/rolls back on error, then invalidates layered/MCP config; the manager catches toggle rejection. Mutation cache updates are not live server enablement.',
        ['Toggle eligible service and inspect upsert/null-file/null-version payload and both config cache families.',
         'Reject write and verify prior snapshots restored and host-scoped settled invalidation; legacy mcpServers cache key handling retained.',
         'Verify stored value and actual service state after required reload/reopen without conflating optimistic UI with runtime state.'], [mcp])
    add(2, '通过浏览器认证 MCP 服务', [('mcp-content-01','ha'),('mcp-content-01','Ca')],
        'Authenticate notLoggedIn service; registration choice auto/cimd/dcr is local to one login and version gated. Request mcpServer/oauth/login, cache authorizationUrl and open external browser. Matching-host completion clears authentication state; success marks restart pending and invalidates status.',
        'Known non-notLoggedIn status blocks start unless status fetch is active. Empty URL/open false/rejection cleans pending and toasts. Cached URL reopens without a new login request. Initial effect event is ignored; external OAuth/browser/callback not exercised.',
        ['Vary status, backend version and registration choice; inspect omitted/default and explicit strategy payloads plus URL reuse.',
         'Test empty URL, browser rejection, request failure and mismatched/initial completion notifications without false success.',
         'Verify a real controlled OAuth roundtrip, host-matched completion, status refresh and post-restart authenticated state under separate authorization.'], [oauth])
    add(2, '重启所选宿主的 MCP 后台以应用配置', [('mcp-content-01','ha')],
        'Pending configuration/auth changes reveal Restart; dispatch codex-app-server-restart {hostId,intent:restart}. Matching initialization event clears pending/hide lists and invalidates host status.',
        'This is an app-server restart request, not desktop application restart. Selected UI does not await acknowledgement or prove restart success; other-host initialization cannot clear this host state.',
        ['Produce pending changes and inspect exact selected-host restart dispatch.',
         'Delay/fail restart and send another-host initialization; do not invent success or clear this host pending state.',
         'Verify real app-server shutdown/start, initialized event and applied service/auth configuration; retain failure and reconnect behavior.'], [mcp,oauth])
    assert len(s) == 17
    return s


def publish():
    assert not STAGE.exists() and not any((OUT/n).exists() for n in NAMES)
    before = read(OUT/'analysis-state.json')
    assert before == read(WORK/'analysis-state-before.json')
    old = read(OUT/'feature-scope-v10.json'); scenarios_old = read(OUT/'feature-scope-v10-scenarios.json')
    assert len(old['features']) == 103 and len(scenarios_old['scenarios']) == 406
    obs = read(WORK/'isolated-observations.json')
    assert obs['passed'] == 10 and obs['failed'] == 0 and obs['modelSubmissionsAdded'] == 0
    RAW.mkdir(parents=True)
    for p in WORK.iterdir():
        if p.is_file(): shutil.copyfile(p, RAW/p.name)
    for n in ['reconcile_environment_extensions.py','environment_extension_publication.py','probe_mcp_config_fallback.cjs']:
        shutil.copyfile(ROOT/'scripts/analysis'/n, RAW/n)
    for n in ['README.md',str(Path('analysis')/BASE/'report.md'),str(Path('analysis')/BASE/'gaps.md')]:
        shutil.copyfile(ROOT/n, RAW/(Path(n).name+'.before'))
    specs = specifications()
    entries = []
    dispositions = read(OUT/'settings-section-dispositions.json')
    visibility = read(OUT/'settings-mode-boundary-contracts.json')
    for slug,page,task in [('local-environments','Local environments','T14'),('hooks-settings','Hooks','T15'),('mcp-settings','MCP','T16')]:
        i,row = next((i,r) for i,r in enumerate(dispositions['entries']) if r['slug']==slug)
        review = next(r for r in visibility['settingsSectionReviews'] if r['slug']==slug)
        entries.append({'slug':slug,'page':page,'taskId':task,'surfaceId':row['entryId'],'factoryId':row['factoryId'],
            'factoryRef':row['factoryRef'],'routeInstanceRef':ref(OUT/'settings-registry-contracts.json',f"/routeInstances/{row['savedSettingsRouteInstance']}"),
            'staticRouteInstance':row['savedSettingsRouteInstance'],'accessFamily':row['accessFamily'],
            'availableInReducedHostList':review['availableInReducedList'],'priorDispositionRef':ref(OUT/'settings-section-dispositions.json',f'/entries/{i}'),
            'conditions':['Preserve selected-host/access-family, outer loading/error/redirect precedence and source page guards.',
                          'Actual host/account/platform/flag values, selected product mode and mounted UI are not observed.'],
            'outerConditionRef':row['outerEntryConditionRef'],'visibilityRef':row['visibilityRef'],'sectionRef':row['sectionRef'],
            'mode':'unknown','confirmedExclusion':False,'actualMountObserved':False,
            'scopeQualification':'Scoped control contracts, not proof of exhaustive page or shared-manager coverage.'})
    contract_path=STAGE/NAMES[0]
    operations=[]
    for i,s in enumerate(specs):
        operations.append({'operationId':f'operation:settings-batch-04:OP-{i+1:03}', 'featureId':f'FSC-{104+i:04}',
            **{k:s[k] for k in ['pageIndex','name','effect','failureAndCancellation']},
            'trigger':'Use the corresponding source-defined control under its recorded host/route/eligibility conditions.',
            'guard':entries[s['pageIndex']]['conditions'],'sourceRefs':[unit(*u) for u in s['units']],
            'supportOperationIds':s['support'],'method':'static-code-and-qualified-isolated-replay',
            'verificationStatus':'source-contract;product-scenarios-not-executed','completeChainProven':False})
    mechanisms=[]
    for i,(name,claim,sources) in enumerate([
        ('Environment save/selection coordination','TOML serialization, expectedRevision save, started invalidation, optional workspace/worktree activation and distinct conflict/selection-failed results.', [('local-editor-01','ht'),('local-editor-01','gt')]),
        ('Hooks query/write/cache coordination','Nonempty-root query guard, JSON-quoted key paths, reloadUserConfig:true, override error, host-scoped snapshots/rollback and broadcast invalidation.', [('hooks-provider-01','assignment-Eqt'),('hooks-provider-01','assignment-wqt')]),
        ('MCP layered config and optimistic writes','Layered cache/default fallback, origin/write-target helpers, replace versus upsert writes, version:null, rollback and invalidation; real helpers/receiver remain external.', [('mcp-provider-01','Jjn'),('mcp-provider-01','Xjn'),('mcp-provider-01','Ljn')]),
        ('MCP authentication/restart coordination','Per-server pending/cached URL state, registration version gate, host-matched completion and initialization event invalidation.', [('mcp-content-01','ha')])]):
        oid=f'operation:settings-batch-04:SUPPORT-{i+1:03}'
        mechanisms.append({'operationId':oid,'name':name,'claim':claim,'sourceRefs':[unit(*u) for u in sources],
            'featureIds':[o['featureId'] for o in operations if oid in o['supportOperationIds']],
            'qualification':'Actual live host, backend, durable storage and runtime consumer effects remain unproved.'})
    identities=[]
    for folder,local in [('hooks-provider-01','jg'),('mcp-content-01','Gt')]:
        p=PRIOR/folder/'source-contracts.json'; x=read(p)
        j,im=next((j,im) for j,im in enumerate(x['imports']) if any(s['local']==local for s in im['specifiers']))
        assert im['module']=='./app-shared-8bd9d0399038.js'
        assert next(s for s in im['specifiers'] if s['local']==local)['imported']=='y$t'
        export=read(PRIOR/'mcp-provider-01/source-contracts.json')['exports'][4]
        assert export['exported']=='y$t' and export['local']=='KI'
        identities.append({'importLocal':local,'importRef':ref(p,f'/imports/{j}'),
            'exportRef':ref(PRIOR/'mcp-provider-01/source-contracts.json','/exports/4'),
            'selectorRef':unit('mcp-provider-01','KI'),'claim':'Same static host RPC selector identity; actual injected scope/manager instance not proved.'})
    gaps=[['Actual localEnvironments.saveConfig receiver/revision validation and durable write',
           'Workspace/worktree activation receiver and setup/cleanup/action execution consumers', 'Project registration flow and cross-entry equivalence'],
          ['Actual hooks/list/config reload receiver and layer precedence','Real plugin roots and enable/trust persistence; hook execution behavior'],
          ['Actual layered config normalizer/write-target/origin helpers and MCP status receiver',
           'Actual OAuth/browser callback and app-server restart consumers','Shared manager remaining plugin/skill/app/marketplace operations']]
    helper_facts=[{'id':'MCP-READ-FALLBACK','claim':'Hjn catches Wq read failure, logs and returns host/cwd cached layered response or dMn. Rjn delegates server normalization and origin/write-target policy. Fresh read success cannot be inferred from returned data alone.',
                   'sourceRefs':[newunit('Hjn'),newunit('Rjn')],'isolatedCases':['MCP-READ-01','MCP-READ-02','MCP-READ-03','MCP-READ-04']},
                  {'id':'MCP-CACHE-SETTLEMENT','claim':'Qjn awaits layered invalidation before parallel MCP-config/status invalidations; early rejection prevents later calls. Zjn filters only null/undefined snapshots. $jn selects legacy mcpServers only when mcp_servers is nullish, delegates mutation, clones config and retains other response fields.',
                   'sourceRefs':[newunit('Qjn'),newunit('Zjn'),newunit('$jn')],
                   'isolatedCases':['MCP-INVALIDATE-01','MCP-INVALIDATE-02','MCP-SNAPSHOT-01','MCP-OPTIMISTIC-01','MCP-OPTIMISTIC-02','MCP-OPTIMISTIC-03']}]
    counts={'newCatalogPageSurfaces':3,'userGoals':17,'supportOperations':4,'newProductScenarioSpecifications':51,
        'reusedFullProgramSelections':11,'newFullProgramParses':0,'newIsolatedSourceCasesPassed':10,
        'previousIsolatedCasesReused':41,'productScenariosExecuted':0,'modelSubmissionsAdded':0,'originalClientRunsAdded':0,
        'confirmedChatGptExclusionsAdded':0}
    contract={'schemaVersion':'settings-operation-batch/1','baselineId':BASE,'recordedAtUtc':datetime.now(timezone.utc).isoformat(),
        'scope':'Three settings entries, finite goals and qualified receiving boundaries; shared-manager operations retained separately.',
        'entries':entries,'operationContracts':operations,'mechanisms':mechanisms,'receivingHelperFacts':helper_facts,
        'hostSelectorBindings':identities,'previousSourceContracts':pin(OUT/'environment-extension-contracts.json'),
        'isolatedObservation':pin(RAW/'isolated-observations.json'),'previousIsolatedObservation':pin(PRIOR/'isolated-observations.json'),
        'modeDecision':{'status':'retain-pending-mode-review','confirmedExclusion':False,
                        'reason':'Selected settings/access families and source bindings do not establish complete mode/shared-consumer closure.'},
        'dependencyBoundary':{'thirdPartyImplementationGenerated':False,
             'keepFirstParty':['environment draft/encoding/selection policy','hook source/trust/override policy','MCP draft/cache/origin/auth/restart policy'],
             'externalize':['React/compiler helpers','query/mutation/schema/form/UI libraries','TOML parsing dependencies','host save/read/editor/browser adapters','app-server config/hooks/MCP services'],
             'versionAuthority':'dependency-import-decisions and embedded-dependency records; no exact package version inferred from aliases.'},
        'presentationAndDelegationDisposition':{'notSeparateFeatures':['inherited list expansion','script platform tabs/action row edits','Back/cancel draft','hook row/issues expansion','OAuth registration choice for one login'],
            'retainedOutsideTheseGoals':['shared manager plugin/skill/app/marketplace tabs','documentation links/native link handling','project add subsystem','runtime hook/script execution']},
        'knownGapsByPage':gaps,'counts':counts,'fullAnalysisCompleted':False,'clientImplementationStarted':False}
    write(contract_path,contract)
    scope=copy.deepcopy(old); scenarios=copy.deepcopy(scenarios_old)
    added_features=[];added_scenarios=[]
    for i,o in enumerate(operations):
        opref=ref(contract_path,f'/operationContracts/{i}');eref=ref(contract_path,f"/entries/{o['pageIndex']}")
        ids=[]
        for j,check in enumerate(specs[i]['acceptance']):
            sid=f"{o['featureId']}:SB04-OP-{i+1:03}:{j+1}";ids.append(sid)
            added_scenarios.append({'scenarioId':sid,'featureId':o['featureId'],'operationId':o['operationId'],
                'kind':['behavior-and-guards','failure-and-cancellation','consumer-and-persistence'][j],
                'preconditions':{'pageEntryRef':eref,'actualValuesObserved':False},'trigger':o['trigger'],'expectedEffect':check,
                'sourceRef':opref,'executionStatus':'not-executed','runtimeObservationRefs':[],
                'sourceQualification':'Source-derived product specification; isolated replay does not execute this scenario.',
                'authorization':'Specification only. Real preference/project/file/browser/OAuth/restart/model actions were not performed.'})
        added_features.append({'featureId':o['featureId'],'baselineId':BASE,'name':o['name'],'page':entries[o['pageIndex']]['page'],
            'definitionStatus':'author-reviewed-scoped-user-goal',
            'granularityRationale':'One parameterized user goal; draft fields, variants, retry and presentation gestures stay with their goal unless a distinct source-defined recovery action.',
            'operationMembers':[{'operationId':o['operationId'],'operationType':'settings-control-goal','trigger':o['trigger'],'operationRef':opref}],
            'supportOperationIds':o['supportOperationIds'],'sourceRefs':[opref,eref],'chain':o['effect'],'conditions':o['guard'],
            'boundaries':[o['failureAndCancellation']],'mode':'unknown','modeEvidence':contract['modeDecision'],
            'retentionStatus':'retain-pending-mode-review','sourceSpecificationStatus':'static-control-and-qualified-service-contract',
            'runtimeStatus':'not-observed-for-this-feature','isolatedObservationRef':contract['isolatedObservation'],
            'completeChainProven':False,'scenarioIds':ids,'knownGaps':gaps[o['pageIndex']]+['Actual selected-mode/shared closure and durable end-to-end acceptance'],
            'implementationAcceptance':specs[i]['acceptance']})
    scope['features']+=added_features
    scope['newDefinitionIds']=[f['featureId'] for f in added_features]
    scope['purpose']='Finite control-goal view, including environment/Hooks/MCP; complete client denominator and global equivalence remain unproved.'
    scope['previousScopeRef']=pin(OUT/'feature-scope-v10.json');scope['previousScenarioRef']=pin(OUT/'feature-scope-v10-scenarios.json')
    for i,m in enumerate(mechanisms):
        scope['supportOperations'].append({'operationId':m['operationId'],'operationRef':ref(contract_path,f'/mechanisms/{i}'),
            'catalogNamespace':'settings-batch-04','featureIds':m['featureIds'],'classificationConfidence':'confirmed',
            'excludedFromProductScope':False,'operationEquivalenceClaimed':False,'actualUiChainObserved':False,
            'status':'supporting-mechanism','supportKind':m['name'],'reason':m['qualification'],'supportDoesNotExhaustConsumers':True})
    scope['rootCandidateDispositions'] += [{'operationId':o['operationId'],'role':'user','childOperationIds':[]} for o in operations]
    scope['rootCandidateDispositions'] += [{'operationId':m['operationId'],'role':'support','childOperationIds':[]} for m in mechanisms]
    for i,e in enumerate(entries):
        ids=[o['featureId'] for o in operations if o['pageIndex']==i];index=len(scope['pageContainerRelations'])
        scope['pageContainerRelations'].append({'page':e['page'],'legacyEntryId':'ROUTE-0152',
            'supportInstancePointer':f"/registrations/151/staticMapInstances/{e['staticRouteInstance']}",'factoryContractId':e['factoryId'],
            'featureIds':ids,'relation':'conditional-route-container-to-factory-to-controls','confidence':'confirmed-static-association',
            'sourceRefs':[e['routeInstanceRef'],e['factoryRef'],ref(contract_path,f'/entries/{i}')],
            'conditions':e['conditions'],'actualMountObserved':False,'sameOperationClaimed':False,'entryCompletelyResolved':False})
        scope['legacyFeatureRelations'] += [{'featureId':fid,'status':'conditional-container-association','entryIds':['ROUTE-0152'],
            'pageRelationIndices':[index],'completeEntryEquivalenceProven':False,'remainingWork':'实际宿主、消费者、模式、持久化与跨入口等价尚待核对。'} for fid in ids]
    scope['crossFeatureOverlapReviews'].append({'id':'SB04-PROJECT-ADD-OVERLAP','featureId':'FSC-0105',
        'operationId':operations[1]['operationId'],'status':'pending','candidateFamily':'local/remote project add entries',
        'sourceRef':ref(contract_path,'/operationContracts/1'),'equivalenceClaimed':False,
        'reason':'Environment entry delegates to project registration; existing project-add entry/receiver identity needs comparison before merging definitions.'})
    scope['legacyEntryCoverage']['mappingUpdates'][0]['featureIds']+=scope['newDefinitionIds']
    scope['legacyEntryCoverage']['qualification']='114 definitions conditionally associated with one route template; no additional legacy entry fully resolved.'
    c=scope['counts'];c.update({'scopedFeatureDefinitions':120,'assignedUserOperations':124,'supportOperations':31,
        'allKnownOperationCandidatesAccountedFor':154,'normalizedBehaviorLeaves':156,'unexecutedScenarioSpecifications':457,
        'featuresConditionallyAssociatedWithLegacyContainers':114,'additionalDiscoveredRootCandidates':83,
        'rootCandidateDispositionCounts':{'user':123,'support':29,'pending':1,'composite':1},
        'modeCounts':{'unknown':120,'codex':0,'chatgpt':0,'shared':0},'additionalCrossFeatureOverlapReviewsPending':2})
    scenarios.update({'previousSnapshotRef':pin(OUT/'feature-scope-v10-scenarios.json'),
        'scenarios':scenarios_old['scenarios']+added_scenarios,'count':457})
    scope_path=STAGE/'feature-scope-v11.json';scenario_path=STAGE/'feature-scope-v11-scenarios.json'
    write(scope_path,scope);write(scenario_path,scenarios)
    with (STAGE/'feature-scope-v11.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['featureId','name','mode','operationCount','runtimeStatus','completeChainProven']);w.writeheader()
        for x in scope['features']:w.writerow({k:(len(x['operationMembers']) if k=='operationCount' else x[k]) for k in w.fieldnames})
    coverage=copy.deepcopy(read(OUT/'restoration-coverage-v1.json'))
    coverage['recordedAtUtc']=datetime.now(timezone.utc).isoformat();coverage['previousSnapshot']=pin(OUT/'restoration-coverage-v1.json')
    coverage['featureLedger']=pin(scope_path);coverage['scenarioLedger']=pin(scenario_path)
    for i,f in enumerate(coverage['features']):f['featureRef']=ref(scope_path,f'/features/{i}')
    for i,f in enumerate(added_features,103):
        page=operations[i-103]['pageIndex'];task=coverage['taskGroups'][13+page]
        coverage['features'].append({'featureId':f['featureId'],'name':f['name'],'taskId':task['taskId'],'module':task['primaryModule'],
            'consumerModules':task['consumerModules'],'featureRef':ref(scope_path,f'/features/{i}'),
            'operationIds':[m['operationId'] for m in f['operationMembers']],'supportOperationIds':f['supportOperationIds'],
            'scenarioIds':f['scenarioIds'],'externalDependencies':task['externalDependencies'],'evidence':[pin(contract_path)],
            **{k:f[k] for k in ['mode','retentionStatus','completeChainProven','runtimeStatus','knownGaps','implementationAcceptance']},
            'readiness':'bounded-source-design-with-explicit-integration-gaps','implementationStarted':False})
    for i,g in enumerate(coverage['taskGroups'][13:]):
        g['featureIds']=[f['featureId'] for f in added_features if f['page']==entries[i]['page']]
        g['evidence'].append(pin(contract_path));g['userGoalLedgerStatus']='finite-goals-mapped-live-integration-gaps-retained'
        g['sourceReceiverGaps']=gaps[i]
    for i,s in enumerate(coverage['supportOperations']):s['sourceRef']=ref(scope_path,f'/supportOperations/{i}')
    for i,m in enumerate(mechanisms,27):
        tasks=sorted({f['taskId'] for f in coverage['features'] if f['featureId'] in m['featureIds']})
        coverage['supportOperations'].append({'operationId':m['operationId'],'sourceRef':ref(scope_path,f'/supportOperations/{i}'),
            'consumerFeatureIds':m['featureIds'],'taskIds':tasks,'disposition':'support-consumer-links-preserved'})
    pending=coverage['unresolvedScope']['pendingSettingsPages'];removed=[e for e in pending if e['slug'] in {e['slug'] for e in entries}]
    assert len(removed)==3
    coverage['unresolvedScope']['pendingSettingsPages']=[e for e in pending if e not in removed]
    coverage['unresolvedScope']['scopedPagesStillHaveLiveIntegrationGaps']=[{'slug':e['slug'],'taskId':e['taskId'],'gaps':gaps[i]} for i,e in enumerate(entries)]
    coverage['unresolvedScope']['associationBacklogRef']=ref(scope_path,'/retainedAssociationBacklog')
    coverage['unresolvedScope']['pendingOperationQueueRef']=ref(scope_path,'/operationReviewQueue')
    coverage['unresolvedScope']['crossFeatureOverlapRef']=ref(scope_path,'/crossFeatureOverlapReviews')
    coverage['counts'].update({'finiteFeatureDefinitions':120,'userOperations':124,'supportOperations':31,'productScenarioSpecifications':457,
        'owningTaskGroupsWithFiniteDefinitions':16,'additionalSourceContractTaskGroups':0,'pendingSettingsPages':32})
    coverage_path=STAGE/'restoration-coverage-v2.json';write(coverage_path,coverage)
    summary='''# 本地环境、Hooks 与 MCP：功能归属和接收边界

本批将既有源码合同落实为17项有限用户目标、4项支撑机制和51条待执行产品规格。当前[台账v11](feature-scope-v11.json)为120项定义、124项用户操作、31项支撑、457条未执行规格；[恢复覆盖表v2](restoration-coverage-v2.json)将全部定义接到原计划的T01至T16，不新增一版实施计划。45个设置容器中13个已有局部控件合同，32个待展开；这不是全功能完成率。

| 原任务 | 本批用户目标 | 恢复决定 |
| --- | --- | --- |
| T14 本地环境 | 浏览项目/继承配置、添加项目、创建/修改并保存配置、冲突后丢弃重读 | 草稿与TOML编码保留为第一方；保存与激活分开。保存失败、revision冲突、保存成功但激活失败各有结果。已有revision编辑不自动重新选择。宿主revision检查、真实文件耐久性和脚本消费者仍待核对。 |
| T15 Hooks | 来源浏览、刷新、详情、单个信任、批量信任、启停、打开本地配置 | 管理状态与信任/启停分开；状态键按JSON引号编码，reloadUserConfig:true；okOverridden必须当作未生效错误。配置层优先级、真实接收实例与运行行为单列。 |
| T16 MCP | 浏览搜索、创建/修改配置、移除、启停、浏览器认证、重启后台 | 分开配置写入、乐观缓存和实际服务状态。保存/删除用batch replace，启停用value upsert；OAuth按宿主匹配完成事件；Restart请求的是app-server。插件/技能/应用等共享管理器目标继续保留。 |

新增六个辅助函数从已保存Program绑定的唯一声明范围提取，没有重复解析整个bundle。10项新隔离回放通过，核对了读取失败的缓存/默认回退、读取选择器边界、失效顺序、早期失败、快照筛选、legacy缓存键和克隆行为。Wq、配置归一化、来源/写入目标计算和eMn采用合成替身，因此这些helper本身及真实后台仍未验证；旧41项回放直接复用，没有重新计作产品通过数。

Hooks的jg和MCP的Gt均静态导入shared的y$t，出口绑定同一KI宿主RPC选择器。这关闭了两个import身份疑问，尚不证明注入的运行scope/manager或真实服务实例。MCP读取失败可能返回旧缓存或默认空配置，恢复实现必须保留该源行为与错误来源，不能把仍有列表或空列表解释为新鲜读取成功。

环境页面的Add project与其他入口可能重叠，已加入待比较项，未假称新功能全局唯一。原12项关联待办、快捷键重叠、旧入口未决和完整模式共享闭包保留。第三方实现不生成，包身份/版本沿用依赖清单；本批没有真实配置写入、Hook执行、OAuth、后台重启、模型请求或客户端运行。

下一步回到普通任务创建、提交、审批、中断和恢复的已定位接收链。先复用已有provider/transport记录，对尚未连接的实际发送方、接收方、状态与持久化作明确处置；三个设置页面的真实宿主/耐久性/OAuth缺口留在各自验收中，不作为继续分析的全局前置条件。完整分析与客户端实现均未完成。
'''
    (STAGE/'settings-operation-batch-04.md').write_text(summary)
    profile={'contracts':pin(contract_path),'summary':pin(STAGE/'settings-operation-batch-04.md'),'counts':counts,
        'featureSnapshot':pin(scope_path),'scenarioSnapshot':pin(scenario_path),'restorationCoverage':pin(coverage_path),
        'fullAnalysisCompleted':False}
    state=copy.deepcopy(before);state['updatedAtUtc']=datetime.now(timezone.utc).isoformat()
    state['settingsOperationBatch04']=profile
    view=state['featureScopeCurrentView'];view.update({'snapshotVersion':11,
        'scope':'Finite120 definitions,124 user operations; complete denominator unknown.',
        'ledger':pin(scope_path),'csv':pin(STAGE/'feature-scope-v11.csv'),'scenarios':pin(scenario_path),'counts':c,
        'previousLedger':pin(OUT/'feature-scope-v10.json'),'reconciliationKind':'environment-hooks-mcp-control-goals',
        'reconciliationArtifact':pin(contract_path),'settingsOperationBatch04Overlay':pin(contract_path),
        'settingsSectionDispositionOverlayQualification':'Original pending-page snapshot is qualified by subsequent scoped control batches; 32 page containers still await operation definitions.'})
    state['restorationCoverage']={**pin(coverage_path),'scope':'All120 definitions,124 user operations,31 support and457 unexecuted specifications; full denominator unknown.'}
    pagecov=state['settingsOperationCoverage'];pagecov['pageSurfacesWithScopedControlContracts'] += [e['page'] for e in entries]
    pagecov['remainingPageContainers']=32;pagecov['preliminaryAdditionalPageSourceContracts']=[]
    pagecov['preliminaryContractsDoNotChangeRemainingOperationContainerCount']=False
    pagecov['latestReconciliation']=pin(contract_path)
    state['analysisMilestones']['currentScopeOverlay']={'coverage':pin(coverage_path),'featureLedger':pin(scope_path),
        'scenarioLedger':pin(scenario_path),'taskIdsUnchanged':True,'taskT14T15T16NowHaveFiniteDefinitions':True,
        'qualification':'v7 plan/milestones remain historical source snapshot; current feature counts and task bindings use this overlay.'}
    stage=state['stageDecisions'];stage['latestSubstep']=profile
    stage['counts'].update({'currentFeatureDefinitions':120,'currentRootOperationCandidates':154,'currentUnexecutedScenarios':457})
    stage['currentScopeOverlay']={'featureLedger':pin(scope_path),'scenarioLedger':pin(scenario_path),
        'restorationCoverage':pin(coverage_path),'pendingSettingsOperationContainers':32,
        'originalNineCriteriaStatusChanged':False,'priorStageDocumentSnapshot':'analysis-stage-decisions-v2.md'}
    stage['nextAction']={'issueId':'SD-01/SD-03/SD-06',
        'completedSubstep':'Three page families reconciled:17 goals,4 support,51 product specs; current120/457 coverage mapped to originalT01..T16. Six saved-binding helpers and10 isolated cases close bounded MCP fallback/cache questions.',
        'fixedInput':'Existing ordinary task creation/submission/approval/interrupt/recovery contracts and saved provider/transport selections. Reuse completed source analyses.',
        'question':'Which remaining concrete sender/receiver/state/persistence links affect the normal task lifecycle recovery decisions?',
        'closure':'Resolve or explicitly disposition each missing critical link with owner/module/contract and acceptance condition; no repeat parsing of completed units or replacement of full-scope requirements.',
        'deferredDedicatedVerification':'Actual local save/revision/durability, hook effective layer state, MCP OAuth/restart, OS/account/native ABI and full mode/shared closure remain local acceptance gaps.'}
    assert state['latestBehaviorAuthorizationState']==before['latestBehaviorAuthorizationState']
    assert state['buildInputDispositions']==before['buildInputDispositions'] and not state['fullAnalysisCompleted']
    write(STAGE/'analysis-state.json',state)
    # Verify preservation and new cross-artifact coverage, without replaying old tests.
    assert scope['features'][:103]==old['features']
    assert scope['supportOperations'][:27]==old['supportOperations']
    assert scenarios['scenarios'][:406]==scenarios_old['scenarios']
    assert scope['retainedAssociationBacklog']==old['retainedAssociationBacklog']
    assert scope['operationReviewQueue']==old['operationReviewQueue']
    assert len(scope['features'])==120 and sum(len(f['operationMembers']) for f in scope['features'])==124
    assert len(scope['supportOperations'])==31 and len(scope['rootCandidateDispositions'])==154
    assert len(scenarios['scenarios'])==457 and len({s['scenarioId'] for s in scenarios['scenarios']})==457
    assert all(s.get('executionStatus',s.get('status'))=='not-executed' for s in scenarios['scenarios'])
    assert dict(collections.Counter(r['role'] for r in scope['rootCandidateDispositions']))==c['rootCandidateDispositionCounts']
    assert len(coverage['features'])==120 and len(coverage['supportOperations'])==31
    assert len(coverage['unresolvedScope']['pendingSettingsPages'])==32 and len(pagecov['pageSurfacesWithScopedControlContracts'])==13
    assert {f['featureId'] for f in coverage['features']}=={f['featureId'] for f in scope['features']}
    assert {s for f in coverage['features'] for s in f['scenarioIds']}=={s['scenarioId'] for s in scenarios['scenarios']}
    assert sum(len(g['featureIds']) for g in coverage['taskGroups'])==120
    assert all(not f['implementationStarted'] for f in coverage['features'])
    checked=set();parsed={};pointers=0
    def verify(v):
        nonlocal pointers
        if isinstance(v,list):
            for z in v:verify(z)
        elif isinstance(v,dict):
            if {'path','bytes','sha256'}<=v.keys():
                n=v['path'];p=STAGE/n
                if not p.exists():p=OUT/n
                b=p.read_bytes();assert len(b)==v['bytes'] and sha(b)==v['sha256'],n
                checked.add(n)
                if 'jsonPointer' in v:
                    if n not in parsed:parsed[n]=json.loads(b)
                    x=parsed[n]
                    for token in v['jsonPointer'].lstrip('/').split('/') if v['jsonPointer'] else []:
                        token=token.replace('~1','/').replace('~0','~');x=x[int(token)] if isinstance(x,list) else x[token]
                    pointers+=1
            for z in v.values():verify(z)
    for x in [contract,scope,scenarios,coverage,state['settingsOperationBatch04'],state['featureScopeCurrentView'],state['stageDecisions']]:verify(x)
    validation={'finiteGoalsAdded':17,'all120FeaturesAnd457ScenariosMapped':True,'old103Features27Support406ScenariosPreserved':True,
        'originalQueuesPreserved':True,'additionalProjectAddOverlapRetained':True,'taskIdsUnchanged':True,'pendingSettingsContainers':32,
        'uniquePinnedFilesVerified':len(checked),'jsonPointersVerified':pointers,'newIsolatedCasesPassed':10,
        'newProductScenarioPasses':0,'modelSubmissionsAdded':0,'originalClientRunsAdded':0,'clientImplementationStarted':False,
        'originalNineCriteriaStatusChanged':False,'fullAnalysisCompleted':False}
    write(RAW/'validation.json',validation)
    lead='''当前以[analysis-state.json](analysis-state.json)和[本批归属结果](settings-operation-batch-04.md)为准。[台账v11](feature-scope-v11.json)有120项有限定义、124项用户操作、31项支撑及457条待执行产品规格，全部接到[恢复覆盖表v2](restoration-coverage-v2.json)的原T01至T16任务；[实施计划v7](implementation-plan-v7.md)保持原任务和依赖结构，其103/406数量是历史快照。

本地环境、Hooks、MCP已从初步源码合同落实为17项目标、4项支撑和51条规格，新增10项隔离回放通过，旧41项直接复用。45个设置容器中13个已有局部控件合同，32个待展开。真实宿主保存、配置耐久性、Hook生效层、OAuth与后台重启仍待验证，没有增加真实产品通过数或模型请求。

九项标准仍为4项资料/范围义务已有交付、5项部分完成。下一步核对普通创建/提交/审批/中断/恢复的关键接收链，局部运行缺口留在所属验收中。完整功能分母、模式共享闭包、独立运行时与完整行为验收未完成。以下批次数量和旧“下一项”均为历史记录。

'''
    docs={}
    for n in ['report.md','gaps.md']:
        text=(OUT/n).read_text();marker='[阶段决定表]'
        start=text.index(marker);header=text.split('\n\n',1)[0]
        docs[OUT/n]=header+'\n\n'+lead+text[start:]
    text=(ROOT/'README.md').read_text()
    marker='以下专项记录保留各自历史范围；当前数量和下一行动见上方阶段决定与状态文件。'
    start=text.index(marker)
    docs[ROOT/'README.md']='''# ccodex

当前为逆向分析阶段。[台账v11](analysis/'''+BASE+'''/feature-scope-v11.json)的120项有限定义、457条待执行规格已接到原实施计划的T01至T16；完整功能分母、模式剥离、独立运行时和真实验收仍待完成。

- [本地环境、Hooks、MCP：功能归属与接收边界](analysis/'''+BASE+'''/settings-operation-batch-04.md)
- [逐项恢复覆盖表v2](analysis/'''+BASE+'''/restoration-coverage-v2.json)
- [统一实施计划v7（任务结构，数量为历史快照）](analysis/'''+BASE+'''/implementation-plan-v7.md)
- [当前分析状态与下一行动](analysis/'''+BASE+'''/analysis-state.json)
- [30条缺失构建输入的处理方案](analysis/'''+BASE+'''/build-input-dispositions-v1.json)

'''+text[start:]
    docs[ROOT/'README.md']=docs[ROOT/'README.md'].replace('当前功能台账为v10','当前功能台账为v11')
    assert read(OUT/'analysis-state.json')==before
    for p in STAGE.rglob('*'):
        if p.is_file() and p.name!='analysis-state.json':
            target=OUT/p.relative_to(STAGE);assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(p,target);assert sha(target.read_bytes())==sha(p.read_bytes());target.chmod(0o444)
    for p,text in docs.items():p.write_text(text)
    temporary=OUT/'analysis-state.json.tmp';write(temporary,state);os.replace(temporary,OUT/'analysis-state.json')
    write(WORK/'publication.json',{'published':NAMES,'stateUpdatedAtUtc':state['updatedAtUtc'],'validation':validation,
        'rawArtifactsImmutable':True,'goalStillActive':True})
    print(json.dumps({'published':NAMES,'counts':counts,'currentDefinitions':120,'currentSpecifications':457,
        'remainingSettingsContainers':32,'validation':validation},ensure_ascii=False))
