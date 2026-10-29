"""Publish bounded repository injection and snapshot context contracts once."""
import datetime
import hashlib
import json
from pathlib import Path
from contract_reader_context import PROFILES, build_context

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
W = ROOT / '.analysis-local/host-state-di-work'
A = W / 'author-01'
PREFIX = 'raw/host-state-di/'


def pin(b):
    return {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}


def encode(d):
    return (json.dumps(d, ensure_ascii=False, indent=2) + '\n').encode()


def read(p):
    return json.loads(p.read_bytes())


c = read(A / 'host-state-di-contracts.json')
counts = read(A / 'counts.json')
verification = read(W / 'verification-01.json')
assert verification['status'] == 'passed' and verification['uniqueSourceSpansChecked'] == 2753
assert len(c['selectedUnits']) == 47 and len(c['facts']) == 20 and len(c['programLexicalJoins']) == 1403
stages = ['analyze-01', 'analyze-02', 'analyze-03', 'window-services-01', 'trust-01', 'extract-01',
          'observe-01', 'observe-02', 'curate-01', 'verify-author-01', 'verify-author-02']
for stage in stages:
    receipt = read(W / 'attempts' / stage / 'receipt.json')
    assert receipt['exitCode'] == (1 if stage in ['analyze-01', 'analyze-02', 'observe-01', 'verify-author-01'] else 0)
    assert receipt['sourcesUnchanged']
planned, copies = {}, []


def copy(relative, path, kind='analysis_metadata'):
    b = path.read_bytes()
    target = PREFIX + relative
    assert target not in planned
    planned[target] = b
    copies.append({'original': str(path), 'outputPath': target, **pin(b), 'kind': kind})


names = ['host-state-di-contracts.json', 'host-state-di-scenarios.json']
for name in names:
    copy('author/' + name, A / name)
    planned[name] = (A / name).read_bytes()
for name in ['counts.json', 'summary.md']:
    copy('author/' + name, A / name)
copy('author/verification-01.json', W / 'verification-01.json')
for number in [1, 2]:
    copy(f'observations/observations-{number:02}.json', W / f'observations-{number:02}.json', 'synthetic_vm_observations')
planned['host-state-di-observations.json'] = (W / 'observations-02.json').read_bytes()
planned['host-state-di-summary.md'] = (A / 'summary.md').read_bytes()
for folder in sorted(p for p in W.glob('source-*') if p.is_dir()):
    for path in sorted(folder.iterdir()):
        assert path.suffix in ['.json', '.txt']
        copy('analysis/' + folder.name + '/' + path.name, path,
             'partial_source_from_failed_derived_analysis' if folder.name in ['source-01', 'source-02'] else
             'selected_application_source' if path.suffix == '.txt' else 'analysis_metadata')
for stage in stages:
    for path in sorted((W / 'attempts' / stage).iterdir()):
        copy('attempts/' + stage + '/' + path.name, path,
             'analysis_tool_source' if path.suffix in ['.py', '.mjs'] else 'execution_metadata')
records = []
for fact in c['facts']:
    r = fact['sourceReferences'][0]
    records.append({'id': fact['id'], 'baselineId': BASE, 'claim': fact['claim'],
                    'sourcePath': r['sourcePath'], 'sourceHash': r['sourceHash'],
                    'locator': {'kind': 'byte-range', **r['byteRange']}, 'spanHash': r['spanHash'],
                    'sourceReferences': fact['sourceReferences'], 'method': fact['method'],
                    'confidence': fact['confidence'], 'verificationStatus': fact['verificationStatus'],
                    'qualification': fact['qualification'], 'mode': 'unknown',
                    'newGlobalEvidenceRecord': False, 'actualUiControlExecuted': False})
planned['host-state-di-evidence.jsonl'] = ('\n'.join(json.dumps(x, ensure_ascii=False) for x in records) + '\n').encode()
index = {'schemaVersion': 1, 'baselineId': BASE, 'kind': 'bounded-host-repository-injection-and-snapshot-context',
         'publishedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'exactCopies': copies,
         'derived': [{'path': n, **pin(planned[n])} for n in names + ['host-state-di-summary.md', 'host-state-di-evidence.jsonl', 'host-state-di-observations.json']],
         **counts, **c['constraints'], 'fullConstructorsExecuted': False,
         'uniqueSourceSpansChecked': 2753, 'sourceCoordinateOccurrencesChecked': 13448,
         'sourceFilesByteChecked': 3, 'retainedPartialUnitsByteChecked': 6,
         'clientDependencyImplementationGenerated': False}
planned['host-state-di-provenance.json'] = encode(index)
readers = ['report.md', 'analysis-state.json', 'implementation-plan.md', 'gaps.md', 'behavior-checks.md']
before = {n: (OUT / n).read_bytes() for n in readers}
old = json.loads(before['analysis-state.json'])
assert len(old) == 96 and 'hostStateDi' not in old and not old['fullAnalysisCompleted']
assert old['latestBehaviorAuthorizationState']['groupRemaining'] == 0
for item in c['inputPins']:
    assert pin((OUT / item['path']).read_bytes()) == {k: item[k] for k in ['bytes', 'sha256']}
previous, _, _ = build_context(OUT, BASE)
assert len(previous) == 30 and all(old[k] == v for k, v in previous.items())
for name in planned:
    assert not (OUT / name).exists()
for name, data in planned.items():
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(0o444)
patch, _, artifacts = build_context(OUT, BASE)
assert len(patch) == len(PROFILES) == 31
assert all(old[k] == v for k, v in patch.items() if k != 'hostStateDi')
state = {**old, 'hostStateDi': patch['hostStateDi']}
assert all(state[k] == v for k, v in old.items())
note = next(p[4] for p in PROFILES if p[0] == 'hostStateDi')
marker = '[完成标准审计](criteria-audit.md)'
report = before['report.md'].decode()
assert report.count(marker) == 1
changes = {'analysis-state.json': encode(state), 'report.md': report.replace(marker, note + '\n\n' + marker).encode()}
additions = {
    'implementation-plan.md': '\n\n[仓库注入与窗口context](host-state-di-summary.md)关闭所选hXe→MMe同对象与vXe→窗口服务→首次快照的静态连接。恢复接口需保留仓库身份、登记集合、frame／URL条件、context先写后回调及快照初值；不能把内存共享误作持久化。真实构造／消息仍待验，第三方实现继续通过依赖引入。\n',
    'gaps.md': '\n\n[仓库注入增量](host-state-di-summary.md)关闭上一批MMe／hXe同对象及$Xe实际参数、窗口context来源的静态缺口；18事实／2推断另存，不追溯改变旧合同范围。真实构造、窗口登记与IPC、React provider、远程连接查询和耐久保存仍未知。修正版26项合成观察通过；7条真实规格未执行，37功能／26队列／160规格与模式排除保持。\n',
    'behavior-checks.md': '\n\n[窗口快照26项隔离观察](host-state-di-observations.json)执行24单位3947字节，所有窗口、IPC、context构造与环境均为替身。首版25项有1条故障注入断言失败；修正版26项通过并补bound函数场景，两次共51次执行。完整工厂／构造未运行，[7条真实规格](host-state-di-scenarios.json)未执行；没有新增客户端、设置或模型操作，模型样例额度余0。\n',
}
for name, text in additions.items():
    changes[name] = before[name] + text.encode()
readme_before = (ROOT / 'README.md').read_bytes()
readme = readme_before + ('\n- [仓库注入与首次快照：静态实例连接及26项合成观察](analysis/' + BASE + '/host-state-di-summary.md)\n').encode()
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
    temporary = path.with_name('.host-state-di-' + path.name)
    assert not temporary.exists()
    temporary.write_bytes(data)
    temporary.chmod(path.stat().st_mode & 0o777)
    temporary.replace(path)
assert (ROOT / 'README.md').read_bytes() == readme_before
temporary = ROOT / '.host-state-di-README.md'
assert not temporary.exists()
temporary.write_bytes(readme)
temporary.chmod((ROOT / 'README.md').stat().st_mode & 0o777)
temporary.replace(ROOT / 'README.md')
print(json.dumps({'status': 'published-and-integrated', 'companionIndices': len(patch), 'oldStateKeysPreserved': len(old),
                  'newStateKeys': 1, 'selectedArtifactsBeforeOwnCapture': len(artifacts),
                  'snapshots': [{'path': n, **pin(b)} for n, b in snapshots.items()],
                  'outputs': {n: pin(b) for n, b in changes.items()}, 'modelSubmissionsAdded': 0, 'fullAnalysisCompleted': False}))
