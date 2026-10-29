# 打开会话、恢复上下文与任务执行的边界

已找到具体页面到“按需恢复会话”hook 的源码绑定。界面使用 `resumeConversation`，旧 `TTC-V-02` 记录的是低层 `resumeThread`；两者不能按 `thread/resume` 方法名直接认定为同一用户操作。

## 已厘清的路径

| 层次 | 所选源码的职责 | 恢复时的决定 |
| --- | --- | --- |
| 页面 `kj/Tj/Sj/st` | 按 shouldResume、交互、host、共享与侧会话条件传 threadId；显示恢复失败、不可用和 writer conflict | 页面打开与显式提交分开；保留不同入口的配置 |
| hook `R` | 观察 needs-resume 与窗口活动；准备 roots/host/settings；触发 KI RPC，控制重试和旧结果屏蔽 | UI 重试状态独立维护 |
| `Dfn.#t/#e` 接口实现 | 释放 readResumeInputs，按线程合并并发恢复，协调不同 source，返回现有 activeTurnId | 复用恢复尝试；区分清理资源、失效 attempt 与取消任务 |
| `Wan/Yin/Han` | 准备上下文、设置和权限，发送 thread/resume，加载/合并历史、取得流角色、分发快照 | 适配器分别处理后台请求与历史/通知/存储 |
| 显式 turn 提交 | 属于原有任务提交链路 | 不能用重发 turn 伪装重新打开或重启恢复 |

页面导入 hook、hook 导入 KI 以及恢复状态 selector 共 5 组模块绑定已核对。**实际 KI provider 是否把这次 UI 调用送到选定 Dfn 实例仍未证明**，因此上表的 manager/hydration 部分保持条件接口合同。

已有 stream role 且 resumeState 不为 needs_resume 时，Wan 可以直接返回 ready；本地 follower 尚未恢复时返回 owner-recovering。ready 中的 activeTurnId 读取既有状态，不能当作新建 turn 的证明。所审查的恢复函数体没有主动发送 turn/start；服务端收到 resume 后的背景行为、完整 provider 副作用和不同模式仍需实际验证，不能据此保证所有打开场景都不会产生后台活动。

## 并发、重试与失败

同一 conversationId 和 source 共用 in-flight promise；不同 source 等待后重查，期间移除线程或销毁 manager 可返回 canceled。每个调用者在 finally 释放自己的 readResumeInputs。attempt 的 cancel 回调只释放 hydration cleanup，本身不会移除 map 或令 current 检查失败；恢复实现必须分别维护这些生命周期条件。

UI 重试和请求重试是两层规则。hook 的可重试错误计数要求小于 5，初始延迟750毫秒、倍增上限60秒；配置错误、writer conflict、归档等有各自处理。Han 默认请求超时120秒，Timeout 可增加到240和480秒；显式 timeout 不走该超时重试。指定 closing-thread 错误最多额外重试4次，等待750/1500/3000/6000毫秒；其他错误传播。

完整 hydration 成功路径会合并历史与已有终态、更新 resumed、释放通知缓冲并广播快照；失败可回到 needs_resume。低层 resumeThread 则可能在后台已接受后因本地映射失败而拒绝，错误提示不能被当作后台没有执行的证明。

## 验证范围和下一步

[14 条源码事实与来源范围](thread-resume-entry-contracts.json)来自4个冻结文件的5次完整 Program 解析。[19个隔离场景](thread-resume-isolated-observations.json)执行9个选定源码单元，全部通过，覆盖并发、资源释放、重试上限、过期 attempt、现有上下文复用和低层请求映射。完整 Wan 只执行4条提前返回路径；其余 manager 场景使用 Wan/Yin 替身，历史合并和完整 hydration 未执行。Error 文本提取、状态映射和 active-turn helper 也有明确替身边界。

本次无客户端运行、模型提交、实际 thread/resume、turn/start、IPC、项目变更或存储写入。既有停止/重启样例观察到 interrupted 且未自动续跑，继续保留为该样例的实际结果；这19个隔离场景不扩大其结论，也不计入真实功能验收。

[v5 功能视图](feature-scope-v5.json)仅注记 resume 候选的调查状态：46项定义、200条未执行规格、72根/74行为条目、3项关联待审与12项关联待办均不变。旧低层 API 到页面的等价关系、实际 provider、模式和持久化仍待核对，不增加覆盖率或确认排除。

接下来按[当前计划 v4](implementation-plan-v4.md)追 fork 的具体入口、参数、结果导航和原线程处理；resume 后续仅追实际接收方、完整 hydration、旧 API 关联与行为，页面/hook 不重复调查。源码和执行回执见[发布索引](thread-resume-entry-provenance.json)。既有 REA 结果继续作为基线依据；原临时 REA 工具路径已不存在，本次补充使用 AST，未新增 REA 分析运行。
