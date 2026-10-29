"""Reconcile existing frozen selections into finite goals; no product execution."""
import collections
import copy
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/environment-extension-reconciliation'
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'


def read(p): return json.loads(p.read_text())
def sha(b): return hashlib.sha256(b).hexdigest()
def write(p, x): p.write_text(json.dumps(x, ensure_ascii=False, indent=2) + '\n')
def pin(p):
    b = p.read_bytes()
    return {'path': os.path.relpath(p, OUT), 'bytes': len(b), 'sha256': sha(b)}
def ref(p, pointer): return {**pin(p), 'jsonPointer': pointer}


def extract():
    assert not WORK.exists()
    WORK.mkdir()
    saved = OUT / 'raw/restoration-plan-v7/mcp-provider-01/source-contracts.json'
    x = read(saved)
    b = (FROZEN / x['sourcePath'].removeprefix('app.asar/')).read_bytes()
    assert sha(b) == x['sourceHash']
    units = []
    for name in ['Hjn', 'Rjn', 'Qjn', 'Yjn', 'Zjn', '$jn']:
        uses = [u for u in x['programBindingUses'] if u['name'] == name]
        definitions = uses[0]['binding']['definitions']
        assert len(definitions) == 1 and definitions[0]['kind'] == 'function'
        assert all(u['binding']['definitions'] == definitions for u in uses)
        u = copy.deepcopy(definitions[0]['declaration'])
        r = u['byteRange']; data = b[r['start']:r['endExclusive']]
        assert sha(data) == u['spanHash']
        filename = f'{len(units)+1:03}-{name}.txt'
        (WORK / filename).write_bytes(data)
        units.append({**u, 'name': name, 'sourceFilename': filename,
                      'bindingEvidence': ref(saved, f"/programBindingUses/{x['programBindingUses'].index(uses[0])}")})
    write(WORK / 'source-contracts.json', {'schemaVersion': 'saved-program-binding-selection/1',
        'baselineId': BASE, 'priorProgramSelection': pin(saved), 'units': units,
        'newFullProgramParses': 0, 'method': 'Extract exact unique declaration spans from saved Program bindings.',
        'targetCodeExecuted': False})
    shutil.copyfile(OUT / 'analysis-state.json', WORK / 'analysis-state-before.json')


if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['extract']:
        extract()
    elif sys.argv[1:] == ['publish']:
        from environment_extension_publication import publish
        publish()
    else:
        raise SystemExit('Use extract or publish')
