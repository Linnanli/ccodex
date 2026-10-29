"""Finite user goals derived from the three pinned settings component families."""

def specifications():
    result = []
    def add(page, name, units, effect, failure, behavior, negative, receiver, support):
        result.append(dict(pageIndex=page, name=name, units=units, effect=effect,
            failureAndCancellation=failure, acceptance=[behavior, negative, receiver], support=support))
    P=lambda *names:[('plugins',name) for name in names]
    S=lambda *names:[('skills',name) for name in names]
    C=lambda *names:[('connections',name) for name in names]
    I=lambda *names:[('initial-selected',name) for name in names]
    # The manager's existing MCP goals are related to FSC-0115..0120, not duplicated.
    add(0,'按宿主、类型和关键词浏览已管理的扩展',P('go','Qa','lo'),
        'Settings forwards the selected host and manageOnly:true; the ordinary plugins entry starts on plugins. Manager resolves plugins/skills/apps/marketplace/mcps tabs, counts, query and eligibility, keeping hidden/unavailable entries distinct.',
        'Plugins-disabled fallback, data pending, load error and zero search results are distinct. Host/account/flag values are unobserved; manageOnly is a layout/context option and does not make every tab an MCP operation.',
        'Vary host, initial tab, current tab counts and search; verify source-defined fallback and non-MCP-tab visibility.',
        'Exercise pending/error/empty/hidden and unavailable plugins without treating cached data as fresh success.',
        'Verify actual host-scoped list providers and mounted route. Shared skills and MCP operations must retain their existing identities.',[0])
    add(0,'从插件设置打开对应扩展目录',P('go'),
        'Browse directory navigates to /plugins with initialHostId, settings analytics entrypoint and initialTab:skills only when the selected management tab is skills; other management tabs select plugins.',
        'Navigation only; catalog fetching/installation lives at the destination. The MCP-only settings wrapper does not expose this header action.',
        'Open directory from skills, plugins, apps and marketplace tabs and inspect route state and selected host.',
        'Verify manageOnly header omission and destination loading/failure; navigation must not be reported as installation.',
        'Verify actual destination consumption of route state and preserve the independently scoped directory subsystem.',[0])
    add(0,'查看已安装插件详情',P('go','Qa','assignment-bo'),
        'Manager chooses detail URL according to the host feature condition; opening details delegates navigation. Nested settings suffix selects a lazy detail route only when its feature condition is true, otherwise redirects.',
        'Lazy route/detail implementation and navigation receiver are external to this selected closure. No plugin mutation is implied by viewing.',
        'Inspect detail targets for both feature branches, nested suffix routing and selected host.',
        'Disable the branch or fail lazy loading; verify source redirect/error boundary and no install/toggle request.',
        'Verify lazy component export, actual detail data receiver and return navigation before claiming full detail coverage.',[0])
    add(0,'安装管理列表中的插件',P('Qa')+I('rpr'),
        'Manager passes plugin, active project, host and settings analytics to installPlugin, with list refresh on success. The hook delegates to apr; install detail flow is a separate adapter.',
        'Installation eligibility, confirmation, file effects and rollback belong to the delegated install subsystem; this sender does not prove their outcomes.',
        'Select an eligible plugin and inspect plugin identity, project/host and success refresh callback.',
        'Cancel or fail the delegated installation and ensure no sender-only success claim.',
        'Verify actual installer receiver, required package files, installed state and failure/cancel behavior with controlled data.',[1])
    add(0,'启用或停用插件',P('Qa')+I('Tkn'),
        'Remote account-backed host uses enable/disable HTTP endpoints with account-change guard. Other remote-source plugins use the HTTP path; ordinary local-source branch uses config/batchWrite with chosen file/version and reloadUserConfig:true. Local optimistic plugin/config snapshots are restored on failure.',
        'Do not collapse account-backed and remote-source branches: only the account-backed branch returns immediately after HTTP. Settled invalidation is separate from effective runtime enablement.',
        'Inspect each host/source branch, exact plugin identity, enable boolean and config file/version payload.',
        'Change account during an account-backed write and reject config/HTTP writes; verify guard, snapshot restoration and error feedback.',
        'Verify actual backend/config receiver and list reload, then effective enablement after reopening.',[1])
    add(0,'卸载插件',P('Qa')+I('Okn'),
        'Account-backed host checks account identity then calls uninstall endpoint. Other hosts delegate vkn, update plugin-list state and await list/marketplace refresh while app refresh also has its own caught async path.',
        'Pending operation identity and settled cleanup are retained. HTTP acknowledgement, cache removal and actual filesystem removal are separate. No global rollback is established.',
        'Inspect local/account-backed payloads, requestPluginId fallback and selected host.',
        'Fail uninstall and app/list refresh independently; verify pending cleanup and source-defined feedback.',
        'Verify actual uninstall receiver, package/config removal and plugin/apps state after refresh/reopen.',[1])
    add(0,'复制或创建插件分享链接',P('Qa'),
        'Load share details, resolve existing/configured link and, when sharing flag and local plugin path permit, create a share before copying. Creation triggers plugin refresh; copy failure has a dedicated toast.',
        'Missing path, absent/empty link, detail/create/copy rejection remain distinct. Copying can create a remote share; it is not a read-only clipboard operation.',
        'Exercise existing, configured and newly created share URLs and inspect refresh/copy ordering.',
        'Fail detail, share creation and clipboard separately; verify empty URL handling and one error path.',
        'Verify real share service, access defaults and clipboard under separate authorized product acceptance.',[1])
    add(0,'修改插件分享对象与可发现性',P('Qa'),
        'Sharing dialog initializes principals/discoverability from resolved share context. Save delegates to saveShareTargets with remotePluginId and targets, then refreshes plugin data and returns principals/capability.',
        'An existing remote share lacking principals blocks opening with an error. Failed save is toasted and rethrown; closing a dialog is not an access update.',
        'Inspect initial principals/discoverability, first-share creation and update target payloads.',
        'Supply incomplete share context or fail save; verify blocking/error propagation without false saved state.',
        'Verify real share permissions, principal identities and reloaded access state.',[1])
    add(0,'更新插件的已分享版本',P('Qa'),
        'Dialog exposes update according to the version helper; existing remotePluginId is required. Save share with local plugin path and same remote ID, refresh, then success toast.',
        'Absent remote ID does nothing. Failed upload is toasted and rethrown; no automatic version rollback is established.',
        'Vary local/shared version and inspect exact pluginPath/remotePluginId reuse.',
        'Fail upload/refresh and inspect dialog error and source-defined success ordering.',
        'Verify actual uploaded version and remote share readback; helper eligibility alone is insufficient.',[1])
    add(0,'用插件预填一个新任务',P('Qa'),
        'Sharing-enabled manager builds plugin default-prompt prefill and starts sidebar composition with the active project.',
        'The callback opens/prefills composition; it does not itself establish model submission or task completion.',
        'Inspect fallback/default prompt, plugin display identity and active-project propagation.',
        'Disable sharing feature or omit default prompt; preserve button visibility and prompt helper behavior.',
        'Verify composer receiver and visible draft without sending an additional model task.',[0])
    add(0,'查看应用工具与事件',P('Qa','Na')+I('nKt','cKt'),
        'Applications list is gated by host availability and authenticated/account-consistent state. Opening one app selects its ID; tools/actions query includes actions and maps MCP events using effective configuration.',
        'Initial list failure, hard-refresh failure, config pending and per-app tool load error differ. Empty visible apps may be an auth/availability guard rather than absence.',
        'Inspect app selection, enabled query guard, effective config restrictions, tools and events.',
        'Vary auth loading/account mismatch/list/tool errors and verify retry/empty boundaries.',
        'Verify actual list/actions receivers and account scoping; account requirements alone do not prove ChatGPT-only product ownership.',[0])
    add(0,'连接应用并完成认证',P('Qa'),
        'Manager invokes host-scoped app-connect flow with oauthReferrer:connector_settings; modal forwards OAuth-start and connected callbacks. Completion refreshes app state through a flag-dependent await/catch branch.',
        'Flow and browser/OAuth receiver are imported boundaries. Closing clears connecting selection; the sender does not prove token persistence or successful authorization.',
        'Inspect host/referrer/options and OAuth/completion callbacks for both lifecycle flag branches.',
        'Cancel modal, reject OAuth and fail refresh independently; retain pending and cleanup behavior.',
        'Verify controlled OAuth callback, actual app lifecycle receiver and persistent connected state under separate authorization.',[0])
    add(0,'启用或停用已连接应用',P('Qa','Na'),
        'Manager obtains setAppEnabled/updatingAppId from the host-scoped app availability provider; list and tools dialog share that callback and configuration pending state.',
        'Actual enable write, cache policy and effective tool restrictions remain delegated; a switch event is not evidence of a successful write.',
        'Compare list/dialog callback identity, selected host, app and requested enabled value.',
        'Hold config pending or reject the provider mutation; verify disabled/pending and failure display.',
        'Verify actual availability receiver and effective tools after refresh and reopening.',[0])
    add(0,'重新加载扩展与应用列表',P('Qa','co','Ma','Ha')+I('nKt'),
        'Manager retry marks skills updated and awaits concurrent plugin, recommended-skill and app refreshes with finally clearing page refresh state. App-only retry uses hardRefetchAppsList, cancels its query first and disables automatic retry.',
        'Page retry catches to a dedicated toast; app-only retry catches its rejection. Partial marketplace data/errors remain visible rather than becoming a total empty result.',
        'Inspect page versus app-only refresh targets and loading cleanup.',
        'Fail one concurrent source and newer hard refresh; verify partial data and newest load error precedence.',
        'Verify actual query invalidation/refetch receivers and host/account-consistent returned lists.',[0])
    add(0,'升级插件市场',P('Qa','co','za')+I('Mkn'),
        'Upgrade delegates marketplace/upgrade with marketplaceName or null, awaits plugin refresh, then treats nonempty response errors as failure feedback even when the request resolves.',
        'Global and single-market pending states differ. Request failure and resolved partial errors have distinct feedback; caller catch does not imply successful upgrade.',
        'Inspect single-market name/null payload and pending identifiers.',
        'Return partial errors or reject request/refresh and verify error feedback without success toast.',
        'Verify actual marketplace receiver, on-disk revision and refreshed installed plugins.',[1])
    add(0,'移除插件市场及其已安装插件',P('Qa','Ka','qa'),
        'Removal dialog loads installed plugins, serially uninstalls from completedCount, then removes marketplace. Each successful step advances count; retry resumes remaining entries. Abort is checked between awaited operations.',
        'Load failure blocks removal. A failed/canceled sequence has no rollback of earlier uninstallations; abort does not cancel an already awaited receiver operation.',
        'Inspect plugin order, completed count, retry suffix and marketplace removal only after all plugin removals.',
        'Fail an intermediate uninstall and abort during an await; verify preserved progress and absence of invented rollback.',
        'Verify actual installer/marketplace receivers and retained partial effects after reopening.',[1])

    add(1,'浏览和搜索所选宿主的技能',S('Bt','Ut','Vt','Wt','St','Yt','Zt'),
        'Entry chooses modern browse or legacy page using a host-scoped availability condition. Both preserve installed/recommended distinctions and search; modern branch also has grouped results, local suggestions and keyboard result navigation.',
        'Recommended eligibility depends on host home/root. No skills, filtered empty, loading and recommendation error are separate. Product-mode subtitle is presentation evidence, not complete ownership closure.',
        'Exercise both branches, host fallback, grouped results, search and modern keyboard selection.',
        'Vary missing roots, empty/filter/loading/error and unavailable host without inventing recommendation support.',
        'Verify actual skills metadata and recommendation receivers for both branches; retain shared manager entry as an additional consumer.',[0,2])
    add(1,'刷新技能列表',S('Wt','St')+[('skills-data','G'),('skills-data','J')],
        'Legacy refresh marks skills updated then awaits recommendation refresh before clearing new-skill indicator. Shared data helper force-reloads installed skills, invalidates/broadcasts and updates skills_refresh_nonce through its coordinator.',
        'Started invalidation/nonce updates and completed backend reload differ. Legacy handler has no selected local catch for recommendation rejection.',
        'Inspect force reload, nonce/invalidation/broadcast and new-skill indicator ordering.',
        'Reject recommendation/installed reload and retain the actual caller error boundary and indicator state.',
        'Verify real query subscribers and fresh skill list after update/reopen.',[2])
    add(1,'安装推荐技能',S('Wt','St','Zt')+[('skills-data','q'),('skills-data','W')],
        'Install-recommended-skill receives hostId, skillId, repoPath, installRoot and statsig override. Success:true in the current generation updates host-specific installed IDs, invalidates recommendations, coordinates refresh and calls installed callback.',
        'Unavailable host root prevents submission. Clearing installed state changes generation so late results cannot update the new generation; settlement clears pending only for matching skill/generation.',
        'Inspect exact install payload, installed match filtering and current-generation success updates.',
        'Return success:false, reject or settle after clear/host change; verify stale completion suppression and pending cleanup.',
        'Verify actual install receiver, SKILL.md destination and refreshed installed identity with controlled files.',[2])
    add(1,'启用或停用已安装技能',[('skill-card','Ge')],
        'Skill card sends skills/config/write with name when the skill name contains colon, otherwise path, plus enabled. Local requested value drives display until backend metadata catches up; error resets local override.',
        'Pending disables toggle. Name-based and path-based identities must not be collapsed, and metadata propagation differs from mutation acknowledgement.',
        'Toggle namespaced and path-addressed skills and inspect mutually exclusive payload keys.',
        'Reject write or delay metadata; verify local override reset/retention and failure toast.',
        'Verify actual app-server config receiver, effective skill availability and persisted state after reopen.',[2])
    add(1,'卸载可移除的技能',[('skill-card','Ge'),('skill-card','Je')],
        'Local non-admin skill exposes uninstall; remove-skill receives hostId/skillPath. Response success determines success/failure toast; settlement refreshes recommendations and notifies skills updater.',
        'Remote or admin skill cannot use this remove action. Resolved success:false remains failure; pending identity is skillPath scoped.',
        'Inspect local/non-admin eligibility and exact remove payload from preview.',
        'Exercise remote/admin/pending, success:false and rejection without false removal feedback.',
        'Verify actual remove receiver, retained protected skill files and resulting installed list.',[2])
    add(1,'打开技能文件或在文件管理器中定位',[('skill-card','Ge')],
        'Open delegates file adapter with scope/path/cwd:null/hostId/openInSidePanel:true; reveal uses target:fileManager. Both are disabled for remote host kind.',
        'Native editor/file manager, path resolution and missing-file handling remain external. Opening preview must not be confused with opening the source file.',
        'Inspect Open versus Reveal arguments and platform-specific label with the same skill path.',
        'Use remote and missing-file cases; verify eligibility and actual adapter error behavior.',
        'Verify controlled file opens in intended panel/manager without changing its content.',[2])
    add(1,'复制技能的原始 Markdown',[('skill-card','qe')],
        'Read original skill contents through host/path hook; copy exact returned text. Disable while contents undefined or error; success toast only if clipboard helper resolves truthy.',
        'Description/preview text is not a substitute for raw SKILL.md. Clipboard rejection is not caught by this selected callback.',
        'Compare copied bytes/text to controlled raw file and inspect host/path selection.',
        'Exercise missing contents, read error and clipboard false/rejection; verify no false success.',
        'Verify actual file-read and clipboard adapters using synthetic content.',[2])
    add(1,'用已启用技能预填一个新任务',[('skill-card','Ge'),('skill-card','Je')],
        'Try now builds skill prefill and sidebar composition with active project after a local preparation action.',
        'Preview footer disables Try while skill disabled or enabled-state update pending. Composer opening alone does not submit a model task.',
        'Inspect selected skill prefill, active project and sidebar flag.',
        'Disable skill or hold toggle pending; verify Try is unavailable and no submission occurs.',
        'Verify composer receiver and visible draft without a new model request.',[2])
    add(1,'从技能页预填创建技能任务',S('Wt'),
        'Legacy New skill requires skillCreatorPath, builds creator prefill with kind:skill and includeStarterPrompt only before first use; sets first-use state and opens sidebar composition.',
        'Missing creator path disables action. This records only the observed legacy entry; modern creation menu remains a separately retained imported boundary.',
        'Inspect creator path, first/subsequent-use prompt and first-use state update ordering.',
        'Omit host root or creator path; verify disabled control and no prefill/state write.',
        'Verify prefill receiver and first-use persistence; creation output remains later task behavior.',[2])

    add(2,'按连接类型浏览宿主与设备',C('fs','Ms','Ns','Fs','cs','lo'),
        'Connections exposes conditional computer/devices/ssh/wsl tabs, normalizes route aliases, sorts lists and redirects invalid routes. Remote-control visibility/auth and WSL loading are distinct conditions; details preserve host identity.',
        'Absent tab or unavailable section uses source fallback. Auth-required/unauthorized/empty/pending differ; account wording does not establish ChatGPT-only product ownership.',
        'Exercise tab routes/fallbacks, online/name/last-seen ordering and type-specific detail data.',
        'Vary auth, missing lists, hidden tabs and malformed action routes; preserve redirects without losing location state.',
        'Verify actual host-state providers, version/status details and source-specific list receivers.',[0,3])
    add(2,'刷新连接与发现 SSH 配置别名',C('fs'),
        'Manual refresh awaits remote connection refresh plus remote-control refresh when visible; discovery retrieves SSH aliases and sorts them. Periodic refresh skips during mutations, avoids overlapping ticks and aborts on cleanup.',
        'Manual any-source rejection uses error toast; periodic AbortError is ignored and other errors debug logged. Discovery can reject before import dialog opens.',
        'Inspect refresh/discovery request names, concurrency, interval skip and cleanup.',
        'Reject one refresh, abort and overlap interval ticks; verify distinct error paths and no concurrent duplicate tick.',
        'Verify actual refresh/discovery receivers and updated host states using controlled configuration.',[3])
    add(2,'手动添加或修改 SSH 连接',C('fs'),
        'Editor delegates draft normalization; add appends autoConnect:true, edit preserves existing autoConnect. Save sends the full managed SSH list. Host identity change aborts associated registration; success closes editor and may connect/watch an external draft.',
        'Saving blocks duplicate save. Failure retains editor and logs failure; closing invokes external onCancel. Draft validation/normalization is a retained imported boundary.',
        'Inspect add/edit full-list payload, auto-connect inheritance, identity changes and success follow-up.',
        'Reject save, cancel editor and change host during registration; verify retained/cleared state and abort behavior.',
        'Verify actual managed-SSH receiver, durable configuration and subsequent connection state.',[3])
    add(2,'导入选定 SSH 配置别名',C('fs','Cs'),
        'Import dialog discovers eligible aliases, tracks selection and saves prior list plus mapped selected aliases sorted by display name; success connects each new host and clears/closes selection.',
        'Empty selection closes without write; pending save blocks repeat. Failed save does not clear successful-state selection as if imported.',
        'Inspect selected-only mapping, existing-list preservation and per-host connect follow-up.',
        'Exercise empty selection, discovery/save failure, duplicate alias eligibility and pending state.',
        'Verify actual SSH discovery/save receivers and controlled host registration/configuration.',[3])
    add(2,'移除已配置的 SSH 连接',C('fs'),
        'Remove aborts any matching project registration, then saves the managed SSH list filtered by hostId.',
        'Pending save prevents submission. Actual backend disconnect/config persistence are outside the list-filter sender.',
        'Inspect host-specific removal and preservation of unrelated connection records.',
        'Fail save or remove the in-flight registration host; verify abort and error boundary.',
        'Verify actual saved list and receiver-defined disconnect/cleanup after reopening.',[3])
    add(2,'连接或断开远程宿主',C('fs'),
        'Register host and mutate set-remote-connection-auto-connect. Watch state/error while awaiting; apply response only when no intervening update or current state is connecting. Finally unsubscribe; disabling aborts matching registration first.',
        'Pending managed SSH save blocks toggle. Rejection delegates its error helper; response state cannot blindly overwrite newer state.',
        'Inspect host/autoConnect payload and response state/error application.',
        'Deliver intervening host updates, reject request and disable during registration; verify stale-update guard and watcher cleanup.',
        'Verify actual transport/session lifecycle for SSH, WSL and remote-control sources independently.',[3])
    add(2,'登录需要认证的远程连接',C('fs'),
        'Authenticate registers host and opens host-scoped authentication dialog. Successful dialog callback marks matching registration authenticated; closing unauthenticated matching registration aborts it and may invoke external draft cancellation.',
        'Authentication UI internals and credentials receiver are separate. Opening or closing dialog does not establish successful login.',
        'Inspect host identity and authenticated marker before closing.',
        'Cancel without authentication, cancel another host and fail login; verify matching-only abort/cancel behavior.',
        'Verify actual controlled login receiver and connected state without accessing personal credentials.',[3])
    add(2,'退出远程连接登录',C('fs'),
        'Call host service logout, then synchronize host error state with code:login-required. Failure logs and shows dedicated logout error.',
        'No successful state change on rejection. Logout receiver and durable credential cleanup remain external.',
        'Inspect selected-host logout and post-success login-required state.',
        'Reject logout; verify no false successful state update and correct error feedback.',
        'Verify actual owned host session removal and reauthentication requirement.',[3])
    add(2,'通过 SSH 深链登记连接或远程项目',C('fs','Ps','ls','us'),
        'Only ssh/add reads trimmed name then nullish alias fallback; optional absolute project path and connect flag drive registration. Reuse cached project unless connection/new creation is required; wait for connected/no-error, handle login and createRemote(reuseExisting:true), select project and navigate with Codex composer state.',
        'Blank name does not fall back to alias. Relative path rejects before registration. Abort/navigation cleanup suppresses follow-ups, but does not imply rollback of already created host/project.',
        'Exercise name/alias, project-path/connect combinations, cached project reuse and exact navigation state.',
        'Use blank name, relative path, login-required, failure and abort at each await; verify cleanup and retained partial effects.',
        'Verify actual registration/project receiver and reconcile identity with FSC-0045/FSC-0105 before claiming globally distinct or equivalent project-add behavior.',[3])
    add(2,'授权当前客户端控制其他设备',C('fs'),
        'Unauthorized non-auth-required remote section exposes setup. Authorization mutation success closes authorization dialog and opens the appropriate add-device branch.',
        'Auth-required and missing local client ID disable add separately. Authorization failure must not advance to a successful add state.',
        'Inspect authorization request, dialog state and post-success add branch selection.',
        'Exercise auth-required, missing client ID, pending and authorization rejection.',
        'Verify real authorization receiver and persistent clientAuthorized state.',[4])
    add(2,'添加可控制的远程设备',C('fs'),
        'Legacy branch adds selected environment IDs to unique persisted list then enables their connections. One-to-one branch claims manual code with local clientId, refreshes remote environments and enables returned environment host.',
        'Empty selection closes without write; missing local client ID/pending blocks claim. Refresh/connect failure after claim is not an automatic claim rollback.',
        'Inspect selected environment persistence and manual-pair payload/refresh/connect ordering.',
        'Exercise empty selection, pending, invalid code/claim failure and refresh failure after successful claim.',
        'Verify actual claim/environment/storage receivers and resulting reachable device; external account/model actions were not run here.',[4])
    add(2,'重命名远程控制设备',C('fs','lo'),
        'Inline rename tracks one editing environment, serializes pending rename and sends envId/name; successful mutation closes editor.',
        'Rename failure is caught and retains edit state while clearing pending. Backend name validation is a receiver concern.',
        'Inspect exact envId/name, pending row and successful close.',
        'Reject rename or submit while another rename pending; verify retained editor and cleared pending.',
        'Verify real environment rename and name persistence across refresh/reopen.',[4])
    add(2,'删除远程控制设备',C('fs'),
        'Selected environment opens confirmation; confirm awaits delete-remote-control-environment with envId and clears selection only on success.',
        'Delete rejection uses dedicated error handling. Closing confirmation does not itself delete; deletion of registration and disconnect effects remain backend-defined.',
        'Inspect selected environment and one confirmed delete payload.',
        'Cancel, hold pending and reject delete; verify no false selection clear/success.',
        'Verify actual environment removal, connection teardown and refreshed device list.',[4])
    add(2,'允许 SSH 或 WSL 宿主接受远程控制',C('lo','So','Ii','ho'),
        'Allow dialog first persists host in allowed list then awaits host remote-control-enabled mutation; success opens details or pairing. Host-specific pending mutation keys aggregate updates.',
        'Second-step failure does not roll back the already written allowed list in this sender. Feature/version/connected-state conditions govern exposure.',
        'Inspect selected host, allowed-list write before remote enable and success continuation.',
        'Reject first/second step independently and vary feature/connection state; preserve partial effects and error handling.',
        'Verify real host enable receiver, allowed-list persistence and effective remote access.',[4])
    add(2,'为 SSH 或 WSL 宿主配对控制设备',C('lo','Eo','ho'),
        'One-to-one flow may rename default WSL environment, snapshots existing clients, waits for a newly paired client and then opens details. Required allow step precedes pairing when host lacks permission/enabled state.',
        'Client-list failure clears waiting state and toasts. Skip/close stops local waiting UI; no source evidence establishes revocation of an already granted device.',
        'Inspect existing-client set, host identity and new-client completion detection.',
        'Fail device list, close/skip wait and reject default rename; retain independent rename warning and no invented revoke.',
        'Verify actual pairing/approval receiver and paired-client identity under separate controlled acceptance.',[4])
    add(2,'设置本机远程控制并添加控制设备',C('zi','Hi'),
        'Setup-completed state selects setup/manage view. Setup starts shared setup flow; manage performs MFA preflight, snapshots existing clients and waits for connected/dismiss. Auth-required error routes to login, other errors toast; close invalidates list.',
        'MFA completion only advances an active MFA-required step. Query loading/error, no clients and one-to-one feature branches differ; shared setup implementation remains delegated.',
        'Inspect setup/manage, MFA-required/preflight/waiting/connected/dismiss transitions and existing-client exclusion.',
        'Fail authorization/list, complete stale MFA and close during wait; verify login/error branch and list invalidation.',
        'Verify actual local setup/MFA/pairing receivers and durable setup/client state.',[4])
    add(2,'允许或禁止本机被远程控制',C('Vi','Ii'),
        'Host-local availability switch calls host-keyed enable mutation; aggregate matching pending mutations disable switch. Labels vary with one-to-one pairing flag.',
        'Shared error helper can consume known errors; otherwise show specific failure toast. Native/runtime remote-control effect is not established by preference acknowledgement.',
        'Inspect local host enable boolean, mutation identity and pending aggregation.',
        'Reject known/unknown error and vary feature flag; verify exact error handling and disabled state.',
        'Verify actual runtime enable/disable, host availability and persistence after restart.',[4])
    add(2,'撤销控制本机的设备访问',C('Hi','ki'),
        'Device row revokes its client through imported receiver. Success removes client from cached list, invalidates list and shows success; failure reports failed analytics/toast. All revoke buttons disable while one request is pending.',
        'DisplayName/deviceModel/platform/clientId fallback is presentation only; revocation identity is clientId. Cache removal is not proof that the server revoked credentials.',
        'Inspect exact selected client identity, pending row and success cache/filter/invalidation.',
        'Reject revoke and repeat during pending; verify failed feedback and no successful cache removal.',
        'Verify actual remote client denial and list state after refresh/restart.',[4])
    add(2,'设置远程访问时插电保持唤醒',C('Bi'),
        'Read keepRemoteControlAwakeWhilePluggedIn with false fallback; write preference through shared setter and report save failure. Page renders this under setup-completed manage branch.',
        'Preference state, OS power assertion and actual remote-access enablement are separate; no OS sleep behavior was exercised.',
        'Inspect stored boolean, false fallback and platform label.',
        'Reject save and vary setup-completed state; verify visibility and dedicated error toast.',
        'Verify actual persistence and power-management consumer while plugged in and remote access enabled.',[4])
    assert len(result)==44
    return result
