#!/usr/bin/env python3
"""Record owned process paths and task-profile open-file evidence without credentials."""
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

workspace = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--record-name', default='runtime-process-verification-normalized')
args = parser.parse_args()
if not args.record_name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.record_name):
    raise SystemExit('Record name must contain only lowercase letters, digits and hyphens')
session = json.loads((workspace / '.analysis-local/current-runtime.json').read_text())
published = workspace / 'analysis' / session['baselineId']
destination = published / (args.record_name + '.json')
if destination.exists():
    raise SystemExit('Preserve previous verification; destination already exists')
expected = str(Path(session['runtimeApplication']) / 'Contents/MacOS/ChatGPT')
data = subprocess.run(['/bin/ps', '-axo', 'pid=,ppid=,comm='], capture_output=True, text=True, check=True).stdout
processes = {}
for line in data.splitlines():
    fields = line.strip().split(None, 2)
    if len(fields) == 3:
        processes[int(fields[0])] = {'pid': int(fields[0]), 'parentPid': int(fields[1]), 'executable': fields[2]}
root = processes.get(session['pid'])
if not root or root['executable'] != expected:
    raise SystemExit('Recorded owned application is not live; no other processes were inspected.')
owned = {session['pid']}
while True:
    added = {pid for pid, entry in processes.items() if entry['parentPid'] in owned} - owned
    if not added:
        break
    owned |= added
selected = [processes[pid] for pid in sorted(owned)]
cli = session['requestedCli']['path']
native_cli = str((Path(cli).parent / '../CodexCLI.app/Contents/MacOS/codex').resolve())
inventory = json.loads((published / 'files.json').read_text())
native_relative = str(Path(native_cli).relative_to(Path(session['runtimeApplication']).resolve()))
native_inventory = next(row for row in inventory['applicationFiles'] if row['sourcePath'] == native_relative)
native_hash = hashlib.sha256(Path(native_cli).read_bytes()).hexdigest()
if native_hash != native_inventory['sha256']:
    raise SystemExit('Runtime CLI differs from frozen inventory')
cli_entries = [entry for entry in selected if str(Path(entry['executable']).resolve()) in {str(Path(cli).resolve()), native_cli}]
profile_files = []
for pid in sorted(owned):
    result = subprocess.run(['/usr/sbin/lsof', '-n', '-P', '-a', '-p', str(pid), '-Ffn'], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if line.startswith('n') and line[1:].startswith(session['profileDirectory'] + '/'):
            profile_files.append({'pid': pid, 'taskProfileRelativePath': str(Path(line[1:]).relative_to(session['profileDirectory']))})
stdio = []
for entry in cli_entries:
    result = subprocess.run(['/usr/sbin/lsof', '-n', '-P', '-a', '-p', str(entry['pid']), '-d', '0,1', '-Fft'], capture_output=True, text=True)
    stdio.append({'pid': entry['pid'], 'fdTypes': [line for line in result.stdout.splitlines() if line[:1] in {'f', 't'}]})
record = {'baselineId': session['baselineId'], 'observedAtUtc': datetime.now(timezone.utc).isoformat(),
          'runtimePid': session['pid'], 'method': 'owned-process-executable-and-task-profile-open-files',
          'ownedProcessTree': selected, 'requestedCliDescendants': cli_entries,
          'requestedCliSha256': hashlib.sha256(Path(cli).read_bytes()).hexdigest(),
          'nativeCliSha256': native_hash, 'cliStandardDescriptors': stdio,
          'nativeCliFrozenInventoryMatch': {'sourcePath': native_relative, 'sha256': native_inventory['sha256'],
                                           'bytes': native_inventory['bytes'], 'matches': True},
          'taskProfileOpenFiles': profile_files,
          'limitations': ['No environment values, process argument strings, file contents or credentials were read.',
                          'Open-file evidence establishes use of the requested profile, not exclusive storage or credential isolation.',
                          'File-descriptor types, including Unix sockets, do not identify a complete transport or protocol.',
                          'Descendant executable identity does not identify each process role or prove final environment values.']}
destination.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'runtimePid': session['pid'], 'ownedProcesses': len(selected), 'frozenCliDescendants': len(cli_entries),
                  'taskProfileOpenFiles': len(profile_files), 'stdio': stdio}))
