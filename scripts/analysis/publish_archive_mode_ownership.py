"""Publish a positive shared-feature decision without changing feature scope."""
import copy
import csv
import datetime
import hashlib
import io
import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASELINE
WORK = ROOT / '.analysis-local/mode-ownership-reconciliation-work'
RAW = OUT / 'raw/mode-ownership-reconciliation'


def read(path):
    return json.loads(path.read_text())


def dump(path, value):
    assert not path.exists(), path
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path, pointer=None):
    result = {'path': str(path.relative_to(OUT)), 'bytes': path.stat().st_size,
              'sha256': digest(path)}
    if pointer is not None:
        result['jsonPointer'] = pointer
    return result


state = read(OUT / 'analysis-state.json')
assert state['updatedAtUtc'] == '2026-10-24T12:48:30.377627+00:00'
assert state['featureScopeCurrentView']['snapshotVersion'] == 21
old_state = copy.deepcopy(state)
old_scope = read(OUT / 'feature-scope-v21.json')
old_coverage = read(OUT / 'restoration-coverage-v12.json')
assert old_scope['counts']['modeCounts'] == {'unknown': 340, 'codex': 0, 'chatgpt': 0, 'shared': 0}
assert read(WORK / 'replay-receipt.json')['exitCode'] == 0
observation = read(WORK / 'isolated-observations.json')
assert observation['counts'] == {'passed': 10, 'failed': 0}
assert not RAW.exists()
assert not (OUT / 'feature-scope-v22.json').exists()
# Published inputs remain immutable; the final readback rechecks these hashes.
input_hashes = {filename: digest(OUT / filename) for filename in [
    'settings-operation-batch-11.json', 'feature-scope-v21.json',
    'feature-scope-v21-scenarios.json', 'restoration-coverage-v12.json',
    'implementation-plan-v8.md']}
dump(WORK / 'state-before.json', state)
shutil.copytree(WORK / 'archive-provider', RAW / 'archive-provider')
for filename in ['isolated-observations.json', 'failed-attempt-01.json',
                 'selector-receipt.json', 'replay-receipt.json',
                 'selector-stdout.txt', 'selector-stderr.txt',
                 'replay-stdout.txt', 'replay-stderr.txt']:
    shutil.copyfile(WORK / filename, RAW / filename)

provider_file = RAW / 'archive-provider/source-contracts.json'
provider = read(provider_file)
caller_file = OUT / 'raw/settings-operation-batch-11/archived-chats/source-contracts.json'
caller = read(caller_file)
assert {item['exported']: item['local'] for item in provider['exports']} == {
    'ZB': 'O4o', 'd5t': 'iPr', 's5t': 'xPr', 'y5t': 'SPr'}
imports = {specifier['local']: (item['module'], specifier['imported'])
           for item in caller['imports'] for specifier in item['specifiers']}
for local, exported in [('Ct', 'ZB'), ('Tt', 'd5t'), ('Gt', 's5t'), ('Zt', 'y5t')]:
    assert imports[local] == ('./app-initial-6350d04672d0.js', exported)

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
contract_path = OUT / 'archive-mode-ownership.json'
summary_path = OUT / 'archive-mode-ownership.md'


def unit_ref(file, index):
    return pin(file, f'/units/{index}')


facts = [
    ('AMO-01', 'hn requests local archived thread/list and combines its result with cloud task and account conversation queries before rendering wn.',
     [unit_ref(caller_file, 0), unit_ref(caller_file, 4), unit_ref(caller_file, 11)]),
    ('AMO-02', 'The exact import/export join Ct→initial.ZB→O4o projects account conversations, cloud tasks and local threads into one archive collection while retaining original task/thread objects and host identity.',
     [unit_ref(caller_file, 0), unit_ref(provider_file, 0)]),
    ('AMO-03', 'The exact Tt→initial.d5t→iPr join excludes conversation_origin=tpp when includeWorkCloud is false and removes that exclusion when true. Account-conversation storage is not automatically a Chat-only boundary.',
     [unit_ref(caller_file, 0), unit_ref(provider_file, 1)]),
    ('AMO-04', 'un distinguishes recover-cloud-task from unarchive-chatgpt-conversation using the archived field. SPr patches is_archived:false by captured ID and refreshes account collections; xPr also retires a work-companion association. These adapters cannot be deleted solely by their names.',
     [unit_ref(caller_file, 31), unit_ref(provider_file, 2), unit_ref(provider_file, 3)]),
]
decisions = [{
    'featureId': 'FSC-0280', 'priorMode': 'unknown', 'mode': 'shared',
    'method': 'static-code', 'confidence': 'confirmed',
    'verificationStatus': 'static-confirmed', 'confirmedExclusion': False,
    'reason': 'One registered user operation consumes both Codex app-server archive rows and account conversation rows, preserving source identity and using the same browse/search/filter/sort UI. This is positive shared-consumer evidence, rather than a name or access-family classification.',
    'evidenceIds': ['AMO-01', 'AMO-02', 'AMO-03'],
    'retentionDecision': 'Retain the shared archive collection/UI and separate local, cloud-task and account-conversation adapters. Filter sources only after individual mode dependencies are proven.',
    'qualification': 'Static feature ownership only. Actual mode/account/host/gate combinations and service/UI behavior remain unverified; this decision does not classify whole modules or individual destructive operations.'
}]
deferred = [
    {'featureId': 'FSC-0281', 'mode': 'unknown', 'reason': 'The selected operation targets local app-server archives; its full product-mode caller set is not established by that backend identity.'},
    {'featureId': 'FSC-0282', 'mode': 'unknown', 'reason': 'The explicit cloud-task recovery branch is known, but its product-mode consumers need a separate connection.'},
    {'featureId': 'FSC-0283', 'mode': 'unknown', 'reason': 'The origin-neutral account unarchive adapter can receive records from the mixed collection. A Chat-only exclusion is unsupported; per-origin product consumers remain unresolved.'},
    {'featureId': 'FSC-0284', 'mode': 'unknown', 'reason': 'The selected account delete adapter also retires work-companion state. Its complete positive caller and data-origin set remains unresolved.'},
]
contract = {
    'schemaVersion': 1, 'baselineId': BASELINE, 'recordedAtUtc': now,
    'scope': 'Existing archive feature ownership and four provider joins; no new features or product scenarios.',
    'inputPins': [pin(OUT / filename) for filename in input_hashes],
    'sourceContract': pin(provider_file), 'reusedCallerContract': pin(caller_file),
    'facts': [{'id': identifier, 'baselineId': BASELINE, 'claim': claim,
               'method': 'static-code', 'confidence': 'confirmed',
               'verificationStatus': 'static-confirmed', 'sourceRefs': references}
              for identifier, claim, references in facts],
    'modeDecisions': decisions, 'deferredModeDecisions': deferred,
    'isolatedObservation': pin(RAW / 'isolated-observations.json'),
    'failedHarnessAttempt': pin(RAW / 'failed-attempt-01.json'),
    'restorationDecision': decisions[0]['retentionDecision'],
    'limits': ['Account access families, home chat/work, product experience, executor location and backend identity remain distinct dimensions.',
               'The imported title/path formatting, HTTP/query/state adapters and real account data were not executed.',
               'Provider bindings and selected helper contracts are closed only for these saved ranges; complete services and runtime assembly remain open.'],
    'counts': {'featureModesChanged': 1, 'featuresAdded': 0, 'confirmedChatGptExclusionsAdded': 0,
               'newFullProgramParses': 1, 'newProviderUnits': 4, 'helperSourceRangesFromQualifiedBindings': 2,
               'qualifiedProviderJoins': 4, 'isolatedCasesPassed': 10,
               'productScenarioPassesAdded': 0, 'modelSubmissionsAdded': 0,
               'realServiceCalls': 0, 'originalClientRunsAdded': 0},
    'fullAnalysisCompleted': False, 'clientImplementationStarted': False}
dump(contract_path, contract)

scope = copy.deepcopy(old_scope)
scope['purpose'] = 'Current finite feature ledger, with positive shared archive ownership reconciled against frozen source.'
scope['previousScopeRef'] = pin(OUT / 'feature-scope-v21.json')
scope['inheritedLedgerRef'] = pin(OUT / 'feature-scope-v21.json')
scope['inheritedScenarioRef'] = pin(OUT / 'feature-scope-v21-scenarios.json')
scope['newDefinitionIds'] = []
scope['modeOwnershipReconciliation'] = pin(contract_path)
feature = next(item for item in scope['features'] if item['featureId'] == 'FSC-0280')
feature['mode'] = 'shared'
feature['modeEvidence'] = {**decisions[0], 'decisionRef': pin(contract_path, '/modeDecisions/0')}
feature['retentionStatus'] = 'retain-shared-feature-integration-pending'
feature['knownGaps'] = [
    'Imported search/filter ranking, effective host/cloud/account providers, delegated delete dialog and focus/navigation remain assigned interfaces.',
    'Actual multi-host/account source aggregation, persistence, partial failure and cross-entry equivalence.',
    'Actual mode/gate/account combinations and end-to-end acceptance; individual adapter ownership remains separate.']
scope['counts']['modeCounts'] = {'unknown': 339, 'codex': 0, 'chatgpt': 0, 'shared': 1}
scope_path = OUT / 'feature-scope-v22.json'
dump(scope_path, scope)
csv_path = OUT / 'feature-scope-v22.csv'
assert not csv_path.exists()
buffer = io.StringIO()
writer = csv.writer(buffer)
writer.writerow(['featureId', 'name', 'mode', 'operationCount', 'runtimeStatus', 'completeChainProven'])
for item in scope['features']:
    writer.writerow([item['featureId'], item['name'], item['mode'], len(item['operationMembers']),
                     item['runtimeStatus'], str(item['completeChainProven']).lower()])
csv_path.write_text(buffer.getvalue())
coverage = copy.deepcopy(old_coverage)
coverage['recordedAtUtc'] = now
coverage['previousSnapshot'] = pin(OUT / 'restoration-coverage-v12.json')
coverage['featureLedger'] = pin(scope_path)
coverage['modeOwnershipReconciliation'] = pin(contract_path)
coverage['counts']['modeCounts'] = scope['counts']['modeCounts']
for index, item in enumerate(coverage['features']):
    assert scope['features'][index]['featureId'] == item['featureId']
    item['featureRef'] = pin(scope_path, f'/features/{index}')
    if item['featureId'] == 'FSC-0280':
        item['mode'] = 'shared'
        item['retentionStatus'] = feature['retentionStatus']
        item['knownGaps'] = feature['knownGaps']
        item['modeDecisionRef'] = pin(contract_path, '/modeDecisions/0')
        item['evidence'].append(pin(contract_path))
group = next(item for item in coverage['taskGroups'] if item['taskId'] == 'T35')
group['evidence'].append(pin(contract_path))
group['sourceReceiverGaps'][0] = feature['knownGaps'][0]
coverage_path = OUT / 'restoration-coverage-v13.json'
dump(coverage_path, coverage)

summary_path.write_text('''# 归档功能的共享归属与保留边界

现有“浏览搜索筛选及排序归档记录”（FSC-0280）归为 `shared`：同一入口把 Codex app-server 本地归档、云任务与账户会话交给同一套浏览、搜索、筛选和排序界面。恢复时保留这套共享逻辑，分别维护三类数据适配器。

账户归档查询在 `includeWorkCloud=false` 时排除 `tpp` 来源，启用时取消排除。账户会话适配器因此不能按 `chatgpt` 名称整块删除。数据转换保留原始 task/thread 对象和 host，后续操作仍能按来源分派；共享集合不意味着三种恢复或删除协议可以合并。

```mermaid
flowchart LR
  Local[app-server 本地归档] --> Project[共享归档集合]
  Cloud[云任务归档] --> Project
  Account[账户会话归档] --> Project
  Project --> UI[浏览 搜索 筛选 排序]
  UI --> Dispatch[按记录来源分派操作]
```

| 已有功能 | 当前归属 | 恢复处理 |
| --- | --- | --- |
| 浏览搜索筛选及排序 | shared | 保留共享集合与界面，分别接入数据适配器 |
| 删除本地归档 | unknown | 保留本地协议；后台身份不单独证明产品模式 |
| 恢复归档云任务 | unknown | 保留云任务恢复分支，继续核对模式消费者 |
| 取消账户会话归档 | unknown | 保留；混合来源不足以证明 ChatGPT 专属 |
| 删除账户归档会话 | unknown | 保留；另有 work companion 清理关系待核对 |

四个 provider 导入已按完整 Program 的导出与词法绑定连接。10 项合成数据隔离用例通过，覆盖来源聚合、身份保留、查询来源过滤、分页以及恢复成功和失败。首次隔离工具因编译含 `import.meta` 的静态证据函数失败，修正工具只加载待执行函数后通过；原源码未改。实际客户端、账户、服务与持久化未在本批验证。

[源码合同与决定](archive-mode-ownership.json)、[台账 v22](feature-scope-v22.json)和[恢复覆盖表 v13](restoration-coverage-v13.json)已同步。有限功能总数仍为340，模式归属为 shared 1、unknown 339；1117 条产品场景规格仍未执行。原九项标准保持4项资料或范围义务有交付、5项部分完成。
''')

state['updatedAtUtc'] = now
view = state['featureScopeCurrentView']
view.update(snapshotVersion=22, ledger=pin(scope_path), csv=pin(csv_path),
            previousLedger=pin(OUT / 'feature-scope-v21.json'), counts=scope['counts'],
            reconciliationKind='positive-shared-archive-consumer-classification',
            reconciliationArtifact=pin(contract_path))
view['scope'] = 'Finite 340 definitions; shared 1, unknown 339; complete denominator unknown.'
view['modeOwnershipOverlay'] = pin(contract_path)
state['restorationCoverage'] = {**pin(coverage_path), 'scope': 'All 340 definitions, 1117 unexecuted specifications; shared 1, unknown 339.'}
state['modeOwnershipReconciliation'] = {'result': pin(contract_path), 'summary': pin(summary_path),
                                        'featureIdsChanged': ['FSC-0280'], 'modeCounts': scope['counts']['modeCounts'],
                                        'wholeModulesExcluded': 0, 'fullAnalysisCompleted': False}
for overlay in [state['analysisMilestones']['currentScopeOverlay'],
                state['stageDecisions']['currentScopeOverlay']]:
    overlay['featureLedger'] = pin(scope_path)
    overlay['modeOwnershipOverlay'] = pin(contract_path)
    key = 'coverage' if 'coverage' in overlay else 'restorationCoverage'
    overlay[key] = pin(coverage_path)
state['stageDecisions']['modeOwnershipOverlay'] = state['modeOwnershipReconciliation']
state['stageDecisions']['counts']['modeCounts'] = scope['counts']['modeCounts']
state['stageDecisions']['nextAction'] = {
    'issueId': 'SD-01/SD-02/SD-06',
    'completedSubstep': 'FSC-0280 source-confirmed shared; four archive provider joins closed; 10 isolated cases passed. Four individual mutation modes remain explicitly unknown.',
    'fixedInput': 'Existing entry-family-map and 968 legacy records; current feature scope v22 and coverage v13. Saved final-three settings selections remain available.',
    'question': 'Which legacy candidates already have definitive resource/metadata/duplicate dispositions, and which still represent unmapped user operations?',
    'closure': 'Reconcile by stable legacy ID and existing source evidence; do not equate unclosed metadata with a missing user feature or add fresh page families.',
    'deferredDedicatedVerification': 'Complete the three already-selected settings contracts and audit the original nine criteria. Individual mode consumers and actual service/runtime acceptance remain separate obligations.'}

prefix = (f'当前以[状态文件](analysis-state.json)和[归档共享归属](archive-mode-ownership.md)为准。'
          '[台账v22](feature-scope-v22.json)含340项有限定义、344项用户操作、103项支撑与1117条未执行规格，'
          '接到[恢复覆盖表v13](restoration-coverage-v13.json)的T01至T45。归属为shared 1、unknown 339；完整产品分母仍未知。\n\n'
          '本轮将已有归档浏览功能确认为共享，关闭四个provider导入连接；10项源码隔离用例通过，未新增功能或产品场景。'
          '45个设置容器仍有3个待完成；原九项标准仍为4项资料或范围义务有交付、5项部分完成。客户端实现尚未开始。以下旧数量与下一行动为历史记录。\n\n')
for filename in ['report.md', 'gaps.md']:
    file = OUT / filename
    text = file.read_text()
    start = text.index('当前以')
    end = text.index('其他当前恢复决定：', start)
    file.write_text(text[:start] + prefix + text[end:])
file = ROOT / 'README.md'
text = file.read_text()
start = text.index('当前为逆向分析阶段。')
end = text.index('- [当前分析状态与下一行动]', start)
relative = f'analysis/{BASELINE}/'
text = text[:start] + (
    f'当前为逆向分析阶段。[归档共享归属]({relative}archive-mode-ownership.md)将已有归档浏览功能归为shared，'
    '保留本地、云任务和账户会话适配器；10项源码隔离用例通过。\n\n'
    f'[台账v22]({relative}feature-scope-v22.json)现有340项有限定义、1117条未执行规格，'
    f'接到[恢复覆盖表v13]({relative}restoration-coverage-v13.json)的T01至T45。shared 1、unknown 339；'
    '45个设置容器中42个已有局部合同、3个待完成。完整分母、实际模式条件、服务、持久化与运行时仍待验证，客户端实现尚未开始。\n\n'
) + text[end:]
text = text.replace('当前功能台账为v21，完整产品分母未知。', '当前功能台账为v22，完整产品分母未知。')
file.write_text(text)

# Preserve queues, old scope IDs, completed behavior budgets and sibling overlays.
assert [item['featureId'] for item in scope['features']] == [item['featureId'] for item in old_scope['features']]
for key in ['supportOperations', 'operationReviewQueue', 'legacyEntryCoverage',
            'operationContainers', 'rootCandidateDispositions', 'retainedAssociationBacklog',
            'pageContainerRelations', 'legacyFeatureRelations', 'crossFeatureOverlapReviews']:
    assert scope[key] == old_scope[key], key
for previous, current in zip(old_scope['features'], scope['features']):
    if previous['featureId'] != 'FSC-0280':
        assert previous == current
assert state['latestBehaviorAuthorizationState'] == old_state['latestBehaviorAuthorizationState']
assert state['settingsOperationCoverage'] == old_state['settingsOperationCoverage']
assert state['stageDecisions']['latestConsolidation'] == old_state['stageDecisions']['latestConsolidation']
for key in ['runtimeBoundaryOverlay', 'productFlowOwnershipOverlay', 'browserCloneRouteOverlay',
            'publicHistoryDuplicateOverlay', 'accountAccessPublicationOverlay']:
    assert state['stageDecisions'][key] == old_state['stageDecisions'][key], key
assert all(digest(OUT / filename) == value for filename, value in input_hashes.items())
(OUT / 'analysis-state.json').write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
dump(WORK / 'publication-receipt.json', {
    'publishedAtUtc': now, 'inputHashes': input_hashes,
    'outputs': [pin(path) for path in [contract_path, summary_path, scope_path, csv_path, coverage_path]],
    'checks': 'Feature identities, unchanged features, queues, source snapshots, behavior budget and sibling overlays preserved.',
    'modeCounts': scope['counts']['modeCounts'], 'fullAnalysisCompleted': False})
print(json.dumps({'modeCounts': scope['counts']['modeCounts'], 'isolatedCasesPassed': 10,
                  'featureCount': len(scope['features']), 'updatedAtUtc': now}))
