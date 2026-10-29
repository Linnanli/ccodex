"""Record Chat-only branch decisions and a positive retained Codex consumer."""
from pathlib import Path
import copy
import csv
import datetime
import hashlib
import io
import json
import shutil

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/chat-branch-decisions-work'
RAW = OUT / 'raw/chat-branch-decisions'


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path, pointer=None):
    value = {'path': str(path.relative_to(OUT)), 'bytes': path.stat().st_size, 'sha256': digest(path)}
    if pointer is not None:
        value['jsonPointer'] = pointer
    return value


def write(path, value):
    with path.open('x') as file:
        file.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


state_path = OUT / 'analysis-state.json'
old_state = read(state_path)
assert old_state['updatedAtUtc'] == '2026-10-24T14:13:43.365252+00:00'
assert old_state['featureScopeCurrentView']['snapshotVersion'] == 24
source = read(WORK / 'branch-source.json')
probe = read(WORK / 'probe-attempt-02.json')
assert source['newFullProgramParses'] == 0 and len(source['fragments']) == 12
assert probe['counts'] == {'cases': 25, 'passed': 25, 'failed': 0}
assert read(WORK / 'probe-receipt-02.json')['exitCode'] == 0
assert probe['sourceContractsSha256'] == digest(WORK / 'branch-source.json')
assert probe['scriptSha256'] == digest(ROOT / 'scripts/analysis/probe_chat_branch_decisions.cjs')
assert read(WORK / 'probe-attempt-01.json')['scriptSha256'] == digest(WORK / 'probe-attempt-01.cjs')
assert digest(ROOT / 'docs/reverse-engineering/analysis-plan.md') == '48dd8b65348efd4a8b5634aac5341c4507c262e7b5c88e8ed9368c88eeb96db4'
old_scope = read(OUT / 'feature-scope-v24.json')
old_coverage = read(OUT / 'restoration-coverage-v15.json')
assert not RAW.exists() and not (OUT / 'feature-scope-v25.json').exists()
write(WORK / 'state-before.json', old_state)
for file in ['report.md', 'gaps.md']:
    shutil.copyfile(OUT / file, WORK / (file + '.before'))
shutil.copyfile(ROOT / 'README.md', WORK / 'README.md.before')
shutil.copytree(WORK, RAW, ignore=shutil.ignore_patterns('state-before.json', '*.before'))
for filename in ['extract_chat_branch_decisions.cjs', 'probe_chat_branch_decisions.cjs', 'publish_chat_branch_decisions.py']:
    shutil.copyfile(ROOT / 'scripts/analysis' / filename, RAW / filename)
source_file = RAW / 'branch-source.json'
fragment_indices = {item['id']: index for index, item in enumerate(source['fragments'])}


def refs(*names):
    return [pin(source_file, '/fragments/' + str(fragment_indices[name])) for name in names]


decisions = [
    {
        'id': 'CBX-01', 'scope': 'render-branch', 'responsibility': '临时Chat页脚',
        'mode': 'chatgpt', 'decision': 'exclude-this-branch-from-restored-client',
        'condition': 'homeComposerMode === chat && chatHomeState.isTemporaryChat',
        'sourceRefs': refs('jRt:chat-temporary-footer'),
        'retainedDependencies': ['jRt shared layout and NRt rendering', 'VIt state provider and other consumers', 'CFt module remains unclassified outside this callsite'],
        'implementationInstruction': 'Omit this conditional footer callsite. Preserve the shared jRt wrapper, state computation and NRt subtree; do not delete CFt or its imports based on this single use.',
        'limitation': 'Source-confirmed branch responsibility. Four synthetic derived-omission comparisons cover selected Codex/Work output trees, not complete-client removal safety.',
    },
    {
        'id': 'CBX-02', 'scope': 'conditional-configuration-family', 'responsibility': 'Chat专用输入提示配置',
        'mode': 'chatgpt', 'decision': 'exclude-chat-alternatives-retain-neutral-policy',
        'condition': 'wzt effective mode W === chat; Ezt mode o === chat',
        'sourceRefs': refs('wzt:chat-inline-enabled', 'wzt:chat-inline-variant', 'Ezt:mode-suggestion-policy', 'Tzt:codex-suggestion-policy'),
        'retainedDependencies': ['Q9 neutral/Codex suggestion triggers', 'controller suggestion setup and effect lifetime', 'Work draft restoration in the same Ezt effect', 'kzt and suggestion modules remain unclassified outside these choices'],
        'implementationInstruction': 'At these choices omit the Chat trigger/options alternatives; preserve Q9 with inline hints disabled and variant undefined, as the Codex Tzt consumer already does. Keep unrelated Work draft restoration in the same effect.',
        'limitation': 'A branch family spans several source sites; it is one decision, not several new user features. General prompt parsing and all suggestion implementations remain retained until separately classified.',
    },
    {
        'id': 'CBX-03', 'scope': 'command-registration-callsite', 'responsibility': '切换到Chat的快捷键入口',
        'mode': 'chatgpt', 'decision': 'exclude-this-registration-callsite',
        'condition': 'Ezt registers switchToMode1 -> callback me(chat); enabled is canSwitchMode',
        'sourceRefs': refs('Ezt:chat-shortcut-registration', 'Ezt:chat-shortcut-callback', 'Ezt:mode-shortcut-eligibility'),
        'retainedDependencies': ['shared mode-transition callback me and its Work branch', 'switchToMode2 and newTask registrations', 'py command framework and other registrations'],
        'implementationInstruction': 'Omit only this Chat-target registration. Audit other Chat-target controls separately; keep the shared transition handler and unrelated command registrations.',
        'limitation': 'The command targets Chat even when invoked from Work. This does not establish that every same-named command implementation is Chat-only or that all Chat entrypoints have been covered.',
    },
]
for decision in decisions:
    decision.update(method='static-code-with-isolated-observations', confidence='confirmed-for-listed-source-sites', sourceBranchDecision=True, wholeFeatureExcluded=False, wholeModuleExcluded=False, removalImplemented=False)
positive = {
    'id': 'CBR-01', 'featureId': 'FSC-0048', 'taskId': 'T03',
    'decision': 'retain-positive-codex-consumer-integration-pending',
    'reason': 'The source Codex-specific Tzt entry supplies isCodexHome:true to M9. Saved qualified sources connect M9 to jRt/NRt and the Codex destination to $X/rpt, which is the already-registered ordinary create/first-turn operation.',
    'sourceRefs': refs('Tzt:positive-Codex-M9', 'M9:retained-jRt', 'jRt:retained-NRt'),
    'existingChainEvidence': [pin(OUT / 'product-flow-ownership.json', '/facts/2'), pin(OUT / 'product-flow-ownership.json', '/facts/3'), pin(OUT / 'thread-start-entry-contracts.json', '/facts/0')],
    'productMode': 'unknown',
    'qualification': 'Positive Codex usage establishes retention. It does not prove exclusive Codex ownership, the complete consumer set, actual mount/host/account conditions, backend effects or durable recovery.',
}
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
artifact = {
    'schemaVersion': 1, 'baselineId': BASE, 'recordedAtUtc': now,
    'scope': 'Existing home/composer branch decisions and FSC-0048 retention; no new page, feature, task or product scenario.',
    'inputPins': [pin(OUT / name) for name in ['feature-scope-v24.json', 'restoration-coverage-v15.json', 'product-flow-ownership.json', 'thread-start-entry-contracts.json']],
    'sourceContract': pin(source_file), 'decisions': decisions, 'positiveRetentionDecisions': [positive],
    'isolatedObservation': pin(RAW / 'probe-attempt-02.json'),
    'failedFixtureAttempt': {'observation': pin(RAW / 'probe-attempt-01.json'), 'script': pin(RAW / 'probe-attempt-01.cjs'), 'reason': 'Eight Ezt cases failed because the synthetic environment omitted the external Wg predicate. The fixture was corrected; no original target source was changed.'},
    'counts': {'confirmedChatOnlyBranchDecisionGroups': 3, 'positiveCodexFeatureRetentionDecisions': 1, 'featureModesChanged': 0, 'newFullProgramParses': 0, 'selectedFunctionParses': 5, 'sourceFragments': 12, 'savedSharedLexicalJoins': 2, 'isolatedCasesPassed': 25, 'derivedFooterOmissionCasesIncluded': 4, 'newFeatures': 0, 'newProductSpecifications': 0, 'confirmedWholeFeatureExclusions': 0, 'confirmedWholeModuleExclusions': 0, 'productScenarioPassesAdded': 0, 'modelSubmissionsAdded': 0, 'originalClientRunsAdded': 0},
    'remainingModeWork': ['Other Chat entrypoints, custom assistants and temporary-chat query consumers need their own exact-site decisions; no global query/transport deletion is approved by this result.', 'Retained Work-cloud and account archive consumers continue to prevent deleting CIt or account/conversation providers by name.', 'Other feature modes, complete discovered-entry disposition and account/runtime conditions remain as previously registered.'],
    'implementationBoundary': 'The future restored project retains shared first-party home/composer/task modules and applies the listed branch policies at their recorded source sites. Third-party implementation remains external dependencies; no client code is generated here.',
    'upgradeAcceptance': ['Rebind the listed source sites and enclosing functions against each new baseline; do not reuse minified local names as stable API.', 'Compare Codex/local first-turn and retained Work-cloud destinations before applying any Chat exclusion.', 'Re-run source branch probes and separately validate actual client entrypoints and retained behavior.'],
    'limits': probe['limits'], 'fullAnalysisCompleted': False, 'clientImplementationStarted': False,
}
artifact_path = OUT / 'chat-branch-decisions.json'
write(artifact_path, artifact)
summary_path = OUT / 'chat-branch-decisions.md'
summary_path.write_text('''# Chat专用分支的排除决定与Codex保留依据

本次确定3组具体源码分支在重建客户端中排除：临时Chat页脚、Chat专用输入提示配置、切换到Chat的快捷键注册。每组均在[决定清单](chat-branch-decisions.json)记录条件、精确源码范围、必须保留的共享依赖和升级检查；这不是整模块或完整功能的排除证明，尚未修改客户端实现。

| 决定 | 排除位置 | 必须保留 |
| --- | --- | --- |
| CBX-01 | `jRt` 中严格chat且临时会话的页脚分支 | 共享布局、状态provider和NRt |
| CBX-02 | `wzt/Ezt` 的Chat专用trigger、inline hints和variant选择 | Codex的Q9配置、controller生命周期及Work草稿恢复 |
| CBX-03 | `Ezt` 中目标为chat的switchToMode1注册 | Work切换、newTask、共享切换处理及命令框架 |

已有“创建新会话并提交首条消息”（FSC-0048）新增明确保留依据：Codex专用Tzt把isCodexHome传给共享M9，经已有jRt／NRt目的地选择进入已登记的本地提交链。其处理由“待模式审查”推进为“已有正向Codex消费者，保留并等待集成验证”。完整独占／共享归属仍为unknown；无需先证明所有其他消费者不存在，才能保留这个已确认被Codex使用的操作。

25项隔离用例通过，覆盖页脚条件、共享提示配置、Chat快捷键目标和Codex入口。其内4项在VM内仅移除页脚条件式，比较合成Codex／Work渲染树保持一致；不作为完整客户端剥离验收。首轮8项因fixture缺少导入谓词Wg失败，修正测试替身后全部通过，两个版本均保留。

复用了已保存完整Program的词法身份，只解析5个已选择函数和12处局部范围；没有重新扫描大bundle、增加模型提交或启动原客户端。主composer、远端Work候选和账户归档适配器仍按已有共享消费者证据保留。

[功能台账v25](feature-scope-v25.json)和[覆盖表v16](restoration-coverage-v16.json)接入上述决定；仍为373项功能、48个任务组、1216条未执行产品规格。模式总数仍是shared 1／unknown 372，整项功能排除仍为0；另有3组源码分支排除决定，二者分别统计。原九项完成标准未改为通过，完整分析尚未完成。
''')
csv_path = OUT / 'chat-branch-decisions.csv'
with csv_path.open('x', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['id', 'scope', 'responsibility', 'mode', 'decision', 'condition', 'wholeFeatureExcluded', 'wholeModuleExcluded', 'removalImplemented'])
    for decision in decisions:
        writer.writerow([decision[key] for key in ['id', 'scope', 'responsibility', 'mode', 'decision', 'condition', 'wholeFeatureExcluded', 'wholeModuleExcluded', 'removalImplemented']])
scope = copy.deepcopy(old_scope)
scope['purpose'] = 'Current finite feature ledger with positive Codex retention and explicit Chat-only branch decisions.'
scope['previousScopeRef'] = pin(OUT / 'feature-scope-v24.json')
scope['inheritedLedgerRef'] = pin(OUT / 'feature-scope-v24.json')
scope['inheritedScenarioRef'] = pin(OUT / 'feature-scope-v24-scenarios.json')
scope['newDefinitionIds'] = []
scope['chatBranchDecisions'] = pin(artifact_path)
feature = next(item for item in scope['features'] if item['featureId'] == 'FSC-0048')
feature['retentionStatus'] = positive['decision']
feature['retentionEvidence'] = pin(artifact_path, '/positiveRetentionDecisions/0')
feature['modeEvidence'] = {'priorEvidence': feature['modeEvidence'], 'positiveCodexConsumer': True, 'exclusiveOrSharedClassification': 'unknown', 'decisionRef': pin(artifact_path, '/positiveRetentionDecisions/0'), 'qualification': positive['qualification']}
feature['sourceRefs'].append(pin(artifact_path, '/positiveRetentionDecisions/0'))
scope_path = OUT / 'feature-scope-v25.json'
write(scope_path, scope)
scope_csv = OUT / 'feature-scope-v25.csv'
buffer = io.StringIO(); writer = csv.writer(buffer)
writer.writerow(['featureId', 'name', 'mode', 'operationCount', 'runtimeStatus', 'completeChainProven'])
for item in scope['features']:
    writer.writerow([item['featureId'], item['name'], item['mode'], len(item['operationMembers']), item['runtimeStatus'], str(item['completeChainProven']).lower()])
with scope_csv.open('x') as file:
    file.write(buffer.getvalue())
coverage = copy.deepcopy(old_coverage)
coverage.update(recordedAtUtc=now, previousSnapshot=pin(OUT / 'restoration-coverage-v15.json'), featureLedger=pin(scope_path), chatBranchDecisions=pin(artifact_path))
for index, item in enumerate(coverage['features']):
    assert item['featureId'] == scope['features'][index]['featureId']
    item['featureRef'] = pin(scope_path, f'/features/{index}')
    if item['featureId'] == 'FSC-0048':
        item['retentionStatus'] = positive['decision']
        item['retentionDecisionRef'] = pin(artifact_path, '/positiveRetentionDecisions/0')
        item['evidence'].append(pin(artifact_path))
next(item for item in coverage['taskGroups'] if item['taskId'] == 'T03')['evidence'].append(pin(artifact_path))
coverage_path = OUT / 'restoration-coverage-v16.json'
write(coverage_path, coverage)
state = copy.deepcopy(old_state)
state['updatedAtUtc'] = now
overlay = {'result': pin(artifact_path), 'summary': pin(summary_path), 'csv': pin(csv_path), 'counts': artifact['counts'], 'retentionFeatureIdsChanged': ['FSC-0048'], 'wholeFeatureExclusions': 0, 'wholeModuleExclusions': 0, 'fullAnalysisCompleted': False}
state['chatBranchDecisions'] = overlay
view = state['featureScopeCurrentView']
view.update(snapshotVersion=25, ledger=pin(scope_path), csv=pin(scope_csv), previousLedger=pin(OUT / 'feature-scope-v24.json'), reconciliationKind='positive-codex-retention-and-chat-branch-decisions', reconciliationArtifact=pin(artifact_path), chatBranchDecisionOverlay=pin(artifact_path))
state['restorationCoverage'] = {**pin(coverage_path), 'scope': 'All373 definitions,1216 unexecuted specifications; 3 branch decision groups,0 whole-feature exclusions; complete denominator unknown.'}
for parent in [state['stageDecisions']['currentScopeOverlay'], state['analysisMilestones']['currentScopeOverlay']]:
    parent['featureLedger'] = pin(scope_path)
    key = 'coverage' if 'coverage' in parent else 'restorationCoverage'
    parent[key] = pin(coverage_path)
    parent['chatBranchDecisionOverlay'] = pin(artifact_path)
state['stageDecisions']['chatBranchDecisionOverlay'] = overlay
state['stageDecisions']['nextAction'] = {
    'issueId': 'SD-01/SD-02/SD-03/SD-05/SD-06',
    'completedSubstep': 'Three Chat-only branch decisions and positive Codex retention of FSC-0048 published; 25 isolated cases passed. No entire feature/module exclusion or full mode closure claimed.',
    'fixedInput': 'Original nine-criterion plan, current scope v25, coverage v16 and all settled frozen-source contracts; retain the existing feature denominator and unresolved-entry accounting.',
    'question': 'Which architecture-changing runtime/provider/storage decisions and discovered-scope dispositions still prevent analysis exit?',
    'closure': 'Complete the original requirement audit using current evidence and resolve named architecture-changing gaps; do not require unknown modes to become zero or treat implementation/product specs as completed behavior.',
    'deferredDedicatedVerification': 'Actual client integration remains separate. No additional model submission authorization remains.'}
assert scope['counts'] == old_scope['counts'] and coverage['counts'] == old_coverage['counts']
for before, after in zip(old_scope['features'], scope['features']):
    if before['featureId'] != 'FSC-0048':
        assert before == after
assert state['latestBehaviorAuthorizationState'] == old_state['latestBehaviorAuthorizationState']
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
paragraph = '\n[Chat分支取舍决定](chat-branch-decisions.md)明确3组Chat专用源码分支在重建时排除，并为已有FSC-0048登记正向Codex保留依据；25项隔离回放通过。当前[台账v25](feature-scope-v25.json)／[覆盖表v16](restoration-coverage-v16.json)保持373项定义、48任务组及1216条未执行规格；3组分支决定与0项整功能排除分别统计。\n'
for filename in ['report.md', 'gaps.md']:
    file = OUT / filename; heading, rest = file.read_text().split('\n', 1)
    file.write_text(heading + '\n' + paragraph + rest)
readme = ROOT / 'README.md'; text = readme.read_text(); heading, rest = text.split('\n', 1)
readme.write_text(heading + '\n\n当前模式取舍补充：[' + 'Chat专用分支决定](analysis/' + BASE + '/chat-branch-decisions.md)登记3组具体分支，并明确保留Codex新建会话链；[台账v25](analysis/' + BASE + '/feature-scope-v25.json)和[覆盖表v16](analysis/' + BASE + '/restoration-coverage-v16.json)为当前快照。功能／规格数量不变，客户端尚未实现，以下编号为历史记录。\n' + rest)
for file in [artifact_path, summary_path, csv_path, scope_path, scope_csv, coverage_path, *[file for file in RAW.rglob('*') if file.is_file()]]:
    file.chmod(0o444)
print(json.dumps({'artifact': str(artifact_path), 'counts': artifact['counts'], 'featureLedger': str(scope_path), 'coverage': str(coverage_path)}, ensure_ascii=False))
