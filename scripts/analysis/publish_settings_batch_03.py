"""Publish settings controls and concrete restoration decisions, without implementing a client."""
import collections
import copy
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
BASE = 'codex-26.1007.30912-c5b273322a83'
OUT = ROOT / 'analysis' / BASE
WORK = ROOT / '.analysis-local/settings-operation-batch-03'
RAW = OUT / 'raw/settings-operation-batch-03'
FROZEN = ROOT / '.analysis-local/baselines' / BASE / 'extracted'


def load(p):
    return json.loads(p.read_text())


def sha(b):
    return hashlib.sha256(b).hexdigest()


def dump(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def pin(p):
    b = p.read_bytes()
    return {'path': os.path.relpath(p, OUT), 'bytes': len(b), 'sha256': sha(b)}


def ref(p, pointer):
    return {**pin(p), 'jsonPointer': pointer}


names = ['settings-operation-batch-03.json', 'settings-operation-batch-03.md', 'settings-restoration-decisions-03.md',
         'feature-scope-v10.json', 'feature-scope-v10.csv', 'feature-scope-v10-scenarios.json']
assert not RAW.exists() and not any((OUT / n).exists() for n in names)
before = load(OUT / 'analysis-state.json')
assert before['featureScopeCurrentView']['snapshotVersion'] == 9
old = load(OUT / 'feature-scope-v9.json')
old_scenarios = load(OUT / 'feature-scope-v9-scenarios.json')
assert len(old['features']) == 73 and len(old_scenarios['scenarios']) == 316
effective_old = copy.deepcopy(old)
overlay = load(OUT / 'feature-scope-v9-support-associations.json')
# Apply the already published correction when inheriting v9; preserve its immutable original.
effective_old['supportOperations'][23]['featureIds'] = ['FSC-0059', 'FSC-0064', 'FSC-0065', 'FSC-0066']
effective_old['features'][64]['supportOperationIds'] = ['operation:settings-batch-02:SUPPORT-001']
observations = load(WORK / 'isolated-observations.json')
assert observations['counts'] == {'isolatedSourceCases': 28, 'passed': 28, 'productScenariosExecuted': 0}
runs = load(WORK / 'parse-execution.json')
assert len(runs) == 9 and all(r['observedExitCode'] == 0 for r in runs)
programs = {r['outputDirectory']: load(WORK / r['outputDirectory'] / 'source-contracts.json') for r in runs}
source_bytes, spans = {}, set()


def verify(v):
    if isinstance(v, list):
        for x in v:
            verify(x)
    elif isinstance(v, dict):
        if 'sourcePath' in v and 'sourceHash' in v:
            p = v['sourcePath']
            if p not in source_bytes:
                source_bytes[p] = (FROZEN / p.removeprefix('app.asar/')).read_bytes()
            b = source_bytes[p]
            assert sha(b) == v['sourceHash']
            r = v.get('byteRange') or v.get('locator')
            if r and 'start' in r and 'endExclusive' in r and 'spanHash' in v:
                assert sha(b[r['start']:r['endExclusive']]) == v['spanHash']
                spans.add((p, r['start'], r['endExclusive']))
        for x in v.values():
            verify(x)


for folder, d in programs.items():
    assert d['fullProgramParsed']
    unresolved = d.get('unresolved', [])
    assert not unresolved or (folder == 'general-appearance-01' and {x['name'] for x in unresolved} == {'jc', 'Ac'})
    verify(d)
    for u in d['units']:
        assert sha((WORK / folder / u['sourceFilename']).read_bytes()) == u['spanHash']
verify(observations)
# The generic closure collector records no direct identifier assignments for these destructured aliases.
b = (FROZEN / 'webview/assets/general-settings-65e65871cdcd.js').read_bytes()
needle = b'{useFontSmoothing:Ac,usePointerCursors:jc}=Xt'
assert b.count(needle) == 1
start = b.index(needle)
alias = {'sourcePath': 'app.asar/webview/assets/general-settings-65e65871cdcd.js', 'sourceHash': sha(b),
         'byteRange': {'start': start, 'endExclusive': start + len(needle)}, 'spanHash': sha(needle),
         'nodeType': 'bounded-destructuring-assignment', 'expression': needle.decode(),
         'qualification': 'Unique exact source span supplements two uninitialized Program declarations; initialization order is not proven.'}
dump(WORK / 'bounded-aliases.json', [alias])
verify(alias)
RAW.mkdir(parents=True)
shutil.copytree(WORK, RAW / 'analysis')
shutil.copyfile(OUT / 'analysis-state.json', RAW / 'analysis-state-before.json')
for n in [Path(__file__).name, 'probe_settings_batch_03.cjs', 'settings_operations_ast.mjs', 'git_settings_ast.mjs']:
    shutil.copyfile(ROOT / 'scripts/analysis' / n, RAW / n)


def unit(folder, name):
    i = next(i for i, u in enumerate(programs[folder]['units']) if u['name'] == name)
    return ref(RAW / 'analysis' / folder / 'source-contracts.json', f'/units/{i}')


contract_path, summary_path, decisions_path, scope_path, csv_path, scenario_path = [OUT / n for n in names]
dispositions = load(OUT / 'settings-section-dispositions.json')
visibility = load(OUT / 'settings-mode-boundary-contracts.json')
entries = []
for slug, page in [('appearance', 'Appearance'), ('appshots', 'Appshots'), ('notifications', 'Notifications'), ('general-settings', 'General delegated desktop notifications')]:
    i, row = next((i, x) for i, x in enumerate(dispositions['entries']) if x['slug'] == slug)
    review = next(x for x in visibility['settingsSectionReviews'] if x['slug'] == slug)
    entries.append({'slug': slug, 'page': page, 'surfaceId': row['entryId'], 'factoryId': row['factoryId'],
                    'factoryRef': row['factoryRef'], 'visibilityRef': row['visibilityRef'], 'sectionRef': row['sectionRef'],
                    'routeInstanceRef': ref(OUT / 'settings-registry-contracts.json', f"/routeInstances/{row['savedSettingsRouteInstance']}"),
                    'staticRouteInstance': row['savedSettingsRouteInstance'], 'accessFamily': row['accessFamily'],
                    'availableInReducedHostList': review['availableInReducedList'], 'outerConditionRef': row['outerEntryConditionRef'],
                    'priorDispositionRef': ref(OUT / 'settings-section-dispositions.json', f'/entries/{i}'),
                    'conditions': ['Preserve selected-host/access-family and outer loading/error/redirect precedence.',
                                   'Account/platform/capability/flag values and actual mounting have not been observed.'],
                    'productMode': 'unknown', 'confirmedExclusion': False, 'actualMountObserved': False})
entries[0]['delegation'] = {'sourceRef': unit('appearance-01', 'f'), 'targetRef': unit('general-appearance-01', 'qs'),
    'contract': 'FA/QA navigation context targetId or targetText defaults Advanced expanded; navigationKey remounts the common appearance component. This is its own operation family, not a duplicate of the 28 previously scoped General goals.'}
entries[1]['conditions'].append('we returns null if imported BIt hook is true, platform loading, or U_t capability is false; Mini row additionally needs flag1532120159 and platform macOS.')
entries[2]['conditions'].append('ct renders the account group only for CNt; CNt is DG.status===allowed, and DG includes an optional debug override. This is not a selected-product-mode predicate.')
entries[2]['accountGuardRef'] = unit('initial-01', 'assignment-oNc')
entries[3]['delegation'] = {'sourceRef': ref(OUT / 'settings-general-page-contracts.json', '/dispatch'),
    'targetRef': unit('notifications-desktop-01', 'lt'), 'contract': 'Imported notification UI is a separate first-party child boundary. Account notification ct/Ye is not interchangeable with desktop task notifications lt/Ve.'}

# One operation is one parameterized user goal. Presentation controls are support, not extra features.
specs = []


def add(page, name, folder, units, effect, failure, acceptance, extra=(), support=()):
    specs.append(dict(pageIndex=page, name=name, folder=folder, units=units, effect=effect, failureAndCancellation=failure,
                      acceptance=acceptance, extra=extra, supportOperationIds=list(support)))


THEME = 'operation:settings-batch-03:SUPPORT-001'
ACCOUNT = 'operation:settings-batch-03:SUPPORT-002'
g = 'general-appearance-01'
add(0, '选择系统、浅色或深色外观', g, ['dc'], 'appearanceTheme defaults system; select system/light/dark through wjt with optimistic:false.',
    'No local catch, cancellation or same-value suppression in the selected callback; shared writer errors remain external.',
    ['Choose each mode and observe the nonoptimistic settings write and actual system appearance consumer.', 'Reject the write and verify no successful effective mode is invented.', 'Reopen/restart with a controlled system appearance change and verify stored mode and both variants.'])
add(0, '选择明暗变体的主题预设', g, ['Xa', 'to', 'io'], 'setCodeThemeId loads a preset, checks editRevision, then coordinates chrome theme and code-theme ID for that variant.',
    'A newer edit suppresses a stale preset load. Selected UI catches with a no-op; provider accent/error side effects and write compensation remain separate.',
    ['Select light/dark presets and verify paired persistence and preview seed loading.', 'Resolve an old preset loader after a newer color/font edit; it must not overwrite the newer edit.', 'Fail the second paired write and inspect compensation, partial flag and stored values after reopen.'], [('theme-provider-01', 'G1s')], [THEME])
add(0, '设置明暗变体的主题颜色', g, ['Xa', 'Fa', 'Ta', 'ka', 'Aa'], 'Per variant accent/surface/ink patches; custom accent sets accentSource:custom. Hex draft sanitizes six digits, commits only full hex. Account accent uses guarded account/user/revision synchronization.',
    'Partial hex is a draft, blur/popover close clears it. Account accent failure has toast handling; source provider catches fire-and-forget custom patches.',
    ['Change accent/background/ink independently in both variants; verify normalized values and custom accent source.', 'Test invalid/partial hex and account change during accent save; no stale account edit may apply.', 'Verify queue rollback and actual theme rendering/reopen with independently saved variants.'], [('theme-provider-01', 'G1s')], [THEME])
add(0, '设置明暗变体的界面、内容和代码字体', g, ['Xa', 'Wa', 'za', 'Ba', 'Ga', 'assignment-Ha'], 'Per-role family/face patch; visual UI shows family and Advanced UI shows style; content/code expose both. Enumerate host fonts, filter code families whose every face is monospaced; fallback accepts trimmed custom CSS family text when catalog is absent.',
    'Blank custom input resets family; same family/face is skipped. Host enumeration and font-face loading are separate adapters; no universal local error/retry UI is established.',
    ['Pick family and nondefault face for each role/variant and verify quoted family plus face metadata.', 'Exercise absent font catalog, custom fallback list, default reset and monospaced filtering.', 'Restart and verify theme font persistence plus host font loading and content fallback behavior.'], [('theme-provider-01', 'G1s')], [THEME])
add(0, '设置明暗变体的主题对比度', g, ['Xa', 'oo'], 'Advanced range control maps Number(input.value), min0/max100/step1, into a per-variant contrast patch.',
    'UI range bounds do not prove backend validation. Theme write queue handles failures; callback adds no explicit cancel.',
    ['Change contrast0/50/100 separately per variant and observe renderer result.', 'Inject a settings failure and inspect snapshot rollback without losing newer edits.', 'Reopen and verify effective contrast, including Advanced reset.'], [('theme-provider-01', 'G1s')], [THEME])
add(0, '设置明暗变体的半透明侧边栏', g, ['Ya', 'Xa'], 'Show unless isSystemBackdropSupported===false; toggle writes opaqueWindows inverse of displayed translucent state.',
    'Unknown support still shows control. Advanced reset preserves the existing opaque value when support is explicitly false.',
    ['Check true/false/unknown backdrop support and the inverse opaqueWindows mapping.', 'Fail a queued write and verify rollback/error boundary.', 'Verify actual backdrop behavior and persistence; unsupported reset must preserve the opaque preference.'], [('theme-provider-01', 'G1s')], [THEME])
add(0, '导入明暗变体的主题分享字符串', g, ['Xa', '$a'], 'Dialog validates through canImportThemeString; trimmed nonempty import calls provider parsing and paired writes; success closes, clears draft and toasts.',
    'Cancel/close clears draft without import. Empty or failed import toasts and keeps open/draft on failure. A failed second write attempts compensation.',
    ['Validate and import a share string for each variant; inspect resulting theme and code theme.', 'Cancel invalid/partial input without writes; fail parsing/write and retain editable input.', 'Fail compensation separately, then reopen and inspect actual partial saved state.'], [('theme-provider-01', 'G1s')], [THEME])
add(0, '复制明暗变体的主题分享字符串', g, ['Xa'], 'exportThemeString uses the current variant snapshot; clipboard adapter true yields success toast.',
    'Clipboard false emits no success toast; the selected callback adds no rejection catch. No settings mutation.',
    ['Copy both variants and decode/compare the theme payload against the actual snapshot.', 'Return clipboard false or rejection and verify source-defined feedback without false success.', 'Change a theme before copying and verify the latest snapshot is exported.'], [('theme-provider-01', 'G1s')])
add(0, '设置界面基础字号', g, ['Cc'], 'parseFloat then sansFontSize.schema.safeParse; invalid restores original text, valid canonicalizes number and skips unchanged value; pointer-up-after-change, blur and Enter commit.',
    'No local cancellation/error toast; schema is a provider boundary, not HTML min/max.',
    ['Check numeric-prefix parsing, invalid/out-of-range restore and unchanged suppression.', 'Exercise pointer drag, blur and Enter; inspect actual write rejection behavior.', 'Reopen and verify UI typography and actual stored size.'])
add(0, '设置代码基础字号', g, ['wc'], 'Same numeric commit structure for codeFontSize, separately applied to code/chat/diff consumer surfaces.',
    'No local catch or explicit cancel; numeric schema and renderer consumers remain separate.',
    ['Verify code schema bounds/prefix parsing and all three commit gestures.', 'Reject save and compare displayed input versus effective store without assuming local feedback.', 'Reopen and verify code/diff typography independently of interface size.'])
add(0, '设置 Pages 内容基础字号', g, ['sa', 'da'], 'CU gate controls the Pages row; dP().fontSize defaults14. parseFloat schema parsing uses parsed.data and skips equal values.',
    'Invalid input restores current size; no local save catch. Pages consumer and mode eligibility remain separate.',
    ['Vary CU gate and commit valid/invalid Pages font sizes under its actual schema.', 'Test pointer-up, blur and Enter plus writer rejection.', 'Reopen and verify Pages typography without changing interface/code sizes.'], [('shared-providers-01', 'dP')])
add(0, '设置减少动态效果偏好', g, ['vc'], 'reduced-motion-preference is system/on/off, defaultsystem, through the shared settings writer.',
    'No local error/cancel handler; actual system-media preference consumer is separate.',
    ['Choose all three values and vary OS reduced-motion state.', 'Reject save and inspect shared rollback/effective state.', 'Restart and verify animations follow the effective preference.'])
add(0, '设置 Pages 全宽偏好', g, ['ca', 'la'], 'CU-gated personal pagesFullWidth defaultsfalse; save a boolean and show danger toast on failure.',
    'This controls viewer preference, not collaborator layout. Callback has no pending disable or cancellation.',
    ['Toggle viewer full width with CU gate on/off.', 'Reject the writer and verify the dedicated toast and shared rollback.', 'Reopen Pages and verify the same viewer preference without assuming a document write.'], [('shared-providers-01', 'dP')])
add(0, '设置 Pages 智能标点偏好', g, ['ca', 'ua'], 'CU-gated pagesSmartPunctuationEnabled defaultstrue; onChange forwards a boolean via void shared write.',
    'No local catch/cancel or pending state in this selected callback.',
    ['Toggle the preference and observe actual editor substitutions under Pages eligibility.', 'Reject save and verify caller/global error behavior explicitly.', 'Reopen and verify both preference and actual typing behavior.'], [('shared-providers-01', 'dP')])
add(0, '设置差异标记样式', g, ['_c', 'qs'], 'AAt-gated Advanced row selects appearanceDiffMarkerStyle color/symbols, defaultcolor.',
    'No local save error/cancel branch; actual review consumers are external.',
    ['Check AAt visibility and color/symbols writes.', 'Reject save and inspect shared rollback.', 'Reopen review surfaces and verify marker rendering.'])
add(0, '设置可交互元素的指针样式', g, ['fc'], 'usePointerCursors defaultsfalse; boolean toggle through the shared writer with dedicated failure toast.',
    'No per-control pending guard or explicit cancel.',
    ['Change preference and inspect cursor consumers across interactive controls.', 'Reject save; verify dedicated danger toast and shared rollback.', 'Restart and verify the effective preference.'])
add(0, '选择 Dock 图标偏好', g, ['pc'], 'Dock row delegates visibility/previews to Xi(platform, dockIconPreviews). Offers app-default/codex-system and flag2200939124-gated space-system.',
    'No local catch. Labels alone do not establish product-mode exclusivity; native icon application is outside this callback.',
    ['Verify helper visibility with absent/present host previews and all gated choices.', 'Reject setting save and inspect effective icon preference.', 'Verify real native/system appearance icon update and restart persistence.'])
add(0, '设置 macOS 字体平滑偏好', g, ['Tc'], 'Only platform===macOS shows useFontSmoothing, defaulttrue; source alias Ac is destructured from the appearance descriptor.',
    'No local catch/cancel; OS/CSS consumers not established by the settings callback.',
    ['Verify macOS-only visibility and boolean writes.', 'Reject save and inspect shared rollback.', 'Restart and observe the actual typography consumer.'])
add(0, '重置高级外观设置', g, ['Jo', 'assignment-$o', 'Yo'], 'Reset visible for separate-mode UI, changed eligible advanced settings, or either variant advanced change; clears separate-mode UI immediately, then Promise.allSettled for changed scalar defaults and both variant resets.',
    'No confirmation. Any rejected result toasts, busy is released, completed effects stay. Advanced variant reset clears code/content fonts and UI face, preserves UI family; unsupported backdrop preserves opaque value.',
    ['Verify reset visibility, scoped changed-setting list and both variant resets.', 'Fail one reset; all siblings still attempt, busy releases and partial-error toast appears.', 'Reopen and inspect every actual stored default/partial effect; mode/colors/presets are not indiscriminately reset.'], [('theme-provider-01', 'G1s')], [THEME])

add(1, '配置或停用 Appshot 全局快捷键', 'appshots-01', ['_e', 've', 'ye', 'assignment-xe'], 'Windows offers DoubleAlt/DoubleShift; other branch DoubleCommand/DoubleOption/DoubleShift. Same selection skipped; None sends null; native appshot.setHotkey response seeds state and refreshes keymap, successful response records analytics.',
    'Capabilityfalse or supportedfalse hides row; pending disables. successfalse or thrown error shows inline error, not success analytics. Actual OS registration is a host boundary.',
    ['Verify platform options, same-value suppression, None and source-defined descriptions.', 'Exercise host absent, supportedfalse, rejected result and exception; inspect inline error/pending behavior.', 'Verify native registration/dispatch and restart with a synthetic capture target.'], [('initial-01', 'assignment-Ana')])
add(1, '设置 Appshot 接收会话策略', 'appshots-01', ['we'], 'appshotDestination defaultautomatic; automatic/last-chat/new-chat choices write shared settings. Unknown value displays first choice. Flag1532120159 changes Mini explanatory text.',
    'Save failure has destination toast. No per-row pending/same guard. Actual routing or capture is not triggered by the preference callback.',
    ['Select all policies and compare stored value with effective label.', 'Fail save and verify toast/shared rollback without a capture.', 'Observe actual recent/current/new-conversation routing and persistence separately.'], [('shared-01', 'assignment-jjt')])
add(1, '设置 Appshot 优先发送到可见 Mini', 'appshots-01', ['we'], 'Only flag1532120159 && platformmacOS shows appshotAlwaysSendToMini, defaultfalse; direct boolean shared write.',
    'No local catch, pending guard or cancellation. This page does not prove Mini routing implementation.',
    ['Vary flag/platform and toggle preference only when present.', 'Reject shared write and observe actual feedback/rollback.', 'Verify capture destination when Mini visible/hidden and after restart.'], [('shared-01', 'assignment-jjt')])
add(1, '设置 Appshot 声音效果', 'appshots-01', ['Te'], 'appshotSoundEnabled defaulttrue; direct boolean shared write.',
    'No local catch/pending/cancel. Actual sound playback consumer is external.',
    ['Toggle and verify preference under page availability guards.', 'Reject write and inspect actual caller/global feedback.', 'Verify actual capture sound and restart preference without conflating task notification sounds.'], [('shared-01', 'assignment-jjt')])

d = 'notifications-desktop-01'
for label, key, effect in [('任务完成提醒时机', 'turnMode', 'notifications-turn-mode off/unfocused/always defaultunfocused; direct write callback has no local catch.'),
                           ('权限请求提醒', 'permissionsEnabled', 'notifications-permissions-enabled boolean defaulttrue; async wrapper catches save failure and toasts.'),
                           ('需要输入时的提问提醒', 'questionsEnabled', 'notifications-questions-enabled boolean defaulttrue; async wrapper catches save failure and toasts.'),
                           ('dot 消息提醒', 'dotEnabled', 'notifications-dot-enabled boolean defaulttrue; async wrapper catches save failure and toasts.')]:
    add(3, '设置' + label, d, ['lt'], effect + ' Controls disabled when Me or Fe&&permissionQueryLoading; disabled OS permission banner retains focus handoff.',
        'Preference change does not prove an actual notification was delivered. OS permission and sender policy remain external.',
        [f'Vary permission loading/denied/allowed and set {key} values; inspect exact preference payload.',
         'Reject the write and verify this control\'s own catch/toast boundary rather than assuming uniform handling.',
         'Observe the corresponding actual notification under focus/OS conditions and verify restart persistence.'], [('shared-providers-01', 'assignment-mMt')])
add(3, '选择或导入桌面任务提醒声音', d, ['Ve', 'He'], 'Shared notifications-sound accepts default/classic/none, Darwin system sounds and selected custom sound. Preview begins before save; custom import provides decodeAudio/preview callbacks, selected result writes sound. Picker cancel does not write.',
    'Disabled/pending/imported Ajt guard blocks selection. Previous preview controller aborts and unmount aborts. Import/save/preview errors have distinct toasts; preview failure is not proof save failed. Advertised file limits are not validated by this UI function.',
    ['Verify platform sound list, custom object row, preview and stored selection.', 'Exercise native picker cancel/error/selected and independent preview/save failures; no write on cancel.', 'Verify local custom sound asset availability and actual notification playback after restart.'], [('shared-providers-01', 'assignment-mMt')])
add(3, '打开系统通知权限设置', d, ['lt', 'ut'], 'Denied OS notifications banner invokes systemPermissions?.openNotificationSettings through a mutation; loading disables its button.',
    'Host absence is an optional no-op; thrown mutation error has a specific toast. Opening settings does not grant permission.',
    ['Check denied-permission banner, pending controls and host call.', 'Reject host opening and verify error toast; missing capability must not claim OS settings opened.', 'Change OS permission externally and verify query refresh/focus handoff and enabled controls.'])
add(2, '管理账户通知类别与渠道', 'notifications-01', ['ct', 'qe', 'Je', 'Ye', 'Qe', 'tt', 'Ze', 'Xe', 'nt'], 'Capability CNt plus personal-account guard; GET/PATCH /notifications/settings with ChatGPT-Account-ID and per-user/account query key. Parameterized categories/channels, teen_safety contact eligibility and tasks manage-link delegation are distinct conditions.',
    'Latest per-account/category/channel mutation owns optimistic cache/rollback; stale success ignored but stale nonaborted error still toasts. Abort suppresses rollback/toast; cleanup invalidates without refetch then aborts tracked requests. Account/user guard rechecked before mutation; contact channels rechecked before update.',
    ['Verify capability/personal-account/loading/error/retry, account identity keying and category-channel rendering; tasks link target remains a navigation boundary.',
     'Race two changes to the same channel and change/unmount account; check latest rollback, stale error toast and abort behavior.',
     'Verify actual server persistence and contact eligibility; account-level ChatGPT settings do not replace local desktop notification preferences.'], [('initial-01', 'assignment-oNc'), ('shared-01', 'assignment-kTn'), ('shared-providers-01', 'assignment-DG')], [ACCOUNT])
assert len(specs) == 30

operations = []
for i, s in enumerate(specs):
    source_refs = [unit(s['folder'], n) for n in s['units']] + [unit(*x) for x in s['extra']]
    operations.append({'operationId': f'operation:settings-batch-03:OP-{i+1:03}', 'featureId': f'FSC-{74+i:04}',
        'pageIndex': s['pageIndex'], 'name': s['name'], 'trigger': 'Use the corresponding source-defined page control under its recorded conditions.',
        'guard': entries[s['pageIndex']]['conditions'], 'effect': s['effect'], 'failureAndCancellation': s['failureAndCancellation'],
        'sourceRefs': source_refs, 'supportOperationIds': s['supportOperationIds'], 'method': 'static-code',
        'verificationStatus': 'source-contract;product-scenarios-not-executed', 'completeChainProven': False})
mechanisms = [
    {'operationId': THEME, 'name': 'Per-variant theme write coordination', 'sourceRef': unit('theme-provider-01', 'G1s'),
     'claim': 'pendingWriteCount/snapshot, per-variant themeWriteQueue continued after rejection, paired write compensation, partial-write flag, pending snapshot cleanup, edit/accent revisions and conditional account synchronization.',
     'featureIds': [operations[i-1]['featureId'] for i in [2, 3, 4, 5, 6, 7, 19]], 'qualification': 'Host persistence, parser/normalizer, query finalizer and rendering adapters remain separate.'},
    {'operationId': ACCOUNT, 'name': 'Account notification optimistic concurrency and cancellation', 'sourceRef': unit('notifications-01', 'Ye'),
     'claim': 'Per channel mutation key/id with optimistic update, latest result ownership, guarded rollback and tracked AbortControllers; cleanup invalidation has refetchType:none.',
     'featureIds': [operations[-1]['featureId']], 'qualification': 'Actual HTTP service, authentication, query lifecycle and server cancellation are not proven by synthetic callbacks.'}]
counts = {'newCatalogPageSurfaces': 3, 'supplementedExistingPageSurfaces': 1, 'userGoals': 30, 'supportOperations': 2,
          'fullProgramParses': 9, 'uniqueSourceFiles': len(source_bytes), 'isolatedSourceCasesPassed': 28,
          'newProductScenarioSpecifications': 90, 'productScenariosExecuted': 0, 'modelSubmissionsAdded': 0,
          'originalClientRunsAdded': 0, 'confirmedChatGptExclusionsAdded': 0}
contract = {'schemaVersion': 'settings-operation-batch/1', 'baselineId': BASE,
    'scope': 'Appearance, Appshots, account Notifications and General delegated desktop notification controls; external adapters qualified.',
    'method': 'Reuse frozen REA-backed registry/factory evidence; nine full Program AST selections, source review and28 isolated source cases.',
    'entries': entries, 'operationContracts': operations, 'mechanisms': mechanisms, 'counts': counts,
    'sourceAliases': pin(RAW / 'analysis/bounded-aliases.json'), 'isolatedObservation': pin(RAW / 'analysis/isolated-observations.json'),
    'modeDecision': {'status': 'retain-pending-mode-review', 'confirmedExclusion': False,
                     'accountNotificationCandidate': 'ct/Ye manages explicit ChatGPT account notification channels, with capability/personal-account guards, but selected product mode and complete shared-consumer closure remain unproven.',
                     'doNotDeleteWholeModule': 'General imports a/i/t/r from the same notifications chunk; lt/Ve supplies desktop task alerts and sound. Appearance contains shared theme and account-accent branches. Module-level names/labels do not justify removal.'},
    'dependencyBoundary': {'thirdPartyImplementationGenerated': False,
        'keepFirstParty': ['appearance theme queue/revisions/compensation', 'font and theme UI policies', 'desktop/account notification separation', 'Appshot preference and host orchestration'],
        'externalize': ['React and compiler helpers', 'query/mutation library', 'schema/validation library', 'primitive controls/animation/color picker', 'host font and clipboard adapters', 'native appshot/notifications/permissions and audio'],
        'qualification': 'Existing dependency-import-decisions and embedded investigations remain package/version authority; chunk names and aliases do not establish package identity or exact versions.'},
    'remainingDecisions': ['actual selected-mode/capability consumers and safe ChatGPT-only branch pruning', 'theme import parser/normalizer and renderer CSS/font consumer contracts',
                           'OS native hotkey/capture/notification/sound adapters and packaged assets', 'actual settings/config flush and reopen/restart behavior',
                           'remaining35 settings page containers, complete entry/function mapping and cross-entry overlap', 'private runtime/protocol source and independent-build route'],
    'fullAnalysisCompleted': False, 'clientImplementationStarted': False}
dump(contract_path, contract)

scope, scenarios = copy.deepcopy(effective_old), copy.deepcopy(old_scenarios)
new_features, new_scenarios = [], []
for i, op in enumerate(operations):
    op_ref = ref(contract_path, f'/operationContracts/{i}')
    entry_ref = ref(contract_path, f"/entries/{op['pageIndex']}")
    ids = []
    for j, expectation in enumerate(specs[i]['acceptance']):
        sid = f"{op['featureId']}:SB03-OP-{i+1:03}:{j+1}"
        ids.append(sid)
        new_scenarios.append({'scenarioId': sid, 'featureId': op['featureId'], 'operationId': op['operationId'],
            'kind': ['behavior-and-guards', 'failure-and-cancellation', 'consumer-and-persistence'][j],
            'preconditions': {'pageEntryRef': entry_ref, 'actualValuesObserved': False}, 'trigger': op['trigger'],
            'expectedEffect': expectation, 'sourceRef': op_ref, 'executionStatus': 'not-executed', 'runtimeObservationRefs': [],
            'sourceQualification': 'Source-derived product specification; isolated function replay does not execute this scenario.',
            'authorization': 'Specification only; no real preference/OS/account/model operation or original client run.'})
    new_features.append({'featureId': op['featureId'], 'baselineId': BASE, 'name': op['name'], 'page': entries[op['pageIndex']]['page'],
        'definitionStatus': 'author-reviewed-scoped-user-goal', 'granularityRationale': 'One parameterized preference/operation; alternate gestures and variant values grouped, automatic coordination kept as support.',
        'operationMembers': [{'operationId': op['operationId'], 'operationType': 'settings-control-goal', 'trigger': op['trigger'], 'operationRef': op_ref}],
        'supportOperationIds': op['supportOperationIds'], 'sourceRefs': [op_ref, entry_ref], 'chain': op['effect'], 'conditions': op['guard'],
        'boundaries': [op['failureAndCancellation']], 'mode': 'unknown', 'modeEvidence': contract['modeDecision'],
        'retentionStatus': 'retain-pending-mode-review', 'sourceSpecificationStatus': 'static-control-and-qualified-service-contract',
        'runtimeStatus': 'not-observed-for-this-feature', 'isolatedObservationRef': contract['isolatedObservation'], 'completeChainProven': False,
        'scenarioIds': ids, 'knownGaps': contract['remainingDecisions'], 'implementationAcceptance': specs[i]['acceptance']})
scope['features'] += new_features
scope['newDefinitionIds'] = [x['featureId'] for x in new_features]
scope['previousScopeRef'] = pin(OUT / 'feature-scope-v9.json')
scope['previousScenarioRef'] = pin(OUT / 'feature-scope-v9-scenarios.json')
scope['appliedPriorSupportAssociationCorrection'] = pin(OUT / 'feature-scope-v9-support-associations.json')
scope['purpose'] = 'Finite user goal view with current settings controls; no complete or globally unique client denominator claimed.'
for i, m in enumerate(mechanisms):
    scope['supportOperations'].append({'operationId': m['operationId'], 'operationRef': ref(contract_path, f'/mechanisms/{i}'),
        'catalogNamespace': 'settings-batch-03', 'featureIds': m['featureIds'], 'classificationConfidence': 'confirmed',
        'excludedFromProductScope': False, 'operationEquivalenceClaimed': False, 'actualUiChainObserved': False,
        'status': 'supporting-mechanism', 'supportKind': m['name'], 'reason': m['qualification'], 'supportDoesNotExhaustConsumers': True})
scope['rootCandidateDispositions'] += [{'operationId': o['operationId'], 'role': 'user', 'childOperationIds': []} for o in operations]
scope['rootCandidateDispositions'] += [{'operationId': m['operationId'], 'role': 'support', 'childOperationIds': []} for m in mechanisms]
for i, page in enumerate(entries):
    ids = [o['featureId'] for o in operations if o['pageIndex'] == i]
    idx = len(scope['pageContainerRelations'])
    scope['pageContainerRelations'].append({'page': page['page'], 'legacyEntryId': 'ROUTE-0152',
        'supportInstancePointer': f"/registrations/151/staticMapInstances/{page['staticRouteInstance']}", 'factoryContractId': page['factoryId'],
        'featureIds': ids, 'relation': 'conditional-route-container-to-factory-to-controls', 'confidence': 'confirmed-static-association',
        'sourceRefs': [page['routeInstanceRef'], page['factoryRef'], ref(contract_path, f'/entries/{i}')],
        'conditions': page['conditions'], 'actualMountObserved': False, 'sameOperationClaimed': False, 'entryCompletelyResolved': False})
    scope['legacyFeatureRelations'] += [{'featureId': fid, 'status': 'conditional-container-association', 'entryIds': ['ROUTE-0152'],
        'pageRelationIndices': [idx], 'completeEntryEquivalenceProven': False,
        'remainingWork': '实际条件、挂载、消费者、持久化及模式仍待验证。'} for fid in ids]
scope['legacyEntryCoverage']['mappingUpdates'][0]['featureIds'] += scope['newDefinitionIds']
scope['legacyEntryCoverage']['qualification'] = '97 finite definitions conditionally relate to one legacy route template; no additional entry fully resolved.'
c = scope['counts']
c.update({'scopedFeatureDefinitions': 103, 'assignedUserOperations': 107, 'supportOperations': 27,
          'allKnownOperationCandidatesAccountedFor': 133, 'unexecutedScenarioSpecifications': 406,
          'normalizedBehaviorLeaves': 135, 'featuresConditionallyAssociatedWithLegacyContainers': 97,
          'additionalDiscoveredRootCandidates': 62,
          'rootCandidateDispositionCounts': {'user': 106, 'support': 25, 'pending': 1, 'composite': 1},
          'modeCounts': {'unknown': 103, 'codex': 0, 'chatgpt': 0, 'shared': 0}})
scenarios.update({'previousSnapshotRef': pin(OUT / 'feature-scope-v9-scenarios.json'),
                  'scenarios': old_scenarios['scenarios'] + new_scenarios, 'count': 406})
assert len(scope['features']) == 103 and len(scope['supportOperations']) == 27
assert sum(len(x['operationMembers']) for x in scope['features']) == 107
assert scope['features'][:73] == effective_old['features']
assert scope['supportOperations'][:25] == effective_old['supportOperations']
assert scenarios['scenarios'][:316] == old_scenarios['scenarios']
assert len({x['scenarioId'] for x in scenarios['scenarios']}) == 406
assert len({x['operationId'] for x in scope['rootCandidateDispositions']}) == 133
assert dict(collections.Counter(x['role'] for x in scope['rootCandidateDispositions'])) == c['rootCandidateDispositionCounts']
assert scope['retainedAssociationBacklog'] == old['retainedAssociationBacklog']
assert scope['operationReviewQueue'] == old['operationReviewQueue']
assert all(x.get('executionStatus', x.get('status')) == 'not-executed' for x in scenarios['scenarios'])
dump(scope_path, scope)
dump(scenario_path, scenarios)
with csv_path.open('w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['featureId', 'name', 'mode', 'operationCount', 'runtimeStatus', 'completeChainProven'])
    w.writeheader()
    for x in scope['features']:
        w.writerow({'featureId': x['featureId'], 'name': x['name'], 'mode': x['mode'], 'operationCount': len(x['operationMembers']),
                    'runtimeStatus': x['runtimeStatus'], 'completeChainProven': x['completeChainProven']})

summary_path.write_text('''# 设置第三批：外观、Appshots 与通知边界

本批交付30项有限用户目标、2项支撑机制、90条待执行产品规格和[具体恢复任务](settings-restoration-decisions-03.md)。累计[台账v10](feature-scope-v10.json)为103项定义、406条未执行规格。28项隔离源码回放通过，产品场景执行新增0；不表示完整功能分母、产品模式或独立构建已经闭合。

| 范围 | 工程决定 |
| --- | --- |
| Appearance | 页面委托 General 中的独立外观组件；恢复明暗变体、主题队列/补偿/版本检查及字体策略。不能只恢复设置表单。 |
| Appshots | 保留偏好与状态编排；将全局热键、捕获、Mini 路由和声音划成明确宿主接口，待核对实际消费者。 |
| Notifications | 账户渠道页面与 General 桌面提醒分开；同一 chunk 中的桌面提醒/声音控件仍需保留，不能按文件名整体剥离。 |

外观包含19项用户目标：模式、主题预设、颜色、字体、对比度、半透明侧边栏、导入、复制、界面字号、代码字号、Pages字号、减少动态效果、Pages全宽、Pages智能标点、差异标记、指针样式、Dock图标、macOS字体平滑及高级重置。高级展开和同时显示两套明暗控件是组件本地呈现状态，不另计持久化功能。高级重置并发尝试符合条件的各项默认值和两套高级主题；部分失败会保留已完成结果。

主题 provider 按变体维护 pending snapshot、write queue 和 edit/accent revisions。主题与 code-theme ID 的第二次写入失败会尝试补偿第一次；补偿失败保留 partial 标记。排队任务在前项失败后继续，较慢预设加载不能覆盖更新的编辑。外部的导入解析/规范化、查询 finalizer、真实存储与渲染器仍是独立边界。

Appshots四项目标分别为热键、接收会话策略、可见Mini优先和声音。热键不是普通参数化命令编辑：它调用 appshot.setHotkey；平台选项、None/null、能力缺失、pending、success:false 与异常各有分支。偏好保存不证明已经捕获或正确路由内容。

General补齐六项目标：任务完成、权限请求、提问和dot四种桌面提醒偏好，提醒声音及打开系统通知设置。声音预览、导入取消、导入失败、保存失败和播放失败分别处理；文案中的文件限制不等于UI已有验证器。Notifications页面另有一项参数化账户渠道目标，采用ChatGPT账户头和账户/用户查询键，按渠道维护乐观并发与AbortController。其能力门来自账户许可及可选debug覆盖，并非直接的所选产品模式；本批仍不发布确认删除项。

9次完整Program解析覆盖6个不同源文件。泛用闭包收集器保留的两个未初始化别名，已由唯一的原始解构赋值补充，未假称解析器自动解决。28项回放使用合成hooks、缓存、schema、transport、host和theme替身；两次早期失败来自夹具标签缺失和跨VM错误字符串预期，修正后全通过，没有因此改动目标源码。完整客户端、真实OS/账户/存储均未运行或修改。

已定位45个设置页面容器中，10个已有控件合同关联，35个待展开；这仅表示控件分析覆盖。原快捷键跨入口去重、12项关联待办、旧入口映射、模式/运行时/协议/持久化缺口继续保留。下一批转到本地环境、Hooks与MCP设置，并同时推进这些入口所需的宿主/协议决定。
''')
decisions_path.write_text('''# 本批恢复任务与依赖决定

这是分析阶段的可执行实施依据，覆盖本批30项目标；不是已经实现或可构建的客户端。全工程仍按原分析计划验收，其他功能组不得被本表替代。

| 恢复任务 | 第一方职责与拟维护模块 | 外部依赖/接口 | 验收出口 |
| --- | --- | --- | --- |
| R03-01 外观状态控制 | renderer/features/appearance：变体快照、串行写入、paired-write补偿、partial标记、edit/accent revisions；页面与provider分开 | settings repository、theme parser/normalizer、query lifecycle | 第二次写入/补偿分别失败、连续编辑、旧预设晚到；与真实持久化核对 |
| R03-02 外观控件 | renderer/features/appearance：19项目标、Advanced/双模式本地状态、数字/hex草稿、导入取消与重置范围 | React、query、schema、菜单/slider/color picker/animation；clipboard与system fonts宿主接口 | 按FSC-0074至0092的57条规格验收；字体、系统外观和Dock图标另测消费者 |
| R03-03 Appshot编排 | renderer/features/appshots：热键状态、偏好、平台/开关、错误反馈；host/capabilities/appshot：独立接口合同 | getState/setHotkey、原生捕获、Mini/会话路由、声音与资产 | FSC-0093至0096；必须观察真实热键注册/捕获/路由，不以保存成功代替 |
| R03-04 桌面通知 | renderer/features/notifications/desktop：四种提醒、声音导入/预览、系统权限反馈；host/capabilities/notifications | systemPermissions、notifications、audio decode/playback、实际事件发送者 | FSC-0097至0102；取消不保存、独立播放/保存失败、重启后自定义音频仍可用 |
| R03-05 账户通知候选剥离 | renderer/features/notifications/account单独隔离；按账户/渠道保存与取消，保持共享控件独立 | /notifications/settings、账户/个人账号许可与contacts、任务管理导航 | FSC-0103；先核对选中模式与全部消费者，再决定只删除账户专属分支；整块chunk删除不允许据此推断 |

模块路径是职责划分提案，不是要还原的原作者目录，也没有在源码树生成这些文件。第三方实现不复制进拟恢复源码；确切包来源、版本、修改状态以[依赖引入决定](dependency-import-decisions.md)和[内嵌依赖调查](embedded-dependency-summary.md)为准。本批只确定引用边界，尚未确认身份的 primitive/color-picker 等不能凭 dist/chunk 名猜包。

实施顺序：先定义设置仓库与宿主capability接口，再恢复外观队列/草稿和桌面通知/Appshot编排，最后接真实宿主、存储和渲染消费者。账户通知剥离核对独立进行，不阻断其余模块的恢复设计；Owl与公开app-server的全局替换决定仍需专项证据。

干净构建的新增输入：主题解析/预设资源与字体加载来源；Dock图标预览/应用接口；Appshot演示与捕获/声音资源；自定义提醒声音的本地导入资产与迁移规则。原归档资源可用于分析定位，正式工程每项都必须有独立资源来源/生成方式和打包路径，不能引用原安装目录。没有来源的资产继续列缺口，不通过删除对应功能缩小范围。

升级时为这30项目标保留稳定FSC标识，以入口条件、偏好schema/default、状态机、宿主方法与90条产品规格比较新版本；bundle文件名和minified符号仅用于证据定位。旧v9的支撑关联修正已应用到v10；旧快照保留。跨入口等价、整体模式分类与其余35个设置容器尚未完成，不能据本表宣称全面可升级。
''')
profile = {'contracts': pin(contract_path), 'summary': pin(summary_path), 'restorationDecisions': pin(decisions_path), 'counts': counts,
           'featureSnapshot': pin(scope_path), 'scenarioSnapshot': pin(scenario_path), 'fullAnalysisCompleted': False}
state = copy.deepcopy(before)
state['updatedAtUtc'] = datetime.now(timezone.utc).isoformat()
state['settingsOperationBatch03'] = profile
view = state['featureScopeCurrentView']
view.update({'snapshotVersion': 10, 'scope': 'Finite103 definitions; original71 roots plus62 additional candidates; full denominator unknown.',
             'ledger': pin(scope_path), 'csv': pin(csv_path), 'scenarios': pin(scenario_path), 'counts': c,
             'previousLedger': pin(OUT / 'feature-scope-v9.json'), 'reconciliationKind': 'appearance-appshot-and-notification-controls',
             'reconciliationArtifact': pin(contract_path), 'settingsOperationBatch03Overlay': pin(contract_path),
             'appliedPriorSupportAssociationCorrection': pin(OUT / 'feature-scope-v9-support-associations.json'),
             'entryConditionOverlayQualification': 'Original v7 entry overlay and newer per-batch entries apply to their respective feature cohorts.',
             'settingsSectionDispositionOverlayQualification': 'Original pending-page snapshot is qualified by later Git, batch02 and batch03 control contracts for seven subsequent pages.'})
view.pop('supportAssociationOverlay', None)
coverage = state['settingsOperationCoverage']
coverage['pageSurfacesWithScopedControlContracts'] += ['Appearance', 'Appshots', 'Notifications']
coverage['remainingPageContainers'] = 35
assert len(coverage['pageSurfacesWithScopedControlContracts']) == 10
stage = state['stageDecisions']
stage['latestSubstep'] = profile
stage['counts'].update({'currentFeatureDefinitions': 103, 'currentRootOperationCandidates': 133, 'currentUnexecutedScenarios': 406})
stage['nextAction'] = {'issueId': 'SD-01/SD-03/SD-06',
    'completedSubstep': 'Three new page surfaces plus General notification delegation;30 goals,28 isolated cases,90 unexecuted product specs and five restoration task groups.',
    'fixedInput': '剩余35个设置页面；优先Local environments、Hooks和MCP，复用已定位factory和宿主/协议证据。',
    'question': '将环境/扩展配置的入口、写入与运行消费者批量连接到恢复任务；同步核对实际公开后台协议适配。',
    'closure': '每组交付功能/支撑/重复处置、依赖引入和验收条件；不把运行缺口当作静态分析的全局前置条件。',
    'deferredDedicatedVerification': 'OS热键/捕获/通知、实际账户许可、持久化耐久性、Owl运行时与完整模式共享闭包。'}
assert state['latestBehaviorAuthorizationState'] == before['latestBehaviorAuthorizationState']
assert state['analysisMilestones'] == before['analysisMilestones'] and not state['fullAnalysisCompleted']
dump(RAW / 'validation.json', {'sourceParses': len(programs), 'uniqueSourceFiles': len(source_bytes), 'verifiedDistinctSpans': len(spans),
    'savedUnitsMatch': True, 'inheritedEffective73FeaturesAnd316ScenariosPreserved': True, 'appliedPriorCorrection': pin(OUT / 'feature-scope-v9-support-associations.json'),
    'queueAndAssociationBacklogPreserved': True, 'authorizationUnchanged': True, 'scopeCounts': c, 'newCounts': counts,
    'artifacts': [pin(OUT / n) for n in names]})
dump(OUT / 'analysis-state.json', state)
for filename, title in [('report.md', '# 阶段报告'), ('gaps.md', '# 未解决项与定向调查')]:
    p = OUT / filename
    text = p.read_text()
    heading, rest = text.split('\n', 1)
    lead = ('\n当前以[analysis-state.json](analysis-state.json)和[功能台账v10](feature-scope-v10.json)为准：103项有限定义、406条待执行规格，'
            '完整功能分母和模式分类尚未闭合。[第三批设置分析](settings-operation-batch-03.md)与[恢复任务](settings-restoration-decisions-03.md)'
            '已发布；10个设置页面有控件合同关联，35个待展开。28项新增隔离回放不是产品验收。'
            '原九项标准仍为4项资料/范围义务满足、5项部分完成，完整分析和客户端实现均未完成。下文历史批次数量按当时快照读取；下一行动以当前状态文件为准。\n')
    p.write_text(heading + '\n' + lead + rest)
for p in [*(OUT / n for n in names), *RAW.rglob('*')]:
    if p.is_file():
        p.chmod(0o444)
print(json.dumps({'published': str(contract_path), 'counts': counts, 'scopeCounts': c}, ensure_ascii=False))
