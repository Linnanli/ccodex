# REA 6.4.0 Bootstrap / Preload 补充分析

2026-10-13。对冻结基线 `codex-26.1007.30912-c5b273322a83` 的真实文件完成一次小范围静态分析，以及两次 feature trace。命令、时间、退出码、原始 stdout/stderr 路径和哈希均已保存。没有修改客户端源码或运行中的应用。

## 输入与身份

输入目录包含原样复制的 `package.json`、`.vite/build/early-bootstrap.js`、`.vite/build/preload.js` 和 `.vite/build/sandbox-preload.js`。4 个文件合计 18073 字节，运行前复核冻结原文件与副本哈希。原始归档 SHA-256 为 `c5b273322a833ce5165429d468021cc6289a11cc68d075b80ae773bd7fb6731f`。

[source-map.json](source-map.json) 是原路径和哈希的来源映射，**不是 JavaScript source map**。独立调查目录具有自己的 REA 根哈希 `d7603fc40a518476aa08b19aba2b16c58dfd4231e3e23de158bce67c09898f23`；它与完整 ASAR 图具有不同身份。未复制的 import、源码映射、主进程 handler 和 renderer consumer 均在本次范围之外。原文件中混合的 Sentry 片段保留用于证据完整性；此次没有生成重建工程或第三方实现代码。

## 实际结果

静态分析 [analyze.run.json](analyze.run.json) 退出码为 0，得到 Evidence `ev_4ea4d310a87223d27447ffe932a60ced32cf79820ccf5270b0a91f5eeb573363`。3 个 JavaScript 文件均解析，访问 3115 个 AST 节点，解析失败为 0。

| 结果 | 节点 / 关系 | coverage | truncated |
| --- | --- | --- | --- |
| application graph | 63 / 63 edges | partial | false |
| semantic graph | 2024 / 1828 relations | unknown | false |

语义图另保留 661 个 unknown。REA 识别 3 个 context bridge API：`electronBridge`、`codexWindowType`、`__SENTRY_IPC__`；API 成员在结构图中未解开。IPC 统计为 26 operations、1 literal channel、25 dynamic channel operations、0 main handlers。这里的 0 不能用于宣称完整客户端缺少 handler 或 API 成员。

第一次 [trace.run.json](trace.run.json) 对 `channel` 类型的 `codex_desktop:message-from-view` 做 exact、case-sensitive、both 追踪，退出码 0，返回 no-match。这个字符串实际存在于原 `preload.js`，但其 IPC 调用使用常量别名，REA 6.4.0 的结构图将这些 channel expression 保留为 dynamic；结果说明这条查询未匹配结构图，不说明功能缺失。原始 no-match Evidence `ev_b32ccbe29334743d45f1c33180d55ca3ad1359490f732ae0a6d6edae89937b1f` 已保留。

随后 [trace-shared-object.run.json](trace-shared-object.run.json) 对原源码直接写出的 `codex_desktop:get-shared-object-snapshot` 做同样查询，退出码 0，得到 Evidence `ev_bd6ac6080c324bde72016551a4a7f064d7152f6408bad17e5d7a16bc19a64524`，匹配 1 个 seed，返回 63 nodes / 63 edges，coverage partial。双向追踪包含关联资产、包及图的结构关系，所以这个数量不代表单个功能的调用链长度。结果为静态图关系，未证明执行、跨进程配对或端到端行为。

完整原始结果位于 `.analysis-local/supplemental/codex-26.1007.30912-c5b273322a83/rea-bootstrap-bridges-v1/raw/`。该目录未加入 Git；[result-summary.json](result-summary.json) 保留可审阅的计数、coverage、限制和 Evidence ID。

## Trace CLI 的实际输入接口

发布包中的 [applicationCommands.js](tool-interface/dist/cli/applicationCommands.js) 为 `trace-application-feature` 注册一个参数 `inputJson`，支持 inline JSON 或 JSON 文件路径。它使用 [javascriptFeatureTraceSchemas.js](tool-interface/dist/domain/javascript/javascriptFeatureTraceSchemas.js) 的严格 schema：

```json
{
  "application": "这里必须放完整原始 Evidence 对象，不能是路径、ID 或裁剪后的 graph",
  "native_observations": [],
  "seed": {"kind":"channel", "value":"codex_desktop:get-shared-object-snapshot", "match":"exact", "case_sensitive":true},
  "direction": "both"
}
```

上例仅解释外层字段；字符串占位不能直接运行。seed kind 可为 `node-id`、`route`、`string`、`api`、`channel`、`module`、`native-export`；direction 可为 outgoing、incoming、both。MCP 的 [applicationWorkflowInputContracts.js](tool-interface/dist/contracts/javascript/applicationWorkflowInputContracts.js) 另接受 `retained-evidence` 同会话引用，独立 CLI 使用的 schema 不包含该分支。

[evidence.js](tool-interface/dist/domain/evidence.js) 会根据包括 `raw_result` 和 `normalized_result` 在内的语义内容重新认证 Evidence ID；[JavaScriptApplicationEvidenceGraph.js](tool-interface/dist/application/javascript/JavaScriptApplicationEvidenceGraph.js) 另验证 provider、predicate、subject、参数及 graph shape。不能删除巨大 semantic graph、保留旧 ID 后把剩余部分伪称原始 Evidence。

## 635 MB Evidence 的读入限制

基线完整返回文件为 635380481 bytes（约 606 MiB），记录 SHA-256 `520cebeac9826dcd80fa3d9221cfe1849fe1fe4dcadd98171f09c7e19745dd5d`。此轮没有对该大文件实际执行 trace，以下限制根据固定发布包源码核实。

[parseCliJsonInput](tool-interface/dist/cliJsonInput.js) 会先尝试解析 inline 文本，然后读取路径指向的 regular file。[JsonInputFile.js](tool-interface/dist/application/JsonInputFile.js) 中的 8 MiB 是选择 native parser 的阈值，**不是文件大小上限**。较大文件使用 64 KiB chunk、严格 UTF-8 和流式 JSON tokenizer，避免先构造整个 JSON 文档字符串。文件必须稳定、格式合法、只有一个 JSON 值；BOM 和无效 UTF-8 会被拒绝。

流式输入最终仍组装完整对象图。工具根据当前 heap headroom 检查容器、键、字符串及 primitive 的保守占用估计，内存不足时返回 resource constraint。单个 scalar 还受 Node `MAX_STRING_LENGTH` 限制，本机值为 536870888 UTF-16 code units。随后 schema 验证、Evidence digest 认证及追踪还会占用更多内存；不存在“文件小于某个固定 MB 数即可成功”的保证。`--max-heap-mb` 控制源码 worker，不能为 trace 进程增加主堆；trace 主堆需使用 Node 的 `--max-old-space-size`，并结合机器实际内存设置。

[streamedJsonOutput.js](tool-interface/dist/cli/streamedJsonOutput.js) 与 [jsonOutput.js](tool-interface/dist/cli/jsonOutput.js) 对普通命令的 `--format json` / `jsonl` 也提供流式输出。保存原始结果应避免 `--token-count`、展示用 filter 和 token window。

工具 [wrap_rea_trace_input.py](../../../../scripts/analysis/wrap_rea_trace_input.py) 可逐块将完整 Evidence 原始字节包进上述 JSON 外层，并强制验证已有的完整文件 SHA-256；不会先 `JSON.parse(readFile(...))` 或重新生成 Evidence。已用本次小 Evidence 验证嵌入字节完全一致，记录于 [wrapper.run.json](wrapper.run.json)。实际大文件可以使用以下参数模板：

```bash
python3 scripts/analysis/wrap_rea_trace_input.py \
  --evidence /绝对路径/rea-application-observed.json \
  --expected-sha256 520cebeac9826dcd80fa3d9221cfe1849fe1fe4dcadd98171f09c7e19745dd5d \
  --output /绝对路径/trace-input.json \
  --seed-value codex_desktop:get-shared-object-snapshot

node --max-old-space-size=8192 \
  /private/tmp/ccodex-rea-tooling/install/node_modules/rea-agents/scripts/rea.mjs \
  trace-application-feature /绝对路径/trace-input.json --format json \
  > /绝对路径/trace-result.json 2> /绝对路径/trace-stderr.jsonl
```

8192 是待结合资源核实的主堆配置示例；此处不把该大文件命令标记为已运行或已通过。源码快照及哈希见 [source-index.json](tool-interface/source-index.json)，机器可读的限制说明见 [cli-input-limits.json](cli-input-limits.json)。
