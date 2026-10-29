# appServerVersion 来源静态调查

基线为 `codex-26.1007.30912-c5b273322a83`。结论是 **来源链已静态确认，实际桌面实例的版本值仍为 unknown**。新增证据只覆盖已选中的具体 `mB` 连接类及其词法依赖；同名属性不能证明运行时是同一个实例，也没有启动客户端、CLI、后台服务、UI 或模型，没有联网。

`mB.appServerVersion` 的完整 getter 返回 `this.initializedAppServerVersion`。`routeIncomingMessage` 在尚未初始化、消息有 response 形状、ID 精确等于 `__codex_initialize__` 且有 pending resolver 时，处理初始化响应：有 truthy error 则拒绝；否则 `t=e.result`，读取 **`t.userAgent`**，调用 `o.sn(t.userAgent)`。符合本地/远程兼容条件时，解析结果 `r` 赋给 `initializedAppServerVersion`，再调用初始化 resolver。此明确赋值路径没有读取 `serverInfo.version` 或 CLI package version。

导入链为 src 的 module-level `const o=require("./application-network-startup-CfAQmSYg.js")` → 该模块 `exports.sn` getter → **top-level local `D`** → `T.exec(input)?.groups?.version ?? null`。`T` 为 `/^.+?\/(?<version>\S+)/`：它从 slash 格式的 userAgent 中提取非空白 token，本身不验证 semver。同一模块还存在名叫 `sn` 的本地 binary digest helper；它不是 exported `sn` 的真实绑定。完整导出 getter、`D`、正则所在完整 declaration 和 exact call 的 enclosing scopes 均已保存；调用处参数、直接 block/catch bindings 未遮蔽导入 `o`。

已有预测调查已覆盖 factory、registry 与 caller，无需重跑：main factory `new i.pn` → src `exports.pn` → local `mB`；`mge.connections.getConnection(hostId)` 的候选连接经 `runPrediction` 传给 `fge` 的 `e` 参数。`fge` 使用 `r.Ti(e.appServerVersion,"experimentalPredictionForkMode")`，而 prior gate 链为 main `r` → `src-CP7XXlpZ.js` exported `Ti` → local `I`。本轮只重新核对旧引用的精确源 span，没有重复解析 gate 模块或 main bundle。运行时 host lookup、registry mutation、真实 instance 和实际 feature 启用仍未知。

旧 gate 的完整源码表明：`I` 对 null/invalid semver 返回 false；通常门槛为 `0.162.0-alpha.20`，保留 `0.162.0-alpha.17.2` 明确例外；`0.0.0` 的 sentinel 分支对该预测 feature 返回 true。先前对冻结包版本字串与公开 `0.162.0` 的推导继续只是字符串输入的静态结果，不能当作本次 getter 值，更不能消除 `experimentalPredictionMode` 的 schema/后端差异。

`installedCodexVersion` 是另一条路径：`connectAndWaitForOpen` 在 transport open 后另行调用可选的 `options.transport.getInstalledCodexVersion()`，赋给该独立字段；`publishRestartAvailableErrorMessage` 也能更新 installed 字段。完整 `mB` 类内可见 5 条直接命名的 version-state assignment：2 条 reset、2 条 installed 赋值、1 条初始化响应赋值。没有把 installed 字段反推为 initialized 字段；动态 transport probe 和外部/computed mutation 未验证。

`initializedAppServerVersion` 初始为 null，`clearInitializedHost` 把它与 installed 字段一起重置。完整类内直接 reset caller 为 `connectAndWaitForOpen`、`stopProcess`、`handleTransportClosed`；这些成员均保留完整范围。`completeInitialization` 与 `sendInitializationSnapshot` 经 `getInitializationMessage` → `LL` 生成 `codex-app-server-initialized` 对象，分别携带 appServerVersion 和 installedCodexVersion。只是通知生成的静态路径，未观察实际发送、顺序、接收或值。

缺失和异常输入也按源码边界登记，没有执行这些分支：

- `result` 存在而普通 missing/null/nonmatching userAgent 经内建正则 string coercion 不匹配时，`D` 返回 null；remote unsupported 条件要求 `r!=null`，因此此源分支可以写入 null 并 resolve。后续预测 gate 拒绝 null。
- `D` 和该 route member 没有本地 `typeof userAgent === "string"` 检查；非字符串结果取决于具体 coercion/accessor，不能概括为全部返回 null 或优雅失败。
- 匹配 response 的 `result` missing/null 时，`t.userAgent` 没有本地 optional guard/try/catch，可以在赋值前抛出；但 `nL` 要求有 ID 且存在 `result` 或 `error` property，因此真正 missing result 还须存在非 truthy 的 error property 才走到此读取分支。两 property 均无的消息不会被该分支选中，truthy error 则走拒绝分支。上层 incoming-line/transport 的传播结果仍未知。
- userAgent 的 slash token 提取成功也可能得到非法 semver；语义验证属于后续 gate。匹配 ID/resolver 未出现或已 initialized 时，不走这一初始化赋值分支。实际事件顺序未观察。

保存的冻结和公开 npm stable/experimental `InitializeResponse.json` 均声明 required string `userAgent`，无 `serverInfo` property；4 份 schema hash 均为 `62ad689c2cb6379913c1d72749cfd8de5089d35760214123518eb92eef11acc9`，各自回到原 generation manifest 的精确 pin。这是契约辅助证据，不是运行输入一定符合 schema 的证明。

只读复核既有两后端 headless `observations.jsonl`：冻结 `cd43ac25437d92608b87c3d1970466a463314af78b87518ef651257dac515b44`、公开 npm `c4d19bf0490594967fcaa4aca05a9200ca89638178f1274321773be2e2985946`。各自 initialize request/response 的 ID 都匹配，第二行只保存 `returnedKeys`，其中包含 `userAgent`；**实际 userAgent 值未保存**。本轮不能解析出那些 session 的版本；即使已存 headless 值存在，也不能证明 owned desktop 连接 getter 的值。

范围与核验：新解析一个 290,566-byte 小模块、一个旧证据已定位的完整 `mB` variable declarator，以及 src 的有界完整 import/helper declarations；没有重跑全应用 AST。产物包含 40 条新源证据，复核 20 条旧预测证据与 8 条旧 gate 证据（合计 28）；完整已选 mB binding 的 class body 共 238 个成员，其中保存 14 个完整成员。全 module 解析分母仅 1 个 `application-network-startup-CfAQmSYg.js`、290,566 bytes、339 个 Program statement 和 291 个顶层 FunctionDeclaration；这些是固定 AST 范围计数，不是行为覆盖率。独立 Python 脚本核对 source/input hashes、UTF-16→UTF-8 定位、完整 member 文本、旧 journal 原行、schema pins 与保存 response metadata，**857 checks、0 errors**。输入与旧 artifacts 的哈希保持一致；这不是产品行为测试。

初版观察器错误地假设 exports 注册都是独立 ExpressionStatement，实际为逗号串；exit 1 的源脚本、stdout/stderr 和 hashes 完整保留于 `attempts/v1`。后续改为 AST CallExpression 选择。并行代理因 thread limit 未能启动，作为工具诊断保留，不登记为产品阻断。已有 HTTP request-facade 是另一种请求边界，没有拿它来解释这一 app-server initialize response。

GAP-04 可更新为“具体连接类的版本来源与预测使用链已静态确认；实际运行 host/instance、initialize userAgent 值、getter 值、通知顺序、服务端实验能力继续 unknown”。本静态批次没有提交任何目标模型任务；行为授权与当前目标运行状态由主线程单独记录，不作为本批静态证据。

复现与主要产物：`node .analysis-local/app-server-version-origin-work/trace-version-origin.cjs`；`python3 .analysis-local/app-server-version-origin-work/validate-version-origin.py`。详见 [version-origin.json](version-origin.json)、[evidence.jsonl](evidence.jsonl)、[selected-member-text.json](selected-member-text.json) 和 [validation.json](validation.json)。只在本工作目录写入，无旧 frozen/root/public 脚本修改。

发布适配元数据：全部 inputs 已分 kind，2 份 Babel parser runtime 独立列于 toolRuntime，4 份固定目标源码独立列于 sourceInputs 并标记 sourcePath/local-only；其他输入为既有分析产物。独立 verifier 为最终 version-origin/evidence/summary 写出 exact path、bytes、SHA256 的 finalProducts。新 journal 原字节不变；主线程仅对 APP-SERVER-VERSION-ORIGIN-* 进行明确 confirmed-source-locator method/confidence 适配。
