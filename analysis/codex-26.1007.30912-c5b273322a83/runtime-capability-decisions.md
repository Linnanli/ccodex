# 运行时能力与依赖处理决定

本批将四项特殊边界落实为[逐项决定](runtime-capability-decisions.json)。独立运行时路线尚未选定或验证，完整Codex功能目标保持；客户端实现未开始。

| 能力 | 已确认的职责和处理决定 | 尚待证明 |
| --- | --- | --- |
| Task Manager | bootstrap顶层guard；Help菜单项无局部debug/平台/access条件。保留真实诊断能力，通过第一方接口接入 | 实际UI/进程行为和独立替代实现 |
| 更新与managed relaunch | 分开普通更新transport与nullable策略provider。null只停止选定强制调度路径；保留有策略时的通知、deadline和重试 | native事件生命周期、平台安装/签名及真实调度 |
| 浏览器所有权与clone | eJ两处同绑定caller接到window.open child与live history clone；保留owner、pending、route和清理。冷恢复仅沿原条件 | lease消费/accept、真实视图转移与克隆行为 |
| Node网络/IPC策略 | 保留拒绝通用net、允许声明IPC的执行要求；第一方管理端点和relaunch，运行时或隔离机制实施权限 | 实际IPC执行、越界负例和目标ABI |

Task Manager不能按“调试专用”删除；函数占位只满足guard形状。更新策略缺失不等于没有更新器：普通安装方法没有读取owlUpdatePolicies；但有效provider的订阅/读取异常可能传播，initializeUpdaterOnce的catch会使updater失效。分析和实现必须分别处理缺失与错误。

浏览器两条路径也不能合并：window.open要求可adopt的child WebContents；live history clone先调用clone再创建lease。source为空时的cold restore并未证明能代替live历史、进程状态或所有权转移。相关模式仍unknown，暂留完整范围。

两份完整原Program共1,080,229个AST节点，新增11条来源事实。22个隔离源码场景通过，覆盖guard、Help handler、空/有效/错误策略、调度/重试及lease销毁清理；均使用内存替身，实际native/UI通过数为0。首个观察尝试因源码选择器歧义在执行场景前失败，修正后的第二次结果与失败记录一并保留。[来源索引](runtime-capability-decisions-provenance.json)保存工具、源码范围及终态。

第三方及运行时实现由独立依赖提供；待恢复的是第一方能力接口、业务编排与状态生命周期。本批没有生成库实现副本、没有触发原客户端或模型任务，既有功能视图和212条未执行验收规格不变。

本批关闭task-manager局部菜单/guard位置、更新null消费者及两处adoption caller的限定问题。下一项用固定版本官方接口/源码核对普通Electron与这四项能力的差异。独立Owl分发、完整ABI、全部私有API和实际行为缺口仍保留；[既有运行时方案](runtime-adapter-options.md)是历史输入，不作为已验证兼容结论。
