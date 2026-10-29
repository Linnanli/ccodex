#!/usr/bin/env python3
"""Archive a frozen criteria audit and its exact historical inputs."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import tempfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def copy_frozen(source, destination, expected_hash, expected_bytes=None):
    data = source.read_bytes()
    assert digest(data) == expected_hash, source
    assert expected_bytes is None or len(data) == expected_bytes, source
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        assert destination.read_bytes() == data, ('Frozen archive differs', destination)
        return
    with tempfile.NamedTemporaryFile(dir=destination.parent, prefix='.audit-', delete=False) as stream:
        temporary = Path(stream.name)
    try:
        shutil.copy2(source, temporary)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


workspace = Path(__file__).resolve().parents[2]
baseline = json.loads((workspace / '.analysis-local/current-baseline.json').read_text())
out = workspace / 'analysis' / baseline['baselineId']
local = workspace / '.analysis-local/completion-audit-work'
manifest_path = local / 'criteria-audit.frozen-manifest.json'
manifest_bytes = manifest_path.read_bytes()
manifest = json.loads(manifest_bytes)
assert manifest['baselineId'] == baseline['baselineId']
archive = out / 'raw/criteria-audit' / manifest['publicationId']
bindings = []
for name, entry in manifest['files'].items():
    assert not Path(name).is_absolute() and '..' not in Path(name).parts
    source = Path(entry['path'])
    destination = out / name if name.startswith('criteria-audit.') else archive / 'scripts' / name
    copy_frozen(source, destination, entry['sha256'], entry['bytes'])
    bindings.append({'originalPath': str(source), 'archivedPath': str(destination.relative_to(workspace)),
                     'sha256': entry['sha256'], 'bytes': entry['bytes']})
for name, entry in manifest['inputs'].items():
    assert not Path(name).is_absolute() and '..' not in Path(name).parts
    source = Path(entry['snapshotPath'])
    destination = archive / 'inputs' / name
    copy_frozen(source, destination, entry['sha256'], entry['bytes'])
    bindings.append({'originalPath': str(source), 'originalPublicPath': entry['publicPath'],
                     'archivedPath': str(destination.relative_to(workspace)),
                     'sha256': entry['sha256'], 'bytes': entry['bytes']})
copy_frozen(manifest_path, out / manifest_path.name, digest(manifest_bytes), len(manifest_bytes))
audit = json.loads((out / 'criteria-audit.json').read_text())
validation = json.loads((out / 'criteria-audit.validation.json').read_text())
assert validation['status'] == 'passed'
assert validation['auditSha256'] == digest((out / 'criteria-audit.json').read_bytes())
assert validation['markdownSha256'] == digest((out / 'criteria-audit.md').read_bytes())
assert audit['publicationInput']['exitCode'] == 0
assert audit['publicationInput']['runnerUnchangedDuringRun']
provenance = {'baselineId': baseline['baselineId'], 'publicationId': manifest['publicationId'],
              'scope': manifest['scope'], 'auditManifestSha256': digest(manifest_bytes),
              'inputCount': len(manifest['inputs']), 'allArchivedHashesVerified': True,
              'bindings': bindings, 'counts': audit['counts']}
(out / 'criteria-audit-provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n')
record = {'recordedAtUtc': datetime.now(timezone.utc).isoformat(), 'baselineId': baseline['baselineId'],
          'method': 'byte-preserving-frozen-audit-publication', 'sourceManifestSha256': digest(manifest_bytes),
          'runnerPath': str(Path(__file__).relative_to(workspace)), 'runnerSha256': digest(Path(__file__).read_bytes()),
          'inputCount': len(manifest['inputs']), 'bindingsVerified': len(bindings),
          'provenanceSha256': digest((out / 'criteria-audit-provenance.json').read_bytes()),
          'targetProgramsExecuted': False, 'modelRequestsSubmitted': 0}
(archive / 'publication.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'archive': str(archive.relative_to(workspace)), 'inputs': record['inputCount'],
                  'verifiedBindings': record['bindingsVerified'], 'counts': audit['counts']}))
