# 细粒度功能、操作与验收映射

本批从已保存的38张General／Agent操作卡中，形成34个有固定编号的功能定义，关联35个操作及140条未执行验收规格。这是作者对有限源码契约的功能粒度审阅；模式归属全部unknown，完整功能分母仍未建立。见[功能清单JSON](feature-scope-ledger.json)、[可筛选CSV](feature-scope-ledger.csv)、[验收规格](feature-scope-scenarios.json)、[34条推断依据](feature-scope-evidence.jsonl)与[来源索引](feature-scope-ledger-provenance.json)。没有增加桌面运行或模型提交。

功能粒度采用“一个可独立配置的目标偏好或宿主动作及其可观察契约”。无项目任务目录的选择与reset归入FSC-0001，但保留两个操作、各自条件与不同错误提示，不声称两操作等价。共享配置writer中的六个不同键分别定义六个功能；实际沙箱／模型能力、宿主应用和持久化仍是各自待验证的后效，不能由配置行直接认定完成。

三个设置条目暂未分配功能ID：GENERAL-OP-017仅展示Managed更新策略，GENERAL-OP-031仅展示访问摘要／tooltip，作为待关联父功能的信息facet保留；GENERAL-OP-032包含已连接host的Add project及未连接／无host的链接，应按实际消费者拆分。它们没有从产品范围排除。另33个协议、提交、通知、审批、电脑使用服务及项目条件候选继续排队；35已关联＋36队列覆盖原71操作，未遗漏或增算旧的重复表示。

复用已保存的settings route数据流／factory／export／控件合同，把General和Agent控制分别接到同一ROUTE-0152设置容器的两个support实例。关系标为inferred条件容器关联，不是操作等价、实际mount或整个入口已解析。968旧入口中只有1个容器部分关联，967在本清单中尚未映射；该容器的其余设置页面也未完成。36旧功能大组继续作为独立taxonomy历史，337 deferred原样保留，不能把34新定义加到36大组上当作产品总数。

本批实际重核4个冻结Program文件身份、169个唯一已保存字节范围及88个元数据pointer。没有新解析原Program或运行REA，作用域关系仍来自引用的既有REA／AST补充合同；字节复核不构成新的独立语义审查。所有功能均保留完整参数／状态、条件、外部边界、源契约、操作和scenario引用。没有把通用globalState候选后端自动指派给这些设置项，也没有根据Codex／Work／ChatGPT名称传播模式归属。

140条规格逐项引用原success／failure／cancel／restore预期，执行数为0；其中“没有显式取消”或“恢复未知”仍按原限定保留，不算已实现的取消／恢复能力。实际界面是否显示、条件值、provider／receiver、最终后效及耐久恢复需要后续核对。此前两个模型样例不覆盖这些设置功能，未附会为本批运行验证。本批不生成客户端实现、第三方实现或新的执行授权。

| 功能ID | 用户目标 | 来源操作 |
| --- | --- | --- |
| FSC-0001 | 设置无项目任务的默认目录 | GENERAL-OP-001、GENERAL-OP-002 |
| FSC-0002 | 选择或自动检测界面语言 | GENERAL-OP-003 |
| FSC-0003 | 设置关闭确认偏好 | GENERAL-OP-004 |
| FSC-0004 | 设置文件与文件夹的默认打开目标 | GENERAL-OP-005 |
| FSC-0005 | 设置Windows集成终端的默认shell | GENERAL-OP-006 |
| FSC-0006 | 设置本机或旧版WSL代理环境偏好 | GENERAL-OP-007 |
| FSC-0007 | 设置macOS菜单栏偏好 | GENERAL-OP-008 |
| FSC-0008 | 设置默认完整视图 | GENERAL-OP-009 |
| FSC-0009 | 切换底部面板控制偏好 | GENERAL-OP-010 |
| FSC-0010 | 设置终端标签的位置 | GENERAL-OP-011 |
| FSC-0011 | 设置任务运行时阻止睡眠的偏好 | GENERAL-OP-012 |
| FSC-0012 | 设置本地历史压缩开关 | GENERAL-OP-013 |
| FSC-0013 | 选择服务档位偏好 | GENERAL-OP-014 |
| FSC-0014 | 设置上下文建议提示开关 | GENERAL-OP-015 |
| FSC-0015 | 设置当前账户的桌面测试版偏好 | GENERAL-OP-016 |
| FSC-0016 | 设置Full Access选项的可用性 | GENERAL-OP-018 |
| FSC-0017 | 设置输入预测偏好 | GENERAL-OP-019 |
| FSC-0018 | 设置教学提示开关 | GENERAL-OP-020 |
| FSC-0019 | 设置纯文本输入框偏好 | GENERAL-OP-021 |
| FSC-0020 | 设置上下文用量指示器开关 | GENERAL-OP-022 |
| FSC-0021 | 设置输入框Enter行为 | GENERAL-OP-023 |
| FSC-0022 | 设置跟进消息的排队或引导偏好 | GENERAL-OP-024 |
| FSC-0023 | 捕获或清除弹出窗口快捷键 | GENERAL-OP-025 |
| FSC-0024 | 设置弹出窗口默认创建无项目任务 | GENERAL-OP-026 |
| FSC-0025 | 设置彩纸效果可用性 | GENERAL-OP-027 |
| FSC-0026 | 设置系统音频可视化偏好 | GENERAL-OP-028 |
| FSC-0027 | 进入依赖许可声明页面 | GENERAL-OP-029 |
| FSC-0028 | 查看并打开Windows启动项设置 | GENERAL-OP-030 |
| FSC-0029 | 配置代理审批策略 | AGENT-CONFIG-01 |
| FSC-0030 | 配置代理沙箱模式 | AGENT-CONFIG-02 |
| FSC-0031 | 配置工作区写入沙箱的网络访问 | AGENT-CONFIG-03 |
| FSC-0032 | 配置网页搜索模式 | AGENT-CONFIG-04 |
| FSC-0033 | 配置模型回复详略 | AGENT-CONFIG-05 |
| FSC-0034 | 配置推理摘要 | AGENT-CONFIG-06 |

下一步先审阅剩余33个非设置操作的粒度与实际消费者，将已有任务完成／中断观察关联到精确适用的场景，而非从协议方法名直接生成feature；再补两条信息facet的父功能和WSL多动作拆分。其他入口、flags、动态域和共享依赖继续保留漏项队列。完整范围、模式排除及实现阶段验收仍需继续闭合。
