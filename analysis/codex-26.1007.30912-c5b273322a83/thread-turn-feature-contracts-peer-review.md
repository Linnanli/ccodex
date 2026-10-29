固定基线 `codex-26.1007.30912-c5b273322a83` 的独立复核结果为 **passed-with-scope-limits**：自有离线 checker 完成 1,575 项检查，0 个错误；9 个最终产品的 SHA-256 与字节数已逐一固定于 `independent-review.json`，完整执行源、全部检查记录及 stdout/stderr/exit 已保存。

复核了 98 个 input pins、58 条新 journal 记录、172 条精确旧记录、82 个不同 JSON pointers 与 28 个不同原 byte ranges。7 methods、19 calls、8 完整函数/成员、9 分支的分母一致；4 个静态 RWC-MANAGER 绑定与 15 个未解决 receiver 保留。旧 FEATURE/ledger 字面范围严格包含于 AST call 范围，未将两种 locator 当成相同范围；2 个直接字面入口仍单列。

初轮发现及原记录已保留，并映射到最终 main 的精确 pin：

- `TTC-V-07` 明确 stable 也声明 `toolOutput`，`additionalContext` / `responsesapiClientMetadata` 才是该 payload 的 experimental-only 字段。
- `TTC-V-03` 的 created 返回以未捕获的 RPC 后工作成功为前提；`s(y)`、`San` 与尾部 `g` 的 catch 外异常现已列明。
- `TTC-V-05` 仅在先前状态不是 active 时设 active；outcome-unknown 保留提交记录仍可能将本地 turn 标为 failed。

stable/experimental 参数、返回字段、required/type/pointers、generation manifest 与 ClientRequest 联合声明分别核对。public repo/tag/commit 只标识保存的比较候选；实际 receiver、mode、通知次序、普通 UI→操作、持久化和业务运行均未证实。protocol-source-review 元数据由本复核者先前编写，本轮检查其原 schema 与 main 引用，不声称该文件有第二位独立作者。

复核者未执行主 producer/verifier/freeze/verify-freeze，也未执行目标/bundled Codex CLI、UI、网络或模型任务；自有离线 Python 元数据分析与 checker 确实执行，并保留原 source/output/exit。主 scope 的 CLI 排除范围指目标 CLI，不能理解为没有任何 shell/Python 命令。

protocol review attempt-01/02 都为 exit 0；attempt-01 仅保留历史源 pin，旧成功源内容未保存，不能据当前源复现。主 producer 失败 01/02 与 verifier 失败 02 保存原 source/stdout/stderr/exit。exploration 失败仅有精确源和 stderr 尾；provider 截断导致完整 stdout 未保存，记录明确 `stdoutFullCaptured=false`，未重放补齐。

freeze 脚本仅作源复核；本报告不声称已冻结。POSIX 只读模式也不是未来不可变性保证。本次可支持限定范围的静态操作契约目录，不构成运行、兼容、持久化或完整客户端验收，不关闭原 36 个泛化组和完整客户端目标。
