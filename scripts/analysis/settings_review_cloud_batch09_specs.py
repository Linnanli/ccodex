"""Bounded settings goals; imported services/editors remain explicit receivers."""


def specifications():
    result = []

    def add(page, name, units, effect, failure, behavior, negative, receiver, support):
        result.append(dict(pageIndex=page, name=name, units=units, effect=effect,
                           failureAndCancellation=failure,
                           acceptance=[behavior, negative, receiver], support=support))

    R = lambda *names: [('code-review', name) for name in names]
    C = lambda *names: [('codex-cloud', name) for name in names]
    add(0, '切换代码审查设置范围与托管平台', R('hr', 'Rn', 'ur', 'assignment-pr'),
        'Use separate app/cloud access results, app/cloud URL tabs and github/gitlab provider selection. The app surface embeds server code-review/tool pull_requests.settings with app lifetime and the selected host; its tool internals remain delegated.',
        'Do not expose a repository detail when cloud access is absent. Access loading/error is separate from an empty repository list; URL provider validation falls back to the supplied provider.',
        'Vary app/cloud visibility, tab and valid/invalid provider; inspect embedded tool identity and repository navigation preserving search.',
        'Remove cloud access with a repository URL and fail both access checks; verify the source visibility/error behavior.',
        'Verify access-family evaluation, embedded tool host bridge and actual Codex/shared mount; authMethod chatgpt does not establish product-mode exclusivity.', [0])
    add(0, '选择桌面审查插件使用的托管实例', R('Qn', '$n', 'ar', 'qn'),
        'Choose default or a connected GitHub/GitLab instance through the distinct githubConnection/gitlabConnectorId preference writers; retain the GitHub feature gate and effective-provider selector.',
        'Loading or save-pending disables selection. A disappeared saved connection shows unavailable; failed save displays its toast and finally releases pending.',
        'Inspect provider-specific option values, saved selection and default-null values.',
        'Reject save, remove the selected connection and vary the GitHub gate; preserve feedback and pending cleanup.',
        'Verify connection catalog eligibility, preference durability and actual plugin connection consumer.', [0, 2])
    add(0, '管理 GitHub 应用的仓库访问范围', R('Qn', 'Un'),
        'Open the default installation URL or query the selected enterprise connection/link installation URL, then request external-browser navigation.',
        'Missing installation URL offers refetch; opening the provider page does not prove repository access changed.',
        'Inspect default versus non-default connector/link and exact external navigation target.',
        'Fail installation URL loading, retry and cancel the external provider flow without claiming a permission update.',
        'Verify installation metadata service and external URL bridge; provider-side permission changes require separate integration acceptance.', [0, 1])
    add(0, '查找并打开云端仓库审查设置', R('Ut', 'Kt', 'It', 'Sn', 'assignment-Rt', 'assignment-zt', 'assignment-Bt'),
        'Filter eligible linked connectors, preserve current/preferred/first valid selection, debounce search 200ms, paginate eight rows and open repository detail. Exact repository lookup falls back only on HTTP 400/403/404; GitHub search excludes archived repositories and caps at page 125.',
        'Abort or identity change rejects connector results. Loading/error/no connections/no repositories remain distinct. Detail is read-only without admin/push; refreshing an error does not retry a save.',
        'Inspect GitHub/GitLab repository normalization, exact lookup/search/list paths, connector scoping, pagination and encoded detail navigation.',
        'Inject archived direct result, allowed fallback error, unrelated error, abort and account change; preserve detail permission/error handling.',
        'Verify connector linking and repository API adapters under actual account, selected mode and repository permissions.', [0, 1])
    add(0, '设置仓库自动代码审查策略', R('Sn', 'wn', 'kt', 'assignment-Vt'),
        'Parameterize automatic enablement, everyone/team/personal scope, trigger and exhaustive review. Personal trigger/exhaustive maps to null; mutations carry repository, current review preference and funding generation.',
        'Pending/fetch/load-error/no-write permission disables controls. A 409 refreshes detail and requires reviewing fresh state; no automatic resubmission.',
        'Inspect scope-to-payload mappings, trigger options and null inheritance, plus single-record PATCH body.',
        'Return 403/409 or fail refresh; verify read-only/error behavior and absence of duplicate saves.',
        'Verify /wham/settings/code_review PATCH, concurrency generation, subsequent read and actual review scheduling.', [1, 2])
    add(0, '重新授权仓库审查使用工作区额度', R('Sn', 'Cn', 'assignment-Vt'),
        'When funding_authorization_required is returned, require the explicit Allow action to submit authorize_funding true with the current repository generation.',
        'A conflict with funding still required shows the funding-specific error and omits the refresh CTA; ordinary refresh must never reconnect funding.',
        'Inspect explicit authorization payload and funding-required visibility.',
        'Return funding conflict, deny write permission or leave dialog/action unconfirmed; verify no implicit authorization.',
        'Verify account funding authorization service, generation conflict and durable repository policy.', [1, 2])
    add(0, '设置仓库自动安全审查与触发方式', R('Sn', 'cn', 'kt'),
        'When security_review exists, use an independent security policy and trigger; smart_detect is offered when enabled by its flag or already selected.',
        'Absent security_review does not create one. Disabled repository state blocks updates; automatic off retains the manual @codex notice.',
        'Inspect security payload nesting, everyone/team/personal scope and trigger option preservation.',
        'Vary feature flag, existing smart_detect and missing security settings; retain source options and guards.',
        'Verify security-review service and actual scheduler independently of code review settings.', [1, 2])
    add(0, '设置安全审查威胁模型来源与文件', R('cn', 'gn'),
        'Choose threat-model source and edit a repository-relative path. Submit trims the path, maps empty to null and sets repository_file; cancel restores the saved draft.',
        'Unchanged trimmed text or disabled editor does not submit. Source trimming does not prove path existence or path validation by the server.',
        'Inspect source choices, trimmed path/null payload and dirty-state behavior.',
        'Submit whitespace, unchanged value, disabled state and cancel; verify exact save/no-op/reset behavior.',
        'Verify repository-file access and server path policy with synthetic repository contents.', [2])
    add(0, '设置仓库安全发现的报告严重程度', R('cn', 'assignment-yn'),
        'Select separate automatic and manual reporting thresholds from critical/high/medium/low and send only the changed field.',
        'Reporting thresholds are independent from the GitHub blocking threshold; server rejection remains a save failure.',
        'Inspect both threshold fields and defaults high versus inherited/manual policy.',
        'Reject update or remove permission; verify disabled controls and unchanged durable state.',
        'Verify persisted thresholds and actual automatic/manual finding filtering.', [2])
    add(0, '设置 GitHub 安全审查合并保护', R('cn', 'assignment-yn'),
        'Show merge protection only under its feature flag for non-GitLab repositories. Only repository admins can edit it; enabling requires the blocking severity to be at least the automatic reporting severity.',
        'An already-enabled gate can still be disabled when severity ordering prevents enabling. Publishing a failing check does not itself configure GitHub required checks.',
        'Inspect provider/flag/admin guards, severity ordering, enable/disable and blocking threshold payloads.',
        'Vary GitLab, push-only permission and invalid severity ordering; verify enable is blocked while existing protection can be turned off.',
        'Verify GitHub check publication and provider branch-protection requirement separately.', [1, 2])
    add(0, '维护仓库路径的安全报告覆盖规则', R('cn', 'gn', 'mn', 'assignment-bn'),
        'Add trimmed path-prefix rules with null auto/manual overrides, update a selected rule by index, remove by index and map inherit to null.',
        'Add editor closes on successful mutation callback; a failed save keeps the draft. No source-side deduplication or path-existence claim is introduced.',
        'Inspect add/update/remove array payloads, inherited severity nulls and success-only draft closure.',
        'Use empty/duplicate prefixes, fail save and cancel; preserve the actual client rules and server validation boundary.',
        'Verify repository security API normalization, persistence and per-path reporting semantics.', [2])
    add(0, '设置个人代码审查偏好', R('zn') + [('cloud-preferences', 'v'), ('cloud-preferences', 'S')],
        'Set personal always/repo_default, pr_open/every_push/smart_detect trigger and exhaustive review through /wham/settings/user; repository policy takes precedence.',
        'Missing preferences shows loading/error and retry. Mutation failure shows a save-error toast; localized ChatGPT wording is not a mode exclusion.',
        'Inspect personal payload fields and query key by user, distinct from repository PATCH.',
        'Reject load/save and vary repository override; verify error handling and policy precedence in integration.',
        'Verify user preference GET/PATCH and review consumer; preserve account/user auth and cache scope semantics.', [2])
    add(0, '设置个人安全审查偏好', R('zn', 'kn') + [('cloud-preferences', 'S')],
        'When personal security preferences exist, set automatic preference, trigger and independent automatic/manual severities as nested security_review changes.',
        'Smart-detect and allowance visibility retain source conditions; no security preferences are fabricated when absent.',
        'Inspect nested payloads, threshold options and source feature/allowance gates.',
        'Remove personal security settings or reject save; verify no unrelated code-review mutation.',
        'Verify personal security preference merge semantics and repository override behavior at the service.', [2])
    add(0, '配置代码与安全审查的信用额度使用', R('zn', 'kn', 'Qt'),
        'Keep allow_credits_for_code_reviews and allow_credits_for_security_reviews separate. Respect credit-management permission and source security conditions; retain usage/pricing links and flag/date-controlled billing notice.',
        'Viewing a notice or pricing link does not authorize funding. Saving credit preference is separate from repository authorize_funding.',
        'Inspect independent booleans, management gates and notice date/visibility.',
        'Deny credit-management permission, use invalid notice date and reject preference save; verify no false permission or funding update.',
        'Verify account allowance/credit policy, user preferences and actual billing effects independently.', [0, 2])
    add(0, '打开仓库审查说明文件', R('rn', 'an'),
        'Build AGENTS.md link from an HTTP(S) clone URL and default branch, preserving origin and repository path; use GitLab -/blob and encode the branch segment.',
        'Missing branch, invalid URL or non-HTTP(S) URL omits the link; opening the link neither creates nor edits instructions.',
        'Inspect GitHub/GitLab URL construction including slash-containing branches and .git suffix.',
        'Use invalid/SSH URLs and missing branch; verify no unsafe or invented destination.',
        'Verify external opener and provider file access without changing repository contents.', [0])

    add(1, '浏览与搜索已保存云环境', C('Vn', 'Un', 'Gn', 'Kn', 'En', 'assignment-Tn'),
        'Gate the page by the cloud capability, search names and resolved repository names locally, and use a 300ms empty-result refresh. Keep signed-out/loading/error/empty/no-match states distinct; show sharing and unpublished status.',
        'Editor/delete selection is identity keyed; stale selections are ignored after account/user changes. Repository-name loading/inaccessible uses its fallback rather than exposing absent metadata.',
        'Inspect search/max length, debounce-refresh conditions, identity ownership and repository fallback/status labels.',
        'Switch identity, reject queries and search with no matches; verify retry route and no stale editor.',
        'Verify saved-config queries, repository metadata and capability/access adapters; catalog UI does not prove a complete environment lifecycle.', [3])
    add(1, '从云环境列表进入创建流程', C('Un'),
        'The signed-in Create action delegates to imported It(scope), sharing the existing environment creation flow.',
        'This entry does not submit a model task or establish draft, publish, runtime or repository-selection implementation.',
        'Inspect signed-in availability and exact creation-action receiver.',
        'Remove account/user or fail the delegated flow; retain signed-out and error behavior.',
        'Link to the existing environment-creation recovery task; resolve cross-entry equivalence without generating duplicate implementations.', [3])
    add(1, '创建独立云环境编辑草稿并打开任务', C('Gn', 'qn', 'assignment-Cn'),
        'Under edit permission, POST environmentConfigs.createDraft with account/user/configId, recheck authentication after the response, attach returned draft/environment metadata and open the returned task with openEnvironmentSetup true.',
        'Null/uncertain/5xx responses produce xn and disable repeat Edit to prevent duplicate tasks; 404 uses a distinct not-found error. Missing thread_id fails. Title-setting failure is a warning after successful creation.',
        'Inspect permission, pre/post identity checks, draft metadata and navigation state for initial/unpublished and published configs.',
        'Inject uncertain/404/permission/identity-change/missing-thread responses and title failure; verify duplicate suppression and distinct messages.',
        'Verify environmentConfigs POST, task/provider adapters and metadata persistence; no model submission is authorized by this source probe.', [3, 4])
    add(1, '查看无编辑权限的云环境配置', C('Gn', 'Wn', 'On'),
        'Offer View when editing is unavailable; load environmentConfigs.request GET into an identity-keyed detail editor and apply read-only permission throughout.',
        'Unavailable receiver/load failure offers retry/cancel. Opening View does not grant edit/delete permission; delete policy also depends on RBAC/ownership.',
        'Inspect View versus Edit actions, detail request and read-only state.',
        'Use no receiver, failed read and account switch; verify no save or stale selection.',
        'Verify GET service, permission evaluator and selected-identity query lifetime.', [3, 4, 5])
    add(1, '修改并保存云环境配置', C('Wn', 'On'),
        'Maintain a local draft for name/access/repositories/network/setup/skills and delegated editor fields. Save combines normalized changes with a pending valid VPN editor save; cancel is disabled while saving.',
        'Require edit permission and matching account/user. Client/server field validation gates submit; conflict refreshes the current config and preserves diagnostics. Successful save updates detail cache and linked task metadata only for current identity.',
        'Inspect dirty/validation/save gating, VPN pending/valid state, normalized payload and identity-guarded cache updates.',
        'Inject permission/authentication/invalid VPN/conflict failures and cancel during pending; verify error diagnostics and no false saved state.',
        'Verify imported config editor/normalizer/validation/save adapters, conflict semantics and persistent repository/network behavior.', [4, 5])
    add(1, '编辑云环境变量与密钥草稿', C('On', 'Fn', 'Pn', 'An', 'kn'),
        'Track variable removals and account/user owner; secrets use replace mode with owner, trimmed nonempty names and source-specific validation. Existing secret rows are represented with blank values and explicit injection targets.',
        'Do not infer secret retrieval from metadata. Invalid source/value state blocks save; identity change must not reuse another owner draft.',
        'Inspect environment-variable names/removals, secret owner/replace mode, blank secret values and header/environment injection mapping.',
        'Use missing environment secret, invalid value, empty names and identity change; verify validation and draft isolation.',
        'Verify vault/config editor and secret update service with separately owned synthetic fixtures; do not read personal credentials.', [5])
    add(1, '删除已保存云环境', C('Gn', '_n', 'vn'),
        'Confirm DELETE through environmentConfigs.delete; on successful same-identity response cancel pending queries, recheck identity, clear matching selection/detail/cache entries and refresh config families.',
        'Close and duplicate submit are blocked while pending. HTTP 403/404/405 are terminal with Close; recoverable errors allow retry. Existing tasks/running environments are explicitly outside this deletion action.',
        'Inspect RBAC/ownership eligibility, confirmation, DELETE payload and success-only cache reconciliation.',
        'Use no receiver, identity change before/after cancellation, rejection and terminal errors; verify no false cache deletion or duplicate submit.',
        'Verify actual delete scope, configuration storage and running-task independence through owned service fixtures.', [3, 4])
    add(1, '进入个人密钥库设置', C('Vn', 'assignment-Xn', 'Hn'),
        'personal-vault tab lazy-loads PersonalVaultSettings from its separate factory, with account-aware loading and explicit module-load failure fallback.',
        'The delegated vault module remains a separate pending settings container; this entry establishes no vault read/write/delete behavior.',
        'Inspect tab selection, lazy factory/export identity and loading/signed-out states.',
        'Fail module loading and change account; verify fallback and no claim of vault mutation.',
        'Recover the separately indexed PersonalVaultSettings operations and credential service before vault acceptance.', [0, 5])
    return result


def configuration():
    return dict(
        number=9, work='settings-review-cloud-batch09-work', previousScope=15, previousCoverage=6,
        expectedState='2026-10-24T10:14:15.285975+00:00',
        selections=['code-review', 'codex-cloud', 'cloud-preferences', 'code-review-access'],
        scriptFiles=['settings_review_cloud_batch09_specs.py', 'probe_settings_review_cloud_batch09.cjs'],
        entries=[('code-review', 'Code review', 'T29'), ('codex-cloud', 'Codex Cloud', 'T30')],
        mechanisms=[
            ('Review access, provider and delegated UI', 'Separate app/cloud access and effective provider from authentication method; preserve embedded tool and external-link contracts.', [('code-review', 'hr'), ('code-review', 'Rn'), ('code-review-access', 'y')]),
            ('Connector and repository query identity', 'Filter eligible linked connectors with abort/current-identity checks; preserve exact lookup/search fallback, pagination, permissions and concurrency refresh.', [('code-review', 'assignment-Rt'), ('code-review', 'assignment-zt'), ('code-review', 'assignment-Bt'), ('code-review', 'assignment-Vt')]),
            ('Personal, plugin and repository preference receivers', 'Keep user-keyed /wham/settings/user preferences, account/user config preferences, desktop provider preferences and repository patch policy distinct.', [('cloud-preferences', 'v'), ('cloud-preferences', 'y'), ('cloud-preferences', 'S'), ('cloud-preferences', 'C'), ('code-review', 'assignment-Vt')]),
            ('Cloud catalog identity and delegated creation', 'Catalog query/search/sharing and creation entry are not the delegated environment creation or personal-vault implementation.', [('codex-cloud', 'Un'), ('codex-cloud', 'Gn'), ('codex-cloud', 'En')]),
            ('Environment config draft/read/delete adapter', 'environmentConfigs is an explicit runtime/service adapter with current-identity, permission, uncertain-response and cache reconciliation policy retained in first party.', [('codex-cloud', 'assignment-Cn'), ('codex-cloud', 'Wn'), ('codex-cloud', '_n')]),
            ('Cloud editor and secret ownership', 'Preserve normalized drafts, conflict/field diagnostics, VPN pending validation and credential owner/blank-value policy; editor/vault/service internals remain delegated.', [('codex-cloud', 'On'), ('codex-cloud', 'Fn'), ('codex-cloud', 'Pn'), ('codex-cloud', 'assignment-Xn')])],
        gaps=[
            ['Embedded pull_requests.settings tool, connection catalogs, effective provider/desktop preference writer, allowance evaluator and review API implementations remain assigned interfaces.', 'Actual Codex/shared mount, access/auth/account state, repository provider policy, review scheduling, funding and durable service effects.'],
            ['Imported environment-creation/config editor/save/validation/VPN/repository-query helpers and PersonalVaultSettings remain assigned interfaces; vault operations are still a pending container.', 'Actual environmentConfigs runtime/service, account/RBAC transitions, task creation/navigation, config/secret persistence and conflict/deletion behavior.']],
        modules=['review/settings', 'cloud-environments/settings'],
        consumers=[['review/plugin-tool', 'review/repository-policy', 'review/user-preferences', 'connections/git-providers', 'settings/preferences'], ['cloud-environments/catalog', 'cloud-environments/editor', 'backend-adapter/environment-configs', 'tasks/environment-setup', 'vault/settings']],
        dependencies=[['React/query/UI packages', 'GitHub/GitLab connection and review REST adapters', 'desktop preferences, embedded tool and external URL bridge'], ['React/query/UI/schema packages', 'environmentConfigs runtime/service adapter', 'shared environment editor/validation/VPN, task and vault adapters']],
        decisions=[
            'Separate desktop review tool/provider preferences from cloud repository policy and personal user preferences. Keep first-party policy, concurrency/funding/permission guards; externalize third-party UI/query packages and connect REST/host adapters.',
            'Keep cloud catalog/editor policy in renderer, assign request/createDraft/delete to environmentConfigs, reuse existing environment creation/task/vault adapters, and preserve identity/credential/uncertain-result rules before implementation.'],
        title='代码审查与云环境：用户操作和服务边界',
        modeReason='Review access uses separate app/cloud decisions and auth/plan/workspace eligibility; cloud settings has capability and identity gates. Neither authMethod chatgpt nor localized ChatGPT strings establishes a ChatGPT-only product mode; selected-mode/shared closure remains unresolved.',
        firstParty=['review scope/provider and repository policy', 'repository concurrency/funding/permission rules', 'personal preference and billing visibility', 'cloud catalog/search/action policy', 'draft uncertain-result and identity guards', 'editor/conflict/secret-owner and delete cache reconciliation'],
        externalize=['React/query/UI/schema packages', 'existing embedded tool, connection and preference adapters', 'review REST service', 'environmentConfigs runtime/service adapter', 'shared config editor/validation/VPN, task and vault interfaces'],
        probeDescription='仅执行冻结源码的仓库规范化、查询/变更回调、账户守卫、草稿创建错误与密钥元数据映射，接收器和记录均为合成替身；未调用真实审查、云环境、密钥库或模型服务',
        modeSummary='保留审查 app/cloud 访问、认证方式、账户与功能开关的独立含义，确认整模块排除仍为0；第三方实现作为依赖引入，第一方门控、策略、错误与缓存协调保留。',
        boundarySummary='两个页面的操作已接到审查 REST/偏好、environmentConfigs、共享环境编辑器、任务和密钥库边界；委托内部实现与实际服务/模式/持久化属于各自局部验收，不能计为产品通过。',
        reportFacts='明确仓库与个人审查的不同写入接口、资金重连的显式动作，以及云环境身份守卫、草稿不确定响应防重与删除缓存协调；无新增真实服务、密钥读取或模型提交。',
        summaryPoints=[
            '代码审查拆为桌面嵌入工具/托管实例、仓库代码与安全策略、个人偏好三组。仓库 PATCH 与用户偏好 PATCH 不共用持久化语义；额度偏好与显式 authorize_funding 也独立。',
            '仓库查询区分 GitLab 空搜索、直接仓库查找和搜索分页；仅400/403/404触发查找回退，GitHub排除归档并最多125页。连接加载在返回前核对账户/用户并支持取消。',
            '安全合并保护还受提供商、功能开关、admin权限及严重程度顺序约束；实际GitHub必需检查设置仍由提供商承担。路径覆盖规则保留继承null和成功后关闭编辑器。',
            '云环境编辑草稿的未知响应会禁用重复Edit以免重复任务；删除成功在取消查询后再次核对身份。秘密值映射为空白，变量/密钥草稿带accountId/userId所有者。创建流程、共享编辑器和个人密钥库继续按已有边界恢复。'],
        nextQualification='Finish remaining entry operation/ownership mapping without reopening settled helpers. Review/config/secret/task adapters retain dedicated integration acceptance; PersonalVaultSettings is still pending. No model authorization remains.')
