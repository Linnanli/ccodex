"""Publish lexical ownership groups without turning mechanisms into features."""
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASELINE
WORK = ROOT / '.analysis-local/entry-family-work'
RAW = OUT / 'raw/entry-families'


def read(path):
    return json.loads(path.read_text())


def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n')


def pin(path):
    data = path.read_bytes()
    return {'path': os.path.relpath(path, OUT), 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest()}


FAMILIES = {
    'renderer-routes': ('renderer', '路由构造', 'apps/desktop/renderer/app/routes',
                        ['route-construction']),
    'renderer-navigation': ('renderer', '导航和重定向', 'apps/desktop/renderer/app/navigation',
                            ['navigate-component-target']),
    'route-conversion': ('renderer', '路由表转换', 'apps/desktop/renderer/app/routes',
                         ['route-conversion-consumer']),
    'command-metadata': ('shared-desktop-command-data', '命令元数据', 'packages/command-contracts',
                         ['command-metadata-instance']),
    'native-menus': ('main', '原生菜单装配', 'apps/desktop/main/menus',
                     ['application-menu-factory', 'application-menu-consumer', 'native-menu-api',
                      'native-menu-schema', 'native-menu-generator-options']),
    'host-dispatch': ('main', '宿主消息分发', 'apps/desktop/main/app-host',
                      ['host-top-level-message-case']),
    'backend-calls': ('desktop-bundle', '后台调用候选', 'packages/backend-adapter',
                      ['app-server-direct-call-lexical-candidate']),
    'ipc-channels': ('mixed', 'IPC 通道候选', 'packages/contracts/ipc',
                     ['ipc-source-channel-lexical-candidate']),
    'settings-resources': ('renderer', '设置图标和导航资源描述', 'apps/desktop/renderer/resources/settings',
                           ['settings-section-lexical-candidate']),
    'shortcut-and-renderer-registration': ('mixed', '快捷键及 renderer 注册', 'packages/command-contracts',
                                          ['os-global-native-registration', 'os-global-wrapper-consumer',
                                           'before-input-event-registration', 'renderer-hook-scope',
                                           'renderer-command-registration-candidate',
                                           'renderer-message-subscription-candidate']),
}
KIND_TO_FAMILY = {kind: key for key, (_, _, _, kinds) in FAMILIES.items() for kind in kinds}


def pointer(doc, text):
    for key in text.lstrip('/').split('/'):
        key = key.replace('~1', '/').replace('~0', '~')
        doc = doc[int(key)] if isinstance(doc, list) else doc[key]
    return doc


def main():
    assert not RAW.exists(), 'Do not overwrite an existing publication'
    names = ['entry-family-map.json', 'entry-family-map.csv', 'entry-family-evidence.jsonl',
             'entry-family-summary.md', 'entry-family-provenance.json']
    assert all(not (OUT / name).exists() for name in names)
    ledger_path = OUT / 'functional-entry-ledger.json'
    ledger = read(ledger_path)
    state = read(OUT / 'analysis-state.json')
    before = deepcopy(state)
    source_docs = sorted((WORK / 'run-01').glob('*-source.json'))
    assert len(source_docs) == 9
    programs = [read(path) for path in source_docs]
    rows = {row['entryId']: (program, index, row) for program in programs
            for index, row in enumerate(program['entries'])}
    assert len(rows) == len(ledger['entries']) == 968
    assert set(rows) == {e['entryId'] for e in ledger['entries']}
    assert all(p['ledger'] == {k: pin(ledger_path)[k] for k in ['bytes', 'sha256']}
               and p['fullProgramParsed'] and p['parserErrors'] == 0 and not p['targetCodeExecuted']
               for p in programs)
    table = read(WORK / 'settings-table.json')
    assert len(table['relations']) == 53 and table['confirmedSettingsPanelsAdded'] == 0
    resources = {r['entryId']: r for r in table['relations']}
    route_path = ROOT / '.analysis-local/feature-work/route-contracts.json'
    menu_path = ROOT / '.analysis-local/entry-work/menu-command-contracts.json'
    route, menu = read(route_path), read(menu_path)
    routes = {r['id']: r for r in route['registrations']}
    commands = {r['contractId']: r for r in menu['metadataRegistry']['commands']}
    assert len(routes) == 170 and len(commands) == 182
    for artifact, path in [('route', route_path), ('menu', menu_path)]:
        old = next(x for x in ledger['sourceArtifacts'] if x['artifactId'] == artifact)
        assert pin(path)['sha256'] == old['sha256']

    # Source-coordinate checks cover every new AST locator, not just sample rows.
    manifest = {r['archivePath']: r for r in read(OUT / 'files.json')['archiveFiles']}
    source_cache = {}
    checked = set()

    def verify(obj):
        if isinstance(obj, dict):
            if all(k in obj for k in ['sourcePath', 'sourceHash', 'byteRange', 'spanHash']) and obj['spanHash']:
                rel = obj['sourcePath'].removeprefix('app.asar/')
                if rel not in source_cache:
                    source_cache[rel] = (ROOT / '.analysis-local/baselines' / BASELINE / 'extracted' / rel).read_bytes()
                    assert hashlib.sha256(source_cache[rel]).hexdigest() == manifest[rel]['sha256']
                data = source_cache[rel]
                a, z = obj['byteRange']['start'], obj['byteRange']['endExclusive']
                assert obj['sourceHash'] == manifest[rel]['sha256'] and 0 <= a < z <= len(data)
                identity = (rel, a, z, obj['spanHash'])
                if identity not in checked:
                    assert hashlib.sha256(data[a:z]).hexdigest() == obj['spanHash']
                    checked.add(identity)
            for value in obj.values():
                verify(value)
        elif isinstance(obj, list):
            for value in obj:
                verify(value)

    for program in programs:
        verify(program)
    verify(table)
    records, evidence, owner_groups = [], [], {}
    source_refs = {p['sourcePath']: f'raw/entry-families/{source_docs[i].name}' for i, p in enumerate(programs)}
    for entry in ledger['entries']:
        program, index, row = rows[entry['entryId']]
        assert row['entryKind'] == entry['entryKind'] and row['originalSourceCoordinates'] == entry['sourceCoordinates']
        family = KIND_TO_FAMILY[entry['entryKind']]
        environment, title, package, _ = FAMILIES[family]
        owner = row['outerBinding']
        group_key = (family, program['sourcePath'], owner['byteRange']['start'] if owner else None,
                     owner['byteRange']['endExclusive'] if owner else None)
        group_id = 'EFG-' + hashlib.sha256(json.dumps(group_key).encode()).hexdigest()[:20]
        if group_id not in owner_groups:
            owner_groups[group_id] = {'groupId': group_id, 'family': family, 'sourcePath': program['sourcePath'],
                                     'lexicalOwner': owner, 'entryIds': [], 'entryCount': 0,
                                     'productMode': 'unknown', 'stateOwner': 'not-established-by-this-analysis',
                                     'suggestedPackage': package, 'packageStatus': 'maintenance-proposal'}
        owner_groups[group_id]['entryIds'].append(entry['entryId'])
        owner_groups[group_id]['entryCount'] += 1
        evidence_id = 'ENTRY-FAMILY-' + hashlib.sha256(entry['entryId'].encode()).hexdigest()[:20]
        ev = row['freshlyHashedSourceSpan']
        evidence.append({'id': evidence_id, 'baselineId': BASELINE,
                         'claim': f"{entry['entryId']} 属于{title}分析组；原范围已在完整 Program 中定位，源码词法所有者及结构条件见对应 AST 记录。此归组不证明产品模式、业务状态所有者或用户操作等价。",
                         'sourcePath': ev['sourcePath'], 'sourceHash': ev['sourceHash'],
                         'locator': {'kind': 'byte-range', **ev['byteRange']}, 'spanHash': ev['spanHash'],
                         'method': 'static-code', 'confidence': 'confirmed',
                         'verificationStatus': 'full-program-ast-ownership; actual-runtime-and-product-scope-pending',
                         'astRef': {'path': source_refs[program['sourcePath']], 'jsonPointer': f'/entries/{index}'}})
        record = {'entryId': entry['entryId'], 'entryKind': entry['entryKind'], 'family': family,
                  'groupId': group_id, 'displayLabel': entry['displayLabel'], 'evidenceId': evidence_id,
                  'sourceCoordinates': ev, 'lexicalOwner': owner,
                  'nearestCallable': row['lexicalCallable'], 'lexicalClass': row['lexicalClass'],
                  'astRef': evidence[-1]['astRef'], 'exactOriginalAstRange': row['exactAstRange'],
                  'structuralGuardCount': len(row['structuralGuards']),
                  'directCallableGuardCount': sum(g['insideNearestCallable'] for g in row['structuralGuards']),
                  'environmentProposal': environment, 'actualRuntimeVerified': False,
                  'productMode': 'unknown', 'stateOwner': 'not-established-by-this-analysis',
                  'featureId': entry['featureId'], 'featureAssociationStatus': entry['featureAssociationStatus'],
                  'originalEvidenceIds': entry['evidenceIds'],
                  'preservedReviewedContractLinkIds': entry.get('reviewedContractLinkIds', []),
                  'suggestedPackage': package}
        if entry['entryId'] in resources:
            record['roleCorrection'] = resources[entry['entryId']]
        if entry['entryId'] in commands:
            cmd = commands[entry['entryId']]
            record['commandMetadata'] = {'id': cmd['id'], 'kind': cmd['kind'],
                                         'requiredAccess': cmd['requiredAccess'],
                                         'shortcutScope': cmd['shortcutScope'],
                                         'handlerStatus': 'metadata-is-not-handler-registration',
                                         'sourceRef': entry['sourceArtifact']}
        if entry['entryId'] in routes:
            registration = routes[entry['entryId']]
            record['routeTopology'] = {key: registration[key] for key in
                                       ['parentRouteIds', 'ancestorRouteIds', 'conversionConsumerIds',
                                        'enclosingConditions', 'enclosingRouteConditions', 'guardReviewIds']}
            record['routeTopology']['guardNoteCaveat'] = 'Inherited note association can name a component family; it is not proof that every note condition gates this route.'
        records.append(record)
    assert len(records) == len(evidence) == 968
    families = []
    for key, (env, title, package, _) in FAMILIES.items():
        selected = [r for r in records if r['family'] == key]
        families.append({'family': key, 'name': title, 'entryCount': len(selected),
                         'ownerGroups': [g['groupId'] for g in owner_groups.values() if g['family'] == key],
                         'environmentProposal': env, 'suggestedPackage': package,
                         'productMode': 'unknown', 'additionalFeatureCountClaimed': 0})
    counts = {'legacyRecordsPreserved': 968, 'sourceFiles': 9, 'fullProgramParses': 10,
              'parsedAstNodes': sum(p['nodeCount'] for p in programs)+table['nodeCount'],
              'exactOriginalAstRanges': sum(p['exactAstMatches'] for p in programs),
              'containedLexicalRanges': sum(not row['exactAstRange'] for _, _, row in rows.values()),
              'mechanismFamilies': len(families), 'lexicalOwnerGroups': len(owner_groups),
              'settingsResourceCorrections': len(resources), 'commandMetadataRecords': len(commands),
              'commandKinds': dict(Counter(c['kind'] for c in commands.values())),
              'sourceFacts': len(evidence), 'uniqueSourceSpansChecked': len(checked),
              'newFeatureDefinitions': 0, 'newConfirmedModeClassifications': 0,
              'newChatGptExclusions': 0, 'newActualBehaviorVerifications': 0,
              'modelSubmissionsAdded': 0, 'originalClientRunsAdded': 0, 'newReaRuns': 0}
    assert counts['exactOriginalAstRanges'] == 824 and counts['containedLexicalRanges'] == 144
    assert sum(f['entryCount'] for f in families) == 968
    assert all(p['parserErrors'] == 0 for p in programs)
    next_actions = [
        {'id': 'EF-NEXT-commands', 'family': 'command-metadata',
         'question': '将 MG 的命令描述、6个 renderer 注册候选和原生菜单消费者按真实绑定连接，分别核对 codexLocal/codexOrWorkLocal 的访问条件；缺省字段不等于无访问限制。',
         'closure': '每个注册消费者有来源身份和条件；元数据、handler、平台和产品模式分别记录，不能按 id/title 合并功能。'},
        {'id': 'EF-NEXT-routes', 'family': 'renderer-routes',
         'question': '按 ZIs 的三次路由转换和已有父子关系核对页面族的实际 mount 与 guard；新增功能候选须包含具体用户目标。',
         'closure': '路由构造、layout、redirect、索引和用户操作分别计数；继承 guard note 不自动扩大到同名组件的全部路由。'},
        {'id': 'EF-NEXT-settings', 'family': 'settings-resources',
         'question': '以真实 panel 注册/可见性消费者确定设置范围，保留这53条资源表映射，不再用资源 key 充当设置功能分母。',
         'closure': '设置 panel 与图标/导航描述有实际连接；不影响当前48项用户功能及其未知模式。'},
        {'id': 'EF-NEXT-runtime', 'family': None,
         'question': 'A2继续按已知 Owl/原生接口能力与独立取得方式作构建决定；入口词法归组不解决运行时取得或ABI。',
         'closure': '每项能力给出可取得输入或替代契约，明确受影响功能；不以归组完成替代独立构建依据。'},
    ]
    result = {'schemaVersion': 1, 'baselineId': BASELINE, 'purpose': 'Legacy entry mechanism and lexical-ownership map; not a product feature census.',
              'sourceLedger': pin(ledger_path), 'counts': counts, 'families': families,
              'ownerGroups': list(owner_groups.values()), 'entries': records, 'nextActions': next_actions,
              'completeFeatureDenominator': None, 'currentFeatureScopeUnchanged': state['featureScopeCurrentView']['ledger'],
              'analysisCompletionClaimed': False,
              'scopeLimits': ['Environment and package paths are maintenance proposals, not proof of actual process instances or original source directories.',
                              'Lexical owner is not the business state owner, implementation ownership or a cross-release module identity.',
                              'Structural guards preserve function-boundary distinctions; guard values and actual reachability were not executed.',
                              'All original entries, links and 337 deferred candidates remain in the frozen ledger; no product function was removed.',
                              '53 settings resources and 182 command metadata records cannot be counted as that many independently implemented user operations.',
                              'No new REA command was run; complete-Program AST supplements the preserved REA and entry evidence.']}

    RAW.mkdir(parents=True)
    for path in source_docs:
        shutil.copyfile(path, RAW / path.name)
    shutil.copyfile(WORK / 'settings-table.json', RAW / 'settings-table.json')
    shutil.copyfile(WORK / 'run-01/receipts.json', RAW / 'receipts.json')
    for name in ['analyze_entry_families.py', 'entry_family_ast.mjs']:
        shutil.copyfile(WORK / 'run-01' / name, RAW / name)
    for name in ['entry_family_tables.mjs', 'publish_entry_families.py']:
        shutil.copyfile(ROOT / 'scripts/analysis' / name, RAW / name)
    write(RAW / 'analysis-state-before.json', before)
    for name in ['README.md', 'report.md', 'gaps.md']:
        source = ROOT / name if name == 'README.md' else OUT / name
        shutil.copyfile(source, RAW / ('before-'+name))
    write(OUT / names[0], result)
    (OUT / names[2]).write_text(''.join(json.dumps(e, ensure_ascii=False)+'\n' for e in evidence))
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(['entryId', 'kind', 'family', 'ownerGroup', 'lexicalOwner', 'proposedEnvironment',
                     'productMode', 'stateOwner', 'exactAstRange', 'directGuardCount', 'displayLabel'])
    for r in records:
        writer.writerow([r['entryId'], r['entryKind'], r['family'], r['groupId'],
                         (r['lexicalOwner'] or {}).get('name'), r['environmentProposal'], r['productMode'],
                         r['stateOwner'], r['exactOriginalAstRange'], r['directCallableGuardCount'], r['displayLabel']])
    (OUT / names[1]).write_text(stream.getvalue())
    table_rows = '\n'.join(f"| {f['name']} | {f['entryCount']} | {len(f['ownerGroups'])} |" for f in families)
    summary = f'''# 旧入口分组与源码所有者映射

基线 `{BASELINE}`。本次将原台账的968条记录全部定位到9个完整原始Program，分成10类机制、{len(owner_groups)}个词法所有者组。[机器清单](entry-family-map.json)、[CSV](entry-family-map.csv)和[来源记录](entry-family-evidence.jsonl)保留全部原入口ID。没有新增模型请求或操作原客户端。

## 会改变后续分析的结论

原“settings-section-lexical-candidate”的53条全部是 `ua` 表的属性。完整Program中只有一个顶层 `ua` 声明、一处赋值和一处读取；`la(e,t)`按key返回 `component`、`commandAsset`、`navigation`资源描述，并对cloud-environments及Windows appshots作特例。53条都不是设置panel注册证明，不能作为设置功能分母。对应源范围和导出保存于[表分析](raw/entry-families/settings-table.json)。后续设置盘点应以真实panel及可见性消费者为入口。

182条命令元数据的源码所有者为 `MG`、`kG`、`AG`。原完整注册合同将其分为153条webview、21条electron-only、8条vscode-only；后两者通过 `NG`附加kind并展开到MG。平台kind不等于产品模式，元数据不是handler注册。它们的命令ID、requiredAccess、shortcutScope和原合同指针逐条保留，下一项按真实注册消费者批量连接。

170个路由构造仍归 `ZIs` 初始化函数，三个转换消费者、47个导航目标分别登记。父子关系、构造条件和原guard note关联保留；layout、redirect、资源或协议分支不能逐条当成用户功能。143个宿主消息case归同一个 `MMe.handleMessage`，实际状态/接收实例仍须沿具体功能合同证明。

## 分组

| 机制 | 原记录 | 词法所有者组 |
| --- | ---: | ---: |
{table_rows}

词法所有者表示源码内包含该范围的外层绑定，不能代替业务状态所有者或运行实例。清单的环境与拟议包路径是维护设计建议；`productMode`保持unknown。

## 核验与后续

9个不同源码文件进行了9次完整Program解析，设置小文件补充解析1次；共{counts['parsedAstNodes']:,}个AST节点。824条原范围恰好对应完整节点，余144条是原词法范围：91条位于完整调用中，53条位于资源ObjectProperty中。没有把这些词法片段改称完整节点。{counts['uniqueSourceSpansChecked']}个不同源码范围的哈希经冻结文件核对。

本次关闭“旧入口缺少统一源码所有者分组”和“53个设置词法候选究竟是什么”两项限定问题。用户功能定义仍为48项，212条功能验收规格仍未执行；旧台账的功能关联、模式、337条deferred及实际行为缺口没有因分组而减少。完整功能分母继续未知，分析未完成。

下一步按[清单中的nextActions](entry-family-map.json)连接命令注册消费者及访问条件，同时推进A2的运行时/依赖决定。设置改从panel消费者盘点。这些组用作有限工作批次；不重复调查已定位的归档、resume、fork和start入口。[实施计划v6](implementation-plan-v6.md)和[原分析计划](../../docs/reverse-engineering/analysis-plan.md)继续有效。
'''
    (OUT / names[3]).write_text(summary)
    index = {'schemaVersion': 1, 'baselineId': BASELINE,
             'publishedAtUtc': datetime.now(timezone.utc).isoformat(),
             'outputs': [pin(OUT / name) for name in names[:-1]],
             'rawArtifacts': [pin(p) for p in sorted(RAW.iterdir()) if p.is_file()],
             'inputs': [pin(ledger_path), pin(OUT / 'files.json'), pin(route_path), pin(menu_path)],
             'counts': counts, 'fullAnalysisCompleted': False, 'clientImplementationAdded': False}
    write(OUT / names[4], index)
    state['updatedAtUtc'] = index['publishedAtUtc']
    state['entryFamilyMap'] = {'provenance': pin(OUT / names[4]), 'map': pin(OUT / names[0]),
                               'summary': pin(OUT / names[3]), 'counts': counts,
                               'nextAction': next_actions[0], 'fullAnalysisCompleted': False}
    assert {k for k in before if before[k] != state[k]} == {'updatedAtUtc'}
    assert set(state)-set(before) == {'entryFamilyMap'}
    write(OUT / 'analysis-state.json', state)
    paragraph = f'\n[旧入口分组](entry-family-summary.md)已将968条记录定位到9个完整Program，建立10类机制和{len(owner_groups)}个词法所有者组；53条旧设置候选确认为图标/导航资源描述，182条命令元数据仍与handler注册分开。该结果改变下一批盘点入口，不增加用户功能、模式分类或真实行为通过数。\n'
    for name in ['report.md', 'gaps.md']:
        path = OUT / name
        lines = path.read_text().splitlines(keepends=True)
        lines.insert(1, paragraph)
        path.write_text(''.join(lines))
    path = ROOT / 'README.md'
    lines = path.read_text().splitlines(keepends=True)
    lines.insert(1, '\n最新入口分析见[旧入口分组](analysis/'+BASELINE+'/entry-family-summary.md)：968条源码记录已分组，53条旧设置候选确认为资源描述。功能分母与运行验证仍待完成。\n')
    path.write_text(''.join(lines))
    for path in [*(OUT / name for name in names), *RAW.iterdir()]:
        if path.is_file():
            path.chmod(0o444)
    print(json.dumps({'published': True, **counts}, ensure_ascii=False))


if __name__ == '__main__':
    main()
