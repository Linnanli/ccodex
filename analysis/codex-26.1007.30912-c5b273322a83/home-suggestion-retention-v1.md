# 首页建议的保留边界与交互合同

首页建议不能随整个 ChatGPT 命名模块删除。已连接真实的懒加载/导出/首页 slot：非 `chat` composer 首页在原条件下进入该组件；`chat` 入口不挂载这组 ambient slot。

| 判断轴 | 固定源码行为 | 恢复决定 |
| --- | --- | --- |
| 外层首页入口 | controller、非chat、布局和当前入口隐藏条件 | 保留共同首页入口，不能将导入存在算作实际挂载 |
| 生成建议准入 | 调用方开关、runtime enabled、projectRoot、个性建议准入 | 保留原组合条件，复用已闭合的应用资格查询 |
| 建议来源 | loading/readiness→pending；override直接返回；eligible且personalized→generated，否则curated | 查询、来源和显示分别建模 |
| 派生surface | detail-level=STEPS_PROSE时为chatgpt_work，否则codex | 与全局产品模式分开；不按名称删除整个分支 |
| 预设分类/入门卡 | 派生Work surface、curated、provider、plan及独立开关 | 条件保留；仍缺少把它们整项判为ChatGPT专属的证据 |

生成建议按插件可用性过滤后最多3项。缺失但可安装的插件走连接引导；已安装但停用/不可用的插件建议被过滤。实际展示还受读取完成、loading与root等条件控制。

| 点击效果 | 接受时机 | 失败与异步边界 |
| --- | --- | --- |
| 预填输入框 | 预填前先标记接受 | 后续预填失败没有统一回滚 |
| 连接插件 | generated项在成功回调接受并刷新 | 点击handler未await安装完成；finally可能先清active ID |
| 入门卡直接建任务 | await创建流程返回后接受 | root缺失不创建；Codex Home政策AbortError静默；导航回调失败不证明没建出线程 |

刷新是独立mutation，成功后使建议查询失效；回调存在和刷新控件实际可见还有不同条件。

已登记6项源码操作候选：生成建议浏览、刷新、预填、插件连接、预设分类选择和入门任务创建。它们尚需与当前525功能/603操作核对重叠，不能直接算作6个新增功能，也不能声称现有清单已完整覆盖这些交互。

本批11项事实、66个定位单元、4条明确ESM策略连接和16项源码检查通过；另列12项未执行观察条件。8份当前权威清单、模式数量、source用途数量及实施图保持。首次验证脚本处理bare变量的同跨度AST节点时出错，已修正验证器并保留初稿；冻结程序没有解析失败。

本批未启动客户端、求值目标JS、提交模型任务或调用服务。实际挂载、有效实验/账户、插件连接、建任务及持久化仍未验证；整体分析尚未完成。

[结构化合同](home-suggestion-retention-v1.json) · [证据](home-suggestion-retention-v1-evidence.jsonl)
