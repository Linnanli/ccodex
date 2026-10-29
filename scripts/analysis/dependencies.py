#!/usr/bin/env python3
"""Inventory dependencies from a frozen release; never execute release code.

Package metadata, attribution notices and literal imports are distinct evidence
classes. Notice versions are candidates, not proof of runtime inclusion or an
unmodified upstream package. No third-party implementation is generated.
"""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import plistlib
import re
import subprocess


def sha(data):
    return hashlib.sha256(data).hexdigest()


def package_name(specifier):
    return '/'.join(specifier.split('/')[:2]) if specifier.startswith('@') else specifier.split('/')[0]


def classification(name, declaration=None):
    if name.startswith('@worklouder/') or name == 'wl-lvgl-wasm':
        return 'third-party-private-vendor'
    if name.startswith(('@oai/', '@openai/')) or (declaration and declaration.startswith(('workspace:', 'link:', 'file:'))):
        return 'first-party-private-candidate'
    return 'third-party-public-candidate'


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def csv_write(path, records, fields):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        for record in records:
            writer.writerow({key: json.dumps(record.get(key), ensure_ascii=False) if isinstance(record.get(key), (dict, list)) else record.get(key, '') for key in fields})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    baseline_path = Path(args.baseline).resolve()
    baseline = json.loads(baseline_path.read_text())
    extracted = Path(baseline['extractedDirectory'])
    snapshot = Path(baseline['snapshotApplication'])
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    inventory = json.loads((baseline_path.parent / 'files.json').read_text())
    archive_records = {r['archivePath']: r for r in inventory['archiveFiles']}
    disk_records = {r['sourcePath']: r for r in inventory['applicationFiles']}
    evidence = []
    evidence_ids = {}

    def ev(path, locator, claim, method='package-metadata', confidence='confirmed'):
        source_path = ('app.asar/' + path) if path in archive_records else path
        key = source_path, json.dumps(locator, sort_keys=True), claim
        if key in evidence_ids:
            return evidence_ids[key]
        record = archive_records.get(path) or disk_records[path]
        identifier = 'dep-e-' + str(len(evidence) + 1).zfill(5)
        evidence_ids[key] = identifier
        evidence.append({'id': identifier, 'baselineId': baseline['baselineId'], 'claim': claim,
                         'sourcePath': source_path, 'sourceHash': record['sha256'], 'locator': locator,
                         'method': method, 'confidence': confidence, 'verificationStatus': 'static-confirmed' if confidence == 'confirmed' else 'needs-verification'})
        return identifier

    root = json.loads((extracted / 'package.json').read_text())
    declarations = {name: spec for scope in ('dependencies', 'devDependencies') for name, spec in root.get(scope, {}).items()}
    installed = []
    descriptors = []
    metadata_errors = []
    package_by_path = {}
    by_name = collections.defaultdict(list)
    license_names = re.compile(r'^(LICENSE|LICENCE|COPYING|NOTICE)(\.|$)', re.I)
    for relative in sorted(p for p in archive_records if p.endswith('/package.json') and p.startswith('node_modules/')):
        try:
            meta = json.loads((extracted / relative).read_text())
        except (OSError, ValueError) as error:
            metadata_errors.append({'path': relative, 'error': str(error)})
            continue
        if not meta.get('name') or not meta.get('version'):
            descriptors.append({'path': relative, 'keys': list(meta), 'evidenceId': ev(relative, {'jsonPointer': '/'}, 'Package-format descriptor lacks package name or version')})
            continue
        directory = str(PurePosixPath(relative).parent)
        licenses = [p for p in archive_records if str(PurePosixPath(p).parent) == directory and license_names.match(PurePosixPath(p).name)]
        item = {'id': 'installed-' + str(len(installed) + 1).zfill(3), 'name': meta['name'], 'version': meta['version'],
                'versionBasis': 'shipped-package-metadata', 'packagePath': directory, 'manifestPath': relative,
                'source': meta.get('repository'), 'homepage': meta.get('homepage'), 'license': meta.get('license'),
                'licenseFiles': [{'sourcePath': 'app.asar/' + p, 'sourceHash': archive_records[p]['sha256']} for p in licenses],
                'classification': classification(meta['name'], declarations.get(meta['name'])),
                'mode': 'unknown', 'modificationStatus': 'unknown-no-upstream-comparison',
                'dependencies': meta.get('dependencies', {}), 'optionalDependencies': meta.get('optionalDependencies', {}),
                'peerDependencies': meta.get('peerDependencies', {}), 'scripts': meta.get('scripts', {}),
                'evidenceIds': [ev(relative, {'jsonPointer': '/'}, f"Shipped manifest identifies {meta['name']} {meta['version']} with dependency/source/license metadata")],
                'recommendedIntegration': 'independent-vendor-package-or-adapter' if classification(meta['name'], declarations.get(meta['name'])) == 'third-party-private-vendor' else 'versioned-package-after-upstream-comparison',
                'unresolved': ['Upstream identity and modifications not independently verified', 'Codex/ChatGPT/shared ownership needs caller trace']}
        installed.append(item)
        by_name[item['name']].append(item)
        package_by_path[relative] = item

    external = []
    external_descriptors = []
    external_errors = []
    for relative in sorted(p for p in disk_records if p.endswith('/package.json') and '/app.asar.unpacked/' not in p):
        try:
            meta = json.loads((snapshot / relative).read_text())
        except (OSError, ValueError) as error:
            external_errors.append({'path': relative, 'error': str(error)})
            continue
        if not meta.get('name') or not meta.get('version'):
            external_descriptors.append({'path': relative, 'keys': list(meta), 'evidenceId': ev(relative, {'jsonPointer': '/'}, 'External package descriptor lacks name or version')})
            continue
        directory = str(PurePosixPath(relative).parent)
        licenses = [p for p in disk_records if str(PurePosixPath(p).parent) == directory and license_names.match(PurePosixPath(p).name)]
        item = {'id': 'external-' + str(len(external) + 1).zfill(3), 'name': meta['name'], 'version': meta['version'],
                'versionBasis': 'shipped-package-metadata', 'packagePath': directory, 'manifestPath': relative,
                'classification': classification(meta['name']), 'source': meta.get('repository'), 'license': meta.get('license'),
                'licenseFiles': [{'sourcePath': p, 'sourceHash': disk_records[p]['sha256']} for p in licenses],
                'dependencies': meta.get('dependencies', {}), 'optionalDependencies': meta.get('optionalDependencies', {}),
                'peerDependencies': meta.get('peerDependencies', {}), 'scripts': meta.get('scripts', {}),
                'mode': 'unknown', 'modificationStatus': 'unknown-no-upstream-comparison',
                'evidenceIds': [ev(relative, {'jsonPointer': '/'}, f"External shipped package {meta['name']} {meta['version']} with metadata")],
                'recommendedIntegration': 'recover-first-party-interface-or-independent-runtime' if classification(meta['name']) == 'first-party-private-candidate' else 'versioned-package-after-upstream-comparison',
                'unresolved': ['Upstream identity and modifications not independently verified', 'Codex/ChatGPT/shared ownership needs caller trace']}
        external.append(item)

    # Each notice is preserved separately, including versions repeated for a name.
    notice_path = 'Contents/Resources/THIRD_PARTY_NOTICES.txt'
    notice_data = (snapshot / notice_path).read_bytes()
    notice_pattern = re.compile(rb'^The following software may be included in this product: (.+?) \(([^\r\n]+)\)\r?$', re.M)
    matches = list(notice_pattern.finditer(notice_data))
    notices = []
    notice_by_name = collections.defaultdict(list)
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(notice_data)
        text = notice_data[match.end():end].decode(errors='replace')
        # These are license text clues, never a license audit conclusion.
        clues = []
        for label, pattern in [('MIT', r'\bMIT License\b|\bThe MIT License\b'), ('Apache-2.0', r'Apache License.*?Version 2\.0|Apache-2\.0'), ('BSD', r'BSD|Redistribution and use in source and binary forms'), ('ISC', r'ISC License|Permission to use, copy, modify, and/or distribute this software'), ('MPL-2.0', r'Mozilla Public License.*?2\.0'), ('0BSD', r'Zero-Clause BSD|BSD Zero Clause'), ('Zlib', r'zlib License|zlib/libpng'), ('LGPL', r'GNU LESSER GENERAL PUBLIC LICENSE'), ('GPL', r'GNU GENERAL PUBLIC LICENSE')]:
            if re.search(pattern, text, re.S | re.I): clues.append(label)
        name, version = (part.decode() for part in match.groups())
        item = {'id': 'notice-' + str(index + 1).zfill(4), 'name': name, 'version': version,
                'versionBasis': 'may-be-included-attribution-only', 'actualInclusion': 'unresolved',
                'licenseTextClues': clues, 'source': 'release-attribution', 'classification': classification(name, declarations.get(name)),
                'mode': 'unknown', 'modificationStatus': 'unknown-no-upstream-comparison',
                'evidenceIds': [ev(notice_path, {'byteStart': match.start(), 'byteEnd': end}, f'Attribution lists {name} ({version}) as may be included', 'release-attribution')]}
        notices.append(item)
        notice_by_name[name].append(item)

    # Literal imports from first-party shipping directories: lexical candidates.
    import_pattern = re.compile(rb'\b(?:require|import)\s*\(\s*["\x27`]([^"\x27`\n]+)["\x27`]\s*\)|\bfrom\s*["\x27`]([^"\x27`\n]+)["\x27`]')
    builtins = set('assert assert/strict async_hooks buffer child_process cluster console constants crypto dgram diagnostics_channel dns dns/promises domain events fs fs/promises http http2 https module net os path path/posix path/win32 perf_hooks process punycode querystring readline readline/promises repl stream stream/promises stream/web string_decoder sys timers timers/promises tls trace_events tty url util util/types v8 vm wasi worker_threads zlib'.split())
    imports = []
    imports_by_name = collections.defaultdict(list)
    scanned = []
    bundled_hints = []
    hint_specs = [
        ('react', rb'\.useTransition=function\([^)]*\)\{[^}]{0,160}\},[a-zA-Z_$][\w$]*\.version=["`]([0-9]+\.[0-9]+\.[0-9]+)["`]'),
        ('react-dom', rb'\.useFormStatus=function\([^)]*\)\{[^}]{0,160}\},[a-zA-Z_$][\w$]*\.version=["`]([0-9]+\.[0-9]+\.[0-9]+)["`]'),
        ('Statsig SDK family', rb'StatsigMetadataProvider=[a-zA-Z_$][\w$]*\.SDK_VERSION=void 0,[a-zA-Z_$][\w$]*\.SDK_VERSION=["`]([0-9]+\.[0-9]+\.[0-9]+)["`]'),
        ('Sentry SDK family', rb'__SENTRY__[^;]{0,100};return [a-zA-Z_$][\w$]*\.version=[a-zA-Z_$][\w$]*\.version\|\|["`]([0-9]+\.[0-9]+\.[0-9]+)["`]'),
        ('zod', rb'\{major:([0-9]+),minor:([0-9]+),patch:([0-9]+)\},[^;]{0,100}\$ZodType'),
    ]
    for relative in sorted(p for p in archive_records if p.endswith(('.js', '.mjs', '.cjs')) and p.startswith(('.vite/', 'webview/'))):
        data = (extracted / relative).read_bytes()
        scanned.append(relative)
        for name, pattern in hint_specs:
            for match in re.finditer(pattern, data):
                version = '.'.join(part.decode() for part in match.groups())
                bundled_hints.append({'id': 'bundle-hint-' + str(len(bundled_hints) + 1).zfill(3), 'name': name, 'version': version,
                                      'versionBasis': 'embedded-self-identification-with-library-context', 'actualBoundary': 'unresolved',
                                      'classification': 'third-party-bundled-candidate', 'modificationStatus': 'unknown-no-upstream-comparison', 'mode': 'unknown',
                                      'evidenceIds': [ev(relative, {'byteStart': match.start(), 'byteEnd': match.end()}, f'Embedded {name} self-identifies version {version}; upstream boundaries remain to verify', 'static-code', 'inferred')]})
        for match in import_pattern.finditer(data):
            spec = next(part for part in match.groups() if part is not None).decode(errors='replace')
            if spec.startswith(('.', '/', 'node:', 'http:', 'https:', 'data:')) or spec in builtins or '${' in spec:
                continue
            name = package_name(spec)
            item = {'specifier': spec, 'name': name, 'sourcePath': 'app.asar/' + relative,
                    'locator': {'byteStart': match.start(), 'byteEnd': match.end()},
                    'evidenceId': ev(relative, {'byteStart': match.start(), 'byteEnd': match.end()}, f'Literal bare import candidate {spec}', 'static-code', 'inferred')}
            imports.append(item)
            imports_by_name[name].append(item)

    def resolve(from_directory, name):
        directory = PurePosixPath(from_directory)
        while True:
            candidate = (directory / 'node_modules' / name / 'package.json').as_posix()
            if candidate in package_by_path:
                return package_by_path[candidate]
            if directory == PurePosixPath('.'):
                return None
            directory = directory.parent

    edges = []
    for item in installed:
        for scope in ('dependencies', 'optionalDependencies', 'peerDependencies'):
            for name, declaration in item[scope].items():
                target = resolve(item['packagePath'], name)
                exact = re.fullmatch(r'\d+\.\d+\.\d+(?:[-+][\w.-]+)?', declaration or '')
                edges.append({'from': item['id'], 'name': name, 'declaration': declaration, 'scope': scope,
                              'to': target['id'] if target else None, 'resolvedVersion': target['version'] if target else None,
                              'resolution': 'shipped-node-resolution-candidate' if target else 'not-shipped-at-resolution-path',
                              'exactDeclarationMismatch': bool(exact and target and declaration != target['version']),
                              'evidenceIds': [ev(item['manifestPath'], {'jsonPointer': '/' + scope + '/' + name.replace('~', '~0').replace('/', '~1')}, f'{item["name"]} declares {name} {declaration}')]})

    roots = []
    for scope in ('dependencies', 'devDependencies'):
        for name, declaration in root.get(scope, {}).items():
            occurrences = by_name.get(name, [])
            root_resolution = resolve('.', name)
            notice_versions = sorted(set(item['version'] for item in notice_by_name.get(name, [])))
            roots.append({'id': 'root-' + str(len(roots) + 1).zfill(3), 'name': name, 'scope': scope,
                          'declaredVersion': declaration, 'installedVersions': sorted(set(item['version'] for item in occurrences)),
                          'installedOccurrenceIds': [item['id'] for item in occurrences], 'noticeVersions': notice_versions,
                          'rootResolvedVersion': root_resolution['version'] if root_resolution else None,
                          'rootResolvedOccurrenceId': root_resolution['id'] if root_resolution else None,
                          'actualVersionStatus': 'shipped-root-manifest-confirmed' if root_resolution else 'nested-manifest-candidate-root-resolution-unresolved' if occurrences else 'unresolved-notice-candidate' if notice_versions else 'unresolved',
                          'source': [item['source'] for item in occurrences if item['source']] or ('monorepo-reference' if classification(name, declaration) == 'first-party-private-candidate' else 'release-declaration-only'),
                          'license': sorted(set(str(item['license']) for item in occurrences if item['license'])),
                          'classification': classification(name, declaration), 'mode': 'unknown',
                          'use': 'runtime-declared' if scope == 'dependencies' else 'build-or-development-declared',
                          'literalImportEvidenceIds': [item['evidenceId'] for item in imports_by_name.get(name, [])],
                          'modificationStatus': 'unknown-no-upstream-comparison',
                          'evidenceIds': [ev('package.json', {'jsonPointer': '/' + scope + '/' + name.replace('~', '~0').replace('/', '~1')}, f'Root declares {name} {declaration} in {scope}')],
                          'recommendedIntegration': 'recover-first-party-interface-and-own-implementation' if classification(name, declaration) == 'first-party-private-candidate' else 'independent-vendor-package-or-adapter' if classification(name, declaration) == 'third-party-private-vendor' else 'versioned-package-after-caller-and-upstream-verification',
                          'unresolved': ['Codex/ChatGPT/shared ownership', 'Upstream comparison and modification status'] + ([] if occurrences else ['Actual runtime package version and bundled code boundary'])})

    native = []
    for relative, record in sorted(archive_records.items()):
        if not relative.endswith(('.node', '.wasm')):
            continue
        owners = [item for item in installed if relative.startswith(item['packagePath'] + '/')]
        owner = max(owners, key=lambda item: len(item['packagePath'])) if owners else None
        physical = extracted / relative
        result = subprocess.run(['file', '-b', str(physical)], capture_output=True, text=True)
        native.append({'id': 'binary-' + str(len(native) + 1).zfill(3), 'sourcePath': 'app.asar/' + relative,
                       'sourceHash': record['sha256'], 'bytes': record.get('bytes'), 'kind': 'native-node-addon' if relative.endswith('.node') else 'wasm-or-webcil',
                       'fileIdentification': result.stdout.strip(), 'owner': owner['id'] if owner else None,
                       'ownerName': owner['name'] if owner else None, 'ownerVersion': owner['version'] if owner else None,
                       'mode': 'unknown', 'buildFromSourceStatus': 'unresolved',
                       'evidenceIds': [ev(relative, {'byteStart': 0, 'byteEnd': min(32, record.get('bytes', 0))}, 'Shipped native/Wasm artifact with file identification ' + result.stdout.strip(), 'file-magic')],
                       'recommendedIntegration': 'pin-independent-package-and-rebuild-for-target-runtime' if owner else 'identify-owner-source-and-runtime-before-replacement'})

    # Record all Mach-O/ELF/PE artifacts in the snapshot except ASAR-unpacked
    # duplicates, so helper executables and frameworks cannot be overlooked.
    runtime = []
    magic = {b'\xcf\xfa\xed\xfe', b'\xce\xfa\xed\xfe', b'\xfe\xed\xfa\xcf', b'\xfe\xed\xfa\xce', b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca', b'\xca\xfe\xba\xbf', b'\xbf\xba\xfe\xca', b'\x7fELF'}
    for relative, record in sorted(disk_records.items()):
        if record.get('kind') != 'file' or '/app.asar.unpacked/' in relative or relative.endswith('app.asar'):
            continue
        physical = snapshot / relative
        with physical.open('rb') as stream:
            header = stream.read(4)
        if header not in magic and not header.startswith(b'MZ'):
            continue
        result = subprocess.run(['file', '-b', str(physical)], capture_output=True, text=True)
        owners = [item for item in external if relative.startswith(item['packagePath'] + '/')]
        owner = max(owners, key=lambda item: len(item['packagePath'])) if owners else None
        runtime.append({'id': 'runtime-' + str(len(runtime) + 1).zfill(3), 'sourcePath': relative,
                        'sourceHash': record['sha256'], 'bytes': record['bytes'], 'fileIdentification': result.stdout.strip(),
                        'kind': 'native-node-addon' if relative.endswith('.node') else 'dynamic-library' if relative.endswith('.dylib') else 'runtime-or-helper',
                        'owner': owner['id'] if owner else None, 'ownerName': owner['name'] if owner else None,
                        'mode': 'unknown', 'version': owner['version'] if owner else None, 'versionStatus': 'owner-manifest' if owner else 'unresolved', 'sourceStatus': 'unresolved',
                        'evidenceIds': [ev(relative, {'byteStart': 0, 'byteEnd': 4}, 'Runtime binary artifact ' + result.stdout.strip(), 'file-magic')]})

    external_wasm = []
    for relative, record in sorted(disk_records.items()):
        if '/app.asar.unpacked/' in relative or not relative.endswith(('.wasm', '.wasm.br')):
            continue
        owners = [item for item in external if relative.startswith(item['packagePath'] + '/')]
        owner = max(owners, key=lambda item: len(item['packagePath'])) if owners else None
        external_wasm.append({'sourcePath': relative, 'sourceHash': record['sha256'], 'bytes': record['bytes'],
                              'kind': 'brotli-compressed-wasm' if relative.endswith('.br') else 'wasm', 'owner': owner['id'] if owner else None,
                              'ownerName': owner['name'] if owner else None, 'ownerVersion': owner['version'] if owner else None,
                              'mode': 'unknown', 'buildFromSourceStatus': 'unresolved',
                              'evidenceIds': [ev(relative, {'byteStart': 0, 'byteEnd': 8}, 'External Wasm artifact; source ownership needs verification', 'file-inventory')]})

    runtime_metadata = []
    for relative in ('Contents/Resources/owl-electron-app.json', 'Contents/Resources/codex-cli/codex-package.json', 'Contents/Resources/codex-cli/codex-resources/voice/manifest.json', 'Contents/Resources/codex-cli/codex-resources/voice/runtime.json', 'Contents/Resources/codex-cli/codex-resources/voice/sources.json'):
        if relative in disk_records:
            meta = json.loads((snapshot / relative).read_text())
            runtime_metadata.append({'sourcePath': relative, 'metadata': meta, 'evidenceIds': [ev(relative, {'jsonPointer': '/'}, 'Shipped runtime/build/source manifest', 'package-metadata')]})
    plist_metadata = []
    for relative in sorted(p for p in disk_records if p.endswith('/Info.plist') and '/app.asar.unpacked/' not in p):
        meta = plistlib.loads((snapshot / relative).read_bytes())
        keys = ('CFBundleName', 'CFBundleIdentifier', 'CFBundleShortVersionString', 'CFBundleVersion', 'CFBundleExecutable')
        plist_metadata.append({'sourcePath': relative, 'metadata': {key: meta.get(key) for key in keys},
                               'evidenceIds': [ev(relative, {'plistKeys': list(keys)}, 'Application/framework/helper reported identity and version', 'package-metadata')]})

    voice_sources = []
    relative = 'Contents/Resources/codex-cli/codex-resources/voice/sources.json'
    if relative in disk_records:
        meta = json.loads((snapshot / relative).read_text())
        for index, item in enumerate(meta.get('sources', [])):
            voice_sources.append({**item, 'modificationStatus': 'unknown-no-source-build-comparison', 'mode': 'unknown',
                                  'evidenceIds': [ev(relative, {'jsonPointer': '/sources/' + str(index)}, 'Voice runtime source declaration ' + item['name'] + ' ' + item['version'], 'package-metadata')]})
        for index, item in enumerate(meta.get('bundled_sources', [])):
            voice_sources.append({**item, 'versionBasis': 'revision', 'modificationStatus': 'unknown-no-source-build-comparison', 'mode': 'unknown',
                                  'evidenceIds': [ev(relative, {'jsonPointer': '/bundled_sources/' + str(index)}, 'Voice bundled source declaration ' + item['name'], 'package-metadata')]})

    source_inputs = []
    for owner in installed + external:
        records = archive_records if owner in installed else disk_records
        prefix = owner['packagePath'] + '/'
        for path in records:
            remainder = path.removeprefix(prefix)
            if path.startswith(prefix) and 'node_modules/' not in remainder and (path.endswith(('binding.gyp', 'Cargo.toml', 'Cargo.lock')) or Path(path).suffix in ('.c', '.cc', '.cpp', '.h', '.hpp', '.m', '.mm', '.rs')):
                source_inputs.append({'owner': owner['id'], 'sourcePath': 'app.asar/' + path if owner in installed else path,
                                      'sourceHash': records[path]['sha256'], 'status': 'source-or-build-input-present-not-build-verified'})

    build_inputs = []
    for script, command in root.get('scripts', {}).items():
        for match in re.finditer(r'(?<![\w])(?:\./|\.\./)[\w./-]+\.(?:mjs|cjs|js|ts)', command):
            target = match.group()
            exists = not target.startswith('../') and target.removeprefix('./') in archive_records
            build_inputs.append({'script': script, 'input': target, 'status': 'shipped' if exists else 'missing-from-release',
                                 'evidenceIds': [ev('package.json', {'jsonPointer': '/scripts/' + script.replace('~', '~0').replace('/', '~1')}, f'Build script {script} references {target}')]})
    for filename in ('pnpm-lock.yaml', 'package-lock.json', 'yarn.lock', 'pnpm-workspace.yaml', 'tsconfig.json', 'forge.config.ts', 'forge.config.js', 'vite.config.ts', 'vite.config.js'):
        build_inputs.append({'input': filename, 'status': 'shipped' if filename in archive_records else 'missing-from-release',
                             'evidenceIds': [], 'basis': 'complete-frozen-archive-path-inventory'})

    duplicate_versions = {name: sorted(set(item['version'] for item in items)) for name, items in by_name.items() if len(set(item['version'] for item in items)) > 1}
    summary = {'baselineId': baseline['baselineId'], 'scope': 'All frozen ASAR and external package manifests, all attribution entries, lexical bare imports across all shipped .vite/webview JavaScript, all .node/Wasm and disk binary magic',
               'counts': {'archiveMembers': len(archive_records), 'nodeModulesPackageJson': len(installed) + len(descriptors) + len(metadata_errors),
                          'installedPackageOccurrences': len(installed), 'installedUniqueNames': len(by_name), 'packageFormatDescriptors': len(descriptors),
                          'metadataErrors': len(metadata_errors), 'rootRuntimeDeclarations': len(root.get('dependencies', {})), 'rootDevDeclarations': len(root.get('devDependencies', {})),
                          'externalPackageJson': len(external) + len(external_descriptors) + len(external_errors), 'externalPackageOccurrences': len(external),
                          'externalPackageUniqueNames': len(set(item['name'] for item in external)), 'externalPackageDescriptors': len(external_descriptors), 'externalMetadataErrors': len(external_errors),
                          'rootDeclarationsWithInstalledManifest': sum(bool(item['installedOccurrenceIds']) for item in roots),
                          'rootDeclarationsWithRootResolvedManifest': sum(bool(item['rootResolvedOccurrenceId']) for item in roots),
                          'rootDeclarationsWithoutInstalledManifest': sum(not item['installedOccurrenceIds'] for item in roots),
                          'rootPrivateCandidates': sum(item['classification'] == 'first-party-private-candidate' for item in roots),
                          'noticeEntries': len(notices), 'noticeUniqueNames': len(notice_by_name),
                          'firstPartyShippingJsScanned': len(scanned), 'literalBareImportCandidates': len(imports), 'literalBareImportUniqueNames': len(imports_by_name),
                          'bundledSelfIdentificationHints': len(bundled_hints),
                          'nativeAddons': sum(item['kind'] == 'native-node-addon' for item in native), 'wasmOrWebcilArtifacts': sum(item['kind'] == 'wasm-or-webcil' for item in native),
                          'diskRuntimeBinaries': len(runtime), 'installedDependencyEdges': len(edges), 'unresolvedInstalledDependencyEdges': sum(not item['to'] for item in edges),
                          'externalNativeAddons': sum(item['kind'] == 'native-node-addon' for item in runtime), 'externalWasmArtifacts': len(external_wasm),
                          'voiceSourceDeclarations': len(voice_sources), 'sourceOrBuildInputsPresent': len(source_inputs),
                          'exactDeclarationMismatches': sum(item['exactDeclarationMismatch'] for item in edges),
                          'buildInputOccurrences': len(build_inputs), 'missingBuildInputOccurrences': sum(item['status'] == 'missing-from-release' for item in build_inputs),
                          'behaviorVerifiedDependencies': 0, 'upstreamComparedPackages': 0},
               'installedMultipleVersions': duplicate_versions,
               'limitations': ['Attribution says may be included and mixes multiple subprojects; it is not a lockfile or actual runtime inclusion proof.',
                               'Package name/version metadata does not prove its shipped files are unmodified upstream.',
                               'Import scanning is lexical; expressions and custom loaders require REA/AST and runtime corroboration.',
                               'Codex/ChatGPT/shared mode ownership remains unresolved until callers are traced.',
                               'Exact package metadata versions are package-reported facts; registry content, integrity and version locks were not verified.',
                               'Native file identification confirms artifact/platform, not source rebuildability or runtime ABI compatibility.']}
    write_json(output / 'dependencies.json', {'rootDeclarations': roots, 'installedPackages': installed, 'externalPackages': external, 'bundledHints': bundled_hints, 'packageDescriptors': descriptors, 'externalPackageDescriptors': external_descriptors, 'metadataErrors': metadata_errors, 'externalMetadataErrors': external_errors, 'installedEdges': edges, 'literalImports': imports})
    write_json(output / 'attribution.json', notices)
    write_json(output / 'native-runtime.json', {'archiveArtifacts': native, 'diskRuntimeBinaries': runtime, 'externalWasmArtifacts': external_wasm, 'runtimeMetadata': runtime_metadata, 'plistMetadata': plist_metadata, 'voiceSources': voice_sources, 'sourceInputs': source_inputs})
    write_json(output / 'build-inputs.json', build_inputs)
    write_json(output / 'summary.json', summary)
    (output / 'evidence.jsonl').write_text(''.join(json.dumps(item, ensure_ascii=False) + '\n' for item in evidence))
    csv_write(output / 'root-dependencies.csv', roots, ['id', 'name', 'scope', 'declaredVersion', 'rootResolvedVersion', 'installedVersions', 'noticeVersions', 'actualVersionStatus', 'classification', 'source', 'license', 'mode', 'use', 'modificationStatus', 'recommendedIntegration', 'evidenceIds', 'literalImportEvidenceIds', 'unresolved'])
    csv_write(output / 'installed-dependencies.csv', installed, ['id', 'name', 'version', 'packagePath', 'classification', 'source', 'license', 'licenseFiles', 'mode', 'modificationStatus', 'evidenceIds', 'unresolved'])
    csv_write(output / 'external-dependencies.csv', external, ['id', 'name', 'version', 'packagePath', 'classification', 'source', 'license', 'licenseFiles', 'mode', 'modificationStatus', 'evidenceIds', 'unresolved'])
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
