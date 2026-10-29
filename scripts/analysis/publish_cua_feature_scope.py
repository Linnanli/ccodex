"""Publish a versioned finite scope without invalidating historical consumer pins."""
import datetime
import hashlib
import json
from pathlib import Path
from contract_reader_context import PROFILES, build_context

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
W = ROOT / '.analysis-local/cua-feature-scope-work'
A = W / 'author-01'
PREFIX = 'raw/cua-feature-scope/'


def read(path):
    return json.loads(path.read_bytes())


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


r = read(A / 'cua-feature-scope.json')
current = read(A / 'feature-scope-v2.json')
verification = read(W / 'verification-01.json')
assert verification['status'] == 'passed' and verification['uniqueSourceSpansChecked'] == 373
assert verification['metadataPointerOccurrencesChecked'] == 521
assert len(r['newFeatures']) == 7 and len(r['operationDecisions']) == 14
assert len(current['features']) == 44 and len(current['operationReviewQueue']) == 12
stages = ['analyze-01', 'verify-author-01']
for stage in stages:
    receipt = read(W / 'attempts' / stage / 'receipt.json')
    assert receipt['exitCode'] == 0 and receipt['sourcesUnchanged']
readers = ['report.md', 'analysis-state.json', 'implementation-plan.md', 'gaps.md', 'behavior-checks.md']
before = {name: (OUT / name).read_bytes() for name in readers}
old = json.loads(before['analysis-state.json'])
assert len(old) == 99 and 'cuaFeatureScope' not in old and 'featureScopeCurrentView' not in old
assert not old['fullAnalysisCompleted'] and old['latestBehaviorAuthorizationState']['groupRemaining'] == 0
previous, _, _ = build_context(OUT, BASE)
assert len(previous) == 33 and all(old[k] == v for k, v in previous.items())
for item in r['inputPins']:
    assert pin((OUT / item['path']).read_bytes()) == {k: item[k] for k in ['bytes', 'sha256']}
planned, copies = {}, []


def copy(relative, path, kind='analysis_metadata'):
    raw = path.read_bytes()
    target = PREFIX + relative
    assert target not in planned
    planned[target] = raw
    copies.append({'original': str(path), 'outputPath': target, **pin(raw), 'kind': kind})


names = ['cua-feature-scope.json', 'cua-feature-scope-scenarios.json',
         'cua-feature-scope-summary.md', 'cua-feature-scope-evidence.jsonl',
         'feature-scope-v2.json', 'feature-scope-v2.csv', 'feature-scope-v2-scenarios.json']
for name in names:
    copy('author/' + name, A / name)
    planned[name] = (A / name).read_bytes()
copy('author/verification-01.json', W / 'verification-01.json')
for stage in stages:
    for path in sorted((W / 'attempts' / stage).iterdir()):
        copy('attempts/' + stage + '/' + path.name, path,
             'analysis_tool_source' if path.suffix == '.py' else 'execution_metadata')
index = {'schemaVersion': 1, 'baselineId': BASE, 'kind': 'consumer-qualified-goals-and-versioned-finite-scope',
  'publishedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'exactCopies': copies, 'derived': [{'path': name, **pin(planned[name])} for name in names],
  **r['constraints'], 'scopedFeatureDefinitions': 44, 'assignedUserOperations': 48,
  'mechanismSupportOperations': 11, 'queuedOperations': 12,
  'knownOperationCandidatesAccountedFor': 71, 'currentUnexecutedScenarioSpecifications': 192,
  'newInferenceRecords': 21, 'newReaRuns': 0, 'newOriginalProgramParses': 0,
  **{k: verification[k] for k in ['sourceFilesByteChecked', 'uniqueSourceSpansChecked',
      'sourceCoordinateOccurrencesChecked', 'inheritedSourceUnitsChecked',
      'metadataPointerOccurrencesChecked', 'uniqueMetadataPointersChecked', 'inputPinsChecked']}}
planned['cua-feature-scope-provenance.json'] = encode(index)
for name in planned:
    assert not (OUT / name).exists(), name
for name, raw in planned.items():
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    path.chmod(0o444)
patch, _, artifacts = build_context(OUT, BASE)
assert len(patch) == len(PROFILES) == 34
assert all(old[k] == v for k, v in patch.items() if k != 'cuaFeatureScope')
view = {'baselineId': BASE, 'snapshotVersion': 2, 'scope': 'Current finite reviewed feature view; full denominator unknown.',
        'ledger': {'path': 'feature-scope-v2.json', **pin(planned['feature-scope-v2.json'])},
        'csv': {'path': 'feature-scope-v2.csv', **pin(planned['feature-scope-v2.csv'])},
        'scenarios': {'path': 'feature-scope-v2-scenarios.json', **pin(planned['feature-scope-v2-scenarios.json'])},
        'reconciliationProfile': 'cuaFeatureScope', 'previousLedger': r['inputPins'][0],
        'counts': current['counts'], 'fullAnalysisCompleted': False}
state = {**old, 'cuaFeatureScope': patch['cuaFeatureScope'], 'featureScopeCurrentView': view}
assert len(state) == 101 and all(state[k] == v for k, v in old.items())
note = next(p[4] for p in PROFILES if p[0] == 'cuaFeatureScope')


def after_title(raw, addition):
    first, rest = raw.decode().split('\n', 1)
    return (first + '\n\n' + addition + '\n' + rest).encode()


changes = {'analysis-state.json': encode(state)}
changes['report.md'] = after_title(before['report.md'], note + '\n\n当前有限功能读者以v2为准；下文及历史合同中的37功能／26队列／160规格属于先前快照。原v1文件、合同与哈希保持不变；完整产品分母与阶段总体完成均未确认。')
changes['implementation-plan.md'] = after_title(before['implementation-plan.md'],
 '[当前功能与恢复门槛增量](cua-feature-scope-summary.md)将电脑使用设置归为FSC-0038至0044。恢复顺序、前置和证据见[cua-feature-scope.json](cua-feature-scope.json)的recoveryStages：声明服务／依赖边界→能力路由与query策略→七组控件→真实provider／receiver及重开验收。当前44功能、48用户操作／11机制／12队列，192规格未执行；此为分析实施依据，不是客户端实现完成。')
changes['gaps.md'] = after_title(before['gaps.md'],
 '[CUA消费者粒度缺口已归并](cua-feature-scope-summary.md)：14候选完成有限用户目标／机制归属，形成7新功能，队列26→12。当前视图见[44项v2清单](feature-scope-v2.json)。尚余两设置facet、一WSL多动作卡、四thread操作、四通知／状态facet和一项目能力父动作；44模式unknown、排除0、967入口未映射、337 deferred及真实运行／持久化缺口仍保留。历史段落的缺口数量按各自快照解释。')
changes['behavior-checks.md'] = after_title(before['behavior-checks.md'],
 '[当前192条未执行功能规格](feature-scope-v2-scenarios.json)保留原160条并加入[32条CUA验收](cua-feature-scope-scenarios.json)。8写操作分别有success／failure／cancel／restore，20条旧CUA控件规格继续作为来源参考而不重复累加。没有新UI／系统设置动作或模型提交；本批metadata／源码范围核对不能算行为执行。')
readme_before = (ROOT / 'README.md').read_bytes()
readme = after_title(readme_before, '- [当前44项有限功能、12项待审操作与192条验收规格](analysis/' + BASE + '/cua-feature-scope-summary.md)\n\n当前功能读者使用版本化v2快照，旧功能文件保留为历史证据。')
snapshots = {PREFIX + 'reader-before/' + name: raw for name, raw in before.items()}
snapshots[PREFIX + 'reader-before/README.md'] = readme_before
for name, raw in snapshots.items():
    path = OUT / name
    assert not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    path.chmod(0o444)
for name, raw in changes.items():
    path = OUT / name
    assert path.read_bytes() == before[name]
    temp = path.with_name('.cua-feature-scope-' + path.name)
    assert not temp.exists()
    temp.write_bytes(raw)
    temp.chmod(path.stat().st_mode & 0o777)
    temp.replace(path)
assert (ROOT / 'README.md').read_bytes() == readme_before
temp = ROOT / '.cua-feature-scope-README.md'
assert not temp.exists()
temp.write_bytes(readme)
temp.chmod((ROOT / 'README.md').stat().st_mode & 0o777)
temp.replace(ROOT / 'README.md')
print(json.dumps({'status': 'published-and-integrated', 'companionIndices': len(patch),
   'oldStateKeysPreserved': len(old), 'newStateKeys': 2, 'currentStateKeys': len(state),
   'selectedArtifactsBeforeOwnCapture': len(artifacts),
   'snapshots': [{'path': name, **pin(raw)} for name, raw in snapshots.items()],
   'outputs': {name: pin(raw) for name, raw in changes.items()},
   'modelSubmissionsAdded': 0, 'fullAnalysisCompleted': False}))
