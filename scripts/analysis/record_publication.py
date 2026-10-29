#!/usr/bin/env python3
"""Record a local publication's exact runner, output and artifact hashes."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

workspace = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('kind', choices=['findings', 'dependencies'])
args = parser.parse_args()
baseline = json.loads((workspace / '.analysis-local/current-baseline.json').read_text())
out = workspace / 'analysis' / baseline['baselineId']
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
raw = out / 'raw' / ('publication' if args.kind == 'findings' else 'dependency-publication') / stamp
raw.mkdir(parents=True, exist_ok=False)
runner = workspace / 'scripts/analysis' / ('publish_findings.py' if args.kind == 'findings' else 'publish_dependencies.py')
source = runner.read_bytes()
(raw / 'publisher-source.py').write_bytes(source)
runner_dependencies = {}
from contract_reader_context import build_context
_, _, bounded_contract_artifacts = build_context(out, 'codex-26.1007.30912-c5b273322a83')
artifacts += bounded_contract_artifacts
if args.kind == 'findings':
    for dependency_name, snapshot_name in (
        ('scripts/analysis/scoped_catalogs.py', 'scoped-catalogs-helper-source.py'),
        ('scripts/analysis/static_boundaries.py', 'static-boundaries-helper-source.py'),
        ('.analysis-local/static-boundary-publication-work/config.json', 'static-boundaries-config.json'),
        ('scripts/analysis/catalog_supplements.py', 'catalog-supplements-helper-source.py'),
        ('.analysis-local/catalog-supplement-publication-work/config.json', 'catalog-supplements-config.json'),
        ('scripts/analysis/deliver_frozen_metadata.py', 'frozen-metadata-delivery-source.py'),
        ('scripts/analysis/deliver_submission_contracts.py', 'submission-delivery-source.py'),
        ('scripts/analysis/publish_capnweb_candidate.py', 'capnweb-candidate-source.py'),
        ('scripts/analysis/deliver_capnweb_peer.py', 'capnweb-peer-delivery-source.py'),
        ('scripts/analysis/deliver_settings_and_rpc.py', 'settings-and-rpc-delivery-source.py'),
        ('scripts/analysis/deliver_requirements_audit.py', 'requirements-audit-delivery-source.py'),
        ('.analysis-local/settings-and-rpc-delivery-work/profiles-v2.json', 'settings-and-rpc-delivery-profiles.json'),
    ):
        dependency = workspace / dependency_name
        dependency_source = dependency.read_bytes()
        snapshot = raw / snapshot_name
        snapshot.write_bytes(dependency_source)
        runner_dependencies[dependency_name] = {
            'bytes': len(dependency_source), 'sha256': hashlib.sha256(dependency_source).hexdigest(),
            'snapshot': snapshot.name,
        }
argv = [sys.executable, str(runner)]
artifacts = ['evidence-validation.json', 'evidence.jsonl', 'report.md', 'behavior-checks.md', 'analysis-state.json',
             'prediction-version-gate.md', 'module-boundary-proposals.json', 'module-boundary-proposals.md',
             'supplement-input-provenance.json', 'functional-entry-ledger.json', 'functional-entry-summary.json',
             'functional-entry-summary.md', 'functional-entry-validation.json', 'functional-entry-reviewed-links.json',
             'functional-entry-manifest.json', 'runtime-adapter-options.json', 'runtime-adapter-options.md',
             'chatgpt-candidate-module-contracts.json', 'chatgpt-candidate-module-evidence.jsonl',
             'chatgpt-mode-boundary-summary.md', 'chatgpt-mode-boundary-validation.json',
             'chatgpt-mode-boundary-manifest.json', 'chatgpt-mode-boundary-ast-summary.json',
             'chatgpt-project-review.json', 'chatgpt-mode-boundary-input-provenance.json',
             'runtime-fuse-observation.json', 'runtime-fuse-evidence.jsonl', 'runtime-fuse-summary.md',
             'runtime-fuse-validation.json', 'runtime-fuse-manifest.json', 'directed-supplement-provenance.json']
artifacts += ['request-facade-contract.json', 'request-facade-evidence.jsonl', 'request-facade-summary.md',
              'request-facade-reused-evidence.jsonl', 'request-facade-validation.json', 'request-facade-manifest.json']
artifacts += ['runtime-native-accessors.json', 'runtime-native-accessors-evidence.jsonl', 'runtime-native-accessors-summary.md',
              'runtime-native-accessors-validation.json', 'runtime-native-accessors-manifest.json',
              'project-local-folder-predicate.json', 'project-local-folder-predicate-evidence.jsonl',
              'project-local-folder-predicate-summary.md', 'project-local-folder-predicate-validation.json',
              'project-local-folder-predicate-manifest.json']
artifacts += ['runtime-node-version.json', 'runtime-node-version-evidence.jsonl', 'runtime-node-version-summary.md',
              'runtime-node-version-validation.json', 'runtime-node-version-manifest.json',
              'project-permission.json', 'project-permission-evidence.jsonl', 'project-permission-summary.md',
              'project-permission-validation.json', 'project-permission-manifest.json',
              'http-service-origin.json', 'http-service-origin-evidence.jsonl', 'http-service-origin-summary.md',
              'http-service-origin-reused-evidence.jsonl',
              'http-service-origin-validation.json', 'http-service-origin-manifest.json']
artifacts += ['preload-app-host.json', 'preload-app-host-evidence.jsonl', 'preload-app-host-summary.md',
              'preload-app-host-validation.json', 'preload-app-host-manifest.json',
              'host-http-service.json', 'host-http-service-evidence.jsonl', 'host-http-service-summary.md',
              'host-http-service-reused-evidence.jsonl',
              'host-http-service-validation.json', 'host-http-service-manifest.json', 'ipc.json']
artifacts += ['app-host-context.json', 'app-host-context-evidence.jsonl', 'app-host-context-summary.md',
              'app-host-context-reused-evidence.jsonl', 'app-host-context-validation.json',
              'app-host-context-manifest.json']
artifacts += ['application-network.json', 'application-network-evidence.jsonl', 'application-network-summary.md',
              'application-network-reused-evidence.jsonl', 'application-network-validation.json',
              'application-network-manifest.json']
artifacts += ['project-feature-condition.json', 'project-feature-condition-evidence.jsonl', 'project-feature-condition-summary.md',
              'project-feature-condition-reused-evidence.jsonl', 'project-feature-condition-validation.json',
              'project-feature-condition-manifest.json']
artifacts += ['runtime-distribution.json', 'runtime-distribution-evidence.jsonl', 'runtime-distribution-summary.md',
              'runtime-distribution-validation.json', 'runtime-distribution-manifest.json']
artifacts += ['app-host-maintenance.json', 'app-host-maintenance-evidence.jsonl', 'app-host-maintenance-summary.md',
              'app-host-maintenance-validation.json', 'app-host-maintenance-manifest.json']
artifacts += ['current-completion-audit.json', 'current-completion-audit.md', 'current-completion-audit-evidence.jsonl',
              'current-completion-audit-inputs.json', 'current-completion-audit-validation.json',
              'current-completion-audit-manifest.json', 'current-completion-audit-provenance.json']
artifacts += ['app-server-version-origin.json', 'app-server-version-origin-evidence.jsonl',
              'app-server-version-origin-summary.md', 'app-server-version-origin-validation.json',
              'app-server-version-origin-manifest.json', 'app-server-version-origin-raw-summary.md']
artifacts += ['thread-turn-feature-contracts.json', 'thread-turn-feature-contracts-evidence.jsonl',
              'thread-turn-feature-contracts-summary.md', 'thread-turn-feature-contracts-validation.json',
              'thread-turn-feature-contracts-manifest.json', 'thread-turn-feature-contracts-peer-review.json',
              'thread-turn-feature-contracts-peer-review.md', 'thread-turn-feature-contracts-protocol-source-review.json',
              'thread-turn-feature-contracts-provenance.json']
artifacts += ['request-entry-reconciliation.json', 'request-entry-reconciliation-summary.md',
              'request-entry-reconciliation-evidence.jsonl', 'request-entry-reconciliation-input-receipts.json',
              'request-entry-reconciliation-source-receipts.json', 'request-entry-reconciliation-validation.json',
              'request-entry-reconciliation-peer-input-check.json', 'request-entry-reconciliation-peer-review.json',
              'request-entry-reconciliation-manifest.json', 'request-entry-reconciliation-provenance.json']
artifacts += ['gaps.md', 'scoped-catalogs-provenance.json', 'scoped-catalogs-evidence-index.jsonl']
artifacts += ['scoped-catalogs-publication-peer-review.json', 'scoped-catalogs-helper-peer-review.json',
              'scoped-catalogs-publication-peer-summary.md', 'implementation-plan.md']
for prefix in ('request-entry-unmatched-review', 'turn-notification-state',
               'approval-entry-contracts', 'computer-use-settings-boundary'):
    artifacts += [prefix + suffix for suffix in ('.json', '-evidence.jsonl', '-summary.md',
        '-raw-summary.md', '-validation.json', '-peer-review.json', '-peer-review.md',
        '-manifest.json', '-provenance.json')]
artifacts += ['static-boundaries-provenance.json']
artifacts += ['static-boundaries-publication-peer-review.json', 'static-boundaries-publication-peer-summary.md']
for prefix in ('task-composer-entry-contracts', 'turn-notification-bindings'):
    artifacts += [prefix + suffix for suffix in ('.json', '-evidence.jsonl', '-summary.md',
        '-raw-summary.md', '-validation.json', '-peer-review.json', '-peer-review.md',
        '-manifest.json', '-provenance.json')]
previous = {}
artifacts += ['catalog-supplements-provenance.json']
artifacts += ['catalog-supplements-helper-peer-review.json', 'catalog-supplements-header-delta-peer-review.json',
              'catalog-supplements-publication-peer-summary.md']
for prefix in ('react-upstream-identity-contracts', 'settings-registry-contracts'):
    artifacts += [prefix + suffix for suffix in ('.json', '-evidence.jsonl', '-summary.md',
        '-raw-summary.md', '-validation.json', '-peer-review.json', '-peer-review.md', '-manifest.json', '-provenance.json')]
recovery_index = out / 'recovery-decision-catalogs-provenance.json'
if recovery_index.exists():
    delivery = json.loads(recovery_index.read_text())
    artifacts += [recovery_index.name]
    for catalog in delivery['catalogs']:
        prefix = catalog['catalogId']
        artifacts += [prefix + '-delivery-provenance.json', prefix + '-summary.md']
        artifacts += [item['published'] for item in catalog['copies']]
    for name in ('settings-module-synthesis.json', 'settings-module-synthesis-summary.md',
                 'dependency-import-decisions.json', 'dependency-import-decisions.md',
                 'recovery-maintenance-proposals-provenance.json'):
        if (out / name).exists():
            artifacts.append(name)
submission_index = out / 'submission-host-instance-provenance.json'
if submission_index.exists():
    submission_delivery = json.loads(submission_index.read_text())
    artifacts += [submission_index.name, 'submission-host-instance-summary.md',
                  'submission-recovery-guidance.json', 'submission-recovery-guidance.md']
    artifacts += [item['published'] for item in submission_delivery['copies']]
settings_and_rpc_index = out / 'settings-and-rpc-delivery-provenance.json'
if settings_and_rpc_index.exists():
    settings_and_rpc_delivery = json.loads(settings_and_rpc_index.read_bytes())
    artifacts += [settings_and_rpc_index.name, 'settings-and-rpc-summary.md']
    for catalog in settings_and_rpc_delivery['catalogs']:
        artifacts.append(catalog['catalogId'] + '-delivery-provenance.json')
        artifacts += [item['published'] for item in catalog['copies']]
    settings_review_index = out / 'settings-and-rpc-delivery-review-provenance.json'
    if settings_review_index.exists():
        settings_review_delivery = json.loads(settings_review_index.read_bytes())
        artifacts.append(settings_review_index.name)
        artifacts += [item['published'] for item in settings_review_delivery['copies']]
    for execution_name in ('delivery-execution-provenance.json', 'reader-integration-execution-provenance.json'):
        execution_index = out / 'raw/settings-and-rpc' / execution_name
        if execution_index.exists():
            execution = json.loads(execution_index.read_bytes())
            artifacts.append(str(execution_index.relative_to(out)))
            artifacts += [item['path'] for item in execution['copies']]
capnweb_candidate_path = out / 'capnweb-upstream-candidate.json'
requirements_audit_index = out / 'analysis-requirements-current-audit-provenance.json'
if requirements_audit_index.exists():
    requirements_audit_delivery = json.loads(requirements_audit_index.read_bytes())
    artifacts += [requirements_audit_index.name, 'analysis-requirements-current-audit.md']
    artifacts += [item['published'] for item in requirements_audit_delivery['copies']]
    for relative in ('raw/analysis-requirements-current-audit/reader-before-report.md',
                     'raw/analysis-requirements-current-audit/reader-before-analysis-state.json',
                     'raw/analysis-requirements-current-audit/delivery-execution-provenance.json'):
        if (out / relative).exists():
            artifacts.append(relative)
            if relative.endswith('delivery-execution-provenance.json'):
                artifacts += [item['path'] for item in json.loads((out / relative).read_bytes())['copies']]
if capnweb_candidate_path.exists():
    capnweb_candidate = json.loads(capnweb_candidate_path.read_bytes())
    artifacts += [capnweb_candidate_path.name, 'capnweb-upstream-candidate-evidence.jsonl',
                  'capnweb-upstream-candidate-summary.md']
    artifacts += [item['published'] for item in capnweb_candidate['provenance']]
    review_index = out / 'capnweb-upstream-candidate-review-provenance.json'
    if review_index.exists():
        review_delivery = json.loads(review_index.read_bytes())
        artifacts.append(review_index.name)
        artifacts += [item['published'] for item in review_delivery['copies']]
    for execution_name in ('execution-provenance.json', 'finish-execution-provenance.json'):
        execution_index = out / 'raw/capnweb-upstream-candidate' / execution_name
        if execution_index.exists():
            execution = json.loads(execution_index.read_bytes())
            artifacts.append(str(execution_index.relative_to(out)))
            artifacts += [item['path'] for item in execution['copies']]
if args.kind == 'findings':
    before_names = ['evidence.jsonl', 'ipc.json', 'report.md', 'analysis-state.json',
                    'scoped-catalogs-provenance.json', 'scoped-catalogs-evidence-index.jsonl',
                    'static-boundaries-provenance.json', 'catalog-supplements-provenance.json']
    before_names += [prefix + suffix for prefix in ('request-entry-unmatched-review',
        'turn-notification-state', 'approval-entry-contracts', 'computer-use-settings-boundary')
        for suffix in ('-provenance.json', '-summary.md')]
    for name in before_names:
        if not (out / name).exists():
            continue
        data = (out / name).read_bytes()
        snapshot = raw / ('before-' + name)
        snapshot.write_bytes(data)
        previous[name] = {'path': str(snapshot.relative_to(out)),
                          'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
if args.kind == 'dependencies':
    argv += ['--baseline', str(out / 'baseline.json'), '--local', str(workspace / '.analysis-local/dependency-work')]
    artifacts = ['dependencies.csv', 'dependency-evidence.jsonl', 'dependency-summary.json', 'dependency-report.md', 'build-inputs.json', 'native-runtime.json']
    for name in artifacts:
        data = (out / name).read_bytes()
        (raw / ('before-' + name)).write_bytes(data)
        previous[name] = {'path': str((raw / ('before-' + name)).relative_to(out)), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
(raw / 'before-artifacts.json').write_text(json.dumps({'baselineId': baseline['baselineId'],
    'previousArtifactSnapshots': previous}, ensure_ascii=False, indent=2) + '\n')
start = time.monotonic()
with (raw / 'stdout.txt').open('wb') as stdout, (raw / 'stderr.txt').open('wb') as stderr:
    result = subprocess.run(argv, cwd=workspace, stdout=stdout, stderr=stderr, check=False)
record = {'baselineId': baseline['baselineId'], 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
          'method': 'local-evidence-publication-and-validation', 'kind': args.kind, 'argv': argv,
          'exitCode': result.returncode, 'elapsedSeconds': time.monotonic() - start,
          'runnerSha256': hashlib.sha256(source).hexdigest(), 'runnerSnapshot': 'publisher-source.py',
          'runnerUnchangedDuringRun': runner.read_bytes() == source,
          'runnerDependencySources': runner_dependencies,
          'stdoutSha256': hashlib.sha256((raw / 'stdout.txt').read_bytes()).hexdigest(),
          'stderrSha256': hashlib.sha256((raw / 'stderr.txt').read_bytes()).hexdigest(),
          'beforeArtifactsManifestSha256': hashlib.sha256((raw / 'before-artifacts.json').read_bytes()).hexdigest(),
          'previousArtifactSnapshots': previous, 'artifacts': {}}
for name, entry in runner_dependencies.items():
    data = (workspace / name).read_bytes()
    entry['unchangedDuringRun'] = len(data) == entry['bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256']
    assert entry['unchangedDuringRun'], ('Publisher dependency changed during run', name)
for name in artifacts:
    if (out / name).exists():
        data = (out / name).read_bytes()
        record['artifacts'][name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
(raw / 'run.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'record': str((raw / 'run.json').relative_to(workspace)), 'exitCode': result.returncode,
                  'runnerUnchangedDuringRun': record['runnerUnchangedDuringRun']}))
if result.returncode:
    print((raw / 'stderr.txt').read_text()[-3000:])
raise SystemExit(result.returncode)
