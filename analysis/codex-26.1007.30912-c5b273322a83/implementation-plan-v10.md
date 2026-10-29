# Codex 独立客户端恢复实施计划草案 版本 10

目标是完整恢复固定基线的 Codex 界面、交互、状态、持久化和桌面集成，剥离有证据证明仅供 ChatGPT 使用的分支，通过依赖管理引入第三方实现。项目须可维护、升级、从干净环境构建打包，运行时不依赖原客户端安装路径。本轮仍为分析与实施依据，客户端实现尚未开始。

当前依据：[功能台账 v27](feature-scope-v27.json)、[场景台账 v24](feature-scope-v24-scenarios.json)、[覆盖表 v18](restoration-coverage-v18.json)。373 项有限功能定义、377 项用户操作、117 项支撑、1216 条未执行产品规格，全部归入 T01 至 T48。373 不是已证明完整产品分母。45 个已发现设置容器均有局部合同；没有新增整功能排除或行为通过项。

[机器可读计划](implementation-milestones-v10.json)保留每个任务的来源、完整 featureId/scenarioId、模块、外部依赖和验收条件。旧 v9 及其他编号快照保留历史含义；当前来源角色状态采用[逐 ID 处置 v5](legacy-entry-dispositions-v5.json)：968 条已保存入口的来源角色待审阅为 0，962 条无功能映射，完整功能身份闭合为 0。不得用角色盘点充抵功能验证。

## 源码准备与真实集成分别排程

以下输出是后续实施工作包，当前阶段只形成设计。源码接口/控制器可依照已保存合同准备；真实运行时、宿主、后台与存储集成继续受各自条件约束。源码准备成功不会把集成里程碑标为通过。

| 任务 | 源码准备上游 | 真实集成上游 | 可交付输出与准备出口 |
| --- | --- | --- | --- |
| W01 合同与来源映射 | 无 |  | 按服务命名空间拆开的 DTO、错误、通知和生命周期接口；原文件/hash/字节范围到维护模块的转换清单；37 个既有职责及 19 条重叠规则的导入边界。每个准备转换的范围有原位置、依赖合同、导入导出/副作用和回归场景；重叠范围只保留一个实现所有者。 |
| W02 独立构建与依赖输入 | 无 |  | 工作区及分进程 TypeScript/Vite/Forge 构建职责配置；202 条依赖的来源/新选版本/引入方式清单与新工程精确锁策略；30 条缺失输入的独立补齐任务和资源来源清单。每条构建输入有负责人、生成/获取方式和验证命令；第三方实现不会生成到第一方源码。 |
| W03 运行时与平台能力 | W01, W02 | W01, W02 | 15 组运行时能力的类型、生命周期和错误合同；RAM-02/04/06 已核实的 JS 策略及适配接口；逐平台 provider 选择和 BG-01 至 BG-04 的构建验收定义。每组明确第一方策略与底层 provider 责任；保留 unsupported、异常和释放语义。 |
| W04 桌面传输与宿主 | W01 | W01, W03 | preload、app-host、HTTP、resolver、扩展连接和 socket 各自的编解码器；身份/信任、订阅、断连、取消和资源释放状态机。真实传输接口被明确注入；端口、身份、owner 和 disposal 不跨服务混用。 |
| W05 后台适配 | W01, W02 | W01, W02 | 按实际 provider 选择的 app-server 请求及通知适配器；10 项可选通知字段的容忍边界；预测 fork 的独立能力接口与不支持状态；环境扩展、命令后台和私有服务的分离接口。保留原参数、错误及通知语义；预测 fork 不降级为普通 fork 或新会话。 |
| W06 状态与持久化 | W01 | W01, W03 | 11 个已分析存储域的根路径配置与 driver 接口；schema/revision/并发写/原子替换、退出和迁移恢复状态机；desktop home、execution home、runtime profile 与认证存储的分别注入。每域有读取/写入/flush/迁移/恢复责任；membership 队列与文件 flush 不互相代替。 |
| W07 应用壳与模式 | W01, W04, W06 | W04, W06 | 应用初始化、路由与多窗口壳；模式/认证家族/执行位置/会话类别/资格的独立状态；共享首页 composer/controller 与 Codex 本地提交策略。共享组件和 provider 生命周期被保留；只剥离有证据的三组 Chat 专用分支。 |
| W08 其余功能与完整范围 | W04, W05, W06, W07 | W04, W05, W06, W07 | 48 个任务的界面、控制器与宿主消费者；终端/文件与变更/Git/远程/云端/系统能力的委托实现清单；每功能正常、失败、取消和恢复场景与条件。373 项现有定义逐项有实现所有者；其他已发现委托能力及未知范围仍在表内。 |
| W09 剥离升级与最终验收 | W08, T01, T02, T03, T04, T05, T06, T07, T08, T09, T10, T11, T12, T13, T14, T15, T16, T17, T18, T19, T20, T21, T22, T23, T24, T25, T26, T27, T28, T29, T30, T31, T32, T33, T34, T35, T36, T37, T38, T39, T40, T41, T42, T43, T44, T45, T46, T47, T48 | W08、T01 至 T48 | 全范围验收表、剥离清单及第三方审计；新基线差分、依赖升级及数据迁移/备份/回退配方；干净安装/构建/打包/升级与原安装路径独立性检查。所有 T01 至 T48 和 W08 的设计结果可追踪到验收；未决能力保留失败/待验证状态。 |

两套依赖图均有 57 个节点，直接采用[当前排序图](restoration-current-ordering-v1.json)。源码准备从 W01/W02 开始，随后 W03/W04/W05/W06，再 W07、T01 至 T48/W08、W09；真实集成则在 W03 后才接 W04/W06。同层只表示合同依赖允许并行，不代表外部输入已取得。每个任务另保留具体账户、平台、服务、原生与持久化前置条件。

## 由职责和来源决定工程结构

发布 chunk 只用于来源定位，不按文件名自动拆业务模块。进程主干沿用 main/preload/renderer/worker；实际职责路径由下表与来源合同确定。原文件 hash、字节范围、转换方式、导入导出、共享状态、副作用、第三方边界与场景必须一起保留。

```text
apps/desktop/src/main/              启动、窗口、宿主、系统和退出
apps/desktop/src/preload/           世界隔离、IPC、端口和注入
apps/desktop/src/renderer/app/      路由、初始化、多窗口和模式
apps/desktop/src/renderer/features/ 功能界面、控制器和状态
apps/desktop/src/workers/           独立生命周期后台工作
apps/desktop/resources/             有来源记录的资产
packages/contracts/src/             按服务分开的 DTO/事件/错误
packages/desktop-transport/src/     宿主、传输、信任和释放
packages/backend-adapter/src/       app-server 与其他服务适配
packages/runtime-adapter/src/       运行时和原生能力接口
packages/state-storage/src/         状态、revision、保存和迁移
tools/recovery/                     来源映射和可审查转换
tools/build/                        自有构建、生成和打包
tests/fixtures/                     合成目录和回归样例
```

这个主干不覆盖或重命名下面的具体职责路径，例如 app-server-client、storage-contracts 和 main 内持久化实现仍按相应证据保留。[37 个逻辑模块合同](logical-module-contracts-v1.json)各有计划要求的十项字段、251 个唯一来源范围和[19 条重叠规则](logical-module-ownership-v1.json)。37 只是既有职责集合；438 个发布文件不能充当源码模块分母。

| 既有逻辑职责 | 基础任务 | 拟维护路径 |
| --- | --- | --- |
| LM-BOUNDARY-STRUCT-RWC-MANAGER：Request scheduling and transport facade | W05 | `packages/app-server-client/src/request-manager.ts` |
| LM-BOUNDARY-STRUCT-RWC-FETCH：Desktop HTTP transport adapter | W04 | `packages/desktop-http-client/src/desktop-fetch.ts` |
| LM-BOUNDARY-STRUCT-RWC-RESOLVER：Injected request resolver | W04 | `packages/app-host-client/src/request-resolver.ts` |
| LM-BOUNDARY-STRUCT-RWC-HOSTED-FILES：Hosted-file extension connection | W05 | `packages/app-server-client/src/extensions/hosted-files.ts` |
| LM-BOUNDARY-STRUCT-RWC-HOST-TRANSPORT：Host connection adapter | W05 | `packages/app-server-client/src/host-connection.ts` |
| LM-BOUNDARY-STRUCT-RWC-COORDINATION：Cross-client coordination adapter | W04 | `apps/desktop/src/main/coordination/socket-client.ts` |
| LM-BOUNDARY-STRUCT-RWC-PROJECTS：Project domain and state contracts | W06 | `packages/projects/src/contracts.ts`；`apps/desktop/src/renderer/projects/project-client.ts`；`apps/desktop/src/main/projects/project-service.ts` |
| LM-BOUNDARY-STRUCT-CHUNK：Host-to-view framing, acknowledgement and assembly | W04 | `packages/desktop-transport/src/chunked-messages.ts` |
| LM-BOUNDARY-STRUCT-browser-annotation-lifecycle：Browser annotation application adapter | W07 | `apps/desktop/src/browser-preload/annotation/browser-annotation-lifecycle.tsx` |
| LM-BOUNDARY-STRUCT-browser-annotation-root：Browser annotation application adapter | W07 | `apps/desktop/src/browser-preload/annotation/browser-annotation-root.tsx` |
| LM-APPHOST-AH-M01：接收窗口 message，并通过注入 IPC adapter 转发所选 port；将 channel/envelope 和 transfer list 合同集中管理。 | W04 | `apps/desktop/src/preload/app-host-bridge.ts` |
| LM-APPHOST-AH-M02：组装注入的 event predicate、context resolver、port/RPC adapter 和 remote view 生命周期，保持连接入口独立。 | W04 | `apps/desktop/src/main/app-host/connection-handler.ts` |
| LM-APPHOST-AH-M03：分别管理 context slot/窗口注册生命周期与 sender/frame predicate，并通过 WindowServices 注入连接入口。 | W04 | `apps/desktop/src/main/window-services/context-registry.ts` |
| LM-APPHOST-AH-M04：仅在 composition root 创建所需 provider 并显式组装 host services，将依赖与 disposal hook 注入。 | W04 | `apps/desktop/src/main/app-host/service-assembly.ts` |
| LM-APPHOST-AH-M05：管理 request id 到 AbortController 的映射、cancel/dispose、callback 调用与 Response bridge 清理。 | W04 | `apps/desktop/src/main/http/http-provider.ts` |
| LM-APPHOST-AH-M06：集中 URL/body/header、destination guards、auth/workspace/retry、response/error normalization；网络与身份/helper 通过依赖注入。 | W04 | `apps/desktop/src/main/http/desktop-fetch.ts` |
| LM-APPHOST-AH-M07：围绕显式 policy state 管理 readiness/generation/refresh/session restrictions，再把 fetch/request 委托给 native runtime adapter。 | W03 | `apps/desktop/src/main/network/application-network.ts` |
| LM-APPHOST-AH-M08：分开 requirements/config 获取、临时 transport lifecycle、schema boundary 与 Node permission/relaunch capability，以 adapter 限制运行时耦合。 | W03 | `apps/desktop/src/main/network/runtime-startup.ts` |
| LM-SOURCE-MODE-TRANSITION：Mode transition guard and ordered state writes; retain supplied store and atoms. | W07 | `apps/desktop/src/renderer/mode/transition.ts` |
| LM-SOURCE-MODE-RESOLVER：Access-sensitive mode resolution, including persisted value passthrough. | W07 | `apps/desktop/src/renderer/mode/resolver.ts` |
| LM-SOURCE-MODE-STATE：Selected state declarations/initialization; actual store/provider ownership remains unresolved. | W07 | `apps/desktop/src/renderer/mode/state.ts` |
| LM-SOURCE-NATIVE-WINDOW-EVENTS：First-party window scroll monitor registration and normal-path removal. | W03 | `apps/desktop/src/main/native/window-events.ts` |
| LM-SOURCE-NATIVE-NOTIFICATIONS：First-party notification permission callback, center cache and RunLoop reference management. | W03 | `apps/desktop/src/main/native/notifications.ts` |
| LM-SOURCE-NATIVE-APPLE-EVENTS：First-party Apple Event wrapper factories; no event execution proven. | W03 | `apps/desktop/src/worker/native/apple-events.ts` |
| LM-PROVIDER-provider-lifecycle：组件所属 scope、effect 安装与清理；registry 存在性选择分支。 | W04 | `apps/desktop/src/renderer/app-host/provider-lifecycle.ts` |
| LM-PROVIDER-host-rpc-selector：primary forHost、client.rpc、缓存、延迟 RPC 及退役条件。 | W04 | `packages/app-host-client/src/host-rpc-selector.ts` |
| LM-PROVIDER-domain-host-registry：X3 注册、条件 Sii 创建、N3 发布／替换／删除及 disposal。 | W04 | `packages/app-server-client/src/domain-host-registry.ts` |
| LM-PROVIDER-internal-manager-rpc-adapter：捕获 manager、MessageChannel、manager／coordinator facade 的原参数转发及重连清理。 | W04 | `apps/desktop/src/renderer/app-host/internal-manager-rpc.ts` |
| LM-PROVIDER-host-provided-rpc-adapter：ready manager RPC 的 duplicate、watch、lease、connection 替换与清理。 | W04 | `apps/desktop/src/renderer/app-host/host-provided-rpc.ts` |
| LM-CONTEXT-HOST-SOURCE-CONTEXT-MODULE-PROPOSAL-001：First-party source-context forwarding and lifecycle adapter for known main-process consumers. | W05 | `apps/desktop/src/main/context/source-context.ts` |
| LM-RUNTIME-RF-1：Allowlisted boolean merge/cache, auth owner and generation invalidation | W03 | `apps/desktop/src/main/runtime/runtime-feature-policy.ts` |
| LM-RUNTIME-RF-2：Expose runtime feature capabilities through the app-host service boundary | W04 | `apps/desktop/src/main/runtime/runtime-feature-provider.ts` |
| LM-RUNTIME-RF-3：Ready/evaluation context checks and runtime-feature gate dispatch | W07 | `apps/desktop/src/renderer/runtime/runtime-feature-gates.ts` |
| LM-SETTINGS-0：Preserve the descriptor table and accessor/initializer wiring as a shared source contract, with imported providers represented by explicit external dependencies. This is asset registration, not the implementation of53 settings workflows. | W07 | `apps/desktop/src/renderer/settings/asset-registry.ts` |
| LM-SETTINGS-1：Restore table keys, reference/loader wiring and explicit external interfaces. Import specifiers and construction records identify implementation targets to investigate; they do not reconstruct each target page or prove delivery. | W07 | `apps/desktop/src/renderer/settings/page-factory-registry.ts` |
| LM-SETTINGS-2：Preserve section data, explicit export/import relation and predicate source boundaries. Treat auth/platform/capability/config and second/third-parameter values as injected context; retain pending/error and switch fall-through semantics. | W07 | `apps/desktop/src/renderer/settings/sections-and-visibility.ts` |
| LM-SETTINGS-3：Restore the single route construction and ordered redirect/lookup branches as a routing contract. Preserve search/hash/state and the recorded mode query write, with navigation and helper results as external interfaces. | W07 | `apps/desktop/src/renderer/settings/route-policy-and-renderer.tsx` |

条件消费者只沿用已有合同中的 taskId/featureId 连接；机器计划更新到当前覆盖表引用，并保留 inferred、实际实例未证明及不完整消费者集合的限制。不会按 Voice、Pets、Browser 或 Debug 名称自动归入 T28/T32/T26/T31。

[首页分流](product-flow-ownership.md)保留同一套共享 composer/controller，将 Codex 入口策略、共享渲染和本地提交分别维护。产品模式、认证家族、执行位置、会话类别和后台资格独立建模。app-server、桌面 HTTP、注入 resolver、扩展连接和协调 socket 保持各自协议/接收方；renderer 通过合同调用宿主。

## 运行时采用和原生输入

[运行时采用矩阵](runtime-adoption-matrix-v1.md)选择第一方能力合同加独立 provider 的维护边界，尚未选出完整合格运行时。固定 stock Electron 42.3.0 直接替换路线已被接口及特权 URL 对照否定；公开 API、同 view 移动或普通历史复制只证明对应原语。完整资格必须覆盖独立来源/版本/校验和、构建输入、ABI、功能、目标平台和升级。

| 能力组 | 第一方适配路径 | 当前未取得的关键条件 |
| --- | --- | --- |
| RAM-01 原生菜单 tracking | `packages/runtime-adapter/src/native-menu-tracking` | 菜单开启、关闭和销毁的原生时序及 tracking 副作用；取得对应实现源码或运行时扩展。 |
| RAM-02 音频 measurement | `packages/runtime-adapter/src/measurement` | 真实 histogram 生产、delta/reset/configured-set、多 reader/平台语义及独立 bridge 来源。 |
| RAM-03 运行时特性与 Windows policy | `packages/runtime-adapter/src/runtime-feature-policy` | 两键的原生效果、默认值与可逆性；supported-feature registry；Windows policy fallback 的实际清理效果。 |
| RAM-04 Chrome 调试页策略 | `packages/runtime-adapter/src/chrome-page-policy` | 真实特权页/策略作用范围、profile/guest 边界及可构建 provider。 |
| RAM-05 Task Manager | `packages/runtime-adapter/src/diagnostics/task-manager` | 基线实际字段、动作、刷新/关闭语义和独立 UI 实现；不以空函数满足 guard。 |
| RAM-06 窗口平台能力 | `packages/runtime-adapter/src/window-capabilities` | 原生能力、setInputShape/hit-testing、坐标/DPI 及真实 RPC/平台效果。 |
| RAM-07 历史滑动导航 | `packages/runtime-adapter/src/history-swipe` | 原生手势、overlay 与导航状态同步的独立 provider 及目标 SDK/headers。 |
| RAM-08 通知授权状态 | `packages/runtime-adapter/src/notifications/authorization` | 目标平台授权 API、bridge 源码与实际状态映射；不从能显示通知推导授权结果。 |
| RAM-09 屏幕光标能力 | `packages/runtime-adapter/src/cursor-capabilities` | 平台能力条件与独立探测 provider；当前 getter 读数不构成跨平台证明。 |
| RAM-10 浏览器权限 prompt | `packages/runtime-adapter/src/browser-permissions` | prompt 参数、响应及生命周期和浏览器服务后效；公开 request handler 不构成同协议实现。 |
| RAM-11 系统字体枚举 | `packages/runtime-adapter/src/fonts` | 返回值格式、字体集合/本地化行为及对应 OS provider 源码和目标 SDK。 |
| RAM-12 浏览器 ownership、adoption 和 clone | `packages/runtime-adapter/src/browser-ownership` | 可独立构建的 clone/adoption 实现；原 live clone 的实际历史/页面状态语义；同一 view 移动不能证明复制能力。 |
| RAM-13 受限 Node 网络与 scoped IPC | `packages/runtime-adapter/src/process-policy` | 能拒绝通用网络和越界 IPC、允许声明端点的执行机制、平台策略与可构建实现；不是 permission.has 的返回值。 |
| RAM-14 普通更新与 managed relaunch | `packages/runtime-adapter/src/updates` | 独立签名/更新 feed/安装配置、平台 updater 以及 managed-policy 事件/注销；Sparkle 来源不覆盖 Owl binding。 |
| RAM-15 四类特权浏览器设置 | `packages/runtime-adapter/src/browser-settings` | 四类页面的底层数据/服务行为、独立 provider 与构建来源；固定 stock guest 已拒绝八个目标 URL。 |

RAM-02 的[音频 owner](audio-measurement-owner-v1.md)、RAM-04 的[调试页策略](debug-chrome-policy-owner-v1.md)、RAM-06 的[input-shape owner](input-shape-owner-v1.md)已经解决选定 JS 生产/消费、启动/写入条件和交互合同。缺少 native provider 不重开这些源码问题；真实 histogram、特权页策略及 hit-testing/平台效果继续开放。15 组能力与历史 17 条缺失 API 路径是不同分母。

| 构建关口 | 覆盖原输入 | 采用条件 |
| --- | --- | --- |
| BG-01 运行时类型与能力合同 | BUILD-001, BUILD-003, BUILD-013, BUILD-015 | types 必须从选定 provider 的合同产生；声明一个不存在的方法不构成兼容。 |
| BG-02 独立获取、启动与源码来源 | BUILD-005, BUILD-006, BUILD-011, BUILD-021 | runtime-driver 只指向独立依赖/源码构建产物；记录 commit、平台、校验和与 SDK/headers。现未取得完整 Owl 输入。 |
| BG-03 原生 ABI 与编译配置 | BUILD-026 | 按目标 runtime headers、NODE_MODULE_VERSION/Node-API 要求、架构与 SDK 重建 native packages。Node 版本、Node-API 10 或本地 Node22 objc load 均不证明 Owl/候选 Electron ABI。 |
| BG-04 独立打包、安装和升级 | BUILD-012, BUILD-017, BUILD-022, BUILD-025, BUILD-027, BUILD-028, BUILD-029, BUILD-030 | 锁定独立 artifact/构建配方、preload/resources/helpers、应用标识/数据根和签名更新配置；新版本重建并验证能力差异，不读取原安装路径。 |

node-pty 的已确认修改保留补丁/适配边界，仍须目标环境 PTY 创建和释放；objc-js 的本地 Node 22 构建及 export-only load 不证明目标 Owl/Electron ABI；Sparkle 的 SPM binary 路线与源码重建分列。不能复制原安装 Owl/原生库充当恢复源码，也不能删除 guard、返回恒真能力、伪造 lease 或用空页面替代真实能力。live clone、cold restore 和 window.open 分别验证，原 clone 是否承诺 JS 堆保留仍按调用与行为证据判断。

## 后台协议采用

[11 个已保存差异变体](protocol-delta-adoption-v1.md)已经逐一有采用决定，维持原 466 变体比较的分母：455 相同、11 不同。无需重新全量发现协议。

| 决定 | 范围 | 实现边界与验收 |
| --- | --- | --- |
| PDA-D01 | 10 个变体 | Retain a tolerant notification boundary and preserve optional extension fields. Missing/null values remain valid. No mandatory-field backfill or model/reasoning UI requirement follows from the frozen contract.；Both old and extended payloads through the chosen real decoder, clone/store and display.；Ordering, buffering/drain, duplicate events, reconnect and persistence behavior. |
| PDA-D02 | 1 个变体 | Preserve prediction fork as a distinct backend capability. Do not delete the flag, silently use ordinary fork, or re-enable fresh-thread fallback. Full fidelity requires the matching backend source/implementation and successful semantic evidence.；Loaded persisted parent and ephemeral/no-override requirements.；Effective configuration/tools/environment/history inheritance and cache behavior.；Temporary-thread lifecycle, cancellation/cleanup and prediction return semantics. |

10 个通知差异是 subAgentActivity 的可选 nullable model/reasoningEffort；保留容忍与字段传递，既有 required 不变。实际 decoder/clone/store/通知顺序仍需验证。预测 fork 的 experimentalPredictionMode 与 ephemeral/excludeTurns、禁止 fresh-thread fallback 的合同保留；公开候选尚未具备预测语义资格，版本门槛通过、未知字段被忽略或普通 fork 成功均不能替代。实际 provider/receiver、私有服务与 npm 到源码 commit 绑定继续开放。

## 存储域、隔离与恢复

[11 域映射](storage-domain-map-v1.md)给出来源权威、路径规则、写入和恢复边界；实际有效根和完整全域隔离尚未证明。desktop home、execution home 与 Electron profile 分别注入；浏览器 partition、native credential 和远端账户服务另有权威。

| 存储域 | 职责与路径 | 维护决定及所缺条件 |
| --- | --- | --- |
| SDMD-01 Electron profile | bootstrap path policy -> runtime profile provider；oD(env override or appData/build flavor/agent run ID); app.setPath(userData,...) | 独立应用标识、显式profile根和runtime配置分别管理；不依靠改目录名称证明全部隔离。；选定runtime的有效userData/session路径、helper配置和迁移规则；不读取个人profile。 |
| SDMD-02 主进程globalState | gT/uT -> startup Vr -> receiver scopedState；desktopCodexHome/.codex-global-state.json; .bak and same-directory temp | 状态接口、调度队列和JSON后端分离；广播、内存完成和文件完成使用不同合同。；实际有效home、schema/defaults与目标runtime/平台耐久性；旧9个隔离文件场景不证明整个客户端。 |
| SDMD-03 桌面设置与旧键迁移 | ki local read -> initialized configClient -> app-server config/batchWrite；startup reads desktopCodexHome/config.toml desktop section; effective backend configuration layer/path unresolved | 保留本地启动读取器、设置状态/迁移协调器和后台配置gateway三个边界；不生成直接覆盖TOML的替代写入器。；pt/config provider实际实例与配置层、descriptor/schema/Pi迁移规则、backend写入/失败/恢复语义。 |
| SDMD-04 thread memberships与projectless路径提示 | AJe local globalState adapter + U0 queue + optional backend membership callback；globalState key families; backend callback may own additional state, whose effective storage is unresolved | 维护membership队列/后台桥和本地状态适配两个职责；不为flush名称凭空新增数据库，也不省略全局状态文件排空。；writeThreadAssignment/getThreadStartProjectId实际provider、跨后台/本地失败原子性、调用完成与磁盘完成的集成时序。 |
| SDMD-05 history-snapshot启动清理 | gT cleanup -> filesystem；desktopCodexHome/sqlite/codex-history-snapshots[[-flavor]].db and three SQLite sidecars | 将启动清理作为显式迁移/维护步骤，保留精确文件族；禁止把它扩大到所有SQLite或会话记录。；snapshot生产者、用途、flavor输入和清理后果；迁移测试只可用自有合成文件。 |
| SDMD-06 app-server任务与执行状态 | selected host transport/CLI/daemon/websocket -> native/backend storage；executionCodexHome is separately resolved; inherited env, WSL, remote websocket or daemon can select another effective authority | backend运行配置必须携带host/transport/executable/home身份；本地桌面home和后端有效home分别验收。；实际transport/executable、服务有效根/数据库、WSL helper、SIGTERM恢复与任务状态提交规则。 |
| SDMD-07 认证与secret storage | desktop auth request -> app-server/native file/keyring/secret provider；auth.json/keyring and keychain access group are frozen capability/metadata clues; active provider and namespace unresolved | 认证仓库、平台密钥命名空间和后台身份作为独立依赖合同；不得将文件目录覆盖当作凭据隔离开关。；可控自有认证环境、明确provider/namespace和迁移选择规则；未读取auth文件、keychain或凭据。 |
| SDMD-08 浏览器持久partition | main partition constructors -> runtime session provider；persist:codex-browser- + encoded name; persist:codex-browser-app-route: + encoded two-input NUL tuple | 独立runtime profile和partition身份一起管理；保留app/route身份及permission处理，不复制原浏览器profile。；实际session storage根、所有partition调用方、账号/host绑定与底层服务迁移；privileged settings仍需runtime provider。 |
| SDMD-09 renderer persisted atoms与窗口标签页 | renderer bridge -> main atom policy -> globalState object；electron-persisted-atom-state with thread-browser-tabs-v1:/thread-tab-routes-v1: subkeys; not automatically renderer localStorage | renderer镜像、IPC策略和main状态后端分开；保留primary owner、删除编码和窗口过滤。；实际store/provider实例、MODE初始化/送达和schema比较器；不以键名决定ChatGPT剥离。 |
| SDMD-10 共享host对象镜像 | hXe sharedObjectRepository -> wee object/Set subscribers；selected main in-memory object and shallow snapshots; no disk path established | 将此域保留为内存发布仓库；持久化由各真实owner另行承担，不重复保存整个镜像。；完整对象owner/重建顺序和实际provider；不得由一次快照声称可重启恢复。 |
| SDMD-11 退出、日志与tracing排空 | quit coordinator -> independent state/settings/backend/log providers；globalState, settingsStore, membership queue, tracing and logger each retain own authority; log paths unresolved here | 退出协调器按provider记录等待/超时/失败，区分正常退出、强停和断电；不以一个flush标签代表全部域。；真实Electron事件、目标平台helper/native、各provider提交与异常退出行为；既有17个替身场景不作产品通过。 |

配置启动 TOML 读取与 app-server config/batchWrite、成功确认后的迁移清理分开；membership 本地状态、后台队列完成与 globalState 文件 flush 分开。snapshot 清理只保留已核实的 DB/-wal/-shm/-journal 家族，不扩大成任意 SQLite/会话迁移。拟路径保留 storage-contracts、main/persistence、settings store、backend config/auth、project membership、runtime profile 和 quit coordinator；全量 plugin/cache/download/update/automation/workspace/remote store 仍有缺口。

## 全部当前功能任务与委托范围

下表 48 个任务完整保留 373 项现有定义。具体 featureId、场景、输入、支撑、来源、消费者、外部依赖及逐项验收见机器计划和[覆盖表 v18](restoration-coverage-v18.json)。共享消费者不重复计算功能。

| 任务 | 定义数 | 第一方主模块 | 真实集成上游 |
| --- | --- | --- | --- |
| T01 General | 28 | `apps/desktop/src/renderer/features/settings/general` | W04, W06, W07 |
| T02 Agent | 6 | `apps/desktop/src/renderer/features/settings/agent` | W05, W06, W07 |
| T03 任务生命周期 | 5 | `apps/desktop/src/renderer/features/tasks` | W04, W05, W06, W07 |
| T04 电脑使用 | 8 | `apps/desktop/src/renderer/features/computer-use` | W04, W05, W06, W07 |
| T05 项目与远程入口 | 1 | `apps/desktop/src/renderer/features/projects` | W04, W05, W06, W07 |
| T06 Git | 10 | `apps/desktop/src/renderer/features/git` | W05, W06, W07 |
| T07 工作树 | 8 | `apps/desktop/src/renderer/features/worktrees` | W04, W05, W06, W07 |
| T08 快捷键 | 5 | `apps/desktop/src/renderer/features/shortcuts` | W03, W06, W07 |
| T09 文件查看器 | 2 | `apps/desktop/src/renderer/features/file-viewers` | W04, W06, W07 |
| T10 外观 | 19 | `apps/desktop/src/renderer/features/appearance` | W03, W06, W07 |
| T11 Appshot | 4 | `apps/desktop/src/renderer/features/appshots` | W03, W04, W06, W07 |
| T12 桌面通知 | 6 | `apps/desktop/src/renderer/features/notifications/desktop` | W03, W04, W06, W07 |
| T13 账户通知 | 1 | `apps/desktop/src/renderer/features/notifications/account` | W05, W06, W07 |
| T14 本地环境 | 4 | `apps/desktop/src/renderer/features/local-environments` | W04, W05, W06, W07 |
| T15 Hooks | 7 | `apps/desktop/src/renderer/features/hooks` | W05, W07 |
| T16 MCP | 6 | `apps/desktop/src/renderer/features/mcp` | W03, W05, W07 |
| T17 Plugins | 16 | `apps/desktop/src/renderer/features/extensions` | W03, W05, W07 |
| T18 Skills | 9 | `apps/desktop/src/renderer/features/skills` | W03, W05, W07 |
| T19 Connections | 19 | `apps/desktop/src/renderer/features/connections` | W03, W05, W07 |
| T20 Usage | 10 | `apps/desktop/src/renderer/features/usage` | W03, W05, W07 |
| T21 Billing | 11 | `apps/desktop/src/renderer/features/billing` | W03, W05, W07 |
| T22 Teams | 13 | `apps/desktop/src/renderer/features/teams` | W03, W05, W07 |
| T23 Age | 2 | `apps/desktop/src/renderer/features/account/age` | W03, W05, W07 |
| T24 Passwords | 5 | `apps/desktop/src/renderer/features/credentials` | W03, W05, W07 |
| T25 Cloud computer | 6 | `apps/desktop/src/renderer/features/cloud-computer` | W03, W05, W07 |
| T26 Browser use | 10 | `apps/desktop/src/renderer/features/browser/settings` | W03, W05, W07 |
| T27 Chronicle | 6 | `apps/desktop/src/renderer/features/chronicle` | W03, W05, W07 |
| T28 Voice | 10 | `apps/desktop/src/renderer/features/voice/settings` | W03, W05, W07 |
| T29 Code review | 15 | `apps/desktop/src/renderer/features/review/settings` | W03, W05, W07 |
| T30 Codex Cloud | 8 | `apps/desktop/src/renderer/features/cloud-environments/settings` | W03, W05, W07 |
| T31 Debug | 2 | `apps/desktop/src/renderer/features/diagnostics/settings` | W03, W05, W07 |
| T32 Pets | 7 | `apps/desktop/src/renderer/features/pets/settings` | W03, W05, W07 |
| T33 Import | 5 | `apps/desktop/src/renderer/features/imports/settings` | W03, W05, W07 |
| T34 Ads controls | 5 | `apps/desktop/src/renderer/features/ads/settings` | W03, W05, W07 |
| T35 Archived chats | 5 | `apps/desktop/src/renderer/features/archives/settings` | W03, W05, W07 |
| T36 Data controls | 8 | `apps/desktop/src/renderer/features/privacy/settings` | W03, W05, W07 |
| T37 Agreements | 2 | `apps/desktop/src/renderer/features/agreements/settings` | W03, W05, W07 |
| T38 Account | 5 | `apps/desktop/src/renderer/features/account/settings` | W03, W05, W07 |
| T39 Extension | 5 | `apps/desktop/src/renderer/features/browser-extension/settings` | W03, W05, W07 |
| T40 Storage | 3 | `apps/desktop/src/renderer/features/storage/settings` | W03, W05, W07 |
| T41 Security | 19 | `apps/desktop/src/renderer/features/account-security/settings` | W03, W05, W07 |
| T42 Parental controls | 4 | `apps/desktop/src/renderer/features/family/settings` | W03, W05, W07 |
| T43 Trusted contact | 5 | `apps/desktop/src/renderer/features/trusted-contact/settings` | W03, W05, W07 |
| T44 Safety | 3 | `apps/desktop/src/renderer/features/time-management/settings` | W03, W05, W07 |
| T45 Cloud settings | 2 | `apps/desktop/src/renderer/features/cloud-preferences/settings` | W03, W05, W07 |
| T46 Cloud environments | 7 | `apps/desktop/src/renderer/features/cloud-environments/legacy-settings` | W03, W05, W07 |
| T47 Personalization | 15 | `apps/desktop/src/renderer/features/personalization/settings` | W03, W05, W07 |
| T48 Codex Micro | 11 | `apps/desktop/src/renderer/features/codex-micro/settings` | W03, W05, W07 |

General/Agent 设置须接上实际消费者；任务提交、后台接受、流式通知、审批、取消、终态、导航及持久化分别验证。本地环境保存后激活失败保留独立结果；Hooks 保留管理层、来源和信任；MCP/插件/技能/连接保留共享管理器和 OAuth 生命周期。导入检测/同步/历史/后置设置与终端、文件变更、Git/PTY/worker、浏览器所有权、远程/云端和系统能力的既有委托合同仍在完整恢复范围，不能仅恢复设置页面。

## 第三方依赖、构建与模式剥离

[依赖清单](dependencies.csv)有 202 条记录、78 项根声明，[逐项调查动作](dependency-investigation-actions-v1.json)覆盖全部 202 条。沿用原来源/版本/许可证/修改证据，新工程独立选版本并生成精确锁；原声明范围不等于实际安装版本。React/UI、query/schema、遥测、capnweb、native/Wasm 和运行时从依赖引入，第一方封装单独恢复。修改库采用受维护依赖、独立补丁或明确适配，未知内嵌代码不作为业务源码输出。

[30 条缺失构建输入](build-input-dispositions-v1.json)对应 21 个唯一原路径，逐条已有补齐决定、依赖任务及验收条件，替代实现仍为 0。TypeScript/Vite/Forge 是来源支持的构建职责候选，完整版本锁和最终运行时集成尚未完成。原 monorepo 脚本无须逐字还原，但类型生成、资源、诊断、原生编译、启动和打包职责必须由独立输入承担。

当前 shared 1、unknown 372，Codex/ChatGPT 整功能正向分类为 0；这不表示未发现 Codex 分支。已明确[3 组 Chat 专用分支](chat-branch-decisions.md)，整功能排除仍为 0。共享归档、首页提交、账户访问及其他 Codex 依赖保留。12 关联/3 重叠的源码关系均已审阅，3 项业务父功能未知；不能为了清零未知而合并或删除。

## 里程碑验收和仍需分析的条件

M1 至 M7 完整沿用 v9 的开始条件、交付、验收与失败动作，机器计划逐字保留。主流程样例或源码隔离检查不能替代它们。

| 里程碑 | 上游 | 完整退出条件 |
| --- | --- | --- |
| M1 独立工程与运行时 | 无 | 干净构建、安装、启动均不读取原应用路径；所有存储位置和认证来源明确 |
| M2 传输与后台适配 | M1 | 请求/响应/通知/超时/异常/断连/销毁/能力释放逐项通过；公开后台差异逐项适配且不静默删除字段 |
| M3 状态与基础界面 | M2 | 初始化、并发写、错误和重开符合基线；迁移失败可恢复备份 |
| M4 任务生命周期 | M2, M3 | 后台接受、终态与界面分别证明；取消和重启恢复不靠本地改状态或重发冒充 |
| M5 其余 Codex 能力 | M2, M3, M4 | 核对真实 worker/Git/PTY/remote/权限；全部实际发现功能均在完整表中 |
| M6 剥离与升级 | M3, M4, M5 | 无误删共享能力且维护源码无第三方实现副本；新基线差分定位模块和回归场景 |
| M7 完整验收 | M1, M2, M3, M4, M5, M6 | 每个保留功能有实际结果；mock/占位/未决服务/未通过项不算完成 |

| 未完成条件 | 性质 | 影响与证据 |
| --- | --- | --- |
| PC-01 | architecture-affecting-analysis | W01, W07, W08：完整功能/模块分母和消费者闭包；模式未明项保留，不能据名称剥离。 |
| PC-02 | external-input-or-provider-development | W02, W03, W04：独立运行时来源/版本/构建输入/ABI 和 15 组能力，三类原生依赖的目标环境构建。 |
| PC-03 | external-input-or-provider-development | W05：匹配预测语义的后台及私有服务；公开候选到实际分发版本的来源绑定。 |
| PC-04 | architecture-affecting-analysis | W05, W06：未覆盖 store 的权威 owner、根路径/认证/backend 边界及迁移责任；实际有效根另列运行验收。 |
| PC-05 | implementation-verification | W03, W04, W05, W06, W08, W09：真实传输/decoder/通知/持久化和逐平台能力；完整构建安装、升级和回退。 |
| PC-06 | behavior-analysis-with-authorization-limit | W08：主要失败/审批/PTY及执行中取消仍缺行为对照，自动续跑未证明；已有模型授权余 0。 |

分析出口继续按[九标准/39 要求复核](analysis-stage-decisions-v4.md)审计；本次不提升原四项记录义务/五项部分完成的状态。1216 条产品规格不自动成为分析阶段全部跑完的前置条件；主要行为对照、足以指导实现的功能/模块关系和会改变架构的未知仍是本阶段义务。未知模式无需机械清零，缺口也不能默默移走。

## 行为证据、授权与升级

已有只读样例完成且可重开；停止后重启观察为 interrupted，自动续跑未证明；取消前任务提前完成，执行中取消未测。失败/审批/PTY 等主要路径仍缺对照。最初 1 次及后续最多 2 次模型样例授权均已耗尽，余 0；本次新增模型、服务、客户端启动和产品场景执行均为 0。不得从 1216 条规格或源码隔离用例推导产品通过。

完整实现须逐功能验证真实服务后效、状态、失败/取消/恢复和落盘；mock、占位或未决 provider 不计完成。干净环境安装/构建/打包须使用独立应用标识、各数据根、认证来源、资产和更新配置，不读原安装路径；source-build 与预编译依赖分别列明。升级建立新基线，比较入口/条件、协议/通知、schema、依赖修改、运行时能力、资产和平台行为；每项差异回到模块、回归场景及迁移/备份/回退。

下一项定向分析限定为 SD-05 插件配置/安装状态/cache 的权威与根路径，影响 W05/W06/T17：从保存合同及冻结源码分清桌面本地 driver 和 app-server/provider 写入。交付选定域的调用与存储边界、原位置和明确缺失的 provider 即停止该子步；不再重复已经完成的运行时 JS owner 或全量协议盘点。完整目标保持进行中。
