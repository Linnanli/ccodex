"""Append reviewed operation and file-change readers without regenerating old analysis."""
import ast
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


snapshots = {}
for name, expected in [('report.md', (44566, '4c74a425287c20d03d747e99536d749b77ec6583c5f20d2f3cac084c175bc367')),
                       ('analysis-state.json', (134085, '5c9b9fd303f67367c36b1446f78ee0afe400d59abfdd04dbc5882b3992d6bc9e'))]:
    path = OUT / 'raw/reviewed-contracts' / ('reader-before-' + name)
    raw = path.read_bytes() if path.exists() else (OUT / name).read_bytes()
    assert pin(raw) == {'bytes': expected[0], 'sha256': expected[1]}
    snapshots[name] = raw

proof_groups = [
    ('current-contracts', ROOT / '.analysis-local/current-contracts-publication-verification-work',
     [('final-review.json', 3332, '5fbd11ff3fb8c0136c19610c2aea49d3fd853f01403a749b8331814168c6a6fe'),
      ('final-review.md', 1097, 'dbdd2fa4bb8045feef5f8d2f90d48debb26f8950b2f6ac17f86a77ab7dfd50d9'),
      ('attempts/verify-01/receipt.json', 1944, 'ca8c54a4f389d2e93533ed5e66fe0a8288f06b4e0766f446acc60a2ca1a67f84'),
      ('links-peer/final-review.json', 12888, '246e641948af78d011e5062d55fa3acab123aac7d2b506c6bfa761e195fc6a98'),
      ('links-peer/final-review.md', 552, '2e85a7ce574aa9e366be4fdadb2b66fc4930890c09464f397bb0205f142d374e'),
      ('links-peer/attempts/attempt-03/receipt.json', 2457, '6b40a2f2fa10efce3e3afbd6fa7e3235ca2a25b68db6cbf5d740444e8c53df84')]),
    ('file-change-view-contracts', ROOT / '.analysis-local/file-change-delivery-code-peer-work',
     [('review.json', 13980, 'c4e78c63bd91cc48ed84a2e81463c3ed0959b66da3a47812c8f246bf3ee2697a'),
      ('review.md', 1937, '532cd68fa73e0768f40cd4a31cd69b88973e5e63fbd2fd7c5bebf236fd5b1c9d'),
      ('attempts/review-01/receipt.json', 2083, '876c0281426301c713f28e3574b6aa30132d6f6f7141540d8b779a8ff66b32eb')]),
]
planned_copies = {}
for kind, source_root, files in proof_groups:
    copies = []
    for name, size, digest in files:
        source = source_root / name
        raw = source.read_bytes()
        assert source.is_file() and not source.is_symlink() and source.stat().st_mode & 0o222 == 0
        assert pin(raw) == {'bytes': size, 'sha256': digest}
        relative = 'raw/' + kind + '/publication-review/' + name
        planned_copies[relative] = raw
        copies.append({'original': str(source), 'path': relative, **pin(raw)})
    if kind == 'current-contracts':
        name, checks, scope = 'publication-review-provenance.json', [902, 281], 'Five companion reader snapshot before file-change and operation-reader integration; counts kept separate.'
    else:
        name, checks, scope = 'delivery-code-peer-provenance.json', [280], 'Post-delivery static code/plan review only, not original source semantics or a pre-delivery gate.'
    index = {'schemaVersion': 1, 'baselineId': BASELINE, 'copies': copies, 'checkScopes': checks,
             'scope': scope, 'targetExecuted': False, 'globalRecordsAdded': 0, 'runtimeRunsAdded': 0}
    planned_copies['raw/' + kind + '/' + name] = encode(index)
for name, raw in snapshots.items():
    planned_copies['raw/reviewed-contracts/reader-before-' + name] = raw
for relative, raw in planned_copies.items():
    target = OUT / relative
    assert target.resolve().is_relative_to(OUT.resolve()) and not target.is_symlink()
    assert not target.exists() or target.read_bytes() == raw
for relative, raw in planned_copies.items():
    target = OUT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_bytes(raw)
    target.chmod(0o444)

state = json.loads(snapshots['analysis-state.json'])
assert state['fullAnalysisCompleted'] is False and state['featureDenominatorEstablished'] is False
patch, _, artifacts = build_context(OUT, BASELINE)
assert len(patch) == 7
new_keys = ['fileChangeViewContracts', 'functionalOperationReconciliation']
assert all(key not in state for key in new_keys)
assert all(state[key] == value for key, value in patch.items() if key not in new_keys)
updated = {**state, **{key: patch[key] for key in new_keys}}
assert all(updated[key] == value for key, value in state.items())
notes = '\n\n'.join(profile[4] for profile in PROFILES if profile[0] in new_keys)
notes += '\n\n[五项索引发布复核](raw/current-contracts/publication-review/final-review.md)按其固定发布前快照核对902项元数据及281项链接／语法，计数分列；不追认后续文件v2、操作目录或新helper。另有[文件交付代码事后审查](raw/file-change-view-contracts/publication-review/review.md)，280项静态检查只针对脚本／plan，不扩大原源码语义或运行结论。'
marker = '[完成标准审计](criteria-audit.md)'
report = snapshots['report.md'].decode()
assert report.count(marker) == 1 and notes not in report
planned = {'analysis-state.json': encode(updated), 'report.md': report.replace(marker, notes + '\n\n' + marker).encode()}
for name in ['publish_findings.py', 'record_publication.py', 'contract_reader_context.py',
             'deliver_functional_reconciliation.py', 'integrate_reviewed_contracts.py']:
    ast.parse((ROOT / 'scripts/analysis' / name).read_bytes(), filename=name)
for name, raw in planned.items():
    target = OUT / name
    assert target.is_file() and not target.is_symlink() and target.read_bytes() in [snapshots[name], raw]
    assert not target.with_name('.reviewed-contracts-' + name).exists()
for name, raw in planned.items():
    target = OUT / name
    if target.read_bytes() != raw:
        temporary = target.with_name('.reviewed-contracts-' + name)
        temporary.write_bytes(raw)
        temporary.chmod(target.stat().st_mode & 0o777)
        temporary.replace(target)
    assert target.read_bytes() == raw
print(json.dumps({'status': 'integrated', 'companionIndices': len(patch), 'newFields': new_keys,
                  'selectedArtifactPaths': len(artifacts), 'proofCopies': 9,
                  'outputs': {name: pin(raw) for name, raw in planned.items()},
                  'priorStateUnchanged': True, 'fullAnalysisCompleted': False,
                  'featureDenominatorEstablished': False, 'globalRecordsAdded': 0,
                  'runtimeRunsAdded': 0, 'additionalModelTasks': 0}))
