# 相邻标签切换的模式归属

FSC-0456「选择工作区或面板的相邻标签」按选定源码归为 **shared**。剥离 ChatGPT 专属功能时，保留这项功能的共同标签控制器和 Codex 消费端。

新增核对了本地任务页 `lc → Gc → Ac → jc` 与 ChatGPT 会话页 `m_ → T_ → Oh → Ac → jc` 的具体调用。两端经已有 `UnifiedTabStrip → NS.selectAdjacentTab → Hji` 契约接入同一套工作区标签逻辑；前后标签命令继续保留原有布局、焦点与可见性条件。归档预览、内联预览及外部 workspace 等路径的差异保留在合同中。

命令前置检查的 `c8n` 是选定键盘组合键状态：初始化为 false，meta+shift 方括号操作可置 true，keyup 及带条件的 reset 可清除。它不能当作 Codex/ChatGPT 模式判断。

模式覆盖表由 **505 unknown / 4 shared** 更新为 **504 unknown / 5 shared**。只改变这一个现有功能的源码分类；509 功能、582 不同操作、1844 未执行规格、来源清单及模块职责身份均未改变。没有新增整项功能或整文件排除。

这不是运行验证。有效模式、组件挂载、命令最终注册、键盘事件、标签激活/焦点、持久化与独立构建仍待验收。主阶段未完成，客户端实现未开始。

依据见 [源码合同](shell-mode-consumer-v1.json) 与 [当前模式覆盖表](feature-mode-dispositions-v7.json)。
