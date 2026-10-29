# 分析计划验收审计

审计基线 `codex-26.1007.30912-c5b273322a83`。只检查本轮分析的9项标准与6阶段交付，不要求客户端已经实现、独立构建或打包。依据是公开产物的逐文件SHA256快照；本次没有运行目标程序或提交模型任务。

9项标准中4项已满足、5项部分满足；6阶段中第一阶段交付已满足，其余5阶段部分满足。这个计数是逐条分析交付验收，不是功能恢复完成率。

## AC-01 已满足：输入版本和哈希已固定，分析结果未混用版本。

已有依据：固定baseline、ASAR hash、版本/构建及归档外清单；原安装、冻结、运行副本复核一致。公开CLI独立版本/来源记录，没有当作冻结CLI相同源码。

保留限制（不阻断本条）：7个unpacked声明哈希矛盾仍以observed-untrusted保留；这不否定实际输入固定，也不能写成声明完整性通过。

维护或后续分析动作：继续以新baseline处理输入版本变化；保持公开CLI版本/发布物/源码commit身份分别登记。

证据定位：CRITERIA-AUDIT-E0001, CRITERIA-AUDIT-E0002, CRITERIA-AUDIT-E0003。

## AC-02 部分满足：已登记所有发现的文件、入口和功能候选，并说明分析覆盖的范围。

已有依据：21,089个ASAR成员和3,806个磁盘文件已登记；REA输入/解析分母及补充扫描范围有统计。已形成868主类/100辅助入口候选账本，并分列176support与337deferred；菜单411稳定合同有来源和分母定义。

具体缺口：账本是已发现入口/合同候选的并集，尚无已确认feature映射或operation等价；36大组不是完整功能总分母。438/14,805非node_modules JS候选扫描不代表穷尽入口，renderer注册覆盖仍unknown，flags/后台事件和动态生成域仍未说明完全覆盖。

必要下一步：在现有entry ledger上补实际注册/绑定、operation/payload/后效和feature的N:M映射；补flags/后台事件/其余registry及动态域覆盖，逐类别记录未扫描与未映射队列。

证据定位：CRITERIA-AUDIT-E0004, CRITERIA-AUDIT-E0005, CRITERIA-AUDIT-E0009, CRITERIA-AUDIT-E0020, CRITERIA-AUDIT-E0021, CRITERIA-AUDIT-E0015, CRITERIA-AUDIT-E0077, CRITERIA-AUDIT-E0078, CRITERIA-AUDIT-E0076, CRITERIA-AUDIT-E0075。

## AC-03 部分满足：已区分 Codex、ChatGPT 专属、共享和未知项，排除理由可追溯。

已有依据：36组按20 codex/9 shared/2 chatgpt/5 unknown登记并显式标inferred；路由/guard和认证边界保留条件、未知和共享约束。

具体缺口：确认ChatGPT排除数为0；36组归属全部推断，438模块全部mode unknown。没有逐排除项已验证Codex调用方闭包和保留依赖表。

必要下一步：将product access、chat/work、local/cloud、账户/平台/开关分别建模；逐拟排除模块追踪实际调用方与共享依赖，证据不足保持unknown。

证据定位：CRITERIA-AUDIT-E0017, CRITERIA-AUDIT-E0018, CRITERIA-AUDIT-E0023, CRITERIA-AUDIT-E0026, CRITERIA-AUDIT-E0052。

## AC-04 部分满足：每个保留功能已追踪到足以说明其职责的模块和关键跨进程或外部边界。

已有依据：19条process/transport边界、central switch、Route、request wrapper及预测fork链已有静态证据；相关小范围调用完整span可核对。

具体缺口：features.json的codeChain仍是通用描述；尚无每个保留功能→模块职责→IPC/服务/存储的逐功能映射。337已发布wrapper候选中242接收方未确定，状态所有权/副作用不穷尽。

必要下一步：以具体feature_id追踪入口到操作、接收方、payload/response、状态和持久化；按unknown receiver优先补静态绑定，不能仅凭同名method连边。

证据定位：CRITERIA-AUDIT-E0024, CRITERIA-AUDIT-E0025, CRITERIA-AUDIT-E0036, CRITERIA-AUDIT-E0038, CRITERIA-AUDIT-E0039, CRITERIA-AUDIT-E0016。

## AC-05 已满足：第三方依赖有版本与来源依据；无法确认的条目列出调查动作。

已有依据：202条依赖记录均有versionBasis、原source path/hash及unresolved/引入建议；17/17嵌入hint现在各有源码自报版本绑定及5项具体TODO，CSV将自报与实际上游版本分列。5个根包已核对精确版本上游归档。

保留限制（不阻断本条）：此条允许版本/来源无法确认而列出调查动作；71根声明缺实际安装版本、17嵌入发行身份未确认及若干私有来源未知均明确记录，不能把自报写成锁定上游。取得分发、修改确认、保留调用方闭包和具体引入决定仍影响阶段3/6。

维护或后续分析动作：执行现有逐条来源/版本/修改/边界/模式/运行TODO；依据保留功能确定必要依赖和取得方式。无需为满足本条声称所有版本已确认或这轮已生成最终锁文件。

证据定位：CRITERIA-AUDIT-E0045, CRITERIA-AUDIT-E0044, CRITERIA-AUDIT-E0082, CRITERIA-AUDIT-E0083, CRITERIA-AUDIT-E0042, CRITERIA-AUDIT-E0046。

## AC-06 已满足：原生、Wasm、辅助程序、定制运行时和私有服务均有独立记录。

已有依据：native-runtime分别列归档native/Wasm、112磁盘runtime/helper、8外部Wasm、Owl元数据和756源码/构建输入；runtime-api单列实际Owl标识及定制接口/生命周期，8类服务/transport契约和私有包/认证来源未知另有独立记录。

保留限制（不阻断本条）：满足的是已发现类别分别记录；实际Node/Electron版本/ABI、源码取得、完整保留能力的调用方和私有服务归属仍unknown。1242个Electron来源调用点和229路径仅属10选定文件，不能证明全部runtime兼容或可替换。

维护或后续分析动作：在架构/实施分析中继续把工件、定制API和私有服务绑定到保留功能/进程，补ABI、接口后效和取得/替代决定；本条不要求已成功重建native、Owl或独立客户端。

证据定位：CRITERIA-AUDIT-E0047, CRITERIA-AUDIT-E0048, CRITERIA-AUDIT-E0049, CRITERIA-AUDIT-E0050, CRITERIA-AUDIT-E0051, CRITERIA-AUDIT-E0084, CRITERIA-AUDIT-E0085, CRITERIA-AUDIT-E0086, CRITERIA-AUDIT-E0054, CRITERIA-AUDIT-E0055, CRITERIA-AUDIT-E0056, CRITERIA-AUDIT-E0057, CRITERIA-AUDIT-E0052。

## AC-07 已满足：Source map 覆盖、构建输入缺失、REA 解析限制和动态关系均有说明。

已有依据：17,848/17,848限定扩展文件的source-map扫描与缺失结果、30项构建输入出现缺口、REA partial/truncated预算和226,389 unknown均说明。动态/接收方与实际运行限制明确保留。

保留限制（不阻断本条）：此项满足的是覆盖和限制的说明；不会关闭semantic图截断、动态关系或构建缺口，不能解读成这些问题已解决。

维护或后续分析动作：根据保留功能继续定向AST/trace并记录新分母；外部/压缩/远端map不在当前结论范围，需有线索再补查。

证据定位：CRITERIA-AUDIT-E0006, CRITERIA-AUDIT-E0007, CRITERIA-AUDIT-E0008, CRITERIA-AUDIT-E0010, CRITERIA-AUDIT-E0011, CRITERIA-AUDIT-E0012, CRITERIA-AUDIT-E0013, CRITERIA-AUDIT-E0039。

## AC-08 部分满足：主要行为与静态结论已对照，未验证项有明确触发条件。

已有依据：30条有限UI/草稿/项目/任务观察、唯一授权README任务、5命令契约、11纯代码场景及32fork负例有独立结果。已完成样例在新PID独立重启后从原自有线程行恢复原提示/精确回复，README未变、0新模型任务、自有进程已停。

具体缺口：一个已完成任务恢复不能证明中断执行恢复；主要任务失败/取消/审批/文件修改/PTY等尚未逐功能对照。36个功能conditions仍是generic文字；新观察也未与账本feature ID关联，不能从30记录推算功能覆盖。

必要下一步：为保留功能建立normal/error/cancel/restart场景、精确flag/account/host/platform条件及static-to-runtime映射；对中断/取消/审批/失败等未验证路径逐条登记可触发条件和必要样例。

证据定位：CRITERIA-AUDIT-E0058, CRITERIA-AUDIT-E0059, CRITERIA-AUDIT-E0060, CRITERIA-AUDIT-E0090, CRITERIA-AUDIT-E0091, CRITERIA-AUDIT-E0092, CRITERIA-AUDIT-E0019, CRITERIA-AUDIT-E0022, CRITERIA-AUDIT-E0061, CRITERIA-AUDIT-E0062, CRITERIA-AUDIT-E0063, CRITERIA-AUDIT-E0064。

## AC-09 部分满足：项目结构建议、恢复顺序和验收条件能够引用分析证据。

已有依据：implementation-plan有process边界、恢复顺序候选、开始条件和升级建议；独立11条局部维护边界建议有138原始范围映射，明确非原目录和全模块覆盖。

具体缺口：本条检查结构建议、恢复顺序、验收条件三者的证据关联，不要求客户端已实现，也不以438 proposedPath空值否定独立局部建议。恢复顺序目前主要为阶段与开始条件模板，未形成关键前后依赖的逐项证据关联；完整保留功能及场景验收条件仍缺feature/entry/contract和预期结果映射。

必要下一步：为恢复阶段/具体功能的前后依赖引用已分析的模块/状态/服务边界；将验收条目关联功能ID、精确使用条件、操作步骤、预期后效和原始证据。完整结构及工程决定继续作为阶段6交付，本条不要求执行客户端实现或打包。

证据定位：CRITERIA-AUDIT-E0066, CRITERIA-AUDIT-E0067, CRITERIA-AUDIT-E0068, CRITERIA-AUDIT-E0069, CRITERIA-AUDIT-E0088, CRITERIA-AUDIT-E0089, CRITERIA-AUDIT-E0015。

## 六阶段交付

| 阶段 | 状态 | 已有交付 | 具体缺口 |
|---|---|---|---|
| 第一阶段 固定输入与文件清单 | 已满足 | 输入层交付齐备：固定包和归档外清单、runtime元数据、限定扩展source-map全扫描及构建引用缺口。7声明矛盾保留，不冒充完整性通过。 | 实际Node/Electron兼容和ABI仍是后续runtime接口调查，当前阶段未以根devDependency冒充实际runtime。 |
| 第二阶段 功能范围盘点 | 部分满足 | 有36候选大组、968入口/辅助记录账本、菜单/route/中央handler及guard的限定来源。 | 缺全域注册覆盖、operation/feature关联和功能总分母、精确条件/行为、逐保留/排除调用方闭包；868主类/100辅助不能当功能数。 |
| 第三阶段 第三方依赖识别 | 部分满足 | 202依赖记录及17/17嵌入hint来源/版本依据和具体未知TODO齐备；5根包有上游比较。 | 计划本阶段要求的所需调用方闭包、混合bundle完整范围、修改库/多版本决定、私有/native/Wasm取得与替代可行性还未齐备；记录未知本身不是失败理由。 |
| 第四阶段 REA 架构与调用链分析 | 部分满足 | process链、限定AST/定制runtime API契约、公开schema导出差异、命令/fork负例均有证据。 | 结构/语义图仍partial；保留功能sender/receiver和状态/持久化未逐功能闭合；局部维护建议不等于所有published chunks已形成职责明确模块。 |
| 第五阶段 行为与依赖验证 | 部分满足 | 30有限观察、自有样例完成及重启恢复、命令/纯代码/负例有可复查结果。 | 未覆盖主要功能的失败/取消/审批/中断恢复和文件修改/PTY链；许多使用条件和static-to-runtime关联仍泛化。 |
| 第六阶段 形成实施依据 | 部分满足 | 阶段报告、恢复/升级建议、11局部维护建议与138原始范围映射已交付，显式标前置未完成。 | 完整源码目录/包/代码范围映射、ChatGPT剥离闭包、依赖/runtime/构建输入工程决定和逐功能验收表仍未齐备。未实现最终客户端不是本轮扣项。 |

## 功能总分母

当前路由、设置、中央handler等候选可合成入口候选账本，不能直接合成可信的功能总数。170个Route构造、144固定path、52动态模板实例、143顶层case、112处理组、28嵌套命令和53设置候选属于不同统计单位；相加、字符串去重或按共用handler合并都会混淆功能与入口。

新账本已有868主类候选、100辅助、176support和337deferred分列；1088静态合同关系及41个同完整handler项尚未形成operation等价或feature映射。36大组使用条件仍是同一泛化待追踪文字；另有11局部维护建议/138来源映射，不能忽略这些建议，也不能当成完整项目边界。flags、其余注册域及entry到operation到feature映射仍需补足。

粒度规则：先固定可审查的功能粒度：以可独立触发的用户目标或后台领域行为及其可观察后置契约为候选；流程阶段、通知、条件分支和URL数据实例不自动另算功能。相同任务的成功/错误/取消/恢复先作场景，只有独立触发及独立职责才提出拆分。保持粒度规则和每次merge/split记录，不能把36大组或schema方法数预设为最终粒度。

1. **扩展现有entry ledger，保持各类别原始计数分开。** 沿用现有baseline-local entry_id与原来源映射；对真实注册点补baseline+source hash+完整AST span+binding identity的证明，记录kind、注册调用方、handler/export identity、payload discriminant、route/setting/command参数和完整条件。layout、导航目标、命令metadata与真实注册分层标注。
2. **建立静态操作图。** 由entry沿lexical binding/import/export/参数注入追到实际handler、IPC接收方、服务契约、状态/持久化后效。动态receiver或传递依赖未绑定就保留unknown edge，禁止同名method或字符串自动合并。
3. **提出operation候选，拆开复用handler中的实际领域动作。** 同一个handler按payload action/type和不同可观察结果可能包含多个功能；多个route/menu/shortcut也可能只是同一动作入口。参数化URL实例、host/account/platform分支通常是条件/数据，只有职责或可观察后置契约不同才提出独立功能。
4. **只对证据支持的别名操作作候选合并。** 可用union-find维护已审查的same-operation等价边，前提是实际绑定/实现关系、输入意义及后效契约得到证据支持，并且条件域兼容；所有merge/split决策记录来源及理由。共享handler只产生候选边，不自动等价；无法证明语义相同则保持两个候选或unknown，不能因为共用组件/服务method直接合并。
5. **生成stable feature_id与entry/operation/contract/scenario的N:M映射。** 逐feature登记名称、职责、保留/排除/unknown、模式/触发条件、输入输出和失败取消恢复、来源、共享依赖及后续复刻观察点。36个原有大组作为taxonomy标签，可拆分或关联，不能锁死完整功能数。
6. **执行闭包与漏项检查，保留未映射队列。** 每个已发现entry必须映射到feature、明确的非功能性layout/metadata、可追溯排除，或unresolved queue；每个保留feature必须能返回原始入口和关键边界。评估未覆盖源文件与动态生成域，账户/flag未触发不能作为不存在。
7. **按功能ID发布多种状态分母。** 仅在入口范围和动态边界有明确穷尽说明、合并/拆分已审查后才称该baseline功能总分母N。分别给N_discovered、N_mode_classified、N_retained、N_excluded、N_unresolved及每功能分析/行为场景状态。分母未闭合时发布已审查features数量+未映射entries数量，不给整体完成百分比。

达到闭包后按feature_id统计保留、排除、unknown及分析/行为状态；在此之前只发布已审查功能数和未映射入口数，不给整体百分比。

## 可检查证据

所有下列定位对应的原始公开文件SHA256及字节快照均在机器结果中登记。JSON pointer/集合运算/文本标记足以复查本审计判断；这不重跑原REA或全量源码校验。

- `CRITERIA-AUDIT-E0001` [baseline.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/baseline.json)：`{"kind": "json-pointer", "pointer": "/archiveSha256"}`；"c5b273322a833ce5165429d468021cc6289a11cc68d075b80ae773bd7fb6731f"
- `CRITERIA-AUDIT-E0002` [baseline-reverification.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/baseline-reverification.json)：`{"kind": "json-pointer", "pointer": "/archiveCopiesMatchBaseline"}`；true
- `CRITERIA-AUDIT-E0003` [baseline-reverification.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/baseline-reverification.json)：`{"kind": "json-pointer", "pointer": "/conflictCount"}`；7
- `CRITERIA-AUDIT-E0004` [files.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/files.json)：`{"kind": "collection-aggregate", "jsonPointer": "/archiveFiles", "operation": "count"}`；21089
- `CRITERIA-AUDIT-E0005` [files.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/files.json)：`{"kind": "collection-aggregate", "jsonPointer": "/applicationFiles", "operation": "count"}`；3806
- `CRITERIA-AUDIT-E0006` [source-maps.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/source-maps.json)：`{"kind": "json-pointer", "pointer": "/summary"}`；{"eligibleFiles": 17848, "scannedFiles": 17848, "readOrHashErrors": 0, "jsonParseErrors": 0, "byGroupAndExtension": {"asar:.js": 15047, "asar:.json": 1005, "asar:.mjs": 20, "asar:.css": 317, "disk:.json": 113, "disk:.mjs": 37, "disk:.css": 12, "disk:.js": 1280, "disk:.cjs": 17}, "rawMarkerOccurrences": 11325, "rawMarkerFiles": 11318, "confirmedDirectiveComments": 11316, "falsePositiveOccurrences": 9, "unresolvedMarke…（完整值见JSON）
- `CRITERIA-AUDIT-E0007` [source-maps.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/source-maps.json)：`{"kind": "json-pointer", "pointer": "/limitations"}`；["Released-file source maps do not establish original repository build inputs or upstream modifications.", "No map URLs outside the frozen inventory were downloaded.", "Files outside the listed extensions and compressed archive contents are not scanned for embedded map directives."]
- `CRITERIA-AUDIT-E0008` [build-inputs.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/build-inputs.json)：`{"kind": "collection-aggregate", "jsonPointer": "", "operation": "count"}`；30
- `CRITERIA-AUDIT-E0009` [rea-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/rea-summary.json)：`{"kind": "json-pointer", "pointer": "/evidence/normalized_result/statistics"}`；{"relevant_files": 16240, "nested_asar_containers": 0, "text_bytes_read": 411558389, "invalid_utf8_files": 0, "parsed_javascript_files": 15212, "visited_ast_nodes": 50063032, "findings": 139120, "modules": 71, "parse_failures": 0}
- `CRITERIA-AUDIT-E0010` [rea-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/rea-summary.json)：`{"kind": "json-pointer", "pointer": "/evidence/normalized_result/graph/coverage"}`；{"status": "partial", "truncated": false, "omitted_count": null, "limits": [{"name": "javascript_analysis_parent_result_budget_bytes", "value": 3753842092, "unit": "bytes"}, {"name": "javascript_analysis_semantic_result_budget_bytes", "value": 0, "unit": "bytes"}, {"name": "javascript_analysis_semantic_result_budget_bytes", "value": 1123, "unit": "bytes"}, {"name": "javascript_analysis_worker_heap_limit_bytes", "valu…（完整值见JSON）
- `CRITERIA-AUDIT-E0011` [rea-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/rea-summary.json)：`{"kind": "json-pointer", "pointer": "/evidence/normalized_result/semantic_graph/coverage/status"}`；"partial"
- `CRITERIA-AUDIT-E0012` [rea-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/rea-summary.json)：`{"kind": "json-pointer", "pointer": "/evidence/normalized_result/semantic_graph/coverage/truncated"}`；true
- `CRITERIA-AUDIT-E0013` [rea-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/rea-summary.json)：`{"kind": "json-pointer", "pointer": "/counts/semantic_graph.unknowns"}`；226389
- `CRITERIA-AUDIT-E0014` [analysis-state.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/analysis-state.json)：`{"kind": "json-pointer", "pointer": "/fullAnalysisCompleted"}`；false
- `CRITERIA-AUDIT-E0015` [analysis-state.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/analysis-state.json)：`{"kind": "json-pointer", "pointer": "/featureDenominatorEstablished"}`；false
- `CRITERIA-AUDIT-E0016` [features.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/features.json)：`{"kind": "collection-aggregate", "jsonPointer": "", "operation": "count"}`；36
- `CRITERIA-AUDIT-E0017` [features.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/features.json)：`{"kind": "collection-aggregate", "jsonPointer": "", "operation": "mode-counts"}`；{"codex": 20, "shared": 9, "unknown": 5, "chatgpt": 2}
- `CRITERIA-AUDIT-E0018` [features.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/features.json)：`{"kind": "collection-aggregate", "jsonPointer": "", "operation": "all-mode-inferred"}`；true
- `CRITERIA-AUDIT-E0019` [features.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/features.json)：`{"kind": "collection-aggregate", "jsonPointer": "", "operation": "generic-conditions-count"}`；36
- `CRITERIA-AUDIT-E0020` [feature-coverage.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/feature-coverage.json)：`{"kind": "json-pointer", "pointer": "/lexicallyScannedFiles"}`；438
- `CRITERIA-AUDIT-E0021` [feature-coverage.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/feature-coverage.json)：`{"kind": "json-pointer", "pointer": "/nonNodeModulesJsDiscovered"}`；14805
- `CRITERIA-AUDIT-E0022` [feature-coverage.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/feature-coverage.json)：`{"kind": "json-pointer", "pointer": "/featuresRuntimeVerified"}`；0
- `CRITERIA-AUDIT-E0023` [analysis-state.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/analysis-state.json)：`{"kind": "json-pointer", "pointer": "/confirmedChatGptExclusions"}`；0
- `CRITERIA-AUDIT-E0024` [modules.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/modules.json)：`{"kind": "collection-aggregate", "jsonPointer": "", "operation": "count"}`；438
- `CRITERIA-AUDIT-E0025` [modules.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/modules.json)：`{"kind": "collection-aggregate", "jsonPointer": "", "operation": "all-module-paths-null"}`；true
- `CRITERIA-AUDIT-E0026` [modules.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/modules.json)：`{"kind": "collection-aggregate", "jsonPointer": "", "operation": "all-module-mode-unknown"}`；true
- `CRITERIA-AUDIT-E0027` [route-contract-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/route-contract-summary.json)：`{"kind": "json-pointer", "pointer": "/actualRouteConstructionCalls"}`；170
- `CRITERIA-AUDIT-E0028` [route-contract-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/route-contract-summary.json)：`{"kind": "json-pointer", "pointer": "/staticallyResolvedPathCalls"}`；144
- `CRITERIA-AUDIT-E0029` [route-contract-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/route-contract-summary.json)：`{"kind": "json-pointer", "pointer": "/dynamicPathCalls"}`；2
- `CRITERIA-AUDIT-E0030` [route-contract-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/route-contract-summary.json)：`{"kind": "json-pointer", "pointer": "/staticallyResolvedMapInstances"}`；52
- `CRITERIA-AUDIT-E0031` [route-contract-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/route-contract-summary.json)：`{"kind": "json-pointer", "pointer": "/pathlessCalls"}`；24
- `CRITERIA-AUDIT-E0032` [route-contract-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/route-contract-summary.json)：`{"kind": "json-pointer", "pointer": "/requestedSourceFiles"}`；2
- `CRITERIA-AUDIT-E0033` [host-message-contract-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/host-message-contract-summary.json)：`{"kind": "json-pointer", "pointer": "/literalLabels"}`；143
- `CRITERIA-AUDIT-E0034` [host-message-contract-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/host-message-contract-summary.json)：`{"kind": "json-pointer", "pointer": "/handlerGroups"}`；112
- `CRITERIA-AUDIT-E0035` [host-message-contract-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/host-message-contract-summary.json)：`{"kind": "json-pointer", "pointer": "/nestedSubDispatchCases"}`；28
- `CRITERIA-AUDIT-E0036` [host-message-contract-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/host-message-contract-summary.json)：`{"kind": "json-pointer", "pointer": "/limitations"}`；["Inventory covers the complete selected main switch, not all Electron/RPC/worker/native handlers.", "Caller payload schemas, response envelopes, timeouts and per-feature domain semantics are not inferred from label names.", "Bound receiver, imported namespace and lexical value are distinct from a fully resolved runtime callee.", "Callback calls are recorded separately; callsite presence does not prove unconditional …（完整值见JSON）
- `CRITERIA-AUDIT-E0037` [settings.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/settings.json)：`{"kind": "collection-aggregate", "jsonPointer": "", "operation": "count"}`；53
- `CRITERIA-AUDIT-E0038` [request-wrapper-contracts.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/request-wrapper-contracts.json)：`{"kind": "json-pointer", "pointer": "/scanDenominator"}`；{"previousLiteralCandidateRows": 337, "previousDistinctLiteralMethods": 108, "previousCandidateFiles": 15, "selectedFiles": 37, "parsedFiles": 37, "astCallsites": 375, "singleLiteralCallsites": 353, "dynamicOrConditionalCallsites": 22, "publishedCandidatesLinked": 337, "astClassificationCounts": {"unresolved": 264, "app-server-extension-connection": 5, "coordination-socket-request": 1, "desktop-http-fetch": 6, "host-…（完整值见JSON）
- `CRITERIA-AUDIT-E0039` [request-wrapper-contracts.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/request-wrapper-contracts.json)：`{"kind": "json-pointer", "pointer": "/unknowns"}`；["Unresolved callsites are retained with their lexical bindings; no whole-bundle/full-program call coverage claim.", "KI is a manager RPC selector with runtime-dependent alternatives, not unconditional proof of AppHost MessagePort transport.", "Observed manager/connection adapters do not establish public app-server method/schema compatibility or successful UI execution.", "No target code, UI, IPC, history read or pro…（完整值见JSON）
- `CRITERIA-AUDIT-E0040` [dependency-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/dependency-summary.json)：`{"kind": "json-pointer", "pointer": "/counts"}`；{"archiveMembers": 21089, "nodeModulesPackageJson": 51, "installedPackageOccurrences": 49, "installedUniqueNames": 34, "packageFormatDescriptors": 2, "metadataErrors": 0, "rootRuntimeDeclarations": 46, "rootDevDeclarations": 32, "externalPackageJson": 59, "externalPackageOccurrences": 58, "externalPackageUniqueNames": 31, "externalPackageDescriptors": 1, "externalMetadataErrors": 0, "rootDeclarationsWithInstalledMani…（完整值见JSON）
- `CRITERIA-AUDIT-E0041` [dependency-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/dependency-summary.json)：`{"kind": "json-pointer", "pointer": "/publishedCounts"}`；{"asar-installed-package": 49, "bundled-version-hint": 17, "external-installed-package": 58, "root-declaration": 78, "dependenciesCsvRows": 202, "evidenceRecords": 2561}
- `CRITERIA-AUDIT-E0042` [dependency-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/dependency-summary.json)：`{"kind": "json-pointer", "pointer": "/limitations"}`；["Attribution says may be included and mixes multiple subprojects; it is not a lockfile or actual runtime inclusion proof.", "Package name/version metadata does not prove its shipped files are unmodified upstream.", "Import scanning is lexical; expressions and custom loaders require REA/AST and runtime corroboration.", "Codex/ChatGPT/shared mode ownership remains unresolved until callers are traced.", "Native file id…（完整值见JSON）
- `CRITERIA-AUDIT-E0043` [dependencies.csv](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/dependencies.csv)：`{"kind": "collection-aggregate", "jsonPointer": "", "operation": "count"}`；202
- `CRITERIA-AUDIT-E0044` [dependencies.csv](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/dependencies.csv)：`{"kind": "collection-aggregate", "jsonPointer": "", "operation": "bundle-hint-empty-investigation-records"}`；[]
- `CRITERIA-AUDIT-E0045` [dependencies.csv](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/dependencies.csv)：`{"kind": "collection-aggregate", "jsonPointer": "", "operation": "dependency-investigation-accounting"}`；{"records": 202, "versionBasisAndSourceEvidence": 202, "recommendedIntegrationAndUnknowns": 202, "blankUpstreamSourceColumnIds": ["installed-039", "installed-040", "installed-041", "external-004", "external-005", "external-015", "external-016"], "incompleteInvestigationIds": []}
- `CRITERIA-AUDIT-E0046` [dependency-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/dependency-summary.json)：`{"kind": "json-pointer", "pointer": "/upstreamComparison"}`；{"path": "upstream-comparison.json", "sha256": "7fb44e3f4e8f30fe73f76b653d1ef016b5cddb04f9dd0832e92bdd629436264d", "comparedPackages": 5, "linkedRootRecords": 10, "scope": "five exact-version frozen root packages; nested occurrences excluded", "runtimeVerified": false}
- `CRITERIA-AUDIT-E0047` [native-runtime.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/native-runtime.json)：`{"kind": "collection-aggregate", "jsonPointer": "/archiveArtifacts", "operation": "count"}`；49
- `CRITERIA-AUDIT-E0048` [native-runtime.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/native-runtime.json)：`{"kind": "collection-aggregate", "jsonPointer": "/diskRuntimeBinaries", "operation": "count"}`；112
- `CRITERIA-AUDIT-E0049` [native-runtime.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/native-runtime.json)：`{"kind": "collection-aggregate", "jsonPointer": "/externalWasmArtifacts", "operation": "count"}`；8
- `CRITERIA-AUDIT-E0050` [native-runtime.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/native-runtime.json)：`{"kind": "collection-aggregate", "jsonPointer": "/runtimeMetadata", "operation": "count"}`；5
- `CRITERIA-AUDIT-E0051` [native-runtime.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/native-runtime.json)：`{"kind": "collection-aggregate", "jsonPointer": "/sourceInputs", "operation": "count"}`；756
- `CRITERIA-AUDIT-E0052` [auth-boundary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/auth-boundary.json)：`{"kind": "json-pointer", "pointer": "/conclusion"}`；{"status": "account-origin-unresolved", "statement": "A separate CODEX_HOME and Electron userData do not establish credential isolation. Frozen JS confirms shell environment import, inherited app-server environment, optional external websocket/local-daemon transports, and a secret-auth-storage config gate. Which mechanism caused the already signed-in runtime observed by the root agent has not been proven."}
- `CRITERIA-AUDIT-E0053` [auth-boundary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/auth-boundary.json)：`{"kind": "json-pointer", "pointer": "/reproducibleIndependentTestConditions"}`；{"status": "proposed-not-executed", "conditions": ["Use a test OS account whose shell startup and OS credential store contain no personal Codex/ChatGPT authentication; CODEX_HOME alone cannot isolate os.userInfo or OS keychain.", "Launch the frozen application executable directly with an explicit environment allowlist rather than inheriting parent process.env. Include required graphical/runtime variables, absolute PA…（完整值见JSON）
- `CRITERIA-AUDIT-E0054` [request-wrapper-contracts.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/request-wrapper-contracts.json)：`{"kind": "collection-aggregate", "jsonPointer": "/contracts", "operation": "count"}`；8
- `CRITERIA-AUDIT-E0055` [request-wrapper-contracts.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/request-wrapper-contracts.json)：`{"kind": "json-pointer", "pointer": "/contracts/2/kind"}`；"desktop-http-fetch"
- `CRITERIA-AUDIT-E0056` [request-wrapper-contracts.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/request-wrapper-contracts.json)：`{"kind": "json-pointer", "pointer": "/contracts/6/kind"}`；"coordination-socket-request"
- `CRITERIA-AUDIT-E0057` [request-wrapper-contracts.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/request-wrapper-contracts.json)：`{"kind": "json-pointer", "pointer": "/contracts/7/kind"}`；"app-host-messageport-service"
- `CRITERIA-AUDIT-E0058` [behavior-observations.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/behavior-observations.json)：`{"kind": "collection-aggregate", "jsonPointer": "", "operation": "count"}`；30
- `CRITERIA-AUDIT-E0059` [behavior-checks.md](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/behavior-checks.md)：`{"kind": "text-line-marker", "line": 3, "marker": "这是有限 UI 观察"}`；"基线：`codex-26.1007.30912-c5b273322a83`。这是有限 UI 观察、一次未提交草稿重启验证及一个获授权的只读桌面任务，不能代表整个功能组通过。"
- `CRITERIA-AUDIT-E0060` [behavior-checks.md](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/behavior-checks.md)：`{"kind": "text-line-marker", "line": 46, "marker": "后续需继续验证其他本地任务路径"}`；"后续需继续验证其他本地任务路径、错误、取消、审批、文件变更、终端和执行中断恢复，并将每次运行关联到具体功能、IPC 与 app-server 契约。云端、远程主机、平台和账户条件分别登记，不以菜单存在代替执行验证；额外模型任务需另获授权。"
- `CRITERIA-AUDIT-E0061` [chunk-fixture-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/chunk-fixture-summary.json)：`{"kind": "json-pointer", "pointer": "/fixtureCount"}`；11
- `CRITERIA-AUDIT-E0062` [chunk-fixture-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/chunk-fixture-summary.json)：`{"kind": "json-pointer", "pointer": "/limitations"}`；["Tests establish extracted pure-code behavior in this Node VM only; not Electron/Owl IPC delivery, renderer UI reachability or application completeness.", "Sender backpressure, critical priority, lifecycle loading retry and lost-ack handling are not executed by these pure-function fixtures.", "No public dependency equivalence, upstream modification or complete mode boundary is established.", "Preload shared-object c…（完整值见JSON）
- `CRITERIA-AUDIT-E0063` [fork-negative-protocol-comparison.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/fork-negative-protocol-comparison.json)：`{"kind": "json-pointer", "pointer": "/verification"}`；{"cliHashesVerified": true, "generationSnapshotsVerified": true, "runnerSnapshotsVerified": true, "schemaHashesVerified": true, "profilesAndRawHashesVerified": true, "caseResponsesMatchRaw": true, "protectedArtifactsUnchanged": true, "actualCliSessions": 4, "forkRequests": 32, "forkSuccesses": 0, "rawRecords": 80, "methodAllowlist": ["initialize", "initialized", "thread/fork"], "targetModelTurnRequests": 0, "allSessi…（完整值见JSON）
- `CRITERIA-AUDIT-E0064` [fork-negative-protocol-comparison.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/fork-negative-protocol-comparison.json)：`{"kind": "json-pointer", "pointer": "/limitations"}`；["All valid requests stop at missing-rollout lookup; no successful fork or prediction semantics were observed.", "Same lookup errors or unknown-field behavior do not prove complete backend compatibility.", "This fixture does not resolve the desktop dynamic sender or actual appServerVersion.", "Public npm binary-to-source-commit binding remains unknown."]
- `CRITERIA-AUDIT-E0065` [analysis-state.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/analysis-state.json)：`{"kind": "json-pointer", "pointer": "/publicProtocolComparison/exportedSchemas"}`；{"generatedFilesCompared": 764, "schemaShape": {"different": 49, "equal": 715}, "referencedContract": {"different": 45, "equal": 715, "not-applicable-definition-collection": 4}, "methodVariantsCompared": 466, "effectiveContract": {"different": 11, "equal": 455}, "methodSetsEqualInEveryUnionAndMode": true, "generatedFileSetsEqualInBothModes": true}
- `CRITERIA-AUDIT-E0066` [implementation-plan.md](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/implementation-plan.md)：`{"kind": "text-line-marker", "line": 3, "marker": "状态：前置分析未完成"}`；"基线：`codex-26.1007.30912-c5b273322a83`。状态：前置分析未完成；本文件给出恢复顺序候选，尚不能作为完整实施计划验收。"
- `CRITERIA-AUDIT-E0067` [implementation-plan.md](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/implementation-plan.md)：`{"kind": "text-line-marker", "line": 44, "marker": "最终目录和包边界"}`；"- 最终目录和包边界，以及每个模块的原始代码映射。"
- `CRITERIA-AUDIT-E0068` [implementation-plan.md](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/implementation-plan.md)：`{"kind": "text-line-marker", "line": 34, "marker": "阶段 0 的调查可与证据充分的模块恢复并行"}`；"阶段 0 的调查可与证据充分的模块恢复并行。未解决的服务、原生或私有依赖继续占据完整验收表，mock 或占位页面不算通过。"
- `CRITERIA-AUDIT-E0069` [implementation-plan.md](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/implementation-plan.md)：`{"kind": "text-line-marker", "line": 40, "marker": "升级交付包括新版本独立基线"}`；"升级交付包括新版本独立基线、入口/契约/依赖/行为差分、受影响模块清单和回归结果。数据格式变化需有迁移、备份与回退验证；维护者新增功能通过明确模块或适配接口保留，不依靠直接覆盖生成目录。升级验收仍使用新基线的完整功能清单。"
- `CRITERIA-AUDIT-E0070` [gaps.md](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/gaps.md)：`{"kind": "text-line-marker", "line": 3, "marker": "状态：调查进行中"}`；"基线：`codex-26.1007.30912-c5b273322a83`。状态：调查进行中。下表按对完整功能复刻和独立构建的影响排列；未解决项不计为已完成。"
- `CRITERIA-AUDIT-E0071` [evidence-validation.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/evidence-validation.json)：`{"kind": "json-pointer", "pointer": "/evidenceCount"}`；42006
- `CRITERIA-AUDIT-E0072` [report.md](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/report.md)：`{"kind": "text-line-marker", "line": 3, "marker": "本报告未宣称分析完成或客户端已重建"}`；"状态：分析进行中。固定基线 `codex-26.1007.30912-c5b273322a83`，版本 `26.1007.30912`，构建 `20156`。本报告未宣称分析完成或客户端已重建。"
- `CRITERIA-AUDIT-E0073` [menu-command-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/menu-command-summary.json)：`{"kind": "json-pointer", "pointer": "/sourceFiles"}`；[{"sourcePath": "app.asar/.vite/build/main-CqEoQDOU.js", "sha256": "09d19386e1f23cf4ccbc950fc40d85a1e8a064a08be588b2a4be6a89f6ada9e6", "sourceBytes": 3824411, "astNodes": 958314, "scope": "complete-source", "parsedSourceBytes": 3824411, "fragmentRanges": null, "archiveByteOffset": 7673297, "parserErrors": 0}, {"sourcePath": "app.asar/.vite/build/src-BJv5Mk7n.js", "sha256": "72e2b366d574206f76fc079c79b64c31ce378970a79…（完整值见JSON）
- `CRITERIA-AUDIT-E0074` [menu-command-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/menu-command-summary.json)：`{"kind": "json-pointer", "pointer": "/contractRecords"}`；411
- `CRITERIA-AUDIT-E0075` [menu-command-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/menu-command-summary.json)：`{"kind": "json-pointer", "pointer": "/rendererWholeSourceRegistrationCoverage"}`；"unknown"
- `CRITERIA-AUDIT-E0076` [menu-command-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/menu-command-summary.json)：`{"kind": "json-pointer", "pointer": "/denominatorDefinitions"}`；{"metadataCommandSchemaSites": "Distinct command object source spans reachable from the bound exported metadata registry initializer, including finite-map callback schema spans; metadata is not a handler registration.", "metadataCommandInstances": "Statically resolved metadata instances: fixed ID schemas plus finite literal array/map/template expansions, preserving shared source spans; not runtime registrations.", "n…（完整值见JSON）
- `CRITERIA-AUDIT-E0077` [functional-entry-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/functional-entry-summary.json)：`{"kind": "json-pointer", "pointer": ""}`；{"baselineId": "codex-26.1007.30912-c5b273322a83", "entryRecords": 968, "primaryEntryRecords": 868, "auxiliaryEntryRecords": 100, "supportNodes": 176, "deferredCandidateRecords": 337, "byDenominator": {"route-constructions": 170, "route-conversion-consumers": 3, "navigate-component-targets": 47, "menu-contract-records": 411, "host-top-level-message-cases": 143, "settings-lexical-candidates": 53, "direct-app-server-ca…（完整值见JSON）
- `CRITERIA-AUDIT-E0078` [functional-entry-validation.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/functional-entry-validation.json)：`{"kind": "json-pointer", "pointer": ""}`；{"status": "passed", "baselineId": "codex-26.1007.30912-c5b273322a83", "ledgerSha256": "a48d715799db66408c96990caba2e45a28dc2dafb4486bc1514413c722c5fff9", "ledgerBytes": 22973530, "inputArtifactsHashVerified": 14, "jsonPointerOccurrencesVerified": 10688, "evidenceReferenceOccurrencesVerified": 74939, "uniqueExistingEvidenceReferences": 8712, "sourceCoordinateOccurrencesVerifiedAgainstFrozenJournalsAndManifest": 14227…（完整值见JSON）
- `CRITERIA-AUDIT-E0079` [functional-entry-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/functional-entry-summary.json)：`{"kind": "json-pointer", "pointer": "/associationByDenominator"}`；{"route-constructions": {"recordCount": 170, "withReviewedContractLinks": 170, "withoutReviewedContractLinks": 0, "withReviewedHandlerIdentityLinks": 0, "withReviewedOperationEquivalenceLinks": 0, "mappedToConfirmedFeature": 0}, "route-conversion-consumers": {"recordCount": 3, "withReviewedContractLinks": 3, "withoutReviewedContractLinks": 0, "withReviewedHandlerIdentityLinks": 0, "withReviewedOperationEquivalenceLin…（完整值见JSON）
- `CRITERIA-AUDIT-E0080` [functional-entry-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/functional-entry-summary.json)：`{"kind": "json-pointer", "pointer": "/entriesWithReviewedOperationEquivalenceLinks"}`；0
- `CRITERIA-AUDIT-E0081` [functional-entry-summary.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/functional-entry-summary.json)：`{"kind": "json-pointer", "pointer": "/entriesMappedToConfirmedFeature"}`；0
- `CRITERIA-AUDIT-E0082` [embedded-dependency-investigation-actions.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/embedded-dependency-investigation-actions.json)：`{"kind": "json-pointer", "pointer": "/scope"}`；{"candidateDenominator": 17, "sourceAndRecommendationMapped": 17, "unknownFieldActionsPerCandidate": 5, "sourceDistributionDecisionsCompleted": 0, "runtimeValidationsCompleted": 0}
- `CRITERIA-AUDIT-E0083` [embedded-dependency-continuation-validation.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/embedded-dependency-continuation-validation.json)：`{"kind": "json-pointer", "pointer": "/candidateHintIntervalOverlapVerified"}`；17
- `CRITERIA-AUDIT-E0084` [runtime-api-contracts.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/runtime-api-contracts.json)：`{"kind": "json-pointer", "pointer": "/scope"}`；{"selection": "Fixed 10 entry/main/bootstrap/preload/network files; mixed published bundles, not recovered modules or full app coverage", "selectedSourceFiles": 10, "parsedSourceFiles": 10, "auxiliaryHelperFiles": 1, "totalCoreBytes": 5379973, "allCallAndConstructorExpressions": 90246, "sourceConfirmedElectronDerivedCallSites": 1242, "electronDerivedMemberReferences": 241, "unresolvedNameOnlyCandidateCalls": 4293, "u…（完整值见JSON）
- `CRITERIA-AUDIT-E0085` [runtime-api-contracts.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/runtime-api-contracts.json)：`{"kind": "json-pointer", "pointer": "/actualRuntime"}`；{"runtimeName": "owl", "evidenceIds": ["RUNTIME-REVIEW-0016", "RUNTIME-REVIEW-0001"], "metadata": {"sourcePath": "Contents/Resources/owl-electron-app.json", "sourceHash": "dfeb6f520a13168b84fad22e1aa61b9eb87d27c8a0daf17f6f82eb81756e4307", "bytes": 237, "metadata": {"runtimeName": "owl", "runtimeArchiveSha": "d47046415e1f69a9c2dd6b272cdf131225bc508582c43b7487065251b1bf9cd8"}}, "actualElectronVersion": "unknown", "actu…（完整值见JSON）
- `CRITERIA-AUDIT-E0086` [runtime-api-validation.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/runtime-api-validation.json)：`{"kind": "json-pointer", "pointer": "/status"}`；"passed"
- `CRITERIA-AUDIT-E0087` [runtime-api-contracts.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/runtime-api-contracts.json)：`{"kind": "json-pointer", "pointer": "/limitations"}`；["Actual packaged runtimeName owl is separate metadata; root devDependency electron version is not an actual runtime version.", "Public API documentation match does not establish Owl replacement equivalence, native ABI, all callback/error ordering, or packaging.", "Resolver caps at 1500 recursive steps per outer expression; budget-hit paths are retained as unknown and per-file counts recorded.", "Dynamic computed pro…（完整值见JSON）
- `CRITERIA-AUDIT-E0088` [module-boundary-proposals.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/module-boundary-proposals.json)：`{"kind": "json-pointer", "pointer": "/scope"}`；{"proposalCount": 11, "fullModuleCoverage": false, "clientCodeGenerated": false}
- `CRITERIA-AUDIT-E0089` [module-boundary-proposals.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/module-boundary-proposals.json)：`{"kind": "collection-aggregate", "jsonPointer": "/proposals", "operation": "proposal-mapping-count"}`；138
- `CRITERIA-AUDIT-E0090` [runtime-artifacts/owned-task-recovery-04.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/runtime-artifacts/owned-task-recovery-04.json)：`{"kind": "json-pointer", "pointer": "/observations"}`；{"threadId": "01a134be-d8bd-7bb0-a124-5cb92fe7b1d3", "newModelTasksSubmitted": 0, "initialOwnPromptOccurrences": 0, "initialExpectedReplyOccurrences": 0, "ownProjectLabelOccurrences": 3, "ownedThreadLinkCount": 0, "navigationIdentityEvidence": {"path": "runtime-artifacts/owned-recovery-project-thread-attributes.json", "sha256": "30b5d7e18b88d47882281ffd711f475076facc3ffedc22c0ae1fc5a2b000953a", "observedRowId": "loca…（完整值见JSON）
- `CRITERIA-AUDIT-E0091` [runtime-artifacts/owned-task-recovery-04.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/runtime-artifacts/owned-task-recovery-04.json)：`{"kind": "json-pointer", "pointer": "/limitations"}`；["Only the already authorized synthetic task, its exact prompt/reply and owned project label are inspected.", "Restoring one completed task does not verify interrupted execution, errors, approvals or every storage layer.", "Profile, CODEX_HOME and CLI identity do not establish authentication isolation.", "A visible sentinel alone is not a task-completion event; the original completed turn is independently identified.…（完整值见JSON）
- `CRITERIA-AUDIT-E0092` [runtime-artifacts/owned-recovery-runtime-stop.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/runtime-artifacts/owned-recovery-runtime-stop.json)：`{"kind": "json-pointer", "pointer": "/observations/allKnownOwnedProcessesGone"}`；true
- `CRITERIA-AUDIT-E0093` [raw/publication/20261013T115019432678Z/run.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/raw/publication/20261013T115019432678Z/run.json)：`{"kind": "json-pointer", "pointer": "/exitCode"}`；0
- `CRITERIA-AUDIT-E0094` [raw/publication/20261013T115019432678Z/run.json](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/raw/publication/20261013T115019432678Z/run.json)：`{"kind": "json-pointer", "pointer": "/runnerUnchangedDuringRun"}`；true

本审计结果：[criteria-audit.json](/Users/nallylin/Documents/code/ccodex/.analysis-local/completion-audit-work/criteria-audit.json)。公开报告和既有冻结证据没有被修改。
