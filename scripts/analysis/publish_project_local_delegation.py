#!/usr/bin/env python3
"""Publish the bounded FSC-0105 delegate decision from frozen-source evidence."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/project-delegation-work'
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'
RAW = OUT / 'raw/project-local-delegation-v1'
PINS = {}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pin(p):
    b = p.read_bytes()
    value = {'path': str(p.relative_to(ROOT)), 'bytes': len(b), 'sha256': sha(b)}
    PINS[value['path']] = value
    return value


def load(p):
    pin(p)
    return json.loads(p.read_text())


def ref(p, pointer):
    value = load(p)
    for token in pointer.lstrip('/').split('/') if pointer else []:
        value = value[int(token)] if isinstance(value, list) else value[token]
    return {**pin(p), 'jsonPointer': pointer}


def write(p, b):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write(b)
    p.chmod(0o444)
    return pin(p)


state_path = OUT / 'analysis-state.json'
before = state_path.read_bytes()
state = json.loads(before)
assert state['fullAnalysisCompleted'] is False
assert state['latestBehaviorAuthorizationState']['groupRemaining'] == 0
assert state['stageDecisions']['nextAction']['issueId'] == 'SD-01'
with (WORK / 'state-before-publication.json').open('xb') as f:
    f.write(before)

initial_path = WORK / 'initial-v1/source-contracts.json'
main_path = WORK / 'main-v1/source-contracts.json'
initial, main = load(initial_path), load(main_path)
local_path = OUT / 'raw/restoration-plan-v7/local-content-01/source-contracts.json'
local = load(local_path)
paths_path = OUT / 'project-path-controls.json'
paths = load(paths_path)
host_path = OUT / 'host-message-contracts.json'
host = load(host_path)
features = load(OUT / 'feature-scope-v26.json')
coverage = load(OUT / 'restoration-coverage-v17.json')
assert features['features'][104]['featureId'] == 'FSC-0105'
assert coverage['taskGroups'][13]['taskId'] == 'T14'
assert len(features['features']) == 373 and len(coverage['taskGroups']) == 48
assert local['calls'][27]['binding']['scopeKind'] == 'Program'
assert {'local': 'Ke', 'imported': 'j$t'} in local['imports'][2]['specifiers']
assert next(x for x in initial['exports'] if x['exported'] == 'j$t')['local'] == 'z0r'
assert main['bindingReferences'][0]['binding']['scopeKind'] == 'Program'
assert main['bindingReferences'][0]['binding']['definitions'][0]['declaration'] == main['bindings'][0]['definitions'][0]['declaration']

selected = []


def select(label, item):
    location = {k: item[k] for k in ['sourcePath', 'sourceHash', 'byteRange', 'spanHash', 'nodeType']}
    source = FROZEN / location['sourcePath'].removeprefix('app.asar/')
    b = source.read_bytes()
    assert sha(b) == location['sourceHash']
    start, end = location['byteRange']['start'], location['byteRange']['endExclusive']
    assert 0 <= start < end <= len(b)
    fragment = b[start:end]
    assert sha(fragment) == location['spanHash']
    artifact = write(RAW / (label + '.txt'), fragment)
    selected.append({'id': label, **location, 'artifact': artifact})


select('local-import', local['imports'][2])
select('local-call', local['calls'][27])
for i in range(6):
    select('initial-' + initial['units'][i]['label'], initial['units'][i])
select('lifecycle-flow', initial['bindingReferences'][4]['calleeBinding']['definitions'][0]['declaration'])
for i, label in [(0, 'picker-definition'), (1, 'picker-construction'),
                 (2, 'message-owner-constructor'), (5, 'picker-add-method'),
                 (13, 'create-or-select-method')]:
    select(label, main['units'][i])
case = host['cases'][119]
select('add-root-handler-case', {
    'sourcePath': main['sourcePath'], 'sourceHash': main['sourceHash'],
    'byteRange': {k: case['clauseRange'][k] for k in ['start', 'endExclusive']},
    'spanHash': sha((FROZEN / '.vite/build/main-CqEoQDOU.js').read_bytes()[2101354:2101468]),
    'nodeType': 'SwitchCase',
})
old = paths['evidence'][10]
select('create-local-comparison', {
    'sourcePath': 'app.asar/' + old['sourcePath'], 'sourceHash': old['sourceHash'],
    'byteRange': {'start': old['byteRange']['start'], 'endExclusive': old['byteRange']['end']},
    'spanHash': old['spanHash'], 'nodeType': old['nodeType'],
})

facts = [
    ('PLD-01', 'Ke in the existing FSC-0105 local branch imports j$t; the initial Program exports z0r as j$t.',
     ['local-import', 'local-call', 'initial-esm-export-j$t', 'initial-esm-definition-j$t']),
    ('PLD-02', 'z0r calls tI with projectType local, then emits electron-add-new-workspace-root-option with an empty payload. It has no return/await/catch for registration. tI returns or updates an in-scope flow record and emits a lifecycle step when newly allocated; this is not a project creation result.',
     ['initial-esm-definition-j$t', 'lifecycle-flow']),
    ('PLD-03', 'The matching MMe handler awaits projectFolderPicker.createOrSelectProject(e,t.root). Its constructor creates the Program-bound Mje with host, windowManager and projectsManager. This closes the saved handler receiver definition at the source level, conditional on message delivery to this handler.',
     ['add-root-handler-case', 'picker-construction', 'message-owner-constructor', 'picker-definition']),
    ('PLD-04', 'The local picker chooses/validates a root and calls createOrSelectLocalProjects([root]); cancellation/no result emits workspace-root-option-add-canceled. Success emits workspace-root-option-added with new/existing identity fields, then navigate-to-route /. Awaited errors have no local catch/finally in this method; this does not prove upstream error behavior.',
     ['picker-definition', 'picker-add-method', 'create-or-select-method']),
    ('PLD-05', 'The reviewed picker registration path is distinct from projects.createLocal. The qHe createOrSelectLocalProjects implementation requests roots, selects the first returned project and publishes local-project/order/selection updates. createLocal separately parses appearance/name/sources/initGit/setActive, can allocate a default root and returns projectId/rootPaths. Actual injected manager identity, backend success and durable effects remain unobserved.',
     ['picker-add-method', 'create-or-select-method', 'create-local-comparison']),
    ('PLD-06', 'The sibling k$t export is B0r, which dispatches open-create-remote-project-modal. It is a separate remote entry; neither it nor WSL creation establishes local createLocal equivalence.',
     ['initial-esm-export-k$t', 'initial-esm-definition-k$t']),
]
by_id = {x['id']: x for x in selected}
evidence = []
for fact_id, claim, ids in facts:
    for i, source_id in enumerate(ids):
        x = by_id[source_id]
        evidence.append({'id': f'{fact_id}-E{i+1:02d}', 'baselineId': BASE, 'claim': claim,
                         'sourcePath': x['sourcePath'], 'sourceHash': x['sourceHash'],
                         'locator': {'byteRange': x['byteRange'], 'spanHash': x['spanHash'], 'nodeType': x['nodeType']},
                         'method': 'frozen-full-Program-binding-and-bounded-source-review',
                         'confidence': 'inferred' if fact_id in ['PLD-03', 'PLD-05'] else 'confirmed',
                         'verificationStatus': 'source-qualified; runtime-not-observed'})

result = {
    'schemaVersion': 1, 'baselineId': BASE, 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
    'status': 'bounded-delegate-non-equivalence-established',
    'feature': ref(OUT / 'feature-scope-v26.json', '/features/104'),
    'task': ref(OUT / 'restoration-coverage-v17.json', '/taskGroups/13'),
    'owner': ref(OUT / 'logical-module-ownership-v1.json', '/responsibilityOwners/6'),
    'facts': [{'id': i, 'claim': claim, 'sourceIds': ids} for i, claim, ids in facts],
    'selectedSource': selected,
    'sourceQueries': [pin(initial_path), pin(main_path)],
    'queryQualifications': ['The dialog filename StringLiteral hit at initial byte 15575 is an asset-index array entry, not a proven dynamic import or dialog-opening call. The 95507-byte array was excluded from curated fragments.',
                            'Source query unit filenames describe local extraction outputs. Only selectedSource artifacts are the published curated source set.'],
    'decision': {'ownerId': 'LM-BOUNDARY-STRUCT-RWC-PROJECTS', 'featureId': 'FSC-0105', 'taskId': 'T14',
                 'relationship': 'Maintain a picker/create-or-select entry alongside the existing project domain; do not merge its contract with createLocal.',
                 'proposedAdditionalPath': 'apps/desktop/src/main/projects/project-folder-picker.ts',
                 'pathStatus': 'new-maintenance-design-only', 'completeConsumerJoinProven': False},
    'remaining': ['Actual Ho bridge delivery and selected MMe/manager instance are unobserved.',
                  'Actual filesystem picker/consent, service registration, UI completion, persistence and mode ownership remain unverified.',
                  'The remote modal and other project-add entries retain their own unresolved consumers; no cross-entry feature IDs are merged.'],
    'counts': {'newFullProgramsParsed': 2, 'curatedSourceFragments': len(selected), 'facts': len(facts),
               'currentFeaturesUnchanged': 373, 'currentTasksUnchanged': 48,
               'newFeatures': 0, 'newScenarioSpecifications': 0, 'newProductScenarioPasses': 0,
               'newModelSubmissions': 0, 'newClientRuns': 0, 'newReaRuns': 0, 'newClientImplementation': 0},
    'inputPins': list(PINS.values()), 'fullAnalysisCompleted': False,
}
pin(Path(__file__))
pin(ROOT / 'scripts/analysis/project_delegation_ast.mjs')
pin(WORK / 'initial-query-v1.json')
pin(WORK / 'main-query-v1.json')
result['inputPins'] = list(PINS.values())
result_pin = write(OUT / 'project-local-delegation-v1.json', (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode())
evidence_pin = write(OUT / 'project-local-delegation-v1-evidence.jsonl', ''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in evidence).encode())
summary = '''# 环境页面添加项目的委托决定

FSC-0105/T14 的本地 Ke 确认为 initial 的 j$t/z0r：记录本地创建 flow 后发送 `electron-add-new-workspace-root-option`。匹配的 main handler 经构造器注入的 Mje 文件夹选择器调用 `createOrSelectLocalProjects`。消息实际送达、有效实例与服务效果未实测。

这条选择／登记项目路径与既有 `projects.createLocal` 弹窗合同分开维护。前者选择根目录、允许选中已有项目，并发送取消或成功及导航消息；后者解析名称、来源、外观、Git 初始化和激活参数，可以创建默认根目录，返回项目 ID 与根路径。不能因名称都含“添加项目”合并合同。

维护决定：沿用项目领域 owner，并增加拟议文件 `apps/desktop/src/main/projects/project-folder-picker.ts`；该路径是恢复设计，尚未生成客户端实现。现有功能 ID 和 T14 保持不变，原 createLocal 合同仍需自己的消费者依据。

远程 qe/k$t 单独发送打开远程项目弹窗的消息。initial 的 dialog 文件名命中仅为资源索引，已排除为“打开弹窗”的证据。没有把 WSL 远程创建关联当成本地等价证明。

本批审查两个完整 Program，公布六项有限事实与精确来源片段。373 项功能、48 组任务和未执行场景规格不变；未调用模型、启动客户端或验证真实持久化。完整分析仍未完成。

数据及来源：[决定与来源](project-local-delegation-v1.json)、[证据](project-local-delegation-v1-evidence.jsonl)。
'''
summary_pin = write(OUT / 'project-local-delegation-v1.md', summary.encode())
state['projectLocalDelegation'] = {'result': result_pin, 'summary': summary_pin, 'evidence': evidence_pin,
                                   'counts': result['counts'], 'boundedDelegateQuestionClosed': True,
                                   'completeRuntimeChainProven': False}
state['logicalModuleInventory']['ownershipReview']['projectConsumerRefinement'] = result_pin
state['stageDecisions']['nextAction'] = {
    'issueId': 'SD-01',
    'question': 'Disposition the saved legacy entry roles in bounded groups, separating metadata, handlers and actual retained consumers.',
    'fixedInput': 'Existing legacy-entry-dispositions, entry-family grouping and source-qualified catalogs; reuse prior consumer joins.',
    'closure': 'Each reviewed group receives an evidence-backed role/feature association or a precise unresolved edge. Do not count catalog records as user features.',
    'authorization': 'Frozen-source/saved-artifact analysis; no app/model/service invocation.',
}
state['updatedAtUtc'] = datetime.now(timezone.utc).isoformat()
assert state['fullAnalysisCompleted'] is False
assert state['latestBehaviorAuthorizationState'] == json.loads(before)['latestBehaviorAuthorizationState']
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'result': result_pin, 'summary': summary_pin, 'sourceFragments': len(selected), 'evidenceRows': len(evidence)}, ensure_ascii=False))
