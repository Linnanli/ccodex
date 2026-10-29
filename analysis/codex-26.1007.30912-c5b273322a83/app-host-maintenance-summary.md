# App-host 可维护重建职责建议（proposal/inferred）

基线 codex-26.1007.30912-c5b273322a83。仅使用 preload-app-host、host-http-service、app-host-context、application-network 四份冻结分析及其精确 journal/primary producer 原字节。26 项建议均标为 proposal、confidence=inferred；运行未验证、模式 unknown、确认排除0。新目录建议不代表原始目录已经恢复。

范围为8个职责模块、6个接口、5个依赖边界、7个未来迁移验证计划；复用 71 条旧 journal 原始记录并继承7个目标source pins。本轮目标源码读取0、AST0、新source证据0、执行/网络/UI/模型/凭据/history均0。24个冻结artifact input pins及4个primary producer的实际原字节哈希固定；不运行旧producer。

| 建议模块 | 拟定路径 | 主要职责 |
| --- | --- | --- |
| AH-M01 Preload app-host bridge | src/preload/app-host-bridge.ts | 接收窗口 message，并通过注入 IPC adapter 转发所选 port；将 channel/envelope 和 transfer list 合同集中管理。 |
| AH-M02 Main connection and remote view lifecycle | src/main/app-host/connection-handler.ts | 组装注入的 event predicate、context resolver、port/RPC adapter 和 remote view 生命周期，保持连接入口独立。 |
| AH-M03 Window context registry and sender predicate | src/main/window-services/context-registry.ts | 分别管理 context slot/窗口注册生命周期与 sender/frame predicate，并通过 WindowServices 注入连接入口。 |
| AH-M04 App-host service assembly | src/main/app-host/service-assembly.ts | 仅在 composition root 创建所需 provider 并显式组装 host services，将依赖与 disposal hook 注入。 |
| AH-M05 HTTP provider request lifecycle | src/main/http/http-provider.ts | 管理 request id 到 AbortController 的映射、cancel/dispose、callback 调用与 Response bridge 清理。 |
| AH-M06 Desktop HTTP orchestration | src/main/http/desktop-fetch.ts | 集中 URL/body/header、destination guards、auth/workspace/retry、response/error normalization；网络与身份/helper 通过依赖注入。 |
| AH-M07 Application network policy and native adapter | src/main/network/application-network.ts | 围绕显式 policy state 管理 readiness/generation/refresh/session restrictions，再把 fetch/request 委托给 native runtime adapter。 |
| AH-M08 Requirements startup and runtime capability adapter | src/main/network/runtime-startup.ts | 分开 requirements/config 获取、临时 transport lifecycle、schema boundary 与 Node permission/relaunch capability，以 adapter 限制运行时耦合。 |

这些路径均为新设计选择。preload/main bridge 负责连接与port边界；WindowServices 拆开context/registry与sender predicate；service assembly 显式注入provider；HTTP provider 管id/abort/cleanup，desktop fetch管request/error/progress；network与runtime startup分开policy/readiness和native/transport能力。

拟定接口分别覆盖 WindowPort/Connection、WindowServices、方向明确的HostTarget/RemoteViewPeer、HTTP provider LegacyResult、ApplicationNetwork/ClientRequest接缝、Requirements/RuntimeStartup ports。使用opaque类型保留尚未恢复的协议与helper，不伪造完整wire schema。每条接口和模块在主JSON中关联精确原journal记录及source locator。

保留的迁移细节：HostTarget.services 与 remote view services 方向不同；context setter不能简化为纯赋值，它涉及注册副作用；membership不等于sender predicate，file URL startsWith不是精确pathname。HTTP URL/log/timing预处理在try外，progress先Buffer.concat后返回，cancel/cleanup的id语义不能自动升级为唯一性或完整流式保证。

网络层保留loading/ready/failed、generation/refresh、session/redirect/dispose。native Electron IPC/net/session、Owl permission/relaunch、RPC/base、schema/version helpers及auth/header/error/stream seams由窄adapter承接。RPC/helper归属未知，不一概称第三方；electron声明42.3.0不证明安装版本或stock兼容。本提案不生成任何依赖完整实现。

迁移验证计划均executionStatus=not-run：版本化有限合同台账→自建port和服务方向fixture→context/registry/frame/URL生命周期fixture→provider abort/cleanup与重复id场景→HTTP错误/try边界/progress buffering→network状态/generation/session fixture→另行定向native与opaque RPC兼容矩阵。当前没有执行这些测试。

原外层binding、dynamic registry、真实context/peer/sender/delivery、账户/backend/session值、native兼容、运行表现、所有consumer、模式和旧历史间接pin漂移继续unknown。属性、域名和chunk/class命名不作为ChatGPT-only排除依据。

evidence.jsonl只拼接既有记录原字节，来源journal line/record-byte range/hash与source span或JSON pointers位于evidenceReferences。sourceInputs是继承的精确元数据，目标源未重新读取/哈希；建议不是新的源码确认。
