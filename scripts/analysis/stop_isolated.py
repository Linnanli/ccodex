#!/usr/bin/env python3
"""Stop only a test application whose PID still matches the recorded executable."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess

workspace = Path(__file__).resolve().parents[2]
record_path = workspace / '.analysis-local/current-runtime.json'
record = json.loads(record_path.read_text())
pid = int(record['pid'])
expected = str(Path(record['runtimeApplication']) / 'Contents/MacOS/ChatGPT')
actual = subprocess.run(['ps', '-p', str(pid), '-o', 'comm='], capture_output=True, text=True, check=False).stdout.strip()
if actual != expected:
    raise SystemExit('No matching owned application: no process changed.')
os.kill(pid, signal.SIGTERM)
record['stoppedAtUtc'] = datetime.now(timezone.utc).isoformat()
record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
archive = workspace / '.analysis-local/runtime' / record['baselineId'] / 'sessions'
archive.mkdir(exist_ok=True)
(archive / ('stopped-' + str(pid) + '.json')).write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'stoppedOwnedPid': pid, 'stoppedAtUtc': record['stoppedAtUtc']}))
