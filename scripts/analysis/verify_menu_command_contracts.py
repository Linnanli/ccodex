#!/usr/bin/env python3
"""Verify original frozen bytes, reference integrity and stable contract coordinates."""
import hashlib
import json
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[2]
output = root / '.analysis-local/entry-work'
baseline = json.loads((root / '.analysis-local/current-baseline.json').read_text())
manifest = json.loads((root / 'analysis' / baseline['baselineId'] / 'files.json').read_text())
file_index = {entry['archivePath']: entry for entry in manifest['archiveFiles']}
contracts_path = output / 'menu-command-contracts.json'
evidence_path = output / 'menu-command-evidence.jsonl'
contracts = json.loads(contracts_path.read_text())
evidence = [json.loads(line) for line in evidence_path.read_text().splitlines()]
digest = lambda value: hashlib.sha256(value).hexdigest()
assert contracts['baselineId'] == baseline['baselineId']
assert len({entry['id'] for entry in evidence}) == len(evidence)
assert [entry['id'] for entry in evidence] == [f'ENTRY-AST-E{i:05d}' for i in range(1, len(evidence) + 1)]
by_id = {entry['id']: entry for entry in evidence}
sources = {}
for entry in evidence:
    assert entry['baselineId'] == baseline['baselineId']
    relative = entry['sourcePath'].removeprefix('app.asar/')
    if relative not in sources:
        data = (Path(baseline['extractedDirectory']) / relative).read_bytes()
        assert digest(data) == file_index[relative]['sha256']
        sources[relative] = data
    data = sources[relative]
    assert entry['sourceHash'] == file_index[relative]['sha256']
    span = entry['locator']
    assert span['kind'] == 'byte-range'
    assert 0 <= span['start'] < span['endExclusive'] <= len(data)
    assert digest(data[span['start']:span['endExclusive']]) == entry['spanHash']

references = []
def walk(value, pointer=''):
    if isinstance(value, str) and value.startswith('ENTRY-AST-E'):
        assert value in by_id, (pointer, value)
        references.append((pointer, value))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            walk(item, f'{pointer}/{index}')
    elif isinstance(value, dict):
        for key, item in value.items():
            walk(item, f'{pointer}/{key}')
walk(contracts)

ids = []
for record in contracts['contractRecordIndex']:
    target = contracts
    for segment in record['jsonPointer'].split('/')[1:]:
        target = target[int(segment)] if isinstance(target, list) else target[segment]
    assert target['contractId'] == record['contractId']
    assert target[record['primaryEvidenceKey']] == record['primaryEvidenceId']
    original = by_id[record['primaryEvidenceId']]
    coordinates = record['coordinates']
    assert coordinates['baselineId'] == baseline['baselineId']
    assert coordinates['sourcePath'] == original['sourcePath']
    assert coordinates['sourceHash'] == original['sourceHash']
    assert coordinates['start'] == original['locator']['start']
    assert coordinates['endExclusive'] == original['locator']['endExclusive']
    encoded = json.dumps(coordinates, separators=(',', ':'), ensure_ascii=False).encode()
    assert record['contractId'] == record['kind'] + ':' + digest(encoded)[:24]
    ids.append(record['contractId'])
assert len(set(ids)) == len(ids) == contracts['summary']['contractRecords']
assert len(evidence) == contracts['summary']['evidenceRecords']
assert len(contracts['metadataRegistry']['commands']) == contracts['summary']['metadataCommandInstances']
assert len({row['definitionEvidenceId'] for row in contracts['metadataRegistry']['commands']}) == contracts['summary']['metadataCommandSchemaSites']
for reviewed in contracts['summary']['rendererReviewInputs']:
    assert digest((output / reviewed['name']).read_bytes()) == reviewed['sha256']

report = {
    'baselineId': baseline['baselineId'],
    'originalEvidenceSpansVerified': len(evidence),
    'originalFrozenSourceFilesVerified': len(sources),
    'evidenceReferencesVerified': len(references),
    'stableContractCoordinatesVerified': len(ids),
    'contractKinds': dict(Counter(row['kind'] for row in contracts['contractRecordIndex'])),
    'inputSha256': {
        contracts_path.name: digest(contracts_path.read_bytes()),
        evidence_path.name: digest(evidence_path.read_bytes()),
    },
    'limitations': 'Original bytes and reference/coordinate integrity only; this check does not prove semantic completeness, original whole-source renderer bindings, feature mode or runtime behavior.',
}
(output / 'menu-command-validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
