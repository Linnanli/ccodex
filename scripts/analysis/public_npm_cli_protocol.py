#!/usr/bin/env python3
"""Verify exact official npm platform archive, then export schemas in isolated directories."""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
from public_cli_protocol import sha256, save, utc


def verify_sri(path, integrity):
    algorithm, digest = integrity.split('-', 1)
    assert algorithm == 'sha512'
    actual = hashlib.sha512()
    with path.open('rb') as source:
        for part in iter(lambda: source.read(1024 * 1024), b''):
            actual.update(part)
    return base64.b64encode(actual.digest()).decode('ascii') == digest


def main():
    workspace = Path(__file__).resolve().parents[2]
    baseline = json.loads((workspace / '.analysis-local/current-baseline.json').read_text())
    out = workspace / 'analysis' / baseline['baselineId']
    raw = out / 'raw/public-cli-npm'
    main_metadata = raw / 'npm-codex-0.162.0.json'
    platform_metadata = raw / 'npm-codex-0.162.0-darwin-x64.json'
    main = json.loads(main_metadata.read_text())
    platform = json.loads(platform_metadata.read_text())
    public = json.loads((out / 'public-protocol-source.json').read_text())
    assert main['name'] == platform['name'] == '@openai/codex'
    assert main['version'] == '0.162.0' and platform['version'] == '0.162.0-darwin-x64'
    assert main['optionalDependencies']['@openai/codex-darwin-x64'] == 'npm:@openai/codex@0.162.0-darwin-x64'
    assert main['bin'] == {'codex': 'bin/codex.js'}
    assert platform['os'] == ['darwin'] and platform['cpu'] == ['x64']
    archives = [(main, main_metadata, raw / 'codex-0.162.0.tgz'),
                (platform, platform_metadata, raw / 'codex-0.162.0-darwin-x64.tgz')]
    record_path = out / 'public-protocol-generation-npm.json'
    if record_path.exists():
        raise RuntimeError('npm generation evidence already exists; preserve it')
    record = {'baselineId': baseline['baselineId'], 'recordedAtUtc': utc(),
              'publicTag': public['tag'], 'publicCommit': public['commit'],
              'source': 'registry.npmjs.org fixed official @openai/codex package versions',
              'npmGitHead': {'wrapper': main.get('gitHead'), 'platform': platform.get('gitHead')},
              'npmRelationToPublicCommit': 'unknown: neither exact npm metadata provides gitHead; version equality is not source identity',
              'releaseAssetDigestRelation': 'unknown: npm SRI is separate from the GitHub release asset SHA-256',
              'method': 'official-npm-platform-cli-schema-generation', 'status': 'verifying',
              'packages': [], 'runs': [], 'cliExecuted': False,
              'limitations': ['No npm install, package lifecycle script, login, server or model call is invoked.',
                              'Only the verified standalone native binary --version and schema generation subcommands are run.',
                              'Exact npm version is a public candidate; public Git commit identity and runtime compatibility remain unproven.']}
    prior_attempt = raw / 'generation-attempt1.json'
    if prior_attempt.exists():
        record['priorAttempts'] = [{'path': str(prior_attempt), 'sha256': sha256(prior_attempt)}]
    save(record_path, record)
    try:
        for metadata, metadata_path, archive in archives:
            assert metadata['dist']['tarball'] == 'https://registry.npmjs.org/@openai/codex/-/' + archive.name
            entry = {'name': metadata['name'], 'version': metadata['version'],
                     'metadataPath': str(metadata_path), 'metadataSha256': sha256(metadata_path),
                     'gitHead': metadata.get('gitHead'), 'dist': metadata['dist'],
                     'archivePath': str(archive), 'archiveBytes': archive.stat().st_size,
                     'archiveSha256': sha256(archive),
                     'distIntegrityVerified': verify_sri(archive, metadata['dist']['integrity']),
                     'distShasumVerified': hashlib.sha1(archive.read_bytes()).hexdigest() == metadata['dist']['shasum']}
            record['packages'].append(entry)
            save(record_path, record)
            if not entry['distIntegrityVerified'] or not entry['distShasumVerified']:
                raise RuntimeError('npm archive does not match dist.integrity/dist.shasum')
        local = workspace / '.analysis-local/public-cli-npm' / baseline['baselineId'] / '0.162.0-darwin-x64'
        bin_dir = local / 'bin'
        bin_dir.mkdir(parents=True, exist_ok=True)
        if any(bin_dir.iterdir()):
            raise RuntimeError('native binary directory must be empty')
        cli = bin_dir / 'codex'
        archive = archives[1][2]
        with tarfile.open(archive, 'r:gz') as package:
            member = package.getmember('package/vendor/x86_64-apple-darwin/bin/codex')
            if not member.isfile():
                raise RuntimeError('native binary member must be regular')
            with package.extractfile(member) as source, cli.open('xb') as target:
                shutil.copyfileobj(source, target, 1024 * 1024)
            os.chmod(cli, 0o700)
            record['archiveMember'] = {'name': member.name, 'bytes': member.size}
        record.update({'cliPath': str(cli), 'cliSha256': sha256(cli), 'cliBytes': cli.stat().st_size,
                       'scriptSha256': sha256(Path(__file__))})
        save(record_path, record)
        for label, extra in [('version', None), ('stable', []), ('experimental', ['--experimental'])]:
            home, temp, cwd = [local / folder / label for folder in ('homes', 'temp', 'working')]
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
            record.update(status='running-' + label, cliExecuted=True)
            save(record_path, record)
            result = subprocess.run(command, env=environment, cwd=cwd, capture_output=True, timeout=120)
            stdout, stderr = raw / (label + '.stdout'), raw / (label + '.stderr')
            stdout.write_bytes(result.stdout)
            stderr.write_bytes(result.stderr)
            run.update({'exitCode': result.returncode, 'endedAtUtc': utc(), 'stdout': str(stdout),
                        'stdoutSha256': sha256(stdout), 'stderr': str(stderr), 'stderrSha256': sha256(stderr),
                        'schemaFiles': [{'path': str(p.relative_to(raw)), 'sha256': sha256(p),
                                         'bytes': p.stat().st_size} for p in sorted(destination.rglob('*.json'))]})
            if label == 'version':
                record['versionOutput'] = result.stdout.decode('utf-8', errors='replace').strip()
            save(record_path, record)
            if result.returncode:
                raise RuntimeError(label + ' exited with ' + str(result.returncode))
        record.update(status='complete', cliHashUnchangedAfterInvocations=sha256(cli) == record['cliSha256'])
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
