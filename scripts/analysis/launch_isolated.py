#!/usr/bin/env python3
"""Launch the frozen app using its supported isolated-profile environment."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
from datetime import datetime, timezone

workspace = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--environment-policy', choices=['inherit', 'allowlist-force-cli'], default='inherit')
parser.add_argument('--profile-name')
args = parser.parse_args()
if args.profile_name and not __import__('re').fullmatch(r'[a-z0-9-]{1,30}', args.profile_name):
    raise SystemExit('Profile name must use 1–30 lowercase letters, digits or hyphens')
baseline = json.loads((workspace / '.analysis-local/current-baseline.json').read_text())
current = workspace / '.analysis-local/current-runtime.json'
if current.exists():
    prior = json.loads(current.read_text())
    expected = str(Path(prior['runtimeApplication']) / 'Contents/MacOS/ChatGPT')
    actual = subprocess.run(['ps', '-p', str(prior['pid']), '-o', 'comm='], capture_output=True, text=True).stdout.strip()
    if actual == expected:
        print(json.dumps({'reusedVerifiedLiveRuntime': prior}, ensure_ascii=False))
        raise SystemExit(0)
runtime = workspace / '.analysis-local/runtime' / baseline['baselineId']
runtime.mkdir(parents=True, exist_ok=True)
short_runtime = Path('/private/tmp/ccodex-behavior') / (args.profile_name or baseline['archiveSha256'][:12])
short_runtime.mkdir(parents=True, exist_ok=True)
profile = short_runtime / 'user-data'
codex_home = short_runtime / 'codex-home'
profile.mkdir(exist_ok=True)
codex_home.mkdir(exist_ok=True)
application = runtime / 'ChatGPT.app'
if not application.exists():
    subprocess.run(['cp', '-cR', baseline['snapshotApplication'], str(application)], check=True)
with socket.socket() as server:
    server.bind(('127.0.0.1', 0))
    port = server.getsockname()[1]
command = [
    str(application / 'Contents/MacOS/ChatGPT'),
    '--remote-debugging-address=127.0.0.1',
    '--remote-debugging-port=' + str(port),
    '--user-data-dir=' + str(profile),
    '--use-mock-keychain',
]
env = os.environ.copy() if args.environment_policy == 'inherit' else {
    key: os.environ[key] for key in ['PATH', 'HOME', 'USER', 'LOGNAME', 'SHELL', 'LANG', 'LC_ALL', 'TMPDIR']
    if key in os.environ}
env.update(CODEX_HOME=str(codex_home), CODEX_ELECTRON_USER_DATA_PATH=str(profile))
cli = application / 'Contents/Resources/codex-cli/bin/codex'
if args.environment_policy == 'allowlist-force-cli':
    env.update(CODEX_APP_SERVER_FORCE_CLI='1', CODEX_CLI_PATH=str(cli))
log = runtime / 'desktop-startup.log'
log_start = log.stat().st_size if log.exists() else 0
with log.open('ab') as stream:
    process = subprocess.Popen(command, env=env, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
record = {
    'baselineId': baseline['baselineId'],
    'launchedAtUtc': datetime.now(timezone.utc).isoformat(),
    'pid': process.pid,
    'runtimeApplication': str(application),
    'debugEndpoint': 'http://127.0.0.1:' + str(port),
    'profileDirectory': str(profile),
    'codexHome': str(codex_home),
    'command': command,
    'log': str(log),
    'logStartByte': log_start,
    'environmentPolicy': args.environment_policy,
    'inheritedCodexEnvironmentNames': sorted(k for k in env if k.startswith('CODEX_') and k not in {
        'CODEX_HOME', 'CODEX_ELECTRON_USER_DATA_PATH', 'CODEX_APP_SERVER_FORCE_CLI', 'CODEX_CLI_PATH'}),
    'requestedCli': {'path': str(cli), 'sha256': hashlib.sha256(cli.read_bytes()).hexdigest()},
    'finalEnvironmentVerified': False,
    'isolationEvidence': [
        '.vite/build/bootstrap-CooIJpZm.js: CODEX_ELECTRON_USER_DATA_PATH sets app userData',
        '.vite/build/application-network-startup-CfAQmSYg.js: CODEX_HOME override',
        '.vite/build/main-CqEoQDOU.js: launch-demo-instance uses both overrides',
    ],
    'authenticationState': 'no credentials copied; app may import account state; anonymity not established',
}
(runtime / 'sessions').mkdir(exist_ok=True)
(runtime / 'sessions' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')).write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
(runtime / 'session.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
(workspace / '.analysis-local/current-runtime.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(record, ensure_ascii=False))
