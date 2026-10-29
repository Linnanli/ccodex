# 内嵌依赖 17 个候选的合并调查状态

基线：codex-26.1007.30912-c5b273322a83。v1 的 6 条和本次其余 11 条均已绑定源码版本声明；17 / 17 的版本证据与原始 hint 范围交叠已逐条验证。实际上游分发确认、运行行为确认均为 0 / 17。

| 来源 | 版本自报范围 | 候选数量 |
| --- | --- | --- |
| React / ReactDOM | 生产工厂 export.version、renderer 身份元数据 19.2.7 | 4 |
| Sentry SDK family | __SENTRY__ 注册表默认值与版本命名空间键 10.29.0 | 3 |
| Statsig SDK family | SDK_VERSION 与 provider 元数据 3.34.0 | 2 |
| Zod | 对应 $ZodType._zod.version 的 core 4.4.3 | 8 |

Sentry 注册表保留已有 truthy 全局 version，因此不能据此断言活跃全局版本。renderer 的 key 初始化属于 lazy initializer，调用顺序尚未运行验证。具体 Sentry 子包仍未知。

Statsig main 初次调查将导出字段清空和 metadata 对象赋值合计，留下 ambiguous 记录。追加复查仅重新解析先前完整 AST 语句的 103987 字节，明确区分两种赋值。main 与 renderer metadata callback 的 AST 形状一致，比较保留所有标识符及属性名；整体 SDK 与 @oai-statsig 具体子包的等价性仍未知。

Zod 8 个候选的版本只约束相应 _zod core；不能覆盖 legacy 接口或整个 chunk。所有实际包来源、修改状态、完整闭包、模式及行为仍待核对。第三方实现未复制进维护源码，冻结 v1 未更改。

后续发布应使用 merged-candidate-contracts.json 作为最终候选调查状态，保留 embedded-dependency-contracts.json 中的初次 ambiguous 结果及 statsig-recheck.json 的修正证据。
