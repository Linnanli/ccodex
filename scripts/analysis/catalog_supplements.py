"""Publish two frozen metadata catalogs, preserving their producer schemas.

This helper reads selected analysis files only. Original programs, complete saved
units and third-party implementations remain local inputs to the recorded work.
It does not repeat semantic analysis or establish a complete feature census.
"""
from collections import Counter
import json
from pathlib import Path

from static_boundaries import atomic_write, byte_pin, encoded, read_selected, relative, require

BASELINE = 'codex-26.1007.30912-c5b273322a83'
CONFIG = '.analysis-local/catalog-supplement-publication-work/config.json'
EXPECTED = {'react-upstream-identity-contracts': 33, 'settings-registry-contracts': 172}
REACT_CORE = {
    'react-upstream-identity-contracts.json', 'evidence.jsonl', 'summary.md',
    'validation.json', 'comparison.json', 'source-pins.json', 'input-receipts.json',
    'upstream/archive-member-inventory.json', 'upstream/fetch-receipts.json',
}
SETTINGS_CORE = {'settings-registry-contracts.json', 'evidence.jsonl', 'summary.md', 'validation.json'}


def public_receipt_metadata(value, path=''):
    """Omit response cookie fields recursively; retain the original locally."""
    omitted = []
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            child_path = path + '/' + key.replace('~', '~0').replace('/', '~1')
            if key.lower() == 'set-cookie':
                omitted.append(child_path)
            else:
                result[key], nested = public_receipt_metadata(child, child_path)
                omitted.extend(nested)
        return result, omitted
    if isinstance(value, list):
        result = []
        for index, child in enumerate(value):
            child_path = path + '/' + str(index)
            if (isinstance(child, list) and len(child) == 2 and isinstance(child[0], str)
                    and child[0].lower() == 'set-cookie'):
                omitted.append(child_path)
            else:
                projected, nested = public_receipt_metadata(child, child_path)
                result.append(projected)
                omitted.extend(nested)
        return result, omitted
    return value, omitted


def owned_relative(value, directory):
    path = Path(value)
    return relative(path.relative_to(directory).as_posix() if path.is_absolute() else value)


def journal_counts(cid, rows):
    require(len(rows) == EXPECTED[cid], 'catalog record count differs')
    require(len({r['id'] for r in rows}) == len(rows), 'duplicate catalog record ID')
    locators, kinds, confidences = Counter(), Counter(), Counter()
    for row in rows:
        require(row.get('baselineId') == BASELINE, 'record baseline differs')
        require(all(k in row for k in ('id', 'claim', 'sourcePath', 'sourceHash', 'locator',
                                      'method', 'confidence', 'verificationStatus')),
                'record lacks a plan field')
        require(all(isinstance(row[k], str) and row[k] for k in
                    ('id', 'claim', 'sourcePath', 'method', 'verificationStatus')), 'invalid record field')
        sha = row['sourceHash']
        require(isinstance(sha, str) and len(sha) == 64 and
                all(c in '0123456789abcdef' for c in sha), 'invalid source hash')
        require(row['confidence'] in ('confirmed', 'inferred', 'unresolved'), 'unknown confidence')
        loc = row['locator']
        require(isinstance(loc, dict), 'invalid typed locator')
        if loc.get('kind') == 'byte-range':
            require(isinstance(loc.get('start'), int) and isinstance(loc.get('endExclusive'), int)
                    and 0 <= loc['start'] < loc['endExclusive'], 'invalid byte range')
        elif loc.get('kind') == 'json-pointer':
            require(isinstance(loc.get('pointer'), str) and loc['pointer'].startswith('/'),
                    'invalid metadata pointer')
        else:
            raise ValueError('unconfigured catalog locator kind')
        locators[loc['kind']] += 1
        confidences[row['confidence']] += 1
        kinds[row.get('recordKind', 'producer-did-not-classify-record-kind')] += 1
    return {'records': len(rows), 'locatorKinds': dict(sorted(locators.items())),
            'producerRecordKinds': dict(sorted(kinds.items())), 'confidences': dict(sorted(confidences.items())),
            'globalRecordsAdded': 0, 'runtimeConfirmedRecords': 0,
            'definition': 'Original producer records. Byte ranges may refer to original application '
                          'code or local official archives; locator kind alone does not establish origin. '
                          'Record counts do not count features or prove runtime behavior.'}


def saved_checks(spec, inputs, directory, inventory):
    results = {}
    for label, profile in spec['checkProfiles'].items():
        check = json.loads(inputs[profile['path']])
        require(check.get('status') == profile['status'] and check.get('errors') == [],
                'saved check failed: ' + label)
        require(check.get(profile['countField']) == profile['count'], 'saved check count differs')
        require(('baselineId' in check) == profile['hasBaselineId'], 'saved check schema differs')
        if profile['hasBaselineId']:
            require(check['baselineId'] == BASELINE, 'saved check baseline differs')
        if 'errorCount' in check:
            require(check['errorCount'] == 0, 'saved check has errors')
        for field in profile.get('productFields', []):
            for product in check[field]:
                name = owned_relative(product['path'], directory)
                require(name in inventory, 'saved check product outside frozen inventory')
                require({k: product[k] for k in ('bytes', 'sha256')} ==
                        {k: inventory[name][k] for k in ('bytes', 'sha256')},
                        'saved check product pin differs')
        if profile.get('manifestField'):
            observed = check[profile['manifestField']]
            require({k: observed[k] for k in ('bytes', 'sha256')} == byte_pin(inputs[spec['manifest']]),
                    'saved freeze confirmation manifest differs')
        results[label] = {'sourcePath': str(directory / profile['path']),
                          **byte_pin(inputs[profile['path']]), 'status': profile['status'],
                          'checks': profile['count'], 'countField': profile['countField'],
                          'baselineIdPresentInOriginal': profile['hasBaselineId'], 'errors': [],
                          'scope': profile['scope']}
    return results


def publish_catalog_supplements(*, out, workspace, baseline):
    require(baseline['baselineId'] == BASELINE, 'publisher baseline differs')
    config_path = workspace / CONFIG
    for path in (config_path, *config_path.parents):
        require(not path.is_symlink(), 'symlink configuration')
    require(config_path.stat().st_mode & 0o777 == 0o444, 'configuration is not frozen')
    raw_config = config_path.read_bytes()
    config = json.loads(raw_config)
    require(config.get('baselineId') == BASELINE, 'configuration baseline differs')
    specs = config['catalogs']
    require(len(specs) == 2 and {s['catalogId'] for s in specs} == set(EXPECTED),
            'unexpected catalog configuration')
    pending, catalogs = {}, []
    for spec in specs:
        cid = spec['catalogId']
        directory = workspace / '.analysis-local' / relative(spec['directory'])
        require(directory.parent == workspace / '.analysis-local', 'unexpected owned directory')
        names = [i['relativePath'] for i in spec['inputFiles']]
        require(len(names) == len(set(names)), 'duplicate selected input')
        inputs = {i['relativePath']: read_selected(directory, i) for i in spec['inputFiles']}
        manifest = json.loads(inputs[spec['manifest']])
        require(manifest.get('baselineId') == BASELINE, 'frozen manifest baseline differs')
        inventory = {owned_relative(i[spec['manifestPathField']], directory): i for i in manifest['files']}
        exceptions = set(spec['outsideManifestFiles']) | {spec['manifest']}
        require(exceptions <= set(inputs), 'unselected manifest exception')
        for name, raw in inputs.items():
            if name in exceptions:
                continue
            require(name in inventory, 'selected input outside frozen inventory: ' + name)
            require(byte_pin(raw) == {k: inventory[name][k] for k in ('bytes', 'sha256')},
                    'selected manifest pin differs')
        main = json.loads(inputs[spec['main']])
        require(main.get('baselineId') == BASELINE, 'main baseline differs')
        confirmation = json.loads(inputs[spec['freezeConfirmation']])
        require(confirmation['status'] == spec['freezeConfirmationStatus'], 'freeze operation differs')
        require({k: confirmation['manifest'][k] for k in ('bytes', 'sha256')} ==
                byte_pin(inputs[spec['manifest']]), 'freeze operation manifest differs')
        core = set(spec['corePublicationFiles'])
        if cid == 'react-upstream-identity-contracts':
            require(core == REACT_CORE == set(main['archivePolicy']['formalProductAllowlist']),
                    'React publication must follow its explicit core allowlist')
        else:
            require(core == SETTINGS_CORE, 'unexpected settings core publication')
        support = set(spec['supportPublicationFiles'])
        require(not core & support and core | support <= set(inputs), 'publication selection differs')
        require(support == set(spec['supportPublicationAllowlist']), 'support allowlist differs')
        forbidden = set(spec['localOnlyArtifacts'])
        require(not (core | support) & forbidden, 'local-only implementation selected')
        if cid == 'react-upstream-identity-contracts':
            require(set(main['archivePolicy']['localOnlyArtifacts']) <= forbidden,
                    'React local-only exclusions missing')
        forbidden_pins = {(i['bytes'], i['sha256']) for i in spec['excludedImplementationPins']}
        for name in core | support:
            require((len(inputs[name]), byte_pin(inputs[name])['sha256']) not in forbidden_pins,
                    'complete implementation selected for publication')
        rows = [json.loads(line) for line in inputs[spec['journal']].splitlines() if line.strip()]
        counts = journal_counts(cid, rows)
        checks = saved_checks(spec, inputs, directory, inventory)
        outputs = []
        for name in sorted(core | support):
            destination = 'raw/catalog-supplements/' + cid + '/' + name
            raw = inputs[name]
            entry = {'originPath': str(directory / name), 'publishedPath': destination}
            if cid == 'react-upstream-identity-contracts' and name == 'upstream/fetch-receipts.json':
                metadata, omitted = public_receipt_metadata(json.loads(raw))
                raw = encoded(metadata)
                entry.update({'role': 'derived-public-http-response-metadata',
                              'originalInput': byte_pin(inputs[name]),
                              'omittedHeaderName': 'set-cookie', 'omittedOriginalPointers': omitted,
                              'originalResponseHeadersRemainLocalOnly': True})
            pending[destination] = raw
            outputs.append({**entry, **byte_pin(raw)})
        for suffix, name in spec['aliases'].items():
            require(name in core | support, 'alias refers to unpublished input')
            destination = cid + suffix
            pending[destination] = inputs[name]
            outputs.append({'originPath': str(directory / name), 'publishedPath': destination,
                            'role': 'exact-byte-alias', **byte_pin(inputs[name])})
        provenance = {'schemaVersion': 1, 'baselineId': BASELINE, 'catalogId': cid,
                      'configuration': {'sourcePath': CONFIG, **byte_pin(raw_config)},
                      'originalManifest': {'sourcePath': str(directory / spec['manifest']),
                                           **byte_pin(inputs[spec['manifest']])},
                      'selectedInputPins': spec['inputFiles'], 'publishedCoreFiles': sorted(core),
                      'publishedSupportFiles': sorted(support), 'localOnlyArtifacts': sorted(forbidden),
                      'counts': counts, 'savedChecks': checks, 'outputs': outputs,
                      'publicationScope': 'Selected frozen metadata bytes and saved check schemas only. '
                                          'Referenced local implementations and larger AST histories remain local; '
                                          'semantic, upstream equivalence, mode and runtime checks are not rerun.',
                      'globalEvidenceJournalReadOrModified': False,
                      'featureDenominatorEstablished': False, 'fullAnalysisCompleted': False}
        if cid == 'react-upstream-identity-contracts':
            provenance['publicHttpReceiptPolicy'] = {
                'path': 'upstream/fetch-receipts.json',
                'transformation': 'Recursively omit case-insensitive set-cookie header keys/pairs; all other values retained.',
                'rawInputPinRetainedInConfigurationAndOriginalManifest': True,
                'publishedReceiptIsDerivedRatherThanAnExactByteCopy': True,
                'sourceJournalLocatorsContinueToIdentifyTheOriginalLocalInputs': True}
        pending[cid + '-provenance.json'] = encoded(provenance)
        receipt_note = ('公开 HTTP 回执递归省略 set-cookie 响应头；此文件是派生元数据，原始回执留在本地，'
                        '原 pin 与省略位置见发布来源。\n\n'
                        if cid == 'react-upstream-identity-contracts' else '')
        pending[cid + '-summary.md'] = (
            f'# {spec["title"]}\n\n固定基线 `{BASELINE}`。本批保留 {counts["records"]} 条原始分析记录。\n\n'
            f'{spec["finding"]}\n\n{spec["limits"]}\n\n'
            f'[原始结果]({cid}.json)、[原始记录]({cid}-evidence.jsonl)、'
            f'[作者摘要]({cid}-raw-summary.md)、[核验]({cid}-validation.json)、'
            f'[同行摘要]({cid}-peer-review.md)、[冻结清单]({cid}-manifest.json)、'
            f'[发布来源]({cid}-provenance.json)。\n\n'
            + receipt_note + '仅发布明确允许的分析元数据与核验资料。完整源码、保存的完整单元、第三方实现和归档留在本地，'
            '不进入客户端恢复源码。原记录字段逐字保留，未增加全局 journal、运行观察或功能确认数。\n'
        ).encode()
        catalogs.append({'catalogId': cid, 'counts': counts, 'outputs': outputs,
                         'provenance': cid + '-provenance.json', 'summary': cid + '-summary.md'})
    index = {'schemaVersion': 1, 'baselineId': BASELINE, 'catalogs': catalogs,
             'catalogCount': len(catalogs), 'recordCount': sum(c['counts']['records'] for c in catalogs),
             'globalRecordsAdded': 0, 'runtimeConfirmedRecords': 0,
             'featureDenominatorEstablished': False, 'fullAnalysisCompleted': False,
             'configuration': {'sourcePath': CONFIG, **byte_pin(raw_config)}}
    pending['catalog-supplements-provenance.json'] = encoded(index)
    pending['raw/catalog-supplements/config.json'] = raw_config
    for name, raw in pending.items():
        atomic_write(out / relative(name), raw)
    return index
