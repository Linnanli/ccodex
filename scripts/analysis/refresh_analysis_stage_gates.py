"""Align current analysis gates with the unchanged original plan."""
import copy
import csv
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/codex-26.1007.30912-c5b273322a83'
WORK = ROOT / '.analysis-local/analysis-stage-gate-refresh-work'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path):
    return {'path': str(path.relative_to(OUT)), 'bytes': path.stat().st_size, 'sha256': sha(path)}


def dump(path, value):
    with path.open('x') as file:
        file.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


state = read(OUT / 'analysis-state.json')
assert state['featureScopeCurrentView']['snapshotVersion'] == 23
before = copy.deepcopy(state)
old = read(OUT / 'analysis-stage-decisions-v2.json')
plan_path = ROOT / 'docs/reverse-engineering/analysis-plan.md'
plan_text = plan_path.read_text()
requirements = [line.removeprefix('- [ ] ') for line in plan_text.splitlines() if line.startswith('- [ ] ')]
assert requirements == [item['requirement'] for item in old['criteria']]
assert sha(plan_path) == old['plan']['sha256']
scope = read(OUT / 'feature-scope-v23.json')
coverage = read(OUT / 'restoration-coverage-v14.json')
dispositions = read(OUT / 'legacy-entry-dispositions.json')
dependency_rows = list(csv.DictReader((OUT / 'dependencies.csv').open()))
assert len(dependency_rows) == 202
assert all(row['versionBasis'] and row['sourcePath'] and row['sourceHash'] and row['recommendedIntegration'] and row['unresolved'] for row in dependency_rows)
assert len(scope['features']) == len(coverage['features']) == 340
assert len(coverage['taskGroups']) == 45
assert len(coverage['unresolvedScope']['pendingSettingsPages']) == 3
assert not WORK.exists()
assert not (OUT / 'analysis-stage-decisions-v3.json').exists()
WORK.mkdir()
dump(WORK / 'state-before.json', before)

# Recheck feature-to-task/module/scenario references, without treating an
# implementation acceptance specification as an executed behavior test.
scenarios_path = OUT / 'feature-scope-v21-scenarios.json'
scenarios = read(scenarios_path)['scenarios']
scenario_index = {item['scenarioId']: item for item in scenarios}
assert len(scenario_index) == 1117
task_index = {item['taskId']: item for item in coverage['taskGroups']}
for item in coverage['features']:
    group = task_index[item['taskId']]
    assert item['featureId'] in group['featureIds']
    assert item['module'] == group['primaryModule']
    assert item['evidence'] and item['scenarioIds']
    for identifier in item['scenarioIds']:
        assert scenario_index[identifier]['featureId'] == item['featureId']

findings = [
    '固定基线及外部候选身份分列沿用；本轮235个来源角色和6个注册调用核对了3个冻结文件、294个不同字节范围。',
    '340项有限功能、344项用户操作、103项支撑和968条旧记录已登记。旧记录新增逐ID处置视图；3个已选定设置合同、12项关联待办及3项交叉重叠仍需收口，不能宣称完整产品分母。',
    '当前模式为shared 1、unknown 339，确认排除0。归档聚合有正向共享消费者证据；其余unknown合法保留，但影响保留边界的模式与共享依赖仍待定向分析。',
    '340项功能均有拟议模块和来源引用，接入45个任务组；局部源码合同持续补齐。关键发送/接收、真实状态所有权和服务边界仍有影响架构的未知，不能仅凭模块路径宣称全功能链已分析。',
    '202项依赖均有版本依据、来源位置及哈希、建议引入方式和未知项字段；这是来源/调查登记义务。新客户端的锁文件与替代后兼容验证属于后续实现。',
    '原生、Wasm、辅助程序、Owl及私有服务的独立记录沿用；公共运行时对照和objc构建候选分别保留范围。独立记录义务不要求本阶段已重建全部原生组件。',
    'source map、REA限制、动态边界及30个构建输入处置已有来源；后续需按决定补齐工程文件，分析阶段不要求这些文件已经实现。',
    '真实只读任务完成、重新打开及停止重启结果已有记录；取消未测。合成源码回放与公共运行时探针不作原客户端通过项，剩余模型提交授权为0。',
    '340项功能均已引用任务、模块、来源与1117条场景规格；30条构建输入有处置。实施计划v8仍是274项/T01至T33快照，当前覆盖表扩展到T45；统一恢复顺序、关键运行时路线和范围收口仍待完成。',
]
analysis_closures = [
    '保持固定输入哈希及来源身份；变化时建新基线，公开候选与基线实际版本分列。',
    '对齐已发现文件、入口和候选的登记域与范围说明；完成已选定页面及待办的处置。支撑/重复/容器/未知有明确位置，不要求每个源码片段变成独立用户功能。',
    '每个候选保留明确模式状态与依据；拟排除项有模式条件和Codex共享依赖检查。会改变功能保留范围的未知有具体调查或外部条件，不能依名称删除；并不要求unknown数量归零。',
    '每个保留功能有足以解释职责的模块与关键跨进程/外部边界；影响架构的断点继续定向分析。无需在分析期完成全部源码恢复或执行完整客户端。',
    '依赖的版本/来源依据、第一方封装及第三方边界、建议引入方式和未知调查动作可核对；保留修改、多版本、原生及实际发行身份的条件。',
    '特殊组件分别登记接口、来源、版本/平台条件及独立引入或替代的可行性；影响架构的未决路线继续调查。',
    '明确source map覆盖、缺失输入及处置、工具截断和动态未知；能据此安排工程补齐与定向调查。',
    '主要流程的真实观察与静态契约能对照；未验证项给出具体前置条件、动作、预期和受限原因。完成、取消、执行中断与重启重新打开分别记录，不要求在分析期跑完全部1117条实施规格。',
    '当前已保留范围接到有来源的目录/包边界、依赖引入、恢复顺序、阶段验收和升级方法；关键架构未决项有影响及关闭条件。实现尚未完成不能单独作为分析不合格的理由。',
]
implementation_acceptance = [
    '按新工程锁定的输入重建和发布，建立后续版本差异检查。',
    '完整保留功能清单逐项实现并验收；mock和占位不算复刻。',
    '在实际模式、账户与开关条件下核验剥离及共享依赖。',
    '实现具体模块、生命周期、错误、取消、持久化与端到端行为。',
    '生成并验证自己的依赖锁文件，接入公开包/补丁，构建并验证兼容；最终源码不复制第三方实现。',
    '构建或独立引入选定原生/运行时依赖，验证目标平台、ABI及替代能力。',
    '编写并验证工程配置、源码和缺失构建输入，在干净环境安装、构建、打包。',
    '执行完整功能验收与回归场景，检验失败、取消、重启恢复及实际服务。',
    '独立应用标识和数据目录，运行不依赖原安装目录；完整构建、打包和升级回归通过。',
]
current_evidence = [
    ['baseline.json', 'baseline-reverification.json', 'legacy-entry-dispositions.json'],
    ['feature-scope-v23.json', 'legacy-entry-dispositions.json', 'restoration-coverage-v14.json'],
    ['feature-scope-v23.json', 'archive-mode-ownership.json', 'desktop-access-publication.json'],
    ['restoration-coverage-v14.json', 'product-flow-ownership.json', 'desktop-access-publication.json'],
    ['dependencies.csv', 'dependency-import-decisions.json'],
    ['native-runtime.json', 'runtime-capability-decisions.json', 'native-browser-settings-comparison.json'],
    ['source-map-validation.json', 'build-inputs.json', 'build-input-dispositions-v1.json'],
    ['behavior-checks.md', 'behavior-stop-restart.json', 'feature-scope-v21-scenarios.json'],
    ['implementation-plan-v8.md', 'restoration-coverage-v14.json', 'build-input-dispositions-v1.json'],
]
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
decision = copy.deepcopy(old)
decision['recordedAtUtc'] = now
decision['previousSnapshot'] = pin(OUT / 'analysis-stage-decisions-v2.json')
decision['reviewScope'] = ('Current gate interpretation and feature/task/scenario/legacy-role accounting. '
                           'Four record obligations retain their bounded historical proof; this is not a renewed full-source or full-behavior audit.')
decision['historicalStagesRef'] = {**pin(OUT / 'analysis-stage-decisions-v2.json'), 'jsonPointer': '/stages'}
decision.pop('stages')
decision['stageRequirementStatusQualification'] = 'All six stages and 39 subordinate requirements remain in the pinned historical view; their old item statuses are not refreshed by this nine-gate review.'
for i, criterion in enumerate(decision['criteria']):
    criterion['currentFinding'] = findings[i]
    criterion['closeWhen'] = analysis_closures[i]
    criterion['implementationAcceptanceDeferred'] = implementation_acceptance[i]
    criterion['currentEvidence'] = [pin(OUT / name) for name in current_evidence[i]]
decision['counts'] = copy.deepcopy(state['stageDecisions']['counts'])
decision['currentScope'] = {
    'featureLedger': pin(OUT / 'feature-scope-v23.json'), 'scenarioLedger': pin(scenarios_path),
    'restorationCoverage': pin(OUT / 'restoration-coverage-v14.json'),
    'legacyEntryDispositions': pin(OUT / 'legacy-entry-dispositions.json'),
    'buildInputDispositions': pin(OUT / 'build-input-dispositions-v1.json'),
    'completeFeatureDenominator': None, 'pendingSettingsOperationContainers': 3,
    'modelSamplesRemaining': 0,
}
decision['nextAction'] = copy.deepcopy(state['stageDecisions']['nextAction'])
decision['interpretation'] = ('Analysis and implementation gates follow the unchanged plan. Unknown mode, '
                              'unexecuted implementation specifications and an unbuilt client are not automatic '
                              'analysis failures. Architecture-changing unknowns still require directed analysis. '
                              'Five original analysis criteria remain partial; no completion status promoted.')
for issue in decision['remainingIssues']:
    if issue['id'] == 'SD-01':
        issue['nextAction'] = '完成已选定的3个设置合同，随后对齐现有发现域、功能关联和交叉重叠；不新增页面调查范围。'
    elif issue['id'] == 'SD-02':
        issue['closeWhen'] = '特殊能力的独立来源、接口差异与替代可行性足以支持运行时架构决定；仍影响架构的未知保持开放。实际替代实现、全能力与ABI验收属于实施期。'
    elif issue['id'] == 'SD-04':
        issue['nextAction'] = '围绕主要任务流程已有观察和未验证条件核对差异；1117条规格作为后续验收输入，新增模型提交仍需新授权。'
    elif issue['id'] == 'SD-06':
        issue['nextAction'] = '将v8实施计划与当前340项/T45覆盖表统一，检查任务依赖、独立运行时路线和升级方法；30条缺失输入按现有决定落实到后续任务。'
        issue['closeWhen'] = '目录、依赖、恢复顺序、验收与升级建议引用当前分析证据；独立构建路线的架构未知有明确处理条件。实际实现、构建、打包和完整回归在实施阶段验收。'
result = OUT / 'analysis-stage-decisions-v3.json'
summary = OUT / 'analysis-stage-decisions-v3.md'
dump(result, decision)
lines = ['# 当前分析阶段的关闭条件', '',
         '原计划和九项标准保持不变。本表将分析交付与实施验收分开：分析需要功能边界、依赖来源、架构证据、主要行为对照及实施依据；干净构建、完整功能复刻和全部回归属于实施阶段。影响架构或完整范围的未知仍须继续定向分析。', '',
         '当前有限范围为340项功能、344项用户操作、103项支撑与1117条未执行规格，接到45个任务组。原九项标准仍为4项资料或范围义务有交付、5项部分完成；本次没有提升完成状态。', '',
         '| 标准 | 状态 | 当前分析结论 |', '| --- | --- | --- |']
for criterion in decision['criteria']:
    status = '资料或范围义务已有交付' if criterion['status'] == 'satisfied-with-scope-limits' else '部分完成'
    lines.append(f"| {criterion['id']} | {status} | {criterion['currentFinding']} |")
lines += ['', '## 分析与实施的区别', '',
          '模式unknown是允许保留的分类，数量不必机械归零；拟排除项仍需明确模式和共享依赖证据。场景规格不是执行结果，但分析完成不要求把后续全部1117条实施规格提前跑完。新客户端尚未实现、没有自己的锁文件或尚未打包，也不能单独作为分析失败的理由。', '',
          'AC-04仍要求每个保留功能的职责和关键边界可解释；AC-08仍要求主要行为的实际对照及具体未验证条件；AC-09仍要求当前范围、目录、依赖、恢复顺序、验收与升级方法有来源。未决运行时路线、遗漏范围或关键行为证据不足时，目标继续保持未完成。', '',
          '235条资源／命令声明和6条注册调用的已确认角色已接入旧入口处置表；726条仍待明确角色，967条仍无功能映射，二者分开计数。它们不能逐条当作用户功能，也不能据角色确认宣称功能链完成。', '',
          '下一步完成已经选定的cloud-environments、personalization和codex-micro三个设置合同；随后统一当前范围与实施计划v8，并核对影响架构的关键未知。继续使用冻结来源，不增加未授权模型任务。', '',
          '[逐项关闭条件与后续实施验收](analysis-stage-decisions-v3.json)、[当前功能台账](feature-scope-v23.json)、[恢复覆盖表](restoration-coverage-v14.json)、[旧入口处置](legacy-entry-dispositions.md)和[实施计划v8](implementation-plan-v8.md)。历史六阶段及39条子要求完整保留在[v2快照](analysis-stage-decisions-v2.json)，其旧状态未由本次九项门槛复核更新。', '']
summary.write_text('\n'.join(lines))
state['updatedAtUtc'] = now
state['stageDecisions']['decisions'] = pin(result)
state['stageDecisions']['summary'] = pin(summary)
state['stageDecisions']['analysisImplementationGateReview'] = {
    'result': pin(result), 'summary': pin(summary), 'originalPlanChanged': False,
    'criterionStatusesChanged': False, 'implementationRequiredForAnalysisCompletion': False,
    'architectureChangingUnknownsStillRequireAnalysis': True,
    'featureTaskLinksChecked': 340, 'scenarioIdentitiesChecked': 1117,
    'dependencyRecordRequiredFieldsChecked': 202,
    'scope': decision['reviewScope'],
}
state['stageDecisions']['currentScopeOverlay']['priorStageDocumentSnapshot'] = 'analysis-stage-decisions-v2.md'
state['stageDecisions']['provenance'] = {
    'path': 'analysis-stage-decisions-v3.json', 'bytes': result.stat().st_size,
    'sha256': sha(result), 'qualification': 'Input pins, review scope and historical source references are embedded in this current decision snapshot.'}
for name in ['report.md', 'gaps.md']:
    path = OUT / name
    text = path.read_text()
    marker = '其他当前恢复决定：'
    index = text.index(marker)
    text = text[:index] + ('[当前分析关闭条件](analysis-stage-decisions-v3.md)已分开分析交付与实施验收；'
                           '完整构建、打包和逐项功能复刻在实施阶段核验，影响架构的未知继续定向分析。\n\n') + text[index:]
    path.write_text(text)
path = ROOT / 'README.md'
text = path.read_text()
text = text.replace('analysis-stage-decisions-v2.md', 'analysis-stage-decisions-v3.md')
text = text.replace('当前实施计划草案](analysis/codex-26.1007.30912-c5b273322a83/implementation-plan-v7.md)',
                    '当前实施计划草案](analysis/codex-26.1007.30912-c5b273322a83/implementation-plan-v8.md)')
path.write_text(text)
assert state['latestBehaviorAuthorizationState'] == before['latestBehaviorAuthorizationState']
assert state['featureScopeCurrentView'] == before['featureScopeCurrentView']
assert state['restorationCoverage'] == before['restorationCoverage']
assert [item['status'] for item in decision['criteria']] == [item['status'] for item in old['criteria']]
assert sha(plan_path) == old['plan']['sha256']
(OUT / 'analysis-state.json').write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
dump(WORK / 'publication-receipt.json', {
    'recordedAtUtc': now, 'outputs': [pin(result), pin(summary)],
    'planHashUnchanged': sha(plan_path), 'previousDecisionHash': sha(OUT / 'analysis-stage-decisions-v2.json'),
    'criterionStatusesUnchanged': True, 'featureTaskLinksChecked': 340,
    'scenarioIdentitiesChecked': 1117, 'dependencyRecordRequiredFieldsChecked': 202,
    'fullAnalysisCompleted': False})
print(json.dumps({'status': 'published', 'criteria': 9, 'criterionStatusesChanged': False,
                  'featureTaskLinksChecked': 340, 'scenarioIdentitiesChecked': 1117,
                  'dependencyRecordRequiredFieldsChecked': 202, 'fullAnalysisCompleted': False}))
