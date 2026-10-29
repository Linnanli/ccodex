"""Publish bounded, saved analysis metadata without copying inspected code."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
DEST = ROOT / 'analysis' / BASELINE
copies = []
planned = {}


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def read(path):
    return json.loads(path.read_bytes())


def add_copy(source, target):
    assert source.is_file() and source.stat().st_mode & 0o222 == 0, source
    raw = source.read_bytes()
    assert target not in planned
    planned[target] = raw
    copies.append({'sourcePath': str(source), 'outputPath': str(target.relative_to(DEST)), **pin(raw)})


def add_reader(name, text):
    path = DEST / name
    assert path not in planned
    planned[path] = text.encode()


def selected_manifest(directory, manifest_name, confirmation_name, names):
    manifest = read(directory / manifest_name)
    confirmation = read(directory / confirmation_name)
    assert confirmation['manifest'] == pin((directory / manifest_name).read_bytes())
    by_name = {i['path']: i for i in manifest['files']}
    for name in names:
        if name in by_name:
            assert pin((directory / name).read_bytes()) == {k: by_name[name][k] for k in ['bytes', 'sha256']}


node = ROOT / '.analysis-local/node-pty-modification-contracts-work'
node_names = ['node-pty-modification-contracts.json', 'evidence.jsonl', 'summary.md', 'validation.json', 'frozen-manifest.json', 'freeze-confirmation.json']
selected_manifest(node, 'frozen-manifest.json', 'freeze-confirmation.json', node_names)
node_core = read(node / node_names[0])
node_validation = read(node / 'validation.json')
assert node_core['baselineId'] == BASELINE and node_core['counts']['records'] == 18
assert node_validation['checks'] == 524 and node_validation['status'] == 'passed' and node_validation['errors'] == []
assert [json.loads(x) for x in (node / 'evidence.jsonl').read_text().splitlines()] == node_core['records']
node_peer = ROOT / '.analysis-local/node-pty-modification-contracts-peer-work'
peer_names = ['review.json', 'review.md', 'attempts/review-02/receipt.json', 'freeze-manifest.json', 'freeze-confirmation.json', 'freeze-attempt-01/receipt.json']
assert pin((node_peer / 'review.json').read_bytes()) == {'bytes': 37394, 'sha256': '4f728adaa9778587f3ab06294a8f090c3760048ae1f4a4e041c35dbbbf170fb7'}
assert pin((node_peer / 'review.md').read_bytes()) == {'bytes': 2501, 'sha256': '1e71ab2fe6782b83a0ff47eb3e493b9d49aa995e0bdfe878c12a240d21a1ff6f'}
peer_review = read(node_peer / 'review.json')
assert peer_review['baselineId'] == BASELINE and peer_review['checkCount'] == 100 and not peer_review['errors']
assert read(node_peer / 'attempts/review-02/receipt.json')['exitCode'] == 0
assert read(node_peer / 'freeze-attempt-01/receipt.json')['exitCode'] == 0
for name in node_names:
    add_copy(node / name, DEST / 'raw/node-pty-modification-contracts/author' / name)
for name in peer_names:
    add_copy(node_peer / name, DEST / 'raw/node-pty-modification-contracts/independent-review' / name)
for source_name, output_name in [('node-pty-modification-contracts.json', 'node-pty-modification-contracts.json'), ('evidence.jsonl', 'node-pty-modification-contracts-evidence.jsonl'), ('validation.json', 'node-pty-modification-contracts-validation.json')]:
    add_copy(node / source_name, DEST / output_name)
add_copy(node_peer / 'review.json', DEST / 'node-pty-modification-contracts-peer-review.json')
node_copies = list(copies)
add_reader('node-pty-modification-contracts-summary.md', '# node-pty 修改与客户端调用边界\n\n固定 node-pty 1.1.0 的两个 Windows JS 有9处差异。所选静态范围形成18条记录（15确认、1推断、2未决）和11个未执行场景，见[合同](node-pty-modification-contracts.json)。\n\n修改增加进程枚举 callback，并改变部分终止分支的顺序和返回值：Promise rejection 可回退，同步调用错误不由该 catch 处理；pre-ready kill 只排队。普通同版本上游包不足以证明接口等价。应评估独立补丁依赖、受维护 fork 或等价适配器；第三方实现留在本地分析副本，未复制到正式合同或维护源码。\n\n[独立审查](node-pty-modification-contracts-peer-review.json)仅覆盖四个小型 package JS、9差异范围，100项检查。作者的[524项坐标及元数据验证](node-pty-modification-contracts-validation.json)另行统计；client main 的连续1383B声明窗口仅经作者静态分析，没有独立语义审查。原作者合同的 pending-peer 字段保留原字节，其后完成的有限 package peer 在[交付来源](node-pty-modification-contracts-provenance.json)单列。\n\n原生来源/ABI、完整包等价、Windows实际运行、模式归属及 renderer services.terminal 到 main adapter 的实例连接仍未知。11个作者场景与15个peer fixture均未执行，不能合并为已验证行为。\n')
planned[DEST / 'node-pty-modification-contracts-provenance.json'] = encode({'schemaVersion': 1, 'baselineId': BASELINE, 'status': 'bounded-static-contracts-with-package-only-peer', 'exactCopies': node_copies, 'authorRecords': 18, 'authorValidation': {'checks': 524, 'scope': 'saved coordinates and metadata only'}, 'independentPackageReview': {'checks': 100, 'scope': 'four small package JS only; client caller unreviewed'}, 'originalCorePendingPeerStatusPreserved': True, 'scenarioProposals': {'author': 11, 'peer': 15, 'executed': 0}, 'globalRecordsAdded': 0, 'runtimeRunsAdded': 0, 'additionalModelTasks': 0, 'sourceImplementationCopied': False})

cards = ROOT / '.analysis-local/settings-feature-operation-mapping-work'
card_names = ['settings-feature-operation-mapping.json', 'evidence.jsonl', 'summary.md', 'validation.json', 'handoff.json']
card_core = read(cards / card_names[0])
card_validation = read(cards / 'validation.json')
assert pin((cards / card_names[0]).read_bytes()) == {'bytes': 1081459, 'sha256': '606f04537f11b3e105945356d28b3ede0028614ed0f75677a9dba12bd99f00dc'}
assert card_core['baselineId'] == BASELINE and card_core['counts']['operationCards'] == 38
assert card_validation['checkCount'] == 2154 and card_validation['errors'] == []
assert card_core['counts']['featureIdsAssigned'] == card_core['counts']['newGlobalRecords'] == card_core['counts']['newModeClassifications'] == card_core['counts']['runtimeObservationsAdded'] == 0
assert not card_core['targetExecuted'] and not card_core['thirdPartyImplementationCopied'] and not card_core['oldLedgerModified']
assert len([json.loads(x) for x in (cards / 'evidence.jsonl').read_text().splitlines()]) == 38
card_copy_start = len(copies)
for name in card_names:
    add_copy(cards / name, DEST / 'raw/settings-feature-operation-mapping' / name)
for source_name, output_name in [('settings-feature-operation-mapping.json', 'settings-feature-operation-mapping.json'), ('evidence.jsonl', 'settings-feature-operation-mapping-evidence.jsonl'), ('summary.md', 'settings-feature-operation-mapping-summary.md'), ('validation.json', 'settings-feature-operation-mapping-validation.json')]:
    add_copy(cards / source_name, DEST / output_name)
planned[DEST / 'settings-feature-operation-mapping-provenance.json'] = encode({'schemaVersion': 1, 'baselineId': BASELINE, 'status': 'author-static-operation-mapping-independent-peer-not-claimed', 'exactCopies': copies[card_copy_start:], 'operationCards': {'total': 38, 'General': 32, 'Agent': 6}, 'validation': {'checks': 2154, 'scope': 'author metadata synthesis'}, 'GeneralAuthorship': 'The mapping author also authored the General source catalog; this is not an independent General source review.', 'scenarioProposals': 'Success/failure/cancel/recovery expectations per card; not runtime executions.', 'featureIdsAssigned': 0, 'globalRecordsAdded': 0, 'modeClassificationsAdded': 0, 'runtimeRunsAdded': 0, 'sourceImplementationCopied': False})

reader = ROOT / '.analysis-local/current-reader-publication-review-work'
assert pin((reader / 'publication-review.json').read_bytes()) == {'bytes': 6399, 'sha256': 'b1cbd9ee16bf555e7119443236ed65daa03dfb11f8e8dc5a5d240ba5af0a7e43'}
reader_copy_start = len(copies)
for name in ['publication-review.json', 'review.md']:
    add_copy(reader / name, DEST / 'raw/analysis-requirements-current-audit/reader-review' / name)
add_copy(reader / 'publication-review.json', DEST / 'analysis-requirements-current-audit-reader-peer-review.json')
planned[DEST / 'analysis-requirements-current-audit-reader-peer-provenance.json'] = encode({'schemaVersion': 1, 'baselineId': BASELINE, 'exactCopies': copies[reader_copy_start:], 'checkCount': 240, 'scope': 'Selected 16 reader inputs at the saved review snapshot. 9 exact-copy declarations and 142 existing local links; not source analysis or a completion claim.', 'limitations': 'Later publications are not retrospectively covered. External links checked syntactically only.', 'globalRecordsAdded': 0, 'runtimeRunsAdded': 0})

# Preflight every destination before writing any product.
for path, raw in planned.items():
    if path.exists():
        assert path.read_bytes() == raw, ('conflicting-existing-output', str(path))
for path, raw in planned.items():
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(raw)
    assert path.read_bytes() == raw
    path.chmod(0o444)
for item in copies:
    assert pin(Path(item['sourcePath']).read_bytes()) == {k: item[k] for k in ['bytes', 'sha256']}
    assert pin((DEST / item['outputPath']).read_bytes()) == {k: item[k] for k in ['bytes', 'sha256']}
print(json.dumps({'status': 'delivered', 'outputs': len(planned), 'exactCopies': len(copies), 'nodePtyRecords': 18, 'settingsOperationCards': 38, 'readerReviewChecks': 240, 'globalRecordsAdded': 0, 'runtimeRunsAdded': 0}))
