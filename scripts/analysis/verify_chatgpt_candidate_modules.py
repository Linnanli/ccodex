#!/usr/bin/env python3
"""Independent integrity checks. Reads frozen bytes; never parses or executes JS."""
import argparse
import collections
import hashlib
import json
import pathlib
import re
import sys

BASELINE_ID = 'codex-26.1007.30912-c5b273322a83'
FRESH = re.compile(r'^(?:MODE-AST-|CGP-E)')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def walk(value, pointer=''):
    yield pointer, value
    if isinstance(value, dict):
        for key, item in value.items():
            escaped = str(key).replace('~', '~0').replace('/', '~1')
            yield from walk(item, pointer + '/' + escaped)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk(item, pointer + '/' + str(index))


def resolve(value, pointer):
    if pointer == '':
        return value
    if not isinstance(pointer, str) or not pointer.startswith('/'):
        raise ValueError('Not a JSON pointer')
    for part in pointer[1:].split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def evidence_id(record):
    return record.get('id') or record.get('evidenceId')


def locator(record):
    for key in ['locator', 'range', 'byteRange']:
        value = record.get(key)
        if isinstance(value, dict) and type(value.get('start')) is int:
            end = value.get('endExclusive')
            if type(end) is not int:
                end = value.get('end')
            if type(end) is int:
                return value['start'], end
    return None


def source_hash(record):
    return record.get('sourceHash') or record.get('sourceSha256')


def span_hash(record):
    return record.get('spanHash') or record.get('spanSha256')


class Verifier:
    def __init__(self, args):
        self.args = args
        self.root = pathlib.Path.cwd().resolve()
        self.documents = {}
        self.raw = {}
        self.catalog = collections.defaultdict(list)
        self.sources = {}
        self.source_checks = {}
        self.errors = []
        self.pointer_checks = []
        self.direct_hash_checks = []
        self.indirect_hash_checks = []
        self.reference_checks = []
        self.external_span_checks = []
        self.catalogs = []
        self.unknowns = []
        self.absent_evidence_fields = 0
        self.structural_reference_checks = []

    def artifact_path(self, value):
        path = pathlib.Path(value)
        path = (self.root / path).resolve() if not path.is_absolute() else path.resolve()
        path.relative_to(self.root)
        rel = str(path.relative_to(self.root))
        if not (rel.startswith('.analysis-local/') or rel.startswith('analysis/') or rel.startswith('scripts/analysis/')):
            raise ValueError('Outside analysis-artifact scope: ' + rel)
        return path

    def read(self, value):
        path = self.artifact_path(value)
        if path not in self.raw:
            self.raw[path] = path.read_bytes()
        return self.raw[path]

    def document(self, value):
        path = self.artifact_path(value)
        if path not in self.documents:
            self.documents[path] = json.loads(self.read(path))
        return self.documents[path]

    def check_pin(self, artifact_path, expected, origin, pointer, layer, expected_bytes=None):
        target = self.direct_hash_checks if layer == 'direct' else self.indirect_hash_checks
        record = {'path': str(artifact_path), 'originArtifact': origin, 'jsonPointer': pointer,
                  'expectedSha256': expected, 'layer': layer}
        try:
            raw = self.read(artifact_path)
            record.update(observedSha256=digest(raw), observedBytes=len(raw))
            record['status'] = 'matched' if expected == record['observedSha256'] else 'mismatch'
            if expected_bytes is not None:
                record['expectedBytes'] = expected_bytes
                if len(raw) != expected_bytes:
                    record['status'] = 'mismatch'
            if record['status'] != 'matched' and layer == 'direct':
                self.errors.append({'kind': 'direct-artifact-pin', **record})
        except Exception as error:
            record.update(status='unreadable', error=str(error))
            if layer == 'direct':
                self.errors.append({'kind': 'direct-artifact-pin', **record})
        target.append(record)

    def add_catalog(self, value, expected=None, origin=None, pointer=None):
        path = self.artifact_path(value)
        if any(x['path'] == str(path.relative_to(self.root)) for x in self.catalogs):
            return
        raw = self.read(path)
        duplicate_ids = []
        seen = set()
        rows = [json.loads(line) for line in raw.decode('utf8').splitlines() if line.strip()]
        for index, record in enumerate(rows):
            name = evidence_id(record)
            if not isinstance(name, str):
                self.errors.append({'kind': 'catalog-record-without-id', 'path': str(path), 'line': index + 1})
                continue
            if name in seen:
                duplicate_ids.append(name)
            seen.add(name)
            self.catalog[name].append((str(path.relative_to(self.root)), index + 1, record))
        self.catalogs.append({'path': str(path.relative_to(self.root)), 'sha256': digest(raw),
                              'records': len(rows), 'duplicateIds': duplicate_ids,
                              'pinLevel': 'matched-explicit-pin' if expected == digest(raw) else 'actual-hash-only' if expected is None else 'mismatched-pin',
                              'pinOrigin': origin, 'pinPointer': pointer})
        if duplicate_ids:
            self.errors.append({'kind': 'catalog-duplicate-ids', 'path': str(path), 'ids': duplicate_ids})

    def add_embedded(self, value, path):
        for pointer, record in walk(value):
            if isinstance(record, dict) and isinstance(evidence_id(record), str) and record.get('sourcePath') and locator(record) and span_hash(record):
                self.catalog[evidence_id(record)].append((str(path), pointer, record))

    def load_journal_descriptors(self, value, path):
        for pointer, record in walk(value):
            if not isinstance(record, dict):
                continue
            journal = record.get('path') or record.get('artifactPath') or record.get('sourceFile')
            expected = record.get('sha256') or record.get('artifactSha256')
            if isinstance(journal, str) and journal.endswith('.jsonl'):
                try:
                    if not journal.startswith(('.analysis-local/', 'analysis/', '/')):
                        journal = str(pathlib.Path(path).parent / journal)
                    self.add_catalog(journal, expected, str(path), pointer)
                except Exception as error:
                    self.unknowns.append({'kind': 'external-catalog-descriptor', 'originArtifact': str(path), 'jsonPointer': pointer, 'path': journal, 'reason': str(error)})

    def source_bytes(self, source_path, expected_hash):
        prefix = 'app.asar/'
        rel = source_path[len(prefix):] if source_path.startswith(prefix) else source_path
        path = pathlib.Path(rel)
        if path.is_absolute():
            path = path.resolve()
        else:
            path = (self.source_root / path).resolve()
        path.relative_to(self.source_root)
        if path not in self.sources:
            raw = path.read_bytes()
            self.sources[path] = raw
            self.source_checks[str(path.relative_to(self.source_root))] = {'sourcePath': 'app.asar/' + str(path.relative_to(self.source_root)), 'observedSha256': digest(raw), 'bytes': len(raw)}
        raw = self.sources[path]
        actual_hash = self.source_checks[str(path.relative_to(self.source_root))]['observedSha256']
        if actual_hash != expected_hash:
            raise ValueError('Frozen source SHA256 mismatch: ' + str(source_path))
        return raw

    def check_span(self, record):
        location = locator(record)
        if not location or not record.get('sourcePath') or not source_hash(record) or not span_hash(record):
            raise ValueError('Incomplete source/byte-range/spanHash metadata')
        raw = self.source_bytes(record['sourcePath'], source_hash(record))
        start, end = location
        if not 0 <= start < end <= len(raw):
            raise ValueError('Out-of-range byte locator')
        # Decode only the span; boundary validation rejects offsets inside UTF-8 codepoints.
        raw[start:end].decode('utf8')
        if digest(raw[start:end]) != span_hash(record):
            raise ValueError('Span SHA256 mismatch')
        return {'sourcePath': record['sourcePath'], 'sourceHash': source_hash(record),
                'range': {'start': start, 'endExclusive': end}, 'spanHash': span_hash(record)}

    def unique_record(self, name):
        candidates = self.catalog.get(name, [])
        if not candidates:
            raise ValueError('Evidence ID missing from loaded catalogs: ' + name)
        identities = {(r.get('sourcePath', '').removeprefix('app.asar/'), source_hash(r), locator(r)) for _, _, r in candidates}
        spans = {span_hash(r) for _, _, r in candidates if span_hash(r)}
        if len(identities) != 1 or len(spans) > 1:
            raise ValueError('Evidence ID has incompatible catalog records: ' + name)
        best = next((x for x in candidates if span_hash(x[2])), candidates[0])
        return best, len(candidates)

    def check_references(self, value, path, artifact_map):
        external_ids = set()
        for pointer, record in walk(value):
            if not isinstance(record, dict):
                continue
            descriptor = record.get('sourceArtifact')
            if isinstance(descriptor, dict):
                key, target_pointer = descriptor.get('key'), descriptor.get('jsonPointer')
                try:
                    target = artifact_map[key]
                    resolve(self.document(target), target_pointer)
                    self.pointer_checks.append({'originArtifact': str(path), 'jsonPointer': pointer + '/sourceArtifact', 'targetKey': key, 'targetArtifact': str(target), 'targetJsonPointer': target_pointer, 'status': 'resolved'})
                except Exception as error:
                    self.errors.append({'kind': 'artifact-json-pointer', 'originArtifact': str(path), 'jsonPointer': pointer, 'descriptor': descriptor, 'error': str(error)})
            if isinstance(record.get('jsonPointer'), str) and isinstance(record.get('artifactPath'), str):
                try:
                    if record.get('artifactSha256'):
                        self.check_pin(record['artifactPath'], record['artifactSha256'], str(path), pointer, 'direct')
                    resolve(self.document(record['artifactPath']), record['jsonPointer'])
                    self.pointer_checks.append({'originArtifact': str(path), 'jsonPointer': pointer, 'targetArtifact': record['artifactPath'], 'targetJsonPointer': record['jsonPointer'], 'status': 'resolved'})
                except Exception as error:
                    self.errors.append({'kind': 'artifact-json-pointer', 'originArtifact': str(path), 'jsonPointer': pointer, 'error': str(error)})
            for key, item in record.items():
                if not re.search(r'evidenceIds?$', key, re.I) and key not in ['bindingEvidence', 'routeContractReferences']:
                    continue
                if item is None:
                    self.absent_evidence_fields += 1
                    continue
                names = item if isinstance(item, list) else [item]
                for index, name in enumerate(names):
                    if not isinstance(name, str):
                        self.errors.append({'kind': 'unsupported-evidence-reference', 'originArtifact': str(path), 'jsonPointer': pointer + '/' + key, 'value': item})
                        continue
                    if name in ['', 'unknown', 'not-available']:
                        self.unknowns.append({'kind': 'explicit-empty-or-unknown-evidence-reference', 'originArtifact': str(path), 'jsonPointer': pointer + '/' + key, 'value': name})
                        continue
                    if key == 'routeContractReferences' and name.startswith('ROUTE-') and not name.startswith('ROUTE-AST-'):
                        routes = self.document(artifact_map['routes'])
                        matches = [i for i, r in enumerate(routes['registrations']) if r['id'] == name]
                        if len(matches) != 1:
                            self.errors.append({'kind': 'structural-route-reference', 'originArtifact': str(path), 'jsonPointer': pointer + '/' + key, 'id': name})
                        else:
                            self.structural_reference_checks.append({'originArtifact': str(path), 'jsonPointer': pointer + '/' + key, 'routeId': name, 'targetJsonPointer': '/registrations/' + str(matches[0]), 'status': 'resolved'})
                        continue
                    try:
                        (catalog_path, line_or_pointer, evidence), copies = self.unique_record(name)
                        self.reference_checks.append({'originArtifact': str(path), 'jsonPointer': pointer + '/' + key + ('/' + str(index) if isinstance(item, list) else ''), 'evidenceId': name, 'catalogPath': catalog_path, 'catalogLocator': line_or_pointer, 'matchingCatalogCopies': copies, 'status': 'resolved'})
                        if not FRESH.match(name):
                            external_ids.add(name)
                    except Exception as error:
                        self.errors.append({'kind': 'evidence-reference', 'originArtifact': str(path), 'jsonPointer': pointer + '/' + key, 'evidenceId': name, 'error': str(error)})
        return external_ids

    def run(self):
        main_path = str(self.artifact_path(self.args.main_json).relative_to(self.root))
        main = self.document(main_path)
        baseline = self.document('.analysis-local/current-baseline.json')
        if main['baselineId'] != BASELINE_ID or baseline['baselineId'] != BASELINE_ID:
            raise ValueError('Baseline identity mismatch')
        self.source_root = pathlib.Path(baseline['extractedDirectory']).resolve()
        artifact_map = {'self': main_path}
        for index, record in enumerate(main['sourceArtifacts']):
            artifact_map[record['key']] = record['path']
            self.check_pin(record['path'], record['sha256'], main_path, f'/sourceArtifacts/{index}', 'direct', record.get('bytes'))
        self.add_catalog(self.args.main_evidence)
        for key in ['routes', 'guards', 'request-wrappers', 'request-wrapper-ast', 'project-review']:
            value = self.document(artifact_map[key])
            self.add_embedded(value, artifact_map[key])
            self.load_journal_descriptors(value, artifact_map[key])
            # Historical dependency pins are audited separately from new direct inputs.
            if key in ['request-wrappers', 'request-wrapper-ast']:
                for index, record in enumerate(value.get('inputs') or []):
                    target = record.get('path') or record.get('artifactPath')
                    expected = record.get('sha256') or record.get('artifactSha256')
                    if isinstance(target, str) and isinstance(expected, str):
                        self.check_pin(target, expected, artifact_map[key], f'/inputs/{index}', 'indirect', record.get('bytes'))
        # This existing route journal is not explicitly pinned by route-contracts.json.
        self.add_catalog('.analysis-local/feature-work/route-contract-evidence.jsonl')
        project = self.document(artifact_map['project-review'])
        self.add_catalog(artifact_map['project-evidence'], next(x['sha256'] for x in main['sourceArtifacts'] if x['key'] == 'project-evidence'), main_path, '/sourceArtifacts')
        for key, meta in project.get('sourceArtifacts', {}).items():
            self.check_pin(meta['artifactPath'], meta['artifactSha256'], artifact_map['project-review'], '/sourceArtifacts/' + key, 'direct')

        fresh_rows = [json.loads(line) for line in self.read(self.args.main_evidence).decode('utf8').splitlines() if line.strip()]
        fresh_checks = []
        for index, record in enumerate(fresh_rows):
            name = evidence_id(record)
            if not name or not FRESH.match(name):
                self.errors.append({'kind': 'unexpected-fresh-evidence-prefix', 'line': index + 1, 'id': name})
                continue
            try:
                fresh_checks.append({'evidenceId': name, **self.check_span(record)})
            except Exception as error:
                self.errors.append({'kind': 'fresh-span', 'line': index + 1, 'id': name, 'error': str(error)})

        function_checks, call_checks, function_ids, call_ids = [], [], set(), set()
        for mi, module in enumerate(main['modules']):
            raw = self.source_bytes(module['sourcePath'], module['sourceHash'])
            if len(raw) != module['sourceBytes']:
                self.errors.append({'kind': 'module-byte-identity', 'moduleIndex': mi})
            for kind, evidence_key, collection, id_set in [('function', 'definitionEvidenceId', function_checks, function_ids), ('call', 'evidenceId', call_checks, call_ids)]:
                for ri, record in enumerate(module['functions' if kind == 'function' else 'calls']):
                    name = record[evidence_key]
                    try:
                        (_, _, evidence), _ = self.unique_record(name)
                        if locator(record) != locator(evidence) or evidence['sourcePath'] != module['sourcePath'] or source_hash(evidence) != module['sourceHash']:
                            raise ValueError('Function/call range or source identity differs from journal')
                        identifier = record.get('functionId') if kind == 'function' else record.get('callId')
                        if identifier:
                            if identifier in id_set:
                                raise ValueError('Duplicate function/call ID')
                            id_set.add(identifier)
                        collection.append({'moduleIndex': mi, 'recordIndex': ri, 'id': identifier, 'evidenceId': name, 'status': 'source-range-and-journal-identity-matched'})
                    except Exception as error:
                        self.errors.append({'kind': kind + '-range-reference', 'moduleIndex': mi, 'recordIndex': ri, 'evidenceId': name, 'error': str(error)})
        for count, actual in [('targetModules', len(main['modules'])), ('targetSourceBytes', sum(x['sourceBytes'] for x in main['modules'])), ('functions', len(function_checks)), ('callAndNewExpressions', len(call_checks)), ('journalRecords', len(fresh_rows))]:
            if main['summary'].get(count) != actual:
                self.errors.append({'kind': 'summary-denominator', 'field': count, 'declared': main['summary'].get(count), 'observed': actual})
        if len(main['modules']) != 9 or len({x['sourcePath'] for x in main['modules']}) != 9:
            self.errors.append({'kind': 'nine-frozen-modules-required'})
        module_id_set = {x['sourcePath'] for x in main['modules']}
        if {x['sourcePath'] for x in fresh_checks} != module_id_set:
            self.errors.append({'kind': 'fresh-evidence-source-denominator'})

        external_ids = self.check_references(main, main_path, artifact_map)
        external_ids |= self.check_references(project, artifact_map['project-review'], artifact_map)
        for name in sorted(external_ids):
            (_, _, record), _ = self.unique_record(name)
            try:
                self.external_span_checks.append({'evidenceId': name, 'status': 'frozen-source-and-span-verified', **self.check_span(record)})
            except Exception as error:
                self.external_span_checks.append({'evidenceId': name, 'status': 'catalog-only; source-span-not-verified', 'reason': str(error)})
                self.unknowns.append({'kind': 'external-span-validation-level', 'evidenceId': name, 'reason': str(error)})

        historical_mismatches = [x for x in self.indirect_hash_checks if x['status'] != 'matched']
        distinct_history = {(x['path'], x['expectedSha256'], x.get('observedSha256')) for x in historical_mismatches}
        report = {
            'schemaVersion': 1, 'baselineId': BASELINE_ID,
            'status': 'core-failed' if self.errors else 'core-passed; historical-input-mismatch' if historical_mismatches else 'core-passed; external-validation-limits' if self.unknowns else 'core-and-requested-reference-layers-passed',
            'scope': {'mainJson': main_path, 'mainJsonSha256': digest(self.read(main_path)), 'mainEvidence': self.args.main_evidence, 'mainEvidenceSha256': digest(self.read(self.args.main_evidence)), 'targetJavascriptExecuted': False, 'newAstParsing': False, 'externalSpanScope': 'Only evidence IDs referenced by the main/project review JSON; unused external catalog spans were not validated.'},
            'reproduction': {'scriptPath': str(pathlib.Path(__file__).resolve().relative_to(self.root)), 'scriptSha256': digest(pathlib.Path(__file__).read_bytes()), 'arguments': vars(self.args)},
            'core': {'errorCount': len(self.errors), 'errors': self.errors, 'directArtifactPinChecks': len(self.direct_hash_checks), 'directArtifactPinMatches': sum(x['status'] == 'matched' for x in self.direct_hash_checks), 'frozenModuleIdentities': [{'sourcePath': m['sourcePath'], 'sourceHash': m['sourceHash'], 'sourceBytes': m['sourceBytes']} for m in main['modules']], 'freshEvidenceRecords': len(fresh_rows), 'freshSpanChecksPassed': len(fresh_checks), 'modeAstRecords': sum((evidence_id(x) or '').startswith('MODE-AST-') for x in fresh_rows), 'cgpRecords': sum((evidence_id(x) or '').startswith('CGP-E') for x in fresh_rows), 'functionRangeChecksPassed': len(function_checks), 'callRangeChecksPassed': len(call_checks), 'functionIdsDistinct': len(function_ids), 'callIdsDistinct': len(call_ids), 'jsonPointersResolved': len(self.pointer_checks), 'evidenceReferenceOccurrencesResolved': len(self.reference_checks), 'nullEvidenceFieldsDeclaredAbsent': self.absent_evidence_fields},
            'directArtifactHashChecks': self.direct_hash_checks,
            'pointerChecks': self.pointer_checks,
            'evidenceReferenceChecks': self.reference_checks,
            'structuralReferenceChecks': self.structural_reference_checks,
            'catalogs': self.catalogs,
            'external': {'evidenceIdsReferenced': len(external_ids), 'sourceSpanChecksPassed': sum(x['status'] == 'frozen-source-and-span-verified' for x in self.external_span_checks), 'catalogOnlySpanRecords': sum(x['status'] != 'frozen-source-and-span-verified' for x in self.external_span_checks), 'historicalInputPinChecks': len(self.indirect_hash_checks), 'historicalInputPinMismatchesDistinct': len(distinct_history), 'historicalInputPinMismatchOccurrences': len(historical_mismatches), 'historicalInputHashChecks': self.indirect_hash_checks, 'spanChecks': self.external_span_checks},
            'sourceHashChecks': list(self.source_checks.values()), 'unknowns': self.unknowns,
            'limitations': ['No new AST parse was performed: function/call syntax classifications are inherited facts, while identity, exact byte spans, hashes and references were checked independently.', 'A route journal without an explicit expected pin is actual-hash-only, even when all referenced source spans match.', 'Historical RWC indirect input pin failures are separate from the nine new module identities, direct artifact pins, fresh spans and reference errors.', 'No product-mode, runtime reachability or exclusion inference is made.'],
            'allLayersPassed': not self.errors and not historical_mismatches and not self.unknowns,
        }
        output_path = self.artifact_path(self.args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'output': str(output_path.relative_to(self.root)), 'sha256': digest(output_path.read_bytes()), 'bytes': output_path.stat().st_size, 'status': report['status'], 'coreErrorCount': len(self.errors), 'freshSpans': len(fresh_checks), 'functionRanges': len(function_checks), 'callRanges': len(call_checks), 'pointers': len(self.pointer_checks), 'evidenceReferenceOccurrences': len(self.reference_checks), 'historicalMismatchesDistinct': len(distinct_history), 'unknowns': len(self.unknowns)}))
        return bool(self.errors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--main-json', default='.analysis-local/mode-boundary-work/chatgpt-candidate-module-contracts.json')
    parser.add_argument('--main-evidence', default='.analysis-local/mode-boundary-work/evidence.jsonl')
    parser.add_argument('--output', default='.analysis-local/mode-boundary-work/validation.json')
    args = parser.parse_args()
    return Verifier(args).run()


if __name__ == '__main__':
    sys.exit(main())
