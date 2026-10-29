"""Classify the eleven saved differing protocol variants into explicit adoption decisions."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/protocol-delta-adoption-work'
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'
sha = lambda b: hashlib.sha256(b).hexdigest()
encode = lambda x: (json.dumps(x, ensure_ascii=False, indent=2) + '\n').encode()
read = lambda p: json.loads(p.read_text())
NOW = datetime.now(timezone.utc).isoformat()


def pin(path):
    p = Path(path)
    if not p.is_absolute():
        p = OUT / p
    raw = p.read_bytes()
    return {'path': str(p.relative_to(ROOT)), 'bytes': len(raw), 'sha256': sha(raw)}


def publish(name, raw):
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write(raw)
    p.chmod(0o444)
    return pin(p)


def main():
    assert not (OUT / 'protocol-delta-adoption-v1.json').exists()
    for name in ['analysis-state.json', 'report.md', 'gaps.md']:
        with (WORK / (name + '.before')).open('xb') as f:
            f.write((OUT / name).read_bytes())
    comparison = read(OUT / 'exported-protocol-comparison.json')
    manifests = {k: read(OUT / v) for k, v in [('public', 'public-protocol-generation-npm.json'), ('frozen', 'protocol-generation.json')]}
    schemas, variants, facts = {}, [], []

    def schema(mode, side, name):
        key = (mode, side, name)
        if key not in schemas:
            p = Path(comparison['comparisons'][mode][side+'SchemaRoot']) / name
            current = pin(p)
            relative = f'schema/{mode}/{name}' if side == 'public' else f'{mode}/{name}'
            matches = [(i, j, x) for i, r in enumerate(manifests[side]['runs']) for j, x in enumerate(r['schemaFiles']) if x['path'] == relative]
            assert len(matches) == 1
            i, j, recorded = matches[0]
            assert recorded['sha256'] == current['sha256'] and recorded['bytes'] == current['bytes']
            schemas[key] = {'pin': current, 'manifestPointer': f'/runs/{i}/schemaFiles/{j}', 'value': read(p)}
        return schemas[key]

    def fact(eid, claim, source, locator, **extra):
        row = {'id': eid, 'baselineId': BASE, 'claim': claim, 'sourcePath': source['path'], 'sourceHash': source['sha256'],
               'locator': locator, 'method': 'static-code', 'confidence': 'confirmed',
               'verificationStatus': 'saved-schema-or-selected-source-confirmed; actual-service-and-product-acceptance-unverified', **extra}
        facts.append(row)
        return eid

    for mode, part in comparison['comparisons'].items():
        for index, row in enumerate(part['variantContracts']):
            if row['effectiveContract']['status'] != 'different':
                continue
            pub = schema(mode, 'public', row['union'])
            old = schema(mode, 'frozen', row['union'])
            eid = f'PDA-{len(variants)+1:02d}'
            is_notification = row['union'] == 'ServerNotification.json'
            pointer = '/definitions/ThreadItem/oneOf/11' if is_notification else '/definitions/ThreadForkParams'
            if is_notification:
                a = pub['value']['definitions']['ThreadItem']['oneOf'][11]
                b = old['value']['definitions']['ThreadItem']['oneOf'][11]
                assert a['properties']['type']['enum'] == b['properties']['type']['enum'] == ['subAgentActivity']
                assert a['required'] == b['required'] and not {'model', 'reasoningEffort'} & set(a['required'])
                assert a.get('additionalProperties', True) is not False and b.get('additionalProperties', True) is not False
                assert set(a['properties']) - set(b['properties']) == {'model', 'reasoningEffort'}
                stripped = json.loads(json.dumps(a))
                for k in ['model', 'reasoningEffort']:
                    del stripped['properties'][k]
                assert stripped == b
                assert a['properties']['model']['type'] == ['string', 'null']
                assert {'type': 'null'} in a['properties']['reasoningEffort']['anyOf']
                claim = f'{mode} {row["method"]}引用的subAgentActivity声明在公开候选中只增加可选且可null的model、reasoningEffort，required与旧字段保持一致。此处验证生成schema，不证明客户端实际解码器或通知运行。'
                decision_id = 'PDA-D01'
            else:
                assert mode == 'experimental' and row['method'] == 'thread/fork'
                a = pub['value']['definitions']['ThreadForkParams']
                b = old['value']['definitions']['ThreadForkParams']
                assert 'experimentalPredictionMode' not in a['properties']
                assert b['properties']['experimentalPredictionMode']['type'] == 'boolean'
                assert 'experimentalPredictionMode' not in b['required']
                stripped = json.loads(json.dumps(b))
                del stripped['properties']['experimentalPredictionMode']
                assert stripped == a
                claim = 'experimental thread/fork的冻结声明含可选boolean experimentalPredictionMode，公开候选无此字段；删除该字段后两份ThreadForkParams声明相同。字段缺失不证明服务具备相同预测fork语义。'
                decision_id = 'PDA-D02'
            fact(eid, claim, pub['pin'], {'kind': 'json-pointer', 'pointer': pointer},
                 sourceKind='saved-public-cli-generated-schema', frozenCounterpart={**old['pin'], 'pointer': pointer},
                 comparisonPointer=f'/comparisons/{mode}/variantContracts/{index}')
            variants.append({'id': f'PDA-V{len(variants)+1:02d}', 'mode': mode, 'union': row['union'], 'method': row['method'],
                             'comparisonPointer': f'/comparisons/{mode}/variantContracts/{index}', 'factId': eid,
                             'fieldDifferences': row['effectiveContract']['fieldDifferences'], 'decisionId': decision_id,
                             'sourcePins': [pub['pin'], old['pin']]})
    assert len(variants) == 11 and sum(x['decisionId'] == 'PDA-D01' for x in variants) == 10
    inspection = read(WORK / 'inspection.json')
    assert inspection['parse'] == 'complete-Program' and not inspection['targetCodeExecuted']
    units = []

    def source(row, label, span_key='spanHash', range_key='byteRange'):
        raw = (FROZEN / row['sourcePath'].removeprefix('app.asar/')).read_bytes()
        s = row[range_key]
        b = raw[s['start']:s['endExclusive']]
        assert sha(raw) == row['sourceHash'] and sha(b) == row[span_key]
        selection = publish(f'raw/protocol-delta-adoption/{len(units)+1:02d}.js.txt', b)
        u = {'id': f'PDA-SOURCE-{len(units)+1:02d}', 'label': label, 'sourcePath': row['sourcePath'], 'sourceHash': row['sourceHash'],
             'byteRange': {'start': s['start'], 'endExclusive': s['endExclusive']}, 'spanHash': sha(b), 'nodeType': row['nodeType'], 'selection': selection}
        if 'owner' in row:
            u['owner'] = row['owner']
        units.append(u)
        return u

    for row in inspection['units']:
        source(row, row['label'])
    legacy = [json.loads(x) for x in (ROOT / '.analysis-local/protocol-work/evidence.jsonl').read_text().splitlines()]
    for eid, label in [('EXPERIMENTAL-PREDICTION-AST-00006', 'prediction-fge'), ('EXPERIMENTAL-PREDICTION-AST-00125', 'prediction-fork-argument'), ('EXPERIMENTAL-PREDICTION-AST-00136', 'prediction-fork-sender')]:
        source(next(x for x in legacy if x['id'] == eid), label, 'spanSha256', 'locator')
    by_label = {x['label']: x for x in units}
    source_facts = [
        ('PDA-12', 'dispatcher-Vnn', 'Vnn的选定完整函数在buffer/follower/discovery等条件后，将thread/started交unn、turn开始/完成交Rnn、item开始/完成交Ktn，并在后续发出通知；真实实例、helper实现和到达顺序不由该函数证明。'),
        ('PDA-13', 'dispatcher-qtn', 'qtn仅对collabAgentToolCall或imageGeneration做转换，其余对象原样返回；选定subAgentActivity输入因此按同一对象返回并保留新增字段。Ktn item/completed case的源码调用qtn并交后续clone/store，后续效果仍分开验证。'),
        ('PDA-14', 'subagent-display-case', 'd1内选定subAgentActivity显示case只投影id、agentThreadId、kind和agentPath派生字段，并受agentPath过滤及显示开关限制；它不读取新增model或reasoningEffort，不代表所有消费者均忽略这些字段。'),
        ('PDA-15', 'prediction-fge', '选定fge对plan/provider/model资格及experimentalPredictionForkMode版本门槛检查后，传experimentalPredictionMode:true和fallbackToFreshThread:false给预测helper；无据将它改成普通fork或新建线程来保持等价。'),
        ('PDA-16', 'prediction-fork-sender', '选定forkThread sender把传入对象展开到thread/fork params并补默认threadSource；已保存预测调用表达式明确传experimentalPredictionMode:true、ephemeral:true、excludeTurns:true。实际动态实例和后台接收不由同名方法推定。'),
    ]
    for eid, label, claim in source_facts:
        u = by_label[label]
        fact(eid, claim, {'path': u['sourcePath'], 'sha256': u['sourceHash']}, {'kind': 'byte-range', **u['byteRange']}, spanHash=u['spanHash'], sourceKind='frozen-JavaScript')
    replay = read(WORK / 'replay.json')
    assert replay['casesPassed'] == len(replay['cases']) == 8
    replay_pin = publish('protocol-delta-adoption-v1-replay.json', encode(replay))
    evidence = publish('protocol-delta-adoption-v1-evidence.jsonl', ''.join(json.dumps(x, ensure_ascii=False)+'\n' for x in facts).encode())
    decisions = [
        {'id': 'PDA-D01', 'variants': [x['id'] for x in variants if x['decisionId'] == 'PDA-D01'],
         'status': 'conditional-schema-compatible-candidate; full-client-decoding-unverified',
         'decision': 'Retain a tolerant notification boundary and preserve optional extension fields. Missing/null values remain valid. No mandatory-field backfill or model/reasoning UI requirement follows from the frozen contract.',
         'proposedPaths': ['packages/contracts/src/app-server/notifications.ts', 'packages/backend-adapter/src/app-server/notifications.ts'],
         'sourceLimits': 'Selected dispatcher, qtn conversion and one display case are traced; all decode/clone/state/storage consumers and notification delivery are not accepted.',
         'implementationChecks': ['Both old and extended payloads through the chosen real decoder, clone/store and display.', 'Ordering, buffering/drain, duplicate events, reconnect and persistence behavior.']},
        {'id': 'PDA-D02', 'variants': [x['id'] for x in variants if x['decisionId'] == 'PDA-D02'],
         'status': 'public-candidate-not-qualified-for-prediction-fork',
         'decision': 'Preserve prediction fork as a distinct backend capability. Do not delete the flag, silently use ordinary fork, or re-enable fresh-thread fallback. Full fidelity requires the matching backend source/implementation and successful semantic evidence.',
         'proposedPaths': ['packages/contracts/src/app-server/prediction-fork.ts', 'packages/backend-adapter/src/app-server/prediction-fork.ts'],
         'savedNegativeEvidence': {'source': pin('fork-negative-protocol-comparison.json'), 'pointer': '/fieldTreatment',
                                   'qualification': 'Existing missing-rollout negative paths recognize/gate the field only in frozen backend; no successful prediction fork was observed.'},
         'sourceLimits': 'Version-gate eligibility, an ignored unknown field or an ordinary fork success cannot qualify prediction semantics.',
         'implementationChecks': ['Loaded persisted parent and ephemeral/no-override requirements.', 'Effective configuration/tools/environment/history inheritance and cache behavior.', 'Temporary-thread lifecycle, cancellation/cleanup and prediction return semantics.']},
    ]
    counts = {'differentVariantsAssignedExactlyOnce': 11, 'distinctDeltaFamilies': 2, 'optionalNotificationVariants': 10,
              'predictionRequestVariants': 1, 'schemaInputs': len(schemas), 'sourceFacts': len(facts), 'sourceSelections': len(units),
              'distinctNewCompletePrograms': 1, 'reusedSourceSelections': 3, 'isolatedSourceCasesPassed': 8,
              'newServiceCalls': 0, 'newModelSubmissions': 0, 'newClientLaunches': 0, 'newProductScenarioPasses': 0,
              'newFeatureDefinitions': 0, 'featureModeChanges': 0, 'clientImplementationAdded': 0}
    doc = {'schemaVersion': 1, 'baselineId': BASE, 'recordedAtUtc': NOW,
           'scope': 'Exactly the eleven saved differing generated-protocol variants; not a full backend acceptance or new protocol census.',
           'comparison': pin('exported-protocol-comparison.json'), 'variants': variants, 'decisions': decisions, 'facts': facts,
           'sourceUnits': units, 'counts': counts, 'replay': replay_pin, 'evidence': evidence,
           'schemaInputs': [{k: v for k, v in x.items() if k != 'value'} for x in schemas.values()],
           'resolutionBuckets': {'analysisResolvedHere': 'All eleven variant deltas have exact fields, selected consumers and an adoption decision.',
                                 'implementationVerification': 'Chosen decoder/store and successful model/backend/notification behavior.',
                                 'externalInputOrProviderDevelopment': 'Matching prediction-capable backend, npm binary-to-public-commit binding and private service/provider requirements.'},
           'inputPins': [pin(WORK / x) for x in ['inspect.cjs', 'inspection.json', 'replay.cjs', 'replay.json']] +
                        [pin(Path(__file__)), pin(ROOT / '.analysis-local/protocol-work/evidence.jsonl')] +
                        [pin(x) for x in ['protocol-generation.json', 'public-protocol-generation-npm.json', 'experimental-prediction-usage.json',
                                         'prediction-version-gate.json', 'turn-notification-state.json', 'fork-negative-protocol-comparison.json',
                                         'backend-ipc-roles-v1.json', 'feature-scope-v27.json', 'restoration-coverage-v18.json', 'feature-scope-v24-scenarios.json']],
           'fullBackendAdoptionQualified': False, 'fullAnalysisCompleted': False}
    result = publish('protocol-delta-adoption-v1.json', encode(doc))
    summary = publish('protocol-delta-adoption-v1.md', '''# 后台协议差异的采用决定

既有 466 个协议变体中 11 个不同，本次逐一核对这 11 个变体，没有重跑全协议发现。它们实际来自两类字段变化。

| 范围 | 精确差异 | 采用决定 |
| --- | --- | --- |
| stable/experimental 各 5 个通知：item/started、item/completed、thread/started、turn/started、turn/completed | subAgentActivity 增加可选且可 null 的 model、reasoningEffort，旧 required 不变 | 公开候选可继续评估；协议边界保留扩展字段，真实解码/store/通知集成另验 |
| experimental thread/fork | 公开候选缺 experimentalPredictionMode | 公开候选未取得预测 fork 资格；保持独立能力，禁止静默删除参数、普通 fork 替代或新建线程回退 |

对通知，已追到选定分发函数、item 完成处理、qtn 转换及一处显示投影。qtn 对 subAgentActivity 原样返回；显示投影不读取两个新字段。它们支持继续采用候选的局部决定，不证明全部解码、clone、存储、重连与实际通知顺序兼容，也不构成新增显示功能的要求。

预测路径有明确第一方调用：fge 先检查资格与版本，再要求 experimentalPredictionMode:true，且 fallbackToFreshThread:false；fork 调用还带 ephemeral:true、excludeTurns:true。已有两后台负例显示冻结后台识别并门控该字段，公开候选在缺失 rollout 路径上与未知字段类似；这不证明成功预测。版本满足或普通 fork 成功不能替代这项语义。

因此整体公开后台仍未取得完整复刻资格。需要匹配的预测实现或有成功语义证据的独立 provider；不能用删除该能力来宣称完整。npm 二进制与公开源码提交绑定、真实 receiver/服务和其它后台能力仍保留各自缺口。

本次有 16 条来源事实、8 个 JS 源码选择及 8 项隔离检查；没有客户端启动、服务调用或模型提交，未增加产品通过数。源码选择含完整函数和完整 case，不能当作恢复模块数。第三方和后台实现仍按依赖/provider 引入。

11 个变体均已分配到上述决定；下一步把这些决定与已交付运行时、存储、逻辑模块合同合入新版实施依据，明确源码准备、外部输入与实施验收，保留完整范围。

[逐变体决策](protocol-delta-adoption-v1.json)、[来源事实](protocol-delta-adoption-v1-evidence.jsonl)、[隔离检查](protocol-delta-adoption-v1-replay.json)。
'''.encode())
    overlay = {'result': result, 'summary': summary, 'evidence': evidence, 'replay': replay_pin, 'counts': counts,
               'qualification': 'eleven-saved-variant-adoption-decisions-resolved; full-backend-provider-and-behavior-open', 'fullBackendAdoptionQualified': False}
    state = read(OUT / 'analysis-state.json')
    state['protocolDeltaAdoption'] = overlay
    state['publicProtocolComparison']['adoptionDecisionRefinement'] = overlay
    state['stageDecisions']['protocolDeltaAdoptionOverlay'] = overlay
    state['stageDecisions']['nextAction'] = {
        'issueId': 'SD-06', 'question': '将运行时采用、11变体后台决定、存储域和37逻辑模块合同合入新版实施依据。',
        'closure': '保持373功能/48任务范围，逐项标明可准备源码、外部输入或provider开发、实施验证和仍影响架构的未知，回读验证当前证据引用。',
        'authorization': '已保存分析产物和自有文档/脚本；不启动客户端、模型服务或读取个人数据。'}
    state['pending'] = ['SD-03: 11个既有差异变体已逐项有采用决定：10项为可选子代理字段，1项为公开候选未取得资格的预测fork。选定分发/转换/显示和预测调用已核对；实际decoder/receiver/通知后效、成功预测及npm源码绑定仍开放，不重复全协议发现。'
                        if isinstance(x, str) and x.startswith('SD-03:') else x for x in state['pending']]
    state['updatedAtUtc'] = NOW
    (OUT / 'analysis-state.json').write_bytes(encode(state))
    lead = '当前[后台差异采用决定](protocol-delta-adoption-v1.md)已把11变体收敛为两类：10项可选子代理通知字段保留兼容候选，1项预测fork要求匹配provider，禁止静默降级；16条来源事实、8项隔离检查通过。此前[调试页策略](debug-chrome-policy-owner-v1.md)已交付并验证。下一步将这些决定与运行时、存储及37逻辑模块合同合入新版实施依据。真实运行时/后台/模式和行为仍有缺口；373功能、48任务、1216未执行规格和模型授权余0不变，完整分析未完成。'
    for name in ['report.md', 'gaps.md']:
        _, tail = (OUT / name).read_text().split('\n\n', 1)
        (OUT / name).write_text(lead+'\n\n'+tail)
    receipt = {'result': result, 'summary': summary, 'evidence': evidence, 'replay': replay_pin, 'counts': counts}
    (WORK / 'publication.json').write_bytes(encode(receipt))
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
