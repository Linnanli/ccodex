"""Publish one delegate contract without changing feature or acceptance denominators."""
from pathlib import Path
import copy
import datetime
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/cloud-environment-editor-contract-work'
RAW = OUT / 'raw/cloud-environment-editor'


def read(path):
    return json.loads(path.read_text())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pin(path):
    data = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(data), 'sha256': digest(data)}


def create(path, value):
    with path.open('x') as file:
        file.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


state_path = OUT / 'analysis-state.json'
state_bytes = state_path.read_bytes()
state = json.loads(state_bytes)
assert state['updatedAtUtc'] == '2026-10-24T13:59:07.776763+00:00', 'Review concurrent updates'
assert not RAW.exists()
selection = read(WORK / 'editor/source-contracts.json')
probe = read(WORK / 'probe-attempt-01.json')
assert probe['counts'] == {'cases': 30, 'passed': 30, 'failed': 0}
assert selection['fullProgramParsed'] and not selection['targetCodeExecuted']
assert probe['sourceContractsSha256'] == digest((WORK / 'editor/source-contracts.json').read_bytes())
assert probe['scriptSha256'] == digest((ROOT / 'scripts/analysis/probe_cloud_environment_editor.cjs').read_bytes())
source = ROOT / '.analysis-local/baselines' / BASE / 'extracted' / selection['sourcePath'][9:]
source_bytes = source.read_bytes()
assert digest(source_bytes) == selection['sourceHash']
for unit in selection['units']:
    span = source_bytes[unit['byteRange']['start']:unit['byteRange']['endExclusive']]
    assert digest(span) == unit['spanHash']
    assert span == (WORK / 'editor' / unit['sourceFilename']).read_bytes()
caller = read(OUT / 'raw/settings-operation-batch-15/cloud-environments/source-contracts.json')
binding = next(item for item in caller['imports'] if item['module'] == './cloud-environment-editor-661e4145e660.js')
assert {'local': 'ht', 'imported': 't'} in binding['specifiers']
assert {'local': 'mt', 'imported': 'n'} in binding['specifiers']
ledger_path = OUT / 'feature-scope-v24.json'
ledger = read(ledger_path)
original_plan = ROOT / 'docs/reverse-engineering/analysis-plan.md'
assert digest(original_plan.read_bytes()) == '48dd8b65348efd4a8b5634aac5341c4507c262e7b5c88e8ed9368c88eeb96db4'
inputs = [pin(path) for path in [original_plan, state_path, ledger_path, OUT / 'restoration-coverage-v15.json', OUT / 'settings-operation-batch-15.json', ROOT / 'scripts/analysis/settings_operations_ast.mjs', ROOT / 'scripts/analysis/probe_cloud_environment_editor.cjs', Path(__file__).resolve(), source, OUT / 'raw/settings-operation-batch-15/cloud-environments/source-contracts.json']]
units = {unit['name']: unit for unit in selection['units']}


def fact(identifier, statement, names, qualification=None):
    result = {'id': identifier, 'statement': statement, 'sourceUnits': [units[name] for name in names]}
    if qualification:
        result['qualification'] = qualification
    return result


facts = [
    fact('CEE-01', 'The saved settings caller imports initializer n as mt and component t as ht. Editor n resolves to Nt; t resolves to wt. wt chooses Tt for nullish environment and Et otherwise.', ['Nt', 'wt', 'Tt']),
    fact('CEE-02', 'Creation selects the initial repository connector first, otherwise the cloud preference connector, otherwise null. Editing supplies preferredConnectorId null.', ['wt', 'Tt'], 'Cloud preference provider values and repository picker behavior remain external.'),
    fact('CEE-03', 'Et initializes form values through Oe(environment, preferredConnectorId, initialRepository, default visibility). The default visibility is workspace when imported plan predicates pass, private otherwise.', ['Et'], 'Oe, pe and ne are imported algorithms; their implementations were not replayed.'),
    fact('CEE-04', 'Local submission requires imported validation _e plus names ready or an unchanged trimmed label. Names ready means data is non-null or an imported API error has status 404.', ['Et'], 'This proves the local gate and arguments, not validation rules or server error identity.'),
    fact('CEE-05', 'Creation calls P.mutate with requestBody be(value) and requestContext. Update calls me.mutate with environmentId, requestBody ye(value, environment) and requestContext.', ['Et'], 'be and ye serialize externally; no wire-field equivalence or endpoint behavior is asserted.'),
    fact('CEE-06', 'Successful non-aborted settlement notifies, resets the form to submitted values, then calls onSaved with the new or original ID. Failed non-aborted settlement notifies without reset. Aborted context suppresses these callbacks.', ['Et'], 'The local submit callback has no initial signal.aborted guard. Suppressing presentation does not prove transport cancellation.'),
    fact('CEE-07', 'requestClose returns while either mutation is pending. Otherwise a dirty form opens the unsaved dialog and a clean form calls onCancel. The exposed imperative ref uses that same handler.', ['Et', 'Ot'], 'Closing is not an abort operation. Form library and dialog implementation remain separate boundaries.'),
    fact('CEE-08', 'The DOM form prevents the default event and calls form.handleSubmit. Name and description controls have maxLength 64 and 512; container-image membership is passed to the validator.', ['Et'], 'HTML input limits do not establish server validation; form-hook duplicate-submit behavior was not tested.'),
    fact('CEE-09', 'Selecting a repository forwards its connector ID, repository ID and full name to form fields; label selection uses imported B. Only the first picker selection is forwarded.', ['pt', 'ht'], 'Repository query, ranking, authentication and label-generation algorithms remain external.'),
    fact('CEE-10', 'The dotenv paste helper skips empty/comment lines, accepts optional export and quoted values, strips unquoted comments, preserves empty values and rejects the whole paste on malformed input.', ['$e', 'it']),
    fact('CEE-11', 'The repository picker and preinstalled-packages dialog are lazy module delegates. Their import locations are recorded, without generating another feature denominator.', ['yt', 'assignment-jt']),
]
imports = {specifier['local']: {'module': item['module'], 'export': specifier['imported'], 'importEvidence': item} for item in selection['imports'] for specifier in item['specifiers']}
pending = [
    {'id': 'CEE-P01', 'question': 'What defaults, validation errors, normalization and repository-label preservation are actually implemented?', 'locals': ['Oe', '_e', 'Ne', 'B'], 'requiredFor': 'FSC-0343/FSC-0344 input and validation contract'},
    {'id': 'CEE-P02', 'question': 'Which create/update wire fields, omitted properties and secret update semantics are generated?', 'locals': ['be', 'ye'], 'requiredFor': 'FSC-0343/FSC-0344 mutation payload contract'},
    {'id': 'CEE-P03', 'question': 'Which service, cache invalidation and request-context cancellation implementations are selected?', 'locals': ['ge', 'Ee', 'De', 've'], 'requiredFor': 'T46 service ownership and failure/cancellation boundary'},
    {'id': 'CEE-P04', 'question': 'What library identity and application wrapper implement form subscriptions, validation and duplicate-submit behavior?', 'locals': ['ze', 'Re'], 'requiredFor': 'External dependency adoption and first-party wrapper separation'},
    {'id': 'CEE-P05', 'question': 'What are the retained picker/packages contracts and actual mode/account/flag conditions?', 'locals': [], 'requiredFor': 'Existing T46 delegates; unknown modes retained without exclusion'},
]
for item in pending:
    item['providers'] = {name: imports[name] for name in item['locals']}

WORK.joinpath('state-before.json').write_bytes(state_bytes)
readers = [OUT / 'report.md', OUT / 'gaps.md']
for reader in readers:
    shutil.copyfile(reader, WORK / (reader.name + '.before'))
RAW.mkdir(parents=True)
shutil.copytree(WORK / 'editor', RAW / 'editor')
for name in ['selector-receipt.json', 'selector.stdout.txt', 'selector.stderr.txt', 'probe-attempt-01.json']:
    shutil.copyfile(WORK / name, RAW / name)
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
result = {
    'baselineId': BASE, 'createdAtUtc': now,
    'scope': {'taskId': 'T46', 'featureIds': ['FSC-0343', 'FSC-0344'], 'newFeatureDefinitions': 0, 'newProductSpecifications': 0, 'productScenarioPassesAdded': 0, 'modelSubmissionsAdded': 0, 'originalClientRunsAdded': 0},
    'counts': {'newCompleteProgramsParsed': 1, 'selectedSourceUnits': len(units), 'facts': len(facts), 'isolatedCasesPassed': 30, 'isolatedCasesFailed': 0, 'explicitPendingProviderGroups': len(pending)},
    'callerBinding': binding, 'editorExports': selection['exports'],
    'facts': facts, 'pendingProviders': pending,
    'inputPins': inputs,
    'rawEvidence': [pin(path) for path in sorted(RAW.rglob('*')) if path.is_file()],
    'qualification': probe['limits'],
    'localEditorControlFlowAnalyzed': True,
    'completeCreateUpdateServiceContractClosed': False,
    'fullAnalysisCompleted': False,
}
result_path = OUT / 'cloud-environment-editor-contracts.json'
create(result_path, result)
summary = OUT / 'cloud-environment-editor-contracts.md'
summary.write_text('''# 云环境创建／编辑的委托边界

本次仅补充既有 T46、FSC-0343／0344 的编辑器，功能台账仍为373项、1216条未执行规格；没有增加页面、功能或计划版本。

已把设置页的 `ht←t` 接到编辑器 `wt`，解释新建／编辑分流、创建时的连接器优先级、重复名称检查等待、创建／更新调用、请求上下文、成功／失败反馈和取消时的未保存确认。提交时实际校验、默认值和报文序列化是导入边界，明确列在[来源合同](cloud-environment-editor-contracts.json)中。

30项精确源码隔离用例通过。它们覆盖局部转发与控制流：名称查询未完成时新建被阻止，编辑未改名称时可进入提交；HTTP 404被当作名称检查可继续；成功先通知、重置再回调；请求被标记中断后回调不再更新界面。最后一项不证明服务请求已取消，局部提交函数也没有预先检查中断标记。

待提交时取消关闭请求；未保存时打开确认框；干净状态调用取消回调。表单库的实际防重复提交、HTTP接口与缓存、校验及报文字段、仓库选择器和软件包弹窗仍有5组明确的provider问题。前4组均已定位到导入模块和导出名，无需再次寻找编辑器入口。

本次核对一个完整冻结Program，选取73个来源单元并验证哈希及字节范围；未启动原客户端、连接账户／服务或提交模型任务。上述结果不计为真实客户端场景通过，原九项完成标准的状态保持不变。
''')
overlay = {'contracts': pin(result_path), 'summary': pin(summary), 'counts': result['counts'], 'featureIds': result['scope']['featureIds'], 'taskId': 'T46', 'completeCreateUpdateServiceContractClosed': False, 'fullAnalysisCompleted': False}
state['cloudEnvironmentEditorContracts'] = copy.deepcopy(overlay)
state['stageDecisions']['cloudEnvironmentEditorOverlay'] = copy.deepcopy(overlay)
state['updatedAtUtc'] = now
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
paragraph = '\n[云环境创建／编辑委托补充](cloud-environment-editor-contracts.md)接上既有T46的实际编辑器：30项局部源码用例通过，明确分流、名称检查等待、提交与关闭时序；校验、报文、服务／缓存、表单库和委托组件保留5组具体provider问题。功能、场景分母及九项完成标准不变。\n'
for reader in readers:
    previous = reader.read_text()
    heading, rest = previous.split('\n', 1)
    reader.write_text(heading + '\n' + paragraph + rest)
for path in [result_path, summary, *[path for path in RAW.rglob('*') if path.is_file()]]:
    path.chmod(0o444)
print(json.dumps({'result': str(result_path), 'summary': str(summary), 'counts': result['counts']}, ensure_ascii=False))
