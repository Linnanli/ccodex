"""Deliver two completed catalogs without repeating target analysis.

Only explicitly selected, frozen metadata is read. Original programs, package
implementations, HTTP responses and attempt stdout remain local analysis inputs.
Producer records and schemas are preserved, including multi-source locators.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

BASELINE = 'codex-26.1007.30912-c5b273322a83'
WORKSPACE = Path(__file__).resolve().parents[2]
OUT = WORKSPACE / 'analysis' / BASELINE
PROFILES = [
    {
        'id': 'settings-entry-reconciliation',
        'directory': 'settings-entry-reconciliation-work',
        'main': 'settings-entry-reconciliation.json',
        'manifest': 'freeze-manifest.json',
        'manifestHash': 'baa59fd1b757ed34936f3d20238173fed5e29577d5dd521d9abbb991532e1d30',
        'pathField': 'relativePath',
        'peer': 'peer-review/peer-summary.json',
        'peerMarkdown': 'peer-review/peer-summary.md',
        'records': 107,
        'authorCountField': 'checks', 'authorChecks': 1651,
        'peerCountField': 'checks', 'peerChecks': 8326,
        'core': ['settings-entry-reconciliation.json', 'evidence.jsonl',
                 'summary.md', 'validation.json'],
    },
    {
        'id': 'sentry-upstream-identity-contracts',
        'directory': 'sentry-upstream-identity-work',
        'main': 'sentry-upstream-identity-contracts.json',
        'manifest': 'frozen-manifest.json',
        'manifestHash': '6a530a29681075839a32c62733e937631ae2b691b5f483f76e8f60a6eccb6405',
        'pathField': 'path',
        'peer': 'peer-review/independent-review.json',
        'peerMarkdown': 'peer-review/independent-review.md',
        'records': 31,
        'authorCountField': 'checks', 'authorChecks': 4845,
        'peerCountField': 'confirmedChecksAfterSupersededComparison', 'peerChecks': 1344,
        'core': ['sentry-upstream-identity-contracts.json', 'evidence.jsonl',
                 'summary.md', 'validation.json', 'comparison.json',
                 'source-pins.json', 'input-receipts.json', 'tools.json',
                 'upstream/source-map-tag-comparison.json'],
    },
]


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_new(path, raw):
    require(not path.is_symlink(), 'output symlink')
    for parent in path.parents:
        require(not parent.is_symlink(), 'output parent symlink')
    if path.exists():
        require(path.read_bytes() == raw, 'existing delivery differs: ' + path.name)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.delivery-tmp')
    require(not temporary.exists(), 'stale delivery temporary')
    temporary.write_bytes(raw)
    temporary.chmod(0o444)
    temporary.replace(path)


def source_name(value, directory):
    p = Path(value)
    p = p.relative_to(directory) if p.is_absolute() else p
    require(not p.is_absolute() and '..' not in p.parts, 'unsafe selected path')
    return p.as_posix()


def prepare(spec):
    directory = WORKSPACE / '.analysis-local' / spec['directory']
    selected = spec['core'] + [spec['manifest'], 'freeze-confirmation.json',
                             spec['peer'], spec['peerMarkdown']]
    inputs = {}
    for name in selected:
        path = directory / source_name(name, directory)
        require(not path.is_symlink(), 'selected symlink')
        for parent in path.parents:
            require(not parent.is_symlink(), 'selected parent symlink')
        require(path.stat().st_mode & 0o777 == 0o444, 'selected metadata is not frozen')
        inputs[name] = path.read_bytes()
    manifest = json.loads(inputs[spec['manifest']])
    require(pin(inputs[spec['manifest']])['sha256'] == spec['manifestHash'], 'manifest revision changed')
    require(manifest['baselineId'] == BASELINE, 'manifest baseline changed')
    inventory = {source_name(r[spec['pathField']], directory): r for r in manifest['files']}
    for name in selected:
        if name in (spec['manifest'], 'freeze-confirmation.json'):
            continue
        require(name in inventory, 'selected file outside closed manifest')
        require(pin(inputs[name]) == {k: inventory[name][k] for k in ('bytes', 'sha256')},
                'selected frozen bytes changed')
    confirmation = json.loads(inputs['freeze-confirmation.json'])
    require({k: confirmation['manifest'][k] for k in ('bytes', 'sha256')} ==
            pin(inputs[spec['manifest']]), 'freeze confirmation revision changed')
    require(confirmation['status'] in ('frozen', 'passed') and not confirmation.get('errors'),
            'freeze operation did not pass')
    main = json.loads(inputs[spec['main']])
    require(main['baselineId'] == BASELINE, 'main baseline changed')
    if spec['id'].startswith('sentry-'):
        require(set(spec['core']) <= set(main['archivePolicy']['formalMetadataAllowlist']),
                'core exceeds author metadata allowlist')
    rows = [json.loads(line) for line in inputs['evidence.jsonl'].splitlines() if line]
    require(len(rows) == spec['records'] and len({r['id'] for r in rows}) == len(rows),
            'journal count or identity changed')
    fields = {'id', 'baselineId', 'claim', 'sourcePath', 'sourceHash', 'locator',
              'method', 'confidence', 'verificationStatus'}
    require(all(fields <= r.keys() and r['baselineId'] == BASELINE and
                r['confidence'] in ('confirmed', 'inferred', 'unresolved') for r in rows),
            'journal minimum fields changed')
    checks = {}
    for label, name, field, count in [
        ('author', 'validation.json', spec['authorCountField'], spec['authorChecks']),
        ('peer', spec['peer'], spec['peerCountField'], spec['peerChecks']),
    ]:
        report = json.loads(inputs[name])
        require(report['baselineId'] == BASELINE and report['errors'] == [] and
                report[field] == count, 'saved selected review failed or changed')
        checks[label] = {'path': name, 'countField': field, 'count': count,
                         'scope': 'Saved bounded review; not rerun by delivery.',
                         'counterInterpretation': report.get('counterInterpretation')}
    metadata = {
        'catalogId': spec['id'], 'records': len(rows),
        'confidences': dict(Counter(r['confidence'] for r in rows)),
        'sourceFieldTypes': dict(Counter(type(r['sourcePath']).__name__ for r in rows)),
        'globalRecordsAdded': 0, 'runtimeConfirmedByDelivery': 0,
        'featureDenominatorEstablished': False,
        'producerMainStatusPreserved': main['status'],
        'savedReview': checks,
        'sourceDirectory': str(directory),
        'manifest': {'path': str(directory / spec['manifest']), **pin(inputs[spec['manifest']])},
        'copies': [],
        'limits': 'Exact producer metadata only. References to original programs, bounded units, '
                  'upstream implementations and execution history remain in pinned local inputs. '
                  'Original pending wording is preserved; later peer outcome is separately identified. '
                  'This delivery does not revalidate all cited semantics or establish runtime equivalence.',
    }
    return inputs, metadata


def main():
    # Read and validate both selected catalogs before writing any output.
    prepared = [(spec, *prepare(spec)) for spec in PROFILES]
    outputs, catalogs = {}, []
    for spec, inputs, metadata in prepared:
        raw_root = Path('raw/recovery-decisions') / spec['id']
        for name, raw in inputs.items():
            target = raw_root / name
            outputs[target] = raw
            metadata['copies'].append({'original': str(WORKSPACE / '.analysis-local' /
                                        spec['directory'] / name),
                                       'published': target.as_posix(), **pin(raw), 'role': 'exact-copy'})
        aliases = {
            spec['id'] + '.json': spec['main'],
            spec['id'] + '-evidence.jsonl': 'evidence.jsonl',
            spec['id'] + '-validation.json': 'validation.json',
            spec['id'] + '-peer-review.json': spec['peer'],
        }
        for target, name in aliases.items():
            outputs[Path(target)] = inputs[name]
            metadata['copies'].append({'original': str(WORKSPACE / '.analysis-local' /
                                        spec['directory'] / name), 'published': target,
                                       **pin(inputs[name]), 'role': 'exact-alias'})
        outputs[Path(spec['id'] + '-delivery-provenance.json')] = encode(metadata)
        catalogs.append(metadata)
    index = {'schemaVersion': 1, 'baselineId': BASELINE, 'catalogs': catalogs,
             'records': sum(c['records'] for c in catalogs), 'globalRecordsAdded': 0,
             'targetExecuted': False, 'targetProgramsRead': False,
             'thirdPartyImplementationCopied': False,
             'scope': 'Two frozen metadata catalogs only; independent from prior publication runs.'}
    outputs[Path('recovery-decision-catalogs-provenance.json')] = encode(index)
    for name, raw in outputs.items():
        write_new(OUT / name, raw)
    require(all(pin((OUT / name).read_bytes()) == pin(raw) for name, raw in outputs.items()),
            'delivered output byte check failed')
    print(json.dumps({'status': 'delivered', 'records': index['records'],
                      'outputs': len(outputs), 'catalogIds': [c['catalogId'] for c in catalogs],
                      'index': str(OUT / 'recovery-decision-catalogs-provenance.json')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
