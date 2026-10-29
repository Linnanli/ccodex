"""Publish selected quit-source contracts and explicitly synthetic observations."""
import datetime
import hashlib
import json
from pathlib import Path
from contract_reader_context import PROFILES, build_context

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASELINE
WORK = ROOT / '.analysis-local/shutdown-persistence-work'


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


source = json.loads((WORK / 'selected-source-02/contracts.json').read_bytes())
observations = json.loads((WORK / 'observations-01/observations.json').read_bytes())
assert len(source['records']) == 20 and len(source['selections']) == 19
assert len(source['parses']) == 1 and source['targetCodeExecuted'] is False
assert source['confidenceCounts'] == {'confirmed': 20, 'inferred': 0, 'unresolved': 0}
assert observations['isolatedScenarios'] == len(observations['cases']) == 17
assert all(c['passed'] for c in observations['cases'])
assert len(observations['loadedSourceUnits']) == 8 and observations['loadedSourceBytes'] == 3408
stages = [('analyze-01', 0), ('verify-source-01', 1), ('analyze-02', 0), ('verify-source-02', 0), ('observe-01', 0)]
for stage, code in stages:
    receipt = json.loads((WORK / 'attempts' / stage / 'receipt.json').read_bytes())
    assert receipt['exitCode'] == code and receipt['sourcesUnchanged'] is True
for unit in source['selections']:
    assert pin((WORK / 'selected-source-02' / unit['localSourceFilename']).read_bytes()) == {'bytes': unit['bytes'], 'sha256': unit['sha256']}

planned, copies = {}, []


def copy(relative, path, kind='metadata_only'):
    raw = path.read_bytes()
    destination = 'raw/shutdown-persistence/' + relative
    assert destination not in planned
    planned[destination] = raw
    copies.append({'original': str(path), 'outputPath': destination, **pin(raw), 'kind': kind})


copy('author/contracts.json', WORK / 'selected-source-02/contracts.json')
copy('author/evidence.jsonl', WORK / 'selected-source-02/evidence.jsonl')
copy('author/observations.json', WORK / 'observations-01/observations.json')
copy('history/noncanonical-source-01-contracts.json', WORK / 'selected-source-01/contracts.json')
for stage, _ in stages:
    for path in sorted((WORK / 'attempts' / stage).iterdir()):
        copy('attempts/' + stage + '/' + path.name, path,
             'analysis_tool_source' if path.suffix in {'.py', '.mjs'} else 'execution_metadata')

reader = {**source, 'candidateObservations': {'path': 'shutdown-persistence-observations.json',
          'commands': 1, 'cases': 17, 'savedSourceUnitsLoaded': 8, 'loadedSourceBytes': 3408,
          'syntheticTimersAndApp': True, 'originalClientRunsAdded': 0},
          'historyQualification': {
              'analysis01': 'The analysis command exited zero, but subsequent byte verification failed: JXe and jXe selected filenames collided on the case-insensitive filesystem. This output is noncanonical and was not executed or integrated. The initial facade-host wording also mistook its uninitialized declaration for its later construction assignment.',
              'analysis02': 'Ordinal filenames plus exclusive writes prevent that collision. The later new hXe assignment was selected and checked against the same lexical host binding. All 19 saved units passed byte verification before the one observation command. The canonical successful attempt parses one Program; prior attempt is retained separately.'},
          'maintenanceProposal': {'confidence': 'inferred', 'mode': 'unknown', 'exclusionsAdded': 0,
              'modules': [
                  {'path': 'apps/desktop/src/main/lifecycle/quit-coordinator.ts',
                   'responsibility': 'First-party quit-confirmation decisions, reentry flag, branch-specific drain groups and app lifecycle adapter.',
                   'selections': ['eZe', 'normalQuitRegistration']},
                  {'path': 'apps/desktop/src/main/lifecycle/cleanup-timeout.ts',
                   'responsibility': 'Bounded waiting contract and separate 5s/12s callers; preserve rejection and noncancellation behavior in the recovered specification.',
                   'selections': ['u7', 'XXe', 'ZXe', 'JXe', 'l7', 'stopMicro']},
                  {'path': 'apps/desktop/src/main/lifecycle/context-disposal.ts',
                   'responsibility': 'Host/session cleanup sequence, network observer unsubscribe and logger finally boundary.',
                   'selections': ['facadeFlush', 'facadeHostConstruction', 'hostDispose', 'facadePreCleanup']}],
              'externalBoundaries': ['Electron lifecycle/dialog APIs', 'Runtime timers and Promise', 'objc-js/native privacy and Windows helpers', 'globalState/settingsStore/backend/tracing/session/logger interfaces'],
              'sourceDirectoryRecovered': False, 'clientImplementationGenerated': False,
              'thirdPartyImplementationRecovered': False}}
planned['shutdown-persistence.json'] = encode(reader)
planned['shutdown-persistence-observations.json'] = encode(observations)
summary = '''# 正常退出、保存与清理顺序

本批在冻结main Program中接上eZe的真实注册调用：globalState与settingsStore来自同一个V启动结果；上下文清理来自vXe facade，stop helper使用ZXe包装G.stopCodexMicro。共19个保存范围、20条源码事实。见[静态契约](shutdown-persistence.json)、[隔离观察](shutdown-persistence-observations.json)与[来源索引](shutdown-persistence-provenance.json)。这些是作用域核对和候选控制流结果，没有运行桌面应用的退出流程。

普通will-quit先preventDefault并设置重入标志，再依次调用两个生命周期管理器的dispose，构造globalState.flush、settingsStore.flush、stopCodexMicro、tracing的Promise.allSettled组。shouldSkipDrainBeforeQuit分支仍调用全局状态、stop和tracing，只省略settingsStore.flush。Promise rejection不会阻止该组继续；同步throw发生在数组求值或管理器清理时，则会跳过后续调用，而重入标志已经设置。再次触发will-quit会直接返回，不重复排空。

首组没有在eZe中套用整体超时。它结算后才调用u7(contextCleanup,5000)，随后dispose外层资源并app.quit。stop helper另有12000ms等待上限。u7先设计时器再调用回调，把回调返回Promise的成功和失败都转为完成；到期结束等待但不取消清理。回调同步抛错或返回非thenable会令外层Promise拒绝，并留下已安排的计时器；eZe后面的成功回调因此不会运行。不能把5000ms描述为整个退出过程的预算。

vXe facade先调用网络观察器的unsubscribe（ve），再在try中依次等待host.dispose及可选artifactSessionHostLifecycle.dispose，finally等待datadogLogger.flush。该x对象是日志参数，不是globalState；ve在try外，抛错会跳过finally。hXe.dispose则先停止远程连接／archives／host managers，等待threadProjectAssignments.flush，随后进入tab、message、terminal、registry、window和IPC清理；方法内部没有try/finally，中途失败会截断后续步骤。这个thread assignments接口也不能等同于全局状态文件保存。

实际执行1条本机Node22命令，在17个场景中加载8个保存的第一方单位3408字节。Electron事件由测试直接调用，app/dialog、native返回值、存储／backend／tracing／logger全部替换，时间由显式fake scheduler推进。观察到首组等待超过合成5000ms仍未开始上下文清理、skip省略设置、重入不重复排空、同步／异步错误的不同结果、5s/12s限时及超时后仍能完成的回调；另覆盖确认／取消／privacy替身、待建worktree条件、facade日志finally和host清理截断。没有真实计时、文件I/O、native加载、CLI、原存储实例或模型提交。

macOS关机observer及privacy查询保留为静态边界，objc-js与平台插件不执行。原应用的Electron事件送达、Windows helper、真实settings/backend清理、SIGTERM是否走这些hook，以及任务变为interrupted的完整机制仍未知。[已授权停止／重启](behavior-stop-restart-summary.md)是独立的真实UI观察，不能由本批替身结果补写其未观察过程。全部模式归属仍未知，未增加ChatGPT专属排除项或完整功能分母。

维护建议把退出协调、限时等待和上下文清理拆为三个第一方职责；Electron、运行时计时器／Promise和objc-js通过依赖与adapter边界接入，不生成第三方实现。该目录是inferred建议，不是恢复出的原源码目录。首次范围文件命名发生大小写冲突，字节检查失败后改为带序号且禁止覆盖的文件名；同时补齐host实际构造赋值。失败检查和两次分析记录均保留，只有后一次19范围用于执行与本批发布。
'''
planned['shutdown-persistence-summary.md'] = summary.encode()
index = {'schemaVersion': 1, 'baselineId': BASELINE,
         'kind': 'scoped-normal-quit-source-and-synthetic-control-flow-observations',
         'publishedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'exactCopies': copies,
         'derived': [{'path': n, **pin(planned[n])} for n in ['shutdown-persistence.json', 'shutdown-persistence-observations.json', 'shutdown-persistence-summary.md']],
         'sourceRecords': 20, 'successfulAnalysisPrograms': 1, 'sourceSelections': 19,
         'confidenceCounts': source['confidenceCounts'], 'isolatedObservationCommands': 1, 'isolatedScenarioCount': 17,
         'savedSourceUnitsLoaded': 8, 'executedSavedSourceBytes': 3408, 'syntheticTimersAndApp': True,
         'originalClientRunsAdded': 0, 'originalStorageInstanceRunsAdded': 0, 'deliveryRuntimeRunsAdded': 0,
         'modelSubmissionsAdded': 0, 'globalRecordsAdded': 0, 'newReaRuns': 0,
         'thirdPartyImplementationsPublished': False, 'fullAnalysisCompleted': False}
planned['shutdown-persistence-provenance.json'] = encode(index)

names = ['report.md', 'analysis-state.json', 'implementation-plan.md', 'gaps.md', 'dependency-import-decisions.md', 'behavior-checks.md']
before = {n: (OUT / n).read_bytes() for n in names}
old = json.loads(before['analysis-state.json'])
assert len(old) == 88 and old['fullAnalysisCompleted'] is False and old['featureDenominatorEstablished'] is False
assert old['latestBehaviorAuthorizationState']['groupRemaining'] == 0 and 'shutdownPersistence' not in old
for name in planned:
    assert not (OUT / name).exists()
for name, raw in planned.items():
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    path.chmod(0o444)
patch, _, artifacts = build_context(OUT, BASELINE)
assert len(patch) == len(PROFILES) == 23
assert all(old[k] == v for k, v in patch.items() if k != 'shutdownPersistence')
state = {**old, 'shutdownPersistence': patch['shutdownPersistence']}
assert all(state[k] == v for k, v in old.items())
note = next(p[4] for p in PROFILES if p[0] == 'shutdownPersistence')
marker = '[完成标准审计](criteria-audit.md)'
report = before['report.md'].decode()
assert report.count(marker) == 1
changes = {'report.md': report.replace(marker, note + '\n\n' + marker).encode(), 'analysis-state.json': encode(state)}
extras = {
 'implementation-plan.md': '\n\n[正常退出与清理合同](shutdown-persistence-summary.md)给出退出协调、限时等待与上下文清理三个inferred维护职责。保留普通／skip分支、数组同步错误、重入标志、首组无整体超时及context限时不取消的边界；logger finally与全局状态保存分开。先用声明接口引入Electron、计时器、objc-js及存储／backend，不生成依赖实现；17个替身场景不证明桌面关闭或完整任务恢复。\n',
 'gaps.md': '\n\n[正常退出来源](shutdown-persistence-summary.md)补齐eZe→启动状态／stop helper／vXe facade→hXe.dispose的所选静态关系，20事实与17替身场景分别登记。首组等待没有整体5秒上限，skip仍flush全局状态，facade最终flush的是datadogLogger。原Electron hook送达、settings与backend真实排空、native/Windows分支和SIGTERM机制仍未知，不能反推实际interrupted任务的持久化过程；模型预算余0，全局分母与模式排除保持。\n',
 'behavior-checks.md': '\n\n[退出隔离观察](shutdown-persistence-summary.md)为1条Node22命令／17场景／8保存单位3408字节；事件、native与后台接口均为替身，时间由fake scheduler推进。覆盖组等待／skip／重入、同步错误和Promise rejection、5s/12s超时不取消、确认／取消／privacy候选、facade finally及host清理截断。没有原应用、真实时间／文件写入、新模型任务或SIGTERM hook观察；与已授权停止／重启的真实UI结果分列。\n',
 'dependency-import-decisions.md': '\n\n[退出清理边界](shutdown-persistence-summary.md)把Electron生命周期／dialog、运行时Promise／timers、objc-js与平台插件、存储和backend接口留作外部依赖；所选退出协调与清理编排属于第一方。17个合成场景没有加载native或依赖实现，不增加第三方源码恢复，也不证明目标Electron/Owl ABI或平台行为。\n',
}
for name, extra in extras.items():
    changes[name] = before[name] + extra.encode()
readme_before = (ROOT / 'README.md').read_bytes()
readme = readme_before + ('\n- [正常退出、状态保存与17个隔离场景](analysis/' + BASELINE + '/shutdown-persistence-summary.md)\n').encode()
snapshots = {'raw/shutdown-persistence/reader-before/' + n: raw for n, raw in before.items()}
snapshots['raw/shutdown-persistence/reader-before/README.md'] = readme_before
for name, raw in snapshots.items():
    path = OUT / name
    assert not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    path.chmod(0o444)
for name, raw in changes.items():
    path = OUT / name
    assert path.read_bytes() == before[name]
    temp = path.with_name('.shutdown-persistence-' + path.name)
    assert not temp.exists()
    temp.write_bytes(raw)
    temp.chmod(path.stat().st_mode & 0o777)
    temp.replace(path)
assert (ROOT / 'README.md').read_bytes() == readme_before
temp = ROOT / '.shutdown-persistence-README.md'
assert not temp.exists()
temp.write_bytes(readme)
temp.chmod((ROOT / 'README.md').stat().st_mode & 0o777)
temp.replace(ROOT / 'README.md')
print(json.dumps({'status': 'published-and-integrated', 'companionIndices': len(patch),
 'oldStateKeysPreserved': len(old), 'oldStateValuesPreserved': True, 'sourceRecords': 20, 'isolatedScenarios': 17,
 'selectedArtifactsBeforeOwnCapture': len(artifacts),
 'snapshots': [{'path': n, **pin(raw)} for n, raw in snapshots.items()],
 'outputs': {n: pin(raw) for n, raw in changes.items()}, 'modelSubmissionsAdded': 0, 'fullAnalysisCompleted': False}))
