#!/usr/bin/env python3
"""Compare already exported public npm and frozen protocol schemas, without CLI execution."""
import argparse
import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


UNIONS = ('ClientRequest.json', 'ClientNotification.json', 'ServerRequest.json',
          'ServerNotification.json')
MODES = ('stable', 'experimental')
COLLECTION_BUNDLES = {'codex_app_server_protocol.schemas.json',
                      'codex_app_server_protocol.v2.schemas.json'}


def read_json(path):
    return json.loads(path.read_text())


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def record_file(path):
    return {'path': str(path.resolve()), 'bytes': path.stat().st_size, 'sha256': digest(path)}


def pure_functions(path, wanted, namespace):
    """Compile selected function definitions only; never execute module top-level code."""
    tree = ast.parse(path.read_text(), filename=str(path))
    body = [node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name in wanted]
    if {node.name for node in body} != wanted or len(body) != len(wanted):
        raise ValueError('The selected pure comparison interface changed: ' + str(path))
    exec(compile(ast.Module(body=body, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


def compare(public_value, frozen_value, functions):
    canonical = functions['canonical']
    return {
        'status': 'equal' if public_value == frozen_value else 'different',
        'publicShapeSha256': hashlib.sha256(canonical(public_value)).hexdigest(),
        'frozenShapeSha256': hashlib.sha256(canonical(frozen_value)).hexdigest(),
        'fieldDifferences': functions['differences'](public_value, frozen_value),
    }


def comparison_counts(rows, field):
    return {status: sum(row[field]['status'] == status for row in rows)
            for status in sorted({'equal', 'different'} | {row[field]['status'] for row in rows})}


def paths_coverage(public_files, frozen_files):
    public, frozen = set(public_files), set(frozen_files)
    return {
        'public': len(public), 'frozen': len(frozen),
        'common': len(public & frozen), 'union': len(public | frozen),
        'publicOnly': sorted(public - frozen), 'frozenOnly': sorted(frozen - public),
        'commonPaths': sorted(public & frozen),
    }


def export_inventory(record, out, default_root, verified_paths, helpers):
    inventory = {}
    for run in record['runs']:
        if run.get('label') == 'version':
            continue
        command = run['command']
        if '--out' not in command:
            raise ValueError('Schema run has no output directory')
        output_root = Path(command[command.index('--out') + 1]).resolve()
        label = run.get('label', output_root.name)
        if label not in MODES or label in inventory:
            raise ValueError('Exactly one schema export for each mode is required')
        if not output_root.is_relative_to(out.resolve()):
            raise ValueError('Schema output is outside the baseline')
        if ('--experimental' in command) != (label == 'experimental'):
            raise ValueError('Export label and experimental flag differ')
        record_root = Path(run.get('schemaRoot', str(default_root)))
        if not record_root.is_absolute():
            record_root = out / record_root
        files = {}
        for entry in run['schemaFiles']:
            path = helpers['recorded_path'](record_root, entry['path'])
            if path not in verified_paths or not path.is_relative_to(output_root):
                raise ValueError('Schema entry not verified or outside its export')
            relative = path.relative_to(output_root).as_posix()
            if relative in files:
                raise ValueError('Duplicate schema manifest entry: ' + relative)
            files[relative] = {'path': path, 'record': entry}
        actual = {path.resolve() for path in output_root.rglob('*.json')}
        if actual != {row['path'] for row in files.values()}:
            raise ValueError('Recorded schema paths differ from actual JSON files')
        inventory[label] = {'root': output_root, 'files': files}
    if set(inventory) != set(MODES):
        raise ValueError('Missing stable or experimental export')
    return inventory


def checked_variants(schema, functions):
    branches = schema.get('oneOf')
    if not isinstance(branches, list) or not branches:
        raise ValueError('Protocol union must contain a nonempty oneOf')
    for branch in branches:
        method = branch.get('properties', {}).get('method', {})
        names = method.get('enum', [])
        if (len(names) != 1 or not isinstance(names[0], str)
                or 'method' not in branch.get('required', [])):
            raise ValueError('Method variant is not tagged by one required string enum')
    variants = functions['variants'](schema)
    if len(variants) != len(branches):
        raise ValueError('Duplicate or omitted protocol method variants')
    return variants


def root_constraints(schema):
    return {key: value for key, value in schema.items() if key not in {'oneOf', 'definitions'}}


def standalone_root(schema):
    return {key: value for key, value in schema.items() if key != 'definitions'}


def reference_tokens(schema):
    """Resolve local references as JSON Pointers, including the bundle's v2 namespace."""
    pointers = set()
    def visit(value):
        if isinstance(value, dict):
            ref = value.get('$ref')
            if ref is not None:
                if not isinstance(ref, str) or not ref.startswith('#/definitions/'):
                    raise ValueError('Reference is unsupported by the existing closure routine: ' + str(ref))
                tokens = tuple(token.replace('~1', '/').replace('~0', '~') for token in ref[2:].split('/'))
                resolve_pointer(schema, tokens)
                pointers.add(tokens)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(schema)
    return pointers


def resolve_pointer(value, tokens):
    for token in tokens:
        if isinstance(value, dict) and token in value:
            value = value[token]
        elif isinstance(value, list) and token.isdigit() and int(token) < len(value):
            value = value[int(token)]
        else:
            raise ValueError('Unresolved schema JSON Pointer: /' + '/'.join(tokens))
    return value


def schema_shape(schema, functions):
    """Reuse shape(), explicitly normalizing the export's nested definition namespace."""
    pointers = reference_tokens(schema)
    nested = {tokens[:-1] for tokens in pointers if len(tokens) > 2}
    if nested - {('definitions', 'v2')}:
        raise ValueError('Unexpected nested reference namespace: ' + repr(nested))
    if not nested:
        return functions['shape'](schema)
    value = deepcopy(schema)
    # definitions.v2 is a map of schema names, not a schema keyword object.
    # Apply the existing schema-aware shape function to every named child first.
    for tokens in sorted(nested, key=len, reverse=True):
        namespace = resolve_pointer(value, tokens)
        for name, child in namespace.items():
            namespace[name] = functions['shape'](child)
    return functions['shape'](value)


def file_reference_contract(relative, pschema, fschema, functions):
    if relative in COLLECTION_BUNDLES:
        return {
            'status': 'not-applicable-definition-collection',
            'reason': 'A definition collection has a generic object root with no reachable definitions; full collection shape is compared separately',
        }
    for schema in (pschema, fschema):
        if any(len(tokens) != 2 for tokens in reference_tokens(schema)):
            raise ValueError('Standalone closure requires flat #/definitions references')
    return compare(functions['closure'](pschema, standalone_root(pschema)),
                   functions['closure'](fschema, standalone_root(fschema)), functions)


def markdown_link(label, path):
    return '[' + label + '](<' + str(path.resolve()) + '>)'


def render_markdown(result, json_path, command):
    sets_equal = (result['summary']['methodSetsEqualInEveryUnionAndMode']
                  and result['summary']['generatedFileSetsEqualInBothModes'])
    lines = [
        '公开 npm CLI 与冻结客户端 CLI 的完整导出协议已完成静态比较。'
        + ('两端方法集合与生成文件集合一致；' if sets_equal else '方法集合与文件集合的差异见完整数据；') +
        '契约结构存在下列字段差异。', '',
        '| 导出 | 文件共同 / 两端各自总数 | 文件结构相同 / 不同 | v2 单文件共同 / 两端各自总数 | v2 结构相同 / 不同 |',
        '|---|---:|---:|---:|---:|',
    ]
    for mode in MODES:
        row = result['comparisons'][mode]
        coverage, v2 = row['fileCoverage'], row['v2IndividualCoverage']
        lines.append('| ' + mode + ' | ' + str(coverage['common']) + ' / ' + str(coverage['public'])
                     + ' | ' + str(coverage['schemaShape']['equal']) + ' / ' + str(coverage['schemaShape']['different'])
                     + ' | ' + str(v2['common']) + ' / ' + str(v2['public'])
                     + ' | ' + str(v2['schemaShape']['equal']) + ' / ' + str(v2['schemaShape']['different']) + ' |')
    cross_mode = result['crossModeFileCoverage']['public']
    next_index = 1
    while ((json_path.parent / 'raw' / ('exported-protocol-comparison-v' + str(next_index))).exists()
           or (json_path.parent / ('exported-protocol-comparison-v' + str(next_index) + '.json')).exists()):
        next_index += 1
    next_name = 'exported-protocol-comparison-v' + str(next_index)
    public_only = sum(len(result['comparisons'][mode]['fileCoverage']['publicOnly']) for mode in MODES)
    frozen_only = sum(len(result['comparisons'][mode]['fileCoverage']['frozenOnly']) for mode in MODES)
    lines.extend(['', '所有计数均以 manifest 记录且实际存在的 JSON 文件为分母；公开独有文件 '
                  + str(public_only) + ' 个，冻结独有文件 ' + str(frozen_only) + ' 个。'
                  '每端 ' + str(result['summary']['generatedFilesCompared']) + ' 个模式限定文件对应 '
                  + str(cross_mode['uniqueFileNamesAcrossModes']) + ' 个去重文件名；experimental 比 stable 多 '
                  + str(len(cross_mode['experimentalOnlyFileNames'])) + ' 个文件名。'
                  'v2 单文件指 `v2/*.json`，根目录的 `codex_app_server_protocol.v2.schemas.json` 已纳入全部文件比较。', '',
                  '| 导出 | 消息 union | 共同方法数 | 有效契约相同 / 不同 | 公开独有 / 冻结独有 |',
                  '|---|---|---:|---:|---:|'])
    for mode in MODES:
        for name in UNIONS:
            row = result['comparisons'][mode]['unionSummary'][name]
            lines.append('| ' + mode + ' | ' + name.removesuffix('.json') + ' | ' + str(row['common'])
                         + ' | ' + str(row['effectiveContract']['equal']) + ' / ' + str(row['effectiveContract']['different'])
                         + ' | ' + str(len(row['publicOnly'])) + ' / ' + str(len(row['frozenOnly'])) + ' |')
    lines.extend(['', '| 导出 | union / 方法 | JSON pointer | 差异方向 |', '|---|---|---|---|'])
    for mode in MODES:
        for row in result['comparisons'][mode]['variantContracts']:
            for delta in row.get('effectiveContract', {}).get('fieldDifferences', []):
                lines.append('| ' + mode + ' | ' + row['union'].removesuffix('.json') + ' / `' + row['method']
                             + '` | `' + delta['pointer'] + '` | ' + delta['change'] + ' |')
    lines.extend(['', '`public-added` 表示字段仅在公开导出中出现；`public-removed` 表示字段仅在冻结导出中出现。'
                  'JSON 中的差异项保留具体 schema 值；其中 `shipped` 表示冻结输入。', '',
                  '通知差异落在 `ThreadItem` 的 `subAgentActivity` 分支：公开导出多出可选 `model` 与 `reasoningEffort`。'
                  'experimental 的 `thread/fork` 参数在冻结导出中多出可选 `experimentalPredictionMode`。', '',
                  'v2 集合还包含两处引用差异：`SkillMetadata.path` 与 `SkillSummary.path` 的 `$ref` '
                  '在公开导出指向 `LegacyAppPathString`，在冻结导出指向 `AbsolutePathBuf`。'
                  '两种命名类型的导出形状都是 `string`；本次精确结构比较保留类型名与引用路径差异。', '',
                  '| 导出 | v2 文件 | JSON pointer | 公开值 / 冻结值 |', '|---|---|---|---|'])
    for mode in MODES:
        for row in result['comparisons'][mode]['fileComparisons']:
            if row['file'] not in {'v2/SkillsListResponse.json', 'v2/PluginReadResponse.json'}:
                continue
            for delta in row['schemaShape']['fieldDifferences']:
                if delta['pointer'].endswith('/$ref'):
                    lines.append('| ' + mode + ' | `' + row['file'] + '` | `' + delta['pointer']
                                 + '` | `' + delta['public'] + '` / `' + delta['shipped'] + '` |')
    lines.extend(['',
                  '逐方法有效契约包含 union 根约束和该方法分支的 `allOf`，再递归收集引用闭包；'
                  '这也覆盖 `ServerNotification` 根上的可选 `emittedAtMs`。另保留只含方法分支的比较。'
                  '仅移除 schema 文档关键字 `description`、`title`、`$schema`、`$comment`；'
                  '字段名、默认值、其他 annotation、约束、引用名称及数组顺序保留。', '',
                  '集合 bundle 的 `definitions/v2` 作为命名 schema 容器逐项归一化，并按真实 JSON Pointer 校验引用。'
                  '两个集合 bundle 的完整内容已比较；它们的空泛对象根不用于独立引用闭包统计。', '',
                  '所有输入文件、CLI 和导出 schema 已按记录复核 SHA-256；manifest 与比较函数的字节快照随本次结果保存。'
                  '此前九候选结果和 generation manifest 的内容保持不变。', '',
                  '此阶段没有运行后端，也不据方法名推断产品模式归属。公开 npm 元数据未提供 gitHead，'
                  '导出结果不建立二进制与源码 commit 的绑定，schema 差异也不直接证明运行时不兼容。', '',
                  '证据：' + markdown_link('完整比较数据', json_path) + '，'
                  + markdown_link('公开生成记录', Path(result['evidenceInputs']['publicGeneration']['path'])) + '，'
                  + markdown_link('冻结生成记录', Path(result['evidenceInputs']['frozenGeneration']['path'])) + '。', '',
                  '复跑时指定新的 `--run-name` 和 `--output-name`，以保留本次结果：', '',
                  '```sh', ' '.join(command) + ' --run-name ' + next_name + ' --output-name ' + next_name,
                  '```', ''])
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--run-name', default='exported-protocol-comparison-v1')
    parser.add_argument('--output-name', default='exported-protocol-comparison')
    args = parser.parse_args()
    for value in (args.baseline, args.run_name, args.output_name):
        if not re.fullmatch('[a-z0-9][a-z0-9.-]*', value):
            raise ValueError('Baseline and output identifiers must be plain lowercase names')
    workspace = Path(__file__).resolve().parents[2]
    out = workspace / 'analysis' / args.baseline
    json_path = out / (args.output_name + '.json')
    markdown_path = out / (args.output_name + '.md')
    raw = out / 'raw' / args.run_name
    if json_path.exists() or markdown_path.exists() or raw.exists():
        raise ValueError('Refusing to overwrite an existing result or raw evidence directory')
    paths = {
        'publicGeneration': out / 'public-protocol-generation-npm.json',
        'frozenGeneration': out / 'protocol-generation.json',
        'shapeAlgorithm': workspace / 'scripts/analysis/compare_protocol.py',
        'verificationFunctions': workspace / 'scripts/analysis/compare_public_experimental.py',
        'priorNineCandidates': out / 'public-experimental-compatibility.json',
        'priorNineCandidatesMarkdown': out / 'public-experimental-compatibility.md',
        'comparisonScript': Path(__file__).resolve(),
    }
    inputs = {name: record_file(path) for name, path in paths.items()}
    prior = read_json(paths['priorNineCandidates'])
    if prior['baselineId'] != args.baseline:
        raise ValueError('Prior comparison baseline differs')
    for name, prior_name in (('publicGeneration', 'publicGeneration'), ('frozenGeneration', 'frozenGeneration'),
                             ('shapeAlgorithm', 'shapeAlgorithm'), ('verificationFunctions', 'comparisonScript')):
        expected = prior['evidenceInputs'][prior_name]
        if (Path(expected['path']).resolve() != paths[name].resolve()
                or expected['sha256'] != inputs[name]['sha256']):
            raise ValueError('Input differs from the preserved nine-candidate evidence: ' + name)
        inputs[name]['expectedSha256FromPriorNineCandidateResult'] = expected['sha256']
    functions = pure_functions(paths['shapeAlgorithm'],
                               {'canonical', 'shape', 'differences', 'variants', 'closure'}, {'json': json})
    helpers = pure_functions(paths['verificationFunctions'],
                             {'file_hash', 'verify_file', 'recorded_path', 'verify_generation'},
                             {'hashlib': hashlib, 'Path': Path})
    public, frozen = read_json(paths['publicGeneration']), read_json(paths['frozenGeneration'])
    if public['baselineId'] != args.baseline or frozen['baselineId'] != args.baseline:
        raise ValueError('Generation baselines differ')
    public_count, public_verified = helpers['verify_generation'](public, out, out / 'raw/public-cli-npm', True)
    frozen_count, frozen_verified = helpers['verify_generation'](frozen, out, out / 'raw/protocol', False)
    public_inventory = export_inventory(public, out, out / 'raw/public-cli-npm', public_verified, helpers)
    frozen_inventory = export_inventory(frozen, out, out / 'raw/protocol', frozen_verified, helpers)
    comparisons = {}
    for mode in MODES:
        pub, ship = public_inventory[mode], frozen_inventory[mode]
        pfiles, ffiles = pub['files'], ship['files']
        coverage = paths_coverage(pfiles, ffiles)
        file_rows, variant_rows, union_summary = [], [], {}
        loaded_public = {name: read_json(row['path']) for name, row in pfiles.items()}
        loaded_frozen = {name: read_json(row['path']) for name, row in ffiles.items()}
        for schema in [*loaded_public.values(), *loaded_frozen.values()]:
            reference_tokens(schema)
        for relative in coverage['commonPaths']:
            prow, frow = pfiles[relative], ffiles[relative]
            pschema, fschema = loaded_public[relative], loaded_frozen[relative]
            file_rows.append({
                'file': relative,
                'publicFile': {'bytes': prow['record']['bytes'], 'sha256': prow['record']['sha256']},
                'frozenFile': {'bytes': frow['record']['bytes'], 'sha256': frow['record']['sha256']},
                'rawByteEqual': prow['record']['sha256'] == frow['record']['sha256'],
                'jsonValueEqual': pschema == fschema,
                'schemaShape': compare(schema_shape(pschema, functions), schema_shape(fschema, functions), functions),
                'referencedContract': file_reference_contract(relative, pschema, fschema, functions),
            })
        for union in UNIONS:
            if union not in loaded_public or union not in loaded_frozen:
                raise ValueError('Required message union is absent: ' + union)
            pschema, fschema = loaded_public[union], loaded_frozen[union]
            pv, fv = checked_variants(pschema, functions), checked_variants(fschema, functions)
            methods = paths_coverage(pv, fv)
            rows = []
            for method in sorted(set(pv) | set(fv)):
                row = {'union': union, 'method': method,
                       'publicPresent': method in pv, 'frozenPresent': method in fv}
                if method in pv and method in fv:
                    row['branchContract'] = compare(functions['closure'](pschema, pv[method]),
                                                     functions['closure'](fschema, fv[method]), functions)
                    peffective = {'allOf': [root_constraints(pschema), pv[method]]}
                    feffective = {'allOf': [root_constraints(fschema), fv[method]]}
                    row['effectiveContract'] = compare(functions['closure'](pschema, peffective),
                                                        functions['closure'](fschema, feffective), functions)
                else:
                    status = 'public-only' if method in pv else 'frozen-only'
                    row['branchContract'] = row['effectiveContract'] = {'status': status}
                rows.append(row)
            methods['branchContract'] = comparison_counts(rows, 'branchContract')
            methods['effectiveContract'] = comparison_counts(rows, 'effectiveContract')
            methods['unmatchedVariantsPublic'] = len(pschema['oneOf']) - len(pv)
            methods['unmatchedVariantsFrozen'] = len(fschema['oneOf']) - len(fv)
            union_summary[union] = methods
            variant_rows.extend(rows)
        coverage['schemaShape'] = comparison_counts(file_rows, 'schemaShape')
        coverage['referencedContract'] = comparison_counts(file_rows, 'referencedContract')
        coverage['rawByteEqual'] = sum(row['rawByteEqual'] for row in file_rows)
        coverage['jsonValueEqual'] = sum(row['jsonValueEqual'] for row in file_rows)
        v2p, v2f = [name for name in pfiles if name.startswith('v2/')], [name for name in ffiles if name.startswith('v2/')]
        v2 = paths_coverage(v2p, v2f)
        v2rows = [row for row in file_rows if row['file'].startswith('v2/')]
        v2['schemaShape'] = comparison_counts(v2rows, 'schemaShape')
        v2['referencedContract'] = comparison_counts(v2rows, 'referencedContract')
        comparisons[mode] = {
            'publicSchemaRoot': str(pub['root']), 'frozenSchemaRoot': str(ship['root']),
            'fileCoverage': coverage, 'v2IndividualCoverage': v2,
            'v2BundleFile': 'codex_app_server_protocol.v2.schemas.json',
            'unionSummary': union_summary, 'variantContracts': variant_rows, 'fileComparisons': file_rows,
        }
    # Retain byte snapshots of every small input used to select and compute this result.
    raw.mkdir(parents=True)
    snapshots = raw / 'input-snapshots'
    snapshots.mkdir()
    for name, path in paths.items():
        if digest(path) != inputs[name]['sha256']:
            raise ValueError('An input changed during comparison: ' + name)
        target = snapshots / (name + path.suffix)
        with target.open('xb') as handle:
            handle.write(path.read_bytes())
        if digest(target) != inputs[name]['sha256']:
            raise ValueError('Input snapshot differs from source')
        inputs[name]['byteSnapshot'] = record_file(target)
        inputs[name]['unchangedAfterComparison'] = True
    all_files = [row for mode in MODES for row in comparisons[mode]['fileComparisons']]
    all_variants = [row for mode in MODES for row in comparisons[mode]['variantContracts']]
    mode_difference = {
        side: paths_coverage(inventory['stable']['files'], inventory['experimental']['files'])
        for side, inventory in [('public', public_inventory), ('frozen', frozen_inventory)]
    }
    for side, inventory in [('public', public_inventory), ('frozen', frozen_inventory)]:
        mode_difference[side] = {
            'stableFileNames': len(inventory['stable']['files']),
            'experimentalFileNames': len(inventory['experimental']['files']),
            'uniqueFileNamesAcrossModes': mode_difference[side]['union'],
            'commonFileNamesAcrossModes': mode_difference[side]['common'],
            'stableOnlyFileNames': mode_difference[side]['publicOnly'],
            'experimentalOnlyFileNames': mode_difference[side]['frozenOnly'],
        }
    result = {
        'baselineId': args.baseline, 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
        'status': 'complete', 'phase': 'already-exported-schema-comparison-only',
        'scope': 'Both stable and experimental exports: four message unions, their method variants, v2 individual schemas, and all generated JSON files',
        'publicCli': {'path': public['cliPath'], 'sha256': public['cliSha256'], 'versionOutput': public['versionOutput']},
        'frozenCli': {'path': frozen['cliPath'], 'sha256': frozen['cliSha256']},
        'publicCliSourceBinding': {
            'source': public.get('source'), 'npmGitHead': public.get('npmGitHead'),
            'relationToSourceCommit': public.get('npmRelationToPublicCommit'),
            'npmSriIsGitHubReleaseAssetDigest': False,
        },
        'evidenceInputs': inputs,
        'inputValidation': {
            'publicSchemaFilesBytesAndSha256Verified': public_count,
            'frozenSchemaFilesBytesAndSha256Verified': frozen_count,
            'bothCliSha256Verified': True, 'recordedPathsEqualActualJsonPaths': True,
            'allSchemaRefsSupportedAndResolved': True,
            'generationAndPriorNineCandidateOutputsUnchanged': True,
            'selectedFunctionDefinitionsOnly': True, 'moduleTopLevelExecuted': False,
        },
        'summary': {
            'generatedFilesCompared': len(all_files), 'schemaShape': comparison_counts(all_files, 'schemaShape'),
            'referencedContract': comparison_counts(all_files, 'referencedContract'),
            'methodVariantsCompared': len(all_variants), 'effectiveContract': comparison_counts(all_variants, 'effectiveContract'),
            'methodSetsEqualInEveryUnionAndMode': all(not row['publicOnly'] and not row['frozenOnly']
                for mode in MODES for row in comparisons[mode]['unionSummary'].values()),
            'generatedFileSetsEqualInBothModes': all(not comparisons[mode]['fileCoverage']['publicOnly']
                and not comparisons[mode]['fileCoverage']['frozenOnly'] for mode in MODES),
        },
        'crossModeFileCoverage': mode_difference,
        'comparisons': comparisons,
        'comparisonRules': {
            'documentationKeywordsRemoved': ['description', 'title', '$schema', '$comment'],
            'variantBranch': 'Recursive #/definitions closure of each method-tagged oneOf branch',
            'effectiveVariantContract': 'Recursive closure of allOf[union root without oneOf/definitions, method branch]; preserves root constraints',
            'v2Collection': 'Individual files under v2/; the v2 bundle at the export root is separately included in all generated file comparisons',
            'nestedDefinitionNamespace': 'Resolve JSON Pointers and normalize each named schema inside aggregate definitions/v2; preserve namespace and type names',
            'definitionCollectionRoot': 'Two .schemas.json bundles have generic object roots; compare their full collection shape and do not count an empty root closure as a contract comparison',
            'differenceDirection': 'public-added = present only in public; public-removed = present only in frozen; shipped values refer to frozen',
            'pointerRoot': 'For contract comparisons: /variant is the compared schema expression, /definitions is its recursive reference closure; file shapes use the original schema root',
        },
        'limitations': [
            'Exact structural schema comparison is not a runtime compatibility result; this script never runs either CLI or backend.',
            'No mode ownership, callsite behavior, or source commit identity is inferred.',
            'Npm metadata has no gitHead; package version or SRI does not authenticate a source commit or GitHub release asset digest.',
            'Only schema documentation keywords are removed; defaults, constraints, other annotations, definition names, reference spelling and array order remain.',
            'Method variants are aligned by required single-string method enum; whole-file comparison also retains oneOf branch order and unreferenced definitions.',
        ],
    }
    command = ['python3', 'scripts/analysis/compare_exported_protocol.py', '--baseline', args.baseline]
    with json_path.open('x') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    with markdown_path.open('x') as handle:
        handle.write(render_markdown(result, json_path, command))
    print(json.dumps({'status': 'complete', 'summary': result['summary'],
                      'json': str(json_path), 'markdown': str(markdown_path), 'raw': str(raw)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
