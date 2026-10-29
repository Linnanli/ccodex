已交付固定基线的终端静态合同：35 条记录（31 条原源码合同、4 条 discovery/未知/恢复建议），另有 6 条继承证据。43 个完整函数/成员是作者选定范围；旧 36 个功能组不变，全局 source records 新增 0。

来源包括 7 个小 renderer/helper 模块、1 个 manager initializer 和 4 个 service-boundary 函数。宿主 terminal 注入、会话/输出/输入/尺寸及清理职责见保存合同；实际 UI、模式、PTY/native receiver、端口送达、跨进程时序、恢复持久化和完整功能分母仍 unknown。

[合同](terminal-feature-contracts.json) · [记录](terminal-feature-contracts-evidence.jsonl) · [接口](terminal-feature-contracts-interfaces.json) · [作者验证](terminal-feature-contracts-validation.json) · [独立审查](terminal-feature-contracts-peer-review.json) · [原作者摘要](raw/terminal-feature-contracts/summary.md)。

独立 source/semantic checks 815 与 metadata delta checks 601 分别保留；作者旧 source checks 52859 为复用，最终 delta checks 672 为另一范围，均不相加。本次只校验并复制允许的 metadata，不重跑任何分析或目标。
