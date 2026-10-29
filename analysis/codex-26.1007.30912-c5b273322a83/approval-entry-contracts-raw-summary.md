# MCP 电脑应用审批：选定静态契约

基线 `codex-26.1007.30912-c5b273322a83`。本补充追踪现有 `approval`、`computer-use` 功能候选中的一个分支。5 个冻结 JS 的完整 Program 解析用于选择范围，语义审查限定为 26 个完整函数或成员、6,845 个选定 AST 节点、8 对导入／导出绑定和 30 条源码证据。运行观察 0，确认模式排除 0，完整功能分母仍未知。

[结构化契约](approval-entry-contracts.json)、[源码证据](evidence.jsonl)、[范围校验](validation.json)。独立审查记录保存在 `peer-review/`；校验通过不替代运行验证。

已接上的组件路径是 `PendingRequestItemPanel.Ur` 的 `mcpServerElicitation` 分支 → MCP 面板 `vt` → 应用审批包装 `lt` → 应用审批卡片 `E`。面板先尝试浏览器审批，再判断电脑应用审批，否则进入其他 elicitation 类型。命令／文件审批与权限请求有独立分支，不能把本补充算成整个审批功能组完成。

应用判定要求 `mcpToolCall`、归一后为 `computer-use` 或其前缀的 connector、非空持久化选项以及可用的应用显示名。显示名优先取展示参数，再取工具参数。该判定没有证明请求提供者身份、模式或权限条件。

卡片以 `[hostId, conversationId, requestId]` 组成请求键，阻止同键重复提交；拒绝 Promise 时仅在键仍匹配时解除本地提交状态。接受动作在调用回复接口之前写入本地“曾批准”atom，所选失败回调未回滚该写入。成功回调调用 `onRequestSettled`；所接函数 `K8n` 按选择器判断条件调用 `FP`，其焦点依赖尚未展开，不能用此回调证明后台送达、审批执行或数据持久化。

“Always allow”取决于 `always` 选项；主动作按是否支持 `session` 发送会话持久化，否则不带持久化值；拒绝发送 `decline`。响应构造器将 `accept` 的 `content` 默认设为 `{}`，拒绝／取消设为 `null`，持久化放在 `_meta`。高风险在这个卡片中选择警示标题。`ChatGPT` 文案没有相应的显式模式判断，不能据此排除该分支。

回复使用由 shared `KI` 选择的 facade。`KI` 可以返回 host router、当前 client RPC 或等待连接的 facade，实际实例仍未确认。另已定位两处同名完整成员候选：一个 getter 转发，另一个把回复交给 `L7t`；它们与卡片实际 receiver 的对应关系尚未建立。

`L7t` 核对待处理请求、限制 `openai/userVerification` 的接受动作、检查审批安全性。角色辅助函数返回真值时，它转交任务拥有者，异步错误由日志处理；否则向注入的 sender 分派响应后调用状态处理接口。未知／空角色也能走后一分支，不能直接把它判为实际 owner。该函数没有等待送达确认，所调用状态 helper 尚有未展开部分。注入 sender、动态角色、下层 RPC 返回值和真实状态恢复仍是断点。

选定安全谓词对 `executionBound` 的持久化拒绝条件限定为 `_meta` 是非空、非数组对象且其 `persist` 非空；不能改写成无条件禁止全部持久化。完整规则还依赖尚未展开的 `z8t`。

共享审批卡片的提交回调检查 loading／disabled。其快捷键启用表达式要求 `Fqc()` 返回真、没有禁用快捷键且不在 loading；输入框焦点检查在此函数中仅影响 autoFocus。控件和快捷键的实际运行行为尚未观察。

后续需要核对待请求生产方的模式及功能条件、facade 注册和接收实例、响应确认层次、atom 与会话状态的持久化，以及错误／请求替换／窗口重开后的表现。具体断点见结构化契约 `APPROVAL-U01`–`APPROVAL-U07`。这些证据可用于设计审批职责边界和回归场景，尚不足以确认独立构建或完成复刻。

三个 AST producer 与各次契约生成均保存 exact source、stdout、stderr、退出码及 hash；前两次契约输出已在 `attempt-04-products/`、`attempt-05-products/` 留存。独立审查将快捷键、角色、安全条件和 helper 效果的措辞收窄到已读范围。目录未归档五个完整原 JS 资产；审查日志含有界函数摘录，属于分析材料，尚未生成客户端维护源码。没有执行目标、CLI、UI、网络或模型任务。
