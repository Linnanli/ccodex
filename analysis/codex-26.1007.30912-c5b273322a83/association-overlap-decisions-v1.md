# 既有关联与重叠的源码决定

固定处理 feature v27 的12项关联与3项重叠，15项均已给出有边界的源码决定。A01/A02/A12的业务父功能仍未确定；15项均保留实际集成限制。373项功能、48任务、1216条未执行规格和模式分类不变。

|编号|决定|任务设计归属|
|---|---|---|
|AO-A01|read-only-facet; business-parent-unresolved|T01|
|AO-A02|read-only-facet; business-parent-unresolved|T01|
|AO-A03|composite-split; project-action-and-connection-navigation|T01, T05, T19|
|AO-A04|supporting-mcp-auxiliary-session; distinct-from-composer-start|T16, W05|
|AO-A05|supporting-raw-resume; distinct-from-page-hydration|T03, W05|
|AO-A06|existing-user-operation; scoped-fork-association|T03, W05|
|AO-A07|supporting-prewarm-cleanup; distinct-from-user-archive|T03, W05|
|AO-A08|shared-lifecycle-state-support; bounded-lexical-chain|T03, W05|
|AO-A09|shared-lifecycle-state-support; bounded-lexical-chain|T03, W05|
|AO-A10|shared-lifecycle-state-support; bounded-lexical-chain|T03, W05|
|AO-A11|shared-lifecycle-state-support; bounded-lexical-chain|T03, W05|
|AO-A12|derived-capability-support; business-parent-unresolved|W06|
|AO-O01|related-command; distinct-api-contracts-equivalence-unresolved|T01, T08|
|AO-O02|shared-remote-entry-subset; distinct-local-picker|T14, T05, W06|
|AO-O03|distinct-ssh-deeplink-workflow; shared-domain-interface-candidate|T19, W06|

以下路径都是新的维护职责建议，不表示恢复原工程目录或生成客户端实现。

## AO-A01

Ks 是 General 的只读 Managed 更新策略行，只有 p(wr) 的显示条件，没有更新动作或偏好写入。把呈现交给 T01；保存的证据不足以将其归到某个已有更新业务功能，不能把它算作独立用户操作。

维护位置：`apps/desktop/src/renderer/features/settings/general/managed-update-policy.tsx`。

剩余边界：准确未闭合边界是 wr 所代表策略的实际 provider 与更新业务消费者；不以行标题推定父功能。；实际 host/account/平台/gate 值、模式和产品表现未观察；源码关系决定不充抵实际行为验证。

## AO-A02

Eo 接收 access 并显示摘要/tooltip；Co/wo/To 的模型或账户读取与显示分流不构成启用动作。呈现归 T01，保留 access 输入边界；没有证据证明它就是 FSC-0280 或其他账户能力功能。

维护位置：`apps/desktop/src/renderer/features/settings/general/access-summary.tsx`。

剩余边界：实际 access provider、账户匹配结果及其业务父功能未闭合；不从 Daybreak 标签推定共享模式或权益。；实际 host/account/平台/gate 值、模式和产品表现未观察；源码关系决定不充抵实际行为验证。

## AO-A03

保留 FSC-0045 为 connected host 的远程建项目动作；非 connected host 的 ps 链接目标精确为 /settings/connections/wsl，导航职责接 T19。无 host 只是安装说明。三种分支不合并成一个创建操作，链接到页面不证明页面内连接操作已执行。

维护位置：`apps/desktop/src/renderer/features/projects/open-remote-project.ts`、`apps/desktop/src/renderer/features/connections/wsl-entry.tsx`。

剩余边界：Wuc 的动态门槛、消息真实送达、ht provider 和保存/重开未验证；没有把导航等同连接成功。；实际 host/account/平台/gate 值、模式和产品表现未观察；源码关系决定不充抵实际行为验证。

## AO-A04

旧 TTC-OP-thread-start 与 MCP queryFn 是同一冻结范围，带 ephemeral:true、read-only 权限及 mcp_extension_host 来源。作为按 host/account/user 管理的 MCP 辅助会话保留；不关联为普通 composer 的 FSC-0048，也不增加用户功能。

维护位置：`apps/desktop/src/renderer/features/mcp/auxiliary-session.ts`。

剩余边界：pending requests/drain、完整 MCP 消费者、实际 ephemeral 与 unsubscribe 后效仍未闭合；本地 retire/abort 检查不证明服务端取消。；实际 host/account/平台/gate 值、模式和产品表现未观察；源码关系决定不充抵实际行为验证。

## AO-A05

用较新的 resume-provider-resolution 纠正旧 backlog 的 unresolved-user-entry：raw resumeThread 已有环境恢复 draft 调用者，参数、返回和状态更新与页面 resumeConversation/hydration 不同。保留为支撑，旧操作排队为0，不新建用户功能或把两接口合并。

维护位置：`packages/app-server-client/src/raw-thread-api.ts`、`apps/desktop/src/renderer/features/tasks/environment-recovery.ts`。

剩余边界：KI 实际选择实例、完整 raw API 消费者、服务/通知/持久化及 draft 展示未验证。；实际 host/account/平台/gate 值、模式和产品表现未观察；源码关系决定不充抵实际行为验证。

## AO-A06

旧 fork 调用保留到已定义 FSC-0047/T03 的源码关联。header/sidebar 经各自条件选择本地或 worktree 分支，创建身份、同步、placement 与导航分别失败；不能把设置后失败当作未创建并自动重试，也不与普通 start 合并。

维护位置：`apps/desktop/src/renderer/features/tasks/fork-thread.ts`。

剩余边界：实际 KI/RPC 到 manager、worktree 创建、client ID 对账、持久 placement/pane 与重启未验收；target-turn 的具体 UI 入口仍未闭合。；实际 host/account/平台/gate 值、模式和产品表现未观察；源码关系决定不充抵实际行为验证。

## AO-A07

旧 archive 箭头作为 Dfn constructor 注入 Pdn 的 archiveThread；discardPrewarmedThread 对 cloud 与其他预热走不同清理，失败被吞掉。职责归 T03 的预热生命周期；明确不把它当成用户 FSC-0046 归档入口。

维护位置：`packages/app-server-client/src/prewarm-lifecycle.ts`。

剩余边界：实际 prewarm 实例、cloud 标志和启动/失效调度仍未知；吞错不构成服务清理成功证明。；实际 host/account/平台/gate 值、模式和产品表现未观察；源码关系决定不充抵实际行为验证。

## AO-A08

thread/started 归 T03 会话/turn 状态支撑。较新的 Program binding 证据确认 Dfn.onNotification→Vnn 及 Vnn→unn/Rnn，替换旧记录中这几条同名边未确认的描述。unn 调 upsertConversationFromThread(thread,live) 并广播；所选 T7t upsert 区分更新元数据与新建 needs_resume 会话，不能视为已完整 hydrate turns。

维护位置：`packages/app-server-client/src/notifications/router.ts`、`packages/app-server-client/src/notifications/reducers.ts`。

剩余边界：已确认的词法边不覆盖所有 helper、动态 receiver 或初始化。准确剩余边界为 transport ingress/manager 实例、注入的状态/存储、UI 订阅者、实际到达/回放与持久化。；实际 host/account/平台/gate 值、模式和产品表现未观察；源码关系决定不充抵实际行为验证。

## AO-A09

turn/started 归 T03 会话/turn 状态支撑。较新的 Program binding 证据确认 Dfn.onNotification→Vnn 及 Vnn→unn/Rnn，替换旧记录中这几条同名边未确认的描述。Rnn 处理不存在的 conversation、匹配 turn/current placeholder、新建 turn 和既有终态保护；不能仅因收到 started 名称就无条件覆盖终态。

维护位置：`packages/app-server-client/src/notifications/router.ts`、`packages/app-server-client/src/notifications/reducers.ts`。

剩余边界：已确认的词法边不覆盖所有 helper、动态 receiver 或初始化。准确剩余边界为 transport ingress/manager 实例、注入的状态/存储、UI 订阅者、实际到达/回放与持久化。；实际 host/account/平台/gate 值、模式和产品表现未观察；源码关系决定不充抵实际行为验证。

## AO-A10

turn/completed 归 T03 会话/turn 状态支撑。较新的 Program binding 证据确认 Dfn.onNotification→Vnn 及 Vnn→unn/Rnn，替换旧记录中这几条同名边未确认的描述。Rnn 先检查 drainBefore；unknown conversation、input buffer 清理、turn 状态/时长和 unread/事件有分别的条件。回放回调不证明真实回放顺序或持久化成功。

维护位置：`packages/app-server-client/src/notifications/router.ts`、`packages/app-server-client/src/notifications/reducers.ts`。

剩余边界：已确认的词法边不覆盖所有 helper、动态 receiver 或初始化。准确剩余边界为 transport ingress/manager 实例、注入的状态/存储、UI 订阅者、实际到达/回放与持久化。；实际 host/account/平台/gate 值、模式和产品表现未观察；源码关系决定不充抵实际行为验证。

## AO-A11

error 归 T03 会话/turn 状态支撑。较新的 Program binding 证据确认 Dfn.onNotification→Vnn 及 Vnn→unn/Rnn，替换旧记录中这几条同名边未确认的描述。Rnn 的 error 分支添加带 willRetry/codexErrorInfo 的错误项，没有直接写 status=failed；它与 turn/completed 中的 failed 终态保持不同。

维护位置：`packages/app-server-client/src/notifications/router.ts`、`packages/app-server-client/src/notifications/reducers.ts`。

剩余边界：已确认的词法边不覆盖所有 helper、动态 receiver 或初始化。准确剩余边界为 transport ingress/manager 实例、注入的状态/存储、UI 订阅者、实际到达/回放与持久化。；实际 host/account/平台/gate 值、模式和产品表现未观察；源码关系决定不充抵实际行为验证。

## AO-A12

保留五条件派生 predicate：gate 真值、projectChatGptProvisioning/projects 存在、identity 与 local-projects query data 非空。已连接的读取者是 chatgpt-project-settings-dialog 的 c(rt)，不能把它改写成已确认的 Codex 项目动作、禁用条件或仅凭文件名排除。设计上置于 W06 项目能力接口，实际父功能仍未确定。

维护位置：`packages/projects/src/local-project-capability.ts`。

剩余边界：准确未闭合边界是该 s 值的实际 action/visibility 消费者及 Codex/shared 保留用途；当前37-owner中 Project domain 仅为设计协作，不证明消费者身份。；实际 host/account/平台/gate 值、模式和产品表现未观察；源码关系决定不充抵实际行为验证。

## AO-O01

FSC-0023 用注入 hotkeyWindowHotkeys.setHotkey(value/null)，处理 success/error/state；FSC-0068 是 commandId 参数化的 set-codex-command-keybinding，支持 set/append/replace/remove/reset/clear。两处均涉及 hotkeyWindow 和 keymap 缓存协调，但不足以证明 setHotkey 的实现等同该 RPC。保留两个目标与各自错误/捕获合同，抽取缓存协调接口；不按标题合并定义。

维护位置：`apps/desktop/src/renderer/features/shortcuts/command-keybindings.ts`、`apps/desktop/src/renderer/features/settings/general/popout-hotkey.tsx`。

剩余边界：准确等价边界为注入的 hotkeyWindowHotkeys.setHotkey provider 与 command RPC 后端注册/保存实现；原生 registration、持久化及冲突行为未观察。；实际 host/account/平台/gate 值、模式和产品表现未观察；源码关系决定不充抵实际行为验证。

## AO-O02

FSC-0105 的 Ut: y!=local 时 qe({hostId:y})，local 时 Ke(scope)。完整 import 把 qe→k$t、Ke→j$t；导出把 k$t→B0r。与 FSC-0045 的 General Kr→k$t→B0r 为同一远程弹窗发送者，两入口均不传 setActive。可共用远程 open helper；FSC-0105 的本地 j$t→z0r→目录 picker 路径仍独立，不能据共享子分支合并整个功能。

维护位置：`apps/desktop/src/renderer/features/projects/open-remote-project.ts`、`apps/desktop/src/main/projects/project-folder-picker.ts`。

剩余边界：共享发送者不证明 Wuc 门槛通过、弹窗挂载、项目创建或相同实际 host。local picker 的注入 manager/provider 与远程 createRemote 仍分开；保存和重开未验证。；实际 host/account/平台/gate 值、模式和产品表现未观察；源码关系决定不充抵实际行为验证。

## AO-O03

FSC-0154 的 ssh/add 深链先检查 name/alias、绝对 project path、connect，再登记/等待连接和登录，可复用缓存项目，createRemote 传 reuseExisting:true，最后选择并导航到 Codex composer。WSL/环境 Add project 经 B0r 打开交互弹窗。保留 SSH 工作流与其 abort/部分完成语义；createRemote 同名接口只支持项目域协作建议，不证明实际 provider 相同或整个操作重复。

维护位置：`apps/desktop/src/renderer/features/connections/ssh-add-deeplink.ts`、`packages/projects/src/contracts.ts`。

剩余边界：projects.createRemote 的实际注入对象、连接服务、缓存/持久化和重开未验证。abort 抑制后续工作不回滚已经创建的 host/project。；实际 host/account/平台/gate 值、模式和产品表现未观察；源码关系决定不充抵实际行为验证。

完整引用、原始字节范围、任务和既有职责归属见同名 JSON；证据15行按九字段发布。

下一项为 SD-02 独立运行时采用决定：复用已有能力差异与发行来源证据，明确每组保留能力的来源、构建输入、provider或准确外部缺口。完整分析尚未完成。
