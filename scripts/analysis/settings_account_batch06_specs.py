"""Bounded account-page goals; delegated dialogs and live services remain explicit."""

def specifications():
    result = []
    def add(page, name, units, effect, failure, behavior, negative, receiver, support):
        result.append(dict(pageIndex=page, name=name, units=units, effect=effect,
            failureAndCancellation=failure, acceptance=[behavior, negative, receiver], support=support))
    U=lambda *names:[('usage',n) for n in names]
    B=lambda *names:[('billing',n) for n in names]
    T=lambda *names:[('teams',n) for n in names]

    add(0,'浏览用量页面并切换可用面板',U('id','Gu','Nu','assignment-ud'),
        'Resolve visible registry sections, canonical path/search and plan density. Panels stay mounted but are hidden when unselected; isPolling follows selection. Main overview preserves personal/workspace and eligibility branches.',
        'Account/access loading, permission hiding, load errors and retries differ. Analytics, consumer-view and usage-code-review lazy children remain retained delegated families, not completed operations.',
        'Check canonical navigation with hash/state, visible tabs, hidden mounted panels and selected-panel polling under each plan branch.',
        'Exercise unavailable/unknown tab, access loading, quota error and auto-reload error independently; one failed credit section must not erase available usage information.',
        'Observe actual account/plan/flag providers and each lazy child separately; confirm route navigation and polling rather than inferring from helper output.',[0])
    add(0,'查看额度历史并切换时间窗口',U('iu','$l'),
        'Read balance history for the authenticated account/user and selected 300 or10080-minute window, accumulate cursor pages, display aggregation gaps and approximate reset boundaries.',
        'Abort is checked before each page;404 means unavailable history,409 permits one query retry. Recent missing points are not zero allowance.',
        'Change time window and inspect cursor aggregation, account-scoped query identity, chart gaps and hover timestamps.',
        'Abort between pages, return404/409, and display pending aggregation distinctly from zero; do not label an approximate reset as exact.',
        'Verify real history data and rendering via external chart dependencies; isolated pagination does not prove the chart or service.',[0])
    add(0,'申请提高个人或工作区用量额度',U('xu','El'),
        'Preserve member/owner/admin, individual/workspace/seat exhaustion, identity and policy branches. A custom request URL opens externally; eligible native requests use the selected reason; fallback actions remain distinct.',
        'Unavailable policy, identity mismatch, loading and disabled fallback remain guarded. Enterprise request-policy editors and backend approval remain delegated.',
        'Select exhaustion reason and role; verify custom URL versus request action and owner/admin affordances.',
        'Fail policy loading or identity checks; preserve retry and avoid revealing the numeric shared balance to an ineligible member.',
        'Verify account-scoped request receiver and resulting administrative workflow; no live request was made in analysis.',[0,1])
    add(0,'从用量设置发起额度购买入口',U('mo','mu','fs','Su'),
        'Forward purchase context, account identity and current account to the shared purchase navigator; workspace auto-reload supplies an account-encoded external credits URL. Balance visibility and purchase eligibility are separate.',
        'Navigation is not a completed purchase. Unknown balance is not an exhausted balance; owner-only disclosure and account conditions remain.',
        'Check personal/workspace entry context, account_id encoding and eligible purchase controls.',
        'Test unavailable balance, ineligible role and missing account without initiating checkout or charging.',
        'Verify shared checkout/browser adapter and account binding using a dedicated authorized test fixture; payment completion remains unobserved.',[0,1])
    add(0,'配置额度自动充值及其付款方式',U('ps','fs','mu','gs','js'),
        'Open the shared dialog to enable/update/disable auto reload. Preserve server state, threshold/target/monthly-limit validation, discounts, selected payment identity and confirmation policy.',
        'Discount/loading and payment eligibility can block submission. Cancellation closes draft/confirmation state; it cannot imply rollback of an already completed remote mutation. Imported validators/payment editors remain delegated.',
        'Exercise enabled/disabled policy, values, discount offer and eligible saved/new payment selection; confirm the intended mutation is selected.',
        'Reject invalid values, unavailable discounts or unresolved payment eligibility; preserve error state and disable-confirmation semantics.',
        'Verify actual subscription/payment APIs, cache refresh and persisted policy under the intended account; no financial request was executed.',[1,2])
    add(0,'从用量设置打开方案管理入口',U('Qs'),
        'Present current plan and forward the usage-settings plan-row source/current-plan context to the pricing or plan-management destination.',
        'The destination and subscription mutation are delegated; an opened pricing flow is not an upgraded plan.',
        'Inspect current-plan presentation and source context at the selected plan-management entry.',
        'Vary ineligible/unavailable plan data and destination failure; do not report navigation as a completed subscription change.',
        'Verify actual pricing destination and mode/account visibility without duplicating the billing subscription workflow.',[0,1])
    add(0,'设置各应用可使用的订阅额度比例',U('Sc','mc','hc'),
        'Under the source flag and authenticated account/user guard, fetch per-app limits, maintain draft percentages and save a global100/per-app map. On success update cached limits, clear draft and invalidate the query.',
        '401/403/404 list responses mean unavailable and hide the section; other failures remain errors. Save only changed values and block pending duplicate submission. Credit-preference child remains a delegated control.',
        'Edit multiple app percentages, save changed values and verify the account header and success cache update.',
        'Exercise unavailable list, load/save failure, unchanged values and in-flight save without discarding an unsaved draft as success.',
        'Verify actual usage-limit service and consumers of changed limits; authMethod chatgpt does not by itself classify the whole feature as ChatGPT-only.',[0,1])
    add(0,'设置是否允许 Codex 按明确请求使用重置额度',U('tl'),
        'Read and write agentUsageResetEnabled through the shared preference writer. The explanatory policy requires an explicit conversation request and low remaining allowance; the toggle is not a redeem action.',
        'Preference write rejection shows a failure toast; the actual policy enforcement and durable preference provider are separate retained boundaries.',
        'Toggle the preference and inspect the exact key/value sent to the preference adapter.',
        'Reject the write and check failure presentation; toggling alone must not consume a reset.',
        'Verify persistence and the task-side explicit-request/remaining-limit enforcement before declaring end-to-end behavior.',[0,1])
    add(0,'使用一个已保存的用量重置额度',U('qc','Nu'),
        'Redeem automatic or selected credit through the controller, distinguish in_flight/transport_error/rejected/reset, preserve retry identity after transport error, and coordinate reset-fill animation with refreshed rate-limit status.',
        'A transport error keeps the credit/count snapshot for retry; rejection clears it and invokes cancel; only reset reports success. Different credit IDs cannot replace an unresolved attempt.',
        'Check selected/automatic redemption, remaining count and success callbacks plus animation/refresh coordination.',
        'Exercise concurrent attempt, different-credit retry, transport failure and rejection without false success or duplicate consumption.',
        'Verify the actual redemption controller, service result and refreshed allowance; VM cases do not consume or restore real credits.',[0,1])
    add(0,'浏览已保存重置额度的使用历史',U('Ec','kc'),
        'Load account/user-scoped reset history with cursors and render granted/redeemed events in the local time zone; page errors and next-page errors have distinct retry actions.',
        'The past30-days empty message is scoped to the fetched history; no grant source is invented. Load more is disabled while fetching.',
        'Read multiple cursor pages and check event kind, local timestamps and ordering.',
        'Exercise empty/loading/initial-error/next-page-error states and select the corresponding retry action.',
        'Verify actual history service, account transitions and pagination subscribers separately from synthetic endpoint checks.',[0])

    add(1,'查看个人账户订阅与计费状态',B('Xr','Zr','kr','br'),
        'Mount only after current account matches the authenticated personal account and user. Preserve no-payment-trial refresh reconciliation, entitlement/customer/store conditions and available sections.',
        'Loading, account mismatch, inaccessible session and unresolved trial data differ; do not turn missing refreshed entitlement into a confirmed active subscription.',
        'Vary account identity, account structure, subscription/store/customer and refreshed trial data; inspect the correct sections.',
        'Check loading, access denial and failed/mismatched trial refresh; retain appropriate retry instead of stale paid-state success.',
        'Verify real account/subscription receivers and mode visibility; accessFamily chatGpt is recorded without assuming all payment consumers are exclusive.',[2])
    add(1,'打开订阅管理或续费方案流程',B('br'),
        'Choose the source-defined compare/manage/renew/external-store action and billing-schedule/annual-offer/keep-saving dialog context from subscription and experiment conditions.',
        'Imported pricing, cadence and store workflows remain explicit delegated families; an opened dialog is not a completed plan or cadence change.',
        'Check action and dialog reason under store-origin, plan/cadence and offer-eligibility combinations.',
        'Disable offer or destination availability and verify fallback without changing subscription state.',
        'Verify the destination/provider and resulting subscription state in its own authorized workflow; this contract covers handoff policy.',[2])
    add(1,'授权订阅的周期性付款',B('cr','lr','nr'),
        'Fetch mandate status, open confirmation, refetch before confirmation and compare displayed terms/payment identity with fresh terms. Delegate bank/Stripe confirmation, then verify server status and clean redirect parameters.',
        'Changed terms require renewed confirmation; missing secrets/keys/terms, provider failure, unmount and account changes cannot be treated as authorization. awaiting_stripe_migration differs from verified.',
        'Check not_required/requires_confirmation/requires_action/verified/migration status and redirect cleanup while preserving other URL state.',
        'Change each mandate identity/term between display and preflight; verify rejection of stale consent and in-flight duplicate guard.',
        'Verify real bank/provider/server sequence only with separately authorized fixtures; no mandate or financial request was sent.',[2])
    add(1,'查看个人余额并进入兑换页面',B('Gr'),
        'Read wallet balance and pricing eligibility, distinguish unavailable results, and navigate to /redeem?entry_point=billing from the balance section.',
        'Balance/pricing fetch errors and wallet eligibility stay separate. Redemption destination is delegated and navigation does not redeem value.',
        'Inspect balance/eligibility presentation and exact redemption entry query.',
        'Exercise unavailable balance and pricing failure without interpreting unknown as zero or reporting redemption success.',
        'Verify wallet/pricing providers and the separate redemption page; preserve shared credits/checkout dependencies.',[2])
    add(1,'浏览账单交易记录与发票',B('Lr','zr','Vr','Br','Mr'),
        'Load four recent rows and expose complete history only with a next cursor; full history uses ten-row pages and a cursor stack. Invoice rows with a URL open the invoice; wallet rows do not invent invoice links.',
        'Block next/previous while fetching, keep empty/error/loading distinct and preserve return-to-billing state. Data is refetched on mount/focus/reconnect with no retained query cache.',
        'Check recent/full history, forward/back cursor navigation, invoice URLs and return action.',
        'Exercise missing cursor, zero rows, error and in-flight pagination; missing invoice URL must not become an actionable invoice.',
        'Verify account_id/limit/cursor and abort signal at the real transaction receiver and browser adapter.',[2])
    add(1,'查看和编辑账单资料及税号',B('qn','Jn','Xn'),
        'Read email/name/address/tax information, open the editor with current account data, preserve secure-form validation and return focus to the edit control on close.',
        'No available profile hides the summary; loading/error/retry differ. Tax type/provider validation and save result remain receiver-specific; dismissal is not save success.',
        'Open and edit the source-supported billing fields and inspect account-bound submission plus restored focus.',
        'Exercise absent profile, query failure, invalid tax/address and save failure without false success.',
        'Verify billing-information endpoints and secure-form/tax adapters, persisted profile and refreshed invoice information.',[2])
    add(1,'添加或编辑已保存的付款方式',B('mr'),
        'Open shared add/edit payment components from the selected account list, preserve method identity and already_saved outcome, refresh shared billing queries on success and restore action focus.',
        'Imported payment forms/provider controls are retained delegated families. Closing or already_saved feedback is distinct from creating another payment method.',
        'Exercise add/edit and already-saved results, account identity and action-menu focus recovery.',
        'Fail provider/save or close the editor; do not mutate the saved list without a verified success result.',
        'Verify package/provider boundaries and shared payment refresh subscribers; do not copy Stripe/UI implementations into restored source.',[2])
    add(1,'设置默认付款方式',B('mr'),
        'For an eligible non-default non-custom method, post account_id and payment_method_id to the default endpoint and refresh billing queries on success.',
        'Block concurrent list mutations; unsupported/default methods omit the action. Remote failure is not a successful local default change.',
        'Select an eligible method and inspect exact default action payload and subsequent refresh.',
        'Check custom/already-default methods, pending duplicate action and rejected request.',
        'Verify actual default-method response and account-scoped list refresh before declaring persistence.',[2])
    add(1,'设置付款方式备用扣款开关',B('mr'),
        'Send the account-scoped enabled value to the backup-payment endpoint and refresh billing data after successful mutation.',
        'Eligibility, unresolved auto-reload data and pending mutation guards remain; submission is not permission to perform live financial tests.',
        'Toggle each source-supported backup state and inspect account_id/enabled.',
        'Exercise unavailable/disabled control and mutation failure without assuming a persisted toggle.',
        'Verify saved backup policy and its account/provider consumer in a dedicated authorized environment.',[2])
    add(1,'移除不再需要的付款方式',B('mr'),
        'Before removal, refetch both payment methods and auto-reload state, locate the method and apply required-by-billing validation; only then delete by method ID with account_id.',
        'Stale/missing method, refetch failure or unresolved/required auto-reload/default dependency rejects deletion. Other completed effects are not rolled back by closing the menu.',
        'Remove an eligible method after fresh dependency checks and verify list refresh and focus.',
        'Make method/default/auto-reload requirements change during refetch; verify deletion is prevented.',
        'Verify fresh payment/auto-reload providers, actual delete result and all remaining consumer dependencies.',[2])
    add(1,'打开取消订阅及挽留确认流程',B('xr','Zr'),
        'Choose the applicable retention prompt or lazy cancellation dialog keyed by subscription identity, then pass the current account and close callback.',
        'Cancellation/retention implementation is a retained delegated family; opening/closing it must not count as a cancelled subscription.',
        'Vary retention availability and subscription identity; inspect the selected handoff and dialog lifecycle.',
        'Fail lazy loading or dismiss the prompt; verify no completed cancellation is claimed.',
        'Verify the full cancellation provider and final subscription state in its dedicated authorized test, including shared pricing/payment consumers.',[2])

    add(2,'浏览团队列表并进入团队页面',T('Br','Vr','Ur'),
        'Require account identity, load account-scoped teams and open encoded team paths. join suffix normalizes to the same detail route with join=true while preserving query/hash/state.',
        'Unavailable errors take precedence over loading; loading/error/empty differ. List navigation is not a membership change.',
        'Open teams with encoded IDs and join URLs; inspect preserved URL state and list/detail identities.',
        'Exercise absent account, unavailable permission, pending data and retryable errors.',
        'Verify real team-list/detail providers and selected product mode; route reachability alone is not mode classification.',[3])
    add(2,'打开团队创建流程并承接保存结果',T('Vr'),
        'Consult team-creation policy again at click time, open the shared setup dialog, and after successful save navigate to encoded team shared tab and invoke setup continuation.',
        'Tooltip/aria-disabled styling alone is not the guard; handler checks policy. Dialog validation/create endpoint are retained delegated families.',
        'Change creation policy between render and click; confirm only permitted creation handoff and saved-team navigation.',
        'Deny policy, cancel or fail creation; no saved identity/navigation should be invented.',
        'Verify shared setup/create provider and post-save continuation with a dedicated synthetic workspace.',[3])
    add(2,'切换团队面板并筛选共享资源',T('Hr'),
        'Normalize members alias to settings, shared to no tab query, and preserve other query/hash/state. Apply source availability fallback for task/space/computer resource filters and forward search to the lazy resource page.',
        'Nonmembers see preview/member information but not shared/activity content. The compiled service-account tab body is null; do not invent an editor. Resource actions remain delegated.',
        'Exercise tab aliases, membership and feature gates, resource filters and search handoff.',
        'Use unavailable tabs/resource categories and a nonmember account; verify fallback and restricted content.',
        'Verify shared-resource/task/space consumers separately, including backend authorization rather than relying on UI membership.',[3])
    add(2,'编辑团队名称或描述',T('Hr','_r'),
        'Members receive inline edit controls; trim fields, require a nonempty name, skip unchanged values, prevent duplicate save and mutate only the selected field. Escape/cancel discards draft; closing normally submits.',
        '409 name conflict and403 permission errors differ from generic save failure; retain failed draft. Frontend membership affordance does not prove backend write permission.',
        'Edit name/description, submit/close, and verify trimmed field-specific payload and200/2000-character inputs.',
        'Exercise empty name, unchanged field, in-flight duplicate,409/403 and Escape/cancel without false save.',
        'Verify real team update receiver, authorization, query refresh and persisted value.',[3])
    add(2,'选择团队头像',T('Hr'),
        'Forward the chosen avatar with account/team identity through the shared team-avatar action from a manageable team header.',
        'Picker/update implementation and error/cancel semantics are retained imported boundaries; opening the picker is not a durable avatar change.',
        'Inspect account/team/avatar parameters and eligible header affordance.',
        'Exercise denied membership and picker/update failure without claiming a saved avatar.',
        'Verify shared avatar adapter, backend access checks and refreshed team presentation.',[3])
    add(2,'浏览和搜索团队成员',T('jr','Mr','Pr'),
        'Load account/team members, filter the default service-account user identity, search display name/email/principal/current-user email, and preserve user/service/group row identities.',
        'Unavailable/error/loading/empty/no-search-match differ. Membership load errors must not establish write/manage permission.',
        'Search names/emails/IDs, verify hidden default service account and visible eligible principals.',
        'Exercise initial error, stale selection/member disappeared and no matches without inventing membership.',
        'Verify actual member provider and privacy/permission boundaries; synthetic filtering proves only the selected predicate.',[3])
    add(2,'打开邀请团队成员流程',T('Ar','Nr'),
        'Open the shared invite dialog under management and pending-mutation guards, forwarding account/team identity and reset copy-failure state.',
        'Invitation validation/search/send endpoint remain delegated; opening the dialog does not send an invitation.',
        'Inspect eligible invite action and dialog parameters for the current team.',
        'Exercise pending mutation, denied management and dialog cancellation without reporting an invitation sent.',
        'Verify imported member dialog and actual invitation receiver only under separate authorized synthetic fixtures.',[3])
    add(2,'复制团队加入链接',T('Nr'),
        'Generate the shared join URL from team identity; clipboard success shows copied feedback, false result opens the invite dialog with initialCopyFailed=true.',
        'A false clipboard result is a fallback, not success. URL generator/clipboard implementation and thrown promise rejection remain imported boundaries.',
        'Check copied URL and success toast versus false-result dialog fallback.',
        'Return false from clipboard and close the fallback; do not claim the clipboard changed.',
        'Verify actual URL generator/browser origin and clipboard permissions without exposing a real team invitation.',[3])
    add(2,'从加入链接打开团队加入确认',T('Br','Hr'),
        'After join-route normalization, a nonmember with known user and loaded membership data may receive the lazy join confirmation. Existing membership takes the normal member path.',
        'Preview gating/availability and a source flag affect the join prompt. Join dialog/server mutation remain retained delegated families.',
        'Inspect join=true with member/nonmember/loading identity combinations and preserved route state.',
        'Fail membership query or omit user identity; do not expose join confirmation prematurely or assume successful membership.',
        'Verify lazy join provider and subsequent membership/access refresh in a dedicated authorized environment.',[3])
    add(2,'退出团队或移除成员',T('jr','Fr'),
        'Resolve fresh selected member and role guards. Remove/leave normally dispatches membership action remove; for the last member the confirmation instead dispatches team deletion. Self exit or deletion invokes onTeamExited.',
        'Owner with other members must transfer ownership before leaving; another owner cannot be removed. Missing member/permission errors prevent submission. Last-member confirmation must disclose deletion.',
        'Check self/other, last/multiple, owner/member and selected-member disappearance; inspect removal versus deletion dispatch.',
        'Deny invalid owner exit/removal or stale member and verify validation; failed request must not navigate as success.',
        'Verify actual membership/delete APIs, remaining access through other memberships and persisted team state.',[3])
    add(2,'转移团队所有权',T('jr','Tr'),
        'Under the source feature flag, current owner may choose another human non-service user; confirm transfer action principalId. Current owner becomes a member and inaccessible shared connections may be disabled.',
        'Exclude self/non-user/service-account targets; imported mutation/error handling and actual shared-connection side effects remain backend boundaries.',
        'Check target eligibility and exact transfer action, account/team and principal identity.',
        'Exercise missing permission, mutation pending/error and cancelled confirmation without claiming changed ownership.',
        'Verify persisted roles and connection access changes with separately authorized synthetic membership.',[3])
    add(2,'删除本人拥有的团队',T('Hr'),
        'Expose the shared delete-team dialog only to a current member who is owner; pass canDelete and onDeleted navigation back to the list.',
        'Deletion dialog/API is imported; pending/permission/error/cancellation remain dedicated validation. Membership alone does not permit this delete control.',
        'Compare owner/member/nonmember and inspect dialog identity plus success navigation contract.',
        'Deny nonowner deletion and dismiss/fail confirmation without claiming the team is gone.',
        'Verify actual delete receiver, authorization and persisted removal; relate its endpoint to last-member exit without merging user intents.',[3])
    add(2,'浏览并继续搜索团队活动历史',T('An','gn','assignment-xn'),
        'Under activity availability, filter known loaded events and text, group by localized date, and load older pages in batches of at most five until new matching data, error or exhaustion.',
        'No matches in loaded history does not mean all history is empty. Loading guard prevents duplicate fetch; unmount stops follow-up state, and no-match-with-more retains the continue action.',
        'Check loaded search, date groups, five-page batch bound and resume search with older pages.',
        'Exercise unavailable activity, page error, no new matches, exhausted cursor and unmount without claiming global search completion.',
        'Verify actual activity pagination provider and known-event formatting; synthetic callback tests do not establish complete history.',[3,4])
    return result
