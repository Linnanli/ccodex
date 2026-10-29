"""Publish the bounded public-runtime/browser-settings feasibility result."""
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
PUBLIC = ROOT / '.analysis-local/public-runtime-comparison-work'
WORK = ROOT / '.analysis-local/native-browser-settings-work'
RAW = OUT / 'raw/native-browser-settings-comparison'
read = lambda path: json.loads(path.read_text())
sha = lambda data: hashlib.sha256(data).hexdigest()


def pin(path):
    data = path.read_bytes()
    try:
        name = str(path.relative_to(OUT))
    except ValueError:
        name = str(path)
    return dict(path=name, bytes=len(data), sha256=sha(data))


def write(path, value):
    with path.open('x') as output:
        json.dump(value, output, ensure_ascii=False, indent=2)
        output.write('\n')


def main():
    before = read(OUT / 'analysis-state.json')
    assert before['updatedAtUtc'] == '2026-10-24T09:36:14.710633+00:00'
    assert not RAW.exists() and not WORK.exists()
    assert not (OUT / 'native-browser-settings-comparison.json').exists()
    success = PUBLIC / 'browser-native-settings-guest-01'
    receipt = read(success / 'receipt.json')
    observation = read(success / 'data/runtime-observations.json')
    assert receipt['exitCode'] == 0 and receipt['runtimeIntegrity']['frameworkMatchesChecksummedArchive']
    assert observation['terminal'] and observation['exitCode'] == 0 and not observation['errors']
    assert observation['hostControl'] == 'CCODEX_OWNED_HOST'
    assert observation['guestControl'] == dict(status='resolved', title='CCODEX_OWNED_GUEST')
    assert len(observation['observations']) == 8
    assert all(row['status'] == 'rejected' and 'ERR_INVALID_URL (-300)' in row['message']
               for row in observation['observations'])
    assert observation['blockedExternalRequests'] == 0
    process_check = read(PUBLIC / 'browser-settings-final-process-check.json')
    assert process_check['matchingOwnedPublicRuntimeProcesses'] == []
    WORK.mkdir(); RAW.mkdir()
    write(RAW / 'analysis-state-before.json', before)
    for path in [ROOT / 'README.md', OUT / 'report.md', OUT / 'gaps.md']:
        shutil.copyfile(path, RAW / (path.name + '.before'))
    attempts = []
    folders = [f'browser-native-settings-{i:02}' for i in range(1, 5)] + ['browser-native-settings-guest-01']
    for name in folders:
        source = PUBLIC / name
        destination = RAW / name
        destination.mkdir()
        selected = ['receipt.json', 'stdout.txt', 'stderr.txt', 'run_public_electron_probe.py']
        selected += [path.name for path in source.glob('probe_*.cjs')]
        selected += ['data/runtime-observations.json', 'data/phase-journal.jsonl']
        for item in selected:
            if not (source / item).exists():
                continue
            target = destination / item
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / item, target)
        r = read(destination / 'receipt.json')
        attempts.append(dict(name=name, receipt=pin(destination / 'receipt.json'), exitCode=r['exitCode'],
            timeout=r.get('timeout', False), completeCapabilityProbe=name == 'browser-native-settings-guest-01',
            observation=pin(destination / 'data/runtime-observations.json')
            if (destination / 'data/runtime-observations.json').exists() else None))
    shutil.copyfile(PUBLIC / 'browser-settings-final-process-check.json', RAW / 'process-check.json')
    shutil.copyfile(Path(__file__), RAW / Path(__file__).name)
    shared = ROOT / '.analysis-local/baselines' / BASE / 'extracted/webview/assets/app-shared-8bd9d0399038.js'
    data = shared.read_bytes()
    assert sha(data) == '607ad0866dd25ed3764711b4467a9b60708353a599485b5249ff4cbe0e870245'
    literals = []
    for row in observation['observations']:
        token = ('`' + row['requestedUrl'] + '`').encode()
        start = data.find(token)
        assert start >= 0
        literals.append(dict(url=row['requestedUrl'], sourcePath='app.asar/webview/assets/app-shared-8bd9d0399038.js',
            sourceHash=sha(data), byteRange=dict(start=start, endExclusive=start + len(token)),
            spanHash=sha(token), occurrenceCount=data.count(token),
            qualification='Exact frozen literal occurrence; not a new complete-Program parse or proof of runtime initializer/host/mode.'))
    write(RAW / 'source-url-literals.json', literals)
    source_path = OUT / 'raw/settings-operation-batch-08/browser-use/source-contracts.json'
    source = read(source_path)
    refs = []
    for name in ['Ai', 'assignment-aa', 'da', 'ba', 'xa']:
        i, unit = next((i, unit) for i, unit in enumerate(source['units']) if unit['name'] == name)
        frozen = ROOT / '.analysis-local/baselines' / BASE / 'extracted' / unit['sourcePath'].removeprefix('app.asar/')
        b = frozen.read_bytes(); r = unit['byteRange']
        assert sha(b) == unit['sourceHash'] and sha(b[r['start']:r['endExclusive']]) == unit['spanHash']
        refs.append(dict(**pin(source_path), jsonPointer=f'/units/{i}'))
    scope_path = OUT / before['featureScopeCurrentView']['ledger']['path']
    scope = read(scope_path)
    feature_index, feature = next((i, f) for i, f in enumerate(scope['features'])
                                 if f['name'] == '打开内嵌浏览器资料、扩展和站点设置')
    assert feature['featureId'] == 'FSC-0221'
    families = {
        'contactInfo': ['chrome://settings/addresses', 'chrome://settings/contactInfo'],
        'passwordManager': ['chrome://password-manager/passwords', 'chrome://password-manager/'],
        'extensions': ['chrome://extensions/'],
        'siteSettings': ['chrome://settings/content', 'chrome://settings/handlers', 'chrome://settings/cookies']}
    comparison = dict(schemaVersion='native-browser-settings-comparison/1', baselineId=BASE,
        recordedAtUtc=datetime.now(timezone.utc).isoformat(),
        question='Can fixed public Electron directly host the privileged settings pages used by the frozen renderer?',
        sourceRefs=refs, literalRefs=pin(RAW / 'source-url-literals.json'),
        featureRef=dict(**pin(scope_path), jsonPointer=f'/features/{feature_index}'),
        owningTask='T26', runtimeModule='packages/runtime-adapter/src/browser-settings',
        rendererModule='apps/desktop/src/renderer/features/browser/settings',
        contractModule='packages/contracts/src/browser-settings',
        implementationStarted=False, runtime=observation['versions'],
        completeObservation=pin(RAW / 'browser-native-settings-guest-01/data/runtime-observations.json'),
        attempts=attempts, processCheck=pin(RAW / 'process-check.json'),
        requiredFamilies=[dict(kind=kind, sourceUrls=urls) for kind, urls in families.items()],
        observedDecision='The tested stock Electron 42.3.0 guest-webview embedding rejects all eight requested chrome URLs with ERR_INVALID_URL. Owned host and guest data controls pass.',
        architectureDecision=dict(id='RUNTIME-DECISION-privileged-browser-settings',
            status='direct-stock-embedding-rejected-in-fixed-probe; independent implementation unresolved',
            callerRequirement='Preserve kind/capability/host checks, source settings partitions, paired mountId lifecycle, theme, URL navigation/history and disposed/late-response guards.',
            interfaceBoundary='Renderer requests a declared settings kind; a runtime adapter owns the privileged page, backing browser services and partition. Renderer markup alone does not supply this capability.',
            externalDependency='A separately obtainable runtime with these pages and backing services, or a behavior-verified independent implementation. Do not generate bundled Chromium/React/third-party implementation copies.',
            candidates=[dict(route='independent runtime/fork providing required WebUI and services', selected=False, independentlyBuildable=False),
                        dict(route='independent settings UI plus equivalent browser-service adapters', selected=False, equivalentBehaviorProven=False)],
            fullTargetPreserved=True, omittedKinds=[],
            acceptance=['All four kinds load and navigate under the correct independent partition and capability gates.',
                        'Mount/unmount pairing, back/forward, route synchronization and stale-response cleanup match the frozen caller contract.',
                        'Native-page operations and backing data/service behavior are inventoried and verified with synthetic records before full-feature acceptance.',
                        'Runtime source/distribution, version, hashes, build/ABI and third-party dependency boundaries support clean build and upgrade.']),
        modeQualification='Source entry has codexOrWorkLocal access family; it is not a product-mode equality test. No ChatGPT-only exclusion follows from the current evidence.',
        failedAttemptQualification='Attempts 01-04 are aborted/crashed/incomplete. Attempt03 preserves a data control and one ERR_FAILED result, but its later crash is not attributed to Chrome URL support. Attempt04 timed out and its post-timeout checkpoint is nonterminal; none is counted as complete capability acceptance.',
        limits=['Fixed public runtime/platform and fresh synthetic embedding only; no original Owl/client execution.',
                'Rejected direct loads do not establish absence in every Electron release, custom fork or alternative implementation.',
                'Native-page functions, actual selected mode, account data, original runtime ABI and full-client behavior remain unverified.'],
        counts=dict(publicRuntimeLaunchAttempts=5, completeGuestCapabilityProbes=1, incompleteAttempts=4,
                    positiveOwnedControls=2, rejectedPrivilegedUrls=8, requiredSettingsFamilies=4,
                    originalClientRunsAdded=0, modelSubmissionsAdded=0, productFeaturePassesAdded=0,
                    featureDefinitionsAdded=0, confirmedModeExclusionsAdded=0),
        fullAnalysisCompleted=False)
    artifact = OUT / 'native-browser-settings-comparison.json'
    write(artifact, comparison)
    report = OUT / 'native-browser-settings-comparison.md'
    report.write_text('''# 原生浏览器设置页：独立运行时差异

固定公共 Electron 42.3.0 darwin-x64 的 guest webview 无法直接加载本次八个 Chromium 设置 URL，均返回 `ERR_INVALID_URL (-300)`。同一次探针的自建 host 与 guest 控制页均成功，进程退出码0；归档及运行时Framework与已校验归档一致。这是公共候选运行时的能力差异，不是原客户端功能验收。

| 原设置类别 | 本次直接加载结果 |
| --- | --- |
| 联系资料 | addresses、contactInfo 均拒绝 |
| 密码管理器 | passwords、根路径均拒绝 |
| 扩展 | extensions 拒绝 |
| 站点权限 | content、handlers、cookies 均拒绝 |

恢复任务T26／FSC-0221必须接入独立的原生浏览器设置能力。renderer保留类别/host/capability门控、路由和展示；`packages/runtime-adapter/src/browser-settings`负责特权页面、底层浏览器服务与分区，合同放在`packages/contracts/src/browser-settings`。以上为模块归属，尚未生成客户端实现。

运行时若保留这些页面，需要可独立取得并固定的运行时或fork；若独立重建设置界面，还须有等价的底层浏览器服务与行为证据。仅修改JS import、复制页面外观或隐藏不可用入口不能满足完整目标。第三方Chromium、UI等实现仍作为外部依赖，不生成进业务源码。两条候选路线均未证明可独立构建或行为等价。

原调用合同还要求特定partition、配对mountId/theme生命周期、back/forward/URL同步、销毁和迟到响应保护；详见[源码操作合同](settings-operation-batch-08.json)。原生页面内部操作及底层数据尚未完整盘点，仍归属于这项运行时任务，不能算已完成。入口的codexOrWorkLocal是权限分类，当前没有ChatGPT专属排除结论。

共五次公共运行时尝试：前四次含SIGABRT、SIGSEGV和超时，均作为不完整探针保留；第三次仅获得控制页与一个ERR_FAILED，崩溃原因未证明。最终一次改为单窗口、真实guest webview，完整测得上述结果。探针未读取真实浏览记录/密码、调用模型或运行原客户端，进程检查无本次残留。

[结构化结果及逐次原始记录](native-browser-settings-comparison.json)保存完整结果、边界、模块归属与验收条件。本结论只排除本次固定运行时中的直接嵌入路线，不宣称所有Electron版本或自定义实现都缺少该能力。原9项分析标准的状态、237项有限定义和808条待执行产品规格保持不变，目标继续。
''')
    profile = dict(comparison=pin(artifact), summary=pin(report), counts=comparison['counts'],
                   owningTask='T26', featureIds=['FSC-0221'], fullAnalysisCompleted=False)
    state = copy.deepcopy(before)
    state['updatedAtUtc'] = datetime.now(timezone.utc).isoformat()
    state['nativeBrowserSettingsComparison'] = profile
    state['runtimeCapabilityDecisions']['additionalCapabilityOverlay'] = profile
    state['publicRuntimeComparison']['additionalBrowserSettingsOverlay'] = profile
    state['analysisMilestones']['currentScopeOverlay']['runtimeFeasibilityOverlay'] = profile
    state['stageDecisions']['runtimeBoundaryOverlay'] = profile
    state['stageDecisions']['nextAction'] = dict(issueId='SD-03/SD-01',
        completedSubstep='Fixed public Electron guest-webview rejects eight required browser settings URLs; preserve explicit T26 native capability requirement.',
        question='Which top-level task/session entry predicates select Codex versus ChatGPT product behavior, independently of account access-family selectors?',
        fixedInput='Reuse saved mode-transition/context/entry contracts and current v15/v6; classify entry ownership and shared consumers before deleting modules.',
        closure='Identify product-flow owners with exact existing source evidence, or keep a localized unresolved mode record; do not repeat settled permission-family helpers or public Chrome URL probes.',
        deferredDedicatedVerification='Browser WebUI/service implementation stays local to T26/runtime adaptation. Twenty settings containers remain in the finite inventory; all original scope and zero remaining model authorization remain unchanged.')
    assert state['featureScopeCurrentView'] == before['featureScopeCurrentView']
    assert state['latestBehaviorAuthorizationState'] == before['latestBehaviorAuthorizationState']
    assert state['buildInputDispositions'] == before['buildInputDispositions']
    lead = '已完成[原生浏览器设置页的公共运行时对照](native-browser-settings-comparison.md)：自建host/guest控制通过，固定Electron 42.3.0中八个内部设置URL均被拒绝。T26／FSC-0221须保留独立运行时/服务能力；这项差异不算原客户端验收，不改变237项有限定义和808条待执行规格。\n\n'
    for name in ['report.md', 'gaps.md']:
        path = OUT / name
        text = path.read_text(); heading, body = text.split('\n\n', 1)
        path.write_text(heading + '\n\n' + lead + body)
    path = ROOT / 'README.md'; text = path.read_text(); heading, body = text.split('\n\n', 1)
    path.write_text(heading + '\n\n' + lead.replace('(native-browser-settings-comparison.md)', f'(analysis/{BASE}/native-browser-settings-comparison.md)') + body)
    assert read(OUT / 'analysis-state.json') == before
    temporary = OUT / 'analysis-state.json.tmp'
    write(temporary, state); os.replace(temporary, OUT / 'analysis-state.json')
    for path in [artifact, report] + list(RAW.rglob('*')):
        if path.is_file():
            path.chmod(0o444)
    write(WORK / 'publication.json', dict(updatedAtUtc=state['updatedAtUtc'], profile=profile,
          allOriginalFeatureAndAuthorizationCountsPreserved=True, goalStillActive=True))
    print(json.dumps(dict(profile=profile, updatedAtUtc=state['updatedAtUtc']), ensure_ascii=False))


if __name__ == '__main__':
    main()
