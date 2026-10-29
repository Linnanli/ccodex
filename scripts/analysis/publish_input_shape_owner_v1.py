"""Publish a bounded avatar-overlay input-shape owner contract and source replay."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/input-shape-owner-work'
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'
NOW = datetime.now(timezone.utc).isoformat()
sha = lambda raw: hashlib.sha256(raw).hexdigest()
encode = lambda value: (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def pin(path):
    p = Path(path)
    if not p.is_absolute():
        p = OUT / p
    data = p.read_bytes()
    return {'path': str(p.relative_to(ROOT)), 'bytes': len(data), 'sha256': sha(data)}


def ref(name, pointer):
    result = pin(name)
    value = json.loads((ROOT / result['path']).read_text())
    for key in pointer[1:].split('/') if pointer else []:
        key = key.replace('~1', '/').replace('~0', '~')
        value = value[int(key)] if isinstance(value, list) else value[key]
    return {**result, 'jsonPointer': pointer}


def publish(name, raw):
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as handle:
        handle.write(raw)
    p.chmod(0o444)
    return pin(p)


def main():
    assert not (OUT / 'input-shape-owner-v1.json').exists()
    for name in ['analysis-state.json', 'report.md', 'gaps.md']:
        with (WORK / (name + '.before')).open('xb') as handle:
            handle.write((OUT / name).read_bytes())
    initial = json.loads((WORK / 'inspection.json').read_text())
    detail = json.loads((WORK / 'detail.json').read_text())
    replay = json.loads((WORK / 'replay.json').read_text())
    assert replay['casesPassed'] == len(replay['cases']) == 16
    units, by_key, by_label = [], {}, {}
    for row in initial['units'] + [u for r in detail['results'] for u in r['units']]:
        label = row['label']
        # Uninitialized declarations and an unrelated same-spelled Li binding are
        # discovery byproducts, not evidence for the selected publisher.
        if label.startswith(('binding-Q_', 'binding-Z_')):
            continue
        raw_unit = (ROOT / row['savedPath']).read_bytes()
        if label.startswith('binding-Li-') and raw_unit != b'Li=On.avatarOverlay':
            continue
        raw = (FROZEN / row['sourcePath'].removeprefix('app.asar/')).read_bytes()
        span = row['byteRange']
        assert sha(raw) == row['sourceHash']
        assert raw[span['start']:span['endExclusive']] == raw_unit and sha(raw_unit) == row['spanHash']
        key = (row['sourcePath'], span['start'], span['endExclusive'])
        if key not in by_key:
            unit = {k: row[k] for k in ['sourcePath', 'sourceHash', 'byteRange', 'spanHash', 'nodeType']}
            unit['id'] = f'ISO-SOURCE-{len(units)+1:02d}'
            unit['labels'] = []
            unit['selection'] = publish('raw/input-shape-owner/' + str(len(units)+1).zfill(2) + '.js.txt', raw_unit)
            by_key[key] = unit
            units.append(unit)
        unit = by_key[key]
        unit['labels'].append(label)
        by_label[label] = unit

    def selected(label):
        return by_label[label]

    specs = [
        ('ISO-01', 'member-supportsInputShape', 'supportsInputShape位于Program绑定Uce的ClassProperty初始化器中，直接调用electron.BrowserWindow.isInputShapeSupported()且没有可选调用/方法存在性保护。它在管理器实例初始化时求值；旧RSDF-11的“顶层能力检测”不能解释为Program加载时直接执行。'),
        ('ISO-02', 'M1e-window-services', '选定M1e装配函数创建new Uce(windowManager,globalState,isRemoteHostedPIPEnabled)，返回avatarOverlayManager，且将petVisibility设置变动接到该实例。此选定装配返回notchOverlayManager为undefined；不是所有其它构造路径或模式归属证明。'),
        ('ISO-03', 'K5-manager-selector', 'K5从options选择overlay manager：无notch manager时返回avatarOverlayManager；存在时结合ownsWebContents及isScreenOverlayWindow选择notch或avatar。createAppHost中的t=K5(this.options,e)传给new xpe(t,e)，故provider不能无条件写死为avatar实例。'),
        ('ISO-04', 'xpe-setPointerRegions', 'xpe保存注入manager与origin；setPointerRegions将origin.id作为首参数，随后透传两组矩形。该provider是窗口来源作用域的应用glue，静态方法形状不证明实际RPC送达。'),
        ('ISO-05', 'Uce-setPointerRegions', 'Uce.setPointerRegions在window不存在、已销毁或webContents.id与来源ID不同时不更新；匹配时替换inputShape与petControlsProximityRects，再执行交互策略。所选方法没有本地矩形schema验证。'),
        ('ISO-06', 'Uce-applyInputShape', 'applyInputShape在能力为假或shape为nullish时返回false；否则必要时先禁用整窗鼠标穿透，再将left/top转换为x/y并保留width/height，调用window.setInputShape。空数组仍会提交；原生返回值原样返回，truthy才将mode再次标记disabled；本方法不捕获原生异常。'),
        ('ISO-07', 'Uce-applyPointerInteractivityPolicy', '交互策略先尝试applyInputShape，再处理窗口可见性。隐藏窗口通常设置ignoreMouseEvents(true,{forward:false})，但win32且mode已disabled时直接返回；可见且shape结果truthy时结束，否则按pointerInteractive选择disabled或forwarding，并在关闭穿透时刷新光标。'),
        ('ISO-08', 'Uce-createWindow', 'createWindow可使用注入windowPresentation或windowManager创建avatarOverlay窗口，并把inputShape清为null、mousePassthroughMode重置disabled后应用策略；show/hide事件再次应用策略。macOS objc appearance桥有独立平台条件，该条件不包围ClassProperty中的能力查询。'),
        ('ISO-09', 'pointer-regions-publisher', '选定renderer发布callback读取F_(root)与I_(root,layout)，两组结果任一不相等时更新引用并调用Li.setPointerRegions。当前Sv作用域的Li=On.avatarOverlay；On由app-shared的fN导入，另一个Zg函数中的同名局部On不在此作用域内。实际fN provider和RPC传输未由本轮证明。'),
        ('ISO-10', 'geometry-M_', 'renderer矩形来自DOM：F_按document范围selector收集元素，经inert/CSS可见性与pointer-events筛选后调用M_；M_裁剪viewport及可滚动/裁剪祖先，向外floor/ceil取整。I_另生成proximity矩形。DOM祖先helper与完整渲染/坐标DPI行为不在本轮闭包中。'),
    ]
    facts = []
    for eid, label, claim in specs:
        unit = selected(label)
        facts.append({'id': eid, 'baselineId': BASE, 'claim': claim,
                      'sourcePath': unit['sourcePath'], 'sourceHash': unit['sourceHash'],
                      'locator': unit['byteRange'], 'spanHash': unit['spanHash'],
                      'method': 'static-code', 'confidence': 'confirmed',
                      'verificationStatus': 'selected-full-Program-source-confirmed; actual-runtime-native-and-RPC-delivery-unverified'})
    joins = [
        {'id': 'ISO-J01', 'claim': 'Program Uce class property -> one saved new Uce in M1e -> returned avatarOverlayManager',
         'units': [selected(x)['id'] for x in ['member-supportsInputShape', 'owner-instance-2', 'M1e-window-services']],
         'bindingProof': initial['identifiers']},
        {'id': 'ISO-J02', 'claim': 'createAppHost local t -> K5 options/origin selector -> new xpe(t,e) -> origin-scoped manager call',
         'units': [selected(x)['id'] for x in ['provider-manager-binding', 'K5-manager-selector', 'new-xpe', 'xpe-constructor', 'xpe-setPointerRegions']],
         'bindingProof': detail['results'][0]['bindings']},
        {'id': 'ISO-J03', 'claim': 'renderer On import -> Sv-local Li -> selected callback/geometry -> setPointerRegions surface; no wire-delivery claim',
         'units': [selected(x)['id'] for x in ['On-provider-specifier', 'On-provider-module', 'binding-Li-307704', 'pointer-regions-publisher', 'geometry-F_', 'geometry-R_', 'geometry-z_', 'geometry-M_', 'geometry-I_', 'selector-Q_', 'selector-Z_']],
         'bindingProof': [x for x in detail['results'][1]['bindings'] if x.get('declaration') and
                          (x['declaration']['text'] == 'Li=On.avatarOverlay' or x['declaration']['text'].startswith('On='))]},
    ]
    for join in joins:
        join['qualification'] = 'Selected lexical/source assembly relationship only; not a complete caller census, mode classification or live provider identity.'
    evidence = publish('input-shape-owner-v1-evidence.jsonl', ''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in facts).encode())
    replay_pin = publish('input-shape-owner-v1-replay.json', encode(replay))
    correction = {
        'priorEvidence': ref('runtime-surface-disposition.json', '/facts/10'),
        'priorClaimFragment': '保存的完整调用为顶层能力检测；该记录没有完整封闭owner',
        'refinement': 'The call is a Uce ClassProperty initializer, evaluated per constructed instance. M1e is a selected construction/return owner; complete product/provider closure remains unproven.',
        'supportingFactIds': ['ISO-01', 'ISO-02'], 'originalImmutableRecordChanged': False,
        'publicPropertyAbsenceObservationChanged': False}
    decision = {
        'runtimeGroup': 'RAM-06', 'status': 'bounded-source-owner-and-interactivity-contract-resolved; native-provider-integration-open',
        'firstPartyUnits': [
            {'responsibility': 'Renderer DOM rectangle collection and change suppression', 'proposedPath': 'apps/desktop/src/renderer/overlays/pointer-regions.ts'},
            {'responsibility': 'Origin-scoped RPC provider and overlay-manager selection', 'proposedPath': 'apps/desktop/src/main/overlays/pointer-region-provider.ts'},
            {'responsibility': 'Overlay shape/passthrough state machine', 'proposedPath': 'apps/desktop/src/main/overlays/pointer-interactivity.ts'},
        ],
        'runtimeProviderContract': ['Query actual input-shape support at manager creation with a defined unsupported result; raw missing-method invocation must not pass through unchanged.',
                                    'Preserve setInputShape rectangles, empty-list submission, exact result/error behavior and setIgnoreMouseEvents interactions.',
                                    'Preserve existing fallback policy, including hidden Windows handling and cursor refresh. Fallback existence does not waive native hit-testing parity.'],
        'mode': 'unknown; retain; pet/Quick Chat/voice names are not positive ChatGPT-only ownership evidence',
        'taskJoin': 'W03/W07 foundation responsibility proposal; exact current feature-consumer joins remain open.',
        'thirdPartyRule': 'Keep window/native runtime and imported RPC/base/equality/DOM helpers behind dependencies; no vendor implementation generated.',
        'newRuntimeBoundary': 'window.setInputShape is an instance effect contract newly associated here; the historical fixed 17-path missing-member denominator is unchanged.',
        'acceptance': ['Capability query, window creation and pointer delivery on each target platform/runtime.',
                       'Rectangle scaling/viewport clipping, empty lists, native return/error and origin mismatch.',
                       'Visible/hidden, interactive/noninteractive, show/hide/recreate and mouse forwarding transitions.',
                       'Actual renderer service/IPC receiver and overlay-kind selection; complete retained-feature/mode consumer ownership.'],
        'fullRuntimeRouteAccepted': False}
    doc = {'schemaVersion': 1, 'baselineId': BASE, 'recordedAtUtc': NOW,
           'scope': 'Selected input-shape consumer/owner and interactivity contract in two frozen Programs. No full avatar/Pets/voice implementation or runtime adoption claim.',
           'facts': facts, 'sourceUnits': units, 'sourceJoins': joins, 'priorEvidenceRefinement': correction,
           'decision': decision, 'replay': replay_pin, 'evidence': evidence,
           'query': pin(WORK / 'literal-query.json'),
           'counts': {'newSourceFacts': len(facts), 'selectedSourceUnits': len(units),
                      'selectedSourceBytes': sum(x['selection']['bytes'] for x in units),
                      'distinctProgramsParsed': 2, 'fullProgramParsePasses': 5, 'isolatedSourceCasesPassed': 16,
                      'newReaRuns': 0, 'newModelSubmissions': 0, 'newClientLaunches': 0,
                      'realNativeCalls': 0, 'productScenariosExecuted': 0, 'newFeatureDefinitions': 0,
                      'featureModeChanges': 0, 'newClientImplementation': 0},
           'remaining': ['Actual native support/result/coordinate semantics and independently buildable runtime implementation.',
                         'Imported shared fN provider instance, RPC/base wire and DOM helper provenance/complete consumers.',
                         'Retained product-mode ownership and complete overlay/Pets/voice/remote-PIP flows.'],
           'inputPins': [pin(WORK / x) for x in ['inspect.cjs', 'inspect_detail.cjs', 'inspection.json', 'detail.json', 'replay.cjs', 'replay.json', 'literal-query.json']] +
                        [pin(Path(__file__)), pin('runtime-adoption-matrix-v1.json'), pin('runtime-surface-disposition.json'),
                         pin('feature-scope-v27.json'), pin('restoration-coverage-v18.json'), pin('feature-scope-v24-scenarios.json')],
           'fullAnalysisCompleted': False, 'fullRuntimeRouteSelected': False}
    result = publish('input-shape-owner-v1.json', encode(doc))
    summary = '\n'.join([
        '# Overlay输入区域：来源与运行时合同', '',
        'isInputShapeSupported的第一方owner已定位到avatar-overlay的Uce管理类。它是实例字段初始化，选定M1e装配会创建该管理器；缺少方法时会在实例初始化抛错，尚未进入后续鼠标穿透fallback。旧“顶层能力检测”的表述由本次限定，原始证据保留。', '',
        'renderer由DOM产生两组矩形并抑制重复发布；xpe provider携带origin.id转发，manager只接受当前有效窗口的同ID更新。createAppHost经K5选择avatar或notch manager，因此provider不能固定绑定到一种overlay。实际fN服务、RPC传输与运行实例仍未验证。', '',
        '原生shape路径把left/top转换为x/y，保留尺寸，空数组仍提交；返回值和异常直接传播。可见窗口的shape结果为假时，按pointerInteractive使用整窗鼠标穿透fallback；隐藏窗口另有Windows分支。创建/show/hide会重置或重算相关策略。', '',
        '维护结构分为renderer矩形收集、来源作用域provider和main交互策略；原生能力查询与setInputShape作为独立runtime合同。已有fallback必须保留，也不能据此放弃原生hit testing的一致性。平台支持、DPI/坐标、返回值、异常和真实鼠标事件都需要所选runtime验证。', '',
        '16个隔离源码场景通过，覆盖无能力、null/空矩形、坐标转换、返回/异常、隐藏Windows、fallback、来源不符以及实例初始化时机。使用window/native/process替身，无原生窗口、客户端或模型服务调用；不计为产品行为通过。', '',
        '本次关闭RAM-06所选input-shape内部owner/策略问题；完整consumer、模式、native provider和运行验收保留。未按pet/Quick Chat/voice名称排除ChatGPT功能，373项功能、48任务及1216条未执行规格不变。下一内部项为RAM-02 measurement生产者和消费者来源追踪。', '',
        '[结构化合同](input-shape-owner-v1.json)、[源码事实](input-shape-owner-v1-evidence.jsonl)、[隔离回放](input-shape-owner-v1-replay.json)。', ''])
    summary_pin = publish('input-shape-owner-v1.md', summary.encode())
    overlay = {'result': result, 'summary': summary_pin, 'evidence': evidence, 'replay': replay_pin,
               'counts': doc['counts'], 'qualification': decision['status'], 'fullRuntimeRouteSelected': False}
    state = json.loads((OUT / 'analysis-state.json').read_text())
    state['inputShapeOwner'] = overlay
    state['runtimeAdoptionMatrix']['inputShapeOwnerRefinement'] = overlay
    state['runtimeSurfaceDisposition']['inputShapeOwnerRefinement'] = overlay
    state['stageDecisions']['inputShapeOwnerOverlay'] = overlay
    state['stageDecisions']['nextAction'] = {
        'issueId': 'SD-02', 'question': '追踪RAM-02具名audio measurement配置的数据生产者、读取/发布消费者及平台条件。',
        'closure': '从冻结源码绑定实际生产者/消费者合同；不能重复以接口存在性或metadata字段代替调用关系，native效果另列。',
        'authorization': '只读冻结源码和自有分析脚本；无新增客户端、模型或个人数据操作。'}
    state['pending'] = [
        'SD-02: 17缺席路径已接入15能力组；input-shape已补avatar/notch owner、renderer矩形与origin provider、native/fallback策略，并以16隔离场景核对。完整Owl/ABI/native效果与其余内部consumer仍开放；普通Electron直接替换资格未通过。'
        if isinstance(x, str) and x.startswith('SD-02:') else x for x in state['pending']]
    state['updatedAtUtc'] = NOW
    (OUT / 'analysis-state.json').write_bytes(encode(state))
    lead = '当前[overlay输入区域合同](input-shape-owner-v1.md)补齐avatar/notch owner、renderer矩形、来源ID转发及native/fallback策略，10条源码事实与16个隔离回放已交付。能力查询为实例初始化且无缺失方法保护，旧“顶层”表述已限定；实际平台/native/RPC与模式仍未验证。前项[37逻辑模块合同](logical-module-contracts-v1.md)已回读通过。下一内部项为RAM-02 measurement生产者/消费者；373功能、48任务、1216未执行规格保持，完整分析未完成。'
    for name in ['report.md', 'gaps.md']:
        _, tail = (OUT / name).read_text().split('\n\n', 1)
        (OUT / name).write_text(lead + '\n\n' + tail)
    receipt = {'result': result, 'summary': summary_pin, 'evidence': evidence, 'replay': replay_pin, 'counts': doc['counts']}
    (WORK / 'publication.json').write_bytes(encode(receipt))
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
