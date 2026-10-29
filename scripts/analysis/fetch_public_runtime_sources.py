"""Fetch a fixed, anonymous public-source comparison set into analysis scratch."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
ITEMS = [
    ('electron-app-doc', 'electron/electron', 'v42.3.0', 'docs/api/app.md'),
    ('electron-webcontents-doc', 'electron/electron', 'v42.3.0', 'docs/api/web-contents.md'),
    ('electron-process-metric-doc', 'electron/electron', 'v42.3.0', 'docs/api/structures/process-metric.md'),
    ('electron-navigation-history-doc', 'electron/electron', 'v42.3.0', 'docs/api/navigation-history.md'),
    ('electron-window-open-response-doc', 'electron/electron', 'v42.3.0', 'docs/api/structures/window-open-handler-response.md'),
    ('electron-webcontents-view-doc', 'electron/electron', 'v42.3.0', 'docs/api/web-contents-view.md'),
    ('electron-app-native', 'electron/electron', 'v42.3.0', 'shell/browser/api/electron_api_app.cc'),
    ('electron-webcontents-native', 'electron/electron', 'v42.3.0', 'shell/browser/api/electron_api_web_contents.cc'),
    ('electron-webcontents-js', 'electron/electron', 'v42.3.0', 'lib/browser/api/web-contents.ts'),
    ('electron-node-dependency', 'electron/electron', 'v42.3.0', 'DEPS'),
    ('node-permissions-doc', 'nodejs/node', 'v24.19.0', 'doc/api/permissions.md'),
    ('node-permission-header', 'nodejs/node', 'v24.19.0', 'src/permission/permission.h'),
    ('node-permission-base-header', 'nodejs/node', 'v24.19.0', 'src/permission/permission_base.h'),
    ('node-permission-source', 'nodejs/node', 'v24.19.0', 'src/permission/permission.cc'),
    ('node-options-source', 'nodejs/node', 'v24.19.0', 'src/node_options.cc'),
    ('node-permission-js', 'nodejs/node', 'v24.19.0', 'lib/internal/process/permission.js'),
]


def main():
    run = sys.argv[1]
    assert run.isascii() and run.replace('-', '').isalnum()
    output = ROOT / '.analysis-local/public-runtime-comparison-work' / run
    output.mkdir(parents=True, exist_ok=False)
    (output / Path(__file__).name).write_bytes(Path(__file__).read_bytes())

    def fetch(item):
        key, repository, tag, source_path = item
        url = f'https://raw.githubusercontent.com/{repository}/{tag}/{source_path}'
        start, clock = datetime.now(timezone.utc).isoformat(), time.monotonic()
        record = {'id': key, 'repository': repository, 'tag': tag, 'sourcePath': source_path,
                  'url': url, 'startedAtUtc': start}
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'ccodex-analysis-public-source/1'})
            with urllib.request.urlopen(request, timeout=15) as response:
                body = response.read(2500000)
                record.update({'httpStatus': response.status, 'finalUrl': response.url,
                               'completeRead': len(body) < 2500000, 'bytes': len(body),
                               'sha256': hashlib.sha256(body).hexdigest()})
                (output / (key + '.txt')).write_bytes(body)
        except Exception as error:
            record['error'] = str(error)
        record.update({'completedAtUtc': datetime.now(timezone.utc).isoformat(),
                       'wallTimeSeconds': time.monotonic() - clock})
        return record

    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(fetch, ITEMS))
    (output / 'manifest.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
    for record in records:
        print(record['id'], record.get('httpStatus'), record.get('bytes'), record.get('error'))


if __name__ == '__main__':
    main()
