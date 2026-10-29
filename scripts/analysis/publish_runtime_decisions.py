"""Publish four capability decisions and the bounded source review behind them."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import shutil

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASELINE
WORK = ROOT / '.analysis-local/runtime-decisions-work'
RAW = OUT / 'raw/runtime-decisions'
NAMES = ['runtime-capability-decisions.json', 'runtime-capability-decisions.md',
         'runtime-capability-decisions-provenance.json']


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def pin(path):
    data = path.read_bytes()
    return {'path': os.path.relpath(path, OUT), 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest()}


def main():
    assert not RAW.exists() and all(not (OUT / name).exists() for name in NAMES)
    main_contract = read(WORK / 'source-01/main-CqEoQDOU/source-contracts.json')
    boot = read(WORK / 'source-01/bootstrap-CooIJpZm/source-contracts.json')
    observations = read(WORK / 'observations-02/observations.json')
    assert len(observations['scenarios']) == 22 and all(x['status'] == 'passed' for x in observations['scenarios'])
    assert read(WORK / 'observations-01-receipt.json')['exitCode'] == 1
    assert read(WORK / 'observations-02-receipt.json')['exitCode'] == 0
    assert all(x['exitCode'] == 0 for x in read(WORK / 'source-01/receipts.json'))
    for contract in [main_contract, boot]:
        assert contract['fullProgramParsed'] and contract['parserErrors'] == 0
    checked, cache = set(), {}

    def verify_spans(value):
        if isinstance(value, dict):
            if all(key in value for key in ['sourcePath', 'sourceHash', 'byteRange', 'spanHash']):
                source_path = value['sourcePath']
                if source_path not in cache:
                    assert source_path.startswith('app.asar/')
                    data = (ROOT / '.analysis-local/baselines' / BASELINE / 'extracted' / source_path.removeprefix('app.asar/')).read_bytes()
                    cache[source_path] = (data, hashlib.sha256(data).hexdigest())
                data, digest = cache[source_path]
                a, z = value['byteRange']['start'], value['byteRange']['endExclusive']
                assert value['sourceHash'] == digest and 0 <= a < z <= len(data)
                key = (source_path, a, z, value['spanHash'])
                if key not in checked:
                    assert hashlib.sha256(data[a:z]).hexdigest() == value['spanHash']
                    checked.add(key)
            for child in value.values():
                verify_spans(child)
        elif isinstance(value, list):
            for child in value:
                verify_spans(child)

    verify_spans(main_contract)
    verify_spans(boot)
    verify_spans(observations)

    def unit(contract, fragment):
        matches = [item for item in contract['units'] if fragment in item['sourceFilename']]
        assert len(matches) == 1, fragment
        return matches[0]

    guard = unit(boot, 'runtime-entry-guard')
    menu_item = unit(main_contract, 'task-manager-item')
    assert [x['nodeType'] for x in guard['ancestors']] == ['Program']
    assert menu_item['structuralConditionsWithinCallable'] == []
    menu_calls = [x for x in main_contract['bindingReferences'] if x['target'] == 'application-menu-factory']
    lease_calls = [x for x in main_contract['bindingReferences'] if x['target'] == 'function-eJ']
    assert len(menu_calls) == 1 and menu_calls[0]['directCall']
    assert len(lease_calls) == 2 and all(x['directCall'] for x in lease_calls)
    assert {x['target'] for x in boot['bindingReferences']} == {'function-ut', 'function-dt', 'function-pt', 'function-mt'}
    old_menu = read(OUT / 'menu-command-contracts.json')
    menu_record = next(x for x in old_menu['nativeMenuItems'] if x['completeItemEvidenceId'] == 'ENTRY-AST-E03416')
    assert menu_record['conditions'] == [] and menu_record['callback']['calls'][0]['expression'] == '_.app.showTaskManager'
    facts = []

    def fact(claim, location):
        facts.append({'id': f'RUNTIME-DECISION-{len(facts)+1:03}', 'baselineId': BASELINE,
                      'claim': claim, **{key: location[key] for key in ['sourcePath', 'sourceHash', 'byteRange', 'spanHash', 'nodeType']},
                      'method': 'static-code; full-original-Program-AST-and-selected-source-review',
                      'confidence': 'confirmed', 'verificationStatus': 'source-contract-confirmed; actual-runtime-unverified'})

    fact('Owl能力guard是bootstrap Program顶层IfStatement，检查Electron版本非null与showTaskManager函数形状；它不是task-manager菜单点击时才执行的检查。', guard)
    fact('Task Manager是Help submenu的直接item，item在CZe内部无结构性条件，只有label/click；没有以allowDebugMenu、平台或requiredAccess包裹该item。此结论以menu factory被实际调用为前提。', menu_item)
    fact('完整main Program中CZe同绑定直接调用1处；工厂选项传入buildFlavor、allowDebugMenu、enableUpdater及desktopFeatureAvailability。该调用不证明真实运行值或产品模式。', menu_calls[0]['parent'])
    fact('ut同绑定直接调用来自更新管理类的observeRelaunchNotificationPolicy；null结果不订阅策略事件，也不启动该处强制调度。有效provider注册策略变化监听并触发调度。', unit(boot, 'method-observeRelaunchNotificationPolicy-'))
    fact('getRelaunchNotificationPolicy在provider为空时返回null；存在provider时调用dt，dt调用native getter后经pt的schema safeParse返回有效数据或null。getter抛错没有在这些函数中catch。', unit(boot, 'method-getRelaunchNotificationPolicy-'))
    fact('强制调度先清理既有timer；未ready、缺少download时间、policy.relaunchNotification不严格等于2或已开始安装时清空notice并返回。null策略停止的是该强制调度路径。', unit(boot, 'method-scheduleForcedUpdateInstall-'))
    fact('普通installUpdatesIfAvailable按launch policy、allowInAppUpdatesForLaunch和updater可用性判断，再调用平台updater；该完整方法不读取owlUpdatePolicies。它与managed relaunch策略是不同职责，不能以null策略省略整个更新功能。', unit(boot, 'method-installUpdatesIfAvailable-48013'))
    fact('initializeUpdaterOnce先按平台初始化updater，有updater后才观察relaunch policy；初始化/订阅抛错会进入catch并把updater置空，不能把shape-valid provider的运行异常当成安全缺省。', unit(boot, 'method-caller-45384'))
    fact('原eJ在main Program有2个同绑定直接调用，来自window.open的createWindow回调和cloneTab方法；caller不再是完全未知的注入来源。', unit(main_contract, '002-function-eJ.txt'))
    fact('window.open createWindow回调要求携带webContents且通过$q形状检查，交给eJ登记owner、route和lease，再发送adoptionLease及adoptedWebContentsId；缺失时抛出专门错误。', unit(main_contract, '013-caller-of-function-eJ-'))
    fact('cloneTab校验owner、导航和admission；有live source时调用webContents.clone并要求可adopt，再通过eJ保留navigation/errorPages。source为空时有materialize/cold-restore路径，不能将其当作live history clone的等价替代。', unit(main_contract, '016-caller-of-function-eJ-'))
    decisions = [
        {'id': 'RUNTIME-DECISION-task-manager', 'capability': 'task-manager presentation',
         'decision': '保留为独立诊断能力；第一方菜单经能力接口调用，由选定运行时或独立实现提供真实UI。不能以debug-only理由排除、以空函数通过guard或用缺省隐藏菜单完成复刻。',
         'firstPartyResponsibility': '菜单接线、能力声明与错误传播；隔离原运行时的私有方法名。',
         'externalDependencyResponsibility': '真实诊断窗口、进程数据和生命周期；尚未选择实现或固定依赖版本。',
         'evidenceIds': ['RUNTIME-DECISION-001', 'RUNTIME-DECISION-002', 'RUNTIME-DECISION-003'],
         'closedQuestions': ['guard是Program顶层', '菜单项不是局部debug分支', '同Program menu factory调用身份'],
         'remaining': ['实际UI字段、动作、刷新与关闭行为', '运行时功能/账户条件', '公开替代能力与固定版本比较'],
         'acceptance': '独立构建中菜单打开真实诊断界面，并按基线观察验证字段、动作和生命周期；能力缺失时该功能仍为未完成。'},
        {'id': 'RUNTIME-DECISION-updates', 'capability': 'update transport and managed relaunch policy',
         'decision': '将普通更新transport与nullable managed-relaunch policy分成两个第一方接口；null provider沿原无强制调度分支。完整复刻仍保留有策略时的通知、deadline、重试及平台更新职责。',
         'firstPartyResponsibility': 'schema验证、策略消费、notice/调度/重试与平台updater编排。',
         'externalDependencyResponsibility': '更新transport和策略provider分别固定来源；process._linkedBinding属于运行时内部能力，不能当作普通npm包导入。',
         'evidenceIds': [f'RUNTIME-DECISION-{i:03}' for i in range(4, 9)],
         'closedQuestions': ['选定null消费者分支', '策略订阅触发点', '普通安装方法与策略读取分开', 'provider运行异常可使初始化失败'],
         'remaining': ['provider实际数据与事件生命周期/注销', '平台updater、签名及安装行为', '完整时间helper与调度运行对照'],
         'acceptance': '分别验收无provider、有策略、provider错误、普通更新与强制安装；22个局部场景不是实际更新通过。'},
        {'id': 'RUNTIME-DECISION-browser-ownership', 'capability': 'window.open adoption and live history clone',
         'decision': '保留为浏览器所有权和历史克隆能力；第一方manager维护pending/owner/route/清理，外部能力提供实际clone与可消费的adoption lease。冷恢复分支仅按原条件使用。',
         'firstPartyResponsibility': '发起者/owner校验、tab路由和消息、pending记录及destroyed清理。',
         'externalDependencyResponsibility': 'view克隆、lease创建与原生消费/转移；不能仅替换类名或生成非空字符串。',
         'evidenceIds': ['RUNTIME-DECISION-009', 'RUNTIME-DECISION-010', 'RUNTIME-DECISION-011'],
         'closedQuestions': ['eJ的两处同绑定直接caller', 'window.open child receiver的结构来源', 'live clone与cold restore不同路径'],
         'remaining': ['完整receiver工厂和lease消费/accept身份', '实际转移、重复消费/失效及浏览历史语义', '目标平台的独立实现可行性'],
         'acceptance': '在选定shell实际完成window.open与live back/forward/reload clone、owner隔离和销毁；失败/缺失能力仍关联未完成的浏览器功能。'},
        {'id': 'RUNTIME-DECISION-process-policy', 'capability': 'restricted Node network and scoped local IPC',
         'decision': '保留进程权限策略为独立运行时要求；运行时必须实际拒绝通用net并允许声明的IPC，或用可验证的独立进程/OS边界实现同一约束。不能删flag、伪造permission.has或放宽权限。',
         'firstPartyResponsibility': '端点构造、restricted/unrestricted策略、relaunch环境/参数与open-event重放。',
         'externalDependencyResponsibility': '实际权限执行；Framework中24.19.0静态Node版本结构不能证明IPC权限实现或ABI兼容。',
         'existingEvidenceIds': ['RUNTIME-REVIEW-0005', 'RUNTIME-REVIEW-0006', 'RUNTIME-REVIEW-0007', 'RUNTIME-REVIEW-0008', 'RUNTIME-REVIEW-0012'],
         'closedQuestions': [], 'newSourceClaim': False,
         'remaining': ['最终IPC端点与所有caller', '普通运行时的IPC权限差异', '实际正反向权限及relaunch观察'],
         'acceptance': '允许端点正例、通用net及越界IPC负例、重启与open-event重放均在选定shell通过。'}]
    for decision in decisions:
        decision.update({'status': 'analysis-design-decision; implementation-and-runtime-validation-pending',
                         'fullFeatureRequirementRetained': True, 'runtimeSubstituteProven': False,
                         'productMode': 'unknown; retained pending evidence for ChatGPT-only exclusion'})
    next_action = {'priority': 'A2', 'question': '以可独立取得的固定Electron版本为对照，核对公开诊断/进程API、WebContents clone/adoption与Node权限能力，形成逐能力差异及是否需独立实现的决定。',
                   'closure': '每个结论引用固定版本官方接口/源码或明确缺席范围；不把名称缺席当全局不存在，不把API近似当行为等价。',
                   'preserve': '独立Owl来源、完整功能/模式和实际客户端行为缺口保持；不重跑已闭合的menu item与两处eJ caller。'}
    counts = {'fullOriginalProgramParses': 2, 'distinctOriginalPrograms': 2,
              'parsedAstNodes': main_contract['nodeCount'] + boot['nodeCount'],
              'sourceFacts': len(facts), 'capabilityDecisions': 4,
              'sameBindingAdoptionCallers': 2, 'isolatedSourceScenariosPassed': 22,
              'actualNativeOrUiBehaviorsVerified': 0, 'newFeatureDefinitions': 0,
              'newConfirmedModeClassifications': 0, 'modelSubmissionsAdded': 0,
              'originalClientRunsAdded': 0, 'newReaRuns': 0, 'sourceSpansChecked': len(checked)}
    result = {'schemaVersion': 1, 'baselineId': BASELINE, 'counts': counts, 'facts': facts,
              'decisions': decisions, 'nextAction': next_action,
              'sourceContracts': ['raw/runtime-decisions/source-01/main-CqEoQDOU/source-contracts.json',
                                  'raw/runtime-decisions/source-01/bootstrap-CooIJpZm/source-contracts.json'],
              'observations': 'raw/runtime-decisions/observations-02/observations.json',
              'failedAttempt': 'observations-01 failed before scenario execution: source selector matched callers as well as definition; corrected to exact saved filename in observations-02.',
              'runtimeRouteSelected': False, 'independentRuntimeBuildProven': False,
              'fullAnalysisCompleted': False, 'clientImplementationStarted': False,
              'limitations': ['Selected class member calls are syntactic, not proof of actual this instance or method dispatch.',
                              'Full-Program binding census is bounded to the selected declarations and direct references, not all native/private API callers.',
                              'Old options/unknowns remain historical snapshots; these decisions close only the selected source questions.',
                              'The fourth policy decision reuses existing evidence and adds no new permission enforcement observation.']}
    state = read(OUT / 'analysis-state.json')
    RAW.mkdir(parents=True)
    for path in WORK.iterdir():
        if path.is_dir():
            shutil.copytree(path, RAW / path.name)
        else:
            shutil.copyfile(path, RAW / path.name)
    shutil.copyfile(Path(__file__), RAW / Path(__file__).name)
    write(RAW / 'analysis-state-before.json', state)
    write(OUT / NAMES[0], result)
    summary = '''# 运行时能力与依赖处理决定

本批将四项特殊边界落实为[逐项决定](runtime-capability-decisions.json)。独立运行时路线尚未选定或验证，完整Codex功能目标保持；客户端实现未开始。

| 能力 | 已确认的职责和处理决定 | 尚待证明 |
| --- | --- | --- |
| Task Manager | bootstrap顶层guard；Help菜单项无局部debug/平台/access条件。保留真实诊断能力，通过第一方接口接入 | 实际UI/进程行为和独立替代实现 |
| 更新与managed relaunch | 分开普通更新transport与nullable策略provider。null只停止选定强制调度路径；保留有策略时的通知、deadline和重试 | native事件生命周期、平台安装/签名及真实调度 |
| 浏览器所有权与clone | eJ两处同绑定caller接到window.open child与live history clone；保留owner、pending、route和清理。冷恢复仅沿原条件 | lease消费/accept、真实视图转移与克隆行为 |
| Node网络/IPC策略 | 保留拒绝通用net、允许声明IPC的执行要求；第一方管理端点和relaunch，运行时或隔离机制实施权限 | 实际IPC执行、越界负例和目标ABI |

Task Manager不能按“调试专用”删除；函数占位只满足guard形状。更新策略缺失不等于没有更新器：普通安装方法没有读取owlUpdatePolicies；但有效provider的订阅/读取异常可能传播，initializeUpdaterOnce的catch会使updater失效。分析和实现必须分别处理缺失与错误。

浏览器两条路径也不能合并：window.open要求可adopt的child WebContents；live history clone先调用clone再创建lease。source为空时的cold restore并未证明能代替live历史、进程状态或所有权转移。相关模式仍unknown，暂留完整范围。

两份完整原Program共1,080,229个AST节点，新增11条来源事实。22个隔离源码场景通过，覆盖guard、Help handler、空/有效/错误策略、调度/重试及lease销毁清理；均使用内存替身，实际native/UI通过数为0。首个观察尝试因源码选择器歧义在执行场景前失败，修正后的第二次结果与失败记录一并保留。[来源索引](runtime-capability-decisions-provenance.json)保存工具、源码范围及终态。

第三方及运行时实现由独立依赖提供；待恢复的是第一方能力接口、业务编排与状态生命周期。本批没有生成库实现副本、没有触发原客户端或模型任务，既有功能视图和212条未执行验收规格不变。

本批关闭task-manager局部菜单/guard位置、更新null消费者及两处adoption caller的限定问题。下一项用固定版本官方接口/源码核对普通Electron与这四项能力的差异。独立Owl分发、完整ABI、全部私有API和实际行为缺口仍保留；[既有运行时方案](runtime-adapter-options.md)是历史输入，不作为已验证兼容结论。
'''
    (OUT / NAMES[1]).write_text(summary)
    provenance = {'schemaVersion': 1, 'baselineId': BASELINE,
                  'publishedAtUtc': datetime.now(timezone.utc).isoformat(), 'counts': counts,
                  'outputs': [pin(OUT / name) for name in NAMES[:-1]],
                  'rawArtifacts': [pin(p) for p in sorted(RAW.rglob('*')) if p.is_file()],
                  'inputs': [pin(OUT / name) for name in ['runtime-api-contracts.json', 'runtime-api-evidence.jsonl',
                              'menu-command-contracts.json', 'menu-command-evidence.jsonl', 'runtime-adapter-options.json',
                              'runtime-distribution.json', 'runtime-node-version.json']], 'fullAnalysisCompleted': False}
    write(OUT / NAMES[2], provenance)
    state['updatedAtUtc'] = provenance['publishedAtUtc']
    state['runtimeCapabilityDecisions'] = {'decisions': pin(OUT / NAMES[0]), 'summary': pin(OUT / NAMES[1]),
                                           'provenance': pin(OUT / NAMES[2]), 'counts': counts,
                                           'nextAction': next_action, 'fullAnalysisCompleted': False}
    write(OUT / 'analysis-state.json', state)
    paragraph = '\n[运行时能力决定](runtime-capability-decisions.md)已明确task-manager保留、普通更新与managed-relaunch策略分离，以及window.open/live clone的所有权边界。22个隔离源码场景通过；实际native/UI、独立运行时与ABI仍未验收。下一项核对固定公开运行时的能力差异，不重复查已闭合caller。\n'
    for name in ['report.md', 'gaps.md']:
        p = OUT / name
        lines = p.read_text().splitlines(keepends=True)
        lines.insert(1, paragraph)
        p.write_text(''.join(lines))
    p = ROOT / 'README.md'
    text = p.read_text()
    lines = text.splitlines(keepends=True)
    lines.insert(1, '\n最新结果见[运行时能力决定](analysis/' + BASELINE + '/runtime-capability-decisions.md)：四项边界已形成处理决定，独立运行时及实际能力仍待验证。\n\n')
    p.write_text(''.join(lines))
    for p in [*(OUT / name for name in NAMES), *RAW.rglob('*')]:
        if p.is_file():
            p.chmod(0o444)
    print(json.dumps({'published': True, **counts}, ensure_ascii=False))


if __name__ == '__main__':
    main()
