# Thread / turn 第一方操作契约目录

固定基线 `codex-26.1007.30912-c5b273322a83`。本目录细分原 36 个泛化 feature groups 中的 `thread-lifecycle` 与 `thread-turn-stream`，得到 7 个操作方法、19 个旧字面调用、8 个完整函数/成员以及 9 个已见分支契约。仅 4 个旧调用静态绑定 RWC-MANAGER，15 个 receiver 仍未解决；确认 UI→操作和 runtime method correlation 的数量均为 0。7 方法目录不是已完成 7 项业务功能，也不改变原 36 组完整目标。

| 方法 | 第一方已见契约 | 主要边界 |
| --- | --- | --- |
| thread/start | MCP extension startup 固定 ephemeral/read-only 参数；返回 thread.id；响应后检查账号与 abort 并调用清理 helper | 普通新会话 UI、receiver、清理效果、实际 mode 未证实 |
| thread/resume | Dfn 完整成员透传参数；将返回 thread 合并到 live manager state；回原 response | sV 映射、调用方与持久化未证实 |
| thread/fork | 先创建 RPC，再同步项目/状态/可选边界内容；created 结果可携带 failed synchronization | n/d 参数构造、成功 fork、源身份持久化未证实；旧样本仅负路径 |
| thread/archive | 类内箭头传 threadId 并回 transport promise | 箭头本身无 archive UI/cache/storage mutation；实际归档恢复未证实 |
| turn/start | Uun optimistic inProgress/active；响应接受后合并实际 turn；已知提交失败与 outcome-unknown 分别处理 | 接受不等于完成；另一 tool-output branch 显式发 turn/start 并转为 turnId |
| turn/steer | toolOutput 为 null 时透传 request 与 clientUserMessageId；无本地状态写入 | tool-output 非空转到 turn/start；活动 turn 校验与竞态未证实 |
| turn/interrupt | 两个类内箭头传 threadId/turnId；async 形式丢弃返回值，另一形式透传 | 无本地终态写入；command/exec/terminate 样例不能作为 turn 中断证据 |

所有 operation/variant 引用精确旧 REQUEST-WRAPPER-AST、FEATURE 与 functional-entry-ledger IDs；源码范围为已有完整函数/成员，逐段核固定源哈希与原 byte range。旧直接 sendAppServerRequest 的 archive/interrupt 字面入口单列，不能仅按 method 字符串与 manager 分支建立业务等价。HTTP BY/Gxn/AW request facade 与 Dfn manager RPC、HTTP stream cancel 与 turn/interrupt 分别记录。

保存 schema 的 stable/experimental 参数与返回字段分别列出。七个 stable 请求与保存 public comparison 一致；experimental fork 有字段差异；start/resume/fork/turn-start 返回嵌套字段也有差异，因此不宣称完整协议相等。resume 的 history/path 与 fork 的 path 只在 experimental 字段中，不能以描述文字向 stable 添加字段。MCP startup 的 permissions 与 tool-output 分支也不可据此推定实际 runtime mode。public repo/tag/commit 仅为保存协议候选来源，不作客户端/CLI 运行版本测量。

Thread/Turn 状态、必要通知与 ephemeral/history/path/fork identity 只作为保存协议声明关系；发出顺序和 desktop handler 未验证。唯一已授权 synthetic read-only task 的旧 read/storage/restart 摘要提供有限行为背景，未将 UI 映射到本目录 RPC。保留三次恢复失败、旧 storage decoder 漏记及 submit 状态的 false success indicators，不增加模型任务，也不重读实际 profile、数据库、rollout、账户或个人历史。

本次只读已存元数据与固定源码，没有执行目标、CLI、UI、网络或模型任务，没有新 AST 解析或复制第三方实现。旧 evidence journal 已整字节快照，后续发布变化不影响本目录 selected 原行定位。独立构建决定仍需实际 caller/transport、完整通知 reducer、参数构造和持久化 helper 依据，以及另行授权的成功/失败/取消/恢复行为样例。本目录不提供兼容替代方案自动升级验收，也不关闭原分析计划的完整功能目标。
