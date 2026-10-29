"""Run the finite 24-file import review and retain per-file terminal receipts."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
WORK = ROOT / '.analysis-local/command-consumers-work'
OUT = ROOT / 'analysis' / BASELINE
NODE = '/Users/nallylin/.nvm/versions/node/v22.23.2/bin/node'


def pin(path):
    data = path.read_bytes()
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def main():
    run = WORK / sys.argv[1]
    run.mkdir(parents=True, exist_ok=False)
    source = OUT / 'command-registration-contracts.json'
    contract = json.loads(source.read_text())
    candidates = contract['lexicalImporterCandidates']
    assert len(candidates) == 24
    indices = [int(value) for value in sys.argv[2:]] if len(sys.argv) > 2 else list(range(len(candidates)))
    assert len(set(indices)) == len(indices) and all(0 <= value < len(candidates) for value in indices)
    producers = [Path(__file__), ROOT / 'scripts/analysis/command_consumers_ast.mjs']
    for p in producers:
        (run / p.name).write_bytes(p.read_bytes())
    receipts = []
    for index in indices:
        candidate = candidates[index]
        directory = run / f'{index+1:02}'
        command = [NODE, '--max-old-space-size=4096', str(producers[1]), str(ROOT), BASELINE,
                   str(index), str(directory)]
        start, clock = datetime.now(timezone.utc).isoformat(), time.monotonic()
        result = subprocess.run(command, cwd=ROOT, capture_output=True)
        stdout, stderr = run / f'{index+1:02}-stdout.txt', run / f'{index+1:02}-stderr.txt'
        stdout.write_bytes(result.stdout)
        stderr.write_bytes(result.stderr)
        output = directory / 'source-contracts.json'
        receipts.append({'candidateIndex': index, 'sourcePath': candidate['sourcePath'], 'command': command,
                         'startedAtUtc': start, 'completedAtUtc': datetime.now(timezone.utc).isoformat(),
                         'wallTimeSeconds': time.monotonic()-clock, 'exitCode': result.returncode,
                         'inputContract': pin(source), 'output': pin(output) if output.exists() else None,
                         'stdout': pin(stdout), 'stderr': pin(stderr)})
        (run / 'receipts.json').write_text(json.dumps(receipts, ensure_ascii=False, indent=2)+'\n')
        print(result.stdout.decode(errors='replace'), end='', flush=True)
        if result.returncode:
            print(result.stderr.decode(errors='replace'), flush=True)
            return result.returncode
    assert len(receipts) == len(indices) and all(r['exitCode'] == 0 for r in receipts)
    assert all(pin(p) == pin(run / p.name) for p in producers)
    for p in run.rglob('*'):
        if p.is_file():
            p.chmod(0o444)
    print(json.dumps({'completed': True, 'importCandidatesReviewed': len(indices), 'modelSubmissionsAdded': 0}), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
