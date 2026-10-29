"""Derive bounded engineering decisions from saved exact-source contracts only."""
import collections
import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/entry-composition-roles-work'
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'
WORK.mkdir(parents=True, exist_ok=True)
PINS, SOURCES, SPANS = {}, {}, set()
sha = lambda data: hashlib.sha256(data).hexdigest()


def pin(path):
    path = Path(path)
    data = path.read_bytes()
    result = {'path': str(path.relative_to(OUT)), 'bytes': len(data), 'sha256': sha(data)} if path.is_relative_to(OUT) else {'path': str(path.relative_to(ROOT)), 'pathBase': 'workspace', 'bytes': len(data), 'sha256': sha(data)}
    PINS[str(path)] = result
    return result


def load(name):
    path = OUT / name
    pin(path)
    return json.loads(path.read_text())


def ref(name, pointer):
    return {**pin(OUT / name), 'jsonPointer': pointer}


def normalize(item):
    name = item['sourcePath']
    if not name.startswith('app.asar/'):
        name = 'app.asar/' + name
    extent = item.get('byteRange', item.get('range', item.get('locator')))
    start, end = extent['start'], extent.get('endExclusive', extent.get('end'))
    if name not in SOURCES:
        SOURCES[name] = (FROZEN / name.removeprefix('app.asar/')).read_bytes()
    data = SOURCES[name]
    source_hash = item.get('sourceHash', item.get('sourceSha256'))
    assert sha(data) == source_hash
    span_hash = sha(data[start:end])
    expected = item.get('spanHash', item.get('spanSha256'))
    assert expected is None or span_hash == expected
    assert 0 <= start < end <= len(data)
    SPANS.add((name, start, end, span_hash))
    return {'sourcePath': name, 'sourceHash': source_hash, 'byteRange': {'start': start, 'endExclusive': end}, 'spanHash': span_hash}


def text(source):
    return SOURCES[source['sourcePath']][source['byteRange']['start']:source['byteRange']['endExclusive']].decode()


def write(name, value):
    path = OUT / name
    data = value if isinstance(value, bytes) else (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    with path.open('xb') as file:
        file.write(data)
    path.chmod(0o444)
    return pin(path)


state_path = OUT / 'analysis-state.json'
before_bytes = state_path.read_bytes()
with (WORK / 'state-before.json').open('xb') as file:
    file.write(before_bytes)
state = json.loads(before_bytes)
assert state['legacyEntryDispositions']['result']['path'] == 'legacy-entry-dispositions-v4.json'
legacy = load('legacy-entry-dispositions-v4.json')
families = load('entry-family-map.json')
routes = load('route-contracts.json')
menus = load('menu-command-contracts.json')
registration = load('command-registration-contracts.json')
load('command-consumer-contracts.json')
load('renderer-command-bridge-helper.json')
load('logical-module-ownership-v1.json')
load('restoration-coverage-v18.json')
load('feature-scope-v27.json')
pin(Path(__file__))
evidence_input = OUT / 'menu-command-evidence.jsonl'
pin(evidence_input)
menu_evidence = {x['id']: x for x in map(json.loads, evidence_input.read_text().splitlines())}
family_by_id = {x['entryId']: x for x in families['entries']}
pending = [x for x in legacy['entries'] if x['disposition'] == 'awaiting-disposition']
assert len(pending) == 253
assert collections.Counter(x['family'] for x in pending) == {'renderer-routes': 169, 'renderer-navigation': 47, 'route-conversion': 3, 'shortcut-and-renderer-registration': 34}
route_by_id = {x['id']: x for x in routes['registrations']}
contract_index = {x['contractId']: x for x in menus['contractRecordIndex']}
ast_inputs = {}


def ast_entry(family):
    artifact = family['astRef']['path']
    if artifact not in ast_inputs:
        ast_inputs[artifact] = load(artifact)
        assert ast_inputs[artifact]['fullProgramParsed'] and ast_inputs[artifact]['parserErrors'] == 0
        assert not ast_inputs[artifact]['targetCodeExecuted']
    result = ast_inputs[artifact]['entries'][int(family['astRef']['jsonPointer'].split('/')[-1])]
    assert result['entryId'] == family['entryId']
    return result


def same_extent(left, right):
    return left['sourcePath'] == right['sourcePath'] and left['range']['start'] == right['range']['start'] and left['range']['endExclusive'] == right['range']['endExclusive']


navigation_joins = []
for nav_index, navigation in enumerate(routes['navigationTargets']):
    source = normalize(navigation)
    assert navigation['component']['terminal']['name'] == routes['routeIdentity']['navigationLocalSymbol']
    navigation_joins.append({'index': nav_index, 'source': source, 'contract': ref('route-contracts.json', f'/navigationTargets/{nav_index}'), 'target': navigation['target']})
direct_pairs = []
wrapper_pairs = []
for route in routes['registrations']:
    element = route.get('element') or {}
    for nav in navigation_joins:
        original_nav = routes['navigationTargets'][nav['index']]
        if element.get('sourcePath') and same_extent(element, original_nav):
            direct_pairs.append({'routeId': route['id'], 'navigationIndex': nav['index'], 'source': nav['source'], 'relation': 'same exact Navigate construction is also the route element'})
    definitions = element.get('component', {}).get('terminal', {}).get('valueDefinitions', [])
    matches = []
    for nav in navigation_joins:
        extent = nav['source']['byteRange']
        for definition in definitions:
            if definition['sourcePath'] == nav['source']['sourcePath'] and definition['range']['start'] <= extent['start'] < extent['endExclusive'] <= definition['range']['endExclusive']:
                matches.append({'navigationIndex': nav['index'], 'componentDefinition': normalize(definition)})
    if matches:
        wrapper_pairs.append({'routeId': route['id'], 'componentExpression': element['component']['expression'], 'navigationBranches': matches,
                              'qualification': 'Navigate syntax is inside the exact resolved component definition. This is not a claim that every render redirects; conditions, props, children and other returns remain part of the component.'})
assert len(direct_pairs) == 7 and len(wrapper_pairs) == 55

roles = []
role_by_kind = {
    'os-global-native-registration': ('native-global-shortcut-registration', 'partial-shortcut-registration-role', 'EC-04'),
    'os-global-wrapper-consumer': ('global-shortcut-adapter-consumer', 'partial-shortcut-registration-role', 'EC-05'),
    'before-input-event-registration': ('window-input-event-registration', 'partial-shortcut-registration-role', 'EC-06'),
    'renderer-hook-scope': ('renderer-registration-composition-function', 'partial-renderer-hook-container', 'EC-08'),
    'renderer-message-subscription-candidate': ('typed-message-subscription-call-candidate', 'partial-message-subscription-candidate', 'EC-08'),
}
for entry in pending:
    family = family_by_id[entry['entryId']]
    raw = ast_entry(family)
    source = normalize(family['sourceCoordinates'])
    assert source == normalize(raw['freshlyHashedSourceSpan'])
    matched = normalize(raw['matchedNode'])
    assert matched['byteRange']['start'] <= source['byteRange']['start'] < source['byteRange']['endExclusive'] <= matched['byteRange']['endExclusive']
    refs = [ref('entry-family-map.json', '/entries/' + str(next(i for i, x in enumerate(families['entries']) if x['entryId'] == entry['entryId']))), ref(family['astRef']['path'], family['astRef']['jsonPointer'])]
    details = {}
    if entry['family'] == 'renderer-routes':
        route = route_by_id[entry['entryId']]
        assert source == normalize(route)
        direct = [x for x in direct_pairs if x['routeId'] == route['id']]
        role = 'redirect-route-construction' if direct else 'index-route-construction' if route.get('index', {}) and route['index'].get('value') is True else 'mapped-route-template' if route['arrayMapTemplates'] else 'layout-route-construction' if not route.get('path') or route['path']['status'] == 'no-path' else 'path-route-construction'
        disposition, owner = 'partial-route-composition', 'EC-01'
        refs.append(ref('route-contracts.json', '/registrations/' + str(routes['registrations'].index(route))))
        details = {'parentRouteIds': route['parentRouteIds'], 'ancestorRouteIds': route['ancestorRouteIds'], 'conversionConsumerIds': route['conversionConsumerIds'], 'path': route.get('path'), 'arrayMapTemplateCount': len(route['arrayMapTemplates']), 'expandedStaticMapInstanceCount': len(route['staticMapInstances']), 'directNavigationIndexes': [x['navigationIndex'] for x in direct]}
        remaining = 'Component behavior, mounting conditions, shared/Codex dependency closure and actual route instances remain separate feature work. Route names do not establish feature identity or exclusion.'
    elif entry['family'] == 'renderer-navigation':
        matches = [x for x in navigation_joins if x['source'] == source]
        assert len(matches) == 1
        nav = matches[0]
        role, disposition, owner = 'navigate-element-construction', 'partial-navigation-role', 'EC-03'
        refs.append(nav['contract'])
        details = {'navigationIndex': nav['index'], 'target': nav['target'], 'callableOwner': normalize(family['lexicalOwner'])}
        remaining = 'Resolved Navigate binding and source target do not prove rendering, target reachability, current state or product mode. Keep source owner guards and replacement/state behavior.'
    elif entry['family'] == 'route-conversion':
        consumer = next(x for x in routes['conversionConsumers'] if x['id'] == entry['entryId'])
        assert source == normalize(consumer)
        role, disposition, owner = 'route-table-conversion-call', 'non-user-operation-source', 'EC-02'
        refs.append(ref('route-contracts.json', '/conversionConsumers/' + str(routes['conversionConsumers'].index(consumer))))
        details = {'inputExpression': consumer['inputExpression'], 'registrationIds': consumer['registrationIds'], 'resultAssignment': consumer['resultAssignment'], 'resolvedCalleeTerminal': consumer['callee']['terminal']}
        remaining = 'Framework conversion plumbing, not a user operation. Preserve the three source graph inputs; actual router provider, runtime instance and selected branch are not established by conversion alone.'
    else:
        role, disposition, owner = role_by_kind[entry['entryKind']]
        contract = contract_index[entry['entryId']]
        refs.append(ref('menu-command-contracts.json', contract['jsonPointer']))
        details = {'lexicalOwner': normalize(family['lexicalOwner']), 'ownerName': family['lexicalOwner']['name'], 'contractPrimaryEvidenceId': contract['primaryEvidenceId']}
        if entry['entryKind'] == 'renderer-message-subscription-candidate':
            remaining = 'Exact xs call and literal message type are saved. The older fragment helper explicitly leaves the cross-file xs identity unresolved; do not upgrade this to confirmed transport delivery or equate it with Pw.'
        else:
            remaining = 'Preserve original scope, callback/options and lifecycle; actual owner/provider, mount/registration success and user-feature identity remain qualified.'
    roles.append({'entryId': entry['entryId'], 'entryKind': entry['entryKind'], 'family': entry['family'], 'source': source, 'matchedNode': matched, 'sourceRole': role, 'disposition': disposition, 'maintenanceDecisionId': owner, 'savedContracts': refs, 'structuralGuards': raw['structuralGuards'], 'details': details, 'remainingWork': remaining, 'actualRuntimeVerified': False, 'functionalEntryFullyResolved': False})

# Structural ancestry is a qualified consumer relation, not 367 new operations.
settings_entry = next(x for x in legacy['entries'] if x['entryId'] == 'ROUTE-0152')
assert len(settings_entry['featureIds']) == 367
settings_route = route_by_id['ROUTE-0152']
ancestors = settings_route['ancestorRouteIds']
assert ancestors == ['ROUTE-0134', 'ROUTE-0169', 'ROUTE-0161', 'ROUTE-0170']
ancestry = {'descendantRouteId': 'ROUTE-0152', 'ancestorRouteIds': ancestors, 'featureIds': settings_entry['featureIds'], 'source': normalize(settings_route),
            'relation': 'conditional ancestor composition context of already associated settings container',
            'qualification': 'These four contexts inherit the existing conditional feature relation. They are not four implementations of each feature, new functional entries, observed mounts, or additional mode evidence.',
            'contract': ref('route-contracts.json', '/registrations/' + str(routes['registrations'].index(settings_route)))}

mechanisms = []
for label, evidence_id, claim in [
    ('EC-SHORTCUT-NATIVE', 'ENTRY-AST-E04974', 'fI increments generation, stores native registration result, and guards callback by suspension counter, registered state and generation.'),
    ('EC-SHORTCUT-ADAPTER', 'ENTRY-AST-E04992', 'aI preserves ownership wrappers, Windows/bare-modifier branches, normalized duplicate rejection, registration failure, release-monitor rollback, suspension and unregister cleanup. Native/helper providers remain external.'),
    ('EC-SHORTCUT-REFRESH', 'ENTRY-AST-E04993', 'pI retains macOS layout re-registration behavior: suspended entries update their key; failed replacement restores old key/generation/registered state; success unregisters the old key.'),
]:
    source = normalize(menu_evidence[evidence_id])
    mechanisms.append({'id': label, 'source': source, 'claim': claim, 'savedEvidence': ref('menu-command-contracts.json', '/globalShortcuts')})
pw = normalize(registration['coreSourceUnits']['definition-Pw'])
assert 'useEffect' in text(pw) and 'Pqt(e,_,{isActive:h,priority:f})' in text(pw)
mechanisms.append({'id': 'EC-COMMAND-REGISTRY', 'source': pw, 'claim': 'Pw is a React effect adapter: enabled/active/priority, keyboard/context handlers, shared registry and menu metadata updates, with cleanup. Preserve it separately from native global shortcuts and message subscriptions.', 'savedEvidence': ref('command-registration-contracts.json', '/coreSourceUnits/definition-Pw')})

def decision(identifier, path, responsibility, role_ids, imports, exports, state_contract, effects, dependency_contract, existing_owner=None):
    selected = [x['entryId'] for x in roles if x['maintenanceDecisionId'] in role_ids]
    return {'decisionId': identifier, 'proposedPath': path, 'responsibility': responsibility, 'environment': 'main' if '/main/' in path else 'renderer', 'productMode': 'unknown', 'entryIds': selected, 'imports': imports, 'exports': exports, 'sharedState': state_contract, 'sideEffects': effects, 'thirdPartyDependencies': dependency_contract, 'sourceRanges': [x['source'] for x in roles if x['entryId'] in selected], 'existingOwnerRelation': existing_owner, 'confidence': 'inferred', 'status': 'source-backed maintenance proposal; not original module/file recovery', 'implementationGenerated': False}

decisions = [
    decision('EC-01', 'apps/desktop/src/renderer/navigation/route-table.tsx', 'Compose route declarations and retain nesting, conditions, map templates and lazy component boundaries.', ['EC-01'], ['Resolved Route/JSX provider and feature page factories', 'LM-SETTINGS-3 route policy and renderer'], ['Route composition factory'], 'Keep qIs/JIs/YIs construction and component-owned context; do not flatten guards or assume initialization order.', ['Constructs route elements; actual page effects remain owned by resolved pages.'], ['Use framework dependencies through imports; preserve first-party composition only. Exact versions remain governed by dependency ledger.'], 'Uses LM-SETTINGS-3; does not duplicate or absorb its settings policy.'),
    decision('EC-02', 'apps/desktop/src/renderer/navigation/router.tsx', 'Adapt the three saved route conversion inputs to the router assembly.', ['EC-02'], ['EC-01 route compositions', 'Resolved JA/createRoutesFromElements provider'], ['Converted route configuration'], 'Preserve distinct conversion inputs and existing result assignment.', ['No user-operation or runtime navigation success claimed.'], ['Import framework conversion implementation; do not regenerate its bundled source.']),
    decision('EC-03', 'apps/desktop/src/renderer/navigation/redirects.tsx', 'Maintain shared redirect helpers while retaining feature-specific branch ownership.', ['EC-03'], ['Resolved Navigate component', 'Caller-provided target, location and context'], ['Navigation helper/component contracts'], 'Dynamic targets, replacement/state and enclosing branch context remain at original owner.', ['Navigation when the enclosing component actually renders.'], ['Import navigation provider; exact package provenance is inherited, not newly established.']),
    decision('EC-04', 'apps/desktop/src/main/shortcuts/global-shortcut-registry.ts', 'Restore first-party registration lifecycle and platform adapter policies.', ['EC-04'], ['Native runtime globalShortcut', 'Ownership/key normalization/release/bare-modifier providers'], ['Register/unregister and suspension/refresh contracts'], 'Registry set, generation, registered flag, suspension count and layout state are shared; use the saved fI/aI/pI contracts.', ['Native shortcut registration, release watcher disposal and layout re-registration rollback.'], ['Runtime and helper implementations are dependencies. Private/modified providers must be qualified separately.']),
    decision('EC-05', 'apps/desktop/src/main/shortcuts/register-client-shortcuts.ts', 'Wire manager-owned callbacks to the shared registry without merging manager state.', ['EC-05'], ['EC-04 registration adapter', 'Original manager callbacks and ownership contracts'], ['Composition/disposal wiring for the ten saved consumers'], 'Dictation and other manager state stays with each resolved lexical class/function.', ['Registers onPressed/onReleased/onCancelled callbacks under source conditions.'], ['Underlying runtime is accessed through EC-04; no third-party code is generated.']),
    decision('EC-06', 'apps/desktop/src/main/windows/input-event-adapter.ts', 'Define input-event attachment contracts; keep the six handler policies with their window/browser/MCP owners.', ['EC-06'], ['Window/WebContents event provider', 'Owner-specific handlers'], ['Attach/dispose interfaces'], 'Actual WebContents instance and owner lifecycle remain unverified; no global handler consolidation.', ['before-input-event registration and original handler effects.'], ['Runtime event API is an explicit dependency.']),
    decision('EC-07', 'apps/desktop/src/renderer/commands/registry.ts', 'Restore shared command registration, dispatch metadata and effect lifecycle.', [], ['React hooks and selected store/registry providers'], ['Pw/Pqt contract equivalents and cleanup interfaces'], 'Existing registry and menu metadata are shared; imported stores remain explicit boundaries.', ['Register/unregister, metadata updates and callback execution under enabled/active/priority conditions.'], ['Import React/store implementations; recover first-party registration glue.']),
    decision('EC-08', 'apps/desktop/src/renderer/commands/registrations.ts', 'Keep seven registration composition functions and ten message-call candidates in their original functional ownership.', ['EC-08'], ['EC-07 for proven Pw bindings', 'Qualified message subscription provider; xs cross-file identity remains unresolved'], ['Owner-scoped registration/subscription compositions'], 'Preserve per-hook dependencies and cleanup. Fsc has no direct Pw call in this saved subset; its scope is not a registration by itself.', ['Command/message callbacks can create, navigate or dispatch through their original providers.'], ['Message hook/provider and React are imported dependencies; transport and command registry remain separate.']),
]
decisions[6]['sourceRanges'] = [pw, normalize(registration['coreSourceUnits']['definition-Pqt']), normalize(registration['coreSourceUnits']['definition-fJt']), normalize(registration['coreSourceUnits']['definition-pJt'])]
counts = {'reviewedRemainingRecords': len(roles), 'sourceRoleCounts': dict(collections.Counter(x['sourceRole'] for x in roles)), 'maintenanceDecisions': len(decisions), 'savedRouteConstructions': len(routes['registrations']), 'directRedirectRoutePairs': len(direct_pairs), 'routeComponentsContainingNavigationBranches': len(wrapper_pairs), 'additionalConditionalAncestorContainers': len(ancestors), 'featuresInExistingConditionalContainerRelation': 367, 'newFeatures': 0, 'newProductScenarioPasses': 0, 'newSourceParses': 0, 'newReaRuns': 0, 'newModelSubmissions': 0, 'newClientRuns': 0, 'newClientImplementation': 0}
review = {'schemaVersion': 1, 'baselineId': BASE, 'recordedAtUtc': datetime.now(timezone.utc).isoformat(), 'scope': 'Disposition all 253 saved remaining source records, derive bounded composition/adapter ownership and preserve unresolved feature/provider/mode work.', 'records': roles, 'maintenanceDecisions': decisions, 'directRedirectPairs': direct_pairs, 'componentNavigationBranches': wrapper_pairs, 'settingsAncestorAssociation': ancestry, 'mechanismContracts': mechanisms, 'counts': counts, 'inputPins': list(PINS.values()), 'sourceValidation': {'uniqueSpansChecked': len(SPANS), 'savedCompleteProgramInputs': list(ast_inputs), 'targetCodeExecuted': False}, 'qualifications': ['A reviewed source role is not a complete functional identity or product denominator.', '55 component definitions contain Navigate syntax; branch execution and full component behavior are not thereby proved.', '8 decisions are maintenance boundaries, not 8 recovered original modules or a replacement whole-client project.', '373 features,48 task groups,1216 unexecuted scenarios and mode classifications remain unchanged.', 'Only proven ChatGPT-only branches may be removed; path names and redirects do not establish exclusion.'], 'fullAnalysisCompleted': False}
review_pin = write('entry-composition-roles-v1.json', review)
evidence = []
for index, record in enumerate(roles):
    source = record['source']
    evidence.append({'id': f'ENTRY-COMPOSITION-{index:03d}', 'baselineId': BASE, 'claim': record['sourceRole'] + '; finite source-role disposition, with functional/provider/runtime qualifications retained.', 'sourcePath': source['sourcePath'], 'sourceHash': source['sourceHash'], 'locator': {'byteRange': source['byteRange'], 'spanHash': source['spanHash'], 'entryId': record['entryId']}, 'method': 'saved-full-Program-AST-and-contract-join; frozen-byte-recheck', 'confidence': 'confirmed', 'verificationStatus': 'bounded-source-role-only; runtime-and-complete-feature-identity-unverified'})
for mechanism in mechanisms:
    source = mechanism['source']
    evidence.append({'id': mechanism['id'], 'baselineId': BASE, 'claim': mechanism['claim'], 'sourcePath': source['sourcePath'], 'sourceHash': source['sourceHash'], 'locator': {'byteRange': source['byteRange'], 'spanHash': source['spanHash']}, 'method': 'saved-complete-source-contract-and-frozen-byte-review', 'confidence': 'confirmed', 'verificationStatus': 'source-contract-only; provider-and-runtime-unverified'})
evidence_pin = write('entry-composition-roles-v1-evidence.jsonl', ''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in evidence).encode())
old_legacy_pin = pin(OUT / 'legacy-entry-dispositions-v4.json')
legacy['previousSnapshot'] = old_legacy_pin
legacy['recordedAtUtc'] = review['recordedAtUtc']
legacy['entryCompositionRoleReview'] = review_pin
role_by_id = {x['entryId']: (i, x) for i, x in enumerate(roles)}
for entry in legacy['entries']:
    if entry['entryId'] not in role_by_id:
        continue
    index, record = role_by_id[entry['entryId']]
    entry.update(disposition=record['disposition'], sourceRoleConfirmed=True, sourceRole=record['sourceRole'], roleEvidenceRef={**review_pin, 'jsonPointer': '/records/' + str(index)}, maintenanceDecisionId=record['maintenanceDecisionId'], remainingWork=record['remainingWork'])
    if entry['entryId'] in ancestors:
        entry['featureIds'] = list(settings_entry['featureIds'])
        entry['featureAssociationKind'] = 'conditional-settings-ancestor-context; not functional identity'
        entry['featureAssociationEvidence'] = {**review_pin, 'jsonPointer': '/settingsAncestorAssociation'}
dispositions = collections.Counter(x['disposition'] for x in legacy['entries'])
assert dispositions['awaiting-disposition'] == 0
assert sum(not x['featureIds'] for x in legacy['entries']) == 962
legacy['counts'].update(entriesAwaitingDisposition=0, nonUserOperationSourceRecords=283, entriesWithoutFeatureMapping=962, dispositionCounts=dict(dispositions), partiallyMappedRouteAncestorContexts=4, sourceRoleReviewedRemainingEntries=253, sourceRoleDispositionCompleteForSaved968Entries=True)
legacy['accountingPolicy']['unknown'] = 'All 968 saved source records have a bounded role disposition; complete functional identities remain unresolved. 962 have no feature association. Four additional route ancestors inherit only a conditional settings-container context, not feature implementations. Product denominator and mode/provider/runtime work remain open.'
legacy['frozenSourceValidation']['entryCompositionSupplement'] = {'review': review_pin, 'savedLegacySpansChecked': 253, 'newSourceParses': 0}
legacy_pin = write('legacy-entry-dispositions-v5.json', legacy)
buffer = io.StringIO()
writer = csv.DictWriter(buffer, fieldnames=['entryId', 'entryKind', 'family', 'label', 'disposition', 'sourceRoleConfirmed', 'productMode', 'functionalEntryFullyResolved'], extrasaction='ignore')
writer.writeheader()
writer.writerows(legacy['entries'])
legacy_csv = write('legacy-entry-dispositions-v5.csv', buffer.getvalue().encode())
summary = '''# 路由、导航和快捷键的工程边界决定

剩余253条已保存来源记录已全部完成有限角色处置：169个路由构造、47个Navigate构造、3个路由转换，以及34个快捷键/renderer组合或订阅候选。旧入口v5保留968个原ID，待角色分类为0；完整功能身份解决仍为0，962条没有功能关联。此处关闭的是来源分类队列。

170个已保存路由中，7个直接构造Navigate，与导航清单中的同一位置配对；另有55个路由的已解析页面组件定义包含Navigate分支。这些组件仍可能有其他返回、条件和副作用，不据此判定它们总会重定向，也不按URL名称剥离ChatGPT功能。3次转换输入分别关联154、169、170个构造，是有重叠的静态图，不能相加为493个页面。

已有ROUTE-0152的367项条件关联，经精确祖先图接到ROUTE-0134、0169、0161、0170四个组合上下文。它们说明恢复时须保留的外层组合，不代表每层各实现367项功能，也不新增模式证据。

## 建议源码职责

| 拟议文件 | 职责及必须保留的边界 |
| --- | --- |
| `renderer/navigation/route-table.tsx` | 路由组合、嵌套、条件、动态map和页面加载；调用已有设置策略，不复制页面实现。 |
| `renderer/navigation/router.tsx` | 三个转换输入与router装配；框架转换代码由依赖提供。 |
| `renderer/navigation/redirects.tsx` | 可共享的导航契约；页面特有的判断、目标、replace/state仍由原页面负责。 |
| `main/shortcuts/global-shortcut-registry.ts` | 注册集合、generation、暂停、释放监视、布局更新及失败回退。 |
| `main/shortcuts/register-client-shortcuts.ts` | 十个管理器消费者的装配；录音等领域状态不并入registry。 |
| `main/windows/input-event-adapter.ts` | 六个窗口输入事件的挂接接口；具体MCP、browser和window策略保持各自所有权。 |
| `renderer/commands/registry.ts` | 已证明Pw绑定的enabled/active/priority、键盘/context、菜单元数据及effect清理。 |
| `renderer/commands/registrations.ts` | 七个组合函数保持原职责；十处xs调用仍为消息订阅候选，与Pw分开。 |

完整路径及职责、环境、来源范围、导入导出、共享状态、副作用、依赖与限制均在[结构化决定](entry-composition-roles-v1.json)中。八项是有源码支持的维护建议，不是原作者模块数，也不是完整客户端目录。底层框架、React和运行时通过依赖提供；第一方适配层需要恢复。

fI/aI/pI合同明确注册结果、所有者检查、重复键、平台/裸修饰键分支、释放监视失败回滚、暂停和布局替换失败时的状态恢复。把这些调用简单替换为globalShortcut.register会遗漏客户端行为。实际native/helper提供方仍需独立取得资格。

本批复用完整Program分析和已有合同，只复核冻结字节，没有新增解析、REA调用、客户端运行、模型任务或产品验收。373项功能、48任务、1216条未执行规格及372 unknown/1 shared保持不变。12项关联、3项重叠、模式共享闭包和实际provider/行为缺口仍需处理。

下一项以既有12项关联和3项重叠为固定队列，决定同一目标的共享消费者或不同操作，并将本批入口职责接入既有任务/逻辑模块方案；不再枚举已分类968条来源。[旧入口v5](legacy-entry-dispositions-v5.json)、[九字段证据](entry-composition-roles-v1-evidence.jsonl)保留限定范围。
'''
summary_pin = write('entry-composition-roles-v1.md', summary.encode())
overlay = {'contracts': review_pin, 'summary': summary_pin, 'evidence': evidence_pin, 'legacyEntryDispositions': legacy_pin, 'counts': counts, 'qualification': 'All saved source roles disposed; product scope/identity and mode/provider/runtime closure remain open.', 'fullAnalysisCompleted': False}
state['entryCompositionRoles'] = overlay
state['stageDecisions']['entryCompositionRoleOverlay'] = overlay
state['restorationCoverageCurrentOverlay']['entryCompositionRoleOverlay'] = overlay
state['legacyEntryDispositions'].update(result=legacy_pin, csv=legacy_csv, summary=summary_pin, counts=legacy['counts'])
view = state['featureScopeCurrentView']
view['legacyEntryDispositionOverlay'] = legacy_pin
view['entryCompositionRoleOverlay'] = review_pin
view['counts'].update(legacyEntriesAwaitingDisposition=0, legacyEntriesWithDefinitiveNonUserRole=283, legacyEntriesUnmappedInThisLedger=962, partiallyMappedLegacyContainers=5, legacyEntriesWithReviewedRouteRole=169, legacyEntriesWithReviewedNavigationRole=47, legacyEntriesWithReviewedShortcutOrRendererCompositionRole=34)
state['stageDecisions']['nextAction'] = {'issueId': 'SD-01', 'question': 'Resolve the existing 12 association items and 3 cross-feature overlap reviews using exact source/provider relations; connect entry ownership decisions to current task/module contracts.', 'fixedInput': 'Feature v27 association/overlap backlog, task v18, logical-module ownership v1 and completed source-role overlays. All968 saved source records have roles; no repeated entry enumeration.', 'closure': 'Each queued relation has a bounded shared-consumer, distinct-operation or exact-unresolvable-boundary decision; no label-only equivalence or mode exclusions.', 'authorization': 'Saved/frozen evidence only; no client, model or service invocation.'}
state['updatedAtUtc'] = datetime.now(timezone.utc).isoformat()
assert state['latestBehaviorAuthorizationState'] == json.loads(before_bytes)['latestBehaviorAuthorizationState']
assert not state['fullAnalysisCompleted']
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
for name in ('report.md', 'gaps.md'):
    path = OUT / name
    original = path.read_text()
    with (WORK / (name + '.before')).open('x') as file:
        file.write(original)
    first, separator, rest = original.partition('\n\n')
    path.write_text('当前[路由、导航与快捷键工程决定](entry-composition-roles-v1.md)已关闭剩余253条来源角色队列：八项职责建议、7处直接重定向配对及四层设置组合关联已登记。旧入口v5待角色分类0、完整功能身份解决0、未关联962；373项功能、48任务、1216未执行规格不变。下一项处理既有12关联/3重叠及其模块任务归属，完整分析未完成。' + separator + rest)
print(json.dumps({'review': review_pin, 'legacy': legacy_pin, 'counts': counts, 'dispositions': dict(dispositions)}, ensure_ascii=False))
