"""Acquire and checksum one official comparison runtime, without launching it."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.analysis-local/public-runtime-comparison-work/electron-42.3.0-01'
BASE_URL = 'https://github.com/electron/electron/releases/download/v42.3.0/'
ARCHIVE = 'electron-v42.3.0-darwin-x64.zip'


def fetch(name, limit):
    start, clock = datetime.now(timezone.utc).isoformat(), time.monotonic()
    output = OUT / name
    request = urllib.request.Request(BASE_URL + name, headers={'User-Agent': 'ccodex-analysis-public-runtime/1'})
    count, digest = 0, hashlib.sha256()
    with urllib.request.urlopen(request, timeout=30) as response, output.open('xb') as stream:
        while chunk := response.read(1024 * 1024):
            count += len(chunk)
            if count > limit or time.monotonic() - clock > 180:
                raise RuntimeError('Acquisition budget exceeded')
            digest.update(chunk)
            stream.write(chunk)
        status = response.status
    return {'url': BASE_URL + name, 'path': name, 'httpStatus': status, 'bytes': count,
            'sha256': digest.hexdigest(), 'completeRead': True, 'startedAtUtc': start,
            'completedAtUtc': datetime.now(timezone.utc).isoformat()}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    receipt = {'version': '42.3.0', 'platform': 'darwin', 'arch': 'x64', 'launched': False, 'downloads': []}
    try:
        sums = fetch('SHASUMS256.txt', 1000000)
        receipt['downloads'].append(sums)
        expected = [line.split()[0] for line in (OUT / 'SHASUMS256.txt').read_text().splitlines()
                    if line.split()[-1].lstrip('*') == ARCHIVE]
        assert len(expected) == 1
        receipt['expectedArchiveSha256'] = expected[0]
        archive = fetch(ARCHIVE, 300000000)
        receipt['downloads'].append(archive)
        assert archive['sha256'] == expected[0], 'Archive checksum mismatch'
        receipt['archiveChecksumVerified'] = True
        with zipfile.ZipFile(OUT / ARCHIVE) as package:
            assert all(not name.startswith('/') and '..' not in Path(name).parts for name in package.namelist())
        destination = OUT / 'unpacked'
        command = ['/usr/bin/ditto', '-x', '-k', str(OUT / ARCHIVE), str(destination)]
        result = subprocess.run(command, capture_output=True, timeout=60)
        receipt['extract'] = {'command': command, 'exitCode': result.returncode,
                              'stdout': result.stdout.decode(), 'stderr': result.stderr.decode()}
        assert result.returncode == 0
        binary = destination / 'Electron.app/Contents/MacOS/Electron'
        data = binary.read_bytes()
        receipt['binary'] = {'path': str(binary), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        receipt['status'] = 'acquired-checksummed-extracted; not-launched'
    except Exception as error:
        receipt['error'] = str(error)
        receipt['status'] = 'failed; not-launched'
    (OUT / 'acquisition.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
