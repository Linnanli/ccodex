公开 npm CLI 与冻结客户端 CLI 的完整导出协议已完成静态比较。两端方法集合与生成文件集合一致；契约结构存在下列字段差异。

| 导出 | 文件共同 / 两端各自总数 | 文件结构相同 / 不同 | v2 单文件共同 / 两端各自总数 | v2 结构相同 / 不同 |
|---|---:|---:|---:|---:|
| stable | 317 / 317 | 295 / 22 | 278 / 278 | 259 / 19 |
| experimental | 447 / 447 | 420 / 27 | 400 / 400 | 377 / 23 |

所有计数均以 manifest 记录且实际存在的 JSON 文件为分母；公开独有文件 0 个，冻结独有文件 0 个。每端 764 个模式限定文件对应 447 个去重文件名；experimental 比 stable 多 130 个文件名。v2 单文件指 `v2/*.json`，根目录的 `codex_app_server_protocol.v2.schemas.json` 已纳入全部文件比较。

| 导出 | 消息 union | 共同方法数 | 有效契约相同 / 不同 | 公开独有 / 冻结独有 |
|---|---|---:|---:|---:|
| stable | ClientRequest | 105 | 105 / 0 | 0 / 0 |
| stable | ClientNotification | 1 | 1 / 0 | 0 / 0 |
| stable | ServerRequest | 10 | 10 / 0 | 0 / 0 |
| stable | ServerNotification | 84 | 79 / 5 | 0 / 0 |
| experimental | ClientRequest | 170 | 169 / 1 | 0 / 0 |
| experimental | ClientNotification | 1 | 1 / 0 | 0 / 0 |
| experimental | ServerRequest | 11 | 11 / 0 | 0 / 0 |
| experimental | ServerNotification | 84 | 79 / 5 | 0 / 0 |

| 导出 | union / 方法 | JSON pointer | 差异方向 |
|---|---|---|---|
| stable | ServerNotification / `item/completed` | `/definitions/ThreadItem/oneOf/11/properties/model` | public-added |
| stable | ServerNotification / `item/completed` | `/definitions/ThreadItem/oneOf/11/properties/reasoningEffort` | public-added |
| stable | ServerNotification / `item/started` | `/definitions/ThreadItem/oneOf/11/properties/model` | public-added |
| stable | ServerNotification / `item/started` | `/definitions/ThreadItem/oneOf/11/properties/reasoningEffort` | public-added |
| stable | ServerNotification / `thread/started` | `/definitions/ThreadItem/oneOf/11/properties/model` | public-added |
| stable | ServerNotification / `thread/started` | `/definitions/ThreadItem/oneOf/11/properties/reasoningEffort` | public-added |
| stable | ServerNotification / `turn/completed` | `/definitions/ThreadItem/oneOf/11/properties/model` | public-added |
| stable | ServerNotification / `turn/completed` | `/definitions/ThreadItem/oneOf/11/properties/reasoningEffort` | public-added |
| stable | ServerNotification / `turn/started` | `/definitions/ThreadItem/oneOf/11/properties/model` | public-added |
| stable | ServerNotification / `turn/started` | `/definitions/ThreadItem/oneOf/11/properties/reasoningEffort` | public-added |
| experimental | ClientRequest / `thread/fork` | `/definitions/ThreadForkParams/properties/experimentalPredictionMode` | public-removed |
| experimental | ServerNotification / `item/completed` | `/definitions/ThreadItem/oneOf/11/properties/model` | public-added |
| experimental | ServerNotification / `item/completed` | `/definitions/ThreadItem/oneOf/11/properties/reasoningEffort` | public-added |
| experimental | ServerNotification / `item/started` | `/definitions/ThreadItem/oneOf/11/properties/model` | public-added |
| experimental | ServerNotification / `item/started` | `/definitions/ThreadItem/oneOf/11/properties/reasoningEffort` | public-added |
| experimental | ServerNotification / `thread/started` | `/definitions/ThreadItem/oneOf/11/properties/model` | public-added |
| experimental | ServerNotification / `thread/started` | `/definitions/ThreadItem/oneOf/11/properties/reasoningEffort` | public-added |
| experimental | ServerNotification / `turn/completed` | `/definitions/ThreadItem/oneOf/11/properties/model` | public-added |
| experimental | ServerNotification / `turn/completed` | `/definitions/ThreadItem/oneOf/11/properties/reasoningEffort` | public-added |
| experimental | ServerNotification / `turn/started` | `/definitions/ThreadItem/oneOf/11/properties/model` | public-added |
| experimental | ServerNotification / `turn/started` | `/definitions/ThreadItem/oneOf/11/properties/reasoningEffort` | public-added |

`public-added` 表示字段仅在公开导出中出现；`public-removed` 表示字段仅在冻结导出中出现。JSON 中的差异项保留具体 schema 值；其中 `shipped` 表示冻结输入。

通知差异落在 `ThreadItem` 的 `subAgentActivity` 分支：公开导出多出可选 `model` 与 `reasoningEffort`。experimental 的 `thread/fork` 参数在冻结导出中多出可选 `experimentalPredictionMode`。

v2 集合还包含两处引用差异：`SkillMetadata.path` 与 `SkillSummary.path` 的 `$ref` 在公开导出指向 `LegacyAppPathString`，在冻结导出指向 `AbsolutePathBuf`。两种命名类型的导出形状都是 `string`；本次精确结构比较保留类型名与引用路径差异。

| 导出 | v2 文件 | JSON pointer | 公开值 / 冻结值 |
|---|---|---|---|
| stable | `v2/PluginReadResponse.json` | `/definitions/SkillSummary/properties/path/anyOf/0/$ref` | `#/definitions/LegacyAppPathString` / `#/definitions/AbsolutePathBuf` |
| stable | `v2/SkillsListResponse.json` | `/definitions/SkillMetadata/properties/path/$ref` | `#/definitions/LegacyAppPathString` / `#/definitions/AbsolutePathBuf` |
| experimental | `v2/PluginReadResponse.json` | `/definitions/SkillSummary/properties/path/anyOf/0/$ref` | `#/definitions/LegacyAppPathString` / `#/definitions/AbsolutePathBuf` |
| experimental | `v2/SkillsListResponse.json` | `/definitions/SkillMetadata/properties/path/$ref` | `#/definitions/LegacyAppPathString` / `#/definitions/AbsolutePathBuf` |

逐方法有效契约包含 union 根约束和该方法分支的 `allOf`，再递归收集引用闭包；这也覆盖 `ServerNotification` 根上的可选 `emittedAtMs`。另保留只含方法分支的比较。仅移除 schema 文档关键字 `description`、`title`、`$schema`、`$comment`；字段名、默认值、其他 annotation、约束、引用名称及数组顺序保留。

集合 bundle 的 `definitions/v2` 作为命名 schema 容器逐项归一化，并按真实 JSON Pointer 校验引用。两个集合 bundle 的完整内容已比较；它们的空泛对象根不用于独立引用闭包统计。

所有输入文件、CLI 和导出 schema 已按记录复核 SHA-256；manifest 与比较函数的字节快照随本次结果保存。此前九候选结果和 generation manifest 的内容保持不变。

此阶段没有运行后端，也不据方法名推断产品模式归属。公开 npm 元数据未提供 gitHead，导出结果不建立二进制与源码 commit 的绑定，schema 差异也不直接证明运行时不兼容。

证据：[完整比较数据](</Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/exported-protocol-comparison.json>)，[公开生成记录](</Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/public-protocol-generation-npm.json>)，[冻结生成记录](</Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/protocol-generation.json>)。

复跑时指定新的 `--run-name` 和 `--output-name`，以保留本次结果：

```sh
python3 scripts/analysis/compare_exported_protocol.py --baseline codex-26.1007.30912-c5b273322a83 --run-name exported-protocol-comparison-v4 --output-name exported-protocol-comparison-v4
```
