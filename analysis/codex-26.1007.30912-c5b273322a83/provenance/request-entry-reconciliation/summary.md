# AC-02 request entry reconciliation

仅对保存产物做范围对齐：375 个完整 AST wrapper call = 353 literal + 22 dynamic/conditional。旧台账的 968 entry、337 deferred 和 176 support 是不同角色的分母；337 deferred 来源是旧 literal 词法候选，不是整个客户端功能总数。

337 个 wrapper call 通过已保存 candidateLink 的 FEATURE ID、精确 artifact pin/JSON pointer、相同 sourcePath/hash 和唯一范围包含关系，对应全部 337 个旧 deferred。旧词法范围严格位于完整 AST call 内，337 个匹配均不属于 same span，不能由此推导同一操作或功能身份。方法/名称仅作一致性检查，从未作为身份键。

剩余 38 个 AST call（16 literal、22 dynamic）没有已保存的旧候选关联或完整主坐标/直接 evidence ID 对齐证据，逐条列于 notAlignedCandidatesForReview。记录为“未对齐”，不自动判作未登记或漏项。台账的所有记录下保存坐标也逐一检查，并把外围包含关系留作空间范围证据；它们不能替代调用登记或功能关联。已证实漏项清单为空；全功能分母继续 unknown。

已对齐的 337 项中，95 项保存 wrapper 分类（5 extension connection、66 host-manager selector、1 resolver facade、23 manager facade），242 项仍 unresolved。95 项只列为旧 deferred 注释复核候选，不更改角色、不升级协议/feature/mode/runtime，也不修改任何旧账本。

所有输入保存在 inputs，27 个 input receipt 含旧 ledger 的 14 份 sourceArtifacts pin；37 份源码 receipt 仅核对已保存 wrapper/files 与 frozen inventory 元数据，没有读取原始目标源码或重哈希目标 span。本批不执行目标、CLI、UI、网络或模型。旧 ledger 独立 validation/manifest 已保存；未找到独立 wrapper validation/manifest，不借命名或未列 wrapper 的发布 run 宣称覆盖。历史审计 snapshot 按实际 hash 独立记录。

独立核验结果和最终产品 pins 写于 validation.json，实际分析脚本、stdout/stderr 和 exit receipt 保留于 attempts/v1。新增 journal 每个候选一行，仅记录 artifact reconciliation；所有 original-source/runtime 结论维持旧范围。
