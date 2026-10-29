"""Device storage, account security and family settings source contracts."""


def specifications():
    result = []
    def add(page, name, names, effect, negative, receiver, support):
        folder = ['storage', 'security', 'parental-controls'][page]
        result.append(dict(pageIndex=page, name=name, units=[(folder, n) for n in names], effect=effect,
            failureAndCancellation=negative, acceptance=[effect, negative, receiver], support=support))
    add(0, '查看并刷新本机 Codex 存储测量', ['lt', 'ut', 'nt', 'rt'],
        'Expose the deviceStorage service only for the local host; read/refresh the device-storage snapshot with query cancellation/cache replacement. Poll every1000ms only while scanning; show partial/completed/error categories and Codex home path.',
        'Remote hosts retain management navigation but no local measurement panel. Scanning/pending disables Refresh; only complete threads/subagents/archived category measurements without query error or refresh pending are passed to cleanup.',
        'Verify the actual deviceStorage scanner, cancellation, byte accounting and local-host selection; a synthetic snapshot is not a filesystem measurement.', [0])
    add(0, '筛选并选择待清理的旧本地会话及子代理', ['Qe', 'Ie', 'Le', 'Fe', 'We', 'Ve'],
        'Require app-server descendant-discovery support and version>=0.143.0-alpha.16. Inventory both archived/unarchived pages, reject duplicate IDs and recover measured missing IDs with at most8 workers. Default to archived older than90days; support30/90/180/365days and all/archived filters. Select eligible parent chats including every descendant and only when all measured bytes exist.',
        'Exclude ephemeral, active, nonfinite/nonpositive/new timestamps, unknown/nonstring source, ineligible threadSource, cloud_threads.create and malformed descendant cycles. Inventory/recovery errors block review. The selected pagination loop has no explicit repeated-cursor guard; complete real inventory remains an acceptance requirement.',
        'Verify actual parent/source normalization, complete inventory, descendant/byte accounting and filter/selection dialog with owned local fixtures.', [1, 2])
    add(0, '二次确认后清理选定父会话及子代理', ['Qe', 'We', 'Je', 'ze', 'Re'],
        'After review and a separate permanent-deletion confirmation, re-inventory and compare the selected parent/descendant identities, counts and updatedAt. Discover a complete descendant snapshot and re-read every parent/descendant before thread/delete(parentId); report deleted/skipped/failed by parent and refresh storage/archive queries.',
        'Missing discovery support fails before deletion. Changed/missing/active/incomplete snapshots are skipped; per-parent request failures increment failed. A review ref suppresses duplicate confirmation. Validation and delete are sequential calls, not a proven backend atomic transaction.',
        'Verify backend recursive deletion, race/partial-failure semantics, actual persistent storage and archival readback on separately authorized owned chats.', [1, 2])
    add(1, '启动添加或更改账户登录密码', ['co', 'Na', 'Pa'],
        'Choose change when changePassword eligibility succeeds, otherwise add only with both eligibility queries successful and add eligible. Advanced protection or pending/successful redirect disables the row; delegate authentication to the imported password flow.',
        'Absent eligibility hides the password row; passkey count can independently retain the login-method section. Failed/failed-result authentication shows recoverable feedback; opening the flow does not prove password change.',
        'Verify imported password/reauth provider and actual account password result independently of the page.', [3, 4])
    add(1, '启用或停用验证器、短信及推送 MFA', ['co', 'li', 'di'],
        'Project TOTP plus flag-available SMS/push factors, enabled factor IDs and trusted-device warning. Enable/disable actions pass through reauth before URL action/factor/factor_id state and the imported confirmation/setup component; disable requires the current factor still present.',
        'Missing/error factor data offers retry. Missing protection or active advanced protection disables switches; pending blocks changes. Missing factor ID cannot issue a disable action; stale factor deletion renders no dialog.',
        'Verify actual MFA reauth/setup/remove providers, delivery channels, factor refresh and account identity. Passkey management has its own goal.', [3, 4])
    add(1, '浏览、添加或移除通行密钥与安全密钥', ['Ra', 'di', 'fi', 'za', 'assignment-vo'],
        'Sort keys newest first; Add requires PublicKeyCredential support and no pending action. Enrollment requests a scoped in-house MFA token, then navigates to the auth host passkey-enroll route with state token and return path. Removal delegates reauth/confirmation for an existing factor ID. Retain the separate lazy YubiKey-order dialog boundary.',
        'Unsupported WebAuthn disables Add; missing/error factor data retries. Pending disables key actions. Ordering opens a delegated dialog and does not prove purchase; enrollment navigation does not prove a new credential.',
        'Verify actual auth URL/token provider, WebAuthn, factor removal and separately owned ordering consent without inferring credential or purchase success.', [3, 4])
    add(1, '重命名通行密钥或安全密钥', ['Ra', 'Ba'],
        'Edit the selected factor name; require a changed trimmed name of1..64 JS code units and no pending request. POST update_factor_name with factor_id/account header, then invalidate MFA and close.',
        'Empty/unchanged/too-long/pending disables Save; pending suppresses dialog close and failed save retains error feedback.',
        'Verify actual factor rename identity, server validation and refreshed key label.', [3, 4])
    add(1, '查看高级账户保护及外部安全计划入口', ['ri', 'ii', 'ai'],
        'Show advanced protection from authoritative eligibility/enabled data. Enrolled users open native management; eligible unenrolled users use an external enrollment URL. Daybreak uses its independent feature/plan guard and external URL; retain imported account-recommendation/lockdown consumers.',
        'Loading/error/plan/capability states cannot be treated as enrollment. External enrollment/program links do not themselves change account protections.',
        'Verify actual account protection/cyber eligibility and external navigation; preserve Codex/shared consumers before mode exclusion.', [3, 5])
    add(1, '经重新认证和确认停用高级账户保护', ['co', 'ai'],
        'Start fresh imported MFA reauth, retain account-bound confirmation URL state and show confirmation only while enabled. Before POST advanced_protection_mode/disable, re-read browser auth and require matching account plus fresh login; success invalidates protection/MFA/password eligibility and returns.',
        'Unmount aborts requests. Missing/stale auth returns reauth_required; aborted/unmounted completion cannot navigate or count disabled. Authentication failure and service errors retain separate recovery paths.',
        'Verify real recent-auth provider, server authorization, account binding and authoritative protection changes with separate authorization.', [3, 5])
    add(1, '确认启用或停用 Lockdown 模式', ['ii', 'zr', 'Br', 'Gr', 'Hr'],
        'Under account/user match and successful aas_eligible protection query, enable only after confirmation; disable uses its own direct toggle path. Cancel prior query, optimistically enable and PATCH lockdown_mode_enabled with signal, then invalidate/read back and report feedback.',
        'Same-account concurrent mutations are blocked; identity change/unmount aborts. Failed enable or abort rolls back the captured value and invalidates. Pending/loading disables controls; real restricted capabilities remain downstream behavior.',
        'Verify actual settings store, eligibility, rollback/readback and effective restrictions on external capabilities.', [3, 5])
    add(1, '查看登录会话及受信设备并记录安全复查', ['co', 'qa', 'Wa', 'fo', 'to'],
        'Load account-scoped active sessions and optionally remembered signed-out devices; preserve current/trusted/signed-out distinctions. A review intent adds user identity, forces a fresh mounted fetch and acknowledges once only after successful nonfetching post-mount data; acknowledge uses expectedIdentity and no retry.',
        'Missing review user disables that query; errors do not acknowledge. Acknowledgement failure retains the list and offers retry. Signed-out is informational, not proof of an unauthorized login.',
        'Verify real session/trusted-device query and recommendation acknowledgement; UI lists are not active connection probes.', [3, 6])
    add(1, '注销其他单个登录会话', ['qa'],
        'After the typed confirmation, revoke a noncurrent session only when session_id.trim() is nonempty, then invalidate the account sessions query.',
        'Current device and missing session ID cannot use this revoke path; preserve pending/error/confirmation behavior. Ending a session is distinct from removing remembered trust.',
        'Verify actual session revocation, selected identity and refreshed device state.', [3, 6])
    add(1, '撤销已注销设备的受信状态', ['qa', 'Wa'],
        'With trusted-device support, require is_trusted_device, can_untrust, noncurrent device, empty session ID and nonempty hash. POST trusted_devices/revoke with the selected hash and expected409 handling, invalidating sessions on success or failure.',
        'Nonmatching devices follow other session behavior; server conflict remains an error after refresh and cannot be silently treated as revoked.',
        'Verify actual remembered-device trust removal independently of active session logout and MFA push availability.', [3, 6])
    add(1, '确认注销账户全部会话', ['qa', 'Ka'],
        'Capture account/auth snapshot and POST accounts/logout_all with account header. Only a still-matching account/accountUserId and compatible userId may trigger local auth cleanup and logout navigation.',
        'Account/user switch or absent/invalid snapshot prevents local logout completion for the new identity. Failed service call cannot count global logout; preserve confirmation and pending state.',
        'Verify account-wide session invalidation and browser/native logout adapters under owned sessions and explicit authorization.', [3, 6])
    add(1, '打开委托安全历史页面', ['co', 'assignment-_o'],
        'The independent history-availability query gates the root entry; view=history lazy-loads SecurityHistorySettings with accountId and back navigation under Suspense.',
        'History load/availability failure does not prove no history. Imported history listing, filters and service implementation are retained as an unresolved delegated family.',
        'Recover and verify the history module separately; mounting its entry is not full history-feature acceptance.', [3, 7])
    add(1, '浏览筛选第三方登录应用及权限详情', ['la', 'ya', 'Xi'],
        'List legacy and third-party sign-in connections; retain all/apps/sites/ads tabs, locale-aware name and normalized-origin search, invalid-tab fallback and selected app detail. Query resource permissions by account/client, with expected404/409 and captured connector metadata queries.',
        'No data/error retries; refreshing is distinct from empty results. Account mismatch disables connector service queries; selected permission errors and partial metadata remain explicit rather than inventing access.',
        'Verify linked-app query, scope classification, third-party identity, connector metadata and actual permissions separately.', [3, 7])
    add(1, '确认断开旧版已授权客户端', ['la'],
        'After the selected legacy app confirmation, DELETE client_applications/{client_id} with account header, cancel its list query, remove only that legacy item and invalidate.',
        'Keep pending/error and selected-client confirmation. This legacy deletion is distinct from modern permission-target revoke and cannot silently remove other list entries.',
        'Verify actual legacy grant/token revocation and refreshed account application list.', [3, 7])
    add(1, '撤销登录应用的细分资源权限', ['Xi'],
        'POST client permissions/revoke using the selected target. Cancel exact permissions query, do not retry, replace cache with authoritative response and close relevant resource selection. Conflict409 refreshes with staleTime0 for review.',
        'While pending, suppress concurrent query refresh/edit. Preserve target/selected connector and expected404/409 errors; conflict is not automatic successful revocation.',
        'Verify actual supported target schemas, connector/plugin grants, server authorization and authoritative cache effects.', [3, 7])
    add(1, '确认断开第三方登录应用的个人或工作区授权', ['Wi', 'Gi'],
        'Expose disconnect only for supported user_grant/workspace_grant target and eligible non-identity-only detail. Capture target in a confirmation, POST permissions/revoke without retry, clear app permission query and invalidate the linked-app list.',
        'Differentiate personal/workspace confirmation scope. On409, refresh and offer Review connection rather than replaying the stale target; preserve pending and disconnecting callbacks.',
        'Verify actual grant scope, current target, token revocation and refreshed selected application after a conflict.', [3, 7])
    add(1, '创建、更改或重新认证重置账户会话锁定 PIN', ['co', 'kr', 'Dr', 'assignment-Nr'],
        'With the source feature flag and user identity, load locked_chats/status. Require a four-digit PIN and confirmation; create/verify/change use their distinct bodies. Reset first requests a challenge and delegates reauth, then posts the challenge header. Per-identity/generation tokens prevent stale UI completion; mutation generation rechecks reset status when another write intervenes.',
        'Duplicate operations, PIN lockout, invalid/mismatched input and stale identity prevent later transitions. invalid_pin/pin_locked refetch status. Selected reset-return effects are empty functions in this build; do not claim they automatically complete the challenge flow.',
        'Verify actual reset-return/delegated auth wiring, backend PIN/lockout semantics, project-cache effects and durable status; do not infer a usable reset merely from retained helpers.', [3, 8])
    add(1, '设置自定义 MCP 应用的 CSP 强制策略', ['gi'],
        'Under the source flag, show connectorEnforceCspInDevMode; PATCH account_user_setting with connector_enforce_csp_in_dev_mode and account header, then invalidate its settings snapshot.',
        'Missing settings/pending disables the switch and request failure shows error. Saving the preference does not prove enforcement in an actual custom app.',
        'Verify actual account setting identity and the downstream custom MCP app CSP consumer.', [3, 9])
    add(1, '设置 Codex 与 Office 的设备码登录许可', ['gi'],
        'Only for a personal account, show enableDeviceCodeAuth and PATCH account_user_setting feature enable_device_code_auth, then invalidate settings. Source text explicitly names Codex and Office consumers, so this control must not be discarded with a whole ChatGPT-labelled page.',
        'Missing settings, workspace account or pending request disables/hides the control; failure does not imply permission changed. The switch is an account policy, not a model-service submission.',
        'Verify effective Codex/headless and Office device-code authorization against the real identity provider; retain shared ownership.', [3, 9])
    add(2, '查看家庭成员并打开按角色授权的成员管理', ['Ie', 'Le', 'Be', 'Ve', 'He'],
        'Require allowed personal-account access and account/user-scoped family/members queries. Show accepted before invited members; route accepted by userId and invited by captured identifier. Owners or a non-owner self open the delegated member-settings editor; retain separate parent/child relationship/removal controls.',
        'Missing members with a stale member parameter removes that parameter; an unavailable member renders an explicit message. Child/member-role users do not gain owner controls; stale-data errors retain refresh feedback. Actual member settings/removal remain delegated.',
        'Verify family access selector, query identity, delegated member policy/removal and role authorization with synthetic or separately authorized family data.', [10])
    add(2, '打开新增家庭关联邀请', ['Ve'],
        'Owners may Add child; unaffiliated roles may Add family member. Child/member-role restrictions suppress entry except a member_role family consisting only of self. Open the imported invite dialog with account/family and forceTeen/forceParent policy props.',
        'Opening a dialog does not send an invitation or prove a new relationship. Preserve role guards and close state; delegated recipient validation and send service remain separate.',
        'Verify actual invite dialog, recipient policy, family creation/send and resulting membership with separate authorization.', [10, 11])
    add(2, '查找并打开待处理家庭邀请', ['Re', 'ze', 'Ve'],
        'Scan notification pages for an unreacted family-invite not already excluded as unavailable, require a family_group_id, and validate the invited family when no cached invitation state exists. A404 continues to the next candidate; the visible invitation button opens a delegated presentation flow.',
        'Malformed payload shows retry; other errors do not silently skip. Preserve identity-scoped family/notification invalidation. Selected recursion has no explicit repeated-cursor guard; no acceptance/rejection service is implemented by this local entry.',
        'Verify actual invitation presentation, accept/reject policies, notifications and family authoritative refresh.', [10, 11])
    add(2, '查看并关闭家庭关联解除通知', ['ke', 'Ae', 'Me', 'je'],
        'Read user/account-scoped graduation notices, group teen/parent messages and dismiss only captured notice_ids. Cancel exact query before POST, retain signal/current identity, remove those IDs from cache and invalidate; newer notices are preserved.',
        'Concurrent dismiss or wrong identity sends no request. Unmount aborts and invalidates without active refetch; failure retains the captured group for retry. Closing these notices does not perform family unlinking or age verification.',
        'Verify actual notice service, identity switches, cancellation and authoritative dismissal independently of family membership.', [10, 12])
    return result


def configuration():
    return dict(number=13, work='settings-safety-batch13-work', previousScope=19, previousCoverage=10,
        expectedState='2026-10-24T12:16:34.906116+00:00', selections=['storage', 'security', 'parental-controls'],
        scriptFiles=['settings_safety_batch13_specs.py', 'probe_settings_safety_batch13.cjs'],
        priorProbeAttempts=[dict(observations='probe-attempt-01.json', probeScript='probe-attempt-01.cjs',
            disposition='33 passed; the recursive invitation-page case expected an injected marker, but the named frozen function correctly binds itself. Corrected the owned assertion to verify the actual Re component and next cursor; frozen source unchanged.')],
        executionArtifacts=['probe-attempt-01.cjs', 'probe-attempt-01.json', 'probe-attempt-01-stdout.txt', 'probe-attempt-01-stderr.txt', 'probe-attempt-01-receipt.json',
            'probe-attempt-02.cjs', 'probe-attempt-02.json', 'probe-attempt-02-stdout.txt', 'probe-attempt-02-stderr.txt', 'probe-attempt-02-receipt.json',
            'storage-stdout.txt', 'storage-stderr.txt', 'storage-receipt.json', 'security-stdout.txt', 'security-stderr.txt', 'security-receipt.json',
            'parental-controls-stdout.txt', 'parental-controls-stderr.txt', 'parental-controls-receipt.json'],
        entries=[('storage', 'Storage', 'T40'), ('security', 'Security', 'T41'), ('parental-controls', 'Parental controls', 'T42')],
        sharedGoalConsumers=[dict(pageIndex=0, featureIds=['FSC-0059', 'FSC-0062', 'FSC-0063', 'FSC-0280', 'FSC-0281', 'FSC-0046'],
            relation='Storage management links delegate to existing worktree/archive goal owners while preserving selected hostId.',
            units=[('storage', 'dt')], acceptance='Verify hostId query encoding and reuse worktree/archive goals without another implementation.'),
            dict(pageIndex=2, featureIds=['FSC-0103'], relation='Owner-only safety notification entry opens the existing account notification manager.',
            units=[('parental-controls', 'Ve')], acceptance='Verify owner gate and /settings/notifications navigation against the existing category/channel goal.')],
        mechanisms=[
            ('Local storage service and scan snapshot', 'Local host alone receives deviceStorage; scanning/partial/error categories and query refresh are distinct from cleanup inventory.', [('storage', 'lt'), ('storage', 'nt'), ('storage', 'rt')]),
            ('Complete thread inventory and eligible descendant groups', 'List both archive states, recover measured IDs, reject duplicates and filter entire parent/descendant groups with complete byte accounting.', [('storage', 'Ie'), ('storage', 'Le'), ('storage', 'Fe'), ('storage', 'Re')]),
            ('Cleanup revalidation, confirmation and result ownership', 'Keep separate review/final confirmation, current snapshot checks and parent-scoped deleted/skipped/failed; backend atomicity is unproved.', [('storage', 'Qe'), ('storage', 'We'), ('storage', 'Je'), ('storage', 'ze')]),
            ('Account security query and subview orchestration', 'Account/user/feature/eligibility, URL view/action and account-bound reauth state remain distinct from product-mode naming.', [('security', 'so'), ('security', 'co')]),
            ('Password and MFA credential delegation', 'Separate password eligibility, MFA factor toggles, passkey WebAuthn/token navigation, rename and imported confirmation/setup/order implementations.', [('security', 'Na'), ('security', 'li'), ('security', 'Ra'), ('security', 'di'), ('security', 'fi'), ('security', 'Ba')]),
            ('Advanced protection and Lockdown lifecycle', 'Fresh account-bound auth, confirmation, abort and settings rollback/readback remain first-party policies over imported auth/provider interfaces.', [('security', 'ai'), ('security', 'ii'), ('security', 'Br')]),
            ('Session, trust and local logout identity', 'Separate live session revoke, remembered trust revoke, account-wide logout and once-after-fetch review acknowledgement; guard local cleanup by auth snapshot.', [('security', 'qa'), ('security', 'Wa'), ('security', 'Ka'), ('security', 'to')]),
            ('Linked grants and delegated security history', 'Preserve legacy deletion versus modern target revoke,409 review/refetch, connector metadata and unexpanded history implementation.', [('security', 'la'), ('security', 'Xi'), ('security', 'Wi'), ('security', 'assignment-_o')]),
            ('Account PIN identity and mutation generations', 'Preserve operation-kind token, identity/generation guards, lockout, confirmation, reset challenge and intervening-write recovery; empty effects remain explicit gaps.', [('security', 'kr'), ('security', 'Dr'), ('security', 'assignment-Pr'), ('security', 'assignment-Nr')]),
            ('Account security preferences and shared Codex consumer', 'Device-code setting explicitly covers Codex/Office; custom-app CSP has its own flag. Both use account setting service and shared invalidation.', [('security', 'gi')]),
            ('Family identity, roles and delegated membership', 'Keep personal access, scoped current/members queries, stale-member routing and owner/self/member/child role guards; managers remain delegated.', [('parental-controls', 'Ie'), ('parental-controls', 'Le'), ('parental-controls', 'Be'), ('parental-controls', 'Ve')]),
            ('Incoming and outgoing family invitation boundaries', 'Keep role-bound invite entry, notification pagination/unavailable-family fallback and delegated invitation presentation/send effects.', [('parental-controls', 'Re'), ('parental-controls', 'ze'), ('parental-controls', 'Ve')]),
            ('Graduation-notice identity and dismissal lifecycle', 'Keep captured notice IDs, account/current guards, signal/cancellation, cache removal and no-active-refetch cleanup; notice dismissal is not unlink.', [('parental-controls', 'ke'), ('parental-controls', 'Ae')])],
        gaps=[['Actual local scanner and app-server source/parent normalization, inventory completeness, descendant deletion and persistence remain assigned interfaces.', 'Version/host capability, concurrent writes, atomicity and real device byte/storage effects require owned integration.'],
            ['Security queries, auth/MFA/passkey/order/history/PIN-reset providers, grant/connector services and effective security consumers remain assigned interfaces.', 'Empty PIN reset-return effects, actual product/shared consumers, identity changes and durable service effects remain explicit integration gaps.'],
            ['Personal access and family queries, invitation/member/removal managers and notification services remain assigned interfaces.', 'Actual family role authorization, incoming/outgoing invitation effects, graduation notice service and mode/shared consumers remain unverified.']],
        modules=['storage/settings', 'account-security/settings', 'family/settings'],
        consumers=[['hosts/device-storage', 'hosts/app-server', 'tasks/descendant-inventory', 'tasks/cleanup', 'worktrees/settings', 'archives/settings'],
            ['app/account-access', 'account/auth-mfa', 'account/security-settings', 'account/sessions-trust', 'account/linked-grants', 'account/pin', 'account/security-history', 'codex/device-code-auth'],
            ['app/account-access', 'family/identity-queries', 'family/invitation-manager', 'family/member-settings', 'family/graduation-notices', 'notifications/settings']],
        dependencies=[['React/UI/query/state packages', 'deviceStorage service', 'app-server discovery/list/read/delete', 'existing archive/worktree managers'],
            ['React/UI/query/state packages', 'account security/settings/sessions/grant services', 'auth/reauth/MFA/WebAuthn providers', 'delegated history/PIN reset/order modules'],
            ['React/UI/query/state packages', 'personal-family query/notification services', 'delegated invitation/member/removal managers']],
        decisions=['Separate local measurement, complete descendant inventory and reviewed cleanup; reuse archive/worktree owners with host context.',
            'Separate credentials, protection, sessions/trust, grants and PIN state machines. Retain device-code policy as an explicit Codex/shared consumer.',
            'Separate role/identity orchestration, delegated invitations/member management and notice-only dismissal; reuse account notifications.'],
        title='存储、安全与家庭设置：清理重查、共享认证及角色边界',
        modeReason='Storage uses chatGptOrCodex; security/family use chatGpt access. Shared access is not a mode label, and the Security device-code control explicitly names Codex. No entire page is excluded.',
        firstParty=['storage scope/scan/review/revalidation policy', 'account security control/identity/URL state', 'session/trust/grant/PIN lifecycle', 'family role routing and notice dismissal'],
        externalize=['React/UI/query/state packages', 'local storage/app-server implementations', 'account/auth/MFA/security/grant services', 'family/invitation/member and notification services'],
        probeDescription='仅执行冻结源码函数/回调与合成库存、身份、查询、服务替身；未扫描真实磁盘、删除会话、修改认证或家庭资料、调用模型服务',
        modeSummary='Security中的设备码许可明确供Codex与Office共用；不按ChatGPT标签删除整页。Storage复用归档/工作树，家庭安全通知复用FSC-0103。',
        boundarySummary='本地清理、账户会话注销、设备信任撤销及家庭通知关闭具有不同对象；委托模块与空PIN返回effects保留缺口。',
        reportFacts='明确父会话/子代理重查及非原子边界、账户认证/信任/授权区别、Codex设备码共享策略与家庭角色/通知生命周期。',
        summaryPoints=[
            'Storage仅本机展示扫描服务；清理按父会话及所有子代理过滤和计量，先审阅再确认，重查变化/执行中/不完整条目并跳过。验证与删除不是已证明的原子事务。',
            'Security区分密码/MFA/通行密钥、账户高级保护、Lockdown、会话注销、设备信任和第三方授权；真实认证、历史、硬件密钥订购等继续由独立接口或委托模块负责。',
            '设备码登录开关的源码明确列出Codex和Office用途；CSP是另一个有独立flag的账户偏好。访问家族不能替代产品模式处置。',
            'PIN有身份/代次和重置挑战保护；所选build的两处返回effects为空，不据此声称重置返回路径已接通。',
            'Parental controls保留角色与成员身份检查、邀请委托与不存在家庭的404续查；解除关联通知的Close仅提交捕获notice_ids，不能当作解绑或年龄验证。'],
        nextQualification='Continue trusted-contact/safety/cloud-settings from saved dispositions. Reuse existing archive/worktree/notification owners. Runtime/account/family services, delegated managers, actual mode and full PIN-reset return remain task-local integration gaps. No model authorization remains.')
