"""Publish scoped construction/source and candidate file-observation evidence."""
import datetime
import hashlib
import json
from pathlib import Path

from contract_reader_context import PROFILES, build_context

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASELINE
WORK = ROOT / '.analysis-local/global-state-storage-work'


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


source = json.loads((WORK / 'selected-source-02/contracts.json').read_bytes())
observations = json.loads((WORK / 'observations-01/observations.json').read_bytes())
assert len(source['parses']) == 3 and len(source['selections']) == 33 and len(source['records']) == 37
assert source['confidenceCounts'] == {'confirmed': 37, 'inferred': 0, 'unresolved': 0}
assert source['targetCodeExecuted'] is False and observations['observationCommands'] == 1
assert len(observations['cases']) == observations['isolatedScenarios'] == 9 and all(x['passed'] for x in observations['cases'])
assert len(observations['loadedSourceUnits']) == 13 and observations['loadedSourceBytes'] == 4774
assert observations['schemaCalls'] == observations['defaultCalls'] == observations['archiveComparatorCalls'] == 0
assert observations['realLocalFileIo'] and observations['originalClientRunsAdded'] == observations['originalStorageInstanceRunsAdded'] == 0
for stage, expected_code in [('tool-install-01', 1), ('tool-install-02', 0), ('analyze-01', 1), ('analyze-02', 0), ('observe-01', 0)]:
    receipt = json.loads((WORK / 'attempts' / stage / 'receipt.json').read_bytes())
    assert receipt['exitCode'] == expected_code
    if 'sourcesUnchanged' in receipt:
        assert receipt['sourcesUnchanged']

planned = {}
copies = []


def copy(relative, path, kind='metadata_only'):
    raw = path.read_bytes()
    destination = 'raw/global-state-storage-origin/' + relative
    assert destination not in planned
    planned[destination] = raw
    copies.append({'original': str(path), 'outputPath': destination, **pin(raw), 'kind': kind})


copy('author/contracts.json', WORK / 'selected-source-02/contracts.json')
copy('author/evidence.jsonl', WORK / 'selected-source-02/evidence.jsonl')
copy('author/observations.json', WORK / 'observations-01/observations.json')
copy('tooling/package.json', WORK / 'tooling/package.json', 'analysis_tool_metadata')
copy('tooling/package-lock.json', WORK / 'tooling/package-lock.json', 'analysis_tool_metadata')
for stage in ['tool-install-01', 'tool-install-02', 'analyze-01', 'analyze-02', 'observe-01']:
    directory = WORK / 'attempts' / stage
    for path in sorted(directory.iterdir()):
        kind = 'analysis_tool_source' if path.suffix in {'.mjs', '.py'} else 'execution_metadata'
        copy('attempts/' + stage + '/' + path.name, path, kind)

reader = {**source, 'candidateObservations': {'path': 'global-state-storage-observations.json',
    'commands': 1, 'cases': 9, 'savedSourceUnitsLoaded': 13, 'loadedSourceBytes': 4774,
    'originalClientRunsAdded': 0, 'originalStorageInstanceRunsAdded': 0, 'actualTargetRuntimeParityEstablished': False},
    'historyQualification': {'toolInstall01': 'Failed with ENOTFOUND in the restricted environment; completed command and stderr retained.',
        'toolInstall02': 'Four packages from the previous analysis lock installed successfully with scripts disabled; exact lock unchanged.',
        'analysis01': 'Stopped at bootstrap export lookup because the first script expected a getter; the actual bootstrap uses an exports.U assignment. Partial selections retained locally; no complete contracts were emitted.',
        'analysis02': 'Corrected export assignment handling; the successful contract output describes three Program parses in this attempt, not total parse invocations across failed and successful attempts.'},
    'maintenanceProposal': {'confidence': 'inferred', 'mode': 'unknown', 'exclusionsAdded': 0,
        'modules': [
            {'path': 'apps/desktop/src/main/persistence/global-state.ts', 'selections': ['Vr', 'm', 'Or', 'Ur', 'Hr'],
             'responsibility': 'First-party memory/default/listener interface and queued persistence, retaining schema and archive-comparison dependencies.'},
            {'path': 'apps/desktop/src/main/persistence/json-file.ts', 'selections': ['Wr', 'Gr', 'Kr', 'qr', 'Jr', 'Yr', 'Xr', 'Zr', 'Ar'],
             'responsibility': 'JSON load, backup policy and temp-file replacement, with declared runtime filesystem/path/crypto/timer dependencies.'}],
        'sourceDirectoryRecovered': False, 'thirdPartyImplementationRecovered': False}}
planned['global-state-storage-origin.json'] = encode(reader)
planned['global-state-storage-observations.json'] = encode(observations)
summary = '''# globalState 构造、文件写入与恢复边界

本批对3个冻结Program作作用域分析，保存33个选定AST范围和37条静态事实：main中的await g.U启动结果，经bootstrap导出的gT、uT(home)和startup的D/Vr构造，返回为globalState，再经vXe/hXe.scopedState传给MMe第9个实参并写入this.globalState。路径是源码中的构造和注入关系；未读取原应用的实际对象或home。见[静态契约](global-state-storage-origin.json)、[候选行为结果](global-state-storage-observations.json)及[来源索引](global-state-storage-origin-provenance.json)。

Vr把状态放在Map中，主文件名为.codex-global-state.json。普通set先改内存、安排写入、同步通知监听器；atom键使用500ms防抖，custom-runtime两键使用microtask合并，其他键直接排队。窗口随后广播不代表文件已写完。flush调用会记录并吞掉写入错误的qr；flushOrThrow使用会抛出的Jr。updateAndPersist另走同步写主文件后才改内存的提交路径；备份或监听器错误各自捕获并记录。不能把这些不同接口合并成同一种“写入完成”保证。

加载时，主文件不存在便返回空Map，不读取单独存在的备份；主文件存在但读取／解析失败时才尝试.bak。写入先序列化到同目录的临时文件，再重命名到目标；普通异步提交先主文件、后备份。所选写入函数没有fsync，主文件与备份没有整体回滚。Windows的特定rename错误有100/200/400ms重试，本批未执行这些平台分支。

实际运行了1条本机Node22命令，共9个隔离场景，执行13个保存的第一方单位4774字节，使用带路径限制的真实文件I/O。观察到atom内存先更新、显式flush完成主／备份写入、自建值可重开；缺失主文件不读备份、损坏主文件读取有效备份；flush错误被吞而flushOrThrow抛ENOENT，之后队列可恢复；updateAndPersist主写失败时旧内存保留，而备份失败时主提交／内存／通知已成功。另区分普通set与已提交更新的监听器错误，并观察两次atom更新在显式flush时只做一对主／备份替换。

这些场景使用空的已知schema集合和合成logger；schema、默认值与archives比较器调用次数均为0。没有运行原应用、实际globalState实例、个人profile、CLI或模型服务；本机Node22不证明目标Node24/Owl、Windows、定时器自然到期、正常关闭flush或断电耐久性。CLI/backend的任务记录可能使用其他存储，本批不能解释原turn变为interrupted的完整机制。

维护建议将第一方global-state接口／队列和JSON文件后端分为两个职责路径，8个以上原范围的逐项映射在契约中；Node fs、path、crypto及timers作为运行时依赖引入，schema和比较器保持独立依赖边界。没有生成客户端源码或第三方实现。首次受限下载ENOTFOUND和首次导出形式假设错误均已保留，后续固定工具安装与修正后的完整分析成功；37条记录不是对旧全局证据或完整功能分母的加算。
'''
planned['global-state-storage-origin-summary.md'] = summary.encode()
index = {'schemaVersion': 1, 'baselineId': BASELINE, 'kind': 'scoped-state-construction-source-and-candidate-io-observations',
    'publishedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'exactCopies': copies,
    'derived': [{'path': n, **pin(planned[n])} for n in ['global-state-storage-origin.json', 'global-state-storage-observations.json', 'global-state-storage-origin-summary.md']],
    'sourceRecords': 37, 'successfulAnalysisPrograms': 3, 'sourceSelections': 33,
    'confidenceCounts': source['confidenceCounts'], 'isolatedObservationCommands': 1, 'isolatedScenarioCount': 9,
    'savedSourceUnitsLoaded': 13, 'executedSavedSourceBytes': 4774, 'realLocalFileIo': True,
    'originalClientRunsAdded': 0, 'originalStorageInstanceRunsAdded': 0, 'deliveryRuntimeRunsAdded': 0,
    'savedFirstPartySourceExecutedInCandidate': True, 'originalClientExecuted': False,
    'modelSubmissionsAdded': 0, 'globalRecordsAdded': 0, 'fullAnalysisCompleted': False,
    'newReaRuns': 0, 'thirdPartyImplementationsPublished': False}
planned['global-state-storage-origin-provenance.json'] = encode(index)

names = ['report.md', 'analysis-state.json', 'implementation-plan.md', 'gaps.md', 'dependency-import-decisions.md', 'behavior-checks.md']
before = {n: (OUT / n).read_bytes() for n in names}
old = json.loads(before['analysis-state.json'])
assert len(old) == 87 and old['fullAnalysisCompleted'] is False and old['featureDenominatorEstablished'] is False
assert old['latestBehaviorAuthorizationState']['groupRemaining'] == 0 and 'globalStateStorageOrigin' not in old
for name in planned:
    assert not (OUT / name).exists()
for name, raw in planned.items():
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    path.chmod(0o444)
patch, _, artifacts = build_context(OUT, BASELINE)
assert len(patch) == len(PROFILES) == 22
assert all(old[k] == v for k, v in patch.items() if k != 'globalStateStorageOrigin')
state = {**old, 'globalStateStorageOrigin': patch['globalStateStorageOrigin']}
assert all(state[k] == v for k, v in old.items())
note = next(p[4] for p in PROFILES if p[0] == 'globalStateStorageOrigin')
marker = '[完成标准审计](criteria-audit.md)'
report = before['report.md'].decode()
assert report.count(marker) == 1
changes = {'report.md': report.replace(marker, note + '\n\n' + marker).encode(), 'analysis-state.json': encode(state)}
extras = {
    'implementation-plan.md': '\n\n[globalState源码与9个候选文件场景](global-state-storage-origin-summary.md)提供global-state接口／队列和JSON文件后端两个inferred维护路径。保持set的内存先行、显式flush两种错误策略、updateAndPersist的提交边界、备份读取条件及主／备份写入顺序；保留schema/default/archives依赖。独立源码构建需声明Node fs/path/crypto/timer接口并核对目标运行时，不能用本机候选观察证明完整任务恢复或原实例耐久性。\n',
    'gaps.md': '\n\n[globalState构造与文件后端](global-state-storage-origin-summary.md)现已用3个冻结Program接上静态注入关系，37条事实说明Vr的Map、延迟调度、flush策略和JSON/备份方法。9个本机真实文件隔离场景补候选控制流与文件结果；不关闭实际home／实例、schema/default/archives、Node24/Owl、Windows重试、正常关闭flush和CLI/backend任务持久化。原turn的interrupted只能保留原UI观察结论。完整功能分母、模式排除数及模型预算均不改。\n',
    'dependency-import-decisions.md': '\n\n[globalState文件后端](global-state-storage-origin-summary.md)的Map／调度／JSON编排属于第一方，选定源码直接require node:fs、node:fs/promises、node:path、node:crypto及node:timers/promises；将它们声明为运行时依赖，不恢复第三方实现。本批重新取得的4个Babel包仅用于分析，沿用旧工具lock的固定版本，不计为客户端依赖。schema/default/archives比较器和Owl运行时的实际接口语义仍需核对。\n',
    'behavior-checks.md': '\n\n[globalState候选文件观察](global-state-storage-origin-summary.md)实际为1条Node22命令／9场景／13保存单位4774字节，使用自建目录真实文件I/O。明确观察缺失／损坏主文件不同回退、set先内存、flush两类错误、主提交与备份失败及监听器分支；空schema集合与合成logger替身分列，schema/default/archives均0调用。没有原应用／存储实例或新模型任务；未覆盖Windows、定时器自然到期、关闭flush、断电及任务后端恢复。\n',
}
for name, extra in extras.items():
    changes[name] = before[name] + extra.encode()
stale = '[行为样例](behavior-interventions-summary.md)本组已用1/2；取消0次点击、执行中恢复0次介入。第二条因原项目名称／ID控件均0而未发送，原因尚未知，剩余1次保留。仅此运行场景的前置条件不可用，其他静态分析继续。恢复README同字节不算持续存储证明；自有应用清理已核实。'
gaps = changes['gaps.md'].decode()
assert gaps.count(stale) == 1
gaps = gaps.replace(stale, '项目恢复前的[行为中间快照](behavior-interventions-summary.md)当时为本组已用1/2、原项目控件缺失。后续明确授权重新登记同一目录并完成第2条；[当前实际结果](behavior-stop-restart-summary.md)为2/2已用、余0，停止／重启后原turn为interrupted、未观察到继续执行；取消仍未测。自有应用已清理，README同字节恢复不证明持续存储。')
changes['gaps.md'] = gaps.encode()
readme_before = (ROOT / 'README.md').read_bytes()
readme = readme_before + ('\n- [globalState构造、文件写入与9个候选行为场景](analysis/' + BASELINE + '/global-state-storage-origin-summary.md)\n').encode()
snapshots = {'raw/global-state-storage-origin/reader-before/' + n: raw for n, raw in before.items()}
snapshots['raw/global-state-storage-origin/reader-before/README.md'] = readme_before
for name, raw in snapshots.items():
    path = OUT / name
    assert not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    path.chmod(0o444)
for name, raw in changes.items():
    path = OUT / name
    assert path.read_bytes() == before[name]
    temp = path.with_name('.global-state-storage-' + path.name)
    assert not temp.exists()
    temp.write_bytes(raw)
    temp.chmod(path.stat().st_mode & 0o777)
    temp.replace(path)
assert (ROOT / 'README.md').read_bytes() == readme_before
temp = ROOT / '.global-state-storage-README.md'
assert not temp.exists()
temp.write_bytes(readme)
temp.chmod((ROOT / 'README.md').stat().st_mode & 0o777)
temp.replace(ROOT / 'README.md')
print(json.dumps({'status': 'published-and-integrated', 'companionIndices': len(patch),
    'oldStateKeysPreserved': len(old), 'oldStateValuesPreserved': True, 'sourceRecords': 37, 'isolatedScenarios': 9,
    'selectedArtifactsBeforeOwnCapture': len(artifacts),
    'snapshots': [{'path': n, **pin(raw)} for n, raw in snapshots.items()],
    'outputs': {n: pin(raw) for n, raw in changes.items()}, 'modelSubmissionsAdded': 0, 'fullAnalysisCompleted': False}))
