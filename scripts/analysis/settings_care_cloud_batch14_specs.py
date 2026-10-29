"""Trusted contacts, time management and cloud preference contracts."""


def specifications():
    result = []
    def add(page, name, units, effect, negative, receiver, support):
        result.append(dict(pageIndex=page, name=name, units=units, effect=effect,
            failureAndCancellation=negative, acceptance=[effect, negative, receiver], support=support))
    add(0, '查看受信联系人状态与邀请说明', [('trusted-contact', 'nt'), ('trusted-contact', 'it'), ('trusted-contact', 'He'), ('trusted-client', 's')],
        'Under allowed personal identity, key the body by user/account. Fetch enabled first; enable the contact-list query only when enabled===true. Show the first contact, pending/active status, name fallback and formatted phone; otherwise expose Add and the introductory expectations/eligibility explanation. Query keys include both identities, retry is false and staleTime is30000ms.',
        'Access error retries accounts/check; loading/denied mounts no body. Query errors retry the failed query; disabled eligibility does not show Add. Country normalization selects the Korea wording only for KR and falls back to US for unsupported values.',
        'Verify actual eligibility, contact visibility, country/phone providers and access/mode consumers without assuming all contacts are rendered or an invitation delivered.', [0, 3])
    add(0, '填写联系资料并同意后邀请受信联系人', [('trusted-contact', 'it'), ('trusted-contact', 'Ke'), ('trusted-contact', 'st'), ('trusted-contact', 'assignment-et'), ('trusted-client', 'a')],
        'Require trimmed nonempty name, matching email syntax and explicit consent; send trimmed email, optional trimmed phone or null and relationship:null. A form ref blocks duplicate submits until finally. POST trusted_contact with captured account headers and blocked-email/phone expected errors; success upserts the returned contact then invalidates its list.',
        'Blank/invalid/unconsented/pending input cannot submit. Closing/reopening increments an epoch: late responses may reconcile the captured query cache but cannot change a newer dialog or call onInvited. Blocked destinations show unavailable/try-another; other current errors show feedback. Closing is not proof that the service request was aborted.',
        'Verify actual invitation permission, recipient delivery/acceptance, routing headers and identity-bound lifecycle using separately authorized synthetic recipients.', [0, 1])
    add(0, '重发待接受的受信联系人邀请', [('trusted-contact', 'it'), ('trusted-client', 'o')],
        'Expose Resend only for pending contacts with a usable email; normalize saved name/email, preserve optional phone/relationship and PUT the selected contact ID with captured account headers. Success gives feedback and invalidates the list.',
        'Missing email and pending request disable Resend; payload construction rejects missing email. Failed resend retains recoverable feedback and does not become accepted status.',
        'Verify actual resend/delivery limits and refreshed pending status independently of invitation acceptance.', [0, 2])
    add(0, '确认取消邀请或移除受信联系人', [('trusted-contact', 'it'), ('trusted-contact', 'Xe')],
        'Use pending/active-specific Cancel invitation or Remove labels, open a separate confirmation and DELETE only the selected trusted_contact_id. Prevent confirmation submit while pending; success closes the removal dialog, shows feedback and invalidates the list.',
        'Missing selected contact or a pending delete cannot invoke another mutation. Failed removal retains error feedback. The dialog close callback alone does not cancel or undo an in-flight deletion.',
        'Verify actual relationship/invitation removal, account scope and authoritative refreshed contact state with separate authorization.', [0, 2])
    add(0, '从邀请确认页打开个人说明邮件或帮助链接', [('trusted-contact', 'Je'), ('trusted-contact', 'at'), ('trusted-contact', 'qe'), ('trusted-contact', 'Ye')],
        'On success with an email, build an encoded mailto recipient/subject/body and try the imported external-browser bridge before location.assign fallback. Keep settings navigation, unavailable/try-another and help links as distinct actions.',
        'No email hides the personal-note action; unavailable never shows that action. Opening a mail composer is not sending a message or proving recipient delivery.',
        'Verify actual external URL handling and localized composition without sending an email as part of this analysis.', [3])
    add(1, '查看静默与学习时段状态并切换编辑视图', [('safety', 'Re'), ('safety', 'ze'), ('safety', 'je'), ('safety', 'Me'), ('safety', 'Ne')],
        'Require allowed access, eligibleNowOrBefore and enable_chatgpt_time_management_settings. Preserve quiet-hours/study-hours/time-management URL views with pathname/hash/state; distinguish scheduled from currently active and parent-managed from unsupported. Legacy always-on study maps through the legacy schedule adapter.',
        'Denied access shows unavailable; loading/error offers scoped retry. Unsupported saved schedules remain unchanged and do not mount an editable schedule. A stale overview fetch error may still allow an already loaded editor; do not flatten these branches into a single failure.',
        'Verify actual provider eligibility, flag and scheduled enforcement; displayed schedule status does not prove ChatGPT availability or study behavior.', [4])
    add(1, '编辑并保存静默时段及其星期时间块', [('safety', 'Pe'), ('safety', 'Te'), ('safety', 'Ee'), ('safety', 'Ie')],
        'Edit enabled state, weekdays and local/overnight start/end blocks; retain imported schedule reducer and validation policy, twelve-block UI limit and minimum-break error mapping. Save re-reads identity, eligibility, parent lock and supported state, then PATCH quiet_hours_schedule as JSON with captured account/signal. Close only after cancel/refetch confirms a nonerror result for the same identity.',
        'No changes, invalid/unsupported/managed state or in-flight controller prevents another write. Identity change/unmount aborts. Distinguish403 parent lock from generic denial and save/refetch error; retain draft for retry. Back uses the unsaved-changes dialog; Cancel exits without writing.',
        'Verify imported validation/reducer algorithms, DST/timezone/backend enforcement, unsaved navigation and durable readback; synthetic policy substitutes do not establish those results.', [4, 5, 6])
    add(1, '编辑并保存学习时段及兼容旧版常开状态', [('safety', 'Pe'), ('safety', 'je'), ('safety', 'Te'), ('safety', 'Ee'), ('study-legacy', 'i'), ('study-legacy', 'a')],
        'Use the shared editor but PATCH study_hours_schedule. Legacy default-to-study becomes an all-week00:00..23:59 synthetic block; editing converts it through the source adapter, assigns a fresh web-study-hours ID and preserves existing recurring blocks. Count converted blocks against the twelve-block capacity.',
        'Keep separate study validation and parent locks on study_hours_schedule/default_to_study_mode. Unsupported recurring state cannot be overwritten. Cancel/unsaved navigation and identity/abort/readback guards remain attached to this goal.',
        'Verify imported reducer/validation and actual legacy-to-recurring service semantics, enforcement and account binding.', [4, 5, 6])
    add(2, '切换云端会话差异视图', [('cloud-settings', 'F'), ('cloud-settings', 'I'), ('cloud-provider', 'v'), ('cloud-provider', 'b'), ('cloud-provider', 'S'), ('cloud-provider', 'C')],
        'Load user preferences and account/user configuration separately; after both load, choose unified or split and PATCH wham/settings/user with git_diff_mode. On success replace the captured user-preferences query cache with the server response; mutation feedback is distinct from rendering.',
        'Either query error exposes retry for both; missing data stays loading. Pending disables both diff options. Query retries are false; user preferences GET forwards its signal whereas config GET has no selected signal forwarding. Account/identity/service effects still require integration.',
        'Verify actual wham service/account scope, query identity and effective cloud diff rendering; this is distinct from local diff preferences.', [7])
    add(2, '验证预览并保存云端分支命名格式', [('cloud-settings', 'I'), ('cloud-settings', 'ae'), ('cloud-provider', 'w'), ('cloud-provider', 'T'), ('cloud-provider', 'E'), ('cloud-provider', 'S')],
        'Keep a draft only while its captured server branch_format baseline still matches. Validate placeholder braces, known tags, generated maximum length, leading slash and allowed characters; preview examples and list available tag values. Changed valid input saves branch_format through the same scoped mutation/cache path.',
        'Unchanged/invalid disables Save; pending disables the input and shows loading on Save. The selected Save disabled expression itself does not include pending, so additional duplicate suppression is delegated to the UI/mutation boundary. New server baseline discards the displayed stale draft; failed save keeps current edits and error feedback.',
        'Verify actual config bounds/placeholders, mutation concurrency and Git ref/server acceptance; this client pattern validator alone is not a complete Git ref validator.', [7, 8])
    return result


def configuration():
    folders = ['trusted-contact', 'safety', 'cloud-settings', 'trusted-client', 'cloud-provider', 'study-legacy']
    return dict(number=14, work='settings-care-cloud-batch14-work', previousScope=20, previousCoverage=11,
        expectedState='2026-10-24T12:35:45.468695+00:00', selections=folders,
        scriptFiles=['settings_care_cloud_batch14_specs.py', 'probe_settings_care_cloud_batch14.cjs'],
        executionArtifacts=['probe-attempt-01.cjs', 'probe-attempt-01.json', 'probe-attempt-01-stdout.txt', 'probe-attempt-01-stderr.txt', 'probe-attempt-01-receipt.json'] + [f+x for f in folders for x in ['-stdout.txt', '-stderr.txt', '-receipt.json']],
        entries=[('trusted-contact', 'Trusted contact', 'T43'), ('safety', 'Safety', 'T44'), ('cloud-settings', 'Cloud settings', 'T45')],
        mechanisms=[
            ('Trusted contact identity and queries', 'Preserve access, account/user keys, enabled-before-list, query retry/staleness and country normalization.', [('trusted-contact', 'nt'), ('trusted-contact', 'it'), ('trusted-contact', 'lt'), ('trusted-client', 's'), ('trusted-client', 'a')]),
            ('Consent form and invitation epochs', 'Keep email/name/consent validation, single form submit, epoch-bound UI completion and captured list cache reconciliation.', [('trusted-contact', 'Ke'), ('trusted-contact', 'it'), ('trusted-contact', 'st'), ('trusted-contact', 'assignment-et')]),
            ('Trusted contact resend and removal', 'Preserve selected-ID PUT/DELETE, email payload normalization and explicit removal confirmation/pending/error.', [('trusted-contact', 'it'), ('trusted-contact', 'Xe'), ('trusted-client', 'o')]),
            ('Contact external composition and help', 'Keep mailto encoding/bridge fallback and distinct external help/settings actions without implying message delivery.', [('trusted-contact', 'Je'), ('trusted-contact', 'He'), ('trusted-contact', 'at'), ('trusted-contact', 'qe'), ('trusted-contact', 'Ye')]),
            ('Time-management access, routes and legacy projection', 'Separate personal eligibility/flag/URL views, unsupported/parent-managed state and legacy study projection.', [('safety', 'Re'), ('safety', 'ze'), ('safety', 'je'), ('study-legacy', 'i'), ('study-legacy', 'a')]),
            ('Schedule save identity, abort and refresh', 'Recheck account/current access before write, watch identity changes, distinguish lock/denial/error and close only after successful readback.', [('safety', 'Pe'), ('safety', 'Ie'), ('safety', 'Fe')]),
            ('Schedule block and weekday drafts', 'Keep unsaved blocks/day-menu state, enable/add/update/remove and legacy capacity; imported reducers/validators remain assigned first-party boundaries.', [('safety', 'Te'), ('safety', 'Ee'), ('safety', 'Pe'), ('study-legacy', 'a')]),
            ('Cloud preference query and captured cache writer', 'Separate account/user config from user preferences; retain no-retry reads, selected signal handling and authoritative mutation response/cache context.', [('cloud-provider', 'v'), ('cloud-provider', 'b'), ('cloud-provider', 'S'), ('cloud-provider', 'y'), ('cloud-provider', 'x'), ('cloud-provider', 'C'), ('cloud-settings', 'I')]),
            ('Cloud branch draft, validation and preview', 'Retain exact supported placeholders, generated-length/character checks, baseline-bound draft and changed/valid save; no full Git ref validation claim.', [('cloud-settings', 'I'), ('cloud-settings', 'ae'), ('cloud-provider', 'w'), ('cloud-provider', 'T'), ('cloud-provider', 'E')])],
        gaps=[['Actual access/country/phone/URL providers, invitation delivery and account-scoped recipient consent remain service/integration boundaries.', 'Epoch isolation does not abort requests; real account switches, cache ownership and mode consumers remain unverified.'],
            ['Imported schedule reducer/validators, provider snapshot/identity watchers and time enforcement remain assigned first-party interfaces.', 'Actual parent policy, timezone/DST, legacy migration, cancellation and durable service readback remain unverified.'],
            ['Wham account/service routing, actual configuration and effective cloud consumers remain integration requirements.', 'Query/mutation cache isolation, duplicate-save behavior and real Git/server validation remain unverified.']],
        modules=['trusted-contact/settings', 'time-management/settings', 'cloud-preferences/settings'],
        consumers=[['app/account-access', 'account/trusted-contact-client', 'account/trusted-contact-invitation', 'app/external-url'],
            ['app/account-access', 'account/time-management-state', 'account/time-management/schedule-policy', 'account/time-management/legacy-study', 'app/unsaved-navigation'],
            ['cloud/preferences-client', 'cloud/preferences-config', 'cloud/diff-view', 'cloud/branch-format']],
        dependencies=[['React/UI/query/state packages', 'phone input/parser packages', 'trusted-contact account services', 'external URL bridge'],
            ['React/UI/query/state packages', 'account settings/identity provider', 'assigned schedule-policy module', 'unsaved-navigation dialog'],
            ['React/UI/query/state packages', 'wham preferences/config service', 'cloud diff/branch consumers']],
        decisions=['Recover identity-scoped contact queries, consent/epoch dialogs and selected-ID mutations; keep recipient delivery outside UI success.',
            'Recover shared recurring editor and legacy adapter with separate quiet/study policies; preserve identity/readback/unsaved navigation.',
            'Recover cloud preference hooks/cache writer and pattern validator as first-party modules; separate cloud consumers from local settings.'],
        title='受信联系人、时间管理与云端偏好分析',
        modeReason='Trusted contact/Safety have chatGpt access; Cloud settings has no access-family label and an existing conditional redirect. Names/texts do not prove exclusive consumers, so none is excluded.',
        firstParty=['contact identity/query/consent/epoch policy and client', 'time-management editor/save/legacy adapter', 'assigned recurring reducer/validation policy', 'cloud preference hooks/cache/pattern validator'],
        externalize=['React/UI/query/state packages', 'phone input/parser packages after inventory mapping', 'remote account/contact/wham services behind explicit adapters'],
        probeDescription='仅以合成身份、联系人、时段、配置和内存查询/服务替身执行冻结源码；没有发送邀请、邮件、修改真实账户或调用模型服务',
        modeSummary='保留访问家族与产品模式的区别；云端偏好与本机差异视图分别归属，未凭名称排除整页。',
        boundarySummary='联系请求完成与邀请送达、时段已保存与实际执行、格式检查通过与Git服务接受分别验收。',
        reportFacts='明确邀请epoch与捕获缓存、时段保存前重查及身份取消、旧版学习适配、云端查询/缓存和分支格式校验。',
        summaryPoints=[
            'Trusted contact先查资格再查列表，当前页只展示首个联系人。邀请需姓名、有效邮箱和同意；关闭或重开表单会隔离旧响应的对话框更新，但不等于取消网络请求。',
            '重发与移除分别调用选中联系人ID；个人说明动作只打开邮件编辑器，邀请成功反馈不证明邮件送达或对方已接受。',
            'Safety区分静默、学习、父级管理及不支持格式；保存时重新核对身份和权限，监听切换并取消，刷新确认后才关闭。旧版常开学习通过独立适配器转成时段。',
            '云端偏好分别读取用户值和账户/用户配置，以服务响应更新捕获的查询缓存。分支草稿绑定服务器基线；格式校验覆盖占位符、长度和字符，不等于完整Git引用规则。',
            '已恢复的查询/写入、旧版适配和格式校验归第一方模块；React等第三方实现不生成维护副本。真实服务、调度算法及模式使用方保留明确验收要求。'],
        nextQualification='Finish cloud-environments/personalization/codex-micro from saved dispositions, then reconcile the original nine completion criteria. Keep service/runtime/mode/algorithm gaps explicit; do not reopen settled page families or add model submissions.')
