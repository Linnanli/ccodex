"""Publish a bounded full-Program registration census and preserve its unknowns."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASELINE
WORK = ROOT / '.analysis-local/entry-command-work'
RAW = OUT / 'raw/command-registration'


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def pin(path):
    data = path.read_bytes()
    return {'path': os.path.relpath(path, OUT), 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest()}


def main():
    names = ['command-registration-contracts.json', 'command-registration-summary.md',
             'command-registration-provenance.json']
    assert not RAW.exists() and all(not (OUT / x).exists() for x in names)
    initial = read(WORK / 'commands-01/source-contracts.json')['program']
    inventory = read(WORK / 'inventory-01/source-contracts.json')['program']
    for stage in ['analyze-commands-01', 'analyze-inventory-01']:
        receipt = read(WORK / 'attempts' / stage / 'receipt.json')
        assert receipt['exitCode'] == 0 and receipt['sourcesUnchanged']
    assert initial['parserErrors'] == inventory['parserErrors'] == 0
    assert initial['sha256'] == inventory['sha256'] == '604b5d2de4fbb41f3d0dc5b3662129c558e1c7b8aac8cc87225286f58dcfaf8f'
    units = {u['name']: u for u in inventory['selectedUnits']}
    registration = units['definition-Pw']
    registry = units['definition-Pqt']
    dispatcher = next(u for u in inventory['selectedUnits'] if u['name'] == 'registry-reference-owner-dJt-Lqt')
    calls = inventory['calleeInventory']
    assert len(calls) == 49
    assert {e['exported'] for e in inventory['exports'] if e['local'] == 'Pw'} == {'IBn'}
    assert Counter(x['name'] for x in inventory['programReferenceInventory'])['Pw'] == 49
    assert all(c['calleeDefinition']['spanHash'] == registration['spanHash'] for c in calls)
    calls_by_range = {(c['call']['byteRange']['start'], c['call']['byteRange']['endExclusive']): c for c in calls}
    ledger = read(OUT / 'functional-entry-ledger.json')
    legacy = [e for e in ledger['entries'] if e['entryKind'] == 'renderer-command-registration-candidate']
    assert len(legacy) == 6
    relations = []
    for entry in legacy:
        r = entry['sourceCoordinates']['byteRange']
        call = calls_by_range[(r['start'], r['endExclusive'])]
        matches = [b for b in initial['bindings'] if b['name'] == 'Pw'
                   and b['reference']['byteRange'] == call['calleeReference']['byteRange']]
        assert len(matches) == 1 and matches[0]['scopeKind'] == 'Program'
        assert matches[0]['declaration']['spanHash'] == registration['spanHash']
        relations.append({'entryId': entry['entryId'], 'sourceCall': call['call'],
                          'commandId': call['commandId'], 'callee': matches[0],
                          'status': 'confirmed-original-program-registration-callee',
                          'actualMountOrDispatchVerified': False})
    binding_units = {}
    for symbol in ['Rqt', 'Oqt']:
        defs = {b['declaration']['spanHash']: b['declaration'] for b in inventory['bindings']
                if b['name'] == symbol and b['scopeKind'] == 'Program'}
        assert len(defs) == 1
        binding_units[symbol] = next(iter(defs.values()))
    data = Path(inventory['localSource']).read_bytes()
    checked = set()

    def verify(obj):
        if isinstance(obj, dict):
            if all(k in obj for k in ['sourcePath', 'sourceHash', 'byteRange', 'spanHash']):
                if obj['sourcePath'] == inventory['sourcePath']:
                    a, z = obj['byteRange']['start'], obj['byteRange']['endExclusive']
                    assert obj['sourceHash'] == inventory['sha256'] and 0 <= a < z <= len(data)
                    identity = (a, z, obj['spanHash'])
                    if identity not in checked:
                        assert hashlib.sha256(data[a:z]).hexdigest() == obj['spanHash']
                        checked.add(identity)
            for v in obj.values():
                verify(v)
        elif isinstance(obj, list):
            for v in obj:
                verify(v)

    verify(initial)
    verify(inventory)
    assets = ROOT / '.analysis-local/baselines' / BASELINE / 'extracted/webview/assets'
    command = ['rg', '-l', '--glob', '*.js', r'\bIBn\b', str(assets)]
    found = subprocess.run(command, cwd=ROOT, capture_output=True)
    assert found.returncode == 0
    candidates = []
    import_pattern = re.compile(r'import\s*\{([^{}]*)\}\s*from\s*[\x22\x27]\./app-initial-6350d04672d0\.js[\x22\x27]')
    for filename in found.stdout.decode().splitlines():
        file = Path(filename)
        if file.name == inventory['file']:
            continue
        source = file.read_bytes()
        text = source.decode()
        for match in import_pattern.finditer(text):
            for spec in match.group(1).split(','):
                parts = spec.strip().split()
                if not parts or parts[0] != 'IBn':
                    continue
                assert len(parts) in [1, 3]
                a = len(text[:match.start()].encode())
                z = len(text[:match.end()].encode())
                candidates.append({'sourcePath': 'app.asar/webview/assets/'+file.name,
                                   'sourceHash': hashlib.sha256(source).hexdigest(), 'sourceBytes': len(source),
                                   'imported': 'IBn', 'localNameCandidate': parts[-1],
                                   'locator': {'kind': 'byte-range', 'start': a, 'endExclusive': z},
                                   'spanHash': hashlib.sha256(source[a:z]).hexdigest(),
                                   'method': 'lexical-discovery', 'confidence': 'unresolved',
                                   'verificationStatus': 'complete-program-import-and-call-binding-review-pending'})
    assert len(candidates) == 24
    facts = []

    def fact(claim, source):
        facts.append({'id': f'COMMAND-REGISTRATION-{len(facts)+1:03}', 'baselineId': BASELINE,
                      'claim': claim, 'sourcePath': source['sourcePath'], 'sourceHash': source['sourceHash'],
                      'locator': {'kind': 'byte-range', **source['byteRange']}, 'spanHash': source['spanHash'],
                      'method': 'static-code', 'confidence': 'confirmed',
                      'verificationStatus': 'selected-source-contract; actual-mount-store-and-dispatch-pending'})

    fact('旧6个renderer命令注册候选的callee都解析到同一个原Program函数Pw；片段分析中的外部callee身份未知在此限定范围内关闭。', registration)
    fact('完整app-initial Program中有49处直接调用同一Pw绑定；其中47处首参数为静态字符串，共44个不同字符串，2处动态首参数仍未知。旧6处为其子集，另有43处直接调用；这不是43个新用户功能。', registration)
    fact('Pw第三参未提供时取空options，enabled默认启用，priority默认normal；isActive包装默认true。useEffect在enabled为falsy时不登记，否则调用Pqt并写Nqt；返回cleanup先注销Pqt登记，再移除Nqt对应对象。实际React、store和挂载未执行。', registration)
    fact('Pw的键盘事件分支先调用keyboardHandler：严格false返回false，严格true直接返回undefined；否则有contextHandler时按其严格false决定结果，缺省调用普通handler。普通handler的返回值没有被return或await，不能用它返回的Promise判断消费完成。同步异常没有本地catch。', registration)
    fact('Pqt把handler/isActive/priority对象追加到同一命令ID的数组，返回按该对象身份lastIndexOf清理的函数；空数组删除key。相同命令ID允许并存多个handler，不能据ID合并语义。', registry)
    fact('Lqt依次检查normal、fallback优先级，同级按注册数组逆序检查；isActive为truthy且handler结果不严格等于false时返回true。未消费时查询Rqt默认handler，并按默认handler结果判断；没有await，实际异常和异步完成不在此处处理。', dispatcher)
    fact('Rqt从uJt默认命令表逐项按严格key相等取handler；默认表和Pw动态登记是两条机制。这个查找函数不能独自证明实际UI或宿主消息接收方。', binding_units['Rqt'])
    fact('Nqt菜单/可用性对象记录与dJt handler表分别更新；fJt追加对象，pJt按对象身份移除。Oqt只返回某个key的数组长度，存在登记不等于命令已执行或功能已验证。', binding_units['Oqt'])
    fact('原Program把Pw导出为IBn；完整模块消费者还须核对实际import、局部绑定、重导出和动态传递。其他文件不能仅按同名callee套用此合同。', inventory['exports'][0]['reference'])
    counts = {'sourceFacts': len(facts), 'fullOriginalProgramParses': 2, 'distinctOriginalProgramFiles': 1,
              'originalProgramAstNodesPerParse': inventory['nodeCount'],
              'legacyRegistrationCandidatesResolved': 6, 'sameBindingDirectCalls': 49,
              'staticIdCalls': sum(c['commandId'] is not None for c in calls),
              'distinctStaticCommandIds': len({c['commandId'] for c in calls if c['commandId'] is not None}),
              'dynamicIdCalls': sum(c['commandId'] is None for c in calls),
              'additionalDirectCallsBeyondLegacySubset': 43, 'lexicalImporterCandidates': 24,
              'sourceSpansChecked': len(checked), 'newFeatureDefinitions': 0,
              'newConfirmedModeClassifications': 0, 'actualCommandDispatchesVerified': 0,
              'originalClientRunsAdded': 0, 'modelSubmissionsAdded': 0, 'newReaRuns': 0}
    assert counts['staticIdCalls'] == 47 and counts['distinctStaticCommandIds'] == 44
    assert counts['dynamicIdCalls'] == 2
    result = {'schemaVersion': 1, 'baselineId': BASELINE, 'counts': counts,
              'facts': facts, 'coreSourceUnits': {**{k: units[k] for k in
                                                    ['definition-Pw', 'definition-Pqt', 'definition-fJt',
                                                     'definition-pJt', 'assignment-dJt', 'assignment-Nqt']},
                                                'dispatcher': dispatcher, **binding_units},
              'legacyCandidateRelations': relations, 'sameBindingDirectCalls': calls,
              'programExport': inventory['exports'], 'lexicalImporterCandidates': candidates,
              'nextAction': {'question': '对24个IBn静态import词法候选作完整Program绑定核对，枚举其直接注册调用和传递/重导出边界；另保留默认命令表和实际dispatch入口。',
                             'completionCondition': '每个候选有真实import及作用域身份、调用清单或明确未调用/动态传递说明；不重复解析已完成的app-initial。'},
              'fullAnalysisCompleted': False, 'completeFeatureDenominator': None,
              'targetCodeExecuted': False,
              'limitations': ['Inventory is complete only for direct Identifier callee calls to the selected Program Pw binding in app-initial.',
                              'It does not claim complete application command registration coverage, runtime mounts or effective guard values.',
                              'Lexical importer candidates are not yet AST-confirmed consumers; namespace, re-export and dynamic aliases remain open.',
                              'No command was dispatched and no original client or model service was used.',
                              'Existing user-feature scope, mode unknowns, deferred candidates and behavior requirements remain unchanged.']}
    state = read(OUT / 'analysis-state.json')
    RAW.mkdir(parents=True)
    for directory in ['commands-01', 'inventory-01', 'attempts']:
        shutil.copytree(WORK / directory, RAW / directory)
    for symbol, loc in binding_units.items():
        a, z = loc['byteRange']['start'], loc['byteRange']['endExclusive']
        (RAW / (symbol+'.txt')).write_bytes(data[a:z])
    shutil.copyfile(Path(__file__), RAW / Path(__file__).name)
    write(RAW / 'import-discovery.json', {'command': command, 'exitCode': found.returncode,
                                        'stdout': found.stdout.decode(), 'stderr': found.stderr.decode(),
                                        'candidates': candidates, 'completeConsumerCoverageClaimed': False})
    write(RAW / 'analysis-state-before.json', state)
    write(OUT / names[0], result)
    summary = '''# Renderer 命令注册的完整 Program 核对

固定基线 `codex-26.1007.30912-c5b273322a83`。旧6个renderer注册候选均已接到同一个原Program函数 `Pw`；此前函数片段保留的callee身份缺口在这6处关闭。实际组件挂载、store实例和命令执行仍未验证。

完整 `app-initial` 中，同一绑定共有49个直接调用，旧6个只是子集；另外43个调用现已登记。[完整清单](command-registration-contracts.json)保存所有范围、参数、局部参数绑定和最近函数。47处使用静态字符串首参，涉及44个不同命令ID；2处动态ID保留。调用数、ID数均不作为用户功能数。

`Pw` 是 effect 注册hook：处理enabled/isActive/priority以及键盘、context和普通handler；调用 `Pqt`登记到 `dJt`，再更新独立的 `Nqt` 菜单/可用性记录，cleanup分别移除。`Pqt`允许同一ID保留多个handler，并按注册对象身份注销。`Lqt`按normal再fallback、同级逆注册顺序尝试，只有严格false表示不消费，再查默认命令表。普通handler的返回值没有由Pw返回，dispatcher也不等待Promise；维护时需要保留这些顺序和返回值语义。

静态scope证明了注册关系；没有执行源码函数、触发原客户端命令或提交模型任务。本次不是行为验收，没有增加用户功能、模式归属或真实通过场景。

`Pw`的真实导出为 `IBn`。另发现24个具有该静态import拼写的文件，作为词法候选保存；尚未据此宣称跨文件绑定或全应用覆盖。下一批逐个完整Program核对这些import和局部作用域，枚举直接调用及传递边界。默认命令表、实际dispatch调用方、账户/平台/模式和挂载条件仍单列，不能把菜单元数据当handler。

本批解析2次同一完整原Program，均无解析错误；既有源码单位和新增核心范围经冻结字节核对。原6条入口ID及原台账保持不变。[来源索引](command-registration-provenance.json)保存解析器、工具源码、命令、stdout/stderr及终态；[旧入口分组](entry-family-summary.md)和[实施计划v6](implementation-plan-v6.md)继续有效。
'''
    (OUT / names[1]).write_text(summary)
    index = {'schemaVersion': 1, 'baselineId': BASELINE, 'publishedAtUtc': datetime.now(timezone.utc).isoformat(),
             'outputs': [pin(OUT / n) for n in names[:-1]],
             'rawArtifacts': [pin(p) for p in sorted(RAW.rglob('*')) if p.is_file()],
             'inputs': [pin(OUT / 'functional-entry-ledger.json'), pin(OUT / 'entry-family-map.json')],
             'counts': counts, 'fullAnalysisCompleted': False}
    write(OUT / names[2], index)
    state['updatedAtUtc'] = index['publishedAtUtc']
    state['rendererCommandRegistration'] = {'provenance': pin(OUT / names[2]), 'contracts': pin(OUT / names[0]),
                                            'summary': pin(OUT / names[1]), 'counts': counts,
                                            'nextAction': result['nextAction'], 'fullAnalysisCompleted': False}
    write(OUT / 'analysis-state.json', state)
    paragraph = '\n[Renderer命令注册](command-registration-summary.md)已关闭旧6处callee身份缺口，并在完整app-initial中登记同一Pw绑定的49个直接调用；另有24个IBn import词法候选待作跨文件核对。未增加功能、模式分类或实际行为通过数。\n'
    for name in ['report.md', 'gaps.md']:
        p = OUT / name
        lines = p.read_text().splitlines(keepends=True)
        lines.insert(1, paragraph)
        p.write_text(''.join(lines))
    p = ROOT / 'README.md'
    lines = p.read_text().splitlines(keepends=True)
    lines.insert(1, '\n命令注册最新结果见[完整Program核对](analysis/'+BASELINE+'/command-registration-summary.md)：旧6处身份已确认，同一文件49处直接调用已登记；跨文件消费者和真实行为继续核对。\n')
    p.write_text(''.join(lines))
    for p in [*(OUT / name for name in names), *RAW.rglob('*')]:
        if p.is_file():
            p.chmod(0o444)
    print(json.dumps({'published': True, **counts}, ensure_ascii=False))


if __name__ == '__main__':
    main()
