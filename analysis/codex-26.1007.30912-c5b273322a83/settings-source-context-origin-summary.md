# source-context 的 Node 内置依赖来源

固定基线 `codex-26.1007.30912-c5b273322a83`。原 Program 的绑定关系确认 lX 内的 rX 来自零参数 AsyncLocalStorage 构造，构造器 namespace 来自 require("node:async_hooks")。lX 同步转发两参数并直接返回 run 的结果，没有本地 await、结果替换或 catch。这给第一方上下文 adapter 与运行时内置依赖的划分提供来源依据。

[读者](settings-source-context-origin.json)连接[9条冻结合同](raw/settings-source-context-origin/author/settings-source-context-contracts.json)、[接口](raw/settings-source-context-origin/author/interfaces.json)与[独立审查](raw/settings-source-context-origin/independent-review/independent-review.md)。9条中6 confirmed、2 inferred、1 unresolved，包含5条新源码合同及1条公开文档候选；4保存小单位相加114字节含重叠。作者298项、独立metadata264项和保存单位解析30项分别登记，不能相加为功能覆盖率。

[Node 24.19.0 官方 run 文档](https://nodejs.org/download/release/v24.19.0/docs/api/async_context.html#asynclocalstoragerunstore-callback-args)仅是候选API合同；保存note为citation元数据，未byte-pin网页，也未验证目标嵌入Node版本。候选维护方案使用所选运行时的内置AsyncLocalStorage，不生成原生实现或新增npm包，采用前需独立核对上下文隔离、callback返回/抛错与Promise行为。

本批只闭合原源码声明关系，实际require返回、namespace后写、当前rX实例、上下文值、原生callback/run语义及整条fetch透明性仍未观察。原模块新完整Program仅解析一次；另外2个rX消费者只计数未分析，0选定直接写不证明任意mutation闭包。旧di16与receiver25保持原快照，客户端、模型、真实文件操作和全局登记新增均为0。后续本机内置API实验另批报告，不升级本批的native行为确认0。
