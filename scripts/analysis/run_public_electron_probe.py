"""Launch only the checksummed public comparison runtime with owned local data."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / '.analysis-local/public-runtime-comparison-work'
ACQUIRED = WORK / 'electron-42.3.0-01'


def pin(path):
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def main():
    acquired = json.loads((ACQUIRED / 'acquisition.json').read_text())
    assert acquired['archiveChecksumVerified'] and acquired['version'] == '42.3.0'
    binary = Path(acquired['binary']['path'])
    assert pin(binary) == acquired['binary']
    assert Path(sys.argv[1]).name == sys.argv[1]
    output = WORK / sys.argv[1]
    output.mkdir(parents=True, exist_ok=False)
    probe_name = sys.argv[2] if len(sys.argv) > 2 else 'probe_public_electron.cjs'
    assert probe_name in ['probe_public_electron.cjs', 'probe_public_browser_ownership.cjs',
                          'probe_public_browser_settings.cjs', 'probe_public_browser_settings_guest.cjs',
                          'probe_public_history_duplicate.cjs']
    script = ROOT / 'scripts/analysis' / probe_name
    copied = output / script.name
    copied.write_bytes(script.read_bytes())
    (output / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    for directory in ['data', 'tmp', 'chromium-user-data']:
        (output / directory).mkdir()
    command = [str(binary), '--user-data-dir=' + str(output / 'chromium-user-data'),
               str(copied), '--ccodex-owned-output=' + str(output / 'data')]
    environment = {'PATH': '/usr/bin:/bin', 'TMPDIR': str(output / 'tmp') + '/', 'LANG': 'en_US.UTF-8'}
    receipt = {'command': command, 'startedAtUtc': datetime.now(timezone.utc).isoformat(),
               'binary': pin(binary), 'probe': pin(copied), 'originalClientRunsAdded': 0,
               'modelSubmissionsAdded': 0, 'environmentKeys': sorted(environment),
               'publicRuntimeRunsAdded': 1}
    if probe_name in ['probe_public_browser_settings.cjs', 'probe_public_browser_settings_guest.cjs',
                      'probe_public_history_duplicate.cjs']:
        archive = ACQUIRED / 'electron-v42.3.0-darwin-x64.zip'
        assert pin(archive)['sha256'] == acquired['expectedArchiveSha256']
        relative = 'Electron.app/Contents/Frameworks/Electron Framework.framework/Versions/A/Electron Framework'
        framework = ACQUIRED / 'unpacked' / relative
        with zipfile.ZipFile(archive) as zipped:
            archived = hashlib.sha256(zipped.read(relative)).hexdigest()
        assert pin(framework)['sha256'] == archived
        receipt['runtimeIntegrity'] = {'archive': pin(archive), 'framework': pin(framework),
                                       'frameworkMatchesChecksummedArchive': True}
    process = subprocess.Popen(command, cwd=output, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    receipt['pid'] = process.pid
    try:
        stdout, stderr = process.communicate(timeout=55 if probe_name == 'probe_public_browser_settings_guest.cjs' else 35)
        (output / 'stdout.txt').write_bytes(stdout)
        (output / 'stderr.txt').write_bytes(stderr)
        receipt.update({'exitCode': process.returncode, 'stdout': pin(output / 'stdout.txt'),
                        'stderr': pin(output / 'stderr.txt')})
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate(timeout=5)
        (output / 'stdout.txt').write_bytes(stdout)
        (output / 'stderr.txt').write_bytes(stderr)
        receipt.update({'exitCode': process.returncode, 'timeout': True,
                        'stdout': pin(output / 'stdout.txt'), 'stderr': pin(output / 'stderr.txt')})
    receipt['completedAtUtc'] = datetime.now(timezone.utc).isoformat()
    (output / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    observation = output / 'data/runtime-observations.json'
    observed = json.loads(observation.read_text()) if observation.exists() else None
    if probe_name == 'probe_public_history_duplicate.cjs':
        print(json.dumps({'pid': receipt['pid'], 'exitCode': receipt['exitCode'],
                          'receiptPath': str(output / 'receipt.json'),
                          'counts': observed.get('counts') if observed else None,
                          'errors': observed.get('errors') if observed else None}, ensure_ascii=False))
    else:
        print(json.dumps({'receipt': receipt, 'observation': observed}, ensure_ascii=False))


if __name__ == '__main__':
    main()
