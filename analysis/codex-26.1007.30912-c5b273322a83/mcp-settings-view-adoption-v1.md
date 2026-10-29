# MCP 应用设置视图：补入正式范围

已将 `/settings/plugins/:server/:toolName` 的实际显示行为登记为 FSC-0507「打开并查看所选 MCP 应用的设置视图」。它选择宿主和服务/工具，匹配视图，再显示旧版读写工具视图或新版嵌入视图；不同于既有的 MCP 服务配置和打开扩展目录。

保留 Electron、认证与访问状态守卫、未找到状态、受开关控制的重新获取、加载/失败处理，以及 component/app 生命周期、嵌入背景和深链参数。T16 拥有该目标，源码模块建议为 renderer/features/mcp/settings-view.tsx；宿主通信、权限/CSP、实际持久化和释放仍是明确外部边界。

功能、操作、未执行规格、任务覆盖、模块职责、路由来源关联及实施计划补充已同步采用。当前 505 项功能、572 个不同操作、125 支撑、1794 条未执行规格和 51 项任务；模式为 502 unknown / 3 shared。未关联来源从 715 降为 714，其中 15 项明确机制；20 个命令消费者缺口保持。没有整功能或模块排除。

复用原路由分析，仅对 26KB 的视图文件补做两次定向 AST 选择，共 10484 节点；未重跑整包 REA。8 条新增规格均未执行，没有目标求值、客户端启动、模型/服务调用或客户端实现。完整分析和独立构建仍未证明。

[采用合同](mcp-settings-view-adoption-v1.json) · [功能清单](feature-scope-v49.json) · [规格](feature-scope-v46-scenarios.json) · [覆盖](restoration-coverage-v40.json) · [职责](feature-module-ownership-v15.json) · [实施计划补充](implementation-plan-v11-mcp-settings-view-addendum-v1.json)
