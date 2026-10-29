"""Consolidate existing analysis decisions and the bounded ownership investigation."""
import csv
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/browser-adoption-work'
PROBE = ROOT / '.analysis-local/public-runtime-comparison-work/owned-browser-transfer-01'
RAW = OUT / 'raw/stage-consolidation'


def read(path):
    return json.loads(path.read_text())


def pin(path):
    b = path.read_bytes()
    return {'path': os.path.relpath(path, OUT), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    names = ['browser-ownership-contracts.json', 'browser-ownership-contracts.md',
             'analysis-stage-decisions.json', 'analysis-stage-decisions.md',
             'stage-consolidation-provenance.json']
    if RAW.exists() or any((OUT / name).exists() for name in names):
        raise RuntimeError('Publication already exists; preserve the previous evidence')
    state_path = OUT / 'analysis-state.json'
    before = read(state_path)
    old_audit = read(OUT / 'analysis-requirements-current-audit.json')
    scope = read(OUT / 'feature-scope-v7.json')
    families = read(OUT / 'entry-family-map.json')
    dependency_rows = list(csv.DictReader((OUT / 'dependencies.csv').open()))
    assert len(dependency_rows) == 202
    assert len(scope['features']) == 48
    plan = ROOT / 'docs/reverse-engineering/analysis-plan.md'
    plan_criteria = re.findall(r'^- \[ \] (.+)$', plan.read_text(), re.M)
    assert len(plan_criteria) == 9
    sources = [read(WORK / folder / 'source-contracts.json') for folder in ['main-02', 'shared-03']]
    unit_lookup = {}
    checked_spans = 0
    for result in sources:
        source = ROOT / '.analysis-local/baselines' / BASE / 'extracted' / result['sourcePath'].removeprefix('app.asar/')
        data = source.read_bytes()
        assert hashlib.sha256(data).hexdigest() == result['sourceHash']
        for unit in result['units']:
            loc = unit['byteRange']
            span = data[loc['start']:loc['endExclusive']]
            assert hashlib.sha256(span).hexdigest() == unit['spanHash']
            unit_lookup[unit['selection']] = unit
            checked_spans += 1
    assert unit_lookup['constant-aU']['spanHash'] != unit_lookup['constant-xBi']['spanHash']
    # Names differ across Programs; their literal attribute values must agree.
    def unit_text(folder, selection):
        unit = next(u for u in read(WORK / folder / 'source-contracts.json')['units'] if u['selection'] == selection)
        return (WORK / folder / unit['sourceFilename']).read_text()
    for left, right in [('constant-aU', 'constant-xBi'), ('constant-PCe', 'constant-SBi')]:
        assert unit_text('main-02', left).split('=', 1)[1] == unit_text('shared-03', right).split('=', 1)[1]
    receipt = read(PROBE / 'receipt.json')
    observation = read(PROBE / 'data/runtime-observations.json')
    process_check = read(PROBE / 'process-check.json')
    assert receipt['exitCode'] == 0 and observation['errors'] == []
    moved, recreated = observation['observations']
    assert moved['sameWebContentsId'] and moved['before'] == moved['after']
    assert moved['after']['heap'] == 'edited-live-heap'
    assert recreated['status'] == 'rejected'
    assert process_check['psExitCode'] == 0 and process_check['ownedProcessRows'] == []
    RAW.mkdir(parents=True)
    shutil.copy2(state_path, RAW / 'analysis-state-before.json')
    for folder in ['main-02', 'shared-02', 'shared-03']:
        shutil.copytree(WORK / folder, RAW / folder)
    shutil.copy2(WORK / 'first-attempt-failures.json', RAW / 'first-attempt-failures.json')
    for relative in ['receipt.json', 'stdout.txt', 'stderr.txt', 'probe_public_browser_ownership.cjs',
                     'run_public_electron_probe.py', 'data/runtime-observations.json', 'process-check.json']:
        destination = RAW / 'public-probe' / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROBE / relative, destination)
    for name in ['browser_adoption_ast.mjs', 'probe_public_browser_ownership.cjs',
                 'run_public_electron_probe.py', Path(__file__).name]:
        destination = RAW / 'recipes' / name
        destination.parent.mkdir(exist_ok=True)
        shutil.copy2(ROOT / 'scripts/analysis' / name, destination)

    fact_specs = [
        ('BA-01', ['constant-aU', 'constant-PCe', 'constant-xBi', 'constant-SBi'],
         'renderer setter与main参数解析使用相同的两个Owl属性名；以完整Program内的词法绑定及静态赋值核对，未观察初始化时序。'),
        ('BA-02', ['host-setAdoptionAttributes'],
         'lease或WebContents ID任一为空时，renderer同时移除两个属性；齐备时写入lease和字符串ID。不能只传ID。'),
        ('BA-03', ['host-constructor'],
         '普通renderer host先设置路由partition、adoption属性和about:blank；windowTransferReceiver分支跳过这组初始化，并非普通新建webview的同一路径。'),
        ('BA-04', ['function-ICe', 'function-qCe', 'function-JCe'],
         'will-attach-webview对非空lease查pending adopted记录，要求lease匹配且尚无acceptedHostIdentity；非法/重复接收会preventDefault。'),
        ('BA-05', ['function-ICe', 'function-MCe', 'function-NCe'],
         '接收还核对路由、存储意图/所有权、pending teardown、rendererInstanceId及hostGeneration；通过后才登记acceptedHostIdentity。lease不是无条件接管令牌。'),
        ('BA-06', ['function-ICe'],
         'adoption失败后的微任务只有在事件被拒绝、renderer与host generation仍匹配且pending记录仍为同一对象时，才stopTracking并销毁尚存guest。'),
        ('BA-07', ['function-LCe', 'function-cU'],
         '附着路径固定浏览session/preload，并覆写sandbox、contextIsolation、webSecurity和Node集成等偏好；迁移视图时必须保留这层策略。'),
        ('BA-08', ['function-ICe', 'function-XCe', 'function-YCe'],
         'did-attach-webview先尝试普通instance记录，再以WebContents ID查已接受adoption；XCe传递route/host身份和initialNavigationOwner（owl或history-clone），callback正常返回后stopTracking，再按已有请求执行back/forward/reload。此顺序不是实际native执行证明。'),
        ('BA-09', ['host-adoptForWindowTransfer'],
         '跨窗口receiver等待prepared后要求webview.adoptWebContents方法；缺失即抛错。这是另一个Owl元素能力，公共主进程view移动不能直接替换其renderer调用。'),
    ]
    facts = [{'id': id_, 'claim': claim, 'method': 'full-original-Program-AST-and-bounded-source-review',
              'confidence': 'confirmed-with-stated-static-scope',
              'sources': [unit_lookup[key] for key in keys]} for id_, keys, claim in fact_specs]
    ownership = {
        'baselineId': BASE, 'facts': facts, 'actualPublicPrimitiveObservations': observation,
        'originalCreationRequirements': pin(OUT / 'runtime-capability-decisions.json'),
        'publicComparison': pin(OUT / 'public-runtime-comparison.json'),
        'implementationDecision': {
            'candidate': 'First-party main-process browser-view ownership manager using one retained WebContentsView per live page.',
            'nowSupported': 'One synthetic live view can move between owned windows while keeping WebContents ID, edited form and edited JS heap.',
            'rejectedAssumption': 'Constructing a replacement view from still-attached WebContents was rejected; removing the view from a contentView did not make this construction succeed.',
            'mustPreserve': ['route admission', 'renderer/host generation', 'paired lease/ID lifecycle or an explicitly validated ownership protocol',
                             'session/preload/security preferences', 'destroy/reject/cleanup', 'initial navigation ownership'],
            'stillUnproven': ['Owl renderer webview lease equivalence', 'view cloning and its history/process state',
                              'cross-process end-to-end delivery', 'all target-browser features', 'network/IPC permission enforcement'],
            'fullRuntimeRouteSelected': False,
        },
        'counts': {'sourcePrograms': 2, 'sourceFacts': len(facts), 'currentSourceUnits': len(unit_lookup),
                   'sourceSpansChecked': checked_spans, 'publicRuntimeProbeProcesses': 1,
                   'publicPrimitiveObservations': 2, 'originalClientRunsAdded': 0, 'modelSubmissionsAdded': 0,
                   'newConfirmedModeClassifications': 0, 'newProductBehaviorAcceptances': 0},
        'producerLimit': 'The saved AST recipe includes a literal-assignment extension added after main-02. shared-03 used that extension; main-02 output and source spans are preserved, without claiming an independently pinned historical producer revision.',
        'failedAttempts': pin(RAW / 'first-attempt-failures.json'),
        'fullAnalysisCompleted': False,
    }
    write(OUT / names[0], ownership)
    (OUT / names[1]).write_text('''# 浏览器所有权接收契约

原客户端的所有权交接包含成对的 lease/ID、路由与存储校验、renderer/host generation、防重复接收和失败销毁；并非传入 WebContents ID 后直接显示。[九条来源事实](browser-ownership-contracts.json)定位到两份完整原 Program 的选定函数、方法和属性赋值。

公共 Electron 42.3.0 的一次独立探针得到了两个结果：

- 把同一个 WebContentsView 从一个隐藏自有窗口移到另一个，WebContents ID、编辑后的表单值和 JS 堆值均保留。
- 移除旧 view 后，用其 WebContents 构造新 view，仍因“already attached to a window”被拒绝。

因此可以评估“主进程持有并移动同一视图”的第一方管理器；不能把重建 view、历史恢复、live clone 和 renderer 的 Owl adoption lease 当成同一能力。公开 [WebContentsView 构造接口](https://github.com/electron/electron/blob/v42.3.0/docs/api/web-contents-view.md)支持传入 WebContents，但本次负例表明仍需处理已有附着关系。

恢复模块须保留接收校验、生命周期、安全偏好和导航所有者。跨窗口 renderer receiver 还会调用 adoptWebContents，这一私有元素方法及 clone、消息送达、完整浏览器行为尚未验证。原生事件的真实时序没有由静态函数检查证明。

探针退出码为 0，无残留自有进程；没有运行原客户端或模型任务。两次初始 AST 抽取因输出父目录缺失而失败，修正后的结果另存，没有将失败计作成功。当前源码范围检查不等于客户端功能验收。[来源与执行记录](stage-consolidation-provenance.json)保留上述边界。
''')

    updates = {
        'AC-01': ('satisfied-with-scope-limits', '固定基线沿用；公共Electron与Node源码/实测版本分列。七条原声明完整性矛盾仍在。', ['baseline.json', 'baseline-reverification.json', 'public-runtime-comparison.json']),
        'AC-02': ('partial', '旧968入口已按10机制族/165词法owner登记，当前73根候选与48定义分列；967旧入口仍未完成用户功能映射，完整功能分母未建立。', ['entry-family-map.json', 'feature-scope-v7.json', 'command-consumer-contracts.json']),
        'AC-03': ('partial', '当前48定义均unknown、确认排除0；设置访问分类不是产品模式。需要实际消费者与共享依赖依据后才可剥离。', ['feature-scope-v7.json', 'settings-mode-boundary-contracts.json']),
        'AC-04': ('partial', '已补提交/归档/resume/fork、持久化、注册与浏览器交接等局部职责；完整保留功能的动态receiver、状态/存储和跨进程链仍未逐项闭合。', ['thread-start-entry-contracts.json', 'global-state-storage-origin.json', 'browser-ownership-contracts.json']),
        'AC-05': ('satisfied-with-scope-limits', '202条依赖记录与调查动作齐备；78根声明仅6有root安装版本，公开候选不等于原安装锁；自己的包锁和完整修改决定仍待落实。', ['dependencies.csv', 'dependency-summary.json', 'dependency-import-decisions.md']),
        'AC-06': ('satisfied-with-scope-limits', '特殊组件独立记录已交付；已有局部objc候选构建和公共运行时实测，不能沿用旧审计“未native重建/公共archive未取得”的全局表述。Owl来源、目标ABI与全能力兼容仍未证明。', ['native-runtime.json', 'objc-independent-build-summary.md', 'public-runtime-comparison.json']),
        'AC-07': ('satisfied-with-scope-limits', '17848限定输入的map调查、30个缺失构建输入出现项及REA截断/动态关系已有说明；这些限制说明没有证明工程可构建。', ['source-map-validation.json', 'build-inputs.json', 'analysis-state.json']),
        'AC-08': ('partial', '已有完成并重开样例；运行中停止/重启后同turn为interrupted，没有续跑证明；取消未测。公共运行时原语及隔离源码场景不增加原客户端功能通过数。', ['behavior-checks.md', 'behavior-stop-restart.json', 'browser-ownership-contracts.json']),
        'AC-09': ('partial', 'v6目录/恢复顺序与212条未执行规格有有限依据；本批细化运行时能力决定，仍缺完整功能到模块/依赖/实际验收的覆盖表及最终独立构建路线。', ['implementation-plan-v6.md', 'implementation-milestones-v6.json', 'feature-scope-v7-scenarios.json']),
    }
    criteria = []
    for index, previous in enumerate(old_audit['criteria']):
        assert previous['requirement'] == plan_criteria[index]
        status, finding, references = updates[previous['id']]
        criteria.append({'id': previous['id'], 'requirement': plan_criteria[index], 'status': status,
                         'currentFinding': finding, 'closeWhen': previous['closeWhen'],
                         'evidence': [pin(RAW / 'analysis-state-before.json' if name == 'analysis-state.json' else OUT / name)
                                      for name in references]})
    stages = []
    stage_references = {
        1: ['baseline.json', 'files.json', 'build-inputs.json'],
        2: ['entry-family-map.json', 'feature-scope-v7.json', 'settings-mode-boundary-contracts.json'],
        3: ['dependencies.csv', 'dependency-import-decisions.md', 'objc-independent-build-summary.md'],
        4: ['browser-ownership-contracts.json', 'command-consumer-summary.md', 'thread-start-entry-contracts.json'],
        5: ['behavior-stop-restart.json', 'behavior-checks.md', 'feature-scope-v7-scenarios.json'],
        6: ['implementation-plan-v6.md', 'implementation-milestones-v6.json', 'public-runtime-comparison.json'],
    }
    for previous in old_audit['stages']:
        number = previous['number']
        stages.append({'number': number, 'deliveryStatus': 'satisfied-with-scope-limits' if number == 1 else 'partial',
                       'requirements': [{'id': row['id'], 'requirement': row['planText'],
                                         'priorStatus': row['status'], 'currentDisposition': 'recorded-with-limits' if number == 1 else 'partial-stage; no blanket completion asserted'}
                                        for row in previous['requirements']],
                       'currentEvidence': [pin(OUT / name) for name in stage_references[number]]})
    assert sum(len(stage['requirements']) for stage in stages) == 39
    issues = [
        {'id': 'SD-01', 'kind': 'internal-analysis', 'impact': '功能分母和ChatGPT剥离范围',
         'nextAction': '用当前旧入口族/owner与具体功能表建立逐组保留、支撑、重复或待定关系，并接上页面/命令实际条件；首先处理设置页使用条件与48定义的关联。',
         'closeWhen': '已发现入口逐项有功能处置；每个拟排除分支有模式和共享依赖证明；未知保留。'},
        {'id': 'SD-02', 'kind': 'mixed-source-and-external-input', 'impact': '运行时和原生组件能否独立引入',
         'nextAction': '沿已列能力合同核对可取得运行时/源码或适配实现来源；保留公共视图移动的可用原语与clone、lease、网络/IPC隔离缺口。',
         'closeWhen': '每个所需特殊能力有独立来源或验证过的替代合同；目标平台ABI与构建方式明确。'},
        {'id': 'SD-03', 'kind': 'internal-contract-and-runtime-validation', 'impact': '公开app-server能否覆盖实际后台能力',
         'nextAction': '连接实际provider/receiver与已比较协议方法，按字段和通知差异逐项决定适配。',
         'closeWhen': '保留功能所需请求、通知、状态和失败后效均有明确适配与实际验收条件。'},
        {'id': 'SD-04', 'kind': 'mixed-validation-conditions', 'impact': '主要功能的真实行为证据',
         'nextAction': '按现有212条规格核对具体前提和可执行场景；无模型路径先执行。新增模型提交保持待授权，不能重用已耗尽次数。',
         'closeWhen': '主要链的正常、失败、取消、恢复有实测或具体受限条件；不把公共原语计作产品验收。'},
        {'id': 'SD-05', 'kind': 'internal-source-and-platform-validation', 'impact': '独立数据目录、持久化与认证范围',
         'nextAction': '沿已有globalState、CUA与host合同核对全部存储和认证来源；保持不读取个人凭据或会话的边界。',
         'closeWhen': '独立启动所需路径、权限及存储迁移有来源和验收，目录不同不能替代隔离证据。'},
        {'id': 'SD-06', 'kind': 'engineering-decision-after-contracts', 'impact': '可维护目录、干净构建和升级',
         'nextAction': '复用v6职责布局，将已明确功能接到来源/依赖/任务/场景；30个缺失输入按自行重建、独立依赖或不需要原脚本分别处置。',
         'closeWhen': '完整恢复覆盖表与独立构建路线成立；最终源码不含第三方实现副本，后续升级有版本差异和回归映射。'},
    ]
    decisions = {
        'baselineId': BASE, 'plan': pin(plan), 'historicalAudit': pin(OUT / 'analysis-requirements-current-audit.json'),
        'criteria': criteria, 'stages': stages, 'remainingIssues': issues,
        'counts': {'completionCriteria': 9, 'satisfiedRecordOrScopeObligations': 4, 'partialCriteria': 5,
                   'stages': 6, 'requirementItems': 39, 'remainingDecisionGroups': len(issues),
                   'legacyEntryRecords': 968, 'legacyMechanismFamilies': 10, 'legacyLexicalOwnerGroups': 165,
                   'currentFeatureDefinitions': 48, 'currentRootOperationCandidates': 73,
                   'currentUnexecutedScenarios': 212, 'confirmedChatGptExclusions': 0},
        'decisionsAlreadySupported': [
            '按main/preload/renderer/worker、状态所有权和生命周期划分维护模块；chunk只作来源定位。',
            '第三方组件通过包/独立运行时/受维护补丁引入；第一方wrapper、状态和生命周期仍需恢复。',
            '固定Electron42.3.0不能原样替换Owl；同一公共view的跨窗口移动可作适配原语，不能据此认定clone/lease/权限完整兼容。',
            '公开app-server需要协议适配决定；候选版本、基线实际版本和新工程锁分开。',
            '当前不生成ChatGPT删除清单；模式unknown合法保留，设置访问分类不代替产品模式。',
        ],
        'interpretation': 'Four satisfied items are record/scope obligations, not a completion percentage or a claim that independent building works. Thirty-nine subordinate requirements remain enumerated; older statuses are historical, not renewed full-source verification.',
        'nextAction': {'issueId': 'SD-01', 'fixedInput': '53个设置可见性分支、当前48个功能定义及3个条件页面容器关系',
                       'question': '把页面级使用条件接到现有功能定义和场景前提，分开访问资格、平台、能力与产品模式；只据真实模式证据更新分类。',
                       'closure': '每项定义给出对应入口条件或明确未映射理由；不能按chatGpt/codex分类标签直接删除代码。'},
        'fullAnalysisCompleted': False, 'clientImplementationStarted': False,
        'modelSubmissionsAdded': 0, 'originalClientRunsAdded': 0,
    }
    write(OUT / names[2], decisions)
    lines = ['# 分析阶段决定与剩余工作', '',
             '本次复用现有成果，按原计划九项标准、六阶段和39条子要求收束。**四项资料/范围义务已有交付，五项仍部分完成；这不是完成百分比，完整分析没有结束。**', '',
             '| 标准 | 当前判定 | 结论 |', '| --- | --- | --- |']
    for row in criteria:
        lines.append(f"| {row['id']} {row['requirement']} | {'资料/范围义务满足' if row['status'].startswith('satisfied') else '部分完成'} | {row['currentFinding']} |")
    lines += ['', '当前能决定的工程边界：', '']
    lines += ['- ' + value for value in decisions['decisionsAlreadySupported']]
    lines += ['', '剩余问题收束为以下六组。每组保持原功能目标，并有具体关闭条件；无需把所有未知项清零才安排其他证据充分的分析。', '',
              '| 组 | 影响 | 下一步与关闭条件 |', '| --- | --- | --- |']
    for row in issues:
        lines.append(f"| {row['id']} | {row['impact']} | {row['nextAction']} 关闭：{row['closeWhen']} |")
    lines += ['', '本轮新增[浏览器所有权接收契约](browser-ownership-contracts.md)，并实测同一公共view移动保留内存、以已有WebContents构造替代view被拒绝。它改变了适配方案的具体边界，没有增加原客户端功能通过数。', '',
              '下一项按SD-01，把53个设置可见性分支关联到当前48定义的页面级前提；已有源码定位不重复调查。需要模型的行为场景保持待授权，当前样例余次为0；其余源码和无模型验证继续执行。', '',
              '旧审计保留为历史快照，当前停止/重启实测、局部objc构建和公共运行时取得状态以本表引用的较新成果为准。[结构化逐项表](analysis-stage-decisions.json)保留39条子要求、证据与关闭条件；[来源索引](stage-consolidation-provenance.json)说明实际检查范围。客户端实现与打包仍属于后续阶段。', '']
    (OUT / names[3]).write_text('\n'.join(lines))
    inputs = ['analysis-requirements-current-audit.json', 'feature-scope-v7.json', 'entry-family-map.json',
              'dependencies.csv', 'dependency-summary.json', 'native-runtime.json', 'source-map-validation.json',
              'build-inputs.json', 'behavior-stop-restart.json', 'implementation-plan-v6.md',
              'implementation-milestones-v6.json', 'public-runtime-comparison.json', 'runtime-capability-decisions.json']
    provenance = {'baselineId': BASE, 'createdAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'inputs': [pin(OUT / name) for name in inputs] + [pin(plan)],
                  'outputs': [pin(OUT / name) for name in names[:4]],
                  'rawFiles': [pin(p) for p in sorted(RAW.rglob('*')) if p.is_file()],
                  'scope': 'Current selected-artifact consolidation and bounded two-Program source review; not a fresh audit of every historical source fact or every actual client behavior.',
                  'executionReceipts': [{'sessionId': 95602, 'exitCode': 0, 'output': 'main-02/source-contracts.json'},
                                        {'sessionId': 30900, 'exitCode': 0, 'output': 'shared-02/source-contracts.json'},
                                        {'sessionId': 95439, 'exitCode': 0, 'output': 'shared-03/source-contracts.json'},
                                        {'sessionId': 92580, 'exitCode': 0, 'output': 'public-probe/receipt.json'}]}
    write(OUT / names[4], provenance)
    state = dict(before)
    state['updatedAtUtc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    state['browserOwnershipContracts'] = {'contracts': pin(OUT / names[0]), 'summary': pin(OUT / names[1]),
                                           'provenance': pin(OUT / names[4]), 'counts': ownership['counts'],
                                           'fullAnalysisCompleted': False}
    state['stageDecisions'] = {'decisions': pin(OUT / names[2]), 'summary': pin(OUT / names[3]),
                               'provenance': pin(OUT / names[4]), 'counts': decisions['counts'],
                               'nextAction': decisions['nextAction'], 'fullAnalysisCompleted': False}
    write(state_path, state)
    for path in [*(OUT / name for name in names), *RAW.rglob('*')]:
        if path.is_file():
            path.chmod(0o444)
    print(json.dumps({'published': names, 'criteria': {'recordOrScopeSatisfied': 4, 'partial': 5},
                      'browserFacts': len(facts), 'publicPrimitiveObservations': 2}, ensure_ascii=False))


if __name__ == '__main__':
    main()
