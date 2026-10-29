#!/usr/bin/env python3
"""Merge reviewed candidate versions without changing either frozen evidence pass."""
from pathlib import Path
import json
import hashlib

ROOT = Path(__file__).resolve().parents[2]
V1 = ROOT / '.analysis-local/embedded-dependency-work'
V2 = ROOT / '.analysis-local/embedded-dependency-work-v2'
BASELINE = json.loads((ROOT / '.analysis-local/current-baseline.json').read_text())
EXTRACTED = Path(BASELINE['extractedDirectory'])

def digest(blob):
    return hashlib.sha256(blob).hexdigest()

def load(p):
    return json.loads(p.read_text())

first_path = V1 / 'embedded-dependency-contracts.json'
second_path = V2 / 'embedded-dependency-contracts.json'
repair_path = V2 / 'statsig-recheck.json'
first, second, repair = map(load, [first_path, second_path, repair_path])
hint_input = load(V2 / 'inputs/hint-candidates.json')
assert repair['contract']['id'] == 'bundle-hint-004'
assert repair['contract']['supersedes']['artifactSha256'] == digest(second_path.read_bytes())
assert repair['comparison']['priorArtifactSha256'] == digest(first_path.read_bytes())

evidence_files = [V1 / 'evidence.jsonl', V2 / 'evidence.jsonl', V2 / 'statsig-recheck-evidence.jsonl']
records = [json.loads(line) for p in evidence_files for line in p.read_text().splitlines()]
by_id = {r['id']: r for r in records}
assert len(by_id) == len(records), 'Duplicate evidence IDs'
buffers = {}
for row in records:
    path = EXTRACTED / row['sourcePath'].removeprefix('app.asar/')
    if path not in buffers:
        buffers[path] = path.read_bytes()
    blob = buffers[path]
    loc = row['locator']
    assert 0 <= loc['start'] < loc['endExclusive'] <= len(blob)
    assert digest(blob) == row['sourceHash']
    assert digest(blob[loc['start']:loc['endExclusive']]) == row['spanHash']
    assert row['confidence'] in {'confirmed', 'inferred', 'unresolved'}

second_contracts = {c['id']: c for c in second['contracts']}
second_contracts[repair['contract']['id']] = repair['contract']
candidates = []
for hint in hint_input['hints']:
    if hint['id'] in second_contracts:
        c = second_contracts[hint['id']]
        assert c['investigationStatus'] == 'source-declaration-bound', c
        if c['name'] == 'zod':
            version_ref = c['evidenceRefs'][0]
            version = c['selfReportedCoreVersion']
        elif c['name'] == 'Sentry SDK family':
            version_ref = c['evidenceRefs'][2]
            version = c['selfReportedNamespaceVersion']
        else:
            version_ref = c['versionEvidenceRef']
            version = c['selfReportedSdkVersion']
        refs = c['evidenceRefs']
        source_artifact = repair_path if hint['id'] == 'bundle-hint-004' else second_path
        reason = 'Constructor core version is lexically bound to _zod.version' if c['name'] == 'zod' else 'Registry default and namespaced SDK version key are explicitly bound' if c['name'] == 'Sentry SDK family' else 'Actual metadata provider export is distinguished from export clearing initialization'
        specific_package = None
    else:
        matches = [c for c in first['contracts'] if c['sourcePath'] == hint['sourcePath'] and c['name'] == hint['name']]
        assert len(matches) == 1, (hint, matches)
        c = matches[0]
        version_ref = c['version']['evidenceRef']
        version = c['version'].get('declaredUpstreamVersion') or c['version'].get('declaredCoreVersion') or c['version'].get('declaredSdkVersion')
        refs = [version_ref]
        source_artifact = first_path
        reason = 'Frozen v1 source export/core version declaration; this merge verifies the exact prior hint interval'
        specific_package = None if hint['name'] == 'Statsig SDK family' else hint['name']
    row = by_id[version_ref]
    assert row['sourcePath'] == hint['sourcePath'] and row['sourceHash'] == hint['sourceHash']
    assert row['locator']['start'] < hint['locator']['byteEnd'] and row['locator']['endExclusive'] > hint['locator']['byteStart'], (hint['id'], row)
    assert version == hint['versionHint']
    for ref in refs:
        assert ref in by_id
    candidates.append({
        'id': hint['id'], 'name': hint['name'], 'sourcePath': hint['sourcePath'], 'sourceHash': hint['sourceHash'],
        'priorHintLocator': hint['locator'], 'priorHintEvidenceIds': hint['priorEvidenceIds'],
        'investigationStatus': 'source-declaration-bound', 'reason': reason,
        'sourceSelfReportedVersion': version, 'sourceSelfReportConfidence': 'confirmed',
        'versionEvidenceRef': version_ref, 'evidenceRefs': refs,
        'sourceArtifact': {'path': str(source_artifact), 'sha256': digest(source_artifact.read_bytes()), 'contractId': c['id']},
        'specificPackage': specific_package,
        'actualUpstreamDistributionVersion': None, 'upstreamModificationStatus': 'unknown-no-upstream-comparison',
        'fullLibraryBoundary': 'unresolved', 'mode': 'unknown', 'runtimeVerification': 'unverified',
        'doesNotProve': ['unmodified upstream distribution', 'dependency replacement compatibility', 'runtime activation', 'mode ownership'],
    })
assert len(candidates) == 17 and len({c['id'] for c in candidates}) == 17
merged = {
    'baselineId': BASELINE['baselineId'],
    'scope': {'originalCandidateDenominator': 17, 'v1Candidates': 6, 'v2Candidates': 11, 'sourceDeclarationsBound': 17, 'unresolvedInvestigationBindings': 0, 'actualUpstreamDistributionsVerified': 0, 'runtimeCandidatesVerified': 0},
    'sourceInputs': [{'path': str(p), 'sha256': digest(p.read_bytes()), 'bytes': p.stat().st_size} for p in [first_path, second_path, repair_path, V2 / 'inputs/hint-candidates.json', *evidence_files]],
    'candidates': candidates,
    'preservedInitialFailure': {'id': 'bundle-hint-004', 'artifactPath': str(second_path), 'evidenceId': 'EMBDEP2-E00006', 'reason': 'Statsig provider metadata ambiguous', 'supersededBy': str(repair_path)},
    'statsigMetadataComparison': repair['comparison'],
    'limitations': ['Source self-reports remain distinct from actual upstream distribution/version locks', 'Sentry active global version can retain an existing value; 10.29.0 is a default/namespaced key', 'Zod versions apply only to bound _zod cores', 'SDK metadata equivalence does not establish entire SDK equality', 'Complete library closure, mode and runtime remain unknown'],
}
merged_path = V2 / 'merged-candidate-contracts.json'
merged_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + '\n')
validation = {
    'baselineId': BASELINE['baselineId'], 'allEvidenceRecords': len(records), 'allEvidenceHashAndSpanVerified': len(records),
    'newV2EvidenceRecords': sum(len(p.read_text().splitlines()) for p in evidence_files[1:]),
    'sourceFiles': len(buffers), 'candidateVersionReferences': len(candidates), 'candidateHintIntervalOverlapVerified': len(candidates),
    'missingReferences': [], 'confidenceErrors': [],
    'claimScope': 'Mechanical source/hash/reference and hint-to-declaration checks; not upstream equivalence or runtime proof',
    'artifacts': [{'path': str(p), 'sha256': digest(p.read_bytes()), 'bytes': p.stat().st_size} for p in [first_path, second_path, repair_path, merged_path, *evidence_files]],
    'runnerSources': [{'path': str(p), 'sha256': digest(p.read_bytes())} for p in [ROOT / 'scripts/analysis/embedded_dependency_contracts_v2.cjs', ROOT / 'scripts/analysis/recheck_statsig_metadata.cjs', Path(__file__)]],
}
(V2 / 'validation.json').write_text(json.dumps(validation, ensure_ascii=False, indent=2) + '\n')
summary = [
    '# 内嵌依赖 17 个候选的合并调查状态', '',
    '基线：' + BASELINE['baselineId'] + '。v1 的 6 条和本次其余 11 条均已绑定源码版本声明；17 / 17 的版本证据与原始 hint 范围交叠已逐条验证。实际上游分发确认、运行行为确认均为 0 / 17。', '',
    '| 来源 | 版本自报范围 | 候选数量 |', '| --- | --- | --- |',
    '| React / ReactDOM | 生产工厂 export.version、renderer 身份元数据 19.2.7 | 4 |',
    '| Sentry SDK family | __SENTRY__ 注册表默认值与版本命名空间键 10.29.0 | 3 |',
    '| Statsig SDK family | SDK_VERSION 与 provider 元数据 3.34.0 | 2 |',
    '| Zod | 对应 $ZodType._zod.version 的 core 4.4.3 | 8 |', '',
    'Sentry 注册表保留已有 truthy 全局 version，因此不能据此断言活跃全局版本。renderer 的 key 初始化属于 lazy initializer，调用顺序尚未运行验证。具体 Sentry 子包仍未知。', '',
    'Statsig main 初次调查将导出字段清空和 metadata 对象赋值合计，留下 ambiguous 记录。追加复查仅重新解析先前完整 AST 语句的 103987 字节，明确区分两种赋值。main 与 renderer metadata callback 的 AST 形状一致，比较保留所有标识符及属性名；整体 SDK 与 @oai-statsig 具体子包的等价性仍未知。', '',
    'Zod 8 个候选的版本只约束相应 _zod core；不能覆盖 legacy 接口或整个 chunk。所有实际包来源、修改状态、完整闭包、模式及行为仍待核对。第三方实现未复制进维护源码，冻结 v1 未更改。', '',
    '后续发布应使用 merged-candidate-contracts.json 作为最终候选调查状态，保留 embedded-dependency-contracts.json 中的初次 ambiguous 结果及 statsig-recheck.json 的修正证据。',
]
(V2 / 'final-summary.md').write_text('\n'.join(summary) + '\n')
print(json.dumps({'scope': merged['scope'], 'newEvidence': validation['newV2EvidenceRecords'], 'allHashAndSpanVerified': len(records), 'metadataCallbackShapeEqual': repair['comparison']['bodyShapeEqual'], 'mergedSha256': digest(merged_path.read_bytes())}, indent=2))
