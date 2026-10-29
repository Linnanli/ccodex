"""Publish bounded interrupt observations while preserving all previous state fields."""
import datetime
import hashlib
import json
from pathlib import Path
from contract_reader_context import PROFILES, build_context

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASELINE
WORK = ROOT / '.analysis-local/interrupt-control-flow-work'
PREFIX = 'raw/interrupt-control-flow/'


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


source = json.loads((WORK / 'source-02/contracts.json').read_bytes())
observations = json.loads((WORK / 'observations-02/observations.json').read_bytes())
findings = json.loads((WORK / 'findings-01/findings.json').read_bytes())
verification = json.loads((WORK / 'verification-01.json').read_bytes())
assert verification['status'] == 'passed' and verification['successfulSuiteScenarios'] == 34
assert len(source['records']) == 8 and len(source['joins']) == 17
assert len(observations['cases']) == 34 and all(c['passed'] for c in observations['cases'])
assert observations['executedSavedSourceBytes'] == 5259 and findings['counts']['observationCommandAttempts'] == 2
stages = ['analyze-01', 'analyze-02', 'observe-01', 'observe-02', 'curate-01', 'verify-author-01']
for stage in stages:
    receipt = json.loads((WORK / 'attempts' / stage / 'receipt.json').read_bytes())
    assert receipt['exitCode'] == (1 if stage == 'observe-01' else 0) and receipt['sourcesUnchanged']

planned, copies = {}, []


def copy(relative, path, kind='metadata_only'):
    raw = path.read_bytes()
    destination = PREFIX + relative
    assert destination not in planned
    planned[destination] = raw
    copies.append({'original': str(path), 'outputPath': destination, **pin(raw), 'kind': kind})


deliverables = {
 'interrupt-control-flow.json': WORK / 'source-02/contracts.json',
 'interrupt-control-flow-evidence.jsonl': WORK / 'source-02/evidence.jsonl',
 'interrupt-control-flow-observations.json': WORK / 'observations-02/observations.json',
 'interrupt-control-flow-findings.json': WORK / 'findings-01/findings.json',
}
for name, path in deliverables.items():
    copy('author/' + name, path)
    planned[name] = path.read_bytes()
copy('author/verification.json', WORK / 'verification-01.json')
copy('history/source-01-contracts.json', WORK / 'source-01/contracts.json')
copy('history/source-01-evidence.jsonl', WORK / 'source-01/evidence.jsonl')
for stage in stages:
    for path in sorted((WORK / 'attempts' / stage).iterdir()):
        copy('attempts/' + stage + '/' + path.name, path,
             'analysis_tool_source' if path.suffix in {'.py', '.mjs'} else 'execution_metadata')

summary = '''# 中断函数的条件与隔离观察

本批核对普通本地停止链中的函数行为：在固定shared Program中重新定位Ien、zen、Len、Pen、Ren、IN及两个Dfn方法，保存8条源码事实、12个范围和17处Program绑定。9个保存单位5259字节在本机Node22的VM中完成34个场景。没有启动桌面应用、点击停止或提交模型任务；真实UI接收实例和Node24／Owl行为仍未知。见[源码契约](interrupt-control-flow.json)、[场景结果](interrupt-control-flow-observations.json)、[限定解释与维护边界](interrupt-control-flow-findings.json)、[证据](interrupt-control-flow-evidence.jsonl)及[来源索引](interrupt-control-flow-provenance.json)。

普通composer的既有源码链没有传expectedTurnId。Ien先取最后一个有turnId的快照；显式expected ID不匹配或该项不是inProgress时直接返回null。没有expected ID且快照非活动时只尝试清理后台终端。新Program分析关闭所选Ien／helper的词法绑定，不关闭[KI/provider的实际实例](submission-host-instance-summary.md)。yda范围沿用旧完整定位并重核字节，没有重新解析整个initial Program。

| 条件或结果 | 本批观察到的函数行为 | 范围 |
| --- | --- | --- |
| 普通成功 | 中断请求履行后本地标记原turn；返回ID与notification完成分别表达 | C04、C05 |
| 服务端报告另一活动ID | 无expected ID可补发一次；补发成功返回报告ID，但该成功分支只标记原turn；补发报精确no-active-turn时另标记报告turn | C09–C12 |
| no-active-turn文本错误 | 无expected ID时本地标记并返回原ID；有expected ID时返回null | C13 |
| 清理前后台 | 无expected ID先发起node_repl清理，显式ID在finally发起；backgroundCleanup不等待清理Promise | C04–C07 |
| 暂停goal失败 | system在中断前退出；user-stop继续中断后抛附带interruptedTurnId的错误，renderer仍可先记录该ID再重抛 | M05、M06 |
| follower不可用 | 只有follower角色加三类指定文本原因才回退本地并标记needsResume | M01–M03 |
| descendant清理 | finally中的被等待清理错误可替换self错误；user-stop调用单独后台方法 | W01–W03 |
| renderer包装 | 显式client避开host选择；user结果更新有精确条件，yda成功返回undefined | R01–R03 |

Pen仅识别两种固定基线文本格式，Ren要求完全相同的`no active turn to interrupt`。不能把任意错误当作可补发。zen的10000ms只在显式假scheduler中推进，goal请求的500ms只验证传入选项；没有观察真实超时强制、native进程终止、bridge送达或后端落盘。等待期间已completed的原turn在本场景不被Len覆盖，也不代表真实通知排序已验证。

所有模型／RPC、follower、logger、events、runtime、scheduler、descendant清理和renderer store均为受控替身。Ben.default用标准Array.findLast边界替代，mz／ah仅处理合成turns数组，canonical历史未执行。IN的generic utility来源未独立归类；Ben依赖只定位到Program声明与使用，不能据此认定包名。原第三方实现没有复制进交付文件，保存源码片段只留在本地分析区；这些替身不能直接作为恢复项目中的兼容实现。

实际启动了两次VM观察命令。首轮在M06的跨VM原型deepStrictEqual断言失败，已有部分函数调用执行但没有完整结果文件；第二轮改为逐字段比较后完成34个场景。失败的精确脚本、stdout、stderr、receipt与首轮source选择均保留。34是成功套件的场景定义数，个别场景含多个变体；不是总调用数、产品功能数或独立运行次数。作者校验另核2个源文件、''' + str(verification['uniqueSourceSpansChecked']) + '''个唯一范围与''' + str(verification['metadataPointersChecked']) + '''个metadata pointer，没有新增独立语义审查。

[已有桌面结果](behavior-stop-restart.json)保持原结论：取消样例没有找到可精确绑定的控制项，取消点击0；另一个样例通过SIGTERM停止并重启后，在绑定的UI中看到同一turn为interrupted。后者不证明停止按钮、yda/Ien或哪一条持久化路径执行，也未观察到继续运行。该两条模型样例组已使用2／2、剩余0；本批不消耗或扩充授权。

维护职责可暂分为取消UI控制、turn中断编排、基线错误适配及runtime清理四个候选边界，具体建议保存在findings JSON。异常需要携带“可能已中断”的结果，避免把goal或descendant后续失败直接视为可以重发的失败。此处是恢复职责提案，没有生成客户端实现。FSC-0001至0034、35已关联操作、36队列和968入口覆盖状态均保持，未从协议方法数增加feature；模式仍unknown，ChatGPT排除0、完整功能分母与整项目构建继续待闭合。
'''
planned['interrupt-control-flow-summary.md'] = summary.encode()
index = {'schemaVersion': 1, 'baselineId': BASELINE,
 'kind': 'bounded-cancellation-source-and-controlled-vm-observations',
 'publishedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'exactCopies': copies, 'derived': [{'path': n, **pin(planned[n])} for n in list(deliverables) + ['interrupt-control-flow-summary.md']],
 'sourceFacts': 8, 'canonicalSourceSelections': 12, 'programLexicalJoins': 17,
 'originalSourceProgramsByteChecked': 2, 'sharedProgramParseCommands': 2,
 'uniqueProgramParsed': 1, 'initialProgramNewlyParsed': False,
 'sourceSpansByteChecked': verification['uniqueSourceSpansChecked'],
 'metadataPointersChecked': verification['metadataPointersChecked'],
 'isolatedObservationCommandAttempts': 2, 'completedObservationCommands': 1,
 'failedObservationCommands': 1, 'isolatedScenarioCount': 34,
 'savedSourceUnitsLoaded': 9, 'executedSavedSourceBytes': 5259,
 'originalClientRunsAdded': 0, 'newActualCancelClicks': 0, 'modelSubmissionsAdded': 0,
 'newFeatureDefinitions': 0, 'modeAssignmentsAdded': 0, 'globalRecordsAdded': 0, 'newReaRuns': 0,
 'featureDenominatorEstablished': False, 'thirdPartyImplementationsPublished': False,
 'independentSemanticPeerReviewAdded': False, 'fullAnalysisCompleted': False}
planned['interrupt-control-flow-provenance.json'] = encode(index)
names = ['report.md', 'analysis-state.json', 'implementation-plan.md', 'gaps.md', 'behavior-checks.md']
before = {n: (OUT / n).read_bytes() for n in names}
old = json.loads(before['analysis-state.json'])
assert len(old) == 90 and not old['fullAnalysisCompleted'] and not old['featureDenominatorEstablished']
assert old['latestBehaviorAuthorizationState']['groupRemaining'] == 0 and 'interruptControlFlowObservations' not in old
for name in planned:
    assert not (OUT / name).exists()
for name, raw in planned.items():
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    path.chmod(0o444)
patch, _, artifacts = build_context(OUT, BASELINE)
assert len(patch) == len(PROFILES) == 25
assert all(old[k] == v for k, v in patch.items() if k != 'interruptControlFlowObservations')
state = {**old, 'interruptControlFlowObservations': patch['interruptControlFlowObservations']}
assert all(state[k] == v for k, v in old.items())
note = next(p[4] for p in PROFILES if p[0] == 'interruptControlFlowObservations')
marker = '[完成标准审计](criteria-audit.md)'
report = before['report.md'].decode()
assert report.count(marker) == 1
changes = {'report.md': report.replace(marker, note + '\n\n' + marker).encode(), 'analysis-state.json': encode(state)}
extras = {
 'implementation-plan.md': '\n\n[中断函数隔离观察](interrupt-control-flow-summary.md)补取消链的异常与状态职责：保留expected-ID快照校验、限定文本补发、goal暂停先后、follower回退和descendant finally。返回ID、局部interrupted状态、后续失败与后端确认必须分开表达；user-stop失败可能已经中断，不能直接重发。9单位5259字节的VM结果不证明真实provider／native；IN／Ben来源与canonical历史保持依赖边界，不复制第三方实现。四个候选模块职责见findings，尚无客户端代码。\n',
 'gaps.md': '\n\n[取消函数来源与34场景](interrupt-control-flow-summary.md)关闭所选Ien／helper的17个Program词法关联；2个shared解析命令和两次VM命令（1次完整、1次断言失败）分别登记。真实取消点击仍0，当前UI实例、KI选支、canonical历史、native清理／计时与真正transport超时均未闭合；SIGTERM重启观察不能覆盖这些缺口。34功能与36待审操作队列原样保留，未做模式排除或新增模型提交。\n',
 'behavior-checks.md': '\n\n[中断隔离结果](interrupt-control-flow-observations.json)含本机Node22单条完成命令中的34场景定义，另有首轮跨VM原型断言失败的部分执行命令。受控follower、goal、请求、状态、清理和假scheduler下，补发成功的局部写入差异、已中断后仍可能抛错、前后台清理和renderer Error属性处理分别有记录。不能升级真实停止按钮或恢复机制；原取消未测试、同turn重启后interrupted及模型组2／2已用的结果保持。\n',
}
for name, extra in extras.items():
    changes[name] = before[name] + extra.encode()
readme_before = (ROOT / 'README.md').read_bytes()
readme = readme_before + ('\n- [中断函数来源、34个隔离场景与取消验证边界](analysis/' + BASELINE + '/interrupt-control-flow-summary.md)\n').encode()
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
    temp = path.with_name('.interrupt-control-flow-' + path.name)
    assert not temp.exists()
    temp.write_bytes(raw)
    temp.chmod(path.stat().st_mode & 0o777)
    temp.replace(path)
assert (ROOT / 'README.md').read_bytes() == readme_before
temp = ROOT / '.interrupt-control-flow-README.md'
assert not temp.exists()
temp.write_bytes(readme)
temp.chmod((ROOT / 'README.md').stat().st_mode & 0o777)
temp.replace(ROOT / 'README.md')
print(json.dumps({'status': 'published-and-integrated', 'companionIndices': len(patch),
 'oldStateKeysPreserved': len(old), 'oldStateValuesPreserved': True, 'completedSuiteScenarios': 34,
 'observationCommandAttempts': 2, 'failedCommandRetained': 1,
 'selectedArtifactsBeforeOwnCapture': len(artifacts),
 'snapshots': [{'path': n, **pin(raw)} for n, raw in snapshots.items()],
 'outputs': {n: pin(raw) for n, raw in changes.items()},
 'modelSubmissionsAdded': 0, 'fullAnalysisCompleted': False}))
