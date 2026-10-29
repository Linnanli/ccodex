# 应用清单与后台建议支撑分析

`app/installed`、`app/read` 的两条来源已确定用途：它们由 Br 聚合，既服务后台建议的应用上下文，也服务所选宿主是否存在可用应用的资格查询。主进程后台事件明确以 `surface:codex` 调用建议生成器，因此这个清单端口需要保留。不能因为同一服务类另有 ChatGPT composer 方法而整体删除。

| 边界 | 已确认的源码行为 | 恢复时需要保持的区别 |
| --- | --- | --- |
| Br 清单聚合 | 先 installed，再按100个ID并行 read；按 installed 顺序归一化 | 单批失败向上传播，没有此函数内的重试/取消 |
| Lr 建议策略 | 过滤可用/启用，按审批配置及 connector TOS 排除，检查 slug 碰撞 | 资格 Boolean 不代表建议策略最终允许的集合 |
| Or/Yr 错误降级 | 清单失败转为 lookupSucceeded:false，并禁用生成配置中的全部应用 | 不能与成功但清单为空混为一类，亦不证明生成成功 |
| 首页资格查询 | 按 host 读取同一清单并 some；拒绝向查询层传播 | host/account 查询键、调用方 enabled、五分钟 staleTime、retry:false |

ChatGPT HTTP TOS 请求在此带 `OAI-Product-Sku: CODEX`。保留判断依据来自实际调用和参数，不来自接口名称。完整功能的模式标签本批仍未改写。

维护职责可分为薄清单适配器、建议应用策略、资格查询桥接；复用既有 backend-adapter/app-host/query 边界。分组辅助函数来自独立 chunk 工厂，本批未证明其公开包名与准确版本；后续选择锁定依赖时需核对兼容性，恢复工程不复制其实现。

4个冻结完整Program、59个AST范围和16项源码检查通过。8项事实及两条来源的完整调用均有哈希与字节定位。969来源中700尚无功能映射，明确机制由238变为240，待用途决定由462变为460；525功能、603操作、1912条未执行规格及原模式标签保持。

本批未启动客户端、提交模型任务、调用服务或进行客户端实现。实际挂载、账户/开关、读取失败效果、缓存失效与独立构建仍待验证。

[结构化合同](app-inventory-suggestion-support-v1.json) · [证据](app-inventory-suggestion-support-v1-evidence.jsonl)
