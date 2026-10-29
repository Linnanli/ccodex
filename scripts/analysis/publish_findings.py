#!/usr/bin/env python3
"""Publish stage findings and validate evidence against frozen source hashes."""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from scoped_catalogs import publish_scoped_catalogs
from static_boundaries import publish_static_boundaries
from catalog_supplements import publish_catalog_supplements


def publish_copy(source, destination):
    """Publish frozen files atomically without changing the read-only producer."""
    source, destination = Path(source), Path(destination)
    if destination.exists() and hashlib.sha256(source.read_bytes()).digest() == hashlib.sha256(destination.read_bytes()).digest():
        return
    with tempfile.NamedTemporaryFile(dir=destination.parent, prefix='.publication-', delete=False) as stream:
        temporary = Path(stream.name)
    try:
        shutil.copy2(source, temporary)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


workspace = Path(__file__).resolve().parents[2]
baseline = json.loads((workspace / '.analysis-local/current-baseline.json').read_text())
out = workspace / 'analysis' / baseline['baselineId']
feature_work = workspace / '.analysis-local/feature-work'
for name in ['features.csv', 'features.json', 'modules.json', 'routes.json', 'settings.json',
             'app-server-methods.json', 'boundaries.json', 'coverage.json']:
    destination = 'feature-coverage.json' if name == 'coverage.json' else name
    publish_copy(feature_work / name, out / destination)
ipc = {'baselineId': baseline['baselineId'],
       'channels': json.loads((feature_work / 'ipc-channels.json').read_text()),
       'transports': json.loads((feature_work / 'ipc-transport-contracts.json').read_text()),
       'hostMessageTypes': json.loads((feature_work / 'host-message-types.json').read_text()),
       'verificationStatus': 'static candidates and reviewed transport contracts; runtime contract tests pending'}
host_contract_source = feature_work / 'host-message-contracts.json'
if host_contract_source.exists():
    for name in ['host-message-contracts.json', 'host-message-contract-summary.json', 'host-message-contract-evidence.jsonl']:
        publish_copy(feature_work / name, out / name)
    host_ast = json.loads(host_contract_source.read_text())
    ipc['centralDispatcherAst'] = {'path': 'host-message-contracts.json', 'summary': host_ast['summary']}
    ipc['hostMessageTypesScope'] = '171 lexical case labels including 28 nested browser command labels; 143 top-level types in AST'
route_source = feature_work / 'route-contracts.json'
route_ast = None
if route_source.exists():
    for name in ['route-contracts.json', 'route-contract-summary.json', 'route-contract-summary.md', 'route-contract-evidence.jsonl']:
        publish_copy(feature_work / name, out / name)
    route_ast = json.loads(route_source.read_text())
    ipc['routeAstIndex'] = {'path': 'route-contracts.json', 'summary': route_ast['summary'],
                            'scope': 'route registrations and source identities; not IPC or mode verification'}
observations = [json.loads(p.read_text()) for p in sorted((out / 'runtime-artifacts').glob('*.json'))]
(out / 'behavior-observations.json').write_text(json.dumps(observations, ensure_ascii=False, indent=2) + '\n')
evidence = []
reused_evidence = []
chunk_source = workspace / '.analysis-local/review-work/chunk-transport.json'
if chunk_source.exists():
    publish_copy(chunk_source, out / 'chunk-transport.json')
    evidence.extend(json.loads(chunk_source.read_text())['evidence'])
auth_source = workspace / '.analysis-local/auth-work/auth-boundary.json'
if auth_source.exists():
    publish_copy(auth_source, out / 'auth-boundary.json')
    auth = json.loads(auth_source.read_text())
    for e in auth['evidence']:
        source_path = e['sourcePath']
        if source_path.startswith('ChatGPT.app/'):
            source_path = source_path[len('ChatGPT.app/'):]
        else:
            source_path = 'app.asar/' + source_path
        evidence.append({'id': e['id'], 'baselineId': baseline['baselineId'],
                         'claim': e['claim'], 'sourcePath': source_path,
                         'sourceHash': e['sourceHash']['value'],
                         'locator': {'kind': 'byte-range', 'start': e['range']['byteStart'],
                                     'endExclusive': e['range']['byteEndExclusive']},
                         'method': 'frozen-binary-string-indicator' if e['kind'] == 'binary-string' else 'frozen-source-review',
                         'confidence': 'inferred' if e['confidence'] == 'indicator-only' else e['confidence'],
                         'verificationStatus': 'source-recorded; account-origin-unresolved'})
for source in [out / 'dependency-evidence.jsonl', out / 'source-map-evidence.jsonl', feature_work / 'evidence.jsonl']:
    evidence.extend(json.loads(line) for line in source.read_text().splitlines() if line.strip())
if host_contract_source.exists():
    evidence.extend(json.loads(line) for line in (out / 'host-message-contract-evidence.jsonl').read_text().splitlines() if line.strip())
if route_ast:
    evidence.extend(json.loads(line) for line in (out / 'route-contract-evidence.jsonl').read_text().splitlines() if line.strip())
wrapper_source = workspace / '.analysis-local/review-work/request-wrapper-contracts.json'
wrapper_contracts = None
if wrapper_source.exists():
    wrapper_contracts = json.loads(wrapper_source.read_text())
    assert wrapper_contracts['baselineId'] == baseline['baselineId']
    publish_copy(wrapper_source, out / 'request-wrapper-contracts.json')
    wrapper_evidence_source = wrapper_source.with_name('request-wrapper-evidence.jsonl')
    publish_copy(wrapper_evidence_source, out / wrapper_evidence_source.name)
    summary_source = wrapper_source.with_name('request-wrapper-summary.md')
    if summary_source.exists():
        publish_copy(summary_source, out / summary_source.name)
    existing_evidence_indices = {entry['id']: index for index, entry in enumerate(evidence)}
    for line in wrapper_evidence_source.read_text().splitlines():
        if line.strip():
            entry = json.loads(line)
            if entry['confidence'] not in ['confirmed', 'inferred', 'unresolved']:
                entry['sourceConfidenceLabel'] = entry['confidence']
                entry['confidence'] = 'confirmed'
            if entry['id'] in existing_evidence_indices:
                index = existing_evidence_indices[entry['id']]
                original = evidence[index]
                for key in ['id', 'baselineId', 'sourcePath', 'sourceHash', 'locator', 'claim', 'confidence']:
                    assert original.get(key) == entry.get(key), ('Conflicting reused evidence', entry['id'], key)
                assert 'spanSha256' not in original or original['spanSha256'] == entry['spanSha256']
                merged = dict(original)
                merged['spanSha256'] = entry['spanSha256']
                merged['sourceObservations'] = [
                    {'artifact': 'feature evidence', 'method': original['method'],
                     'verificationStatus': original['verificationStatus']},
                    {'artifact': 'request-wrapper-evidence.jsonl', 'method': entry['method'],
                     'verificationStatus': entry['verificationStatus'], 'claimScope': entry['claimScope'],
                     'locatorScope': entry['locatorScope']}]
                evidence[index] = merged
                reused_evidence.append({'id': entry['id'], 'identityFieldsMatched': True,
                                        'additionalSpanHashValidated': True,
                                        'metadataRetainedIn': 'sourceObservations'})
            else:
                evidence.append(entry)
prediction_source = workspace / '.analysis-local/protocol-work/experimental-prediction-usage.json'
prediction_usage = None
if prediction_source.exists():
    prediction_usage = json.loads(prediction_source.read_text())
    assert prediction_usage['baselineId'] == baseline['baselineId']
    publish_copy(prediction_source, out / 'experimental-prediction-usage.json')
    prediction_evidence_source = prediction_source.with_name('evidence.jsonl')
    assert hashlib.sha256(prediction_evidence_source.read_bytes()).hexdigest() == prediction_usage['evidenceFile']['sha256']
    publish_copy(prediction_evidence_source, out / 'experimental-prediction-evidence.jsonl')
    for line in prediction_evidence_source.read_text().splitlines():
        if line.strip():
            entry = json.loads(line)
            entry['claim'] = entry['claimScope'] + ': ' + entry['locatorScope']
            entry['method'] = 'narrow-frozen-ast-client-property-review'
            entry['confidence'] = 'confirmed'
            evidence.append(entry)
prediction_gate_source = workspace / '.analysis-local/protocol-work/prediction-version-gate.json'
prediction_gate = None
if prediction_gate_source.exists():
    prediction_gate = json.loads(prediction_gate_source.read_text())
    assert prediction_gate['baselineId'] == baseline['baselineId']
    assert prediction_gate['locatorVerification']['allSourceAndSpanHashesVerified']
    publish_copy(prediction_gate_source, out / 'prediction-version-gate.json')
    gate_evidence_source = prediction_gate_source.with_name('prediction-version-gate-evidence.jsonl')
    assert hashlib.sha256(gate_evidence_source.read_bytes()).hexdigest() == prediction_gate['evidenceFile']['sha256']
    publish_copy(gate_evidence_source, out / gate_evidence_source.name)
    for line in gate_evidence_source.read_text().splitlines():
        if line.strip():
            entry = json.loads(line)
            entry['claim'] = entry['claimScope'] + ': ' + entry['locatorScope']
            entry['method'] = 'narrow-frozen-ast-prediction-version-gate-review'
            entry['confidence'] = 'confirmed'
            evidence.append(entry)
    for supplemental in [prediction_usage, prediction_gate]:
        for entry in supplemental['inputs'].values():
            if isinstance(entry, dict) and {'path', 'sha256', 'bytes'} <= entry.keys():
                data = Path(entry['path']).read_bytes()
                assert len(data) == entry['bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256']
for source, destination in [(feature_work / 'route-guard-notes.json', 'route-guard-notes.json'),
                            (workspace / '.analysis-local/auth-work/project-path-controls.json', 'project-path-controls.json')]:
    if not source.exists():
        continue
    record = json.loads(source.read_text())
    assert record['baselineId'] == baseline['baselineId']
    if destination == 'route-guard-notes.json':
        for note in record.get('notes', []):
            note.pop('routeContractReferences', None)
        record['publicationNotes'] = ['Legacy snapshot routeContractReferences removed; current registrationReferences are in route-contracts.json.']
        (out / destination).write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    else:
        publish_copy(source, out / destination)
    if source.with_suffix('.md').exists():
        publish_copy(source.with_suffix('.md'), out / Path(destination).with_suffix('.md'))
    for entry in record['evidence']:
        evidence.append({'id': entry['id'], 'baselineId': baseline['baselineId'],
                         'claim': 'Complete static source span: ' + entry['label'],
                         'sourcePath': 'app.asar/' + entry['sourcePath'], 'sourceHash': entry['sourceHash'],
                         'locator': {'kind': 'byte-range', 'start': entry['byteRange']['start'],
                                     'endExclusive': entry['byteRange']['end']},
                         'spanSha256': entry['spanSha256'], 'method': 'complete-frozen-ast-source-review',
                         'confidence': 'confirmed', 'verificationStatus': 'static-span-confirmed; runtime-and-mode-unverified'})
shell_source = workspace / '.analysis-local/auth-work/shell-env-controls.json'
if shell_source.exists():
    shell_controls = json.loads(shell_source.read_text())
    publish_copy(shell_source, out / 'shell-env-controls.json')
    for entry in shell_controls['evidence']:
        evidence.append({'id': entry['id'], 'baselineId': baseline['baselineId'], 'claim': entry['claim'],
                         'sourcePath': 'app.asar/' + entry['sourcePath'], 'sourceHash': entry['sourceHash']['value'],
                         'locator': {'kind': 'byte-range', 'start': entry['range']['byteStart'],
                                     'endExclusive': entry['range']['byteEndExclusive']},
                         'method': 'complete-frozen-startup-condition-review', 'confidence': 'confirmed',
                         'verificationStatus': 'static-source-recorded; runtime-and-credential-origin-unresolved'})
static_supplements = {}
supplement_specs = [
    ('.analysis-local/embedded-dependency-work', 'embedded-dependency-contracts.json', 'evidence.jsonl',
     {'summary.md': 'embedded-dependency-summary.md', 'validation.json': 'embedded-dependency-validation.json'}),
    ('.analysis-local/entry-work', 'menu-command-contracts.json', 'menu-command-evidence.jsonl',
     {name: name for name in ['menu-command-summary.json', 'menu-command-summary.md', 'menu-command-validation.json',
                             'renderer-command-notes.json', 'renderer-command-notes.md', 'renderer-command-bridge-helper.json']}),
    ('.analysis-local/embedded-dependency-work-v2', 'merged-candidate-contracts.json', 'evidence.jsonl',
     {'final-summary.md': 'embedded-dependency-continuation-summary.md',
      'investigation-actions.json': 'embedded-dependency-investigation-actions.json',
      'validation.json': 'embedded-dependency-continuation-validation.json',
      'embedded-dependency-contracts.json': 'embedded-dependency-continuation-initial.json',
      'statsig-recheck.json': 'embedded-statsig-recheck.json',
      'statsig-recheck-evidence.jsonl': 'embedded-statsig-recheck-evidence.jsonl'}),
    ('.analysis-local/runtime-api-work', 'runtime-api-contracts.json', 'evidence.jsonl',
     {'summary.md': 'runtime-api-summary.md', 'validation.json': 'runtime-api-validation.json'}),
    ('.analysis-local/mode-boundary-work', 'chatgpt-candidate-module-contracts.json', 'evidence.jsonl',
     {'summary.md': 'chatgpt-mode-boundary-summary.md',
      'validation.json': 'chatgpt-mode-boundary-validation.json',
      'frozen-manifest.json': 'chatgpt-mode-boundary-manifest.json',
      'ast-summary.json': 'chatgpt-mode-boundary-ast-summary.json',
      'project-review.json': 'chatgpt-project-review.json'}),
]
for directory, contract_name, evidence_name, additional in supplement_specs:
    directory = workspace / directory
    contract = json.loads((directory / contract_name).read_text())
    assert contract['baselineId'] == baseline['baselineId']
    if contract_name == 'chatgpt-candidate-module-contracts.json':
        mode_manifest = json.loads((directory / 'frozen-manifest.json').read_text())
        assert mode_manifest['baselineId'] == baseline['baselineId']
        for entry in mode_manifest['files']:
            frozen_path = Path(entry['path'])
            if not frozen_path.is_absolute():
                frozen_path = workspace / frozen_path
            data = frozen_path.read_bytes()
            assert len(data) == entry['bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256'], entry['path']
        mode_validation = json.loads((directory / 'validation.json').read_text())
        assert mode_validation['core']['errorCount'] == 0 and not mode_validation['core']['errors']
        assert mode_validation['scope']['mainJsonSha256'] == hashlib.sha256((directory / contract_name).read_bytes()).hexdigest()
        assert mode_validation['scope']['mainEvidenceSha256'] == hashlib.sha256((directory / evidence_name).read_bytes()).hexdigest()
        assert contract['summary']['unknownModuleMode'] == 9 and contract['summary']['confirmedModeExclusions'] == 0
    static_supplements[contract_name] = contract
    publish_copy(directory / contract_name, out / contract_name)
    published_evidence_name = contract_name.removesuffix('-contracts.json') + '-evidence.jsonl'
    publish_copy(directory / evidence_name, out / published_evidence_name)
    for line in (directory / evidence_name).read_text().splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if contract_name == 'chatgpt-candidate-module-contracts.json' and 'confidence' not in entry:
            assert entry['id'].startswith('CGP-E') and entry['id'] == entry['evidenceId']
            assert entry['range']['kind'] == 'byte-range' and 'spanHash' in entry
            entry = {**entry, 'claim': 'Frozen source range: ' + entry['kind'] + ' (' + entry['nodeType'] + ')',
                     'locator': entry['range'], 'method': 'scoped-complete-module-ast-range-review',
                     'confidence': 'confirmed', 'verificationStatus': 'source-range-confirmed; runtime-and-mode-unverified',
                     'sourceJournalSchema': 'CGP range/kind/nodeType; original byte-preserving journal retained'}
        if entry['confidence'] not in ['confirmed', 'inferred', 'unresolved']:
            assert entry['confidence'] in ['source-confirmed', 'source-confirmed-locator']
            entry['sourceConfidenceLabel'] = entry['confidence']
            entry['confidence'] = 'confirmed'
        evidence.append(entry)
    for source_name, destination_name in additional.items():
        publish_copy(directory / source_name, out / destination_name)
evidence.extend(json.loads(line) for line in (out / 'embedded-statsig-recheck-evidence.jsonl').read_text().splitlines() if line.strip())
for name in ['renderer-command-notes.json', 'renderer-command-bridge-helper.json']:
    renderer_review = json.loads((out / name).read_text())
    assert renderer_review['baselineId'] == baseline['baselineId']
    for entry in renderer_review['evidence']:
        source_hash = entry['sourceSha256']
        if 'sourceHash' in entry:
            assert entry['sourceHash'] == source_hash
        evidence.append({'id': entry['id'], 'baselineId': baseline['baselineId'],
                         'claim': 'Frozen source range recorded by bounded renderer command review: ' + entry['label'],
                         'sourcePath': 'app.asar/' + entry['sourcePath'], 'sourceHash': source_hash,
                         'locator': {'kind': 'byte-range', 'start': entry['byteRange']['start'],
                                     'endExclusive': entry['byteRange']['end']},
                         'spanSha256': entry['spanSha256'], 'method': 'bounded-renderer-command-source-review',
                         'confidence': 'confirmed',
                         'verificationStatus': 'source-range-confirmed; original-outer-binding-runtime-and-mode-unverified',
                         'originalScopeVerification': entry.get('originalScopeVerification', 'See bounded review scope limitations'),
                         'producerArtifact': name})
runtime_decision_directory = workspace / '.analysis-local/runtime-decision-work'
runtime_options = json.loads((runtime_decision_directory / 'runtime-adapter-options.json').read_text())
assert runtime_options['baselineId'] == baseline['baselineId']
assert runtime_options['validation']['status'] == 'passed' and not runtime_options['validation']['errors']
decision_runner = workspace / runtime_options['runnerSource']['path']
assert hashlib.sha256(decision_runner.read_bytes()).hexdigest() == runtime_options['runnerSource']['sha256']
decision_archive = out / 'raw/runtime-adapter-options'
decision_archive.mkdir(parents=True, exist_ok=True)
publish_copy(decision_runner, decision_archive / decision_runner.name)
publish_copy(runtime_decision_directory / 'runtime-adapter-options.json', out / 'runtime-adapter-options.json')
publish_copy(runtime_decision_directory / 'summary.md', out / 'runtime-adapter-options.md')
static_supplements['runtime-adapter-options.json'] = runtime_options
preserved_inputs = {}
mode_contract = static_supplements['chatgpt-candidate-module-contracts.json']
mode_archive = out / 'raw/chatgpt-mode-boundary'
mode_archive.mkdir(parents=True, exist_ok=True)
mode_archived_inputs = []
for index, entry in enumerate(mode_contract['sourceArtifacts']):
    source = workspace / entry['path']
    data = source.read_bytes()
    assert len(data) == entry['bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256'], entry['path']
    destination = mode_archive / 'inputs' / (str(index).zfill(2) + '-' + entry['key'] + source.suffix)
    destination.parent.mkdir(parents=True, exist_ok=True)
    publish_copy(source, destination)
    preserved_inputs[entry['sha256']] = destination
    mode_archived_inputs.append({**entry, 'archivedPath': str(destination.relative_to(workspace))})
mode_archived_scripts = []
for entry in mode_manifest['files']:
    source = Path(entry['path'])
    if not source.is_absolute():
        source = workspace / source
    if source.suffix in ['.py', '.mjs']:
        destination = mode_archive / 'scripts' / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        publish_copy(source, destination)
        mode_archived_scripts.append({**entry, 'archivedPath': str(destination.relative_to(workspace))})
mode_archived_catalogs = []
mode_imported_external_evidence = []
available_ids = {entry['id'] for entry in evidence}
external_ids = {entry['evidenceId'] for entry in mode_validation['external']['spanChecks']}
missing_external_ids = external_ids - available_ids
catalog_descriptors = {entry['path']: entry for entry in mode_validation['catalogs']}
catalog_sources = {}
for reference in mode_validation['evidenceReferenceChecks']:
    evidence_id = reference['evidenceId']
    if evidence_id not in missing_external_ids:
        continue
    path = reference['catalogPath']
    if path not in catalog_sources:
        descriptor = catalog_descriptors[path]
        assert descriptor['pinLevel'] == 'matched-explicit-pin'
        source = workspace / path
        data = source.read_bytes()
        assert hashlib.sha256(data).hexdigest() == descriptor['sha256']
        records = [json.loads(line) for line in data.decode().splitlines() if line.strip()]
        assert len(records) == descriptor['records']
        catalog_sources[path] = records
        destination = mode_archive / 'catalogs' / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        publish_copy(source, destination)
        mode_archived_catalogs.append({'path': path, 'archivedPath': str(destination.relative_to(workspace)),
            'sha256': descriptor['sha256'], 'bytes': len(data), 'pinLevel': descriptor['pinLevel'],
            'pinOrigin': descriptor['pinOrigin'], 'pinPointer': descriptor['pinPointer']})
    record = catalog_sources[path][reference['catalogLocator'] - 1]
    assert record['id'] == evidence_id
    assert 'spanSha256' in record and record['locator']['kind'] == 'byte-range'
    evidence.append({**record, 'claim': record['claimScope'] + ': ' + record['locatorScope'],
        'method': 'reused-frozen-ast-export-locator', 'confidence': 'confirmed',
        'verificationStatus': 'source-range-confirmed; external-business-runtime-and-mode-unverified'})
    mode_imported_external_evidence.append({'id': evidence_id, 'catalogPath': path,
        'catalogLine': reference['catalogLocator'], 'scope': 'Existing source locator only; no new AST parse or business inference.'})
    missing_external_ids.remove(evidence_id)
assert not missing_external_ids, ('Missing mode external source evidence', missing_external_ids)
mode_published_artifacts = []
mode_names = {'chatgpt-candidate-module-contracts.json': 'chatgpt-candidate-module-contracts.json',
                   'evidence.jsonl': 'chatgpt-candidate-module-evidence.jsonl',
                   'summary.md': 'chatgpt-mode-boundary-summary.md',
                   'validation.json': 'chatgpt-mode-boundary-validation.json',
                   'frozen-manifest.json': 'chatgpt-mode-boundary-manifest.json',
                   'ast-summary.json': 'chatgpt-mode-boundary-ast-summary.json',
                   'project-review.json': 'chatgpt-project-review.json'}
mode_directory = workspace / '.analysis-local/mode-boundary-work'
for source_name, published_name in mode_names.items():
    source = mode_directory / source_name
    data = source.read_bytes()
    assert (out / published_name).read_bytes() == data
    mode_published_artifacts.append({'path': str(source.relative_to(workspace)),
        'publishedPath': str((out / published_name).relative_to(workspace)),
        'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
(out / 'chatgpt-mode-boundary-input-provenance.json').write_text(json.dumps({
    'baselineId': baseline['baselineId'], 'sourceArtifacts': mode_archived_inputs,
    'scripts': mode_archived_scripts, 'publishedArtifacts': mode_published_artifacts,
    'referencedExternalCatalogs': mode_archived_catalogs,
    'importedExternalEvidence': mode_imported_external_evidence,
    'allArchivedHashesVerified': True, 'allPublishedBytesMatched': True,
    'indirectInputStatus': mode_validation['external']['historicalInputHashChecks'],
    'scope': 'Byte-preserving direct inputs and frozen producer scripts; historical indirect pin failures remain unresolved.'
}, ensure_ascii=False, indent=2) + '\n')
publication_manifests = list((out / 'raw/dependency-publication').glob('*/run.json')) + list((out / 'raw/publication').glob('*/run.json'))
publication_manifests += list((out / 'raw/dependency-publication').glob('*/before-artifacts.json'))
publication_manifests += list((out / 'raw/publication').glob('*/before-artifacts.json'))
for manifest in sorted(publication_manifests):
    publication = json.loads(manifest.read_text())
    for entry in publication.get('previousArtifactSnapshots', {}).values():
        snapshot = out / entry['path']
        assert hashlib.sha256(snapshot.read_bytes()).hexdigest() == entry['sha256']
        preserved_inputs[entry['sha256']] = snapshot
input_bindings = []
directed_external_evidence_sources = {}
directed_specs = [
    ('runtime-fuse', '.analysis-local/runtime-fuse-work', 'runtime-fuse-observation.json',
     {'evidence.jsonl': 'runtime-fuse-evidence.jsonl', 'summary.md': 'runtime-fuse-summary.md',
      'validation.json': 'runtime-fuse-validation.json', 'frozen-manifest.json': 'runtime-fuse-manifest.json'}),
    ('runtime-native-accessors', '.analysis-local/runtime-native-accessors-work', 'runtime-native-accessors.json',
     {'evidence.jsonl': 'runtime-native-accessors-evidence.jsonl', 'summary.md': 'runtime-native-accessors-summary.md',
      'validation.json': 'runtime-native-accessors-validation.json', 'frozen-manifest.json': 'runtime-native-accessors-manifest.json'}),
    ('request-facade', '.analysis-local/mode-facade-work', 'request-facade-contract.json',
     {'evidence.jsonl': 'request-facade-evidence.jsonl', 'summary.md': 'request-facade-summary.md',
      'referenced-existing-evidence.jsonl': 'request-facade-reused-evidence.jsonl',
      'validation.json': 'request-facade-validation.json', 'frozen-manifest.json': 'request-facade-manifest.json'}),
    ('project-local-folder-predicate', '.analysis-local/project-upstream-work', 'review.json',
     {'review.json': 'project-local-folder-predicate.json', 'evidence.jsonl': 'project-local-folder-predicate-evidence.jsonl',
      'summary.md': 'project-local-folder-predicate-summary.md', 'validation.json': 'project-local-folder-predicate-validation.json',
      'frozen-manifest.json': 'project-local-folder-predicate-manifest.json'}),
    ('runtime-node-version', '.analysis-local/runtime-node-version-work', 'runtime-node-version.json',
     {'evidence.jsonl': 'runtime-node-version-evidence.jsonl', 'summary.md': 'runtime-node-version-summary.md',
      'validation.json': 'runtime-node-version-validation.json', 'frozen-manifest.json': 'runtime-node-version-manifest.json'}),
    ('project-permission', '.analysis-local/project-permission-work', 'project-permission.json',
     {'evidence.jsonl': 'project-permission-evidence.jsonl', 'summary.md': 'project-permission-summary.md',
      'validation.json': 'project-permission-validation.json', 'frozen-manifest.json': 'project-permission-manifest.json'}),
    ('http-service-origin', '.analysis-local/http-service-origin-work', 'http-service-origin.json',
     {'evidence.jsonl': 'http-service-origin-evidence.jsonl', 'summary.md': 'http-service-origin-summary.md',
      'referenced-existing-evidence.jsonl': 'http-service-origin-reused-evidence.jsonl',
      'validation.json': 'http-service-origin-validation.json', 'frozen-manifest.json': 'http-service-origin-manifest.json'}),
    ('preload-app-host', '.analysis-local/preload-app-host-work', 'preload-app-host.json',
     {'evidence.jsonl': 'preload-app-host-evidence.jsonl', 'summary.md': 'preload-app-host-summary.md',
      'validation.json': 'preload-app-host-validation.json', 'frozen-manifest.json': 'preload-app-host-manifest.json'}),
    ('host-http-service', '.analysis-local/host-http-service-work', 'host-http-service.json',
     {'evidence.jsonl': 'host-http-service-evidence.jsonl', 'summary.md': 'host-http-service-summary.md',
      'referenced-existing-evidence.jsonl': 'host-http-service-reused-evidence.jsonl',
      'validation.json': 'host-http-service-validation.json', 'frozen-manifest.json': 'host-http-service-manifest.json'}),
    ('app-host-context', '.analysis-local/app-host-context-work', 'app-host-context.json',
     {'evidence.jsonl': 'app-host-context-evidence.jsonl', 'summary.md': 'app-host-context-summary.md',
      'referenced-existing-evidence.jsonl': 'app-host-context-reused-evidence.jsonl',
      'validation.json': 'app-host-context-validation.json', 'frozen-manifest.json': 'app-host-context-manifest.json'}),
    ('application-network', '.analysis-local/application-network-work', 'application-network.json',
     {'evidence.jsonl': 'application-network-evidence.jsonl', 'summary.md': 'application-network-summary.md',
      'referenced-host-evidence.jsonl': 'application-network-reused-evidence.jsonl',
      'validation.json': 'application-network-validation.json', 'frozen-manifest.json': 'application-network-manifest.json'}),
    ('project-feature-condition', '.analysis-local/project-feature-condition-work', 'project-feature-condition.json',
     {'evidence.jsonl': 'project-feature-condition-evidence.jsonl', 'summary.md': 'project-feature-condition-summary.md',
      'referenced-existing-evidence.jsonl': 'project-feature-condition-reused-evidence.jsonl',
      'validation.json': 'project-feature-condition-validation.json', 'frozen-manifest.json': 'project-feature-condition-manifest.json'}),
    ('runtime-distribution', '.analysis-local/runtime-distribution-work', 'main.json',
     {'main.json': 'runtime-distribution.json', 'evidence.jsonl': 'runtime-distribution-evidence.jsonl',
      'summary.md': 'runtime-distribution-summary.md', 'validation.json': 'runtime-distribution-validation.json',
      'freeze-manifest.json': 'runtime-distribution-manifest.json'}),
    ('app-host-maintenance', '.analysis-local/app-host-maintenance-work', 'app-host-maintenance.json',
     {'evidence.jsonl': 'app-host-maintenance-evidence.jsonl', 'summary.md': 'app-host-maintenance-summary.md',
      'validation.json': 'app-host-maintenance-validation.json', 'frozen-manifest.json': 'app-host-maintenance-manifest.json'}),
    ('app-server-version-origin', '.analysis-local/app-server-version-origin-work', 'version-origin.json',
     {'version-origin.json': 'app-server-version-origin.json', 'evidence.jsonl': 'app-server-version-origin-evidence.jsonl',
      'summary.md': 'app-server-version-origin-raw-summary.md', 'validation.json': 'app-server-version-origin-validation.json',
      'manifest.json': 'app-server-version-origin-manifest.json'}),
]
directed_provenance = []
for key, directory_name, contract_name, aliases in directed_specs:
    directory = workspace / directory_name
    reused_journal_names = [name for name in ['referenced-existing-evidence.jsonl', 'referenced-host-evidence.jsonl']
                            if name in aliases]
    assert len(reused_journal_names) <= 1, (key, 'Ambiguous reused journal')
    reused_journal_name = reused_journal_names[0] if reused_journal_names else None
    manifest_name = ('freeze-manifest.json' if key == 'runtime-distribution' else
                     'manifest.json' if key == 'app-server-version-origin' else 'frozen-manifest.json')
    manifest_path = directory / manifest_name
    manifest = json.loads(manifest_path.read_text())
    contract = json.loads((directory / contract_name).read_text())
    validation_record = json.loads((directory / 'validation.json').read_text())
    assert manifest['baselineId'] == contract['baselineId'] == validation_record['baselineId'] == baseline['baselineId']
    assert validation_record['status'].startswith('passed'), (key, validation_record['status'])
    assert not validation_record['errors'], (key, validation_record['errors'])
    validation_inputs = {}
    if key == 'runtime-distribution':
        assert set(validation_record['inputs']) == {'main.json', 'evidence.jsonl', 'summary.md'}
        validation_inputs = {name: {**pin, 'path': str((directory / name).relative_to(workspace))}
                             for name, pin in validation_record['inputs'].items()}
    elif key == 'app-server-version-origin':
        products = {entry['path']: entry for entry in validation_record['finalProducts']}
        assert len(products) == len(validation_record['finalProducts']) == 3
        validation_inputs = {name: {**products[str(directory / name)],
                                   'path': str((directory / name).relative_to(workspace))}
                             for name in [contract_name, 'evidence.jsonl', 'summary.md']}
    elif key == 'runtime-node-version':
        products = {entry['path']: entry for entry in validation_record['snapshots']['products']}
        validation_inputs = {name: products[str((directory / name).relative_to(workspace))]
                             for name in [contract_name, 'evidence.jsonl', 'summary.md']}
    elif key == 'project-permission':
        validation_inputs = {contract_name: validation_record['artifacts']['review'],
                             'evidence.jsonl': validation_record['artifacts']['evidence']}
        assert all(entry['independentPinMatched'] for entry in validation_inputs.values())
    elif key == 'http-service-origin':
        scope = validation_record['scope']
        validation_inputs = {name: {'path': scope[field], 'sha256': scope[field + 'Sha256']}
                             for name, field in [(contract_name, 'mainJson'), ('evidence.jsonl', 'journal'),
                                                 ('referenced-existing-evidence.jsonl', 'reusedJournal')]}
    elif key in ['preload-app-host', 'host-http-service', 'app-host-context', 'application-network', 'project-feature-condition', 'app-host-maintenance']:
        products = {entry['path']: entry for entry in validation_record['finalProducts']}
        assert len(products) == len(validation_record['finalProducts']), (key, 'Duplicate validation product pin')
        validated_names = [contract_name, 'evidence.jsonl', 'summary.md']
        if reused_journal_name is not None:
            validated_names.append(reused_journal_name)
        validation_inputs = {name: products[str((directory / name).relative_to(workspace))]
                             for name in validated_names}
    validation_bindings = []
    for name, pin in validation_inputs.items():
        source = directory / name
        data = source.read_bytes()
        assert pin['path'] == str(source.relative_to(workspace)), (key, name, 'Validation path differs')
        assert hashlib.sha256(data).hexdigest() == pin['sha256'], (key, name, 'Validation input changed')
        if 'bytes' in pin:
            assert len(data) == pin['bytes'], (key, name, 'Validation input size differs')
        if 'expectedSha256' in pin:
            assert pin['sha256'] == pin['expectedSha256'], (key, name, 'Independent expected pin differs')
        validation_bindings.append({'path': pin['path'], 'bytes': len(data), 'sha256': pin['sha256']})
    auxiliary_frozen_inputs = []
    pinned_contract_inputs = {entry['path']: entry for category in ['sourceInputs', 'inputs', 'scripts', 'sourceArtifacts']
                             for entry in contract.get(category, [])}
    for entry in manifest.get('auxiliaryFrozenInputs', []):
        source = Path(entry['path'])
        if not source.is_absolute():
            source = workspace / source
        data = source.read_bytes()
        assert len(data) == entry['bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256'], entry['path']
        assert source.stat().st_mode & 0o222 == 0, ('Frozen auxiliary input is writable', entry['path'])
        pin = pinned_contract_inputs[entry['path']]
        assert pin['bytes'] == entry['bytes'] and pin['sha256'] == entry['sha256'], ('Auxiliary input pin differs', entry['path'])
        auxiliary_frozen_inputs.append(entry)
    archive = out / 'raw/directed-supplements' / key
    frozen_files = []
    frozen_entries = (manifest['finalProducts'] + manifest['supportingArtifacts']
                      if key == 'runtime-distribution' else manifest['files'])
    for entry in frozen_entries:
        source = Path(entry['path'])
        if not source.is_absolute():
            source = workspace / source
        data = source.read_bytes()
        assert len(data) == entry['bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256'], entry['path']
        assert source.stat().st_mode & 0o222 == 0, ('Frozen supplement is writable', entry['path'])
        destination = archive / 'frozen' / source.relative_to(workspace)
        destination.parent.mkdir(parents=True, exist_ok=True)
        publish_copy(source, destination)
        frozen_files.append({**entry, 'archivedPath': str(destination.relative_to(workspace))})
        preserved_inputs[entry['sha256']] = destination
    if key == 'runtime-distribution':
        for entry in auxiliary_frozen_inputs:
            source = workspace / entry['path']
            auxiliary_destination = archive / 'auxiliary-frozen' / source.relative_to(workspace)
            auxiliary_destination.parent.mkdir(parents=True, exist_ok=True)
            publish_copy(source, auxiliary_destination)
            preserved_inputs[entry['sha256']] = auxiliary_destination
            entry['archivedPath'] = str(auxiliary_destination.relative_to(workspace))
    destination = archive / 'frozen-manifest.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    publish_copy(manifest_path, destination)
    names = {contract_name: contract_name, **aliases}
    frozen_paths = {str((workspace / entry['path']).relative_to(workspace)) for entry in frozen_entries}
    assert manifest_path.stat().st_mode & 0o222 == 0, ('Frozen manifest is writable', key)
    for source_name in names:
        if source_name != manifest_name:
            assert str((directory / source_name).relative_to(workspace)) in frozen_paths, ('Unfrozen public alias', key, source_name)
    published_files = []
    for source_name, published_name in names.items():
        source = directory / source_name
        publish_copy(source, out / published_name)
        data = source.read_bytes()
        assert (out / published_name).read_bytes() == data
        published_files.append({'path': str(source.relative_to(workspace)),
            'publishedPath': str((out / published_name).relative_to(workspace)),
            'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    derived_documents = []
    if key == 'app-server-version-origin':
        # Preserve the raw summary, and adapt only its three relative links for
        # readers of the public analysis directory.
        source = directory / 'summary.md'
        member_path = archive / 'frozen' / (directory / 'selected-member-text.json').relative_to(workspace)
        replacements = {
            '(version-origin.json)': '(app-server-version-origin.json)',
            '(selected-member-text.json)': '(' + str(member_path.relative_to(out)) + ')',
            '(validation.json)': '(app-server-version-origin-validation.json)',
        }
        adapted = source.read_text()
        for original, replacement in replacements.items():
            assert adapted.count(original) == 1, ('Unexpected summary link scope', original)
            adapted = adapted.replace(original, replacement)
        generated = archive / 'summary-with-public-links.md'
        generated.write_text(adapted)
        destination = out / 'app-server-version-origin-summary.md'
        publish_copy(generated, destination)
        derived_documents.append({'path': str(destination.relative_to(workspace)),
            'bytes': destination.stat().st_size, 'sha256': file_sha256(destination),
            'producerPath': str(source.relative_to(workspace)), 'producerSha256': file_sha256(source),
            'linkReplacements': replacements,
            'scope': 'Only three relative Markdown link targets changed; raw frozen summary is separately preserved.'})
    archived_inputs, frozen_source_inputs, local_tool_runtime_inputs = [], [], []
    input_categories = ['sourceInputs', 'inputs', 'scripts', 'sourceArtifacts']
    if key == 'app-server-version-origin':
        # This producer repeats its four target pins in sourceInputs and its
        # two tool pins in toolRuntime; inputs is the complete 22-pin list.
        input_categories = ['inputs']
    if key == 'app-host-maintenance':
        input_categories.append('sourceProducerPins')
    for category in input_categories:
        for entry in contract.get(category, []):
            assert {'path', 'sha256', 'bytes'} <= entry.keys(), (key, category, entry)
            source = workspace / entry['path']
            if key == 'app-server-version-origin' and entry['kind'] == 'tool-runtime':
                assert source in [Path('/private/tmp/ccodex-rea-tooling/install/node_modules/@babel/parser/lib/index.js'),
                                  Path('/private/tmp/ccodex-rea-tooling/install/node_modules/@babel/parser/package.json')]
                assert entry in contract['toolRuntime'] and source.stat().st_size == entry['bytes']
                assert file_sha256(source) == entry['sha256']
                local_tool_runtime_inputs.append({**entry, 'scope': 'Analysis tool pin only; third-party implementation is not copied into publication.'})
                continue
            if key == 'runtime-distribution' and entry['kind'] in ['frozen-asar-byte-identity', 'frozen-target-metadata-or-native-provenance']:
                assert source.is_relative_to(Path(baseline['snapshotApplication'])) or (
                    entry['kind'] == 'frozen-target-metadata-or-native-provenance'
                    and source == Path(baseline['extractedDirectory']) / 'package.json'
                ), ('Unexpected frozen runtime source', source)
                assert source.stat().st_size == entry['bytes']
                source_digest = hashlib.sha256()
                with source.open('rb') as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b''):
                        source_digest.update(block)
                assert source_digest.hexdigest() == entry['sha256'], source
                frozen_source_inputs.append({**entry, 'scope': 'Original frozen metadata/native/archive source retained locally; implementation is not copied into publication.'})
                continue
            resolved = preserved_inputs.get(entry['sha256'], source)
            data = resolved.read_bytes()
            assert len(data) == entry['bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256'], entry['path']
            if 'sourcePath' in entry:
                frozen_source_inputs.append({**entry, 'scope': 'Original frozen source retained locally; implementation is not copied into publication.'})
                continue
            if resolved == source:
                assert source.suffix in ['.json', '.jsonl', '.md', '.py', '.cjs', '.mjs'], ('Undeclared implementation input', entry['path'])
                resolved = archive / 'inputs' / (entry['sha256'][:12] + '-' + source.name)
                resolved.parent.mkdir(parents=True, exist_ok=True)
                publish_copy(source, resolved)
                preserved_inputs[entry['sha256']] = resolved
            archived_inputs.append({**entry, 'category': category, 'archivedPath': str(resolved.relative_to(workspace))})
    available = {entry['id']: entry for entry in evidence}
    imported_ids, reused_ids = [], []
    journals = [directory / 'evidence.jsonl']
    if reused_journal_name is not None:
        journals.append(directory / reused_journal_name)
        subset_bytes = journals[-1].read_bytes()
        subset_records = [json.loads(line) for line in subset_bytes.splitlines() if line.strip()]
        def directed_record_id(entry):
            if 'id' in entry:
                return entry['id']
            assert key == 'project-feature-condition' and entry['evidenceId'].startswith('CGP-E'), (key, 'Unexpected reused record schema')
            return entry['evidenceId']
        subset = {directed_record_id(entry): entry for entry in subset_records}
        assert len(subset) == len(subset_records) == len(contract['existingEvidenceReferences']), ('Duplicate or missing reused source journal record', key)
        original_journals = {}
        original_journal_hashes = {}
        expected_subset_bytes = []
        for reference in contract['existingEvidenceReferences']:
            source = workspace / reference['path']
            journal_sha256 = reference.get('sha256')
            if journal_sha256 is None:
                assert key == 'application-network', (key, 'Missing original journal pin')
                journal_sha256 = reference['journalSha256']
            if reference['path'] not in original_journals:
                original_data = source.read_bytes()
                original_journal_hashes[reference['path']] = hashlib.sha256(original_data).hexdigest()
                original_journals[reference['path']] = original_data
            assert original_journal_hashes[reference['path']] == journal_sha256
            original_data = original_journals[reference['path']]
            span = reference['recordByteRange']
            raw_record = original_data[span['start']:span['endExclusive']]
            assert hashlib.sha256(raw_record).hexdigest() == reference['recordSha256']
            assert original_data[:span['start']].count(b'\n') + 1 == reference['line']
            expected_subset_bytes.append(raw_record + b'\n')
            original_record = json.loads(raw_record)
            assert directed_record_id(original_record) == reference['id'] and original_record == subset[reference['id']], ('Referenced source journal record changed', reference['id'])
        assert set(subset) == {entry['id'] for entry in contract['existingEvidenceReferences']}
        assert subset_bytes == b''.join(expected_subset_bytes), ('Reused source journal subset bytes changed', key)
    for journal in journals:
        for line in journal.read_text().splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            if key == 'runtime-distribution':
                assert journal.name == 'evidence.jsonl' and entry['id'].startswith('RUNTIME-DISTRIBUTION-')
                pin = next(item for item in contract['inputs'] if item['path'] == entry['frozenPath'])
                assert pin['sha256'] == entry['sourceHash'] and pin['bytes'] == entry['sourceBytes']
                original_locator = entry['locator']
                assert original_locator['kind'] in ['whole-original-file', 'native-whole-file-hash', 'original-byte-range',
                    'provider-capture-byte-range', 'http-response-body-original-range', 'http-response-body-original-item-range']
                entry = {**entry, 'producerLocator': original_locator,
                    'locator': {'kind': 'byte-range', 'start': original_locator['byteStart'],
                                'endExclusive': original_locator['byteEndExclusive']},
                    'spanSha256': original_locator['rangeSha256']}
                source_path = preserved_inputs.get(entry['sourceHash'], Path(entry['frozenPath']))
                directed_external_evidence_sources[entry['id']] = {'path': source_path, 'pin': pin}
            if 'id' not in entry:
                assert key == 'project-feature-condition' and journal.name == reused_journal_name
                assert entry['evidenceId'].startswith('CGP-E') and entry['range']['kind'] == 'byte-range' and 'spanHash' in entry
                assert 'confidence' not in entry
                entry = {**entry, 'id': entry['evidenceId'],
                    'claim': 'Frozen source range: ' + entry['kind'] + ' (' + entry['nodeType'] + ')',
                    'locator': entry['range'], 'method': 'scoped-complete-module-ast-range-review',
                    'confidence': 'confirmed', 'verificationStatus': 'source-range-confirmed; runtime-and-mode-unverified',
                    'sourceJournalSchema': 'CGP range/kind/nodeType; original byte-preserving journal retained'}
            if 'confidence' not in entry:
                if key == 'app-server-version-origin':
                    assert entry['id'].startswith('APP-SERVER-VERSION-ORIGIN-AST-')
                    assert entry['locator']['kind'] == 'byte-range' and entry['claim'] and entry['verificationStatus']
                    entry = {**entry, 'method': 'scoped-complete-ast-source-locator-review', 'confidence': 'confirmed',
                        'globalConfidenceScope': 'Original AST source coordinates and span only; actual connection instance, version value and lifecycle remain unverified.'}
                else:
                    assert entry['id'].startswith('REQUEST-WRAPPER-AST-') and 'claimScope' in entry
                    entry = {**entry, 'claim': entry['claimScope'] + ': ' + entry['locatorScope'],
                        'method': 'reused-frozen-ast-source-locator', 'confidence': 'confirmed',
                        'verificationStatus': 'source-range-confirmed; runtime-and-mode-unverified'}
            if entry['confidence'] == 'high-for-coordinate-identity':
                assert key == 'project-local-folder-predicate'
                entry = {**entry, 'sourceConfidenceLabel': entry['confidence'], 'confidence': 'confirmed',
                    'globalConfidenceScope': 'Source coordinates and span only; producer journal retains its original label.'}
            if key == 'project-permission' and entry['confidence'] == 'high':
                assert entry['confidenceScope'] == 'coordinate-identity-only', entry['id']
                entry = {**entry, 'sourceConfidenceLabel': entry['confidence'], 'confidence': 'confirmed',
                    'globalConfidenceScope': 'Source coordinate identity only; original-module binding, runtime and mode remain unverified.'}
            if key in ['app-host-context', 'app-host-maintenance'] and entry['confidence'] == 'confirmed-static-local-source':
                assert entry['verificationStatus'] == 'static-source-confirmed; outer-bindings-registry-runtime-mode-unverified'
                entry = {**entry, 'sourceConfidenceLabel': entry['confidence'], 'confidence': 'confirmed',
                    'globalConfidenceScope': entry['claimScope']}
            assert entry['confidence'] in ['confirmed', 'inferred', 'unresolved'], (key, entry['id'], entry['confidence'])
            prior = available.get(entry['id'])
            if prior:
                for field in ['baselineId', 'sourcePath', 'sourceHash', 'locator']:
                    assert prior[field] == entry[field], ('Conflicting reused source evidence', key, entry['id'], field)
                assert prior.get('spanSha256', prior.get('spanHash')) == entry.get('spanSha256', entry.get('spanHash')), ('Conflicting reused span', entry['id'])
                reused_ids.append(entry['id'])
            else:
                evidence.append(entry)
                available[entry['id']] = entry
                imported_ids.append(entry['id'])
    if key == 'app-host-maintenance':
        assert not imported_ids and len(reused_ids) == contract['scope']['reusedOriginalEvidenceRecords'] == 71
    if key == 'app-server-version-origin':
        assert len(imported_ids) == contract['selection']['denominators']['newEvidence'] == 40 and not reused_ids
        assert len(local_tool_runtime_inputs) == 2 and len(frozen_source_inputs) == 4
    static_supplements[names[contract_name]] = contract
    directed_provenance.append({'key': key, 'manifestPath': str(manifest_path.relative_to(workspace)),
        'manifestSha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        'manifestArchivedPath': str((archive / 'frozen-manifest.json').relative_to(workspace)),
        'frozenFiles': frozen_files, 'publishedFiles': published_files,
        'derivedPublishedDocuments': derived_documents,
        'auxiliaryFrozenInputBindings': auxiliary_frozen_inputs,
        'validationInputBindings': validation_bindings,
        'archivedInputs': archived_inputs, 'locallyRetainedFrozenSourceInputs': frozen_source_inputs,
        'locallyRetainedToolRuntimeInputs': local_tool_runtime_inputs,
        'importedSourceEvidenceIds': imported_ids, 'reusedSourceEvidenceIds': reused_ids,
        'sourceEvidenceScope': 'Source identity and span only; retained runtime and mode limitations are in the producer material.'})
(out / 'directed-supplement-provenance.json').write_text(json.dumps({
    'baselineId': baseline['baselineId'], 'supplements': directed_provenance,
    'allFrozenHashesVerified': True, 'allPublishedBytesMatched': True,
    'scope': 'Frozen directed supplements and producer bytes; input bindings are separately preserved in supplement-input-provenance.json.'
}, ensure_ascii=False, indent=2) + '\n')
runtime_fuses = static_supplements['runtime-fuse-observation.json']
runtime_native = static_supplements['runtime-native-accessors.json']
request_facade = static_supplements['request-facade-contract.json']
project_predicate = static_supplements['project-local-folder-predicate.json']
runtime_node = static_supplements['runtime-node-version.json']
project_permission = static_supplements['project-permission.json']
http_origin = static_supplements['http-service-origin.json']
preload_app_host = static_supplements['preload-app-host.json']
host_http_service = static_supplements['host-http-service.json']
app_host_context = static_supplements['app-host-context.json']
application_network = static_supplements['application-network.json']
project_feature_condition = static_supplements['project-feature-condition.json']
runtime_distribution = static_supplements['runtime-distribution.json']
app_host_maintenance = static_supplements['app-host-maintenance.json']
app_server_version_origin = static_supplements['app-server-version-origin.json']
ipc['directedAppHostHttpSources'] = {
    'rendererOrigin': {'path': 'http-service-origin.json', 'scope': http_origin['scope']},
    'preloadBridge': {'path': 'preload-app-host.json', 'scope': preload_app_host['scope']},
    'hostService': {'path': 'host-http-service.json', 'scope': host_http_service['scope']},
    'contextAndTrustSources': {'path': 'app-host-context.json', 'scope': app_host_context['scope']},
    'applicationNetworkSources': {'path': 'application-network.json', 'scope': application_network['scope']},
    'verificationScope': 'Selected fixed-source nodes and declared pins; each producer retains its binding and dependency limitations.',
    'crossProcessDeliveryVerified': False,
    'actualHttpRequestVerified': False,
    'productModeOrExclusionVerified': False,
}
(out / 'ipc.json').write_text(json.dumps(ipc, ensure_ascii=False, indent=2) + '\n')
for name, contract in static_supplements.items():
    input_categories = ['sourceInputs', 'inputs', 'scripts', 'sourceArtifacts']
    if name == 'app-server-version-origin.json':
        input_categories = ['inputs']
    if name == 'app-host-maintenance.json':
        input_categories.append('sourceProducerPins')
    for category in input_categories:
        inputs = contract.get(category, [])
        if not isinstance(inputs, list):
            continue
        for entry in inputs:
            if not isinstance(entry, dict) or not {'path', 'sha256'} <= entry.keys():
                continue
            source = Path(entry['path'])
            if not source.is_absolute():
                source = workspace / source
            if entry['sha256'] in preserved_inputs:
                resolved = preserved_inputs[entry['sha256']]
            else:
                assert file_sha256(source) == entry['sha256'], (name, category, entry['path'], 'Input changed without preserved snapshot')
                resolved = source
            external_tool_pin = name == 'app-server-version-origin.json' and entry['kind'] == 'tool-runtime'
            resolved_path = str(resolved) if external_tool_pin else str(resolved.relative_to(workspace))
            input_bindings.append({'artifact': name, 'category': category, 'originalPath': entry['path'],
                                   'sha256': entry['sha256'], 'resolvedPath': resolved_path,
                                   'preservedSnapshotUsed': resolved != source})
(out / 'supplement-input-provenance.json').write_text(json.dumps({'baselineId': baseline['baselineId'],
    'bindings': input_bindings, 'allResolvedHashesVerified': True,
    'scope': 'Producer inputs/scripts only; historical mutable indexes resolve through byte-preserving snapshots.'}, ensure_ascii=False, indent=2) + '\n')
structure_source = workspace / '.analysis-local/structure-work/module-boundary-proposals.json'
structure_proposals = json.loads(structure_source.read_text())
assert structure_proposals['baselineId'] == baseline['baselineId']
for entry in structure_proposals['inputs'] + [structure_proposals['runnerSource']]:
    assert hashlib.sha256((workspace / entry['path']).read_bytes()).hexdigest() == entry['sha256']
for name in ['module-boundary-proposals.json', 'module-boundary-proposals.md']:
    publish_copy(structure_source.with_name(name), out / name)

ledger_directory = workspace / '.analysis-local/entry-ledger-work'
ledger_manifest = json.loads((ledger_directory / 'frozen-manifest.json').read_text())
assert ledger_manifest['baselineId'] == baseline['baselineId']
for entry in ledger_manifest['files']:
    data = (workspace / entry['path']).read_bytes()
    assert len(data) == entry['bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256'], entry['path']
entry_ledger = json.loads((ledger_directory / 'functional-entry-ledger.json').read_text())
assert entry_ledger['baselineId'] == baseline['baselineId']
for entry in entry_ledger['sourceArtifacts']:
    assert hashlib.sha256((workspace / entry['path']).read_bytes()).hexdigest() == entry['sha256'], entry['path']
ledger_validation = json.loads((ledger_directory / 'validation.json').read_text())
assert ledger_validation['status'] == 'passed'
assert ledger_validation['ledgerSha256'] == hashlib.sha256((ledger_directory / 'functional-entry-ledger.json').read_bytes()).hexdigest()
for source_name, destination_name in {
    'functional-entry-ledger.json': 'functional-entry-ledger.json',
    'summary.md': 'functional-entry-summary.md',
    'summary.json': 'functional-entry-summary.json',
    'validation.json': 'functional-entry-validation.json',
    'reviewed-links.json': 'functional-entry-reviewed-links.json',
    'frozen-manifest.json': 'functional-entry-manifest.json',
}.items():
    publish_copy(ledger_directory / source_name, out / destination_name)

criteria_audit = json.loads((out / 'criteria-audit.json').read_text())
criteria_provenance = json.loads((out / 'criteria-audit-provenance.json').read_text())
assert criteria_audit['baselineId'] == criteria_provenance['baselineId'] == baseline['baselineId']
assert criteria_provenance['allArchivedHashesVerified']
assert criteria_provenance['inputCount'] == len(criteria_audit['inputs'])
criteria_validation = json.loads((out / 'criteria-audit.validation.json').read_text())
assert criteria_validation['auditSha256'] == hashlib.sha256((out / 'criteria-audit.json').read_bytes()).hexdigest()

# This audit observes a fixed publication's analysis artifacts. Its journal is
# kept separate from target-source evidence and from the older criteria audit.
completion_directory = workspace / '.analysis-local/completion-audit-refresh-work/coverage-audit'
completion_manifest_path = completion_directory / 'frozen-manifest.json'
completion_manifest = json.loads(completion_manifest_path.read_text())
completion_audit = json.loads((completion_directory / 'current-requirement-matrix.json').read_text())
completion_validation = json.loads((completion_directory / 'validation.json').read_text())
completion_inputs = json.loads((completion_directory / 'inputs-manifest.json').read_text())
assert completion_manifest['baselineId'] == completion_audit['baselineId'] == completion_validation['baselineId'] == baseline['baselineId']
assert completion_manifest['publicationRun'] == completion_audit['publicationRun'] == completion_validation['publicationRun'] == '20261013T164818487650Z'
assert completion_validation['status'] == 'passed' and not completion_validation['errors']
assert completion_audit['publicationArtifactCount'] == 93
assert not completion_audit['fullAnalysisCompleted'] and not completion_audit['finalClientImplementationAcceptanceClaimed']
assert len(completion_audit['criteria']) == 9 and len(completion_audit['stages']) == 6
assert completion_manifest_path.stat().st_mode & 0o222 == 0
completion_archive = out / 'raw/completion-audit-refresh'
completion_frozen = []
completion_paths = {}
for entry in completion_manifest['files']:
    source = workspace / entry['path']
    assert source.is_relative_to(completion_directory), ('Audit input outside its frozen directory', source)
    assert source.stat().st_mode & 0o222 == 0
    assert source.stat().st_size == entry['bytes'] and file_sha256(source) == entry['sha256']
    assert str(source) not in completion_paths, ('Duplicate audit snapshot', source)
    destination = completion_archive / 'frozen' / source.relative_to(completion_directory)
    destination.parent.mkdir(parents=True, exist_ok=True)
    publish_copy(source, destination)
    completion_paths[str(source)] = {**entry, 'archivedPath': str(destination.relative_to(workspace))}
    completion_frozen.append(completion_paths[str(source)])
assert len(completion_frozen) == completion_manifest['counts']['files'] == 88
completion_product_bindings = []
for entry in completion_validation['finalProducts']:
    pin = completion_paths[entry['path']]
    assert pin['sha256'] == entry['sha256'] and pin['bytes'] == entry['bytes']
    completion_product_bindings.append(entry)
completion_input_bindings = []
for entry in completion_inputs['files']:
    pin = completion_paths[entry['snapshotPath']]
    assert pin['sha256'] == entry['sha256'] and pin['bytes'] == entry['bytes']
    completion_input_bindings.append({**entry, 'archivedPath': pin['archivedPath']})
assert len(completion_input_bindings) == 63
completion_rows = [json.loads(line) for line in (completion_directory / 'evidence.jsonl').read_text().splitlines() if line.strip()]
completion_ids = {row['id'] for row in completion_rows}
assert len(completion_ids) == len(completion_rows) == 44
for row in completion_rows:
    assert row['baselineId'] == baseline['baselineId'] and row['id'].startswith('COMPLETION-REFRESH-')
    pin = completion_paths[row['frozenPath']]
    assert pin['sha256'] == row['sourceHash'] and pin['bytes'] == row['sourceBytes']
    source = Path(row['frozenPath'])
    locator = row['locator']
    if 'jsonPointer' in locator:
        value = json.loads(source.read_text())
        pointer = locator['jsonPointer']
        for component in pointer.split('/')[1:] if pointer else []:
            component = component.replace('~1', '/').replace('~0', '~')
            value = value[int(component)] if isinstance(value, list) else value[component]
        assert value == row['value'], ('Audit JSON pointer changed', row['id'])
    elif 'lines' in locator:
        lines = source.read_text().splitlines()
        assert all(1 <= number <= len(lines) for number in locator['lines'])
        assert '\n'.join(lines[number - 1] for number in locator['lines']) == row['value']
    else:
        assert row['id'] == 'COMPLETION-REFRESH-0044' and set(locator) == {'derivedFromSources'}
        assert row['value'] == completion_audit['metrics']
        for name in locator['derivedFromSources']:
            assert str(completion_directory / 'inputs/analysis' / baseline['baselineId'] / name) in completion_paths
for entry in completion_audit['criteria'] + completion_audit['stages']:
    assert all(reference in completion_ids for reference in entry.get('evidenceRefs', entry.get('currentAuthority', [])))
completion_aliases = {
    'current-requirement-matrix.json': 'current-completion-audit.json',
    'summary.md': 'current-completion-audit.md',
    'evidence.jsonl': 'current-completion-audit-evidence.jsonl',
    'inputs-manifest.json': 'current-completion-audit-inputs.json',
    'validation.json': 'current-completion-audit-validation.json',
    'frozen-manifest.json': 'current-completion-audit-manifest.json',
}
completion_published = []
for source_name, destination_name in completion_aliases.items():
    source = completion_directory / source_name
    assert source_name == 'frozen-manifest.json' or str(source) in completion_paths
    publish_copy(source, out / destination_name)
    completion_published.append({'path': str(source.relative_to(workspace)),
        'publishedPath': str((out / destination_name).relative_to(workspace)),
        'bytes': source.stat().st_size, 'sha256': file_sha256(source)})
completion_archive.mkdir(parents=True, exist_ok=True)
publish_copy(completion_manifest_path, completion_archive / 'frozen-manifest.json')
completion_provenance = {
    'baselineId': baseline['baselineId'], 'auditedPublicationId': completion_audit['publicationRun'],
    'auditedPublicationArtifactCount': 93, 'matchedSelectedPublicationPins': 25,
    'frozenFiles': completion_frozen, 'inputBindings': completion_input_bindings,
    'validationInputBindings': completion_product_bindings, 'publishedFiles': completion_published,
    'manifestSha256': file_sha256(completion_manifest_path),
    'manifestArchivedPath': str((completion_archive / 'frozen-manifest.json').relative_to(workspace)),
    'allArchivedHashesVerified': True, 'allPublishedBytesMatched': True,
    'auditEvidenceRecords': 44, 'targetSourceEvidenceRecordsAdded': 0,
    'scope': 'Fixed 93-artifact publication and 63 selected snapshots only. Audit records remain separate from the global target-source journal; later supplements and final client acceptance are outside this audit.'
}
(out / 'current-completion-audit-provenance.json').write_text(json.dumps(completion_provenance, ensure_ascii=False, indent=2) + '\n')

# Insert after current-completion-audit-provenance.json is written and before fork_negative.
# Independent authored catalog: do not append to evidence/static_supplements/reference_files.
import csv as _ttc_csv
import hashlib as _ttc_hashlib
import json as _ttc_json
from pathlib import Path as _ttc_Path

_ttc_directory = workspace / '.analysis-local/thread-turn-feature-contracts-work'
_ttc_manifest_path = _ttc_directory / 'freeze-manifest.json'
_ttc_manifest_pin = {'bytes': 48986, 'sha256': 'fdf3d457110e69f8d98751df60a66527002c8edd68eb671fd27b147089883422'}
_ttc_confirmation_pin = {'bytes': 576, 'sha256': '2749af4e27d14664b86ac2ef6a8cdba5e8618facdf09589b8c1877703e2f99c8'}
_ttc_cache, _ttc_json_cache, _ttc_sources = {}, {}, {}
_ttc_preserved = globals().get('preserved_inputs', {})
_ttc_checks = {'frozenFiles': 0, 'sourceArtifacts': 0, 'finalProducts': 0, 'reviewedProducts': 0,
               'authoredRecords': 0, 'inheritedRecords': 0, 'jsonPointers': 0, 'originalRanges': 0,
               'csvRows': 0, 'callLedgerAssociations': 0}


def _ttc_bytes(path):
    path = str(_ttc_Path(path).resolve())
    if path not in _ttc_cache:
        _ttc_cache[path] = _ttc_Path(path).read_bytes()
    return _ttc_cache[path]


def _ttc_sha(raw):
    return _ttc_hashlib.sha256(raw).hexdigest()


def _ttc_canonical(value):
    return _ttc_json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def _ttc_pin(path, entry):
    path = _ttc_Path(path).resolve()
    assert path.is_relative_to(workspace.resolve()), ('Thread/turn input outside workspace', str(path))
    assert path.stat().st_size == entry['bytes'] and file_sha256(path) == entry['sha256'], ('Thread/turn pin differs', entry['path'] if 'path' in entry else str(path))
    raw = _ttc_bytes(path)
    assert len(raw) == entry['bytes'] and _ttc_sha(raw) == entry['sha256'], ('Thread/turn cached bytes differ', str(path))
    return raw


def _ttc_object(path):
    path = str(_ttc_Path(path).resolve())
    if path not in _ttc_json_cache:
        _ttc_json_cache[path] = _ttc_json.loads(_ttc_bytes(path))
    return _ttc_json_cache[path]


def _ttc_pointer(value, pointer):
    for component in pointer.split('/')[1:] if pointer else []:
        component = component.replace('~1', '/').replace('~0', '~')
        value = value[int(component)] if isinstance(value, list) else value[component]
    return value


def _ttc_walk(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from _ttc_walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _ttc_walk(item)


# Fresh read-only preflight of every input/product precedes archive mutations.
_ttc_pin(_ttc_manifest_path, _ttc_manifest_pin)
assert _ttc_manifest_path.stat().st_mode & 0o222 == 0
_ttc_manifest = _ttc_object(_ttc_manifest_path)
assert _ttc_manifest['baselineId'] == baseline['baselineId'] == 'codex-26.1007.30912-c5b273322a83'
assert _ttc_manifest['status'] == 'frozen-read-only' and _ttc_manifest['ownerDirectory'] == str(_ttc_directory)
_ttc_frozen = {entry['path']: entry for entry in _ttc_manifest['files']}
assert len(_ttc_frozen) == len(_ttc_manifest['files']) == 70
for _ttc_path, _ttc_entry in _ttc_frozen.items():
    _ttc_source = _ttc_Path(_ttc_path)
    assert _ttc_source.is_relative_to(_ttc_directory) and _ttc_source.stat().st_mode & 0o222 == 0
    _ttc_pin(_ttc_source, _ttc_entry)
    _ttc_checks['frozenFiles'] += 1
assert {str(path) for path in _ttc_directory.rglob('*') if path.is_file() and path.name not in ['freeze-manifest.json', 'freeze-confirmation.json']} == set(_ttc_frozen)
thread_turn_catalog = _ttc_object(_ttc_directory / 'main.json')
_ttc_validation = _ttc_object(_ttc_directory / 'validation.json')
_ttc_review = _ttc_object(_ttc_directory / 'independent-review.json')
_ttc_protocol = _ttc_object(_ttc_directory / 'protocol-source-review.json')
assert all(record['baselineId'] == baseline['baselineId'] for record in [thread_turn_catalog, _ttc_validation, _ttc_review, _ttc_protocol])
assert _ttc_validation['status'] == 'passed' and not _ttc_validation['errors']
assert _ttc_review['status'] == 'passed-with-scope-limits' and not _ttc_review['errors']
assert _ttc_protocol['verification']['passed'] and not _ttc_protocol['verification']['errors']
assert len(_ttc_manifest['finalProducts']) == 7 and len(_ttc_manifest['reviewedProducts']) == 9
for _ttc_category in ['finalProducts', 'reviewedProducts']:
    assert len({entry['path'] for entry in _ttc_manifest[_ttc_category]}) == len(_ttc_manifest[_ttc_category])
    for _ttc_entry in _ttc_manifest[_ttc_category]:
        assert _ttc_frozen[_ttc_entry['path']] == _ttc_entry
        _ttc_checks[_ttc_category] += 1
assert _ttc_review['reviewedProducts'] == _ttc_manifest['reviewedProducts']
for _ttc_entry in _ttc_validation['verifiedProducts'] + [_ttc_validation['verifier']]:
    assert _ttc_frozen[_ttc_entry['path']] == _ttc_entry
assert _ttc_manifest['sourceArtifacts'] == thread_turn_catalog['inputPins']
assert len(thread_turn_catalog['inputPins']) == 98
_ttc_js = {
    str(workspace / '.analysis-local/baselines' / baseline['baselineId'] / 'extracted/.vite/build/src-BJv5Mk7n.js'),
    str(workspace / '.analysis-local/baselines' / baseline['baselineId'] / 'extracted/webview/assets/app-initial-6350d04672d0.js'),
    str(workspace / '.analysis-local/baselines' / baseline['baselineId'] / 'extracted/webview/assets/app-shared-8bd9d0399038.js'),
}
_ttc_drift = []
for _ttc_entry in _ttc_manifest['sourceArtifacts']:
    _ttc_path = _ttc_entry['path']
    assert _ttc_path not in _ttc_sources
    _ttc_source = _ttc_Path(_ttc_path)
    _ttc_current_matches = (_ttc_source.exists() and _ttc_source.stat().st_size == _ttc_entry['bytes'] and file_sha256(_ttc_source) == _ttc_entry['sha256'])
    if _ttc_path in _ttc_js:
        # Original implementation is checked locally, never copied to publication.
        assert _ttc_current_matches, ('Original JavaScript changed', _ttc_path)
        _ttc_resolved = _ttc_source
    else:
        assert _ttc_source.suffix in ['.json', '.jsonl', '.csv', '.md', '.py'], ('Unexpected implementation input', _ttc_path)
        _ttc_resolved = _ttc_source if _ttc_current_matches else _ttc_preserved.get(_ttc_entry['sha256'])
        assert _ttc_resolved is not None, ('Pinned metadata unavailable; do not substitute current publication', _ttc_path)
        _ttc_resolved = _ttc_Path(_ttc_resolved)
        if not _ttc_current_matches:
            assert _ttc_resolved.stat().st_mode & 0o222 == 0, ('Changed input fallback must be a read-only snapshot', _ttc_path)
            _ttc_drift.append({'originalPath': _ttc_path, 'expectedSha256': _ttc_entry['sha256'],
                               'currentPathStatus': 'missing' if not _ttc_source.exists() else 'different-from-frozen-pin',
                               'resolvedFrozenPath': str(_ttc_resolved), 'scope': 'Expected frozen bytes only; current publication content was not substituted.'})
    _ttc_pin(_ttc_resolved, _ttc_entry)
    _ttc_sources[_ttc_path] = {'pin': _ttc_entry, 'resolved': _ttc_resolved, 'currentPathMatched': _ttc_current_matches}
    _ttc_checks['sourceArtifacts'] += 1
assert len(_ttc_sources) == 98 and len(set(_ttc_sources) & _ttc_js) == 3
assert thread_turn_catalog['snapshotOrigin']['originPath'] not in _ttc_sources
_ttc_origin = thread_turn_catalog['snapshotOrigin']
_ttc_snapshot = _ttc_sources[_ttc_origin['snapshotPath']]
assert _ttc_snapshot['pin']['bytes'] == _ttc_origin['originBytes'] and _ttc_snapshot['pin']['sha256'] == _ttc_origin['originSha256']
assert _ttc_origin['originBeforeAfterStable'] is True
# Validate the closure-external diagnostic separately, without counting it as a frozen file.
_ttc_confirmation_path = _ttc_directory / 'freeze-confirmation.json'
_ttc_pin(_ttc_confirmation_path, _ttc_confirmation_pin)
assert _ttc_confirmation_path.stat().st_mode & 0o222 == 0
_ttc_confirmation = _ttc_object(_ttc_confirmation_path)
assert _ttc_confirmation['status'] == 'passed' and not _ttc_confirmation['errors']
assert _ttc_confirmation['manifest'] == {'path': str(_ttc_manifest_path), **_ttc_manifest_pin}

_ttc_authored = [_ttc_json.loads(line) for line in _ttc_bytes(_ttc_directory / 'evidence.jsonl').splitlines()]
_ttc_ids = {record['id'] for record in _ttc_authored}
assert len(_ttc_ids) == len(_ttc_authored) == 58
_ttc_inherited_ids = {record['id'] for record in thread_turn_catalog['inheritedReferences']}
assert len(thread_turn_catalog['inheritedReferences']) == 172
_ttc_unrechecked_original_locators = []
for _ttc_record in thread_turn_catalog['inheritedReferences']:
    _ttc_journal_pin = _ttc_record['journalSource']
    assert _ttc_sources[_ttc_journal_pin['path']]['pin'] == _ttc_journal_pin
    _ttc_raw = _ttc_bytes(_ttc_sources[_ttc_journal_pin['path']]['resolved'])
    _ttc_range = _ttc_record['journalByteRange']
    _ttc_piece = _ttc_raw[_ttc_range['start']:_ttc_range['endExclusive']]
    assert 0 <= _ttc_range['start'] < _ttc_range['endExclusive'] <= len(_ttc_raw)
    assert _ttc_sha(_ttc_piece) == _ttc_record['recordSha256IncludingLineEnding']
    assert _ttc_json.loads(_ttc_piece) == _ttc_record['record'] and _ttc_record['record']['id'] == _ttc_record['id']
    assert _ttc_raw[:_ttc_range['start']].count(b'\n') + 1 == _ttc_record['line']
    if _ttc_record.get('originalSourceVerification'):
        _ttc_original = _ttc_record['originalSourceVerification']
        assert _ttc_original['source']['sha256'] == _ttc_record['record']['sourceHash']
        _ttc_locator = _ttc_record['record']['locator']
        assert _ttc_original['byteRange'] == {'start': _ttc_locator['start'], 'endExclusive': _ttc_locator['endExclusive']}
        if _ttc_record['record'].get('spanSha256'):
            assert _ttc_original['spanSha256'] == _ttc_record['record']['spanSha256']
    else:
        _ttc_unrechecked_original_locators.append({'id': _ttc_record['id'], 'sourcePath': _ttc_record['record'].get('sourcePath'),
                                                  'sourceHash': _ttc_record['record'].get('sourceHash'), 'locator': _ttc_record['record'].get('locator'),
                                                  'scope': 'Exact inherited JSONL record verified; underlying original locator was not newly verified by the frozen catalog or this publisher block.'})
    _ttc_checks['inheritedRecords'] += 1
_ttc_pointer_seen, _ttc_range_seen, _ttc_csv_seen = set(), set(), set()
for _ttc_item in list(_ttc_walk(thread_turn_catalog)) + list(_ttc_walk(_ttc_authored)):
    if str(_ttc_item.get('evidenceId', '')).startswith('THREAD-TURN-CONTRACT-'):
        assert _ttc_item['evidenceId'] in _ttc_ids
    _ttc_pin_ref = _ttc_item.get('source')
    if not isinstance(_ttc_pin_ref, dict) or not {'path', 'bytes', 'sha256'} <= _ttc_pin_ref.keys():
        continue
    _ttc_binding = _ttc_sources[_ttc_pin_ref['path']]
    assert _ttc_binding['pin'] == {key: _ttc_pin_ref[key] for key in ['path', 'bytes', 'sha256']}
    if 'jsonPointer' in _ttc_item:
        _ttc_key = (_ttc_pin_ref['path'], _ttc_item['jsonPointer'], _ttc_item['valueCanonicalSha256'])
        if _ttc_key not in _ttc_pointer_seen:
            _ttc_value = _ttc_pointer(_ttc_object(_ttc_binding['resolved']), _ttc_item['jsonPointer'])
            assert _ttc_sha(_ttc_canonical(_ttc_value)) == _ttc_item['valueCanonicalSha256']
            _ttc_pointer_seen.add(_ttc_key)
    if 'byteRange' in _ttc_item and 'spanSha256' in _ttc_item:
        _ttc_range = _ttc_item['byteRange']
        _ttc_key = (_ttc_pin_ref['path'], _ttc_range['start'], _ttc_range['endExclusive'], _ttc_item['spanSha256'])
        if _ttc_key not in _ttc_range_seen:
            _ttc_raw = _ttc_bytes(_ttc_binding['resolved'])
            assert 0 <= _ttc_range['start'] < _ttc_range['endExclusive'] <= len(_ttc_raw)
            assert _ttc_sha(_ttc_raw[_ttc_range['start']:_ttc_range['endExclusive']]) == _ttc_item['spanSha256']
            _ttc_range_seen.add(_ttc_key)
    if 'csvDataRow' in _ttc_item:
        _ttc_key = (_ttc_pin_ref['path'], _ttc_item['csvDataRow'], _ttc_item['rowCanonicalSha256'])
        if _ttc_key not in _ttc_csv_seen:
            _ttc_rows = list(_ttc_csv.DictReader(_ttc_bytes(_ttc_binding['resolved']).decode().splitlines()))
            assert 1 <= _ttc_item['csvDataRow'] <= len(_ttc_rows)
            assert _ttc_sha(_ttc_canonical(_ttc_rows[_ttc_item['csvDataRow'] - 1])) == _ttc_item['rowCanonicalSha256']
            _ttc_csv_seen.add(_ttc_key)
for _ttc_record in _ttc_authored:
    assert _ttc_record['baselineId'] == baseline['baselineId'] and _ttc_record['id'].startswith('THREAD-TURN-CONTRACT-')
    assert set(_ttc_record['inheritedEvidenceIds']) <= _ttc_inherited_ids
    _ttc_checks['authoredRecords'] += 1
_ttc_checks.update(jsonPointers=len(_ttc_pointer_seen), originalRanges=len(_ttc_range_seen), csvRows=len(_ttc_csv_seen))
assert (_ttc_checks['jsonPointers'], _ttc_checks['originalRanges'], _ttc_checks['csvRows']) == (82, 28, 2)
assert thread_turn_catalog['denominators'] == {'originalGenericFeatureGroups': 36, 'selectedGenericFeatureGroups': 2,
    'refinedOperationMethods': 7, 'selectedLiteralWrapperCalls': 19, 'selectedCallsStaticRwcManager': 4,
    'selectedCallsReceiverUnresolved': 15, 'canonicalCompleteFunctionOrMemberUnits': 8, 'authoredObservedBranchVariants': 9,
    'separateDirectLexicalCandidates': 2, 'confirmedUiToOperationContracts': 0, 'runtimeMethodCorrelatedOperationContracts': 0,
    'fullFeatureCompletenessClaimed': False}
for _ttc_call in thread_turn_catalog['callCatalog']:
    _ttc_wrapper = _ttc_pointer(_ttc_object(_ttc_sources[_ttc_call['oldWrapperReference']['source']['path']]['resolved']), _ttc_call['oldWrapperReference']['jsonPointer'])
    _ttc_ledger = _ttc_pointer(_ttc_object(_ttc_sources[_ttc_call['ledgerReference']['source']['path']]['resolved']), _ttc_call['ledgerReference']['jsonPointer'])
    _ttc_candidate = _ttc_pointer(_ttc_object(_ttc_sources[_ttc_call['oldCandidateLinkReference']['source']['path']]['resolved']), _ttc_call['oldCandidateLinkReference']['jsonPointer'])
    assert _ttc_wrapper['callEvidenceId'] == _ttc_call['astCallEvidenceId'] == _ttc_candidate['astCallEvidenceId']
    assert _ttc_wrapper['method'] == _ttc_call['method'] and _ttc_wrapper['receiver'] == _ttc_call['receiver']
    assert _ttc_wrapper['kind'] == _ttc_call['receiverClassification'] and _ttc_wrapper['contractId'] == _ttc_call['contractId']
    assert _ttc_ledger['candidateId'] == _ttc_call['ledgerId'] and _ttc_ledger['sourceCoordinates']['evidenceId'] == _ttc_candidate['publishedEvidenceId']
    _ttc_lexical, _ttc_ast = _ttc_ledger['sourceCoordinates']['byteRange'], _ttc_call['sourceCall']['byteRange']
    assert _ttc_ast['start'] <= _ttc_lexical['start'] < _ttc_lexical['endExclusive'] <= _ttc_ast['endExclusive']
    assert _ttc_call['uiTrigger'] == _ttc_call['executionMode'] == 'unknown' and _ttc_call['runtimeStatus'] == 'unverified'
    _ttc_checks['callLedgerAssociations'] += 1
for _ttc_operation in thread_turn_catalog['methodCatalog']:
    assert all(_ttc_operation[key] == 'unknown' for key in ['uiTrigger', 'receiverRuntime', 'actualInitializationMode', 'runtimeMethodCorrelation'])
    assert _ttc_operation['necessaryDeclarationRelations']['relationConfidence'].startswith('inferred')
    # Schema-field/union/comparison semantics are covered by the pinned 2131/1575 reports;
    # this publisher block verifies their products/input identities and explicit locators.
    for _ttc_variant in _ttc_operation['observedVariants']:
        assert _ttc_variant['method'] == _ttc_operation['method'] and _ttc_variant['runtimeStatus'] == 'unverified'
        assert _ttc_variant['uiTrigger'] == _ttc_variant['executionMode'] == 'unknown'
        for _ttc_call in _ttc_variant['callReferences']:
            _ttc_unit, _ttc_call_range = _ttc_variant['sourceUnit']['byteRange'], _ttc_call['sourceCall']['byteRange']
            assert _ttc_variant['sourceUnit']['source'] == _ttc_call['sourceCall']['source']
            assert _ttc_unit['start'] <= _ttc_call_range['start'] < _ttc_call_range['endExclusive'] <= _ttc_unit['endExclusive']
assert all(not thread_turn_catalog['scope'][key] for key in ['targetExecution', 'cliExecution', 'uiExecution', 'networkExecution', 'credentialsOrPersonalHistoryRead', 'newAstParsing'])
assert thread_turn_catalog['scope']['modelTasks'] == 0

# Publication is a sequence of atomic single-file copies, not a batch transaction.
_ttc_archive = out / 'raw/thread-turn-feature-contracts'
_ttc_archived, _ttc_frozen_bindings = {}, []
for _ttc_path, _ttc_entry in _ttc_frozen.items():
    _ttc_source = _ttc_Path(_ttc_path)
    _ttc_destination = _ttc_archive / 'frozen' / _ttc_source.relative_to(_ttc_directory)
    _ttc_destination.parent.mkdir(parents=True, exist_ok=True)
    publish_copy(_ttc_source, _ttc_destination)
    _ttc_pin(_ttc_destination, _ttc_entry)
    _ttc_destination.chmod(0o444)
    _ttc_archived[_ttc_path] = _ttc_destination
    _ttc_frozen_bindings.append({**_ttc_entry, 'archivedPath': str(_ttc_destination.relative_to(workspace))})
_ttc_manifest_destination = _ttc_archive / 'freeze-manifest.json'
publish_copy(_ttc_manifest_path, _ttc_manifest_destination)
_ttc_pin(_ttc_manifest_destination, _ttc_manifest_pin)
_ttc_manifest_destination.chmod(0o444)
_ttc_confirmation_destination = _ttc_archive / 'diagnostics/freeze-confirmation.json'
_ttc_confirmation_destination.parent.mkdir(parents=True, exist_ok=True)
publish_copy(_ttc_confirmation_path, _ttc_confirmation_destination)
_ttc_pin(_ttc_confirmation_destination, _ttc_confirmation_pin)
_ttc_confirmation_destination.chmod(0o444)
_ttc_input_bindings = []
for _ttc_index, (_ttc_path, _ttc_binding) in enumerate(_ttc_sources.items()):
    _ttc_entry = _ttc_binding['pin']
    if _ttc_path in _ttc_js:
        _ttc_input_bindings.append({**_ttc_entry, 'resolvedPath': str(_ttc_binding['resolved'].relative_to(workspace)),
                                    'archivedPath': None, 'policy': 'original-JavaScript-local-hash-and-range-only; implementation-not-copied'})
        continue
    _ttc_destination = _ttc_archived.get(_ttc_path)
    if _ttc_destination is None:
        _ttc_destination = _ttc_archive / 'inputs' / (f'{_ttc_index:03d}-' + _ttc_Path(_ttc_path).name)
        _ttc_destination.parent.mkdir(parents=True, exist_ok=True)
        publish_copy(_ttc_binding['resolved'], _ttc_destination)
        _ttc_destination.chmod(0o444)
    _ttc_pin(_ttc_destination, _ttc_entry)
    assert _ttc_destination.stat().st_mode & 0o222 == 0
    _ttc_input_bindings.append({**_ttc_entry, 'resolvedPath': str(_ttc_binding['resolved'].relative_to(workspace)),
                               'archivedPath': str(_ttc_destination.relative_to(workspace)), 'currentPathMatched': _ttc_binding['currentPathMatched'],
                               'policy': 'exact-pinned-metadata-bytes; archived-read-only'})
    _ttc_preserved[_ttc_entry['sha256']] = _ttc_destination
_ttc_aliases = {'main.json': 'thread-turn-feature-contracts.json', 'evidence.jsonl': 'thread-turn-feature-contracts-evidence.jsonl',
    'summary.md': 'thread-turn-feature-contracts-summary.md', 'validation.json': 'thread-turn-feature-contracts-validation.json',
    'freeze-manifest.json': 'thread-turn-feature-contracts-manifest.json', 'independent-review.json': 'thread-turn-feature-contracts-peer-review.json',
    'independent-review.md': 'thread-turn-feature-contracts-peer-review.md', 'protocol-source-review.json': 'thread-turn-feature-contracts-protocol-source-review.json'}
_ttc_published = []
for _ttc_name, _ttc_alias in _ttc_aliases.items():
    _ttc_source = _ttc_directory / _ttc_name
    _ttc_entry = _ttc_manifest_pin if _ttc_name == 'freeze-manifest.json' else _ttc_frozen[str(_ttc_source)]
    publish_copy(_ttc_source, out / _ttc_alias)
    _ttc_pin(out / _ttc_alias, _ttc_entry)
    _ttc_published.append({'path': str(_ttc_source.relative_to(workspace)), 'publishedPath': str((out / _ttc_alias).relative_to(workspace)),
                            'bytes': _ttc_entry['bytes'], 'sha256': _ttc_entry['sha256']})
thread_turn_provenance = {'schemaVersion': 'thread-turn-feature-contracts-publication/1', 'baselineId': baseline['baselineId'],
    'catalogStatus': thread_turn_catalog['status'], 'denominators': thread_turn_catalog['denominators'],
    'frozenFiles': _ttc_frozen_bindings, 'inputBindings': _ttc_input_bindings, 'publishedFiles': _ttc_published,
    'manifestSha256': _ttc_manifest_pin['sha256'], 'manifestBytes': _ttc_manifest_pin['bytes'],
    'manifestArchivedPath': str(_ttc_manifest_destination.relative_to(workspace)),
    'postFreezeDiagnostic': {**_ttc_confirmation_pin, 'archivedPath': str(_ttc_confirmation_destination.relative_to(workspace)), 'partOfFrozenFiles': False},
    'frozenFilesCount': 70, 'sourceArtifactCount': 98, 'originalJavaScriptLocalOnly': 3,
    'metadataInputBindings': 95, 'metadataBindingsReusingOwnedArchive': len(set(_ttc_sources) & set(_ttc_frozen)),
    'authoredJournalRecords': 58, 'inheritedExactReferences': 172, 'targetSourceEvidenceRecordsAdded': 0,
    'globalEvidenceCountChangedByThisBlock': False, 'allArchivedHashesVerified': True, 'allPublishedBytesMatched': True,
    'freshPublisherChecks': _ttc_checks, 'changedCurrentInputPaths': _ttc_drift,
    'originalLocatorVerificationLimits': _ttc_unrechecked_original_locators,
    'savedValidation': {'status': _ttc_validation['status'], 'checks': _ttc_validation['checks'], 'errors': _ttc_validation['errors']},
    'savedIndependentReview': {'status': _ttc_review['status'], 'checks': _ttc_review['checks'], 'errors': _ttc_review['errors']},
    'scope': 'Byte-preserving independent authored catalog publication. Local JSON/CSV/source-range and exact inherited-record checks only; no target or bundled CLI/UI/network/model execution, no credential/history read, no new AST parsing. Current global journal is not read. Frozen analysis/peer semantics and confidence labels are retained; fresh publisher checks do not prove UI/business/runtime/mode/persistence equivalence, full feature completion or independent-build compatibility. Original JavaScript implementation is never copied.'}
(out / 'thread-turn-feature-contracts-provenance.json').write_text(_ttc_json.dumps(thread_turn_provenance, ensure_ascii=False, indent=2) + '\n')


# Insert after publisher defines workspace/out/baseline/file_sha256/publish_copy.
# publish_copy(Path source, Path destination) returns None; caller creates parent.
# All reads below are this group's frozen owned files and its 27 saved snapshots.
# This independent reconciliation journal must not be appended to a target-source journal.
from pathlib import Path as _request_entry_Path
import json as _request_entry_json
import hashlib as _request_entry_hashlib
import os as _request_entry_os
import tempfile as _request_entry_tempfile

_request_entry_work = _request_entry_Path(workspace) / ".analysis-local/request-entry-reconciliation-work"
_request_entry_out = _request_entry_Path(out)
_request_entry_baseline_id = "codex-26.1007.30912-c5b273322a83"
assert baseline["baselineId"] == _request_entry_baseline_id
_request_entry_manifest_path = _request_entry_work / "manifest.json"
assert file_sha256(_request_entry_manifest_path) == "8efa147f3e684c698ff0a213437bf5d2a533b47e538b0fec633edf612e3709d1"
_request_entry_manifest = _request_entry_json.loads(_request_entry_manifest_path.read_text())
assert _request_entry_manifest["baselineId"] == _request_entry_baseline_id
assert _request_entry_manifest["status"] == "frozen-after-independent-artifact-reconciliation-verification"
_request_entry_owned = {}
for _request_entry_file in _request_entry_manifest["files"]:
    _request_entry_relative = _request_entry_file["relativePath"]
    _request_entry_path = _request_entry_work / _request_entry_relative
    assert _request_entry_path.resolve().is_relative_to(_request_entry_work.resolve())
    assert str(_request_entry_path) == _request_entry_file["path"]
    assert _request_entry_path.stat().st_size == _request_entry_file["bytes"]
    assert file_sha256(_request_entry_path) == _request_entry_file["sha256"]
    assert _request_entry_path.stat().st_mode & 0o777 == 0o444
    assert _request_entry_relative not in _request_entry_owned
    _request_entry_owned[_request_entry_relative] = _request_entry_file
assert len(_request_entry_owned) == 50
assert {str(p.relative_to(_request_entry_work)) for p in _request_entry_work.rglob("*") if p.is_file()} == set(_request_entry_owned) | {"manifest.json"}
assert _request_entry_manifest_path.stat().st_mode & 0o777 == 0o444
_request_entry_owned["manifest.json"] = {
    "relativePath": "manifest.json", "path": str(_request_entry_manifest_path),
    "bytes": _request_entry_manifest_path.stat().st_size,
    "sha256": file_sha256(_request_entry_manifest_path),
}

_request_entry_json_cache = {}
_request_entry_lines_cache = {}
def _request_entry_load(relative):
    if relative not in _request_entry_json_cache:
        assert relative in _request_entry_owned
        _request_entry_json_cache[relative] = _request_entry_json.loads((_request_entry_work / relative).read_text())
    return _request_entry_json_cache[relative]
def _request_entry_lines(relative):
    if relative not in _request_entry_lines_cache:
        assert relative in _request_entry_owned
        _request_entry_lines_cache[relative] = (_request_entry_work / relative).read_bytes().splitlines(keepends=True)
    return _request_entry_lines_cache[relative]
def _request_entry_pointer(obj, pointer):
    for bit in pointer[1:].split("/") if pointer else []:
        bit = bit.replace("~1", "/").replace("~0", "~")
        obj = obj[int(bit)] if isinstance(obj, list) else obj[bit]
    return obj

_request_entry_main = _request_entry_load("reconciliation.json")
_request_entry_validation = _request_entry_load("validation.json")
_request_entry_receipts = _request_entry_load("input-receipts.json")
_request_entry_sources = _request_entry_load("source-receipts.json")
_request_entry_journal = [_request_entry_json.loads(line) for line in _request_entry_lines("journal.jsonl")]
assert _request_entry_main["baselineId"] == _request_entry_validation["baselineId"] == _request_entry_baseline_id
assert _request_entry_validation["status"] == "passed" and _request_entry_validation["checks"] == 8744 and _request_entry_validation["errors"] == []
for _request_entry_product in _request_entry_validation["finalProducts"]:
    _request_entry_product_path = _request_entry_Path(_request_entry_product["path"])
    assert _request_entry_product_path.resolve().is_relative_to(_request_entry_work.resolve())
    _request_entry_product_relative = str(_request_entry_product_path.relative_to(_request_entry_work))
    assert _request_entry_owned[_request_entry_product_relative]["bytes"] == _request_entry_product["bytes"]
    assert _request_entry_owned[_request_entry_product_relative]["sha256"] == _request_entry_product["sha256"]
assert len(_request_entry_receipts["inputs"]) == 27
assert _request_entry_receipts["ledgerSourceArtifactsVerified"] == 14
_request_entry_by_origin = {}
_request_entry_by_snapshot = {}
for _request_entry_receipt in _request_entry_receipts["inputs"]:
    _request_entry_snapshot = _request_entry_Path(_request_entry_receipt["snapshotPath"])
    assert _request_entry_snapshot.resolve().is_relative_to((_request_entry_work / "inputs").resolve())
    _request_entry_snapshot_relative = str(_request_entry_snapshot.relative_to(_request_entry_work))
    _request_entry_record = _request_entry_owned[_request_entry_snapshot_relative]
    assert _request_entry_record["sha256"] == _request_entry_receipt["sha256"]
    assert _request_entry_record["bytes"] == _request_entry_receipt["bytes"]
    assert _request_entry_receipt["originalTargetSourceRead"] is False
    _request_entry_by_origin[_request_entry_receipt["originPath"]] = _request_entry_receipt
    _request_entry_by_snapshot[_request_entry_receipt["snapshotPath"]] = _request_entry_snapshot_relative
assert len(_request_entry_by_origin) == len(_request_entry_by_snapshot) == 27

def _request_entry_witness(witness):
    receipt = _request_entry_by_origin[witness["artifactPath"]]
    assert witness["artifactSha256"] == receipt["sha256"]
    assert witness["snapshotPath"] == receipt["snapshotPath"]
    relative = _request_entry_by_snapshot[witness["snapshotPath"]]
    return _request_entry_pointer(_request_entry_load(relative), witness["jsonPointer"]) if witness["jsonPointer"] else None
def _request_entry_check_line(witness):
    _request_entry_witness(witness)
    relative = _request_entry_by_snapshot[witness["snapshotPath"]]
    lines = _request_entry_lines(relative)
    assert 1 <= witness["line"] <= len(lines)
    raw = lines[witness["line"] - 1]
    assert _request_entry_hashlib.sha256(raw).hexdigest() == witness["rawLineSha256"]
    return _request_entry_json.loads(raw)
def _request_entry_walk_witnesses(value):
    if isinstance(value, dict):
        if {"artifactPath", "snapshotPath", "artifactSha256", "jsonPointer"}.issubset(value):
            yield value
        for child in value.values():
            yield from _request_entry_walk_witnesses(child)
    elif isinstance(value, list):
        for child in value:
            yield from _request_entry_walk_witnesses(child)

_request_entry_base = "analysis/" + _request_entry_baseline_id
_request_entry_wrapper = _request_entry_load("inputs/" + _request_entry_base + "/request-wrapper-contracts.json")
_request_entry_ledger = _request_entry_load("inputs/" + _request_entry_base + "/functional-entry-ledger.json")
assert len(_request_entry_wrapper["calls"]) == len(_request_entry_main["candidates"]) == len(_request_entry_journal) == 375
assert len(_request_entry_ledger["entries"]) == 968
assert len(_request_entry_ledger["deferredCandidates"]) == 337
assert len(_request_entry_ledger["supportNodes"]) == 176
assert _request_entry_main["summary"]["registrationCounts"] == {"notAligned": 38, "registeredDeferred": 337}
assert _request_entry_main["summary"]["notAlignedByMethodKind"] == {"single-literal": 16, "dynamic-or-conditional": 22}
assert _request_entry_main["summary"]["confirmedOmissions"] == _request_entry_main["summary"]["newFeaturesClaimed"] == 0
assert _request_entry_main["confirmedOmissionCandidates"] == []
assert _request_entry_main["summary"]["denominators"]["featureCensusDenominator"] == "unknown"
assert _request_entry_main["summary"]["denominators"]["wrapperSingleLiteral"] == 353
assert _request_entry_main["summary"]["denominators"]["wrapperDynamicOrConditional"] == 22
assert _request_entry_main["legacyValidation"]["wrapperStandaloneValidation"].startswith("not-located")
assert _request_entry_main["legacyValidation"]["wrapperStandaloneManifest"].startswith("not-located")
for _request_entry_flag in ["targetSourceRead", "targetExecuted", "cliExecuted", "uiUsed", "modelInvoked", "networkUsed"]:
    assert _request_entry_main[_request_entry_flag] is False
assert len(_request_entry_ledger["sourceArtifacts"]) == 14
for _request_entry_legacy_source in _request_entry_ledger["sourceArtifacts"]:
    _request_entry_legacy_snapshot = "inputs/" + _request_entry_legacy_source["path"]
    assert _request_entry_owned[_request_entry_legacy_snapshot]["sha256"] == _request_entry_legacy_source["sha256"]
    assert _request_entry_owned[_request_entry_legacy_snapshot]["bytes"] == _request_entry_legacy_source["bytes"]

_request_entry_witness_checks = 0
for _request_entry_document in [_request_entry_main, _request_entry_journal, _request_entry_sources]:
    for _request_entry_item in _request_entry_walk_witnesses(_request_entry_document):
        _request_entry_witness(_request_entry_item)
        _request_entry_witness_checks += 1
_request_entry_registered = 0
_request_entry_not_aligned = 0
_request_entry_linked_old_ids = set()
_request_entry_literal = 0
_request_entry_dynamic = 0
for _request_entry_i, (_request_entry_candidate, _request_entry_note) in enumerate(zip(_request_entry_main["candidates"], _request_entry_journal)):
    _request_entry_call = _request_entry_witness(_request_entry_candidate["wrapperWitness"])
    _request_entry_ev = _request_entry_check_line(_request_entry_note["callJournalWitness"])
    assert _request_entry_call == _request_entry_wrapper["calls"][_request_entry_i]
    assert _request_entry_call["callEvidenceId"] == _request_entry_candidate["callEvidenceId"] == _request_entry_note["callEvidenceId"] == _request_entry_ev["id"]
    assert _request_entry_call["sourcePath"] == _request_entry_candidate["sourcePath"] == _request_entry_note["sourcePath"]
    assert _request_entry_call["sourceHash"] == _request_entry_candidate["sourceHash"] == _request_entry_note["sourceHash"]
    assert _request_entry_call["methodKind"] == _request_entry_candidate["methodKind"]
    assert (_request_entry_candidate["sourcePath"], _request_entry_candidate["sourceHash"], _request_entry_candidate["completeCallRange"], _request_entry_candidate["spanSha256"]) == (_request_entry_ev["sourcePath"], _request_entry_ev["sourceHash"], _request_entry_ev["locator"], _request_entry_ev["spanSha256"])
    assert _request_entry_note["locator"] == _request_entry_candidate["completeCallRange"]
    assert _request_entry_note["retainedSpanSha256"] == _request_entry_candidate["spanSha256"]
    assert _request_entry_note["mainJsonPointer"] == "/candidates/" + str(_request_entry_i)
    assert _request_entry_note["registrationStatus"] == _request_entry_candidate["registrationStatus"]
    assert _request_entry_candidate["mode"] == _request_entry_candidate["runtime"] == "unknown"
    assert _request_entry_candidate["featureId"] is None and _request_entry_candidate["confirmedOmission"] is False
    _request_entry_literal += int(_request_entry_candidate["methodKind"] == "single-literal")
    _request_entry_dynamic += int(_request_entry_candidate["methodKind"] == "dynamic-or-conditional")
    _request_entry_association = _request_entry_candidate["deferredAssociation"]
    assert _request_entry_note["deferredAssociation"] == _request_entry_association
    for _request_entry_context in _request_entry_candidate["savedScopeContexts"]:
        assert _request_entry_witness(_request_entry_context["witness"]) == _request_entry_context["oldCoordinates"]
        assert _request_entry_context["identityClaim"] is False and _request_entry_context["featureAssociation"] is False
    if _request_entry_association is None:
        assert _request_entry_candidate["registrationStatus"] == "not-aligned-to-old-callsite-registration"
        assert _request_entry_candidate["exactPrimaryRangeMatches"] == _request_entry_candidate["exactSecondaryRangeMatches"] == _request_entry_candidate["directEvidenceIdMembership"] == []
        _request_entry_not_aligned += 1
        continue
    _request_entry_registered += 1
    _request_entry_old = _request_entry_witness(_request_entry_association["ledgerWitness"])
    _request_entry_link = _request_entry_witness(_request_entry_association["explicitLinkWitness"])
    _request_entry_rpc = _request_entry_witness(_request_entry_association["oldSourceArtifactWitness"])
    _request_entry_old_ev = _request_entry_check_line(_request_entry_association["oldJournalWitness"])
    _request_entry_old_coord = _request_entry_old["sourceCoordinates"]
    _request_entry_old_range = _request_entry_old_coord["byteRange"]
    assert _request_entry_association["oldCoordinates"] == _request_entry_old_coord
    assert _request_entry_old["candidateId"] == _request_entry_association["recordId"]
    assert _request_entry_link["publishedEvidenceId"] == _request_entry_association["oldEvidenceId"] == _request_entry_rpc["evidenceId"] == _request_entry_old_ev["id"]
    assert _request_entry_link["astCallEvidenceId"] == _request_entry_candidate["callEvidenceId"]
    assert _request_entry_old_coord["sourcePath"] == _request_entry_old_ev["sourcePath"] == _request_entry_candidate["sourcePath"]
    assert _request_entry_old_coord["sourceHash"] == _request_entry_old_ev["sourceHash"] == _request_entry_candidate["sourceHash"]
    assert _request_entry_old_ev["locator"] == _request_entry_old_range == _request_entry_association["oldCoordinates"]["byteRange"]
    _request_entry_containing = [candidate["callEvidenceId"] for candidate in _request_entry_main["candidates"]
        if candidate["sourcePath"] == _request_entry_old_coord["sourcePath"] and candidate["sourceHash"] == _request_entry_old_coord["sourceHash"]
        and candidate["completeCallRange"]["start"] <= _request_entry_old_range["start"]
        and _request_entry_old_range["endExclusive"] <= candidate["completeCallRange"]["endExclusive"]]
    assert _request_entry_containing == [_request_entry_candidate["callEvidenceId"]]
    assert _request_entry_candidate["completeCallRange"] != _request_entry_old_range
    assert _request_entry_association["sameSpan"] is False and _request_entry_association["operationIdentity"] is False and _request_entry_association["featureIdentity"] is False
    assert _request_entry_association["oldEvidenceId"] not in _request_entry_linked_old_ids
    _request_entry_linked_old_ids.add(_request_entry_association["oldEvidenceId"])
assert (_request_entry_registered, _request_entry_not_aligned, _request_entry_literal, _request_entry_dynamic) == (337, 38, 353, 22)
assert len(_request_entry_linked_old_ids) == 337
assert len(_request_entry_sources) == 37 and sum(x["astSendRequestCount"] for x in _request_entry_sources) == 375
for _request_entry_source in _request_entry_sources:
    _request_entry_saved_inventory = _request_entry_witness(_request_entry_source["inventoryWitness"])
    assert _request_entry_source["sourcePath"] == _request_entry_saved_inventory["sourcePath"]
    assert _request_entry_source["sourceHash"] == _request_entry_saved_inventory["sha256"]
    assert _request_entry_source["bytes"] == _request_entry_saved_inventory["bytes"]
    assert _request_entry_source["targetSourceBytesRead"] is False and _request_entry_source["targetSpanBytesRehashed"] is False

_request_entry_aliases = {
    "reconciliation.json": "request-entry-reconciliation.json",
    "summary.md": "request-entry-reconciliation-summary.md",
    "journal.jsonl": "request-entry-reconciliation-evidence.jsonl",
    "input-receipts.json": "request-entry-reconciliation-input-receipts.json",
    "source-receipts.json": "request-entry-reconciliation-source-receipts.json",
    "validation.json": "request-entry-reconciliation-validation.json",
    "peer-input-check.json": "request-entry-reconciliation-peer-input-check.json",
    "peer-review.json": "request-entry-reconciliation-peer-review.json",
    "manifest.json": "request-entry-reconciliation-manifest.json",
}
_request_entry_copied = []
for _request_entry_relative, _request_entry_file in sorted(_request_entry_owned.items()):
    _request_entry_destination_relative = "provenance/request-entry-reconciliation/" + _request_entry_relative
    _request_entry_destination = _request_entry_out / _request_entry_destination_relative
    _request_entry_destination.parent.mkdir(parents=True, exist_ok=True)
    publish_copy(_request_entry_work / _request_entry_relative, _request_entry_destination)
    assert _request_entry_destination.stat().st_size == _request_entry_file["bytes"]
    assert file_sha256(_request_entry_destination) == _request_entry_file["sha256"]
    _request_entry_copied.append({"ownedRelativePath": _request_entry_relative, "publishedPath": _request_entry_destination_relative,
        "bytes": _request_entry_file["bytes"], "sha256": _request_entry_file["sha256"]})
_request_entry_alias_records = []
for _request_entry_relative, _request_entry_alias in _request_entry_aliases.items():
    _request_entry_destination = _request_entry_out / _request_entry_alias
    _request_entry_destination.parent.mkdir(parents=True, exist_ok=True)
    publish_copy(_request_entry_work / _request_entry_relative, _request_entry_destination)
    _request_entry_file = _request_entry_owned[_request_entry_relative]
    assert _request_entry_destination.stat().st_size == _request_entry_file["bytes"]
    assert file_sha256(_request_entry_destination) == _request_entry_file["sha256"]
    _request_entry_alias_records.append({"ownedRelativePath": _request_entry_relative, "publishedPath": _request_entry_alias,
        "bytes": _request_entry_file["bytes"], "sha256": _request_entry_file["sha256"]})
request_entry_reconciliation_provenance = {
    "schemaVersion": 1, "baselineId": _request_entry_baseline_id,
    "status": "frozen-owned-artifact-publication-checks-passed; original-target-source-and-runtime-unverified",
    "sourceManifestSha256": _request_entry_owned["manifest.json"]["sha256"],
    "frozenOwnedFilesCopied": 51, "ownedInputSnapshotsCopied": 27, "ledgerSourceArtifactPins": 14,
    "wrapperCandidates": 375, "registeredDeferred": 337, "notAligned": 38, "confirmedOmissions": 0,
    "literalCalls": 353, "dynamicOrConditionalCalls": 22, "featureCensusDenominator": "unknown",
    "witnessOccurrencesChecked": _request_entry_witness_checks,
    "checksScope": "Frozen owned-file pins/modes/closure, 27 owned snapshots, final product pins, exact JSON pointers and raw saved journal lines, qualified unique containment in 375 saved full-call ranges, and 14 legacy saved-artifact receipts. No origin/current or original target-source reads.",
    "legacyWrapperStandaloneValidation": _request_entry_main["legacyValidation"]["wrapperStandaloneValidation"],
    "legacyWrapperStandaloneManifest": _request_entry_main["legacyValidation"]["wrapperStandaloneManifest"],
    "journalScope": "375 independent artifact-reconciliation rows; excluded from global target-source journal.",
    "originalTargetSourceRead": False, "originalTargetSpanRehashed": False, "targetExecuted": False,
    "cliExecuted": False, "uiUsed": False, "modelInvoked": False, "networkUsed": False,
    "copiedFiles": _request_entry_copied, "aliases": _request_entry_alias_records,
}
request_entry_reconciliation_provenance["scope"] = request_entry_reconciliation_provenance["checksScope"]
_request_entry_provenance_path = _request_entry_out / "request-entry-reconciliation-provenance.json"
_request_entry_provenance_path.parent.mkdir(parents=True, exist_ok=True)
with _request_entry_tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=_request_entry_provenance_path.parent, delete=False) as _request_entry_tmp:
    _request_entry_json.dump(request_entry_reconciliation_provenance, _request_entry_tmp, ensure_ascii=False, indent=2)
    _request_entry_tmp.write("\n")
    _request_entry_tmp_path = _request_entry_Path(_request_entry_tmp.name)
_request_entry_tmp_path.chmod(0o444)
_request_entry_os.replace(_request_entry_tmp_path, _request_entry_provenance_path)
request_entry_reconciliation_publication = {
    "baselineId": _request_entry_baseline_id, "status": _request_entry_main["status"],
    "publicationCheckStatus": "passed-own-frozen-artifact-scope",
    "main": "request-entry-reconciliation.json", "summary": "request-entry-reconciliation-summary.md",
    "journal": "request-entry-reconciliation-evidence.jsonl", "validation": "request-entry-reconciliation-validation.json",
    "manifest": "request-entry-reconciliation-manifest.json",
    "provenance": {"path": "request-entry-reconciliation-provenance.json", "bytes": _request_entry_provenance_path.stat().st_size, "sha256": file_sha256(_request_entry_provenance_path)},
    "wrapperCandidates": 375, "registeredDeferred": 337, "notAligned": 38, "confirmedOmissions": 0,
    "literalCalls": 353, "dynamicOrConditionalCalls": 22,
    "featureCensusDenominator": "unknown", "runtimeStatus": "unknown",
    "legacyWrapperStandaloneValidation": _request_entry_main["legacyValidation"]["wrapperStandaloneValidation"],
    "legacyWrapperStandaloneManifest": _request_entry_main["legacyValidation"]["wrapperStandaloneManifest"],
    "globalTargetSourceJournalRecordsAdded": 0,
}
request_entry_reconciliation = _request_entry_main

scoped_static_catalogs = publish_scoped_catalogs(out=out, workspace=workspace, baseline=baseline)
static_boundaries = publish_static_boundaries(out=out, workspace=workspace, baseline=baseline)
catalog_supplements = publish_catalog_supplements(out=out, workspace=workspace, baseline=baseline)


fork_negative = json.loads((out / 'fork-negative-protocol-comparison.json').read_text())
assert fork_negative['baselineId'] == baseline['baselineId']
assert fork_negative['verification']['forkRequests'] == 32
assert fork_negative['verification']['forkSuccesses'] == fork_negative['verification']['targetModelTurnRequests'] == 0
for entry in fork_negative['inputs'] + fork_negative['priorFailuresPreserved']:
    assert hashlib.sha256((out / entry['path']).read_bytes()).hexdigest() == entry['sha256']
for case in fork_negative['comparison']['matrix']:
    for backend in ['frozen', 'publicNpm']:
        entry = case[backend]['rawEvidence']
        raw = Path(entry['path']).read_bytes()
        assert len(raw) == entry['bytes'] and hashlib.sha256(raw).hexdigest() == entry['sha256']
fork_path = 'analysis/' + baseline['baselineId'] + '/fork-negative-protocol-comparison.json'
fork_hash = hashlib.sha256((out / 'fork-negative-protocol-comparison.json').read_bytes()).hexdigest()
for index, case in enumerate(fork_negative['comparison']['matrix']):
    evidence.append({'id': 'FORKNEG-COMP-' + str(index + 1).zfill(3), 'baselineId': baseline['baselineId'],
                     'claim': 'Saved paired negative responses: ' + case['case'] + '; experimentalApi=' + str(case['experimentalApi']),
                     'sourcePath': fork_path, 'sourceHash': fork_hash,
                     'locator': {'kind': 'json-pointer', 'pointer': '/comparison/matrix/' + str(index)},
                     'method': 'saved-app-server-negative-response-comparison', 'confidence': 'confirmed',
                     'verificationStatus': 'negative-path-observed; successful-fork-and-prediction-semantics-unverified'})
behavior_hash = hashlib.sha256((out / 'behavior-observations.json').read_bytes()).hexdigest()
for index, observation in enumerate(observations):
    evidence.append({'id': 'RUNTIME-E' + str(index + 1).zfill(4), 'baselineId': baseline['baselineId'],
                     'claim': f"Runtime observation {observation['action']}: {observation['status']}; see structured observations",
                     'sourcePath': 'analysis/' + baseline['baselineId'] + '/behavior-observations.json',
                     'sourceHash': behavior_hash, 'locator': {'kind': 'json-pointer', 'pointer': '/' + str(index)},
                     'method': observation.get('method', 'runtime-ui-playwright-cdp'), 'confidence': 'confirmed',
                     'verificationStatus': 'observation-recorded; does not establish full feature correctness'})

inventory = json.loads((out / 'files.json').read_text())
sources = {r['sourcePath']: r for group in ['archiveFiles', 'applicationFiles'] for r in inventory[group] if 'sha256' in r}
errors = []
ids = set()
for e in evidence:
    if e['id'] in ids:
        errors.append({'id': e['id'], 'error': 'duplicate-id'})
    ids.add(e['id'])
    if e['baselineId'] != baseline['baselineId']:
        errors.append({'id': e['id'], 'error': 'wrong-baseline'})
    source = sources.get(e['sourcePath'])
    if e['id'] in directed_external_evidence_sources:
        binding = directed_external_evidence_sources[e['id']]
        local_source = binding['path']
        pin = binding['pin']
        assert e['sourceHash'] == pin['sha256'] and local_source.stat().st_size == pin['bytes']
        loc = e['locator']
        assert loc['kind'] == 'byte-range' and 0 <= loc['start'] <= loc['endExclusive'] <= pin['bytes']
        with local_source.open('rb') as stream:
            stream.seek(loc['start'])
            span_digest = hashlib.sha256()
            remaining = loc['endExclusive'] - loc['start']
            while remaining:
                block = stream.read(min(1024 * 1024, remaining))
                assert block, ('Unexpected source end', e['id'])
                span_digest.update(block)
                remaining -= len(block)
        assert span_digest.hexdigest() == e['spanSha256'], ('Directed metadata span changed', e['id'])
        if e['producerLocator'].get('jsonPointers'):
            metadata = json.loads(local_source.read_text())
            for pointer in e['producerLocator']['jsonPointers']:
                value = metadata
                for component in pointer.split('/')[1:]:
                    component = component.replace('~1', '/').replace('~0', '~')
                    value = value[int(component)] if isinstance(value, list) else value[component]
    elif source:
        if source['sha256'] != e['sourceHash']:
            errors.append({'id': e['id'], 'error': 'source-hash-mismatch'})
        loc = e.get('locator', {})
        if loc.get('kind') == 'byte-range' and not (0 <= loc['start'] <= loc['endExclusive'] <= source['bytes']):
            errors.append({'id': e['id'], 'error': 'source-range-invalid'})
        expected_span_hash = e.get('spanSha256', e.get('spanHash'))
        if expected_span_hash and loc.get('kind') == 'byte-range':
            if source['sourcePath'].startswith('app.asar/'):
                original = Path(baseline['extractedDirectory']) / source['sourcePath'][len('app.asar/'):]
            else:
                original = Path(baseline['snapshotApplication']) / source['sourcePath']
            with original.open('rb') as stream:
                stream.seek(loc['start'])
                span = stream.read(loc['endExclusive'] - loc['start'])
            if hashlib.sha256(span).hexdigest() != expected_span_hash:
                errors.append({'id': e['id'], 'error': 'source-span-hash-mismatch'})
    elif e['sourcePath'] in ['analysis/' + baseline['baselineId'] + '/behavior-observations.json', fork_path]:
        local_source = workspace / e['sourcePath']
        if hashlib.sha256(local_source.read_bytes()).hexdigest() != e['sourceHash']:
            errors.append({'id': e['id'], 'error': 'generated-observation-source-hash-mismatch'})
        try:
            value = json.loads(local_source.read_text())
            for component in e['locator']['pointer'].split('/')[1:]:
                component = component.replace('~1', '/').replace('~0', '~')
                value = value[int(component)] if isinstance(value, list) else value[component]
        except (ValueError, KeyError, IndexError, TypeError):
            errors.append({'id': e['id'], 'error': 'generated-observation-json-pointer-invalid'})
    else:
        errors.append({'id': e['id'], 'error': 'source-not-in-frozen-inventory', 'sourcePath': e['sourcePath']})
reference_files = ['features.json', 'modules.json', 'ipc.json', 'module-boundary-proposals.json',
                   'functional-entry-ledger.json', 'functional-entry-reviewed-links.json',
                   'renderer-command-notes.json', 'renderer-command-bridge-helper.json',
                   'embedded-dependency-investigation-actions.json', 'embedded-statsig-recheck.json']
reference_files.extend(static_supplements)
if host_contract_source.exists():
    reference_files.append('host-message-contracts.json')
if chunk_source.exists():
    reference_files.append('chunk-transport.json')
if route_ast:
    reference_files.append('route-contracts.json')
for name in ['route-guard-notes.json', 'project-path-controls.json']:
    if (out / name).exists():
        reference_files.append(name)
if wrapper_contracts:
    reference_files.append('request-wrapper-contracts.json')
if prediction_usage:
    reference_files.append('experimental-prediction-usage.json')
if prediction_gate:
    reference_files.append('prediction-version-gate.json')
nullable_evidence_references = []
for name in reference_files:
    def validate_refs(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ['evidenceId', 'evidenceRef'] or key.endswith('EvidenceId'):
                    if item is None:
                        nullable_evidence_references.append({'file': name, 'field': key})
                    elif item not in ids:
                        errors.append({'file': name, 'error': 'missing-evidence-reference', 'id': item})
                if key in ['evidenceIds', 'evidenceRefs'] or key.endswith('EvidenceIds'):
                    if isinstance(item, dict):
                        assert name == 'app-server-version-origin.json' and key in ['helperEvidenceIds', 'srcHelperEvidenceIds']
                        assert all(isinstance(ref, str) and ref.startswith('APP-SERVER-VERSION-ORIGIN-AST-') for ref in item.values())
                        references = item.values()
                    else:
                        references = item
                    for ref in references:
                        if ref not in ids:
                            errors.append({'file': name, 'error': 'missing-evidence-reference', 'id': ref})
                validate_refs(item)
        elif isinstance(value, list):
            for item in value:
                validate_refs(item)
    validate_refs(json.loads((out / name).read_text()))
validation = {'baselineId': baseline['baselineId'], 'validatedAtUtc': datetime.now(timezone.utc).isoformat(),
              'evidenceCount': len(evidence), 'uniqueEvidenceIds': len(ids), 'errors': errors,
              'reusedEvidence': reused_evidence,
              'modeImportedExternalEvidence': mode_imported_external_evidence,
              'directedSourceEvidenceReuse': [{'key': entry['key'], 'ids': entry['reusedSourceEvidenceIds'],
                    'rule': 'Matching baseline/source/hash/byte locator/span only; semantic claims are not merged.'} for entry in directed_provenance],
              'directedExternalMetadataSources': [{'id': evidence_id, 'path': str(binding['path'].relative_to(workspace)),
                    'sha256': binding['pin']['sha256'], 'bytes': binding['pin']['bytes'],
                    'scope': 'Explicit pinned metadata/provider capture source and original byte span; no archive acquisition or runtime compatibility claim.'}
                    for evidence_id, binding in directed_external_evidence_sources.items()],
              'nullableEvidenceReferences': nullable_evidence_references,
              'scope': 'Evidence IDs, baseline identity, frozen inventory source hashes, byte bounds and supplied span digests, and published references. Earlier merged observations require matching source/claim identity and retain both metadata records; directed source-only reuse matches baseline/source/hash/locator/span and does not merge semantic claims. Null refs remain unresolved. Not semantic or runtime correctness.'}
(out / 'evidence-validation.json').write_text(json.dumps(validation, ensure_ascii=False, indent=2) + '\n')
if errors:
    print(json.dumps(validation, ensure_ascii=False))
    raise SystemExit('Evidence publication failed validation')
(out / 'evidence.jsonl').write_text(''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in evidence))

rea = json.loads((out / 'rea-summary.json').read_text())
run = json.loads((out / 'rea-application-observed.run.json').read_text())
assert run['status'] == 'finished' and run['exitCode'] == 0
assert rea['sourceSha256'] == run['stdoutSha256'] and rea['sourceBytes'] == run['stdoutBytes']
assert rea['evidence']['normalized_result']['root_artifact_sha256'] == baseline['archiveSha256']
stats = rea['evidence']['normalized_result']['statistics']
dep = json.loads((out / 'dependency-summary.json').read_text())
maps = json.loads((out / 'source-maps.json').read_text())['summary']
coverage = json.loads((out / 'feature-coverage.json').read_text())
route_counts = route_ast['summary'] if route_ast else None
protocol = json.loads((out / 'protocol-coverage.json').read_text())
compatibility = json.loads((out / 'protocol-compatibility.json').read_text())
experimental = json.loads((out / 'public-experimental-compatibility.json').read_text())
exported_protocol = json.loads((out / 'exported-protocol-comparison.json').read_text())
backend_commands = json.loads((out / 'command-backend-comparison.json').read_text())
runtime_processes = json.loads((out / 'runtime-process-verification-frozen-match.json').read_text())
owned_storage = json.loads((out / 'runtime-artifacts/owned-task-storage-v2.json').read_text())
owned_reply = json.loads((out / 'runtime-artifacts/owned-task-bounded-reply.json').read_text())
owned_recovery = json.loads((out / 'runtime-artifacts/owned-task-recovery-04.json').read_text())
recovery_processes = json.loads((out / 'runtime-process-verification-recovery-01.json').read_text())
recovery_stop = json.loads((out / 'runtime-artifacts/owned-recovery-runtime-stop.json').read_text())
assert all(record['baselineId'] == baseline['baselineId'] for record in [owned_recovery, recovery_processes, recovery_stop])
assert owned_recovery['status'] == 'observed' and owned_recovery['observations']['newModelTasksSubmitted'] == 0
assert owned_recovery['observations']['restoredReplyExactMatch'] and owned_recovery['observations']['fixtureReadmeUnchanged']
assert owned_recovery['runtimePid'] == recovery_processes['runtimePid'] == recovery_stop['runtimePid']
assert owned_recovery['runtimePid'] != owned_reply['runtimePid'] and owned_recovery['priorRuntimePid'] == owned_reply['runtimePid']
assert recovery_stop['observations']['allKnownOwnedProcessesGone']
for entry in [owned_recovery['processVerification'], owned_recovery['observations']['navigationIdentityEvidence']]:
    assert hashlib.sha256((out / entry['path']).read_bytes()).hexdigest() == entry['sha256']
owned_task = owned_storage['observations']
assert owned_storage['baselineId'] == owned_reply['baselineId'] == baseline['baselineId']
assert owned_task['ownedPromptCount'] == 1 and len(owned_task['taskCompleteEvents']) == 1
assert owned_task['taskCompleteEvents'][0]['turnId'] == owned_task['ownedTurnId']
assert owned_task['taskCompleteEvents'][0]['expectedSentinelPresent']
assert owned_reply['observations']['ownedReplyVisible'] and owned_task['fixtureReadmeUnchanged']
assert owned_reply['observations']['fixtureReadmeUnchanged']
assert experimental['baselineId'] == exported_protocol['baselineId'] == backend_commands['baselineId'] == baseline['baselineId']
assert experimental['status'] == 'complete' and experimental['inputValidation']['publicSchemaFilesHashVerified'] == 764
for run in backend_commands['runs'].values():
    assert hashlib.sha256((out / run['record']).read_bytes()).hexdigest() == run['sha256']
for entry in experimental['evidenceInputs'].values():
    if isinstance(entry, dict) and 'path' in entry and 'sha256' in entry:
        assert hashlib.sha256(Path(entry['path']).read_bytes()).hexdigest() == entry['sha256']
commands = json.loads((out / 'command-protocol-normal-host.json').read_text())
chunk_fixtures = json.loads((out / 'chunk-fixture-summary.json').read_text())
chunk_manifest = json.loads((out / 'chunk-fixture-artifacts.json').read_text())
for name, entry in chunk_manifest['artifacts'].items():
    data = (out / name).read_bytes()
    assert len(data) == entry['bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256'], name
assert hashlib.sha256((workspace / chunk_fixtures['runner']['sourcePath']).read_bytes()).hexdigest() == chunk_fixtures['runner']['sourceSha256']
assert hashlib.sha256((out / commands['rawObservations']['path']).read_bytes()).hexdigest() == commands['rawObservations']['sha256']
assert commands['cliSha256'] == json.loads((out / 'protocol-generation.json').read_text())['cliSha256']
for record in [compatibility, commands, chunk_fixtures, chunk_manifest]:
    assert record['baselineId'] == baseline['baselineId']
features = json.loads((out / 'features.json').read_text())
state = {'baselineId': baseline['baselineId'], 'updatedAtUtc': datetime.now(timezone.utc).isoformat(),
         'status': 'in-progress', 'formalReaRunCompleted': True, 'fullAnalysisCompleted': False,
         'evidenceValidated': len(evidence), 'reaStatistics': stats, 'reaCounts': rea['counts'],
         'featureGroupCandidates': len(features), 'featureDenominatorEstablished': False,
         'runtimeObservationRecords': len(observations), 'confirmedChatGptExclusions': 0,
         'publicProtocolComparison': {'status': 'stable-and-experimental-schema-compared; limited-command-runtime-compared',
                                     'publicCommit': compatibility['publicCommit'],
                                     'directClientCandidates': compatibility['directClientCandidates'],
                                     'experimentalCandidateContracts': experimental['summary'],
                                     'exportedSchemas': exported_protocol['summary'],
                                     'npmSourceCommitBinding': 'unknown'},
         'headlessCommandChecks': {'method': commands['method'], 'count': len(commands['checks']),
                                  'passed': sum(r['passed'] for r in commands['checks']), 'desktopUiVerified': False},
         'chunkPureCodeFixtures': {'count': chunk_fixtures['fixtureCount'], 'assertions': chunk_fixtures['assertionCount'],
                                  'passed': chunk_fixtures['passedFixtures'], 'ipcVerified': False},
         'upstreamComparedRootPackages': dep['counts']['upstreamComparedPackages'],
         'centralDispatcherAst': host_ast['summary'] if host_contract_source.exists() else None,
         'routeAst': route_ast['summary'] if route_ast else None,
         'requestWrapperAst': wrapper_contracts['scanDenominator'] if wrapper_contracts else None,
         'commandBackendComparison': {'contracts': len(backend_commands['comparisons']),
                                      'equal': backend_commands['equalContracts'], 'completeBackendVerified': False},
         'ownedRuntimeProcessVerification': {'runtimePid': runtime_processes['runtimePid'],
                                            'frozenNativeCliMatch': runtime_processes['nativeCliFrozenInventoryMatch']['matches'],
                                            'cliDescendants': len(runtime_processes['requestedCliDescendants']),
                                            'authenticationIsolationVerified': False,
                                            'stoppedAfterOwnedTaskObservation': True},
         'authorizedOwnedDesktopTask': {'submittedTasks': 1, 'completedTasks': 1,
                                        'threadId': owned_task['threadId'], 'turnId': owned_task['ownedTurnId'],
                                        'expectedReplyVisible': True, 'fixtureReadmeUnchanged': True,
                                        'fullFeatureGroupVerified': False},
         'experimentalPredictionClientUsage': prediction_usage['summary'] if prediction_usage else None,
         'submittedTaskRestartRecovery': {'runtimePid': owned_recovery['runtimePid'],
                                          'priorRuntimePid': owned_recovery['priorRuntimePid'],
                                          'initialOwnPromptOccurrences': owned_recovery['observations']['initialOwnPromptOccurrences'],
                                          'reopenedFromObservedOwnedSidebarRow': True,
                                          'restoredReplyExactMatch': True, 'newModelTasksSubmitted': 0,
                                          'fixtureReadmeUnchanged': True, 'knownOwnedProcessesGone': True,
                                          'interruptedExecutionRecoveryVerified': False},
         'forkNegativeProtocolComparison': {'pairedCases': fork_negative['comparison']['pairedCaseDenominator'],
                                            'sameErrorContracts': fork_negative['comparison']['sameErrorContracts'],
                                            'differentErrorContracts': fork_negative['comparison']['differentErrorContracts'],
                                            'actualCliSessions': fork_negative['verification']['actualCliSessions'],
                                            'successfulForks': 0, 'modelTurnRequests': 0,
                                            'predictionSemanticsVerified': False},
         'embeddedDependencyContracts': static_supplements['embedded-dependency-contracts.json']['scope'],
         'menuAndCommandCensus': static_supplements['menu-command-contracts.json']['summary'],
         'embeddedHintDeclarations': static_supplements['merged-candidate-contracts.json']['scope'],
         'runtimeApiScope': static_supplements['runtime-api-contracts.json']['scope'],
         'runtimeFuseObservation': {'path': 'runtime-fuse-observation.json', 'scope': runtime_fuses['scope'],
                                    'observedWire': runtime_fuses['conclusions']['observedWire'],
                                    'runtimeEnforcementVerified': False, 'actualVersionsAndAbiVerified': False},
         'runtimeNativeAccessors': {'path': 'runtime-native-accessors.json', 'scope': runtime_native['scope'],
                                    'selectedFuseReadBindingsVerified': True, 'nodeApiVersionStaticallyEncoded': 10,
                                    'startupExecutionAndAbiVerified': False},
         'runtimeNodeVersion': {'path': 'runtime-node-version.json', 'summary': runtime_node['summary'],
                                'staticGetterVersion': runtime_node['versionStructure']['encodedVersion'],
                                'staticGetterRelease': runtime_node['versionStructure']['release'],
                                'observedExecutedNodeVersion': runtime_node['conclusions']['observedExecutedNodeVersion'],
                                'legacyNativeAbiVerified': False},
         'runtimeAdapterOptions': {'path': 'runtime-adapter-options.json', 'scope': runtime_options['scope'],
                                   'status': runtime_options['status'], 'replacementProven': False},
         'runtimeDistribution': {'path': 'runtime-distribution.json', 'scope': runtime_distribution['scope'],
                                 'status': runtime_distribution['status'], 'independentOwlDistributionEstablished': False,
                                 'clientArchiveAcquiredOrCorrespondenceVerified': False},
         'reviewedMaintenanceBoundaryProposals': structure_proposals['scope'],
         'appHostMaintenanceProposals': {'path': 'app-host-maintenance.json', 'scope': app_host_maintenance['scope'],
                                        'newDesignProposalsOnly': True, 'fullDirectoryRecoveryOrMigrationVerified': False},
         'functionalEntryLedger': {'path': 'functional-entry-ledger.json', **entry_ledger['summary']},
         'chatgptCandidateModeBoundary': {'path': 'chatgpt-candidate-module-contracts.json',
                                        **mode_contract['summary'],
                                        'independentValidationStatus': mode_validation['status'],
                                        'allValidationLayersPassed': mode_validation['allLayersPassed']},
         'requestFacadeContinuation': {'path': 'request-facade-contract.json',
                                       'scope': request_facade['denominator'],
                                       'concreteTransportVerified': False, 'runtimeAndModeVerified': False},
         'projectLocalFolderPredicate': {'path': 'project-local-folder-predicate.json',
                                        **project_predicate['summary'], 'originalOuterBindingAndRuntimeVerified': False},
         'projectPermissionPredicate': {'path': 'project-permission.json', 'scope': project_permission['scope'],
                                        'summary': project_permission['summary'],
                                        'originalOuterBindingRuntimeAndModeVerified': False},
         'httpServiceOrigin': {'path': 'http-service-origin.json', 'scope': http_origin['scope'],
                               'concreteHostTransportRuntimeAndModeVerified': False},
         'preloadAppHostBridge': {'path': 'preload-app-host.json', 'scope': preload_app_host['scope'],
                                  'crossProcessDeliveryAndModeVerified': False},
         'hostHttpService': {'path': 'host-http-service.json', 'scope': host_http_service['scope'],
                             'actualHttpRequestAndModeVerified': False},
         'appHostContextAndTrust': {'path': 'app-host-context.json', 'scope': app_host_context['scope'],
                                    'dynamicRegistryInstanceRuntimeAndModeVerified': False},
         'applicationNetwork': {'path': 'application-network.json', 'scope': application_network['scope'],
                                'nativeApiCompatibilityRuntimeAndModeVerified': False},
         'projectFeatureCondition': {'path': 'project-feature-condition.json', 'scope': project_feature_condition['scope'],
                                     'originalBindingDynamicStateRuntimeAndModeVerified': False},
         'appServerVersionOrigin': {'path': 'app-server-version-origin.json',
                                    'selection': app_server_version_origin['selection'],
                                    'status': app_server_version_origin['status'],
                                    'actualRunningInstanceVersionVerified': False,
                                    'installedVersionAndInitializedVersionMerged': False},
         'threadTurnFeatureContracts': {'path': 'thread-turn-feature-contracts.json',
                                        'denominators': thread_turn_catalog['denominators'],
                                        'authoredCatalogRecords': 58, 'inheritedEvidenceRecords': 172,
                                        'globalTargetSourceEvidenceAdded': 0,
                                        'scope': thread_turn_provenance['scope']},
         'requestEntryReconciliation': {'path': 'request-entry-reconciliation.json',
                                        'summary': request_entry_reconciliation['summary'],
                                        'globalTargetSourceEvidenceAdded': 0,
                                        'functionalLedgerChanged': False,
                                        'scope': request_entry_reconciliation_provenance['scope']},
         'scopedStaticCatalogs': scoped_static_catalogs,
         'staticBoundaryCatalogs': static_boundaries,
         'catalogSupplementCatalogs': catalog_supplements,
         'scopedCatalogNamingClarification': {
             'source': 'raw/scoped-catalogs/approval-entry-contracts/scoped-ast.json',
             'sourceSha256': '41bb82414aa64f267b1f9699c810e06bec303d9dce0d29429cbb2d504e0cc8a8',
             'jsonPointer': '/files/2/selectedUnits/4/ancestors',
             'initializerFunctionName': 'Ofn', 'selectedClassExpressionName': None,
             'classByteRange': [3199539, 3255806],
             'originalModuleBindingReview': 'turn-notification-bindings-summary.md',
             'scope': 'Ofn labels the enclosing initializer function in the saved AST, not a named class. Original catalog labels are preserved. A separate Program binding review proves the selected Dfn assignment; runtime receiver remains unverified.'},
         'analysisCriteriaAudit': {'path': 'criteria-audit.json', 'publicationId': criteria_provenance['publicationId'],
                                   'counts': criteria_audit['counts'],
                                   'scope': 'Frozen historical publication and input snapshots only; later supplements are outside this audit.'},
         'analysisCriteriaAuditRefresh': {'path': 'current-completion-audit.json',
                                         'auditedPublicationId': completion_audit['publicationRun'],
                                         'counts': completion_audit['counts'], 'selectedInputSnapshots': 63,
                                         'matchedSelectedPublicationPins': 25, 'fullAnalysisCompleted': False,
                                         'scope': completion_provenance['scope']},
         'predictionVersionGate': {'minimumVersion': prediction_gate['gateBindings']['feature']['minimumVersion'],
                                   'staticCases': prediction_gate['staticCases'],
                                   'conclusion': prediction_gate['conclusion']} if prediction_gate else None,
         'pending': ['deep per-feature call chains and mode guards', 'full feature census',
                     'actual callsite handling and model/approval/recovery backend runtime comparison', 'native/Owl/private interfaces',
                     'remaining desktop task paths, failures, cancellation and interrupted-execution restart recovery',
                     'dependency version provenance and upstream modifications']}
recovery_delivery_path = out / 'recovery-decision-catalogs-provenance.json'
recovery_delivery_note = ''
if recovery_delivery_path.exists():
    recovery_delivery_raw = recovery_delivery_path.read_bytes()
    recovery_delivery = json.loads(recovery_delivery_raw)
    assert recovery_delivery['baselineId'] == baseline['baselineId']
    assert recovery_delivery['records'] == 138 and recovery_delivery['globalRecordsAdded'] == 0
    state['recoveryDecisionCatalogs'] = {
        'path': recovery_delivery_path.name,
        'bytes': len(recovery_delivery_raw),
        'sha256': hashlib.sha256(recovery_delivery_raw).hexdigest(),
        'catalogs': [{'catalogId': c['catalogId'], 'records': c['records']}
                     for c in recovery_delivery['catalogs']],
        'scope': recovery_delivery['scope'], 'globalRecordsAdded': 0,
        'runtimeConfirmedByDelivery': 0,
    }
    recovery_delivery_note = '''[旧设置候选对账](settings-entry-reconciliation-summary.md)另保存107条原记录，53个资产候选与50个route支持实例按原ID、哈希和字节定位对齐；功能、模式与运行状态未提升。
[Sentry来源与导入边界](sentry-upstream-identity-contracts-summary.md)另保存31条原记录，确认官方core候选的两个所选公开helper入口；getSentryCarrier没有公开root或carrier子路径，完整修改状态及基线安装锁仍未知。
两批选定冻结元数据及实际复制字节见[独立交付索引](recovery-decision-catalogs-provenance.json)；138条记录没有改写全局journal或功能分母。交付未重跑原程序分析，也没有新增目标或模型执行。
'''
submission_delivery_path = out / 'submission-host-instance-provenance.json'
submission_delivery_note = ''
if submission_delivery_path.exists():
    submission_delivery_raw = submission_delivery_path.read_bytes()
    submission_delivery = json.loads(submission_delivery_raw)
    submission_guidance_path = out / 'submission-recovery-guidance.json'
    submission_guidance_raw = submission_guidance_path.read_bytes()
    submission_guidance = json.loads(submission_guidance_raw)
    assert submission_guidance['baselineId'] == baseline['baselineId']
    assert submission_delivery['records'] == 30 and submission_delivery['globalRecordsAdded'] == 0
    assert submission_delivery['runtimeConfirmedByDelivery'] == 0
    assert len(submission_guidance['modules']) == 5 and len(submission_guidance['scenarios']) == 7
    state['submissionProviderCatalog'] = {
        'path': submission_delivery_path.name,
        'bytes': len(submission_delivery_raw),
        'sha256': hashlib.sha256(submission_delivery_raw).hexdigest(),
        'records': 30,
        'guidance': {'path': submission_guidance_path.name, 'bytes': len(submission_guidance_raw),
                     'sha256': hashlib.sha256(submission_guidance_raw).hexdigest()},
        'moduleProposals': 5, 'behaviorScenarios': 7,
        'scope': 'Conditional static provider composition and recovery proposals; actual runtime instance unresolved.',
        'globalRecordsAdded': 0, 'runtimeConfirmedByDelivery': 0,
    }
    submission_delivery_note = '''[提交 provider 与 host 实例](submission-host-instance-summary.md)另保存30条限定记录、19个完整单元及10条导入／导出路由。内部分支条件连接OMc、N3 manager、MessageChannel与coordinator façade；X3自身没有forHost，host-provided分支尚未关联Dfn。
KI在provider为unavailable且host未登记时仍允许primary尝试，已登记则跳过；实际scope、host、初始化顺序、RPC transport送达与接收实例仍未知。
[维护职责与行为场景](submission-recovery-guidance.md)给出5个职责建议和7个场景；均不是功能分母或已实现客户端。选定冻结元数据见[交付索引](submission-host-instance-provenance.json)，实际复制未增加运行或模型任务；唯一已完成样例不能覆盖执行中取消或中断恢复。
'''
settings_and_rpc_note = ''
settings_and_rpc_path = out / 'settings-and-rpc-delivery-provenance.json'
if settings_and_rpc_path.exists():
    settings_and_rpc_raw = settings_and_rpc_path.read_bytes()
    settings_and_rpc = json.loads(settings_and_rpc_raw)
    assert settings_and_rpc['baselineId'] == baseline['baselineId']
    assert settings_and_rpc['records'] == 153 and settings_and_rpc['globalRecordsAdded'] == 0
    assert settings_and_rpc['runtimeRunsAdded'] == 0
    state['settingsAndRpcCatalogs'] = {
        'path': settings_and_rpc_path.name, 'bytes': len(settings_and_rpc_raw),
        'sha256': hashlib.sha256(settings_and_rpc_raw).hexdigest(),
        'records': 153, 'catalogs': [{'catalogId': c['catalogId'], 'records': c['records']}
                                   for c in settings_and_rpc['catalogs']],
        'scope': settings_and_rpc['scope'], 'globalRecordsAdded': 0, 'runtimeRunsAdded': 0,
    }
    settings_review_path = out / 'settings-and-rpc-delivery-review-provenance.json'
    if settings_review_path.exists():
        settings_review_raw = settings_review_path.read_bytes()
        settings_review = json.loads(settings_review_raw)
        assert settings_review['baselineId'] == baseline['baselineId']
        assert settings_review['reviewedDelivery']['sha256'] == hashlib.sha256(settings_and_rpc_raw).hexdigest()
        assert settings_review['checks'] == 2664 and settings_review['errors'] == []
        state['settingsAndRpcCatalogs']['deliveryReview'] = {
            'path': settings_review_path.name, 'bytes': len(settings_review_raw),
            'sha256': hashlib.sha256(settings_review_raw).hexdigest(),
            'checks': 2664, 'scope': settings_review['scope'],
        }
    settings_and_rpc_note = '''[设置页面、RPC 与 local host](settings-and-rpc-summary.md)另交付153条限定证据：Agent65、General39、RPC24、local host25。General/family复用同一factory，32操作／展示；Agent六项配置共用写入函数并保留project callback、校验与保存链。
RPC能力引用、根session关闭与普通引用释放分别记录；N3仅local创建候选，X3注册替换、删除与三个lookup caller保留身份和生命周期条件。四批只支持所选静态范围，实际实例、双端送达、持久化和完整功能分母仍未证明。
原schema、ID、sourceHash与locator按原字节保留，各author/peer范围不相加。实际复制与失败历史见[独立交付索引](settings-and-rpc-delivery-provenance.json)，没有新增运行或模型任务，也没有改写旧全局journal及模式排除。
[交付复核](settings-and-rpc-delivery-peer-review.md)另有2664项限定检查通过，覆盖交付逻辑与64份拷贝／别名；不新增General源码语义的独立验证。
'''
capnweb_candidate_note = ''
capnweb_candidate_path = out / 'capnweb-upstream-candidate.json'
if capnweb_candidate_path.exists():
    capnweb_candidate_raw = capnweb_candidate_path.read_bytes()
    capnweb_candidate = json.loads(capnweb_candidate_raw)
    assert capnweb_candidate['baselineId'] == baseline['baselineId']
    assert capnweb_candidate['counts']['records'] == 14
    assert capnweb_candidate['counts']['interfaceGroups'] == 4
    assert capnweb_candidate['counts']['memberShapes'] == 18
    assert capnweb_candidate['globalRecordsAdded'] == capnweb_candidate['runtimeRunsAdded'] == 0
    state['capnwebUpstreamCandidate'] = {
        'path': capnweb_candidate_path.name, 'bytes': len(capnweb_candidate_raw),
        'sha256': hashlib.sha256(capnweb_candidate_raw).hexdigest(),
        'records': 14, 'interfaceGroups': 4, 'memberShapes': 18,
        'versionCandidate': '0.11.1', 'installedVersion': 'unknown',
        'fullEquivalence': 'unknown', 'modifiedStatus': 'unknown',
        'scope': 'Official candidate and limited name/parameter-count correspondences only.',
        'globalRecordsAdded': 0, 'runtimeRunsAdded': 0,
    }
    capnweb_review_path = out / 'capnweb-upstream-candidate-review-provenance.json'
    if capnweb_review_path.exists():
        capnweb_review_raw = capnweb_review_path.read_bytes()
        capnweb_review = json.loads(capnweb_review_raw)
        assert capnweb_review['baselineId'] == baseline['baselineId']
        assert capnweb_review['reviewedCandidate']['sha256'] == hashlib.sha256(capnweb_candidate_raw).hexdigest()
        assert capnweb_review['independentReview']['checks'] == 334 and capnweb_review['independentReview']['errors'] == []
        state['capnwebUpstreamCandidate']['independentReview'] = {
            'path': capnweb_review_path.name, 'bytes': len(capnweb_review_raw),
            'sha256': hashlib.sha256(capnweb_review_raw).hexdigest(),
            'checks': 334, 'scope': capnweb_review['scope'],
        }
    capnweb_candidate_note = '''[capnweb 官方候选](capnweb-upstream-candidate-summary.md)另保存14条记录。官方0.11.1归档通过声明的SRI与SHA-1；4组18个成员只确认名称与声明参数个数相符，工厂另有3个有限调用形状对应。
这些对应支持公开root包导入候选；基线实际安装锁、完整修改状态、wire及能力释放等价性仍未知。第三方实现与source-map内容保留本地，第一方manager／coordinator、host／scope和生命周期职责需单独恢复。该批没有增加运行或模型任务，也没有改写全局journal及功能分母。
[独立复核](capnweb-upstream-candidate-peer-review.md)已完成334项限定检查，覆盖冻结元数据及18个成员形状；归档SRI仍为保存的作者观察，候选原始pending字段按原字节保留。
'''
requirements_audit_note = ''
requirements_audit_path = out / 'analysis-requirements-current-audit-provenance.json'
if requirements_audit_path.exists():
    requirements_audit_raw = requirements_audit_path.read_bytes()
    requirements_audit = json.loads(requirements_audit_raw)
    assert requirements_audit['baselineId'] == baseline['baselineId']
    assert requirements_audit['checks'] == 194 and requirements_audit['fullAnalysisCompleted'] is False
    state['analysisRequirementsCurrentAudit'] = {
        'path': requirements_audit_path.name, 'bytes': len(requirements_audit_raw),
        'sha256': hashlib.sha256(requirements_audit_raw).hexdigest(),
        'checks': 194, 'completionCriteria': 9, 'phases': 6, 'requirementItems': 39,
        'fullAnalysisCompleted': False, 'scope': requirements_audit['scope'],
    }
    requirements_audit_note = '''[当前需求审计](analysis-requirements-current-audit.md)另按原计划9项完成标准、6阶段及39条子要求核对包含153条补充证据的固定读者快照。4项记录／范围义务满足、5项部分；阶段1输入交付齐备，其余5阶段部分。194项元数据检查只证明所列来源与范围，完整分析仍未完成。
下一步是跨catalog登记与逐操作职责、状态、外部边界和具体验收场景，并关闭会改变工程方案的运行时与后台门槛；该审计不追认其固定输入之后的新调查。
'''
from contract_reader_context import build_context
bounded_contract_state, bounded_contract_note, _ = build_context(out, baseline['baselineId'])
state.update(bounded_contract_state)
(out / 'analysis-state.json').write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
rows = []
for o in observations:
    result = json.dumps(o.get('observations', {key: o[key] for key in ['present', 'controls', 'structuralCounts'] if key in o}),
                        ensure_ascii=False).replace('|', '\\|').replace('\n', ' ')
    rows.append(f"| {o['action']} | {o['status']} | {result} |")
behavior = f'''# 实际行为核对记录

基线：`{baseline['baselineId']}`。这是有限 UI 观察、一次未提交草稿重启验证及一个获授权的只读桌面任务，不能代表整个功能组通过。

测试应用为冻结包的独立运行副本，使用短路径 userData 和 CODEX_HOME；未复制个人凭据，但应用自动呈现现有账户状态。认证来源仍待追踪。仅按用户明确授权提交了一个读取新建合成 README 的模型任务；保存的观察限定于自有测试资料、固定控件与该任务，不读取个人历史或凭据。启动命令与 PID 由本地 sessions 记录。

| 动作 | 记录状态 | 实际观察 |
| --- | --- | --- |
{chr(10).join(rows)}

`settings` 快捷键探测未取得设置页存在的充分证据；随后 `settings-menu` 通过菜单观察到“设置／常规”。这两个记录不能合并成“快捷键验证通过”。

`draft-fill` 与重启后的 `draft-read` 均匹配同一专用草稿，支持在这些条件下未提交草稿可恢复。唯一已完成任务也已在后续重启中重新打开，详见下节；具体存储层和执行中断恢复仍待验证。

REA 6.4.0 的 Electron 被动观察接口排除了 `app://` 目标；上述 UI 证据来自 Playwright/CDP，方法已单独标记。原始小型观察已汇总到 `behavior-observations.json`；局部截图在本地 runtime-artifacts 中，哈希列于记录。

后续需继续验证其他本地任务路径、错误、取消、审批、文件变更、终端和执行中断恢复，并将每次运行关联到具体功能、IPC 与 app-server 契约。云端、远程主机、平台和账户条件分别登记，不以菜单存在代替执行验证；额外模型任务需另获授权。

## 独立命令协议验证

使用冻结随包 CLI 的实际 app-server stdio 接口，在专用目录运行 printf、false 和可终止的 sleep，未提交模型任务。`command-protocol-normal-host.json` 的 5 项检查均通过：initialize、退出 0 的输出、退出 1、空 command 参数拒绝、流式通知后 terminate。实际 CLI 返回与记录哈希保存在 raw/command-protocol/normal-host/。

首次在代理 sandbox 中运行命令被系统 sandbox-exec 拒绝（exit 71），失败保留于 `command-protocol-sandboxed.json`。随后正常本机环境复验仍使用 readOnly/no-network 策略。后者证明上述独立命令路径，并不证明桌面终端 PTY、模型任务、审批、会话恢复或公开 CLI 兼容。

冻结和公开 npm CLI 随后分别在新建专用 HOME/CODEX_HOME 中通过相同五项检查，保存输出、参数错误码和取消结果全部相同。见 [独立命令后端比较](command-backend-comparison.md)。initialize 仅比较返回字段名；此结果不代表模型、审批或完整后端兼容。公开运行保存了生成记录和验证脚本的字节快照；较早公开运行的生成记录后来补充元数据，其旧哈希不能完整复核，保留历史记录并使用新 run 作为比较依据。

## 自有实例进程与项目设置

`runtime-process-verification-frozen-match.json` 确认观察时自有实例有 3 个随包 native CLI 子进程，其可执行字节与冻结清单一致，并观察到专用 profile 的打开文件。stdin/stdout 的 Unix socket 类型不能确定完整协议或每个进程角色；最终环境、认证来源与存储是否完全隔离仍未验证。

样例核对结束后，只向经路径核对的自有主进程发送 SIGTERM；随后主 PID 和上述三个 CLI PID 均不再匹配存活进程。见 owned-runtime-stop.json。这次清理不是已提交会话重启恢复测试。

项目设置经静态确认的 host project service 调用，使用新建 UUID 临时目录，返回的 rootPaths 与该目录相同，界面出现专用项目名。该过程不是项目创建 UI 流程的验收。文件夹信任对话探测未匹配任何对话，但先前设置调用已完成；这不能作为信任对话验证通过。静态来源见 project-path-controls.json。目录新建也不单独证明无历史 hint；测试以此前不存在的随机路径没有历史 cwd/hint/canonical alias 为前提。

点击信任按钮曾被自动审批拒绝，未执行；后续只读核对确认该动作无需继续。模型任务首次提交也被自动审批拒绝；用户随后明确允许这一个样例任务，才执行一次提交。没有通过其他接口绕过，也没有重复提交。

## 唯一获授权的桌面样例任务

任务 `{owned_task['threadId']}` 的自有提示在 rollout 中出现一次；UserMessage 的 item_completed 将其关联到 turn `{owned_task['ownedTurnId']}`，同 turn 的 task_started 与 task_complete 各一个。完成回复包含 `Sentinel: CCODEX_OWNED_FIXTURE_01`，界面的有界 MarkdownRoot 回复也可见，README 的 SHA256 保持不变。见 owned-task-storage-v2.json 与 owned-task-bounded-reply.json。

提交后一秒的 submissionIndicated=false 是早期采样，不能据此重发。初版 owned-task-storage.json 只识别旧 user_message 格式，ownedPromptRecorded=false 是观察器遗漏；v2 改用实际 response_item/message 和同 turn 事件复核，旧记录保留。普通 mode=ro SQLite 读取两次打开失败；v2 只在无 WAL 且查询前后文件 digest 相同的条件下采用 immutable 只读查询，它不是原子的实时数据库快照。

界面预期文本本身不证明作者身份或任务完成；这里由自有提示、同 turn 完成事件和预期短回复共同限定证据范围。三个 exec orchestration 工具调用经自有 rollout 窄复核：两次仅发现工具元数据，一次调用 Node fs.readFile 读取自有 README；没有使用 shell 命令工具。记录只保存输入 hash、API 分类和匹配输出计数，见 owned-task-tool-review.json。该任务仅验证这个 README 只读路径，不能扩大为写入、审批、取消、PTY、云端任务或全部功能通过。

## 冻结纯代码验证

codec/assembler 的 {chunk_fixtures['fixtureCount']} 组场景、{chunk_fixtures['assertionCount']} 条断言全部通过，完整来源范围和实际结果见 [纯代码报告](chunk-fixture-report.md)。它与上面的 {len(observations)} 条运行观察和 5 项命令检查分别统计；没有据此把整个 IPC 或功能组改为通过。

## 已完成样例重启恢复

原 PID {owned_reply['runtimePid']} 停止后，用相同专用 profile 与 CODEX_HOME 启动新 PID {owned_recovery['runtimePid']}。新实例的随包 native CLI 与冻结清单哈希相同，见 runtime-process-verification-recovery-01.json。

启动观察中自有提示和预期回复的匹配数均为 0，因此没有证明自动恢复当前会话。专用项目内实际存在一行已知样例，data-app-action-sidebar-thread-id 为 local: 加样例 UUID；以这一观察身份及唯一项目容器定位后点击，原提示出现一次，回复与之前核对的 MarkdownRoot 文本精确匹配，README 哈希不变，新增模型任务为 0。见 runtime-artifacts/owned-task-recovery-04.json。

此前 recovery-01 没找到 UUID 链接，recovery-02 用原 UUID 未匹配带 local: 前缀的行，recovery-03 全局匹配到两行而拒绝点击；这些观察器失败均保留。最终只在已观察到的专用项目容器内选择唯一行，没有猜测路由或重新发送任务。该结果支持此已完成任务可重新打开，不验证执行中断、待审批、错误或取消状态的恢复。结束后仅停止经路径核对的自有实例，主 PID 和已记录 CLI PID 均已消失，见 owned-recovery-runtime-stop.json。

## thread/fork 参数负例比较

两后端各用 experimentalApi=true/false 的新 HOME/CODEX_HOME 会话，共 4 个实际 CLI 会话、32 个 thread/fork 请求。OS sandbox 禁止网络并限制写入自有目录；没有模型请求或成功 fork。16 组配对负例中 13 个错误契约相同、3 个不同，完整响应定位见 [负例比较](fork-negative-protocol-comparison.md)。

冻结后端识别 experimentalPredictionMode，错误字符串触发布尔类型拒绝，true 在无实验 capability 时被门控。公开 npm 后端未在 schema 声明该字段，true/false/错误字符串均与未知字段对照到达同一缺失 rollout lookup，表现符合本负例路径未识别或忽略。已知 ephemeral 错误类型及 beforeTurnId capability 门控作为正控制均成立。这不能证明公开后端支持预测或成功 fork 行为相同；版本门槛通过也不能消除此差异。
'''
(out / 'behavior-checks.md').write_text(behavior)
report = f'''# Codex 客户端逆向分析阶段报告

状态：分析进行中。固定基线 `{baseline['baselineId']}`，版本 `{baseline['application']['CFBundleShortVersionString']}`，构建 `{baseline['application']['CFBundleVersion']}`。本报告未宣称分析完成或客户端已重建。

## 已取得的证据

REA 6.4.0 正式运行已结束，退出码 0，原始 Evidence `{rea['evidence']['evidence_id']}`。完整输出 {rea['sourceBytes']:,} 字节；摘要流式读取了全部 JSON，并核对输出哈希和基线 ASAR 哈希。

| 范围 | 实际覆盖 | 限制 |
| --- | --- | --- |
| ASAR 文件盘点 | {baseline['archiveMemberCount']:,} 个成员 | 盘点不等于功能分析 |
| REA 源码输入 | {stats['relevant_files']:,} 个；JS 解析 {stats['parsed_javascript_files']:,} 个；解析失败 {stats['parse_failures']} | 结构图 partial，语义图 partial 且 truncated |
| 结构图 | {rea['counts']['graph.nodes']:,} 节点，{rea['counts']['graph.edges']:,} 边 | 静态关系，不证明运行可达 |
| 语义图 | {rea['counts']['semantic_graph.nodes']:,} 节点，{rea['counts']['semantic_graph.relations']:,} 关系，{rea['counts']['semantic_graph.unknowns']:,} unknown 记录 | 100000 节点上限和结果预算；省略总数未知 |
| Source map | {maps['scannedFiles']:,}/{maps['eligibleFiles']:,} 文件；{maps['confirmedDirectiveComments']:,} 条真实注释 | 冻结清单所列扩展中，所有目标 map 缺失；外置、内联和 sourcesContent 均为 0 |
| 依赖 | 78 根声明；49 ASAR、58 外部安装包 occurrence；202 个合并清单条目 | 仅 6 根声明有根路径安装版本；模式及其余包的修改状态仍 unknown |
| 精确版本上游比较 | {dep['counts']['upstreamComparedPackages']} 个根包；共同源码 69/71 相同 | node-pty 两个 Windows JS 不同；原生来源、ABI 和运行未验证 |
| 内嵌依赖定向调查 | 两批累计 255 条证据、17/17 既有版本声明绑定；9 条首批契约与 2 条应用适配器候选 | 每 hint 的来源、处理建议与五项调查动作已登记；实际上游身份/修改与运行仍未验证 |
| 原生和 Wasm | 66 个 .node、42 个 Wasm 工件 | 含其他平台；存在不证明能从源码构建 |
| 桌面运行时 API | 10 核心文件、90,246 call/new；1,242 绑定调用、241 member、229 callee paths | 11,512 条来源证据；4,293 名称候选与 34 预算触顶保留未知；替换与 ABI 未验证 |
| 运行时方案 | 3候选路线、4优先特殊边界、6共通条件 | 9个输入及177次引用已核对；未来验证尚未执行，未证明取得性或替代成功 |
| 补充功能扫描 | {coverage['lexicallyScannedFiles']}/{coverage['nonNodeModulesJsDiscovered']} 非 node_modules JS 候选文件 | 438 份是候选及混合 bundle，其他大量资源尚未逐一归属 |
| 功能候选 | {len(features)} 组：20 codex、9 shared、2 chatgpt、5 unknown（模式均为推断） | 功能总分母尚未建立；确认排除 0 |
| 入口与接口 | 25 显式通道、143 顶层消息 type + 28 嵌套命令、53 设置项 | 主 switch 143/143 有完整 AST 范围；其他 handlers 与功能可达性仍待核对 |
| 菜单与命令 AST | 31 原生 API、130 item schema + 26 generator options；174 command schema 源位置、182 固定实例；411 个稳定契约 ID | 6,806 条证据；原生注册、元数据、选定 renderer hook 分开统计，模式与运行未验证 |
| 入口台账 | 868 主类、100 辅助类；另有176支持节点和337未解析候选 | 1,088 条结构关系；同handler来源涉及41入口；已确认业务操作等价与功能映射均为0，功能总分母仍unknown |
| ChatGPT候选模式续查 | 9完整发布模块、704,298字节；1,841函数、9,592 call/new、24边界形式候选 | 23,011新增来源范围；9模块模式unknown，确认排除0；候选形式、源码复用和运行可达分别判断 |
| 路由 AST | {route_counts['actualRouteConstructionCalls']} 个实际 Route 构造、{route_counts['pathBearingCalls']} 有 path、{route_counts['staticallyResolvedPathCalls']} 固定 path、{route_counts['dynamicPathCalls']} 动态 path；模板展开 {route_counts['staticallyResolvedMapInstances']} 个实例 | 两个目标文件解析成功；仅静态构造和转换可达，模式与实际运行未确认 |
| app-server 与请求 wrapper | 91 直接调用位置，52 方法；337 wrapper 候选已关联 AST，其中 242 接收方未确认 | 43 个公开稳定请求契约相同，另 9 个实验候选 request/params/response 共 27 项相同；调用身份及运行仍有缺口 |
| 公开 CLI 导出比较 | 两套各 764 个模式限定 schema 文件；466 个 method variant 中 455 相同、11 不同 | 方法集合相同；experimental thread/fork、5 类通知和 v2 路径引用存在差异；源码 commit 绑定 unknown |
| 运行观察记录 | {len(observations)} 条有限 UI／项目设置观察；专用草稿重启后保留；一个授权 README 桌面任务完成 | 项目 API 设置与 UI 创建分别判断；已完成样例重启后可重新打开；其他任务路径、失败、取消与执行中断恢复尚未验证 |
| 独立命令协议 | 随包 app-server 的 5/5 检查通过 | 不覆盖模型任务、桌面 PTY、审批或公开 CLI |
| 两个后端命令比较 | 两者各 5/5 检查通过；保存的 5 个契约观察相同 | initialize 只比较字段名；不代表完整后端兼容 |
| thread/fork 负例 | 4 会话、32 请求、16 配对：13 错误契约相同、3 不同 | 无模型请求、无成功 fork；仅验证参数解码与门控，预测语义仍未知 |
| 纯代码行为 | codec/assembler 的 {chunk_fixtures['fixtureCount']}/{chunk_fixtures['fixtureCount']} 场景、{chunk_fixtures['assertionCount']} 断言通过 | 不覆盖真实 IPC 投递和 sender 生命周期 |
| 证据校验 | {len(evidence):,} 条；ID、输入 hash、定位范围、引用通过 | 机械校验不等于结论全部正确 |

## 已确认的架构线索

Owl 的 [运行时契约调查](runtime-api-summary.md) 给出完整 bootstrap guard：process.versions.electron 非空且 app.showTaskManager 不是函数时，抛出要求 Owl 外壳、拒绝 stock Electron 的错误。另有私有 update policy binding、Node 网络与 IPC 策略、定制 scoped user-agent switches，以及 WebContents-like adoption lease 的注入接口。普通 Electron 的部分公开表面只能支撑适配候选，229 条路径的整体替换结论均为 unknown；删除启动 guard 不会提供这些契约。

[运行时方案](runtime-adapter-options.md) 分别提出独立固定Owl、普通Electron加第一方适配器、其他shell重写三条调查路线。当前建议先核对Owl的独立取得与版本来源，同时定义自有能力接口；普通Electron的功能片段仅为中间技术验证，完整Codex目标保持。四个特殊边界、六项共通条件及全量验收缺口仍保留，所有路线均未证明替代成功。

[运行时取得来源补充](runtime-distribution-summary.md)核对声明的Owl archive标识、缺失构建输入及公开分发元数据。
公开x64更新XML的完整24,046字节包含10项，其中有基线版本/build；首次部分响应和超时仍保留。
该渠道提供整客户端线索，archive未下载、验算或验签，与冻结ASAR字节对应仍未知。
普通Electron和Sparkle的公开版本、源码/许可线索及发布摘要只提供依赖候选；本轮未取得二进制或验证替代兼容。
独立Owl archive/源码/许可/types/构建输入、ABI与升级渠道仍未知，GAP-08保持open。29条新增元数据证据与47个输入pin不构成完整客户端构建或运行证明。

冻结包的运行时元数据自报 Owl，Framework 与 CDP 观察的 Chromium 版本为 `155.0.8059.40`；它不证明 Owl 的 Node、Electron 兼容版本或原生 ABI。根 devDependency `electron: 42.3.0` 不能作为实际运行时版本依据。随包 CLI 为 `0.162.0-alpha.17.2`。主入口链路如下：

```mermaid
flowchart LR
  Early[early-bootstrap] --> Bootstrap[bootstrap] --> Main[main]
  HTML[webview index.html] --> Index[renderer index]
  Index --> RPC[rpc / app-main] --> App[app-initial / React]
  App <--> Preload[preload electronBridge]
  Preload <--> Main
  App <--> Port[MessagePort app-host RPC]
  Port <--> Main
  Main <--> Server[app-server connection]
  Main <--> Worker[worker manager]
```

图为源码证据中的关系，不表示每条边都完成运行验证；证据见 boundaries.json 与 ipc.json。部分 FEATURE 定位只支撑函数名或通道存在，完整契约需更大来源范围。chunk-transport.json 已补充 host-to-view 的 tokenizer、逐块 ack、排队与 renderer assembler 完整函数证据；异常恢复仍待验证。worker 通道计算 workerId；MessagePort RPC 是另一条服务边界。后续恢复需保留这些契约、生命周期和副作用。

主 `MMe.handleMessage` 的顶层 `switch(t.type)` 经 AST 核对为 143 个 case、112 个处理组、285 个调用点。原 171 字面候选中多出的 28 个全部来自 `browser-sidebar-command` 内的 `t.command.type` 子分发。完整范围和绑定分类见 host-message-contracts.json；655 条证据范围校验通过。此中央分发器的 33 个 effective-noop 标签可能由前置处理或其他边界处理，不能作为功能缺失或可剥离证据；模式和实际行为均未确认。

路由 AST 以 shared 中真实 Route/Navigate/createRoutesFromElements 导出身份定位调用，而不是扫描所有 JSX path 属性。{route_counts['actualRouteConstructionCalls']} 处构造都在 app-initial，目标 app-primary 中为 0；{route_counts['pathlessCalls']} 个无 path（包含 {route_counts['indexCalls']} 个 index），{route_counts['nonRouteJSXPathProps']} 个非 Route path 属性与 {route_counts['navigationTargetCandidates']} 个 Navigate 目标分别登记。动态模板不是独立源码构造次数，{route_counts['staticallyResolvedPathCalls']} 个固定 path 与 {route_counts['staticallyResolvedMapInstances']} 个展开实例不可直接相加为功能数。详见 route-contract-summary.md、route-contracts.json 和 route-guard-notes.md。

sendRequest 的带作用域 AST 清单覆盖 375 个调用，其中 337 个对应先前字面候选；方法字符串相同并不代表同一服务。KI selector、Dfn manager façade、扩展连接、HTTP fetch、注入式 resolver 与 coordination socket 分别登记，242/337 已发布候选仍未确认接收方身份。项目 createLocal 已记录 renderer factory、host service 与 main handler 链，见 request-wrapper-contracts.json；这些静态身份分类不代表每个调用已完成运行验证。

独立 REA 补充分析实际运行了三个 JS，并对两个字面通道执行 feature trace，见 [补充报告](supplemental/rea-bootstrap-bridges-v1/report.md)。常量别名引起的 no-match 保留为工具限制；没有运行完整 635 MB Evidence 的 feature trace，也没有把补充输入的图视为原应用全量图。

公开协议比较固定到 `rust-v0.162.0` 提交 `{compatibility['publicCommit']}`；105 个稳定请求递归契约相同，84 个通知中 5 个因两个可选 subAgentActivity 字段不同，v2 集合另有两个路径类型引用变化。详细定位与限制见 [协议比较](protocol-comparison.md)。同名接口、JSON 结构相同与实际运行兼容分别判断。

公开 npm CLI `0.162.0` 的 wrapper/platform 发布物已按 SRI 与 shasum 校验，独立 native CLI 实际导出了 stable/experimental schema。九个实验调用候选的 27 项契约相同，见 [实验候选比较](public-experimental-compatibility.md)；全导出比较见 [完整导出比较](exported-protocol-comparison.md)。其 npm 元数据没有 gitHead，公开二进制与上述 Rust 提交的源码关系仍为 unknown。GitHub release 下载两次超时的失败及 partial 字节记录保留，未执行 partial 下载。

完整导出差异中的 experimentalPredictionMode 并非仅有类型声明：窄 AST 追踪确认 main 的预测入口向 Rq 传入 true，Rq 在条件满足时构造 h.forkThread 的该参数，且该值继续控制 startTurn 参数分支。174 条完整来源范围见 experimental-prediction-usage.json 与 experimental-prediction-evidence.jsonl，不能将静态调用构造当作后端已收到请求。

版本门控 Ti→I 的完整来源另有 95 条证据：该功能通常使用 `0.162.0-alpha.20` 门槛，但 `0.162.0-alpha.17.2` 命中明确例外；输入 `0.162.0` 时，比较器对同基础版本的正式版优先分支返回 1。两个字串均静态通过。实际 appServerVersion、其他前置条件及 host 接收方仍未知，后续负例已区分该字段的参数解码与门控；成功 fork 的预测语义仍未知。见 [预测版本门槛](prediction-version-gate.md)。

[版本来源补充](app-server-version-origin-summary.md)追踪选定mB连接候选的initialize响应和状态。
`__codex_initialize__.result.userAgent`经导出sn/局部D解析，赋给initializedAppServerVersion，再由getter提供给预测门槛。
installedCodexVersion由transport另行取得；初始化通知携带两个独立字段，clearInitializedHost重置其状态。
新增40条来源、引用28条旧证据，审阅14个完整成员；完整class定位含238成员，不能计为全成员语义审查。
一个290566字节module完整解析，main与src整源仍未完整解析。857项独立工件核验通过，原journal字节和失败尝试均保留。
旧headless观察只存initialize返回键，没有userAgent实值；当前实例版本、通知送达/顺序、启动与reset执行仍unknown。

后续 [thread/fork 负例比较](fork-negative-protocol-comparison.md) 固定到不存在的合成 UUID，32 请求全部被拒绝，未提交模型任务。冻结版本识别 experimentalPredictionMode 的布尔类型并对 true 要求实验 capability；公开版本对错误类型也未拒绝，表现与未知字段对照一致。16 配对中 3 个错误契约不同，不能以相同 lookup 错误宣称成功路径兼容。

## 对工程恢复的影响

菜单和命令的 [定向清单](menu-command-summary.md) 区分原生 API、item schema、有限 metadata 实例和真实注册。1 个 application menu 工厂及消费者、31 个原生 API、1 个 globalShortcut.register 与 6 个 before-input-event 均有完整来源；174 个 command schema 源位置有限展开为 182 实例，不等于 182 个独立功能。156 个 schema/生成器参数中 126 个有注册数据流，30 个仅定位构造作用域。411 个稳定契约 ID 的坐标、7 个源文件与 6,806 条证据已机械复核。

选定 renderer 中 Pw 注册与 xs 消息订阅分别登记；dispatchHostMessage 的候选实现仅本地分发，dispatchMessage 才进入 preload IPC。片段内部和完整菜单 Program 的绑定与原整源外层绑定分别标注；后者和全 renderer 注册分母仍未知。这些注册记录的模式和实际行为也尚未验证，不能按菜单名称或 requiredAccess 直接删除。

[入口台账](functional-entry-summary.md) 汇总此前14份冻结输入中的入口来源和结构关系，各类分母独立保留：170 Route、411菜单契约、143 host case、53设置字面候选、91直接app-server候选为868主类；Navigate、路由转换及IPC来源/通道对为100辅助类。463/868主类已有结构契约链接、405/868尚无；全部968记录中466有关联、502无关联。route→conversion只证明构造/API合同适用关系，不能当逐路由运行可达或同一功能；41个同handler来源关联也不证明输入、效果或功能等价。台账已校验14输入哈希、10688 JSONpointer及8712既有证据引用，完整功能归属仍需逐项核对。后续模式续查的局部调用记录单独登记，不自动扩大该台账分母。

发布文件、原源码模块和拟维护模块须分别记录。没有可用 source map，最终目录需根据职责、运行环境、状态和接口提出，并保留原字节位置映射；现有 modules.json 仍是发布文件候选。另按已审查契约提出 11 条局部维护边界与 138 个来源映射，见 [模块边界建议](module-boundary-proposals.md)；它们不是原作者目录或全部模块恢复，尚需运行环境与共享闭包审查。

[app-host维护补充](app-host-maintenance-summary.md)从4组冻结产物、24个直接pin、4份原producer及71条原记录提出8个职责模块、6个接口、5个依赖边界和7项未来迁移验证。
26项均为proposal/inferred；本轮没有新增目标源码读取、AST或源码事实，71条仅按原来源范围复用。
建议分开preload/main连接、context与sender、host服务装配、HTTP生命周期、desktop fetch、applicationNetwork及requirements/native startup。
setter注册副作用、provider清理与进度响应buffering、网络generation/permission和未知RPC/Owl/第三方归属仍需保留。
拟定路径和类型属于新维护设计；未执行迁移验证，也未证明完整目录或功能恢复，不能与此前11条建议直接合并成完整覆盖统计。

ChatGPT、chat/work、Codex、local/cloud thread kind 是多个维度。部分 ChatGPT conversation route 允许 Work；Codex 权限菜单也使用“ChatGPT 操作”字样。名称不能作为排除依据。当前尚无已确认可删除清单。

[模式边界续查](chatgpt-mode-boundary-summary.md)完整解析两组ChatGPT候选的9个发布文件，复用既有路由和guard记录，新增23,011条来源范围。conversation页面和turn-content的完整函数范围存在chat/work复用，另有带来源ID的Work handoff转换、共享页面包装导出和project设置的localFolders条件分支。这里的Work维度不能直接提升为Codex共享；动态服务实现、完整消费者闭包及运行条件仍未知，9模块模式均unknown、确认排除0。24边界形式候选与已审查业务调用分别登记。

独立核验对新材料的直接哈希、范围和引用层无core错误，但旧request-wrapper的间接全局index pin已有历史哈希漂移；该项在[验证记录](chatgpt-mode-boundary-validation.json)保留为未解决，没有宣称全部传递来源层通过。[输入归档](chatgpt-mode-boundary-input-provenance.json)保存本次9份直接输入和冻结工具的原字节。

[请求 facade 续查](request-facade-summary.md)把其中3文件的3个import、18个直接调用接到真实shared `$wt`→`BY=new Gxn(...)`→`AW.getInstance()`。initial导出的同名BY实际是vko初始化函数，两者不能混同。20个完整选定范围新增54条证据；普通路径到e6.httpFetch，特定路径转向host dispatch。该份未覆盖具体host实现；初始化、实际请求和模式仍unknown。safe方法保留重抛分支，header标签也不证明模式归属。120条既有journal原记录子集独立核对；此结果不解决旧间接pin漂移，也不形成全客户端HTTP调用分母。

[项目 localFolders 条件续查](project-local-folder-predicate-summary.md)审查1,580字节完整片段中的6个函数与7处调用；片段另有8个顶层声明未作语义审查。Emn候选定义要求bO(project)及open-default memory scope，检查的是数据资格，未直接读取产品模式。settings的L实际来自Pt函数局部Re→Me(Fe,a)/memo，Me导入initial.gkn；该Re遮蔽了顶层同名rOn导入，不能按拼写串接。gkn的后续选定来源见权限补充；该份尚未覆盖c(rt)，后续来源见功能条件补充。原整源外层绑定、挂载及运行条件仍未知，确认排除项为0。38条范围中15条新增、23条冻结复用；此分母不覆盖全部项目消费者。

完整 guard 来源显示 allowWork=true 的 conversation 能力可接受 ChatGPT product access 或允许的 Work cloud policy，同时仍取决于 config、Statsig 和账户能力；OrbitConversationRoute 本身直接返回 children。这些静态条件不能替代当前账户/功能开关的运行核对，也不意味着全部 ChatGPT 页都须保留。

第三方实现只保留在本地只读分析副本。依赖清单区分声明、安装 occurrence 和嵌入线索；通知表的“may be included”不能当锁文件。第一方 wrapper 和私有 @oai 包仍属接口与源码调查范围。

定向 [内嵌依赖调查](embedded-dependency-summary.md) 绑定了 React/ReactDOM 19.2.7、router 7.18.1、Statsig family 3.34.0 与 Zod core 4.4.3 的源码版本自报。它们不证明实际上游来源或未修改；ProseMirror model/view 版本仍 unknown。Statsig 通知候选为私有 @oai-statsig 系列，不能直接替换为普通公开 SDK。browser annotation 的 jx/Mx 是应保留的应用适配器候选，不能随库实现一起剥离；模式归属和运行依赖仍待验证。

五个根包已通过官方 npm 归档 integrity 和逐文件比较，见 [上游比较](upstream-comparison.md)。tslib/node-addon-api 的全部文件相同；node-pty 的两个 Windows JS 有静态修改，不能直接换包后宣称行为一致。原生文件及裁剪构建输入另行记录；同版本嵌套包不继承根包结论。这五个依赖归档仅作逐文件比较，未安装或执行其中实现；上述公开 CLI 则已按独立记录执行版本、schema 和命令协议检查。

启动路径未发现已验证的 shell-env 跳过开关。FORCE_CLI、CLI_PATH、USER_DATA_PATH 在环境导入后使用；只有 CODEX_HOME 有条件恢复，见 shell-env-controls.json。因此独立目录不证明账号隔离，后续行为验证需确认实际后端、进程及 profile，且不读取个人凭据。

原构建脚本引用的 30 个输入出现项未在发布包中找到。Owl、私有组件、原生/Wasm 来源和公开服务兼容性会影响构建方案，故实施计划现阶段只能列出调查门槛和恢复顺序候选。

[运行时 fuse 字节核对](runtime-fuse-summary.md)完整扫描两份选定运行副本二进制，哈希均与冻结清单一致。Framework 唯一标准格式 wire 为v1/长度9/`010011001`；依据官方外部schema，RunAsNode、NODE_OPTIONS、NodeCliInspect 序号字节均为禁用值，因此没有用这些方式启动诊断。外部schema版本不能当作实际Owl版本；这份字节补充没有验证原生消费者、实际执行效果、Node版本或传统原生模块ABI。10条原始byte spans独立核对通过，材料和producer原字节已冻结。ASAR integrity的启用字节不解释7条历史声明矛盾。

后续[原生 accessor 核对](runtime-native-accessors-summary.md)通过Mach-O段映射与有限机器码确认9个fuse访问函数读取对应wire字节，并返回是否等于ASCII1；这补上选定访问函数的读取绑定，启动调用点与完整执行效果仍未知。另一个77字节完整函数`napi_get_version`在非空指针分支向输出写入10。Node-API版本编码、Node发行版本及传统NODE_MODULE_VERSION分开记录；该份补充尚未确定后两者及原生模块兼容性。10函数主体共230字节、48条来源范围及小型工具原输出均冻结，未执行目标或新增模型任务。

[Node 发行版本接口补充](runtime-node-version-summary.md)核对选定Framework的完整`napi_get_node_version`、其直接引用的24字节结构与release的Mach-O chained fixup。结构静态编码为{runtime_node['versionStructure']['encodedVersion']}，release为`{runtime_node['versionStructure']['release']}`；共{runtime_node['summary']['newEvidenceCount']}条新证据，{runtime_node['summary']['getterBodyBytes']}字节函数主体和{runtime_node['summary']['selectedChainPointerCount']}个选定链指针。它补上该原生接口的静态发行版本数据；执行查询、Electron兼容版本、传统原生ABI及模块兼容性继续unknown。两次producer断言失败的输出及脚本快照已保留，独立核验覆盖最终产物。

[项目权限条件补充](project-permission-summary.md)通过saved export将settings的Me接到initial.gkn/local ymn候选。完整47字节函数要求状态严格等于`allowed`且can_write严格等于true；另解析完整70字节memo表达式，保留重算与读取cache n[13]的差异。{project_permission['summary']['freshEvidenceRecords']}条新来源和{project_permission['summary']['reusedEvidenceRecords']}条复用来源通过独立核验；该份未覆盖c(rt)，后续来源见功能条件补充。原initial外层绑定、memo运行一致性和完整挂载行为仍未知，确认模式排除仍为0。

[项目功能条件补充](project-feature-condition-summary.md)按settings中c(rt)的保存词法来源，连接shared hook facade候选与local-folders模块的实际导出。
完整小模块{project_feature_condition['scope']['smallCompleteModuleBytes']}字节、{project_feature_condition['scope']['smallModuleTopLevelStatements']}个顶层语句，区分同名局部L；另有{project_feature_condition['scope']['selectedSharedCompleteFunctions']}个选定shared完整函数。
合计{project_feature_condition['scope']['parseUnits']}个parse units、{project_feature_condition['scope']['parsedOriginalBytesIncludingOverlaps']}字节（含重叠），新增{project_feature_condition['scope']['newEvidenceRecords']}条来源，逐字复用{project_feature_condition['scope']['reusedOriginalJournalRecords']}条原记录。
选定derived-state callback同时检查gate truthy、两个remote capability非null、identity非null和LOCAL_PROJECTS data非null；这些是功能条件候选，字段名和gate名称不证明产品模式。
原shared整源外层绑定及重赋值范围、动态gate与应用状态、全部settings消费者、挂载与运行仍未知。首次同名L声明被误列为reference的记录分类已修正，修前原件保留。
此补充没有解决历史间接input pin漂移，确认ChatGPT-only排除仍为0；完整小模块解析不等于整个shared bundle或所有消费者语义完成。

[HTTP 服务来源补充](http-service-origin-summary.md)定位候选qli将e6赋为await $3.services、Uli创建并转交MessageChannel port、hFt返回remote-main代理。Bli.services属于本地callback集合，不能当作e6的远端服务集合。{http_origin['scope']['selectedNewCompleteFunctions']}个选定完整函数共{http_origin['scope']['selectedParseUnitBytesIncludingOverlaps']}字节、{http_origin['scope']['newEvidenceRecords']}条新来源通过独立核验；该份尚未覆盖具体host httpFetch注册及实现，后续选定来源见主进程补充。全模块外层绑定、初始化与请求运行、模式归属仍unknown。静态消息边界不代表实际网络成功。

[preload 转发补充](preload-app-host-summary.md)单独核对窗口message的来源及type条件、局部port读取和ipcRenderer.postMessage的转交参数。
完整{preload_app_host['scope']['completePreloadBytes']}字节小Program有{preload_app_host['scope']['topLevelStatements']}个顶层语句和{preload_app_host['scope']['astNodes']}个AST nodes，新增{preload_app_host['scope']['newEvidenceRecords']}条来源；选定词法绑定与同名变量已区分，源码直接写入扫描不证明没有外部对象修改。
完整小Program解析不等于逐一审查无关功能。外部require返回身份、窗口发消息者、端口peer及实际送达仍保留其验证范围。此来源与主进程的通道注册分别记录于[IPC清单](ipc.json)，模式排除仍未确认。

[主进程 HTTP 服务补充](host-http-service-summary.md)追踪bootstrap通道导出、main接收处理器、选定context class的createAppHost及httpFetch provider。
{host_http_service['scope']['sourceFilesReadAndHashed']}份源的{host_http_service['scope']['selectedParseUnits']}个完整有界parse units共{host_http_service['scope']['selectedParseUnitBytesIncludingOverlaps']}字节（含重叠），只审查{host_http_service['scope']['selectedClassMembers']}个选定class成员，新增{host_http_service['scope']['newEvidenceRecords']}条来源、复用{host_http_service['scope']['reusedOriginalJournalRecords']}条原记录。
处理器保留注入的信任过滤和动态context获取；选定factory直接登记provider，后者调用fetch wrapper并带response observer，销毁事件和provider cancellation/disposal分开记录。
fetch wrapper的静态来源包含URL/headers/body准备、网络及认证条件、abort和有限401重试；progress分支先缓冲响应，异常转换限定于自身try。该份未覆盖applicationNetwork实际adapter来源，后续选定来源见网络补充；RPC/base及部分helper仍待核对。
完整class范围与已审查成员范围分开计数，不能将整class字节定位当全部成员语义完成。该份未覆盖context获取和信任适配器的caller来源，后续选定来源见context补充；实际实例、跨进程送达、HTTP运行结果和模式仍未验证。

[context 与信任过滤补充](app-host-context-summary.md)审查main的u0e、M1e、vXe三个完整函数中的选定节点，以及10个有限trust成员/helper范围。
合计{app_host_context['scope']['selectedParseUnits']}个parse units、{app_host_context['scope']['selectedSourceBytesIncludingOverlaps']}字节（含重叠），新增{app_host_context['scope']['newEvidenceRecords']}条来源并复用{app_host_context['scope']['reusedOriginalJournalRecords']}条原记录。
u0e以无spread对象传入H.getContextForWebContents与Oe信任适配器；M1e的context slot初始null，仅在WebContents注册集合包含输入id时返回该slot。
vXe构造hXe并调用setWindowContext，支持同一选定作用域中的静态候选链。信任来源包含sender注册、main frame和URL判断；file入口使用startsWith前缀，不能改述为精确路径相等。
动态集合populate/unregister、成功初始化和实际实例、原完整Program外层绑定、真实sender/port及运行和模式仍未知，不能据静态判断确认消息已获认可或完成送达。
首次producer的ReferenceError及精确失败脚本保留；它属于分析脚本自身失败，没有执行目标代码。旧补充保留各自冻结时的范围。

[底层网络适配器补充](application-network-summary.md)核对bootstrap.tr的fetch/request及策略、readiness、session限制和dispose等选定来源。
{application_network['scope']['sourceFilesReadAndHashed']}份原始输入、{application_network['scope']['newParseUnits']}个完整有界parse units共{application_network['scope']['newParseUnitBytesIncludingOverlaps']}字节（含重叠）、{application_network['scope']['selectedClassMembers']}个tr成员；新增{application_network['scope']['newEvidenceRecords']}条来源并逐字复用{application_network['scope']['reusedHostJournalRecords']}条host记录。
oE的局部r=new tr通过闭包注册network-startup的tt，并返回applicationNetwork:r；main选定u0e/vXe节点再将它传给hXe/Ude。
tr.fetch和tr.request委托required Electron的net API；network-startup的初始bare fetch外层绑定仍未知，chunk名不能证明服务实例。
应用自己的policy/readiness、连接与账户通知、session限制及取消/销毁候选需要作为第一方封装保留，归属目前为inferred；第三方和原生实现仍通过依赖边界登记。
普通fetch与progress使用两种API，progress consumer精确调用end(body)/abort，响应先缓冲。两次措辞修正前材料保留；它们不增加实际网络成功或原生兼容证据。
原整源外层绑定、成功初始化与实际实例、Owl permission/native行为、运行时API兼容和产品模式仍unknown，确认模式排除仍为0。

严格完整性分析曾退出失败。正式运行采用 record-and-continue，保留 7 条 unpacked 声明哈希与实际字节矛盾及 observed-untrusted 标记。baseline-reverification.json 核对这 7 个文件和 ASAR 在原安装、冻结及测试运行副本中一致；相同副本不代表声明完整性通过，矛盾来源仍未确定。

## 继续工作

[会话与任务操作契约](thread-turn-feature-contracts-summary.md)细分原36组中的thread-lifecycle和thread-turn-stream，记录7方法、19旧字面调用、8完整函数/成员与9已见分支。
58条新编写的多来源目录记录与172条冻结旧证据分别保留；4个旧调用静态绑定manager，15个receiver未解决，已确认UI→操作和runtime方法关联均为0。
thread/start的选定路径用于MCP extension启动；turn/start区分乐观状态、响应接受与完成，toolOutput分支的steer可转为turn/start，interrupt箭头自身不写终态。
这些契约供后续恢复状态与接口使用，不能据方法名替代实际入口、通知顺序、持久化和运行验证；本批未新增目标或模型执行，未改变完整功能范围。

[请求入口对账](request-entry-reconciliation-summary.md)逐一比较375个完整AST调用与旧台账968个入口、176个support nodes、337个deferred候选，递归检查5513个保存坐标对象。
337个旧候选按原FEATURE ID、来源hash及唯一完整调用包含范围对齐；旧词法范围与完整AST调用范围的粒度不同，精确范围相同数为0。
剩余38个未对齐（16字面、22动态/条件），已确认漏项为0；95条旧注释可继续审查，功能分母仍unknown，不能直接把未对齐数作为漏项数。
27份输入快照、375条工件对账记录与37份库存元数据回执独立归档；本批未重新读取目标源或验证其span，旧wrapper的独立validation/manifest未找到的限制仍保留。
此对账不改旧入口台账，也不增加全局目标源码证据、业务功能确认数或模式排除项。

[未对齐候选的定向审查](request-entry-unmatched-review-summary.md)补读5个原始文件的38个调用与27个完整作用域。
16个旧字面方法均不含`/`；当前保存的发现脚本要求直接字面方法含`/`，这个规则与保存台账分母一致，历史revision及执行身份仍未知。
20个有限方法、1个索引未知的字面表与17个计算／转发方法单列，旧375/337/38和16/22分母不改；5513个旧坐标中没有call范围对应，caller/class的空间关系不证明操作登记。确认遗漏、新功能和模式排除仍为0。

[通知与状态补充](turn-notification-state-summary.md)记录18个observer完整单元和221条新源码记录。
选定turn/completed候选先drain流再写payload终态；error分支追加错误项，取消候选在特定条件下写interrupted。
此批跨单元外层词法身份未接齐；后续[通知绑定核对](turn-notification-bindings-summary.md)另保存所选模块作用域关系，原221条记录不改。完整turn持久化、实际通知顺序与执行中断恢复仍未知。

[MCP电脑应用审批](approval-entry-contracts-summary.md)确认待处理面板→MCP面板→包装→卡片的8对导入／导出绑定，审查26完整单元并保留30条源码记录。
同键提交守卫、先写批准atom、失败时条件清理和响应构造已有静态来源；成功回调不证明后台送达。动态facade实例、回复确认层次、helper效果与共享状态持久化仍未知，ChatGPT展示文案不构成模式排除。
审批记录中的Ofn来自外层初始化函数标签：保存AST的ClassExpression本身无名称，两个成员位于相同类范围。后续Program作用域核对另确认Dfn的赋值关系，不能把Ofn标签当作恢复源码中的类名或真实receiver。

[电脑使用设置](computer-use-settings-boundary-summary.md)把9个操作、5个query接到main发布服务的14个同名方法，保留28条独立源码记录。
query awaitable的dispose和main worker/文件/installer效果分别记录；非Windows授权JSON路径在homedir下的CUAService容器，Windows默认Codex home resolver未展开，Electron userData隔离不能替代授权数据隔离证明。
4个补充的原manifest、全部允许发布的分析资料、独立journal与同行审查通过[独立分析发布索引](scoped-catalogs-provenance.json)关联；原始method/confidence与范围逐字保留。
其中部分producer采用限定置信度或以units间接定位，缺少计划规定的标准字段；[标准字段视图](scoped-catalogs-evidence-index.jsonl)为每个原记录提供固定基线、发布journal哈希和逐条定位，保留原字段及其差异。
该视图只证明317个已保存分析工件记录的身份，不能将其改算成317条新源码事实；原221+30+28条局部源码分析与38条旧候选复核仍分别计数。
旧全局journal仍为65,571条，新增局部源码证据在各自journal单列；这4个补充均没有目标、模型或运行观察，也没有改变36组候选或完整功能分母未知的状态。

[提交入口契约](task-composer-entry-contracts-summary.md)另保存39条限定静态记录、33个完整单元和5条来源限定的导入／导出路由。
X7e/rut经Qft、Zut/Put/Cdt、rpt/_9e和Tta接到KI；该批分析止于KI选择边界，其自身未确定所选RPC实例与Dfn的关系。
普通取消回调没有传expectedTurnId；界面当前turn ID与实际wire参数分开记录。38条confirmed仅确认限定静态断言，1条职责边界为inferred；实际UI与操作关联仍为0。

[通知绑定核对](turn-notification-bindings-summary.md)另保存31条记录，完整Program作用域区分Dfn模块变量、Ofn初始化函数和匿名ClassExpression。
选定构造函数接上this.threadStore、T7t和notification context的赋值关系；选定onNotification及取消回调的词法身份分别核对，避免把三处局部i拼成同一receiver。
所选源码中的模块绑定与字段关系有静态证据，完整外部写入、实际实例／模式／transport和持久化仍未知；原通知221条及审批30条没有重写。

这两批共70条原始保存记录通过[单独发布索引](static-boundaries-provenance.json)关联，包含源码范围、元数据引用及混合引用，分母分别列出。
发布只复制选定最终分析资料与实际执行回执；较大的AST和失败历史保留在本地冻结清单中。没有把70条改算成70项功能或全部新源码事实，没有增加全局journal，也未执行新客户端或模型任务。

[设置注册表与页面工厂](settings-registry-contracts-summary.md)另保留172条静态记录，分别核对53个资产注册项、53个延迟页面工厂、51个section、50个既有route实例和53个lookup分支。
旧53个设置词法候选唯一落在ua的图标／导航资产属性；没有证明ua与lQa页面表存在直接消费者数据流，不能按名称把两表合并或把资产数当页面功能数。
选定gWa、profile filter、M6与lQa关系保留work-settings提前返回、redirect及usage绕过MNs的条件；实际显示、模块交付、平台／账户值与模式仍待验证。

[React公开依赖身份](react-upstream-identity-contracts-summary.md)核对4/17个既有线索、6个已保存factory与3个官方production模块。
react／react-dom 19.2.7官方归档通过SRI和SHA-1核验，npm gitHead与官方tag对应；114个export occurrence、92个参数形状、38个有限转发形状和4个root方法形状分别计数。
正常包导入候选为react、react-dom和react-dom/client；这些静态形状及官方发行身份不证明基线原安装lock、完整factory等价、未修改或全依赖闭包，scheduler范围也不等于安装版本。

这两批原始journal、冻结来源、限定审查与明确发布allowlist见[补充索引](catalog-supplements-provenance.json)。仅发布分析元数据与核验资料，完整目标单元和第三方实现留在本地；205条保存记录没有改变全局journal、完整功能分母、模式排除或运行确认数。

{recovery_delivery_note}

{submission_delivery_note}

{capnweb_candidate_note}

{settings_and_rpc_note}

{requirements_audit_note}

{bounded_contract_note}

[完成标准审计](criteria-audit.md) 固定于20261013T115019432678Z发布及61份输入快照：9项标准4满足、5部分；6阶段中阶段1满足、其余5部分。94处定位、13项发布工件哈希及17个依赖调查动作映射复核通过；[历史输入归档](criteria-audit-provenance.json)保留原始字节和迁移定位。该审计不覆盖此后新增的任何补充，也不代表客户端实施验收。

[完成标准复核](current-completion-audit.md)另固定于20261013T164818487650Z的93件发布及63份选定快照；其中25份发布输入pin匹配。
原9项标准仍为4满足、5部分；原6阶段为1满足、5部分。44条工件观察记录和88份冻结材料通过来源定位核对，保留首次producer失败材料。
候选登记完整性与功能分母分开判断；unknown是分类状态，不能直接授权排除。逐功能职责/状态/边界、主要行为条件及完整结构验收关联仍有缺口。
该复核不追认后续运行时元数据或维护建议，也不证明客户端构建与实施完成；工件观察journal独立保留，不增加全局目标源码证据或功能计数。

内嵌依赖 [续查](embedded-dependency-continuation-summary.md) 已逐一处理剩余 11 个 hint，总共 17/17 源码声明绑定；[调查动作表](embedded-dependency-investigation-actions.json) 为每条给出来源、引入建议及五项具体 TODO。Sentry 10.29.0 只证明注册表默认值和命名空间键，已有 truthy 全局版本可能保留；Statsig 两处元数据工厂规范 AST 相同只覆盖元数据片段；Zod 的版本仅覆盖 core。CSV 单独使用 sourceSelfReportedVersion，实际上游 version 为空，旧 CSV 字节在 dependency-publication 快照中保留。

具体未完成项见 gaps.md；行为场景见 behavior-checks.md；工程顺序候选见 implementation-plan.md。完成门槛仍按分析计划逐项验收，不能把本轮成功的 REA 命令或有限 UI 检查作为完整目标完成。
'''
(out / 'report.md').write_text(report)
if prediction_gate:
    gate_rows = '\n'.join('| ' + case['version'] + ' | true | ' + case['branch'] + ' |' for case in prediction_gate['staticCases'])
    gate_report = f'''# 预测功能版本门槛静态补充

基线：`{baseline['baselineId']}`。这里仅推导输入两个固定版本字串时的条件结果，未执行目标代码或预测请求。

绑定链为 main fge 的 r.Ti → src-CP7XXlpZ.js 的 exports.Ti getter → I。完整 AST 范围确认 `experimentalPredictionForkMode` 通常使用 `{prediction_gate['gateBindings']['feature']['minimumVersion']}` 门槛；I 先接受合法版本，再对 `0.162.0-alpha.17.2` 明确返回 true。

| 输入字串 | 静态 gate 结果 | 来源分支 |
| --- | --- | --- |
{gate_rows}

公开 `0.162.0` 的基础版本与门槛相同，P 的正式版优先于预发布分支返回 1；冻结 alpha.17.2 虽低于 alpha.20，实际走明确例外。

后续[版本来源补充](app-server-version-origin-summary.md)确认选定mB候选从initialize响应userAgent解析并写入initializedAppServerVersion，getter提供该独立字段；installedCodexVersion另行取得。实际运行实例和版本值、动态host接收方、通知顺序及后端启用状态仍unknown；其他fge条件也可能提前返回null。这项静态门槛检查不能消除experimentalPredictionMode schema差异，也不能证明公开后端支持该实验参数。此前174条调用参数证据见[调用调查](experimental-prediction-usage.json)。

新增解析范围为一个203,781字节模块及 main 的两个完整原始片段，没有重跑全应用。95条证据的源文件 hash、UTF-16到UTF-8定位和完整 span digest 均已复核；见 [结构化记录](prediction-version-gate.json) 与 [证据](prediction-version-gate-evidence.jsonl)。公开 npm 二进制与 Rust源码提交的关系仍为 unknown。
'''
    (out / 'prediction-version-gate.md').write_text(gate_report)
for entry in input_bindings:
    assert file_sha256(workspace / entry['resolvedPath']) == entry['sha256'], ('Published producer input changed', entry)
for entry in mode_archived_inputs + mode_archived_scripts + mode_archived_catalogs:
    data = (workspace / entry['archivedPath']).read_bytes()
    assert len(data) == entry['bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256'], ('Published mode archive changed', entry)
for supplement in directed_provenance:
    assert hashlib.sha256((workspace / supplement['manifestArchivedPath']).read_bytes()).hexdigest() == supplement['manifestSha256']
    for entry in supplement['frozenFiles'] + supplement['publishedFiles'] + supplement['archivedInputs']:
        destination = workspace / entry.get('archivedPath', entry.get('publishedPath'))
        data = destination.read_bytes()
        assert len(data) == entry['bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256'], ('Published directed supplement changed', entry)
input_provenance = json.loads((out / 'supplement-input-provenance.json').read_text())
input_provenance['postPublicationHashesVerified'] = True
(out / 'supplement-input-provenance.json').write_text(json.dumps(input_provenance, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'published': str(out), 'validatedEvidence': len(evidence), 'fullAnalysisCompleted': False}, ensure_ascii=False))
