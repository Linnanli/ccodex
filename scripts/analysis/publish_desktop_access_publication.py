"""Publish the bounded desktop access-input contract without changing feature modes."""
import copy
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/desktop-access-publication-work'
RAW = OUT / 'raw/desktop-access-publication'


def read(path):
    return json.loads(path.read_text())


def pin(name):
    data = (OUT / name).read_bytes()
    return dict(path=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def write(name, data):
    with (OUT / name).open('x') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    before_bytes = (OUT / 'analysis-state.json').read_bytes()
    before = json.loads(before_bytes)
    assert before_bytes == (WORK / 'before-analysis-state.json').read_bytes()
    assert before['updatedAtUtc'] == '2026-10-24T11:16:13.527688+00:00'
    assert before['analysisMilestones']['path'] == 'implementation-milestones-v8.json'
    assert before['latestBehaviorAuthorizationState']['groupRemaining'] == 0
    observed = read(WORK / 'isolated-observations-01.json')
    assert observed['passed'] == 27 and observed['failed'] == 0
    assert len(observed['cases']) == 27
    for key in ['productScenariosExecuted', 'originalClientRunsAdded', 'modelSubmissionsAdded', 'realServiceCalls']:
        assert observed[key] == 0
    initial, shared = [read(WORK / name / 'source-contracts.json') for name in ['initial', 'shared']]
    for selection in [initial, shared]:
        assert selection['selectionMode'] == 'explicit'
        assert selection['fullProgramParsed'] and not selection['unresolved']
        source = ROOT / '.analysis-local/baselines' / BASE / 'extracted' / selection['sourcePath'].removeprefix('app.asar/')
        data = source.read_bytes()
        assert hashlib.sha256(data).hexdigest() == selection['sourceHash']
        for unit in selection['units'] + selection['callbacks']:
            r = unit['byteRange']
            assert hashlib.sha256(data[r['start']:r['endExclusive']]).hexdigest() == unit['spanHash']
    joins = []
    for local, exported, target in [('zne', 'ENt', 'yTn'), ('Gr', 'DAt', 'dq'), ('xg', 'xNt', 'TG')]:
        candidates = [(i, j, imp, spec) for i, imp in enumerate(initial['imports']) for j, spec in enumerate(imp['specifiers']) if spec['local'] == local]
        assert len(candidates) == 1
        i, j, imp, spec = candidates[0]
        assert imp['module'] == './app-shared-8bd9d0399038.js' and spec['imported'] == exported
        ex = [(k, e) for k, e in enumerate(shared['exports']) if e['exported'] == exported]
        assert len(ex) == 1 and ex[0][1]['local'] == target
        target_unit = next(u for u in shared['units'] if u['name'] == target)
        assert ex[0][1]['binding']['definitions'][0]['declaration']['byteRange'] == target_unit['byteRange']
        joins.append(dict(local=local, imported=exported, target=target,
                          importPointer=f'/imports/{i}/specifiers/{j}', exportPointer=f'/exports/{ex[0][0]}'))
    caller = [u for u in initial['programBindingUses'] if u['unit'] == 'EUs' and u['name'] == 'SHs']
    assert caller
    shs = next(u for u in initial['units'] if u['name'] == 'SHs')
    assert all(u['binding']['definitions'][0]['declaration']['byteRange'] == shs['byteRange'] for u in caller)
    for receipt in ['initial-receipt.json', 'shared-receipt.json', 'probe-01-receipt.json']:
        assert read(WORK / receipt)['exitCode'] == 0
    assert not RAW.exists()
    shutil.copytree(WORK, RAW)
    for name in ['settings_operations_ast.mjs', 'probe_desktop_access_publication.cjs', 'publish_desktop_access_publication.py']:
        shutil.copyfile(ROOT / 'scripts/analysis' / name, RAW / name)
    for name, path in [('before-README.md', ROOT / 'README.md'), ('before-report.md', OUT / 'report.md'), ('before-gaps.md', OUT / 'gaps.md')]:
        shutil.copyfile(path, RAW / name)
    now = datetime.now(timezone.utc).isoformat()
    facts = [
        dict(id='ACCESS-PUB-01', claim='EUs constructs SHs under its account/auth provider for the selected authentication paths. The complete selected function has no home chat/work predicate controlling that construction.',
             sourceUnits=['initial:EUs'], observations=[c['id'] for c in observed['cases'] if c['id'].startswith('AUTH-PROVIDER:')],
             limit='JSX construction with synthetic hooks is observed; actual bootstrap, React mounting and layout-effect execution remain unobserved.'),
        dict(id='ACCESS-PUB-02', claim='The selected SHs layout-effect callback publishes supportedSurface:true to ChatGPT inputs via zne and supportedSurface:true plus workCloudSupportedSurface:true directly to Gr. Its HTTP account identity remains guarded by loading, auth method, account/user and token.',
             sourceUnits=['initial:SHs', 'shared:yTn', 'shared:TG', 'shared:dq'], observations=[c['id'] for c in observed['cases'] if c['id'].startswith('PUBLISH:')],
             limit='These are access-input booleans, not proof of successful authorization, product-mode membership or service capability.'),
        dict(id='ACCESS-PUB-03', claim='yTn can retain a matching cached account-user while pending, but publishes the new access input, invalidates the prior identity when account/user/account-user changes, and clears an ineligible or settled cached profile.',
             sourceUnits=['shared:yTn', 'reused:assignment-EG'],
             limit='The state batch and invalidation receiver are synthetic substitutes; no actual stored profile or account was read.'),
        dict(id='ACCESS-PUB-04', claim='xbn independently derives loading, missing-account, mismatch, unsupported-plan, unsupported-surface and not-chatgpt-auth outcomes. It accepts no home composer mode parameter; token auth is distinct from chatgpt auth in this selector.',
             sourceUnits=['shared:xbn'], observations=[c['id'] for c in observed['cases'] if c['id'].startswith('ACCESS:')],
             limit='The supported-plan predicate was substituted explicitly. No complete real plan entitlement matrix is claimed.'),
        dict(id='ACCESS-PUB-05', claim='SHs registers a separate unmount cleanup that resets account/HTTP access inputs and delegates prior-identity cleanup. The selected account-input lifecycle is separate from the previously analyzed home-mode preference persistence.',
             sourceUnits=['initial:SHs'], observations=[c['id'] for c in observed['cases'] if c['id'].startswith('CLEANUP:')],
             limit='Default values, state batching and the cleanup service are supplied fixture boundaries; no real unmount or persistence is observed.'),
    ]
    decisions = [
        dict(id='ACCESS-D01', disposition='retain-shared-first-party-account-access-layer', owners=['W04', 'W07'],
             paths=['packages/contracts/src/account-access.ts', 'apps/desktop/src/renderer/app/account-access-provider.tsx'],
             reason='Account identity publication, access inputs and profile lifetime must stay separate from ChatGPT conversation features. They supply both ChatGPT and Codex/Work access selectors in the selected desktop source.', evidence=['ACCESS-PUB-01', 'ACCESS-PUB-02', 'ACCESS-PUB-03']),
        dict(id='ACCESS-D02', disposition='reject-access-family-as-product-exclusion-rule',
             affectedCatalog='40 access-family labels and 53 settings predicates in settings-mode-boundary-contracts.json',
             reason='A chatGpt label requires account/auth/capability conditions; the desktop publisher does not turn its surface support off according to the home chat/work preference. Classify feature consumers and effects before deleting branches.',
             evidence=['ACCESS-PUB-01', 'ACCESS-PUB-02', 'ACCESS-PUB-04'],
             prohibition='Do not delete an entire settings page, chunk, authentication adapter or shared account service solely because of chatgpt naming or a chatGpt access label.'),
        dict(id='ACCESS-D03', disposition='preserve-status-and-identity-contract', owners=['W04', 'W07'],
             reason='Keep loading, error/denial, account matching, token identity, pending-profile and cleanup contracts explicit. supportedSurface:true must not become a blanket feature permission.', evidence=['ACCESS-PUB-02', 'ACCESS-PUB-03', 'ACCESS-PUB-04', 'ACCESS-PUB-05']),
        dict(id='ACCESS-D04', disposition='close-selected-publisher-identity-investigation',
             reason='The selected caller, cross-module publication bindings and reader are now connected. Continue scope decisions at concrete feature consumers; do not repeat access-publisher tracing without a named conflict or missing behavior.',
             stillOpen=['Actual provider bootstrap and lifecycle integration', 'Each retained feature consumer and real service entitlement', 'Complete Codex/ChatGPT feature classification'], evidence=[f['id'] for f in facts]),
    ]
    document = dict(schemaVersion='desktop-access-publication/1', baselineId=BASE, recordedAtUtc=now,
        inputPins=[pin(n) for n in ['implementation-milestones-v8.json', 'feature-scope-v17.json', 'restoration-coverage-v8.json', 'settings-mode-boundary-contracts.json', 'settings-entry-callers-contracts.json', 'product-flow-ownership.json']],
        sourceMetadata=[pin(f'raw/desktop-access-publication/{n}/source-contracts.json') for n in ['initial', 'shared']],
        importExportJoins=joins, sourceSelections=observed['sourceSelections'],
        observations=pin('raw/desktop-access-publication/isolated-observations-01.json'),
        facts=facts, restorationDecisions=decisions,
        upgradeChecks=['Recheck EUs→SHs binding and layout-effect registration after input changes.', 'Recheck ENt/DAt/xNt module identity and export bindings, not just minified names.', 'Recheck access-input shapes, identity invalidation, pending-profile and cleanup ordering.', 'Recheck concrete feature consumers before changing a retained/shared/excluded decision.'],
        counts=dict(newFullProgramSelections=2, newSourceUnits=8, reusedSourceUnits=1, selectedCallbacks=2, isolatedCasesPassed=27,
                    sourceFacts=5, restorationDecisions=4, featureDefinitionsAdded=0, featureModesChanged=0, confirmedChatGptExclusionsAdded=0,
                    productScenarioPassesAdded=0, modelSubmissionsAdded=0, originalClientRunsAdded=0, realServiceCalls=0, newReaRuns=0, clientImplementationAdded=0),
        limits=observed['limits'], fullAnalysisCompleted=False, clientImplementationStarted=False)
    assert len(initial['units']) + len(shared['units']) == document['counts']['newSourceUnits']
    write('desktop-access-publication.json', document)
    summary = '''# 桌面账户访问发布端与产品模式边界

恢复时保留独立的共享账户访问层；不能按 `chatGpt` 设置分类或函数名删除整个页面、认证适配器和账户服务。所选桌面发布端同时写入 ChatGPT 与 Codex/Work 的 surface 支持，随后仍由各访问选择器检查认证、账户、计划和功能条件。具体功能的保留或剥离须依据消费者和后效。[结构化合同与恢复决定](desktop-access-publication.json)保存来源、边界和升级检查。

本批连接完整 Program 中的 `EUs → SHs → zne/Gr`，以及跨模块的 `zne → ENt → yTn`、`Gr → DAt → dq`、`xg → xNt → TG`。EUs 在所选认证路径下均构造 SHs；其构造没有 home chat/work 条件。SHs 的 layout-effect 发布 callback 将两个访问输入的 `supportedSurface` 写为 true，并将 Work cloud 支持写为 true。**这不等于这些功能已获授权，也不证明每个页面均属于两个产品模式。**

| 边界 | 本批确定的恢复要求 |
| --- | --- |
| 认证与账户 provider | 同时保留认证加载、账户查询、HTTP 账户身份和上下文发布；与 conversation UI 分开 |
| 访问判定 | 保留账户缺失/不匹配、计划、surface、认证种类及 loading 等结果；不折叠成产品模式布尔值 |
| 身份切换 | 保留 pending profile 的精确身份匹配与旧身份失效处理 |
| 生命周期 | 保留卸载时的访问输入重置和旧身份清理；不混同 home mode 偏好持久化 |
| 模式剥离 | 设置 access family 是访问资格，不能单独成为整页或整块 chunk 的排除证据 |

两个完整原 Program 各作一次新的定向选择，保存8个源码单位、复用1个既有单位，并执行2个精确 callback。27项隔离用例全部通过，涵盖五种认证路径的 JSX 构造、两类输入发布、pending profile、身份失效、访问拒绝和卸载清理。React hooks、状态批处理、计划谓词及清理服务使用合成替身；没有真实 React 挂载、原客户端运行、账户访问、模型请求或服务调用。

所选发布端的绑定和静态生命周期调查到此收束。后续仅在出现具体冲突或新增行为要求时重开；实际 bootstrap、provider 集成和服务资格留在对应集成任务。下一步使用已有三个设置页选择，按本地线程、云任务和账户会话区分操作所有者及保留范围，不再重复追查本批发布端。

当前274项有限功能、278项用户操作、64项支撑、919条未执行规格及15个待展开设置容器保持原记录；没有改写模式、增加产品通过数或确认新的整项 ChatGPT 排除。原九项标准仍为四项资料/范围义务有交付、五项部分完成，完整分析尚未结束。
'''
    with (OUT / 'desktop-access-publication.md').open('x') as stream:
        stream.write(summary)
    overlay = dict(result=pin('desktop-access-publication.json'), summary=pin('desktop-access-publication.md'), counts=document['counts'], selectedPublisherSourceContractClosed=True, actualIntegrationVerified=False)
    state = copy.deepcopy(before)
    state['desktopAccessPublication'] = overlay
    state['analysisMilestones']['currentScopeOverlay']['accountAccessPublicationOverlay'] = overlay
    state['stageDecisions']['accountAccessPublicationOverlay'] = overlay
    state['stageDecisions']['nextAction'] = dict(issueId='SD-01/SD-06',
        completedSubstep='Selected desktop access publisher and reader joined; access-family labels rejected as a product-exclusion rule. Shared account-access source retained independently of conversation UI.',
        fixedInput='Current v17/v8 and saved settings-data-batch11-work selections. Reuse desktop-access-publication; no repeat access-publisher trace without a concrete conflict.',
        question='Which concrete local-thread, cloud-task and account-conversation operations must be retained or isolated in ads-controls, archived-chats and data-controls?',
        closure='Publish finite action ownership and shared consumers for the three saved page selections. Preserve typed deletion/recovery scopes and explicit mode/service integration residuals.',
        deferredDedicatedVerification='Real provider bootstrap, runtime qualification, remaining full-scope mapping and actual product scenarios. No model submission remains authorized.')
    state['updatedAtUtc'] = now
    assert state['featureScopeCurrentView'] == before['featureScopeCurrentView']
    assert state['latestBehaviorAuthorizationState'] == before['latestBehaviorAuthorizationState']
    assert state['stageDecisions']['counts'] == before['stageDecisions']['counts']
    for key in ['runtimeBoundaryOverlay', 'productFlowOwnershipOverlay', 'browserCloneRouteOverlay', 'publicHistoryDuplicateOverlay']:
        assert state['stageDecisions'][key] == before['stageDecisions'][key]
    (OUT / 'analysis-state.json').write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
    paragraph = '[账户访问与模式剥离边界](desktop-access-publication.md)已连接所选桌面发布端和访问选择器，27项合成用例通过。恢复时保留共享账户访问层；chatGpt访问分类不能单独作为整页删除依据。该源码调查已收束，真实provider集成与完整功能归属仍待验证。'
    for name in ['report.md', 'gaps.md']:
        p = OUT / name
        first, rest = p.read_text().split('\n', 1)
        p.write_text(first + '\n\n' + paragraph + '\n\n' + rest.lstrip())
    p = ROOT / 'README.md'
    first, rest = p.read_text().split('\n', 1)
    p.write_text(first + '\n\n' + paragraph.replace('(desktop-access-publication.md)', f'(analysis/{BASE}/desktop-access-publication.md)') + '\n\n' + rest.lstrip())
    current = read(OUT / 'analysis-state.json')
    assert current == state
    validation = dict(recordedAtUtc=now, sourceRangeHashesVerified=True, importExportBindingsVerified=3,
        selectedCallerBindingVerified=True, allThreeCommandsExitedZero=True, all27IsolatedCasesPassed=True,
        featureLedgerAndCountsUnchanged=True, previousRuntimeAndProductDecisionsPreserved=True, behaviorAuthorizationUnchanged=True,
        fullAnalysisCompleted=current['fullAnalysisCompleted'],
        beforeStateSha256=hashlib.sha256(before_bytes).hexdigest(), afterState=pin('analysis-state.json'),
        outputPins=[pin(n) for n in ['desktop-access-publication.json', 'desktop-access-publication.md', 'raw/desktop-access-publication/isolated-observations-01.json']])
    write('raw/desktop-access-publication/validation.json', validation)
    print(json.dumps(document['counts']))


if __name__ == '__main__':
    main()
