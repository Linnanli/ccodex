"""Acquire two fixed public API descriptions; never execute downloaded content."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / '.analysis-local/runtime-surface-disposition-work'
if len(sys.argv) > 1:
    assert sys.argv[1] == 'attempt-02'
    WORK = WORK / sys.argv[1]
ITEMS = [
    ('electron-api.json', 'c464321e07ebc309729ffb49afd799a5a82fdb3b7a736b50207d651ed074323f'),
    ('electron.d.ts', '80c5c937e55e650f8b70a9b481d6abebb7df1d774f507188fc5c28def5409c77'),
]


def fetch(item):
    name, expected = item
    url = 'https://github.com/electron/electron/releases/download/v42.3.0/' + name
    record = dict(name=name, url=url, expectedSha256=expected,
                  startedAtUtc=datetime.now(timezone.utc).isoformat())
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'ccodex-analysis/1'})
        with urllib.request.urlopen(request, timeout=25) as response:
            body = response.read(4000001)
            record.update(httpStatus=response.status, finalUrl=response.url,
                          bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        assert len(body) < 4000001, 'response exceeded bound'
        assert record['sha256'] == expected, 'published asset digest mismatch'
        (WORK / name).write_bytes(body)
        record['verified'] = True
    except Exception as error:
        record.update(verified=False, error=str(error))
    record['completedAtUtc'] = datetime.now(timezone.utc).isoformat()
    return record


if __name__ == '__main__':
    WORK.mkdir(exist_ok=False)
    with ThreadPoolExecutor(max_workers=2) as pool:
        records = list(pool.map(fetch, ITEMS))
    (WORK / 'acquisition.json').write_text(json.dumps(records, indent=2) + '\n')
    for record in records:
        print(record['name'], record['verified'], record.get('bytes'), record.get('error'))
    assert all(x['verified'] for x in records)
