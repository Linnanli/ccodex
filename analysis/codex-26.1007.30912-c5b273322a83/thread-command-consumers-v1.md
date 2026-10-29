# 线程命令：注册、直接去向与功能归并提议

本批只读冻结源码，核对8个ID、10处已保存注册与32条来源事实；提出6项不同目标及1项现有目标扩展、6项维护职责。本批不修改全局功能/操作/规格账本，不把提议重复计入已采纳数。

| 命令 | 已确认的静态行为 | 归并提议 |
| --- | --- | --- |
| openThreadInNewWindow | gate与线程ID控制，发送带本地/host路由的open-in-new-window | 当前线程新窗口目标；区别于FSC-0388固定/新窗口 |
| deleteChat | 打开确认，重查身份后走账户删除；特定404视为已删除 | 扩展FSC-0284；当前/归档入口共享s5t→xPr，不重复建目标，不并入本地归档 |
| markThreadUnread | 本地route/eligibility与账户async-status是不同注册及后端 | 与clearAllUnreads列为未读状态目标的两个操作，保留各来源条件 |
| copyConversationMarkdown | 先加载会话及可选父历史，trim只判空，复制原文 | 独立会话导出目标；不并入技能或目录复制 |
| copyLastCodeBlock | 最近助手完整块/内容引用选择、历史补载、重复触发抑制及stale abort | 独立代码块复制目标；enabled与canCopy分开 |
| openSideChat | 溢出菜单与面板动作注册不同；pending tab/会话创建/取消清理分阶段 | 侧聊创建目标；不并入fork或面板toggle |
| clearAllUnreads | 默认确认，可记住跳过；清本地/远端/账户/计划更新，确认后立即关闭 | 未读目标的批量操作；不保证全局原子成功或完成时才关闭 |
| openReviewTab | ready及git/remote条件，打开/采用DIFF标签并可聚焦 | Changes标签目标；区别于toggleReviewTab和展示偏好 |

所有模式仍unknown：账户domain、chunk名、codexLocal标签或局部route不能单独证明完整模式闭包，本批无整项排除。外部manager、服务、剪贴板、窗口、tab、存储的实际执行结果均未验证；第三方只作为包或运行时依赖，不生成其实现。

本批8条来源目标去向已审阅，另外95条命令完整保留。全局账本仍444项有限功能、476用户操作、118支撑、1482条未执行规格，来源无功能关联仍797，命令目标关联待采纳仍103。下一步是按本批事实采纳/修订目标、操作、职责及规格，并做相同provider去重；不能把本批7个提议直接加到444上。

[结构化合同](thread-command-consumers-v1.json)、[证据](thread-command-consumers-v1-evidence.jsonl)、[命令表](thread-command-consumers-v1.csv)。无客户端启动、模型/服务提交、Git动作、剪贴板访问或产品/构建通过。
