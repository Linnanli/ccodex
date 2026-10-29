38 个既存未对齐候选的限定静态审查已完成；旧 375/337/38 分母保持原样，未证实遗漏、未登记功能入口或新功能。

覆盖 5 个固定源码文件的哈希核对，以及 27 个既存完整作用域（205,464 字节；43,645 AST nodes 含合成包装），38 个调用与 caller 的原始字节范围/sha 全匹配。没有整 bundle AST 或目标实现复制。

16 literal 全部不含 slash，旧 337 已登记 deferred 方法全部含 slash。当前保存的 features.py 明确要求直接首参字面量含 slash，并排除模板插值；22 dynamic 首参也超出该直接字面筛选。当前脚本身份已 pin，历史 revision/执行未单独核实；只能确认当前规则与保存分母一致。

方法细化：20 项直接 literal/条件分支具有有限字符串；1 项 HTTP table 保存五个 own values，实际 key/未列或继承属性未知；17 项仍为参数、spread、对象属性或其他计算转发。旧 16/22 分类不改。

在 5513 个旧坐标范围中，38 call 的相等、双向包含和重叠全为 0。caller 关联 3 次，owner-class 关联 97 次，仅为空间上下文，不证明这些 request 已登记或属于相同 operation/feature。

既存 adapter kind：22 unresolved、6 HTTP fetch、4 selector、4 manager、1 resolver、1 coordination。逐项列出完整 caller、method AST/条件、保存合同与注入边界。exact qualified owner class 支持的语义细化单列，不覆盖旧分类或自动登记。

归属边界：这 5 个 embedded bundle 的 placement 与 adapter shape 不足以确定作用域 first-party/third-party 作者归属或 upstream 等价；逐项 attribution 均 unknown。未复制第三方或目标实现。Codex/ChatGPT/shared 模式、实时 receiver/host/transport 与行为均 unknown。

REA 保存 summary 的 5 文件均有 semantic/expanded relationship 受限记录；本批未恢复原 graph edges，也不把图中缺失当作漏项。raw 635 MB output 未读取或复制。

v1 完整 AST/原字节核验通过，但 finite 方法描述最初未涵盖静态 TemplateLiteral，保守记 unknown。原 v1 source/output/receipt 保留；v2 修正静态 template 和字面表的 metadata；peer 指出参数同名检查不等于 lexical binding，v3 进一步只保留 parameter-name-match candidate 并明确 binding/mutation unknown。旧分母均保持。所有新脚本真实 source/stdout/stderr/exit/hash 收据留于 attempts。

| 原 call ID | 首参分类 | 保存 adapter | 静态 method 结果 |
| --- | --- | --- | --- |
| REQUEST-WRAPPER-AST-00001 | single-literal | unresolved | ping |
| REQUEST-WRAPPER-AST-00004 | dynamic-or-conditional | unresolved | computed/forwarded unknown |
| REQUEST-WRAPPER-AST-00016 | dynamic-or-conditional | unresolved | computed/forwarded unknown |
| REQUEST-WRAPPER-AST-00019 | dynamic-or-conditional | unresolved | computed/forwarded unknown |
| REQUEST-WRAPPER-AST-05591 | dynamic-or-conditional | unresolved | computed/forwarded unknown |
| REQUEST-WRAPPER-AST-05748 | dynamic-or-conditional | unresolved | thread/stop, thread/unsubscribe |
| REQUEST-WRAPPER-AST-05818 | dynamic-or-conditional | unresolved | computed/forwarded unknown |
| REQUEST-WRAPPER-AST-05825 | dynamic-or-conditional | unresolved | computed/forwarded unknown |
| REQUEST-WRAPPER-AST-05856 | single-literal | unresolved | getAuthStatus |
| REQUEST-WRAPPER-AST-05860 | dynamic-or-conditional | unresolved | computed/forwarded unknown |
| REQUEST-WRAPPER-AST-05862 | dynamic-or-conditional | unresolved | computed/forwarded unknown |
| REQUEST-WRAPPER-AST-05868 | single-literal | coordination-socket-request | initialize |
| REQUEST-WRAPPER-AST-05871 | single-literal | unresolved | ide-context |
| REQUEST-WRAPPER-AST-05874 | single-literal | unresolved | thread-owner-discovery |
| REQUEST-WRAPPER-AST-05876 | single-literal | unresolved | thread-owner-discovery |
| REQUEST-WRAPPER-AST-05878 | dynamic-or-conditional | unresolved | computed/forwarded unknown |
| REQUEST-WRAPPER-AST-07064 | single-literal | desktop-http-fetch | POST |
| REQUEST-WRAPPER-AST-07079 | dynamic-or-conditional | host-manager-rpc-selector | computed/forwarded unknown |
| REQUEST-WRAPPER-AST-07178 | single-literal | desktop-http-fetch | POST |
| REQUEST-WRAPPER-AST-07226 | dynamic-or-conditional | unresolved | computed/forwarded unknown |
| REQUEST-WRAPPER-AST-07235 | dynamic-or-conditional | host-manager-rpc-selector | remoteControl/enable, remoteControl/disable |
| REQUEST-WRAPPER-AST-07247 | single-literal | host-manager-rpc-selector | gitDiffToRemote |
| REQUEST-WRAPPER-AST-07256 | single-literal | unresolved | fuzzyFileSearch |
| REQUEST-WRAPPER-AST-07259 | dynamic-or-conditional | host-manager-rpc-selector | computed/forwarded unknown |
| REQUEST-WRAPPER-AST-07263 | single-literal | desktop-http-fetch | GET |
| REQUEST-WRAPPER-AST-12659 | dynamic-or-conditional | resolver-request-facade | computed/forwarded unknown |
| REQUEST-WRAPPER-AST-12816 | dynamic-or-conditional | manager-request-facade | thread/stop, thread/unsubscribe |
| REQUEST-WRAPPER-AST-12886 | dynamic-or-conditional | unresolved | computed/forwarded unknown |
| REQUEST-WRAPPER-AST-12893 | dynamic-or-conditional | manager-request-facade | computed/forwarded unknown |
| REQUEST-WRAPPER-AST-12924 | single-literal | manager-request-facade | getAuthStatus |
| REQUEST-WRAPPER-AST-12928 | dynamic-or-conditional | manager-request-facade | computed/forwarded unknown |
| REQUEST-WRAPPER-AST-12930 | single-literal | unresolved | GET |
| REQUEST-WRAPPER-AST-12933 | single-literal | unresolved | POST |
| REQUEST-WRAPPER-AST-12935 | single-literal | unresolved | PUT |
| REQUEST-WRAPPER-AST-12938 | dynamic-or-conditional | desktop-http-fetch | GET, POST, PATCH, PUT, DELETE |
| REQUEST-WRAPPER-AST-12943 | dynamic-or-conditional | desktop-http-fetch | PUT, PATCH |
| REQUEST-WRAPPER-AST-12944 | single-literal | desktop-http-fetch | DELETE |
| REQUEST-WRAPPER-AST-16923 | dynamic-or-conditional | unresolved | computed/forwarded unknown |
