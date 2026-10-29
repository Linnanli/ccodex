"""Assemble reviewable analysis deliverables; publishing is a separate step."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import copy
import hashlib
import json
import shutil
import sys

ROOT = Path(sys.argv[1]).resolve()
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/settings-operation-batch-04'
DRAFT = WORK / 'deliverables'
RAW = DRAFT / 'raw/restoration-plan-v7'
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'
DRAFT.mkdir(exist_ok=True)
RAW.mkdir(parents=True, exist_ok=True)

def read(path):
    return json.loads(path.read_text())

def write(name, value):
    p = DRAFT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    return p

def pin(path, pointer=None):
    data = path.read_bytes()
    try:
        name = str(path.relative_to(DRAFT))
    except ValueError:
        try:
            name = str(path.relative_to(OUT))
        except ValueError:
            name = str(path)
    value = dict(path=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    if pointer is not None:
        value['jsonPointer'] = pointer
    return value

def ref(name, pointer=None):
    return pin(OUT / name, pointer)

now = datetime.now(timezone.utc).isoformat()
state = read(OUT / 'analysis-state.json')
assert state['featureScopeCurrentView']['snapshotVersion'] == 10
shutil.copy2(OUT / 'analysis-state.json', RAW / 'analysis-state-before.json')
ledger = read(OUT / 'feature-scope-v10.json')
scenarios = read(OUT / 'feature-scope-v10-scenarios.json')
previous = read(OUT / 'implementation-milestones-v6.json')

# Preserve scope and reuse the completed AST selections, rather than reparse them.
asts = {}
for d in sorted(WORK.iterdir()):
    if not d.is_dir() or not (d / 'source-contracts.json').exists():
        continue
    target = RAW / d.name
    shutil.copytree(d, target, dirs_exist_ok=True)
    asts[d.name] = read(target / 'source-contracts.json')
assert len(asts) == 11, list(asts)
for name in ['probe_environment_extensions.cjs', 'assemble_restoration_plan.py',
             'settings_operations_ast.mjs', 'git_settings_ast.mjs']:
    shutil.copy2(ROOT / 'scripts/analysis' / name, RAW / name)
shutil.copy2(WORK / 'isolated-observations.json', RAW / 'isolated-observations.json')
shutil.copy2(WORK / 'validate_deliverables.py', RAW / 'validate_deliverables.py')
observations = read(RAW / 'isolated-observations.json')
assert observations['passed'] == 41 and observations['failed'] == 0
write('raw/restoration-plan-v7/attempts.json', {
    'parses': {'completed': 11, 'failed': 0, 'newReaRuns': 0,
               'method': 'Full Program parsing with bounded export/lexical selections; imported boundaries remain separate.'},
    'probeAttempts': [
        {'sessionId': 60056, 'exitCode': 1, 'cause': 'Fixture expected non-ASCII MCP name to fall back; saved function returns a hyphen. No target source changed.'},
        {'sessionId': 95524, 'exitCode': 0, 'passed': 41}],
    'validationAttempts': [{'sessionId':44256,'exitCode':1,'cause':'Verifier assumed one scenario status field; inherited snapshots use both status and executionStatus. Source and scenario ledgers unchanged.'}],
    'productScenariosExecuted': 0, 'modelSubmissionsAdded': 0,
    'originalClientRunsAdded': 0})

def unit(directory, name):
    units = asts[directory]['units']
    i = next(i for i, u in enumerate(units) if u['name'] == name)
    return pin(RAW / directory / 'source-contracts.json', f'/units/{i}')

fact_specs = [
 ('ENV-ENTRY', 'local-environments-01', ['p'],
  'Local-host flag redirect changes the selected local-environments route to codex-cloud, converts personal-vault to tab and preserves hash/state. The normal child is keyed by host and location.'),
 ('ENV-STATE', 'local-content-01', ['Ut'],
  'Workspace/project/config selection, workflow return, fetching, parse/read errors and editor navigation are distinct. A successful conflict reload increments an editor key; entering edit does not itself save.'),
 ('ENV-EDITOR', 'local-editor-01', ['Ft','it','Rt'],
  'Editor captures initial config/revision, guards dirty/name/action/read/project/saving states, offers conflict discard and separately reports saved-but-selection-failed. Script and action controls update a local draft.'),
 ('ENV-SAVE', 'local-editor-01', ['ht','gt'],
  'saveConfig receives expectedRevision and serialized raw data. Invalidation starts even for a conflict; nonconflict awaits invalidation, then activation. Worktree selection needs a Git root; workspace selection has its own callback. Actual host implementation is outside this selection.'),
 ('ENV-ENCODING', 'local-editor-01', ['ot','st','J'],
  'First-party TOML generation preserves version, setup/cleanup and per-platform scripts, filters blank actions, trims names/commands and normalizes CRLF. Runtime script execution is a separate consumer.'),
 ('HOOK-ENTRY', 'hooks-01', ['Jt','Ot','gt'],
  'Page resolves host/project roots and source selection, lists or refreshes hooks, opens details and submits individual enabled/trustedHash edits or bulk trust. Root and query error/loading/empty states are separate.'),
 ('HOOK-MODEL', 'hooks-model-01', ['o','s','d','x','v'],
  'Sources are grouped as plugin/user/admin/project/sessionFlags/unknown. Managed sources normalize to admin; active means managed or enabled-and-trusted. Hook keys deduplicate first occurrence; route selection requires the project root to be present.'),
 ('HOOK-ROW', 'hooks-rows-01', ['z','V'],
  'Managed rows display an always-on disabled switch. Untrusted/modified hooks require review and display disabled toggles. Local unmanaged rows can open the source config; remote rows omit that action. Details differ by command/prompt/agent/MCP-tool type.'),
 ('HOOK-QUERY', 'hooks-provider-01', ['assignment-wqt'],
  'Host-scoped hooks/list query sends cwds. No roots disables the query and its queryFn explicitly rejects empty roots, even though the public schema allows omitted/empty cwds.'),
 ('HOOK-WRITE', 'hooks-provider-01', ['assignment-Eqt','assignment-Tqt','bqt'],
  'config/batchWrite writes hooks.state.<JSON.stringify(key)>.enabled and/or trusted_hash with upsert, filePath:null, expectedVersion:null and reloadUserConfig:true. okOverridden throws HookStateOverriddenError. Saved cache responses roll back on error; settled invalidation is host-scoped and broadcast.'),
 ('MCP-ENTRY', 'mcp-01', ['d'],
  'MCP settings delegates to the shared extensions component with manageOnly:true.'),
 ('MCP-SHARED', 'mcp-content-01', ['go','Qa'],
  'manageOnly chooses initialManageTab:mcps and uses the shared management component. The same chunk includes plugins, skills, marketplaces and apps; this entry does not prove the whole chunk is MCP-only or ChatGPT-only.'),
 ('MCP-MANAGER', 'mcp-content-01', ['ha','Ca'],
  'Manager distinguishes configured/plugin-provided servers, auth states, search, edit/create/uninstall, pending restart and project-source read-only controls. A restart dispatch requests app-server restart for the selected host.'),
 ('MCP-WRITE', 'mcp-provider-01', ['Jjn','Xjn'],
  'MCP save/delete uses config/batchWrite replace at mcp_servers.<key> and the chosen writable file; toggle uses config/value/write upsert at mcp_servers.<key>.enabled with default file. Both explicitly use expectedVersion:null; toggle owns optimistic cache/rollback/settled refresh.'),
 ('MCP-EDITOR', 'mcp-content-01', ['na','aa','oa','Sa'],
  'Editor separates stdio and streamable_http fields, retains base timeouts/tool lists and OAuth fields, trims argument/env/header rows and reports save/uninstall errors. Existing transport changes require uninstall first. Name normalization can return a hyphen for non-ASCII-only names.'),
 ('MCP-OAUTH', 'mcp-content-01', ['ha'],
  'mcpServer/oauth/login sends name and conditionally clientRegistration. It caches the authorization URL, rejects empty/invalid browser-open results, clears pending authentication state on error, consumes matching-host completion and invalidates status only on success. Actual browser and OAuth service remain untested.'),
 ('MCP-SELECTOR', 'mcp-provider-01', ['KI'],
  'Requests use a host selector with manager/connected client/cached/deferred RPC paths and watchers. Selected import/export identity is proven; the actual injected manager and live host are not established by isolated replay.')]
facts = [dict(id=i, claim=c, method='static-full-program-bounded-selection', confidence='confirmed-with-stated-boundaries',
              sourceUnits=[unit(d,n) for n in names], actualProductBehaviorProven=False)
         for i,d,names,c in fact_specs]

def normalize(v):
    if isinstance(v, dict):
        return {k: normalize(x) for k,x in v.items() if k not in ('$schema', '$id', 'title', 'description')}
    if isinstance(v, list):
        return [normalize(x) for x in v]
    return v

schema_names = ['HooksListParams','HooksListResponse','ConfigBatchWriteParams','ConfigValueWriteParams',
                'ConfigWriteResponse','McpServerOauthLoginParams','McpServerOauthLoginResponse',
                'McpServerOauthLoginCompletedNotification']
comparisons=[]
for mode in ['stable','experimental']:
    for name in schema_names:
        original=OUT/f'raw/protocol/{mode}/v2/{name}.json'
        public=OUT/f'raw/public-cli-npm/schema/{mode}/v2/{name}.json'
        x,y=read(original),read(public)
        comparisons.append(dict(schema=name, mode=mode, frozen=pin(original), publicCandidate=pin(public),
            jsonEqual=x==y, contractShapeEqual=normalize(x)==normalize(y),
            requiredFields=x.get('required', []), propertyNames=sorted(x.get('properties', {}))))
assert all(c['contractShapeEqual'] for c in comparisons)
entries=read(OUT/'settings-section-dispositions.json')['entries']
selected=[]
for slug in ['local-environments','hooks-settings','mcp-settings']:
    i=next(i for i,e in enumerate(entries) if e['slug']==slug)
    selected.append(dict(slug=slug, entryRef=ref('settings-section-dispositions.json',f'/entries/{i}'),
                         operationDefinitionStatus='source-contract-added-finite-user-goal-ledger-not-yet-expanded',
                         mode='unknown',confirmedExclusion=False,actualMountObserved=False))
contracts = dict(schemaVersion=1, baselineId=BASE, recordedAtUtc=now, scope='Three environment/extension pages and selected first-party providers',
    entries=selected, facts=facts, astSelections=[pin(RAW/d/'source-contracts.json') for d in asts],
    isolatedObservations=pin(RAW/'isolated-observations.json'),
    protocolSchemaComparisons=comparisons,
    protocolDecision={'methods':['hooks/list','config/batchWrite','config/value/write','mcpServer/oauth/login'],
        'adopt':'Explicit backend-adapter contracts for selected compatible shapes; maintain host selector, layer errors, restart and notifications in first-party modules.',
        'uiStricterThanSchema':'Keep nonempty project roots guard for hooks/list.',
        'concurrencyDifference':'Environment save expectedRevision is independent of config API expectedVersion:null.',
        'actualCompatibilityProven':False,
        'pending':['Actual provider/transport identity','Hook execution/trust effects','Configuration durability and restart','MCP OAuth/browser/completion lifecycle','Full backend method coverage']},
    counts=dict(pageSourceContractsAdded=3,staticFacts=len(facts),fullProgramSelections=len(asts),
        schemaPairs=len(comparisons),schemaFiles=2*len(comparisons),isolatedCasesPassed=41,
        newFiniteFeatureDefinitions=0,productScenariosExecuted=0,modelSubmissionsAdded=0,originalClientRunsAdded=0),
    fullAnalysisCompleted=False, clientImplementationStarted=False)
write('environment-extension-contracts.json',contracts)

def fids(start,end):
    return [f'FSC-{n:04}' for n in range(start,end+1)]

# A single owning task per finite feature; cross-cutting consumers stay explicit.
group_specs=[
 ('T01','General',fids(1,28),'settings/general',['W04','W06','W07'],['settings-general-page-contracts.json'],
  ['composer/preferences','terminal/preferences','window/preferences','shortcuts/popup','localization'],['query/schema/UI packages','runtime/platform capabilities']),
 ('T02','Agent',fids(29,34),'settings/agent',['W05','W06','W07'],['settings-agent-page-contracts.json','settings-config-dispatch.json','settings-config-receiver-origin.json'],
  ['tasks/configuration','backend-adapter/config'],['config repository','schema/query packages']),
 ('T03','任务生命周期',fids(35,36)+fids(46,48),'tasks',['W04','W05','W06','W07'],['thread-turn-feature-contracts.json','thread-archive-entry-contracts.json','thread-resume-entry-contracts.json','thread-fork-entry-contracts.json','thread-start-entry-contracts.json'],
  ['composer','approvals','projects','worktrees','notifications'],['backend request/event transport','stream rendering']),
 ('T04','电脑使用',fids(37,44),'computer-use',['W04','W05','W06','W07'],['cua-feature-scope.json'],
  ['approvals','host/capabilities/computer-use'],['native permissions/IPC','query/audio packages']),
 ('T05','项目与远程入口',fids(45,45),'projects',['W04','W05','W06','W07'],['wsl-project-actions-contracts.json'],
  ['connections','host/project-registry'],['filesystem/remote connection adapters']),
 ('T06','Git',fids(49,58),'git',['W05','W06','W07'],['settings-git-page-contracts.json'],
  ['changes','pull-requests','watchers'],['Git/PR adapters','query/schema packages']),
 ('T07','工作树',fids(59,66),'worktrees',['W04','W05','W06','W07'],['settings-operation-batch-02.json'],
  ['projects','tasks','host/worktrees'],['Git/worktree adapters','backend archive']),
 ('T08','快捷键',fids(67,71),'shortcuts',['W03','W06','W07'],['settings-operation-batch-02.json'],
  ['commands','window','tabs','links'],['platform keyboard registration','key parser/UI packages']),
 ('T09','文件查看器',fids(72,73),'file-viewers',['W04','W06','W07'],['settings-operation-batch-02.json'],
  ['files','host/open-target'],['file discovery/provider adapters']),
 ('T10','外观',fids(74,92),'appearance',['W03','W06','W07'],['settings-operation-batch-03.json'],
  ['renderer/app/theme','window/dock','resources/fonts'],['theme parser/normalizer','query/schema/UI packages','clipboard/fonts/OS']),
 ('T11','Appshot',fids(93,96),'appshots',['W03','W04','W06','W07'],['settings-operation-batch-03.json'],
  ['mini','tasks','host/capabilities/appshot'],['native capture','keyboard','audio/assets']),
 ('T12','桌面通知',fids(97,102),'notifications/desktop',['W03','W04','W06','W07'],['settings-operation-batch-03.json'],
  ['tasks','approvals','questions','dot','host/capabilities/notifications'],['OS notification/audio/import adapters']),
 ('T13','账户通知',fids(103,103),'notifications/account',['W05','W06','W07'],['settings-operation-batch-03.json'],
  ['account','notifications/shared-controls'],['account HTTP service','query/schema packages']),
 ('T14','本地环境',[],'local-environments',['W04','W05','W06','W07'],['environment-extension-contracts.json'],
  ['projects','worktrees','host/local-environments'],['host save/read/selection','TOML/schema/form packages']),
 ('T15','Hooks',[],'hooks',['W05','W07'],['environment-extension-contracts.json'],
  ['projects','plugins','backend-adapter/config'],['hooks/list','config/batchWrite','query/UI packages']),
 ('T16','MCP',[],'mcp',['W03','W05','W07'],['environment-extension-contracts.json'],
  ['extensions/shared-manager','backend-adapter/config','host/external-browser'],['config APIs','MCP OAuth/status/notifications','query/UI packages'])]

def evidence(name):
    return pin(DRAFT/name) if (DRAFT/name).exists() else ref(name)

groups=[]
for gid,name,ids,folder,deps,sources,consumers,externals in group_specs:
    groups.append(dict(taskId=gid,name=name,featureIds=ids,
        primaryModule=f'apps/desktop/src/renderer/features/{folder}',consumerModules=consumers,
        dependsOn=deps,evidence=[evidence(s) for s in sources],externalDependencies=externals,
        sourceDesignCanProceed=True,implementationStarted=False,
        productAcceptancePrerequisites=['Actual entry/host/account/platform conditions','Effective receiver and side effects','Feature-specific failure/cancel/restart','Mode and shared-dependency closure'],
        userGoalLedgerStatus='finite-definitions-linked' if ids else 'new-source-contracts-pending-operation-reconciliation'))
feature_rows=[]
for index,f in enumerate(ledger['features']):
    g=next(g for g in groups if f['featureId'] in g['featureIds'])
    feature_rows.append(dict(featureId=f['featureId'],name=f['name'],taskId=g['taskId'],module=g['primaryModule'],
        consumerModules=g['consumerModules'],featureRef=ref('feature-scope-v10.json',f'/features/{index}'),
        operationIds=[m['operationId'] for m in f['operationMembers']],supportOperationIds=f.get('supportOperationIds',[]),
        scenarioIds=f['scenarioIds'],externalDependencies=g['externalDependencies'],evidence=g['evidence'],
        mode=f['mode'],retentionStatus=f['retentionStatus'],completeChainProven=f['completeChainProven'],
        runtimeStatus=f['runtimeStatus'],knownGaps=f['knownGaps'],implementationAcceptance=f['implementationAcceptance'],
        readiness='bounded-source-design-with-explicit-integration-gaps',implementationStarted=False))
covered_slugs={'general-settings','agent','computer-use','git-settings','worktrees','keyboard-shortcuts','file-type-handlers','appearance','appshots','notifications'}
pending_pages=[dict(entryId=e['entryId'],slug=e['slug'],entryRef=ref('settings-section-dispositions.json',f'/entries/{i}'),
    currentContractTask=next((g['taskId'] for g in groups if (g['taskId'],e['slug']) in [('T14','local-environments'),('T15','hooks-settings'),('T16','mcp-settings')]),None),
    disposition='retained-pending-operation-definition',mode='unknown')
    for i,e in enumerate(entries) if e['entryKind'] in ['catalog-page-container','existing-feature-page-container'] and e['slug'] not in covered_slugs]
assert len(pending_pages)==35
support_rows=[]
for i,op in enumerate(ledger['supportOperations']):
    oid=op['operationId']
    consumers=[f['featureId'] for f in feature_rows if oid in f['supportOperationIds']]
    support_rows.append(dict(operationId=oid,sourceRef=ref('feature-scope-v10.json',f'/supportOperations/{i}'),
        consumerFeatureIds=consumers,taskIds=sorted({f['taskId'] for f in feature_rows if f['featureId'] in consumers}),
        disposition='support-consumer-links-preserved' if consumers else 'cross-cutting-support-retained-owner-reconciliation-pending'))
families=read(OUT/'entry-family-map.json')['families']
coverage=dict(schemaVersion=1,baselineId=BASE,recordedAtUtc=now,featureLedger=ref('feature-scope-v10.json'),
    scenarioLedger=ref('feature-scope-v10-scenarios.json'),taskGroups=groups,features=feature_rows,supportOperations=support_rows,
    unresolvedScope=dict(pendingSettingsPages=pending_pages,legacyFamilies=families,
        legacyLedger=ref('entry-family-map.json'),legacyEntries=968,legacyEntriesFullyMapped=0,
        associationBacklogRef=ref('feature-scope-v10.json','/retainedAssociationBacklog'),
        pendingOperationQueueRef=ref('feature-scope-v10.json','/operationReviewQueue'),
        crossFeatureOverlapRef=ref('feature-scope-v10.json','/crossFeatureOverlapReviews'),
        otherRequiredCapabilities=['Files and changes','Terminal/PTY','Approvals and service requests','Remote/cloud','Browser ownership','Automations and other discovered commands/routes','Window/platform/system integration']),
    counts=dict(finiteFeatureDefinitions=103,userOperations=107,supportOperations=27,productScenarioSpecifications=406,
        owningTaskGroupsWithFiniteDefinitions=13,additionalSourceContractTaskGroups=3,pendingSettingsPages=35,
        featuresImplemented=0,newProductScenarioPasses=0,confirmedChatGptExclusions=0),
    completeFeatureDenominator=None,fullAnalysisCompleted=False)
write('restoration-coverage-v1.json',coverage)

builds=read(OUT/'build-inputs.json')
decisions=[]
for i,b in enumerate(builds):
    p=b['input']
    if p.endswith('ensure-owl-electron-types.mjs'):
        category='runtime-types';target='packages/runtime-adapter/src/types + tools/build/runtime-types';action='Author types from the selected runtime capability contract; retain unresolved private APIs as explicit unsupported capability decisions.';gates=['W03']
    elif p.endswith(('prepare-dev.mjs','owl-shell.mjs')):
        category='runtime-driver';target='tools/build/runtime-driver';action='Author acquisition, launch and native-rebuild driver for an independently sourced, pinned runtime; do not copy the installed app.';gates=['W02','W03']
    elif p.endswith('generate-types.mjs'):
        category='contract-generator';target='tools/build/generate-contracts + packages/contracts';action='Generate from verified fixed schema inputs; maintain desktop extensions and protocol differences separately.';gates=['W01','W05']
    elif p.endswith(('run-package-typescript.mjs','run-package-oxlint.mjs','build-dev-vite.mjs')):
        category='workspace-tooling';target='tools/build + workspace package scripts';action='Author equivalent compile/lint/dev-build orchestration without original monorepo relative imports.';gates=['W02']
    elif p.endswith(('package.mjs','dev-metadata.ts')):
        category='packaging-metadata';target='tools/build/package + apps/desktop build metadata';action='Author independent identity/version/resource/runtime layout and reproducible build metadata.';gates=['W02','W03']
    elif p in ['pnpm-lock.yaml','package-lock.json','yarn.lock']:
        category='new-project-lock';target='pnpm-lock.yaml';action='Generate one exact new-project lock for the proposed pnpm workspace; preserve original installed-version uncertainty. Alternative lock names are inventory occurrences, not three required locks.';gates=['W02']
    elif p=='pnpm-workspace.yaml':
        category='workspace-config';target=p;action='Author package membership and local dependency boundaries for the independent workspace.';gates=['W02']
    elif p=='tsconfig.json':
        category='typescript-config';target='tsconfig.base.json + per-process tsconfig.json';action='Author process-specific type environments/references, target runtime and renderer compilation.';gates=['W02','W03']
    elif p.startswith('forge.config'):
        category='packager-config';target='apps/desktop/forge.config.ts or selected runtime packager integration';action='Author one packaging config after runtime integration is established; keep independent IDs, native ABI, resources, signing and update channel.';gates=['W02','W03']
    elif p.startswith('vite.config'):
        category='bundler-config';target='apps/desktop/vite.config.ts + per-process entry configs';action='Author separate main/preload/renderer/worker entries and externalize native and third-party dependencies appropriately.';gates=['W02','W03']
    elif p.endswith('analyze-heap-snapshot.mjs'):
        category='diagnostic-tool';target='tools/diagnostics/heap';action='Author diagnostic tooling independently; not a product startup prerequisite. Keep product Task Manager capability in W03.';gates=['W02']
    else:
        assert p.endswith(('computer-use-native-pipe-e2e.mjs','playwright-electron-agent-cdp.mjs')),p
        category='verification-tool';target='tests/desktop + tools/diagnostics';action='Author owned-fixture desktop/native-pipe/CDP verification. Retain the actual computer-use/browser features and their acceptance requirements.';gates=['W03','W04']
    decisions.append(dict(id=f'BUILD-{i+1:03}',originalOccurrenceRef=ref('build-inputs.json',f'/{i}'),
        original=b,input=p,decisionClass=category,replacement=target,action=action,dependsOn=gates,
        acceptance='Clean install/build/package or the named dedicated verification succeeds without original monorepo/install paths.',
        decisionStatus='analysis-disposition-proposed',replacementImplemented=False,originalInputRecovered=False))
write('build-input-dispositions-v1.json',dict(baselineId=BASE,recordedAtUtc=now,source=ref('build-inputs.json'),
    decisions=decisions,counts=dict(originalOccurrences=len(builds),uniqueOriginalInputPaths=len({b['input'] for b in builds}),
        dispositionRecords=len(decisions),implementedReplacements=0),
    packagingChoice='TypeScript/Vite/Forge responsibilities are source-derived candidates; runtime integration and exact new lock remain pending.',
    originalBuildReproduced=False,independentClientBuildProven=False))

foundation_specs=[
 ('W01','合同与来源映射',[],'packages/contracts + tools/recovery',['boundaries.json','ipc.json','module-boundary-proposals.json'],
  'Versioned DTO/error/notification/lifecycle contracts and first-party source map; preserve different service namespaces.'),
 ('W02','独立构建与依赖输入',[],'tools/build + workspace configuration',['build-input-dispositions-v1.json','dependency-import-decisions.json','dependencies.csv'],
  'Own exact lock and complete independent inputs/assets; original installed versions remain separately evidenced.'),
 ('W03','运行时与平台能力',['W01','W02'],'packages/runtime-adapter',['runtime-capability-decisions.json','public-runtime-comparison.json','browser-ownership-contracts.json'],
  'Independently available runtime, all required capabilities, native ABI and platform negative tests; no runtime route selected yet.'),
 ('W04','桌面传输与宿主',['W01','W03'],'packages/desktop-transport + apps/desktop/src/main',['preload-app-host.json','app-host-context.json','host-state-provider-contracts.json'],
  'Identity, trust, framing, messages/ports, errors, disconnect, ownership and disposal verified on the actual host.'),
 ('W05','后台适配',['W01','W02'],'packages/backend-adapter',['protocol-compatibility.json','exported-protocol-comparison.json','environment-extension-contracts.json'],
  'Actual provider/method identity and request/response/notification semantics verified; preserve all observed fields and unsupported capability errors.'),
 ('W06','状态与持久化',['W01','W03'],'packages/state-storage',['global-state-storage-origin-contracts.json','main-persistence-policy-contracts.json','shutdown-persistence-contracts.json'],
  'Independent paths, schema/defaults, revisions, flush/atomic replacement, shutdown, backup and migration durability verified.'),
 ('W07','应用壳与模式',['W04','W06'],'apps/desktop/src/renderer/app',['route-contracts.json','mode-transition-origin.json','settings-feature-entry-conditions.json'],
  'Initialization, routing, selected mode, account/platform gates, shared providers and window lifetime preserved.'),
 ('W08','其余功能与完整范围',['W04','W05','W06','W07'],'apps/desktop/src/renderer/features + main/workers',['entry-family-map.json','file-change-view-contracts-v2.json','terminal-feature-contracts.json'],
  'Reconcile all discovered entries and preserve every Codex/shared/unknown capability; no subset counts as full restoration.'),
 ('W09','剥离升级与最终验收',['W08']+[g['taskId'] for g in groups],'tools/recovery + tests + packaging',['feature-scope-v10.json','restoration-coverage-v1.json'],
  'Proven mode exclusions, all retained feature results, clean build/install, upgrade migration and rollback; no unresolved mocks/private dependencies counted complete.')]
# Resolve the established storage artifact names without guessing their content.
for k,n in enumerate(foundation_specs):
    if n[0]=='W06':
        alternatives=['global-state-storage-origin.json','main-persistence-policy.json','shutdown-persistence.json']
        foundation_specs[k]=(n[0],n[1],n[2],n[3],alternatives,n[5])
foundations=[dict(taskId=i,name=n,dependsOn=d,module=p,evidence=[evidence(s) for s in sources],
    exitCondition=exit_,status='planned-not-implemented') for i,n,d,p,sources,exit_ in foundation_specs]
milestones={k:copy.deepcopy(previous[k]) for k in [
    'baselineId','scope','currentAuthorizationScope','analysisMilestones',
    'implementationMilestones','sourceMappingRequiredFields','originalAnalysisCriteria']}
for m in milestones['analysisMilestones']:
    m['evidencePaths']=[p for p in m['evidencePaths'] if not p.startswith(('feature-scope-v','implementation-plan-v'))]
    if m['id']=='A1':
        m['evidencePaths']+=['feature-scope-v10.json','restoration-coverage-v1.json','entry-family-map.json']
        m['currentUnresolved']=dict(pendingUserEntryCandidates=1,retainedAssociationOrIntegrationItemsFromOldQueue=12,
            featuresWithConditionalAssociationToOneSettingsContainer=97,featuresAwaitingLegacyEntryIdentity=6,
            fullyResolvedOldEntries=0,oldEntriesUnmappedInFiniteView=967,unknownModeFeatures=103,
            pendingSettingsOperationContainers=35,completeFeatureDenominator=None)
    elif m['id']=='A2':
        m['evidencePaths']+=['build-input-dispositions-v1.json','runtime-capability-decisions.json','public-runtime-comparison.json']
    elif m['id']=='A3':
        m['evidencePaths']+=['restoration-coverage-v1.json','environment-extension-contracts.json']
    else:
        m['evidencePaths']+=['implementation-plan-v7.md','feature-scope-v10-scenarios.json']
milestones.update(dict(schemaVersion=7,recordedAtUtc=now,previousSnapshot=ref('implementation-milestones-v6.json'),
    currentFeatureScope={'ledger':ref('feature-scope-v10.json'),'counts':ledger['counts']},currentScenarios=ref('feature-scope-v10-scenarios.json'),
    restorationCoverage=pin(DRAFT/'restoration-coverage-v1.json'),buildInputDispositions=pin(DRAFT/'build-input-dispositions-v1.json'),
    environmentExtensionContracts=pin(DRAFT/'environment-extension-contracts.json'),foundationTasks=foundations,
    restorationTaskGroups=groups,behaviorAuthorization=copy.deepcopy(state['latestBehaviorAuthorizationState']),
    fullAnalysisCompleted=False,implementationCompleted=False,
    currentStatus='consolidated-evidence-backed-restoration-design-with-explicit-unresolved-full-scope',
    nextAnalysisActions=[
      {'id':'NEXT-01','question':'Complete provider/source/receiver and finite operation reconciliation for the three environment/extension pages.',
       'inputs':['environment-extension-contracts.json','settings-section-dispositions.json'],
       'exit':'Stable user goals with source, field/error/state/persistence and mode conditions; reconcile shared plugins entry without double counting.'},
      {'id':'NEXT-02','question':'Close actual task submit/stream/approval/interrupt/resume receiver bindings against existing contracts.',
       'inputs':['thread-turn-feature-contracts.json','thread-start-entry-contracts.json','thread-resume-entry-contracts.json'],
       'exit':'Same host/provider chain with explicit remaining runtime cases; reuse existing AST and no unapproved model submissions.'},
      {'id':'NEXT-03','question':'Decide each runtime and build-critical capability source/adapter route.',
       'inputs':['runtime-capability-decisions.json','build-input-dispositions-v1.json'],
       'exit':'Independent source/version/ABI or validated alternative for each required capability; keep product behavior intact.'},
      {'id':'NEXT-04','question':'Reconcile the rest of the discovered entry families and settings, including mode/shared closure.',
       'inputs':['entry-family-map.json','restoration-coverage-v1.json'],
       'exit':'All discovered entries have semantic dispositions and complete retained function denominator; unknowns stay listed.'}],
    investigationRule='Reuse completed source contracts. Each batch must change a specific function/adapter/dependency/build/acceptance decision. Record local blockers on affected tasks; preserve the full objective.'))
write('implementation-milestones-v7.json',milestones)
shutil.copy2(WORK/'implementation-plan-v7.md',DRAFT/'implementation-plan-v7.md')
stage=copy.deepcopy(read(OUT/'analysis-stage-decisions.json'))
stage['previousSnapshot']=ref('analysis-stage-decisions.json')
stage['recordedAtUtc']=now
findings={
 'AC-01':'固定基线沿用；本批11个Program选择按原字节核对，公开后台候选与冻结客户端来源分列。',
 'AC-02':'当前103项有限定义、107用户操作、27支撑、1待审；968旧入口与35个设置容器的完整功能处置仍未结束，完整分母未知。',
 'AC-03':'103项定义均unknown，确认ChatGPT专属排除0；共享扩展管理器和桌面通知的混合来源不允许整块删除。',
 'AC-04':'环境保存/激活、Hooks信任/启停和MCP配置/OAuth已接到选定provider及协议字段；真实实例、运行消费者及全功能闭包仍不完整。',
 'AC-05':'202项依赖及来源/引入动作保留；78根声明仅6有root安装版本，候选和新工程锁分开，完整替换兼容仍待验证。',
 'AC-06':'原生/Wasm/Owl等特殊边界独立记录保留；公共运行时局部原语与objc构建候选不证明全能力和目标ABI。',
 'AC-07':'map、REA截断、动态关系和构建缺口已记录；本批对30条缺失输入提出逐项处置，尚未生成替代配置或证明独立构建。',
 'AC-08':'真实完成/重开和停止重启记录保留；取消仍未测。新增41隔离源码场景与16对schema核对不增加产品通过数；模型样例剩余0。',
 'AC-09':'103定义、107操作、27支撑和406规格已接到恢复任务；30构建输入有处置，目录/依赖/顺序/升级已统一。完整功能映射、运行时路线和真实验收尚未完成。'}
stage_evidence={
 'AC-01':['environment-extension-contracts.json'],
 'AC-02':['restoration-coverage-v1.json','feature-scope-v10.json'],
 'AC-03':['feature-scope-v10.json','environment-extension-contracts.json'],
 'AC-04':['environment-extension-contracts.json','restoration-coverage-v1.json'],
 'AC-05':['dependency-import-decisions.json'],
 'AC-06':['runtime-capability-decisions.json','public-runtime-comparison.json'],
 'AC-07':['build-input-dispositions-v1.json'],
 'AC-08':['environment-extension-contracts.json','behavior-stop-restart.json'],
 'AC-09':['implementation-plan-v7.md','implementation-milestones-v7.json','restoration-coverage-v1.json','build-input-dispositions-v1.json']}
for c in stage['criteria']:
 c['currentFinding']=findings[c['id']]
 c['currentSupplementaryEvidence']=[evidence(n) for n in stage_evidence[c['id']]]
stage['counts'].update(currentFeatureDefinitions=103,currentRootOperationCandidates=133,currentUnexecutedScenarios=406,
                       confirmedChatGptExclusions=0)
stage['currentScope']=dict(featureLedger=ref('feature-scope-v10.json'),scenarioLedger=ref('feature-scope-v10-scenarios.json'),
    restorationCoverage=pin(DRAFT/'restoration-coverage-v1.json'),buildInputDispositions=pin(DRAFT/'build-input-dispositions-v1.json'),
    completeFeatureDenominator=None,pendingSettingsOperationContainers=35,modelSamplesRemaining=0)
for s in stage['stages']:
 if s['number'] in [2,4,5,6]:
  s['currentSupplementaryEvidence']=[evidence(n) for n in (['restoration-coverage-v1.json'] if s['number']==2 else
     ['environment-extension-contracts.json'] if s['number'] in [4,5] else ['implementation-plan-v7.md','build-input-dispositions-v1.json'])]
stage['nextAction']=dict(issueId='SD-01/SD-03/SD-06',
    completedSubstep='统一103项有限定义与全部406规格的恢复任务映射；处置30构建输入；新增环境/Hooks/MCP合同、16对schema核对及41隔离场景。',
    fixedInput='本批三个页面/选定provider及已有源码，复用已完成AST；完整范围仍含35个待归属设置容器及其余入口族。',
    question='先完成三个页面的操作与实际provider链归属，再核对普通创建/提交/审批/中断/恢复的关键接收链。',
    closure='稳定用户目标、源范围、状态/字段/错误/接收方/持久化及具体运行缺口接到恢复任务；不增加未授权模型请求。',
    deferredDedicatedVerification='OS/账户/OAuth、真实配置耐久性、原生ABI/Owl全能力、实际取消与完整模式共享闭包。')
stage['fullAnalysisCompleted']=False
write('analysis-stage-decisions-v2.json',stage)
rows=['# 当前分析阶段决定','',
 '当前有限范围为103项定义、406条待执行产品规格；完整功能分母未知。九项标准中四项资料/范围义务有交付、五项部分完成。客户端实现尚未开始。','',
 '| 标准 | 状态 | 当前结论 |','| --- | --- | --- |']
for c in stage['criteria']:
 rows.append(f"| {c['id']} | {'资料/范围义务已有交付' if c['status']=='satisfied-with-scope-limits' else '部分完成'} | {c['currentFinding']} |")
rows+=['','[统一实施计划](implementation-plan-v7.md)与[恢复覆盖表](restoration-coverage-v1.json)落实已定义功能的模块、依赖和验收；[构建输入处置](build-input-dispositions-v1.json)保留全部30条记录。',
 '',stage['nextAction']['question'],'',
 '各局部运行缺口只限制对应验收，静态与离线分析继续推进。35个设置容器、968旧入口处置、12项关联待办、模式共享闭包和完整功能分母保留；不能据当前表宣称完整分析或可构建客户端。',
 '', '[逐项依据与原39条子要求](analysis-stage-decisions-v2.json)保留原标准文本和历史判定，当前结论与新增证据单列。','']
(DRAFT/'analysis-stage-decisions-v2.md').write_text('\n'.join(rows))
(DRAFT/'environment-extension-summary.md').write_text('''# 本地环境 Hooks 与 MCP 的恢复边界

本批为三个页面和选定 provider 增加 17 条静态合同、41 项隔离源码回放及 16 对协议 schema 比较。未新增正式功能定义，当前仍为 103 项有限定义、406 条待执行产品规格；35 个设置容器的完整操作归属继续保留。

本地环境保存与激活分开，revision 冲突触发重新读取；保存后激活失败保留 selection-failed。Hooks 保留来源分组、受管理/待信任状态、带 JSON 引号的状态键、okOverridden 错误与回滚。MCP 将保存/删除、启停、OAuth 和后台重启分开，保留 stdio/HTTP 字段和项目来源只读条件。

冻结与公开候选的八类 schema 在 stable/experimental 中共 16 对合同形状相同，详见[结构化合同](environment-extension-contracts.json)。Hooks 列表的页面规则比 schema 更严格：无项目根时不查询。实际服务身份、宿主保存、OAuth、通知和耐久性尚待核对。41 个回放使用合成替身，没有真实配置写入、模型任务、hook 执行或原客户端运行。第一次回放的错误预期已修正，失败与成功记录均保留。

[统一实施草案](implementation-plan-v7.md)将这些边界安排为环境、Hooks、MCP 三组恢复任务，并连接当前全部有限功能与构建缺口。后续先完成三页面的操作归属及真实 provider 链，再回到任务生命周期的主要接收链核对；不以设置页局部调查代替完整目标。
''')
inputs=['baseline.json','files.json','build-inputs.json','feature-scope-v10.json','feature-scope-v10-scenarios.json',
        'entry-family-map.json','settings-section-dispositions.json','analysis-stage-decisions.json',
        'implementation-milestones-v6.json']
write('restoration-plan-v7-provenance.json',dict(baselineId=BASE,recordedAtUtc=now,inputs=[ref(n) for n in inputs],
    stateBefore=pin(RAW/'analysis-state-before.json'),scripts=[pin(RAW/n) for n in ['assemble_restoration_plan.py','probe_environment_extensions.cjs','settings_operations_ast.mjs','git_settings_ast.mjs','validate_deliverables.py']],
    outputScope='103 finite definitions mapped; original full analysis requirements and unknown full denominator retained.',
    analysisRuns='Completed formal REA output reused; bounded full Program AST supplements, selected public/frozen schema comparison and isolated source replay added.',
    authorization={'scope':'analysis and behavior verification','modelRemaining':0,'modelSubmissionsAdded':0,'originalClientRunsAdded':0},
    targetSourceModified=False,thirdPartyClientImplementationsGenerated=False,clientImplementationStarted=False))
print(json.dumps(dict(draft=str(DRAFT),features=len(feature_rows),scenarios=len(scenarios['scenarios']),
    buildOccurrences=len(decisions),astSelections=len(asts),schemaPairs=len(comparisons),isolatedCases=41)))
