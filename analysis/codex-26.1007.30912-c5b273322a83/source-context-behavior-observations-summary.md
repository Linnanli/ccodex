# source-context 本机候选观察

一次实际 Node v22.23.2/x64 命令完成 8 个有限场景，8 项预期检查均通过。实验只执行保存的 36 B lX wrapper，每个场景使用新建本机内置 AsyncLocalStorage；输入、callback、Promise 和 observer 都是自有内存替身。本次交付只复制 metadata，没有重跑实验。

对象与 Promise 返回身份保留；同步 throw 以同一 Error 传播并恢复外层 store；嵌套 run 正常退出也恢复外层。Pending Promise 在 settlement 前已返回，同步 scope 已恢复；run 内创建的异步 continuation 则继承创建时的 store。Rejection 的处理来自独立 observer，不归给 lX 源码。

[薄读者](source-context-behavior-observations.json)连接[原始观察 metadata](raw/source-context-behavior-observations/author/source-context-behavior-observations.json)、[作者摘要](raw/source-context-behavior-observations/author/summary.md)、[一次实际执行收据](raw/source-context-behavior-observations/author/observe-receipt.json)和[handoff](raw/source-context-behavior-observations/author/handoff.json)。8 场景共享同一命令/stdio/receipt，不是八次子进程运行。

结论仅限本机 Node22 候选；文档候选 Node24、目标嵌入 Node 版本、实际 rX receiver/require namespace、provider/fetch、存储、UI 和模型行为仍未验证。其余三份小单位未执行，旧 9 静态记录、di16、receiver25 和 global 保持原未知。FullAnalysisCompleted=false。

正式文件只含有限 metadata、pins、坐标和观察结果。保存源码、fixture/runner 及含实现的诊断均仅本地；本交付新增 original client/storage/native/model/target 运行均为 0。
