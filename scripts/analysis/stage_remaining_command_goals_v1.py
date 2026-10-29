#!/usr/bin/env python3
"""Stage/publish a source-only review; never starts or evaluates the client."""
import argparse
import gzip
import hashlib
import io
import json
import pathlib
import shutil
import subprocess
import sys
import tarfile

ROOT = pathlib.Path('/Users/nallylin/Documents/code/ccodex')
BASE = 'codex-26.1007.30912-c5b273322a83'
WORK = ROOT / '.analysis-local/remaining-command-goals-78-work'
OUT = ROOT / 'analysis' / BASE
STAGE = WORK / 'publication'
RAW_NAME = pathlib.Path('raw/remaining-command-goals-v1')
NAMES = ['remaining-command-goals-v1.json', 'remaining-command-goals-v1.md',
         'remaining-command-goals-v1.csv', 'remaining-command-goals-v1-evidence.jsonl']
VERIFIER = ROOT / 'scripts/analysis/verify_remaining_command_goals_v1.py'


def verify(artifacts, raw):
    p = subprocess.run([sys.executable, str(VERIFIER), '--root', str(ROOT),
        '--artifacts', str(artifacts), '--raw', str(raw)], check=True, capture_output=True, text=True)
    return json.loads(p.stdout)


def save(p, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2)+'\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--publish', action='store_true')
    args = ap.parse_args()
    if not args.publish:
        STAGE.mkdir()
        raw = STAGE / RAW_NAME
        raw.mkdir(parents=True)
        for n in NAMES:
            shutil.copyfile(WORK/n, STAGE/n)
        for n in ['selected-entries.json','literal-census.json','hits-by-command.json',
                  'searched-js-files.txt','complete-matching-files.txt','identifier-patterns.txt']:
            shutil.copyfile(WORK/n, raw/n)
        sources = list((WORK/'programs').glob('*/literal-consumers.json'))
        sources += list((WORK/'closures').glob('*/source-contracts.json'))
        units = {}
        for p in sorted(sources):
            dest = raw/p.relative_to(WORK)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, dest)
            d = json.loads(p.read_text())
            for ref in d.get('sourceUnits', d.get('selectedSourceUnits', [])):
                name = ref['savedPath'] if 'sourceUnits' in d else str(p.parent.relative_to(WORK)/ref['savedPath'])
                assert name not in units
                units[name] = (WORK/name).read_bytes()
        assert len(units) == 1152
        with (raw/'source-units.tar.gz').open('xb') as f:
            with gzip.GzipFile(filename='', mode='wb', fileobj=f, mtime=0) as gz:
                with tarfile.open(fileobj=gz, mode='w') as tf:
                    for name, body in sorted(units.items()):
                        info = tarfile.TarInfo(name)
                        info.size = len(body)
                        info.mode = 0o444
                        info.mtime = 0
                        tf.addfile(info, io.BytesIO(body))
        scripts = raw/'scripts'
        scripts.mkdir()
        for p in [WORK/'build_review.py', WORK/'scan.mjs',
                  ROOT/'.analysis-local/parameterized-command-paths-work/extract.mjs',
                  VERIFIER, pathlib.Path(__file__).resolve()]:
            shutil.copyfile(p, scripts/p.name)
        receipt = verify(STAGE, raw)
        save(raw/'verification.json', receipt)
        manifest = []
        for p in sorted(STAGE.rglob('*')):
            if p.is_file():
                body = p.read_bytes()
                manifest.append({'path':str((OUT/p.relative_to(STAGE)).relative_to(ROOT)),
                                 'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()})
        save(raw/'publication-manifest.json', dict(baselineId=BASE,files=manifest,
             qualification='Manifest excludes itself and the later published-verification receipt. Source units are an analysis archive, not recovered client sources.'))
        print(json.dumps({'stage':str(STAGE),'filesPinned':len(manifest),
                          'sourceUnits':len(units),'archiveBytes':(raw/'source-units.tar.gz').stat().st_size,
                          'verification':receipt},ensure_ascii=False,indent=2))
        return
    raw = STAGE/RAW_NAME
    verify(STAGE, raw)
    for p in STAGE.rglob('*'):
        if p.is_file():
            assert not (OUT/p.relative_to(STAGE)).exists(), 'Refusing to replace a published artifact'
    for p in sorted(STAGE.rglob('*')):
        if p.is_file():
            dest = OUT/p.relative_to(STAGE)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(p,dest)
    published = verify(OUT, OUT/RAW_NAME)
    save(OUT/RAW_NAME/'published-verification.json',published)
    for p in STAGE.rglob('*'):
        if p.is_file():
            (OUT/p.relative_to(STAGE)).chmod(0o444)
    (OUT/RAW_NAME/'published-verification.json').chmod(0o444)
    print(json.dumps({'published':str(OUT/RAW_NAME),'verification':published},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
