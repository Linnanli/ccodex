"""Deliver explicit frozen metadata profiles; never load target implementations."""
from collections import Counter
import json
from pathlib import Path

from deliver_frozen_metadata import BASELINE, WORKSPACE, OUT, encode, pin, require, source_name, write_new

CONFIG = WORKSPACE / '.analysis-local/settings-and-rpc-delivery-work/profiles-v2.json'


def pointer(value, path):
    for key in path.split('/')[1:]:
        key = key.replace('~1', '/').replace('~0', '~')
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def prepare(spec):
    root = WORKSPACE / '.analysis-local' / spec['directory']
    require(root.parent == WORKSPACE / '.analysis-local', 'unsafe input directory')
    selected = spec['selected']
    require(len(selected) == len(set(selected)), 'duplicate selected metadata')
    data = {}
    for name in selected:
        path = root / source_name(name, root)
        require(not path.is_symlink(), 'selected symlink')
        require(all(not p.is_symlink() for p in path.parents), 'selected parent symlink')
        require(path.stat().st_mode & 0o777 == 0o444, 'selected metadata not frozen')
        data[name] = path.read_bytes()
    manifest = json.loads(data[spec['manifest']])
    require(manifest['baselineId'] == BASELINE, 'manifest baseline changed')
    require(pin(data[spec['manifest']])['sha256'] == spec['manifestHash'], 'manifest revision changed')
    confirmation = json.loads(data[spec['confirmation']])
    inventory = {source_name(r[spec['manifestPathField']], root): r
                 for r in manifest[spec.get('manifestFilesField', 'files')]}
    external = {source_name(r['path'], root): r for r in confirmation.get('peerFiles', [])}
    for name in selected:
        if name in (spec['manifest'], spec['confirmation']):
            continue
        if name in spec.get('externalPeerSelections', []):
            require(name in external, 'selected external peer is not pinned by owner confirmation')
            entry = external[name]
        else:
            require(name in inventory, 'selection outside owned manifest: ' + name)
            entry = inventory[name]
        require(pin(data[name]) == {k: entry[k] for k in ('bytes', 'sha256')},
                'selected metadata bytes changed: ' + name)
    if spec.get('confirmationDeclaresBaseline', True):
        require(confirmation['baselineId'] == BASELINE, 'confirmation baseline changed')
    require(pin(data[spec['manifest']]) == {k: confirmation['manifest'][k] for k in ('bytes', 'sha256')},
            'confirmation manifest changed')
    require(confirmation['status'] == spec['confirmationStatus'] and not confirmation.get('errors'),
            'freeze confirmation not passed')
    main = json.loads(data[spec['main']])
    require(main['baselineId'] == BASELINE, 'main baseline changed')
    rows = [json.loads(line) for line in data[spec['journal']].splitlines() if line]
    require(len(rows) == spec['records'] and len({r['id'] for r in rows}) == len(rows),
            'evidence record identity changed')
    fields = {'id', 'baselineId', 'claim', 'sourcePath', 'sourceHash', 'locator',
              'method', 'confidence', 'verificationStatus'}
    require(all(fields <= r.keys() and r['baselineId'] == BASELINE and
                r['confidence'] in ('confirmed', 'inferred', 'unresolved') for r in rows),
            'evidence minimum fields changed')
    reviews = []
    for check in spec['reviews']:
        report = json.loads(data[check['path']])
        require(report.get('baselineId', BASELINE) == BASELINE and report['errors'] == [],
                'selected review has errors or a conflicting baseline')
        require(pointer(report, check['countPointer']) == check['count'], 'review counter changed')
        reviews.append({**check,
            'baselineBasis': 'declared-report-field' if 'baselineId' in report else 'pinned-same-baseline-owner-manifest',
            'scope': 'Saved bounded review only; counters for different scopes are not summed.'})
    return data, {'catalogId': spec['id'], 'records': len(rows),
        'confidence': dict(Counter(r['confidence'] for r in rows)),
        'sourceDirectory': str(root), 'producerStatusPreserved': main.get('status'),
        'manifest': {'path': str(root / spec['manifest']), **pin(data[spec['manifest']])},
        'savedReviews': reviews, 'copies': [], 'globalRecordsAdded': 0, 'runtimeRunsAdded': 0,
        'featureDenominatorEstablished': False,
        'scope': 'Selected exact producer metadata, evidence and bounded reviews. No implementation extraction, original-source reparse or runtime equivalence claim.'}


def main():
    config_raw = CONFIG.read_bytes()
    config = json.loads(config_raw)
    require(config['baselineId'] == BASELINE, 'config baseline changed')
    require({s['id'] for s in config['profiles']} == {'settings-agent-page-contracts',
        'settings-general-page-contracts', 'submission-rpc-dependency-contracts', 'local-host-registration-contracts'},
        'profile scope changed')
    # Validate all selected input bytes before producing any output.
    prepared = [(spec, *prepare(spec)) for spec in config['profiles']]
    outputs, catalogs = {}, []
    for spec, data, catalog in prepared:
        for name, raw in data.items():
            target = Path('raw/settings-and-rpc') / spec['id'] / name
            outputs[target] = raw
            catalog['copies'].append({'original': str(WORKSPACE / '.analysis-local' / spec['directory'] / name),
                'published': target.as_posix(), **pin(raw), 'role': 'exact-producer-metadata-copy'})
        aliases = {spec['id'] + '.json': spec['main'], spec['id'] + '-evidence.jsonl': spec['journal'],
            spec['id'] + '-validation.json': spec['authorValidation'],
            spec['id'] + '-peer-review.json': spec['peer'], spec['id'] + '-peer-review.md': spec['peerMarkdown']}
        for target, name in aliases.items():
            outputs[Path(target)] = data[name]
            catalog['copies'].append({'original': str(WORKSPACE / '.analysis-local' / spec['directory'] / name),
                'published': target, **pin(data[name]), 'role': 'exact-producer-metadata-alias'})
        outputs[Path(spec['id'] + '-delivery-provenance.json')] = encode(catalog)
        catalogs.append(catalog)
    index = {'schemaVersion': 1, 'baselineId': BASELINE, 'catalogs': catalogs,
        'config': {'path': str(CONFIG), **pin(config_raw)}, 'records': sum(c['records'] for c in catalogs),
        'globalRecordsAdded': 0, 'runtimeRunsAdded': 0, 'targetExecuted': False,
        'originalSourceReadOrParsed': False, 'thirdPartyImplementationCopied': False,
        'scope': 'Four independently scoped frozen metadata catalogs; separate from the old global journal and feature denominator.'}
    outputs[Path('settings-and-rpc-delivery-provenance.json')] = encode(index)
    for name, raw in outputs.items():
        write_new(OUT / name, raw)
    require(all((OUT / name).read_bytes() == raw for name, raw in outputs.items()), 'delivery byte check failed')
    print(json.dumps({'status': 'delivered', 'records': index['records'], 'outputs': len(outputs),
        'catalogs': [c['catalogId'] for c in catalogs], 'runtimeRunsAdded': 0}))


if __name__ == '__main__':
    main()
