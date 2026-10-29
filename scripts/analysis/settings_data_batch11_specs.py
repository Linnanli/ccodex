"""Separate ad/account data, cloud tasks and local archived threads."""


def specifications():
    result = []
    def add(page, name, units, effect, failure, behavior, negative, receiver, support):
        result.append(dict(pageIndex=page, name=name, units=units, effect=effect,
                           failureAndCancellation=failure, acceptance=[behavior, negative, receiver], support=support))
    A = lambda *names: [('ads-controls', n) for n in names]
    R = lambda *names: [('archived-chats', n) for n in names]
    D = lambda *names: [('data-controls', n) for n in names]
    add(0, '设置广告个性化', A('Ge', 'Ve') + [('ads-state', 'w')],
        'Patch bazaar_personalization_enabled for the selected account, merge the saved preference and remove the exact topics query. Availability, data, pending and personalization-unavailable guards are distinct.',
        'The settings path rejects unavailable personalization; the separate consent context has its own capability/override rules. Rejection or identity change returns false, with feedback guarded by the captured identity.',
        'Inspect settings versus consent guards, account headers, boolean payload and topics invalidation.',
        'Use missing data, unavailable state, account switch and failed patch; do not claim successful saving for a stale identity.',
        'Verify the account settings service, exact query invalidation and actual personalization consumer.', [0, 1])
    add(0, '选择免费广告退出或恢复广告', A('Ve', 'De') + [('ads-state', 'w')],
        'Under the source flag, set free_ads_opt_out. The opt-out choice describes reduced message limits; returning to ads refreshes eligibility before accepting success.',
        'Pending controls, disabled flag, request failure and identity change prevent success. The Plus action only delegates an external plan URL; it does not purchase a plan.',
        'Inspect both boolean values, flag guard, refresh order and external upgrade navigation.',
        'Reject refresh or switch identities during it; retain false outcome and prevent duplicate pending submission.',
        'Verify account entitlement refresh and the existing external billing entry; do not create another purchase implementation.', [0])
    add(0, '查看广告历史及分页', A('Ve', 'je', 'Me', 'Pe', 'Ne', 'Re') + [('ads-state', 'assignment-E')],
        'Navigate to ads-history and read account/identity-scoped cursor pages. Show pending, empty, retry and advertiser/viewed/opened summaries; the selected history row has control:null.',
        'Ads opt-out hides history access; error blocks further-page loading. Historical opened labels do not establish an interactive ad-opening action.',
        'Inspect account/identity query keys, cursor requests, empty projection and read-only rows.',
        'Use empty/error pages and opt-out state; no invented click-through, write or false pagination success.',
        'Verify history service, cancellation and query isolation across account changes.', [0, 1])
    add(0, '查看广告兴趣主题及分页', A('Ve', 'Fe', 'Le', 'Re') + [('ads-state', 'assignment-D')],
        'Navigate to ads-topics only with eligible personalization; query scoped preferences with cursors and render topics as a read-only collection.',
        'Missing preference data, personalization disabled/unavailable or opt-out suppresses entry/query according to its own guards. Loading, retry and empty states remain distinct.',
        'Inspect topic eligibility, account/identity keys, preferences endpoint and cursor projection.',
        'Disable personalization or return errors/empty pages; do not invent topic editing/removal controls.',
        'Verify query enablement and personalized preferences service under real entitlement conditions.', [0, 1])
    add(0, '确认删除广告历史与兴趣数据', A('Ve', 'Ee') + [('ads-state', 'T')],
        'After confirmation, delete /bazaar/profile for the selected account, clear the scoped history/topics pages and invalidate both queries. The unavailable-region wording distinguishes history-only data.',
        'Pending blocks close/submit. Failed delete or changed identity does not close as successful; confirming suppresses cancellation analytics. This deletes ad data, not conversations or local threads.',
        'Inspect confirmation, delete headers, query clearing and successful close guard.',
        'Cancel, repeat while pending, fail the request or switch identity; preserve feedback and scope.',
        'Verify actual ad-profile deletion and reload results without touching task/conversation APIs.', [0, 1])
    add(1, '浏览搜索筛选及排序归档记录', R('hn', 'wn', 'Cn', 'Sn', 'bn', 'vn', 'gn'),
        'Merge selected-host and eligible durable archived local threads, archived cloud tasks and account conversations. Preserve type/project/search filters, updated/created/alphabetical sorting, retry and qualified pagination.',
        'Streamed local listing checks abort before/after requests and rejects repeated cursors. Durable query is account-scoped and connection-dependent; reconnect is distinct from refetch. Local unavailability resets a local-only filter.',
        'Inspect typed source aggregation, host/account keys, filters, grouping, sort and cloud/conversation pagination.',
        'Abort, repeat a cursor, disconnect durable or fail one source; keep partial data and retry/reconnect ownership explicit.',
        'Verify app-server lists, cloud/account queries, projects/automation grouping and real focus/navigation integration.', [2, 3])
    add(1, '删除本地归档线程、项目归档或全部宿主归档', R('wn', 'Pn', 'En', 'Tn'),
        'Confirm a typed single/project/all deletion. Single and project paths call deleteArchivedConversation for named IDs; all calls deleteAllArchivedConversations on the selected host, independently of the current search/filter rows.',
        'Delete UI is restricted to eligible local-host rows. Optimistic removal uses requested local IDs, restores prior cache on failure and invalidates afterward. Returned deletion count may exceed the visible filtered set.',
        'Inspect payload kind, exact IDs and host-wide scope of all; preserve distinct destructive confirmation wording.',
        'Apply search/project filters, reject one deletion or return unsupported thread/delete; do not present all as deleting only visible results.',
        'Verify actual archive storage/backend deletion, partial failure semantics and cache/focus restoration using owned threads.', [2, 3])
    add(1, '恢复已归档云任务', R('un'),
        'Rows with the cloud-task archived shape recover via POST /wham/tasks/{task_id}/recover, remove that task from the account archive query and offer /remote/{id} navigation.',
        'Pending suppresses repeats; failure feedback and final task-query invalidation remain. The selected cloud row has no conversation-delete button.',
        'Inspect cloud shape discrimination, recover path ID, scoped cache removal and View now route.',
        'Reject recover or omit route data; no local unarchive/conversation delete call or false recovery success.',
        'Verify cloud task recovery service and resulting task/archive state separately from local app-server operations.', [2, 3])
    add(1, '取消账户会话归档', R('un'),
        'A non-cloud account-conversation row delegates to the account conversation unarchive adapter and offers its conversation navigation.',
        'Use its separate mutation/pending/error/focus behavior. This path is not the existing local-thread unarchive operation.',
        'Inspect row discrimination, conversation ID, delegated callback and navigation consumer.',
        'Fail the adapter or repeat while pending; do not call cloud recover or local host unarchive.',
        'Verify account conversation service and archive refresh, and classify its retained product consumers before removal.', [2, 3])
    add(1, '确认删除账户归档会话', R('un'),
        'Only account-conversation rows expose the selected delete action. Confirm through the delegated dialog, delete via the account conversation adapter and invalidate its account archive query.',
        'Failure retains error feedback. Cloud-task rows omit this delete button; local archived deletion belongs to the separate host operation.',
        'Inspect conversation-only button gate, ID, confirmation and successful query invalidation.',
        'Cancel or reject deletion and supply cloud-task rows; no extra cloud/local destructive action.',
        'Verify delegated delete confirmation, service identity and actual account conversation visibility.', [2, 3])
    add(2, '设置账户训练数据偏好', D('dn') + [('training-query', 'a')],
        'Patch training_allowed and update its query snapshot only when settings data, locks, current/real account match and workspace training eligibility allow it. Workspace eligibility is separately queried.',
        'Absent data, lock, mismatch, workspace query error or non-permitted policy rejects the change. Error feedback is guarded by current account; account settings are not local thread preferences.',
        'Inspect training switch, workspace query enablement, query identity and guarded patch/optimistic value.',
        'Vary lock/account/policy/error and reject patch; no request on a denied guard and no stale-account feedback.',
        'Verify actual account setting and workspace policy; reuse the retained shared account-access layer.', [4, 8])
    for action, label in [('archive', '批量归档账户会话'), ('delete', '批量删除账户会话')]:
        add(2, label, D('dn'),
            'Confirm ' + action + ' and PATCH /conversations with ' + ('is_archived:true' if action == 'archive' else 'is_visible:false') + '. Clear current-account list state only if identity remains current, then invalidate account lists and persisted cached history.',
            'Pending/confirmation and errors retain their own UI states. This service acts on account conversations, not selected-host archived threads or filesystem projects.',
            'Inspect action-specific confirmation and exact request body plus cache/identity effects.',
            'Cancel, fail the request or switch accounts during it; no host-wide local deletion and no clearing a new account list.',
            'Verify account conversation batch scope and persisted cache eviction; actual service semantics require account-level acceptance.', [4, 8])
    add(2, '请求账户数据导出', D('dn', 'Pt', 'Ft'),
        'Gate export by matching user/account and workspace permission. Obtain reauthentication headers, recheck the request token and POST /accounts/data_export with expectedIdentity; requested means asynchronous email export, not a downloaded file.',
        'A stale/cancelled token skips the export request. Pending, close/unmount, reauth, 409, required email/phone and general errors keep their dedicated outcomes. Ft does not read its third callback argument; do not claim that unused callback is another guard.',
        'Inspect permission and token lifetime, reauth purpose, identity header and requested/cancelled results.',
        'Cancel/switch/unmount during reauth, reject export or return conflict/auth errors; no duplicate request or premature download success.',
        'Verify real account export/reauth service and email-completion integration; retained dialog machinery does not prove every branch reachable from Ft.', [4, 5, 8])
    add(2, '设置营销与广告隐私同意', D('dn', 'Rt'),
        'Post user_granular_consent for the selected marketing/personalization key with account headers and merge its query data. With the source flag and browser Global Privacy Control, the payload sets all three consent categories false.',
        'Preserve feature entry gate, mutation errors and account/query state. GPC inclusion of analytics in the payload does not prove a separately rendered analytics control.',
        'Inspect category-specific versus GPC override payload, headers and query merge.',
        'Vary the GPC flag/browser signal and reject save; do not invent additional controls or claim cookie/service effects from the UI alone.',
        'Verify account consent service, imported consent adapters and effective downstream privacy behavior.', [6, 8])
    add(2, '设置精确位置许可与设备授权', D('dn', 'Ut', 'Wt'),
        'Separate feature capability, server precise_location_allowed, lock/restriction, device permission and identity. Enabling from false refreshes settings before patching and requesting device permission; disabling stops sharing only under the captured account/user/identity.',
        'Stale identity, refreshed lock/restriction or missing capability stops later effects. Denied permission has its own dialog; pending finally releases and errors are identity-guarded.',
        'Inspect fresh eligibility, expectedIdentity/account headers, patch and device-permission order.',
        'Switch identity during refresh/patch, deny device permission or apply a parental restriction; no stale-account permission request or stop.',
        'Verify device permission, location-sharing receiver and actual server setting independently.', [4, 6, 8])
    add(2, '设置云端 Work 网络访问', D('dn', 'Zt'),
        'Read enableFloraNetworkAccess and delegate its boolean mutation. Missing/error data, pending and the matching amphora lock disable the switch; read/save errors expose Reload.',
        'The imported mutation implementation and endpoint are not selected here. A successful UI callback alone does not prove cloud network access changed.',
        'Inspect checked/disabled/lock state, boolean mutation and read/save reload action.',
        'Use missing data, lock, pending and failed save; preserve disabled controls and error feedback.',
        'Recover the imported mutation/authorization service and verify effective cloud Work network policy.', [4, 7, 8])
    add(2, '确认重置当前云端 Work 环境', D('dn', 'an', 'on', 'tn'),
        'Under the reset feature flag and loaded eligible personal/workspace account, confirm POST /flora/workspace/reset with account/user expectedIdentity and no retries. The dialog describes deleting current remote environment data while preserving Library files.',
        'Workspace requires the flora feature. Pending blocks close/submit; failure keeps the confirmation available and success closes it. This is not local-project deletion or account-wide Library deletion.',
        'Inspect entry eligibility, destructive scope, identity headers and both no-retry settings.',
        'Cancel, repeat while pending, remove workspace capability or fail reset; no local directory effect or false reset success.',
        'Verify real remote environment reset, Library preservation and creation of the subsequent fresh environment.', [4, 7, 8])
    return result


def configuration():
    return dict(number=11, work='settings-data-batch11-work', previousScope=17, previousCoverage=8,
        expectedState='2026-10-24T11:42:47.417406+00:00',
        selections=['ads-controls', 'archived-chats', 'data-controls', 'ads-state', 'ads-availability', 'training-query'],
        scriptFiles=['settings_data_batch11_specs.py', 'probe_settings_data_batch11.cjs'],
        priorProbeAttempts=[dict(observations='probe-attempt-01.json', probeScript='probe-attempt-01.cjs',
            disposition='26 passed; one fixture selector matched both mutation and onMutate callbacks. Tightened the selector to unarchiveConversation; frozen source unchanged.')],
        executionArtifacts=['probe-attempt-01-stdout.txt', 'probe-attempt-01-stderr.txt', 'probe-attempt-01-receipt.json',
            'probe-attempt-02-stdout.txt', 'probe-attempt-02-stderr.txt', 'probe-attempt-02-receipt.json', 'probe-attempt-02.cjs', 'probe-attempt-02.json'],
        entries=[('ads-controls', 'Ads controls', 'T34'), ('archived-chats', 'Archived chats', 'T35'), ('data-controls', 'Data controls', 'T36')],
        sharedGoalConsumers=[dict(pageIndex=1, featureIds=['FSC-0046'],
            relation='Archived local-row unarchive is another consumer of the existing local thread archive/unarchive goal; preserve host/cache/focus and already-open error handling here.',
            units=[('archived-chats', 'wn'), ('archived-chats', 'Pn')],
            acceptance='Verify host-specific unarchiveConversation with useAppServerPins, optimistic removal/rollback distinction, invalidation and View now; do not add another local-unarchive feature owner.')],
        mechanisms=[
            ('Ads account, identity and eligibility', 'Keep account/identity, capability, flags, opt-out and consent-context checks separate; data updates cannot authorize other services.', [('ads-state', 'w'), ('ads-state', 'T'), ('ads-availability', 'assignment-v')]),
            ('Ads scoped query and read-only projection', 'History/topics have distinct cursor queries, enabled conditions, empty/error states and read-only row projections.', [('ads-state', 'assignment-E'), ('ads-state', 'assignment-D'), ('ads-controls', 'Me'), ('ads-controls', 'je'), ('ads-controls', 'Fe')]),
            ('Typed archive aggregation and pagination', 'Local/durable app-server threads, cloud tasks and account conversations keep their host/account keys, source shape, filters and pagination.', [('archived-chats', 'hn'), ('archived-chats', 'wn'), ('archived-chats', 'Cn'), ('archived-chats', 'Sn')]),
            ('Archive mutations, cache and focus', 'Different row types retain different recover/unarchive/delete APIs, optimistic caches, rollback, invalidation, count and focus ownership.', [('archived-chats', 'wn'), ('archived-chats', 'un'), ('archived-chats', 'Pn')]),
            ('Account settings and workspace eligibility', 'Selected settings account, real account, user/identity and workspace permissions remain independent of local host and product mode.', [('data-controls', 'dn'), ('training-query', 'a'), ('data-controls', 'an')]),
            ('Export request token and reauthentication', 'Retain request-token lifetime, disabled-by-default reauth query and delegated email/auth completion; requested is asynchronous account export.', [('data-controls', 'dn'), ('data-controls', 'Pt'), ('data-controls', 'Ft')]),
            ('Consent, server location and device permission', 'Keep granular consent/GPC, server allowance/locks and device permission/sharing receivers separate, with account identity guards.', [('data-controls', 'Rt'), ('data-controls', 'Ut'), ('data-controls', 'Wt')]),
            ('Cloud Work policy and reset services', 'Network preference mutation is delegated; reset has identity/no-retry/confirmation and cloud environment versus Library scope.', [('data-controls', 'Zt'), ('data-controls', 'an'), ('data-controls', 'tn')]),
            ('Data-controls root and delegated managers', 'Preserve flag/view routing to Ads, Information sharing and shared-link management as page orchestration boundaries; their imported implementations are not exhausted by these finite controls.', [('data-controls', 'dn'), ('data-controls', 'assignment-gn'), ('data-controls', 'assignment-_n')])],
        gaps=[
            ['Actual ad availability/entitlement, consent and account services, query identity/cancellation and downstream ads consumers remain assigned interfaces.', 'Actual Codex/shared consumers, flags, real save/delete effects and ad-free entitlement behavior.'],
            ['Archive normalizer/filter/project/automation grouping, host/cloud/account list and mutation adapters, delegated delete dialog and focus/navigation remain assigned interfaces.', 'Actual multi-host/account source aggregation, irreversible scope/partial failure, persistence and cross-entry equivalence.'],
            ['Settings/training/permission/consent/export/reauth, location device/sharing, Work network/reset and shared-link/information-sharing managers remain assigned interfaces.', 'Actual selected product consumers, account policy, identity changes, remote service effects, Library preservation and device permissions.']],
        modules=['ads/settings', 'archives/settings', 'privacy/settings'],
        consumers=[['app/account-access', 'ads/account-state', 'ads/history-topics', 'billing/external-entry'], ['tasks/archive', 'hosts/app-server', 'cloud/tasks', 'account/conversations', 'projects/grouping', 'app/navigation-focus'], ['app/account-access', 'account/settings', 'account/conversations', 'account/export-reauth', 'privacy/consent', 'privacy/location', 'cloud/work-environment', 'account/shared-managers']],
        dependencies=[['React/UI/query/state packages', 'account ad settings/availability/profile services', 'external billing navigation'], ['React/UI/query/state packages', 'app-server archive APIs', 'cloud task and account conversation services', 'project/focus/navigation adapters'], ['React/UI/query/state packages', 'account/settings/training/export/reauth/consent services', 'device location and cloud Work services', 'shared-link/information-sharing managers']],
        decisions=[
            'Separate ad preferences, entitlement and read-only history/topics from account conversations; delegate external billing entry.',
            'Aggregate typed sources in presentation while preserving separate local host, cloud task and account conversation effect adapters; reuse existing local unarchive owner.',
            'Separate account conversation data, privacy/permission and remote Work environment services; preserve delegated managers and shared account access.'],
        title='广告、归档与数据控制：明确操作对象及批量作用域',
        modeReason='Ads uses chatGpt access; archives/data use chatGptOrCodex access and host/auth predicates. The retained desktop access publisher proves these access families are not product-mode labels. No whole page is excluded by naming.',
        firstParty=['ad/account identity and eligibility policy', 'read-only query projection and confirmations', 'typed archive source/mutation orchestration', 'host-wide versus named-ID deletion scope', 'account conversation/export request and cache guards', 'privacy/GPC/location and cloud Work reset policy'],
        externalize=['React/UI/query/state packages', 'app-server/cloud/account ad and conversation services', 'shared account/consent/reauth/location managers', 'cloud Work environment services', 'delegated shared-link/information-sharing managers'],
        probeDescription='仅执行冻结源码函数/回调及合成状态、查询和服务替身；未读取账户数据、提交真实删除/导出/重置、请求设备位置或调用模型服务',
        modeSummary='三页保留待具体消费者的模式核对；共享账户访问层沿用已收束合同，本地取消归档复用FSC-0046。第三方实现及服务接收方保持外置边界。',
        boundarySummary='“全部本地归档”是选定宿主的整体操作，不等于当前筛选结果；账户批量会话操作、广告数据清理和云端Work重置分别验收。',
        reportFacts='区分本地线程/云任务/账户会话的不同API，保留宿主级全删、账户会话批处理、导出token及云端环境/Library边界。',
        summaryPoints=[
            'Ads的历史行与兴趣主题为只读展示；删除接口清理广告profile。广告退出/恢复受独立资格和身份约束，升级链接仅负责外部导航。',
            'Archived chats混合不同类型来源：本地线程调用宿主archive适配器，云任务调用recover，账户会话调用自己的取消归档/删除服务。云任务行没有所选会话删除按钮。',
            '本地“删除全部归档”调用deleteAllArchivedConversations，作用于所选宿主；当前搜索/项目筛选不能缩小这个接口的语义。按项目删除则逐个处理明确ID。',
            'Data controls的批量archive/delete调用账户/conversations；导出是异步邮件请求，需保留token/身份守卫。位置的服务器许可与设备权限分开；Work reset仅针对当前远端环境并声明保留Library。',
            '共享链接、Information sharing和其他懒加载管理器保留委托边界；不能把页面导航当成这些管理器功能已完整恢复。'],
        nextQualification='Continue agreements/account/extension from saved dispositions. Reuse closed desktop-access publication. Real account/cloud/local effects, delegated managers and mode/shared closure remain per-task integration requirements. No model authorization remains.')
