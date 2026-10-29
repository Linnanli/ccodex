"""Bounded batch ownership analysis of every frozen legacy entry source."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
WORK = ROOT / '.analysis-local/entry-family-work'
OUT = ROOT / 'analysis' / BASELINE
NODE = '/Users/nallylin/.nvm/versions/node/v22.23.2/bin/node'


def pin(path):
    data = path.read_bytes()
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def main():
    run = WORK / sys.argv[1]
    run.mkdir(parents=True, exist_ok=False)
    ledger = json.loads((OUT / 'functional-entry-ledger.json').read_text())
    sources = sorted({e['sourceCoordinates']['sourcePath'] for e in ledger['entries']})
    producers = [Path(__file__), ROOT / 'scripts/analysis/entry_family_ast.mjs']
    for source in producers:
        (run / source.name).write_bytes(source.read_bytes())
    receipts = []
    for index, source in enumerate(sources, 1):
        dest = run / f'{index:02}-source.json'
        command = [NODE, '--max-old-space-size=4096', str(producers[1]), str(ROOT), BASELINE, source, str(dest)]
        start = datetime.datetime.now(datetime.timezone.utc).isoformat()
        clock = time.monotonic()
        result = subprocess.run(command, cwd=ROOT, capture_output=True)
        for name, data in [('stdout', result.stdout), ('stderr', result.stderr)]:
            (run / f'{index:02}-{name}.txt').write_bytes(data)
        receipt = {'sourcePath': source, 'command': command, 'startedAtUtc': start,
                   'completedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   'wallTimeSeconds': time.monotonic() - clock, 'exitCode': result.returncode,
                   'output': {'path': dest.name, **pin(dest)} if dest.exists() else None}
        receipts.append(receipt)
        (run / 'receipts.json').write_text(json.dumps(receipts, ensure_ascii=False, indent=2)+'\n')
        print(result.stdout.decode(errors='replace'), end='', flush=True)
        if result.returncode:
            print(result.stderr.decode(errors='replace'), flush=True)
            return result.returncode
    assert len(receipts) == 9 and all(x['exitCode'] == 0 for x in receipts)
    assert all(pin(p) == pin(run / p.name) for p in producers)
    for p in run.iterdir():
        p.chmod(0o444)
    print(json.dumps({'completed': True, 'sourceFiles': len(receipts), 'modelSubmissionsAdded': 0}), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
