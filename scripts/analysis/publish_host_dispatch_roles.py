"""Integrate a complete saved host-switch role review without claiming feature completion."""
import copy
import csv
import hashlib
import io
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/host-dispatch-roles-work'
PINS = {}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pin(p):
    b = p.read_bytes()
    v = {'path': str(p.relative_to(OUT)), 'bytes': len(b), 'sha256': sha(b)} if p.is_relative_to(OUT) else {'path': str(p.relative_to(ROOT)), 'pathBase': 'workspace', 'bytes': len(b), 'sha256': sha(b)}
    PINS[str(p)] = v
    return v


def load(p):
    pin(p)
    return json.loads(p.read_text())


def ref(p, ptr):
    v = load(p)
    for token in ptr.strip('/').split('/') if ptr else []:
        v = v[int(token)] if isinstance(v, list) else v[token]
    return {**pin(p), 'jsonPointer': ptr}


def write(p, value):
    b = value if isinstance(value, bytes) else (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write(b)
    p.chmod(0o444)
    return pin(p)


state_path = OUT / 'analysis-state.json'
before = state_path.read_bytes()
with (WORK / 'state-before.json').open('xb') as f:
    f.write(before)
state = json.loads(before)
assert state['featureScopeCurrentView']['snapshotVersion'] == 26
assert state['latestBehaviorAuthorizationState']['groupRemaining'] == 0
assert state['fullAnalysisCompleted'] is False
scope = load(OUT / 'feature-scope-v26.json')
coverage = load(OUT / 'restoration-coverage-v17.json')
old_legacy = load(OUT / 'legacy-entry-dispositions.json')
families = load(OUT / 'entry-family-map.json')
host = load(OUT / 'host-message-contracts.json')
query = load(WORK / 'class-roles.json')
project = load(OUT / 'project-local-delegation-v1.json')
pin(ROOT / 'scripts/analysis/analyze_host_dispatch_roles.mjs')
pin(Path(__file__))
assert query['counts']['legacyRecordsReviewed'] == 143
assert query['prelude']['condition'] == 'gR(t)'
assert query['targetCodeExecuted'] is False
assert [x['entryId'] for x in families['entries']] == [x['entryId'] for x in old_legacy['entries']]
raw_pin = write(OUT / 'raw/host-dispatch-roles-v1/class-roles.json', (WORK / 'class-roles.json').read_bytes())
class_pin = write(OUT / 'raw/host-dispatch-roles-v1/source-class.txt', (WORK / 'source-class.txt').read_bytes())
family_index = {x['entryId']: i for i, x in enumerate(families['entries'])}
row_index = {x['entryId']: i for i, x in enumerate(query['rows'])}
case_feature = next(x for x in query['rows'] if x['caseIndex'] == 119)
assert case_feature['label'] == 'electron-add-new-workspace-root-option'
project_source = next(x for x in project['selectedSource'] if x['id'] == 'add-root-handler-case')
assert case_feature['byteRange'] == project_source['byteRange']
assert case_feature['spanHash'] == project_source['spanHash']

review = {
    'schemaVersion': 1, 'baselineId': BASE, 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
    'scope': 'All 143 labels in the selected MMe.handleMessage switch, conditional on the prelude not routing elsewhere.',
    'sourceQuery': raw_pin, 'completeSelectedClass': class_pin,
    'prelude': query['prelude'], 'records': query['rows'],
    'counts': query['counts'],
    'retentionDecision': 'Preserve the prelude, literal labels, effective body groups and explicit unsupported-error behavior. Delegate domain operations to retained services; do not implement every label as an independent feature or omit no-op labels globally.',
    'featureAssociations': [{'entryId': case_feature['entryId'], 'featureId': 'FSC-0105', 'taskId': 'T14',
                             'status': 'conditional-source-handler-association',
                             'basis': ref(OUT / 'project-local-delegation-v1.json', '/facts/2'),
                             'completeEntryEquivalenceProven': False}],
    'limitations': ['The gR prelude may handle a message before this switch; no-op and unsupported classifications apply only to selected switch consequents.',
                    'Sender/receiver delivery, concrete services, mode/shared closure and runtime effects remain unverified.',
                    '143 source-role decisions establish no new user features and close no full functional-entry mapping.'],
    'newModelSubmissions': 0, 'newClientRuns': 0, 'newReaRuns': 0,
    'newProductScenarioPasses': 0, 'newClientImplementation': 0,
    'inputPins': list(PINS.values()), 'fullAnalysisCompleted': False,
}
review_pin = write(OUT / 'host-dispatch-roles-v1.json', review)
evidence = []
for row in query['rows']:
    evidence.append({'id': 'HOST-ROLE-' + str(row['caseIndex']).zfill(3), 'baselineId': BASE,
                     'claim': f"{row['label']}: {row['effect']}, effective case {row['effectiveCaseIndex']}; classification applies after the gR(t) prelude is bypassed.",
                     'sourcePath': row['sourcePath'], 'sourceHash': row['sourceHash'],
                     'locator': {'byteRange': row['byteRange'], 'spanHash': row['spanHash'], 'nodeType': row['nodeType'], 'effectiveCase': row['effectiveCase']},
                     'method': 'complete-frozen-class-AST; exact-saved-case-and-legacy-span-join',
                     'confidence': 'confirmed', 'verificationStatus': 'selected-source-role-confirmed; global-feature-role-and-runtime-unverified'})
evidence_pin = write(OUT / 'host-dispatch-roles-v1-evidence.jsonl', ''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in evidence).encode())

legacy = copy.deepcopy(old_legacy)
legacy['recordedAtUtc'] = review['recordedAtUtc']
legacy['previousSnapshot'] = pin(OUT / 'legacy-entry-dispositions.json')
legacy['hostDispatchRoleReview'] = review_pin
for row in legacy['entries']:
    if row['entryId'] not in row_index:
        continue
    n = row_index[row['entryId']]
    role = query['rows'][n]
    assert row['disposition'] == 'awaiting-disposition'
    source = families['entries'][family_index[row['entryId']]]['sourceCoordinates']
    assert all(source[k] == role[k] for k in ['sourcePath', 'sourceHash', 'byteRange', 'spanHash'])
    row.update(disposition='partial-host-dispatch-role', sourceRoleConfirmed=True,
               sourceRole=role['effect'], roleEvidenceRef={**review_pin, 'jsonPointer': '/records/' + str(n)},
               effectiveHandlerCaseIndex=role['effectiveCaseIndex'],
               sourceRoleQualification='Selected switch only, conditional on gR(t) being false; not a global user-operation role.',
               retentionDecision=review['retentionDecision'],
               remainingWork='Identify concrete senders, services and retained user consumers; establish mode/shared and actual effect separately.')
    if row['entryId'] == case_feature['entryId']:
        row['featureIds'] = ['FSC-0105']
        row['featureAssociation'] = review['featureAssociations'][0]
container = next(x for x in legacy['entries'] if x['entryId'] == 'ROUTE-0152')
container['featureIds'] = scope['legacyEntryCoverage']['mappingUpdates'][0]['featureIds']
container['currentScopeContainerRef'] = ref(OUT / 'feature-scope-v26.json', '/legacyEntryCoverage/mappingUpdates/0')
counts = Counter(x['disposition'] for x in legacy['entries'])
legacy['counts'].update(entriesAwaitingDisposition=counts['awaiting-disposition'], partialHostDispatchRoles=143,
                        selectedSwitchNoOpLabels=33, selectedSwitchUnsupportedLabels=6, selectedSwitchHandlerLabels=104,
                        entriesWithoutFeatureMapping=sum(not x['featureIds'] for x in legacy['entries']),
                        conditionalHostHandlerFeatureAssociations=1, dispositionCounts=dict(counts),
                        selectedClassParsesAdded=1, newFullProgramParses=0)
assert legacy['counts']['entriesAwaitingDisposition'] == 583
assert legacy['counts']['entriesWithoutFeatureMapping'] == 966
legacy['accountingPolicy'].update(
    featureMapping='966 entries still have no feature association; the container and one host handler have partial conditional mappings. None is fully resolved.',
    partialMappings='One conditional settings container maps 367 current definitions; one host handler conditionally supports FSC-0105; six registrations have known callees but no feature identity.',
    unknown='583 entries still await source-role disposition; 143 host labels have selected-switch roles but retain global consumer/effect gaps.',
    hostSwitch='33 no-op and 6 explicit unsupported labels are conditional on bypassing the prelude. They are not ChatGPT exclusions or absent user features.')
legacy['frozenSourceValidation']['hostDispatchSupplement'] = {'sourceQuery': raw_pin, 'sourceClass': query['sourceClass'], 'caseSpansChecked': 143}
legacy_pin = write(OUT / 'legacy-entry-dispositions-v2.json', legacy)
buf = io.StringIO(); columns = ['entryId', 'entryKind', 'family', 'label', 'disposition', 'sourceRoleConfirmed', 'productMode', 'functionalEntryFullyResolved']
writer = csv.DictWriter(buf, fieldnames=columns, extrasaction='ignore'); writer.writeheader(); writer.writerows(legacy['entries'])
legacy_csv_pin = write(OUT / 'legacy-entry-dispositions-v2.csv', buf.getvalue().encode())

scope['previousScopeRef'] = pin(OUT / 'feature-scope-v26.json')
scope['legacyEntryDispositions'] = legacy_pin
scope['hostDispatchRoleReview'] = review_pin
scope['legacyEntryCoverage'].update(unmappedEntryCount=966, dispositionRef=legacy_pin, dispositionCounts=dict(counts),
    qualification='367 definitions have conditional container associations; one host handler additionally associates FSC-0105. All 968 entries remain functionally unresolved; source roles are a separate axis.')
scope['legacyEntryCoverage']['mappingUpdates'].append({'entryId': case_feature['entryId'], 'status': 'conditional-handler-association', 'featureIds': ['FSC-0105'], 'source': review_pin, 'completeEntryEquivalenceProven': False})
scope['counts'].update(legacyEntriesAwaitingDisposition=583, legacyEntriesUnmappedInThisLedger=966,
                       legacyEntriesWithReviewedDispatchRole=143, partiallyMappedLegacyHandlers=1)
feature = scope['features'][104]
feature['sourceRefs'].extend([pin(OUT / 'project-local-delegation-v1.json'), review_pin])
feature['localDelegationRefinement'] = {'source': pin(OUT / 'project-local-delegation-v1.json'), 'handlerEntryId': case_feature['entryId'], 'status': 'conditional-static-picker-chain; actual-delivery-unobserved'}
feature['chain'] = 'Local Ke(scope) imports j$t/z0r, records a local flow and emits the add-root desktop message. The matching MMe handler conditionally calls the Mje folder picker/createOrSelectLocalProjects chain. This is distinct from the createLocal dialog. Remote qe/k$t requests its remote modal.'
feature['knownGaps'] = [x if x != 'Project registration flow and cross-entry equivalence' else 'Actual bridge delivery/injected manager/backend, durable registration and other project-entry relationships remain unverified; picker vs createLocal distinction is established.' for x in feature['knownGaps']]
relation = next(x for x in scope['legacyFeatureRelations'] if x['featureId'] == 'FSC-0105')
relation['entryIds'].append(case_feature['entryId']); relation['status'] = 'conditional-container-and-handler-association'; relation['handlerRoleRef'] = review_pin
scope_pin = write(OUT / 'feature-scope-v27.json', scope)
scope_csv_pin = write(OUT / 'feature-scope-v27.csv', (OUT / 'feature-scope-v26.csv').read_bytes())
coverage['previousSnapshot'] = pin(OUT / 'restoration-coverage-v17.json')
coverage['recordedAtUtc'] = review['recordedAtUtc']; coverage['featureLedger'] = scope_pin
coverage['legacyEntryDispositions'] = legacy_pin; coverage['hostDispatchRoleReview'] = review_pin
for i, row in enumerate(coverage['features']):
    assert row['featureId'] == scope['features'][i]['featureId']
    row['featureRef'] = {**scope_pin, 'jsonPointer': '/features/' + str(i)}
    if row['featureId'] == 'FSC-0105':
        row['knownGaps'] = feature['knownGaps']; row['evidence'].extend([pin(OUT / 'project-local-delegation-v1.json'), review_pin])
coverage['taskGroups'][13]['evidence'].extend([pin(OUT / 'project-local-delegation-v1.json'), review_pin])
coverage['taskGroups'][13]['sourceReceiverGaps'] = [x if x != 'Project registration flow and cross-entry equivalence' else feature['knownGaps'][2] for x in coverage['taskGroups'][13]['sourceReceiverGaps']]
for family in coverage['unresolvedScope']['legacyFamilies']:
    family['entryDispositionCounts'] = dict(Counter(x['disposition'] for x in legacy['entries'] if x['family'] == family['family']))
coverage_pin = write(OUT / 'restoration-coverage-v18.json', coverage)

summary = '''# 主进程分发入口角色处置

143 条旧记录已按精确源码范围逐条接上选定 `MMe.handleMessage` 的 switch：104 个标签进入处理体、33 个在该 switch 中为空操作、6 个显式抛出“不支持 Electron”错误。31 个空标签的后继归属均已核对，不能把空标签等同于空操作。

方法在进入 switch 前先判断 `gR(t)`，可交给 overlay manager 并提前返回。因此上述空操作和错误仅描述选定 switch 的分支，不能据此排除全局功能或判定为 ChatGPT 专用。恢复时须保留该前置分流、标签组和错误语义。

其中添加根目录的 handler 已条件关联现有 FSC-0105/T14，依据是已核对的 Ke/j$t 消息和文件夹选择器链。真实送达、有效实例、模式与持久化仍未验证。没有按消息标签自动新增功能。

旧入口中 583 条尚待源码角色处置，143 条本批记录仍保留功能消费者缺口。两条入口有部分功能关联，966 条暂无功能关联；完整解决数仍为 0。源角色明确不等于功能复刻完成。

当前[功能台账 v27](feature-scope-v27.json)与[恢复覆盖表 v18](restoration-coverage-v18.json)保持 373 项功能、48 组任务和 1216 条未执行规格；[旧入口处置 v2](legacy-entry-dispositions-v2.json)保留全部 968 个 ID。仅解析一个完整原始 class，未执行其代码、调用模型或启动客户端。

明细：[角色与维护决定](host-dispatch-roles-v1.json)、[九字段证据](host-dispatch-roles-v1-evidence.jsonl)。下一批处理原生菜单，区分菜单结构、系统 role 与实际回调消费者。
'''
summary_pin = write(OUT / 'host-dispatch-roles-v1.md', summary.encode())
state['legacyEntryDispositions'].update(result=legacy_pin, csv=legacy_csv_pin, summary=summary_pin, counts=legacy['counts'])
state['featureScopeCurrentView'].update(snapshotVersion=27, ledger=scope_pin, csv=scope_csv_pin,
    previousLedger=pin(OUT / 'feature-scope-v26.json'), counts=scope['counts'], legacyEntryDispositionOverlay=legacy_pin,
    hostDispatchRoleOverlay=review_pin, reconciliationArtifact=review_pin,
    reconciliationKind='source-role-and-conditional-host-handler-association')
state['restorationCoverageCurrentOverlay'] = {'coverage': coverage_pin, 'qualification': '373 feature IDs, 48 task groups and 1216 specifications unchanged; source-role accounting and the existing T14 project consumer evidence updated. Ordering v1 remains valid for these same feature/task identities.'}
overlay = {'contracts': review_pin, 'summary': summary_pin, 'evidence': evidence_pin,
           'sourceRoleCounts': query['counts'], 'legacyCounts': legacy['counts'], 'fullAnalysisCompleted': False}
state['hostDispatchRoles'] = overlay
state['stageDecisions']['hostDispatchRoleOverlay'] = overlay
state['stageDecisions']['nextAction'] = {'issueId': 'SD-01',
    'question': 'Disposition the saved native-menu family: separate menu structure, standard roles and custom action callbacks, then join retained consumers with exact source evidence.',
    'fixedInput': '189 saved native-menu records, complete menu source contracts and entry-family Program-scope metadata; preserve original IDs and prior consumer joins.',
    'closure': 'Each reviewed menu record has a source-qualified role and specific consumer/effect gaps; labels alone never create features or exclusions.',
    'authorization': 'Frozen-source and saved-artifact analysis only; no app/model/service invocation.'}
state['updatedAtUtc'] = datetime.now(timezone.utc).isoformat()
assert state['latestBehaviorAuthorizationState'] == json.loads(before)['latestBehaviorAuthorizationState']
assert state['fullAnalysisCompleted'] is False
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
for name in ['report.md', 'gaps.md']:
    p = OUT / name; text = p.read_text(); first, sep, rest = text.partition('\n\n')
    (WORK / (name + '.before')).write_text(text)
    first = '当前入口处置见[主进程分发角色](host-dispatch-roles-v1.md)：143个标签已明确选定switch中的角色，须保留gR前置分流；583条旧入口仍待角色处置，完整功能入口解决数仍为0。功能台账v27／恢复覆盖v18保持373项、48任务和1216条未执行规格；下一批为原生菜单，完整分析未完成。'
    p.write_text(first + sep + rest)
print(json.dumps({'review': review_pin, 'scope': scope_pin, 'coverage': coverage_pin, 'legacyCounts': legacy['counts']}, ensure_ascii=False))
