#!/usr/bin/env python3
"""Generate schema evidence from the frozen CLI, without starting a server."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

workspace = Path(__file__).resolve().parents[2]
baseline = json.loads((workspace / '.analysis-local/current-baseline.json').read_text())
cli = Path(baseline['snapshotApplication']) / 'Contents/Resources/codex-cli/bin/codex'
out = workspace / 'analysis' / baseline['baselineId']
raw = out / 'raw' / 'protocol'
raw.mkdir(parents=True, exist_ok=True)
home = Path('/private/tmp/ccodex-behavior/protocol-home')
home.mkdir(exist_ok=True)
env = {k: v for k, v in os.environ.items() if not k.startswith('CODEX_')}
env['CODEX_HOME'] = str(home)
record = {'baselineId': baseline['baselineId'], 'observedAtUtc': datetime.now(timezone.utc).isoformat(),
          'cliPath': str(cli), 'cliSha256': hashlib.sha256(cli.read_bytes()).hexdigest(),
          'codexHome': str(home), 'runs': [], 'method': 'bundled-cli-schema-generation',
          'limitations': ['Generated schemas establish shipped CLI contracts, not coverage by a public release or runtime execution.']}
for label, extra in [('stable', []), ('experimental', ['--experimental'])]:
    destination = raw / label
    command = [str(cli), 'app-server', 'generate-json-schema', '--out', str(destination), *extra]
    result = subprocess.run(command, env=env, capture_output=True)
    (raw / (label + '.stdout')).write_bytes(result.stdout)
    (raw / (label + '.stderr')).write_bytes(result.stderr)
    files = [{'path': str(p.relative_to(raw)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}
             for p in sorted(destination.rglob('*.json'))]
    record['runs'].append({'command': command, 'exitCode': result.returncode, 'schemaFiles': files})
    if result.returncode != 0:
        break
(out / 'protocol-generation.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'runs': [{'exitCode': r['exitCode'], 'schemaFileCount': len(r['schemaFiles'])} for r in record['runs']]}))
