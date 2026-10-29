#!/usr/bin/env python3
"""Compare fixed public checked-in schemas to shipped CLI schema generation."""
import hashlib
import json
from pathlib import Path
import re

workspace = Path(__file__).resolve().parents[2]
baseline = json.loads((workspace / '.analysis-local/current-baseline.json').read_text())
out = workspace / 'analysis' / baseline['baselineId']
public = json.loads((out / 'public-protocol-source.json').read_text())
assert public['status'] == 'downloaded'
paths = {'public': out / 'raw/public-protocol/schema', 'shippedStable': out / 'raw/protocol/stable',
         'shippedExperimental': out / 'raw/protocol/experimental'}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def shape(value):
    """Remove schema documentation keywords without dropping named business fields/data."""
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            if key in {'description', 'title', '$schema', '$comment'}:
                continue
            if key in {'properties', 'patternProperties', 'definitions', '$defs', 'dependentSchemas'}:
                result[key] = {name: shape(schema) for name, schema in child.items()}
            elif key in {'oneOf', 'anyOf', 'allOf', 'prefixItems'}:
                result[key] = [shape(schema) for schema in child]
            elif key == 'items' and isinstance(child, list):
                result[key] = [shape(schema) for schema in child]
            elif key in {'items', 'additionalItems', 'additionalProperties', 'unevaluatedProperties',
                         'propertyNames', 'contains', 'not', 'if', 'then', 'else'}:
                result[key] = shape(child)
            elif key == 'dependencies':
                result[key] = {name: shape(schema) if isinstance(schema, dict) else schema
                               for name, schema in child.items()}
            else:
                result[key] = child
        return result
    return value


def differences(public_value, shipped_value, pointer=''):
    """JSON-pointer differences, with direction explicit and no documentation noise."""
    if type(public_value) is not type(shipped_value):
        return [{'pointer': pointer, 'change': 'changed', 'public': public_value, 'shipped': shipped_value}]
    if isinstance(public_value, dict):
        result = []
        for key in sorted(set(public_value) | set(shipped_value)):
            child = pointer + '/' + key.replace('~', '~0').replace('/', '~1')
            if key not in shipped_value:
                result.append({'pointer': child, 'change': 'public-added', 'public': public_value[key]})
            elif key not in public_value:
                result.append({'pointer': child, 'change': 'public-removed', 'shipped': shipped_value[key]})
            else:
                result.extend(differences(public_value[key], shipped_value[key], child))
        return result
    if isinstance(public_value, list) and len(public_value) == len(shipped_value):
        return [delta for i, (left, right) in enumerate(zip(public_value, shipped_value))
                for delta in differences(left, right, pointer + '/' + str(i))]
    return [] if public_value == shipped_value else [
        {'pointer': pointer, 'change': 'changed', 'public': public_value, 'shipped': shipped_value}]


def variants(schema):
    result = {}
    for variant in schema.get('oneOf', []):
        names = variant.get('properties', {}).get('method', {}).get('enum', [])
        if len(names) == 1:
            result[names[0]] = variant
    return result


def closure(schema, value):
    definitions = schema.get('definitions', {})
    required = {}

    def visit(obj):
        if isinstance(obj, dict):
            ref = obj.get('$ref')
            if ref and ref.startswith('#/definitions/'):
                name = ref[len('#/definitions/'):]
                if name not in required:
                    assert name in definitions, 'Unresolved definition: ' + name
                    required[name] = definitions[name]
                    visit(definitions[name])
            for child in obj.values():
                visit(child)
        elif isinstance(obj, list):
            for child in obj:
                visit(child)
    visit(value)
    return {'variant': shape(value), 'definitions': {name: shape(schema) for name, schema in required.items()}}


unions = ['ClientRequest.json', 'ClientNotification.json', 'ServerRequest.json', 'ServerNotification.json']
all_schemas = {label: {name: json.loads((directory / name).read_text()) for name in unions}
               for label, directory in paths.items()}
generation = json.loads((out / 'protocol-generation.json').read_text())
assert generation['baselineId'] == baseline['baselineId']
verified_inputs = []
for entry in public['downloads']:
    data = (out / entry['path']).read_bytes()
    assert len(data) == entry['bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256'], entry['path']
    verified_inputs.append({'source': 'fixed-public-download', **entry})
for run in generation['runs']:
    assert run['exitCode'] == 0
    for entry in run['schemaFiles']:
        data = (out / 'raw/protocol' / entry['path']).read_bytes()
        assert len(data) == entry['bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256'], entry['path']
        verified_inputs.append({'source': 'frozen-cli-schema-generation', **entry})
file_comparisons = []
for p in sorted(paths['public'].glob('*.json')):
    pub = json.loads(p.read_text())
    shipped = json.loads((paths['shippedStable'] / p.name).read_text())
    file_comparisons.append({'file': p.name, 'publicSha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                             'shippedStableSha256': hashlib.sha256((paths['shippedStable'] / p.name).read_bytes()).hexdigest(),
                             'jsonValueEqual': pub == shipped,
                             'shapeEqualIgnoringDocumentation': shape(pub) == shape(shipped),
                             'publicShapeSha256': hashlib.sha256(canonical(shape(pub))).hexdigest(),
                             'shippedShapeSha256': hashlib.sha256(canonical(shape(shipped))).hexdigest(),
                             'fieldDifferences': differences(shape(pub), shape(shipped))})
contracts = []
union_summary = {}
for name in unions:
    pub = variants(all_schemas['public'][name])
    stable = variants(all_schemas['shippedStable'][name])
    experimental = variants(all_schemas['shippedExperimental'][name])
    for method in sorted(set(pub) | set(experimental)):
        row = {'union': name, 'method': method, 'publicCheckedIn': method in pub,
               'shippedStable': method in stable, 'shippedExperimental': method in experimental,
               'publicSourceCommit': public['commit']}
        if method in pub and method in stable:
            left = closure(all_schemas['public'][name], pub[method])
            right = closure(all_schemas['shippedStable'][name], stable[method])
            row.update(publicContractShapeSha256=hashlib.sha256(canonical(left)).hexdigest(),
                       shippedStableContractShapeSha256=hashlib.sha256(canonical(right)).hexdigest(),
                       shapeEqual=left == right)
            if left != right:
                row['fieldDifferences'] = differences(left, right)
                row['changedDefinitions'] = sorted(k for k in set(left['definitions']) | set(right['definitions'])
                                                    if left['definitions'].get(k) != right['definitions'].get(k))
        contracts.append(row)
    union_summary[name] = {'publicCheckedIn': len(pub), 'shippedStable': len(stable), 'shippedExperimental': len(experimental),
                           'missingFromPublic': sorted(set(experimental) - set(pub)),
                           'publicOnly': sorted(set(pub) - set(experimental)),
                           'commonStableShapesEqual': sum(1 for r in contracts if r['union'] == name and r.get('shapeEqual') is True),
                           'commonStableShapesDifferent': sum(1 for r in contracts if r['union'] == name and r.get('shapeEqual') is False)}
direct = json.loads((out / 'protocol-coverage.json').read_text())['clientMethods']
direct_comparisons = [r for r in contracts if r['union'] == 'ClientRequest.json' and r['method'] in direct]
common_source = out / 'raw/public-protocol/source/codex-rs/app-server-protocol/src/protocol/common.rs'
text = common_source.read_bytes()
missing = [r['method'] for r in direct_comparisons if not r['publicCheckedIn']]
source_matches = []
for method in missing:
    encoded = method.encode()
    match = re.search(rb'\w+\s*=>\s*"' + re.escape(encoded) + rb'"', text)
    assert match, 'Missing direct candidate also absent from public macro: ' + method
    start = max(0, match.start() - 600)
    end = min(len(text), match.end() + 450)
    preceding = text[start:match.start()]
    source_matches.append({'method': method, 'sourcePath': str(common_source.relative_to(out)),
                           'sourceHash': hashlib.sha256(text).hexdigest(), 'byteStart': start, 'byteEndExclusive': end,
                           'experimentalAttributePrecedesVariant': bool(re.search(rb'#\[experimental\("' + re.escape(encoded) + rb'"\)\](?:\s|///[^\n]*\n)*$', preceding)),
                           'claim': 'Variant is present in fixed public Rust protocol source; public experimental JSON/handler execution not verified'})
summary = {'baselineId': baseline['baselineId'], 'publicTag': public['tag'], 'publicCommit': public['commit'],
           'inputValidation': {'allRecordedPublicDownloadsAndGeneratedSchemasHashVerified': True,
                               'verifiedInputCount': len(verified_inputs), 'shippedCliSha256': generation['cliSha256']},
           'publicSchemaVisibility': 'checked-in default stable export; experimental APIs filtered by export.rs',
           'fileComparisons': file_comparisons, 'unionSummary': union_summary, 'contracts': contracts,
           'directClientCandidates': {'count': len(direct), 'publicCheckedIn': sum(r['publicCheckedIn'] for r in direct_comparisons),
                                      'commonShapesEqual': sum(r.get('shapeEqual') is True for r in direct_comparisons),
                                      'commonShapesDifferent': sum(r.get('shapeEqual') is False for r in direct_comparisons),
                                      'notInPublicStableSchema': missing},
           'publicSourcePresenceForMissingDirectMethods': source_matches,
           'limitations': ['Comparison is schema equality with recursive referenced definitions, not runtime service compatibility.',
                           'shape removes only description/title/$schema/$comment; defaults, enum order, required fields and constraints remain.',
                           'Public experimental parameter/response schemas and implementations were not generated or run.',
                           'Responses are covered by the v2 schema bundle comparison; no per-client callsite parameter compatibility or wrapper identity is established.',
                           'All 52 direct occurrences remain candidates; public method presence does not determine Codex/ChatGPT ownership.']}
(out / 'protocol-compatibility.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'direct': summary['directClientCandidates'], 'fileCount': len(file_comparisons),
                  'equalFileShapes': sum(r['shapeEqualIgnoringDocumentation'] for r in file_comparisons), 'unions': union_summary}, ensure_ascii=False))
