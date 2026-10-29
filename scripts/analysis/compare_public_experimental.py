#!/usr/bin/env python3
"""Compare only the nine missing-stable client candidates to a public CLI export.

This script does not run either CLI or execute compare_protocol.py's top level.
The unavailable branch records unknown contracts after a failed public export.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


def load_json(path):
    return json.loads(path.read_text())


def file_hash(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify_file(path, record):
    data = path.read_bytes()
    if len(data) != record['bytes'] or hashlib.sha256(data).hexdigest() != record['sha256']:
        raise ValueError('Recorded file changed: ' + str(path))


def recorded_path(root, name):
    path = Path(name)
    path = path.resolve() if path.is_absolute() else (root / path).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Schema record is outside schemaRoot: ' + str(path))
    return path


def verify_generation(record, out, default_root, require_complete):
    if require_complete and record.get('status') != 'complete':
        raise ValueError('Public generation status must be complete')
    cli = Path(record['cliPath'])
    if file_hash(cli) != record['cliSha256']:
        raise ValueError('Recorded CLI changed: ' + str(cli))
    count = 0
    verified_paths = set()
    runs = record['runs']
    if not runs:
        raise ValueError('Generation has no successful runs')
    export_labels = set()
    for run in runs:
        if run.get('label') == 'version' and not run.get('schemaFiles'):
            if run['exitCode'] != 0 or record.get('versionOutput') != 'codex-cli 0.162.0':
                raise ValueError('Version run must confirm the exact public 0.162.0 CLI')
            continue
        if run['exitCode'] != 0 or not run.get('schemaFiles'):
            raise ValueError('Generation run did not produce a verified schema export')
        label = run.get('label')
        if label is None and '--out' in run.get('command', []):
            label = Path(run['command'][run['command'].index('--out') + 1]).name
        export_labels.add(label)
        root = Path(run.get('schemaRoot', str(default_root)))
        if not root.is_absolute():
            root = out / root
        for entry in run['schemaFiles']:
            path = recorded_path(root, entry['path'])
            verify_file(path, entry)
            verified_paths.add(path)
            count += 1
    if not {'stable', 'experimental'}.issubset(export_labels):
        raise ValueError('Stable and experimental exports must both be present and hash verified')
    return count, verified_paths


def load_verified_json(path, verified_paths):
    if path.resolve() not in verified_paths:
        raise ValueError('Compared schema is not in the verified generation manifest: ' + str(path))
    return load_json(path)


def shape_functions(path):
    """Load the existing pure functions without executing its write-on-import body."""
    wanted = {'canonical', 'shape', 'differences', 'variants', 'closure'}
    source = path.read_text()
    parsed = ast.parse(source, filename=str(path))
    body = [node for node in parsed.body
            if isinstance(node, ast.FunctionDef) and node.name in wanted]
    if {node.name for node in body} != wanted:
        raise ValueError('Expected comparison functions have changed')
    namespace = {'json': json}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


def compare_values(public_value, shipped_value, functions):
    canonical = functions['canonical']
    delta = functions['differences'](public_value, shipped_value)
    return {
        'status': 'equal' if public_value == shipped_value else 'different',
        'shapeEqual': public_value == shipped_value,
        'publicShapeSha256': hashlib.sha256(canonical(public_value)).hexdigest(),
        'shippedShapeSha256': hashlib.sha256(canonical(shipped_value)).hexdigest(),
        'fieldDifferences': delta,
    }


def root_without_definitions(schema):
    return {key: value for key, value in schema.items() if key != 'definitions'}


def markdown_link(label, path):
    return '[' + label + '](<' + str(path.resolve()) + '>)'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generation-record', default='public-protocol-generation.json',
                        help='Generation manifest filename relative to this baseline, or absolute path')
    parser.add_argument('--record-unavailable', action='store_true',
                        help='Record unknown results when public generation did not complete')
    args = parser.parse_args()
    workspace = Path(__file__).resolve().parents[2]
    current = load_json(workspace / '.analysis-local/current-baseline.json')
    out = workspace / 'analysis' / current['baselineId']
    public_generation_path = Path(args.generation_record)
    if not public_generation_path.is_absolute():
        public_generation_path = out / public_generation_path
    public_generation_path = public_generation_path.resolve()
    public_generation = load_json(public_generation_path)
    frozen_generation_path = out / 'protocol-generation.json'
    frozen_generation = load_json(frozen_generation_path)
    compatibility_path = out / 'protocol-compatibility.json'
    compatibility = load_json(compatibility_path)
    source_record_path = out / 'public-protocol-source.json'
    source_record = load_json(source_record_path)
    for record in (frozen_generation, compatibility, source_record, public_generation):
        if record['baselineId'] != current['baselineId']:
            raise ValueError('Baseline identities differ')
    if args.record_unavailable:
        if public_generation.get('status') == 'complete':
            raise ValueError('A complete public export must use the comparison branch')
    elif public_generation.get('status') != 'complete':
        raise ValueError('Public export unavailable; explicitly use --record-unavailable')

    frozen_count, frozen_verified = verify_generation(frozen_generation, out, out / 'raw/protocol', False)
    public_count = None
    public_verified = set()
    if not args.record_unavailable:
        public_count, public_verified = verify_generation(public_generation, out, out / 'raw/public-cli', True)
    common_relative = 'raw/public-protocol/source/codex-rs/app-server-protocol/src/protocol/common.rs'
    common_path = out / common_relative
    common_record = next(row for row in source_record['downloads'] if row['path'] == common_relative)
    verify_file(common_path, common_record)
    common_source = common_path.read_text()
    methods = compatibility['directClientCandidates']['notInPublicStableSchema']
    expected_methods = {
        'project/delete', 'project/list', 'project/move', 'project/read', 'project/update',
        'remoteControl/enable', 'rollout/compress', 'thread/realtime/stop', 'thread/settings/update',
    }
    if set(methods) != expected_methods or len(methods) != 9:
        raise ValueError('The recorded nine-method candidate scope changed')
    algorithm_path = workspace / 'scripts/analysis/compare_protocol.py'
    functions = shape_functions(algorithm_path)
    shipped_root = out / 'raw/protocol/experimental'
    public_root = None
    shipped_request_path = shipped_root / 'ClientRequest.json'
    shipped_request = load_verified_json(shipped_request_path, frozen_verified)
    shipped_variants = functions['variants'](shipped_request)
    if not args.record_unavailable:
        matches = [path for path in public_verified
                   if path.name == 'ClientRequest.json' and path.parent.name == 'experimental']
        if len(matches) != 1:
            raise ValueError('Manifest must identify exactly one experimental ClientRequest schema')
        public_request_path = matches[0]
        public_root = public_request_path.parent
        public_request = load_verified_json(public_request_path, public_verified)
        public_variants = functions['variants'](public_request)
    rows = []
    for method in methods:
        match = re.search(r'\w+\s*=>\s*"' + re.escape(method) + r'"\s*\{(.*?)\n\s*\}',
                          common_source, re.S)
        if not match:
            raise ValueError('Missing pinned source mapping: ' + method)
        response_match = re.search(r'response:\s*v2::(\w+)', match[1])
        if not response_match:
            raise ValueError('Missing pinned response mapping: ' + method)
        response_type = response_match[1]
        shipped_variant = shipped_variants[method]
        shipped_params = shipped_variant['properties']['params']
        shipped_response_path = shipped_root / 'v2' / (response_type + '.json')
        shipped_response = load_verified_json(shipped_response_path, frozen_verified)
        row = {
            'method': method,
            'responseType': response_type,
            'responseMapping': {'kind': 'pinned-public-Rust-declaration',
                                'path': str(common_path), 'sha256': common_record['sha256'],
                                'sourceByteStart': len(common_source[:match.start()].encode()),
                                'sourceByteEndExclusive': len(common_source[:match.end()].encode()),
                                'claim': 'Response type mapping only; this is not a public generated contract or runtime result'},
            'shippedParamsSchema': shipped_params,
            'shippedParamsRequired': 'params' in shipped_variant.get('required', []),
            'shippedResponseSchema': {'path': str(shipped_response_path), 'sha256': file_hash(shipped_response_path)},
        }
        if args.record_unavailable:
            row['publicExperimentalGenerated'] = False
            row['request'] = {'status': 'unknown', 'reason': 'public-cli-generation-unavailable'}
            row['params'] = {'status': 'unknown', 'reason': 'public-cli-generation-unavailable'}
            row['response'] = {'status': 'unknown', 'reason': 'public-cli-generation-unavailable'}
        elif method not in public_variants:
            row['publicExperimentalGenerated'] = True
            row['publicMethodPresent'] = False
            row['request'] = {'status': 'public-method-absent'}
            row['params'] = {'status': 'unknown', 'reason': 'public-method-absent'}
            row['response'] = {'status': 'unknown', 'reason': 'public-method-absent'}
        else:
            public_variant = public_variants[method]
            public_response_path = public_root / 'v2' / (response_type + '.json')
            public_response = load_verified_json(public_response_path, public_verified)
            row['publicExperimentalGenerated'] = True
            row['publicMethodPresent'] = True
            row['publicParamsSchema'] = public_variant['properties']['params']
            row['publicResponseSchema'] = {'path': str(public_response_path), 'sha256': file_hash(public_response_path)}
            row['request'] = compare_values(functions['closure'](public_request, public_variant),
                                            functions['closure'](shipped_request, shipped_variant), functions)
            row['params'] = compare_values(functions['closure'](public_request, public_variant['properties']['params']),
                                           functions['closure'](shipped_request, shipped_params), functions)
            row['response'] = compare_values(
                functions['closure'](public_response, root_without_definitions(public_response)),
                functions['closure'](shipped_response, root_without_definitions(shipped_response)), functions)
        rows.append(row)
    categories = ('request', 'params', 'response')
    result = {
        'baselineId': current['baselineId'],
        'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
        'status': 'unavailable' if args.record_unavailable else 'complete',
        'phase': 'schema-comparison-only; no-public-app-server-runtime-execution',
        'scope': 'nine direct client method candidates absent from checked-in public stable schema',
        'publicTag': source_record['tag'], 'publicSourceCommit': source_record['commit'],
        'publicSourceFieldsRole': 'Fixed Rust reference for method/response type mapping; not a source binding for the compared native CLI',
        'publicCliSourceBinding': {
            'source': public_generation.get('source', public_generation.get('method')),
            'npmGitHead': public_generation.get('npmGitHead'),
            'relationToReferenceCommit': public_generation.get('npmRelationToPublicCommit',
                'Unknown unless explicitly authenticated by the generation manifest'),
            'npmSriIsGitHubReleaseDigest': False,
        },
        'frozenCli': {'path': frozen_generation['cliPath'], 'sha256': frozen_generation['cliSha256']},
        'publicCli': {'path': public_generation.get('cliPath'), 'sha256': public_generation.get('cliSha256'),
                      'generationStatus': public_generation.get('status')},
        'evidenceInputs': {
            'publicGeneration': {'path': str(public_generation_path), 'sha256': file_hash(public_generation_path)},
            'frozenGeneration': {'path': str(frozen_generation_path), 'sha256': file_hash(frozen_generation_path)},
            'candidateList': {'path': str(compatibility_path), 'sha256': file_hash(compatibility_path)},
            'sourceMapping': {'path': str(common_path), 'sha256': common_record['sha256']},
            'shapeAlgorithm': {'path': str(algorithm_path), 'sha256': file_hash(algorithm_path)},
            'comparisonScript': {'path': str(Path(__file__).resolve()), 'sha256': file_hash(Path(__file__).resolve())},
        },
        'inputValidation': {'frozenSchemaFilesHashVerified': frozen_count,
                            'publicSchemaFilesHashVerified': public_count,
                            'publicSchemasUsed': not args.record_unavailable,
                            'publicExperimentalSchemaRoot': str(public_root) if public_root else None},
        'summary': {category: {status: sum(row[category]['status'] == status for row in rows)
                              for status in sorted({row[category]['status'] for row in rows})}
                    for category in categories},
        'contracts': rows,
        'limitations': [
            'Exact structure equality of recursively collected #/definitions reference closures; no runtime service compatibility is established.',
            'Only description/title/$schema/$comment are removed; other annotations, defaults, constraints and array order remain.',
            'Definition names and $ref spellings remain; semantically equivalent schemas may compare different.',
            'Pinned Rust declarations map response type names; source presence alone does not establish generated public support.',
            'Method candidates do not establish Codex/ChatGPT ownership or per-callsite parameter compatibility.',
            'Public npm package metadata has no gitHead; the compared CLI is not bound to the fixed Rust source commit by version naming or SRI.',
        ],
    }
    if args.record_unavailable:
        result['publicGenerationUnavailableEvidence'] = {
            key: public_generation[key] for key in ('status', 'failures', 'attempts', 'downloads', 'limitations')
            if key in public_generation
        }
        result['limitations'].append('Public CLI download/export did not complete; all 27 comparison results are unknown.')
    json_path = out / 'public-experimental-compatibility.json'
    markdown_path = out / 'public-experimental-compatibility.md'
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    unavailable = args.record_unavailable
    introduction = ('公开 CLI 下载或 schema 导出未完成，9 个候选方法的 request、params、response 共 27 项均为 unknown。'
                    if unavailable else '已比较公开发布 CLI 与冻结客户端 CLI 的 9 个实验候选方法；下表记录三类 schema 闭包的精确结构比较。')
    source_description = ('比较二进制来自官方 npm `@openai/codex@0.162.0-darwin-x64`，SRI 校验通过。'
                          if public_generation.get('method') == 'official-npm-platform-cli-schema-generation'
                          else '比较二进制来源见公开生成记录。')
    md = [introduction, '', source_description, '',
          'Rust 映射参考：`' + source_record['tag'] + '` / `' + source_record['commit'] + '`。'
          'npm 元数据未提供 gitHead，比较二进制与此源码提交的关系为 unknown；npm SRI 也不等同于 GitHub release asset 摘要。', '',
          '冻结 CLI SHA-256：`' + frozen_generation['cliSha256'] + '`。', '',
          '公开 CLI SHA-256：' + ('`' + public_generation['cliSha256'] + '`。'
                                    if public_generation.get('cliSha256') else 'unknown（未得到完整、可验证的二进制）。'), '',
          '| 方法 | Request | Params | Response |', '|---|---|---|---|']
    for row in rows:
        md.append('| ' + row['method'] + ' | ' + ' | '.join(row[k]['status'] for k in categories) + ' |')
    md.extend(['', '比较阶段仅处理 schema；未执行公开 app-server 运行时。去除字段仅限 `description`、`title`、`$schema`、`$comment`；默认值、约束、其他 annotation 与数组顺序保留。', '',
               '固定 Rust 源码仅用于 method → response 类型映射，不能据此认定公开生成协议支持这些方法。', '',
               '证据：' + markdown_link('公开生成记录', public_generation_path) + '，' +
               markdown_link('冻结生成记录', frozen_generation_path) + '，' +
               markdown_link('完整比较数据', json_path) + '。', '',
               '复跑：`python3 scripts/analysis/compare_public_experimental.py' +
               (' --generation-record ' + str(public_generation_path)
                if args.generation_record != 'public-protocol-generation.json' else '') +
               (' --record-unavailable' if unavailable else '') + '`。', ''])
    markdown_path.write_text('\n'.join(md))
    print(json.dumps({'status': result['status'], 'methods': len(rows), 'summary': result['summary'],
                      'json': str(json_path), 'markdown': str(markdown_path)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
