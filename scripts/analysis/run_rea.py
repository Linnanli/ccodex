#!/usr/bin/env python3
"""Persist a REA run without truncating its stdout or stderr."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

workspace = Path(__file__).resolve().parents[2]
baseline = json.loads((workspace / '.analysis-local/current-baseline.json').read_text())
parser = argparse.ArgumentParser()
parser.add_argument('name')
parser.add_argument('arguments', nargs=argparse.REMAINDER)
args = parser.parse_args()
if not args.name.replace('-', '').replace('_', '').isalnum():
    parser.error('name must contain only letters, numbers, hyphens or underscores')
cli = Path('/private/tmp/ccodex-rea-tooling/install/node_modules/rea-agents/scripts/rea.mjs')
package = json.loads((cli.parents[1] / 'package.json').read_text())
out = workspace / 'analysis' / baseline['baselineId']
raw = out / 'raw'
raw.mkdir(parents=True, exist_ok=True)
result_path = raw / (args.name + '.json')
log_path = raw / (args.name + '.progress.jsonl')
record_path = out / (args.name + '.run.json')
if result_path.exists() or record_path.exists():
    parser.error('run name already exists; use a new name to preserve previous evidence')
command = ['node', '--max-old-space-size=8192', str(cli), *args.arguments]
record = {
    'baselineId': baseline['baselineId'], 'toolPackage': package['name'],
    'toolVersion': package['version'], 'toolCliSha256': hashlib.sha256(cli.read_bytes()).hexdigest(),
    'command': command, 'startedAtUtc': datetime.now(timezone.utc).isoformat(),
    'stdout': str(result_path.relative_to(out)), 'stderr': str(log_path.relative_to(out)),
    'status': 'running',
}
with result_path.open('wb') as stdout, log_path.open('wb') as stderr:
    process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
    record['pid'] = process.pid
    record_path.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'run': str(record_path), 'pid': process.pid}), flush=True)
    record['exitCode'] = process.wait()
record['endedAtUtc'] = datetime.now(timezone.utc).isoformat()
record['status'] = 'finished'
for key, path in [('stdout', result_path), ('stderr', log_path)]:
    record[key + 'Sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    record[key + 'Bytes'] = path.stat().st_size
record_path.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'exitCode': record['exitCode'], 'stdoutBytes': record['stdoutBytes']}), flush=True)
sys.exit(record['exitCode'])
