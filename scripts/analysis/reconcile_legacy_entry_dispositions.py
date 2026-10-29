"""Integrate already-proven legacy source roles into the current analysis view."""
import collections
import copy
import csv
import datetime
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'
WORK = ROOT / '.analysis-local/legacy-entry-dispositions-work'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path, pointer=None):
    value = {'path': str(path.relative_to(OUT)), 'bytes': path.stat().st_size,
             'sha256': sha(path)}
    if pointer is not None:
        value['jsonPointer'] = pointer
    return value


def dump(path, value):
    with path.open('x') as file:
        file.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def pointer(document, locator):
    for part in locator.strip('/').split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        document = document[int(part)] if isinstance(document, list) else document[part]
    return document


state = read(OUT / 'analysis-state.json')
assert state['updatedAtUtc'] == '2026-10-24T13:13:24.490233+00:00'
assert state['featureScopeCurrentView']['snapshotVersion'] == 22
old_state = copy.deepcopy(state)
scope = read(OUT / 'feature-scope-v22.json')
old_scope = copy.deepcopy(scope)
coverage = read(OUT / 'restoration-coverage-v13.json')
old_coverage = copy.deepcopy(coverage)
families = read(OUT / 'entry-family-map.json')
original = read(OUT / 'functional-entry-ledger.json')
metadata = read(OUT / 'menu-command-contracts.json')
registrations = read(OUT / 'command-registration-contracts.json')
consumers = read(OUT / 'command-consumer-contracts.json')
resources = read(OUT / 'raw/entry-families/settings-table.json')
assert not WORK.exists()
assert not (OUT / 'legacy-entry-dispositions.json').exists()
assert not (OUT / 'feature-scope-v23.json').exists()
assert not (OUT / 'restoration-coverage-v14.json').exists()
WORK.mkdir()
dump(WORK / 'state-before.json', state)

input_names = ['entry-family-map.json', 'functional-entry-ledger.json',
               'menu-command-contracts.json', 'command-registration-contracts.json',
               'command-consumer-contracts.json', 'raw/entry-families/settings-table.json',
               'feature-scope-v22.json', 'restoration-coverage-v13.json',
               'feature-scope-v21-scenarios.json', 'implementation-plan-v8.md']
input_hashes = {name: sha(OUT / name) for name in input_names}
inputs = {name: pin(OUT / name) for name in input_names}


def ref(name, locator):
    return {**inputs[name], 'jsonPointer': locator}


files = {}
checked_spans = set()


def check_span(position):
    source = position['sourcePath']
    assert source.startswith('app.asar/')
    if source not in files:
        path = FROZEN / source.removeprefix('app.asar/')
        data = path.read_bytes()
        files[source] = (data, hashlib.sha256(data).hexdigest())
    data, digest = files[source]
    assert digest == position['sourceHash'], source
    bounds = position['byteRange']
    start, end = bounds['start'], bounds['endExclusive']
    assert 0 <= start < end <= len(data)
    assert hashlib.sha256(data[start:end]).hexdigest() == position['spanHash']
    checked_spans.add((source, start, end))


old_ids = [item['entryId'] for item in original['entries']]
family_ids = [item['entryId'] for item in families['entries']]
assert old_ids == family_ids and len(set(old_ids)) == 968
metadata_index = {item['contractId']: (i, item)
                  for i, item in enumerate(metadata['metadataRegistry']['commands'])}
resource_index = {item['entryId']: (i, item)
                  for i, item in enumerate(resources['relations'])}
registration_index = {item['entryId']: (i, item)
                      for i, item in enumerate(registrations['legacyCandidateRelations'])}
key_matches = {}
for i, match in enumerate(consumers['metadataKeyJoins']):
    for identifier in match['metadataContractIds']:
        assert identifier not in key_matches
        assert metadata_index[identifier][1]['id'] == match['commandId']
        key_matches[identifier] = (i, match)
assert len(metadata_index) == 182 and len(resource_index) == 53
assert len(registration_index) == 6 and len(key_matches) == 80
assert resources['fullProgramParsed'] and resources['parserErrors'] == 0
for key in ['declaration', 'assignment', 'consumer', 'lookup']:
    check_span(resources[key])
check_span(registrations['coreSourceUnits']['definition-Pw'])

# Store known registration sites by exact literal key. This is an index into
# verified source contracts, not a claim of operation equivalence or dispatch.
registration_sites = collections.defaultdict(list)
for i, call in enumerate(registrations['sameBindingDirectCalls']):
    if call['commandId'] is not None:
        registration_sites[call['commandId']].append(
            ref('command-registration-contracts.json', f'/sameBindingDirectCalls/{i}'))
for i, consumer in enumerate(consumers['consumers']):
    assert consumer['fullProgramParsed'] and consumer['parserErrors'] == 0
    for j, call in enumerate(consumer['directCalls']):
        if call['commandId'] is not None:
            registration_sites[call['commandId']].append(
                ref('command-consumer-contracts.json', f'/consumers/{i}/directCalls/{j}'))
assert set(registration_sites) == set(consumers['combinedStaticCommandIds'])

rows = []
for index, entry in enumerate(families['entries']):
    identifier = entry['entryId']
    row = {
        'entryId': identifier, 'entryKind': entry['entryKind'],
        'family': entry['family'], 'label': entry['displayLabel'],
        'sourceEntryRef': ref('entry-family-map.json', f'/entries/{index}'),
        'disposition': 'awaiting-disposition',
        'sourceRoleConfirmed': False, 'functionalEntryFullyResolved': False,
        'productMode': entry['productMode'], 'actualRuntimeVerified': False,
        'featureIds': [],
    }
    if entry['family'] == 'settings-resources':
        i, correction = resource_index[identifier]
        assert entry['roleCorrection'] == correction
        assert correction['isSettingsPanelRegistration'] is False
        check_span(entry['sourceCoordinates'])
        check_span(correction['property'])
        row.update(
            disposition='non-user-operation-source', sourceRoleConfirmed=True,
            sourceRole=correction['role'], proposedModule=entry['suggestedPackage'],
            roleEvidenceRef=ref('raw/entry-families/settings-table.json', f'/relations/{i}'),
            consumerRef=ref('raw/entry-families/settings-table.json', '/consumer'),
            retentionDecision='Maintain the resource descriptor table and getter; import icon/component dependencies. No panel handler or independent user goal is established by this entry.',
            remainingWork='Connect retained UI consumers and mode conditions; resource role does not establish a panel implementation or runtime acceptance.')
    elif entry['family'] == 'command-metadata':
        i, command = metadata_index[identifier]
        assert entry['commandMetadata']['sourceRef']['sha256'] == inputs['menu-command-contracts.json']['sha256']
        assert entry['commandMetadata']['id'] == command['id']
        assert entry['commandMetadata']['kind'] == command['kind']
        assert pointer(metadata, entry['commandMetadata']['sourceRef']['jsonPointer']) == command
        assert command['handler'] == 'metadata-only; actual consumer binding required'
        check_span(entry['sourceCoordinates'])
        check_span(entry['lexicalOwner'])
        row.update(
            disposition='non-user-operation-source', sourceRoleConfirmed=True,
            sourceRole='command-metadata-declaration', proposedModule=entry['suggestedPackage'],
            commandId=command['id'], commandKind=command['kind'],
            roleEvidenceRef=ref('menu-command-contracts.json', f'/metadataRegistry/commands/{i}'),
            sameLiteralRegistrationRefs=registration_sites.get(command['id'], []),
            registrationJoin='literal-key-equality-only; not-operation-equivalence',
            retentionDecision='Maintain IDs, access/shortcut data and platform-specific descriptors as contracts; keep registration handlers in their owning application modules.',
            remainingWork='Verify effective registration context, handler behavior, access/mode consumers and runtime dispatch. A declaration is not an executed command.')
        if identifier in key_matches:
            row['literalKeyJoinRef'] = ref('command-consumer-contracts.json',
                                         f'/metadataKeyJoins/{key_matches[identifier][0]}')
    elif identifier in registration_index:
        i, relation = registration_index[identifier]
        for key in ['sourcePath', 'sourceHash', 'byteRange', 'spanHash']:
            assert entry['sourceCoordinates'][key] == relation['sourceCall'][key]
        assert relation['status'] == 'confirmed-original-program-registration-callee'
        assert relation['actualMountOrDispatchVerified'] is False
        check_span(relation['sourceCall'])
        check_span(relation['callee']['declaration'])
        row.update(
            disposition='partial-handler-registration', sourceRoleConfirmed=True,
            sourceRole='renderer-command-registration-call', commandId=relation['commandId'],
            registrationEvidenceRef=ref('command-registration-contracts.json', f'/legacyCandidateRelations/{i}'),
            retentionDecision='Retain the registration hook and its handler in the enclosing feature; do not replace the registration with metadata.',
            remainingWork='Establish effective mount/enabled context, complete handler/arguments, feature identity, mode and actual dispatch.')
    elif identifier == 'ROUTE-0152':
        mapping = scope['legacyEntryCoverage']['mappingUpdates'][0]
        assert mapping['entryId'] == identifier and mapping['entryCompletelyResolved'] is False
        row.update(
            disposition='partial-feature-container', sourceRoleConfirmed=True,
            featureIds=mapping['featureIds'],
            featureMappingRef=ref('feature-scope-v22.json', '/legacyEntryCoverage/mappingUpdates/0'),
            remainingWork='Container association is conditional; retained page receiver/mode/runtime and cross-entry behavior remain open.')
    else:
        row['remainingWork'] = 'Determine support/container/duplicate/user-operation role using existing contracts before proposing any new feature.'
    rows.append(row)

disposition_counts = dict(collections.Counter(row['disposition'] for row in rows))
assert disposition_counts == {'awaiting-disposition': 726, 'partial-feature-container': 1,
                              'non-user-operation-source': 235, 'partial-handler-registration': 6}
assert sum(disposition_counts.values()) == 968
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
counts = {
    'legacyEntryRecords': 968, 'nonUserOperationSourceRecords': 235,
    'settingsResourceDescriptors': 53, 'commandMetadataDeclarations': 182,
    'commandMetadataKinds': dict(collections.Counter(row['commandKind'] for row in rows if 'commandKind' in row)),
    'metadataRecordsWithSavedLiteralKeyJoin': 80,
    'partialHandlerRegistrations': 6, 'partialFeatureContainers': 1,
    'entriesAwaitingDisposition': 726, 'functionalEntriesFullyResolved': 0,
    'entriesWithoutFeatureMapping': 967,
    'dispositionCounts': disposition_counts,
    'featureDefinitionsAdded': 0, 'modeClassificationsChanged': 0,
    'productScenariosExecuted': 0, 'clientImplementationAdded': 0,
    'modelSubmissionsAdded': 0, 'originalClientRunsAdded': 0,
    'newReaRuns': 0, 'newFullProgramParses': 0,
}
result_path = OUT / 'legacy-entry-dispositions.json'
csv_path = OUT / 'legacy-entry-dispositions.csv'
summary_path = OUT / 'legacy-entry-dispositions.md'
dump(result_path, {
    'schemaVersion': 1, 'baselineId': BASE, 'recordedAtUtc': now,
    'scope': 'ID-level integration of saved source-role and registration-callee evidence; all 968 original records preserved.',
    'inputPins': list(inputs.values()), 'counts': counts,
    'accountingPolicy': {
        'sourceRole': '235 entries are declarations/resource descriptors, not independent user-operation definitions. They remain retained source responsibilities.',
        'featureMapping': '967 entries still have no feature mapping. Source-role disposition and callee identity do not reduce this functional mapping count.',
        'partialMappings': 'One conditional container maps 334 feature definitions; six other entries have confirmed registration callees but no feature identity.',
        'unknown': '726 entries have no disposition in this integration; this is not a count of missing user features.',
        'metadataJoin': '80 metadata records have saved literal-key matches to lexically verified registration calls. Equal keys do not establish operation equivalence or dispatch.',
        'maintenanceModules': 'Proposed paths describe first-party contract/resource responsibilities. Third-party implementations remain external package dependencies.',
    },
    'entries': rows,
    'frozenSourceValidation': {
        'files': [{'sourcePath': source, 'sourceHash': value[1], 'bytes': len(value[0])}
                  for source, value in sorted(files.items())],
        'uniqueSpansChecked': len(checked_spans),
        'qualification': 'Checks source coordinates for the 235 role decisions, six registration calls, their selected owners and the saved resource consumer; existing imported-consumer source contracts are reused.'},
    'fullAnalysisCompleted': False,
})
with csv_path.open('x', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=['entryId', 'entryKind', 'family', 'label',
                                            'disposition', 'sourceRoleConfirmed',
                                            'productMode', 'functionalEntryFullyResolved'])
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row[key] for key in writer.fieldnames})

scope['purpose'] = 'Finite feature ledger with separate legacy source-role dispositions and functional mapping accounting.'
scope['previousScopeRef'] = pin(OUT / 'feature-scope-v22.json')
scope['inheritedLedgerRef'] = pin(OUT / 'feature-scope-v22.json')
scope['newDefinitionIds'] = []
scope['legacyEntryDispositions'] = pin(result_path)
scope['legacyEntryCoverage']['dispositionRef'] = pin(result_path)
scope['legacyEntryCoverage']['dispositionCounts'] = disposition_counts
scope['legacyEntryCoverage']['qualification'] = (
    '334 conditional feature definitions in one container; 235 non-user-operation source roles and six registration-callee identities accounted for separately. '
    '726 entries await disposition. Functional mappings remain one partial container, 967 unmapped, zero fully resolved.')
scope['counts']['legacyEntriesWithDefinitiveNonUserRole'] = 235
scope['counts']['legacyEntriesWithConfirmedRegistrationCallee'] = 6
scope['counts']['legacyEntriesAwaitingDisposition'] = 726
scope_path = OUT / 'feature-scope-v23.json'
scope_csv = OUT / 'feature-scope-v23.csv'
dump(scope_path, scope)
with scope_csv.open('x', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['featureId', 'name', 'mode', 'operationCount', 'runtimeStatus', 'completeChainProven'])
    for feature in scope['features']:
        writer.writerow([feature['featureId'], feature['name'], feature['mode'], len(feature['operationMembers']),
                         feature['runtimeStatus'], str(feature['completeChainProven']).lower()])
coverage['recordedAtUtc'] = now
coverage['previousSnapshot'] = pin(OUT / 'restoration-coverage-v13.json')
coverage['featureLedger'] = pin(scope_path)
coverage['legacyEntryDispositions'] = pin(result_path)
coverage['unresolvedScope']['legacyEntryDispositionRef'] = pin(result_path)
coverage['unresolvedScope']['legacyEntryDispositionCounts'] = disposition_counts
for family in coverage['unresolvedScope']['legacyFamilies']:
    family['entryDispositionCounts'] = dict(collections.Counter(
        row['disposition'] for row in rows if row['family'] == family['family']))
for index, feature in enumerate(coverage['features']):
    feature['featureRef'] = pin(scope_path, f'/features/{index}')
coverage_path = OUT / 'restoration-coverage-v14.json'
dump(coverage_path, coverage)

summary_path.write_text('''# 旧入口的资源声明和注册调用归并

968 条原入口记录全部保留并按原 ID 接入当前台账。235 条已确定是支撑源码记录：53 条设置图标与导航资源描述、182 条命令声明；另有 6 条 renderer 命令注册调用已接到确定的注册函数。它们不再作为无角色线索重复调查。

| 处置 | 原记录数 | 当前结论 |
| --- | ---: | --- |
| 资源描述和命令声明 | 235 | 角色已确认，按资源表或命令契约维护 |
| 命令注册调用 | 6 | 注册函数身份已确认，处理函数和实际挂载仍待核对 |
| 设置路由容器 | 1 | 既有 334 项功能的条件关联保留 |
| 待处置 | 726 | 继续区分支撑、容器、重复入口和用户操作 |

来源角色和功能映射分别计数。原来没有功能映射的 967 条仍是 967 条，完整功能链关闭数仍为 0；726 是待明确角色的记录数，不能当作缺失功能数。现有 340 项功能、344 项用户操作、103 项支撑操作和 1117 条未执行场景规格均保持不变。

设置资源表按键返回 component、commandAsset 和 navigation，并对两个条件分支作特殊处理。它可维护为 `apps/desktop/renderer/resources/settings`；真实设置页面继续按已确认的页面工厂和消费者维护。命令声明可维护为 `packages/command-contracts`，保存命令 ID、平台描述、访问与快捷键数据，处理函数仍放在所属应用模块。这些是已有来源支持的包边界建议，第三方图标和库实现通过包依赖引入。

182 条命令声明包括 153 条 webview、21 条 electron-only、8 条 vscode-only；平台类别不等于产品模式。其中 80 条已有静态命令键与注册调用的精确匹配，逐条连接已保存。匹配键只能帮助找到注册位置，不能证明两个入口行为相同或命令已实际执行。

本次复用既有完整 Program 分析，并核对所采纳角色和注册调用的冻结源码范围。没有新增产品行为通过项；模式仍为 shared 1、unknown 339。原九项完成标准仍有五项部分完成。

[逐 ID 机器清单](legacy-entry-dispositions.json)和[CSV](legacy-entry-dispositions.csv)已接入[功能台账 v23](feature-scope-v23.json)、[恢复覆盖表 v14](restoration-coverage-v14.json)及[当前状态](analysis-state.json)。下一步完成已选定的三个设置合同，再按原九项标准核验当前成果，避免继续新增页面调查范围。
''')

state['updatedAtUtc'] = now
view = state['featureScopeCurrentView']
view.update(snapshotVersion=23, ledger=pin(scope_path), csv=pin(scope_csv),
            previousLedger=pin(OUT / 'feature-scope-v22.json'), counts=scope['counts'],
            reconciliationKind='legacy-source-role-and-registration-callee-accounting',
            reconciliationArtifact=pin(result_path))
view['legacyEntryDispositionOverlay'] = pin(result_path)
state['restorationCoverage'] = {**pin(coverage_path), 'scope': 'All 340 definitions and 1117 unexecuted specifications; legacy role dispositions separate from functional mappings.'}
state['legacyEntryDispositions'] = {'result': pin(result_path), 'summary': pin(summary_path),
                                    'csv': pin(csv_path), 'counts': counts,
                                    'fullAnalysisCompleted': False}
for overlay in [state['analysisMilestones']['currentScopeOverlay'], state['stageDecisions']['currentScopeOverlay']]:
    overlay['featureLedger'] = pin(scope_path)
    overlay['legacyEntryDispositions'] = pin(result_path)
    overlay['coverage' if 'coverage' in overlay else 'restorationCoverage'] = pin(coverage_path)
state['stageDecisions']['legacyEntryDispositionOverlay'] = state['legacyEntryDispositions']
state['stageDecisions']['counts'].update(
    legacyNonUserOperationSourceRecords=235, legacyPartialRegistrationCalls=6,
    legacyEntriesAwaitingDisposition=726, legacyEntriesWithoutFeatureMapping=967)
state['stageDecisions']['nextAction'] = {
    'issueId': 'SD-01/SD-02/SD-06',
    'completedSubstep': 'All 968 original IDs reconciled. Integrated 235 confirmed non-user-operation source roles and six confirmed registration-callee identities; one existing partial container retained. No functional chain or mode closure claimed.',
    'fixedInput': 'The three already-selected settings contracts in settings-final-batch15-work; current scope v23, scenarios v21 and restoration coverage v14. No new page families.',
    'question': 'What controls, state changes, delegated boundaries and conditions are already selected for cloud-environments, personalization and codex-micro?',
    'closure': 'Publish their existing source contracts and operation/acceptance mapping, then audit the original nine criteria against current evidence. Keep unknown mode and actual runtime/service verification explicit.',
    'deferredDedicatedVerification': '726 legacy records await role disposition; 967 have no feature mapping. These are separate accounting axes. Further model submissions have no remaining authorization; offline work remains available.'}

prefix = ('当前以[状态文件](analysis-state.json)和[旧入口归并](legacy-entry-dispositions.md)为准。'
          '[台账v23](feature-scope-v23.json)保持340项有限定义、344项用户操作、103项支撑和1117条未执行规格，'
          '接到[恢复覆盖表v14](restoration-coverage-v14.json)的T01至T45。模式仍为shared 1、unknown 339；完整产品分母未知。\n\n'
          '968条原记录中，235条支撑源码角色已确认，6条注册函数身份已确认，1条保留既有部分容器关联，726条待处置。'
          '来源角色与功能映射分开计数：967条仍无功能映射，完整功能链关闭数仍为0。'
          '三个已选定设置合同待交付；原九项标准仍为4项资料或范围义务有交付、5项部分完成。客户端实现尚未开始。以下旧数量与下一行动为历史记录。\n\n')
for name in ['report.md', 'gaps.md']:
    path = OUT / name
    text = path.read_text()
    start, end = text.index('当前以'), text.index('其他当前恢复决定：')
    path.write_text(text[:start] + prefix + text[end:])
path = ROOT / 'README.md'
text = path.read_text()
start, end = text.index('当前为逆向分析阶段。'), text.index('- [当前分析状态与下一行动]')
relative = f'analysis/{BASE}/'
text = text[:start] + (
    f'当前为逆向分析阶段。[旧入口归并]({relative}legacy-entry-dispositions.md)保留全部968个原ID，'
    '将235条资源／命令声明和6条确定的注册调用接入当前台账。来源角色与功能映射分别计数，仍有726条待处置、967条无功能映射。\n\n'
    f'[台账v23]({relative}feature-scope-v23.json)保持340项有限定义、1117条未执行规格，'
    f'接到[恢复覆盖表v14]({relative}restoration-coverage-v14.json)的T01至T45。shared 1、unknown 339；'
    '45个设置容器中42个已有局部合同、3个已选定待完成。原九项标准仍有5项部分完成，客户端实现尚未开始。\n\n'
) + text[end:]
text = text.replace('当前功能台账为v22，完整产品分母未知。', '当前功能台账为v23，完整产品分母未知。')
path.write_text(text)

# Preserve behavior authorization, features, deferred queues and sibling decisions.
assert scope['features'] == old_scope['features']
for key in ['supportOperations', 'operationReviewQueue', 'operationContainers',
            'rootCandidateDispositions', 'retainedAssociationBacklog',
            'pageContainerRelations', 'legacyFeatureRelations', 'crossFeatureOverlapReviews']:
    assert scope[key] == old_scope[key], key
for key in ['fullyResolvedLegacyEntries', 'partiallyMappedLegacyContainers',
            'legacyEntriesUnmappedInThisLedger', 'modeCounts']:
    assert scope['counts'][key] == old_scope['counts'][key], key
assert coverage['taskGroups'] == old_coverage['taskGroups']
assert coverage['scenarioLedger'] == old_coverage['scenarioLedger']
assert coverage['counts'] == old_coverage['counts']
for key in ['latestBehaviorAuthorizationState', 'settingsOperationCoverage',
            'desktopAccessPublication', 'modeOwnershipReconciliation']:
    assert state[key] == old_state[key], key
for key in ['latestConsolidation', 'runtimeBoundaryOverlay', 'productFlowOwnershipOverlay',
            'browserCloneRouteOverlay', 'publicHistoryDuplicateOverlay',
            'accountAccessPublicationOverlay', 'modeOwnershipOverlay']:
    assert state['stageDecisions'][key] == old_state['stageDecisions'][key], key
assert all(sha(OUT / name) == digest for name, digest in input_hashes.items())
(OUT / 'analysis-state.json').write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
dump(WORK / 'publication-receipt.json', {
    'recordedAtUtc': now, 'inputHashes': input_hashes,
    'outputs': [pin(path) for path in [result_path, csv_path, summary_path, scope_path, scope_csv, coverage_path]],
    'sourceValidation': {'files': len(files), 'uniqueSpans': len(checked_spans)},
    'counts': counts, 'fullAnalysisCompleted': False})
print(json.dumps({'status': 'published', 'counts': counts,
                  'sourceFilesChecked': len(files), 'sourceSpansChecked': len(checked_spans),
                  'updatedAtUtc': now}, ensure_ascii=False))
