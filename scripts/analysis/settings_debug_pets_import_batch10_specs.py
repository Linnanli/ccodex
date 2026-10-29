"""Settings entry ownership; shared keyboard/MCP/plugin goals keep their owners."""


def specifications():
    result = []
    def add(page, name, units, effect, failure, behavior, negative, receiver, support):
        result.append(dict(pageIndex=page, name=name, units=units, effect=effect,
                           failureAndCancellation=failure, acceptance=[behavior, negative, receiver], support=support))
    D = lambda *names: [('debug', n) for n in names]
    P = lambda *names: [('pets', n) for n in names]
    I = lambda *names: [('import', n) for n in names]
    add(0, '启用受信任的 Chrome 诊断页面', D('P', 'F'),
        'Only show the chrome diagnostics preference when allowDebugMenu(prod) permits it; write debugChromePagesEnabled through the preference adapter.',
        'The preference description permits trusted chrome diagnostics while chrome-untrusted stays blocked. The control alone proves neither URL policy enforcement nor runtime page availability.',
        'Inspect root gate, exact preference identity and boolean callback payload.',
        'Deny the debug-menu gate or reject preference persistence; do not report a browser capability change.',
        'Verify trusted URL classifier, durable preference and runtime opener; reuse the existing browser runtime boundary.', [0])
    add(0, '切换 GPU 合成诊断选项', D('P', 'I'),
        'Render six parameterized switches: disableScrollFadeMask, disableScrollFadeMaskAnimation, disableBackdropBlur, disableCssMotion, disableSquircles, forceOpaqueRendererBackground. Dispatch the selected key/value to the GPU debug setter.',
        'The group is constructed independently of the chrome-pages gate; its stated effects are active only under the separate debug gate. A rendered switch does not prove CSS/native composition changed.',
        'Inspect all six keys, current values and exact setter dispatch.',
        'Vary the chrome-pages gate and effective GPU gate; distinguish control visibility, preference and renderer effects.',
        'Verify imported GPU state/setter and actual styles/compositor integration, including immediate apply and debug-gate disable.', [0])
    add(1, '显示或收起 Mini 浮层', P('hr', 'ur', 'fr', 'On'),
        'The feature flag chooses the modern or legacy collection. Show/Hide dispatches avatar-overlay-open and records the current open/closed action; the settings preview remains an inert illustration.',
        'Dispatch is a host request, not proof the floating window opened. Modern visibility preference, petVisible and overlay-open state are separate.',
        'Inspect both layouts and Show/Hide event identity with selected-avatar fallback.',
        'Vary open state, layout flag and unavailable host receiver; do not infer a successful window transition from analytics.',
        'Verify overlay host lifecycle, actual open state and focus; reuse command infrastructure for the shortcut consumer.', [1])
    add(1, '设置 Mini 常驻或按需显示', P('ur'),
        'Under the source flag/host predicate, select always-visible or on-demand via petVisibility.schema.parse and the preference writer; on-demand help reflects the configured shortcut.',
        'A failed write displays the dedicated save-error toast; invalid input must fail schema parsing. This preference is not petVisible or current window-open state.',
        'Inspect allowed values, schema call, preference key and shortcut-dependent description.',
        'Reject save, provide invalid value or disable the source gate; preserve error and visibility behavior.',
        'Verify durable preference and floating-window click-away/menu/shortcut consumers.', [1])
    add(1, '选择宠物或隐藏宠物外观', P('ir', 'On', 'ar', 'or', 'jn'),
        'Modern selection writes selected avatar, enables petVisible when needed, and is a no-op for the already visible selection. None clears petVisible without deleting the avatar. Legacy selection keeps its distinct callback.',
        'Do not equate selecting None with hiding the Mini window, deleting custom files or resetting the selected ID.',
        'Inspect selected-visible, selected-hidden, different-avatar and None branches in both layouts.',
        'Fail preference/selection receiver or vary legacy layout; retain actual source ordering without invented rollback.',
        'Verify selected-avatar resolver, persistence and overlay artwork consumer using owned synthetic avatars.', [1, 2])
    add(1, '调整并恢复宠物尺寸', P('ir', 'On', 'Qn'),
        'The range control spans 80..224, writes Number(input.value), and Reset writes petSize.default; modern preview/customize dialog reuses that size control and respects reduced motion.',
        'Reset is disabled at the default. Numeric conversion is not independent schema validation; the inert preview does not start voice or show real notifications.',
        'Inspect range bounds, numeric dispatch, default reset and preview scale/layout.',
        'Use unchanged/default values and invalid synthetic event values; distinguish browser input constraint from storage validation.',
        'Verify preference schema, actual pet layout and rendering adapter under real scale/reduced-motion conditions.', [1, 2])
    add(1, '查看和刷新自定义宠物资源', P('Vn', 'ir', 'On', 'Cn'),
        'Display custom pet loading/error/options; Refresh invalidates the three source query families. Under the legacy/local directory condition, Open folder requests fileManager with cwd null and workspace mode.',
        'Missing directory/cloud feature condition hides the folder surface. An unsuccessful open result or rejected request shows an error; refresh does not prove files were repaired.',
        'Inspect query invalidations, catalog states and folder receiver payload.',
        'Return unavailable directory, load error and failed folder request; preserve fallback and feedback.',
        'Verify local/cloud avatar catalog, manifest/rendering adapter and file-manager receiver without reading personal assets.', [2])
    add(1, '准备宠物创建流程', P('Vn', 'Pn', 'In', 'Hn'),
        'Resolve an eligible work-pets plugin or install/enable the recommended hatch-pet skill, refresh skills and build a composer prefill. Plugin installation/enabling, default-host new conversation and optional cloud callback retain separate branches.',
        'Blocked plugin, missing cloud account, identity change, install/enable failure and exceptions do not continue the flow; finally releases creation pending. This settings action prepares a prompt and does not submit it to a model.',
        'Inspect plugin versus skill preparation, required enablement, prefill and account checks.',
        'Inject blocked/missing/failed setup and account changes; verify no false creation success or automatic model submission.',
        'Reuse plugin/skill managers and composer interfaces; validate actual pet generation/installation separately with explicit model authorization.', [2])
    add(1, '准备已有自定义宠物的升级流程', P('Vn', 'Fn', 'In', 'or', 'jn'),
        'Offer Update only with an upgrade directory/callback under the source flag; prepare hatch-pet, normalize CR/LF in the display name, and prefill an upgrade prompt using the existing directory reference.',
        'Preparation failure shows the upgrade error. The callback does not upgrade files or submit the prepared prompt by itself.',
        'Inspect update eligibility, normalized name/directory reference and skill-enable requirement.',
        'Remove upgrade directory or fail skill preparation; verify no prefill on failure and no claimed asset change.',
        'Verify skill/composer and pet asset format upgrade using owned fixtures in a separately authorized execution.', [2])
    add(2, '检测并进入外部 AI 应用导入流程', I('$n', 'fn'),
        'Detect providers/items with local host, provider/session limits and applicable workspace roots; show loading/error/unsupported-project/running states. Import opens the shared selection controller with preselected provider, source settings and restore-focus callback.',
        'A running import for this host takes precedence. No compatible rows means no import action; retry/check-again only reruns detection. Actual copy/overwrite/cancellation is delegated to the import controller.',
        'Inspect provider-specific entry payload, workspace applicability, running/loading/error precedence and focus restoration.',
        'Use no items, unsupported projects, detection failure and another host running; verify no fabricated import results.',
        'Recover shared detector/controller and native importer/session/config adapters; use synthetic fixtures before any real filesystem import.', [3])
    add(2, '启用或暂停后续自动同步', I('Jn'),
        'Write syncEnabled separately from syncItemTypes. The switch is disabled by source eligibility; Customize additionally requires a version-1 sync state with provider IDs. Paused sync retains content choices.',
        'Toggle failure sets the local save-error state. Enabling sync does not prove an import executed or remove previously imported content.',
        'Inspect capability/initial-import conditions and exact boolean preference dispatch.',
        'Reject save or remove usable sync state; preserve disabled/error and saved-category behavior.',
        'Verify sync scheduler, durable preferences and provider/workspace scope; imported content effects require importer acceptance.', [3])
    add(2, '自定义自动同步的内容类别', I('Jn', 'Un', 'assignment-zn', 'assignment-Bn'),
        'Edit all/current/future category preferences across sessions, instructions, config, skills, plugins, MCP, subagents, hooks, commands and memory. Require at least one enabled category; category help preserves bundled plugin content and command-to-skill conversion.',
        'Pending save blocks controls/submit; failed save preserves the dialog and error. Save applies to future syncs, not deletion of prior imported content.',
        'Inspect all-versus-explicit category mappings, future category toggle and source category eligibility.',
        'Unselect every category, reject save and cancel; verify validation, pending release and draft handling.',
        'Verify shared category resolver, preference storage and actual importer filtering, including Cowork config bundled tools.', [3])
    add(2, '查看导入记录并打开导入目标', I('$n', 'wn', 'Tn', 'En', 'vn', 'Nn', 'yn', 'bn', 'xn'),
        'Merge this host running import with histories, show initial/latest versus View more, expand category results and preserve imported/failed/needs-review/authentication summaries. Navigate successful sessions, skills/commands, MCP, plugin or Hooks targets using typed routes.',
        'History failure supports retry; no recorded results remains distinct from success. Failures or missing/unsupported targets must not create navigation; pending records are not completed imports.',
        'Inspect history expansion/counts, warning precedence and encoded successful-target routes.',
        'Use failed/missing target, history error and running import; verify safe fallback titles and no false completion.',
        'Verify history store, target/thread lookup and existing manager routes; reuse MCP/plugin/skill/hook modules for their actual operations.', [3, 4])
    add(2, '完成导入后的应用连接设置', I('$n', 'rr') + [('import-setup', 'oe'), ('import-setup', 'U'), ('import-actions', 'We')],
        'Derive Needs attention from imported connector/plugin/MCP/hook state; classify already accessible apps versus installable matching plugins, deduplicate plugins and open the shared account connection dialog.',
        'Readiness/loading/error and retry remain per source family. Closing the dialog clears the connecting app; OAuth start is not connection success. Existing MCP authentication and plugin installation are shared consumers, not new feature owners.',
        'Inspect app/plugin classification, accessible/installed cases, tabs, setup-start and connection completion refresh.',
        'Fail discovery/refresh or close OAuth; preserve pending/error state without claiming connected or imported.',
        'Verify connection/OAuth, marketplace/runtime app catalog and imported state adapters with owned fixtures.', [4, 5])
    return result


def configuration():
    return dict(
        number=10, work='settings-debug-pets-import-batch10-work', previousScope=16, previousCoverage=7,
        expectedState='2026-10-24T10:29:24.573902+00:00',
        selections=['debug', 'pets', 'import', 'import-actions', 'import-setup'],
        scriptFiles=['settings_debug_pets_import_batch10_specs.py', 'probe_settings_debug_pets_import_batch10.cjs'],
        priorProbeAttempts=[dict(observations='probe-attempt-01.json', probeScript='probe-attempt-01.cjs',
                                 disposition='21 pass; one fixture traversal failure: row.control omitted; target source unchanged.')],
        entries=[('debug', 'Debug', 'T31'), ('pets', 'Pets', 'T32'), ('import', 'Import', 'T33')],
        sharedGoalConsumers=[
            dict(pageIndex=1, featureIds=['FSC-0068'], relation='Mini shortcut is an additional consumer of command-keybinding editing; keep the existing keyboard feature owner.', units=[('pets', 'dr')], acceptance='Verify openAvatarOverlay command metadata/gates, set-codex-command-keybinding payload and keymap invalidation; no new feature root.'),
            dict(pageIndex=2, featureIds=['FSC-0119'], relation='Imported MCP authentication reuses mcpServer/oauth/login and external URL adapters; import-specific in-flight URL map and host event guards remain here.', units=[('import', 'rr'), ('import-actions', 'We')], acceptance='Verify per-server duplicate suppression, saved URL reopening, failure retry and same-host completion invalidation; whole entry equivalence remains unproven.'),
            dict(pageIndex=2, featureIds=['FSC-0124'], relation='Imported plugin installation delegates to the existing plugin manager; preserve import source/surface and host/plugin pending suppression.', units=[('import', 'rr'), ('import-actions', 'We')], acceptance='Verify host/plugin duplicate suppression, success-marked pending app, rejection cleanup and actual manager policy; no additional installation feature owner.')],
        mechanisms=[
            ('Debug preference and effective renderer policy', 'Separate chrome-page gate, GPU control construction, stored diagnostic state and actual CSS/native effects.', [('debug', 'P'), ('debug', 'F'), ('debug', 'I')]),
            ('Mini preference, host overlay and command consumers', 'Visibility mode, petVisible, selected ID, size and current overlay state are independent; keybinding uses existing command owner.', [('pets', 'hr'), ('pets', 'ur'), ('pets', 'fr'), ('pets', 'dr'), ('pets', 'ir')]),
            ('Pet catalog and plugin/skill preparation', 'Retain manifest/catalog and directory interfaces; plugin/skill install/enable and prompt preparation do not themselves submit a model task.', [('pets', 'Vn'), ('pets', 'In'), ('pets', 'Pn'), ('pets', 'Fn'), ('pets', 'Cn')]),
            ('Import detection, history and automatic sync policy', 'Keep local host/workspace/provider/session inputs, progress/history projection and preference/draft categories separate from importer execution.', [('import', '$n'), ('import', 'fn'), ('import', 'Jn'), ('import', 'Un'), ('import', 'En')]),
            ('Imported app/plugin readiness classification', 'Preserve partial-query/error/ready states, accessible app matching and plugin deduplication; targeted catalog merges preserve installed metadata.', [('import-setup', 'oe'), ('import-setup', 'U'), ('import-setup', 'W'), ('import-setup', 'assignment-Q'), ('import-setup', 'assignment-J')]),
            ('Shared import setup OAuth/install/navigation consumers', 'Per-server OAuth requests and host completion events, retry families, plugin status and route guards stay in import presentation; existing managers own effects.', [('import-actions', 'We'), ('import', 'rr'), ('import', 'xn')])],
        gaps=[
            ['GPU imported state/setter/style consumer, preferences, trusted URL enforcement and actual native/compositor behavior remain integration boundaries.', 'Actual debug gates, preference durability and runtime diagnostics availability.'],
            ['Avatar catalog/selected resolver, preferences, overlay runtime, command bindings, plugin/skill managers and rendering remain assigned interfaces.', 'Actual host/flags, local/cloud catalog, window/focus behavior, asset validity and separately authorized generation/upgrade.'],
            ['Detector/import selection controller, native filesystem/session/config importer, sync resolver/scheduler, histories, app/OAuth/plugin/MCP/target managers remain assigned interfaces.', 'Actual Codex/shared mount, local workspace/provider access, import overwrite/cancel/rollback and durable sync/setup/history behavior.']],
        modules=['diagnostics/settings', 'pets/settings', 'imports/settings'],
        consumers=[['settings/preferences', 'diagnostics/renderer', 'host/browser-runtime'], ['pets/catalog', 'pets/overlay', 'settings/preferences', 'commands/keybindings', 'extensions/plugin-manager', 'skills/manager', 'tasks/composer'], ['imports/detector', 'imports/controller', 'imports/sync', 'imports/history', 'connections/apps', 'extensions/plugin-manager', 'mcp/settings', 'hooks/settings']],
        dependencies=[['React/UI packages', 'preference/debug renderer adapters', 'trusted browser diagnostics runtime'], ['React/UI/motion/query packages', 'avatar rendering/catalog and overlay runtime', 'preference/command/plugin/skill/composer adapters'], ['React/UI/query/lodash packages', 'native importer and sync/history adapters', 'account/OAuth/plugin/MCP/hook/route services']],
        decisions=[
            'Keep diagnostic control definitions in renderer, route stored preference and effective CSS/GPU policy through explicit adapters, and reuse browser runtime capability constraints.',
            'Separate pet preferences/catalog, floating overlay, renderer preview and creation/upgrade preparation; reuse keybindings and plugin/skill managers, with generation as separately authorized task execution.',
            'Separate detection/import controller, automatic sync, result history and post-import setup; reuse existing OAuth/plugin/MCP/skill/hook owners rather than creating duplicate implementations.'],
        title='诊断、Pets 与 Import：操作归属及共享模块复用',
        modeReason='Import retains codexOrWorkLocal access. Debug and Pets have null access-family metadata plus local flags/host predicates; actual selected product mode remains unresolved. ChatGPT labels do not establish whole-page exclusion.',
        firstParty=['diagnostic control/key/gate policy', 'pet selection/visibility/preview and preparation orchestration', 'import host/provider/workspace entry policy', 'automatic sync draft validation', 'history and post-import setup classification', 'OAuth/install duplicate and host guards'],
        externalize=['React/UI/motion/query/lodash packages', 'debug/browser/overlay runtime adapters', 'avatar catalog/rendering', 'native importer, preference/sync/history stores', 'existing command/plugin/skill/OAuth/MCP/hook/composer managers'],
        probeDescription='仅执行冻结控制回调、合成插件/应用分类、技能准备、导入偏好守卫与 OAuth 请求替身；未安装插件/技能、打开浏览器、读取个人资源、执行导入或提交模型任务',
        modeSummary='三页继续保留待模式核对；快捷键、MCP认证和插件安装登记为已有功能的新消费者，未重复增加相应功能定义。第三方包通过既有依赖清单外置，第一方策略与协调保留。',
        boundarySummary='实际渲染/浮层/资源、导入执行与同步、账户连接和共享管理器均有明确接收边界；局部隔离通过不代表运行时、导入或产品验收。',
        reportFacts='明确六项GPU诊断键、Mini三种可见状态的区别、宠物创建/升级仅准备提示，以及导入检测/同步/历史/后置设置的不同所有者；三项既有功能按消费者关联。',
        summaryPoints=[
            'Debug的Chrome诊断行受allowDebugMenu控制，GPU组仍被构造；实际GPU效果另受debug gate控制。偏好写入、URL信任策略和底层能力分别验收。',
            'Pets区分petVisibility、petVisible和overlay-open；None只隐藏宠物外观。创建/升级先安装启用必要技能或插件，再准备提示；不能计为自动模型提交或资源生成。',
            'Import区分检测与选择入口、实际导入控制器、自动同步偏好、历史结果和导入后连接。暂停同步保留类别，修改类别仅影响后续同步。',
            'Mini快捷键复用FSC-0068，导入后的MCP认证复用FSC-0119，插件安装复用FSC-0124；各入口仍保留自己的失败、重试、账户/宿主和防重条件。'],
        nextQualification='Continue remaining containers without reopening these source selections. Effective debug/rendering/overlay, native import/sync/history and shared service managers retain local integration acceptance. No model authorization remains.')
