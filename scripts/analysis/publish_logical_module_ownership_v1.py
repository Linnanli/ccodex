#!/usr/bin/env python3
"""Resolve saved proposal overlaps as design decisions, without target execution."""
import copy
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/logical-module-ownership-v1-work'
WORK.mkdir(parents=True, exist_ok=True)
PINS = {}
CACHE = {}


def digest(b):
    return hashlib.sha256(b).hexdigest()


def load(name):
    p = OUT / name
    if name not in CACHE:
        b = p.read_bytes()
        PINS[name] = {'path': str(p.relative_to(ROOT)), 'bytes': len(b), 'sha256': digest(b)}
        CACHE[name] = json.loads(b)
    return CACHE[name]


def value_at(v, ptr):
    for token in ptr[1:].split('/') if ptr else []:
        k = token.replace('~1', '/').replace('~0', '~')
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def ref(name, ptr=''):
    v = load(name)
    value_at(v, ptr)
    return {**PINS[name], 'jsonPointer': ptr}


catalog = load('logical-module-inventory-v1.json')
coverage = load('restoration-coverage-v17.json')
features = load('feature-scope-v26.json')
milestones = load('implementation-milestones-v9.json')
ordering = load('restoration-current-ordering-v1.json')
load('feature-scope-v24-scenarios.json')
load('analysis-stage-decisions-v4.json')
rows = catalog['records']
assert len(rows) == 38 and len(catalog['sourceOverlapReviews']) == 19
by_id = {r['id']: r for r in rows}
by_index = {r['id']: i for i, r in enumerate(rows)}
foundation = {t['taskId']: (i, t) for i, t in enumerate(milestones['foundationTasks'])}
tasks = {t['taskId']: (i, t) for i, t in enumerate(coverage['taskGroups'])}
feature_index = {f['featureId']: i for i, f in enumerate(features['features'])}


def module_ref(index):
    return ref('logical-module-inventory-v1.json', f'/records/{index}')


def idx(prefix, suffix):
    key = 'LM-' + prefix + '-' + suffix
    assert key in by_id
    return key


MANAGER = idx('BOUNDARY', 'STRUCT-RWC-MANAGER')
OLD_SELECTOR = idx('BOUNDARY', 'STRUCT-RWC-SELECTOR')
SELECTOR = idx('PROVIDER', 'host-rpc-selector')
RESOLVER = idx('BOUNDARY', 'STRUCT-RWC-RESOLVER')
REGISTRY = idx('PROVIDER', 'domain-host-registry')
LIFECYCLE = idx('PROVIDER', 'provider-lifecycle')
INTERNAL = idx('PROVIDER', 'internal-manager-rpc-adapter')
HOSTED = idx('BOUNDARY', 'STRUCT-RWC-HOSTED-FILES')
PROJECTS = idx('BOUNDARY', 'STRUCT-RWC-PROJECTS')
ASSEMBLY = idx('APPHOST', 'AH-M04')
CONNECTION = idx('APPHOST', 'AH-M02')
POLICY = idx('RUNTIME', 'RF-1')
PROVIDER = idx('RUNTIME', 'RF-2')
GATES = idx('RUNTIME', 'RF-3')

# A canonical responsibility owner is a maintenance decision, not an original module.
canonical = {r['id']: r['id'] for r in rows}
canonical[OLD_SELECTOR] = SELECTOR
primary = ['W05', 'W04', 'W04', 'W04', 'W05', 'W05', 'W04', 'W06', 'W04', 'W07', 'W07',
           'W04', 'W04', 'W04', 'W04', 'W04', 'W04', 'W03', 'W03',
           'W07', 'W07', 'W07', 'W03', 'W03', 'W03',
           'W04', 'W04', 'W04', 'W04', 'W04', 'W05', 'W03', 'W04', 'W07',
           'W07', 'W07', 'W07', 'W07']
assert len(primary) == len(rows)
pending = [
    'Identify each consumer/provider branch of Dfn and its configured transport; conditional T03 composition is not the whole consumer set.',
    'The KI contract is unified with the later host selector proposal; enumerate additional callers separately.',
    'Trace renderer AW/TFt callers and desktop fetch completion; a containing-file classification is not complete runtime placement.',
    'Only reviewed X2t resolver/forwarding members are assigned; other class members and consumers remain unreviewed.',
    'Map hosted-file extension consumers, schemas and results to retained user goals; source factory wiring alone is insufficient.',
    'Identify each host connection/provider and concrete backend delivery; do not infer public CLI adoption.',
    'Identify p1 injected client, socket consumers and corresponding user goals.',
    'Compare the createLocal dialog/service chain with FSC-0105 local delegation; T05/FSC-0045 covers remote WSL creation and cannot supply this identity.',
    'Map send/sendInline/sendCritical and assembled handlers to retained domain consumers; codec evidence is not a whole-feature assignment.',
    'Bind annotation mounting/preview/disposal to concrete browser user entry and mode consumers.',
    'Bind annotation root/rendering to concrete browser user entry; do not infer T26 membership from the browser label.',
    'Identify each window/port sender and hosted feature consumer; real delivery is unobserved.',
    'Map accepted context/remote-view connections to feature entries with sender and lifetime identity.',
    'Close registry populate/unregister and frame predicates for the actual window types.',
    'Associate each published service with consumers; keep provider implementations separate from composition.',
    'Join HTTP request IDs, callbacks, response/stream cleanup to concrete feature callers.',
    'Join URL/auth/workspace/retry orchestration to the retained HTTP consumers and effective receiver.',
    'Join network restrictions and readiness requirements to retained consumers and actual runtime policy.',
    'Join requirements/config startup to actual transports, native permission and relaunch consumers.',
    'Follow requested-mode transition calls to concrete Codex entries; work/chat values do not prove product equivalence.',
    'Identify actual access/provider inputs and persisted-mode consumers.',
    'Identify actual store/factory implementation and storage/reactive behavior; keyed state is not proof of persistence.',
    'Find callers of bpe/window monitor and their cleanup ownership before assigning a feature.',
    'Find the actual permission request caller and notification service chain; T12 preferences do not establish a call to wqe.',
    'Find pFe factory consumers and actual Apple Event dispatch; do not infer a computer-use feature by API name.',
    'Mount/effect/scope and selected branch remain unobserved; conditional T03 consumers are not a runtime receipt.',
    'Known KI consumers are associated below; remaining consumers and actual host selection remain open.',
    'Other N3 producers and ordinary host registration remain unresolved; conditional T03 composition is retained.',
    'RPC framework delivery/reconnect and captured manager identity remain unobserved; conditional T03 composition is retained.',
    'Main jfe/vp/kM source endpoint is conditional on the startup flag; actual selected instance and backend result remain unknown.',
    'Complete the selected project config receiver -> source-context helper -> actual callback/storage chain before assigning feature-level effects.',
    'Associate the two native feature policies and auth invalidation with actual retained consumers; no product-only exclusion follows from auth strings.',
    'Associate published owlFeatures service capabilities and native results with actual callers.',
    'Associate gate evaluation context and capability consumers with user goals; source gate IDs do not identify a product feature.',
    'Join actual asset getter consumers to navigation/page presentation; ua descriptors are not settings workflows.',
    'Join factory selections and loaders to actual routed page/feature consumers; imports do not prove page behavior.',
    'Join visible/pending/error results and injected host/auth/capability context to retained settings task consumers.',
    'Join M6 route parent/redirect/page mounting to the feature entries; source route instances alone do not establish runtime mounting.',
]

def foundation_ref(work_id):
    n, _ = foundation[work_id]
    return ref('implementation-milestones-v9.json', f'/foundationTasks/{n}')


def feature_join(ids, scope, evidence):
    return {'taskId': 'T03', 'task': ref('restoration-coverage-v17.json', '/taskGroups/2'),
            'featureIds': ids,
            'features': [ref('feature-scope-v26.json', '/features/' + str(feature_index[f])) for f in ids],
            'relationship': scope, 'confidence': 'inferred', 'evidence': evidence,
            'actualUiReceiverIdentityProven': False, 'completeChainProven': False,
            'modeAssignmentChanged': False, 'runtimeAcceptanceChanged': False}


joins = {}
selector_features = ['FSC-0035', 'FSC-0036', 'FSC-0046', 'FSC-0047', 'FSC-0048']
joins[SELECTOR] = [feature_join(selector_features, 'source-level KI selector consumer; provider selection remains conditional',
    [ref('thread-fork-entry-contracts.json', '/facts/7'), ref('thread-start-entry-contracts.json', '/facts/4'),
     ref('thread-archive-entry-contracts.json', '/facts'), ref('submission-host-instance.json', '/contracts/27')])]
for id in [MANAGER, REGISTRY, INTERNAL, RESOLVER, LIFECYCLE, idx('PROVIDER', 'host-provided-rpc-adapter')]:
    joins[id] = [feature_join(['FSC-0035'], 'conditional provider/manager support for the existing-local submit consumer; not universal dispatch',
                             [ref('submission-host-instance.json', '/contracts/27'), ref('resume-provider-resolution.json', '/providerBranches')])]

owners = []
assignments = []
for i, r in enumerate(rows):
    owner_id = canonical[r['id']]
    assignments.append({'proposalId': r['id'], 'proposal': module_ref(i), 'ownerId': owner_id,
                        'relationship': 'refines-same-KI-contract' if r['id'] == OLD_SELECTOR else 'owns-bounded-proposed-responsibility',
                        'confidence': 'inferred', 'fullOriginalModuleRecovered': False})
    if r['id'] == OLD_SELECTOR:
        continue
    work_id = primary[i]
    paths = [r['proposedPath']['value']]
    if paths[0].startswith('src/'):
        paths[0] = 'apps/desktop/' + paths[0]
    path_decision = 'Retain the saved path as a new maintenance proposal; this does not recover the original directory.'
    if r['id'] == idx('BOUNDARY', 'STRUCT-RWC-FETCH'):
        paths = ['packages/desktop-http-client/src/desktop-fetch.ts']
        path_decision = 'Move the proposed renderer HTTP facade out of the main directory into an injected client package; the main Ude HTTP orchestration remains AH-M06. Containing-file renderer evidence supports this design; complete runtime placement still needs consumer closure.'
    if r['id'] == PROJECTS:
        paths = ['packages/projects/src/contracts.ts',
                 'apps/desktop/src/renderer/projects/project-client.ts',
                 'apps/desktop/src/main/projects/project-service.ts']
        path_decision = 'Separate shared contract, renderer facade and main qHe service; broad hXe/init/import spans are wiring witnesses and must not be copied into the project domain.'
    if r['id'] == SELECTOR:
        path_decision = 'Use this one host-rpc-selector path for the shared KI contract; the earlier host-selector proposal becomes its evidence/refinement alias.'
    consumer_joins = joins.get(r['id'], [])
    owner = {'ownerId': r['id'], 'memberProposalIds': [id for id, c in canonical.items() if c == r['id']],
             'responsibility': r['responsibility']['value'], 'proposal': module_ref(i),
             'proposedPaths': paths, 'pathDecision': path_decision,
             'primaryFoundationTask': {'taskId': work_id, 'task': foundation_ref(work_id),
                                       'relationship': 'inferred source-design responsibility assignment; integration acceptance remains unchanged'},
             'consumerTaskJoins': consumer_joins,
             'consumerJoinGap': pending[i], 'allConsumersAssigned': False,
             'implementationScope': 'Only the reviewed responsibility/interfaces; enclosing source spans and unreviewed members are not wholesale implementation assignments.',
             'sourceMode': 'unknown', 'disposition': 'retain', 'runtimeValidated': False,
             'clientImplementationGenerated': False}
    if r['id'] == PROJECTS:
        owner['candidateConsumerJoin'] = {
            'featureId': 'FSC-0105', 'taskId': 'T14', 'status': 'pending-source-qualified-delegation-identity',
            'feature': ref('feature-scope-v26.json', '/features/104'),
            'task': ref('restoration-coverage-v17.json', '/taskGroups/13'),
            'basis': [ref('settings-operation-batch-04.json', '/operationContracts/1'),
                      ref('raw/restoration-plan-v7/local-content-01/source-contracts.json', '/imports/2'),
                      ref('raw/restoration-plan-v7/local-content-01/source-contracts.json', '/calls/27'),
                      ref('request-wrapper-contracts.json', '/projectCreateLocal')],
            'known': 'Ut local branch calls Ke(r), and the source-qualified Program import binds Ke to app-initial export j$t. FSC-0105 records the delegated user goal.',
            'missing': 'Join initial j$t to its local declaration and full dialog/accessor/provider chain before equating it with projects.createLocal; remote qe/k$t is a separate branch.',
            'notAddedAsNewFeature': True,
            'relatedRemoteGoal': {'featureId': 'FSC-0045', 'taskId': 'T05', 'feature': ref('feature-scope-v26.json', '/features/44'),
                                   'qualification': 'Known WSL remote create branch; not evidence of local createLocal identity.'}}
    owners.append(owner)

# Every overlap gets a bounded decision. These are code-ownership proposals, not runtime closure.
decisions = []
shared_helper = {0, 1, 15}
assembly_pairs = set(range(4, 15))
for i, o in enumerate(catalog['sourceOverlapReviews']):
    decision = {'id': f'LM-OVERLAP-DECISION-{i+1:02}', 'overlap': ref('logical-module-inventory-v1.json', f'/sourceOverlapReviews/{i}'),
                'left': o['left'], 'right': o['right'], 'sharedRanges': o['sharedRanges'],
                'confidence': 'inferred', 'decisionScope': 'bounded-maintenance-ownership',
                'completeSourcePartitionProven': False, 'runtimeEquivalenceClaimed': False}
    if i in shared_helper:
        decision.update({'kind': 'delegate-shared-helper',
                         'implementationOwner': REGISTRY,
                         'rule': 'The domain registry owns the shared Vfn availability predicate and Sii/loi domain construction contract. The provider lifecycle and request manager use that contract; do not generate separate Vfn/Sii/loi copies.',
                         'preserve': 'Vfn reads e6?.appServerManagers separately from Bfn; its unused argument is not a host-specific or product-mode predicate. Registry construction injects the manager/transport; actual availability and other N3 producers remain unknown.',
                         'evidence': [ref('submission-host-instance.json', '/contracts/4'), ref('submission-host-instance.json', '/contracts/10'), ref('submission-host-instance.json', '/contracts/11')]})
    elif i == 2:
        decision.update({'kind': 'unify-same-contract-proposals', 'implementationOwner': SELECTOR,
                         'rule': 'Both proposals cite the exact same complete KI function range. Keep one host selector implementation responsibility; retain the older proposal as source evidence and refinement history.',
                         'preserve': 'Primary forHost guards, caught primary error, connected/cache/deferred fallbacks, duplicates and retirement remain distinct paths.',
                         'evidence': [ref('submission-host-instance.json', f'/contracts/{n}') for n in [5, 6, 7, 8]]})
    elif i == 3:
        decision.update({'kind': 'adapter-uses-resolver', 'implementationOwner': RESOLVER,
                         'rule': 'X2t resolver/forwarding behavior belongs to the request-resolver responsibility. Internal yMc/vMc owns acquisition, MessageChannel and RPC client/server lifetime, and imports/uses the facade. The enclosing X2t initializer is not a second implementation to copy.',
                         'preserve': 'Only reviewed facade members are assigned here; other class members and complete helper ownership remain open. RPC framework implementation is an external boundary.',
                         'evidence': [ref('submission-host-instance.json', f'/contracts/{n}') for n in [15, 16, 17, 18, 19, 20]]})
    elif i in assembly_pairs:
        rule = 'The broad hXe/createAppHost/constructor/import ranges are composition or dependency witnesses, not whole implementations owned by every service. AH-M04 owns service assembly; hosted-file/project/native-feature providers own their respective reviewed behavior; AH-M02 owns connection acceptance.'
        if i == 10:
            rule += ' Authentication-reset policy belongs to RF-1; app-state subscription wiring remains composition/lifecycle code, not project state behavior.'
        if i in [11, 12]:
            rule += ' The broad initial ImportDeclaration is an import-link witness; do not move all imported code or unrelated names into the project module.'
        decision.update({'kind': 'composition-or-import-witness',
                         'implementationOwnersByResponsibility': {'serviceAssembly': ASSEMBLY, 'connectionEntry': CONNECTION,
                                                                  'hostedFiles': HOSTED, 'projectDomain': PROJECTS,
                                                                  'nativeFeaturePolicy': POLICY, 'nativeFeatureProvider': PROVIDER,
                                                                  'rendererFeatureGates': GATES},
                         'rule': rule,
                         'preserve': 'Keep injected provider callbacks, request/signal/progress, constructor ordering and disposal hooks. Do not infer one module from a common containing class or import statement.',
                         'evidence': [ref('request-wrapper-contracts.json', '/contracts/4'), ref('request-wrapper-contracts.json', '/contracts/7'),
                                      ref('app-host-maintenance.json', '/modules/3'), ref('runtime-feature-policy-contracts.json', '/facts/8')]})
    else:
        assert i in [16, 17, 18]
        decision.update({'kind': 'separate-policy-provider-and-renderer',
                         'implementationOwnersByResponsibility': {'allowlistCacheOwnerGeneration': POLICY,
                                                                  'uzeServiceAndUnsupportedErrorProjection': PROVIDER,
                                                                  'rendererEvaluationAndDispatch': GATES,
                                                                  'appHostConstructionAndAuthSubscriptions': ASSEMBLY},
                         'rule': 'RF-1 owns allowlisted merge/cache/reset and owner/generation policy; RF-2 owns the uze service interface and specified unsupported-error projection; RF-3 owns bZs/xZs renderer evaluation/dispatch. Main/provider/renderer supporting spans remain cross-boundary evidence, not source to copy to every file.',
                         'preserve': 'Keep setter/reset error ordering, principal/account predicates, two exact runtime keys, readiness/evaluation guards and error propagation. Native effects and intermediate RPC delivery remain unverified.',
                         'evidence': [ref('runtime-feature-policy-contracts.json', f'/facts/{n}') for n in range(9)]})
    decisions.append(decision)

state_path = OUT / 'analysis-state.json'
before = state_path.read_bytes()
assert not (WORK / 'state-before.json').exists()
(WORK / 'state-before.json').write_bytes(before)
state = json.loads(before)
assert state['logicalModuleInventory']['catalog']['sha256'] == PINS['logical-module-inventory-v1.json']['sha256']
document = {'schemaVersion': 1, 'baselineId': BASE, 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
            'status': 'bounded-ownership-design-and-task-association; full analysis incomplete',
            'catalog': PINS['logical-module-inventory-v1.json'],
            'assignmentInterpretation': '38 saved proposal records form 37 provisional responsibility owners after one KI-contract unification. Responsibility owners are not original source modules, independently recovered files, implemented tasks or a whole-client denominator.',
            'proposalAssignments': assignments, 'responsibilityOwners': owners, 'overlapDecisions': decisions,
            'currentTaskScope': {'coverage': PINS['restoration-coverage-v17.json'], 'ordering': PINS['restoration-current-ordering-v1.json'],
                                 'foundationDescription': PINS['implementation-milestones-v9.json'],
                                 'qualification': 'Foundation descriptions W01-W09 are reused from the historical plan. Current ordering/coverage have 48 feature tasks; historical W09/45-task entries are not adopted as current task counts.'},
            'sourceRangePolicy': 'Inherited ranges are evidence locators. Unless a reviewed contract assigns that specific behavior, an enclosing class, initializer, import or assembly range is not permission to duplicate or label all enclosed implementation first-party.',
            'counts': {'inputProposalRecords': 38, 'responsibilityOwners': 37, 'unifiedSameContractPairs': 1,
                       'overlapsWithBoundedDecision': 19, 'overlapDecisionKinds': dict(Counter(d['kind'] for d in decisions)),
                       'proposalsAssociatedToFoundationWork': 38, 'ownersWithConditionalFeatureTaskJoins': len(joins),
                       'candidateProjectConsumerJoins': 1, 'currentFeaturesUnchanged': 373, 'currentFeatureTasksUnchanged': 48,
                       'newFeatures': 0, 'newScenarioSpecifications': 0, 'newSourceParses': 0, 'newReaRuns': 0,
                       'newModelSubmissions': 0, 'newClientRuns': 0, 'newProductAcceptancePasses': 0, 'newClientImplementation': 0},
            'limitations': ['All ownership and file assignments are inferred maintenance design. Complete source partitions/import/export/consumer closure remain open.',
                            'Feature task joins are bounded source/conditional support relationships and do not prove selected runtime receiver or protocol equivalence.',
                            'A pending association with existing FSC-0105 prevents treating the known createLocal chain as a new distinct user feature without source-qualified comparison.',
                            'Third-party implementation, native ABI, private runtime route, full product denominator and original nine completion criteria are not changed.',
                            'No original source file is read, parsed or executed by this producer; no application/model/account/state mutation outside analysis artifacts occurs.'],
            'nextAction': {'issueId': 'SD-01',
                           'question': 'Join the existing FSC-0105 local Add project delegate Ke -> initial j$t to the already reviewed projects.createLocal chain, or preserve a specific non-equivalence.',
                           'fixedInput': 'Saved local-content Program import/call metadata and existing initial/dialog/project accessor contracts. Reuse original identities; do not create a new feature or equate WSL remote creation by label.',
                           'closure': 'An exact import/export/local binding and delegate contract establishes the local target, its request/result/cleanup and relationship to FSC-0105; any unavailable edge remains explicitly pending.',
                           'authorization': 'Read-only frozen-source/saved-artifact analysis and owned pure fixtures as needed; no application/model/service invocation.'},
            'fullAnalysisCompleted': False, 'implementationReady': False, 'inputPins': list(PINS.values())}


def publish(name, obj):
    path = OUT / name
    assert not path.exists()
    text = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, indent=2) + '\n'
    path.write_text(text)
    path.chmod(0o444)
    b = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(b), 'sha256': digest(b)}


doc_pin = publish('logical-module-ownership-v1.json', document)
md = ['# 模块职责归属与任务关联 v1', '',
      '38 条既有建议已关联到现有基础恢复工作 W03–W07，并整理为 37 组暂定职责：两份 KI host 选择器建议统一为一个实现责任。这里统计的是维护职责，不是已恢复源码模块数。', '',
      '19 组来源重叠均已有有限设计处置：3 组共享 helper 委托、1 组合并同一 KI 合同、1 组 resolver/调用适配器分工、11 组组装或 import 证据分离、3 组运行时 policy/provider/renderer 分工。完整源码分区与运行效果仍未证明。', '',
      '具体工程决定：renderer 的 AW/TFt HTTP facade 改放 `packages/desktop-http-client/src/desktop-fetch.ts`；main 的 Ude HTTP 编排保持独立。项目领域按 shared contract、renderer client、main service 分成三个拟议文件。App-host 旧 `src/` 建议统一到 `apps/desktop/src/`。所有路径均为新维护设计。', '',
      'KI 及相关 provider/manager 职责已条件关联 T03 的已知用户链路。其余职责已明确基础工作归属，并逐项记录所缺的功能消费者证据；没有按名称或同文件批量指定功能。', '',
      '项目关联核对发现：FSC-0105/T14 已记录“从环境页面添加项目”，本地分支 Ke 的导入绑定到 initial 的 j$t，但到既有 createLocal dialog/service 的目标身份尚待核对。FSC-0045/T05 是 WSL 远程创建；本轮没有新增或合并功能。', '',
      '| 职责 owner | 基础工作 | 拟议文件 |', '| --- | --- | --- |']
for o in owners:
    md.append('| ' + o['ownerId'] + ' | ' + o['primaryFoundationTask']['taskId'] + ' | ' + '<br>'.join('`' + p + '`' for p in o['proposedPaths']) + ' |')
md += ['', '373 项功能、48 组功能任务、1216 条未执行场景规格及原九项完成标准保持原状态。未运行原客户端、调用模型或生成客户端/第三方实现。下一项是补齐 FSC-0105 本地委托与 createLocal 的准确来源关系。', '']
summary_pin = publish('logical-module-ownership-v1.md', '\n'.join(md))
journal = []
for d in decisions:
    journal.append({'id': d['id'], 'baselineId': BASE, 'claim': d['rule'],
                    'sourcePath': d['overlap']['path'], 'sourceHash': d['overlap']['sha256'],
                    'locator': {'kind': 'json-pointer', 'jsonPointer': d['overlap']['jsonPointer']},
                    'method': 'existing-artifact source-coordinate and responsibility reconciliation; maintenance inference',
                    'confidence': 'inferred', 'verificationStatus': 'bounded-design-decision; complete-source-partition-and-runtime-unverified'})
for i, a in enumerate(assignments):
    journal.append({'id': f'LM-TASK-ASSIGNMENT-{i+1:02}', 'baselineId': BASE,
                    'claim': f"{a['proposalId']} uses responsibility owner {a['ownerId']}; foundation work is an inferred design assignment, with feature consumer limits retained.",
                    'sourcePath': a['proposal']['path'], 'sourceHash': a['proposal']['sha256'],
                    'locator': {'kind': 'json-pointer', 'jsonPointer': a['proposal']['jsonPointer']},
                    'method': 'existing-artifact task responsibility inference', 'confidence': 'inferred',
                    'verificationStatus': 'maintenance-task-association; not implementation-or-product-acceptance'})
evidence_pin = publish('logical-module-ownership-v1-evidence.jsonl', ''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in journal))
state['logicalModuleInventory']['ownershipReview'] = {'decisions': doc_pin, 'summary': summary_pin,
                                                     'evidence': evidence_pin, 'counts': document['counts'],
                                                     'qualification': document['assignmentInterpretation']}
state['stageDecisions']['nextAction'] = document['nextAction']
state['updatedAtUtc'] = datetime.now(timezone.utc).isoformat()
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
for name in ['report.md', 'gaps.md']:
    path = OUT / name
    old = path.read_bytes()
    (WORK / ('before-' + name)).write_bytes(old)
    prefix = ('当前模块职责见[归属与任务关联](logical-module-ownership-v1.md)：38条建议形成37组暂定职责，19组来源重叠已有有限设计处置；'
              '基础工作归属已明确，完整消费者与源码分区仍待证。FSC-0105已记录环境页添加项目，下一项核对其Ke/j$t到createLocal的委托关系；'
              '373项/48任务及九项完成标准不变，完整分析未完成。下文早期下一行动保留为历史记录。\n\n')
    path.write_bytes(prefix.encode() + old)
publication = {'decisions': doc_pin, 'summary': summary_pin, 'evidence': evidence_pin,
               'producer': {'path': str(Path(__file__).relative_to(ROOT)), 'sha256': digest(Path(__file__).read_bytes()), 'bytes': Path(__file__).stat().st_size}}
(WORK / 'publication.json').write_text(json.dumps(publication, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'published': doc_pin, 'counts': document['counts']}, ensure_ascii=False))
