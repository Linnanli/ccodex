"""Bounded browser, computer-history and voice recovery decisions.

Imported/native/service implementations remain assigned integration boundaries.
No source-module replay is a product acceptance result.
"""


def specifications():
    result = []

    def add(page, name, units, effect, failure, behavior, negative, receiver, support):
        result.append(dict(pageIndex=page, name=name, units=units, effect=effect,
                           failureAndCancellation=failure,
                           acceptance=[behavior, negative, receiver], support=support))

    B = lambda *names: [('browser-use', name) for name in names]
    C = lambda *names: [('chronicle', name) for name in names]
    V = lambda *names: [('voice', name) for name in names]
    add(0, '设置网页与本地开发 URL 的打开位置', B('da', 'fa', 'Ca', 'Ta'),
        'Keep web and local-development destinations as two independent preference keys in one parameterized destination control. Save/analytics run only when selection changes; retain host and in-app-browser availability gates.',
        'A same-value selection has no write. Root loading/redirect differs from a disabled subpage; the preference writer and actual URL-opening consumer remain external.',
        'Vary web/local destination independently and verify source option sets, key and change-only dispatch.',
        'Select the current value, change host or delay capability loading; preserve no-op/loading/redirect behavior.',
        'Verify durable preference and actual URL-opening adapter under selected host and mode.', [0])
    add(0, '设置浏览器地址栏完整 URL 显示', B('fa', 'Ea'),
        'Write showFullUrl preference from the gated general browser section; on rejection display the dedicated save-error toast.',
        'Showing a preference control does not prove the browser address bar consumes or persists it.',
        'Toggle and inspect exact key/value; check path/query/fragment rendering in the eventual browser consumer.',
        'Reject preference save and verify dedicated error feedback without reporting a durable update.',
        'Connect shared preference storage to actual address-bar rendering and restart behavior.', [0])
    add(0, '设置浏览器批注截图规则', B('fa', 'Sa'),
        'Select always or necessary for annotationScreenshotsMode; necessary is presented as drag-selection-only screenshots.',
        'Screenshot capture, transmission and quota effects are delegated; this control alone does not prove a capture happened or that the feature is ChatGPT-exclusive.',
        'Inspect both values and the annotation consumer for drag-selection versus other comments.',
        'Vary capability/host and unavailable capture service; do not equate preference write with screenshot creation.',
        'Verify annotation capture policy and durable preference without accessing personal screen content.', [0])
    add(0, '按类型或全部清除浏览器数据', B('fa', 'Oa'),
        'When browsingHistory service exists, open the delegated native browsing-data dialog; otherwise use source-defined per-type/all mutation controls and success/error feedback.',
        'Block duplicate fallback mutation while pending; dialog-launch failure has separate feedback. Native deletion implementation and actual type coverage remain delegated.',
        'Inspect native-versus-fallback choice, allowed data types and requested type/all payload.',
        'Fail native launch or mutation, attempt pending duplicate, and verify no false cleared state.',
        'Verify actual browser partition, permission and deletion effects using separately authorized synthetic browser data.', [0, 1])
    add(0, '设置下载目录与保存位置提示', B('pa'),
        'Under downloads capability, choose a directory, save only a non-null selection, reset directory to null, or toggle promptForDownloadLocation.',
        'Directory cancellation does not write; choose/save failure shows error and finally clears pending. Reset/toggle callbacks retain their source behavior without invented rollback.',
        'Inspect directory selection/cancel/default reset and independent save-dialog preference.',
        'Reject directory selection/save and verify pending release; preserve no write for cancelled selection.',
        'Verify native directory picker, preference storage and actual download destination/prompt behavior.', [0, 1])
    add(0, '浏览搜索和打开浏览历史', B('Gr', 'Nr', 'qr', 'jr'),
        'Require browsingHistory capability; initialize query from q, debounce search 200ms, filter visit source, paginate and group by local calendar day. Open through current conversation browser when accepted, otherwise source browser-event/navigation fallback.',
        'Loading, error, empty source, no matches and pagination failure differ. Row identity includes URL, visit time and actor flag; favicon accepts data:image/ only.',
        'Inspect q initialization, source filter, day groups, pagination and open-routing choices with synthetic records.',
        'Fail first/next page or remove capability; check retry/redirect and avoid classifying an error as empty history.',
        'Verify actual history service, conversation-browser ownership and URL-opening behavior without reading personal history.', [0, 1])
    add(0, '移除单条或选中的浏览历史', B('Gr', 'Pr', 'Mr', 'jr'),
        'Require dataRemovalPermitted.history=true and no pending removal; map selected row identities to deduplicated URL/local-day requests, remove through history service, clear matching selection and invalidate browser-browsing-history.',
        'No permission, empty selection or pending state prevents dispatch. Failure reports error and releases pending; row-level actor identity is finer than removal identity.',
        'Check single/bulk removal, same-day deduplication, actor/ordinary rows and selection cleanup.',
        'Deny permission, reject removal or submit empty/pending removal; verify guard and final state.',
        'Verify native removal semantics and authoritative history refresh on synthetic records only.', [1])
    add(0, '浏览和操作下载历史', B('ci', 'Qr', 'di', 'assignment-ni'),
        'Debounce search 200ms and paginate; merge live downloads into persisted results using started/in_progress/paused candidates, retaining persisted fileExists for matching IDs and descending start order. Dispatch source row actions through the downloads receiver and require ok before invalidation.',
        'Live-only completed/nonmatching records are not injected. Failed/throwing action reports error and clears pending ID. The concrete filesystem/download commands remain delegated.',
        'Inspect persisted/live merge, search, grouping, pagination and source-defined row-action availability.',
        'Vary ok:false, rejected action, missing file and query failure without showing an action as complete.',
        'Verify actual download receiver, file ownership/status and action effects with synthetic downloads.', [1])
    add(0, '清空下载历史记录', B('ci'),
        'Invoke downloads.clearHistory, invalidate browser-download-history on success, show dedicated clear error and release clearing state in finally.',
        'Clearing history is not evidence of deleting downloaded files; actual service semantics remain external.',
        'Check explicit clear trigger and authoritative history invalidation.',
        'Reject clearHistory and verify error feedback and pending release without a false empty list.',
        'Verify record removal and any independent file effects against an owned synthetic fixture.', [1])
    add(0, '打开内嵌浏览器资料、扩展和站点设置', B('da', 'ba', 'xa', 'Ai', 'Ri', 'Bi', 'Yi', 'Xi', 'ea', 'assignment-aa'),
        'Use capability-gated contactInfo/passwordManager/extensions/siteSettings native pages. Mount via browser-settings-webview-mounted with unique mountId/theme and the source partition; unmount/listener cleanup pairs the ID. Preserve Chrome settings URL/route and synthetic navigation-stack rules.',
        'Late mount/title responses are guarded after disposal or webview replacement. Native page internals and Chromium/Owl embedding cannot be replaced by ordinary renderer markup without an adapter decision.',
        'Inspect kind/capability, partition, URL, paired lifecycle and back/forward/site-details routing.',
        'Dispose before mount/title completion, fail bridge or navigate back then branch; verify cleanup and history truncation.',
        'Verify independent runtime can expose the required privileged pages, IPC lifecycle, partition and navigation behavior.', [0, 1])

    add(1, '启用或关闭 Computer history', C('En', 'Pt', 'Vt'),
        'Gate by selected host config, chronicle service and memory capability. First enable offers allow-all/customize onboarding; memory-disabled path enables memories then reads chronicle state to select already_active/enable_required/retry_required. Turn-off uses host-bound toggle.',
        'Loading/service absence/pending prevents toggle. Requested enable with returned enabled:false reports permission denial; onboarding dismissal is not enabled state. Imported enable-memory/state helpers remain delegated.',
        'Inspect onboarding branches, hostId, memory prerequisite and authoritative returned enabled state.',
        'Deny permissions, fail memory enable or config/service loading; preserve distinct failure and pending states.',
        'Verify actual recorder/service/OS permissions, config persistence and memory prerequisites without recording personal activity.', [2])
    add(1, '暂停恢复或重试 Computer history 录制', C('Dn', 'En'),
        'Separate enabled config from recorderState/activationState. Starting/waiting/failed/unavailable select retry/resume/setup states; normal pause/resume mutation receives the current recorder state.',
        'Disable during toggle/pause pending; service or newer query error is not a confirmed off state. Failure has dedicated pause/resume or activation feedback.',
        'Vary starting/waiting/idle/stopped/failed recorder conditions and inspect chosen action.',
        'Fail pause/resume/retry or return newer query error; retain correct enabled versus running distinction.',
        'Verify effective recorder lifecycle and callbacks using an isolated owned recorder fixture.', [2])
    add(1, '配置 Computer history 的应用和网站范围', C('En', 'Dn', 'on'),
        'Show selected applicationBundleIdentifiers plus urlDomains count, invalidate settings before opening imported permissions dialog, and enable only after customization saved when onboarding requested it. History rows can update per-application observed policy.',
        'Closing customization clears the deferred-enable flag; service-unavailable disables selection. Imported dialog and settings normalization are retained integration work.',
        'Inspect permissions entry, selected count, customization-save sequencing and application/observed mutation.',
        'Close without save, reject application update or lose service; verify no unintended enable/update success.',
        'Verify app/domain policy receiver, recorder enforcement and persistence with synthetic application identifiers.', [2, 3])
    add(1, '设置菜单栏录制指示器', C('Sn'),
        'Write chronicleMenuBarIndicatorEnabled through shared preference adapter; retain source disable condition and dedicated save error.',
        'Indicator visibility is a display preference and does not establish recorder permission or recorder state.',
        'Inspect preference key, value and menu-bar indicator consumer.',
        'Reject write or disable control and verify dedicated feedback without implying recorder state changed.',
        'Verify preference persistence and actual menu-bar integration on supported platform.', [2])
    add(1, '浏览 Computer history 时间分组与应用记录', C('on', '_n', 'vn', 'sn', 'ln'),
        'Query and group records by local calendar day with today/yesterday/date labels; retain expand/highlight, item/application detail and load/error/retry/empty states.',
        'This is separate from browser URL history and audio recordings. Imported query/record fields and real capture remain explicit; displaying synthetic groups does not validate recording.',
        'Inspect multi-day and multi-application grouping, details, expansion and highlight behavior.',
        'Fail loading, vary date boundaries or unmount during highlight timeout; verify cleanup and correct empty/error distinction.',
        'Verify actual history query/recorder data contract using owned synthetic records only.', [3])
    add(1, '确认删除 Computer history 条目或时间范围', C('on', 'pn', 'kn', 'An'),
        'Use interval request for individual item and last_ten_minutes/last_hour/last_day/all with interval:null for range clearing; confirm before mutation. Copy states that actions and derived memories will be deleted; this downstream effect remains to verify.',
        'Null request or pending blocks confirmation dispatch; success closes range dialog and error reports dedicated failure. Escape/outside pointer cancels inline confirmation.',
        'Inspect interval/range request, confirmation title and success close behavior.',
        'Cancel, submit null/pending or reject deletion; preserve data and avoid asserting derived-memory deletion without service evidence.',
        'Verify actual deletion scope, derived-memory effect and authoritative refresh on synthetic records.', [3])

    add(2, '选择麦克风输入设备', V('Cn', 'wn', 'On', 'Dn', 'Tn'),
        'When media enumeration exists, list non-default audioinput devices with nonempty IDs; null preference means system default. Opening picker requests permission/media, refreshes devices and stops obtained tracks in finally. Preserve selected/unavailable/fallback labels.',
        'Enumeration unsupported disables picker; error/empty/loading differ. Selection-write failure reports error; permission acquisition and OS device access remain adapters.',
        'Inspect supported/unsupported list, default/custom preference and post-refresh track cleanup.',
        'Deny capture, reject refresh/save or remove selected device; verify cleanup and fallback labels.',
        'Verify OS permission/device preference and actual dictation/voice consumer without enabling a real microphone in analysis.', [4])
    add(2, '设置语音识别主语言', V('sn', 'assignment-ln'),
        'Read saved voiceMainLanguage with auto fallback; patch account_user_setting feature voice_main_language and optional ChatGPT-Account-ID, then invalidate account settings and voice query.',
        'Missing data/pending disables selection; initial load error offers retry. Save failure shows error. An endpoint/header containing ChatGPT does not establish product-mode exclusivity.',
        'Inspect source language options, account header, exact patch query and invalidations.',
        'Fail initial read or patch; verify retry/pending and no successful invalidation after failed patch.',
        'Verify account-bound service and actual recognition language behavior in the selected product mode.', [4])
    add(2, '选择实时语音聊天声音', V('Qt'),
        'Gate section and effective access separately; find effectiveVoiceSlug in compatible voices, open imported picker and save parsed selection through the voice adapter for new voice chats.',
        'Unavailable account voice/error offers retry; missing data/effective voice shows loading. Picker preview/audio playback and save internals remain delegated.',
        'Inspect access loading/error/unavailable, effective selection and save-adapter input.',
        'Return unavailable/unknown voice or fail loading; avoid treating dialog close/preview as saved preference.',
        'Verify compatible voice service, selection persistence and realtime consumer under a separately authorized synthetic flow.', [4])
    add(2, '设置实时语音聊天快捷键', V('tn'),
        'Set or clear commandId realtimeVoice through set-codex-command-keybinding; update codex-command-keymap-state cache from success and invalidate it.',
        'Preserve capture cancel/pending/error presentation; actual command registry/OS registration remains shared integration work.',
        'Inspect set accelerator versus clear update and cache reconciliation.',
        'Reject mutation or cancel capture; verify error state and no unintended registration.',
        'Verify the existing command/keybinding adapter and OS shortcut consumer; cross-entry equivalence is not assumed.', [4])
    add(2, '控制语音聊天的屏幕上下文', V('Qt', 'en'),
        'Show only under macOS, host feature and dynamicTools.appshotsEnabled. Disable saves screenContextEnabled=false directly; enable saves true through imported permission callback.',
        'No enable preference write before permission callback. Preference does not prove foreground-screen inspection or live voice tool authorization.',
        'Inspect platform/host/tool gates and enable-versus-disable sequencing.',
        'Withhold permission callback or disable capability; verify no enable write/capture.',
        'Verify screen-context adapter and actual permission/voice-call boundaries without inspecting personal screen content.', [4])
    add(2, '控制听写开始和结束提示音', V('kn', 'An'),
        'When dictation and source extra capability permit, write dictationSoundsEnabled and report dedicated save failure.',
        'Saving this preference does not play audio or verify actual capture/playback behavior.',
        'Inspect capability, exact key/value and actual start/stop-cue consumer.',
        'Reject write or disable dictation and verify gating and dedicated error.',
        'Verify preference persistence and cue behavior using an isolated synthetic media adapter.', [4])
    add(2, '设置按住或单次切换听写快捷键', V('kn', 'Ln'),
        'Under global dictation support, distinguish hold/double-tap and optional single-tap toggle modes; call their separate command names with hotkey payload, update hotkey cache and invalidate both hotkey/keymap queries.',
        'success:false shortcut-conflict produces explicit alternate-shortcut error; thrown errors and capture cancellation retain their source handling. OS registration is delegated.',
        'Inspect hold/toggle endpoints, clear/null, conflict response and cache reconciliation.',
        'Return shortcut conflict, throw or cancel capture; do not show an unregistered shortcut as successful.',
        'Verify OS shortcut service and distinction from general command keybindings before merging adapters.', [4])
    add(2, '管理本机听写录音与转写结果', V('kn', '_n', 'vn'),
        'Show recent local recordings even when dictation is unavailable if records remain. Support recording query selection, show-all URL cleanup and source copy/download/delete/retranscribe actions; disable parallel row actions and clear pending in finally.',
        'Retranscription failure gets dedicated toast; other action failures are logged. Audio playback, export, deletion, transcription and storage internals remain delegated.',
        'Inspect recent/selected/all records, recording query parameter and action receiver choice.',
        'Reject each action or lose dictation capability with retained items; verify pending release and differentiated feedback.',
        'Verify local recording ownership, playback/export/storage and transcription service using synthetic media only; no new model task is authorized.', [5])
    add(2, '编辑本地听写词典', V('jn', 'Mn', 'In', 'Fn'),
        'Use local dictionary fallback when account identity is unavailable and global dictation supported. Add/edit/remove draft rows; blur/remove saves trimmed nonempty phrases, Enter inserts a row and suppresses the immediate blur save.',
        'Trim/filter does not deduplicate phrases. Preference write failure is not converted to successful reset; retain pending draft and source behavior.',
        'Inspect add/Enter/blur/remove, trimming, empty filtering and duplicate preservation.',
        'Reject save or switch account-backed view; verify draft/reset only follows successful write.',
        'Verify local dictionary storage and recognition consumer without treating it as the account dictionary service.', [5])
    add(2, '打开账户语音词典编辑器', V('dn', 'fn'),
        'When accountId/userId exists, key the dictionary surface by both values and pass them to the account dictionary editor; otherwise use the provided local fallback.',
        'The editor and account vocabulary storage are a separately assigned boundary; this entry contract does not establish edit/delete/save semantics.',
        'Inspect account/user keyed remount, Manage opening and local fallback.',
        'Change identity or close editor; verify no reused draft from the prior identity.',
        'Verify delegated vocabulary editor, account service and consumer separately from the local preference dictionary.', [5])
    return result


def configuration():
    return dict(
        number=8, work='settings-history-batch08-work', previousScope=14, previousCoverage=5,
        expectedState='2026-10-24T09:21:00.074538+00:00',
        selections=['browser-use', 'chronicle', 'voice'],
        scriptFiles=['settings_history_batch08_specs.py', 'probe_settings_history_batch08.cjs'],
        entries=[('browser-use', 'Browser use', 'T26'), ('chronicle', 'Chronicle', 'T27'), ('voice', 'Voice', 'T28')],
        mechanisms=[
            ('Host/capability browser policy and plugin entry', 'Retain host-specific availability, loading/redirect and preference keys. Imported plugin card/install/try-in-chat are delegated shared-manager consumers; prefill is not model submission.', [('browser-use', 'da'), ('browser-use', 'fa'), ('browser-use', 'sa')]),
            ('Native browser ownership, history and download adapters', 'Native partitions/pages, mount ID lifecycle and history/download receivers remain explicit runtime interfaces.', [('browser-use', 'Ai'), ('browser-use', 'Gr'), ('browser-use', 'ci'), ('browser-use', 'Qr')]),
            ('Chronicle host enablement and recorder state', 'Separate host config/memory prerequisite, permission onboarding, effective enabled state and recorder activation/pause state.', [('chronicle', 'En'), ('chronicle', 'Dn'), ('chronicle', 'Sn')]),
            ('Chronicle history, permission and clear requests', 'Separate recorded activity from browser/audio history; preserve application policy and interval/range confirmation. Ask-about-history only prefills existing chat flow.', [('chronicle', 'on'), ('chronicle', 'kn'), ('chronicle', 'pn'), ('chronicle', 'un')]),
            ('Voice capability, media permission and preference services', 'Distinguish device/global preferences, account language/compatible voices, command keybindings and OS/media permission adapters.', [('voice', 'Cn'), ('voice', 'wn'), ('voice', 'Qt'), ('voice', 'Ln'), ('voice', 'assignment-ln')]),
            ('Local recordings and two dictionary storage paths', 'Preserve local recording actions, draft normalization and identity-keyed account dictionary fallback as separate receiver contracts.', [('voice', '_n'), ('voice', 'Mn'), ('voice', 'dn')])],
        gaps=[
            ['Plugin card/control and try-in-chat, site-permission/WebMCP rows, native pages/dialogs, source query helpers, URL opener and preference writer remain delegated interfaces.', 'Actual runtime partition/privileged page support, browser history/download semantics, host/mode and persistent consumers.'],
            ['Chronicle service queries, memory-enable orchestration, permissions dialog/normalization, recorder/native and derived-memory deletion remain assigned integration boundaries.', 'Actual host/OS permission, recorder state, policy enforcement, activity query/deletion and durable state.'],
            ['Compatible voice picker/service, recognition/media/audio/recording helpers, account vocabulary editor and OS shortcuts remain assigned integration boundaries.', 'Actual access/mode, OS permission, account identity transitions, media/recording ownership, service behavior and persistence.']],
        modules=['browser/settings', 'chronicle', 'voice/settings'],
        consumers=[['host/browser-runtime', 'browser/history', 'browser/downloads', 'settings/preferences', 'extensions/plugin-manager'], ['host/chronicle', 'memory/settings', 'history/activity', 'settings/preferences'], ['host/media-permissions', 'backend-adapter/voice', 'commands/keybindings', 'voice/recordings', 'voice/dictionary']],
        dependencies=[['React/query/UI packages', 'browser runtime/privileged pages and history/download APIs', 'plugin manager and preferences adapters'], ['React/query/UI packages', 'chronicle/native recorder and permission APIs', 'memory/config/history APIs'], ['React/query/UI/schema packages', 'OS/media/shortcut and recording adapters', 'account voice/vocabulary APIs']],
        decisions=[
            'Keep browser preference/history/download presentation in renderer, assign privileged settings pages, partition/mount lifecycle and actual browser operations to a runtime adapter; reuse plugin manager only through its existing contract.',
            'Separate Computer history enablement/permissions/recorder lifecycle from recorded-activity browsing/deletion and derived-memory service effects; browser and audio history remain independent modules.',
            'Separate local device/preferences, account voice services, OS command/shortcut registration, local media records and account/local dictionary stores; preserve capability/identity gates.'],
        title='浏览器、Computer history 与语音：模块和运行时边界',
        modeReason='Browser use/Chronicle have codexOrWorkLocal access families and Voice has codex access family. Source access-family evidence is retained, but actual mount/account/flag/shared-consumer closure is not inferred; localized ChatGPT wording and headers do not prove exclusion.',
        firstParty=['host/capability routing and preference policy', 'history/download selection and reconciliation', 'native page ownership/navigation lifecycle', 'Chronicle onboarding/recorder/history/clear-request policy', 'voice media cleanup and capability/identity gates', 'dictionary draft and local/account fallback policy'],
        externalize=['React/query/UI/schema packages', 'native browser/Chronicle/media/OS shortcut runtime adapters', 'history/download/recording storage adapters', 'account language/voice/vocabulary and memory APIs', 'existing plugin manager'],
        probeDescription='仅用合成记录、设备、权限回调、query与写入替身核对历史身份/下载合并、原生设置导航、清理请求guard、麦克风track释放和词典/账户语言保存；未读取真实历史、调用麦克风、录制屏幕、播放音频、访问服务或提交模型任务',
        modeSummary='保留两个codexOrWorkLocal入口与一个codex入口的静态访问证据，实际模式闭包仍待核对，确认排除为0。第三方实现通过既有依赖清单和服务/运行时适配引入；第一方保留门控、生命周期、请求与展示策略。',
        boundarySummary='浏览器原生页面/partition、Chronicle录制与权限、媒体/音频/快捷键、词典及账户服务均已归属到对应适配任务；委托内部实现、实际运行、模式与持久化留作局部验收。',
        reportFacts='未新增真实服务、浏览器/活动/录音读取、媒体调用或模型请求。源码明确浏览器原生页面生命周期、URL/活动/音频三种历史的独立接收器、Chronicle配置与录制状态差异，以及本地/账户语音配置和词典边界。',
        summaryPoints=[
            'Browser use把网页/本地URL打开偏好、地址栏/批注规则、数据清理与历史/下载分开；内嵌Chrome设置依赖特权页面、partition和配对mountId，应接运行时适配，不能按普通Web页面替代。插件管理与Try in chat作为既有扩展/会话流程的委托入口保留。',
            '浏览历史行身份含URL、时间和agent标记，删除身份按URL与本地日去重；下载合并只补入匹配搜索的进行中条目，并保留历史fileExists。清下载历史不能直接声称删除文件。',
            'Chronicle区分配置启用、权限/记忆前置条件、activationState和recorderState；应用/网站范围、活动浏览和区间/时间范围删除分别接服务。删除文案包含派生记忆，实际服务效果需单独验收。',
            'Voice区分系统默认/具体麦克风、账户语言与实时声音、命令快捷键与听写快捷键、本机录音和词典。账户词典按accountId:userId重挂载，本地词典只trim并过滤空项，不推断去重；媒体权限和track清理使用合成替身验证。'],
        nextQualification='Native browser/Chronicle/media/OS shortcut and account/recording implementations remain local integration tasks; settled page selections and helper probes are not global blockers. No model authorization remains.')
