#!/usr/bin/env python3
"""Rehash frozen/runtime archives and every observed ASAR integrity conflict."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

workspace = Path(__file__).resolve().parents[2]
baseline = json.loads((workspace / '.analysis-local/current-baseline.json').read_text())
out = workspace / 'analysis' / baseline['baselineId']
summary = json.loads((out / 'rea-summary.json').read_text())
apps = {'source': Path(baseline['sourceApplication']), 'frozen': Path(baseline['snapshotApplication']),
        'runtime': workspace / '.analysis-local/runtime' / baseline['baselineId'] / 'ChatGPT.app'}


def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as stream:
        while data := stream.read(4 * 1024 * 1024):
            h.update(data)
    return h.hexdigest()


archives = {label: {'path': str(app / 'Contents/Resources/app.asar'),
                    'sha256': digest(app / 'Contents/Resources/app.asar')}
            for label, app in apps.items()}
conflicts = []
for c in summary['evidence']['normalized_result']['integrity_contradictions']:
    actual = {}
    for label, app in apps.items():
        p = app / 'Contents/Resources/app.asar.unpacked' / c['logical_path']
        actual[label] = {'sha256': digest(p), 'bytes': p.stat().st_size}
    conflicts.append({**c, 'copies': actual,
                      'allCopiesMatchObserved': all(x['sha256'] == c['observed_sha256'] for x in actual.values())})
record = {'baselineId': baseline['baselineId'], 'verifiedAtUtc': datetime.now(timezone.utc).isoformat(),
          'expectedArchiveSha256': baseline['archiveSha256'], 'archives': archives,
          'archiveCopiesMatchBaseline': all(x['sha256'] == baseline['archiveSha256'] for x in archives.values()),
          'conflictCount': len(conflicts), 'conflicts': conflicts,
          'allConflictCopiesMatchObserved': all(x['allCopiesMatchObserved'] for x in conflicts),
          'declaredIntegrityVerified': False,
          'limitations': ['Matching copies establish observed input identity; the declared unpacked integrity contradictions remain unresolved.',
                          'Signing or packaging may affect native bytes, but no causal attribution has been established.']}
(out / 'baseline-reverification.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: record[k] for k in ['archiveCopiesMatchBaseline', 'conflictCount', 'allConflictCopiesMatchObserved', 'declaredIntegrityVerified']}))
