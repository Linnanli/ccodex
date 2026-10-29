"""Integrate the pinned storage/DI/context sources and isolated MODE observations."""
import hashlib
import json
from pathlib import Path

from contract_reader_context import PROFILES, build_context

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASELINE


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


names = ['report.md', 'analysis-state.json', 'implementation-plan.md', 'gaps.md',
         'dependency-import-decisions.md', 'behavior-checks.md']
before = {name: (OUT / name).read_bytes() for name in names}
readme_before = (ROOT / 'README.md').read_bytes()
assert pin(before['report.md']) == {'bytes': 47684, 'sha256': 'c6a9eaa7ced60fd34eca5757ceaf3693670ca675dd31d985e0ff5bed19bfcb43'}
assert pin(before['analysis-state.json']) == {'bytes': 137092, 'sha256': '976980c7ab6133c663737e4d59612fe4087a4fb0fd9ea4f7f84bc67118c94ac4'}
old_state = json.loads(before['analysis-state.json'])
assert old_state['fullAnalysisCompleted'] is False and old_state['featureDenominatorEstablished'] is False
patch, _, artifacts = build_context(OUT, BASELINE)
new_keys = ['modePreferenceStorageOrigin', 'settingsDiSource', 'modeBehaviorObservations', 'settingsSourceContextOrigin']
assert len(patch) == 15 and all(key not in old_state for key in new_keys)
assert all(old_state[key] == value for key, value in patch.items() if key not in new_keys)

source_reader = json.loads((OUT / 'settings-source-context-origin.json').read_bytes())
source_snapshot = source_reader['authorSnapshot']
source_raw = (OUT / source_snapshot['path']).read_bytes()
assert pin(source_raw) == {key: source_snapshot[key] for key in ['bytes', 'sha256']}
source = json.loads(source_raw)
assert source['denominators']['journalRecords'] == 9 and len(source['selectedUnits']) == 4
selected_units = [source['selectedUnits'][i] for i in [0, 1, 3]]
proposal = {
    'schemaVersion': 1, 'baselineId': BASELINE, 'id': 'HOST-SOURCE-CONTEXT-MODULE-PROPOSAL-001',
    'confidence': 'inferred', 'status': 'maintenance-proposal; not original directory or implemented client',
    'proposedPath': 'apps/desktop/src/main/context/source-context.ts',
    'responsibility': 'First-party source-context forwarding and lifecycle adapter for known main-process consumers.',
    'environment': 'Main host candidate based on the known config receiver; other source exports/consumers remain unclassified.',
    'mode': 'unknown', 'sourceSnapshot': source_snapshot,
    'sourceMappings': [{'unitId': unit['unitId'], 'originalLocator': unit['locator'],
                        'metadataPointer': '/selectedUnits/' + str(source['selectedUnits'].index(unit))}
                       for unit in selected_units],
    'contractIds': ['SETTINGS-SOURCE-CONTEXT-0002', 'SETTINGS-SOURCE-CONTEXT-0003',
                    'SETTINGS-SOURCE-CONTEXT-0004', 'SETTINGS-SOURCE-CONTEXT-0005',
                    'SETTINGS-SOURCE-CONTEXT-0006', 'SETTINGS-SOURCE-CONTEXT-0007'],
    'dependency': {'specifier': 'node:async_hooks', 'kind': 'runtime-builtin',
                   'implementationRecoveryRequired': False, 'npmPackageRequired': False,
                   'targetRuntimeVersion': 'unknown'},
    'candidateInterface': {'name': 'runWithSourceContext', 'arguments': ['source/context value', 'callback'],
                           'types': 'unresolved; choose after actual source inputs and consumers are established',
                           'return': 'Preserve selected run return value, including Promise identity, without adding await or catch.'},
    'upgradeChecks': ['Pin the selected runtime and its builtin API.',
                      'Diff original binding/source ranges separately from the inferred maintenance path.',
                      'Verify callback return/throw, Promise identity, nested contexts and async inheritance.',
                      'Verify real client/source inputs and receiver lifetime before claiming whole fetch parity.'],
    'limits': ['This proposal does not recreate the original directory.',
               'Current namespace/instance, mutations, target embedded runtime and actual native behavior remain unobserved.',
               'Isolated local Node observations are a separate candidate contract and cannot substitute for actual target behavior.'],
    'globalRecordsAdded': 0, 'fullAnalysisCompleted': False, 'thirdPartyImplementationCopied': False,
}
proposal_raw = encode(proposal)
proposal_md = '''# source-context 的维护模块建议

建议路径 `apps/desktop/src/main/context/source-context.ts`，用于维护已知主进程配置接收链所用的第一方上下文转发。该路径由职责提出，原作者目录与其他消费者尚未知；模式归属保持 unknown。

[结构化映射](source-context-module-proposal.json)把 lX、rX 和 k 的三个原始范围接到[新来源合同](settings-source-context-origin-summary.md)，每项保留完整文件 hash、byte/UTF-16范围和小单位 hash。原 frozen 6 个来源模块建议保持不变。

依赖采用所选运行时内置 `node:async_hooks` 的 AsyncLocalStorage。维护 adapter 保留同步转发、原返回值和异常边界；不复制 Node 原生实现，也不为内置API生成 npm 包。接口类型、实际source值、实例生命周期与其他消费者须继续调查。

升级时分别检查新基线绑定/范围变化、运行时API、上下文隔离、return/throw/Promise identity与异步继承。候选本机实验和真实主进程/client行为分别验收，完整fetch、I/O取消及持久化仍未验证。
'''
proposal_key = 'sourceContextModuleProposal'
assert proposal_key not in old_state
new_state = {**old_state, **{key: patch[key] for key in new_keys}, proposal_key: {
    'path': 'source-context-module-proposal.json', **pin(proposal_raw), 'proposalCount': 1,
    'sourceMappings': 3, 'confidence': 'inferred', 'runtimeRunsAdded': 0, 'globalRecordsAdded': 0,
    'fullAnalysisCompleted': False}}
assert all(new_state[key] == value for key, value in old_state.items())

notes = '\n\n'.join(profile[4] for profile in PROFILES if profile[0] in new_keys)
notes += '\n\n[上下文维护模块建议](source-context-module-proposal.md)另提出1个第一方adapter路径，接到3个原始范围；全部为inferred/proposal，与既有6个来源模块建议分开。内置API由运行时提供，完整客户端结构仍未确定。'
marker = '[完成标准审计](criteria-audit.md)'
report = before['report.md'].decode()
assert report.count(marker) == 1 and notes not in report
planned = {'report.md': report.replace(marker, notes + '\n\n' + marker).encode(),
           'analysis-state.json': encode(new_state), 'source-context-module-proposal.json': proposal_raw,
           'source-context-module-proposal.md': proposal_md.encode()}
supplements = {
    'implementation-plan.md': '\n[模式存储来源](mode-preference-storage-origin-summary.md)支持将模式resolver、偏好factory、内存状态/订阅与publisher适配分别维护。实际ARt第二参数及provider/backend尚未定位，不能把generic localStorage实现作为MODE存储。读者须应用[清理勘误](raw/mode-preference-storage-origin/qualification/cleanup-errata.json)，保留setup/cleanup失败可能留下注册的条件。[di来源](settings-di-source-summary.md)要求把第一方G封装与传入client分开；readFile与mkdir/writeFile的client实参位置不同。\n\n[上下文来源](settings-source-context-origin-summary.md)为[1个新维护模块建议](source-context-module-proposal.md)提供3原始范围映射。候选路径用于已知main消费者的小型第一方adapter，内置node:async_hooks由所选运行时提供；旧6条来源模块建议保持冻结。接口类型、actual source/client/实例生命周期及其余消费者仍须调查。20个[模式隔离场景](mode-behavior-observations-summary.md)可作为这些小函数后续回归的局部参照，不能代替真实UI、存储、失败/取消/恢复验收。\n',
    'dependency-import-decisions.md': '\n[source-context来源](settings-source-context-origin-summary.md)确认所选构造器namespace为node:async_hooks，属于Node运行时内置依赖。候选方案仅恢复第一方转发与生命周期adapter，由固定运行时提供AsyncLocalStorage；不生成原生实现或额外npm依赖。Node24.19官方文档只作公开API候选，actual target/runtime/current namespace/instance尚未证明。本机Node22隔离实验另批记录，采用前需核对完整client/source与运行时兼容。\n',
    'behavior-checks.md': '\n## 模式函数的20个隔离场景\n\n[模式函数观察](mode-behavior-observations-summary.md)实际用一条Node22.23.2命令运行20个独立、限时VM场景：gS 6、lPt 8、FJ 6。仅执行3保存小函数901字节，内存替身在VM内创建，未提供process/require或真实外部资源。逐场景预期与实际均通过，真实命令、stdio、时间、exit与源码pin可回到该批metadata。\n\ngS首setter和FJ publisher同步抛错会阻止后续写；其返回rejected Promise的所选分支仍继续。lPt两处persisted分支保留对象身份；能力表达式同步抛错可先于extension结果。Promise rejection立即挂观察catch、settlement另列，不能当同步异常。FJ coerce/delay只用于通用factory场景，实际MODE两参数调用未启用选项；内存publisher故意不更新持久Map。\n\n范围只证明明确替身下的控制流与返回身份，未执行真实hI/ARt、provider/store、UI、持久化、native、传输或原客户端。20场景共享1条命令，新增模型任务0，旧MODE26与Storage46的真实场景保持未执行状态。\n\n[存储来源](mode-preference-storage-origin-summary.md)、[di来源](settings-di-source-summary.md)及[source-context来源](settings-source-context-origin-summary.md)仍属静态分析。新的原绑定闭合不追溯升级旧16/25快照；Node文档候选不算目标runtime观察。真实publisher/backend、client/source实参、context实例、I/O取消和重启恢复继续列入行为验收。\n',
}
for name, extra in supplements.items():
    assert extra not in before[name].decode()
    planned[name] = before[name] + extra.encode()
gap_extra = '\n[存储来源](mode-preference-storage-origin-summary.md)已确认偏好/atom/订阅factory，actual ARt caller与第二参数publisher、provider/backend、真实模式值及恢复仍待调查；[清理勘误](raw/mode-preference-storage-origin/qualification/cleanup-errata.json)限定setup/cleanup失败条件。[di](settings-di-source-summary.md)和[source-context](settings-source-context-origin-summary.md)将源getter接到G/lX与node:async_hooks，但client/source实参、current namespace/instance、target runtime、native语义和整fetch尚未知。[20隔离场景](mode-behavior-observations-summary.md)只覆盖3小函数与内存替身，实际UI/persistence与完整模式归属未增加确认。\n'
gaps = before['gaps.md'].decode()
table_at = gaps.index('\n| ')
planned['gaps.md'] = (gaps[:table_at] + gap_extra + gaps[table_at:]).encode()
readme_extra = '\n- [模式偏好、状态与存储来源](analysis/' + BASELINE + '/mode-preference-storage-origin-summary.md)\n- [文件di与source helper来源](analysis/' + BASELINE + '/settings-di-source-summary.md)\n- [source-context的Node内置依赖](analysis/' + BASELINE + '/settings-source-context-origin-summary.md)\n- [20个模式函数隔离行为场景](analysis/' + BASELINE + '/mode-behavior-observations-summary.md)\n- [source-context维护模块与原范围映射](analysis/' + BASELINE + '/source-context-module-proposal.md)\n'
assert readme_extra not in readme_before.decode()
readme_after = readme_before + readme_extra.encode()
snapshots = {'raw/storage-context-integration/reader-before-' + name: raw for name, raw in before.items()}
snapshots['raw/storage-context-integration/reader-before-README.md'] = readme_before
for relative, raw in {**snapshots, **planned}.items():
    target = OUT / relative
    assert target.resolve().is_relative_to(OUT.resolve()) and not target.is_symlink()
    if relative in before:
        assert target.read_bytes() == before[relative]
    else:
        assert not target.exists() or target.read_bytes() == raw
assert (ROOT / 'README.md').read_bytes() == readme_before
for relative, raw in snapshots.items():
    target = OUT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_bytes(raw)
    target.chmod(0o444)
for relative, raw in planned.items():
    target = OUT / relative
    temporary = target.with_name('.storage-context-' + target.name)
    assert not temporary.exists()
    temporary.write_bytes(raw)
    temporary.chmod(target.stat().st_mode & 0o777 if target.exists() else 0o444)
    temporary.replace(target)
    assert target.read_bytes() == raw
temporary = ROOT / '.storage-context-README.md'
assert not temporary.exists()
temporary.write_bytes(readme_after)
temporary.chmod((ROOT / 'README.md').stat().st_mode & 0o777)
temporary.replace(ROOT / 'README.md')
print(json.dumps({'status': 'integrated', 'companionIndices': 15, 'newStateFields': new_keys + [proposal_key],
                  'oldStateValuesPreserved': True, 'snapshots': {name: pin(raw) for name, raw in snapshots.items()},
                  'outputs': {name: pin(raw) for name, raw in planned.items()}, 'readme': pin(readme_after),
                  'selectedArtifactPaths': len(artifacts), 'globalRecordsAdded': 0,
                  'isolatedObservationCommands': 1, 'isolatedScenarioCount': 20,
                  'originalClientRunsAdded': 0, 'originalStorageRunsAdded': 0,
                  'deliveryRuntimeRunsAdded': 0, 'additionalModelTasks': 0, 'fullAnalysisCompleted': False}))
