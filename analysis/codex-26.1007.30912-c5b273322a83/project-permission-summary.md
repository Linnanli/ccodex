# 项目权限与状态计算的有限静态补充

固定基线：`codex-26.1007.30912-c5b273322a83`。只沿已确认的 `Pt.Me ← app-initial.gkn` 查一个完整候选函数，保留函数体局部 `L ← Re` 的数据流。没有修改旧冻结产物/脚本，没有操作 UI、账户、凭据或历史，没有执行目标代码、项目 mutation、HTTP/IPC 或模型调用。

**新增结论是计算条件，确认可排除功能/模块数仍为 0，运行验证链数为 0。** 原始 initial 全模块定义的词法身份、完整消费者、状态和权限值的来源、实际模式与缓存运行条件仍未知。

保存的 source-qualified 导出索引 `/files/2/exports/0/bindings/6499` 明确 `ymn as gkn`；它不是其他模块的同名导出。新解析的完整候选函数为 initial UTF-8 半开范围 `[1978766,1978813)`，**47 字节**，只有参数 `e/t`、一个 return，没有 helper 或调用。源码计算为第二个参数严格等于 `allowed`，且第一个参数严格等于布尔 `true`。它不直接读取产品模式、flag 或环境变量，也没有网络/IPC 调用。函数片段能建立自身参数绑定；没有据此推断全 initial 外层定义或后续赋值身份。

保存的完整设置模块 AST 确认 `Me(Fe,a)` 绑定 Program import `Me ← initial.gkn`；`Fe` 是 Pt-body 局部 `project.gizmo.current_user_permission?.can_write`，`a` 来自 `projectCrudStatus` prop。另新解析 Pt 的完整 ConditionalExpression `[31818,31888)`，**70 字节**，只包含 1 个 `Me` 调用和 5 个赋值；同一调用与保存的 `CGP-E01504` 原始范围完全一致。

| 分支 | 原始源码的数据流 |
| --- | --- |
| `n[11] !== a` 或 `n[12] !== Fe` | 局部 `Re = Me(Fe,a)`；随后保存 `n[11]=a`、`n[12]=Fe`、`n[13]=Re` |
| 缓存输入相等 | 同一个局部 `Re = n[13]` |
| 随后声明 | `L = Re`，其中 Re 为 body scope-88 的 binding-448 |

在重算分支，该候选函数检查 `can_write === true` 且 `projectCrudStatus === allowed`。缓存分支只确认读 `n[13]`；没有验证 `n` 的初始化与所有写入、缓存不变量或实际运行值，因此不将 `L` 声称为运行时无条件恒等于该布尔公式。局部 `Re` 遮蔽 Program import `Re ← initial.rOn`，本轮没有接到那个同名 import。

保存的 `localFolders` property 还要求 `s && L && je(project)`；另一个 `fkn/Emn` 数据资格 predicate 和 `s` 条件不能由本轮权限计算代替。`projectCrudStatus` 的上游生成、权限响应来源、挂载、模式与其他 guard 不在本轮范围；字段名、状态常量或模块名称不能推出 ChatGPT 独占或整模块可删。

`project-permission.json` 包含 8 个原始 input/sourceArtifact metadata pins、2 份固定 sourceInputs/sourceFiles，以及两份自有 replay/validator 的 script pins。复用证据保留原 ID 和源身份/范围，origin 指向已 pin 的原 journal 精确字节；JSONL pointer `/N` 使用原始有序记录数组的零基索引。每条证据有标准 claim、sourcePath/sourceHash、locator、spanSha256、method、confidence=`high`，并明确 confidence 只适用于坐标身份。目标 JS 只作为本地冻结输入引用，不作为恢复后的客户端实现输出。

新 AST 总分母为 **117 字节**：1 个完整候选函数、0 个 helper、0 个函数内调用，加 1 个完整消费者表达式、1 个消费者调用、5 个赋值；不是整个 initial、整个 Pt 或所有 gkn 消费者分母。语义 review 是人工审查，源身份、范围和引用由独立 validator 核对。没有声称所有历史输入链或旧 journal 的未引用行都通过。

重放命令（冻结后应在可写副本中运行）：

```sh
/Users/nallylin/.nvm/versions/node/v22.23.2/bin/node scripts/analysis/project_permission_review.mjs
python3 scripts/analysis/verify_project_permission.py
```

独立结果保存在 `validation.json`，冻结产物与脚本身份保存在 `frozen-manifest.json`。
独立核验最终结果：`passed=true`、`errors=[]`，主结果与 journal 的显式 expected SHA256 均匹配。核对了 24 条标准源码 span（11 fresh、13 reused），8 个 input pins、8 个 sourceArtifact pins、2 个 sourceFiles、2 个 sourceInputs、2 个 scripts，以及 29 处 sourceArtifact 引用、38 处 evidence 引用（23 个唯一引用 ID）。候选上游函数 target 为 1；每类检查的失败数均为 0。这是本轮声明的输入、坐标与引用核验，不增加原始模块绑定、缓存或运行时结论。

Journal 保留 producer 原始 `confidence=high` 和 `confidenceScope=coordinate-identity-only`；若全局发布索引将 label 显式映射为 `confirmed`，其确认范围仍仅为原始源坐标身份，不提升 unknown 的词法绑定或运行时推断。
