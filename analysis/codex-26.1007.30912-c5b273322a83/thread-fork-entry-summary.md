# 现有会话分支：入口、已创建身份与设置失败

已连接 header 和侧栏分支菜单到本地/同 worktree、新 worktree 两种动作。恢复实现须分别保存“后台已创建”“后续设置结果”“界面是否导航”和“待准备 worktree 的客户端身份”。通用错误提示不能证明后台没有创建成功。

| 层次 | 已确认的源码行为 | 实现影响 |
| --- | --- | --- |
| 菜单 jJo、header hn、侧栏 CZo | 条件菜单选择 Zda/Qda；非空结果才导航 | 保留入口和 selector 条件，不能按菜单文案推定模式 |
| 本地动作 Zda | 按 source 去重，传 roots、模型/effort 等；同步失败警告后仍返回新 ID；标题失败容忍 | 新 ID 与设置结果分别保存 |
| 本地 pane 复制 Nha | 在已取得新 ID 后仍可能抛错，Zda 外层返回 null | 界面未导航不代表创建失败；不能据此自动再次 fork |
| 新 worktree 动作 Qda | 先查 Git，再以 working-tree 起点排程，返回 pending clientThreadId | 待定身份与后台线程 ID 分开；pane 缓存失败可能发生在排程后 |
| worktree runner OPc | worktree-ready 后 fork；同步失败仍 created，成功记录 firstTurn:not-requested | 准备工作区、创建分支和执行新 turn 分开验收 |
| Hoa / KI-selected RPC | 按 targetTurnId 属性选择 Latest/FromTurn，附输入与默认身份映射 | 实际 RPC/provider 到所选 Dfn 实例仍是待验证关系 |
| Dfn / xan / San / Can | fork 与映射、resume、assignment、placement 分阶段；后续失败保留已接受 ID | 保留部分成功状态和各阶段错误；没有事务性自动回滚 |
| N9t | 能力/版本允许时用 beforeTurnId/lastTurnId；旧式先 fork 再回滚新线程 | 回滚目标必须是新 ID，原线程保留 |

4组导入导出绑定已核对。具体入口和参数来自冻结源码；manager 部分以接口实现合同表达，**未证明这次 UI 调用的实际 RPC receiver 身份**。

## 对旧记录的限定

旧 `TTC-V-03` 只截取发送 `thread/fork` 的内部 async callback。该 callback 内部的身份回调或同步调用可以拒绝，但完整外层 `xan` 已先保存响应 ID，catch 会返回 `status:created` 和 `synchronization:failed`。旧内部结论不能直接升级为整个 fork 方法拒绝。

这项保证从“已取得响应 ID”开始；请求拒绝、响应 ID 尚未取得的错误仍可传播。服务端已接受而响应丢失的情况，本批证据不能恢复其身份。San 依次尝试 resume、assignment 和 placement，前一步失败仍继续，后续错误消息可覆盖前一条。真实存储及服务副作用未验证。

## 验证与范围

[15条源码事实](thread-fork-entry-contracts.json)依据3个完整 Program 解析和一次106500字节的末尾导出声明解析。导出声明的首次单独解析因未声明的本地绑定而失败；第二次允许外部声明后成功，并与既有完整 Program 的选定函数交叉核对，失败回执保留。

[21个隔离场景](thread-fork-isolated-observations.json)全部通过，执行5个选定完整函数：xan、San、Zda、N9t、Qda。服务、Git、worktree、UI、状态映射及产品能力均使用明确的内存替身；没有运行原应用模块，没有模型提交、实际 fork、worktree 创建、IPC、项目修改或持久化写入。这些观察不计入真实功能验收。

[v6功能视图](feature-scope-v6.json)新增“从现有会话创建分支”定义，将原 fork 候选按具体用户目标归属；47项定义、51用户操作、21支撑、2项关联待审。72根/74行为条目与12项关联待办保留。新增8条目的地×正常/失败/取消/重启规格，合计208条未执行；967个旧入口仍未映射，47项模式unknown，确认排除0，完整产品分母未知。

fork 的入口调查至此交付；不重复追同一菜单。后续只补实际 receiver、完整能力 provider、真实 worktree/存储、模式及行为。下一项按[计划v5](implementation-plan-v5.md)核对普通新会话与 MCP extension start，另保留全部其他架构、依赖和行为缺口。[来源及执行回执](thread-fork-entry-provenance.json)可回溯所有输出；本批使用 AST 补充既有 REA 分析，未新增 REA 运行。
