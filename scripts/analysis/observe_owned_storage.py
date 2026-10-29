#!/usr/bin/env python3
"""Read metadata/events only for the thread whose cwd is the owned UUID fixture."""
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import re
import sqlite3

parser = argparse.ArgumentParser()
parser.add_argument('--record-name', default='owned-task-storage-v2')
args = parser.parse_args()
assert re.fullmatch(r'[a-z0-9-]{1,64}', args.record_name), 'Invalid record name'
workspace = Path(__file__).resolve().parents[2]
session = json.loads((workspace / '.analysis-local/current-runtime.json').read_text())
fixture = json.loads((workspace / '.analysis-local/current-project-fixture.json').read_text())
assert fixture['runtimePid'] == session['pid'] and fixture['baselineId'] == session['baselineId']
home = Path(session['codexHome']).resolve()
database = home / 'state_5.sqlite'
destination = workspace / 'analysis' / session['baselineId'] / 'runtime-artifacts' / (args.record_name + '.json')
assert not destination.exists(), 'Preserve earlier observation'
wal = database.with_name(database.name + '-wal')
assert not wal.exists(), 'Immutable read cannot include pending WAL'
database_hash_before = hashlib.sha256(database.read_bytes()).hexdigest()
connection = sqlite3.connect(database.as_uri() + '?mode=ro&immutable=1', uri=True)
try:
    columns = {row[1] for row in connection.execute('PRAGMA table_info(threads)')}
    assert {'id', 'cwd', 'rollout_path'} <= columns, 'Required thread columns unavailable'
    rows = connection.execute('SELECT id,cwd,rollout_path FROM threads WHERE cwd=?', (fixture['root'],)).fetchall()
finally:
    connection.close()
assert not wal.exists() and hashlib.sha256(database.read_bytes()).hexdigest() == database_hash_before, 'Database changed during bounded query'
record = {'baselineId': session['baselineId'], 'action': 'owned-task-storage', 'runtimePid': session['pid'],
          'observationName': args.record_name,
          'observedAtUtc': datetime.now(timezone.utc).isoformat(), 'status': 'observed',
          'method': 'read-only-sqlite-exact-owned-cwd-and-owned-rollout-events',
          'databaseRead': {'mode': 'immutable-read-only-with-no-WAL-and-before-after-digest-check',
                           'sha256AtQuery': database_hash_before,
                           'limitations': 'This bounded unchanged-file observation is not an atomic live database snapshot.'},
          'observations': {'ownedCwdThreadCount': len(rows)},
          'limitations': ['No auth/keychain contents or unrelated thread rows are queried.',
                          'Only this UUID fixture thread is inspected; it does not establish storage behavior for all features.']}
if len(rows) == 1:
    thread_id, cwd, rollout_name = rows[0]
    rollout = Path(rollout_name).resolve()
    assert rollout.is_relative_to(home / 'sessions'), 'Do not read rollout outside owned sessions'
    assert rollout.stat().st_size < 10 * 1024 * 1024, 'Owned fixture rollout exceeds bounded size'
    data = rollout.read_bytes()
    lines = data.decode().splitlines()
    metadata = json.loads(lines[0])
    assert metadata['type'] == 'session_meta' and metadata['payload']['id'] == thread_id
    assert metadata['payload']['cwd'] == fixture['root'], 'Owned rollout identity differs'
    marker = 'CCODEX_DESKTOP_ANALYSIS_01：'
    expected = 'Sentinel: CCODEX_OWNED_FIXTURE_01'
    entries = [json.loads(line) for line in lines[1:]]
    prompt_indices = []
    prompt_events = []
    for index, entry in enumerate(entries):
        payload = entry.get('payload', {})
        if entry.get('type') == 'response_item' and payload.get('type') == 'message' and payload.get('role') == 'user':
            texts = [item.get('text', '') for item in payload.get('content', []) if isinstance(item, dict)]
            if any(text.startswith(marker) for text in texts):
                prompt_indices.append(index)
        if entry.get('type') == 'event_msg' and payload.get('type') == 'item_completed':
            item = payload.get('item', {})
            if item.get('type') == 'UserMessage' and marker in json.dumps(item.get('content', []), ensure_ascii=False):
                assert payload.get('thread_id') == thread_id, 'Prompt event belongs to another thread'
                prompt_events.append(payload)
    assert len(prompt_indices) == len(prompt_events) == 1, 'Expected exactly one owned prompt and matching completion event'
    turn_id = prompt_events[0]['turn_id']
    completions, tool_names, starts = [], [], []
    for index, entry in enumerate(entries):
        payload = entry.get('payload', {})
        if entry.get('type') == 'event_msg' and payload.get('type') == 'task_started' and payload.get('turn_id') == turn_id:
            starts.append({'timestamp': entry.get('timestamp'), 'turnId': payload.get('turn_id')})
        if entry.get('type') == 'event_msg' and payload.get('type') == 'task_complete' and payload.get('turn_id') == turn_id:
            reply = payload.get('last_agent_message', '')
            completions.append({'timestamp': entry.get('timestamp'), 'turnId': payload.get('turn_id'),
                                'expectedSentinelPresent': expected in reply,
                                'reply': reply if expected in reply and len(reply) <= 500 else None})
        if index > prompt_indices[0] and entry.get('type') == 'response_item' and payload.get('type') in ['function_call', 'custom_tool_call']:
            tool_names.append(payload.get('name'))
        if index > prompt_indices[0] and entry.get('type') == 'event_msg' and payload.get('type') == 'item_completed' and payload.get('item', {}).get('type') == 'UserMessage':
            assert payload.get('turn_id') == turn_id, 'Unexpected subsequent user turn in single-task fixture'
    assert len(starts) == 1 and len(completions) <= 1, 'Unexpected task lifecycle event count'
    readme_hash = hashlib.sha256((Path(fixture['root']) / 'README.md').read_bytes()).hexdigest()
    record['observations'].update({'threadId': thread_id, 'rolloutPathRelativeToOwnedHome': str(rollout.relative_to(home)),
                                  'rolloutSha256AtObservation': hashlib.sha256(data).hexdigest(),
                                  'rolloutBytesAtObservation': len(data), 'ownedPromptRecorded': True,
                                  'ownedPromptCount': len(prompt_indices), 'ownedTurnId': turn_id,
                                  'taskStartedEvents': starts, 'taskCompleteEvents': completions,
                                  'toolCallNamesAfterOwnedPrompt': tool_names,
                                  'fixtureReadmeSha256AtObservation': readme_hash,
                                  'fixtureReadmeUnchanged': readme_hash == fixture['files'][0]['sha256']})
runner_source = Path(__file__).read_bytes()
runner_snapshot = destination.parent.parent / 'raw/desktop-task' / ('runner-' + args.record_name + '.py')
runner_snapshot.parent.mkdir(parents=True, exist_ok=True)
with runner_snapshot.open('xb') as stream:
    stream.write(runner_source)
record['runner'] = {'path': str(runner_snapshot.relative_to(destination.parent.parent)),
                    'sha256': hashlib.sha256(runner_source).hexdigest()}
with destination.open('x') as stream:
    stream.write(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(record['observations'], ensure_ascii=False))
