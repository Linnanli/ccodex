# 审批回复、转发与状态清理

本批明确了8条可用于恢复实现的源码契约，26项隔离探针通过。审批入口返回、所属窗口处理、后台接收、界面状态和持久化必须分别记录。

条件工厂 `Sii` 把发送回调注入 `Dfn`，构造器保存后由审批 context 使用。该回调调用 `Pvn` 后没有返回或等待其结果；审批入口同样不等待 sender。跟随窗口则发起向所属窗口的异步转发，注册失败日志后立即返回。因此，成功调用这些入口不能证明后台已经接受审批。

等价请求先整体检查，再逐项发送并更新本地状态。后一次同步发送失败会留下此前已完成的更新。`apply` 会尝试更新 turn item，随后删除待请求；turnId 为空或 lookup 返回无 turn 时仍会删除请求。`discard` 只清理匹配类型与请求 ID 的 item。这些是会话内存转换；真实 updater 的持久化没有在本批验证。

连接器等价比较要求 connector/link/reason 相同且没有 consent，scopes 按集合比较。执行绑定审批的局部参数形状和 persist 检查也已核对；完整 schema、URL 分类、规范化和后台执行绑定仍开放。

恢复时由现有 T03/T04 的 approvals 消费者使用三个边界：`packages/backend-adapter/src/approvals` 负责决定与发送编排，`packages/desktop-transport/src/coordination` 负责所属窗口转发，`packages/state-storage/src/conversations` 负责请求与投影状态。路径是维护建议，不是原作者目录恢复。逐条来源、探针与真实验收条件见[合同](approval-response-settlement-contracts.json)。

旧 APPROVAL-U03/U04/U06 仅关闭上述静态部分。真实 manager/RPC 实例、Pvn 序列化和接收方、后台确认、卡片异常及存储恢复仍是局部验收项；其他审批类型与模式归属继续保留。

25个源码单元均有固定文件哈希和字节范围；复用旧 Program 绑定，并对保存的完整工厂函数做了一次局部 AST 选择。探针只运行精确选取的函数/回调，IPC、发送、turn lookup、updater 和 schema 识别均为明确的合成边界。没有启动目标客户端、提交模型任务或增加真实产品通过数。

本批没有新增完整功能定义或重写实施计划。现有120项有限定义、457条待执行产品规格和恢复覆盖表保持原样；8条合同的真实验收条件独立列在合同中，不能算作已通过的功能。
