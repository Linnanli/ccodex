#!/usr/bin/env python3
"""Verify a pinned official CLI asset and generate schemas without starting a server."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    workspace = Path(__file__).resolve().parents[2]
    baseline = json.loads((workspace / '.analysis-local/current-baseline.json').read_text())
    out = workspace / 'analysis' / baseline['baselineId']
    raw = out / 'raw/public-cli'
    public = json.loads((out / 'public-protocol-source.json').read_text())
    release_path = out / 'raw/public-protocol/release.json'
    release = json.loads(release_path.read_text())
    assert public['tag'] == release['tag_name'] == 'rust-v0.162.0'
    expected_release = next(item for item in public['downloads'] if item['path'] == 'raw/public-protocol/release.json')
    assert sha256(release_path) == expected_release['sha256']
    asset = next(item for item in release['assets'] if item['name'] == 'codex-x86_64-apple-darwin.tar.gz')
    assert asset['browser_download_url'] == ('https://github.com/openai/codex/releases/download/'
                                               'rust-v0.162.0/codex-x86_64-apple-darwin.tar.gz')
    archive = raw / asset['name']
    record_path = out / 'public-protocol-generation.json'
    if record_path.exists():
        raise RuntimeError('public generation record already exists; preserve existing evidence')
    record = {'baselineId': baseline['baselineId'], 'publicTag': public['tag'], 'publicCommit': public['commit'],
              'recordedAtUtc': utc(), 'releaseMetadataSha256': sha256(release_path),
              'asset': {k: asset[k] for k in ('id', 'name', 'size', 'digest', 'browser_download_url')},
              'archivePath': str(archive), 'downloadEvidenceDirectory': str(raw), 'runs': [],
              'method': 'official-release-cli-schema-generation', 'status': 'verifying',
              'limitations': ['Only --version and app-server generate-json-schema are invoked.',
                              'No app-server service, login, model call or runtime handler is exercised.',
                              'Public release is a comparison candidate, not an identical desktop CLI build.']}
    download_runs = raw / 'download-runs.json'
    if download_runs.exists():
        record['downloadRuns'] = json.loads(download_runs.read_text())
    save(record_path, record)
    try:
        archive_hash = sha256(archive)
        record['archiveSha256'] = archive_hash
        record['archiveBytes'] = archive.stat().st_size
        if archive_hash != asset['digest'].removeprefix('sha256:') or archive.stat().st_size != asset['size']:
            raise RuntimeError('downloaded asset does not match fixed official release size/digest')
        record['assetDigestVerified'] = True
        local = workspace / '.analysis-local/public-cli' / baseline['baselineId'] / public['tag']
        bin_dir = local / 'bin'
        bin_dir.mkdir(parents=True, exist_ok=False)
        cli = bin_dir / 'codex'
        with tarfile.open(archive, 'r:gz') as package:
            members = package.getmembers()
            candidates = [m for m in members if m.isfile() and Path(m.name).name in (
                'codex', 'codex-x86_64-apple-darwin')]
            if len(candidates) != 1:
                raise RuntimeError('expected exactly one matching CLI executable in release archive')
            member = candidates[0]
            with package.extractfile(member) as source, cli.open('xb') as target:
                shutil.copyfileobj(source, target, 1024 * 1024)
            os.chmod(cli, 0o700)
            record['archiveMember'] = {'name': member.name, 'bytes': member.size}
        record['cliPath'] = str(cli)
        record['cliSha256'] = sha256(cli)
        record['cliBytes'] = cli.stat().st_size
        record['scriptSha256'] = sha256(Path(__file__))
        save(record_path, record)
        for label, extra in [('version', None), ('stable', []), ('experimental', ['--experimental'])]:
            home = local / 'homes' / label
            temp = local / 'temp' / label
            cwd = local / 'working' / label
            for directory in (home, temp, cwd):
                directory.mkdir(parents=True, exist_ok=False)
            environment = {'PATH': '/usr/bin:/bin', 'CODEX_HOME': str(home), 'TMPDIR': str(temp),
                           'LC_ALL': 'C', 'NO_COLOR': '1'}
            destination = raw / 'schema' / label
            command = [str(cli), '--version'] if extra is None else [
                str(cli), 'app-server', 'generate-json-schema', '--out', str(destination), *extra]
            run = {'label': label, 'command': command, 'environment': environment, 'cwd': str(cwd),
                   'schemaRoot': str(raw), 'schemaPathsRelativeTo': 'schemaRoot',
                   'codexHomeEmptyBeforeInvocation': not any(home.iterdir()), 'startedAtUtc': utc()}
            record['runs'].append(run)
            record['status'] = 'running-' + label
            save(record_path, record)
            result = subprocess.run(command, env=environment, cwd=cwd, capture_output=True, timeout=120)
            stdout, stderr = raw / (label + '.stdout'), raw / (label + '.stderr')
            stdout.write_bytes(result.stdout)
            stderr.write_bytes(result.stderr)
            run.update({'exitCode': result.returncode, 'endedAtUtc': utc(),
                        'stdout': str(stdout), 'stdoutSha256': sha256(stdout),
                        'stderr': str(stderr), 'stderrSha256': sha256(stderr),
                        'schemaFiles': [{'path': str(p.relative_to(raw)), 'sha256': sha256(p),
                                         'bytes': p.stat().st_size} for p in sorted(destination.rglob('*.json'))]})
            if label == 'version':
                record['versionOutput'] = result.stdout.decode('utf-8', errors='replace').strip()
            save(record_path, record)
            if result.returncode:
                raise RuntimeError(label + ' generation exited with ' + str(result.returncode))
        record['cliHashUnchangedAfterInvocations'] = sha256(cli) == record['cliSha256']
        record['status'] = 'complete'
        save(record_path, record)
        print(json.dumps({'record': str(record_path), 'version': record.get('versionOutput'),
                          'runs': [{'label': r['label'], 'exitCode': r['exitCode'],
                                    'schemaFileCount': len(r['schemaFiles'])} for r in record['runs']]}))
        return 0
    except Exception as error:
        record.update(status='failed', failure=str(error), endedAtUtc=utc())
        save(record_path, record)
        raise


if __name__ == '__main__':
    sys.exit(main())
