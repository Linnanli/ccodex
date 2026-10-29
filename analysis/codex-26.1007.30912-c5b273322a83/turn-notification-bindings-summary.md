# 通知处理的模块绑定与实例字段

固定基线 `codex-26.1007.30912-c5b273322a83`。新增 31 条限定范围的保存记录；源码范围、元数据引用与运行验证分别判断，完整功能分母仍未确定。

固定 shared Program 的所选词法证据区分 Dfn 模块变量、Ofn 初始化函数和匿名 ClassExpression，接上所选 this.threadStore、T7t 与 notification context 赋值。取消成员内 3 个局部 i、6 处引用和 2 处调用分别定位。

31 条 confirmed 仅确认保存范围内的源码断言。238 个所选字段访问、6 条 call/new 关系没有证明所有外部写入、实际实例／模式／transport、通知送达或完整持久化。原 221 条通知记录与 30 条审批记录不改；同行审查的 577 条语义检查和 197 条格式检查分别保存。

[原始结果](turn-notification-bindings.json)、[原始记录](turn-notification-bindings-evidence.jsonl)、[作者摘要](turn-notification-bindings-raw-summary.md)、[核验](turn-notification-bindings-validation.json)、[同行审查](turn-notification-bindings-peer-review.md)、[冻结清单](turn-notification-bindings-manifest.json)、[发布来源](turn-notification-bindings-provenance.json)。

本次仅发布选定分析资料的逐字副本与派生索引。较大的本地 AST 和历史尝试由冻结清单引用；未复制完整原客户端或第三方实现，未增加全局 journal 记录，未执行新的客户端或模型任务。
