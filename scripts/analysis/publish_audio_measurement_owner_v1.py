"""Publish bounded measurement consumers and separate source decisions from native gates."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/audio-measurement-owner-work'
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'
NOW = datetime.now(timezone.utc).isoformat()
sha = lambda raw: hashlib.sha256(raw).hexdigest()
encode = lambda x: (json.dumps(x, ensure_ascii=False, indent=2) + '\n').encode()


def pin(path):
    p = Path(path)
    if not p.is_absolute():
        p = OUT / p
    b = p.read_bytes()
    return {'path': str(p.relative_to(ROOT)), 'bytes': len(b), 'sha256': sha(b)}


def publish(name, data):
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as handle:
        handle.write(data)
    p.chmod(0o444)
    return pin(p)


def main():
    assert not (OUT / 'audio-measurement-owner-v1.json').exists()
    for name in ['analysis-state.json', 'report.md', 'gaps.md']:
        with (WORK / (name + '.before')).open('xb') as handle:
            handle.write((OUT / name).read_bytes())
    inspections = {k: json.loads((WORK / (k + '-inspection.json')).read_text()) for k in ['main', 'shared', 'initial']}
    replay = json.loads((WORK / 'replay.json').read_text())
    assert replay['casesPassed'] == len(replay['cases']) == 22
    units, by_label = [], {}
    for kind, inspection in inspections.items():
        assert inspection['parse']['type'] == 'complete-Program'
        raw = (FROZEN / inspection['sourcePath'].removeprefix('app.asar/')).read_bytes()
        assert sha(raw) == inspection['sourceHash']
        for row in inspection['units']:
            span = row['byteRange']
            selected = raw[span['start']:span['endExclusive']]
            assert selected == (ROOT / row['savedPath']).read_bytes() and sha(selected) == row['spanHash']
            unit = {k: row[k] for k in ['sourcePath', 'sourceHash', 'byteRange', 'spanHash', 'nodeType', 'labels']}
            unit['id'] = f'AMO-SOURCE-{len(units)+1:02d}'
            unit['selection'] = publish(f'raw/audio-measurement-owner/{len(units)+1:02d}.js.txt', selected)
            units.append(unit)
            for label in unit['labels']:
                by_label[kind + ':' + label] = unit

    def u(kind, label):
        return by_label[kind + ':' + label]

    specs = [
        ('AMO-01', 'main', 'binding-jNe', '通用histogram provider由jNe按两个app方法均为function决定是否创建，并缓存MNe实例；该factory没有平台条件。已缓存后不重新检查方法存在性。'),
        ('AMO-02', 'main', 'binding-MNe', 'MNe.configureMeasurementCollection是async方法但既不return也不await运行时configure返回值；collectMeasurements则return运行时返回值，异步方法会采用其Promise结果。两方法均不在本地捕获异常。'),
        ('AMO-03', 'main', 'property-microphoneDiagnostics-3331688', 'createAppHost服务对象直接构造new vIe；与同对象的histogramCollector:jNe()为不同provider。vIe构造函数调用gIe，通用provider被能力检查省略不代表具名诊断不尝试配置。'),
        ('AMO-04', 'main', 'binding-gIe', '具名配置的进程级dZ在等待app readiness前即置true；ready立即调用hZ，否则whenReady().then(hZ)。后续构造不会重试；此函数没有本地平台判断或whenReady拒绝处理。'),
        ('AMO-05', 'main', 'binding-hZ', 'hZ用单元素数组配置Media.AudioSystem.GetDeviceDescription.Result；同步成功后写configuredAtMs/intervalStartedAtMs、generation=1、status=missing，异常只改unavailable。它不检查方法存在性，也不await配置返回值。'),
        ('AMO-06', 'main', 'binding-_Ie', '_Ie仅在configuredAtMs非null后增加collectionSequence并同步读取collectedAt、measurements。ready时[0,1)桶累加到droppedReplyCount、[1,2)桶累加到deliveredReplyCount；JS没有对前后快照做差，不能从此确认native返回的是增量。'),
        ('AMO-07', 'main', 'binding-_Ie', '找不到具名histogram时status为missing；不支持的桶或counter_discontinuity会清零两计数、增加generation并以本次collectedAt重设interval。收集异常改unavailable且不主动清旧计数；只有ready向返回对象暴露累计计数。'),
        ('AMO-08', 'main', 'binding-vIe', 'vIe.getSnapshot依次组合Date.now()、_le()的audioService和_Ie()的audioDiscovery；两项数据源不同。getSnapshot本身没有本地catch或平台分支。'),
        ('AMO-09', 'main', 'audio-service-onChildProcessGone', '音频服务生命周期处理器仅在type=Utility且serviceName=audio.mojom.AudioService时调用vle；该调用先于clean-exit检查，故选定处理器也累计符合条件的clean exit。register将此处理器接到child-process-gone，Nh/_le/vle分别保存、复制读取、更新退出次数与末次原因/退出码。'),
        ('AMO-10', 'shared', 'binding-Gli', 'Gli先删旧全局入口，provider存在时发布window.__codexHistogramCollector。configure等待RPC；collect通过GI.u要求结果可dispose，structuredClone后在finally释放，释放失败可使调用拒绝。cleanup只删除仍属于本次安装的全局对象。'),
        ('AMO-11', 'shared', 'binding-qli', 'qli把await $3.services赋给Program e6，并安装Gli(e6.histogramCollector)的断链cleanup。e6导出为fN，app-initial以Pd导入fN，Gia读取Pd.microphoneDiagnostics；这是选定静态装配关系，不证明实际RPC receiver实例或送达。'),
        ('AMO-12', 'initial', 'Gia-caller-5350443', '选定capture方法在diagnosticContext存在且采集成功时以Math.random()<.01抽样调用Gia；错误路径须为Error且name为NotFoundError或DevicesNotFoundError才调用。调用均未await，不阻塞原成功返回或错误重新抛出；其余失败不由该分支诊断。'),
        ('AMO-13', 'initial', 'binding-Gia', 'Gia并行查询浏览器audioinput聚合与可选host快照，合入session、采集上下文、开始/结束时间、visibility和focus，再写Realtime microphone discovery diagnostics日志并调用可选onDiagnostic。浏览器子结果只含计数、布尔和时间，不包含原始deviceId/label；其它合入字段t的内容不据此获得全日志匿名保证。host缺席为unsupported，外层异常被吞掉。'),
        ('AMO-14', 'initial', 'binding-Kia', 'Kia将回调成功/拒绝转为succeeded/failed，与qia超时竞争；Jia把qia初始化为2000ms。超时返回timed_out并abort，finally总会清timer并abort。Gia的host请求通过uh包装。'),
        ('AMO-15', 'shared', 'binding-JL', 'app-initial的uh导入shared s$t，后者导出Program JL。JL在signal abort或finally至多一次调用请求的Symbol.dispose，前后检查abort并移除监听；浏览器enumerateDevices回调未将signal转给浏览器API。'),
        ('AMO-16', 'initial', 'media-setup-analytics', '选定createMediaSetupAnalytics传给raa的diagnosticContext.onDiagnostic为e=>{}；媒体setup事件另交给connectionSetup.observeMediaSetup和Ap。本轮没有把完整诊断对象经该空回调发送的证据；日志接收和其它实例仍未验证。'),
    ]
    facts = []
    for eid, kind, label, claim in specs:
        unit = u(kind, label)
        facts.append({'id': eid, 'baselineId': BASE, 'claim': claim, 'sourcePath': unit['sourcePath'],
                      'sourceHash': unit['sourceHash'], 'locator': unit['byteRange'], 'spanHash': unit['spanHash'],
                      'method': 'static-code', 'confidence': 'confirmed',
                      'verificationStatus': 'selected-complete-Program-source-confirmed; actual-native-RPC-and-product-behavior-unverified'})
    join_specs = [
        ('AMO-J01', 'Separate service providers -> shared native app methods; named process-wide collector state',
         [('main', x) for x in ['property-microphoneDiagnostics-3331688', 'property-histogramCollector-3333052', 'binding-jNe', 'binding-MNe', 'binding-vIe', 'binding-gIe', 'binding-hZ', 'binding-_Ie', 'binding-uZ', 'binding-mZ']]),
        ('AMO-J02', 'Main lifecycle hook -> filtered service exit -> Nh -> _le -> diagnostic snapshot',
         [('main', x) for x in ['audio-service-register', 'audio-service-onChildProcessGone', 'binding-vle', 'binding-Nh', 'binding-_le', 'binding-vIe']]),
        ('AMO-J03', 'Awaited shared services -> e6/fN -> initial Pd -> Gia host snapshot; s$t/JL -> initial uh',
         [('shared', x) for x in ['binding-qli', 'export-fN', 'binding-Gli', 'binding-GI', 'export-s$t', 'binding-JL']] +
         [('initial', x) for x in ['import-Pd', 'import-uh', 'import-source-Pd', 'binding-Gia', 'binding-Kia', 'binding-Jia']]),
        ('AMO-J04', 'Capture success sampling/not-found error -> Gia -> aggregate/log/optional callback; selected callback is empty',
         [('initial', x) for x in ['Gia-caller-5350443', 'Gia-call-5350443', 'Gia-call-5351127', 'binding-Gia', 'media-setup-analytics', 'property-onDiagnostic-5359564']]),
    ]
    joins = [{'id': jid, 'claim': claim, 'unitIds': [u(k, label)['id'] for k, label in labels],
              'qualification': 'Selected static lexical/assembly relationship; actual instances and native/RPC effects unverified.'}
             for jid, claim, labels in join_specs]
    witnesses = {k: {'programDeclarations': [x for x in v['declarations'] if x['programScope']],
                      'selectedCalls': [x for x in v['calls'] if x.get('kind') == 'object-property' or 'Measurement' in x.get('callee', '') or x.get('callee') == 'Gia'],
                      'exports': v['exports']} for k, v in inspections.items()}
    witnesses['initial']['PdDeclarationsAllScopes'] = [x for x in inspections['initial']['declarations'] if x['name'] == 'Pd']
    evidence = publish('audio-measurement-owner-v1-evidence.jsonl', ''.join(json.dumps(f, ensure_ascii=False) + '\n' for f in facts).encode())
    replay_pin = publish('audio-measurement-owner-v1-replay.json', encode(replay))
    primary = {
        'reviewedAtUtc': NOW, 'scope': 'Public upstream candidate; not frozen Owl provenance or a native-bridge implementation.',
        'sources': [
            {'url': 'https://raw.githubusercontent.com/chromium/chromium/main/services/audio/public/cpp/audio_system_to_service_adapter.cc',
             'locator': 'ReportGetDeviceDescriptionResult, lines 169-172; GetDeviceDescriptions, lines 225-245',
             'retrieval': 'web tool read succeeded; moving main branch, no immutable commit or saved body hash established',
             'observation': 'A Boolean histogram records normal replies versus default callbacks. Both input and output device-description queries use it, so the name is not microphone-exclusive.'},
            {'url': 'https://chromium.googlesource.com/chromium/src/+/bb8f0e1d53b56671df73fe9440b9af88538e8de0/tools/metrics/histograms/metadata/media/histograms.xml',
             'locator': 'Media.AudioSystem.GetDeviceDescription.Result',
             'retrieval': 'web search returned indexed XML fragment; direct open failed; not a complete body retrieval',
             'observation': 'Metadata describes successful service replies versus crash-related default empty results. This corroborates intent, not Owl build identity or collection delta semantics.'}],
        'localSavedBodyRetrieval': pin(WORK / 'primary-retrieval.json'),
        'unresolved': ['Exact Chromium/Owl revision and patches.', 'Native JS bridge, configured-set ownership, sampling/reset semantics and multi-reader effects.'],
        'frozenSourceFactCountAdded': 0,
    }
    primary_pin = publish('audio-measurement-primary-review-v1.json', encode(primary))
    buckets = {
        'analysisResolvedHere': ['Two providers and their readiness/one-shot/error paths.', 'Named JS response fields, bucket accumulation and reset behavior.',
                                 'Selected renderer import/service/sampling/timeout/disposal/log path and empty callback.', 'Separate process audio-service exit state.'],
        'implementationVerification': ['Selected runtime must supply the exact histogram data and status/interval semantics.',
                                     'Actual RPC result disposal/structuredClone, cancellation, readiness and restart behavior.',
                                     'Configuration interaction and multi-window/multi-reader collection without duplicated or lost counts.',
                                     'Actual platform/device-discovery failures and mode/feature integration.'],
        'externalInputOrProviderDevelopment': ['Owl/native bridge source/build inputs, or a separately implemented and validated equivalent provider.',
                                             'Revision/provenance binding between upstream Chromium and frozen Owl.'],
        'notReopenedByMissingRuntime': 'Selected JS source findings stay resolved; native unknowns do not require repeating the same JS census.',
    }
    decision = {
        'runtimeGroup': 'RAM-02', 'status': 'selected-JS-producer-consumer-contract-resolved; native-producer-provider-open',
        'firstPartyUnits': [
            {'responsibility': 'Generic guarded RPC histogram provider', 'proposedPath': 'apps/desktop/src/main/diagnostics/histogram-provider.ts'},
            {'responsibility': 'Named process-wide audio discovery counters/readiness', 'proposedPath': 'apps/desktop/src/main/diagnostics/microphone-discovery.ts'},
            {'responsibility': 'Audio service exit lifecycle snapshot', 'proposedPath': 'apps/desktop/src/main/diagnostics/audio-service-lifecycle.ts'},
            {'responsibility': 'Renderer capture diagnostic aggregation/sampling integration', 'proposedPath': 'apps/desktop/src/renderer/realtime/microphone-discovery-diagnostics.ts'},
            {'responsibility': 'Renderer generic global entry and owned cleanup', 'proposedPath': 'apps/desktop/src/renderer/diagnostics/histogram-access.ts'},
        ],
        'providerBoundary': 'packages/runtime-adapter/src/measurement; runtime histogram implementation remains a dependency/provider, never generated vendor code.',
        'contractDecisions': [
            'Specify configure and collect sync/async behavior separately; named JS assumes synchronous snapshots.',
            'Preserve unavailable/missing/ready/unsupported/counter_discontinuity distinctions, generation and interval boundaries.',
            'Never substitute ordinary process metrics, audio samples, or empty ready responses for this histogram.',
            'Resolve native delta/reset and configured-set behavior before choosing a counter adapter. JS adds every ready bucket.',
            'Keep process-wide state separate from per-window service object lifetimes; serialize or coordinate only if native semantics require it, with parity tests.',
            'Retain required disposal/cancel interfaces through a dependency contract; GI/JL code is analysis evidence, not a recovered vendor implementation.',
        ],
        'consumerOwnership': {'confirmedSelectedConsumer': 'Realtime microphone capture diagnostics, a support path.',
                              'taskProposal': 'W03 runtime foundation; Voice/T28 is a potential product owner, but its existing ten settings features do not establish this capture flow identity.',
                              'confirmedFeatureIdsAdded': [], 'completeConsumerCensus': False},
        'mode': 'unknown; retained; no ChatGPT-only exclusion follows from voice/chat naming',
        'resolutionBuckets': buckets, 'fullRuntimeRouteAccepted': False,
    }
    counts = {'sourceFacts': len(facts), 'sourceUnits': len(units), 'sourceBytes': sum(x['selection']['bytes'] for x in units),
              'sourceJoins': len(joins), 'distinctCompletePrograms': 3, 'isolatedSourceCasesPassed': 22,
              'newReaRuns': 0, 'modelSubmissions': 0, 'clientLaunches': 0, 'realNativeCalls': 0,
              'productScenariosExecuted': 0, 'featureDefinitionsAdded': 0, 'featureModeChanges': 0, 'clientImplementationAdded': 0}
    doc = {'schemaVersion': 1, 'baselineId': BASE, 'recordedAtUtc': NOW,
           'scope': 'RAM-02 selected source producer/consumer and lifecycle analysis; native bridge/complete product closure remains open.',
           'facts': facts, 'sourceUnits': units, 'sourceJoins': joins, 'lexicalWitnesses': witnesses,
           'decision': decision, 'counts': counts, 'replay': replay_pin, 'evidence': evidence, 'primaryReview': primary_pin,
           'query': pin(WORK / 'exact-literal-query.json'),
           'inputPins': [pin(WORK / x) for x in ['inspect.cjs', 'main-inspection.json', 'shared-inspection.json', 'initial-inspection.json', 'replay.cjs', 'replay.json', 'primary-retrieval.json']] +
                        [pin(Path(__file__)), pin('runtime-adoption-matrix-v1.json'), pin('runtime-surface-disposition.json'),
                         pin('restoration-coverage-v18.json'), pin('feature-scope-v27.json'), pin('feature-scope-v24-scenarios.json')],
           'fullAnalysisCompleted': False, 'fullRuntimeRouteSelected': False}
    result = publish('audio-measurement-owner-v1.json', encode(doc))
    text = '''# 音频 measurement：生产与消费边界

已定位两条独立服务：通用 histogram RPC provider，以及实时语音麦克风发现诊断。后者在 createAppHost 创建时触发一次配置，进程 readiness 后配置具名 histogram；同步配置失败不自动重试。它同步读取 measurements，逐次累加两个布尔桶，处理 missing、unsupported、counter_discontinuity 和 unavailable。音频服务退出次数由独立的 child-process-gone 状态提供。

renderer 的选定采集方法在设备未找到错误时诊断，成功时按 1% 抽样。诊断并行读取浏览器设备聚合和 host 快照，以 2000ms 为超时，保留请求释放与取消。结果写入日志；选定装配的 onDiagnostic 为空回调，不能把它描述成已确认的诊断上传链。通用全局入口另在 clone 后释放 RPC 结果，并按对象身份清理。

[Chromium 上游实现](https://raw.githubusercontent.com/chromium/chromium/main/services/audio/public/cpp/audio_system_to_service_adapter.cc)提供设备查询正常／默认回调的布尔 histogram 线索，且输入和输出查询共用该名称。它尚未绑定冻结 Owl 版本，也不证明 Owl 的 JS 采集桥、增量或重置语义。

维护结构分为 main 的通用 provider、具名计数、音频服务生命周期，以及 renderer 的诊断聚合与通用入口。原生采集留在独立 runtime provider；第三方 RPC／释放 helper 不生成实现副本。JS 每次累加桶值，故必须在适配前核实 native 返回增量还是累计快照，以及多窗口、多读取方和重新配置的影响。不能用普通进程 metrics 或空 ready 结果代替。

本次关闭选定 JS owner、数据格式、调用和发布路径问题；保留完整消费者／模式归属及 native 实现缺口。22 个隔离源码场景通过，使用合成 app、设备、RPC、时钟数据，未启动客户端、调用原生接口或提交模型任务；不计产品场景通过。

后续问题分三类：源码结论本次交付；真实 RPC、平台、设备、计数和重启行为列为实施验证；Owl 采集桥来源／构建输入或经验证的等效 provider 列为取得或开发前提。缺少原生环境不重新打开已解决的 JS 盘点。下一内部分析项是 RAM-04 调试页策略的启动 owner 和完整条件。

[结构化合同](audio-measurement-owner-v1.json)、[源码事实](audio-measurement-owner-v1-evidence.jsonl)、[隔离回放](audio-measurement-owner-v1-replay.json)、[上游线索及限制](audio-measurement-primary-review-v1.json)。
'''
    summary = publish('audio-measurement-owner-v1.md', text.encode())
    overlay = {'result': result, 'summary': summary, 'evidence': evidence, 'replay': replay_pin, 'primaryReview': primary_pin,
               'counts': counts, 'qualification': decision['status'], 'fullRuntimeRouteSelected': False}
    state = json.loads((OUT / 'analysis-state.json').read_text())
    state['audioMeasurementOwner'] = overlay
    state['runtimeAdoptionMatrix']['audioMeasurementOwnerRefinement'] = overlay
    state['runtimeSurfaceDisposition']['audioMeasurementOwnerRefinement'] = overlay
    state['stageDecisions']['audioMeasurementOwnerOverlay'] = overlay
    state['stageDecisions']['nextAction'] = {
        'issueId': 'SD-02', 'question': '追踪RAM-04调试页策略的启动owner、设置写入与allowDebugMenu组合条件。',
        'closure': '交付完整选定源码条件与作用域决定；实际特权页/provider效果单列，不重复泛查接口存在性。',
        'authorization': '只读冻结源码和自有分析脚本；无新增客户端、模型或个人数据操作。'}
    state['pending'] = [
        'SD-02: 15运行时能力组中input-shape和measurement的选定JS owner/策略已交付；measurement具名计数、renderer采样/超时/释放、日志和空callback已绑定。native采集增量/重置、多读取方、Owl来源/ABI与平台效果仍开放；下一内部源码项RAM-04调试页策略。'
        if isinstance(x, str) and x.startswith('SD-02:') else x for x in state['pending']]
    state['updatedAtUtc'] = NOW
    (OUT / 'analysis-state.json').write_bytes(encode(state))
    lead = '当前[音频measurement合同](audio-measurement-owner-v1.md)已分开通用histogram与具名麦克风诊断，绑定main配置/累计、音频服务退出状态及renderer采样/超时/释放/日志，交付16条源码事实和22个隔离回放。native生产桥、增量/重置、多读取方和实际模式/平台仍未验证；问题已分为源码结论、实施验证和外部输入/provider开发。下一内部项为RAM-04调试页策略。373功能、48任务及1216未执行规格不变，完整分析未完成。'
    for name in ['report.md', 'gaps.md']:
        _, tail = (OUT / name).read_text().split('\n\n', 1)
        (OUT / name).write_text(lead + '\n\n' + tail)
    receipt = {'result': result, 'summary': summary, 'evidence': evidence, 'replay': replay_pin, 'primaryReview': primary_pin, 'counts': counts}
    (WORK / 'publication.json').write_bytes(encode(receipt))
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
