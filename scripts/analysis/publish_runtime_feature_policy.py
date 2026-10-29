"""Publish the bounded runtime policy contract; retain original scope and snapshots."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/runtime-feature-policy-work'
RAW = OUT / 'raw/runtime-feature-policy'


def read(p):
    return json.loads(p.read_text())


def save(p, obj):
    with p.open('x') as stream:
        stream.write(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def pin(p):
    return {'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size,
            'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}


def main():
    state_path = OUT / 'analysis-state.json'
    before = read(state_path)
    save(WORK / 'state-before.json', before)
    sources = {family: read(WORK / family / 'source-contracts.json')
               for family in ['main', 'startup', 'initial', 'shared']}
    replay = read(WORK / 'replay.json')
    assert replay['passed'] == 12 and replay['failed'] == 0
    assert all(x['fullProgramParsed'] and x['parserErrors'] == 0 for x in sources.values())
    # These are selected first-party glue and policies, not third-party implementations.
    RAW.mkdir(exist_ok=False)
    for family in sources:
        shutil.copytree(WORK / family, RAW / family)
    shutil.copyfile(WORK / 'replay.json', RAW / 'replay.json')
    for name in ['runtime_feature_policy_ast.mjs', 'probe_runtime_feature_policy.cjs', 'publish_runtime_feature_policy.py']:
        shutil.copyfile(ROOT / 'scripts/analysis' / name, RAW / name)

    facts = []

    def fact(identifier, claim, selections, qualification='Frozen source semantics; native effects and live integration unverified.'):
        spans = []
        for family, label in selections:
            unit = next(x for x in sources[family]['units'] if x['label'] == label)
            spans.append({k: unit[k] for k in ['sourcePath', 'sourceHash', 'byteRange', 'spanHash', 'nodeType']})
        facts.append({'id': identifier, 'baselineId': BASE, 'claim': claim,
                      'sourcePath': spans[0]['sourcePath'], 'sourceHash': spans[0]['sourceHash'],
                      'locator': spans[0], 'supportingSourceSpans': spans,
                      'method': 'fixed-inventory-hash-check + whole-Program lexical-binding query + selected-source inspection',
                      'confidence': 'confirmed', 'verificationStatus': 'bounded-static-contract-confirmed',
                      'qualification': qualification})

    fact('RFPC-01', 'Program绑定At只含OwlOpenAIGoLinks、OwlRemoteSearchSuggestions；setter只合并这两项的boolean，包括false，忽略其他键和非boolean。',
         [('main', 'binding-At'), ('main', 'binding-uze')])
    fact('RFPC-02', 'e$是Program共享缓存。setter先调用原生方法再提交缓存；reset先清空缓存再调用原生方法。两种调用抛错时的缓存状态不同。',
         [('main', 'binding-e$'), ('main', 'binding-uze'), ('main', 'binding-dze')])
    fact('RFPC-03', 'legacy启用限定Windows、非空账号、异步取得principal后generation未变化且accountId相等，再检查方法存在且为function。n$仅为能力形状检查。',
         [('main', 'binding-uze'), ('main', 'binding-n$'), ('main', 'binding-t$'), ('main', 'binding-fze'), ('main', 'binding-r$')])
    fact('RFPC-04', '重置回调P先fze再dze；认证principal账号或用户变化，以及account/updated的authMode既非chatgpt也非chatgptAuthTokens时调用它。current为null的principal事件本身仅保存旧身份后返回。',
         [('main', 'reset-callback-declaration'), ('main', 'reset-callback-consumer-3321370-owner'), ('main', 'reset-callback-consumer-3322041-owner')])
    fact('RFPC-05', 'owner键经main的l.j接到startup导出j/Sr，即electron-legacy-chrome-policy-fallback-owner；pze比较账号及用户，r$先删除owner再按Windows能力条件禁用。RPC基类Pt仅外部依赖别名，本批不恢复其实现。',
         [('main', 'binding-l'), ('startup', 'binding-Sr'), ('startup', 'cjs-export-j'), ('startup', 'binding-ft'), ('startup', 'cjs-export-Pt'), ('main', 'binding-pze'), ('main', 'binding-r$')])
    fact('RFPC-06', 'shared初始化wAt/TAt为两个特性键并导出Q3t/$3t；initial分别导入为Bhe/l，SZs将3646210497映射GoLinks、3217069062映射RemoteSearchSuggestions。',
         [('shared', 'binding-EAt'), ('initial', 'binding-Bhe'), ('initial', 'binding-l'), ('initial', 'binding-wZs')],
         'Import/export joins are pinned in raw contracts; no remote gate service or initializer runtime executed.')
    fact('RFPC-07', 'bZs在Ready且owlFeatures存在时并行处理legacy请求和runtime键；runtime键允许LocalOverride或以:Recognized结尾的reason。isOwlFeatureEnabled只吞掉特定Unsupported Owl feature: Error，其他错误继续抛出。',
         [('initial', 'binding-bZs'), ('initial', 'reference-bZs-9236317-owner'), ('main', 'binding-uze')])
    fact('RFPC-08', 'xZs校验chatgpt认证、workspace/account一致、qhi评估上下文、有限account_creation_time及WeakMap身份连续性；legacy gate3384989494必须value为真且reason以:Recognized结尾。qhi依赖SDK数据adapter/hash及相等helper，其底层实现未由本批证明。',
         [('initial', 'binding-xZs'), ('initial', 'binding-qhi')])
    fact('RFPC-09', 'createAppHost构造owlFeatures:new uze(this.appState,()=>o.getAuthenticatedPrincipal())；renderer使用shared的fN导入Pd.owlFeatures。本批确认两端调用职责，未执行中间RPC传输。认证字符串chatgpt本身不证明ChatGPT产品模式专属。',
         [('main', 'reference-uze-3336711-owner'), ('initial', 'binding-Pd'), ('initial', 'binding-bZs')],
         'Source endpoints only; shared registry export resolution and actual RPC/native behavior are not claimed complete.')

    joins = []
    for local, original, gate in [('Bhe', 'wAt', '3646210497'), ('l', 'TAt', '3217069062')]:
        imp = next(x for x in sources['initial']['imports'] if x['local'] == local)
        exp = next(x for x in sources['shared']['exports'] if x['name'] == original)
        assert imp['imported'] == exp['exported']
        joins.append({'gate': gate, 'initialLocal': local, 'sharedLocal': original, 'import': imp, 'export': exp})

    counts = {'newOriginalProgramParses': 4, 'distinctOriginalPrograms': 4,
              'parsedAstNodes': sum(x['nodeCount'] for x in sources.values()),
              'selectedSourceUnits': sum(len(x['units']) for x in sources.values()),
              'selectedSourceBytesIncludingOverlaps': sum((RAW / family / u['file']).stat().st_size
                                                        for family, x in sources.items() for u in x['units']),
              'sourceFacts': len(facts), 'allowedRuntimeFeatureKeys': 2, 'runtimeGateJoins': 2,
              'isolatedSourceReplayCasesPassed': 12, 'nativeProviderEffectsUnresolved': 3,
              'newReaRuns': 0, 'modelSubmissionsAdded': 0, 'originalClientRunsAdded': 0,
              'productScenarioPassesAdded': 0, 'featureDefinitionsAdded': 0,
              'modeClassificationsChanged': 0, 'wholeFeatureExclusionsAdded': 0, 'clientImplementationAdded': 0}
    next_action = {
        'issueId': 'SD-01-through-SD-06-convergence',
        'fixedInput': 'Current stage snapshot plus existing scope, provider, runtime, behavior and restoration overlays; include runtime-feature-policy-contracts.json.',
        'question': 'Which original analysis exit conditions are now met, and which remaining architecture/scope decisions still prevent an honest final analysis handoff?',
        'closure': 'One finite decision matrix for the original nine criteria and six issue groups. For each remaining item state evidence, architectural consequence and a bounded resolution or explicit external prerequisite. Do not add features, re-scan sources or demand zero unknowns/all implementation tests as part of this consolidation.',
        'authorization': 'Read existing artifacts only for this consolidation; no new model tasks, original-client launches or client implementation.'}
    result = {'schemaVersion': 1, 'baselineId': BASE, 'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
              'scope': 'Two runtime feature keys and legacy-policy first-party orchestration; not complete Owl runtime equivalence.',
              'inputPins': [pin(OUT / name) for name in ['files.json', 'runtime-surface-disposition.json',
                             'runtime-api-contracts.json', 'analysis-stage-decisions-v3.json',
                             'feature-scope-v25.json', 'restoration-coverage-v16.json']],
              'rawPins': [pin(p) for p in sorted(RAW.rglob('*')) if p.is_file()],
              'facts': facts, 'gateJoins': joins, 'counts': counts,
              'maintenanceDecision': {
                  'status': 'bounded-first-party-contract-closed; native-provider-behavior-unresolved',
                  'proposedSourceUnits': ['runtime/runtime-feature-policy.ts', 'runtime/runtime-feature-provider.ts', 'renderer/runtime-feature-gates.ts'],
                  'qualification': 'Proposed responsibility boundaries, not recovered original paths or generated client code.',
                  'firstPartyResponsibilities': ['Allowlisted boolean merge/cache and reset ordering', 'Authentication owner and generation invalidation',
                                                'Ready/evaluation context and gate dispatch', 'Specific unsupported-error mapping'],
                  'externalDependencies': ['Existing RPC transport/base via dependency import', 'Existing gate SDK and helpers via dependency import'],
                  'mode': 'unknown; retain pending positive ChatGPT-product-only evidence',
                  'exclusionReason': None},
              'unresolvedNativeEffects': [
                  {'api': 'app.setRuntimeFeatures', 'unknown': 'Actual Chromium/Owl effect, default policy and reversibility of both allowed keys.'},
                  {'api': 'app.isRuntimeFeatureEnabled', 'unknown': 'Runtime supported-feature registry and returned state outside the first-party wrapper.'},
                  {'api': 'app.setLegacyChromePolicyFallbackEnabled', 'unknown': 'Actual Windows policy fallback semantics and native ownership/cleanup behavior.'}],
              'priorSubstepClosure': {'allowedKeys': True, 'AtCachePredicateBindings': True, 'resetAndUnsupportedConditions': True,
                                      'sourceConsumersBounded': True, 'effectsAssignedToExplicitUnresolvedProvider': True,
                                      'closedScope': 'Previous stage.nextAction only; not the whole SD-02 or analysis.'},
              'remainingLimits': ['No middle RPC transport execution or full shared service-registry closure added.',
                                  'Twelve selected-source replays use synthetic helpers/providers and do not verify SDK/native/client behavior.',
                                  'Debug Chrome pages and other runtime capability groups retain previous disposition without re-analysis.',
                                  'Complete feature denominator, product mode decisions and full runtime route remain unresolved.'],
              'nextAction': next_action, 'fullAnalysisCompleted': False, 'fullRuntimeRouteSelected': False,
              'clientImplementationStarted': False}
    save(OUT / 'runtime-feature-policy-contracts.json', result)
    with (OUT / 'runtime-feature-policy-evidence.jsonl').open('x') as stream:
        stream.write(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in facts))
    summary = '''# 运行时特性策略的第一方边界

本批关闭上一轮限定的源码问题：`At`、`e$`和`n$`已有完整Program绑定与调用者证据；允许键、重置入口、异常处理和原生职责已明确。两个允许键是`OwlOpenAIGoLinks`、`OwlRemoteSearchSuggestions`，分别接到灰度开关`3646210497`、`3217069062`。

第一方setter只合并允许键中的boolean，包括false；多实例共享缓存。setter在原生调用成功后提交缓存，reset先清空缓存再调用原生方法，因此两种路径失败后的缓存状态不同。缺失方法的TypeError不会自动进入`Unsupported Owl feature:`异常回退。

Windows legacy策略启用要求非空且匹配的认证账号，异步认证返回时generation仍有效，并且运行时方法存在且为function。成功后保存账号/用户owner；清理先删除owner再按平台/能力禁用。账号或用户切换、退出相应认证类型会重置。renderer另检查评估上下文、账号时间及身份连续性；legacy开关`3384989494`需要Recognized结果，LocalOverride不足以启用。

维护决定是保留三个第一方职责单元：策略状态、运行时provider接口、renderer灰度分发。RPC与灰度SDK按第三方依赖引入，不生成其实现。源码中的`chatgpt`是认证条件，不能据此将这组能力整体作为ChatGPT产品模式删除。本批不改变任何功能模式分类。

底层三个效果仍未知：两键如何改变Owl/Chromium、运行时特性注册/查询、Windows旧策略回退。它们属于明确的运行时provider前置条件；公开Electron的同名接口缺失结论沿用[上一轮对照](runtime-surface-disposition.md)。本批没有实现替代provider，也未证明完整运行时路线。

四个冻结Program的定向解析、精确范围与跨文件import/export连接见[结构化合同](runtime-feature-policy-contracts.json)。12条选定源码离线回放通过，使用合成RPC基类、状态、原生方法及SDK helper；它们不计入真实客户端或产品场景通过。新增REA运行、模型提交、原客户端运行、功能定义和客户端实现均为0。

上一轮的有限源码问题已收口，整个分析仍未完成。下一步只基于现有产物汇总原九项标准与六组架构问题，区分已交付、仍缺证据和外部前置条件；不在这次汇总中扩充功能清单、重新扫描源码或要求实施测试全部通过。
'''
    with (OUT / 'runtime-feature-policy-contracts.md').open('x') as stream:
        stream.write(summary)
    overlay = {'result': pin(OUT / 'runtime-feature-policy-contracts.json'),
               'summary': pin(OUT / 'runtime-feature-policy-contracts.md'),
               'evidence': pin(OUT / 'runtime-feature-policy-evidence.jsonl'),
               'counts': counts, 'priorSubstepClosedWithinScope': True, 'fullAnalysisCompleted': False}
    after = copy.deepcopy(before)
    after['updatedAtUtc'] = datetime.now(timezone.utc).isoformat()
    after['runtimeFeaturePolicyContracts'] = overlay
    after['runtimeCapabilityDecisions']['currentFeaturePolicyOverlay'] = overlay
    after['stageDecisions']['runtimeFeaturePolicyOverlay'] = overlay
    after['stageDecisions']['nextAction'] = next_action
    assert read(state_path) == before
    state_path.write_text(json.dumps(after, ensure_ascii=False, indent=2) + '\n')
    for name in ['report.md', 'gaps.md']:
        original = (OUT / name).read_text()
        (WORK / (name + '.before')).write_text(original)
        note = '当前补充：[运行时特性策略](runtime-feature-policy-contracts.md)关闭两键、缓存/重置、认证generation与能力predicate的有限源码问题；三项底层效果仍需运行时provider。下一步为现有分析退出条件的有限汇总。\n\n'
        (OUT / name).write_text(note + original)
    for p in [OUT / 'runtime-feature-policy-contracts.json', OUT / 'runtime-feature-policy-contracts.md',
              OUT / 'runtime-feature-policy-evidence.jsonl'] + [p for p in RAW.rglob('*') if p.is_file()]:
        p.chmod(0o444)
    print(json.dumps({'counts': counts, 'fullAnalysisCompleted': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
