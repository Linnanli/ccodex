#!/usr/bin/env python3
"""Read frozen runtime fuse bytes without launching or modifying the application."""
from datetime import datetime, timezone
import hashlib
import json
import mmap
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
SENTINEL = b'dL7pKGdnNz796PbbjQWNKmHXBZaB9tsX'
SCHEMA = [
    'run_as_node', 'cookie_encryption', 'node_options', 'node_cli_inspect',
    'embedded_asar_integrity_validation', 'only_load_app_from_asar',
    'load_browser_process_specific_v8_snapshot', 'grant_file_protocol_extra_privileges',
    'wasm_trap_handlers',
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def describe(path):
    data = path.read_bytes()
    return {'path': str(path.relative_to(WORKSPACE)), 'bytes': len(data), 'sha256': digest(data)}


def main():
    baseline_path = WORKSPACE / '.analysis-local/current-baseline.json'
    baseline = json.loads(baseline_path.read_text())
    out = WORKSPACE / 'analysis' / baseline['baselineId']
    inventory_path = out / 'files.json'
    inventory = json.loads(inventory_path.read_text())
    originals = {entry['sourcePath']: entry for entry in inventory['applicationFiles'] if 'sha256' in entry}
    application = WORKSPACE / '.analysis-local/runtime' / baseline['baselineId'] / 'ChatGPT.app'
    paths = ['Contents/MacOS/ChatGPT',
             'Contents/Frameworks/Codex Framework.framework/Versions/155.0.8059.40/Codex Framework']
    observations, evidence = [], []
    for source_path in paths:
        original = originals[source_path]
        actual = application / source_path
        with actual.open('rb') as stream:
            with mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
                actual_hash = digest(data)
                assert actual_hash == original['sha256'] and len(data) == original['bytes']
                hits, start = [], 0
                while True:
                    hit = data.find(SENTINEL, start)
                    if hit < 0:
                        break
                    header = hit + len(SENTINEL)
                    version, length = data[header], data[header + 1]
                    end = header + 2 + length
                    assert end <= len(data)
                    wire = bytes(data[header + 2:end])
                    assert version == 1 and length == len(SCHEMA) and set(wire) <= {48, 49, 114}
                    wire_id = 'RUNTIME-FUSE-E' + str(len(evidence) + 1).zfill(3)
                    evidence.append({'id': wire_id, 'baselineId': baseline['baselineId'],
                        'claim': 'Exact standard-format v1 fuse wire bytes; schema interpretation is separate from runtime enforcement.',
                        'sourcePath': source_path, 'sourceHash': actual_hash,
                        'locator': {'kind': 'byte-range', 'start': hit, 'endExclusive': end},
                        'spanSha256': digest(bytes(data[hit:end])), 'method': 'read-only-frozen-binary-fuse-wire-scan',
                        'confidence': 'confirmed', 'verificationStatus': 'bytes-confirmed; target-native-fuse-consumers-unverified'})
                    states = []
                    for index, name in enumerate(SCHEMA):
                        at = header + 2 + index
                        identifier = 'RUNTIME-FUSE-E' + str(len(evidence) + 1).zfill(3)
                        evidence.append({'id': identifier, 'baselineId': baseline['baselineId'],
                            'claim': 'Exact fuse byte at v1 ordinal ' + str(index) + '; official schema name ' + name,
                            'sourcePath': source_path, 'sourceHash': actual_hash,
                            'locator': {'kind': 'byte-range', 'start': at, 'endExclusive': at + 1},
                            'spanSha256': digest(bytes(data[at:at + 1])), 'method': 'read-only-frozen-binary-fuse-wire-scan',
                            'confidence': 'confirmed', 'verificationStatus': 'byte-confirmed; name/state semantics use external schema'})
                        states.append({'ordinal': index, 'officialSchemaName': name, 'rawByte': wire[index],
                            'asciiValue': chr(wire[index]),
                            'schemaInterpretation': {48: 'disabled', 49: 'enabled', 114: 'removed'}[wire[index]],
                            'targetNativeConsumerVerified': False, 'evidenceId': identifier})
                    hits.append({'byteStart': hit, 'byteEndExclusive': end, 'version': version,
                        'wireLength': length, 'wireHex': wire.hex(), 'wireAscii': wire.decode('ascii'),
                        'evidenceId': wire_id, 'states': states})
                    start = end
                observations.append({'sourcePath': source_path, 'runtimeCopyPath': str(actual.relative_to(WORKSPACE)),
                    'sourceHash': actual_hash, 'bytes': len(data), 'frozenInventoryHashMatch': True,
                    'sentinelMatches': len(hits), 'wireCandidates': hits,
                    'scope': 'Complete selected binary scanned for the exact sentinel; other binaries not scanned.'})
    framework = observations[1]
    assert framework['sentinelMatches'] == 1
    states = framework['wireCandidates'][0]['states']
    assert [states[index]['asciiValue'] for index in [0, 2, 3]] == ['0', '0', '0']
    work = WORKSPACE / '.analysis-local/runtime-fuse-work'
    work.mkdir(parents=True, exist_ok=True)
    record = {'baselineId': baseline['baselineId'], 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
        'status': 'static-observed; runtime-enforcement-unverified',
        'scope': {'selectedBinaries': 2, 'completeBinaryBytes': sum(entry['bytes'] for entry in observations),
                  'fuseWires': 1, 'sourceEvidenceRecords': len(evidence), 'targetApplicationLaunched': False,
                  'targetBinaryModified': False, 'nodeDiagnosticAttempted': False, 'modelTasksSubmitted': 0},
        'sourceInputs': [describe(baseline_path), describe(inventory_path)],
        'scripts': [describe(Path(__file__).resolve())], 'observations': observations,
        'schemaReferences': [
            {'url': 'https://www.electronjs.org/docs/latest/tutorial/fuses',
             'role': 'Sentinel/version/length/state wire format and RunAsNode/NodeOptions/NodeCliInspect semantics; checked 2026-10-13.'},
            {'url': 'https://github.com/electron/electron/blob/v44.7.0/build/fuses/fuses.json5',
             'role': 'External v1 schema ordinal mapping; this is not a claim that Owl is Electron v44.7.0.'}],
        'conclusions': {'observedWire': framework['wireCandidates'][0]['wireAscii'],
            'nodeDiagnosticDecision': 'Do not launch RunAsNode, NODE_OPTIONS, or inspect diagnostics using a disabled-valued wire as an enabled precondition.',
            'actualNodeVersion': 'unknown', 'actualElectronCompatibilityVersion': 'unknown',
            'nativeModulesAbi': 'unknown', 'runtimeNativeFuseConsumption': 'unknown'},
        'limitations': ['A standard-format wire and official schema support decoding the bytes; the custom Owl native consumers were not executed or disassembled.',
            'No fuse editing, code-signature changes, application startup, network request, account access, or model request occurred.',
            'Two selected binaries are the scan denominator, not all runtime files.',
            'Embedded ASAR integrity fuse bytes do not resolve the seven historical archive/unpacked declaration mismatches.']}
    (work / 'runtime-fuse-observation.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    (work / 'evidence.jsonl').write_text(''.join(json.dumps(entry, ensure_ascii=False) + '\n' for entry in evidence))
    rows = '\n'.join('| ' + str(entry['ordinal']) + ' | ' + entry['officialSchemaName'] + ' | ' + entry['asciiValue'] + ' | ' + entry['schemaInterpretation'] + ' |' for entry in states)
    summary = f'''# 定制运行时 fuse 字节只读核对

基线 `{baseline['baselineId']}`。主可执行文件与 Codex Framework 两份完整二进制共 {record['scope']['completeBinaryBytes']:,} 字节，运行副本哈希与冻结清单一致。主可执行文件未匹配 sentinel；Framework 匹配一处 v1/长度9 的标准格式数据，wire 为 `{record['conclusions']['observedWire']}`。这是两个选定二进制的分母。

| 序号 | 外部 v1 schema 名称 | 原字节 | schema 解读 |
| --- | --- | --- | --- |
{rows}

解码依据为 [Electron 官方 fuse 格式与说明](https://www.electronjs.org/docs/latest/tutorial/fuses)及 [v44.7.0 schema](https://github.com/electron/electron/blob/v44.7.0/build/fuses/fuses.json5)。外部 schema 仅用于序号和字节含义，不能将该版本当作 Owl 实际版本；Owl 的原生消费者与执行效果未验证。

RunAsNode、NODE_OPTIONS、NodeCliInspect 对应字节均为0，因此未据此尝试运行环境诊断。未改 fuse、签名或安装包，未启动客户端或提交模型任务。实际 Node/Electron 兼容版本和原生模块 ABI 仍unknown；完整 wire 与逐字节10条来源证据保留原始范围和 span digest。

embedded ASAR integrity 的启用值不解释此前7条 unpacked 声明矛盾，也不证明它们的运行校验通过。
'''
    (work / 'summary.md').write_text(summary)
    print(json.dumps({'path': str(work.relative_to(WORKSPACE)), 'sourceEvidenceRecords': len(evidence),
                      'observedWire': record['conclusions']['observedWire'], 'applicationLaunched': False}))


if __name__ == '__main__':
    main()
