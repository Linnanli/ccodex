"""Publish bounded settings callers, REA subset and synthetic host observations once."""
import datetime
import hashlib
import json
from pathlib import Path
from contract_reader_context import PROFILES, build_context

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/settings-entry-callers-work'
AUTHOR = WORK / 'author-01'
PREFIX = 'raw/settings-entry-callers/'


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def read(path):
    return json.loads(path.read_bytes())


contract = read(AUTHOR / 'settings-entry-callers-contracts.json')
verification = read(WORK / 'verification-01.json')
assert verification['status'] == 'passed' and verification['uniqueSourceSpansChecked'] == 426
assert len(contract['facts']) == 24 and len(contract['selectedUnits']) == 67
assert len(contract['programLexicalJoins']) == 270 and len(contract['qualifiedImportExportUses']) == 6
stages = ['install-01', 'install-online-01', 'analyze-01', 'hosts-01', 'qualify-01', 'inventory-01',
          'prepare-rea-01', 'rea-analyze-01', 'rea-analyze-02', 'rea-analyze-03', 'observe-01',
          'project-rea-01', 'project-rea-02', 'curate-01', 'verify-author-01']
failed = {'install-01', 'rea-analyze-01', 'rea-analyze-02', 'project-rea-01'}
for stage in stages:
    receipt = read(WORK / 'attempts' / stage / 'receipt.json')
    assert receipt['exitCode'] == (1 if stage in failed else 0) and receipt['sourcesUnchanged']
planned = {}
copies = []


def copy(relative, path, kind='analysis_metadata'):
    data = path.read_bytes()
    destination = PREFIX + relative
    assert destination not in planned
    planned[destination] = data
    copies.append({'original': str(path), 'outputPath': destination, **pin(data), 'kind': kind})


names = ['settings-entry-callers-contracts.json', 'settings-entry-callers-scenarios.json']
for name in names:
    copy('author/' + name, AUTHOR / name)
    planned[name] = (AUTHOR / name).read_bytes()
planned['settings-entry-callers-observations.json'] = (WORK / 'observations-01.json').read_bytes()
copy('observations/observations-01.json', WORK / 'observations-01.json', 'synthetic_vm_observations')
for number in range(1, 4):
    folder = WORK / f'source-{number:02}'
    for path in sorted(folder.iterdir()):
        if path.name == 'source-contracts.json' and number in [1, 3]:
            continue
        assert path.suffix in ['.txt', '.json', '.gz']
        copy('analysis/' + folder.name + '/' + path.name, path,
             'selected_application_source' if path.suffix == '.txt' else 'analysis_metadata_or_lossless_gzip')
for name in ['inventory.json.gz', 'metadata-archives.json', 'verification-01.json', 'tooling-manifest.json']:
    copy('author/' + name, WORK / name)
for name in ['package.json', 'package-lock.json']:
    copy('tooling/' + name, WORK / 'tooling' / name, 'analysis_tool_dependency_metadata_only')
for name in ['rea-source-map.json', 'rea-projection.json', 'rea-output.json', 'rea-stderr.jsonl', 'rea-result.json',
             'rea-02-output.json', 'rea-02-stderr.jsonl', 'rea-02-result.json',
             'rea-03-output.json.gz', 'rea-03-stderr.jsonl', 'rea-03-result.json']:
    copy('rea/' + name, WORK / name, 'rea_static_output_or_lossless_gzip')
for stage in stages:
    for path in sorted((WORK / 'attempts' / stage).iterdir()):
        copy('attempts/' + stage + '/' + path.name, path,
             'analysis_tool_source' if path.suffix in ['.py', '.mjs'] else 'execution_metadata')
records = []
for fact in contract['facts']:
    reference = fact['sourceReferences'][0]
    records.append({'id': fact['id'], 'baselineId': BASE, 'claim': fact['claim'],
                    'sourcePath': reference['sourcePath'], 'sourceHash': reference['sourceHash'],
                    'locator': {'kind': 'byte-range', **reference['byteRange']}, 'spanHash': reference['spanHash'],
                    'sourceReferences': fact['sourceReferences'], 'method': fact['method'],
                    'confidence': fact['confidence'], 'verificationStatus': fact['verificationStatus'],
                    'qualification': fact['qualification'], 'mode': 'unknown', 'newGlobalEvidenceRecord': False,
                    'actualUiControlExecuted': False})
planned['settings-entry-callers-evidence.jsonl'] = ('\n'.join(json.dumps(x, ensure_ascii=False) for x in records) + '\n').encode()
summary = '''# 设置入口参数、主机解析与隔离观察

两个设置入口传给可见性hook的第二参数，均来自所选主机解析后的kind===local，不能直接当作Codex／ChatGPT模式边界。见[24条限定合同](settings-entry-callers-contracts.json)、[证据行](settings-entry-callers-evidence.jsonl)、[17项隔离观察](settings-entry-callers-observations.json)、[8条待执行UI规格](settings-entry-callers-scenarios.json)及[完整归档索引](settings-entry-callers-provenance.json)。这是固定基线的分析增量，没有生成客户端工程。

| 入口 | hook参数 | 本地条件来源 |
| --- | --- | --- |
| SettingsPage / ri | 当前slug（time-management归为safety）、b、f | ne(f).kind===local；ne经shared.N$t连接pzt |
| 设置命令项 / U | null、isSelectedHostLocal、selectedHostId | Fa先计算ce(selectedHostId).kind===local，再经lazy组件props传入；ce也连接pzt |

两处selectedHostId都来自同一initial模块的Q6导入，但真实provider、配置发布者和运行实例尚未证明。页面还从usage的tab query得到候选slug；该解析器本批未执行。hook第二参数为false时使用上一批保存的12项精简列表，仍叠加各页访问与能力条件。它不等于home composer的chat/work偏好，也不构成删除ChatGPT页面的依据。

命令菜单还受shared.OAt→XAn访问条件、搜索／Configure组条件控制；lazy loader按字面模块路径选择VisibleSettingsCommandMenuSectionItems→U。U先过滤disabled，内部列表为空时整组返回null；之后才构造按认证来源和gate控制的外部账户／安全项。K区分appRoute、host路由消息和onNavigate callback；回调正常返回后由外层负责关闭，helper返回false则提前退出。profile事件及外部浏览器调用的先后顺序、同步异常与未await的Promise分别保留，真实导航与bridge receiver仍未知。

pzt优先返回ID匹配的host_config对象，否则解析远程列表；列表顺序为SSH、WSL、remote-control，重复ID取首项。未匹配ID回退默认Local。environment-git:hosted:前缀在没有匹配配置覆盖时返回“Cloud executor”，kind仍为local。前缀后缀经过decodeURIComponent，畸形编码可抛错。因此kind:local描述此解析器的返回值，不能代替物理主机、网络可达性或访问授权判断。

一次Node22 VM命令加载15个保存单位共1941字节，包含10个函数及5个常量赋值，17项合成场景全部通过：默认与未知ID回退、列表缺失与等待、云执行器、畸形编码、SSH alias／参数、WSL、remote-control、重复ID、配置优先级、null／undefined及memo复用。FI记录与React编译器memo cache均为明确替身，每项新建VM；没有读取真实主机配置，没有运行返回的SSH／WSL命令，也没有启动原客户端、执行UI、修改设置或提交模型。它们支持所选函数在这些输入下的行为，不能升级原功能验收。

REA固定版本6.4.0重新分析package.json与四个设置／菜单JS的字节相同副本：应用图140节点／953边，限于这五文件子集的coverage为complete；语义图27173节点／29013关系，coverage为unknown，8815个未知项，所有语义关系族均partial。大部分导入有意未纳入子集。两处hook调用按模块hash与UTF-16范围各匹配一个REA call-site，但没有直接关联该site的语义关系；callee与参数连接来自另存的完整Program词法分析，不能称REA已经闭合整条调用链。

完整REA成功输出以[无损gzip](raw/settings-entry-callers/rea/rea-03-output.json.gz)保存，解压后53911108字节及SHA均已核对；[紧凑投影](raw/settings-entry-callers/rea/rea-projection.json)保留两处原JSON pointer、节点、覆盖情况与hash。不会将大图节点数当成功能数量。此前两次REA因macOS Swift辅助程序的模块缓存写权限失败；尝试调整缓存后仍失败，获自动审批的正常执行完成，工具所有权检查未被移除。工具安装的离线缓存失败及投影脚本首次把families误当字典的失败均保留；修正投影未重跑REA，也未重跑17个VM场景。

本批22条源码事实／2条推断，67个规范AST单位（长度合计37735字节，含重叠）、270处词法引用、6项跨模块连接。三条作者解析命令共解析9个完整Program，涉及5个不同文件；REA另解析其子集的4个JS文件，不重复合并计数。字面文件名扫描覆盖14770个JS共381823019字节，仅5文件命中，不能替代计算路径和运行时加载调查。作者核对6个含范围文件的426个唯一范围、968处坐标、五份REA输入及全部14770文件hash；没有增加独立语义审查。

恢复源码可按职责组织host descriptor resolver、account/workspace access、settings catalog/visibility、command navigation adapter，并用包管理器引入React、状态与路由依赖。这里的目录建议是维护设计推断；并未找回原作者目录，也未完成这些库的全量版本与补丁鉴定。应保留host_config优先级、未知ID回退、列表顺序、加载与异常合同，再用真实UI／provider证据决定兼容策略。

当前37项有限功能、40用户操作／5机制／26队列、160条功能待执行规格、967未映射旧入口与337 deferred均保持。新增8条UI规格独立列出，全部未执行。没有新模式归属或确认ChatGPT-only排除，完整分母与分析目标仍未闭合；下一步应追Q6/provider与真实host配置发布者，核对共享消费者后再收窄重建范围。此前获批模型样例组2／2已用、剩余0，本批没有新增模型提交。
'''
planned['settings-entry-callers-summary.md'] = summary.encode()
index = {'schemaVersion': 1, 'baselineId': BASE, 'kind': 'bounded-settings-callers-host-resolver-rea-and-isolated-observations',
         'publishedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'exactCopies': copies,
         'derived': [{'path': name, **pin(planned[name])} for name in names +
                     ['settings-entry-callers-observations.json', 'settings-entry-callers-evidence.jsonl', 'settings-entry-callers-summary.md']],
         'sourceFacts': 22, 'inferredFacts': 2, 'selectedSourceUnits': 67, 'selectedSourceByteSumWithOverlap': 37735,
         'programLexicalJoins': 270, 'qualifiedImportExportUses': 6,
         'newOriginalProgramParses': 9, 'distinctParsedSourcePrograms': 5, 'analysisCommands': 3,
         'newReaCommandAttempts': 3, 'successfulReaCommands': 1, 'failedReaCommands': 2,
         'reaSubsetFiles': 5, 'reaJsProgramsParsed': 4, 'reaSemanticUnknowns': 8815, 'reaSemanticCoverage': 'unknown',
         'unexecutedScenarios': 8, 'runtimeRunsAdded': 1, 'isolatedObservationCommands': 1, 'isolatedScenarioCount': 17,
         'savedSourceUnitsLoaded': 15, 'savedFunctionsLoaded': 10, 'executedSavedSourceBytes': 1941,
         'originalClientRunsAdded': 0, 'originalStorageInstanceRunsAdded': 0,
         'modelSubmissionsAdded': 0, 'actualSettingsMutationsAdded': 0, 'newFeatureDefinitions': 0,
         'newModeAssignments': 0, 'newConfirmedExclusions': 0, 'globalRecordsAdded': 0,
         'uniqueSourceSpansChecked': 426, 'sourceCoordinateOccurrencesChecked': 968,
         'inventoryFilesByteChecked': 14770, 'targetCodeExecuted': True,
         'targetExecutionScope': 'Saved host functions in synthetic Node VM only.', 'syntheticProvidersOnly': True,
         'clientDependencyImplementationGenerated': False, 'independentSemanticPeerReviewAdded': False,
         'featureDenominatorEstablished': False, 'fullAnalysisCompleted': False}
planned['settings-entry-callers-provenance.json'] = encode(index)
readers = ['report.md', 'analysis-state.json', 'implementation-plan.md', 'gaps.md', 'behavior-checks.md']
before = {name: (OUT / name).read_bytes() for name in readers}
old = json.loads(before['analysis-state.json'])
assert len(old) == 94 and 'settingsEntryCallers' not in old and not old['fullAnalysisCompleted']
assert old['latestBehaviorAuthorizationState']['groupRemaining'] == 0
for item in contract['inputPins']:
    assert pin((OUT / item['path']).read_bytes()) == {k: item[k] for k in ['bytes', 'sha256']}
for name in planned:
    assert not (OUT / name).exists()
for name, data in planned.items():
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(0o444)
patch, _, artifacts = build_context(OUT, BASE)
assert len(patch) == len(PROFILES) == 29
assert all(old[key] == value for key, value in patch.items() if key != 'settingsEntryCallers')
state = {**old, 'settingsEntryCallers': patch['settingsEntryCallers']}
assert all(state[key] == value for key, value in old.items())
note = next(p[4] for p in PROFILES if p[0] == 'settingsEntryCallers')
marker = '[完成标准审计](criteria-audit.md)'
report = before['report.md'].decode()
assert report.count(marker) == 1
changes = {'analysis-state.json': encode(state), 'report.md': report.replace(marker, note + '\n\n' + marker).encode()}
extra = {
    'implementation-plan.md': '\n\n[设置入口与主机解析](settings-entry-callers-summary.md)支持将host descriptor、account access、设置可见性和导航adapter分责。两个入口的第二参数来自kind===local；未知主机与Cloud executor均可得到local，不能据此删ChatGPT功能。保存配置优先级、列表顺序及异常分支；17个合成VM场景尚不证明真实provider／UI，第三方实现继续用依赖引入。\n',
    'gaps.md': '\n\n[设置实际调用参数](settings-entry-callers-summary.md)已接到两个入口及所选host解析器。REA五文件子集应用图完整、语义图unknown／8815未知；实际Q6/provider、FI配置发布者、导航receiver和运行时access仍未知。17合成VM观察与8未执行UI规格分列；37功能／26队列／160功能规格、完整分母及模式排除保持。\n',
    'behavior-checks.md': '\n\n[主机解析17项隔离观察](settings-entry-callers-observations.json)由一次Node22 VM命令完成，保存函数搭配合成FI与memo替身；仅返回SSH／WSL参数数据，无平台命令、原客户端或模型提交。[新增8条UI规格](settings-entry-callers-scenarios.json)全部未执行，不升级原160条功能规格，也不增加模型／设置操作授权。\n',
}
for name, text in extra.items():
    changes[name] = before[name] + text.encode()
readme_before = (ROOT / 'README.md').read_bytes()
readme = readme_before + ('\n- [设置入口与主机解析：REA子集和17项合成观察](analysis/' + BASE + '/settings-entry-callers-summary.md)\n').encode()
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
    temporary = path.with_name('.settings-entry-callers-' + path.name)
    assert not temporary.exists()
    temporary.write_bytes(data)
    temporary.chmod(path.stat().st_mode & 0o777)
    temporary.replace(path)
assert (ROOT / 'README.md').read_bytes() == readme_before
temporary = ROOT / '.settings-entry-callers-README.md'
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
