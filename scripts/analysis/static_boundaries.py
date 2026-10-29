"""Publish selected, frozen analysis products without evaluating target code.

The root-authored configuration pins two specific catalogs. Their larger saved
AST inventories stay local and are referenced by the original frozen manifests.
Publication verifies selected byte identities, not all semantic claims again.
"""
from collections import Counter
from pathlib import Path, PurePosixPath
import hashlib
import json
import os
import tempfile

BASELINE = 'codex-26.1007.30912-c5b273322a83'
CONFIG = '.analysis-local/static-boundary-publication-work/config.json'
EXPECTED = {'task-composer-entry-contracts': 39, 'turn-notification-bindings': 31}


def require(value, message):
    if not value:
        raise ValueError(message)


def byte_pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def relative(value):
    require(isinstance(value, str) and value, 'missing relative path')
    p = PurePosixPath(value)
    require(not p.is_absolute() and '..' not in p.parts and '.' not in p.parts
            and p.as_posix() == value and '\\' not in value, 'unsafe relative path')
    return value


def read_selected(directory, item):
    name = relative(item['relativePath'])
    path = directory / name
    for part in (path, *path.parents):
        require(not part.is_symlink(), 'symlink selected input: ' + str(path))
    require(path.is_file(), 'missing selected file: ' + str(path))
    require(path.stat().st_mode & 0o777 == 0o444, 'selected input is not frozen: ' + str(path))
    raw = path.read_bytes()
    require(byte_pin(raw) == {k: item[k] for k in ('bytes', 'sha256')},
            'selected input changed: ' + str(path))
    role = item['role']
    suffix = path.suffix
    if role == 'authored-analysis-helper':
        require(suffix in ('.py', '.cjs', '.mjs'), 'unclassified code origin')
    elif role == 'analysis-json':
        require(suffix == '.json', 'JSON role mismatch')
        json.loads(raw)
    elif role == 'analysis-journal':
        require(suffix == '.jsonl', 'journal role mismatch')
        for line in raw.splitlines():
            if line.strip():
                json.loads(line)
    elif role == 'analysis-prose-or-log':
        require(suffix in ('.md', '.txt', '.stdout', '.stderr'), 'text role mismatch')
        raw.decode('utf-8')
    else:
        raise ValueError('unknown selected file origin: ' + name)
    return raw


def frozen_relative(path, directory):
    p = Path(path)
    if p.is_absolute():
        return relative(p.relative_to(directory).as_posix())
    return relative(path)


def journal_summary(catalog_id, rows):
    require(len(rows) == EXPECTED[catalog_id], 'fixed record count differs')
    require(len({r['id'] for r in rows}) == len(rows), 'duplicate record ID')
    classes = Counter()
    locations = Counter()
    for row in rows:
        require(row.get('baselineId') == BASELINE, 'record baseline mismatch')
        require(isinstance(row.get('claim'), str) and row['claim'], 'missing claim')
        require(row.get('confidence') in ('confirmed', 'inferred', 'unresolved'),
                'confidence is not a plan enum')
        require('method' in row and 'verificationStatus' in row, 'missing plan field')
        sources, hashes, locators = [row[k] for k in ('sourcePath', 'sourceHash', 'locator')]
        if isinstance(sources, list):
            require(isinstance(hashes, list) and isinstance(locators, list)
                    and len(sources) == len(hashes) == len(locators) > 0,
                    'parallel contributing reference arrays differ')
        else:
            sources, hashes, locators = [sources], [hashes], [locators]
        kinds = set()
        for source, sha, loc in zip(sources, hashes, locators):
            require(isinstance(source, str) and source, 'missing qualified source')
            require(isinstance(sha, str) and len(sha) == 64
                    and all(c in '0123456789abcdef' for c in sha), 'missing source hash')
            require(isinstance(loc, dict) and isinstance(loc.get('kind'), str),
                    'missing typed locator')
            kind = loc['kind']
            kinds.add(kind)
            locations[kind] += 1
            if kind == 'original-source-byte-range':
                span = loc.get('byteRange', {})
                require(isinstance(span.get('start'), int)
                        and isinstance(span.get('endExclusive'), int)
                        and 0 <= span['start'] < span['endExclusive'], 'invalid source range')
            elif kind == 'byte-range':
                require(isinstance(loc.get('startByte'), int)
                        and isinstance(loc.get('endByte'), int)
                        and 0 <= loc['startByte'] < loc['endByte'], 'invalid direct range')
            elif kind == 'frozen-analysis-metadata-json-pointer':
                require(isinstance(loc.get('jsonPointer'), str), 'missing metadata pointer')
            else:
                raise ValueError('unconfigured locator kind: ' + kind)
        classes[' + '.join(sorted(kinds))] += 1
    return {'records': len(rows), 'recordLocatorClasses': dict(sorted(classes.items())),
            'contributingLocatorOccurrences': dict(sorted(locations.items())),
            'confidences': dict(sorted(Counter(r['confidence'] for r in rows).items())),
            'globalRecordsAdded': 0, 'runtimeConfirmedRecords': 0,
            'definition': 'Selected producer claim records, with original typed references unchanged. '
                          'Metadata-only records, mixed references and source ranges are counted separately; '
                          'none establishes a feature denominator or runtime behavior.'}


def atomic_write(path, raw):
    for part in (path, *path.parents):
        require(not part.is_symlink(), 'symlink publication destination: ' + str(part))
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.is_symlink(), 'symlink publication destination')
    if path.exists():
        require(path.read_bytes() == raw, 'immutable publication alias changed: ' + str(path))
        return
    fd, temp = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def saved_check(check, profile, selected, directory, manifest_pin):
    """Validate the saved producer schema, without adding fields to that producer."""
    require(check.get('status') == profile['status'] and check.get('errors') == [],
            'saved check is not successful')
    require(check.get(profile['countField']) == profile['count'], 'saved check count differs')
    if profile['hasBaselineId']:
        require(check.get('baselineId') == BASELINE, 'saved check baseline differs')
    else:
        require('baselineId' not in check, 'saved producer schema changed')
    if 'errorCount' in check:
        require(check['errorCount'] == 0, 'saved check has failures')
    if profile.get('sourcePin'):
        require({k: check['source'][k] for k in ('bytes', 'sha256')} == profile['sourcePin'],
                'saved check source pin differs')
    if profile.get('hasManifestPin'):
        require({k: check['manifest'][k] for k in ('bytes', 'sha256')} == manifest_pin,
                'saved confirmation manifest pin differs')
    for field in profile.get('productFields', []):
        for item in check[field]:
            name = frozen_relative(item['path'], directory)
            require(name in selected, 'saved review product not selected: ' + name)
            require(byte_pin(selected[name]) == {k: item[k] for k in ('bytes', 'sha256')},
                    'saved review product differs: ' + name)
    return {'originalStatus': check['status'], 'originalCountField': profile['countField'],
            'checks': profile['count'], 'errors': [], 'baselineIdPresentInOriginal': profile['hasBaselineId'],
            'scope': profile['scope']}


def publish_static_boundaries(*, out, workspace, baseline):
    require(baseline['baselineId'] == BASELINE, 'publisher baseline mismatch')
    config_path = workspace / CONFIG
    for part in (config_path, *config_path.parents):
        require(not part.is_symlink(), 'symlink configuration')
    require(config_path.stat().st_mode & 0o777 == 0o444, 'configuration is not frozen')
    config_raw = config_path.read_bytes()
    config = json.loads(config_raw)
    require(config.get('baselineId') == BASELINE, 'configuration baseline mismatch')
    specs = config['catalogs']
    require(len(specs) == 2 and {s['catalogId'] for s in specs} == set(EXPECTED),
            'unexpected catalog configuration')
    pending, catalogs = {}, []
    for spec in specs:
        cid = spec['catalogId']
        directory = workspace / '.analysis-local' / relative(spec['directory'])
        require(directory.parent == workspace / '.analysis-local', 'unexpected owned directory')
        names = [i['relativePath'] for i in spec['selectedFiles']]
        require(len(names) == len(set(names)), 'duplicate selected file')
        selected = {i['relativePath']: read_selected(directory, i) for i in spec['selectedFiles']}
        manifest = json.loads(selected[spec['manifest']])
        require(manifest.get('baselineId') == BASELINE, 'manifest baseline mismatch')
        inventory = {frozen_relative(r['path'], directory): r for r in manifest['files']}
        exceptions = set(spec['outsideManifestFiles']) | {spec['manifest']}
        require(exceptions <= set(selected), 'unselected manifest exception')
        for name, raw in selected.items():
            if name in exceptions:
                continue
            require(name in inventory, 'selected file is outside frozen inventory: ' + name)
            require(byte_pin(raw) == {k: inventory[name][k] for k in ('bytes', 'sha256')},
                    'manifest selected pin differs: ' + name)
        main = json.loads(selected[spec['main']])
        require(main.get('baselineId') == BASELINE, 'main baseline mismatch')
        rows = [json.loads(line) for line in selected[spec['journal']].splitlines() if line.strip()]
        counts = journal_summary(cid, rows)
        saved_checks = {}
        for field in ('validation', 'peer', 'freezeConfirmation'):
            check = json.loads(selected[spec[field]])
            saved_checks[field] = saved_check(check, spec['checkProfiles'][field], selected,
                                             directory, byte_pin(selected[spec['manifest']]))
        forbidden = {(p['bytes'], p['sha256']) for p in spec['excludedImplementationPins']}
        rawbase = 'raw/static-boundaries/' + cid + '/'
        outputs = []
        for item in spec['selectedFiles']:
            name, raw = item['relativePath'], selected[item['relativePath']]
            require((len(raw), byte_pin(raw)['sha256']) not in forbidden,
                    'complete source or tool implementation cannot be published')
            published = rawbase + name
            pending[published] = raw
            outputs.append({'originPath': str(directory / name), 'publishedPath': published,
                            'role': item['role'], **byte_pin(raw)})
        aliases = {'.json': spec['main'], '-evidence.jsonl': spec['journal'],
                   '-raw-summary.md': spec['summary'], '-validation.json': spec['validation'],
                   '-peer-review.json': spec['peer'], '-peer-review.md': spec['peerSummary'],
                   '-manifest.json': spec['manifest']}
        for suffix, name in aliases.items():
            published = cid + suffix
            pending[published] = selected[name]
            outputs.append({'originPath': str(directory / name), 'publishedPath': published,
                            'role': 'exact-byte-alias', **byte_pin(selected[name])})
        provenance = {'schemaVersion': 1, 'baselineId': BASELINE, 'catalogId': cid,
                      'configuration': {'sourcePath': CONFIG, **byte_pin(config_raw)},
                      'originalManifest': {'sourcePath': str(directory / spec['manifest']),
                                           **byte_pin(selected[spec['manifest']])},
                      'ownedInventoryFiles': len(inventory), 'publishedSelectedFiles': len(selected),
                      'publicationScope': 'Selected final metadata, authored helpers and actual execution '
                                          'captures only. Larger frozen AST inventories remain local. '
                                          'Selected hashes/modes verified; whole closure/semantic/runtime '
                                          'checks are not rerun by this publisher.',
                      'excludedImplementationPins': spec['excludedImplementationPins'],
                      'counts': counts, 'savedChecks': saved_checks, 'outputs': outputs,
                      'unpublishedLocalInputsRemainReferenced': True,
                      'globalEvidenceJournalReadOrModified': False,
                      'featureDenominatorEstablished': False,
                      'fullAnalysisCompleted': False}
        pending[cid + '-provenance.json'] = encoded(provenance)
        summary = (f'# {spec["title"]}\n\n'
                   f'固定基线 `{BASELINE}`。新增 {counts["records"]} 条限定范围的保存记录；'
                   '源码范围、元数据引用与运行验证分别判断，完整功能分母仍未确定。\n\n'
                   f'{spec["finding"]}\n\n'
                   f'{spec["limits"]}\n\n'
                   f'[原始结果]({cid}.json)、[原始记录]({cid}-evidence.jsonl)、'
                   f'[作者摘要]({cid}-raw-summary.md)、[核验]({cid}-validation.json)、'
                   f'[同行审查]({cid}-peer-review.md)、[冻结清单]({cid}-manifest.json)、'
                   f'[发布来源]({cid}-provenance.json)。\n\n'
                   '本次仅发布选定分析资料的逐字副本与派生索引。较大的本地 AST 和历史尝试由'
                   '冻结清单引用；未复制完整原客户端或第三方实现，未增加全局 journal 记录，'
                   '未执行新的客户端或模型任务。\n').encode()
        pending[cid + '-summary.md'] = summary
        catalogs.append({'catalogId': cid, 'counts': counts, 'provenance': cid + '-provenance.json',
                         'summary': cid + '-summary.md', 'outputs': outputs})
    index = {'schemaVersion': 1, 'baselineId': BASELINE, 'catalogs': catalogs,
             'catalogCount': 2, 'recordCount': sum(c['counts']['records'] for c in catalogs),
             'globalRecordsAdded': 0, 'runtimeConfirmedRecords': 0,
             'featureDenominatorEstablished': False, 'fullAnalysisCompleted': False,
             'configuration': {'sourcePath': CONFIG, **byte_pin(config_raw)}}
    pending['static-boundaries-provenance.json'] = encoded(index)
    pending['raw/static-boundaries/config.json'] = config_raw
    for name, raw in pending.items():
        atomic_write(out / relative(name), raw)
    return index
