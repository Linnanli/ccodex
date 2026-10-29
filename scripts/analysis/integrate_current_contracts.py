"""Integrate delivered companions without regenerating prior analysis."""
import ast
import hashlib
import json
from pathlib import Path

from contract_reader_context import build_context

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASELINE


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


names = ['report.md', 'analysis-state.json', 'analysis-requirements-current-audit.md']
before = {}
for name in names:
    snapshot = OUT / 'raw/current-contracts' / ('reader-before-' + name)
    before[name] = snapshot.read_bytes() if snapshot.exists() else (OUT / name).read_bytes()
assert pin(before['report.md']) == {'bytes': 42804, 'sha256': '3e988822ad7283799586c619387e4f3e0a897322bf2b51457e2ab55c4ba7d794'}
assert pin(before['analysis-state.json']) == {'bytes': 132148, 'sha256': 'b513f669141f80741294ed7727bf5220d57676d33e5deff1e3c8027ad83fe3af'}
state = json.loads(before['analysis-state.json'])
assert state['fullAnalysisCompleted'] is False and state['featureDenominatorEstablished'] is False
protected_keys = ['fullAnalysisCompleted', 'featureDenominatorEstablished']
protected = {key: state[key] for key in protected_keys}
patch, note, artifacts = build_context(OUT, BASELINE)
assert len(patch) == 5
for name in ['publish_findings.py', 'record_publication.py', 'contract_reader_context.py', 'deliver_current_contracts.py', 'integrate_current_contracts.py']:
    ast.parse((ROOT / 'scripts/analysis' / name).read_bytes(), filename=name)
for name, raw in before.items():
    target = OUT / 'raw/current-contracts' / ('reader-before-' + name)
    target.parent.mkdir(parents=True, exist_ok=True)
    assert not target.exists() or target.read_bytes() == raw
    if not target.exists():
        target.write_bytes(raw)
    target.chmod(0o444)
state.update(patch)
assert all(state[key] == value for key, value in protected.items())
marker = '[完成标准审计](criteria-audit.md)'
report = before['report.md'].decode()
assert report.count(marker) == 1 and note not in report
# This reader is derived prose. The exact audit JSON and frozen original remain untouched.
audit = before['analysis-requirements-current-audit.md'].decode()
old = '[当前需求审计](analysis-requirements-current-audit.md)另按原计划'
assert audit.count(old) == 1
planned = {'analysis-state.json': encode(state),
           'report.md': report.replace(marker, note + '\n\n' + marker).encode(),
           'analysis-requirements-current-audit.md': audit.replace(old, '本次审计按原计划').encode()}
# Accept only the saved pre-state or this exact prior partial result.
for name, raw in planned.items():
    target = OUT / name
    assert target.parent.is_dir() and target.is_file() and not target.is_symlink()
    assert target.read_bytes() in [before[name], raw], ('unexpected-reader-change', name)
    temporary = target.with_name('.current-contracts-' + name)
    assert not temporary.exists()
for name, raw in planned.items():
    target = OUT / name
    if target.read_bytes() != raw:
        temporary = target.with_name('.current-contracts-' + name)
        temporary.write_bytes(raw)
        temporary.chmod(target.stat().st_mode & 0o777)
        temporary.replace(target)
    assert target.read_bytes() == raw
print(json.dumps({'status': 'integrated', 'companionIndices': len(patch), 'selectedArtifactPaths': len(artifacts),
    'outputs': {name: pin((OUT / name).read_bytes()) for name in before},
    'fullAnalysisCompleted': False, 'featureDenominatorEstablished': False,
    'globalRecordsAdded': 0, 'runtimeRunsAdded': 0, 'additionalModelTasks': 0}))
