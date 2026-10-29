"""Append reviewed MODE/objc evidence and explicitly proposed maintenance paths."""
import hashlib
import json
from pathlib import Path

from contract_reader_context import PROFILES, build_context

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASELINE


def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


names = ['report.md', 'analysis-state.json', 'implementation-plan.md', 'gaps.md',
         'dependency-import-decisions.md', 'chatgpt-mode-boundary-summary.md']
before = {name: (OUT / name).read_bytes() for name in names}
readme_before = (ROOT / 'README.md').read_bytes()
assert pin(before['report.md']) == {'bytes': 45791, 'sha256': '25bf85c75e82118fe7a92110c636cc3246de98abbebc4d47a567cf7afc1ffcab'}
assert pin(before['analysis-state.json']) == {'bytes': 134907, 'sha256': '0dd7fd3135d73e0f7ed639819a6e3348b6596d1dfe72b4c3e306aee02b7ec8af'}
old_state = json.loads(before['analysis-state.json'])
assert old_state['fullAnalysisCompleted'] is False and old_state['featureDenominatorEstablished'] is False
patch, _, artifacts = build_context(OUT, BASELINE)
new_keys = ['modeTransitionOrigin', 'objcModificationContracts']
assert len(patch) == 9 and all(key not in old_state for key in new_keys)
assert all(old_state[key] == value for key, value in patch.items() if key not in new_keys)

mode_path = 'raw/mode-transition-origin/author/mode-transition-origin-contracts.json'
objc_path = 'raw/objc-modification-contracts/author/objc-modification-contracts.json'
mode = json.loads((OUT / mode_path).read_bytes())
objc = json.loads((OUT / objc_path).read_bytes())


def source_ref(path, values, key, index):
    unit = values[index]
    return {'artifact': path, 'artifactPin': pin((OUT / path).read_bytes()),
            'pointer': '/' + key + '/' + str(index),
            'sourceUnitId': unit.get('unitId', unit.get('id')),
            'sourcePath': unit['sourcePath'], 'sourceHash': unit['sourceHash']}


specs = [
    ('MODE-TRANSITION', 'apps/desktop/src/renderer/mode/transition.ts',
     'Mode transition guard and ordered state writes; retain supplied store and atoms.', mode_path, mode['sourceUnits'], 'sourceUnits', [0]),
    ('MODE-RESOLVER', 'apps/desktop/src/renderer/mode/resolver.ts',
     'Access-sensitive mode resolution, including persisted value passthrough.', mode_path, mode['sourceUnits'], 'sourceUnits', [3]),
    ('MODE-STATE', 'apps/desktop/src/renderer/mode/state.ts',
     'Selected state declarations/initialization; actual store/provider ownership remains unresolved.', mode_path, mode['sourceUnits'], 'sourceUnits', [4, 5]),
    ('NATIVE-WINDOW-EVENTS', 'apps/desktop/src/main/native/window-events.ts',
     'First-party window scroll monitor registration and normal-path removal.', objc_path, objc['selectedUnits'], 'selectedUnits', [24]),
    ('NATIVE-NOTIFICATIONS', 'apps/desktop/src/main/native/notifications.ts',
     'First-party notification permission callback, center cache and RunLoop reference management.', objc_path, objc['selectedUnits'], 'selectedUnits', [25, 26, 27]),
    ('NATIVE-APPLE-EVENTS', 'apps/desktop/src/worker/native/apple-events.ts',
     'First-party Apple Event wrapper factories; no event execution proven.', objc_path, objc['selectedUnits'], 'selectedUnits', [28]),
]
proposals = []
for identifier, path, responsibility, artifact, units, key, indices in specs:
    proposals.append({'id': identifier, 'proposedPath': path, 'responsibility': responsibility,
                      'status': 'proposal', 'confidence': 'inferred', 'modeOwnership': 'unknown',
                      'sourceRefs': [source_ref(artifact, units, key, index) for index in indices],
                      'limitations': ['New maintenance design, not original source directory recovery.',
                                      'Selected source units do not establish complete consumer closure or runtime parity.']})
mapping = {'schemaVersion': 1, 'baselineId': BASELINE, 'status': 'bounded-maintenance-proposal',
           'proposals': proposals, 'proposalCount': 6, 'sourceUnitReferences': 9,
           'relationshipToEarlierProposals': 'Separate supplement; original 11 proposals and 8 app-host proposals unchanged.',
           'thirdPartyBoundary': 'objc-js implementation stays in dependency management; these paths represent first-party wrappers.',
           'fullSourceModuleDenominator': 'unknown', 'globalRecordsAdded': 0,
           'runtimeRunsAdded': 0, 'confirmedChatGptExclusionsAdded': 0, 'fullAnalysisCompleted': False}
for row in proposals:
    for ref in row['sourceRefs']:
        source = json.loads((OUT / ref['artifact']).read_bytes())
        _, key, index = ref['pointer'].split('/')
        selected = source[key][int(index)]
        assert selected.get('unitId', selected.get('id')) == ref['sourceUnitId']
        assert selected['sourcePath'] == ref['sourcePath'] and selected['sourceHash'] == ref['sourceHash']
assert sum(len(row['sourceRefs']) for row in proposals) == 9
mapping_bytes = encode(mapping)
table = '\n'.join('| `' + row['proposedPath'] + '` | ' + row['responsibility'] + ' | ' + str(len(row['sourceRefs'])) + ' |'
                  for row in proposals)
mapping_md = '''# 已审查来源到维护路径的补充建议

固定基线 `''' + BASELINE + '''`。以下6条为新维护设计，confidence=inferred，不是原作者目录，也不增加已确认功能或模式归属。9个来源单位引用保留发布文件哈希和已固定合同中的精确JSON位置。

| 拟议路径 | 职责 | 来源单位引用 |
| --- | --- | ---: |
''' + table + '''

[机器映射](source-contract-module-proposals.json)可回到完整source locator；[模式合同](mode-transition-origin-summary.md)和[原生适配边界](objc-modification-contracts-summary.md)给出已审查范围。MODE state的实际provider／存储所有权继续待调查，不能从键名推定localStorage。objc-js库实现由依赖包引入，仅恢复应用自己的wrapper、条件和生命周期。

原11条模块建议与8条app-host建议保持各自范围，不把不同合同的重复表示相加为完整模块分母。消费者闭包、模式归属、实际运行和最终工程结构尚未完成；这些路径仍需随着证据修订。
'''
new_state = {**old_state, **{key: patch[key] for key in new_keys},
             'sourceContractModuleProposals': {'path': 'source-contract-module-proposals.json',
                                             **pin(mapping_bytes), 'proposals': 6, 'sourceUnitReferences': 9,
                                             'confidence': 'inferred', 'fullAnalysisCompleted': False}}
assert all(new_state[key] == value for key, value in old_state.items())
notes = '\n\n'.join(profile[4] for profile in PROFILES if profile[0] in new_keys)
notes += '\n\n[来源到维护路径补充](source-contract-module-proposals.md)提出6个renderer/main/worker职责边界和9个来源单位引用，全部proposal/inferred。原11条与8条app-host建议保持，最终模块分母与工程结构仍未知。'
marker = '[完成标准审计](criteria-audit.md)'
report = before['report.md'].decode()
assert report.count(marker) == 1 and notes not in report
planned = {'report.md': report.replace(marker, notes + '\n\n' + marker).encode(),
           'analysis-state.json': encode(new_state), 'source-contract-module-proposals.json': mapping_bytes,
           'source-contract-module-proposals.md': mapping_md.encode()}
supplements = {
    'implementation-plan.md': '\n[来源到维护路径补充](source-contract-module-proposals.md)将所选模式切换／解析／初始化与窗口事件、通知／RunLoop、Apple Event wrapper提出6个职责路径。路径来自职责和进程边界，全部为proposal/inferred；9个来源单位有固定hash与JSON定位，不代表整chunk恢复。第三方objc-js源码通过依赖引入，第一方wrapper单独维护；状态provider、完整调用闭包及运行验收继续调查。\n',
    'dependency-import-decisions.md': '\n[objc-js来源与替换边界](objc-modification-contracts-summary.md)核对所选9文件与官方1.5.0一致，binary差异与ABI来源继续单列。当前没有修改这两个native源文件或维护source fork的依据；应固定官方来源，分别验证独立构建与窗口事件／通知／Apple Event adapter。原peer仅审静态单位，不能据同版本或导出名直接认定可替换。\n',
    'chatgpt-mode-boundary-summary.md': '\n[模式切换来源补充](mode-transition-origin-summary.md)将两处Jo调用接到jqn/gS及初始化、lPt。gS无值域校验，lPt有两处原样返回persistedMode；chat/work实参和codex字面缺失不能限定全局域。e导入身份用新增保存metadata有限关闭，工厂／存储、真实运行与Codex归属继续未知，原9模块及排除0不改。\n',
}
for name, extra in supplements.items():
    assert extra not in before[name].decode()
    planned[name] = before[name] + extra.encode()
gap_extra = '\n[模式切换来源](mode-transition-origin-summary.md)补上真实gS、初始化及lPt透传边界；完整模式域、存储和Codex归属仍待调查（GAP-03）。[objc-js源码边界](objc-modification-contracts-summary.md)将源码相同与binary差异分开，保留callback正常路径、ABI及独立构建／行为缺口（GAP-07、08）。[6条维护路径建议](source-contract-module-proposals.md)是独立补充，原模块建议分母不改。\n'
gaps = before['gaps.md'].decode()
table_at = gaps.index('\n| ')
planned['gaps.md'] = (gaps[:table_at] + gap_extra + gaps[table_at:]).encode()
readme_extra = '\n- [模式切换、状态与完整模式域的待验证边界](analysis/' + BASELINE + '/mode-transition-origin-summary.md)\n- [objc-js源码、原生二进制与第一方适配边界](analysis/' + BASELINE + '/objc-modification-contracts-summary.md)\n- [已审查源码到6条维护路径的补充建议](analysis/' + BASELINE + '/source-contract-module-proposals.md)\n'
readme_after = readme_before + readme_extra.encode()

snapshots = {'raw/source-contracts/reader-before-' + name: raw for name, raw in before.items()}
snapshots['raw/source-contracts/reader-before-README.md'] = readme_before
all_payloads = {**snapshots, **planned}
for relative, raw in all_payloads.items():
    target = OUT / relative
    assert target.resolve().is_relative_to(OUT.resolve()) and not target.is_symlink()
    if relative in before:
        assert target.read_bytes() == before[relative]
    else:
        assert not target.exists() or target.read_bytes() == raw
assert (ROOT / 'README.md').read_bytes() == readme_before
for relative, raw in snapshots.items():
    target = OUT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_bytes(raw)
    target.chmod(0o444)
for relative, raw in planned.items():
    target = OUT / relative
    temporary = target.with_name('.source-contracts-' + target.name)
    assert not temporary.exists()
    temporary.write_bytes(raw)
    temporary.chmod(target.stat().st_mode & 0o777 if target.exists() else 0o444)
    temporary.replace(target)
    assert target.read_bytes() == raw
temporary = ROOT / '.source-contracts-README.md'
assert not temporary.exists()
temporary.write_bytes(readme_after)
temporary.chmod((ROOT / 'README.md').stat().st_mode & 0o777)
temporary.replace(ROOT / 'README.md')
print(json.dumps({'status': 'integrated', 'companionIndices': 9, 'newStateFields': new_keys + ['sourceContractModuleProposals'],
                  'oldStateValuesPreserved': True, 'proposalCount': 6, 'sourceUnitReferences': 9,
                  'snapshots': {name: pin(raw) for name, raw in snapshots.items()},
                  'outputs': {name: pin(raw) for name, raw in planned.items()},
                  'readme': pin(readme_after), 'selectedArtifactPaths': len(artifacts),
                  'globalRecordsAdded': 0, 'runtimeRunsAdded': 0, 'fullAnalysisCompleted': False}))
