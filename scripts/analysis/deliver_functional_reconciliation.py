"""Publish reviewed saved metadata and a smaller operation reader."""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASELINE
AUTHOR = ROOT / '.analysis-local/functional-catalog-reconciliation-work'
PEER = ROOT / '.analysis-local/functional-catalog-reconciliation-peer-work'


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


handoff_bytes = (AUTHOR / 'handoff.json').read_bytes()
handoff = json.loads(handoff_bytes)
assert handoff['baselineId'] == BASELINE and not handoff['errors']
peer_bytes = (PEER / 'independent-review.json').read_bytes()
assert pin(peer_bytes) == {'bytes': 115916, 'sha256': 'c081eae23c2d346ee7d09917efd360aad4b5ef1ce435ae0ca0dceee542bbdffa'}
peer = json.loads(peer_bytes)
assert peer['baselineId'] == BASELINE and peer['status'] == 'passed-with-scope-limits'
assert peer['errors'] == [] and peer['checkCount'] == 15912
assert peer['reviewedProducts'] == handoff['coreFiles']
assert len(handoff['coreFiles']) == 7

payloads = {}
copies = []


def copy(source, destination, expected):
    source = Path(source)
    assert source.is_file() and not source.is_symlink()
    raw = source.read_bytes()
    assert pin(raw) == {key: expected[key] for key in ['bytes', 'sha256']}
    assert source.stat().st_mode & 0o222 == 0
    assert destination not in payloads
    payloads[destination] = raw
    copies.append({'original': str(source), 'outputPath': destination, **pin(raw)})


for item in handoff['coreFiles']:
    source = Path(item['path'])
    assert source.parent == AUTHOR
    copy(source, 'raw/functional-catalog-reconciliation/author/' + source.name, item)
copy(AUTHOR / 'handoff.json', 'raw/functional-catalog-reconciliation/author/handoff.json', pin(handoff_bytes))
peer_products = [
    ('independent-review.json', 115916, 'c081eae23c2d346ee7d09917efd360aad4b5ef1ce435ae0ca0dceee542bbdffa'),
    ('independent-review.md', 2991, '6252bdcf80a498d3557bbbb37f5c3061153959e7469ace15ed5811f79d4dcbb5'),
    ('attempts/review-04/receipt.json', 2432, 'b2c7735119fd1a504ad5a5cbf73f1b9ccf478aed8b545e0b32757832fdead38b'),
]
for name, size, digest in peer_products:
    destination = 'raw/functional-catalog-reconciliation/independent-review/' + Path(name).name
    copy(PEER / name, destination, {'bytes': size, 'sha256': digest})

original_name = 'raw/functional-catalog-reconciliation/author/functional-catalog-reconciliation.json'
original = json.loads(payloads[original_name])
assert pin(payloads[original_name]) == {'bytes': 12922000, 'sha256': '0de6e794a002ae573cafa1259d95d8960aad30e29ccb8da1faf8621e5f29e230'}
counts = original['counts']
assert len(original['operationCandidates']) == counts['recoverableOperationCandidates'] == 71
assert len(original['typedRelations']) == counts['typedMetadataOrSourceContractRelationEdges'] == 311
assert sum(row['confidence'] == 'confirmed' for row in original['typedRelations']) == 282
assert sum(row['confidence'] == 'inferred' for row in original['typedRelations']) == 29
assert counts['newEntryFeatureAssignments'] == counts['newModeAssignments'] == counts['runtimeObservations'] == 0
assert counts['completeFunctionalDenominator'] == 'unknown'
receipt = json.loads(payloads['raw/functional-catalog-reconciliation/independent-review/receipt.json'])
assert receipt['exitCode'] == 0
assert any(row['sha256'] == pin(peer_bytes)['sha256'] for row in receipt['productsAtExit'])

# Preserve these arrays exactly; the broad registry remains in the raw author product.
retained = ['counts', 'countDefinitions', 'identityPolicy', 'operationCandidates', 'typedRelations',
            'fileCandidateRelations', 'duplicateRepresentationGroups', 'unassignedBoundaryExamples',
            'nextSubstantiveActions', 'peerFindingRevision', 'sourceEvidenceLimit']
reader = {'schemaVersion': 'functional-operation-reader/1', 'baselineId': BASELINE,
          'status': original['status'], 'original': {'path': original_name, **pin(payloads[original_name])},
          'independentReview': {'path': 'raw/functional-catalog-reconciliation/independent-review/independent-review.json', **pin(peer_bytes)},
          'scope': original['scope'],
          'readerOmission': '2384-node candidate registry and repeated source facets remain in the exact raw original; no operation or relation array omitted.'}
reader.update({key: original[key] for key in retained})
payloads['functional-operation-reconciliation.json'] = encode(reader)

labels = {'ttc': '会话与任务协议', 'composer': '提交入口', 'notification-state': '通知与状态',
          'approval': '审批入口', 'cua': '电脑使用服务', 'project-condition': '项目条件',
          'general': 'General 设置／展示', 'agent': 'Agent 配置'}
rows = '\n'.join('| ' + labels[key] + ' | ' + str(value) + ' |'
                 for key, value in counts['operationCandidatesByNamespace'].items())
summary = f'''# 功能操作与来源关联

固定基线 `{BASELINE}`。本次将已有清单接成 **71 个操作候选**，保留参数、条件、状态、外部边界及未执行场景。它们来自已保存的有限合同，完整功能分母仍未知，模式和运行结果未增加确认。

| 来源范围 | 操作候选 |
| --- | ---: |
{rows}

[操作读者 JSON](functional-operation-reconciliation.json)完整保留71项操作、311条关联和下一步动作；原2384节点登记表与全部原始字段在[冻结作者原件]({original_name})。操作读者省去重复登记表，未删操作或关联。38张设置卡与旧 pending namespace 是同一批操作的不同表示，不重复增加功能数量。

311条关联中，282条有明确的保存来源，29条是作者人工选择的 composer 支持关系，标为 inferred。结构包含、绑定或文件候选关联不证明操作等价、运行可达或可合并功能。723个来源facets包含旧元数据记录，也不是新增功能数量。

[独立审查](raw/functional-catalog-reconciliation/independent-review/independent-review.md)针对保存元数据和声明的静态来源关联，实际15912项检查、0错误；29条关系曾误写confirmed，已修订并保留历史。作者21613项与独立审查分别统计。该审查未重读原JS、未执行目标，也没有新增General原源码的独立语义审查。[作者原摘要](raw/functional-catalog-reconciliation/author/summary.md)保留其原路径和限定范围。

后续优先补实际receiver、逐操作持久化／恢复、模式条件和来源消费者。完整Codex范围、ChatGPT专属排除和原生／后台替代方案仍需证据；本次没有修改36个功能组、968项旧入口或337项deferred候选。
'''
payloads['functional-operation-reconciliation-summary.md'] = summary.encode()
provenance = {'schemaVersion': 1, 'baselineId': BASELINE,
              'kind': 'saved-metadata-delivery-and-derived-operation-reader',
              'exactCopies': copies,
              'derived': [{'path': key, **pin(payloads[key])} for key in ['functional-operation-reconciliation.json', 'functional-operation-reconciliation-summary.md']],
              'preservedArrays': retained, 'authorChecks': 21613, 'independentChecks': 15912,
              'counts': counts, 'formalMetadataInputs': 11,
              'globalRecordsAdded': 0, 'runtimeRunsAdded': 0, 'additionalModelTasks': 0,
              'originalSourceReadOrExecuted': False, 'wholeAstRead': False,
              'reportStateOrGlobalModified': False, 'fullAnalysisCompleted': False}
payloads['functional-operation-reconciliation-provenance.json'] = encode(provenance)

# Preflight every path before any publication mutation.
for relative, raw in payloads.items():
    target = OUT / relative
    assert target.resolve().is_relative_to(OUT.resolve()) and not target.is_symlink()
    parent = target.parent
    while not parent.exists():
        parent = parent.parent
    assert parent.is_dir() and os.access(parent, os.W_OK)
    assert not target.exists() or (target.is_file() and target.read_bytes() == raw)
for relative, raw in payloads.items():
    target = OUT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_bytes(raw)
    target.chmod(0o444)
    assert target.read_bytes() == raw
for key in retained:
    assert json.loads((OUT / 'functional-operation-reconciliation.json').read_bytes())[key] == original[key]
print(json.dumps({'status': 'delivered', 'outputs': len(payloads), 'exactCopies': len(copies),
                  'operationCandidates': 71, 'confirmedRelations': 282, 'inferredRelations': 29,
                  'reader': pin(payloads['functional-operation-reconciliation.json']),
                  'globalRecordsAdded': 0, 'runtimeRunsAdded': 0, 'fullAnalysisCompleted': False}))
