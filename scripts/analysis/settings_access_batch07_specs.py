"""Age, saved credential and cloud-computer source contracts."""
def specifications():
    result=[]
    def add(page,name,units,effect,failure,behavior,negative,receiver,support):
        result.append(dict(pageIndex=page,name=name,units=units,effect=effect,
            failureAndCancellation=failure,acceptance=[behavior,negative,receiver],support=support))
    A=lambda *n:[('age',x) for x in n]
    P=lambda *n:[('passwords',x) for x in n]
    C=lambda *n:[('cloud-computer',x) for x in n]
    add(0,'查看年龄状态与相关说明',A('Te','Y','J','Ee','Ae'),
        'Under the source access selector, present teen/unsure/fallback loading-error state and eligible verification control. Back replaces /settings/account#age; help destinations differ for teen and unknown-age explanations.',
        'Denied access redirects to account settings; query failure does not establish an age group. Age normalization/provider remains imported.',
        'Vary access, age group and canVerifyAge; inspect back route, fallback/error and help destinations.',
        'Fail or delay status loading and retry without labeling an unknown age as adult/teen or confirmed.',
        'Verify actual account/age provider and product-mode conditions; wording and export name do not prove all shared age services are exclusive.',[0])
    add(0,'发起年龄验证或刷新验证状态',A('U','Ce','assignment-z'),
        'Get a settings-scoped verification controller; require matching account/user/auth/eligibility/current-account identity before start. Reuse controller and watch identity/eligibility changes to dispose/reset. UI retry uses phase retry when present, otherwise start.',
        'loading/active/refreshing disable action. pending/redirect/refresh-error offer authoritative readback rather than assuming success or submitting another inquiry. Provider controller and authoritative readback remain delegated.',
        'Inspect settings entry context, identity guard, phase labels and retry versus new-start action.',
        'Change account/user/auth/eligibility during a verification attempt; verify disposal and idle reset. Provider completion without authoritative evidence must remain pending.',
        'Verify provider lifecycle, callbacks, authoritative account readback and durable age state in a separately authorized synthetic flow.',[0])
    add(1,'浏览和搜索已保存密码的元数据',P('qe','Je','Ue','Ye','ze','assignment-Ge'),
        'Wait for account/user identity, fetch cursor pages with expectedIdentity and account header, search loaded origin/account_label and show metadata details. Schema contains credential_id/origin/account_label/created_at, not plaintext password; count is total only after all pages.',
        'No query retry/cache retention; load errors, empty data and no loaded match differ. More pages require load-more before search can cover the rest. Metadata surfaces carry privacy masking.',
        'Check account-scoped query, cursor pagination, loaded-only search and origin/masked account/created-at details.',
        'Fail loading or change identity; do not infer no saved passwords from an error or a partial search. Do not add a plaintext reveal feature absent from source.',
        'Verify saved-credential provider, schema/identity enforcement, privacy and no-retained-cache behavior without reading real saved credentials.',[1])
    add(1,'确认删除已保存的网站密码',P('Je','We','Be'),
        'Confirm the selected credential identity, block duplicate pending deletion, issue account/user-bound delete without retry and require deleted response validation. Success clears selection and refetches list.',
        'Uncertain delete/list results show reconciliation error and refresh; refresh does not retry deletion. Deleting stored credentials does not sign out an existing website session.',
        'Inspect confirmation identity, credential path, account header, expectedIdentity and nonretry policy; verify successful refresh.',
        'Fail/lose response or close confirmation; verify uncertain-state messaging and no automatic delete retry.',
        'Verify real delete/status/list reconciliation only with dedicated synthetic credential records; current probes use synthetic receivers.',[1])
    add(1,'查看并刷新 1Password 连接状态',P('Ne','Pe'),
        'Under feature flag, key status by user/account; suppress query/actions when callback workspace differs. connecting polls every1500ms except unconfirmed callback. Clean callback parameters only after confirmed connected readback or successful disconnect.',
        'Unavailable, unknown, connecting, failed/reconnect_required and unconfirmed callback differ. Error means unconfirmed operation; closing authorization browser is not connection success.',
        'Check account/user binding, workspace mismatch, polling and connected/disconnected callback cleanup preserving other URL state.',
        'Exercise 403/404/503, missing identity and unconfirmed callback; retain manual workspace switching and refresh without false success.',
        'Verify real status provider and callback validation separately from saved-password storage and provider OAuth.',[1,2])
    add(1,'连接或重新连接 1Password',P('Pe','Fe'),
        'After identity/availability checks, request enrollment with expected_account_user_id and never retry. Accept only three exact HTTPS origins with /oauth/authorize. Use provided tab or external browser; tab path clears sessionStorage and adds no-referrer metadata before replacement.',
        'Null/closed tab, missing identity or invalid destination rejects and closes the provided tab. Enrollment URL/navigation is not a persisted connection; refetch authoritative status on settled.',
        'Inspect enrollment identity/payload, allowed destination, tab preparation and status reconciliation.',
        'Reject unexpected scheme/host/path, closed tab and failed enrollment with no navigation to an unvalidated destination.',
        'Verify provider OAuth/backend callback and persisted connection only under separate authorization; synthetic allowlist tests never contact 1Password.',[2])
    add(1,'断开 1Password 连接',P('Pe'),
        'Confirm disconnect and send identity/account-bound delete with retry never; refetch connection status on settled and clean callback query only after confirmed outcome.',
        'Network/response error remains unconfirmed and requires refresh. Disconnecting provider access does not imply deletion of all saved-password records or website logout.',
        'Inspect confirmation, account header, expectedIdentity, nonretry policy and subsequent status refresh.',
        'Cancel or fail disconnect; verify no false disconnected state and preserve refresh reconciliation.',
        'Verify actual provider connection revocation and independent stored-credential/session effects with synthetic fixtures.',[2])
    add(2,'设置云电脑默认网站审批方式',C('Et','Dt','kt','Ot','assignment-Mt'),
        'Fetch config per account-user identity and serialize mutations per query scope. Map always_ask to always_ask/disable_auto_review:true, auto_approve to always_ask/false, always_allow to never_ask/true. Update cache from successful response.',
        'Disable controls until data available or while mutation pending; loading/unavailable labels differ. OnePassword callback query redirects to passwords while preserving spread location fields; no separate Navigate state prop is supplied.',
        'Check all three visible choices and exact two-field patches, current config mapping and callback redirect.',
        'Fail config or mutation and check dedicated error state; do not treat request submission as persisted permission.',
        'Verify config receiver, account binding, actual approval consumer and persistent effect, separately from Codex local approval configuration.',[3])
    add(2,'添加修改或移除网站专属权限',C('Dt','ht','gt','dt','Ot'),
        'Normalize and validate a site/pattern through the shared parser; add/update sends canonicalPattern and selected decision as origin_mutation, remove sends decision unset. Pending dialog cannot close/reset draft or resubmit.',
        'Nonempty invalid/overlength input is rejected. Add failure remains in dialog rather than duplicate toast; successful addition closes. Shared pattern parser/schema remains a dependency boundary.',
        'Check missing scheme/default HTTPS, trailing slash handling, canonical pattern and update/remove payloads.',
        'Exercise invalid/overlength patterns, pending close/submission and rejected patch while retaining error/draft.',
        'Verify the real pattern parser, origin matching/precedence and config persistence; normalization tests do not validate backend pattern semantics.',[3])
    add(2,'查看 Work 或 dot 保存的网站 Cookie 元数据',C('Dt','Ye','st','at','Qe','$e'),
        'Work reads flora cookies by account-user key. dot uses Orbit surface plus account/user expectedIdentity and current-account checks before/after fetch, requires a target, and recognizes target-unavailable404 separately. Group host/count metadata by site with host expansion.',
        'Account mismatch/abort or absent target cannot present stale data as current. No dot found is different from query error or zero cookies. Imported grouping/domain rules and actual target acquisition remain delegated.',
        'Switch Work/dot views, inspect surface/account/user/target, site groups, individual hosts and cookie counts.',
        'Change identity while fetching, return target-unavailable404 or missing target, and verify specific unavailable/error states without leaking stale metadata.',
        'Verify real cookie providers, domain grouping and dot target ownership without reading personal cookie values.',[3,4])
    add(2,'确认清除网站或全部云电脑 Cookie',C('Ye','Xe','st','Qe','$e'),
        'Choose exact host, site including subdomains or all; confirm before mutation. Work deletes by host or agent/browser_context then filters/invalidate cache. dot first cancels queries and checks account/target, sending Orbit surface and captured target with nonretry policy.',
        'Changed identity or unavailable target aborts dot deletion. Failure keeps confirmation/error; success closes. Host-only deletion preserves child/sibling hosts; all clears the selected context, not arbitrary other targets.',
        'Check host/site/all payloads and confirmation text for Work versus dot; inspect subdomain cache filtering.',
        'Change account or target availability before mutation, fail delete or cancel confirmation; verify no wrong-context or duplicate operation.',
        'Verify actual deletion, target affinity, cache reconciliation and session impact only using separately authorized synthetic browser data.',[3,4])
    add(2,'查看已保存的云电脑 Passkey 元数据',C('Dt','bt','St'),
        'Render passkey section only when webauthn_enabled=true, query per account-user identity, show relying_party_id and user display/name with loading/error/empty/retry states.',
        'Feature disabled omits the section; missing/error data is not an empty saved-passkey list. Key material is not requested by this metadata view.',
        'Check enabled flag, identity-scoped query and displayed relying party/account metadata.',
        'Exercise disabled feature, loading/error/empty and retry without exposing key material or treating unknown as empty.',
        'Verify actual metadata provider, account transitions and privacy without accessing real credentials.',[3])
    add(2,'确认删除云电脑 Passkey',C('bt','xt'),
        'Select a passkey, confirm its credential identity, delete by credential_id and on success remove only that item from cache, close confirmation and invalidate the query.',
        'Block pending duplicate mutation; failure shows dedicated toast and does not report deleted status. Other browser credentials/sessions are separate effects.',
        'Inspect selected passkey confirmation, delete path and targeted cache update/refetch.',
        'Cancel or reject mutation and verify pending guard, error feedback and retained remaining keys.',
        'Verify actual key removal and consumer behavior only with a synthetic authorized credential; no live deletion was performed.',[3])
    return result

def configuration():
    return dict(
        number=7,work='settings-access-batch07-work',previousScope=13,previousCoverage=4,
        expectedState='2026-10-24T09:10:12.286940+00:00',
        selections=['age-entry','age','passwords','cloud-computer'],
        scriptFiles=['settings_access_batch07_specs.py','probe_settings_access_batch07.cjs'],
        entries=[('age','Age','T23'),('passwords','Passwords','T24'),('cloud-computer','Cloud computer','T25')],
        mechanisms=[
            ('Age verification lifecycle','Identity/eligibility watch, settings entry, disposal and phase-specific retry/readback.', [('age','Te'),('age','U'),('age','assignment-z')]),
            ('Saved credential metadata and delete reconciliation','Identity-bound schema, cursor/loaded-search/no-cache and nonretry delete reconciliation.', [('passwords','Ue'),('passwords','We'),('passwords','assignment-Ge'),('passwords','Je')]),
            ('1Password identity, enrollment and revocation','Workspace callback mismatch, authoritative status, strict OAuth destination and nonretry mutations.', [('passwords','Pe'),('passwords','Fe')]),
            ('Cloud browser configuration and credential metadata','Default/site patches, serialized mutations, host grouping and passkey lifecycle.', [('cloud-computer','Dt'),('cloud-computer','assignment-Mt'),('cloud-computer','ht'),('cloud-computer','bt')]),
            ('Orbit cookie identity and target affinity','Account/user current checks, postfetch abort, mandatory target and context-bound delete after query cancellation.', [('cloud-computer','at'),('cloud-computer','st')])],
        gaps=[
            ['Age normalization/query and verification provider/readback controller remain imported boundaries.', 'Actual authenticated values, provider lifecycle, selected mode and durable authoritative age state.'],
            ['Saved credential service/schema primitives, provider OAuth callback/enrollment/status/revocation and browser adapters remain external boundaries.', 'Actual account/user transitions, stored metadata/provider state, product mode, privacy and nonretry reconciliation.'],
            ['Pattern parser, cookie domain grouping, actual Orbit target acquisition, HTTP identity assertions and credential storage remain imported boundaries.', 'Actual config/approval/cookie/passkey receivers, account/target affinity, mode and persistent effects.']],
        modules=['account/age','credentials','cloud-computer'],
        consumers=[['account/summary','backend-adapter/age','provider/verification'],['backend-adapter/credentials','host/external-browser','provider/onepassword'],['backend-adapter/cloud-browser','browser/approval','browser/target-ownership']],
        dependencies=[['React/query/UI/DI packages','age/provider/account APIs'],['React/query/schema/UI packages','saved-credentials and 1Password APIs','browser adapters'],['React/query/UI/schema/domain packages','cloud-browser config/cookie/passkey APIs','Orbit target and identity adapters']],
        decisions=[
            'Separate age presentation from settings-scoped verification lifecycle and provider/authoritative-readback adapters; preserve phase distinction and identity disposal.',
            'Separate masked saved-credential metadata/delete reconciliation from 1Password enrollment/status/revocation. Preserve expectedIdentity and nonretry mutations; do not add plaintext password storage or reveal.',
            'Separate config/site permission policy, cookie views and passkey metadata from adapters; retain distinct Work and Orbit target/identity rules rather than merging endpoints.'],
        title='年龄、密码与云电脑：操作归属和恢复边界',
        modeReason='All three entries have a chatGpt access family, but age/account/credential/browser services can have shared consumers; names, strings and entry visibility alone do not prove complete product-mode exclusivity.',
        firstParty=['age phase/identity/disposal policy','metadata-only credential presentation and loaded-search/delete reconciliation','1Password callback identity/OAuth destination policy','default/site approval patches and serialized mutations','Work versus Orbit cookie target/identity/cache policy','passkey confirmation/cache policy'],
        externalize=['React/query/UI/DI/schema/domain packages','age verification/provider and account APIs','saved credential and 1Password services','browser/OAuth adapters','cloud browser config/cookie/passkey and Orbit target services'],
        probeDescription='核对身份/游标/非重试策略、OAuth目的地与合成tab、Cookie账户与target约束、删除分发、模式输入规范化，以及年龄控制器资格/复用/身份变化销毁；所有接收器为合成替身，未运行原应用模块，未读取真实凭据、访问验证/OAuth供应商或新增模型提交',
        modeSummary='三个入口虽属chatGpt访问族，但账户/年龄/凭据/浏览器共享消费者未完成模式闭合，确认排除仍为0。第三方React、query、UI、schema、domain和provider实现不生成，沿既有清单或服务适配引入；第一方保留身份、生命周期、对账、目标与缓存策略。',
        boundarySummary='导入的年龄/provider、OAuth、pattern/domain、target、HTTP身份和存储边界保留在合同及覆盖表，实际运行、权限、模式、持久化与委托内部实现仍待验收。',
        reportFacts='真实服务、凭据/provider运行、产品验收与模型请求未增加。源码明确年龄阶段/身份销毁、密码元数据与非重试删除对账、1Password目的地限制、Work/dot Cookie身份与target差异。',
        summaryPoints=[
            '年龄验证区分发起、进行中、等待权威结果、刷新失败；身份或资格变化时销毁控制器并复位，刷新失败不能当作验证成功或直接重新发起。',
            '密码页只读取credential_id、网站、掩码账户、创建时间和游标；未出现明文密码读取/显示。删除响应不确定时刷新对账，不自动重试删除，也不声称网站已退出。',
            '1Password绑定账户/用户并阻断回调工作区不匹配；连接目的地只接受三个精确HTTPS origin及/oauth/authorize。导航或关闭浏览器均不等于连接成功。',
            '云电脑三种默认审批映射到两个字段，站点权限单独patch。Work与dot Cookie保持不同身份/target/surface约束；dot先取消查询、重查身份，再按捕获target删除。Passkey只分析元数据和确认删除。'],
        nextQualification='Imported age/provider/OAuth, pattern/grouping/target and real credential/browser services stay local; do not repeat settled selections or source probes. No additional model authorization remains.')
