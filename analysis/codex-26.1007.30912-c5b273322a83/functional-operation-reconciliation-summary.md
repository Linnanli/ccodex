# 功能操作与来源关联

固定基线 `codex-26.1007.30912-c5b273322a83`。本次将已有清单接成 **71 个操作候选**，保留参数、条件、状态、外部边界及未执行场景。它们来自已保存的有限合同，完整功能分母仍未知，模式和运行结果未增加确认。

| 来源范围 | 操作候选 |
| --- | ---: |
| 会话与任务协议 | 7 |
| 提交入口 | 3 |
| 通知与状态 | 5 |
| 审批入口 | 3 |
| 电脑使用服务 | 14 |
| 项目条件 | 1 |
| General 设置／展示 | 32 |
| Agent 配置 | 6 |

[操作读者 JSON](functional-operation-reconciliation.json)完整保留71项操作、311条关联和下一步动作；原2384节点登记表与全部原始字段在[冻结作者原件](raw/functional-catalog-reconciliation/author/functional-catalog-reconciliation.json)。操作读者省去重复登记表，未删操作或关联。38张设置卡与旧 pending namespace 是同一批操作的不同表示，不重复增加功能数量。

311条关联中，282条有明确的保存来源，29条是作者人工选择的 composer 支持关系，标为 inferred。结构包含、绑定或文件候选关联不证明操作等价、运行可达或可合并功能。723个来源facets包含旧元数据记录，也不是新增功能数量。

[独立审查](raw/functional-catalog-reconciliation/independent-review/independent-review.md)针对保存元数据和声明的静态来源关联，实际15912项检查、0错误；29条关系曾误写confirmed，已修订并保留历史。作者21613项与独立审查分别统计。该审查未重读原JS、未执行目标，也没有新增General原源码的独立语义审查。[作者原摘要](raw/functional-catalog-reconciliation/author/summary.md)保留其原路径和限定范围。

后续优先补实际receiver、逐操作持久化／恢复、模式条件和来源消费者。完整Codex范围、ChatGPT专属排除和原生／后台替代方案仍需证据；本次没有修改36个功能组、968项旧入口或337项deferred候选。
