"""Align the implementation plan with already published analysis; no source analysis."""
import copy
import hashlib
import json
import pathlib
import re
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/codex-26.1007.30912-c5b273322a83'
WORK = ROOT / '.analysis-local/restoration-plan-v9-work'


def read(name):
    return json.loads((OUT / name).read_text())


def ref(name):
    data = (OUT / name).read_bytes()
    return dict(path=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def dag(graph):
    nodes = {row['id']: row['dependsOn'] for row in graph}
    assert len(nodes) == len(graph)
    visited, active = set(), set()

    def visit(node):
        assert node in nodes, node
        assert node not in active, node
        if node in visited:
            return
        active.add(node)
        for dependency in nodes[node]:
            visit(dependency)
        active.remove(node)
        visited.add(node)

    for node in nodes:
        visit(node)


def main():
    state = read('analysis-state.json')
    assert state['updatedAtUtc'] == '2026-10-24T13:34:12.538235+00:00'
    for name in ['implementation-plan-v9.md', 'implementation-milestones-v9.json',
                 'restoration-plan-v9-provenance.json']:
        assert not (OUT / name).exists(), name
    WORK.mkdir(parents=True, exist_ok=False)
    dump(WORK / 'state-before.json', state)
    now = datetime.now(timezone.utc).isoformat()
    scope = read('feature-scope-v23.json')
    coverage = read('restoration-coverage-v14.json')
    scenarios = read('feature-scope-v21-scenarios.json')
    old = read('implementation-milestones-v8.json')
    pins = [ref(name) for name in [
        'feature-scope-v23.json', 'feature-scope-v21-scenarios.json',
        'restoration-coverage-v14.json', 'implementation-plan-v8.md',
        'implementation-milestones-v8.json', 'analysis-stage-decisions-v3.json',
        'build-input-dispositions-v1.json', 'archive-mode-ownership.json',
        'legacy-entry-dispositions.json', 'browser-clone-route-qualification.json',
        'public-history-duplicate-comparison.json', 'desktop-access-publication.json',
        'behavior-stop-restart.json']]
    features = {row['featureId']: row for row in coverage['features']}
    scope_ids = {row['featureId'] for row in scope['features']}
    scenario_ids = {row['scenarioId'] for row in scenarios['scenarios']}
    tasks = copy.deepcopy(coverage['taskGroups'])
    task_ids = [row['taskId'] for row in tasks]
    owners = [fid for task in tasks for fid in task['featureIds']]
    assert len(owners) == len(set(owners)) == len(features) == 340
    assert set(owners) == set(features) == scope_ids
    assert len(task_ids) == len(set(task_ids)) == 45
    assert len(scenario_ids) == len(scenarios['scenarios']) == 1117
    linked_scenarios = set()
    for task in tasks:
        for fid in task['featureIds']:
            row = features[fid]
            assert row['taskId'] == task['taskId']
            assert row['module'] == task['primaryModule']
            assert row['scenarioIds'] and set(row['scenarioIds']) <= scenario_ids
            linked_scenarios.update(row['scenarioIds'])
    assert linked_scenarios == scenario_ids
    assert coverage['counts']['modeCounts'] == dict(unknown=339, codex=0, chatgpt=0, shared=1)

    milestones = copy.deepcopy(old)
    milestones.update(schemaVersion=9, recordedAtUtc=now,
        previousSnapshot=ref('implementation-milestones-v8.json'),
        currentFeatureScope=ref('feature-scope-v23.json'),
        currentScenarios=ref('feature-scope-v21-scenarios.json'),
        restorationCoverage=ref('restoration-coverage-v14.json'),
        currentCounts=copy.deepcopy(coverage['counts']),
        restorationTaskGroups=tasks,
        supportOperations=copy.deepcopy(coverage['supportOperations']),
        sharedGoalConsumerRelations=copy.deepcopy(coverage['sharedGoalConsumerRelations']),
        unresolvedScope=copy.deepcopy(coverage['unresolvedScope']),
        analysisStageDecisionRef=ref('analysis-stage-decisions-v3.json'),
        modeOwnershipOverlay=ref('archive-mode-ownership.json'),
        legacyEntryDispositionOverlay=ref('legacy-entry-dispositions.json'),
        fullAnalysisCompleted=False, implementationCompleted=False,
        originalCriteriaStatusChanged=False,
        currentStatus='current-published-scope-aligned-analysis-still-incomplete')
    milestones['historicalRestorationDecisions'] = milestones.pop('restorationDecisions')
    milestones['restorationDecisions'] = [dict(id='RD9-01',
        decision='Use all 340 definitions and 45 owners from the current coverage. Final scope acceptance depends on every owner and unresolved-scope disposition.',
        evidence=[ref('restoration-coverage-v14.json'), ref('feature-scope-v23.json')],
        affectedTasks=['W09'] + task_ids, implementationStarted=False)]
    milestones['nextAnalysisActions'] = [dict(id='NEXT-01',
        question='Publish the three saved cloud-environments, personalization and codex-micro selections as bounded operation contracts.',
        inputs=['.analysis-local/settings-final-batch15-work', 'restoration-coverage-v14.json'],
        exit='Operations, state changes, delegated interfaces and verification conditions are recorded; no new page families or whole-program reparse.'),
        dict(id='NEXT-02', question='Resolve architecture-changing gaps against SD-01 through SD-06, then audit the original nine criteria.',
        inputs=['analysis-stage-decisions-v3.json', 'browser-clone-route-qualification.json',
                'public-history-duplicate-comparison.json', 'desktop-access-publication.json'],
        exit='Each architectural choice is supported or remains explicitly open with a precise evidence condition. Unknown classifications and future implementation tests are not required to be mechanically zero.')]
    milestones['investigationRule'] = ('Reuse saved contracts. Before selecting more code, name the affected SD issue, the architectural or scope decision, and its closure condition. '
        'Do not repeat settled parsing or grow page families. Runtime, build and full regression acceptance remain implementation gates. Additional model submissions have no remaining authorization.')
    for row in milestones['analysisMilestones']:
        row['evidencePaths'] += [name for name in ['feature-scope-v23.json', 'restoration-coverage-v14.json',
            'analysis-stage-decisions-v3.json'] if name not in row['evidencePaths']]
        if row['id'] == 'A1':
            row['currentUnresolved'] = dict(scope['counts'], pendingSettingsOperationContainers=3)
    final_dependencies = ['W08'] + task_ids
    for row in milestones['foundationTasks']:
        if row['taskId'] == 'W09':
            for key in ['dependsOn', 'sourcePreparationDependsOn', 'integrationDependsOn']:
                row[key] = final_dependencies.copy()
            row['evidence'] = [ref('feature-scope-v23.json'), ref('restoration-coverage-v14.json')]
    previous_preparation = {row['id']: row for row in old['sourcePreparationTasks']}
    preparation = []
    for index, task in enumerate(tasks):
        row = copy.deepcopy(previous_preparation.get(task['taskId'], old['sourcePreparationTasks'][0]))
        row.update(id=task['taskId'], taskRef=dict(ref('restoration-coverage-v14.json'), jsonPointer=f'/taskGroups/{index}'))
        preparation.append(row)
    milestones['sourcePreparationTasks'] = preparation
    for key in ['sourcePreparationGraph', 'integrationGraph']:
        graph = [copy.deepcopy(row) for row in old[key] if row['id'].startswith('W')]
        next(row for row in graph if row['id'] == 'W09')['dependsOn'] = final_dependencies.copy()
        graph += (copy.deepcopy(preparation) if key == 'sourcePreparationGraph' else
                  [dict(id=task['taskId'], dependsOn=task['dependsOn']) for task in tasks])
        dag(graph)
        milestones[key] = graph
    dump(OUT / 'implementation-milestones-v9.json', milestones)

    plan = (OUT / 'implementation-plan-v8.md').read_text()
    plan = plan.replace('版本 8', '版本 9').replace('feature-scope-v17', 'feature-scope-v23')
    # The scenario snapshot does not share the scope ledger's version number.
    plan = plan.replace('feature-scope-v23-scenarios', 'feature-scope-v21-scenarios')
    plan = plan.replace('功能台账 v17', '功能台账 v23').replace('restoration-coverage-v8', 'restoration-coverage-v14')
    plan = plan.replace('恢复覆盖表 v8', '恢复覆盖表 v14').replace('implementation-milestones-v8', 'implementation-milestones-v9')
    plan = plan.replace('274项', '340项').replace('278项', '344项').replace('64项', '103项').replace('919条', '1117条')
    plan = plan.replace('33个', '45个').replace('T01至T33', 'T01至T45').replace('全部33个', '全部45个')
    plan = plan.replace('旧版计划中的103项定义及T01至T16排程由本版替代。',
        '本版统一v8计划之后已发布的范围；未开始客户端实现，也未增加分析或行为通过项。')
    plan = plan.replace('六项共享消费者关系', '十项共享消费者关系')
    table = ['| 任务 | 定义数 | 第一方主模块 | 真实集成依赖 |', '| --- | --- | --- | --- |']
    for task in tasks:
        table.append(f"| {task['taskId']} {task['name']} | {len(task['featureIds'])} | `{task['primaryModule']}` | {', '.join(task['dependsOn'])} |")
    plan, changes = re.subn(r'\| 任务 \| 定义数 \|.*?(?=\n\nGeneral与Agent)', '\n'.join(table), plan, flags=re.S)
    assert changes == 1
    unresolved = '''## 未完成范围与分析出口

45个已发现设置容器中42个有局部操作合同；cloud-environments、personalization、codex-micro的源码选择已保存，尚待归并为操作与恢复规格。本版未把选择源码计为完成页面分析。保留12项关联待办、3项交叉重叠及全部其他所需能力，完整产品分母未知。

340项定义中shared 1、unknown 339，确认ChatGPT整项排除0。未知归属合法保留；拟删除分支仍须核对模式条件、消费者及共享依赖。不能以认证家族、文件名或设置页名称替代产品模式判定。[归档共享消费者证据](archive-mode-ownership.json)与[账户访问边界](desktop-access-publication.md)分别约束模式和访问条件。

968条旧入口原ID全部保留：235条资源／命令声明为已确认非用户操作来源，6条注册调用已确认callee，1条保留部分功能容器关联，726条角色待定；967条仍无功能映射。来源角色、功能映射和完整行为链是不同计数，不能互相充抵。详见[逐ID处置](legacy-entry-dispositions.md)。

先交付上述三个已选设置合同，再依[六组未决问题及关闭条件](analysis-stage-decisions-v3.json)核对会改变架构的未知：独立运行时和native来源、后台provider／receiver、数据与认证边界及主要行为差异。浏览器clone需求已经有[合同与候选路线](browser-clone-route-qualification.md)和[公共历史复制对照](public-history-duplicate-comparison.md)，复用这些结果，只调查仍缺的后效与实现来源。

新增选择必须指出影响哪个范围或架构决定，以及停止调查的证据条件。未知分类数量无需机械归零；独立客户端构建、打包和全部产品回归在实施阶段完成。会改变完整范围或架构的未知仍不得宣称关闭。

'''
    plan, changes = re.subn(r'## 未完成范围与分析出口\n.*?(?=## 行为验收与升级)', unresolved, plan, flags=re.S)
    assert changes == 1
    plan = plan.replace('结构和排程已对齐当前证据；完整功能分母、模式、运行时资格和主要行为缺口继续待关闭。',
        '本版只消除已发布功能台账与实施排程的脱节。AC-09中的范围排程子步骤已同步；目录与边界决定、运行时可行性、主要行为及其他原标准仍按当前证据逐项审计，未提升完成状态。')
    (OUT / 'implementation-plan-v9.md').write_text(plan)
    validation = dict(passed=True, featureDefinitions=340, uniqueOwningTasks=45,
        linkedUnexecutedSpecifications=1117, preparationGraphNodes=len(milestones['sourcePreparationGraph']),
        integrationGraphNodes=len(milestones['integrationGraph']), bothGraphsAcyclic=True,
        finalAcceptanceDependsOnEveryTask=True, modeCounts=coverage['counts']['modeCounts'],
        originalCriteriaStatusChanged=False, modelSubmissionsAdded=0, originalClientRunsAdded=0,
        clientImplementationStarted=False)
    dump(WORK / 'validation.json', validation)
    provenance = dict(baselineId=state['baselineId'], recordedAtUtc=now,
        method='Reconcile already published task ownership and dependency graphs; no new source parsing or runtime execution.',
        inputPins=pins, previousStateSha256=hashlib.sha256((WORK / 'state-before.json').read_bytes()).hexdigest(),
        script=dict(path=str(pathlib.Path(__file__).relative_to(ROOT)),
            sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()),
        outputs=[ref('implementation-plan-v9.md'), ref('implementation-milestones-v9.json')],
        validation=validation, fullAnalysisCompleted=False)
    dump(OUT / 'restoration-plan-v9-provenance.json', provenance)
    state['updatedAtUtc'] = now
    state['stageDecisions']['latestConsolidation'] = dict(
        plan=ref('implementation-plan-v9.md'), milestones=ref('implementation-milestones-v9.json'),
        coverage=ref('restoration-coverage-v14.json'), buildInputs=ref('build-input-dispositions-v1.json'),
        provenance=ref('restoration-plan-v9-provenance.json'), finiteFeatureDefinitions=340,
        productSpecificationsUnexecuted=1117, restorationTaskGroups=45,
        sourcePreparationAndIntegrationGatesSeparated=True, fullAnalysisCompleted=False,
        clientImplementationStarted=False)
    state['stageDecisions']['currentPlanOverlay'] = dict(plan=ref('implementation-plan-v9.md'),
        qualification='AC-09 current-scope scheduling substep aligned; remaining architecture and original nine criteria are not marked complete.')
    dump(OUT / 'analysis-state.json', state)
    for path in [ROOT / 'README.md', OUT / 'report.md', OUT / 'gaps.md']:
        text = path.read_text()
        text = text.replace('[当前实施计划草案](analysis/codex-26.1007.30912-c5b273322a83/implementation-plan-v8.md)',
            '[当前实施计划草案](analysis/codex-26.1007.30912-c5b273322a83/implementation-plan-v9.md)')
        text = text.replace('[当前统一实施计划](implementation-plan-v8.md)', '[当前统一实施计划](implementation-plan-v9.md)')
        if path.name in ['report.md', 'gaps.md']:
            first, body = text.split('\n', 1)
            text = first + '\n\n[实施计划v9](implementation-plan-v9.md)已同步当前340项功能、45个任务组和1117条未执行规格；最终验收依赖全部45组。此更新修正排程滞后，未增加行为通过项或提升原九项标准。历史阶段表中的v8计划滞后问题以本条更新为准。\n' + body
        path.write_text(text)
    for item in pins:
        assert ref(item['path']) == item, item['path']
    for name in ['implementation-plan-v9.md', 'implementation-milestones-v9.json', 'restoration-plan-v9-provenance.json']:
        (OUT / name).chmod(0o444)
    print(json.dumps(validation, ensure_ascii=False))


if __name__ == '__main__':
    main()
