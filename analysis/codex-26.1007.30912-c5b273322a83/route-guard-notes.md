# 路由包装层静态复核

冻结基线 `codex-26.1007.30912-c5b273322a83`。已校验 156 条原始 UTF-8 范围及 SHA-256；仅解析源码，没有执行目标、操作 UI 或读取个人数据。所有路由结构 `mode` 保持 `unknown`。

详细条件、未知项和证据见 [route-guard-notes.json](/Users/nallylin/Documents/code/ccodex/.analysis-local/feature-work/route-guard-notes.json)。

| 包装层/组件 | 静态结论 |
| --- | --- |
| oZ | allowWork=true 选择 chatgpt.conversations；该策略接受 chatgpt 或 Work 云端 allowed，仍受 in_app_chat 配置约束。没有直接 productMode 检查。 |
| WKa | WEB: ID 重定向 /；local-chatgpt: 与 temporary-chat=true 跳过预取，仍返回子页面。 |
| zKa | 订阅能力后直接返回 children，没有读取能力结果或阻止路由。 |
| gHa | 真实 OrbitConversationRoute 完整函数直接返回 children；父 mHa 的条件仍适用。 |
| mHa | 真实 FeatureNavigationRoute 依据 /dots 路径、门控和 workspace access 决定 loader、Outlet 或重定向。 |
| tFs | local 与 Work 访问状态的 allowed 联合判定，不是 ChatGPT chat-mode 专属条件。 |
| hFs | 依据文件/分享路径例外、chatgpt 能力门控及 library availability，在 library、space、sites 之间路由。 |
| ChatGptProjectSettingsDialog | 同一侧栏函数包含 Work 模式分支、本地 Codex task 入口、linked local project 与 settings 调用；调用条件不要求 chat 模式。 |

ChatGptConversationPage 的两个实际 Route 为 `/c/:conversationId` 与 `/g/:gizmoId/c/:conversationId`，均使用 `oZ(allowWork=true)` 加 `WKa`。该事实不能单独决定是否排除页面，因为保留 Work/cloud task 路径的用途和下游限制仍未验证。

共享项目设置证据只证明代码复用关系：最终平台守卫、账号权限、侧栏可见性和下游对话框规则仍为未知。不能仅按 ChatGpt 文件或组件名删除。

JSON 的每条 note 包含 componentNames、routeComponentCandidates、conclusion、conditions、unknowns、evidenceIds。evidence 保存 sourcePath、sourceHash/sourceSha256、byteRange、spanHash/spanSha256 和完整对应片段，方便 guardReviewReferences 关联。

项目入口补充（guard-sFs-project-entry）：`/g/:projectId/project` 的 `sFs` 最终使用默认 `oZ(allowWork=false)` 包装 `OJa`，但在门控关闭且未找到账号范围内的唯一 local-project 映射时，可先重定向 `/` 并保留 `chatGptProjectId`。这个专属 URL 的守卫与共享侧栏项目、设置及本地 Codex task 复用关系不同，不能直接等价排除。有效门控、最终页面和 home 消费模式仍未知。完整函数、别名与映射定义均附精确 byteRange/spanHash；本次未做全文件 AST 解析。
