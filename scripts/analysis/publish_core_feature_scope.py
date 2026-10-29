"""Publish append-only core feature definitions and a bounded current scope reader."""
import datetime
import hashlib
import json
from pathlib import Path
from contract_reader_context import PROFILES, build_context

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASELINE
WORK = ROOT / '.analysis-local/core-feature-scope-work'
AUTHOR = WORK / 'analysis-02'
PREFIX = 'raw/core-feature-scope/'


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


review = json.loads((AUTHOR / 'core-feature-scope.json').read_bytes())
current = json.loads((AUTHOR / 'feature-scope-current.json').read_bytes())
verification = json.loads((WORK / 'verification-01.json').read_bytes())
assert verification['status'] == 'passed' and verification['metadataPointersOrLinesChecked'] == 223
assert len(review['newFeatures']) == 3 and len(review['operationDecisions']) == 33
assert len(current['features']) == 37 and len(current['supportOperations']) == 5 and len(current['operationReviewQueue']) == 26
stages = ['analyze-01', 'analyze-02', 'verify-author-01']
for stage in stages:
    receipt = json.loads((WORK / 'attempts' / stage / 'receipt.json').read_bytes())
    assert receipt['exitCode'] == 0 and receipt['sourcesUnchanged']
planned, copies = {}, []


def copy(relative, path, kind='metadata_only'):
    raw = path.read_bytes()
    destination = PREFIX + relative
    assert destination not in planned
    planned[destination] = raw
    copies.append({'original': str(path), 'outputPath': destination, **pin(raw), 'kind': kind})


names = ['core-feature-scope.json', 'core-feature-scope-scenarios.json', 'feature-scope-current.json',
         'feature-scope-current-scenarios.json', 'feature-scope-current.csv']
for name in names:
    copy('author/' + name, AUTHOR / name)
    planned[name] = (AUTHOR / name).read_bytes()
    copy('history/analysis-01/' + name, WORK / 'analysis-01' / name)
copy('author/verification.json', WORK / 'verification-01.json')
for stage in stages:
    for path in sorted((WORK / 'attempts' / stage).iterdir()):
        copy('attempts/' + stage + '/' + path.name, path,
             'analysis_tool_source' if path.suffix in {'.py', '.mjs'} else 'execution_metadata')

evidence = []
for feature in review['newFeatures']:
    primary = feature['operationMembers'][0]['operationRef']
    evidence.append({'id': 'CORE-FEATURE-' + str(len(evidence)+1).zfill(4), 'baselineId': BASELINE,
     'claim': 'Define ' + feature['featureId'] + ': ' + feature['name'] + '. ' + feature['granularityRationale'],
     'sourcePath': primary['path'], 'sourceHash': primary['sha256'],
     'locator': {'kind': 'json-pointer', 'pointer': primary['jsonPointer']},
     'method': 'inference', 'confidence': 'inferred', 'featureId': feature['featureId'],
     'verificationStatus': 'author-granularity-review; inherited-bounded-source; selected-bytes-rechecked; no-new-runtime',
     'operationEquivalenceClaimed': False, 'modeClassificationClaimed': False, 'newGlobalEvidenceRecord': False})
for decision in review['operationDecisions']:
    primary = decision['operationRef']
    evidence.append({'id': 'CORE-FEATURE-' + str(len(evidence)+1).zfill(4), 'baselineId': BASELINE,
     'claim': 'Classify ' + decision['operationId'] + ' as ' + decision['status'] + '. ' + decision['reason'],
     'sourcePath': primary['path'], 'sourceHash': primary['sha256'],
     'locator': {'kind': 'json-pointer', 'pointer': primary['jsonPointer']},
     'method': 'inference', 'confidence': 'inferred', 'operationId': decision['operationId'],
     'featureIds': decision['featureIds'], 'verificationStatus': 'author-granularity-review; actual-consumer/receiver qualification retained',
     'operationEquivalenceClaimed': False, 'modeClassificationClaimed': False, 'newGlobalEvidenceRecord': False})
assert len(evidence) == 36
planned['core-feature-scope-evidence.jsonl'] = ('\n'.join(json.dumps(e, ensure_ascii=False) for e in evidence) + '\n').encode()
summary = '''# 核心功能粒度与当前有限清单

本批为已有本地提交、普通停止和MCP电脑应用审批新增FSC-0035至FSC-0037三个baseline-local功能定义。当前有限清单累计37项，关联40个用户操作、5个机制支撑，另26个候选继续排队，三类合计覆盖原71操作。完整产品功能分母仍未知。见[本批分析](core-feature-scope.json)、[当前有限清单JSON](feature-scope-current.json)、[CSV](feature-scope-current.csv)、[160条待执行规格](feature-scope-current-scenarios.json)、[36条作者推断记录](core-feature-scope-evidence.jsonl)及[来源](core-feature-scope-provenance.json)。没有新增运行、审批决定或模型提交。

| 新功能ID | 用户目标 | 关联的直接操作 | 仍待闭合 |
| --- | --- | --- | --- |
| FSC-0035 | 向已有本地对话提交消息 | renderer-existing-local-submit | 实际目标／scope／host、KI选支、送达、队列及耐久状态 |
| FSC-0036 | 停止已有本地对话的当前执行 | ordinary-local-cancel | 真实stop按钮和同turn绑定、下游结果、native及重开后的状态来源 |
| FSC-0037 | 决定MCP电脑应用使用请求 | accept-session-or-null、accept-always、decline | 实际请求生产条件／模式、receiver、响应确认、安全规则及持久化 |

这三个定义采用用户目标与有条件的入口契约。已有本地提交与新建对话、cloud、worktree保持各自范围；本批不声称后者已分析完成。提交链把draft／UI ownership、局部接纳、队列、start／steer和最终完成分开。普通stop未传expectedTurnId，不能从确认框里的turnId推断wire有该参数；goal暂停失败后可能已中断，后续异常也不等于可以重发。

三个审批动作归于一次应用使用决定，保留各自action／persist条件与响应，不称操作等价。主动作仅在支持session时发送session，否则null；always取决于对应选项；拒绝是decline。accept先写曾批准atom，所选rejection分支只按当前request key恢复ref/loading，没有回滚atom。此定义只覆盖mcpServerElicitation中经browser优先分支后选中的电脑应用卡片，不覆盖command／file审批、permissionRequest或整个审批组。ChatGPT文案和computer-use名字均未用于模式排除。

原33个非设置候选全部经过本批作者的有限粒度审阅：5个分配为直接用户操作；turn/start、turn/steer、turn/interrupt、conditional-Dfn-capability和一条源中断状态表示共5个保留为机制支撑。它们的关联不穷尽所有调用方，也不是“一种协议方法等于一种feature”。尤其notification目录中的turn/interrupt记录描述源码状态转移，不能当成已经收到某个通知。

另23个非设置候选仍排队：thread start／resume／fork／archive四项缺具体用户消费者，thread/started、turn/started、turn/completed、error四项缺状态到实际展示目标的连接，14个电脑使用query／service包装缺真实设置控件与模式条件，一个项目能力派生条件缺父动作。加上原两条设置只读facet和一条WSL多动作卡，共26队列。所有候选仍保留在产品调查范围，没有被当作“不存在”或排除。

本批新增20条未执行规格，逐操作覆盖success／failure／cancel／restore，并保留旧140条；累计160条执行数仍为0。每条包含精确条件、参数状态引用、源合同及预期限度。此前[34个中断VM场景](interrupt-control-flow-summary.md)只支持指定替身下的函数条件，[SIGTERM重启观察](behavior-stop-restart.json)只支持绑定UI中的同turn interrupted；两者都没有覆盖真实stop控制和完整功能验收。已有两条模型样例组已消耗2／2、剩余0，本批没有使用或扩充授权。

本批新读取并核对6个冻结Program文件、84个唯一范围、223个metadata pointer／JSONL line，涵盖选定composer、provider、approval及interrupt单位。没有新解析Program或运行REA，词法和语义关系仍沿用已引用的有限REA／AST补充合同；字节校验不是新的独立语义审查。首轮结果使用概念性数组pointer引用JSONL记录，第二轮改为显式line locator；两个版本的工具、元数据和完整命令捕获均保留，当前交付使用第二轮。

原FSC-0001至0034及140规格逐对象保持；当前读者以37／40／5／26／160替代旧34／35／36／140的当前有限视图，旧文件作为不可改写的历史快照继续保留。37项仍全部mode unknown，confirmed排除0；36旧大组是另一粒度，不能相加。968旧入口仍只有一个设置容器部分关联、967未映射、0完全解析；composer命令标签尚未证明与这些回调同一身份，因此本批没有虚增旧入口覆盖。337 deferred没有消解。

后续先接队列项的真实消费者和模式／依赖条件，再扩展细粒度功能及模块恢复表。source→条件→操作→用户目标→验收可作为恢复顺序的依据；本批没有生成客户端源码或第三方实现，也没有把条件机制包装成已可独立构建的功能。
'''
planned['core-feature-scope-summary.md'] = summary.encode()
index = {'schemaVersion': 1, 'baselineId': BASELINE, 'kind': 'scoped-core-goals-and-operation-granularity',
 'publishedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'exactCopies': copies,
 'derived': [{'path': n, **pin(planned[n])} for n in names + ['core-feature-scope-evidence.jsonl', 'core-feature-scope-summary.md']],
 'scopedFeatureDefinitions': 37, 'newScopedFeatureDefinitions': 3,
 'assignedUserOperations': 40, 'mechanismSupportOperations': 5, 'queuedOperations': 26,
 'reviewedNonsettingsOperationCandidates': 33, 'knownOperationCandidatesAccountedFor': 71,
 'currentUnexecutedScenarioSpecifications': 160, 'newUnexecutedScenarioSpecifications': 20,
 'newInferenceRecords': 36, 'sourceProgramsByteChecked': 6, 'sourceSpansByteChecked': 84,
 'metadataPointersOrLinesChecked': 223, 'originalClientRunsAdded': 0, 'modelSubmissionsAdded': 0,
 'runtimeObservationsAdded': 0, 'globalRecordsAdded': 0, 'newReaRuns': 0, 'newOriginalProgramParses': 0,
 'newModeAssignments': 0, 'newConfirmedExclusions': 0, 'featureDenominatorEstablished': False,
 'thirdPartyImplementationsPublished': False, 'independentSemanticPeerReviewAdded': False, 'fullAnalysisCompleted': False}
planned['core-feature-scope-provenance.json'] = encode(index)
readers = ['report.md', 'analysis-state.json', 'implementation-plan.md', 'gaps.md', 'behavior-checks.md']
before = {n: (OUT / n).read_bytes() for n in readers}
old = json.loads(before['analysis-state.json'])
assert len(old) == 91 and not old['fullAnalysisCompleted'] and not old['featureDenominatorEstablished']
assert old['latestBehaviorAuthorizationState']['groupRemaining'] == 0 and 'coreFeatureScope' not in old
for name in planned:
    assert not (OUT / name).exists()
for name, raw in planned.items():
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    path.chmod(0o444)
patch, _, artifacts = build_context(OUT, BASELINE)
assert len(patch) == len(PROFILES) == 26
assert all(old[k] == v for k, v in patch.items() if k != 'coreFeatureScope')
state = {**old, 'coreFeatureScope': patch['coreFeatureScope']}
assert all(state[k] == v for k, v in old.items())
note = next(p[4] for p in PROFILES if p[0] == 'coreFeatureScope')
marker = '[完成标准审计](criteria-audit.md)'
report = before['report.md'].decode()
assert report.count(marker) == 1
changes = {'report.md': report.replace(marker, note + '\n\n' + marker).encode(), 'analysis-state.json': encode(state)}
extras = {
 'implementation-plan.md': '\n\n[当前37项有限功能及核心操作](core-feature-scope-summary.md)补FSC-0035已有本地提交、0036普通停止和0037电脑应用审批。先恢复用户目标与精确条件下的操作，再接provider／transport／state和验收；三个审批选择保持不同响应，协议／状态支持不另算feature。当前40用户操作／5支撑／26队列覆盖旧71候选，160规格未执行，完整功能分母仍未知。新建对话／cloud／worktree及其他审批不因此完成；未知模式和第三方边界继续保留。\n',
 'gaps.md': '\n\n[核心功能粒度审阅](core-feature-scope-summary.md)把33个非设置候选分为5个用户操作、5个机制支撑、23个待查，加原3设置条目共26队列。累计37功能／40用户操作／160未执行规格只覆盖有限语料；37模式unknown、排除0、967旧入口未映射、337 deferred保持。6个源文件84范围／223 pointer或line的复核未解决真实消费者／选支、通知展示、approval producer／sender、耐久恢复或完整功能分母。\n',
 'behavior-checks.md': '\n\n[当前160条未执行功能验收规格](feature-scope-current-scenarios.json)包含原140及本批20条，新增已有本地提交、普通停止和三种电脑应用审批选择。源条件、操作参数／响应、错误和恢复边界逐项关联；没有一次新的UI动作、审批决定或模型提交。中断VM34场景只作有限函数支持，SIGTERM重启只作独立进程控制上下文，均未计入真实stop功能验收。模型样例组剩余0。\n',
}
for name, extra in extras.items():
    changes[name] = before[name] + extra.encode()
readme_before = (ROOT / 'README.md').read_bytes()
readme = readme_before + ('\n- [当前37项有限功能、核心操作粒度与160条待执行规格](analysis/' + BASELINE + '/core-feature-scope-summary.md)\n').encode()
snapshots = {PREFIX + 'reader-before/' + n: raw for n, raw in before.items()}
snapshots[PREFIX + 'reader-before/README.md'] = readme_before
for name, raw in snapshots.items():
    path = OUT / name
    assert not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    path.chmod(0o444)
for name, raw in changes.items():
    path = OUT / name
    assert path.read_bytes() == before[name]
    temp = path.with_name('.core-feature-scope-' + path.name)
    assert not temp.exists()
    temp.write_bytes(raw)
    temp.chmod(path.stat().st_mode & 0o777)
    temp.replace(path)
assert (ROOT / 'README.md').read_bytes() == readme_before
temp = ROOT / '.core-feature-scope-README.md'
assert not temp.exists()
temp.write_bytes(readme)
temp.chmod((ROOT / 'README.md').stat().st_mode & 0o777)
temp.replace(ROOT / 'README.md')
print(json.dumps({'status': 'published-and-integrated', 'companionIndices': len(patch),
 'oldStateKeysPreserved': len(old), 'oldStateValuesPreserved': True, 'newScopedFeatureDefinitions': 3,
 'currentScopedFeatureDefinitions': 37, 'assignedUserOperations': 40, 'mechanismSupportOperations': 5,
 'queuedOperations': 26, 'unexecutedScenarioSpecifications': 160,
 'selectedArtifactsBeforeOwnCapture': len(artifacts),
 'snapshots': [{'path': n, **pin(raw)} for n, raw in snapshots.items()],
 'outputs': {n: pin(raw) for n, raw in changes.items()},
 'modelSubmissionsAdded': 0, 'fullAnalysisCompleted': False}))
