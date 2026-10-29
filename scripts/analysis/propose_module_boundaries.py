#!/usr/bin/env python3
"""Propose maintenance boundaries from reviewed contracts, without generating client code."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

workspace = Path(__file__).resolve().parents[2]
baseline = json.loads((workspace / '.analysis-local/current-baseline.json').read_text())
out = workspace / 'analysis' / baseline['baselineId']
work = workspace / '.analysis-local/structure-work'
work.mkdir(exist_ok=True)
wrappers_path = out / 'request-wrapper-contracts.json'
chunk_path = out / 'chunk-transport.json'
embedded_path = workspace / '.analysis-local/embedded-dependency-work/embedded-dependency-contracts.json'
wrappers = json.loads(wrappers_path.read_text())
chunk = json.loads(chunk_path.read_text())
embedded = json.loads(embedded_path.read_text())
assert all(r['baselineId'] == baseline['baselineId'] for r in [wrappers, chunk, embedded])
evidence = {e['id']: e for e in map(json.loads, (out / 'evidence.jsonl').read_text().splitlines())}
for e in map(json.loads, (embedded_path.parent / 'evidence.jsonl').read_text().splitlines()):
    if e['id'] in evidence:
        assert evidence[e['id']] == e
    evidence[e['id']] = e

proposals = {
    'RWC-MANAGER': ('packages/app-server-client/src/request-manager.ts', 'Request scheduling and transport facade', 'Multiple configured transports remain separate; do not collapse them into one public app-server client.'),
    'RWC-SELECTOR': ('packages/app-host-client/src/host-selector.ts', 'Host-specific service selection', 'Retain host selection, deferred resolution and connection lifetime as explicit interfaces.'),
    'RWC-FETCH': ('apps/desktop/src/main/network/desktop-fetch.ts', 'Desktop HTTP transport adapter', 'Keep ordinary HTTP, desktop fetch and cancellation distinct from app-server method requests.'),
    'RWC-RESOLVER': ('packages/app-host-client/src/request-resolver.ts', 'Injected request resolver', 'Preserve dependency injection until concrete callers and transport ownership are bound.'),
    'RWC-HOSTED-FILES': ('packages/app-server-client/src/extensions/hosted-files.ts', 'Hosted-file extension connection', 'Treat extension methods as a separate contract; public backend support is unresolved.'),
    'RWC-HOST-TRANSPORT': ('packages/app-server-client/src/host-connection.ts', 'Host connection adapter', 'Preserve request envelope, trace context and prewarm branch; concrete wire transport is unresolved.'),
    'RWC-COORDINATION': ('apps/desktop/src/main/coordination/socket-client.ts', 'Cross-client coordination adapter', 'Keep source/target client identity, host identity and timeout; actual socket lifecycle requires verification.'),
    'RWC-PROJECTS': ('packages/projects/src/project-service.ts', 'Project domain and state contracts', 'Renderer client, shared service interface and main persistence implementation occupy different runtime files; this path names the domain boundary, not a literal move of all ranges.'),
}
rows = []
for contract in wrappers['contracts']:
    proposed_path, responsibility, rule = proposals[contract['id']]
    rows.append({'id': 'STRUCT-' + contract['id'], 'sourceContract': contract['id'],
                 'responsibility': responsibility, 'proposedPath': proposed_path,
                 'proposalConfidence': 'inferred', 'mode': 'unknown', 'runtimePlacementRequiresReview': True,
                 'evidenceIds': contract['evidenceIds'], 'maintenanceRule': rule,
                 'unresolved': contract['unknowns']})
rows.append({'id': 'STRUCT-CHUNK', 'sourceContract': 'chunk-transport.json',
             'responsibility': 'Host-to-view framing, acknowledgement and assembly',
             'proposedPath': 'packages/desktop-transport/src/chunked-messages.ts',
             'proposalConfidence': 'inferred', 'mode': 'unknown', 'runtimePlacementRequiresReview': True,
             'evidenceIds': [e['id'] for e in chunk['evidence']],
             'maintenanceRule': 'Separate pure codec from sender/receiver lifecycle and IPC adapters; preserve reviewed frame and acknowledgement contracts.',
             'unresolved': chunk['unverifiedBoundaries']})
for wrapper in embedded['firstPartyWrappers']:
    rows.append({'id': 'STRUCT-' + wrapper['id'], 'sourceContract': wrapper['id'],
                 'responsibility': 'Browser annotation application adapter',
                 'proposedPath': 'apps/desktop/src/browser-preload/annotation/' + wrapper['id'] + '.tsx',
                 'proposalConfidence': 'inferred', 'mode': 'unknown', 'runtimePlacementRequiresReview': True,
                 'evidenceIds': wrapper['evidenceRefs'],
                 'maintenanceRule': wrapper['maintenanceDecision'],
                 'unresolved': ['Codex/shared mode ownership, runtime reachability, library import equivalence and closure remain unverified.']})
for row in rows:
    row['sourceMappings'] = []
    for evidence_id in row['evidenceIds']:
        e = evidence[evidence_id]
        assert e['baselineId'] == baseline['baselineId']
        row['sourceMappings'].append({'evidenceId': evidence_id, 'sourcePath': e['sourcePath'],
                                     'sourceHash': e['sourceHash'], 'locator': e['locator']})
record = {'baselineId': baseline['baselineId'], 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
          'status': 'reviewed-contract-maintenance-proposal; not recovered original module layout',
          'scope': {'proposalCount': len(rows), 'fullModuleCoverage': False, 'clientCodeGenerated': False},
          'runnerSource': {'path': str(Path(__file__).relative_to(workspace)), 'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
          'inputs': [{'path': str(p.relative_to(workspace)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in [wrappers_path, chunk_path, embedded_path]],
          'proposals': rows,
          'openArchitectureDecisions': [
              'Owl shell source/distribution and required API replacements must be settled before selecting a runnable desktop shell.',
              'Prediction and other private backend capabilities need an explicit contract decision; equal schemas or version gates do not establish support.',
              'No complete feature denominator or confirmed ChatGPT-only removal set exists yet.',
              'Embedded library self-reports are not sufficient to select an unmodified upstream dependency.',
              'These reviewed ranges do not account for all 438 module candidates, shared closures, state ownership or platform integrations.'],
          'upgradeRule': 'Create a new frozen baseline; compare contract IDs, source mappings, entry guards, dependency identities and owned behavior scenarios; update first-party modules through reviewed changes and regenerate dependency lockfiles only after provenance decisions.'}
(work / 'module-boundary-proposals.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
lines = ['# 由已审查契约提出的维护模块边界', '', f"基线：`{baseline['baselineId']}`。11 条局部建议；不表示原作者目录已恢复，也不覆盖全部模块。未生成客户端源码。", '',
         '| 契约 | 拟维护位置 | 依据与边界 |', '| --- | --- | --- |']
for row in rows:
    lines.append(f"| {row['sourceContract']} | `{row['proposedPath']}` | {row['responsibility']}；来源范围与未解决项见结构化记录 |")
lines += ['', '路径由职责和运行边界提出。源范围只作为溯源，不可逐段复制进拟议文件：同一契约可能包含 renderer、main 和共享接口，应在实现阶段按运行环境拆开。mode 均保留 unknown，不能据路径把整个浏览器或网络模块排除。', '',
          '第三方实现通过依赖导入；第一方封装按契约恢复。项目服务、请求选择器、HTTP、app-server 扩展和协调 socket 分别保留边界，避免把同名 sendRequest 混为一种协议。', '',
          'Owl、私有后端能力、库版本来源、共享闭包和全功能覆盖仍影响最终项目结构；这些决定未完成前，目录仅作维护建议。原输入哈希、证据 ID、来源范围和每项未知见 module-boundary-proposals.json。升级需重建新基线并比较接口、模式条件、依赖和行为场景。', '']
(work / 'module-boundary-proposals.md').write_text('\n'.join(lines))
print(json.dumps({'proposalCount': len(rows), 'sourceMappingOccurrences': sum(len(r['sourceMappings']) for r in rows), 'fullModuleCoverage': False, 'clientCodeGenerated': False}))
