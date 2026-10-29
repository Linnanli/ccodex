"""Publish the selected Chrome policy owner contract without native acceptance claims."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/debug-chrome-policy-owner-work'
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'
NOW = datetime.now(timezone.utc).isoformat()
sha = lambda b: hashlib.sha256(b).hexdigest()
encode = lambda v: (json.dumps(v, ensure_ascii=False, indent=2) + '\n').encode()


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
    assert not (OUT / 'debug-chrome-policy-owner-v1.json').exists()
    for name in ['analysis-state.json', 'report.md', 'gaps.md']:
        with (WORK / (name + '.before')).open('xb') as f:
            f.write((OUT / name).read_bytes())
    kinds = ['main', 'shared', 'flavor', 'bootstrap', 'renderer', 'rendererShared']
    inspections = {k: json.loads((WORK / (k + '-inspection.json')).read_text()) for k in kinds}
    replay = json.loads((WORK / 'replay.json').read_text())
    assert replay['casesPassed'] == len(replay['cases']) == 15
    units, by_label = [], {}

    def add(kind, row, selection):
        raw = (FROZEN / row['sourcePath'].removeprefix('app.asar/')).read_bytes()
        s = row['byteRange']
        span = raw[s['start']:s['endExclusive']]
        assert sha(raw) == row['sourceHash'] and sha(span) == row['spanHash']
        assert span == selection.read_bytes()
        u = {k: row[k] for k in ['sourcePath', 'sourceHash', 'byteRange', 'spanHash', 'nodeType', 'labels']}
        u['id'] = f'DCP-SOURCE-{len(units)+1:02d}'
        u['kind'] = kind
        u['selection'] = publish(f'raw/debug-chrome-policy-owner/{len(units)+1:02d}.js.txt', span)
        units.append(u)
        for label in u['labels']:
            key = (kind, label)
            assert key not in by_label
            by_label[key] = u

    for kind, inspection in inspections.items():
        assert inspection['parse'] == 'complete-Program' and not inspection['targetCodeExecuted']
        for row in inspection['units']:
            add(kind, row, ROOT / row['savedPath'])
    audio = json.loads((OUT / 'audio-measurement-owner-v1.json').read_text())
    electron = next(x for x in audio['sourceUnits'] if 'binding-_' in x['labels'])
    add('main', electron, ROOT / electron['selection']['path'])
    assert len(units) == 63

    def u(kind, label):
        return by_label[(kind, label)]

    specs = [
        ('DCP-01', 'shared', 'preference-debugChromePagesEnabled', 'debugChromePagesEnabled默认false、agentAccess为hidden，key复用DEBUG_CHROME_PAGES_ENABLED（debug-chrome-pages-enabled）；声明描述Browser Use的可信chrome诊断页，不证明native允许列表。'),
        ('DCP-02', 'shared', 'binding-R', 'allowDebugMenu委托isInternal；Hi仅含dev、agent、nightly、internal-alpha，public-beta和prod不允许。构建类型不是Codex/ChatGPT模式归属。'),
        ('DCP-03', 'flavor', 'binding-m', 'resolve优先接受去空白且有效的BUILD_FLAVOR，再读codexBuildFlavor包元数据，最后按NODE_ENV===production选择prod，否则dev。主进程设置副作用重新调用resolve，不仅依赖启动缓存。'),
        ('DCP-04', 'flavor', 'binding-o', '元数据读取依次检查候选文件、解析JSON并选择首个经parse接受的非空字段。JSON.parse没有本地catch；损坏候选会抛出，不静默进入下一候选或默认构建类型。'),
        ('DCP-05', 'bootstrap', 'binding-oE', 'bootstrap上下文factory oE在aE存在时直接返回缓存；首次buildFlavor为传入e或l.t.resolve()。启动路径以oE($)供给已解析构建类型，exports.I=oE供main的g.I()读取。完整factory有其它副作用，本次不执行。'),
        ('DCP-06', 'main', 'binding-u0e', 'runMainAppStartup即u0e，从g.I()解构buildFlavor:o并计算allowDebugMenu(o)。在app.whenReady、加载g.U、Moe迁移、captureInitialFollowUpQueueMode和joe后，以j&&settingsStore.getEffective(key)===true得到le，先调用native再uf(le)。u0e整段仅作为生命周期上下文，不据此认领全部业务职责。'),
        ('DCP-07', 'main', 'method-setGlobalStateValue', '旧setGlobalStateValue的调试页分支将输入严格true与重新resolve后的allowDebugMenu合取；依次native、uf和globalState.set，存入的是门控后的值。native抛错时后两步不执行，store抛错时native与本地flag已经更新。'),
        ('DCP-08', 'main', 'method-setGlobalStateValue', 'setGlobalStateValue在分支完成后向所有窗口广播global-state-updated并携带原key；native/store抛错会跳过该广播。此处是发送代码证据，不证明实际窗口接收。'),
        ('DCP-09', 'main', 'method-setConfigurationValue', 'setConfigurationValue先把原输入写入globalState，再执行applySettingSideEffects；调试页native失败不会在此回滚已经完成的set。实际store落盘不由这一方法证明。'),
        ('DCP-10', 'main', 'settings-adapter-write', 'AL.write是async，先store.set，再用store.get的读回值调用afterWrite。选定注入把afterWrite接到applySettingSideEffects；setSettingValue先经r.F再await settings.write。副作用失败可使写入调用拒绝，但此前set已发生；真实校验/持久化语义仍取决于store/provider。'),
        ('DCP-11', 'main', 'method-applySettingSideEffects', '调试页设置副作用以value===true与allowDebugMenu(resolve())合取，然后native和uf；它不把归一化值重写store。因而stored、effective/native请求和本地flag是不同状态层。'),
        ('DCP-12', 'main', 'native-call-startup', '完整main AST只找到三个_.app.setDebugChromePagesEnabled调用：启动、旧global setter和设置副作用；三个均无本地try祖先或方法存在性检查，且结果未await。bootstrap加载并await main startup的外层catch另处理启动失败，不能把它理解为这些方法各自吞掉native错误。'),
        ('DCP-13', 'shared', 'binding-ka', 'r.ii导出ka，Oa把chrome downloads/history映射到对应/settings/browser-use路由。ka规范chrome斜线、拒绝非chrome协议及凭据/端口，按解码后小写host匹配并保留search；未匹配返回null。这里不是version/histograms或全部chrome页面的native允许列表。'),
        ('DCP-14', 'main', 'binding-Ake', 'Ake在r.ii映射存在且df()为false时先调用截获回调；未截获则给owner发送navigate-to-route，返回true。映射不存在或flag=true返回false，不等于完整导航政策允许。'),
        ('DCP-15', 'main', 'flag-consumer-1533856', '选定请求回调在没有rewrite结果时，将mainFrame的r.ii映射且!df条件与HCe、isRestrictedBrowserNavigation等策略组合。另有rewrite结果时返回redirectURL；仅检查本地flag不能证明最终URL可访问。'),
        ('DCP-16', 'renderer', 'binding-P', 'debug-settings从app-shared导入aen为d；aen导出FM，IM初始化FM的allowDebugMenu与main的内部构建规则一致。P固定调用d.allowDebugMenu(prod)，所以该冻结render函数的Chrome设置行条件为false；真实窗口挂载/其它入口未验证。'),
        ('DCP-17', 'renderer', 'binding-F', 'F控件读debugChromePagesEnabled并在onChange调用设置helper；帮助文案列version/histograms且声明chrome-untrusted仍阻止。文案只记录产品意图，不充当native执行证据，亦不能因prod行隐藏推断为ChatGPT专属而删除。'),
    ]
    facts = []
    for eid, kind, label, claim in specs:
        item = u(kind, label)
        facts.append({'id': eid, 'baselineId': BASE, 'claim': claim, 'sourcePath': item['sourcePath'],
                      'sourceHash': item['sourceHash'], 'locator': item['byteRange'], 'spanHash': item['spanHash'],
                      'method': 'static-code', 'confidence': 'confirmed',
                      'verificationStatus': 'selected-complete-Program-source-confirmed; native-and-product-effects-unverified'})
    join_specs = [
        ('DCP-J01', 'Build policy -> bootstrap cached context -> main startup gate/effective preference -> native/local flag',
         [('shared', 'binding-R'), ('shared', 'binding-Hi'), ('shared', 'export-wi'), ('flavor', 'binding-m'), ('flavor', 'export-t'),
          ('bootstrap', 'binding-l'), ('bootstrap', 'binding-$'), ('bootstrap', 'context-factory-call-458121'), ('bootstrap', 'binding-oE'), ('bootstrap', 'export-I'),
          ('main', 'binding-g'), ('main', 'startup-e'), ('main', 'startup-context-fields'), ('main', 'startup-j'), ('main', 'startup-V'), ('main', 'startup-le'),
          ('main', 'native-call-startup'), ('main', 'binding-_'), ('main', 'binding-uf'), ('main', 'export-runMainAppStartup'), ('bootstrap', 'main-startup-import'), ('bootstrap', 'ready-startup-callback')]),
        ('DCP-J02', 'One preference key -> three write routes with distinct ordering -> side effect -> local flag',
         [('shared', 'preference-DEBUG_CHROME_PAGES_ENABLED'), ('shared', 'preference-debugChromePagesEnabled'), ('main', 'binding-r'), ('main', 'binding-p'),
          ('main', 'method-setGlobalStateValue'), ('main', 'method-setConfigurationValue'), ('main', 'method-setSettingValue'), ('main', 'settings-adapter-constructor'),
          ('main', 'settings-adapter-write'), ('main', 'settings-adapter-injection'), ('main', 'method-applySettingSideEffects'), ('main', 'binding-uf')]),
        ('DCP-J03', 'Process local flag -> mapped-page route/request consumers; separate native policy',
         [('main', 'binding-lf'), ('main', 'binding-uf'), ('main', 'binding-df'), ('main', 'binding-Ake'), ('main', 'flag-consumer-1533856'),
          ('shared', 'export-ii'), ('shared', 'binding-ka'), ('shared', 'binding-Oa'), ('shared', 'route-ma'), ('shared', 'route-va')]),
        ('DCP-J04', 'Renderer actual import/export -> initialized build policy -> constant prod UI condition',
         [('renderer', 'flavor-import-source'), ('renderer', 'flavor-import'), ('rendererShared', 'export-aen'), ('rendererShared', 'binding-FM'),
          ('rendererShared', 'binding-IM'), ('renderer', 'binding-P'), ('renderer', 'binding-F')]),
    ]
    joins = [{'id': jid, 'claim': claim, 'unitIds': [u(k, label)['id'] for k, label in labels],
              'qualification': 'Selected static lexical/import/assembly relationship; actual native/window/provider effects unverified.'}
             for jid, claim, labels in join_specs]
    buckets = {
        'analysisResolvedHere': ['Six build-flavor gates, resolver precedence and malformed metadata behavior.',
                                 'Bootstrap owner/cache and selected startup ordering.',
                                 'Three write routes, store readback, exception propagation and window broadcast position.',
                                 'Local flag mapped-URL consumers and separate constant-prod renderer gate.'],
        'implementationVerification': ['Exact trusted diagnostic page policy, chrome-untrusted restrictions and profile/guest boundaries.',
                                     'Native failure/return semantics, startup error handling and actual settings/RPC delivery.',
                                     'Stored/effective/native/local state behavior across writes, changes and restart.'],
        'externalInputOrProviderDevelopment': ['Independent Owl policy source/build inputs, or an independently implemented provider with parity evidence.'],
        'notReopenedByMissingRuntime': 'Missing native acceptance does not reopen the selected JS owner/condition findings.',
    }
    decision = {
        'runtimeGroup': 'RAM-04', 'status': 'selected-JS-startup-write-and-consumer-contract-resolved; native-privileged-page-provider-open',
        'firstPartyUnits': [
            {'responsibility': 'Build-flavor parse and explicit debug policy', 'proposedPath': 'apps/desktop/src/shared/build-flavor.ts'},
            {'responsibility': 'Startup preference application and mapped page behavior', 'proposedPath': 'apps/desktop/src/main/browser/chrome-page-policy.ts'},
            {'responsibility': 'Legacy and settings write side effects with distinct order', 'proposedPath': 'apps/desktop/src/main/settings/browser-diagnostics-effects.ts'},
            {'responsibility': 'Debug setting presentation and constant build gate', 'proposedPath': 'apps/desktop/src/renderer/settings/debug-settings.tsx'},
        ],
        'providerBoundary': 'packages/runtime-adapter/src/chrome-page-policy',
        'contractPath': 'packages/contracts/src/runtime/chrome-page-policy.ts',
        'contractDecisions': [
            'Keep strict boolean and build-flavor conditions; startup captures context, writes resolve again.',
            'Keep store, effective preference, native request and local flag distinct; no invented transaction or rollback.',
            'Preserve the legacy post-success global-state broadcast and skipped broadcast on exceptions.',
            'Keep native trusted-page enforcement separate from downloads/history application routes and other request policies.',
            'Treat Electron/Owl and schema/RPC/React helpers as dependency contracts, not generated third-party implementations.',
            'A hidden prod control is a build condition, not a proven ChatGPT-only exclusion.',
        ],
        'consumerOwnership': {'foundationTasks': ['W02', 'W03'], 'confirmedFeatureIdsAdded': [], 'completeConsumerCensus': False,
                              'qualification': 'No new T26/T31 feature identity follows merely from Browser Use/debug naming.'},
        'mode': 'unknown; retained', 'resolutionBuckets': buckets, 'fullRuntimeRouteAccepted': False,
    }
    witnesses = {k: {'programDeclarations': [x for x in v['declarations'] if x['programScope']],
                      'selectedNativeCalls': [x for x in v['calls'] if x.get('callee') == '_.app.setDebugChromePagesEnabled'],
                      'exports': v['exports']} for k, v in inspections.items()}
    evidence = publish('debug-chrome-policy-owner-v1-evidence.jsonl', ''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in facts).encode())
    replay_pin = publish('debug-chrome-policy-owner-v1-replay.json', encode(replay))
    counts = {'sourceFacts': len(facts), 'sourceUnits': len(units), 'sourceBytesIncludingOverlappingContext': sum(x['selection']['bytes'] for x in units),
              'sourceJoins': len(joins), 'distinctCompletePrograms': 6, 'reusedSourceSelections': 1, 'isolatedSourceCasesPassed': 15,
              'newReaRuns': 0, 'modelSubmissions': 0, 'clientLaunches': 0, 'realNativeCalls': 0, 'productScenariosExecuted': 0,
              'featureDefinitionsAdded': 0, 'featureModeChanges': 0, 'clientImplementationAdded': 0}
    doc = {'schemaVersion': 1, 'baselineId': BASE, 'recordedAtUtc': NOW,
           'scope': 'RAM-04 selected JS owner, build conditions and write/navigation contracts; native privileged pages unaccepted.',
           'facts': facts, 'sourceUnits': units, 'sourceJoins': joins, 'lexicalWitnesses': witnesses, 'decision': decision,
           'counts': counts, 'evidence': evidence, 'replay': replay_pin, 'query': pin(WORK / 'literal-query.json'),
           'fixtureCorrection': 'Initial replay lacked a windowManager broadcast double and failed. Corrected fixture records successful global-state broadcasts and verifies skipped broadcasts on exceptions; target source was unchanged.',
           'inputPins': [pin(WORK / name) for name in ['inspect.cjs', 'replay.cjs', 'replay.json'] + [k+'-inspection.json' for k in kinds]] +
                        [pin(Path(__file__)), pin('audio-measurement-owner-v1.json'), pin('runtime-adoption-matrix-v1.json'),
                         pin('runtime-surface-disposition.json'), pin('restoration-coverage-v18.json'), pin('feature-scope-v27.json'),
                         pin('feature-scope-v24-scenarios.json'), pin('exported-protocol-comparison.json')],
           'fullAnalysisCompleted': False, 'fullRuntimeRouteSelected': False}
    result = publish('debug-chrome-policy-owner-v1.json', encode(doc))
    summary = publish('debug-chrome-policy-owner-v1.md', '''# 调试页策略：启动、写入与导航边界

调试页开关要求值严格等于 true，且构建类型允许调试菜单。允许的构建是 dev、agent、nightly、internal-alpha；public-beta 和 prod 不允许。主进程解析顺序为有效 BUILD_FLAVOR、包元数据、NODE_ENV 默认值。损坏的候选 JSON 会抛错。

启动从 bootstrap 缓存上下文取得构建类型，在 app readiness、store 加载及选定迁移之后读取有效设置，再调用原生接口并更新本地 flag。设置写入则重新解析构建类型。冻结 renderer 导入的策略在该设置行固定检查 prod，因此控件条件为 false；这不是 ChatGPT 模式排除依据。

| 写入入口 | 顺序 | 原生调用抛错后的选定源码结果 |
| --- | --- | --- |
| setGlobalStateValue | native → flag → globalState.set → 窗口广播 | flag/store/广播均未执行 |
| setConfigurationValue | globalState.set → native → flag | set 已发生，flag 未更新，无本地回滚 |
| settings adapter | store.set → store.get → afterWrite → native → flag | 写入调用拒绝，set 已发生，flag 未更新 |

store 实际落盘与调用端错误处理不由这张表证明。三处 native 调用均无本地方法存在性检查或 try；启动异常另交给 bootstrap 外层处理。native 请求、本地 flag、stored 与 effective 设置应分别建模，不能自动加上回滚或把它们合并。

本地 flag 的两个选定消费者控制 downloads/history 到应用设置的映射及请求条件；其它 rewrite、权限和受限导航策略仍独立存在。这里不能证明 version/histograms 的 native 允许列表。帮助文案宣称可信诊断页可开放、chrome-untrusted 仍阻止，只作为产品意图记录。

建议将构建策略、main 启动/路由策略、设置副作用及 renderer 控件分别维护；原生执行经 runtime-adapter 的 chrome-page-policy 合同引入。第三方实现仍作为依赖。63 个源码选择含重叠生命周期上下文，不代表 63 个恢复模块。

17 条源码事实、4 条静态关联和 15 个隔离场景已交付。场景使用合成环境、包元数据、store、native 方法和 JSX；没有启动客户端、提交模型任务或执行真实原生调用，不计产品通过。首次脚本漏写广播替身的失败已修正，并增加成功/失败时广播检查。

选定 JS owner 与条件问题在此收口；真实特权页、profile/guest 隔离、native 返回/失败、设置送达与重启列为实施验证；独立 Owl 来源或经等价验证的 provider 列为构建前提。RAM-02/04/06 的选定内部源码项均已有结论，15 组运行时能力的完整采用资格仍未成立。下一项为 SD-03 已保存的 11 个协议变体差异及采用决定。

[结构化结论](debug-chrome-policy-owner-v1.json)、[源码事实](debug-chrome-policy-owner-v1-evidence.jsonl)、[隔离检查](debug-chrome-policy-owner-v1-replay.json)。
'''.encode())
    overlay = {'result': result, 'summary': summary, 'evidence': evidence, 'replay': replay_pin, 'counts': counts,
               'qualification': decision['status'], 'fullRuntimeRouteSelected': False}
    state = json.loads((OUT / 'analysis-state.json').read_text())
    state['debugChromePolicyOwner'] = overlay
    for key in ['runtimeAdoptionMatrix', 'runtimeSurfaceDisposition']:
        state[key]['debugChromePolicyOwnerRefinement'] = overlay
    state['stageDecisions']['debugChromePolicyOwnerOverlay'] = overlay
    state['stageDecisions']['nextAction'] = {
        'issueId': 'SD-03', 'question': '按exported-protocol-comparison.json的11个不同变体，定位精确字段、已有消费者和公开后台采用决定。',
        'closure': '逐变体给出来源、受影响合同与采用限制；来源或实际服务缺口单列，不重跑全协议发现。',
        'authorization': '只读已保存schema、冻结源码和自有分析脚本；无新增客户端、模型或个人数据操作。'}
    state['pending'] = ['SD-02: RAM-02/04/06选定JS owner及条件问题已交付；调试页补齐bootstrap构建类型、三类写入顺序、广播及renderer门控。15组运行时完整采用资格、native效果/来源/ABI、特权页和平台隔离仍开放；不重复已解决的JS盘点。'
                        if isinstance(x, str) and x.startswith('SD-02:') else x for x in state['pending']]
    state['updatedAtUtc'] = NOW
    (OUT / 'analysis-state.json').write_bytes(encode(state))
    lead = '当前[调试页策略](debug-chrome-policy-owner-v1.md)已交付17条源码事实、4条静态关联和15项隔离检查，明确启动缓存构建类型、设置重解析、三种写入顺序和prod控件门控。RAM-02/04/06选定JS源码项均已收口；native/provider、平台与特权页验证仍开放，不重新泛查已解决的JS条件。下一项为SD-03已保存的11个协议变体差异采用决定。373功能、48任务、1216未执行规格及模型授权余0不变，完整分析未完成。'
    for name in ['report.md', 'gaps.md']:
        _, tail = (OUT / name).read_text().split('\n\n', 1)
        (OUT / name).write_text(lead + '\n\n' + tail)
    receipt = {'result': result, 'summary': summary, 'evidence': evidence, 'replay': replay_pin, 'counts': counts}
    (WORK / 'publication.json').write_bytes(encode(receipt))
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
