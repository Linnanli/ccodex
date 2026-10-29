"""Compare exact flag acceptance and actual local transport with the public Node."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / '.analysis-local/public-runtime-comparison-work'
OUT = WORK / 'node-permissions-01'


def pin(path):
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def main():
    acquisition = json.loads((WORK / 'electron-42.3.0-01/acquisition.json').read_text())
    assert acquisition['archiveChecksumVerified']
    binary = Path(acquisition['binary']['path'])
    assert pin(binary) == acquisition['binary']
    OUT.mkdir(parents=True, exist_ok=False)
    producer = ROOT / 'scripts/analysis/probe_public_node_permissions.cjs'
    script = OUT / producer.name
    script.write_bytes(producer.read_bytes())
    (OUT / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    receipts = []
    with tempfile.TemporaryDirectory(prefix='ccx-ep-', dir='/private/tmp') as temporary:
        socket = str(Path(temporary) / 'fixture.sock')
        environment = {'PATH': '/usr/bin:/bin', 'TMPDIR': temporary + '/', 'LANG': 'en_US.UTF-8', 'ELECTRON_RUN_AS_NODE': '1'}
        common = [str(binary), '--permission', '--allow-fs-read=*', '--allow-fs-write=*',
                  '--allow-addons', '--allow-child-process', '--allow-worker']
        commands = [('owl-ipc-flag', common + ['--allow-ipc=' + socket, '-e', 'console.log("owned flag accepted")']),
                    ('permission-local-transports', common + [str(script), str(OUT / 'observations.json'), socket])]
        for name, command in commands:
            receipt = {'id': name, 'command': command, 'startedAtUtc': datetime.now(timezone.utc).isoformat(),
                       'binary': pin(binary), 'environmentKeys': sorted(environment)}
            process = subprocess.Popen(command, cwd=OUT, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            receipt['pid'] = process.pid
            try:
                stdout, stderr = process.communicate(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate(timeout=5)
                receipt['timeout'] = True
            (OUT / (name + '-stdout.txt')).write_bytes(stdout)
            (OUT / (name + '-stderr.txt')).write_bytes(stderr)
            receipt.update({'exitCode': process.returncode, 'completedAtUtc': datetime.now(timezone.utc).isoformat(),
                            'stdout': pin(OUT / (name + '-stdout.txt')), 'stderr': pin(OUT / (name + '-stderr.txt'))})
            receipts.append(receipt)
            print(name, process.returncode, stdout.decode(), stderr.decode(), flush=True)
    (OUT / 'receipts.json').write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + '\n')
    (OUT / 'cleanup.json').write_text(json.dumps({'fixtureDirectoryRemoved': not Path(temporary).exists(),
                                                'socketRemoved': not Path(socket).exists()}, indent=2) + '\n')


if __name__ == '__main__':
    main()
