#!/usr/bin/env python3
"""Freeze official published protocol sources; never execute downloaded code."""
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess

workspace = Path(__file__).resolve().parents[2]
baseline = json.loads((workspace / '.analysis-local/current-baseline.json').read_text())
out = workspace / 'analysis' / baseline['baselineId']
raw = out / 'raw' / 'public-protocol'
raw.mkdir(parents=True, exist_ok=True)
tag = 'rust-v0.162.0'
fetched = []


def fetch(url, relative):
    destination = raw / relative
    if destination.exists() and destination.stat().st_size:
        data = destination.read_bytes()
        mode = 'reused-existing-download'
    else:
        # Use the host's configured curl trust/proxy path. No authentication is supplied.
        result = subprocess.run(['curl', '--location', '--max-redirs', '3', '--fail', '--silent', '--show-error', '--max-time', '45', url],
                                capture_output=True, timeout=50)
        if result.returncode:
            (raw / 'last-download-failure.json').write_text(json.dumps({'url': url, 'exitCode': result.returncode,
                                                                      'stderr': result.stderr.decode('utf8', errors='replace')}, indent=2) + '\n')
            raise RuntimeError('Public source download failed; see last-download-failure.json')
        data = result.stdout
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        mode = 'downloaded'
    fetched.append({'url': url, 'path': str(destination.relative_to(out)),
                    'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'mode': mode})
    return data


ref = json.loads(fetch('https://api.github.com/repos/openai/codex/git/ref/tags/' + tag, 'ref.json'))
obj = ref['object']
while obj['type'] == 'tag':
    obj = json.loads(fetch(obj['url'], 'tag-' + obj['sha'] + '.json'))['object']
assert obj['type'] == 'commit'
commit = obj['sha']
commit_info = json.loads(fetch('https://api.github.com/repos/openai/codex/git/commits/' + commit, 'commit.json'))
release = json.loads(fetch('https://api.github.com/repos/openai/codex/releases/tags/' + tag, 'release.json'))
schema_root = 'codex-rs/app-server-protocol/schema/json/'
# API directory access is not required. Enumerate the contracts actually compared;
# do not infer a count or absence for all files in the public repository.
names = ['ClientRequest.json', 'ClientNotification.json', 'ServerRequest.json', 'ServerNotification.json',
         'codex_app_server_protocol.v2.schemas.json', 'CommandExecutionRequestApprovalResponse.json',
         'FileChangeRequestApprovalResponse.json', 'PermissionsRequestApprovalResponse.json',
         'ToolRequestUserInputResponse.json']
selected = [schema_root + name for name in names]
jobs = [(p, 'schema/' + p[len(schema_root):]) for p in selected]
jobs += [(p, 'source/' + p) for p in ['codex-rs/app-server-protocol/src/protocol/common.rs',
                                    'codex-rs/app-server-protocol/src/export.rs', 'codex-rs/app-server/README.md']]
with ThreadPoolExecutor(max_workers=4) as pool:
    futures = [pool.submit(fetch, 'https://raw.githubusercontent.com/openai/codex/' + commit + '/' + p, relative)
               for p, relative in jobs]
    failures = []
    for (p, _), future in zip(jobs, futures):
        try:
            future.result()
        except Exception as error:
            failures.append({'sourcePath': p, 'error': str(error)})
record = {'baselineId': baseline['baselineId'], 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
          'repository': 'https://github.com/openai/codex', 'tag': tag, 'commit': commit,
          'commitDate': commit_info['committer']['date'], 'publishedAt': release['published_at'],
          'releaseUrl': release['html_url'], 'selectionReason': 'Published 0.162.0 candidate for the shipped 0.162.0-alpha.17.2 CLI; identity/compatibility not assumed',
          'status': 'partial' if failures else 'downloaded', 'selectedSchemaFiles': selected,
          'downloads': sorted(fetched, key=lambda x: x['path']), 'failures': failures,
          'limitations': ['Checked-in public schemas are contract evidence; no public app-server runtime was built or launched.',
                          'Public tag postdates the desktop baseline and is a comparison candidate, not an exact source match.']}
(out / 'public-protocol-source.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'tag': tag, 'commit': commit, 'status': record['status'], 'downloadedFiles': len(fetched), 'failures': failures}, ensure_ascii=False))
