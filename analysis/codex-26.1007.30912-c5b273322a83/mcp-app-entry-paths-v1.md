# MCP 应用深链与全局视图

FSC-0509「解析插件应用深链并打开目标入口」归入 T17；FSC-0510「打开 MCP 应用全局视图并恢复关联上下文」归入 T16。分别保留加载、未找到、歧义、插件激活恢复，以及宿主选择、托管会话恢复、取消、连接重试和视图生命周期。复用现有插件详情、连接与设置视图接口。

托管上下文的 Codex 匹配路径是 `/mcp-app/connector_openai_code_review/pull_requests.open`，其他托管路径默认选择 ChatGPT 上下文；另有独立的 app-server 视图分支。这个 productContext 是路径选择结果，不是客户端全局模式。全局视图保留为来源限定的 shared；不能因文件名或会话包装符号含 ChatGPT 而整页删除。深链目标的全局模式归属仍为 unknown。

提出三个可维护职责：插件深链解析、MCP 全局视图、托管会话协调器。`hosted-mcp-conversations-v1` 只确认为逻辑缓存键；其物理存储权威、跨窗口同步及重启耐久性仍未验证。第三方库通过依赖管理引入，不恢复其打包实现。

当前 508 项功能、575 个不同操作、125 项支撑、1820 条未执行规格、51 项任务；111 项限定职责提议、48 个粗 facade。未关联来源 710 项，其中40项已有明确机制决定，670项仍需目标或机制决定。有效模式504 unknown / 4 shared。506项旧功能、1802条旧规格及两套任务图依赖边保留。

本批只解析冻结源码并复用已有证据；178个来源片段、12条事实、18条未执行规格已校验并采用。没有客户端启动、目标代码求值、模型/服务调用、运行通过或构建通过。完整分析与客户端实现尚未完成。

[分析合同](mcp-app-entry-paths-v1.json) · [功能](feature-scope-v51.json) · [规格](feature-scope-v48-scenarios.json) · [职责](feature-module-ownership-v17.json) · [实施计划补充](implementation-plan-v11-mcp-app-entry-addendum-v1.json)
