"""Normalize existing responsibility owners and selected legacy evidence, without target execution."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'
WORK = ROOT / '.analysis-local/logical-module-contracts-v1-work'
NOW = datetime.now(timezone.utc).isoformat()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def path(name):
    p = Path(name)
    return p if p.is_absolute() else OUT / p


def pin(name):
    p = path(name)
    raw = p.read_bytes()
    return {'path': str(p.relative_to(ROOT)), 'bytes': len(raw), 'sha256': digest(raw)}


def read(name):
    return json.loads(path(name).read_text())


def ref(name, pointer):
    value = read(name)
    for token in pointer[1:].split('/') if pointer else []:
        token = token.replace('~1', '/').replace('~0', '~')
        value = value[int(token)] if isinstance(value, list) else value[token]
    return {**pin(name), 'jsonPointer': pointer}


def publish(name, raw):
    p = path(name)
    with p.open('xb') as handle:
        handle.write(raw)
    p.chmod(0o444)
    return pin(p)


def distinct(values):
    return list(dict.fromkeys(values))


def main():
    assert not path('logical-module-contracts-v1.json').exists()
    WORK.mkdir(parents=True, exist_ok=True)
    for name in ['analysis-state.json', 'report.md', 'gaps.md']:
        (WORK / (name + '.before')).write_bytes(path(name).read_bytes())
    catalog = read('logical-module-inventory-v1.json')
    ownership = read('logical-module-ownership-v1.json')
    state = read('analysis-state.json')
    required = catalog['requiredFields']
    assert len(required) == 10 and len(ownership['responsibilityOwners']) == 37
    proposals = {r['id']: (i, r) for i, r in enumerate(catalog['records'])}
    owners = ownership['responsibilityOwners']
    assigned = {a['proposalId']: a['ownerId'] for a in ownership['proposalAssignments']}
    source_units, unit_index = [], {}
    files = {}

    def source_unit(proposal_index, range_index, raw):
        source_path = raw['sourcePath']
        if source_path not in files:
            data = (FROZEN / source_path.removeprefix('app.asar/')).read_bytes()
            assert digest(data) == raw['sourceHash']
            files[source_path] = data
        data = files[source_path]
        span = raw['byteRange']
        assert 0 <= span['start'] < span['endExclusive'] <= len(data)
        span_hash = digest(data[span['start']:span['endExclusive']])
        assert span_hash == raw['verifiedSpanHash']
        key = (source_path, span['start'], span['endExclusive'])
        origin = ref('logical-module-inventory-v1.json', f'/records/{proposal_index}/sourceRanges/{range_index}')
        if key not in unit_index:
            unit_index[key] = len(source_units)
            source_units.append({'id': f'LMC-SOURCE-{len(source_units)+1:03d}',
                                 'sourcePath': source_path, 'sourceHash': raw['sourceHash'],
                                 'byteRange': span, 'spanHash': span_hash, 'inheritedOrigins': [],
                                 'qualification': 'Identity-checked inherited evidence locator; not an exclusive implementation assignment or a new source analysis.'})
        unit = source_units[unit_index[key]]
        if origin not in unit['inheritedOrigins']:
            unit['inheritedOrigins'].append(origin)
        return unit['id']

    path_changes = {
        'LM-RUNTIME-RF-1': 'apps/desktop/src/main/runtime/runtime-feature-policy.ts',
        'LM-RUNTIME-RF-2': 'apps/desktop/src/main/runtime/runtime-feature-provider.ts',
        'LM-RUNTIME-RF-3': 'apps/desktop/src/renderer/runtime/runtime-feature-gates.ts',
        'LM-SETTINGS-0': 'apps/desktop/src/renderer/settings/asset-registry.ts',
        'LM-SETTINGS-1': 'apps/desktop/src/renderer/settings/page-factory-registry.ts',
        'LM-SETTINGS-2': 'apps/desktop/src/renderer/settings/sections-and-visibility.ts',
        'LM-SETTINGS-3': 'apps/desktop/src/renderer/settings/route-policy-and-renderer.tsx',
    }
    # Explicit references to already reviewed source boundaries. A candidate package
    # row is not proof that every owner consumes that package or version.
    dep_rows = read('dependency-investigation-actions-v1.json')['rows']

    def dependency_row(index, relationship):
        r = dep_rows[index]
        return {'name': r['name'], 'dependencyId': r['dependencyId'],
                'relationship': relationship,
                'versionAndInvestigation': ref('dependency-investigation-actions-v1.json', f'/rows/{index}'),
                'acceptedExactDependency': False}

    updates = {
        'LM-BOUNDARY-STRUCT-RWC-MANAGER': [ref('resume-provider-resolution.json', '/providerBranches'), ref('host-dispatch-roles-v1.json', '')],
        'LM-BOUNDARY-STRUCT-RWC-HOST-TRANSPORT': [ref('host-dispatch-roles-v1.json', '')],
        'LM-BOUNDARY-STRUCT-RWC-PROJECTS': [ref('project-local-delegation-v1.json', '/decision'), ref('storage-domain-map-v1.json', '/domains/3')],
        'LM-SOURCE-MODE-STATE': [ref('mode-persistence-receiver.json', '/records'), ref('storage-domain-map-v1.json', '/domains/8')],
        'LM-PROVIDER-internal-manager-rpc-adapter': [ref('resume-provider-resolution.json', '/providerBranches')],
        'LM-PROVIDER-host-provided-rpc-adapter': [ref('resume-provider-resolution.json', '/providerBranches')],
    }
    rows, facts = [], []
    for oi, owner in enumerate(owners):
        oid = owner['ownerId']
        members = [proposals[x] for x in owner['memberProposalIds']]
        owner_ref = ref('logical-module-ownership-v1.json', f'/responsibilityOwners/{oi}')
        module_refs = [ref('logical-module-inventory-v1.json', f'/records/{i}') for i, _ in members]
        ranges = distinct([source_unit(i, j, r) for i, member in members for j, r in enumerate(member['sourceRanges'])])
        overlap_refs = [ref('logical-module-ownership-v1.json', f'/overlapDecisions/{i}')
                        for i, d in enumerate(ownership['overlapDecisions'])
                        if oid in {assigned[d['left']], assigned[d['right']]} or d.get('implementationOwner') == oid]
        bindings = []
        for i, member in members:
            for key, surface in [('imports', 'contractDependencies'), ('exports', 'observedContractSurface')]:
                bindings.append({'direction': key, 'contract': member[key][surface],
                                 'basis': ref('logical-module-inventory-v1.json', f'/records/{i}/{key}')})
        dependencies = []
        extra = list(updates.get(oid, []))
        if oid.startswith('LM-SOURCE-NATIVE-'):
            dependencies.append(dependency_row(125, 'Named objc-js import boundary in this saved native adapter; shipped package metadata is not target ABI/behavior acceptance.'))
            extra.append(ref('runtime-adoption-matrix-v1.json', '/nativeDependencyJoins'))
        if oid in ['LM-BOUNDARY-STRUCT-browser-annotation-lifecycle', 'LM-BOUNDARY-STRUCT-browser-annotation-root']:
            dependencies.extend(dependency_row(i, 'Saved browser-preload package candidate; exact lock, library modification and wrapper consumer closure remain open.') for i in [186, 187])
            extra.append(ref('dependency-import-decisions.json', '/decisions'))
        if oid.startswith('LM-SETTINGS-'):
            dependencies.extend(dependency_row(i, 'Containing shared renderer bundle package candidate, not an exact dependency assignment for this proposed split.') for i in [193, 194])
            extra.append(ref('entry-composition-roles-v1.json', ''))
        if oid.startswith('LM-RUNTIME-'):
            dependencies.append(dependency_row(195 if oid.endswith('3') else 188,
                                               'Saved SDK-family boundary; public Statsig is not accepted as a replacement for the private fork.'))
            extra.append(ref('runtime-feature-policy-contracts.json', '/maintenanceDecision'))
            extra.append(ref('runtime-adoption-matrix-v1.json', ''))
        if oid in ['LM-APPHOST-AH-M07', 'LM-APPHOST-AH-M08']:
            extra.append(ref('runtime-adoption-matrix-v1.json', ''))
        builtin = []
        if oid.startswith('LM-CONTEXT-'):
            builtin.append({'specifier': 'node:async_hooks', 'kind': 'runtime-builtin',
                            'npmPackageRequired': False, 'targetRuntimeAcceptance': 'unverified'})
        paths = [path_changes[oid]] if oid in path_changes else owner['proposedPaths']
        row = {
            'ownerId': oid, 'proposalIds': owner['memberProposalIds'],
            'responsibility': {'value': owner['responsibility'], 'confidence': 'inferred', 'basis': owner_ref},
            'environment': {'sourcePlacements': [member['environment'] for _, member in members],
                            'maintenancePlacement': paths,
                            'qualification': 'Selected source placement and proposed ownership; actual live provider instance remains unobserved.'},
            'mode': {'value': 'unknown', 'disposition': 'retain',
                     'reason': 'These inputs do not prove whole-owner ChatGPT-only consumer closure.'},
            'sourceRanges': ranges,
            'imports': {'contractInputs': [x for x in bindings if x['direction'] == 'imports'],
                        'sharedOwnershipRules': overlap_refs, 'exactEsmImportClosure': False,
                        'qualification': 'A composition/import witness is not authority to copy every dependency or helper.'},
            'exports': {'observedSurfaces': [x for x in bindings if x['direction'] == 'exports'],
                        'originalEsmExportsRecovered': False, 'completeConsumerClosure': False,
                        'interfaceRule': 'Preserve the referenced argument/result/error/cancellation contract; new source names and final types are implementation decisions.'},
            'sharedState': {'contracts': [member['sharedState'] for _, member in members],
                            'ownershipRules': overlap_refs, 'completeOwnershipClosure': False},
            'sideEffects': {'contracts': [member['sideEffects'] for _, member in members],
                            'compositionRules': overlap_refs, 'actualExecutionObservedHere': False},
            'thirdPartyDependencies': {'inheritedBoundaryRefs': [ref('logical-module-inventory-v1.json', f'/records/{i}/thirdPartyDependencies') for i, _ in members],
                                       'namedPackageLinks': dependencies, 'runtimeBuiltins': builtin,
                                       'exactDependencyClosure': False, 'generateVendorImplementation': False,
                                       'rule': 'Only the reviewed first-party wrapper is proposed for reconstruction. Unknown helpers retain unresolved provenance; candidate package rows are not automatic import/lock choices.'},
            'proposedPath': {'values': paths, 'basis': owner_ref,
                             'normalization': 'Place the saved responsibility under its reviewed main/renderer environment.' if oid in path_changes else owner['pathDecision'],
                             'status': 'inferred-maintenance-design; not original source recovery'},
            'taskOwnership': {'foundation': owner['primaryFoundationTask'],
                              'conditionalConsumerJoins': copy.deepcopy(owner['consumerTaskJoins']),
                              'allConsumersAssigned': False, 'remaining': owner['consumerJoinGap']},
            'currentContractRefinements': extra,
            'historyRule': 'Historical proposal unknowns are not copied as current blockers; newer pinned refinements qualify only their stated source scope.',
            'completeSourcePartitionProven': False,
            'runtimeValidated': False, 'clientImplementationGenerated': False,
            'evidenceId': f'LMC-OWNER-{oi+1:03d}', 'proposalEvidence': module_refs,
        }
        if oid == 'LM-BOUNDARY-STRUCT-RWC-PROJECTS':
            row['taskOwnership']['currentLocalDelegateDecision'] = ref('project-local-delegation-v1.json', '/decision')
            row['taskOwnership']['remaining'] = 'The saved local Ke -> j$t delegate identity is resolved by the pinned refinement; complete project consumers, confirmation/persistence integration and mode remain unresolved.'
        rows.append(row)
        facts.append({'id': row['evidenceId'], 'baselineId': BASE,
                      'claim': 'Existing responsibility normalized with plan-required fields, source references, bounded interfaces, shared ownership and dependency qualifications: ' + oid,
                      'sourcePath': owner_ref['path'], 'sourceHash': owner_ref['sha256'],
                      'locator': {'jsonPointer': owner_ref['jsonPointer']},
                      'method': 'inference', 'confidence': 'inferred',
                      'verificationStatus': 'maintenance-design-only; inherited-source-identities-checked; no-new-runtime-or-product-acceptance'})

    legacy = [json.loads(line) for line in path('request-entry-unmatched-review-evidence.jsonl').read_text().splitlines()]
    normalized = []
    for index, original in enumerate(legacy):
        item = copy.deepcopy(original)
        raw = (FROZEN / item['sourcePath'].removeprefix('app.asar/')).read_bytes()
        span = item['locator']
        assert digest(raw) == item['sourceHash'] and digest(raw[span['start']:span['endExclusive']]) == item['spanSha256']
        item['method'] = 'inference'
        item['confidence'] = 'inferred'
        item['verificationStatus'] = 'inherited-bounded-AST-review; source-range-identity-rechecked; no-runtime-or-complete-feature-claim'
        item['normalizationOrigin'] = {**pin('request-entry-unmatched-review-evidence.jsonl'), 'line': index + 1,
                                       'originalMethod': original['method'], 'originalConfidence': original['confidence']}
        normalized.append(item)
    unmatched_pin = publish('request-entry-unmatched-review-evidence-normalized-v1.jsonl',
                            ''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in normalized).encode())

    receiver = read('mode-persistence-receiver.json')['records']
    receiver_normalized = []
    for index, original in enumerate(receiver):
        raw = (FROZEN / original['sourcePath'].removeprefix('app.asar/')).read_bytes()
        span = original['byteRange']
        assert digest(raw) == original['sourceSha256'] and digest(raw[span['start']:span['endExclusive']]) == original['spanSha256']
        receiver_normalized.append({'id': original['id'], 'baselineId': BASE, 'claim': original['claim'],
                                    'sourcePath': original['sourcePath'], 'sourceHash': original['sourceSha256'],
                                    'locator': span, 'spanHash': original['spanSha256'],
                                    'method': 'inference' if original['confidence'] == 'inferred' else 'static-code',
                                    'confidence': original['confidence'],
                                    'verificationStatus': 'inherited-selected-source-contract; source-range-identity-rechecked; target-runtime-not-executed',
                                    'normalizationOrigin': ref('mode-persistence-receiver.json', f'/records/{index}')})
    receiver_pin = publish('mode-persistence-receiver-evidence-normalized-v1.jsonl',
                           ''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in receiver_normalized).encode())
    correction = {'schemaVersion': 1, 'baselineId': BASE,
                  'scope': 'Only the 38 unmatched journal rows identified in the stage audit and the 12 saved main receiver rows; no global legacy-journal census claim.',
                  'unmatched': {'original': pin('request-entry-unmatched-review-evidence.jsonl'), 'effectiveEvidence': unmatched_pin,
                                'count': len(legacy), 'rule': 'Claims, IDs, source coordinates and hashes preserved; compound confidence conservatively lowered to inferred and verificationStatus added.'},
                  'mainReceiver': {'original': pin('mode-persistence-receiver.json'), 'effectiveEvidence': receiver_pin,
                                   'count': len(receiver), 'rule': 'Field aliases normalized and baseline/method/verificationStatus added; claims, confidence and original records preserved.'},
                  'oldFilesModified': False, 'newSourceClaims': 0, 'newBehaviorObservations': 0}
    correction_pin = publish('selected-evidence-schema-normalization-v1.json', encoded(correction))
    evidence_pin = publish('logical-module-contracts-v1-evidence.jsonl',
                           ''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in facts).encode())
    input_names = ['logical-module-inventory-v1.json', 'logical-module-ownership-v1.json',
                   'feature-scope-v27.json', 'restoration-coverage-v18.json', 'feature-scope-v24-scenarios.json',
                   'dependency-investigation-actions-v1.json', 'runtime-adoption-matrix-v1.json',
                   'storage-domain-map-v1.json', 'project-local-delegation-v1.json',
                   'request-entry-unmatched-review-evidence.jsonl', 'mode-persistence-receiver.json']
    doc = {'schemaVersion': 1, 'baselineId': BASE, 'recordedAtUtc': NOW,
           'scope': 'Fixed 37 provisional responsibility owners from 38 saved proposals; this is not the full-client module denominator.',
           'requiredFields': required, 'records': rows, 'sourceUnits': source_units,
           'overlapPolicy': ref('logical-module-ownership-v1.json', '/overlapDecisions'),
           'publishedFileInventory': {'records': 438, 'source': pin('modules.json'), 'meaning': 'Published files, not original source modules or these 37 maintenance owners.'},
           'journalNormalization': correction_pin, 'evidence': evidence_pin,
           'boundedClosure': 'All 37 existing owners have explicit plan-required fields, source identities and unresolved closure flags; the selected 50 old records now have normalized evidence views. This closes this formatting/integration substep only.',
           'remaining': ['Complete first-party source partition and all consumers are not established by this finite saved-proposal set.',
                         'Unknown mode, live provider identity, exact package locks and native/runtime effects remain in SD-01/02/03/05.',
                         'Unexecuted product scenarios are not promoted by reference or schema checks.'],
           'counts': {'proposalRecords': 38, 'responsibilityOwners': len(rows), 'requiredFieldsPerOwner': len(required),
                      'uniqueInheritedSourceUnits': len(source_units), 'sourceFilesIdentityChecked': len(files),
                      'overlapRulesJoined': 19, 'placementPathsNormalized': len(path_changes),
                      'normalizedLegacyEvidenceRecords': len(normalized) + len(receiver_normalized),
                      'newOriginalSourceParses': 0, 'newReaRuns': 0, 'newModelSubmissions': 0,
                      'newClientLaunches': 0, 'newProductScenarioPasses': 0, 'newClientImplementation': 0},
           'inputPins': [pin(n) for n in input_names] + [pin(Path(__file__)), pin(ROOT / 'docs/reverse-engineering/analysis-plan.md')],
           'fullAnalysisCompleted': False, 'implementationReady': False}
    contracts_pin = publish('logical-module-contracts-v1.json', encoded(doc))
    lines = ['# 逻辑模块合同与维护边界', '',
             '现有38条提案已统一为37个职责单元；每个单元明确职责、环境、模式、来源、导入、导出、共享状态、副作用、第三方依赖及拟议路径。它们是维护设计，不是恢复出的原作者模块，也不是完整客户端模块分母。', '',
             '沿用19项源码重叠决定：KI selector只维护一份；Vfn/Sii/loi由domain registry承担；X2t与RPC连接生命周期分开；hXe装配范围不复制给每个provider；runtime policy、service与renderer gate分别维护。', '',
             '本次将7条runtime/settings建议路径按main/renderer职责放入统一目录。此前已纠正的renderer fetch与main fetch、project跨进程三文件边界继续有效。项目本地delegate的旧待查状态由已保存的来源结论替代，完整集成仍未验证。', '',
             '|职责单元|拟议维护路径|基础任务|', '|---|---|---|']
    for row in rows:
        lines.append('|' + row['ownerId'] + '|' + '<br>'.join(row['proposedPath']['values']) + '|' + row['taskOwnership']['foundation']['taskId'] + '|')
    lines += ['', '## 第三方与接口', '',
              '仅已有明确边界的objc-js、browser annotation React/DOM和Statsig家族接入对应依赖调查记录。含包候选的bundle不代表每个逻辑模块都直接消费该包；实际锁定版本、修改状态和RPC等opaque helper来源仍需核实。node:async_hooks作为runtime builtin，不新增npm替代实现。', '',
              '导入字段记录合同输入和共享职责规则；导出字段保留已观察的接口。完整ESM导入导出、所有consumer及运行实例没有被字段齐全所证明；最终类型和新源码命名留给实施阶段依据合同确定。', '',
              '## 证据格式与分析出口', '',
              '38条旧unmatched journal补齐verificationStatus，将复合confidence保守规范为inferred；12条main receiver记录补齐基线、来源哈希别名、method和验证状态。原文件、结论及来源坐标保留，规范视图共50条，未增加源码或行为通过项。', '',
              '本轮关闭37单元字段整合和这50条格式缺口；不能据此关闭整个SD-06或原计划九项标准。后续定向调查转向SD-02的input-shape owner/consumer：已有运行时取舍明确保留这一内部源码缺口，应先追消费者再选平台provider。无需新增客户端或模型调用。', '',
              '[结构化合同](logical-module-contracts-v1.json)、[职责推断](logical-module-contracts-v1-evidence.jsonl)、[证据规范映射](selected-evidence-schema-normalization-v1.json)。', '']
    summary_pin = publish('logical-module-contracts-v1.md', '\n'.join(lines).encode())
    overlay = {'contracts': contracts_pin, 'summary': summary_pin, 'evidence': evidence_pin,
               'journalNormalization': correction_pin, 'counts': doc['counts'],
               'qualification': doc['boundedClosure'], 'fullAnalysisCompleted': False}
    state['logicalModuleInventory']['currentContractView'] = overlay
    state['logicalModuleContracts'] = overlay
    state['stageDecisions']['logicalModuleContractOverlay'] = overlay
    state['stageDecisions']['nextAction'] = {
        'issueId': 'SD-02', 'question': '追踪运行时input-shape接口的第一方owner、调用消费者与平台/模式条件。',
        'closure': '从冻结源码的接口调用绑定到具体功能职责及参数/返回/清理合同；界定runtime provider缺口。避免重复已完成的接口存在性枚举。',
        'authorization': '只读冻结源码及自有分析脚本；无新增模型、客户端或个人数据操作。'}
    state['stageDecisions']['selectedEvidenceNormalization'] = correction_pin
    state['modePersistenceReceiver']['normalizedEvidence'] = receiver_pin
    state['pending'] = [
        'SD-06: 现有37职责单元的10项模块字段、19重叠规则和当前任务/合同引用已统一；选定38+12旧证据已补规范视图。完整模块分母、消费者/模式及运行时/后台依赖仍未闭合；438发布文件不作源码模块计数。'
        if isinstance(item, str) and item.startswith('SD-06:') else item for item in state['pending']]
    state['updatedAtUtc'] = NOW
    path('analysis-state.json').write_bytes(encoded(state))
    lead = '当前[逻辑模块合同](logical-module-contracts-v1.md)将38提案归并的37职责单元统一为计划要求的10项字段，接入19重叠规则并规范50条旧证据；7条runtime/settings路径按运行环境统一。字段齐全不证明完整模块/消费者/模式或运行验收。下一内部项为SD-02 input-shape owner/consumer定向追踪；373功能、48任务、1216未执行规格及授权次数保持，完整分析未完成。前项[存储职责](storage-domain-map-v1.md)与[运行时取舍](runtime-adoption-matrix-v1.md)继续有效。'
    for name in ['report.md', 'gaps.md']:
        previous = path(name).read_text()
        _, tail = previous.split('\n\n', 1)
        path(name).write_text(lead + '\n\n' + tail)
    publication = {'contracts': contracts_pin, 'summary': summary_pin, 'evidence': evidence_pin,
                   'journalNormalization': correction_pin, 'counts': doc['counts']}
    (WORK / 'publication.json').write_bytes(encoded(publication))
    print(json.dumps(publication, ensure_ascii=False))


if __name__ == '__main__':
    main()
