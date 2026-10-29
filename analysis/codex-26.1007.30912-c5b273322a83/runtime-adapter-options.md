# 定制运行时处理方案（分析阶段）

基线：`codex-26.1007.30912-c5b273322a83`。仅从已冻结 runtime API 清单、公开 native/private 依赖记录和局部模块建议推导；未重新扫描目标，未运行客户端、UI 或模型，未读取认证或个人历史。来源哈希、JSON pointer/CSV record locator 和 evidenceId 见结构化文件。

当前建议先调查是否能独立取得并固定 Owl 分发、开发接口和构建工具，同时明确自有能力/传输接口。取得性仍为 unknown。若不能形成独立可固定的依赖记录，优先调查普通 Electron 加第一方 adapter 的功能子集技术可行性；其他 shell 保留为重写方案。这是分析阶段调查顺序，三条路线均未证明替代成功。

**完整 Codex 功能目标保持。** 功能子集只用于技术可行性和中间验证；未覆盖契约、临时 unsupported/回退和未测试能力必须留在后续全量验收矩阵，不能以缩小功能交付关闭分析缺口。

| 路线 | 必要条件 | 当前边界 |
| --- | --- | --- |
| 独立固定 Owl | 分发/源码与开发接口可独立取得，版本与真实交付物哈希可固定；明确 Node/Electron/ABI、原生构建与升级能力 | 包内 `runtimeName=owl`、`runtimeArchiveSha` 仅证明元数据身份；复制现有 app 不证明取得性、可重建或升级渠道 |
| 普通 Electron + 自有 adapter | 固定真实选定版本；先通过中间功能片段验证能力接口、私有包/原生依赖、同步 preload 与 IPC 契约，随后扩展全量验收 | 公开 API 文档匹配仅提供候选；片段验证不关闭完整 Codex 的剩余功能和契约缺口 |
| 其他 shell 重写 | 重新实现 host/preload、世界隔离、窗口/会话/浏览器所有权、权限及传输；显式迁移同步调用 | 当前没有选定 shell、成本或兼容性结论；不能把原 Electron/Owl bundle 直接视作可移植实现 |

四个必须单独决策的边界：

1. **Task manager 门槛**：原 bootstrap 在 Electron 版本字段非空且 `app.showTaskManager` 不是函数时抛错。能力应有真实实现或明确的功能回退；删 guard 或放占位函数不实现兼容。
2. **Native linked binding**：`electron_browser_owl_update_policies` 的发现失败会返回 null，但这只证明局部发现函数可选。必须追保留功能的 null 消费分支与事件/重启策略，不能据此省略整个更新功能。
3. **WebContents adoption lease**：已有完整 shape/routine 要求 owner、非空 lease、pending 和 destroyed 清理；注入受体与消费者仍未完全绑定。普通 view API 或任意非空字符串不能证明原生所有权转移等价。
4. **Node permissions / IPC scope**：限制分支涉及 denied general net、允许的动态本地 IPC 路径、relaunch 参数/环境、open-event 队列及平台差异。替代必须验证正向 IPC 与网络/越界 IPC 的负向用例；删除 flag 或放宽权限改变契约。

四项优先边界不构成全部私有 API 清单。保留功能中的 Session permission prompt、native menu tracking、runtime features、measurement、history swipe 和自定义 UA switch 仍需逐项明确实现或回退；进程网络/IPC 权限和会话 permission prompt 是不同契约。

所有路线还需保留 app-server、app-host RPC、协调 socket 的身份边界，定义 clone/chunk ACK、MessagePort 所有权、同步初始化、销毁清理与平台条件的 fixtures。原生文件识别和私有 workspace/file/link 声明不能证明独立依赖可取得、可重新构建或 ABI 兼容；已记录缺失的 Owl types/preparation/rebuild、monorepo types 和根构建/lock 输入必须由独立项目补齐。

拟调查顺序：独立 Owl 取得与版本来源 → 四个特殊边界及保留调用者 → 中间最小功能/依赖矩阵 → 契约 fixture 定义 → 自有隔离 adapter 集成 → 干净构建、版本升级比较和完整 Codex 功能验收。每一步的来源、动作和退出条件在 JSON 中；本轮没有执行这些未来门槛。

范围沿用原 runtime 清单：10 核心文件、90,246 call/new 表达式、1,242 Electron 派生调用和 229 条路径；4,293 名称候选、34 预算触顶表达式保留未知。局部 11 条模块建议不覆盖全项目。当前公开参考未找到特定 Owl 名称只是一组已查文档的缺席记录，不是所有版本不存在该实现的证明。

引用验证：9 个输入哈希前后不变，177 次引用（JSON pointer 与 CSV record locator），151 个唯一证据 ID，0 errors。该验证只确认记录/引用一致性，不新增运行或替代成功证据。
