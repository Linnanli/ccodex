"""Consolidate existing evidence against the unchanged plan; no target scan or launch."""
import copy
import csv
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/analysis-convergence-v4-work'
RAW = OUT / 'raw/analysis-convergence-v4'
PLAN = ROOT / 'docs/reverse-engineering/analysis-plan.md'


def read(p):
    return json.loads(p.read_text())


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pin(p):
    return {'path': str(p.relative_to(OUT)) if p.is_relative_to(OUT) else str(p.relative_to(ROOT)),
            'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())}


def save(p, obj):
    with p.open('x') as stream:
        stream.write(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def levels(graph):
    remaining = {x['id']: set(x['dependsOn']) for x in graph}
    assert len(remaining) == len(graph)
    assert all(v <= remaining.keys() for v in remaining.values())
    done, batches = set(), []
    while remaining:
        ready = sorted(k for k, v in remaining.items() if v <= done)
        assert ready, 'Cyclic restoration dependencies'
        batches.append(ready)
        done.update(ready)
        for item in ready:
            del remaining[item]
    return batches


# R means the stated record/proposal obligation has bounded evidence. It is not
# a complete feature, mode, runtime, package compatibility or product-pass claim.
REQUIREMENTS = {
 '1.1': ('R', '版本、构建、入口、架构及Owl身份已记录；实际ABI和独立运行时来源仍未知。', ['baseline.json', 'runtime-distribution.json', 'runtime-node-version-summary.md']),
 '1.2': ('R', '继承冻结副本与原归档/副本哈希复核；7项unpacked声明矛盾保留，本轮不重扫全部原始字节。', ['baseline.json', 'baseline-reverification.json', 'files.json']),
 '1.3': ('R', '归档内外文件及native/Wasm/可执行类别分别登记，不把识别当源码可构建证明。', ['files.json', 'native-runtime.json', 'dependency-summary.json']),
 '1.4': ('R', '限定扩展的17848输入扫描完成；11316条map指令指向冻结输入中缺失文件，sourcesContent覆盖0。', ['source-maps.json', 'source-map-validation.json']),
 '1.5': ('R', '30个缺失引用、21个独立路径已有补齐职责和验收建议，实施数0。', ['build-inputs.json', 'build-input-dispositions-v1.json']),
 '2.1': ('P', '发现域有登记，尚有726条旧来源角色、12项关联与3项重叠未收口；完整功能分母不能成立。', ['feature-scope-v25.json', 'legacy-entry-dispositions.json', 'entry-family-map.json']),
 '2.2': ('P', '任务、审批、文件、终端、项目及系统集成均有调查合同；设置清单373项不能覆盖全部非设置功能。', ['core-feature-scope.json', 'terminal-feature-contracts.json', 'file-change-view-contracts-v2.json']),
 '2.3': ('R', '373项有限定义均有唯一稳定ID和名称；不称完整产品分母。', ['feature-scope-v25.json']),
 '2.4': ('R', '373项均保留操作成员及触发描述/来源合同；这些是源码入口记录，不是已挂载界面。', ['feature-scope-v25.json']),
 '2.5': ('P', '输入、状态、失败与取消已有局部合同及规格；主要流程真实后效与部分委托实现未闭合。', ['feature-scope-v25.json', 'feature-scope-v24-scenarios.json', 'behavior-stop-restart.json']),
 '2.6': ('R', '373项均保留条件字段和未求值说明，平台/账号/开关的实际取值不据此确认。', ['feature-scope-v25.json', 'settings-feature-entry-conditions.json']),
 '2.7': ('R', '模式枚举完整登记：shared 1、unknown 372；未知合法保留，但这不关闭模式边界调查。', ['feature-scope-v25.json', 'chat-branch-decisions.json']),
 '2.8': ('P', '每项有来源和拟议职责，仍有真实provider、receiver、持久化及服务后效断点。', ['restoration-coverage-v16.json', 'thread-resume-entry-contracts.json']),
 '2.9': ('R', '功能保留源码/元数据引用和静态、行为、待验证状态；引用完整性另由本批回读检查。', ['feature-scope-v25.json', 'restoration-coverage-v16.json']),
 '2.10': ('R', '1216条规格记录前置、动作和期望；它们全部未执行，不计产品通过。', ['feature-scope-v24-scenarios.json']),
 '3.1': ('R', '包元数据、公开候选与条件性引入建议分列；未知未修改状态没有被提升为已确认。', ['dependencies.csv', 'dependency-summary.json', 'upstream-comparison.json']),
 '3.2': ('R', '17个内嵌提示及选定React/Sentry等接口边界有记录；按依赖导入而非导出其实现。', ['dependencies.csv', 'dependency-import-decisions.json']),
 '3.3': ('R', '安装/声明/通知候选及多版本分列，不能用根声明替代实际锁定版本。', ['dependency-summary.json', 'dependencies.csv']),
 '3.4': ('P', 'node-pty/objc等修改或候选边界有证据，其他unknown修改与fork适配仍需来源和消费者确认。', ['node-pty-modification-contracts.json', 'objc-independent-build-summary.md', 'dependency-import-decisions.json']),
 '3.5': ('P', '私有包、Owl和服务来源缺口已列出；独立取得/完整替代的可行性仍影响架构。', ['dependencies.csv', 'runtime-distribution.json', 'app-host-maintenance-summary.md']),
 '3.6': ('P', 'native/Wasm/辅助组件版本、平台及接口有独立记录；ABI、独立运行时和若干组件构建路线未闭合。', ['native-runtime.json', 'runtime-surface-disposition.json', 'objc-independent-build-summary.md']),
 '3.7': ('R', '202行保留版本依据、来源、许可线索、用途、模式和引入建议；本批给全部202行接上明确调查动作，未知结论不变。', ['dependencies.csv', 'dependency-investigation-actions-v1.json']),
 '4.1': ('P', 'main/preload/renderer/worker入口和局部生命周期有图与合同，全部辅助进程及保留功能生命周期闭包尚未证明。', ['boundaries.json', 'ipc.json', 'preload-app-host-summary.md', 'app-host-maintenance-summary.md']),
 '4.2': ('P', '中央分发、chunk、MessagePort和局部请求契约有来源；实际接收方、超时/取消后效仍有断点。', ['ipc.json', 'host-message-contracts.json', 'request-wrapper-contracts.json', 'approval-response-wire-contracts.json']),
 '4.3': ('P', '路由、模式、globalState与退出保存有局部状态所有权合同，完整持久化/恢复和所有功能接入未证明。', ['route-contracts.json', 'global-state-storage-origin.json', 'shutdown-persistence.json']),
 '4.4': ('P', 'app-server、HTTP、resolver、socket及native边界有分列；不能因方法同名将其合并为公开后台。', ['request-wrapper-contracts.json', 'application-network-summary.md', 'environment-extension-contracts.json']),
 '4.5': ('P', '动态导入、通道计算与闭包有定向补充，完整保留依赖闭包和副作用仍未形成全域结论。', ['route-contracts.json', 'request-wrapper-contracts.json', 'settings-di-source-summary.md']),
 '4.6': ('R', '整Program/作用域和精确字节映射已有实际产物；最新四Program定向结果仍是有限语义范围。', ['runtime-feature-policy-contracts.json', 'runtime-api-contracts.json']),
 '4.7': ('P', '固定公开CLI的764文件/466方法变体比较和有限运行差异已有证据；实际provider绑定及11组有效契约差异的采用决定未全闭合。', ['exported-protocol-comparison.json', 'command-backend-comparison.json', 'fork-negative-protocol-comparison.json']),
 '5.1': ('P', '一个自有只读任务完成/重开及另一执行中停止重启有观察；不能推广到全部主要功能链。', ['behavior-checks.md', 'behavior-stop-restart.json']),
 '5.2': ('P', '完成与interrupted重开分别记录；取消未测、自动续跑未证明，失败/审批/PTY等主要行为仍不完整。', ['behavior-stop-restart.json', 'behavior-checks.md']),
 '5.3': ('R', '未观察条件、保留功能和未来具体场景均有登记；本批不新增模型任务或个人数据读取。', ['feature-scope-v24-scenarios.json', 'behavior-stop-restart.json']),
 '6.1': ('R', '进程、状态所有权与共享关系支持目录/包边界建议；它们是拟维护设计，不是还原的原作者目录。', ['implementation-plan-v9.md', 'module-boundary-proposals.json', 'source-contract-module-proposals.json']),
 '6.2': ('P', '438条发布文件记录和局部逻辑模块映射并存；职责、导出、第三方边界等尚无覆盖全部保留功能的统一模块表。', ['modules.json', 'module-boundary-proposals.json', 'restoration-coverage-v16.json']),
 '6.3': ('P', '3组Chat专属分支决定、1项Codex正向保留及1项共享归属已有证据；整项排除0，完整剥离范围未闭合。', ['chat-branch-decisions.json', 'archive-mode-ownership.json', 'product-flow-ownership.json']),
 '6.4': ('P', '第三方引入和native/provider职责有建议，Owl独立来源及若干底层等价效果仍未知。', ['dependency-investigation-actions-v1.json', 'runtime-feature-policy-contracts.json', 'runtime-distribution.json']),
 '6.5': ('R', '30项构建输入有处置；公开app-server的候选范围与差异、采用前置条件明确列出。实际补齐和服务接入属于实施。', ['build-input-dispositions-v1.json', 'exported-protocol-comparison.json', 'implementation-plan-v9.md']),
 '6.6': ('R', '本批把373项/48任务接入源码准备与真实集成两套57节点无环图；完整产品分母仍未知，全部产品验收未开始。', ['restoration-current-ordering-v1.json', 'restoration-coverage-v16.json']),
 '6.7': ('R', '新基线、协议/依赖/行为差异、模块/回归映射及迁移回退有升级建议；升级实测属于实施期。', ['implementation-plan-v9.md', 'chat-branch-decisions.json']),
}

CRITERIA = {
 'AC-01': ('R', '固定输入与公开候选版本分列；冻结复核的7个声明矛盾继续保留，未混用版本。', ['baseline.json', 'baseline-reverification.json', 'runtime-distribution.json'], []),
 'AC-02': ('P', '24895条归档/磁盘清单记录分别登记；373项有限定义/48任务已对齐。726条旧来源角色、12关联和3重叠仍待处置，完整分母未知。', ['files.json', 'feature-scope-v25.json', 'legacy-entry-dispositions.json'], ['SD-01']),
 'AC-03': ('P', 'shared 1、unknown 372；3组分支级Chat专属决定和Codex正向保留已有证据，整项排除0。未知无需机械归零，影响保留范围的共享闭包仍须查明。', ['feature-scope-v25.json', 'chat-branch-decisions.json', 'archive-mode-ownership.json'], ['SD-01']),
 'AC-04': ('P', '373项均有任务、拟议模块、来源及规格；实际provider/receiver和部分委托/原生/存储断点仍影响架构。438发布文件记录不是完整逻辑模块清单。', ['restoration-coverage-v16.json', 'modules.json', 'thread-resume-entry-contracts.json', 'runtime-feature-policy-contracts.json'], ['SD-02', 'SD-03', 'SD-05']),
 'AC-05': ('R', '202项依赖的版本/来源依据与未知分列；补齐185行原空白的显式调查动作，17行原动作保留。没有新增版本或修改状态确认。', ['dependencies.csv', 'dependency-investigation-actions-v1.json', 'dependency-import-decisions.json'], ['SD-02']),
 'AC-06': ('R', 'native/Wasm/辅助程序/Owl/私有服务分别登记；这项记录义务不证明独立运行时来源、ABI或源码构建已取得资格。', ['native-runtime.json', 'runtime-distribution.json', 'runtime-surface-disposition.json', 'environment-extension-contracts.json'], ['SD-02']),
 'AC-07': ('R', 'source map、30项缺失输入、REA限制和动态未知有范围说明；本批未重跑工具或宣称未知关系清零。', ['source-maps.json', 'build-input-dispositions-v1.json', 'rea-application-observed.run.json', 'runtime-api-contracts.json'], []),
 'AC-08': ('P', '完成/重开及执行中停止重启有实际观察；执行中取消未测、自动续跑未证明。源码回放/公开运行时探针及1216条未执行规格不计产品通过。', ['behavior-checks.md', 'behavior-stop-restart.json', 'feature-scope-v24-scenarios.json'], ['SD-04']),
 'AC-09': ('P', '当前373项、48任务的排序已接到两套57节点依赖图；目录和升级方法有依据。完整模块/模式范围和运行时/后台决定仍缺证据，不能宣称最终方案已闭合。', ['restoration-current-ordering-v1.json', 'implementation-plan-v9.md', 'restoration-coverage-v16.json', 'runtime-distribution.json'], ['SD-01', 'SD-02', 'SD-03', 'SD-05', 'SD-06']),
}


def dependency_actions(rows):
    result = []
    for row in rows:
        inherited = json.loads(row['investigationActions']) if row['investigationActions'] else []
        actions = copy.deepcopy(inherited)
        if not inherited:
            if not row['version'] or 'unresolved' in row['versionBasis']:
                actions.append({'field': 'actualVersion', 'action': f"从{row['name']}本行冻结声明/manifest及实际调用绑定确定被消费的包实例与精确版本；notice和声明范围仅作候选。若发布输入不足，记录所需锁文件/发行来源，不猜测版本。"})
            if row['classification'] in ['first-party-private-candidate', 'third-party-private-vendor']:
                actions.append({'field': 'privateSourceAndIntegration', 'action': f"依据本行{row['sourcePath']}及{row['name']}调用接口取得独立源码/分发与构建条件；不可取得时，列出完整接口和保留消费者后评估自有适配，不能复制原安装目录充当独立依赖。"})
            else:
                actions.append({'field': 'upstreamAndModification', 'action': f"对{row['name']}本行已记录版本或明确候选，核验官方发行来源与完整性，再比较保留消费者实际需要的导出和行为；将修改、多版本或bundle变换分别记录，不以包名/元数据判定未修改。"})
            if 'native' in row['recommendedIntegration']:
                actions.append({'field': 'nativeBuild', 'action': f"对{row['name']}本行native接口确定源码、平台/架构、ABI和独立构建步骤；重建后验证调用与释放，不用预编译文件存在代替可构建证据。"})
            if not row['license'] or row['license'] == '[]':
                actions.append({'field': 'license', 'action': f"从{row['name']}实际选定版本的发行物/上游来源核对许可证；归档notice候选不能证明本行许可范围。"})
            actions.append({'field': 'modeAndCaller', 'action': f"从本行sourcePath/locator及evidenceIds追踪{row['name']}的第一方封装和Codex共享消费者；只有明确产品模式条件与共享依赖闭包才允许排除。"})
        for action in actions:
            action.setdefault('status', 'pending; not executed by consolidation')
        result.append({'dependencyId': row['id'], 'name': row['name'], 'sourcePath': row['sourcePath'],
                       'sourceHash': row['sourceHash'], 'locator': json.loads(row['locator']),
                       'version': row['version'], 'versionBasis': row['versionBasis'],
                       'unresolved': json.loads(row['unresolved']), 'recommendedIntegration': row['recommendedIntegration'],
                       'evidenceIds': json.loads(row['evidenceIds']), 'actions': actions,
                       'actionBasis': 'inherited-explicit-actions-not-reassessed' if inherited else 'derived-from-this-row-existing-fields',
                       'confidence': 'inferred', 'investigationExecuted': False})
    return {'baselineId': BASE, 'source': pin(OUT / 'dependencies.csv'), 'rows': result,
            'counts': {'dependencyRows': len(rows), 'rowsWithInheritedExplicitActions': sum(bool(r['investigationActions']) for r in rows),
                       'rowsWithNewExplicitActions': sum(not r['investigationActions'] for r in rows),
                       'rowsWithExplicitActionsNow': len(result), 'versionOrModificationClaimsChanged': 0},
            'qualification': 'Action planning overlay only; original dependency records and unknown findings unchanged. No investigation performed and no package installed.'}


def current_ordering(old, coverage):
    tasks = coverage['taskGroups']
    ids = [t['taskId'] for t in tasks]
    old_preparation = {x['id']: x for x in old['sourcePreparationTasks']}
    preparation, integration = [], []
    for group, target in [('sourcePreparationGraph', preparation), ('integrationGraph', integration)]:
        for row in old[group]:
            if not row['id'].startswith('W'):
                continue
            item = copy.deepcopy(row)
            if row['id'] == 'W09':
                item['dependsOn'] = ['W08'] + ids
            target.append(item)
    for i, task in enumerate(tasks):
        task_ref = {**pin(OUT / 'restoration-coverage-v16.json'), 'jsonPointer': f'/taskGroups/{i}'}
        preparation.append({'id': task['taskId'],
                            'dependsOn': old_preparation[task['taskId']]['dependsOn'] if task['taskId'] in old_preparation else ['W01', 'W05', 'W06', 'W07'],
                            'taskRef': task_ref, 'confidence': 'inferred',
                            'qualification': 'Source/interface preparation only; native provider and all real integration prerequisites retained.'})
        integration.append({'id': task['taskId'], 'dependsOn': task['dependsOn'], 'taskRef': task_ref})
    return {'baselineId': BASE, 'sourcePlan': pin(OUT / 'implementation-milestones-v9.json'),
            'coverage': pin(OUT / 'restoration-coverage-v16.json'),
            'sourcePreparationGraph': preparation, 'integrationGraph': integration,
            'sourcePreparationLevels': levels(preparation), 'integrationLevels': levels(integration),
            'counts': {'features': len(coverage['features']), 'taskGroups': len(tasks),
                       'sourcePreparationNodes': len(preparation), 'integrationNodes': len(integration),
                       'scenarioSpecifications': coverage['counts']['productScenarioSpecifications']},
            'derivation': 'Existing W01-W09 and T01-T45 source-preparation policy retained. T46-T48 use the same W01/W05/W06/W07 design prerequisites as T30/T45, based on current sourceDesignCanProceed; current coverage supplies all real integration dependencies. W09 consumes every current task.',
            'qualification': 'Prospective ordering, not completed implementation, complete functional denominator or runtime adoption. Original M1-M7 integration acceptance remains required.',
            'allUnknownFeaturesRetained': True, 'implementationStarted': False}


def main():
    state = read(OUT / 'analysis-state.json')
    prior = read(OUT / 'analysis-stage-decisions-v3.json')
    old_stages = read(OUT / 'analysis-stage-decisions-v2.json')['stages']
    ledger = read(OUT / 'feature-scope-v25.json')
    coverage = read(OUT / 'restoration-coverage-v16.json')
    scenarios = read(OUT / 'feature-scope-v24-scenarios.json')
    modules = read(OUT / 'modules.json')
    dependencies = list(csv.DictReader((OUT / 'dependencies.csv').open()))
    plan_bytes = PLAN.read_bytes()
    assert sha(plan_bytes) == '48dd8b65348efd4a8b5634aac5341c4507c262e7b5c88e8ed9368c88eeb96db4'
    feature_ids = {x['featureId'] for x in ledger['features']}
    assert len(feature_ids) == 373 and len(coverage['taskGroups']) == 48
    assert {x['featureId'] for x in coverage['features']} == feature_ids
    assert {s['featureId'] for s in scenarios['scenarios']} == feature_ids
    assert len(scenarios['scenarios']) == 1216 and all(s.get('executionStatus', s.get('status')) == 'not-executed' for s in scenarios['scenarios'])
    owners = [f for t in coverage['taskGroups'] for f in t['featureIds']]
    assert set(owners) == feature_ids and len(owners) == len(feature_ids)
    assert all(x['name'] and x['operationMembers'] and x['conditions'] and x['scenarioIds'] for x in ledger['features'])
    assert len(dependencies) == 202
    actions = dependency_actions(dependencies)
    ordering = current_ordering(read(OUT / 'implementation-milestones-v9.json'), coverage)
    # Validate all quoted requirements before creating publication files.
    def plan_location(text):
        needle = text.encode()
        start = plan_bytes.find(needle)
        if start < 0:
            raise ValueError('Plan quote not found: ' + text)
        return {'sourcePath': str(PLAN.relative_to(ROOT)), 'sourceHash': sha(plan_bytes),
                'byteRange': {'start': start, 'endExclusive': start + len(needle)}, 'spanHash': sha(needle)}
    for phase in old_stages:
        for row in phase['requirements']:
            plan_location(row['requirement'])
            assert row['id'] in REQUIREMENTS
    assert sum(len(x['requirements']) for x in old_stages) == len(REQUIREMENTS) == 39
    for row in prior['criteria']:
        plan_location(row['requirement'])
    for names in [row[2] for row in REQUIREMENTS.values()] + [row[2] for row in CRITERIA.values()]:
        for name in names:
            assert name in ['dependency-investigation-actions-v1.json', 'restoration-current-ordering-v1.json'] or (OUT / name).is_file(), name
    WORK.mkdir(exist_ok=False)
    RAW.mkdir(exist_ok=False)
    save(WORK / 'state-before.json', state)
    shutil.copyfile(WORK / 'state-before.json', RAW / 'state-before.json')
    for name in ['report.md', 'gaps.md']:
        shutil.copyfile(OUT / name, RAW / (name + '.before'))
    shutil.copyfile(Path(__file__), RAW / Path(__file__).name)
    save(OUT / 'dependency-investigation-actions-v1.json', actions)
    save(OUT / 'restoration-current-ordering-v1.json', ordering)
    criteria, stages = [], []
    status_names = {'R': 'record-or-proposal-obligation-supported-with-limits', 'P': 'partial; material-analysis-work-remains'}
    for old in prior['criteria']:
        flag, finding, names, issues = CRITERIA[old['id']]
        criteria.append({'id': old['id'], 'requirement': old['requirement'], 'planLocator': plan_location(old['requirement']),
                         'status': status_names[flag], 'finding': finding, 'evidence': [pin(OUT / name) for name in names],
                         'remainingIssueIds': issues, 'implementationAcceptanceDeferred': old['implementationAcceptanceDeferred']})
    for phase in old_stages:
        rows = []
        for old in phase['requirements']:
            flag, finding, names = REQUIREMENTS[old['id']]
            rows.append({'id': old['id'], 'requirement': old['requirement'], 'planLocator': plan_location(old['requirement']),
                         'status': status_names[flag], 'finding': finding, 'evidence': [pin(OUT / name) for name in names]})
        stages.append({'number': phase['number'], 'deliveryStatus': 'partial' if any(x['status'].startswith('partial') for x in rows) else 'record-obligations-supported-with-limits', 'requirements': rows})
    journal_checks = []
    required = ['id', 'baselineId', 'claim', 'sourcePath', 'sourceHash', 'locator', 'method', 'confidence', 'verificationStatus']
    for name in ['evidence.jsonl', 'runtime-feature-policy-evidence.jsonl', 'request-entry-unmatched-review-evidence.jsonl']:
        rows = [json.loads(line) for line in (OUT / name).read_text().splitlines() if line.strip()]
        journal_checks.append({'path': name, 'records': len(rows),
                               'missingFields': {k: sum(k not in row for row in rows) for k in required},
                               'nonPlanConfidenceValues': dict(Counter(str(r.get('confidence')) for r in rows if r.get('confidence') not in ['confirmed', 'inferred', 'unresolved']))})
    next_action = {'issueId': 'SD-03', 'question': 'For the existing UI resumeConversation path and old raw resumeThread candidate, which exact provider/request descriptor and receiver are selected, and are their operations equivalent?',
                   'fixedInput': 'thread-resume-entry-contracts.json, request wrapper/facade contracts and their saved source selections; frozen sources only if a specific binding is missing.',
                   'closure': 'Locate both concrete provider/receiver chains and their request/notification/state effects, or give the exact unresolvable injection boundary. Classify the one existing queued operation without adding new features or redoing route discovery. Static closure is separate from actual service acceptance.',
                   'authorization': 'Offline analysis only; no new model submission, original-client launch, account mutation or client implementation.'}
    issues = [
        {'id': 'SD-01', 'status': 'open-internal', 'impact': '完整功能分母、ChatGPT剥离与共享依赖', 'evidence': ['feature-scope-v25.json', 'legacy-entry-dispositions.json', 'chat-branch-decisions.json'], 'remaining': '726角色待定、12关联、3重叠及影响保留边界的模式闭包；45设置容器局部合同已全部交付，不再列为缺口。', 'boundedResolution': '按已保存来源分组处置角色/关联/重复，保留unknown；每个拟排除分支独立核对Codex共享消费者。', 'externalPrerequisite': None},
        {'id': 'SD-02', 'status': 'open-mixed', 'impact': '独立运行时、native来源与完整能力', 'evidence': ['runtime-distribution.json', 'runtime-surface-disposition.json', 'runtime-feature-policy-contracts.json', 'browser-ownership-contracts.json', 'public-history-duplicate-comparison.json'], 'remaining': '17个已解析私有接口不是全部分母；两特性键、reset和predicate已收口，native效果、clone/lease、权限隔离、特权设置及更新等仍未取得完整独立实现资格。', 'boundedResolution': '复用现有差异与源码合同，逐能力明确可独立取得的provider/源码、所需行为及采用决定；不重复接口存在性探针。', 'externalPrerequisite': '适用Owl的独立发行/源码及构建来源，或足以实现全部保留能力的公开来源与原生行为证据；当前没有合格路线。'},
        {'id': 'SD-03', 'status': 'open-internal-and-service', 'impact': '实际provider/receiver及公开app-server采用范围', 'evidence': ['thread-resume-entry-contracts.json', 'request-wrapper-contracts.json', 'exported-protocol-comparison.json', 'fork-negative-protocol-comparison.json'], 'remaining': '公开导出差异11组、实际接收身份与通知后效尚未全闭合，npm二进制与公开提交绑定未知；UI resume与raw API仍有1项排队判定。', 'boundedResolution': next_action['closure'], 'externalPrerequisite': '成功路径实际服务/后台契约与发行来源；负例/schema等同不能代替。'},
        {'id': 'SD-04', 'status': 'open-validation', 'impact': '主要行为对照', 'evidence': ['behavior-checks.md', 'behavior-stop-restart.json', 'feature-scope-v24-scenarios.json'], 'remaining': '执行中取消未测；自动续跑未证明；失败、审批、PTY等主要路径缺实际观察。', 'boundedResolution': '保留每条未验证场景的前置、动作、预期和限制；仅在已获相应授权/环境时执行实际观察，源码回放不充抵。', 'externalPrerequisite': '需要新增模型任务的场景必须有新授权；当前剩余0。平台/服务相关场景还需匹配环境。'},
        {'id': 'SD-05', 'status': 'open-source-and-platform', 'impact': '独立数据、认证、持久化与迁移', 'evidence': ['global-state-storage-origin.json', 'main-persistence-policy.json', 'shutdown-persistence.json', 'mode-persistence-receiver.json'], 'remaining': 'globalState保存合同不能证明所有backend/native/账号数据均隔离；实际有效根目录、认证存储、异常退出和迁移边界仍需全域职责映射。', 'boundedResolution': '从已有store/owner/provider合同列出每个保留存储及认证来源的路径输入、权限、写入/迁移/退出责任和明确未验证条件；不读个人数据。', 'externalPrerequisite': '平台认证/密钥存储和真实驱动后效需受控自有环境；目录名称不同本身不能证明隔离。'},
        {'id': 'SD-06', 'status': 'open-design-integration', 'impact': '逻辑模块、证据格式、构建与升级依据', 'evidence': ['modules.json', 'restoration-current-ordering-v1.json', 'build-input-dispositions-v1.json', 'dependency-investigation-actions-v1.json'], 'remaining': '当前373/48排序已统一，30缺失输入有处置。438记录仍为发布文件；统一逻辑模块必要字段与部分旧journal格式仍需闭合。', 'boundedResolution': '将已审查职责/范围/导入导出/共享状态/副作用/第三方/拟议路径接成统一视图；缺证据显式unknown，保持原始journal并补具备来源的规范视图。运行时/后台决定继承SD02/03。', 'externalPrerequisite': '实际干净构建、安装、打包、平台ABI与升级回归属于后续实施验收，不要求本阶段伪造通过。'},
    ]
    for issue in issues:
        issue['evidence'] = [pin(OUT / name) for name in issue['evidence']]
    req_counts = dict(Counter(x['status'] for stage in stages for x in stage['requirements']))
    result = {'schemaVersion': 4, 'baselineId': BASE, 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
              'plan': pin(PLAN), 'previousSnapshot': pin(OUT / 'analysis-stage-decisions-v3.json'),
              'historicalStageRequirements': pin(OUT / 'analysis-stage-decisions-v2.json'),
              'reviewScope': 'Unchanged nine completion criteria, all 39 mapped plan requirements, six issue groups and explicit evidence/module format obligations. Existing artifacts only; no target rescan.',
              'criteria': criteria, 'stages': stages, 'remainingIssues': issues,
              'counts': {'completionCriteria': 9, 'satisfiedRecordOrScopeObligations': 4, 'partialCriteria': 5,
                         'stages': 6, 'requirementItems': 39, 'requirementStatusCounts': req_counts,
                         'currentFeatureDefinitions': 373, 'currentUnexecutedScenarios': 1216, 'currentRestorationTaskGroups': 48,
                         'remainingDecisionGroups': 6, 'modeCounts': dict(Counter(x['mode'] for x in ledger['features'])),
                         'confirmedWholeFeatureExclusions': 0, 'confirmedChatOnlyBranchDecisionGroups': 3,
                         'newOriginalSourceParses': 0, 'newReaRuns': 0, 'newModelSubmissions': 0, 'newOriginalClientLaunches': 0,
                         'newFeatureDefinitions': 0, 'newProductScenarioPasses': 0, 'newClientImplementation': 0},
              'dependencyActionOverlay': pin(OUT / 'dependency-investigation-actions-v1.json'),
              'currentOrdering': pin(OUT / 'restoration-current-ordering-v1.json'),
              'moduleInventoryAudit': {'records': len(modules), 'boundaryKind': 'published-file; not recovered logical module',
                                       'missingExplicitFields': {k: sum(k not in row for row in modules) for k in ['responsibility', 'exports', 'thirdPartyDependencies']},
                                       'qualification': 'Logical-module proposals and per-feature references supplement this inventory, but no complete unified required-field view is proved. Whole-file hashes/bytes are not logical module cuts.'},
              'selectedJournalSchemaAudit': journal_checks,
              'crossCuttingRequirements': [
                  {'id': 'X-01', 'requirement': '完整固定基线Codex范围；最小流程只是实施中间里程碑', 'status': 'partial', 'evidence': 'SD-01, AC-02/04; 373 finite definitions retained, complete denominator unknown'},
                  {'id': 'X-02', 'requirement': '仅排除ChatGPT专属；保留Codex共享依赖', 'status': 'partial', 'evidence': 'SD-01, AC-03; three bounded branch decisions, zero whole-feature exclusions'},
                  {'id': 'X-03', 'requirement': '第三方实现通过依赖引入，临时分析副本与维护源码分开', 'status': 'proposal-and-analysis-boundary-supported', 'evidence': 'AC-05/06; no client code or third-party implementation generated by this batch'},
                  {'id': 'X-04', 'requirement': '独立标识/目录、干净构建打包及升级，无原安装路径依赖', 'status': 'analysis-route-partial; implementation-acceptance-deferred', 'evidence': 'SD-02/05/06; ordering does not prove a qualified runtime or build'},
                  {'id': 'X-05', 'requirement': '结论可回溯且证据记录具备计划九字段与规定confidence', 'status': 'partial', 'evidence': 'selectedJournalSchemaAudit; known producer deviations retained, no blanket normalization/equivalence claimed'},
                  {'id': 'X-06', 'requirement': '模块清单职责/环境/模式/范围/导入导出/状态/副作用/第三方/拟议路径齐备', 'status': 'partial', 'evidence': 'moduleInventoryAudit; scoped proposals do not establish complete logical module inventory'},
                  {'id': 'X-07', 'requirement': '分别统计发现、分类、分析、验证、排除、未知并保留分母', 'status': 'bounded-counts-supported', 'evidence': 'counts + current ledger/coverage; file entries, source roles, functional mapping, branch decisions and runtime observations counted separately'},
              ],
              'interpretation': ['R supports the specific record/proposal obligation with stated limits; it is not product completion.',
                                 'Unknown mode/version/platform values may remain explicit, but architecture-changing gaps stay open.',
                                 'All 1216 implementation specifications are unexecuted; analysis exit does not require executing them all.',
                                 'No independent client implementation/build is claimed or required as a substitute for the current analysis deliverable.',
                                 'Original plan is unchanged. Current scope overlays supersede historical 340/45 counts without overwriting old snapshots.'],
              'nextAction': next_action, 'fullAnalysisCompleted': False, 'clientImplementationStarted': False}
    names = sorted({name for row in REQUIREMENTS.values() for name in row[2]} | {name for row in CRITERIA.values() for name in row[2]} |
                   {'analysis-stage-decisions-v2.json', 'analysis-stage-decisions-v3.json', 'entry-family-map.json', 'request-entry-unmatched-review-evidence.jsonl', 'evidence.jsonl', 'runtime-feature-policy-evidence.jsonl'})
    result['inputPins'] = [pin(OUT / name) for name in names] + [pin(RAW / 'state-before.json')]
    save(OUT / 'analysis-stage-decisions-v4.json', result)
    table = '\n'.join(f"| {row['id']} | {'资料/范围义务有交付' if row['status'].startswith('record') else '部分完成'} | {row['finding']} |" for row in criteria)
    req_table = '\n'.join(f"| {row['id']} | {'有限记录/建议有证据' if row['status'].startswith('record') else '仍有分析缺口'} | {row['finding']} |" for stage in stages for row in stage['requirements'])
    issue_table = '\n'.join(f"| {row['id']} | {row['impact']} | {row['remaining']} | {row['boundedResolution']} |" for row in issues)
    summary = f'''# 原计划分析退出条件复核 版本4

本次只汇总既有产物，逐项复核原计划九项标准、39条映射要求和六组未决问题。完整分析尚未完成；四项资料/范围义务有交付，五项仍部分完成。R类记录只证明对应资料或建议已形成，不表示功能、依赖兼容或产品通过。

当前有限范围是373项功能定义、377项用户操作、116项支撑、48个恢复任务和1216条未执行规格。45个设置容器的局部操作合同已全部交付。shared 1、unknown 372；已有3组分支级Chat专属决定，整项功能排除0。完整产品分母未知，所有未知能力继续保留。

本批修正两处具体脱节：依赖清单202行中只有17行原有显式调查动作，已为其余185行补[逐行调查动作表](dependency-investigation-actions-v1.json)，没有改变版本/修改状态；当前373项/48任务已接入[两套57节点依赖图](restoration-current-ordering-v1.json)，W09覆盖全部任务，旧v9快照保留。源码准备和真实集成仍分别验收。

| 原标准 | 状态 | 当前证据结论 |
| --- | --- | --- |
{table}

## 会改变范围或架构的剩余问题

| 问题 | 影响 | 仍缺什么 | 有限关闭动作 |
| --- | --- | --- | --- |
{issue_table}

独立Owl/适用native来源、实际服务行为、匹配平台和新增模型样例授权是各自的外部前置条件；当前模型样例剩余0。内部源码问题仍可推进，因此本次不把整个目标标为blocked。普通Electron直接替换已被固定对照否定，第一方适配/运行时候选尚未取得完整资格。

## 六阶段39条要求

这些编号沿用旧审计对计划段落、表格字段和项目的映射，不声称原文全部采用同样编号。每条原文的精确字节定位与证据pin见[结构化复核](analysis-stage-decisions-v4.json)。

| 要求 | 本次判断 | 范围与限制 |
| --- | --- | --- |
{req_table}

## 格式与实施边界

438条modules.json记录仍是发布文件；职责、导出和第三方依赖没有统一显式字段。局部模块建议可以复用，不能代替完整逻辑模块清单。选定旧journal仍有计划字段或confidence枚举偏差，原记录保留；本次没有靠填猜测值或修改原证据宣称格式完成。

本批没有新REA运行、目标源码解析、原客户端启动、模型提交、功能定义、产品通过或客户端实现。12条最新运行时特性源码回放、公开运行时探针和1216条实施规格均不能充抵真实产品验收。实际独立构建、打包及全部回归属于后续实施；仍会改变架构的未知不能因此计为完成。

下一步限定为现有UI resumeConversation与旧raw resumeThread的provider/request descriptor/receiver及效果关系，处置唯一排队操作；不重做路由发现、不增加功能条目。该问题的静态结论与实际后台接受分别记录。
'''
    with (OUT / 'analysis-stage-decisions-v4.md').open('x') as stream:
        stream.write(summary)
    records = []
    for row in criteria:
        source = row['evidence'][0]
        records.append({'id': 'ACV4-' + row['id'], 'baselineId': BASE, 'claim': row['finding'],
                        'sourcePath': source['path'], 'sourceHash': source['sha256'], 'locator': {'kind': 'analysis-artifact-whole-file', 'bytes': source['bytes']},
                        'method': 'existing-analysis-artifact-review; not new target-source evidence', 'confidence': 'inferred',
                        'verificationStatus': row['status'], 'supportingArtifacts': row['evidence'], 'planLocator': row['planLocator']})
    with (OUT / 'analysis-stage-decisions-v4-evidence.jsonl').open('x') as stream:
        stream.write(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in records))
    after = copy.deepcopy(state)
    after['updatedAtUtc'] = datetime.now(timezone.utc).isoformat()
    stage = after['stageDecisions']
    stage['decisions'], stage['summary'] = pin(OUT / 'analysis-stage-decisions-v4.json'), pin(OUT / 'analysis-stage-decisions-v4.md')
    stage['provenance'] = {**pin(OUT / 'analysis-stage-decisions-v4.json'), 'qualification': 'Exact plan locators, current evidence pins, all 39 requirements and scope/format qualifications embedded.'}
    stage['counts'] = result['counts']
    stage['nextAction'] = next_action
    stage['latestConvergence'] = {'audit': pin(OUT / 'analysis-stage-decisions-v4.json'), 'ordering': pin(OUT / 'restoration-current-ordering-v1.json'), 'dependencyActions': pin(OUT / 'dependency-investigation-actions-v1.json')}
    after['analysisRequirementsCurrentAudit'] = {'path': 'analysis-stage-decisions-v4.json', 'sha256': sha((OUT / 'analysis-stage-decisions-v4.json').read_bytes()),
                                               'completionCriteria': 9, 'phases': 6, 'requirementItems': 39, 'fullAnalysisCompleted': False,
                                               'scope': 'Current nine criteria, all 39 plan requirements, six issue groups and bounded format checks; historical audits retained.'}
    after['dependencyInvestigationActions'] = pin(OUT / 'dependency-investigation-actions-v1.json')
    after['currentRestorationOrdering'] = pin(OUT / 'restoration-current-ordering-v1.json')
    after['pending'] = [f"{x['id']}: {x['remaining']}" for x in issues]
    assert read(OUT / 'analysis-state.json') == state
    (OUT / 'analysis-state.json').write_text(json.dumps(after, ensure_ascii=False, indent=2) + '\n')
    for name in ['report.md', 'gaps.md']:
        note = '当前分析出口以[九标准/39要求复核v4](analysis-stage-decisions-v4.md)为准：373项/48任务已统一排序，202行依赖均接有调查动作；四项记录义务有交付、五项部分完成。六组架构/范围问题及旧模块/journal格式缺口明确保留，目标仍未完成。下文保留历次分析叙述，其旧数量和后续动作按本次复核更新。\n\n'
        (OUT / name).write_text(note + (RAW / (name + '.before')).read_text())
    for p in [OUT / 'analysis-stage-decisions-v4.json', OUT / 'analysis-stage-decisions-v4.md', OUT / 'analysis-stage-decisions-v4-evidence.jsonl', OUT / 'dependency-investigation-actions-v1.json', OUT / 'restoration-current-ordering-v1.json'] + [p for p in RAW.rglob('*') if p.is_file()]:
        p.chmod(0o444)
    print(json.dumps({'counts': result['counts'], 'dependencyActions': actions['counts'], 'ordering': ordering['counts'], 'fullAnalysisCompleted': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
