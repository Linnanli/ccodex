"""Publish bounded host state source contracts and synthetic observations once."""
import datetime
import hashlib
import json
from pathlib import Path
from contract_reader_context import PROFILES, build_context

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/host-state-provider-work'
AUTHOR = WORK / 'author-01'
PREFIX = 'raw/host-state-provider/'


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def read(path):
    return json.loads(path.read_bytes())


contract = read(AUTHOR / 'host-state-provider-contracts.json')
counts = read(AUTHOR / 'counts.json')
verification = read(WORK / 'verification-01.json')
assert verification['status'] == 'passed' and verification['uniqueSourceSpansChecked'] == 5153
assert len(contract['facts']) == 28 and len(contract['selectedUnits']) == 75
assert len(contract['programLexicalJoins']) == 328 and len(contract['qualifiedImportExportUses']) == 9
stages = ['analyze-01', 'trace-01', 'main-01', 'bridge-01', 'snapshot-01', 'receiver-01',
          'observe-01', 'curate-01', 'verify-author-01']
for stage in stages:
    receipt = read(WORK / 'attempts' / stage / 'receipt.json')
    assert receipt['exitCode'] == 0 and receipt['sourcesUnchanged']
planned = {}
copies = []


def copy(relative, path, kind='analysis_metadata'):
    data = path.read_bytes()
    destination = PREFIX + relative
    assert destination not in planned
    planned[destination] = data
    copies.append({'original': str(path), 'outputPath': destination, **pin(data), 'kind': kind})


names = ['host-state-provider-contracts.json', 'host-state-provider-scenarios.json']
for name in names:
    copy('author/' + name, AUTHOR / name)
    planned[name] = (AUTHOR / name).read_bytes()
copy('author/counts.json', AUTHOR / 'counts.json')
copy('author/verification-01.json', WORK / 'verification-01.json')
planned['host-state-provider-observations.json'] = (WORK / 'observations-01.json').read_bytes()
copy('observations/observations-01.json', WORK / 'observations-01.json', 'synthetic_vm_observations')
for number in range(1, 7):
    folder = WORK / f'source-{number:02}'
    for path in sorted(folder.iterdir()):
        assert path.suffix in ['.txt', '.json']
        copy('analysis/' + folder.name + '/' + path.name, path,
             'selected_application_source_including_explicit_rejected_candidate' if path.suffix == '.txt' else 'analysis_metadata')
for stage in stages:
    for path in sorted((WORK / 'attempts' / stage).iterdir()):
        copy('attempts/' + stage + '/' + path.name, path,
             'analysis_tool_source' if path.suffix in ['.py', '.mjs'] else 'execution_metadata')
records = []
for fact in contract['facts']:
    ref = fact['sourceReferences'][0]
    records.append({'id': fact['id'], 'baselineId': BASE, 'claim': fact['claim'],
                    'sourcePath': ref['sourcePath'], 'sourceHash': ref['sourceHash'],
                    'locator': {'kind': 'byte-range', **ref['byteRange']}, 'spanHash': ref['spanHash'],
                    'sourceReferences': fact['sourceReferences'], 'method': fact['method'],
                    'confidence': fact['confidence'], 'verificationStatus': fact['verificationStatus'],
                    'qualification': fact['qualification'], 'mode': 'unknown',
                    'newGlobalEvidenceRecord': False, 'actualUiControlExecuted': False})
planned['host-state-provider-evidence.jsonl'] = ('\n'.join(json.dumps(x, ensure_ascii=False) for x in records) + '\n').encode()
summary = '''# 主机选择、共享快照与状态更新

Q6已连接到主机选择hook p8a；共享配置的NI订阅、preload缓存和首次快照IPC channel也已分别定位。见[28条限定合同](host-state-provider-contracts.json)、[证据行](host-state-provider-evidence.jsonl)、[26项隔离观察](host-state-provider-observations.json)、[8条待执行UI规格](host-state-provider-scenarios.json)和[完整归档索引](host-state-provider-provenance.json)。本批补充固定基线的完整Program作用域分析，没有新的REA执行；上一批REA语义unknown与8815未知项保持。

| 状态层 | 已确认的源码行为 | 仍未知 |
| --- | --- | --- |
| 所选主机p8a | 插件host、settings query、h8a依次取候选；按访问资格及连接状态选择ID | 实际React provider、连接查询Zs/a8a及dNn合并规则 |
| 共享对象NI | 从快照取初值，按键订阅更新；setter先登记历史，再发送，最后写本地值 | 真实store实例、消息送达及跨窗口一致性 |
| preload快照A | 同步IPC取初值；shared-object-set先更新A再invoke | 真实IPC成功／失败与上层恢复策略 |
| main共享仓库wee | 内存对象、浅快照、同步订阅通知；所选构造初始化Local配置 | MMe与hXe的仓库注入是否同实例、上游持久化 |

p8a的插件详情hostId优先且未在此trim；只有settings路径才读取并trim query hostId，空字符串经||回退h8a。访问条件Ge来自shared.AAt→ejn，沿用此前pq本地访问资格；它不是home composer的chat/work偏好。连接数据或状态尚未得到时s8a返回undefined，u8a会保留未知候选；得到列表后，候选不在connected列表且不是local才回退local。这与后续pzt描述符的未知ID回退是两个状态层。

h8a由fd(q,as)创建，fd经shared.don连接Uk signal工厂，此调用没有传持久化key；不能据此认定它已经落盘，实际scope/store和存储策略仍未知。setter先store.set(h8a,id)，再更新路由：插件详情跳回/settings/plugins-settings并replace；普通settings仅在query已有hostId时修改，不额外创建该参数。后续同步导航异常不会在所选函数内回滚已经完成的状态写入。

NI的初始化器通过可选bridge getter读取快照。onMount先登记shared-object-updated listener，再发送subscribe；清理先退listener再发unsubscribe。izt先调用历史管理替身对应的tRt，随后dispatch shared-object-set，最后e.set；Object.is相等只跳过历史项，仍发送和更新。Hf/Vf/ire继续连接可选electronBridge及window事件；bridge返回Promise的catch处理不能证明main已经收到或保存。

preload的A由sendSync(codex_desktop:get-shared-object-snapshot)??{}初始化；getter直接读A[key]。发送shared-object-set时先更新A，再await ipcRenderer.invoke；所选函数没有失败回滚。接收非chunked的shared-object-updated也先更新A，再派发window MessageEvent。这里确认的是源代码顺序，没有新增真实Electron或IPC观察。

首次快照注册者为main.$Xe，使用g.kt；g require bootstrap，而bootstrap实际exports.kt=Pt，Pt才是快照channel字面值。callback先调用isTrustedIpcEvent，拒绝时返回{}，否则调用getContextForWebContents(sender)?.getSharedObjectSnapshot()??{}。hXe的同名方法委托其仓库getSnapshot。实际$Xe调用参数、context resolver实例及与MMe仓库的注入连接仍需核对，不能以同名字段代替同实例证明。

wee小类本身没有持久化I/O：undefined删除，其他值赋入，随后同步通知；listener抛错会在值已改变后中断后续listener。所选hXe构造new wee，并以startup.m初始化host_config；该导出getter连接$r={id:local,display_name:Local,kind:local}。另保存SSH／WSL／remote-control的set调用位置及SSH空数组初始化，但只覆盖完整调用范围，没有推断整套发现、保存或远程连接机制。MMe的subscribe按sender/key引用计数并立即发送当前值，unsubscribe减计数，destroyed清理；实际外层接收器验证与实例仍未观察。

一次Node22 VM命令加载9个保存单位共2243字节，含7函数、1类及1工厂赋值；26项合成场景全部通过。覆盖候选优先级、trim、连接缺失／断开、状态先写后导航及异常、快照初值、订阅／清理顺序、函数更新、相等值仍发送、仓库删除／浅拷贝和listener异常。router/access/store/status/memo/bridge/history均为明确替身，原t8a查询、Uk、Vf、preload及真实IPC未执行；没有客户端启动、设置修改或模型提交。这些结果不升级真实功能验收。

六条分析命令共完成14次完整Program解析，涉及6个不同源码文件。形成26条源码事实／2条设计推断，75个去重规范AST单位（长度合计12450字节，含重叠）、328处词法位置及9项跨模块连接。作者字节核对检查8源码文件、5153个唯一范围和13008次坐标出现，原始79个保存选段与规范75单位均一致；这不是新增独立语义审查。

source-05曾按未限定名称误选7144字节QXe，已从规范合同剔除；bootstrap的defineProperty导出搜索为空，也未作为不存在channel的证据。source-06改按真实getSharedObjectSnapshot callee和exports.kt=Pt赋值定位。两项派生候选错误、原文件和完整执行记录均保留；没有重跑26项VM观察来改写历史结果。

重建工程可按主机选择与路由、连接状态过滤、共享订阅桥和主进程内存仓库划分职责。合同中的features/hosts、platform/shared-objects、services/shared-objects只是维护设计建议，并非找回原作者目录。React、路由、状态和Electron实现通过依赖引入；上游持久化应另立明确合同，不能把内存仓库替换成任意文件存储后宣称等价。

原37项有限功能、40用户操作／5机制／26队列、160条未执行功能规格、967未映射旧入口及337 deferred保持。新增8条UI规格全部未执行且单独计数，模式归属与确认排除仍未增加。获批模型样例组2/2已使用、剩余0；停止／重启的既有interrupted观察保留。本批收窄provider与配置来源缺口，下一步应继续核对仓库构造注入和连接状态查询，再决定哪些行为能够独立重建；完整功能分母和总体分析目标仍未闭合。
'''
planned['host-state-provider-summary.md'] = summary.encode()
index = {'schemaVersion': 1, 'baselineId': BASE,
         'kind': 'bounded-host-state-provider-snapshot-and-synthetic-observations',
         'publishedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'exactCopies': copies,
         'derived': [{'path': name, **pin(planned[name])} for name in names +
                     ['host-state-provider-observations.json', 'host-state-provider-evidence.jsonl', 'host-state-provider-summary.md']],
         **counts, 'analysisCommands': 6, 'newReaCommandAttempts': 0,
         'rejectedDerivedSelections': 2, 'runtimeRunsAdded': 1, 'isolatedObservationCommands': 1,
         'savedSourceUnitsLoaded': 9, 'savedFunctionsLoaded': 7, 'savedClassesLoaded': 1,
         'savedFactoryAssignmentsLoaded': 1, 'executedSavedSourceBytes': 2243,
         'originalClientRunsAdded': 0, 'originalStorageInstanceRunsAdded': 0,
         'modelSubmissionsAdded': 0, 'actualIpcMessagesAdded': 0, 'actualSettingsMutationsAdded': 0,
         'newFeatureDefinitions': 0, 'newModeAssignments': 0, 'newConfirmedExclusions': 0, 'globalRecordsAdded': 0,
         'uniqueSourceSpansChecked': 5153, 'sourceCoordinateOccurrencesChecked': 13008,
         'sourceFilesByteChecked': 8, 'targetCodeExecuted': True,
         'targetExecutionScope': 'Saved host selection/shared state/repository units in synthetic Node VM only.',
         'syntheticProvidersOnly': True, 'clientDependencyImplementationGenerated': False,
         'independentSemanticPeerReviewAdded': False, 'featureDenominatorEstablished': False,
         'fullAnalysisCompleted': False}
planned['host-state-provider-provenance.json'] = encode(index)
readers = ['report.md', 'analysis-state.json', 'implementation-plan.md', 'gaps.md', 'behavior-checks.md']
before = {name: (OUT / name).read_bytes() for name in readers}
old = json.loads(before['analysis-state.json'])
assert len(old) == 95 and 'hostStateProvider' not in old and not old['fullAnalysisCompleted']
assert old['latestBehaviorAuthorizationState']['groupRemaining'] == 0
for item in contract['inputPins']:
    assert pin((OUT / item['path']).read_bytes()) == {k: item[k] for k in ['bytes', 'sha256']}
previous_patch, _, _ = build_context(OUT, BASE)
assert len(previous_patch) == 29 and all(old[key] == value for key, value in previous_patch.items())
for name in planned:
    assert not (OUT / name).exists()
for name, data in planned.items():
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(0o444)
patch, _, artifacts = build_context(OUT, BASE)
assert len(patch) == len(PROFILES) == 30
assert all(old[key] == value for key, value in patch.items() if key != 'hostStateProvider')
state = {**old, 'hostStateProvider': patch['hostStateProvider']}
assert all(state[key] == value for key, value in old.items())
note = next(p[4] for p in PROFILES if p[0] == 'hostStateProvider')
marker = '[完成标准审计](criteria-audit.md)'
report = before['report.md'].decode()
assert report.count(marker) == 1
changes = {'analysis-state.json': encode(state), 'report.md': report.replace(marker, note + '\n\n' + marker).encode()}
extra = {
    'implementation-plan.md': '\n\n[主机选择与共享快照](host-state-provider-summary.md)支持按选择／路由、连接过滤、订阅桥与主进程共享仓库分责。状态先写后导航、preload先更新缓存再invoke、相等值仍发送需保留；存储策略和仓库同实例仍需明确。目录为维护设计推断，第三方实现继续由依赖引入；26合成场景不等于真实UI验收。\n',
    'gaps.md': '\n\n[主机provider增量](host-state-provider-summary.md)接上Q6定义、NI/preload及实际首次快照channel，保留两项派生候选纠正。MMe／hXe仓库注入、真实React provider、dNn/Zs连接查询、context resolver及上游耐久保存仍未闭合。无新REA执行或模式归属，26合成观察与8未执行UI规格分列，原37功能／26队列／160规格保持。\n',
    'behavior-checks.md': '\n\n[主机状态26项隔离观察](host-state-provider-observations.json)由一次Node22 VM命令完成，执行9单位2243字节；router/access/store/status/memo/bridge/history均为显式替身。[8条新增UI规格](host-state-provider-scenarios.json)全部未执行，不升级原160条功能规格。没有新增真实客户端、IPC、设置修改或模型提交；既有模型样例授权余0。\n',
}
for name, text in extra.items():
    changes[name] = before[name] + text.encode()
readme_before = (ROOT / 'README.md').read_bytes()
readme = readme_before + ('\n- [主机选择与共享快照：来源链及26项合成观察](analysis/' + BASE + '/host-state-provider-summary.md)\n').encode()
snapshots = {PREFIX + 'reader-before/' + name: data for name, data in before.items()}
snapshots[PREFIX + 'reader-before/README.md'] = readme_before
for name, data in snapshots.items():
    path = OUT / name
    assert not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(0o444)
for name, data in changes.items():
    path = OUT / name
    assert path.read_bytes() == before[name]
    temporary = path.with_name('.host-state-provider-' + path.name)
    assert not temporary.exists()
    temporary.write_bytes(data)
    temporary.chmod(path.stat().st_mode & 0o777)
    temporary.replace(path)
assert (ROOT / 'README.md').read_bytes() == readme_before
temporary = ROOT / '.host-state-provider-README.md'
assert not temporary.exists()
temporary.write_bytes(readme)
temporary.chmod((ROOT / 'README.md').stat().st_mode & 0o777)
temporary.replace(ROOT / 'README.md')
print(json.dumps({'status': 'published-and-integrated', 'companionIndices': len(patch),
                  'oldStateKeysPreserved': len(old), 'newStateKeys': 1,
                  'selectedArtifactsBeforeOwnCapture': len(artifacts),
                  'snapshots': [{'path': name, **pin(data)} for name, data in snapshots.items()],
                  'outputs': {name: pin(data) for name, data in changes.items()},
                  'modelSubmissionsAdded': 0, 'fullAnalysisCompleted': False}))
