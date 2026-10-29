"""Publish menu restoration decisions, preserving immutable historical snapshots."""
import copy
import csv
import hashlib
import io
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/native-menu-roles-work'
PINS = {}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pin(p):
    b = p.read_bytes()
    v = {'path': str(p.relative_to(OUT)), 'bytes': len(b), 'sha256': sha(b)} if p.is_relative_to(OUT) else {'path': str(p.relative_to(ROOT)), 'pathBase': 'workspace', 'bytes': len(b), 'sha256': sha(b)}
    PINS[str(p)] = v
    return v


def load(p):
    pin(p)
    return json.loads(p.read_text())


def write(p, value):
    b = value if isinstance(value, bytes) else (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write(b)
    p.chmod(0o444)
    return pin(p)


state_path = OUT / 'analysis-state.json'
before = state_path.read_bytes()
with (WORK / 'state-before.json').open('xb') as f:
    f.write(before)
state = json.loads(before)
assert state['featureScopeCurrentView']['snapshotVersion'] == 27
assert state['latestBehaviorAuthorizationState']['groupRemaining'] == 0
scope = load(OUT / 'feature-scope-v27.json')
coverage = load(OUT / 'restoration-coverage-v18.json')
legacy = load(OUT / 'legacy-entry-dispositions-v2.json')
families = load(OUT / 'entry-family-map.json')
menu = load(OUT / 'menu-command-contracts.json')
query = load(WORK / 'menu-roles.json')
actions = load(OUT / 'dependency-investigation-actions-v1.json')
project = load(OUT / 'project-local-delegation-v1.json')
pin(OUT / 'dependencies.csv')
pin(OUT / 'project-path-controls.json')
pin(ROOT / 'scripts/analysis/analyze_native_menu_roles.mjs')
pin(Path(__file__))
assert query['counts']['legacyRecordsReviewed'] == 189
assert query['targetCodeExecuted'] is False
assert query['upstreamComparison']['matchedActionRecords'] == 19
upstream = []
for x in load(WORK / 'upstream/v4.1.2/retrieval.json'):
    p = WORK / 'upstream/v4.1.2' / x['file']
    b = p.read_bytes()
    assert hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest() == x['blobSha']
    upstream.append({**x, 'cachedInput': pin(p), 'gitBlobIdentityVerified': True})
assert json.loads((WORK / 'upstream/v4.1.2/package.json').read_text())['version'] == '4.1.2'
query_pin = write(OUT / 'raw/native-menu-roles-v1/menu-roles.json', (WORK / 'menu-roles.json').read_bytes())

unit_specs = [
    ('application-menu', ['CZe', 'PZe', 'bZe'], '应用菜单装配、命令元数据、快捷键和可用性条件', 'apps/desktop/src/main/menus/application-menu.ts',
     '保留 metadata producer、权限与平台/feature 条件、隐藏快捷键生成、刷新与安装顺序；动作回调委托现有窗口/领域服务。',
     ['commandKeymapState', 'desktopFeatureAvailability', 'applicationMenuManager'], ['安装或刷新应用菜单', '向窗口发送命令', '调用注入服务']),
    ('dock-menu', ['Qie', 'qf'], 'dock 菜单装配及动作委托', 'apps/desktop/src/main/menus/dock-menu.ts',
     '保留 darwin 条件和注入动作；菜单模板不等于新增业务功能。', ['owner instance', 'injected actions'], ['设置 dock 菜单', '调用注入动作']),
    ('mcp-context-menu', ['nse'], 'MCP App 上下文菜单和 DevTools 动作', 'apps/desktop/src/main/menus/mcp-context-menu.ts',
     '保留 webContents 存活检查及 DevTools 条件，归入 MCP App 宿主适配层。', ['target webContents'], ['打开 DevTools', '创建/弹出菜单']),
    ('browser-context-menu', ['Lke', 'Rke'], '浏览器上下文动作及密码动作菜单', 'apps/desktop/src/main/browser/context-menu.ts',
     '保留浏览器拥有者回调、对象存活检查和密码动作；标准 cut/copy/paste 仍委托 runtime role。', ['target webContents', 'injected browser/password handlers'], ['浏览器导航', '剪贴板', '图像/标注或密码动作委托']),
    ('dynamic-menu-adapter', ['xXe'], '动态菜单描述到原生 MenuItem 的适配', 'apps/desktop/src/main/menus/menu-item-adapter.ts',
     '保留 role、id、checked、enabled、icon、toolTip、submenu、label 转义与 registerAccelerator=false；具体动作来自调用方。', ['incoming menu descriptor'], ['创建原生菜单对象', '调用注入 click handler']),
    ('tray-menu', ['DXe', 'i7', 'n7'], '托盘菜单模板、动作委托和系统 quit 标签', 'apps/desktop/src/main/menus/tray-menu.ts',
     '保留系统 quit 标签的 runtime 查询、平台与托盘生命周期；不要把生成标签的 quit schema 当成又一退出功能。', ['tray owner instance', 'nativeIntl', 'appName'], ['构造/更新托盘菜单', '调用新线程/反馈/打开窗口/退出回调']),
    ('trace-menu-item', ['uMe'], '跟踪录制菜单项的动作与启用状态', 'apps/desktop/src/main/diagnostics/trace-menu-item.ts',
     '菜单项只持有录制动作的入口；录制生命周期和上传继续属于诊断服务。', ['trace menu state', 'injected recording callback'], ['调用录制回调']),
    ('context-menu-dependency', ['R$e'], 'electron-context-menu 候选第三方默认动作生成器', None,
     '恢复为包依赖及第一方配置/回调适配；不生成其第三方实现。v4.1.2 仅为已核对上游候选，不能据此锁定实际打包版本或宣称无修改。', ['library context-menu listener', 'provided options'], ['库内部菜单构造与事件监听', 'runtime/clipboard/download 调用']),
]
units = []
for unit_id, names, responsibility, proposed, rule, shared, effects in unit_specs:
    records = [x for x in query['rows'] if x['ownerName'] in names]
    units.append({'id': 'MENU-UNIT-' + unit_id, 'responsibility': responsibility, 'environment': 'main',
                  'mode': 'unknown', 'sourceRanges': [x for x in query['owners'] if x['name'] in names],
                  'imports': {'sourceContract': pin(OUT / 'menu-command-contracts.json'), 'completeImportClosure': 'unknown'},
                  'exports': {'boundDefinitions': names, 'esmExports': 'not-established-by-selected-owner-review'},
                  'sharedState': shared, 'sideEffects': effects,
                  'thirdPartyDependencies': ['electron-context-menu'] if names == ['R$e'] else ['electron-runtime; full dependency closure unresolved'],
                  'proposedPath': proposed, 'preservationRule': rule, 'entryIds': [x['entryId'] for x in records],
                  'recordCount': len(records), 'assignment': 'proposed-maintenance-group; not recovered original modules',
                  'runtimeValidated': False, 'clientImplementationGenerated': False})
assert sum(x['recordCount'] for x in units) == 189
row_index = {x['entryId']: i for i, x in enumerate(query['rows'])}
unit_by_entry = {entry: u['id'] for u in units for entry in u['entryIds']}
role_rules = {
    'application-menu-assembly-factory': '恢复第一方装配及过滤/快捷键策略；通过服务与命令注册表委托动作。',
    'application-menu-factory-consumer': '恢复依赖注入、刷新与重建关系；注入参数不等于实际实例身份。',
    'native-menu-installation-call': '恢复平台条件和安装/刷新时序；此 API 调用本身不是用户功能。',
    'native-template-construction-call': '以 runtime API 构造模板；保留实际模板输入和动态条目。',
    'native-item-construction-call': '以 runtime MenuItem API 构造；不恢复 runtime 的第三方实现。',
    'custom-action-schema': '恢复第一方声明、条件和回调，动作继续接入领域/窗口服务；不得按标签新增或剥离功能。',
    'menu-generator-options': '保留传入生成器的选项和回调；输出数量取决于实际生成器/条件，不按一条选项等同一个菜单实例。',
    'runtime-role-item': '保留 role 声明及可用性条件，通过独立 runtime 实现；实际平台行为须另验。',
    'runtime-role-with-submenu': '同时保留 role 和显式 submenu，不能以标准 role 为由丢弃应用菜单内容。',
    'submenu-container': '保留层级和条件；容器不是独立业务动作。',
    'dynamic-menu-item-adapter': '恢复动态描述到 MenuItem 的适配；具体角色和动作取决于调用方载荷。',
}
for row in query['rows']:
    row['maintenanceUnitId'] = unit_by_entry[row['entryId']]
    row['restorationDecision'] = role_rules[row['sourceRole']]
    if row['origin'] == 'electron-context-menu-selected-factory-candidate':
        row['restorationDecision'] = unit_specs[-1][4]
        row['originConfidence'] = 'inferred'
        row['remainingWork'] = '确认实际打包版本、所需导出/选项与修改状态及第一方启用调用；不得将候选上游当成精确发行。'
    elif row['sourceRole'] in ('runtime-role-item', 'runtime-role-with-submenu'):
        row['remainingWork'] = '核对实际平台/菜单条件、独立 runtime 的 role 效果及保留功能消费者。'
    elif row['sourceRole'] in ('custom-action-schema', 'menu-generator-options', 'dynamic-menu-item-adapter'):
        row['remainingWork'] = '追踪注入回调/动态参数的具体消费者、模式与效果；已有源码条件和调用引用保留。'
    else:
        row['remainingWork'] = '核对动态模板/启用条件与实际调用方；结构角色完成不代表所有功能归属已闭合。'

open_folder = menu['nativeMenuItems'][10]
assert open_folder['callback']['calls'][2]['expression'] == 't.createOrSelectProject'
folder_row = next(x for x in query['rows'] if x['contractPointer'] == '/nativeMenuItems/10')
candidate = {'entryId': folder_row['entryId'], 'sourceContract': {'path': 'menu-command-contracts.json', 'jsonPointer': '/nativeMenuItems/10/callback'},
             'chain': 'ensure/focus window -> injected getElectronMessageHandlerForWindow(window) -> optional handler.createOrSelectProject(window.webContents)',
             'consumerInjection': {'path': 'menu-command-contracts.json', 'jsonPointer': '/applicationMenu/consumers/0/injectedValues'},
             'possibleDomainContract': {'path': 'project-path-controls.json', 'jsonPointer': '/evidence/4'},
             'relatedExistingFeature': 'FSC-0105', 'relatedTask': 'T14',
             'decision': '候选公共 picker 入口关系；实际注入的 handler 身份尚未证明，不合并功能或增加旧入口功能关联。',
             'receiverIdentityProven': False, 'featureEquivalenceProven': False}
dep_row = next(x for x in actions['rows'] if x['dependencyId'] == 'root-023')
dependency = {'dependencyId': 'root-023', 'name': 'electron-context-menu',
              'sourceDeclaration': {k: dep_row[k] for k in ('sourcePath', 'sourceHash', 'locator', 'versionBasis')},
              'declaredRange': '^4.1.2', 'noticeCandidateVersions': ['4.1.2'], 'actualVersion': 'unknown',
              'upstreamReferenceVersion': '4.1.2', 'referenceLicense': 'MIT', 'upstreamInputs': upstream,
              'selectedFactory': query['upstreamComparison']['targetFactory'],
              'comparison': query['upstreamComparison'], 'selectedMenuRecordCount': 20,
              'decision': unit_specs[-1][4], 'modificationStatus': 'unknown', 'mode': 'unknown',
              'actionProgress': {'actualVersion': 'unresolved; reference version verified, bundled version not established',
                                 'upstreamAndModification': 'partial; fixed-tag source retrieved, Git blob hashes verified and 19 action fingerprints matched; complete code/semantic comparison absent',
                                 'license': 'reference-release MIT verified; exact consumed artifact linkage remains unresolved',
                                 'modeAndCaller': 'partial; selected factory mapped, first-party installation and product-mode closure unresolved'},
              'allInvestigationActionsClosed': False}

review = {'schemaVersion': 1, 'baselineId': BASE, 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
          'scope': 'All 189 saved native-menu source records; role, maintenance and selected third-party ownership decisions.',
          'sourceQuery': query_pin, 'counts': query['counts'], 'records': query['rows'],
          'maintenanceUnits': units, 'dependencyDecision': dependency, 'crossEntryCandidates': [candidate],
          'retentionDecision': '保留菜单层级、平台/feature/权限条件、快捷键生成、标准 role 和应用回调。第一方适配器恢复为源码；选定第三方默认动作生成器通过包引入。',
          'limits': ['130 schema constructions, 26 generator-option records and 33 factory/consumer/API records are different source denominators, not 189 user features or final runtime items.',
                     'Matched fingerprints support selected-factory package ownership; exact installed version, upstream modifications and whole-package equivalence remain unknown.',
                     'All original feature/task definitions, modes and unexecuted scenario counts remain unchanged; no runtime behavior or full functional mapping is claimed.'],
          'newModelSubmissions': 0, 'newClientRuns': 0, 'newReaRuns': 0, 'newProductScenarioPasses': 0,
          'newClientImplementation': 0, 'fullAnalysisCompleted': False, 'inputPins': list(PINS.values())}
review_pin = write(OUT / 'native-menu-roles-v1.json', review)
evidence = []
for i, row in enumerate(query['rows']):
    evidence.append({'id': 'MENU-ROLE-' + str(i).zfill(3), 'baselineId': BASE,
                     'claim': row['sourceRole'] + ': ' + row['restorationDecision'],
                     'sourcePath': row['sourcePath'], 'sourceHash': row['sourceHash'],
                     'locator': {'byteRange': row['byteRange'], 'spanHash': row['spanHash'], 'nodeType': row['nodeType'], 'contractPointer': row['contractPointer']},
                     'method': 'complete-selected-owner-AST; exact-legacy-contract-span-join' + ('; fixed-tag-default-action-fingerprint-inference' if row['originConfidence'] == 'inferred' else '') if 'originConfidence' in row else 'complete-selected-owner-AST; exact-legacy-contract-span-join',
                     'confidence': 'inferred' if row.get('originConfidence') == 'inferred' else 'confirmed',
                     'verificationStatus': 'source-role-confirmed; maintenance-design-proposed; runtime-and-full-feature-role-unverified'})
evidence_pin = write(OUT / 'native-menu-roles-v1-evidence.jsonl', ''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in evidence).encode())
legacy['recordedAtUtc'] = review['recordedAtUtc']
legacy['previousSnapshot'] = pin(OUT / 'legacy-entry-dispositions-v2.json')
legacy['nativeMenuRoleReview'] = review_pin
family_map = {x['entryId']: x for x in families['entries']}
for row in legacy['entries']:
    if row['entryId'] not in row_index:
        continue
    i = row_index[row['entryId']]
    r = query['rows'][i]
    assert row['disposition'] == 'awaiting-disposition'
    assert all(r[k] == family_map[row['entryId']]['sourceCoordinates'][k] for k in ('sourcePath', 'sourceHash', 'byteRange', 'spanHash'))
    row.update(disposition='partial-native-menu-role', sourceRoleConfirmed=True, sourceRole=r['sourceRole'],
               roleEvidenceRef={**review_pin, 'jsonPointer': '/records/' + str(i)},
               retentionDecision=r['restorationDecision'], maintenanceUnitId=r['maintenanceUnitId'], remainingWork=r['remainingWork'])
counts = Counter(x['disposition'] for x in legacy['entries'])
assert counts['awaiting-disposition'] == 394
legacy['counts'].update(entriesAwaitingDisposition=394, partialNativeMenuRoles=189, nativeMenuExternalLibraryCandidateRecords=20,
                        nativeMenuRuntimeRoleSchemas=33, nativeMenuCustomCallbackSchemas=88,
                        nativeMenuGeneratorOptionRecords=26, nativeMenuDynamicAdapters=1, dispositionCounts=dict(counts),
                        selectedOwnerParsesAdded=14, newFullProgramParses=0)
legacy['accountingPolicy']['unknown'] = '394 entries await source-role disposition. 143 host labels and 189 native-menu records have bounded source roles; their full feature/mode/effect mappings remain unresolved.'
legacy['accountingPolicy']['nativeMenu'] = 'Do not count schemas, generator options or construction/install calls as user features. 20 records have selected-factory external-library attribution supported by inference; exact bundled package remains unresolved.'
legacy['frozenSourceValidation']['nativeMenuSupplement'] = {'sourceQuery': query_pin, 'exactSourceNodesChecked': 189, 'completeOwnersParsed': 14}
legacy_pin = write(OUT / 'legacy-entry-dispositions-v3.json', legacy)
buf = io.StringIO()
writer = csv.DictWriter(buf, fieldnames=['entryId', 'entryKind', 'family', 'label', 'disposition', 'sourceRoleConfirmed', 'productMode', 'functionalEntryFullyResolved'], extrasaction='ignore')
writer.writeheader(); writer.writerows(legacy['entries'])
legacy_csv = write(OUT / 'legacy-entry-dispositions-v3.csv', buf.getvalue().encode())

# Definitions are unchanged: use a bounded overlay rather than cloning both large ledgers.
overlay = {'contracts': review_pin, 'summary': None, 'evidence': evidence_pin, 'legacyEntryDispositions': legacy_pin,
           'counts': query['counts'], 'legacyCounts': legacy['counts'],
           'featureLedgerBase': pin(OUT / 'feature-scope-v27.json'), 'restorationCoverageBase': pin(OUT / 'restoration-coverage-v18.json'),
           'qualification': 'Base feature/task/scenario definitions unchanged. This overlay supersedes only legacy source-role counts and menu/dependency maintenance decisions.',
           'fullAnalysisCompleted': False}
summary = '''# 原生菜单的恢复边界

本批对原有 189 条菜单记录逐条核对冻结源码和已保存的完整 Program 身份，不增加功能定义。

| 来源角色 | 数量 | 恢复决定 |
| --- | ---: | --- |
| 自定义回调 schema | 88 | 保留应用条件及回调，委托领域/窗口服务 |
| 标准 runtime role schema | 29 | 保留 role 声明，runtime 行为另验 |
| role 与显式 submenu 并存 | 4 | 两者同时保留，不能丢弃应用子菜单 |
| 纯子菜单容器 | 8 | 保留层级和条件，不另算业务功能 |
| 动态描述适配 schema | 1 | 保留字段、label 转义及动态 click 委托 |
| 生成器选项 | 26 | 保留参数和回调，不当作最终菜单实例数 |
| 构造/安装 API、工厂及消费者 | 33 | 保留装配、注入、刷新和生命周期 |

其中 20 条属于 `R$e` 候选第三方生成器。已从官方 `electron-context-menu` 的 `v4.1.2` 标签取得源码、manifest 和 MIT license，三个文件的 Git blob 身份均核对一致；19 组默认动作的键、属性集合、ID、标签及回调参数个数与冻结生成器吻合。结合包声明，这支持选定函数的第三方归属，不能证明实际打包版本、无修改或语义等价。[上游源码](https://github.com/sindresorhus/electron-context-menu/blob/v4.1.2/index.js)、[上游 manifest](https://github.com/sindresorhus/electron-context-menu/blob/v4.1.2/package.json)。

恢复决定是通过包引入该生成器，恢复第一方配置和回调适配；不生成库的实现副本。目前不能把 `4.1.2` 当作已确认的实际版本或可直接替换的锁定版本。依赖 root-023 的四项调查仅取得部分进展，修改、实际版本及第一方启用关系仍保留。

八组拟维护职责已分开：应用菜单、dock、MCP App context、浏览器 context、动态菜单适配、tray、trace 入口及外部库。它们是维护建议，未宣称还原原作者模块或完成全部消费者映射。源码中的 Chat 命名不作为剥离依据。

原生 Open Folder 回调已明确到注入的 `getElectronMessageHandlerForWindow(window)` 及 `createOrSelectProject(window.webContents)`。它与既有 T14 picker 合同存在候选关系，但实际注入身份未证明，故不合并功能、不新增功能关联。

当前旧入口中 394 条尚待源码角色处置；完整功能解决数仍为 0。保留 [v27 功能定义](feature-scope-v27.json)、[v18 恢复任务](restoration-coverage-v18.json) 和 1216 条未执行规格，当前菜单与旧入口计数由本批 overlay 更新，避免复制无变化的大台账。

明细：[角色及维护决定](native-menu-roles-v1.json)、[旧入口 v3](legacy-entry-dispositions-v3.json)、[九字段证据](native-menu-roles-v1-evidence.jsonl)。后续处理现有 backend/IPC 候选的协议归属和实际接收边界；不重扫菜单。没有启动客户端、提交模型任务或执行目标代码。
'''
summary_pin = write(OUT / 'native-menu-roles-v1.md', summary.encode())
overlay['summary'] = summary_pin
state['nativeMenuRoles'] = overlay
state['stageDecisions']['nativeMenuRoleOverlay'] = overlay
state['legacyEntryDispositions'].update(result=legacy_pin, summary=summary_pin, csv=legacy_csv, counts=legacy['counts'])
state['featureScopeCurrentView']['legacyEntryDispositionOverlay'] = legacy_pin
state['featureScopeCurrentView']['nativeMenuRoleOverlay'] = review_pin
state['featureScopeCurrentView']['counts'].update(legacyEntriesAwaitingDisposition=394, legacyEntriesWithReviewedNativeMenuRole=189)
state['restorationCoverageCurrentOverlay']['nativeMenuRoleOverlay'] = overlay
state['stageDecisions']['dependencyInvestigationOverlay'] = {'source': review_pin, 'dependencyId': 'root-023', 'actionsFullyClosed': False}
state['stageDecisions']['nextAction'] = {'issueId': 'SD-03',
    'question': 'Resolve saved backend-call and IPC candidates to concrete protocol, injection boundary and existing consumer roles.',
    'fixedInput': '91 backend-call and 50 IPC legacy records plus existing request-wrapper, host-service and app-host contracts.',
    'closure': 'Classify declared channel/API sites separately from domain operations; join exact call evidence to known provider/receiver or identify the precise injection gap.',
    'authorization': 'Frozen source and saved artifacts only; no target/client/model/service invocation.'}
state['updatedAtUtc'] = datetime.now(timezone.utc).isoformat()
assert state['latestBehaviorAuthorizationState'] == json.loads(before)['latestBehaviorAuthorizationState']
assert not state['fullAnalysisCompleted']
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
for name in ('report.md', 'gaps.md'):
    p = OUT / name
    text = p.read_text()
    (WORK / (name + '.before')).write_text(text)
    first, sep, rest = text.partition('\n\n')
    p.write_text('当前菜单恢复边界见[原生菜单决定](native-menu-roles-v1.md)：189条旧记录已区分应用回调、runtime role、结构/生成器及装配；20条选定生成器记录支持第三方归属，实际包版本/修改仍未知。旧入口v3尚有394条待角色处置，完整功能解决0；373项功能、48任务、1216条未执行规格不变。当前overlay更新计数，下一步核对已有backend/IPC接收边界，完整分析未完成。' + sep + rest)
print(json.dumps({'review': review_pin, 'legacy': legacy_pin, 'legacyCounts': legacy['counts']}, ensure_ascii=False))
