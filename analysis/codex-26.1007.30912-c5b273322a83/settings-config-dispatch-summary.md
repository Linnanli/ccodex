# 配置写入与分发路径分析

本批包含 40 条静态源码契约：38 条确认、2 条未决。原分析解析了 19 个完整选定单元，累计 20,501 字节、5,409 个节点（含重叠）。这些是分析规模，不是功能总数。六个 Agent 页面控件复用既有记录，原 65 条页面记录及全局功能、入口和模式分类在本次交付中未被修改；新增全局记录 0，确认 ChatGPT 专属排除 0。

非项目写入通过 `KI(scope, host).sendRequest` 请求 `config/value/write`；项目分支在源码中等待 `projectWrite()`。项目读取/保存路径进入 `$G → yDn → AW.post`，`vscode://codex/` 前缀选择 `AW.sendRequest → Vf.dispatchMessage` 的 `fetch/cancel-fetch` 分支，经 `are/ire` 桥发送。原生 `MMe` 的对应分支调用注入的 `fetchWrapper`。单独的 `Ude` 构造、`fetchHandler` 与注入的接收对象仍是条件候选，尚未证明它们属于同一实际实例，也未核实磁盘写入、运行时取消或协议交付。

取消处理先移除 pending 项与监听器，再同步分发 `cancel-fetch`，显式 Promise 拒绝发生在分发正常返回之后。同步分发抛错会跳过这次拒绝；已取消信号在 Promise executor 中执行与后续事件监听器抛错具有不同结果。桥调用或 `.catch` 注册同步抛错也会跳过后续 CustomEvent。桥返回 Promise 的异步拒绝仅记录日志，不能据此声称 AW 的 pending Promise 已结束。

作者验证为 3,673 项，范围是选定原始字节片段及保存的元数据。独立复核为 421 项（159 项保存文本语义检查与 262 项最终元数据检查）；此前 25 项作者身份推导不计入独立复核。这些计数不相加，不代表实际运行、端到端成功或完整功能覆盖。本次交付只验证冻结元数据、允许发布范围与逐字节复制，未执行原分析器、目标源码、UI、网络或模型任务。

正式 [契约 JSON](settings-config-dispatch.json)、[证据日志](settings-config-dispatch-evidence.jsonl)、[作者验证](settings-config-dispatch-validation.json)、[独立复核](settings-config-dispatch-peer-review.md) 与 [交付记录](settings-config-dispatch-delivery-provenance.json) 可供后续工程恢复使用。原始元数据在 [raw 快照](raw/settings-config-dispatch/settings-config-dispatch-contracts.json)，其相对路径和原绝对路径保留作者记录的上下文；未引用为新执行证明。完整单元文本、AST、依赖与工具实现未发布。
