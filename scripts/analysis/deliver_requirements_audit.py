"""Publish the frozen current-plan audit with its exact reviewed reader pins."""
import ast
import json
from pathlib import Path

from deliver_frozen_metadata import BASELINE, WORKSPACE, OUT, encode, pin, require, write_new

LOCAL = WORKSPACE / '.analysis-local/analysis-requirements-current-audit-work'
NOTE = '''[当前需求审计](analysis-requirements-current-audit.md)另按原计划9项完成标准、6阶段及39条子要求核对包含153条补充证据的固定读者快照。4项记录／范围义务满足、5项部分；阶段1输入交付齐备，其余5阶段部分。194项元数据检查只证明所列来源与范围，完整分析仍未完成。
下一步是跨catalog登记与逐操作职责、状态、外部边界和具体验收场景，并关闭会改变工程方案的运行时与后台门槛；该审计不追认其固定输入之后的新调查。
'''


def main():
    review_raw = (LOCAL / 'review.json').read_bytes()
    require(pin(review_raw) == {'bytes': 46813, 'sha256': '7a68c28cd81120f80f8b888df5d813d88d6e2e260ece60bc8d8be97ca440db27'}, 'audit revision changed')
    review = json.loads(review_raw)
    require(review['baselineId'] == BASELINE and review['checkCount'] == 194 and review['errors'] == [], 'audit not passed')
    require(review['fullAnalysisCompleted'] is False and review['finalClientImplementationAcceptanceClaimed'] is False, 'scope upgraded')
    require(review['criterionStatusCounts'] == {'satisfied-with-scope-limits': 4, 'partial': 5}, 'criteria changed')
    require(len(review['criteria']) == 9 and len(review['stages']) == 6, 'requirements changed')
    names = ['review.json', 'review.md', 'selected-metadata-snapshot.json', 'input-pins.json',
        'attempts/attempt-03/receipt.json', 'freeze-manifest.json', 'freeze-confirmation.json', 'freeze-attempt-01/receipt.json']
    inputs = {}
    for name in names:
        path = LOCAL / name
        require(not path.is_symlink() and path.stat().st_mode & 0o777 == 0o444, 'audit input not frozen')
        inputs[name] = path.read_bytes()
    require(pin(inputs['freeze-manifest.json'])['sha256'] == '41126a74f010e5f2de113a1ccc20b016192483194f30450f47e41f54c6165c5b', 'manifest changed')
    require(pin(inputs['freeze-confirmation.json'])['sha256'] == '055af44284b50384ad0e8a5ac65d51af5be7ca63f10148484b577b3bace8a462', 'seal changed')
    for name in ['attempts/attempt-03/receipt.json', 'freeze-attempt-01/receipt.json']:
        require(json.loads(inputs[name].rstrip(b'\\n'))['exitCode'] == 0, 'actual audit run failed')
    before = {name: (OUT / name).read_bytes() for name in ['report.md', 'analysis-state.json']}
    require(pin(before['report.md']) == {'bytes': 42243, 'sha256': '834c48eac031048888b3eb3ce2d055b1ca72656813ab097a78d2e5589c9517f3'}, 'audited report changed')
    require(pin(before['analysis-state.json']) == {'bytes': 131652, 'sha256': 'b9eb39cc4180a10e8c284de6aac8b6f6d23d33114b90278dd80c26bd16105879'}, 'audited state changed')
    ast.parse((WORKSPACE / 'scripts/analysis/publish_findings.py').read_bytes())
    ast.parse((WORKSPACE / 'scripts/analysis/record_publication.py').read_bytes())
    copies = []
    for name, raw in inputs.items():
        relative = 'raw/analysis-requirements-current-audit/' + name
        write_new(OUT / relative, raw)
        copies.append({'original': str(LOCAL / name), 'published': relative, **pin(raw)})
    write_new(OUT / 'analysis-requirements-current-audit.json', review_raw)
    copies.append({'original': str(LOCAL / 'review.json'), 'published': 'analysis-requirements-current-audit.json', **pin(review_raw)})
    index = {'schemaVersion': 1, 'baselineId': BASELINE, 'review': {'path': 'analysis-requirements-current-audit.json', **pin(review_raw)},
        'checks': 194, 'criterionStatusCounts': review['criterionStatusCounts'], 'stageDeliveryStatusCounts': review['stageDeliveryStatusCounts'],
        'reviewedReaders': {name: pin(raw) for name, raw in before.items()}, 'copies': copies,
        'scope': 'Nine original completion criteria, six phases and 39 requirement items against the explicitly pinned pre-publication reader snapshot only.',
        'fullAnalysisCompleted': False, 'globalRecordsAdded': 0, 'runtimeRunsAdded': 0}
    index_raw = encode(index)
    write_new(OUT / 'analysis-requirements-current-audit-provenance.json', index_raw)
    summary = '# 当前原计划需求审计\n\n' + NOTE + '\n本次固定审计发布前的 report/state 字节，随后增加的审计链接及状态指针不追溯计入审计输入。原始读者 pins 和8项冻结输入见[交付索引](analysis-requirements-current-audit-provenance.json)。\n\n详细9项标准、6阶段和39条原计划子要求见[逐项表](analysis-requirements-current-audit.json)，原始说明见[冻结审计说明](raw/analysis-requirements-current-audit/review.md)。\n\n新增设置、配置转发、终端和文件差异调查分别按其自己的输入范围核对。行为、模式、运行时与完整客户端验收仍未完成；冻结与审计检查分别统计，没有合并为覆盖比例。\n'
    write_new(OUT / 'analysis-requirements-current-audit.md', summary.encode())
    state = json.loads(before['analysis-state.json'])
    state['analysisRequirementsCurrentAudit'] = {'path': 'analysis-requirements-current-audit-provenance.json', **pin(index_raw),
        'checks': 194, 'completionCriteria': 9, 'phases': 6, 'requirementItems': 39,
        'fullAnalysisCompleted': False, 'scope': index['scope']}
    marker = '[完成标准审计](criteria-audit.md)'
    report = before['report.md'].decode()
    require(report.count(marker) == 1 and NOTE not in report, 'report marker changed')
    for name, raw in before.items():
        write_new(OUT / ('raw/analysis-requirements-current-audit/reader-before-' + name), raw)
    (OUT / 'analysis-state.json').write_bytes(encode(state))
    (OUT / 'report.md').write_text(report.replace(marker, NOTE + '\n' + marker))
    print(json.dumps({'status': 'audit-delivered', 'copies': len(copies), 'checks': 194,
        'fullAnalysisCompleted': False, 'runtimeRunsAdded': 0,
        'outputs': {name: pin((OUT / name).read_bytes()) for name in ['report.md', 'analysis-state.json']}}))


if __name__ == '__main__':
    main()
