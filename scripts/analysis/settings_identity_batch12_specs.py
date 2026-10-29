"""Bound account identity and legal actions separately from extension policy."""


def specifications():
    result = []
    def add(page, name, units, effect, failure, behavior, negative, receiver, support):
        result.append(dict(pageIndex=page, name=name, units=units, effect=effect,
                           failureAndCancellation=failure, acceptance=[behavior, negative, receiver], support=support))
    A = lambda *names: [('agreements', n) for n in names]
    C = lambda *names: [('account', n) for n in names]
    E = lambda *names: [('extension', n) for n in names]
    add(0, '查看工作区服务协议及 BAA 状态与说明',
        A('V', 'H', 'W', 'U', 'assignment-J', 'assignment-Y', 'assignment-X') + [('agreements-access', 'assignment-f')],
        'Under account access, selected account, account-query and imported eligible-plan guards, read workspace agreements metadata. Always show the service-agreement link; show BAA only for the HIPAA workspace flag, including signed/timestamp state and external document/help links.',
        'Loading, denied, account-query error and metadata error are distinct. Stale metadata may remain visible beside retry; signed falls back to timestamp only when signed is nullish. Invalid timestamp text is retained rather than invented.',
        'Inspect eligibility, account-specific headers/query key, HIPAA gate and external destinations; distinguish explicit signed:false from timestamp fallback.',
        'Use missing account, ineligible plan, denied access, loading/error and invalid timestamps; do not expose signing for other workspaces or count opening a link as accepting terms.',
        'Verify actual account policy, agreement metadata and external document navigation without implying any legal acceptance.', [0, 1])
    add(0, '确认签署当前工作区 BAA', A('H'),
        'For an unsigned HIPAA workspace, Agree posts /quorum/workspace/{account_id}/sign_baa using the selected workspace/account headers; success merges signed:true and returned timestamp, then invalidates the exact metadata query.',
        'Pending disables the Agree control; failure displays the sign error and permits retry. The selected callback has no extra confirmation dialog. Signing is a legal/account service action, never a navigation effect.',
        'Inspect unsigned/HIPAA/pending UI gates, selected account path and headers, cache merge and invalidation order.',
        'Use signed/non-HIPAA/pending/error state and a rejected stub request; preserve metadata and error feedback without claiming acceptance.',
        'Verify a separately authorized real signing flow, server permission and authoritative metadata; this analysis executes synthetic substitutes only.', [0, 1])
    add(1, '查看账户套餐、资料及只读构建者信息', C('gn', 'vn', 'xn', 'assignment-xn'),
        'Display planAtLogin and current-user data; query /profiles/me and show builder profile only when viewer_access.can_edit. Its selected display row has control:null. Preserve the chatgpt.cme-gated imported manager and the shared age row as delegated consumers.',
        'Missing current-user data disables dependent controls. The builder can_edit flag gates read-only presentation here and does not establish an editor. Lazy manager and age implementations retain separate ownership.',
        'Inspect profile endpoint, current-user and auth queries, builder visibility/read-only row and imported manager/age boundaries.',
        'Remove current user, profile eligibility or capability; no invented builder edit, independent logout button or duplicate age implementation.',
        'Verify actual account/profile providers and separately owned imported manager; reuse FSC-0199/FSC-0200 for age rather than duplicating goals.', [2, 3])
    add(1, '保存账户显示名称', C('gn', '_n'),
        'Keep a local name draft and PATCH /accounts/users/name with {name}. On success invalidate chatgpt-current-user; clear the draft only if it still equals the submitted value.',
        'Missing current user, null draft and pending disable Save. Failure raises the account-update toast; typing a newer draft during a request must not lose that draft on success.',
        'Inspect exact patch payload, Save/input disabled conditions and matching-versus-newer draft clearing.',
        'Use missing user, pending, failed patch and edits made during the request; no false success or lost newer text.',
        'Verify current-user service identity, authoritative refresh and downstream display-name consumers.', [2])
    add(1, '查看用户名并打开委托编辑器', C('un', 'mn', 'assignment-mn'),
        'Read /wham/profiles/me using account headers and account/user-scoped query and mutation keys. Trim username for @handle presentation; Add/edit opens the imported username editor with identity and initial value.',
        'Missing identity disables the query; pending or a matching active mutation disables the row. Query error changes the row action to refetch rather than opening the editor; expected errors include403/404.',
        'Inspect scoped keys, query enablement/header/signal, trimmed empty value, retry action and editor props.',
        'Use empty/error/pending/missing identity and a matching active mutation; no invented username-save endpoint or successful edit from opening a dialog.',
        'Recover and verify the delegated username editor, validation, service identity and resulting profile refresh.', [2, 3])
    add(1, '通过外部账户设置添加或更改邮件', C('nn', 'rn'),
        'Query change-email eligibility for the selected user/account. When eligible, Add/Change routes to https://chatgpt.com/#settings/Account through the external-browser bridge. The selected root fixes auth0ClientId to null.',
        'Because that client ID is null, this root disables the local reauth query and never mounts the local email/OTP modal. Retained dormant helpers are not additional reachable local email operations. Pending disables the visible action.',
        'Inspect eligibility and external bridge event/target; render the root and verify the local reauth query is disabled and its local editor absent.',
        'Deny eligibility, omit current-user data or use pending state; no local begin/OTP call from the visible action and no email-change success claim.',
        'Verify external account navigation and service eligibility separately; classify actual product consumers before exclusion.', [2, 3])
    add(1, '确认永久删除个人账户', C('gn', 'Dt', 'Rt', 'kt', 'Ct', 'At'),
        'Only a loaded personal account with matching user/account may open confirmation. Require recent token, subscription query loaded, exact trimmed keyword and case-insensitive contact match; recheck token on submit. POST /accounts/deactivate with acquired risk headers, then delegate logout/navigation.',
        'Pending suppresses repeat submit. Close/unmount aborts refresh; stale-login errors clear fields and start refresh. Reauth validates user/account/nonce/age and password-auth time. Organization-managed and sole-business-owner errors remain distinct. This is account-wide service deletion, not local project/thread cleanup.',
        'Inspect personal identity/dialog guards, exact confirmation conditions, token recheck, deactivate headers/order, reauth return and error policy.',
        'Cancel/unmount, mismatch contact/keyword, expire token, reject header acquisition/request or return stale/org/owner errors; do not imply a UI callback proves deletion or subscription cancellation.',
        'Verify separately authorized destructive service behavior, identity, external refresh, logout and durable result; no real deletion is performed by this analysis.', [2, 4, 5])
    add(2, '设置扩展的默认站点、下载和上传审批方式', E('Me', 'Ee', 'assignment-W', 'assignment-U'),
        'Project saved approval modes into the shared Chrome site-permission manager. For origin/download/upload, map neverAsk to never_ask and the other supported selection to always_ask; send expected_revision and the resource-specific preference field.',
        'The shared manager retains enterprise policy and disabled state; the callback is not a substitute for its supported-value validation. All writes retain captured identity, no retry and revision conflict handling.',
        'Inspect the three supported resource mappings, preference projection, expected_revision and manager capability props.',
        'Use managed/disabled/mutation-pending and revision conflict; do not claim unsupported full-CDP per-site/default approval edits.',
        'Verify shared permission manager, policy and real extension consumer against the server revision result.', [6, 7])
    add(2, '设置或移除扩展的各站点权限规则', E('Me', 'Ee', 'De', 'assignment-G'),
        'For origin/download/upload/webMcp, encode allow/deny/default as allow/deny/null rule_updates with expected_revision; map webMcp to webmcp. Removal clears existing rules, absent default is a no-op, fullCdp resource is skipped, and explicit ask throws.',
        'The local pattern validator checks nonempty, at most4096 Unicode code points and no whitespace/control; it does not normalize or validate URL schemes. Manager dialog/policy remains delegated. Failed writes invalidate the scoped query.',
        'Inspect rule projection, supported resource mapping, remove/no-op behavior, revision and exact validator boundary.',
        'Supply ask, only fullCdp, absent defaults, whitespace/control or4097 code points; no empty patch, unsupported per-site CDP action or invented URL allowlist.',
        'Verify manager add/edit/remove UI and authoritative rule effects in an actual extension session.', [6, 7])
    add(2, '设置扩展历史访问权限', E('Me', 'Ae', 'assignment-je'),
        'Render never_ask/always_ask/disabled choices and PATCH history_approval_mode with expected_revision. Enterprise extension/history permission and allow-never-ask checks determine managed state, disabled option and effective displayed value.',
        'Denied history projects disabled; a saved never_ask becomes always_ask when never-ask is disallowed. Query/mutation fetching disables changes; menu also disables managed controls. Conflict receives dedicated feedback without automatic retry.',
        'Inspect policy combinations, effective fallback, disabled option and exact revision/identity payload.',
        'Deny history/never-ask, use pending or409 conflict; no automatic reapplication of a rejected edit.',
        'Verify actual workspace bundle normalization, history policy and extension-side access behavior.', [6, 7])
    add(2, '设置扩展默认网站工具许可', E('Me', 'Ee', 'Ne', 'Pe'),
        'Default webmcp_enabled to true and update it with expected_revision. Preserve the shared manager callback for the same preference and the external help link; saved per-site rules remain separate.',
        'Identity/query loading and mutation pending disable edits; failed mutation invalidates the scoped query. This changes the default website-tool preference, not installation or connection status.',
        'Inspect both control consumers, default checked state, boolean payload/revision and external help navigation.',
        'Use identity mismatch, pending, failure or a per-site override; do not overwrite rules or claim an extension installation.',
        'Verify browser service, WebMCP/site tools consumer and rule/default precedence.', [6, 7])
    add(2, '设置扩展全局完整 CDP 访问', E('Me', 'Ee'),
        'With extension policy allowed and browser_use_full_cdp_access not false, display the saved global full_cdp_access_enabled (default false), risk warning and revision-based toggle. Managed denial forces unchecked/disabled state.',
        'The shared site editor receives isFullCdpAccessEnabled:false and its update callback skips fullCdp resources; do not infer per-site full-CDP editing from projected rule lists. Query/mutation pending disables the global control.',
        'Inspect policy and default/checked/disabled state plus exact global preference payload and revision.',
        'Deny extension/full-CDP policy, use pending or conflict and attempt fullCdp-only rules; no unsupported per-site CDP patch.',
        'Verify independently authorized real extension capability and effective CDP access against enterprise policy.', [6, 7])
    return result


def configuration():
    return dict(number=12, work='settings-identity-batch12-work', previousScope=18, previousCoverage=9,
        expectedState='2026-10-24T11:58:16.139695+00:00',
        selections=['agreements', 'account', 'extension', 'agreements-access'],
        scriptFiles=['settings_identity_batch12_specs.py', 'probe_settings_identity_batch12.cjs'],
        previousGoalTurnClassification='no progress: preceding turn only inspected status and explained the stall; this batch resumes the existing finite queue.',
        priorProbeAttempts=[dict(observations='probe-attempt-01.json', probeScript='probe-attempt-01.cjs',
            disposition='27 passed; two deletion-root fixture cases lacked the Ot help-link renderer. Injected the exact selected Ot function; frozen source unchanged.')],
        executionArtifacts=['probe-attempt-01.cjs', 'probe-attempt-01.json', 'probe-attempt-01-stdout.txt',
            'probe-attempt-01-stderr.txt', 'probe-attempt-01-receipt.json', 'probe-attempt-02.cjs', 'probe-attempt-02.json',
            'probe-attempt-02-stdout.txt', 'probe-attempt-02-stderr.txt', 'probe-attempt-02-receipt.json'],
        entries=[('agreements', 'Agreements', 'T37'), ('account', 'Account', 'T38'), ('extension', 'Extension', 'T39')],
        sharedGoalConsumers=[dict(pageIndex=1, featureIds=['FSC-0199', 'FSC-0200'],
            relation='Account embeds the age-settings t export as gt. Retain the existing age status/verification owners; this entry alone does not prove full route equivalence.',
            units=[('account', 'gn')], acceptance='Verify the delegated age row and navigation against the existing age contracts; do not duplicate age status/verification goals.')],
        mechanisms=[
            ('Agreement access eligibility', 'Shared access, selected account query, plan predicate and HIPAA flag are independent guards; access family is not product-mode membership.', [('agreements-access', 'assignment-f'), ('agreements', 'V')]),
            ('Agreement metadata and signing cache', 'Separate readonly external links from legal signing; preserve account headers, signed fallback, error/retry and exact cache merge/invalidation.', [('agreements', 'H'), ('agreements', 'W'), ('agreements', 'U')]),
            ('Account query, current-user draft and personal identity', 'Keep auth/current-user/profile queries, user/account keys, draft-preserving success and personal-account dialog gating.', [('account', 'gn'), ('account', '_n'), ('account', 'vn')]),
            ('Account delegated identity controls', 'Username editor, age row and capability-gated CME manager remain separate consumers. Null email client ID selects the external action and disables local email modal/reauth.', [('account', 'gn'), ('account', 'un'), ('account', 'nn'), ('account', 'rn')]),
            ('Deletion recent-login and reauth return', 'Preserve token-age predicate including missing issuedAt behavior, single-use pending state, nonce/identity/age and seconds-versus-milliseconds password-auth time.', [('account', 'kt'), ('account', 'Rt'), ('account', 'assignment-Ut'), ('account', 'assignment-Wt')]),
            ('Deletion confirmation, risk headers and lifecycle', 'Keep confirmation inputs, submit-time freshness, refresh abort, header fallback, deactivate ordering and stale/organization/owner error distinctions.', [('account', 'Dt'), ('account', 'Ct'), ('account', 'At')]),
            ('Extension identity, query and revision writer', 'Use captured expectedIdentity and user/account query keys, no retries, cancel/set/event on success and invalidation/rethrow on failure;409 is a dedicated conflict.', [('extension', 'Me'), ('extension', 'assignment-Oe'), ('extension', 'assignment-ke')]),
            ('Extension permission and enterprise projection', 'Preserve manager capability props, supported resource mappings, Unicode pattern boundary and distinct history/full-CDP policy projection.', [('extension', 'Ee'), ('extension', 'Me'), ('extension', 'Ae'), ('extension', 'De')])],
        gaps=[
            ['Imported eligible-plan predicate and actual account/HIPAA policy, metadata, signature service and external browser bridge remain interfaces.', 'Actual product-mode consumers, legal action authorization and authoritative signing result remain unverified.'],
            ['Current-user/profile, username editor, shared age/CME manager, external email bridge, session/risk SDK and account deactivation services remain assigned interfaces.', 'Actual account/identity changes, delegated manager behavior, external refresh/logout, destructive result and mode/shared ownership remain unverified.'],
            ['Shared permission-manager dialogs, workspace bundle normalization/policy, browser settings service and extension consumers remain assigned interfaces.', 'Actual extension session, policy, revision conflict, per-site/default precedence and selected product consumers remain unverified.']],
        modules=['agreements/settings', 'account/settings', 'browser-extension/settings'],
        consumers=[['app/account-access', 'account/agreement-metadata', 'account/workspace-signature', 'app/external-browser'],
            ['app/account-access', 'account/current-user-profile', 'account/username-editor', 'account/age', 'account/shared-managers', 'account/external-email', 'account/deletion-reauth', 'app/session'],
            ['app/account-access', 'browser/permission-manager', 'browser/enterprise-policy', 'browser/settings-service', 'browser/extension-consumer']],
        dependencies=[['React/UI/query/state packages', 'account/plan/agreement/signature services', 'external browser bridge'],
            ['React/UI/query/state packages', 'account/profile/username/deactivation services', 'shared age/CME and email/session bridges', 'reauth/risk-header providers'],
            ['React/UI/query/state packages', 'browser permission manager and enterprise policy', 'browser settings/config services', 'external browser extension']],
        decisions=['Separate legal document reading from explicit workspace signing and scoped metadata state.',
            'Separate current-user/profile, delegated identity editors and personal-account deletion; preserve external email route and shared age ownership.',
            'Recover browser permission policy editing with revision/identity and enterprise guards; do not invent installation or connection controls.'],
        title='协议、账户与扩展：区分法律操作、账户身份及浏览器权限策略',
        modeReason='All three settings entries have chatGpt access, whose shared publisher is already qualified. Authentication/access naming does not establish exclusive product mode, so no whole-page exclusion is made.',
        firstParty=['workspace agreement/signing orchestration', 'account draft and identity UI', 'personal deletion/reauth lifecycle policy', 'extension permission/revision/cache orchestration'],
        externalize=['React/UI/query/state packages', 'account and legal service implementations', 'delegated username/age/CME managers', 'auth/session/risk providers', 'browser policy/permission manager and extension service'],
        probeDescription='仅执行冻结源码函数、回调和根组件，使用合成身份、查询、UI与服务替身；未接受真实协议、删除账户、更改权限或调用模型服务',
        modeSummary='沿用共享账户访问边界；账户年龄入口复用FSC-0199/FSC-0200。用户名与CME管理器保留委托，邮件本地流程不可由当前按钮触达。',
        boundarySummary='协议链接与签署、账户删除与本地数据清理、全局CDP与站点规则分别验收；扩展页没有安装或连接操作。',
        reportFacts='明确BAA签署/缓存、账户邮件外部路径与删除确认、扩展expected_revision/身份和企业策略；年龄功能复用已有归属。',
        summaryPoints=[
            'Agreements将服务协议/BAA文档导航与签署分开；签署只在未签署HIPAA工作区展示，提交后合并时间戳并刷新该工作区元数据。',
            'Account保存姓名时保留请求期间的新草稿；用户名打开委托编辑器，builder profile所选行只读，年龄复用已有功能。',
            '当前邮件根组件把auth0ClientId固定为null：可见Add/Change打开外部账户设置，本地reauth查询及邮件/OTP弹窗没有被该路径启用。',
            '个人账户删除保留身份、近期登录、确认文字/联系方式、提交时重查、刷新取消及错误区分；风险头获取有回退，失败可能返回空头，并非强制终止请求。',
            'Extension管理审批默认、站点规则、历史、网站工具和全局CDP；保存带身份和expected_revision，冲突不自动重试。站点回调跳过fullCdp，拒绝显式ask，校验器不做URL规范化。'],
        nextQualification='Continue storage/security/parental-controls from saved dispositions. Reuse closed access publication and existing age ownership. Legal/account/extension services, delegated managers, actual mode and runtime acceptance remain local integration requirements. No model authorization remains.')
