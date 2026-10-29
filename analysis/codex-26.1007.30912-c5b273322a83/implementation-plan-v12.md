# Codex 独立客户端工程方案 v12

本方案把当前功能、职责、依赖、构建输入和运行时路线汇总到一个工程入口，替代 v11 正文中已过时的规模数字。目标仍为完整保留 Codex 客户端能力，按证据排除 ChatGPT 产品分支，维护源码不生成第三方实现副本。本次交付是分析与工程设计，尚未开始客户端实现或证明独立构建。

基线：`codex-26.1007.30912-c5b273322a83`。原始[分析计划](../../docs/reverse-engineering/analysis-plan.md)及其九项完成标准保持不变。v11 和历次来源合同作为不可变历史证据保存。

## 当前依据与适用范围

| 项目 | 当前数值与含义 |
| --- | --- |
| 有限功能定义 | 509；并非证明发现了全部产品功能 |
| 用户操作 | 582 个不同 ID、583 次功能归属出现 |
| 支撑操作 | 125 |
| 产品场景规格 | 1844 条不同规格、1847 次功能关联；3 条跨功能共享，全部未执行 |
| 业务任务 | 51；另有 W01—W09 九项基础任务 |
| 限定职责 | 115；解析到 120 个不同拟议路径，保留十项模块字段 |
| 粗工作流 facade | 48；不能当成已恢复源码模块 |
| 来源 witness | 2874，涉及 156 个冻结文件；34 条共享处置 |
| 模式 | 504 unknown、5 shared；unknown 保留，整项功能排除为 0 |
| 第三方/内部依赖记录 | 202 条记录，未等同于 202 个不同 npm 包 |
| 构建输入 | 30 次出现、21 个路径、12 项补齐义务 |
| 运行时/存储 | 15 组运行时能力；11 个存储域；基础选定边界 16、功能链接 17 |
| 源码入口待办 | 968 个身份中 706 未关联功能；其中 181 已明确为机制，525 待目标或机制判定；另有 20 个命令消费者缺口 |
| 实施与验证 | 客户端实现 0；合格完整运行时路线 0；未证明独立构建 |

机器合同为 [implementation-milestones-v12.json](implementation-milestones-v12.json)：`featureWorkItems` 按 ID 联接当前范围、覆盖、职责和模式覆盖表；`logicalModuleWorkItems` 保存 115 项职责的十字段原值和引用；`dependencyWorkItems` 保留原始行并区分新工程锁。模式覆盖只改变新视图的 `effectiveMode`，不改写历史行。

逐项目录见[职责与拟议路径](implementation-plan-v12-module-paths.csv)，逐项依赖见[依赖处置](implementation-plan-v12-dependencies.csv)。每个拟议路径是维护设计；源码范围、原始模块边界和实际运行实例的证据强度仍按各合同的限定解释。

## 工程目录与职责

```text
apps/desktop/
  src/main/
    early-bootstrap.ts       早期启动、开关与延迟加载门槛
    bootstrap.ts             门槛通过后的装配
    index.ts                 主应用生命周期与服务装配
    persistence/             global-state 等第一方存储职责
    settings/                desktop-settings-store 等职责
    projects/                项目与线程归属
    lifecycle/               退出与释放协调
    worker/ 或 workers/      沿用各项已提议路径，待入口清单核对
  src/preload/
    app.ts                   应用窗口桥接
    app-host-bridge.ts        复用已提出的宿主桥接职责
    mcp-sandbox.ts            MCP guest 端口初始化
  src/browser-preload/
    index.ts                 浏览器页面入口
    annotation/              复用已有页面标注职责
  src/renderer/
    app/                     壳、路由、模式和窗口状态
    features/                509 项功能对应的 51 个业务任务
packages/
  contracts/                 新工程 DTO、通知、错误与能力合同
  app-server-client/         请求调度及协议客户端
  app-host-client/           宿主服务客户端
  desktop-transport/         按服务区分的消息、端口与编解码
  desktop-http-client/       HTTP 客户端职责
  automation-domain/        自动化领域职责
  projects/                 项目领域职责
  runtime-adapter/           15 组能力与独立 provider 边界
  backend-adapter/           后台、认证与配置适配
  storage-contracts/         存储根、schema 与权威边界
tools/recovery/              基线差分与来源映射
tools/build/                 构建输入、资源及打包配方
tests/fixtures/              合成数据与后续回归输入
```

路径以机器合同和 CSV 为逐项依据。此树只展示已选维护边界，不声称每个目录已有源码，也不自动将一个 bundle 或一个控制器拆为一个包。职责允许共享 witness；相同范围被多项引用不能复制成多份实现。

## 编译、入口和打包

采用 pnpm workspace、TypeScript、按进程编译的设计。Vite/Forge 承担前端构建和应用打包是已有来源导出的候选；工具的精确版本、目标运行时、配置和新锁尚待选择与验证。新工程的精确锁、完整性和构建配方独立于原发布版本证据。

| 入口 | 拟议输出 | 约束 |
| --- | --- | --- |
| `src/main/early-bootstrap.ts` | `dist/early-bootstrap.js`；拟议 `package.main` | 门槛前只加载必要早期依赖；不得把后续 bootstrap/main 的副作用导入提升到权限初始化前 |
| `src/main/bootstrap.ts`、`src/main/index.ts` | 独立主进程阶段/产物，文件名由新配方固定 | 保留延迟装配、资源相对位置和退出错误归因 |
| `src/preload/app.ts` | `dist/preload.js` | 单个 CommonJS 兼容 bundle，应用桥接 |
| `src/browser-preload/index.ts` | `dist/browser-page-preload.js` | 单个 CommonJS 兼容 bundle，页面与 main-world 合同 |
| `src/preload/mcp-sandbox.ts` | `dist/sandbox-preload.js` | 单个 CommonJS 兼容 bundle，guest 端口合同 |
| renderer | `dist/renderer/` | 按功能/共享包生成可维护源码，再由工具分块；不保留巨大反编译文件作为维护单元 |
| worker、helper、native、资源 | 逐项入口/目标平台资源 | 清单仍待完整核对；不得用通用 worker 占位宣称全覆盖 |

新核对的 `early-bootstrap.js` 完整 AST 中，函数 `d` 先等待早期准备，再加载 `initializeNodeNetworkPermissions`；其结果为真后才延迟 require bootstrap。这是静态顺序证据。Electron 本身已在顶层 require，不能把结论扩成“权限初始化前没有任何导入”。构建须验证后续阶段没有因打包提升而提前执行；实际权限效果尚未观察。

三个 preload 复用[入口与构建合同](preload-build-boundaries-v1.md)。`electron` 由运行时提供，保持 external；受控 sandbox require 不能任意加载 npm 包，因此可达纯 JS 包从新锁安装并打进各入口。第三方实现出现在构建产物不等于在维护源码中生成 vendor 副本。主进程与 worker 的 external 处置按运行环境逐项决定，不把 preload 规则泛化为所有进程规则。

应用桥接的 22 项属性、4 次启动同步读取，浏览器页面的 3 次 `executeInMainWorld`，MCP 的 12 个必需/7 个可选端口分别保留。Sentry session 注入有独立路径，不能混为应用窗口的 preload 加载。`window.open` 的完整中间对象流、应用窗口未显式给出的 sandbox 默认、实际主世界执行和端口交付保留为具名缺口。

## 第三方依赖与新工程锁

202 条记录逐项保留来源、定位、原版本证据、未决项和行动。公开包通过依赖引入；第一方封装、领域逻辑、平台策略恢复为独立源码。修改过的包保留修改比较、补丁维护、版本来源与目标 ABI 验证任务，不能仅凭包名直接换成最新版。

冻结根声明中的 Electron 为 `42.3.0`，node-pty 为 `^1.1.0`，冻结已安装 node-pty manifest 另有 `1.1.0` 证据。新视图按精确历史行引用附上这两项资格，不覆盖原始空版本行，不把声明范围当精确锁，也不据此判定定制 Owl 二进制等于公开 Electron。React/ReactDOM 的 `19.2.7` 自报信息同样不足以确定完整上游发行物、修改状态或新锁。

机器合同每条依赖的 `baselineRecord` 与 `newProjectSelection` 分开；后者的版本、完整性目前为空，`locked=false`。七段运行时内嵌 JS 中的 23 个包名提示单列为线索，不加入 202 的记录分母。许可证与上游完整性需要按实际选定发行物核对。

30 条构建输入和 12 项义务沿用已有补齐决定。对 bundler-config 类历史广义 external 建议，preload 范围以本方案和 PBB-B01/B02 的入口打包规则为准；原始输入行仍完整保留。node-pty、objc-js 的修改合同与 Sparkle 的二进制分发边界各自保留；本机 Node22 的一次有限加载不证明目标运行时或 ARM 平台 ABI。

## 运行时与后台路线

第一方能力合同与独立取得的运行时/provider 分离。现有三条路线都没有完整资格：Owl 缺独立来源、SDK/headers 与构建输入；固定公开 Electron 42.3.0 不能直接替代全部定制能力；自有 bridge/运行时扩展/等价服务是逐组实施候选，尚未实现。七段内嵌 JS 的边界和包名不构成 C++ 源码、SDK 或 ABI。

| 能力组 | 独立 provider 候选 | 所需材料/合同 |
| --- | --- | --- |
| RAM-01 | 平台菜单 bridge 或运行时扩展 | 菜单 tracking 源码/接口、窗口生命周期绑定、目标平台 SDK 和所选 runtime headers。 |
| RAM-02 | 具名 histogram 采集 bridge | Owl histogram 桥或独立等效实现；具名计数生产者版本、增量/累计/重置和多读取方语义。 |
| RAM-03 | 运行时特性 registry 与平台策略实现 | 两个 allowlist 键的引擎实现/默认值/reset、feature registry、Windows policy 清理实现。 |
| RAM-04 | 可信诊断页策略 provider | 特权页面及服务实现、允许/拒绝范围、build flavor 和 profile/guest 策略连接。 |
| RAM-05 | 诊断 UI 与真实进程数据 provider | 原生 Task Manager 的实际字段/动作/刷新/关闭行为资料，或经对照的独立 UI 与数据实现。 |
| RAM-06 | 窗口能力探测与 input-shape 实现 | 平台能力条件、setInputShape/hit testing 源码或独立实现、DPI/坐标及窗口生命周期接口。 |
| RAM-07 | macOS 手势/窗口 bridge | 原生滑动手势、overlayBounds/Color 及导航状态同步实现，所选 runtime headers/SDK。 |
| RAM-08 | OS 通知授权 bridge | 状态查询/授权请求/系统设置打开实现、应用标识与打包条件、平台 SDK。 |
| RAM-09 | 屏幕/光标能力 provider | 支持条件、坐标/权限能力探测和 controller 生命周期接口；目标平台实现及 SDK。 |
| RAM-10 | 权限 prompt 协议与浏览器权限状态服务 | prompt 参数、响应/取消/过期和所有权生命周期；独立 partition 与浏览器权限服务实现。 |
| RAM-11 | OS 字体目录 bridge | 能提供 family/faces、PostScript/full/style name、isMonospaced 的枚举实现与平台 SDK。 |
| RAM-12 | live clone/adoption 引擎或等价所有权协议 | clone/adoption 源码或独立实现、lease 消费/失效/拒绝、live 页面历史/表单/堆状态的准确契约。 |
| RAM-13 | 受限网络与 scoped IPC 的执行机制 | 运行时补丁或独立进程/OS enforcement 源码、端点策略、重启参数和允许/拒绝用例。 |
| RAM-14 | 平台 updater 与独立 managed-policy provider | 固定版本更新依赖/源码配方、bridge 和策略事件/注销；自有签名/feed/应用安装布局。 |
| RAM-15 | 特权 WebUI/backing services 或等价独立服务 | contactInfo/passwordManager/extensions/siteSettings 的底层数据/服务和独立构建来源。 |

每组的具体前提、第一方职责、最近公共原语的能力损失与验收逐项保存在 `runtimeCapabilityWorkItems`。这些外部输入只阻断对应集成验收，不阻断已具备来源合同的目录、接口、依赖和构建配方设计。

四个构建关口保持：BG-01 类型与能力合同；BG-02 独立取得、来源与启动；BG-03 目标 headers、架构与 ABI；BG-04 独立打包、安装和升级。不从原客户端安装路径取运行时作为“独立项目已完成”的证据。

app-server、app-host、HTTP、resolver/socket 和原生能力保持不同服务身份。复用[协议差异采用合同](protocol-delta-adoption-v1.json)：466/455 的既有对照中 11 项不同；涉及模型/reasoningEffort 的可选/可空通知字段须保留，prediction fork 要匹配真实后台，不能用普通 fork 冒充。静态重放只验证适配层，不证明真实 receiver 或后效。

## 状态与模式

11 个存储域复用既有所有者；基础 16 个选定边界/17 个功能链接，加上认证、插件、inbox、tab 等后续合同，在机器入口集中索引。保留根路径注入、schema/defaults、revision、并发、原子替换、flush、退出、备份和迁移。内存写成功或历史 SIGTERM 不能证明落盘完成；完整逐功能持久化权威仍有缺口。

504 个 unknown 功能全部保留。5 个 shared 使用当前覆盖表，不把旧基础账本的 507 unknown/2 shared 再当有效模式。历史三个 ChatGPT 分支组有分支级边界，不形成整项功能排除。认证中的 `identity.kind=chatgpt`、访问家族或页面名均不单独证明 ChatGPT 产品模式；删除须核对具体谓词、保留消费者与共享依赖。

## 顺序与验收

源码准备和真实集成使用两张不同图，原 60 个节点及边保持。W01/W02 可先完成来源合同与构建输入设计；需要原生/provider 的集成关口仍留在集成图中。不得把所有静态任务排在真实原生验收之后形成循环。

| 任务 | 当前交付边界 | 准备依赖 / 集成依赖 |
| --- | --- | --- |
| W01 合同与来源映射 | 509 项功能与 115 条限定职责、48 个粗 facade 的来源映射；2874 witness、34 条共享处置及十项模块字段 | 无 / 无 |
| W02 独立构建与依赖输入 | pnpm workspace、工具版本资格与新精确锁任务；分进程编译、早期门槛、三个 preload 及 202 依赖/30 输入的构建配方 | 无 / 无 |
| W03 运行时与平台能力 | 15 组独立能力合同、来源与生命周期；BG-01 至 BG-04 的 provider/headers/ABI/平台前提；完整路线仍为 0 | W01,W02 / W01,W02 |
| W04 桌面传输与宿主 | 三个 preload 入口及按服务区分的消息/端口传输；身份、信任、订阅、取消、断连和资源释放合同 | W01 / W01,W03 |
| W05 后台适配 | 两个协议差异族的采用与字段保留；prediction fork 和其他服务的独立能力与不支持合同 | W01,W02 / W01,W02 |
| W06 状态与持久化 | 11 个存储域、16 个基础选定边界及认证/插件/inbox 等补充；根路径、权威、revision、flush、退出、备份和迁移职责 | W01 / W01,W03 |
| W07 应用壳与模式 | 壳、路由、窗口、504 unknown/5 shared 的保留与条件；认证身份、产品模式与访问家族分别核对 | W01,W04,W06 / W04,W06 |
| W08 其余功能与完整范围 | 509 项有限功能与 51 个业务任务的消费者和状态对应；582 不同操作、125 支撑及 1844 未执行场景的实现验收对应 | W04,W05,W06,W07 / W04,W05,W06,W07 |
| W09 剥离升级与最终验收 | M1—M7 全范围验收与分支剥离；第三方审计、新基线差分、模块回归和数据迁移回退 | W08,T01,T02,T03,T04,T05,T06,T07,T08,T09,T10,T11,T12,T13,T14,T15,T16,T17,T18,T19,T20,T21,T22,T23,T24,T25,T26,T27,T28,T29,T30,T31,T32,T33,T34,T35,T36,T37,T38,T39,T40,T41,T42,T43,T44,T45,T46,T47,T48,T49,T50,T51 / W08,T01,T02,T03,T04,T05,T06,T07,T08,T09,T10,T11,T12,T13,T14,T15,T16,T17,T18,T19,T20,T21,T22,T23,T24,T25,T26,T27,T28,T29,T30,T31,T32,T33,T34,T35,T36,T37,T38,T39,T40,T41,T42,T43,T44,T45,T46,T47,T48,T49,T50,T51 |

51 个业务任务及各功能、操作、场景、源码范围、状态权威和依赖从当前账本逐项联接，见机器合同。业务任务的依赖按两张图分别读取，不把一种图的 `dependsOn` 套到另一种图。

| 里程碑 | 交付与验收 |
| --- | --- |
| M1 独立工程与运行时 | 干净构建、安装、启动均不读取原应用路径；所有存储位置和认证来源明确 |
| M2 传输与后台适配 | 请求/响应/通知/超时/异常/断连/销毁/能力释放逐项通过；公开后台差异逐项适配且不静默删除字段 |
| M3 状态与基础界面 | 初始化、并发写、错误和重开符合基线；迁移失败可恢复备份 |
| M4 任务生命周期 | 后台接受、终态与界面分别证明；取消和重启恢复不靠本地改状态或重发冒充 |
| M5 其余 Codex 能力 | 核对真实 worker/Git/PTY/remote/权限；全部实际发现功能均在完整表中 |
| M6 剥离与升级 | 无误删共享能力且维护源码无第三方实现副本；新基线差分定位模块和回归场景 |
| M7 完整验收 | 每个保留功能有实际结果；mock/占位/未决服务/未通过项不算完成 |

原九项分析完成标准完整继承。1844 条场景属于后续产品验收规格，不要求在分析阶段把所有产品测试提前跑完；但主要行为的静态对照、会改变架构的未知项和明确验收前提仍是分析义务。unknown 数量不要求机械清零，也不据此宣称当前分析已经完成。

已批准的三个模型样例次数已使用，剩余 0。新的实际模型请求、客户端重启或服务操作另按既定授权边界执行；此限制不影响冻结来源的静态工作。本次没有新增目标执行、客户端启动、模型/服务请求、客户端代码或构建尝试。

## 继续工作的收敛条件

本方案已把当前 509 项功能、115 项职责、202 条依赖、30 条构建输入和 15 组运行时能力放在同一入口。本次交付解决的是工程依据分散与 v11 数字过时，不增加功能发现数，也不算运行通过。

下一项静态交付限定为完整进程、worker/helper 与资源入口清单：明确每个入口的维护路径、构建目标、运行时要求和未决条件，复用三类 preload 和已提取运行时源码。碰到已命名 provider 边界即引用现有合同，避免从每个消费者重新追到底层。新增细分分析必须说明它会改变哪个目录、接口、构建输入或验收决定。

升级时新版本固定为新基线；比较功能条件、协议通知、schema、运行时能力、依赖修改和资源，将差异回到具体模块与回归场景。旧证据不覆盖，数据迁移有备份与回退。最终完成仍以每项保留能力的真实结果及干净构建为准。
