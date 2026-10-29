# 首页分流、共享 composer 与模式剥离边界

固定基线 `codex-26.1007.30912-c5b273322a83`。已将首页注册、Codex 专用入口、Chat／Work 共享入口和本地／远端 composer 的源码连接收束为四项恢复决定。选择了14个原始单位共65,682字节；27个隔离场景通过。客户端实现尚未开始。

`/ → dFs → OJa → HomeComposerRoute → primary.t → wzt` 是已确认的静态注册／构造链。`wzt` 分别选择 Codex 专用 `Tzt` 和共享 `Ezt`；两者都会向 `M9` 传入参数，后者继续调用 `jRt/NRt`。**首页主 composer 必须作为共享第一方模块保留，不能按 ChatGPT 文件名整块删除。** 初始化与真实页面挂载仍未观察。

模式和执行位置分别决定行为。`wzt` 可以依据路径、项目、草稿、共享快照、sketch、临时聊天参数和能力条件覆盖 chat/work。`cPt` 是切换可用性谓词。它们与权限 access family、agent 的 plan/default 模式和会话 kind 分开维护。

| 源码条件 | 已确认的 composer 路径 | 恢复处理 |
| --- | --- | --- |
| Codex 专用 Tzt | M9 → jRt → NRt；普通路径选择 $X → rpt | 保留共享渲染及现有本地任务链 |
| Work + local execution | `er=true`，选择 $X → rpt | 保留项目、host、权限与首 turn 身份 |
| Chat，或普通 Work-cloud | 满足 Qt 且非 er、非 ht 时，选择 CIt | 保留远端共享候选；继续核实消费者与服务契约 |
| 特定 Work-cloud 条件 ht | 可改选 $X → rpt | 保留特殊目的地规则，不能按 work 字面量统一后端 |
| 控制器缺失或模式未定 | 有独立占位／加载处理 | 不自动发送任务或默认为其他服务 |

恢复目录按职责提出：`features/home` 负责入口和 surface policy，`features/composer` 负责共享渲染及远端适配，`features/tasks` 负责本地提交，`packages/contracts` 记录目的地与状态。它们是维护建议，不是原作者目录或已生成的客户端源码。

临时 Chat footer、chat 专用 inline system hints、custom Chat assistant／temporary-chat 入口可以在入口和明确条件分支处隔离。**这些事实没有证明整个 CFt、CIt、项目设置或 chatgpt 命名模块可删除。** 原237项功能的 mode 字段、完整功能分母、808条产品场景及现有第三方依赖决定均保留。

27个场景执行完整 wzt/cPt，以及 NRt 中保存的目的地谓词和选定 render callback；依赖和闭包自由变量使用合成值。它们验证所选源码的控制与渲染分流，不证明完整 React 挂载、真实客户端、后台执行、IPC、原生能力或重启持久化。首次尝试的6个合成环境错误及21个通过结果原样保留，修正 fixture 后27项通过；原源码未改动。

实际产品验收仍须覆盖 Codex 首页、本地任务、需要保留的 Work 目的地、输入接管、取消、首 turn、通知及重启恢复。ChatGPT 专属分支剥离和所有第三方包引入在实施时按这些边界执行。详细事实、来源范围、恢复路径、验收与升级检查见[结构化结果](product-flow-ownership.json)；原始小单位和观察见[证据目录](raw/product-flow-ownership/selected-units/contracts.json)。未新增模型任务或原客户端运行。
