"""Final three saved settings selections; imported implementations remain boundaries."""


def specifications():
    rows = []

    def add(page, name, names, effect, negative, receiver, support):
        folder = ['cloud-environments', 'personalization', 'codex-micro'][page]
        rows.append(dict(pageIndex=page, name=name, units=[(folder, n) for n in names],
            effect=effect, failureAndCancellation=negative,
            acceptance=[effect, negative, receiver], support=support))

    add(0, '浏览、搜索和分页选择旧版云环境', ['Ut', 'Lt', 'Rt', 'zt'],
        'The root renders the list. Trim search, defer it200ms, cap input at128, use the imported query normalizer and sorter, flatten returned pages and navigate a selected environment to its detail route. Row Edit requires can_write===true.',
        'Keep initial loading, searching, empty list, no search results, initial-query error/retry and next-page error/retry distinct. Fetch more only under the saved pagination conditions; actual sorting and normalization remain imported contracts.',
        'Verify the actual environment-list query, account/workspace scope, cursor semantics, normalizer/sorter and row availability. Selection is navigation and does not execute a task.', [0])
    add(0, '查看云环境详情与配置摘要', ['Ut', 'Gt', 'vt', 'xt', 'yt', 'bt'],
        'Fetch the selected ID and show repositories, machine, creator, creation date, sharing/network labels and configured-script indicators. Show environment-variable names and secret names; a nonempty secrets object takes precedence over secrets_with_domains, whose null names are skipped.',
        'Pending and error/retry are distinct; unknown sharing/network values do not acquire invented labels. Edit/delete/reset eligibility follows separate strict permissions and cache conditions. The summary does not expose secret values.',
        'Verify authoritative detail data and permissions, repository/date formatting and redaction. Loaded metadata does not prove a usable execution environment.', [0, 2])
    add(0, '创建旧版云环境并进入保存结果', ['Ut'],
        'Only the single new path segment opens the imported editor with environment:null. Cancel returns to the root; onSaved(id) navigates to that environment detail. Keep editor validation, payload and service ownership in the delegated cloud-environment-editor interface.',
        'Invalid multi-segment/new routes redirect to the root. Closing the wrapper alone proves neither request abort nor successful creation; editor errors and duplicate-submit behavior remain delegated.',
        'Resolve the imported editor form, actual create receiver, authorization, validation and durable environment readback before implementing or accepting creation.', [0, 1])
    add(0, '编辑有写权限的旧版云环境', ['Ut', 'Kt'],
        'For id/edit, fetch the selected ID before mounting the imported editor keyed by returned data.id. Mount only when permissions.can_write===true. Pass the loaded environment; Cancel and Saved return to detail.',
        'Query error redirects to detail, pending renders loading and breadcrumb, and absent/false/truthy nonboolean write permission redirects to detail. Do not infer edit permission from delete permission or a loaded environment.',
        'Verify editor patch/replace semantics, validation and actual write authorization, stale-data handling and readback. Shared create/edit UI is a first-party delegated family, not generated third-party code.', [0, 1])
    add(0, '确认删除旧版云环境', ['Gt', 'wt'],
        'Expose Delete under can_delete===true, open its confirmation and submit the imported delete mutation for the selected ID. Success shows feedback and navigates to the root; the dialog explains that existing chats remain while follow-ups with this environment become unavailable.',
        'Pending disables Cancel and marks the submit button loading. The form callback itself only prevents default and confirms; it contains no independent in-flight guard. Failure shows deletion feedback, and closing a dialog is not transport cancellation.',
        'Verify the delete receiver, authorization, duplicate-submit protection, list invalidation and actual retained-chat/follow-up behavior with owned service data.', [2])
    add(0, '确认重置旧版云环境的容器缓存', ['Gt', 'Tt'],
        'Expose cache reset only with can_write===true and post_setup_cache_enabled defaulting to true. Submit the imported cache-reset mutation after confirmation; success closes the dialog and gives feedback. The confirmation states that all users of the environment are affected.',
        'Explicitly disabled cache or lack of write permission hides the action. Pending/loading and form callback qualification match the delete dialog; reset failure has separate feedback and does not become a successful cache invalidation.',
        'Verify cache scope, authoritative reset receiver, pending/duplicate behavior and the next container creation; a success toast alone is insufficient.', [2])
    add(0, '把旧版云环境复制为新云环境草稿并启动引导', ['Ot', 'Pt'],
        'Require gate375130565, native environmentConfigs and the imported migration predicate. Build a new onboarding draft from legacy ID, label, repository names with ID fallback and model settings; flush its store selection before starting onboarding navigation.',
        'Disable migration until model settings and both prerequisite state values are loaded. The callback creates/selects a draft through delegated helpers; it does not prove provisioning, legacy deletion or successful server migration.',
        'Verify migration eligibility, initializer/selection/navigation helpers, model settings and final provisioning. Keep old environments available as described for Code Review and integrations.', [3])

    add(1, '切换所选主机的 Codex 记忆', ['ka', 'Xr'],
        'Resolve the selected local/remote host, configuration and memory feature. Pass featureWrite plus paired memories.generate_memories/use_memories config edits to the imported orchestration helper; disabling on an eligible local host also supplies the Chronicle-disable operation.',
        'Keep loading/error/unavailable and scoped retries. Imported orchestration owns sequencing, rollback and logging; the callback alone does not prove atomic writes or native Chronicle availability.',
        'Verify feature/config receivers, helper transaction behavior, local-versus-remote host binding and actual memory generation/use after reload.', [4])
    add(1, '允许或跳过工具辅助会话的 Codex 记忆', ['Xr'],
        'Invert the visible allow checkbox to disableOnExternalContext. Write memories.disable_on_external_context and clear legacy memories.no_memories_if_mcp_or_web_search with null through the imported config writer/orchestrator.',
        'Keep current-host configuration and per-write error feedback; toggling the setting does not erase existing memories or establish immediate tool-context behavior.',
        'Verify config precedence, legacy migration, effective memory consumers and persisted values for the selected host.', [4])
    add(1, '确认删除所选主机的 Codex 记忆', ['Xr'],
        'Confirm reset. On an eligible local host with native Chronicle, await deletion of all Chronicle history first; then call the selected host memory/reset request. Success closes the confirmation and shows Codex-memory feedback.',
        'A failed prerequisite prevents memory/reset; failures retain error feedback. Remote/unavailable Chronicle skips that local prerequisite. Dialog dismissal and request cancellation are different operations.',
        'Verify Chronicle scope, selected-host backend reset, partial failure and durable cleared state. Do not treat a UI close as proof of memory deletion.', [4])
    add(1, '编辑所选主机的 AGENTS.md 或旧版本地指令', ['ka', 'wi', 'Ti', '_i'],
        'Select the host and unified-instructions mode, query its instructions and preserve override status. Save codex-agents-md-save with captured hostId and contents; reconcile the submitted host cache using returned path and submitted contents, then close only through successful editor save.',
        'Require loaded contents, a changed draft and no active save. Error without loaded data has retry; stale loaded text can remain editable. Back prompts when dirty, Cancel discards directly, and saving disables both. Cmd/Ctrl+Enter excludes IME; the shared save handler rechecks eligibility.',
        'Verify actual host file location/override precedence, save receiver, concurrent changes, rich-text/source view and durable readback. Host and account instruction stores remain distinct.', [5])
    add(1, '编辑账户级 Codex 自定义指令', ['ka', 'Si', 'Ci', 'Ti', '_i'],
        'Use the account Codex instruction entry and cloud-preferences query; default custom_instructions to empty only after data is loaded. Save the custom_instructions patch through the imported cloud preference mutation and shared guarded editor.',
        'No data is not an empty editable baseline. Preserve unsaved navigation, save error and account-keyed remount conditions; local AGENTS.md is not overwritten by this adapter.',
        'Verify cloud preference query/mutation identity, captured cache context, actual Codex consumer and persistence across account changes.', [5, 6])
    add(1, '打开账户自定义规则与权限编辑页', ['Br', 'Vr', 'Ur', 'Gr', 'assignment-Jr', 'Hr'],
        'Require the saved feature flag, ChatGPT authentication family, user/account identity and account tbo availability. The overview queries rule counts; route rules=custom removes instructions and supports settings hashes. Dirty navigation is queued before mounting the lazy UserRulesPage keyed by account/user.',
        'Preserve account loading/error/retry, unavailable/Back and Suspense/gate fallbacks. Only the entry and delegated page contract are covered; no rule CRUD or enforcement is claimed.',
        'Resolve the lazy rules page operations, provider and actual permission enforcement before accepting this retained family. Authentication family alone is not proof of product-mode exclusivity.', [5, 8])
    add(1, '打开所选主机的写作风格设置', ['ka', 'Rr', 'assignment-Ga'],
        'Mount the lazy WritingStyleSettings only under the saved access=allowed and selected-host eligibility conditions. Preserve its placement in Personalization and the independent host selection.',
        'Unavailable access or host conditions suppress the entry. Lazy import presence establishes a delegate, not its editing, storage or collection behavior.',
        'Resolve writing-style controls, Chronicle/service prerequisites, selected-host consumers and durable effects; retain mode unknown until consumers are checked.', [8])
    add(1, '编辑账户资料与 ChatGPT 自定义指令草稿', ['ka', 'Ma', 'Ui', 'qi', 'Ji', '_i'],
        'Read account/user system-message context, maintain a sparse changed-field draft and PATCH user_system_messages with the captured account header. Apply1500-character field limits and the separately clamped custom-instruction limit. Success installs the server response, clears draft and closes the active instruction editor.',
        'No changes, pending state, missing draft or an over-limit field prevents Save. Moderated-field errors stay field-specific; other failures retain draft and feedback. Keyboard save excludes IME and the local AGENTS editor.',
        'Verify system-message service schema, actual catalog limits, account/user switching, nickname/profile and instruction consumers; retain these discovered operations pending branch-mode proof.', [5, 6])
    add(1, '切换账户个性风格及特征强度', ['Ma'],
        'Load personality type and trait catalogs. Selection sends enabled:true plus type or the changed trait, preserving other traits; only less/more remain special, other choices normalize to default. Optimistically merge into the captured system-message query and replace with the server response on success.',
        'Cancel the query before snapshot/optimistic write; failed mutation restores its captured prior cache and shows feedback. Keep shared mutation scope, identity and availability guards; optimistic display is not a committed service result.',
        'Verify serialized service writes, rollback interaction, catalog eligibility and account/user cache ownership under rapid changes.', [6])
    add(1, '切换账户记忆、历史引用及相关搜索偏好', ['Ma', 'la'],
        'Distinguish M3M from legacy Sunshine/Moonshine and parent/workspace/account locks. Write the primary preference; disabling memory also disables memory-in-search when necessary, while the legacy path synchronizes defined history-reference state. Run dependent updates with allSettled and invalidate captured memory/summary caches.',
        'Unavailable identity, loading, query errors and restricted access do not become false editable defaults. A dependent failure has feedback; invalidate an active snapshot only while account/user still match. Preference disable does not itself delete historical data.',
        'Verify primary/dependent receiver semantics, all partial failures, actual history/search consumers and memory persistence for the correct account.', [6])
    add(1, '打开已保存记忆或关于自己的摘要管理器', ['Ma'],
        'Resolve modal=memories or about_you=summary from normal/hash navigation under M3M/legacy/opt-out eligibility. Clean the alternate query parameters and transient source/contextualHints while preserving other location state; mount the corresponding imported manager.',
        'Navigation completion is checked before returning a destination. Keep unavailable and opt-out conditions; entry presence does not prove delegated memory CRUD or summary generation.',
        'Resolve saved-memories and about-you manager operations and services, account binding, close/return routes and actual read/write behavior.', [6, 8])
    add(1, '上传或替换账户人像与全身参考照片', ['Sa', 'Ca'],
        'Under the photo/account and VTO gates, query image tags by account and kind. Accept the first selected file, clear the input and call the imported uploader with accountId, imageFile, kind and current imageTagId; successful upload closes the editor.',
        'Preserve face versus full-body visibility, loading/error/pending controls and same-account feedback. File accept hints are not actual validation; validation, upload transport and file lifecycle remain delegated.',
        'Verify uploader validation/storage, consent/eligibility, tag selection, account switching and authoritative refreshed image state using separately authorized owned images.', [7])
    add(1, '确认移除账户参考照片', ['Sa', 'Ca'],
        'Face removal deletes the selected tag; full-body removal deletes all current tags of that kind via image-tags endpoints and captured account headers. After success cancel the query and filter deleted IDs from cache; invalidate on settlement.',
        'Block dialog outside-close during pending removal and retain edit/confirm return behavior. Promise.all failure can leave partial service deletion; cache filtering after full success is not transaction rollback.',
        'Verify selected/all-kind tag ownership, partial failure reconciliation, image storage effects and account-scoped readback.', [7])
    add(1, '切换账户工具与图像生成偏好', ['Ma', 'Ii'],
        'Apply web/code disabled_tools changes while preserving other entries and workspace browsing eligibility. Keep the separately gated image-generation toggle and its own pending/error path.',
        'Missing context/account data disables controls; absent workspace capability is not a user preference. Image-generation errors stay separate from system-message mutation errors.',
        'Verify effective tool/image providers and actual product-mode consumers; the presence of ChatGPT labels is not enough to exclude a shared implementation.', [6])
    add(1, '切换账户语音、资料搜索与其他个性偏好', ['Ma', 'Ii'],
        'Parameterize the account-setting writer for voice_enabled, file_library_auto_reference, connector_search_enabled, instant_answers_enabled, task_suggestions_enabled and hive_referenced_in_internal_knowledge. Preserve FedRAMP/registration-country/workspace permission and feature gates, legacy checked-state fallbacks and the local pending guard.',
        'Restricted or unavailable selected-workspace permissions disable the relevant controls. Keep setting-specific visibility and save errors; an unchecked restricted control is not evidence of its stored value.',
        'Verify each setting receiver, entitlement and effective consumer, captured account identity and persisted state. Do not infer a common backend transaction across these fields.', [6])

    add(2, '查看 Micro 设备连接、输入预览与电量', ['ui', 'di', 'gi', 'mi', 'pi', 'bi'],
        'Mount only when the native codexMicro bridge exists. Distinguish Codex Micro and Creator Micro, connection status and control-plane availability; show battery only when connected with available battery data. Render pressed-key, knob-pulse and joystick preview state.',
        'Bridge absence renders null. Control-plane unavailable takes precedence over a device-error description; connected-but-unavailable remains a warning, not a usable connection.',
        'Verify independent hardware bridge/provider, subscriptions, detach/reconnect and real preview/electric state; synthetic rendering is not device verification.', [9])
    add(2, '检查并打开 macOS 输入监控权限', ['di', 'pi'],
        'Only macOS enables the getInputMonitoringPermissionStatus query with background polling, always-on-mount refetch and five-second staleness. Preserve granted/denied/unavailable labels and the native openInputMonitoringSettings action.',
        'Non-macOS does not enable that query. Opening system settings does not grant permission; unavailable and unknown permission remain distinct from granted.',
        'Verify the native permission API, OS settings URL and actual post-grant input behavior on the target platform.', [9])
    add(2, '确认移除不可用的 Micro 连接', ['di', 'Mr', 'kr'],
        'Under the saved removable-connection predicate, confirm removal and recheck the store eligibility immediately before calling the imported remove-connection action. The dialog describes preserving preferences, custom assignments and Bluetooth pairing.',
        'Confirmation Cancel only closes. The shared form invokes confirm then close synchronously and does not await a promise; do not infer completed native removal or rollback.',
        'Verify removal eligibility, actual connection-manager side effects, preserved settings/pairing and reconnect behavior.', [9])
    add(2, '设置 Micro 灯光亮度与自动熄灭', ['di', 'fi', 'assignment-ji'],
        'Expose brightness as a range0..100 with step10 and percentage display; convert the input value with Number and write lightingBrightness. Select lightingAutoOff only from the imported preference options.',
        'The change handler does not independently clamp arbitrary values; HTML range and imported writer own validation. UI write invocation alone does not prove device acknowledgement or persistence.',
        'Verify preference validation/defaults, native light updates, write error behavior and reload/reconnect persistence.', [9])
    add(2, '设置 Micro Agent 键来源与单击行为', ['di', 'assignment-Ai'],
        'Choose an agent-source mode from its preference options, clear the open custom-agent editor and write agentSource. The independent singleTapAgentKeys control writes its own preference.',
        'Custom assignments are shown only under custom mode and remain separately stored. Changing mode does not prove deletion of assignments or a completed native mode switch.',
        'Verify source-mode meanings, selected tasks/agents, single-versus-double-tap consumers and persisted preferences.', [9, 12])
    add(2, '设置 Micro 语音键模式和独立麦克风键', ['di', 'ii', 'li'],
        'When voice capability is available, write voiceButtonMode in the normalized layout; otherwise use push-to-talk for display behavior. Independently toggle separateMicrophoneKeys, which expands the combined ACT10_ACT11 slot into the split slots.',
        'Capability-disabled voice mode does not become a service entitlement. Layout writing and physical key/voice execution remain separate; closing an editor does not undo prior immediate writes.',
        'Verify layout normalization, split-slot migration and actual push-to-talk/realtime behavior with the corresponding audio and hardware providers.', [9, 10])
    add(2, '编辑 Micro 命令键、技能与本地插入文本', ['di', 'yi', 'wi', 'mr', 'Ei', 'Di'],
        'Select slot/keycap, search compatible keycaps and choose default/unassigned, command, skill or composer-text action. Preserve an existing assignment when choosing its already-used keycap. Submit keycapId, commandId and only skill/composer-text action payloads; update layout through gn and close after its write promise resolves.',
        'Empty composer text blocks submit; whitespace is not rejected by this handler. Cancel discards the local dialog draft. Save failure has no local catch in the wrapper and must not be reported as a completed persisted assignment.',
        'Verify slot compatibility, imported layout transform and preference writer, exact command/skill execution and insertion without sending a prompt. Keep command catalog and skill providers external to this UI contract.', [10, 11])
    add(2, '设置 Micro 旋钮模式及各手势动作', ['di', 'bi', 'br', 'Ci', 'er'],
        'Select a predefined encoder mode or custom, writing encoderMode in the layout. Custom opens the editor for left/right/click/longPress; selecting/clearing a command or skill immediately calls the encoder transform and writes layout.',
        'Done closes the editor and clears search; it is not a commit/rollback boundary. Predefined mode tooltips describe actions but do not establish hardware execution or retained custom mappings.',
        'Verify encoder normalization, per-gesture callbacks, actual execution, pending/errors and layout persistence while switching modes.', [10, 11])
    add(2, '设置 Micro 摇杆各方向动作', ['di', 'bi', 'ar', 'er', 'or'],
        'Choose up/right/down/left and immediately set or clear a command/skill through the analog layout transform. Show the selected direction, active joystick preview and current assignment.',
        'Closing resets search and reports editor-open false; unmount also reports closed. No draft-wide Save/Cancel rollback exists for these immediate writes.',
        'Verify analog transform/deadzone provider, actual direction actions and persisted layout; preview animation alone does not prove execution.', [10, 11])
    add(2, '分配或移除 Micro 自定义 Agent 键目标', ['Jr', 'Ir', 'Hr', 'Jn', 'Yn', 'Zr'],
        'Choose chat, shortcut, keycap or skill. Search local/connected-host threads with deferred query and allSettled, combine supported loaded results and retain hostId/threadKey. Filter unavailable command capabilities, personalitySettings and custom-shortcut-only keycaps; select calls Sn(store,key,assignment), then closes. Remove writes null.',
        'Show loading/empty and discard results for an outdated deferred query; failed host searches contribute empty results. Cancel has no assignment write. This selector closes synchronously, unlike the slot editor promise; backend search, rank/dedupe and assignment persistence remain imported boundaries.',
        'Verify cross-host identity, query debounce/ranking and command/skill eligibility, duplicate task assignments and actual native key activation after persistence.', [11, 12])
    add(2, '确认恢复 Micro 默认键盘布局', ['di', 'kr'],
        'On confirmation, write the imported default layout through the preference writer. The description promises command keys/analog defaults while retaining agent-source mode and custom assignments.',
        'Cancel closes without writing. The shared confirmation closes immediately after invoking the write and has no local asynchronous success/error gate.',
        'Verify the default layout object, exact retained preference fields, write failure and native/readback state after reconnect.', [9, 10])
    return rows


def configuration():
    c, p, m = 'cloud-environments', 'personalization', 'codex-micro'
    return dict(number=15, work='settings-final-batch15-work', previousScope=23, previousCoverage=14,
        expectedState='2026-10-24T13:46:04.358292+00:00', selections=[c, p, m],
        scriptFiles=['settings_final_batch15_specs.py', 'probe_settings_final_batch15.cjs'],
        executionArtifacts=[f'{folder}-{suffix}' for folder in [c, p, m] for suffix in ['stdout.txt', 'stderr.txt', 'receipt.json']],
        entries=[(c, 'Cloud environments', 'T46'), (p, 'Personalization', 'T47'), (m, 'Codex Micro', 'T48')],
        mechanisms=[
            ('Cloud environment route/query ownership', 'Separate list/detail query and guarded route ownership from editor, mutation and onboarding services.', [(c, 'Ut'), (c, 'Lt'), (c, 'Gt'), (c, 'Kt')]),
            ('Cloud editor delegate', 'Create and edit use the imported editor with different initial state and return routes; internal form/receiver remains retained.', [(c, 'Ut'), (c, 'Kt')]),
            ('Cloud mutation and confirmation lifetime', 'Delete/reset permissions, pending UI, callbacks and post-success routes remain distinct from transport cancellation.', [(c, 'Gt'), (c, 'wt'), (c, 'Tt')]),
            ('Cloud migration and shared preferences', 'Migration selects a draft before onboarding; preferences tab delegates to the existing cloud-preference page.', [(c, 'Ot'), (c, 'Ut'), (c, 'Nt')]),
            ('Codex host memory orchestration', 'Host config/feature writers, Chronicle prerequisite and memory/reset are distinct operations; imported orchestration is retained.', [(p, 'Xr')]),
            ('Instruction editor and host identity', 'Preserve host/account adapters, loaded baseline, dirty registry, save guards and differing Back/Cancel behavior.', [(p, 'wi'), (p, 'Ci'), (p, 'Ti'), (p, '_i')]),
            ('Account preference query/mutation ownership', 'Keep system-message optimistic scope, captured account headers, dependent memory updates and account-setting writer distinct.', [(p, 'Ma'), (p, 'la'), (p, 'Ii')]),
            ('Photo account/tag lifecycle', 'Imported upload and local selected/all-kind deletion have different success and partial-failure behavior.', [(p, 'Ca'), (p, 'Sa')]),
            ('Lazy rules and writing-style families', 'Entry conditions and navigation are bounded; lazy provider contents remain required operations to analyze.', [(p, 'Br'), (p, 'Ur'), (p, 'Gr'), (p, 'assignment-Jr'), (p, 'Rr')]),
            ('Micro hardware bridge and preference writer', 'Native availability, connection state, OS permission query and preference writes have separate owners.', [(m, 'ui'), (m, 'di'), (m, 'kr')]),
            ('Micro layout transforms and editor lifetimes', 'Slot save waits for write; encoder/analog edits write immediately; shared confirmation closes synchronously.', [(m, 'di'), (m, 'yi'), (m, 'br'), (m, 'ar')]),
            ('Micro command/skill choice providers', 'Capability filters, command grouping and enabled/deduplicated skill choices are first-party adapters around external catalogs.', [(m, 'di'), (m, 'Jn'), (m, 'Yn'), (m, 'mr'), (m, 'er')]),
            ('Micro cross-host search/assignment', 'Retain host IDs, async result qualification, imported ranking/dedupe and assignment-store ownership.', [(m, 'Ir'), (m, 'Hr'), (m, 'Jr')])],
        sharedGoalConsumers=[dict(pageIndex=0, featureIds=['FSC-0339', 'FSC-0340'],
            relation='Root tab=preferences renders imported cloud-preferences page; existing diff-mode/branch-format goals retained rather than duplicated.',
            units=[(c, 'Ut'), (c, 'Nt')],
            remainingWork='Imported page/export and actual account consumer equivalence remain qualified; no new whole-feature mode classification.')],
        modules=['cloud-environments/legacy-settings', 'personalization/settings', 'codex-micro/settings'],
        consumers=[['cloud-environments/editor', 'cloud-environments/onboarding', 'cloud-preferences/settings'],
            ['memory/host', 'instructions/host', 'instructions/account', 'rules', 'writing-style', 'personalization/account', 'image-tags'],
            ['runtime-adapter/codex-micro', 'codex-micro/layout', 'codex-micro/assignments', 'commands', 'skills', 'tasks/search']],
        dependencies=[['environment queries/mutations', 'environment editor', 'native environmentConfigs', 'query/UI packages'],
            ['host config/app-server', 'Chronicle native service', 'account preference/image services', 'query/schema/UI packages'],
            ['independent native Micro bridge', 'preference store', 'command/skill/thread providers', 'query/UI packages']],
        gaps=[
            ['Retain imported environment editor, query/mutation receivers and migration/onboarding implementations as required delegated families.',
             'Actual workspace/account authorization, cache reset/deletion semantics and environment provisioning remain unobserved.'],
            ['Retain lazy UserRulesPage, WritingStyleSettings, saved-memories/about-you managers and imported memory/upload orchestration as required delegated families.',
             'Actual host/account identity, native Chronicle, config/system-message/image-tag receivers, storage and selected-mode consumer closure remain unobserved.'],
            ['Retain native codexMicro bridge, preference/layout/assignment stores, command/skill catalogs and cross-host search/ranking as required delegated families.',
             'Actual device/OS permission, native execution/acknowledgement, preference durability and selected-mode closure remain unobserved.']],
        decisions=['旧环境管理、编辑器和新环境引导分开；复用既有云偏好目标。',
            '按主机记忆、本地／账户指令、账户偏好和委托页面拆分；保留模式判定。',
            '界面与硬件桥接、布局变换、偏好及目标分配分开，保留不同保存时机。'],
        title='最后三个设置页面的操作与边界合同',
        modeReason='Personalization positively contains Codex host memory and instructions alongside account controls. Authentication labels, page names and native capability presence do not prove branch-level product-mode ownership; all new goals remain unknown.',
        firstParty='Page routing, permission and identity guards, draft/control state, request adapters, orchestration, layout/assignment glue and provider lifetimes.',
        externalize='React/compiler runtime, UI/query/schema and utility implementations use existing package inventories. Native Micro/Chronicle and private services require independently qualified dependencies/adapters; imported first-party delegates are not mislabeled as third-party.',
        probeDescription='使用合成主机、账户、设备状态与服务替身，未导入目标模块或连接真实设备／服务；导入算法仍按接口保留',
        modeSummary='新增功能全部保留unknown；既有归档shared 1不变，确认整项ChatGPT排除0。Personalization中的Codex记忆／指令构成正向保留理由，但不替代全页模式归属。',
        boundarySummary='45个容器的入口级局部合同已归并；委托页面、设备／服务接收方、旧入口处置、模式及真实行为缺口仍明确保留，不能称为全功能分母。',
        reportFacts='区分云环境删除／缓存／迁移、主机和账户指令、记忆级联以及Micro的等待保存／即时写入／同步关闭。',
        summaryPoints=[
            '云环境合同保留列表搜索分页、权限严格比较、详情中秘密名称展示、委托创建／编辑、删除、缓存重置和新环境草稿迁移。preferences入口关联既有FSC-0339／0340，不重复生成功能。',
            'Personalization按主机Codex记忆和指令、账户Codex指令、规则／写作风格入口、账户资料与个性、记忆、照片和工具偏好拆分。Back确认未保存，Cancel直接丢弃；账户偏好与主机文件不混用。委托管理页和服务实现仍待定向分析。',
            'Codex Micro保留设备桥接条件、权限与连接、灯光、Agent／语音模式、命令键和旋钮／摇杆、自定义目标及默认布局。命令键写入完成后关闭；旋钮／摇杆即时写入；分配与确认框同步关闭，三类时序不能统一成虚构事务。'],
        nextQualification='所有已发现设置容器已有有界入口合同；未分析的委托操作不能计为完成。下一步审计原九项标准及六组架构未知；模型剩余授权0，离线工作可继续。',
        nextAction=dict(issueId='SD-01/SD-02/SD-03/SD-05/SD-06',
            completedSubstep='All45 discovered settings containers now have bounded entry/control contracts; imported delegate families remain explicitly required.',
            fixedInput='Published batch15 contracts, current scope/coverage and original nine-criterion decisions; reuse all settled source selections.',
            question='Which retained delegated operations and architecture-changing unknowns still prevent a defensible analysis exit?',
            closure='Audit original criteria against current evidence; identify exact missing operation/provider/runtime/storage decisions and conditions. Reconcile current scope with the implementation schedule without equating scenario specifications to passed behavior.',
            deferredDedicatedVerification='No additional model submission authorization remains. Actual device/service and complete implementation acceptance remain separate from source-contract observations.'))
