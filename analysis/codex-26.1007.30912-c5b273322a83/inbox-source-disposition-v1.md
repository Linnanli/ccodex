# 两个收件项写侧来源的归属决定

已复用既有写侧、查询和计划任务合同，为两个来源作出不同决定，对应原计划2.1／2.2。

| 来源 | 决定 | 限定 |
| --- | --- | --- |
| inbox-item-set-read-state | 条件关联现有FSC-0434的mark-read／mark-unread | q7r／K7r在原功能合同与写侧合同中具有相同Program哈希、范围及内容；实际消息交付、身份和SQL结果未验证 |
| inbox-items-create | 保留为计划任务执行记录的内部元数据写机制 | 所选persistAndNotify→X$→da仅更新已有automation_runs；不能据名称新增独立“创建收件项”功能，也不推断其他处理器或产品功能不存在 |

已发布[来源清单v34](legacy-entry-dispositions-v34.json)与[队列v18](retained-entry-backlog-v18.json)。全部968条来源身份保留，966条未选记录完全不变；未关联功能的来源709→708，明确机制180→181，待功能／机制决定529→527。已有批量已读分支关联原样保留，不重复计数。

509项功能、582个不同操作、1844条未执行规格、51项任务和505 unknown／4 shared模式计数保持。没有新增源码解析、用户功能、场景、运行通过或客户端实现；20个命令消费者缺口仍在。新关联只是条件源码支持，不能当作端到端行为完成。

详细依据见[逐条决定](inbox-source-disposition-v1.json)、[表格](inbox-source-disposition-v1.csv)和[证据](inbox-source-disposition-v1-evidence.jsonl)。better-sqlite3继续通过受管理依赖引入，原生ABI、迁移、有效home／身份与耐久性仍需独立验证；本批不继续追踪provider。
