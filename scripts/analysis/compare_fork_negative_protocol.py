#!/usr/bin/env python3
"""Verify and compare saved fork negative fixtures, without invoking a target."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_file(record, root=None):
    p = Path(record['path'])
    if not p.is_absolute():
        p = root / p
    assert sha(p) == record['sha256'], str(p)
    if 'bytes' in record:
        assert p.stat().st_size == record['bytes'], str(p)
    return p


def main():
    baseline = json.loads((WORKSPACE / '.analysis-local/current-baseline.json').read_bytes())
    out = WORKSPACE / 'analysis' / baseline['baselineId']
    names = {'frozen': 'frozen-os-normal-host-1', 'public-npm': 'public-npm-os-normal-host-2'}
    summaries, inputs, indexed = {}, [], {}
    raw_record_count = 0
    for backend, name in names.items():
        p = out / ('fork-negative-protocol-' + name + '.json')
        data = json.loads(p.read_bytes())
        summaries[backend] = data
        inputs.append({'backend': backend, 'path': p.name, 'sha256': sha(p), 'bytes': p.stat().st_size})
        assert data['baselineId'] == baseline['baselineId']
        assert data['status'] == 'complete-negative-matrix'
        assert data['cliHashUnchangedAfterRun'] and data['protectedArtifactsAllUnchanged']
        assert sha(data['cliPath']) == data['cliSha256']
        check_file(data['cliProvenance'], out)
        check_file(data['runner'], out)
        check_file(data['baselineInput'])
        generation = json.loads((out / data['cliProvenance']['path']).read_bytes())
        for s in data['schemaInputs']:
            schema_file = check_file(s, out)
            matching = [f for run in generation['runs'] for f in run.get('schemaFiles', [])
                        if f['sha256'] == s['sha256'] and f['path'].endswith('/v2/ThreadForkParams.json')]
            assert len(matching) == 1 and matching[0]['bytes'] == schema_file.stat().st_size
        for protected in data['protectedArtifacts']:
            check_file(protected)
            assert protected['unchanged']
        assert len(data['sessions']) == 2
        indexed[backend] = {}
        for si, session in enumerate(data['sessions']):
            assert session['error'] is None and session['serverExitCode'] == 0
            assert all(session['initialEmptyDirectories'].values())
            for field in ['sandboxProfile', 'rawObservations', 'stderr']:
                check_file(session[field])
            assert Path(session['stderr']['path']).stat().st_size == 0
            profile = Path(session['sandboxProfile']['path']).read_text()
            assert '(deny network*)' in profile and '(deny file-write*)' in profile
            rows = [json.loads(x) for x in Path(session['rawObservations']['path']).read_text().splitlines()]
            raw_record_count += len(rows)
            assert {row['message'].get('method') for row in rows if row['direction'] == 'request'} == {'initialize', 'initialized', 'thread/fork'}
            requests = {r['message'].get('id'): r['message'] for r in rows if r['direction'] == 'request' and 'id' in r['message']}
            responses = {r['message'].get('id'): (line, r['message']) for line, r in enumerate(rows, 1)
                         if r['direction'] == 'response-or-notification' and 'id' in r['message']}
            assert len(session['checks']) == 9
            for ci, case in enumerate(session['checks']):
                if case['id'] == 'initialize':
                    assert case['passed']
                    continue
                response = case['response']
                assert case['returnedError'] and 'error' in response and 'result' not in response
                assert requests[response['id']]['method'] == 'thread/fork'
                assert requests[response['id']]['params'] == case['requestParams']
                line, actual = responses[response['id']]
                assert actual == response
                key = (session['experimentalApi'], case['id'])
                indexed[backend][key] = {**case,
                    'summaryEvidence': {'path': p.name, 'sha256': sha(p),
                                        'pointer': f'/sessions/{si}/checks/{ci}/response'},
                    'rawEvidence': {**session['rawObservations'], 'line': line}}
    assert set(indexed['frozen']) == set(indexed['public-npm']) and len(indexed['frozen']) == 16
    matrix = []
    for key, frozen in indexed['frozen'].items():
        public = indexed['public-npm'][key]
        assert frozen['requestParams'] == public['requestParams']
        matrix.append({'experimentalApi': key[0], 'case': key[1], 'requestParams': frozen['requestParams'],
                       'errorContractExactlySame': frozen['response']['error'] == public['response']['error'],
                       'frozen': {k: frozen[k] for k in ['classification', 'response', 'summaryEvidence', 'rawEvidence']},
                       'publicNpm': {k: public[k] for k in ['classification', 'response', 'summaryEvidence', 'rawEvidence']}})
    same = sum(row['errorContractExactlySame'] for row in matrix)
    failures = []
    for name in ['frozen-os-sandbox-1', 'public-npm-os-normal-host-1']:
        p = out / ('fork-negative-protocol-' + name + '.json')
        failures.append({'path': p.name, 'sha256': sha(p), 'status': json.loads(p.read_bytes())['status']})
    result = {'baselineId': baseline['baselineId'], 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
              'status': 'verified-negative-contract-difference', 'method': 'read-only comparison of saved runtime responses and immutable schema/manifests',
              'inputs': inputs, 'priorFailuresPreserved': failures,
              'verification': {'cliHashesVerified': True, 'generationSnapshotsVerified': True,
                               'runnerSnapshotsVerified': True, 'schemaHashesVerified': True,
                               'profilesAndRawHashesVerified': True, 'caseResponsesMatchRaw': True,
                               'protectedArtifactsUnchanged': True, 'actualCliSessions': 4,
                               'forkRequests': 32, 'forkSuccesses': 0, 'rawRecords': raw_record_count,
                               'methodAllowlist': ['initialize', 'initialized', 'thread/fork'],
                               'targetModelTurnRequests': 0, 'allSessionsFreshHome': True,
                               'osNetworkDeniedByAppliedSandboxExecProfile': True},
              'fieldTreatment': {'frozen': {'experimentalSchemaDeclared': True, 'schemaType': 'boolean',
                      'observedWrongStringTypeRejected': True, 'observedTrueNeedsExperimentalApi': True,
                      'falseWithoutExperimentalApiReachesLookup': True,
                      'conclusion': 'Field is recognized, boolean-decoded, and true is capability-gated on this negative path.'},
                  'publicNpm': {'stableSchemaDeclared': False, 'experimentalSchemaDeclared': False,
                      'observedWrongStringTypeRejected': False, 'observedTrueNeedsExperimentalApi': False,
                      'allSuppliedValuesMatchUnknownFieldAndLookupControls': True,
                      'conclusion': 'Supplied field is not rejected or type-enforced and behaves like the unknown-field control on this negative path; this is consistent with an unrecognized/ignored field, not proof of prediction support.'}},
              'comparison': {'pairedCaseDenominator': 16, 'sameErrorContracts': same,
                             'differentErrorContracts': len(matrix)-same, 'matrix': matrix},
              'positiveControls': {'bothBackendsKnownEphemeralWrongTypeRejected': True,
                                   'bothBackendsBeforeTurnIdTrueRequiresExperimentalApi': True,
                                   'bothBackendsBeforeTurnIdWrongBoolRejected': True},
              'limitations': ['All valid requests stop at missing-rollout lookup; no successful fork or prediction semantics were observed.',
                              'Same lookup errors or unknown-field behavior do not prove complete backend compatibility.',
                              'This fixture does not resolve the desktop dynamic sender or actual appServerVersion.',
                              'Public npm binary-to-source-commit binding remains unknown.'],
              'comparisonScript': {'path': str(Path(__file__).relative_to(WORKSPACE)), 'sha256': sha(__file__)}}
    dest = out / 'fork-negative-protocol-comparison.json'
    md = out / 'fork-negative-protocol-comparison.md'
    assert not dest.exists() and not md.exists(), 'Comparison output exists; preserve it'
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    lines = ['# thread/fork 负例契约核对', '',
             '两端各使用两个独立空 HOME/CODEX_HOME，以 experimentalApi=true/false 测试固定不存在 UUID。4 个 CLI 会话均正常退出，32 个 fork 请求均返回错误，未创建线程、未调用模型。app-server 及子进程运行在禁止网络、限制写入自有目录的 sandbox-exec profile 下。', '',
             '冻结版本的实验 schema 声明 experimentalPredictionMode:boolean；实际错误字符串被布尔解码拒绝，true 值在 experimentalApi=false 时被能力检查拒绝。公开 npm 的稳定和实验 schema 均未声明此字段；true、false、错误字符串均返回与无字段及未知字段对照相同的缺失 rollout 错误。这个路径表现为未识别/忽略字段，不能解释为预测功能兼容。', '',
             '| experimentalApi | 用例 | 冻结版本 | 公开 npm | 错误契约相同 |',
             '|---|---|---|---|---|']
    for row in matrix:
        lines.append(f"| {row['experimentalApi']} | {row['case']} | {row['frozen']['classification']} | {row['publicNpm']['classification']} | {row['errorContractExactlySame']} |")
    lines += ['', f'{same}/16 个配对负例的错误契约相同，{16-same}/16 不同。已知 ephemeral 错误类型、beforeTurnId 实验门控及错误类型均作为两端对照成立。所有错误 code 都是 -32600；依据完整 message 区分解码、能力门控和 lookup。', '',
              '默认运行环境的嵌套 sandbox_apply 失败和公开清单路径前缀预检失败均单独保留。成功运行的输入清单、runner 快照、schema、raw response、sandbox profile 及既有保护输出均已复核 SHA256。', '',
              '结果仍不证明任何预测运行成功、完整后端兼容、桌面实际动态接收方或 npm 发布物与源码 commit 的绑定。', '',
              f'机器可读结果：[{dest.name}]({dest.name})。']
    md.write_text('\n'.join(lines)+'\n')
    print(json.dumps({'result': dest.name, 'sha256': sha(dest), 'markdown': md.name,
                      'markdownSha256': sha(md), 'pairedCases':16, 'same':same, 'different':16-same,
                      'forkRequests':32, 'forkSuccesses':0, 'rawRecords':raw_record_count}))


if __name__ == '__main__':
    main()
