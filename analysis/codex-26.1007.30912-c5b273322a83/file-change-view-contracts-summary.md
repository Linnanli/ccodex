固定基线的文件与变更查看静态合同当前为版本2：原30条合同保留，仅C012缓存预热与C018 worker请求的异常边界由两条元数据errata限定。旧36功能组、原30条journal与51个选定单位的分母不变；新增source/global/功能/运行观察均为0。

[当前合同](file-change-view-contracts-v2.json) · [两条errata记录](file-change-view-errata-evidence.jsonl) · [修订清单](file-change-view-errata.json) · [限定delta审查](file-change-view-errata-peer-review.json) · [交付来源](file-change-view-contracts-delivery-provenance.json)。

Wt仅吞掉callback返回值经local .catch处理的Promise rejection；同步调用或.catch异常进入outer catch并受token/generation条件约束。IWn.request先插入pending；返回Promise rejection可清理，同步sender/.catch异常逃出非async请求，所选路径没有该清理。已保存async preload声明不证明实际bridge receiver。

[原冻结核心](raw/file-change-view-contracts/original/file-change-view-contracts.json)及[原30行journal](raw/file-change-view-contracts/original/evidence.jsonl)保存历史原字节；[原peer](raw/file-change-view-contracts/original/peer-review.json)仍为completed-with-two-static-wording-findings，1486项metadata检查不等于全语义通过。[原摘要](raw/file-change-view-contracts/original/summary.md)、[errata原摘要](raw/file-change-view-contracts/errata/summary.md)也原字节保留。原摘要相对链接按原本地上下文理解，本阅读页仅提供正式位置导航。

作者609、限定peer130、errata封存后162为不同范围，分别保存、不相加、未在交付时重跑。实际UI、transport/main/app-server/Git receiver、持久化、运行时序与模式仍待证实；Git写操作没有由名称得到确认。交付脚本只读显式元数据，不读取原JS/AST/完整单位或执行目标。一次作者目录诊断误对旧保存AST做字节哈希读取，未解析/复制/引入新事实，详见交付provenance披露。
