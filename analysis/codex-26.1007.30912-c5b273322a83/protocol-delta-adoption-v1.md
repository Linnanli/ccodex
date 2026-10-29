# 后台协议差异的采用决定

既有 466 个协议变体中 11 个不同，本次逐一核对这 11 个变体，没有重跑全协议发现。它们实际来自两类字段变化。

| 范围 | 精确差异 | 采用决定 |
| --- | --- | --- |
| stable/experimental 各 5 个通知：item/started、item/completed、thread/started、turn/started、turn/completed | subAgentActivity 增加可选且可 null 的 model、reasoningEffort，旧 required 不变 | 公开候选可继续评估；协议边界保留扩展字段，真实解码/store/通知集成另验 |
| experimental thread/fork | 公开候选缺 experimentalPredictionMode | 公开候选未取得预测 fork 资格；保持独立能力，禁止静默删除参数、普通 fork 替代或新建线程回退 |

对通知，已追到选定分发函数、item 完成处理、qtn 转换及一处显示投影。qtn 对 subAgentActivity 原样返回；显示投影不读取两个新字段。它们支持继续采用候选的局部决定，不证明全部解码、clone、存储、重连与实际通知顺序兼容，也不构成新增显示功能的要求。

预测路径有明确第一方调用：fge 先检查资格与版本，再要求 experimentalPredictionMode:true，且 fallbackToFreshThread:false；fork 调用还带 ephemeral:true、excludeTurns:true。已有两后台负例显示冻结后台识别并门控该字段，公开候选在缺失 rollout 路径上与未知字段类似；这不证明成功预测。版本满足或普通 fork 成功不能替代这项语义。

因此整体公开后台仍未取得完整复刻资格。需要匹配的预测实现或有成功语义证据的独立 provider；不能用删除该能力来宣称完整。npm 二进制与公开源码提交绑定、真实 receiver/服务和其它后台能力仍保留各自缺口。

本次有 16 条来源事实、8 个 JS 源码选择及 8 项隔离检查；没有客户端启动、服务调用或模型提交，未增加产品通过数。源码选择含完整函数和完整 case，不能当作恢复模块数。第三方和后台实现仍按依赖/provider 引入。

11 个变体均已分配到上述决定；下一步把这些决定与已交付运行时、存储、逻辑模块合同合入新版实施依据，明确源码准备、外部输入与实施验收，保留完整范围。

[逐变体决策](protocol-delta-adoption-v1.json)、[来源事实](protocol-delta-adoption-v1-evidence.jsonl)、[隔离检查](protocol-delta-adoption-v1-replay.json)。
