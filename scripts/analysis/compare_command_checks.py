#!/usr/bin/env python3
"""Compare recorded command fixtures without running either backend."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    workspace = Path(__file__).resolve().parents[2]
    baseline = json.loads((workspace / '.analysis-local/current-baseline.json').read_text())
    out = workspace / 'analysis' / baseline['baselineId']
    runs = {}
    expected_ids = ['initialize', 'command-completion', 'command-nonzero-exit',
                    'command-input-validation', 'command-stream-and-terminate']
    for source, name in [('frozen', 'frozen-home-normal-host'), ('public-npm', 'public-npm-manifest-snapshot')]:
        record_path = out / ('command-protocol-' + name + '.json')
        record = json.loads(record_path.read_text())
        assert record['baselineId'] == baseline['baselineId']
        assert record['cliSource'] == source and record['error'] is None and record['serverExitCode'] == 0
        assert [check['id'] for check in record['checks']] == expected_ids
        assert all(check['passed'] for check in record['checks'])
        assert digest(out / record['rawObservations']['path']) == record['rawObservations']['sha256']
        provenance_path = out / record['cliProvenance']['path']
        assert digest(provenance_path) == record['cliProvenance']['sha256']
        provenance = json.loads(provenance_path.read_text())
        assert digest(Path(provenance['cliPath'])) == record['cliSha256'] == provenance['cliSha256']
        runner_snapshot = out / record['runner'].get('snapshotPath', 'raw/command-protocol/' + name + '/runner-source.py')
        assert digest(runner_snapshot) == record['runner']['sha256']
        checks = {check['id']: check for check in record['checks']}
        raw = [json.loads(line) for line in (out / record['rawObservations']['path']).read_text().splitlines()]
        initialization = next(row['message']['result']['returnedKeys'] for row in raw
                              if row['direction'] == 'response-or-notification' and row['message'].get('id') == 1)
        contracts = {
            'initialize': {'returnedKeys': initialization},
            'command-completion': checks['command-completion']['observed'],
            'command-nonzero-exit': checks['command-nonzero-exit']['observed'],
            'command-input-validation': {'errorCode': checks['command-input-validation']['observedErrorCode']},
            'command-stream-and-terminate': {
                'terminationResult': checks['command-stream-and-terminate']['terminationResponse']['result'],
                'finalResult': checks['command-stream-and-terminate']['finalResponse']['result'],
                'streamOutputMatchesFixture': checks['command-stream-and-terminate']['streamOutputMatchesFixture'],
            },
        }
        runs[source] = {'record': record_path.name, 'sha256': digest(record_path),
                        'cliSha256': record['cliSha256'], 'contracts': contracts,
                        'environmentPolicy': record['environmentPolicy'],
                        'allChecksPassed': True}
    comparisons = [{'id': key, 'equal': runs['frozen']['contracts'][key] == runs['public-npm']['contracts'][key],
                    'frozen': runs['frozen']['contracts'][key], 'public': runs['public-npm']['contracts'][key]}
                   for key in expected_ids]
    result = {'baselineId': baseline['baselineId'], 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
              'status': 'compared', 'scope': 'five owned readOnly/no-network non-model command fixtures',
              'runs': runs, 'comparisons': comparisons,
              'equalContracts': sum(row['equal'] for row in comparisons),
              'limitations': [
                  'Initialization values were excluded; only response keys were compared.',
                  'Fixture outputs, error codes and terminate results are compared; timestamps and timing are not.',
                  'The frozen CLI hash identifies its shell entry wrapper; the public CLI hash identifies its native executable.',
                  'No desktop UI, model turn, approval, terminal PTY, submitted-thread recovery or complete backend compatibility is established.',
                  'The npm release source relationship to the pinned public Rust commit remains unknown.',
              ]}
    path = out / 'command-backend-comparison.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    lines = ['# 独立命令场景后端比较', '',
             '冻结随包 CLI 与公开 npm `0.162.0` 分别使用新建专用 HOME/CODEX_HOME；两者五项检查均通过。', '',
             '| 场景 | 保存结果是否相同 |', '| --- | --- |']
    lines.extend('| ' + row['id'] + ' | ' + ('是' if row['equal'] else '否') + ' |' for row in comparisons)
    lines.extend(['', '比较完成输出、非零退出、参数错误码、流式样例输出和取消结果；initialize 仅比较返回字段名。', '',
                  '这组场景使用 readOnly/no-network 策略，未提交模型任务。结果不证明桌面、PTY、审批或整个后端兼容。', '',
                  '公开 npm 包与固定 Rust 提交的源码关系仍为 unknown。冻结 CLI 哈希是入口 shell wrapper，公开 CLI 哈希是 native executable，不能直接用两者哈希判断二进制差异。', '',
                  '来源：[完整比较](command-backend-comparison.json)、[冻结运行](command-protocol-frozen-home-normal-host.json)、[公开运行](command-protocol-public-npm-manifest-snapshot.json)。', ''])
    (out / 'command-backend-comparison.md').write_text('\n'.join(lines))
    print(json.dumps({'equalContracts': result['equalContracts'], 'contracts': len(comparisons), 'path': str(path)}))


if __name__ == '__main__':
    main()
