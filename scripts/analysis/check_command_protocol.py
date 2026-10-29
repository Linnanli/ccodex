#!/usr/bin/env python3
"""Exercise pinned app-server command contracts with owned, non-model fixtures."""
from datetime import datetime, timezone
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import threading
import time

workspace = Path(__file__).resolve().parents[2]
baseline = json.loads((workspace / '.analysis-local/current-baseline.json').read_text())
out = workspace / 'analysis' / baseline['baselineId']
parser = argparse.ArgumentParser()
parser.add_argument('--run-name', default='sandboxed')
parser.add_argument('--cli-source', choices=['frozen', 'public-npm'], default='frozen')
args = parser.parse_args()
if not re.fullmatch(r'[a-zA-Z0-9_-]+', args.run_name):
    raise SystemExit('Invalid run name')
summary_path = out / ('command-protocol-' + args.run_name + '.json')
if summary_path.exists():
    raise SystemExit('Run exists; use a new name to preserve prior evidence')
raw = out / 'raw' / 'command-protocol' / args.run_name
raw.mkdir(parents=True, exist_ok=True)
run_root = Path('/private/tmp/ccodex-behavior/command-runs') / args.run_name
if run_root.exists():
    raise SystemExit('Fixture directory exists; use a new run name')
home = run_root / 'codex-home'
user_home = run_root / 'user-home'
fixture = run_root / 'fixture'
for directory in [home, user_home, fixture]:
    directory.mkdir(parents=True, mode=0o700)
generation_path = out / ('public-protocol-generation-npm.json' if args.cli_source == 'public-npm' else 'protocol-generation.json')
generation_bytes = generation_path.read_bytes()
generation = json.loads(generation_bytes)
if generation['baselineId'] != baseline['baselineId']:
    raise SystemExit('CLI provenance baseline differs')
if args.cli_source == 'public-npm' and generation.get('status') != 'complete':
    raise SystemExit('Public npm CLI has not completed verified export')
cli = Path(generation['cliPath'])
cli_hash = hashlib.sha256(cli.read_bytes()).hexdigest()
if cli_hash != generation['cliSha256']:
    raise SystemExit('CLI executable hash differs from generation manifest')
generation_snapshot = raw / 'cli-generation.json'
generation_snapshot.write_bytes(generation_bytes)
runner_snapshot = raw / 'runner-source.py'
runner_snapshot.write_bytes(Path(__file__).read_bytes())
env = {k: v for k, v in os.environ.items() if k in {'PATH', 'HOME', 'USER', 'LOGNAME', 'SHELL', 'LANG', 'LC_ALL', 'TMPDIR'}}
env['CODEX_HOME'] = str(home)
env['HOME'] = str(user_home)
command = [str(cli), '-c', 'cli_auth_credentials_store="file"', '-c', 'features.secret_auth_storage=false',
           'app-server', '--listen', 'stdio://']
records = []
messages = []
inbox = queue.Queue()
counter = 0


def send(method, params=None, notify=False):
    global counter
    message = {'method': method}
    if params is not None:
        message['params'] = params
    if not notify:
        counter += 1
        message['id'] = counter
    records.append({'direction': 'request', 'atMonotonic': time.monotonic(), 'message': message})
    process.stdin.write((json.dumps(message) + '\n').encode())
    process.stdin.flush()
    return message.get('id')


def await_message(predicate, seconds=10):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = inbox.get(timeout=max(0.001, deadline - time.monotonic()))
        messages.append(value)
        if predicate(value):
            return value
    raise TimeoutError('Expected protocol response did not arrive')


def request(method, params):
    identifier = send(method, params)
    return await_message(lambda m: m.get('id') == identifier)


def reader():
    for line in process.stdout:
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        # Preserve only fixture request responses and command notifications.
        # Account, login, history and token APIs are never requested.
        if 'id' in value or value.get('method', '').startswith('command/exec/'):
            records.append({'direction': 'response-or-notification', 'atMonotonic': time.monotonic(), 'message': value})
        inbox.put(value)


checks = []
error = None
with (raw / 'stderr.log').open('wb') as stderr:
    process = subprocess.Popen(command, cwd=fixture, env=env, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=stderr)
    threading.Thread(target=reader, daemon=True).start()
    try:
        initialized = request('initialize', {'clientInfo': {'name': 'ccodex_analysis_fixture', 'version': '1'},
                                             'capabilities': {'experimentalApi': False}})
        checks.append({'id': 'initialize', 'passed': 'result' in initialized})
        if 'result' not in initialized:
            raise RuntimeError('Initialize failed')
        send('initialized', notify=True)
        policy = {'type': 'readOnly', 'networkAccess': False}
        common = {'cwd': str(fixture), 'sandboxPolicy': policy, 'timeoutMs': 5000}
        completed = request('command/exec', {**common, 'command': ['/usr/bin/printf', 'ccodex-command-fixture\\n']})
        result = completed.get('result', {})
        checks.append({'id': 'command-completion', 'passed': result.get('exitCode') == 0 and result.get('stdout') == 'ccodex-command-fixture\n',
                       'observed': result, 'responseHasError': 'error' in completed})
        failed = request('command/exec', {**common, 'command': ['/usr/bin/false']})
        checks.append({'id': 'command-nonzero-exit', 'passed': failed.get('result', {}).get('exitCode') == 1,
                       'observed': failed.get('result'), 'responseHasError': 'error' in failed})
        invalid = request('command/exec', {**common, 'command': []})
        checks.append({'id': 'command-input-validation', 'passed': invalid.get('error', {}).get('code') == -32600,
                       'observedErrorCode': invalid.get('error', {}).get('code')})
        start = time.monotonic()
        running_id = send('command/exec', {**common, 'timeoutMs': 20000, 'processId': 'ccodex-cancel-fixture',
                                         'streamStdoutStderr': True,
                                         'command': ['/bin/sh', '-c', "printf 'fixture-ready\\n'; exec /bin/sleep 15"]})
        output_delta = await_message(lambda m: m.get('method') == 'command/exec/outputDelta' and
                                    m.get('params', {}).get('processId') == 'ccodex-cancel-fixture')
        delta = output_delta.get('params', {})
        decoded_delta = base64.b64decode(delta.get('deltaBase64', ''), validate=True).decode('utf8')
        terminated = request('command/exec/terminate', {'processId': 'ccodex-cancel-fixture'})
        final = next((m for m in messages if m.get('id') == running_id), None)
        if final is None:
            final = await_message(lambda m: m.get('id') == running_id)
        elapsed = time.monotonic() - start
        exit_code = final.get('result', {}).get('exitCode')
        checks.append({'id': 'command-stream-and-terminate', 'passed': 'result' in terminated and 'result' in final and
                       isinstance(exit_code, int) and exit_code != 0 and elapsed < 15 and
                       decoded_delta == 'fixture-ready\n',
                       'elapsedSeconds': elapsed, 'terminationResponse': terminated,
                       'streamOutputMatchesFixture': decoded_delta == 'fixture-ready\n',
                       'finalResponse': final})
    except Exception as exc:
        error = str(exc) or type(exc).__name__
    finally:
        process.stdin.close()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
for r in records:
    if r['message'].get('id') == 1 and 'result' in r['message']:
        r['message']['result'] = {'returnedKeys': sorted(r['message']['result'])}
record_path = raw / 'observations.jsonl'
record_path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records))
summary = {'baselineId': baseline['baselineId'], 'observedAtUtc': datetime.now(timezone.utc).isoformat(),
           'runName': args.run_name,
           'method': 'actual-' + args.cli_source + '-app-server-stdio-owned-command-fixture', 'command': command,
           'cliSource': args.cli_source, 'cliSha256': cli_hash, 'codexHome': str(home),
           'userHome': str(user_home), 'environmentPolicy': 'allowlist-with-dedicated-home-and-codex-home',
           'cliProvenance': {'path': str(generation_snapshot.relative_to(out)), 'originalPath': generation_path.name,
                             'sha256': hashlib.sha256(generation_bytes).hexdigest()},
           'runner': {'path': str(Path(__file__).relative_to(workspace)), 'snapshotPath': str(runner_snapshot.relative_to(out)),
                      'sha256': hashlib.sha256(runner_snapshot.read_bytes()).hexdigest()},
           'serverPid': process.pid, 'serverExitCode': process.returncode, 'checks': checks, 'error': error,
           'rawObservations': {'path': str(record_path.relative_to(out)), 'sha256': hashlib.sha256(record_path.read_bytes()).hexdigest()},
           'limitations': ['No desktop UI, terminal PTY, model turn, approval or thread recovery was tested.',
                           'These five command contracts do not establish compatibility of the complete backend.',
                           'File credential configuration was supplied; prevention of native credential migration was not established.',
                           'Only owned printf/false/sleep command fixtures were requested.']}
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'checks': [{'id': c['id'], 'passed': c['passed']} for c in checks], 'error': error, 'serverExitCode': process.returncode}))
