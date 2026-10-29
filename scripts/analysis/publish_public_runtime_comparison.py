"""Publish the completed, bounded public-runtime comparison without rerunning probes."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASELINE
WORK = ROOT / '.analysis-local/public-runtime-comparison-work'
RAW = OUT / 'raw/public-runtime-comparison'


def read(path):
    return json.loads(path.read_text())


def pin(path):
    data = path.read_bytes()
    return {'path': os.path.relpath(path, OUT), 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest()}


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def publish():
    targets = [OUT / f'public-runtime-comparison{suffix}'
               for suffix in ['.json', '.md', '-provenance.json']]
    if RAW.exists() or any(path.exists() for path in targets):
        raise RuntimeError('Publication already exists; preserve immutable evidence')
    state_path = OUT / 'analysis-state.json'
    previous_state = read(state_path)
    manifest = read(WORK / 'fetch-02/manifest.json')
    assert len(manifest) == 16
    public_sources = []
    for entry in manifest:
        source = WORK / 'fetch-02' / (entry['id'] + '.txt')
        observed = pin(source)
        assert entry['httpStatus'] == 200 and entry['completeRead']
        assert observed['bytes'] == entry['bytes'] and observed['sha256'] == entry['sha256']
        public_sources.append({**entry, 'localInput': observed})
    acquisition = read(WORK / 'electron-42.3.0-01/acquisition.json')
    archive = WORK / 'electron-42.3.0-01/electron-v42.3.0-darwin-x64.zip'
    assert acquisition['archiveChecksumVerified']
    assert pin(archive)['sha256'] == acquisition['expectedArchiveSha256']
    main = read(WORK / 'probe-02/data/runtime-observations.json')
    main_receipt = read(WORK / 'probe-02/receipt.json')
    node = read(WORK / 'node-permissions-01/observations.json')
    node_receipts = read(WORK / 'node-permissions-01/receipts.json')
    cleanup = read(WORK / 'node-permissions-01/cleanup.json')
    process_check = read(WORK / 'final-process-check.json')
    assert main_receipt['exitCode'] == 0 and main['errors'] == []
    assert main['versions']['electron'] == '42.3.0' and main['versions']['node'] == '24.15.0'
    assert [row['exitCode'] for row in node_receipts] == [9, 0]
    assert node['permissionEnabled'] and node['scopes'] == {'net': False, 'ipc': False}
    assert all(row['status'] == 'roundtrip-completed' for row in node['observations'])
    assert cleanup == {'fixtureDirectoryRemoved': True, 'socketRemoved': True}
    assert process_check['psExitCode'] == 0 and process_check['ownedProcessRows'] == []
    history = next(row for row in main['observations'] if row['id'] == 'public-navigation-history-restore')
    assert history['restoredState']['input'] == 'edited-owned-fixture'
    assert history['restoredState']['heap'] == 'owned-memory-only'

    RAW.mkdir(parents=True)
    shutil.copy2(state_path, RAW / 'analysis-state-before.json')
    inputs = [
        'fetch-01/manifest.json', 'fetch-02/manifest.json',
        'electron-42.3.0-01/acquisition.json', 'electron-42.3.0-01/SHASUMS256.txt',
        'probe-01/receipt.json', 'probe-01/stdout.txt', 'probe-01/stderr.txt',
        'probe-01/probe_public_electron.cjs', 'probe-01-process-check.json',
        'probe-02/receipt.json', 'probe-02/stdout.txt', 'probe-02/stderr.txt',
        'probe-02/probe_public_electron.cjs', 'probe-02/data/runtime-observations.json',
        'node-permissions-01/receipts.json', 'node-permissions-01/observations.json',
        'node-permissions-01/cleanup.json', 'node-permissions-01/probe_public_node_permissions.cjs',
        'node-permissions-01/owl-ipc-flag-stdout.txt', 'node-permissions-01/owl-ipc-flag-stderr.txt',
        'node-permissions-01/permission-local-transports-stdout.txt',
        'node-permissions-01/permission-local-transports-stderr.txt', 'final-process-check.json',
    ]
    for relative in inputs:
        destination = RAW / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(WORK / relative, destination)
    producers = ['fetch_public_runtime_sources.py', 'acquire_electron_comparison.py',
                 'probe_public_electron.cjs', 'run_public_electron_probe.py',
                 'probe_public_node_permissions.cjs', 'run_public_node_permissions.py',
                 Path(__file__).name]
    for name in producers:
        destination = RAW / 'producers' / name
        destination.parent.mkdir(exist_ok=True)
        shutil.copy2(ROOT / 'scripts/analysis' / name, destination)

    next_action = {
        'kind': 'finite-stage-consolidation',
        'question': '复用现有证据，按分析计划九项完成标准给出已满足、内部待补和外部输入缺失的阶段交付；把剩余调查限定为会改变功能边界、依赖引入或独立构建决定的问题。',
        'closure': '每个未满足项有影响、下一项动作和验收条件；不要求所有unknown清零，不把已闭合源码定位重复作为进度。',
        'scopePreserved': '完整Codex目标与ChatGPT专属排除证据要求不变；客户端实施仍属于后续阶段。',
    }
    comparison = {
        'baselineId': BASELINE,
        'scope': 'Fixed public Electron 42.3.0 darwin-x64 primitive comparison; not a Codex client behavior acceptance run.',
        'originalRequirements': pin(OUT / 'runtime-capability-decisions.json'),
        'publicRuntimeVersions': main['versions'],
        'owlStaticVersionBoundary': {'node': '24.19.0', 'chromium': '155.0.8059.40',
                                      'kind': 'previous static binary evidence; no Owl runtime or traditional ABI measured here'},
        'nodeSourceComparisonTag': 'v24.19.0',
        'versionLimitation': 'Public runtime Node 24.15.0 observations and Node 24.19.0 source inputs are distinct; N-API 10 does not establish traditional ABI compatibility.',
        'capabilities': main['capabilities'],
        'decisions': [
            {'id': 'diagnostics', 'observation': 'showTaskManager is undefined; getAppMetrics returned CPU and memory field shapes.',
             'decision': 'Public metrics are a candidate data primitive. A maintained first-party task-manager UI and behavior verification remain required; a placeholder does not meet the original guard capability.'},
            {'id': 'managed-update-policy', 'observation': 'electron_browser_owl_update_policies linked binding is unavailable.',
             'decision': 'Keep ordinary updater transport separate from nullable managed policy. Prior source null handling supports a policy-provider boundary, not removal of all update functionality.'},
            {'id': 'browser-ownership-and-clone', 'observation': 'clone, _createWebViewAdoptionLease and setAgentActive are undefined. Public history restoration resolved and retained edited form state, but returned the initial page heap value instead of the edited live value.',
             'decision': 'History restoration is a tested candidate primitive only. Live clone, view ownership, lease acceptance and lifecycle still need explicit contracts and acceptance; full equivalence is unproven.'},
            {'id': 'node-network-and-ipc', 'observation': 'The Owl --allow-ipc flag exited 9 as an unknown option. With --permission, both has(net) and has(ipc) returned false while owned TCP loopback and Unix socket round trips succeeded.',
             'decision': 'Permission.has(false) does not establish transport denial in this public runtime. Preserve the original network/declared-IPC requirement; a real isolation or runtime implementation is needed. This probe does not test arbitrary remote destinations.'},
        ],
        'runtimeRouteDecision': 'Reject unmodified Electron 42.3.0 as a direct drop-in for the observed Owl contracts. Electron with first-party adapters remains a candidate; no full runtime route is selected or independently built.',
        'publicMainObservations': main['observations'],
        'publicNodeObservations': node,
        'counts': {'officialSourceInputs': 16, 'publicRuntimeLaunchAttempts': 4,
                   'successfulMainProbeProcesses': 1, 'successfulNodeTransportProbeProcesses': 1,
                   'expectedUnsupportedFlagProcesses': 1, 'mainProbeFailuresBeforeCapabilityChecks': 1,
                   'capabilityDecisions': 4, 'originalClientRunsAdded': 0, 'modelSubmissionsAdded': 0,
                   'newReaRuns': 0, 'newFeatureDefinitions': 0, 'newConfirmedModeClassifications': 0},
        'failedAttempts': ['Initial public source fetch had DNS failures; successful second fetch retained separately.',
                           'First main probe used the wrong argument position and failed before capability checks; timed out, was terminated, and no owned processes remained. Corrected second probe exited 0.'],
        'cleanup': {'ownedProcessesRemaining': 0, **cleanup},
        'nextAction': next_action,
        'fullAnalysisCompleted': False, 'independentRuntimeBuildProven': False,
        'limitations': ['Synthetic local pages and endpoints only; no original account or model task used.',
                        'Fixed tag URLs and received body hashes recorded; upstream commit identity was not independently resolved.',
                        'Full functional denominator, mode classification and the 212 unexecuted scenario specifications remain unchanged.',
                        'Acquisition receipt says not launched at acquisition time; later launch receipts are separate historical records.',
                        'The public binary archive and browser caches are not copied into published raw output; third-party source inputs remain analysis-only.'],
    }
    write(targets[0], comparison)
    targets[1].write_text('''# 公共 Electron 运行时对照结果

固定的 Electron 42.3.0 darwin-x64 **不能直接替换现有 Owl**。官方归档通过 SHA-256 核验；实际进程测得 Node 24.15.0、Chromium 148.0.7778.180、传统 modules ABI 146、N-API 10。这些数值不能代替原 Owl 的实际运行版本或 ABI。

| 能力 | 实测结果 | 工程决定 |
| --- | --- | --- |
| 任务管理器 | showTaskManager 缺失；getAppMetrics 返回 CPU/内存字段 | 公开数据接口可作为候选，仍需第一方诊断界面及行为验收 |
| managed update policy | Owl linked binding 缺失 | 策略 provider 与普通更新 transport 分开；沿用已确认的 nullable 分支边界 |
| 浏览器 clone/所有权 | clone、adoption lease、setAgentActive 缺失；公开 history restore 保留编辑后的表单，但没有保留编辑后的 JS 堆值 | 历史恢复只证明一个可用原语；live clone 与 lease 生命周期仍有差距 |
| Node 网络/IPC | --allow-ipc 被拒绝；启用 --permission 后 has(net/ipc) 为 false，但自有 TCP/Unix socket 均可往返 | 不能把 false 当成网络隔离，不能只删除不支持的参数；仍需实际权限实现 |

[结构化结果](public-runtime-comparison.json)区分四次公共运行时启动：首次主探针在能力检查前因参数错误失败，修正后的主探针成功，另有一次预期的非法参数退出和一次成功的本地传输探针。进程检查无残留，自建 socket 已清理。首次下载的 DNS 失败也保留，未计作成功取证。

16 份固定版本官方源码/文档、下载记录、探针、终态和哈希见[来源索引](public-runtime-comparison-provenance.json)。Node 24.19.0 的源码对照与实际 Node 24.15.0 探针分列。公开 [history 接口](https://github.com/electron/electron/blob/v42.3.0/docs/api/navigation-history.md)和 [WebContentsView](https://github.com/electron/electron/blob/v42.3.0/docs/api/web-contents-view.md)可用于评估适配路线，尚未证明 Owl 行为等价。

本批没有运行原客户端、调用模型、生成客户端依赖实现或增加产品功能验收。完整功能分母、模式归属和 212 条未执行验收规格保持原状态。独立 Owl 来源、其他私有 API、原生 ABI 及全客户端行为仍是缺口。

下一项先复用现有证据完成阶段收束：按原计划九项标准列出已满足项、内部待补项和缺失的外部输入，把后续调查限定到会改变功能、依赖或独立构建决定的问题；不继续重复已闭合的源码定位。
''')
    provenance = {'baselineId': BASELINE, 'createdAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'publicSources': public_sources, 'archive': pin(archive),
                  'rawFiles': [pin(path) for path in sorted(RAW.rglob('*')) if path.is_file()],
                  'outputs': [pin(path) for path in targets[:2]],
                  'priorRequirements': pin(OUT / 'runtime-capability-decisions.json')}
    write(targets[2], provenance)
    state = dict(previous_state)
    state['updatedAtUtc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    state['publicRuntimeComparison'] = {'comparison': pin(targets[0]), 'summary': pin(targets[1]),
                                        'provenance': pin(targets[2]), 'counts': comparison['counts'],
                                        'runtimeRouteDecision': comparison['runtimeRouteDecision'],
                                        'nextAction': next_action, 'fullAnalysisCompleted': False}
    write(state_path, state)
    for path in [*targets, *RAW.rglob('*')]:
        if path.is_file():
            path.chmod(0o444)
    print(json.dumps({'published': [str(p) for p in targets], 'counts': comparison['counts']}, ensure_ascii=False))


if __name__ == '__main__':
    publish()
