"""Close the finite import review without claiming runtime or feature coverage."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASELINE
WORK = ROOT / '.analysis-local/command-consumers-work'
RAW = OUT / 'raw/command-consumers'
NAMES = ['command-consumer-contracts.json', 'command-consumer-summary.md',
         'command-consumer-provenance.json']


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def pin(path):
    data = path.read_bytes()
    return {'path': os.path.relpath(path, OUT), 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest()}


def verify_pin(path, expected):
    actual = pin(path)
    assert all(actual[key] == expected[key] for key in ['bytes', 'sha256']), str(path)


def main():
    assert not RAW.exists() and all(not (OUT / name).exists() for name in NAMES)
    previous = read(OUT / 'command-registration-contracts.json')
    candidates = previous['lexicalImporterCandidates']
    assert len(candidates) == 24
    receipts = []
    for run, expected in [('run-01', 24), ('primary-export-fix-01', 1)]:
        rows = read(WORK / run / 'receipts.json')
        assert len(rows) == expected
        for receipt in rows:
            assert receipt['exitCode'] == 0
            index = receipt['candidateIndex']
            directory = WORK / run / f'{index+1:02}'
            verify_pin(OUT / 'command-registration-contracts.json', receipt['inputContract'])
            verify_pin(directory / 'source-contracts.json', receipt['output'])
            for stream in ['stdout', 'stderr']:
                verify_pin(WORK / run / f'{index+1:02}-{stream}.txt', receipt[stream])
            receipts.append({'run': run, **receipt})
    assert receipts[-1]['candidateIndex'] == 9
    exporter = previous['programExport']
    assert len(exporter) == 1 and exporter[0]['local'] == 'Pw' and exporter[0]['exported'] == 'IBn'
    consumers, facts, checked, source_cache = [], [], set(), {}

    def verify_spans(value):
        if isinstance(value, dict):
            if all(key in value for key in ['sourcePath', 'sourceHash', 'byteRange', 'spanHash']):
                source_path = value['sourcePath']
                if source_path not in source_cache:
                    assert source_path.startswith('app.asar/')
                    path = ROOT / '.analysis-local/baselines' / BASELINE / 'extracted' / source_path.removeprefix('app.asar/')
                    data = path.read_bytes()
                    source_cache[source_path] = (data, hashlib.sha256(data).hexdigest())
                data, digest = source_cache[source_path]
                a, z = value['byteRange']['start'], value['byteRange']['endExclusive']
                assert digest == value['sourceHash'] and 0 <= a < z <= len(data)
                key = (source_path, a, z, value['spanHash'])
                if key not in checked:
                    assert hashlib.sha256(data[a:z]).hexdigest() == value['spanHash']
                    checked.add(key)
            for child in value.values():
                verify_spans(child)
        elif isinstance(value, list):
            for child in value:
                verify_spans(child)

    for index, candidate in enumerate(candidates):
        run = 'primary-export-fix-01' if index == 9 else 'run-01'
        path = WORK / run / f'{index+1:02}/source-contracts.json'
        item = read(path)
        assert item['candidateIndex'] == index and item['sourcePath'] == candidate['sourcePath']
        assert item['sourceHash'] == candidate['sourceHash'] and item['sourceBytes'] == candidate['sourceBytes']
        assert item['fullProgramParsed'] and item['parserErrors'] == 0
        assert not item['targetCodeExecuted'] and not item['otherReferences'] and not item['localReexports']
        assert len(item['confirmedImports']) == 1
        imported = item['confirmedImports'][0]
        assert imported['imported'] == 'IBn' and imported['module'] == './app-initial-6350d04672d0.js'
        assert imported['localName'] == candidate['localNameCandidate']
        for call in item['directCalls']:
            assert call['importSpecifier'] == imported['specifier']
            assert not call['actualMountOrDispatchVerified']
        verify_spans(item)
        facts.append({'id': f'COMMAND-CONSUMER-{index+1:03}', 'baselineId': BASELINE,
                      'claim': f"完整Program确认{imported['localName']}来自app-initial的IBn导出；同绑定直接调用{len(item['directCalls'])}处。实际挂载、访问条件和dispatch尚未验证。",
                      **imported['specifier'], 'method': 'static-code', 'confidence': 'confirmed',
                      'verificationStatus': 'original-program-import-and-direct-call-binding-confirmed; runtime-unverified'})
        consumers.append({'selectedRawContract': f'raw/command-consumers/{run}/{index+1:02}/source-contracts.json',
                          'exportRelation': exporter[0], **item})
    verify_spans(exporter)
    calls = [call for item in consumers for call in item['directCalls']]
    old_calls = previous['sameBindingDirectCalls']
    combined = old_calls + calls
    identities = {(c['call']['sourcePath'], c['call']['byteRange']['start'],
                   c['call']['byteRange']['endExclusive']) for c in combined}
    assert len(identities) == len(combined) == 105 and len(calls) == 56
    new_ids = {c['commandId'] for c in calls if c['commandId'] is not None}
    ids = {c['commandId'] for c in combined if c['commandId'] is not None}
    assert len(new_ids) == 40 and len(ids) == 80
    assert sum(c['commandId'] is None for c in calls) == 5
    assert sum(c['commandId'] is None for c in combined) == 7
    metadata = read(OUT / 'menu-command-contracts.json')['metadataRegistry']['commands']
    assert len(metadata) == 182 and ids <= {item['id'] for item in metadata}
    joins = [{'commandId': command_id,
              'metadataContractIds': [item['contractId'] for item in metadata if item['id'] == command_id],
              'relation': 'literal-key-equality-only; not-operation-equivalence'} for command_id in sorted(ids)]
    old_primary = read(WORK / 'run-01/10/source-contracts.json')
    assert len(old_primary['otherReferences']) == 1 and old_primary['directCalls'] == consumers[9]['directCalls']
    counts = {'fullOriginalProgramParsesAdded': 25, 'distinctConsumerPrograms': 24,
              'selectedConsumerAstNodes': sum(item['nodeCount'] for item in consumers),
              'parsedAstNodesIncludingCorrection': sum(item['nodeCount'] for item in consumers) + old_primary['nodeCount'],
              'confirmedImportRelations': 24, 'consumerDirectCalls': 56, 'consumerStaticIdCalls': 51,
              'consumerDistinctStaticIds': 40, 'consumerDynamicIdCalls': 5,
              'combinedDistinctPrograms': 25, 'combinedDirectCalls': 105,
              'combinedStaticIdCalls': 98, 'combinedDistinctStaticIds': 80, 'combinedDynamicIdCalls': 7,
              'metadataRecords': 182, 'literalMetadataKeyMatches': 80,
              'sourceFacts': len(facts), 'sourceSpansChecked': len(checked),
              'newFeatureDefinitions': 0, 'newConfirmedModeClassifications': 0,
              'actualCommandDispatchesVerified': 0, 'modelSubmissionsAdded': 0,
              'originalClientRunsAdded': 0, 'newReaRuns': 0}
    next_action = {'priority': 'A2', 'question': '将运行时四个特殊边界落实为保留能力、独立依赖或适配的逐项决定，先核对task-manager启动guard和实际caller条件。',
                   'closure': '交付有限的能力/依赖决定表、受影响功能与未验证条件；不以删除guard或复制原二进制宣称独立构建完成。',
                   'commandFollowupDeferred': '默认命令表、实际dispatch、requiredAccess及组件挂载条件作为已有缺口保留，不重跑已完成的24个import。'}
    result = {'schemaVersion': 1, 'baselineId': BASELINE, 'counts': counts, 'facts': facts,
              'consumers': consumers, 'combinedStaticCommandIds': sorted(ids), 'metadataKeyJoins': joins,
              'initialRegistrationContract': pin(OUT / 'command-registration-contracts.json'),
              'erratum': {'affectedRun': 'run-01', 'candidateIndex': 9,
                          'reason': 'ExportSpecifier的exported标签py被误当成本地import引用；yM as py不转发hook。',
                          'correctionRun': 'primary-export-fix-01', 'directCallInventoryChanged': False,
                          'oldResultPreserved': True, 'authoritativeOtherReferences': 0},
              'limitations': ['Complete only for direct selected binding calls in these 25 Programs; not all application command APIs.',
                              'Namespace imports, indirect aliases, dynamic imports and default-handler tables are outside this census.',
                              'Literal metadata key equality does not prove behavior, access, product mode or operation equivalence.',
                              'No feature count, mode classification or actual behavior acceptance changed.'],
              'nextAction': next_action, 'fullAnalysisCompleted': False, 'targetCodeExecuted': False}
    state = read(OUT / 'analysis-state.json')
    RAW.mkdir(parents=True)
    for run in ['run-01', 'primary-export-fix-01']:
        shutil.copytree(WORK / run, RAW / run)
    shutil.copyfile(Path(__file__), RAW / Path(__file__).name)
    write(RAW / 'analysis-state-before.json', state)
    write(OUT / NAMES[0], result)
    summary = '''# 命令注册消费者批次结案

24个静态import候选已全部通过完整Program核对，均导入`app-initial`的`IBn → Pw`绑定；共56个直接注册调用，其中51处静态ID、40个不同静态ID、5处动态ID。[合同清单](command-consumer-contracts.json)保存逐文件import、参数绑定、最近函数和结构条件。

加上此前`app-initial`的49处，限定25个Program共105处直接调用、98处静态ID、80个不同静态ID及7处动态ID。80个ID均可按字面key连接到182条元数据中的记录；这只建立key关联，不证明功能等价、访问权限或模式。多个handler可共用ID，动态ID仍单列，默认handler表亦不在本次分母内。

本批关闭“24个import是否真实连接同一hook、有哪些直接调用和局部传递引用”这一有限问题。当前选定结果没有其他引用或本地重导出。它不覆盖namespace、动态import及全应用的其他注册API，也没有验证实际组件挂载或dispatch。既有48项有限功能、212条未执行验收规格、模式unknown和完整功能分母未知均保持。

初次primary分析把`yM as py`的导出标签`py`误计为import引用。已修正规则并仅重跑primary，当前otherReferences为0，5个直接调用完全相同。原结果和修正结果均保留；共25次完整解析、24个不同文件。[来源记录](command-consumer-provenance.json)包含每次命令、终态和输出哈希。

没有新增模型提交、原客户端运行或REA重跑。本批结束后不继续扩张注册细节，下一项转入[运行时方案](runtime-adapter-options.md)的A2能力/依赖决定：先核对task-manager启动guard与caller条件。默认命令表、实际dispatch、requiredAccess和挂载条件保留为后续明确缺口，不算已关闭。完整分析仍在进行。
'''
    (OUT / NAMES[1]).write_text(summary)
    provenance = {'schemaVersion': 1, 'baselineId': BASELINE,
                  'publishedAtUtc': datetime.now(timezone.utc).isoformat(),
                  'outputs': [pin(OUT / name) for name in NAMES[:-1]],
                  'rawArtifacts': [pin(p) for p in sorted(RAW.rglob('*')) if p.is_file()],
                  'inputs': [pin(OUT / 'command-registration-contracts.json'), pin(OUT / 'menu-command-contracts.json')],
                  'counts': counts, 'fullAnalysisCompleted': False}
    write(OUT / NAMES[2], provenance)
    state['updatedAtUtc'] = provenance['publishedAtUtc']
    state['commandConsumers'] = {'contracts': pin(OUT / NAMES[0]), 'summary': pin(OUT / NAMES[1]),
                                'provenance': pin(OUT / NAMES[2]), 'counts': counts,
                                'nextAction': next_action, 'fullAnalysisCompleted': False}
    write(OUT / 'analysis-state.json', state)
    paragraph = '\n[命令消费者批次已结案](command-consumer-summary.md)：24个import均已确认，新增56处直接调用；与initial合计105处、80个不同静态ID。没有增加功能或实际行为通过数。下一项转A2运行时能力/依赖决定，已完成的import不再重复调查。\n'
    for name in ['report.md', 'gaps.md']:
        p = OUT / name
        lines = p.read_text().splitlines(keepends=True)
        lines.insert(1, paragraph)
        p.write_text(''.join(lines))
    p = ROOT / 'README.md'
    lines = p.read_text().splitlines(keepends=True)
    lines[1:4] = ['\n命令注册的24个消费者批次已完成，见[结案结果](analysis/' + BASELINE + '/command-consumer-summary.md)。下一项为运行时能力/依赖决定；完整功能范围与实际行为验收仍待完成。\n']
    p.write_text(''.join(lines))
    for p in [*(OUT / name for name in NAMES), *RAW.rglob('*')]:
        if p.is_file():
            p.chmod(0o444)
    print(json.dumps({'published': True, **counts}, ensure_ascii=False))


if __name__ == '__main__':
    main()
