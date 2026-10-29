# 独立重建可行性：运行时与构建输入 v1

当前保存材料尚不能支撑一条具备完整能力的独立运行时路线。可以重新编写构建脚本，但脚本无法补出运行时实现、原生桥、headers、工具链或缺失的服务契约。本批只形成分析和采用决定；实际构建、打包与升级仍属于后续实施验收。

固定范围为15组运行时能力、30条构建输入出现记录（21个不同路径，归并为12类职责）。15组不是整个运行时的完整能力清单，30条也不是全部构建材料。原功能、模式与完整验收要求保持。

| 路线 | 本批决定 |
| --- | --- |
| 独立 Owl 依赖 | 尚未建立独立获取渠道、版本/源码/许可、headers或完整构建输入；保留候选，不声称全球不存在来源。 |
| 固定 stock Electron 42.3.0 | 沿用既有对照：不能直接替换整个 Owl；公开原语可以参与逐能力适配，未证明完整等价。 |
| 自有适配与运行时扩展 | 保留为维护架构；引擎和平台实现分别取得或开发，接口同名、占位或原安装路径都不能充抵能力。 |

明确的预编译依赖符合原计划的可选引入方式，但必须固定独立来源、版本/hash、许可、平台/ABI和资源布局；它不代表该组件已恢复源码。整包官方下载线索也没有自动建立独立 Owl SDK。

| 能力 | 独立候选及缺少材料 | 简化替代的具体缺失 |
| --- | --- | --- |
| RAM-01 原生菜单 tracking | 菜单 tracking 源码/接口、窗口生命周期绑定、目标平台 SDK 和所选 runtime headers。 | 只调用普通 popup 无法证明 begin/end tracking、销毁和重复清理的成对副作用。 |
| RAM-02 音频 measurement | Owl histogram 桥或独立等效实现；具名计数生产者版本、增量/累计/重置和多读取方语义。 | 进程 metrics 或空 ready 响应丢失音频设备发现计数、状态与周期语义。 |
| RAM-03 运行时特性与 Windows policy | 两个 allowlist 键的引擎实现/默认值/reset、feature registry、Windows policy 清理实现。 | 仅保存布尔设置或返回 supported 不能产生引擎效果，不能证明限制可逆。 |
| RAM-04 Chrome 调试页策略 | 特权页面及服务实现、允许/拒绝范围、build flavor 和 profile/guest 策略连接。 | 普通页面路由或放宽全部导航会改变可信页范围和拒绝策略。 |
| RAM-05 Task Manager | 原生 Task Manager 的实际字段/动作/刷新/关闭行为资料，或经对照的独立 UI 与数据实现。 | getAppMetrics 只有数据原语；空函数或普通静态表不能替代基线 Task Manager 的行为。 |
| RAM-06 窗口平台能力 | 平台能力条件、setInputShape/hit testing 源码或独立实现、DPI/坐标及窗口生命周期接口。 | 恒真能力探测或整窗鼠标穿透会失去矩形级命中；源码已有 fallback 仍需保留，但不免除原生一致性。 |
| RAM-07 历史滑动导航 | 原生滑动手势、overlayBounds/Color 及导航状态同步实现，所选 runtime headers/SDK。 | 只调用 back/forward 不覆盖滑动动画、overlay 和销毁时手势状态。 |
| RAM-08 通知授权状态 | 状态查询/授权请求/系统设置打开实现、应用标识与打包条件、平台 SDK。 | 能展示通知或 beacon 返回 true 都不能证明授权；忽略内部吞错会错误承诺 renderer toast。 |
| RAM-09 屏幕光标能力 | 支持条件、坐标/权限能力探测和 controller 生命周期接口；目标平台实现及 SDK。 | 仅有 getCursorScreenPoint 不能证明平台能力或 controller 的建立/清理条件。 |
| RAM-10 浏览器权限 prompt | prompt 参数、响应/取消/过期和所有权生命周期；独立 partition 与浏览器权限服务实现。 | 普通 request handler 不能自动复现 prompt 协议、重复请求、状态及默认拒绝后效。 |
| RAM-11 系统字体枚举 | 能提供 family/faces、PostScript/full/style name、isMonospaced 的枚举实现与平台 SDK。 | 字符串字体列表丢失 face 和等宽判定；目录失败不能静默改为空，FontFace 加载仍是单独职责。 |
| RAM-12 浏览器 ownership、adoption 和 clone | clone/adoption 源码或独立实现、lease 消费/失效/拒绝、live 页面历史/表单/堆状态的准确契约。 | 移动同一 view、cold restore 或生成 lease 字符串不能证明复制活动页面状态。 |
| RAM-13 受限 Node 网络与 scoped IPC | 运行时补丁或独立进程/OS enforcement 源码、端点策略、重启参数和允许/拒绝用例。 | 普通 permission flags 或查询返回 true 不能证明网络和越界 IPC 实际被拒绝。 |
| RAM-14 普通更新与 managed relaunch | 固定版本更新依赖/源码配方、bridge 和策略事件/注销；自有签名/feed/应用安装布局。 | Sparkle 的 binaryTarget 不是源码重建，也不覆盖 Owl managed binding；普通更新不能充抵策略强制更新。 |
| RAM-15 四类特权浏览器设置 | contactInfo/passwordManager/extensions/siteSettings 的底层数据/服务和独立构建来源。 | 占位设置页或能加载普通 URL 会丢失四类真实服务操作；已保存 stock guest 拒绝八个目标 URL。 |

构建输入按职责归并，原30条记录完整保留：

| 职责 | 原出现数 | 处理 |
| --- | ---: | --- |
| runtime-types | 4 | 类型可以重新编写，但必须描述实际 provider；声明文件不能制造缺失方法。 |
| workspace-tooling | 5 | 原 monorepo 相对脚本无需恢复原名；按新的 workspace 编译/lint/dev 职责编写。 |
| runtime-driver | 4 | driver 可编写，独立 runtime 来源/锁定/hash/headers/SDK 必须实际取得，路径改写不补足它们。 |
| contract-generator | 3 | 从选定固定 schema 和桌面扩展生成；成功生成类型不证明真实服务覆盖。 |
| packaging-metadata | 2 | 应用标识、资源和版本布局重新定义；最终需与所选 runtime/helpers 一起验收。 |
| diagnostic-tool | 1 | heap 分析脚本不是产品启动前置；RAM-05 产品 Task Manager 继续完整保留。 |
| verification-tool | 2 | 自有样例/native-pipe/CDP 检查重新编写；测试 harness 不是待复刻产品能力的替代。 |
| new-project-lock | 3 | 三种锁文件名是替代选项；所提 pnpm workspace 只生成一个准确新锁，不能回填为原锁。 |
| workspace-config | 1 | 按已提出包边界配置成员；不依赖原作者 workspace 文件。 |
| typescript-config | 1 | 分离进程类型环境和编译目标；此项不独自覆盖 native ABI/编译配方。 |
| packager-config | 2 | ts/js 名为替代选项，选一个配置；最终需独立 runtime、native ABI、resources、签名与更新通道。 |
| bundler-config | 2 | ts/js 名为替代选项，分 main/preload/renderer/worker 入口并外置第三方/native。 |

锁文件的三种名称以及 Forge/Vite 的 ts/js 配置名是替代选项，不是要求全部找回的文件。新锁须对应新工程准确解析，不能冒充原锁；原生编译配方和引擎材料仍要独立记录。heap 分析脚本不是产品启动前置，但产品 Task Manager 能力完整保留。

三项旧源码待办已经有后续合同：RAM-02 的音频生产/消费、RAM-04 的启动与策略条件、RAM-06 的 input-shape owner。只退休这些相同源码问题；底层采集、特权页、hit testing及完整消费者/模式仍未验收。RAM-05/08/11 的后续消费者合同也进入当前视图。

版本依据另作限定：冻结根 devDependency 明确为 Electron 42.3.0，旧调查行动行的空 version 不能覆盖它；这仍不证明实际 Owl 映射。node-pty 根声明为 ^1.1.0，冻结已安装包另有 1.1.0 证据，不能把范围归一化结果当原锁。

native伴随依赖保留各自范围：node-pty 的修改不得随普通上游替换丢失；objc-js 已有 Node22/x64 的有限 native 构建/加载成功，但整包、目标 runtime和ARM未证明；Sparkle SPM binaryTarget为预编译路线，不证明源码构建或managed policy。Wasm/私有包等其他依赖不由这三项覆盖。

本批没有新运行、构建、下载、模型或服务调用，没有新增功能台账/实施计划版本。已有488项功能、534个不同操作、125个支撑、1650条未执行规格及原九项标准保持。

[逐组合同](independent-build-feasibility-v1.json) · [15组CSV](independent-build-feasibility-v1.csv) · [30条构建输入CSV](independent-build-feasibility-v1-build-inputs.csv) · [证据](independent-build-feasibility-v1-evidence.jsonl)
