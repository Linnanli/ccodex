#!/usr/bin/env python3
"""Freeze a desktop release and index its ASAR without executing app code."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import plistlib
import shutil
import struct
import subprocess
from datetime import datetime, timezone


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def asar_entries(archive):
    with archive.open('rb') as stream:
        size_pickle, header_size, payload_size, json_size = struct.unpack('<4I', stream.read(16))
        if size_pickle != 4 or not 0 < json_size <= 64 * 1024 * 1024:
            raise ValueError('Unexpected ASAR header')
        header = json.loads(stream.read(json_size))
    entries = []

    def walk(items, prefix=''):
        for name, value in items.items():
            name = prefix + name
            if 'files' in value:
                walk(value['files'], name + '/')
            else:
                relative = PurePosixPath(name)
                if relative.is_absolute() or '..' in relative.parts:
                    raise ValueError('Unsafe archive path: ' + name)
                entries.append((name, value))

    walk(header['files'])
    return 8 + header_size, entries


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--app', default='/Applications/ChatGPT.app')
    parser.add_argument('--workspace', default=str(Path(__file__).resolve().parents[2]))
    args = parser.parse_args()
    app = Path(args.app).resolve()
    workspace = Path(args.workspace).resolve()
    source_info = (app / 'Contents/Info.plist').read_bytes()
    info = plistlib.loads(source_info)
    archive = app / 'Contents/Resources/app.asar'
    archive_hash = digest(archive)
    baseline_id = 'codex-' + info['CFBundleShortVersionString'] + '-' + archive_hash[:12]
    local = workspace / '.analysis-local/baselines' / baseline_id
    output = workspace / 'analysis' / baseline_id
    local.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    snapshot = local / app.name
    if not snapshot.exists():
        result = subprocess.run(['cp', '-cR', str(app), str(snapshot)], capture_output=True, text=True)
        if result.returncode:
            if snapshot.exists():
                raise RuntimeError('Partial snapshot exists; inspect before retry: ' + result.stderr)
            shutil.copytree(app, snapshot, symlinks=True)
    frozen_archive = snapshot / 'Contents/Resources/app.asar'
    if digest(frozen_archive) != archive_hash:
        raise RuntimeError('Snapshot archive hash mismatch')
    if digest(archive) != archive_hash or (app / 'Contents/Info.plist').read_bytes() != source_info:
        raise RuntimeError('Installed release changed during snapshot')

    disk_files = []
    for root, dirs, names in os.walk(snapshot, followlinks=False):
        for name in sorted(dirs + names):
            path = Path(root) / name
            if path.is_symlink():
                disk_files.append({'sourcePath': path.relative_to(snapshot).as_posix(), 'kind': 'symlink', 'target': os.readlink(path)})
            elif path.is_file():
                disk_files.append({'sourcePath': path.relative_to(snapshot).as_posix(), 'kind': 'file', 'bytes': path.stat().st_size, 'sha256': digest(path)})

    offset, entries = asar_entries(frozen_archive)
    extracted = local / 'extracted'
    extracted.mkdir(exist_ok=True)
    unpacked = snapshot / 'Contents/Resources/app.asar.unpacked'
    archive_files = []
    errors = []
    with frozen_archive.open('rb') as stream:
        for name, value in entries:
            record = {'sourcePath': 'app.asar/' + name, 'archivePath': name, 'kind': 'asar-file', 'unpacked': bool(value.get('unpacked'))}
            target = extracted / name
            if 'link' in value:
                record.update(kind='asar-link', target=value['link'])
                archive_files.append(record)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if value.get('unpacked'):
                source = unpacked / name
                if not source.exists():
                    errors.append({'path': name, 'error': 'Missing unpacked file'})
                    archive_files.append(record)
                    continue
                data = source.read_bytes()
            else:
                stream.seek(offset + int(value['offset']))
                data = stream.read(value['size'])
                if len(data) != value['size']:
                    raise RuntimeError('Truncated archive member: ' + name)
                record['archiveByteOffset'] = offset + int(value['offset'])
            record.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), extension=Path(name).suffix.lower())
            if not target.exists() or digest(target) != record['sha256']:
                target.write_bytes(data)
            target.chmod(0o444)
            archive_files.append(record)

    baseline = {
        'baselineId': baseline_id,
        'capturedAtUtc': datetime.now(timezone.utc).isoformat(),
        'sourceApplication': str(app),
        'snapshotApplication': str(snapshot),
        'snapshotArchive': str(frozen_archive),
        'extractedDirectory': str(extracted),
        'application': {k: info.get(k) for k in ['CFBundleName', 'CFBundleIdentifier', 'CFBundleShortVersionString', 'CFBundleVersion']},
        'archiveSha256': archive_hash,
        'infoPlistSha256': hashlib.sha256(source_info).hexdigest(),
        'platform': os.uname().sysname,
        'machine': os.uname().machine,
        'snapshotVerifiedAgainstSource': True,
        'diskFileCount': len(disk_files),
        'archiveMemberCount': len(archive_files),
        'extractionErrors': errors,
        'analysisStatus': 'baseline-frozen',
    }
    (output / 'baseline.json').write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + '\n')
    (output / 'files.json').write_text(json.dumps({'baselineId': baseline_id, 'applicationFiles': disk_files, 'archiveFiles': archive_files}, ensure_ascii=False, indent=2) + '\n')
    (workspace / '.analysis-local/current-baseline.json').write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'baselineId': baseline_id, 'output': str(output), 'snapshot': str(snapshot), 'extracted': str(extracted), 'archiveMembers': len(archive_files), 'extractionErrors': errors}, ensure_ascii=False))


if __name__ == '__main__':
    main()
