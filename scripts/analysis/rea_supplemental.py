#!/usr/bin/env python3
"""Analyze byte-identical frozen bootstrap/preload files as a distinct REA input."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['prepare', 'analyze', 'trace'])
    parser.add_argument('--name', default='rea-bootstrap-bridges-v1')
    parser.add_argument('--trace-name', default='trace')
    parser.add_argument('--seed-kind', default='channel',
                        choices=['node-id', 'route', 'string', 'api', 'channel', 'module', 'native-export'])
    parser.add_argument('--seed-value', default='codex_desktop:message-from-view')
    args = parser.parse_args()
    if not args.name.replace('-', '').replace('_', '').isalnum():
        parser.error('name must contain only letters, numbers, hyphens or underscores')
    if not args.trace_name.replace('-', '').replace('_', '').isalnum():
        parser.error('trace-name must contain only letters, numbers, hyphens or underscores')
    workspace = Path(__file__).resolve().parents[2]
    baseline = json.loads((workspace / '.analysis-local/current-baseline.json').read_text())
    baseline_id = baseline['baselineId']
    local = workspace / '.analysis-local/supplemental' / baseline_id / args.name
    out = workspace / 'analysis' / baseline_id / 'supplemental' / args.name
    input_root = local / 'input'
    raw = local / 'raw'
    manifest_path = out / 'source-map.json'
    cli = Path('/private/tmp/ccodex-rea-tooling/install/node_modules/rea-agents/scripts/rea.mjs')

    if args.phase == 'prepare':
        if manifest_path.exists() or input_root.exists():
            parser.error('supplemental input already exists; use a new name')
        source_root = Path(baseline['extractedDirectory'])
        members = ['package.json', '.vite/build/early-bootstrap.js',
                   '.vite/build/preload.js', '.vite/build/sandbox-preload.js']
        source_map = []
        for member in members:
            original = source_root / member
            target = input_root / member
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, target)
            original_hash = sha256(original)
            copied_hash = sha256(target)
            if original_hash != copied_hash:
                raise RuntimeError('copied input differs from frozen source: ' + member)
            source_map.append({'artifactPath': member, 'originalArchivePath': member,
                               'originalFilePath': str(original), 'copiedFilePath': str(target),
                               'sha256': original_hash, 'bytes': original.stat().st_size,
                               'byteIdentical': True})
        write_json(manifest_path, {
            'baselineId': baseline_id, 'name': args.name,
            'originalArchiveSha256': baseline['archiveSha256'],
            'inputRoot': str(input_root), 'preparedAtUtc': datetime.now(timezone.utc).isoformat(),
            'purpose': 'Small distinct input for bootstrap and preload static analysis and feature tracing.',
            'scope': 'Four byte-identical files; missing imports, maps, main handlers and renderer consumers remain outside scope.',
            'identity': 'This directory receives its own REA artifact digest; no claim of identity with the original ASAR graph.',
            'files': source_map,
        })
        print(json.dumps({'prepared': str(manifest_path), 'files': len(source_map)}), flush=True)
        return 0

    manifest = json.loads(manifest_path.read_text())
    for entry in manifest['files']:
        for field in ['originalFilePath', 'copiedFilePath']:
            if sha256(Path(entry[field])) != entry['sha256']:
                raise RuntimeError('supplemental input/source changed: ' + entry[field])
    raw.mkdir(parents=True, exist_ok=True)
    run_name = args.phase if args.phase != 'trace' else args.trace_name
    record_path = out / (run_name + '.run.json')
    stdout_path = raw / (run_name + '.json')
    stderr_path = raw / (run_name + '.stderr.jsonl')
    if record_path.exists() or stdout_path.exists():
        parser.error('phase evidence already exists; choose a new name or trace-name')
    if args.phase == 'analyze':
        arguments = ['analyze-javascript-application', str(input_root), '--artifact-format',
                     'directory', '--max-heap-mb', '2048', '--analysis-timeout-ms', '300000',
                     '--integrity-policy', 'fail', '--format', 'json']
    else:
        application = json.loads((raw / 'analyze.json').read_text())
        if application.get('operation') != 'analyze_javascript_application' or 'evidence_id' not in application:
            raise RuntimeError('analysis is not a complete returned REA Evidence record')
        trace_input = raw / (run_name + '-input.json')
        write_json(trace_input, {'application': application,
                                'seed': {'kind': args.seed_kind, 'value': args.seed_value,
                                         'match': 'exact', 'case_sensitive': True},
                                'direction': 'both'})
        arguments = ['trace-application-feature', str(trace_input), '--format', 'json']
    command = ['node', '--max-old-space-size=4096', str(cli), *arguments]
    record = {'baselineId': baseline_id, 'supplementalName': args.name,
              'command': command, 'toolVersion': json.loads((cli.parents[1] / 'package.json').read_text())['version'],
              'toolCliSha256': sha256(cli), 'sourceMap': str(manifest_path),
              'stdout': str(stdout_path), 'stderr': str(stderr_path),
              'status': 'running', 'startedAtUtc': datetime.now(timezone.utc).isoformat()}
    if args.phase == 'trace':
        record['inputSha256'] = sha256(trace_input)
        record['sourceEvidenceId'] = application['evidence_id']
    with stdout_path.open('wb') as stdout, stderr_path.open('wb') as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        record['pid'] = process.pid
        write_json(record_path, record)
        print(json.dumps({'run': str(record_path), 'pid': process.pid}), flush=True)
        record['exitCode'] = process.wait()
    record.update({'status': 'finished', 'endedAtUtc': datetime.now(timezone.utc).isoformat(),
                   'stdoutSha256': sha256(stdout_path), 'stdoutBytes': stdout_path.stat().st_size,
                   'stderrSha256': sha256(stderr_path), 'stderrBytes': stderr_path.stat().st_size})
    write_json(record_path, record)
    print(json.dumps({'exitCode': record['exitCode'], 'stdoutBytes': record['stdoutBytes']}), flush=True)
    return record['exitCode']


if __name__ == '__main__':
    sys.exit(main())
