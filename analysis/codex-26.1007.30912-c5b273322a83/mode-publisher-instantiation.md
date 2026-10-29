# 模式发布端：有限静态合同

本批包含 23 条合同（21 confirmed、1 inferred、1 unresolved），13 个场景全部未执行。正式交付只复制作者 safe6、handoff 和三份独立 peer metadata；没有重跑解析、REA 查询、fixture、客户端或模型。

保存的完整 Rkc 中，三处 mIe 调用把同一局部 s 作为第二参数；精确导入导出 metadata 给出 mIe←i1t→ARt、WKe←s1t→YRt 与 Ho←Nvn→Hf。YRt→Rkc 的 seed 调用和 Ho→Hf 的接收链都是限定静态 joins。实际 bootstrap、参数 e、gS.store、provider/native receiver、浏览器存储访问、落盘和重启读回、UI 调用及产品 mode 仍未知。

静态 publisher 会在 dispatch 前修改 pending buffer；同步抛错可跳过后续效果。permission 传给 onHydrated，没有成为完整 s 的 guard。超时仅设置 hydration 状态，首次 host sync 状态仍独立。Setup 同步失败与 cleanup 较早抛错不保证后续清理；没有 durable acknowledgement。这些是条件代码事实，没有观测为运行结果。

[薄 reader](mode-publisher-instantiation.json)连接[原合同](raw/mode-publisher-instantiation/author/mode-publisher-instantiation-contracts.json)、[23 条 journal](raw/mode-publisher-instantiation/author/evidence.jsonl)、[作者摘要](raw/mode-publisher-instantiation/author/summary.md)、[作者校验](raw/mode-publisher-instantiation/author/validation.json)、[精度修正历史](raw/mode-publisher-instantiation/author/author-precision-history.json)与[handoff](raw/mode-publisher-instantiation/author/metadata-handoff.json)。[独立 peer](raw/mode-publisher-instantiation/peer/independent-review.md)、[peer metadata](raw/mode-publisher-instantiation/peer/independent-review.json)及[最终收据](raw/mode-publisher-instantiation/peer/attempts/post-01/receipt.json)保留审查分母。

作者 query02 的实际耗时为 3840.554999 秒；未重复查询。零匹配不证明调用不存在，查询中的 JSON.stringify 重编码 hash 不等于原始 record 字节或排序 canonical hash。query01 初始化 TypeError 与 assemble01 SyntaxError 的真实失败历史仍保留。首次 835-check 只代表实际执行范围，其 overwritten kind 跳过 typed-pointer 循环；最终作者 1178-check/101 refs/68 unique 的范围单独保留。Peer 的 734 个小单位解析检查与 529 个 metadata 检查也分别记录，两个自有假设失败没有改写成作者或目标错误。

旧 Storage46、MODE26、清理 errata 和全局台账没有改写。新增功能、排除及 runtime 确认均为 0，fullAnalysisCompleted=false。源单位、AST、原始 REA、作者工具与 stdio、peer 含实现 capture 均仅本地保存。正式 metadata delivery 的[执行索引](raw/mode-publisher-instantiation/delivery-execution-provenance.json)只证明复制与 pins。
