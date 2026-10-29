# 本地文件夹资格上游的有限静态审查

固定基线：`codex-26.1007.30912-c5b273322a83`。本轮只审查一条资格链：项目设置页 `je` → `app-initial.fkn` → 保存导出索引中的本地 `Emn` 候选定义，以及五个直接或传递的 predicate helper。没有新增完整大 bundle AST、UI 操作、账户或历史读取、凭据读取、模型调用或目标 HTTP/IPC 执行。

**确认可排除功能/模块数为 0，运行验证链数为 0。** 这次补充收窄了数据资格条件，尚不能证明该分支属于哪一种客户端产品模式，也不能证明 Codex 本地项目都能进入它。

新 AST 的分母是 initial 原始 UTF-8 半开范围 `[1977943,1979523)`，共 **1,580 字节**，是可独立解析的连续完整 Program fragment。片段有 14 个顶层函数声明、469 个 AST 节点；其中只选定 **6 个完整函数、7 个调用**作本轮审查。14 个声明并不意味着 14 个函数都获得语义审查，更不是全部 initial 函数的分母。

| 选定完整函数 | UTF-8 起点 | 终点（不含） | 本轮作用 |
| --- | ---: | ---: | --- |
| `Emn` | 1979470 | 1979523 | `bO(project)` 且归一化 memory scope 为 `open-default` |
| `vO` | 1977943 | 1977992 | ID 的 `startsWith(g-p-)` 返回 true |
| `yO` | 1977992 | 1978150 | 验证 gizmo ID、名称和 sharing subjects 的数据形状 |
| `bO` | 1978150 | 1978419 | 私有、无分享对象、无特殊项目类型的数据条件 |
| `xmn` | 1978871 | 1978941 | `project_v2` 映射为 `project-only`，其他值映射为 `open-default` |
| `xO` | 1979381 | 1979470 | 项目具有 `memory_scope` 字段时调用 `xmn`，否则返回 undefined |

`bO` 要求 `yO`、`vO` 成立；`first_party_project_type` 不存在或为 null；`gizmo_snorlax_type` 为 null/undefined；`share_recipient` 为 `private`；`hasSharingSubjects` 不为 true；分享对象数量为 0。缺少 `memory_scope` 字段会让 `Emn` 失败。六个函数完整体没有直接网络/IPC 调用或 `chat/work/codex`、feature flag、环境变量读取；对象成员方法的真实实现和运行数据没有验证。这些是数据形状和资格事实，不能将 `g-p-` 前缀或 gizmo 字段等同于 ChatGPT 独占来源。

保存的完整项目模块 AST 确认 `je(i)` 使用 Program import `je ← initial.fkn`，`i` 来自 `project` prop。保存的完整 initial 导出索引确认 `Emn as fkn`。索引没有 `Emn` 的原模块完整定义 binding；本轮片段可以绑定片段内 helper，但没有验证原模块的全部外层词法作用域、同名声明或后续赋值。因此原始模块定义的最终绑定限制仍为 unknown。

设置页的完整 `localFolders` property 附加 `s && L && je(i)` 条件，并渲染 `local-folders-section.t`。`s` 来自 `c(rt)`，`c` 导入自 `shared.Ban`，其实现和值不在本轮范围。`L` 来自 **Pt 函数体内局部 `Re`（binding-448）**，其赋值为 `Me(Fe,a)` 或 memo cache；`Me ← initial.gkn`，局部 `Fe` 为 `i.gizmo.current_user_permission?.can_write`，`a` 为 `projectCrudStatus`。这个局部 `Re` 遮蔽了 Program import `Re ← initial.rOn`，不能按同名把 `L` 接到 `rOn`。本轮只保留这些消费者条件，不扩展 `gkn/Ban/local-folders-section` 的实现。

复用的 `pss/Dos/jos` guard notes 把同一个设置导出关联到包含 Work 和本地任务上下文的 sidebar/settings。它们不能证明所有上下文都能满足 `localFolders` 的数据与外层条件。专用 `sFs` 项目路由的映射、redirect 与默认 `oZ.allowWork=false` guard 适用于该路由，不能取代共享设置调用方，也不能作为这条 predicate 的排除边界。实际挂载、平台/entitlement/flag、完整消费者分母、项目数据来源与产品模式仍未知。

`review.json` 写入 6 个输入 artifact 的 path/bytes/SHA256，包含复用的 project/guard/AST JSON 与原始 project/AST journal pins；`sourceInputs` 和 `sourceFiles` 写入两份固定目标源码身份；`scripts` 写入两份自有 replay/validator 的 path/bytes/SHA256；`reproduction` 保留重放脚本和 parser implementation SHA256。目标 JS 只在本地作为冻结源身份引用，没有复制进公开分析产物。`evidence.jsonl` 的 38 条证据由 15 条新定位证据和 23 条保存证据复用组成。复用 ID 保留原始源身份与范围，`origin.sourceArtifact` 指向已 pin 的原产物；JSONL 指针按原始有序记录数组的零基索引解释。每条具有标准 claim、sourcePath/sourceHash、locator、spanSha256、method、confidence、verificationStatus，并保留 range/spanHash/origin。

重放命令：

```sh
/Users/nallylin/.nvm/versions/node/v22.23.2/bin/node scripts/analysis/project_upstream_review.mjs
python3 scripts/analysis/verify_project_upstream.py
```

独立 verifier 使用显式 expected review/journal SHA256 运行，`passed=true`、`errors=[]`。通过范围为 6 个函数、7 个调用、38 条证据 span/标准字段、6 个输入 pin、2 份 sourceFiles、2 个 scripts pin、2 份 sourceInputs pin、44 处去重 sourceArtifact 引用和 50 处证据引用（36 个不同 ID）。5 个调用保留明确的片段内函数目标，另 2 个成员调用保留 unknown 实现；没有将 unknown 绑定按名称连接到外层 import。

新证据与旧证据的验证范围只限本轮实际引用；没有声称全部旧 journal、历史 producer pin 或完整初始 bundle 都通过核验。独立验证结果保存在 `validation.json`，冻结产物和脚本身份保存在 `frozen-manifest.json`。冻结后应在可写副本中重放，以保留本轮产物身份。
