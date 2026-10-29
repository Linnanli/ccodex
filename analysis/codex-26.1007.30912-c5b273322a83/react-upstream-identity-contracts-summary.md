# React 候选发行与包导入边界

固定基线 `codex-26.1007.30912-c5b273322a83`。本批保留 33 条原始分析记录。

4/17 既有线索、6 个保存的目标 factory 与 3 个官方 production 模块有单独分母。官方 react／react-dom 19.2.7 归档通过 SRI 与 SHA-1，npm gitHead 与官方 tag 对应；包导入候选为 react、react-dom、react-dom/client，第一方 annotation 适配器另行保留。

114 个 export occurrence、92 个参数形状、38 个有限转发形状和 4 个 root 方法形状不证明完整 factory 等价或未修改。基线实际 lock、JSX／compiler／Scheduler 绑定、全依赖闭包、模式和恢复后的运行效果仍待确认。正式核心只发布作者九项 allowlist；核验资料单独列为 support，完整实现／归档保持 local-only。

[原始结果](react-upstream-identity-contracts.json)、[原始记录](react-upstream-identity-contracts-evidence.jsonl)、[作者摘要](react-upstream-identity-contracts-raw-summary.md)、[核验](react-upstream-identity-contracts-validation.json)、[同行摘要](react-upstream-identity-contracts-peer-review.md)、[冻结清单](react-upstream-identity-contracts-manifest.json)、[发布来源](react-upstream-identity-contracts-provenance.json)。

公开 HTTP 回执递归省略 set-cookie 响应头；此文件是派生元数据，原始回执留在本地，原 pin 与省略位置见发布来源。

仅发布明确允许的分析元数据与核验资料。完整源码、保存的完整单元、第三方实现和归档留在本地，不进入客户端恢复源码。原记录字段逐字保留，未增加全局 journal、运行观察或功能确认数。
