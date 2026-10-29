"""Publish scoped feature/operation/scenario associations without promoting global coverage."""
import datetime
import hashlib
import json
from pathlib import Path
from contract_reader_context import PROFILES, build_context

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASELINE
WORK = ROOT / '.analysis-local/feature-scope-work'


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


source = json.loads((WORK / 'analysis-01/feature-scope-ledger.json').read_bytes())
scenarios = json.loads((WORK / 'analysis-01/feature-scope-scenarios.json').read_bytes())
assert len(source['features']) == 34 and len(source['operationReviewQueue']) == 36
assert len(scenarios['scenarios']) == 140 and scenarios['executed'] == 0
assert source['counts']['operationsAssigned'] == 35 and source['counts']['completeFeatureDenominator'] is None
assert source['sourceByteVerification']['uniqueSpanCount'] == 169
assert source['sourceByteVerification']['metadataPointerCount'] == 88
for stage in ['analyze-01', 'verify-author-01']:
    receipt = json.loads((WORK / 'attempts' / stage / 'receipt.json').read_bytes())
    assert receipt['exitCode'] == 0 and receipt['sourcesUnchanged']

planned, copies = {}, []


def copy(relative, path, kind='metadata_only'):
    raw = path.read_bytes()
    destination = 'raw/feature-scope-ledger/' + relative
    assert destination not in planned
    planned[destination] = raw
    copies.append({'original': str(path), 'outputPath': destination, **pin(raw), 'kind': kind})


for name in ['feature-scope-ledger.json', 'feature-scope-scenarios.json', 'feature-scope-ledger.csv']:
    copy('author/' + name, WORK / 'analysis-01' / name)
    planned[name] = (WORK / 'analysis-01' / name).read_bytes()
for stage in ['analyze-01', 'verify-author-01']:
    for path in sorted((WORK / 'attempts' / stage).iterdir()):
        copy('attempts/' + stage + '/' + path.name, path,
             'analysis_tool_source' if path.suffix in {'.py', '.mjs'} else 'execution_metadata')

evidence = []
for i, decision in enumerate(source['granularityDecisions']):
    feature = source['features'][i]
    primary = feature['operationMembers'][0]['cardRef']
    evidence.append({'id': 'FEATURE-SCOPE-' + str(i+1).zfill(4), 'baselineId': BASELINE,
        'claim': 'Define ' + feature['featureId'] + ': ' + feature['name'] + '. ' + decision['rationale'],
        'sourcePath': primary['path'], 'sourceHash': primary['sha256'],
        'locator': {'kind': 'json-pointer', 'pointer': primary['jsonPointer']},
        'method': 'inference', 'confidence': 'inferred',
        'verificationStatus': 'author-granularity-review; saved-source-locators-byte-checked; no-new-runtime',
        'decisionId': decision['decisionId'], 'featureId': feature['featureId'],
        'basis': decision['basis'], 'operationEquivalenceClaimed': False,
        'modeClassificationClaimed': False, 'newGlobalEvidenceRecord': False})
planned['feature-scope-evidence.jsonl'] = ('\n'.join(json.dumps(e, ensure_ascii=False) for e in evidence) + '\n').encode()
table = '\n'.join('| ' + f['featureId'] + ' | ' + f['name'] + ' | ' + '、'.join(m['originalContractId'] for m in f['operationMembers']) + ' |' for f in source['features'])
summary = '''# 细粒度功能、操作与验收映射

本批从已保存的38张General／Agent操作卡中，形成34个有固定编号的功能定义，关联35个操作及140条未执行验收规格。这是作者对有限源码契约的功能粒度审阅；模式归属全部unknown，完整功能分母仍未建立。见[功能清单JSON](feature-scope-ledger.json)、[可筛选CSV](feature-scope-ledger.csv)、[验收规格](feature-scope-scenarios.json)、[34条推断依据](feature-scope-evidence.jsonl)与[来源索引](feature-scope-ledger-provenance.json)。没有增加桌面运行或模型提交。

功能粒度采用“一个可独立配置的目标偏好或宿主动作及其可观察契约”。无项目任务目录的选择与reset归入FSC-0001，但保留两个操作、各自条件与不同错误提示，不声称两操作等价。共享配置writer中的六个不同键分别定义六个功能；实际沙箱／模型能力、宿主应用和持久化仍是各自待验证的后效，不能由配置行直接认定完成。

三个设置条目暂未分配功能ID：GENERAL-OP-017仅展示Managed更新策略，GENERAL-OP-031仅展示访问摘要／tooltip，作为待关联父功能的信息facet保留；GENERAL-OP-032包含已连接host的Add project及未连接／无host的链接，应按实际消费者拆分。它们没有从产品范围排除。另33个协议、提交、通知、审批、电脑使用服务及项目条件候选继续排队；35已关联＋36队列覆盖原71操作，未遗漏或增算旧的重复表示。

复用已保存的settings route数据流／factory／export／控件合同，把General和Agent控制分别接到同一ROUTE-0152设置容器的两个support实例。关系标为inferred条件容器关联，不是操作等价、实际mount或整个入口已解析。968旧入口中只有1个容器部分关联，967在本清单中尚未映射；该容器的其余设置页面也未完成。36旧功能大组继续作为独立taxonomy历史，337 deferred原样保留，不能把34新定义加到36大组上当作产品总数。

本批实际重核4个冻结Program文件身份、169个唯一已保存字节范围及88个元数据pointer。没有新解析原Program或运行REA，作用域关系仍来自引用的既有REA／AST补充合同；字节复核不构成新的独立语义审查。所有功能均保留完整参数／状态、条件、外部边界、源契约、操作和scenario引用。没有把通用globalState候选后端自动指派给这些设置项，也没有根据Codex／Work／ChatGPT名称传播模式归属。

140条规格逐项引用原success／failure／cancel／restore预期，执行数为0；其中“没有显式取消”或“恢复未知”仍按原限定保留，不算已实现的取消／恢复能力。实际界面是否显示、条件值、provider／receiver、最终后效及耐久恢复需要后续核对。此前两个模型样例不覆盖这些设置功能，未附会为本批运行验证。本批不生成客户端实现、第三方实现或新的执行授权。

| 功能ID | 用户目标 | 来源操作 |
| --- | --- | --- |
''' + table + '''

下一步先审阅剩余33个非设置操作的粒度与实际消费者，将已有任务完成／中断观察关联到精确适用的场景，而非从协议方法名直接生成feature；再补两条信息facet的父功能和WSL多动作拆分。其他入口、flags、动态域和共享依赖继续保留漏项队列。完整范围、模式排除及实现阶段验收仍需继续闭合。
'''
planned['feature-scope-ledger-summary.md'] = summary.encode()
index = {'schemaVersion': 1, 'baselineId': BASELINE,
    'kind': 'scoped-feature-definitions-and-unexecuted-acceptance-specifications',
    'publishedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'exactCopies': copies,
    'derived': [{'path': n, **pin(planned[n])} for n in ['feature-scope-ledger.json', 'feature-scope-ledger.csv',
                'feature-scope-scenarios.json', 'feature-scope-evidence.jsonl', 'feature-scope-ledger-summary.md']],
    'scopedFeatureDefinitions': 34, 'assignedOperations': 35, 'queuedOperations': 36,
    'unexecutedScenarioSpecifications': 140, 'sourceProgramsByteChecked': 4,
    'sourceSpansByteChecked': 169, 'metadataPointersChecked': 88, 'newModeAssignments': 0,
    'newConfirmedExclusions': 0, 'originalClientRunsAdded': 0, 'runtimeObservationsAdded': 0,
    'modelSubmissionsAdded': 0, 'globalRecordsAdded': 0, 'newReaRuns': 0,
    'featureDenominatorEstablished': False, 'thirdPartyImplementationsPublished': False, 'fullAnalysisCompleted': False}
planned['feature-scope-ledger-provenance.json'] = encode(index)
names = ['report.md', 'analysis-state.json', 'implementation-plan.md', 'gaps.md', 'behavior-checks.md']
before = {n: (OUT / n).read_bytes() for n in names}
old = json.loads(before['analysis-state.json'])
assert len(old) == 89 and old['fullAnalysisCompleted'] is False and old['featureDenominatorEstablished'] is False
assert old['latestBehaviorAuthorizationState']['groupRemaining'] == 0 and 'featureScopeLedger' not in old
for name in planned:
    assert not (OUT / name).exists()
for name, raw in planned.items():
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    path.chmod(0o444)
patch, _, artifacts = build_context(OUT, BASELINE)
assert len(patch) == len(PROFILES) == 24
assert all(old[k] == v for k, v in patch.items() if k != 'featureScopeLedger')
state = {**old, 'featureScopeLedger': patch['featureScopeLedger']}
assert all(state[k] == v for k, v in old.items())
note = next(p[4] for p in PROFILES if p[0] == 'featureScopeLedger')
marker = '[完成标准审计](criteria-audit.md)'
report = before['report.md'].decode()
assert report.count(marker) == 1
changes = {'report.md': report.replace(marker, note + '\n\n' + marker).encode(), 'analysis-state.json': encode(state)}
extras = {
 'implementation-plan.md': '\n\n[34个细粒度功能定义](feature-scope-ledger-summary.md)提供FSC-0001至FSC-0034固定baseline-local身份、35个操作与140条未执行验收规格。后续恢复用feature→operation→source/conditions→scenario追踪，不能用页面或共享writer代替功能等价；配置值与下游有效能力分别验收。两条信息facet、一张WSL多动作卡和33个非设置候选有显式队列。34模式仍unknown，先保留后核对调用方／依赖，不能据此开始ChatGPT剥离或宣布完整目录／功能范围。\n',
 'gaps.md': '\n\n[细粒度功能账本](feature-scope-ledger-summary.md)补34个编号定义／35操作及140条待执行规格，原71操作全部有分配或队列。仍有36操作待粒度／父功能／拆分审阅，968旧入口仅ROUTE-0152部分容器映射，其余967未映射；此计数不包含337 deferred的消解。4个Program／169范围／88 metadata pointer复核不关闭真实条件、provider、服务后效、模式或完整动态入口范围。旧36大组与新34定义属于不同粒度，不可相加；完整分母、模式排除0及模型预算0保持。\n',
 'behavior-checks.md': '\n\n[功能验收规格](feature-scope-scenarios.json)为34个功能的35操作逐项关联success/failure/cancel/restore，共140规格、执行0。每条保留精确源条件、触发、参数状态与原预期限度；无显式取消或持久化未知的场景未升级为可用能力。已有模型样例未验证这些设置项，本批没有桌面偏好变更或新增模型任务。后续按FSC ID和source条件选择获授权行为观察。\n',
}
for name, extra in extras.items():
    changes[name] = before[name] + extra.encode()
readme_before = (ROOT / 'README.md').read_bytes()
readme = readme_before + ('\n- [34个细粒度功能、操作映射与待执行验收规格](analysis/' + BASELINE + '/feature-scope-ledger-summary.md)\n').encode()
snapshots = {'raw/feature-scope-ledger/reader-before/' + n: raw for n, raw in before.items()}
snapshots['raw/feature-scope-ledger/reader-before/README.md'] = readme_before
for name, raw in snapshots.items():
    path = OUT / name
    assert not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    path.chmod(0o444)
for name, raw in changes.items():
    path = OUT / name
    assert path.read_bytes() == before[name]
    temp = path.with_name('.feature-scope-ledger-' + path.name)
    assert not temp.exists()
    temp.write_bytes(raw)
    temp.chmod(path.stat().st_mode & 0o777)
    temp.replace(path)
assert (ROOT / 'README.md').read_bytes() == readme_before
temp = ROOT / '.feature-scope-ledger-README.md'
assert not temp.exists()
temp.write_bytes(readme)
temp.chmod((ROOT / 'README.md').stat().st_mode & 0o777)
temp.replace(ROOT / 'README.md')
print(json.dumps({'status': 'published-and-integrated', 'companionIndices': len(patch),
    'oldStateKeysPreserved': len(old), 'oldStateValuesPreserved': True,
    'scopedFeatureDefinitions': 34, 'unexecutedScenarioSpecifications': 140,
    'selectedArtifactsBeforeOwnCapture': len(artifacts),
    'snapshots': [{'path': n, **pin(raw)} for n, raw in snapshots.items()],
    'outputs': {n: pin(raw) for n, raw in changes.items()},
    'modelSubmissionsAdded': 0, 'fullAnalysisCompleted': False}))
