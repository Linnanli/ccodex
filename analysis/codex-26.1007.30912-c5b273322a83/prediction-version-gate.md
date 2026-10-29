# 预测功能版本门槛静态补充

基线：`codex-26.1007.30912-c5b273322a83`。这里仅推导输入两个固定版本字串时的条件结果，未执行目标代码或预测请求。

绑定链为 main fge 的 r.Ti → src-CP7XXlpZ.js 的 exports.Ti getter → I。完整 AST 范围确认 `experimentalPredictionForkMode` 通常使用 `0.162.0-alpha.20` 门槛；I 先接受合法版本，再对 `0.162.0-alpha.17.2` 明确返回 true。

| 输入字串 | 静态 gate 结果 | 来源分支 |
| --- | --- | --- |
| 0.162.0-alpha.17.2 | true | Exact-version exception after valid-version guard: e === 0.162.0-alpha.17.2 returns true before P |
| 0.162.0 | true | P compares equal major/minor/patch, stable prerelease is empty and threshold prerelease is nonempty; a.length===0 returns 1 |

公开 `0.162.0` 的基础版本与门槛相同，P 的正式版优先于预发布分支返回 1；冻结 alpha.17.2 虽低于 alpha.20，实际走明确例外。

后续[版本来源补充](app-server-version-origin-summary.md)确认选定mB候选从initialize响应userAgent解析并写入initializedAppServerVersion，getter提供该独立字段；installedCodexVersion另行取得。实际运行实例和版本值、动态host接收方、通知顺序及后端启用状态仍unknown；其他fge条件也可能提前返回null。这项静态门槛检查不能消除experimentalPredictionMode schema差异，也不能证明公开后端支持该实验参数。此前174条调用参数证据见[调用调查](experimental-prediction-usage.json)。

新增解析范围为一个203,781字节模块及 main 的两个完整原始片段，没有重跑全应用。95条证据的源文件 hash、UTF-16到UTF-8定位和完整 span digest 均已复核；见 [结构化记录](prediction-version-gate.json) 与 [证据](prediction-version-gate-evidence.jsonl)。公开 npm 二进制与 Rust源码提交的关系仍为 unknown。
