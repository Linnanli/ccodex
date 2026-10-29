#!/usr/bin/env python3
"""Compare isolated app-server thread/fork rejection paths without model turns."""
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import threading
import time


WORKSPACE = Path(__file__).resolve().parents[2]
ABSENT_THREAD_ID = '00000000-0000-4000-8000-000000000004'
ABSENT_TURN_ID = '00000000-0000-4000-8000-000000000005'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def describe(path, relative_to=None):
    path = Path(path)
    return {'path': str(path.relative_to(relative_to) if relative_to else path),
            'bytes': path.stat().st_size, 'sha256': digest(path)}


def classify(response):
    if 'result' in response:
        return 'unexpected-success-stop'
    error = response.get('error', {})
    text = str(error.get('message', '')).lower()
    if any(s in text for s in ('invalid type', 'missing field', 'expected a boolean',
                                'expected a string', 'unknown variant')):
        return 'parameter-decoding-rejection'
    if 'experimental' in text and any(s in text for s in ('capabilit', 'experimentalapi',
                                                         'not enabled', 'requires')):
        return 'experimental-capability-rejection'
    if any(s in text for s in ('not found', 'no rollout found', 'could not find',
                               'does not exist', 'unknown thread', 'no such file')):
        return 'absent-thread-or-rollout-lookup-rejection'
    if 'prediction' in text:
        return 'prediction-specific-rejection'
    return 'other-rejection-review-raw-message'


def schema_evidence(out, generation, cli_source):
    schema_root = out / ('raw/public-cli-npm/schema' if cli_source == 'public-npm'
                         else 'raw/protocol')
    result = []
    for mode in ['stable', 'experimental']:
        path = schema_root / mode / 'v2/ThreadForkParams.json'
        manifest_path = ('schema/' if cli_source == 'public-npm' else '') + mode + '/v2/ThreadForkParams.json'
        entries = [f for run in generation['runs'] for f in run.get('schemaFiles', [])
                   if f['path'] == manifest_path]
        if len(entries) != 1 or digest(path) != entries[0]['sha256']:
            raise RuntimeError('ThreadForkParams schema differs from generation record')
        data = json.loads(path.read_bytes())
        result.append({**describe(path, out), 'mode': mode, 'generationEntry': entries[0], 'required': data.get('required'),
                       'experimentalPredictionModeDeclared': 'experimentalPredictionMode' in data['properties'],
                       'experimentalPredictionModeSchema': data['properties'].get('experimentalPredictionMode'),
                       'beforeTurnIdSchema': data['properties'].get('beforeTurnId'),
                       'ephemeralSchema': data['properties'].get('ephemeral'),
                       'additionalPropertiesExplicit': 'additionalProperties' in data,
                       'additionalPropertiesValue': data.get('additionalProperties'),
                       'unknownPropertiesSchemaDefault': 'allowed by JSON Schema when additionalProperties is absent; runtime behavior measured separately'})
    return result


def run_session(cli, root, raw, capability, run_name):
    label = 'experimental-client' if capability else 'stable-client-control'
    session_root, session_raw = root / label, raw / label
    session_raw.mkdir(mode=0o700)
    home, user_home, fixture, tmp = [session_root / p for p in ['codex-home', 'user-home', 'fixture', 'tmp']]
    for directory in [home, user_home, fixture, tmp]:
        directory.mkdir(parents=True, mode=0o700)
    initial_empty = {str(p): not any(p.iterdir()) for p in [home, user_home, fixture, tmp]}
    if not all(initial_empty.values()):
        raise RuntimeError('Disposable fixture must start empty')
    env = {'PATH': '/usr/bin:/bin', 'HOME': str(user_home), 'CODEX_HOME': str(home),
           'TMPDIR': str(tmp) + '/', 'LC_ALL': 'C', 'NO_COLOR': '1'}
    stderr_path = session_raw / 'stderr.log'
    profile_path = session_raw / 'sandbox.sb'
    # Network is denied for this app-server process and any subprocess. Writes are
    # confined to its own empty runtime root and its dedicated stderr file.
    profile = ('(version 1)\n(allow default)\n(deny network*)\n(deny file-write*)\n'
               '(allow file-write* (subpath ' + json.dumps(str(session_root)) + ') '
               '(literal ' + json.dumps(str(stderr_path)) + ') (literal "/dev/null"))\n')
    profile_path.write_text(profile)
    command = ['/usr/bin/sandbox-exec', '-f', str(profile_path), str(cli),
               '-c', 'cli_auth_credentials_store="file"', '-c', 'features.secret_auth_storage=false',
               '-c', 'sandbox_mode="read-only"', '-c', 'sandbox_workspace_write.network_access=false',
               '-c', 'approval_policy="never"', '-c', 'web_search="disabled"',
               'app-server', '--listen', 'stdio://']
    records, inbox, counter = [], queue.Queue(), 0
    checks, session_error, process = [], None, None
    records_lock = threading.Lock()

    def append_record(direction, message):
        with records_lock:
            records.append({'direction': direction, 'atMonotonic': time.monotonic(), 'message': message})

    def reader():
        for line in process.stdout:
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                append_record('non-json-stdout', {'text': line.decode('utf8', errors='replace')})
                continue
            # This process has an empty home and only fixture requests. Preserve
            # request errors verbatim; initialization paths are reduced to keys.
            recorded = value
            if value.get('id') == 1 and 'result' in value:
                recorded = {**value, 'result': {'returnedKeys': sorted(value['result'])}}
            append_record('response-or-notification', recorded)
            inbox.put(value)
        inbox.put({'fixtureReaderEof': True})

    def send(method, params=None, notify=False):
        nonlocal counter
        if method not in {'initialize', 'initialized', 'thread/fork'}:
            raise RuntimeError('Method outside negative fixture allowlist')
        message = {'method': method}
        if params is not None:
            message['params'] = params
        if not notify:
            counter += 1
            message['id'] = counter
        append_record('request', message)
        process.stdin.write((json.dumps(message) + '\n').encode())
        process.stdin.flush()
        return message.get('id')

    def request(method, params):
        identifier = send(method, params)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            try:
                message = inbox.get(timeout=max(0.001, deadline - time.monotonic()))
            except queue.Empty as exc:
                raise TimeoutError('No response before fixture deadline') from exc
            if message.get('fixtureReaderEof'):
                raise RuntimeError('App-server stdout closed before expected response')
            if message.get('method') in {'thread/started', 'turn/started'}:
                raise RuntimeError('Unexpected thread or turn started notification; stopped negative fixture')
            if message.get('id') == identifier:
                return message
        raise TimeoutError('Expected fixture response did not arrive')

    common = {'threadId': ABSENT_THREAD_ID, 'ephemeral': True, 'excludeTurns': True}
    cases = [
        ('without-prediction-field', {}),
        ('prediction-false', {'experimentalPredictionMode': False}),
        ('prediction-true', {'experimentalPredictionMode': True}),
        ('prediction-invalid-string', {'experimentalPredictionMode': 'ccodex-not-a-boolean'}),
        ('unknown-field-control', {'ccodexNegativeControlField': 'ccodex-not-a-boolean'}),
        ('known-ephemeral-invalid-string', {'ephemeral': 'ccodex-not-a-boolean'}),
        ('known-experimental-before-turn-id', {'beforeTurnId': ABSENT_TURN_ID}),
        ('known-experimental-before-turn-invalid-bool', {'beforeTurnId': True}),
    ]
    started_at = datetime.now(timezone.utc).isoformat()
    reader_thread = None
    with stderr_path.open('wb') as stderr:
        try:
            process = subprocess.Popen(command, cwd=fixture, env=env, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=stderr)
            reader_thread = threading.Thread(target=reader, daemon=True)
            reader_thread.start()
            initialized = request('initialize', {'clientInfo': {'name': 'ccodex_fork_negative_fixture',
                                                               'version': '1'},
                                                 'capabilities': {'experimentalApi': capability}})
            checks.append({'id': 'initialize', 'passed': 'result' in initialized,
                           'capabilityRequested': capability,
                           'response': {'id': initialized.get('id'),
                                        **({'resultKeys': sorted(initialized['result'])} if 'result' in initialized
                                           else {'error': initialized.get('error')})}})
            if 'result' not in initialized:
                raise RuntimeError('Fixture initialization failed')
            send('initialized', notify=True)
            for label, added in cases:
                params = {**common, **added}
                response = request('thread/fork', params)
                category = classify(response)
                checks.append({'id': label, 'requestParams': params, 'response': response,
                               'classification': category, 'returnedError': 'error' in response,
                               'classificationBasis': 'Error-message inspection; exact response retained for review'})
                if 'result' in response:
                    raise RuntimeError('Unexpected fork success for absent owned fixture UUID; stopped before any subsequent request')
        except Exception as exc:
            session_error = str(exc) or type(exc).__name__
        finally:
            if process is not None:
                try:
                    process.stdin.close()
                except (BrokenPipeError, OSError):
                    pass
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
                if reader_thread:
                    reader_thread.join(timeout=2)
    observations = session_raw / 'observations.jsonl'
    observations.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records))
    after = [{'path': str(p.relative_to(session_root)), 'bytes': p.stat().st_size}
             for p in sorted(session_root.rglob('*')) if p.is_file()]
    baseline_check = next((c for c in checks if c['id'] == 'without-prediction-field'), None)
    baseline_error = baseline_check.get('response', {}).get('error') if baseline_check else None
    for check in checks:
        if check['id'] != 'initialize':
            check['errorExactlyMatchesNoPredictionField'] = check['response'].get('error') == baseline_error
    return {'label': label if not checks else ('experimental-client' if capability else 'stable-client-control'),
            'experimentalApi': capability, 'startedAtUtc': started_at,
            'endedAtUtc': datetime.now(timezone.utc).isoformat(), 'command': command,
            'environment': env, 'runtimeRoot': str(session_root), 'initialEmptyDirectories': initial_empty,
            'policy': {'osNetwork': 'deny network* through sandbox-exec for app-server and children',
                       'osFileWrites': 'limited to the owned empty session root, dedicated stderr, /dev/null',
                       'modelToolSandbox': 'read-only config, workspace-write network_access=false',
                       'credentialConfig': 'file store plus features.secret_auth_storage=false; no credentials copied'},
            'sandboxProfile': describe(profile_path), 'serverPid': process.pid if process else None,
            'serverExitCode': process.returncode if process else None, 'checks': checks, 'error': session_error,
            'rawObservations': describe(observations), 'stderr': describe(stderr_path),
            'ownedRuntimeFilesAfter': after}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-name', required=True)
    parser.add_argument('--cli-source', choices=['frozen', 'public-npm'], required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', args.run_name):
        raise SystemExit('Invalid run name')
    baseline_path = WORKSPACE / '.analysis-local/current-baseline.json'
    baseline = json.loads(baseline_path.read_bytes())
    out = WORKSPACE / 'analysis' / baseline['baselineId']
    summary_path = out / ('fork-negative-protocol-' + args.run_name + '.json')
    raw = out / 'raw/fork-negative-protocol' / args.run_name
    run_root = Path('/private/tmp/ccodex-behavior/fork-negative-runs') / args.run_name
    if summary_path.exists() or raw.exists() or run_root.exists():
        raise SystemExit('Run exists; choose a fresh name to preserve all prior evidence')
    generation_path = out / ('public-protocol-generation-npm.json' if args.cli_source == 'public-npm'
                             else 'protocol-generation.json')
    generation_bytes = generation_path.read_bytes()
    generation = json.loads(generation_bytes)
    if generation['baselineId'] != baseline['baselineId']:
        raise SystemExit('Generation baseline differs')
    if args.cli_source == 'public-npm' and generation.get('status') != 'complete':
        raise SystemExit('Public npm export is incomplete')
    cli = Path(generation['cliPath'])
    cli_hash = digest(cli)
    if cli_hash != generation['cliSha256']:
        raise SystemExit('CLI hash differs from immutable generation record')
    schemas = schema_evidence(out, generation, args.cli_source)
    protected = [WORKSPACE / '.analysis-local/protocol-work' / n for n in
                 ['experimental-prediction-usage.json', 'evidence.jsonl',
                  'prediction-version-gate.json', 'prediction-version-gate-evidence.jsonl']]
    protected += [out / n for n in ['protocol-generation.json', 'public-protocol-generation-npm.json',
                                  'public-experimental-compatibility.json', 'public-experimental-compatibility.md',
                                  'exported-protocol-comparison.json', 'exported-protocol-comparison.md']]
    protected_hashes = [describe(p) for p in protected if p.exists()]
    raw.mkdir(parents=True, mode=0o700)
    run_root.mkdir(parents=True, mode=0o700)
    manifest_snapshot = raw / 'cli-generation.json'
    manifest_snapshot.write_bytes(generation_bytes)
    runner_snapshot = raw / 'runner-source.py'
    runner_snapshot.write_bytes(Path(__file__).read_bytes())
    sessions = []
    for experimental_api in [True, False]:
        session = run_session(cli, run_root, raw, experimental_api, args.run_name)
        sessions.append(session)
        if session['error']:
            break
    unchanged = all(digest(p['path']) == p['sha256'] for p in protected_hashes)
    cli_unchanged = digest(cli) == cli_hash
    summary = {'baselineId': baseline['baselineId'], 'observedAtUtc': datetime.now(timezone.utc).isoformat(),
               'runName': args.run_name, 'method': 'actual-isolated-' + args.cli_source + '-app-server-stdio-negative-thread-fork',
               'cliSource': args.cli_source, 'cliSha256': cli_hash, 'cliPath': str(cli),
               'cliHashUnchangedAfterRun': cli_unchanged,
               'cliProvenance': {**describe(manifest_snapshot, out), 'originalPath': str(generation_path)},
               'runner': {**describe(runner_snapshot, out), 'originalPath': str(Path(__file__))},
               'schemaInputs': schemas, 'baselineInput': describe(baseline_path),
               'fixture': {'absentThreadId': ABSENT_THREAD_ID, 'absentTurnId': ABSENT_TURN_ID,
                           'historyOrCredentialsCopied': False, 'targetTurnMethodsSent': [],
                           'methodAllowlist': ['initialize', 'initialized', 'thread/fork']},
               'sessions': sessions,
               'status': 'complete-negative-matrix' if len(sessions) == 2 and all(s['error'] is None for s in sessions) else 'incomplete-see-session-errors',
               'protectedArtifacts': [{**p, 'unchanged': digest(p['path']) == p['sha256']} for p in protected_hashes],
               'protectedArtifactsAllUnchanged': unchanged,
               'limitations': ['An error after decoding is not a successful thread fork or prediction execution.',
                               'The fixed UUID is absent in each fresh dedicated HOME/CODEX_HOME; no real thread or rollout is loaded.',
                               'Matching unknown-field and baseline errors only shows that the supplied unknown field was not rejected on this path; it does not establish complete compatibility.',
                               'Error classification uses message inspection; exact code/message/data are retained.',
                               'No thread/start, turn/start, model, login, account, history, command execution, or desktop app request was sent.',
                               'Npm publication-to-source-commit relation remains unknown.']}
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'summary': str(summary_path), 'status': summary['status'],
                      'cliSource': args.cli_source, 'sessions': [{'label': s['label'], 'error': s['error'],
                      'exitCode': s['serverExitCode'], 'checks': [{'id': c['id'],
                       'classification': c.get('classification'), 'response': c.get('response')} for c in s['checks']]}
                      for s in sessions], 'protectedUnchanged': unchanged}))
    if not unchanged or not cli_unchanged:
        raise SystemExit('Protected input changed')


if __name__ == '__main__':
    main()
