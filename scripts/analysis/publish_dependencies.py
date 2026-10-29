#!/usr/bin/env python3
"""Publish compact dependency indexes from the local static investigation."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--local', required=True)
    args = parser.parse_args()
    baseline_path = Path(args.baseline).resolve()
    output = baseline_path.parent
    baseline = json.loads(baseline_path.read_text())
    local = Path(args.local).resolve()
    data = json.loads((local / 'dependencies.json').read_text())
    summary = json.loads((local / 'summary.json').read_text())
    evidence = [json.loads(line) for name in ('evidence.jsonl', 'supplemental-evidence.jsonl') for line in (local / name).read_text().splitlines()]
    indexed = {item['id']: item for item in evidence}
    records = []
    for key, occurrence_type in [('rootDeclarations', 'root-declaration'), ('installedPackages', 'asar-installed-package'), ('externalPackages', 'external-installed-package'), ('bundledHints', 'bundled-version-hint')]:
        for item in data[key]:
            source = indexed[item['evidenceIds'][0]]
            record = {**item, 'occurrenceType': occurrence_type, 'sourcePath': source['sourcePath'],
                      'sourceHash': source['sourceHash'], 'locator': source['locator'],
                      'confidence': source['confidence'], 'verificationStatus': source['verificationStatus']}
            if occurrence_type == 'root-declaration':
                record['version'] = item.get('rootResolvedVersion')
                record['versionBasis'] = item['actualVersionStatus']
            if occurrence_type in ('asar-installed-package', 'external-installed-package'):
                record['use'] = 'shipped-package-runtime-reachability-unverified'
            records.append(record)
    embedded_action_path = local.parent / 'embedded-dependency-work-v2/investigation-actions.json'
    embedded_actions = None
    if embedded_action_path.exists():
        embedded_actions = json.loads(embedded_action_path.read_text())
        assert embedded_actions['baselineId'] == baseline['baselineId']
        actions_by_id = {item['candidateId']: item for item in embedded_actions['candidates']}
        hints = [record for record in records if record['occurrenceType'] == 'bundled-version-hint']
        assert len(hints) == len(actions_by_id) == 17
        for record in hints:
            action = actions_by_id[record['id']]
            assert action['sourcePath'] == record['sourcePath'] and action['sourceHash'] == record['sourceHash']
            record.update({'source': action['source'], 'version': None,
                           'versionBasis': 'actual-upstream-distribution-unknown; source-declaration-separately-recorded',
                           'sourceSelfReportedVersion': action['sourceSelfReportedVersion'],
                           'use': 'embedded-library-candidate; retained-caller-reachability-unverified',
                           'license': record.get('license') or 'unknown-concrete-package-unresolved',
                           'recommendedIntegration': action['recommendedIntegration'], 'unresolved': action['unresolved'],
                           'investigationActions': action['investigationActions'],
                           'verificationStatus': 'source-declaration-bound; upstream-identity-modifications-and-runtime-unverified',
                           'embeddedContractReferences': {'path': 'embedded-dependency-investigation-actions.json',
                                                          'sha256': digest(embedded_action_path), 'candidateId': record['id'],
                                                          'versionEvidenceRef': action['versionEvidenceRef']}})
    upstream_path = output / 'upstream-comparison.json'
    upstream = json.loads(upstream_path.read_text()) if upstream_path.exists() else None
    upstream_linked_records = 0
    if upstream:
        assert upstream['baselineId'] == baseline['baselineId'] and upstream['sourceArchiveSha256'] == baseline['archiveSha256']
        compared = {item['name']: item for item in upstream['packages'] if item['status'] == 'compared'}
        for record in records:
            result = compared.get(record['name'])
            is_root = record['occurrenceType'] == 'root-declaration' or (
                record['occurrenceType'] == 'asar-installed-package' and record.get('packagePath') == 'node_modules/' + record['name'])
            if not result or not is_root or record.get('version') != result['version']:
                continue
            record['modificationStatus'] = result['modificationStatus']
            record['upstreamComparison'] = {'path': 'upstream-comparison.json', 'sha256': digest(upstream_path),
                                            'name': result['name'], 'version': result['version'], 'scope': 'frozen-root-package-only'}
            record['unresolved'] = [issue for issue in record.get('unresolved', []) if issue not in {
                'Upstream comparison and modification status', 'Upstream identity and modifications not independently verified'}]
            if result['sourceOrBuildInputModificationCandidates']:
                record['recommendedIntegration'] = 'maintained-patched-package-or-first-party-adapter-after-caller-verification'
                record['unresolved'].append('Modified upstream files require a behavior-preserving integration decision')
            elif 'native-unverified' in result['modificationStatus']:
                record['recommendedIntegration'] = 'versioned-package-and-independent-native-build-after-interface-verification'
            else:
                record['recommendedIntegration'] = 'versioned-upstream-package-after-caller-verification'
            if 'native-unverified' in result['modificationStatus']:
                record['unresolved'].append('Native provenance, ABI and independent build remain unverified')
            upstream_linked_records += 1
    fields = ['id', 'occurrenceType', 'name', 'version', 'versionBasis', 'declaredVersion', 'rootResolvedVersion',
              'installedVersions', 'noticeVersions', 'scope', 'packagePath', 'classification', 'source', 'license',
              'licenseFiles', 'use', 'mode', 'modificationStatus', 'recommendedIntegration', 'unresolved',
              'sourcePath', 'sourceHash', 'locator', 'confidence', 'verificationStatus', 'evidenceIds', 'literalImportEvidenceIds', 'upstreamComparison',
              'sourceSelfReportedVersion', 'embeddedContractReferences', 'investigationActions']
    with (output / 'dependencies.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        for record in records:
            writer.writerow({key: json.dumps(record.get(key), ensure_ascii=False) if isinstance(record.get(key), (dict, list)) else record.get(key, '') for key in fields})
    (output / 'dependency-evidence.jsonl').write_text(''.join(json.dumps(item, ensure_ascii=False) + '\n' for item in evidence))
    for name in ('build-inputs.json', 'native-runtime.json'):
        shutil.copyfile(local / name, output / name)
    inventory = json.loads((output / 'files.json').read_text())
    notice_source = next(item for item in inventory['applicationFiles'] if item['sourcePath'] == 'Contents/Resources/THIRD_PARTY_NOTICES.txt')
    summary['publishedCounts'] = {occurrence_type: sum(item['occurrenceType'] == occurrence_type for item in records) for occurrence_type in sorted(set(item['occurrenceType'] for item in records))}
    summary['publishedCounts']['dependenciesCsvRows'] = len(records)
    summary['publishedCounts']['evidenceRecords'] = len(evidence)
    if embedded_actions:
        summary['embeddedHintInvestigation'] = {'path': 'embedded-dependency-investigation-actions.json',
                                                'sha256': digest(embedded_action_path),
                                                'sourceDeclarationsBound': 17, 'actualUpstreamDistributionsVerified': 0,
                                                'actualDistributionVersionColumn': 'empty; separate sourceSelfReportedVersion is not a lock',
                                                'unknownFieldActionsPerCandidate': embedded_actions['scope']['unknownFieldActionsPerCandidate']}
    if upstream:
        summary['counts']['upstreamComparedPackages'] = upstream['comparedPackages']
        summary['upstreamComparison'] = {'path': 'upstream-comparison.json', 'sha256': digest(upstream_path),
                                         'comparedPackages': upstream['comparedPackages'], 'linkedRootRecords': upstream_linked_records,
                                         'scope': 'five exact-version frozen root packages; nested occurrences excluded',
                                         'runtimeVerified': False}
        summary['limitations'] = [issue for issue in summary['limitations'] if issue !=
                                  'Exact package metadata versions are package-reported facts; registry content, integrity and version locks were not verified.']
        summary['limitations'].append('Five root package registry archives were integrity verified; other packages and nested occurrences remain unverified. Runtime compatibility and a final dependency lockfile are not established.')
    summary['attributionIndex'] = {'localPath': str(local / 'attribution.json'), 'localSha256': digest(local / 'attribution.json'),
                                   'localBytes': (local / 'attribution.json').stat().st_size,
                                   'sourcePath': notice_source['sourcePath'], 'sourceHash': notice_source['sha256'],
                                   'entries': summary['counts']['noticeEntries'], 'uniqueNames': summary['counts']['noticeUniqueNames'],
                                   'versionInterpretation': 'may-be-included-candidate-not-runtime-lockfile'}
    summary['localDetailedIndex'] = {'path': str(local / 'dependencies.json'), 'sha256': digest(local / 'dependencies.json'),
                                     'contains': ['installedEdges', 'literalImports', 'packageDescriptors', 'metadataErrors', 'all published package records']}
    summary['validation'] = json.loads((local / 'validation.json').read_text())
    summary['publicArtifacts'] = {name: {'bytes': (output / name).stat().st_size, 'sha256': digest(output / name)} for name in ('dependencies.csv', 'dependency-evidence.jsonl', 'build-inputs.json', 'native-runtime.json')}
    source_map_path = output / 'source-maps.json'
    source_map_report = None
    if source_map_path.exists():
        source_map_report = json.loads(source_map_path.read_text())
        summary['sourceMapCoverage'] = source_map_report['summary']
        summary['sourceMapArtifacts'] = {name: {'bytes': (output / name).stat().st_size, 'sha256': digest(output / name)} for name in ('source-maps.json', 'source-map-evidence.jsonl', 'source-map-validation.json') if (output / name).exists()}
    (output / 'dependency-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    report = (local / 'dependency-analysis.md').read_text()
    if upstream:
        report += '\n## 公开精确版本归档核对\n\n已静态比较五个根包，官方 npm 的 dist.integrity 全部通过，详见 [逐文件报告](upstream-comparison.md)。node-pty 的两个 Windows JS 文件与上游不同；objc-js 原生文件也不同。better-sqlite3/node-pty/objc-js 的原生来源、ABI 和独立构建尚未验证；发布文件缺失与源码修改分别统计。CSV 中仅对应根声明及根安装 occurrence 更新修改状态，同版嵌套安装不继承该结论。先前静态盘点中的“尚未比较”描述是历史范围，现以上游比较记录补充，依赖运行验证仍为 0。\n'
    if embedded_actions:
        report += '\n## 内嵌版本声明与逐项调查动作\n\n17/17 既有 bundle hint 已绑定源码声明，详见 [内嵌依赖续查](embedded-dependency-continuation-summary.md) 与 [逐项调查动作](embedded-dependency-investigation-actions.json)。CSV 的 source、recommendedIntegration、unresolved 和 investigationActions 已逐条补齐。sourceSelfReportedVersion 单独记录源码自报，version 保留为空，因为实际上游分发版本仍未确认；Sentry 注册表默认值和索引不等于活跃版本，私有 Statsig 不等于普通公开包。第一方适配器保留，完整第三方闭包、修改状态、模式与运行均继续调查。原 CSV 字节和哈希由 raw/dependency-publication 的 before 快照保存。\n'
    report += '\n## 基线目录发布清单\n\n本说明已发布到固定基线目录；此前列出的 dependencies.json 与各独立 CSV 保留于 `.analysis-local/dependency-work/`。公开合并清单为 `dependencies.csv`，使用 occurrenceType 区分 root-declaration、asar-installed-package、external-installed-package、bundled-version-hint，共 ' + str(len(records)) + ' 条。证据位于 `dependency-evidence.jsonl`；统计和本地完整索引的路径与 SHA-256 位于 `dependency-summary.json`。构建输入和原生/Wasm 清单分别为 `build-inputs.json`、`native-runtime.json`。source map 全范围扫描单独记录在 `source-maps.json` 和 `source-map-evidence.jsonl`。\n'
    if source_map_report:
        stats = source_map_report['summary']
        report += f'''
## Source map 全范围核实

读取并对照基线哈希的文件为 {stats['scannedFiles']}/{stats['eligibleFiles']} 个，包含全部 ASAR 与归档外 JS/MJS/CJS/CSS/JSON；独立 `.map` 文件按完整文件清单检查。ASAR-unpacked 的磁盘重复件与 symlink 排除计数、逐文件路径/hash 都保存在 source-maps.json。

共 {stats['rawMarkerOccurrences']} 个 sourceMappingURL 文本出现点，涉及 {stats['rawMarkerFiles']} 个 JS 文件；全部由 Babel 完整解析并确认注释位置。实际 directive 注释 {stats['confirmedDirectiveComments']} 个，均引用冻结输入中缺失的相对 `.map` 文件。{stats['falsePositiveOccurrences']} 个文本误报出现在外部 Playwright 的 babelBundleImpl.js/utilsBundleImpl.js 字符串、代码或正则中，未计为可用 source map。解析未解决 marker 为 {stats['unresolvedMarkerOccurrences']}，读取/哈希错误为 {stats['readOrHashErrors']}，JSON 解析错误为 {stats['jsonParseErrors']}。

独立 map 文件 {stats['standaloneMapFiles']}；内联解码 map {stats['inlineDecodedMaps']}；JSON source map 对象 {stats['jsonSourceMapObjects']}；可取得的 sourcesContent 条目 {stats['sourcesContentEntries']}。这证明冻结发布输入没有可利用的 source map 源码覆盖；原构建环境、远端调试服务或其他未随发布输入提供的 map 是否存在仍未知。包内已有的未打包源码文件另行记录，不能由 map 缺失推断所有源码文件都不存在。

source-map-evidence.jsonl 的 11325 条证据已核对 sourceHash、字节定位边界和引用，marker 总数等于真实注释+误报+未解决数；验证结果见 source-map-validation.json。
'''
    (output / 'dependency-report.md').write_text(report)
    print(json.dumps({'output': str(output), 'records': len(records), 'evidence': len(evidence)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
