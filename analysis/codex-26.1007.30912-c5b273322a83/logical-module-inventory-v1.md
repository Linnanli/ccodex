# 已有逻辑模块建议统一清单 v1

本次将七组既有建议的 38 条记录整理为统一视图。38 是建议记录数；存在源码重叠，不能称为 38 个独立恢复模块。

每条记录保留职责、来源环境与拟议运行位置、模式、源码范围、输入接口、输出接口、共享状态、副作用、第三方边界及拟议路径。完整导入/导出闭包和实际运行结果仍未知。

438 条发布文件记录保持原样。373 项功能、48 组恢复任务和 1216 条未执行场景规格保持原样。没有生成客户端代码或第三方实现。

| 建议记录 | 职责 | 拟议路径 |
| --- | --- | --- |
| LM-BOUNDARY-STRUCT-RWC-MANAGER | Request scheduling and transport facade | `packages/app-server-client/src/request-manager.ts` |
| LM-BOUNDARY-STRUCT-RWC-SELECTOR | Host-specific service selection | `packages/app-host-client/src/host-selector.ts` |
| LM-BOUNDARY-STRUCT-RWC-FETCH | Desktop HTTP transport adapter | `apps/desktop/src/main/network/desktop-fetch.ts` |
| LM-BOUNDARY-STRUCT-RWC-RESOLVER | Injected request resolver | `packages/app-host-client/src/request-resolver.ts` |
| LM-BOUNDARY-STRUCT-RWC-HOSTED-FILES | Hosted-file extension connection | `packages/app-server-client/src/extensions/hosted-files.ts` |
| LM-BOUNDARY-STRUCT-RWC-HOST-TRANSPORT | Host connection adapter | `packages/app-server-client/src/host-connection.ts` |
| LM-BOUNDARY-STRUCT-RWC-COORDINATION | Cross-client coordination adapter | `apps/desktop/src/main/coordination/socket-client.ts` |
| LM-BOUNDARY-STRUCT-RWC-PROJECTS | Project domain and state contracts | `packages/projects/src/project-service.ts` |
| LM-BOUNDARY-STRUCT-CHUNK | Host-to-view framing, acknowledgement and assembly | `packages/desktop-transport/src/chunked-messages.ts` |
| LM-BOUNDARY-STRUCT-browser-annotation-lifecycle | Browser annotation application adapter | `apps/desktop/src/browser-preload/annotation/browser-annotation-lifecycle.tsx` |
| LM-BOUNDARY-STRUCT-browser-annotation-root | Browser annotation application adapter | `apps/desktop/src/browser-preload/annotation/browser-annotation-root.tsx` |
| LM-APPHOST-AH-M01 | 接收窗口 message，并通过注入 IPC adapter 转发所选 port；将 channel/envelope 和 transfer list 合同集中管理。 | `src/preload/app-host-bridge.ts` |
| LM-APPHOST-AH-M02 | 组装注入的 event predicate、context resolver、port/RPC adapter 和 remote view 生命周期，保持连接入口独立。 | `src/main/app-host/connection-handler.ts` |
| LM-APPHOST-AH-M03 | 分别管理 context slot/窗口注册生命周期与 sender/frame predicate，并通过 WindowServices 注入连接入口。 | `src/main/window-services/context-registry.ts` |
| LM-APPHOST-AH-M04 | 仅在 composition root 创建所需 provider 并显式组装 host services，将依赖与 disposal hook 注入。 | `src/main/app-host/service-assembly.ts` |
| LM-APPHOST-AH-M05 | 管理 request id 到 AbortController 的映射、cancel/dispose、callback 调用与 Response bridge 清理。 | `src/main/http/http-provider.ts` |
| LM-APPHOST-AH-M06 | 集中 URL/body/header、destination guards、auth/workspace/retry、response/error normalization；网络与身份/helper 通过依赖注入。 | `src/main/http/desktop-fetch.ts` |
| LM-APPHOST-AH-M07 | 围绕显式 policy state 管理 readiness/generation/refresh/session restrictions，再把 fetch/request 委托给 native runtime adapter。 | `src/main/network/application-network.ts` |
| LM-APPHOST-AH-M08 | 分开 requirements/config 获取、临时 transport lifecycle、schema boundary 与 Node permission/relaunch capability，以 adapter 限制运行时耦合。 | `src/main/network/runtime-startup.ts` |
| LM-SOURCE-MODE-TRANSITION | Mode transition guard and ordered state writes; retain supplied store and atoms. | `apps/desktop/src/renderer/mode/transition.ts` |
| LM-SOURCE-MODE-RESOLVER | Access-sensitive mode resolution, including persisted value passthrough. | `apps/desktop/src/renderer/mode/resolver.ts` |
| LM-SOURCE-MODE-STATE | Selected state declarations/initialization; actual store/provider ownership remains unresolved. | `apps/desktop/src/renderer/mode/state.ts` |
| LM-SOURCE-NATIVE-WINDOW-EVENTS | First-party window scroll monitor registration and normal-path removal. | `apps/desktop/src/main/native/window-events.ts` |
| LM-SOURCE-NATIVE-NOTIFICATIONS | First-party notification permission callback, center cache and RunLoop reference management. | `apps/desktop/src/main/native/notifications.ts` |
| LM-SOURCE-NATIVE-APPLE-EVENTS | First-party Apple Event wrapper factories; no event execution proven. | `apps/desktop/src/worker/native/apple-events.ts` |
| LM-PROVIDER-provider-lifecycle | 组件所属 scope、effect 安装与清理；registry 存在性选择分支。 | `apps/desktop/src/renderer/app-host/provider-lifecycle.ts` |
| LM-PROVIDER-host-rpc-selector | primary forHost、client.rpc、缓存、延迟 RPC 及退役条件。 | `packages/app-host-client/src/host-rpc-selector.ts` |
| LM-PROVIDER-domain-host-registry | X3 注册、条件 Sii 创建、N3 发布／替换／删除及 disposal。 | `packages/app-server-client/src/domain-host-registry.ts` |
| LM-PROVIDER-internal-manager-rpc-adapter | 捕获 manager、MessageChannel、manager／coordinator facade 的原参数转发及重连清理。 | `apps/desktop/src/renderer/app-host/internal-manager-rpc.ts` |
| LM-PROVIDER-host-provided-rpc-adapter | ready manager RPC 的 duplicate、watch、lease、connection 替换与清理。 | `apps/desktop/src/renderer/app-host/host-provided-rpc.ts` |
| LM-CONTEXT-HOST-SOURCE-CONTEXT-MODULE-PROPOSAL-001 | First-party source-context forwarding and lifecycle adapter for known main-process consumers. | `apps/desktop/src/main/context/source-context.ts` |
| LM-RUNTIME-RF-1 | Allowlisted boolean merge/cache, auth owner and generation invalidation | `runtime/runtime-feature-policy.ts` |
| LM-RUNTIME-RF-2 | Expose runtime feature capabilities through the app-host service boundary | `runtime/runtime-feature-provider.ts` |
| LM-RUNTIME-RF-3 | Ready/evaluation context checks and runtime-feature gate dispatch | `renderer/runtime-feature-gates.ts` |
| LM-SETTINGS-0 | Preserve the descriptor table and accessor/initializer wiring as a shared source contract, with imported providers represented by explicit external dependencies. This is asset registration, not the implementation of53 settings workflows. | `settings/asset-registry.ts` |
| LM-SETTINGS-1 | Restore table keys, reference/loader wiring and explicit external interfaces. Import specifiers and construction records identify implementation targets to investigate; they do not reconstruct each target page or prove delivery. | `settings/page-factory-registry.ts` |
| LM-SETTINGS-2 | Preserve section data, explicit export/import relation and predicate source boundaries. Treat auth/platform/capability/config and second/third-parameter values as injected context; retain pending/error and switch fall-through semantics. | `settings/sections-and-visibility.ts` |
| LM-SETTINGS-3 | Restore the single route construction and ordered redirect/lookup branches as a routing contract. Preserve search/hash/state and the recorded mode query write, with navigation and helper results as external interfaces. | `settings/route-policy-and-renderer.tsx` |

已列出 19 组具有重叠来源范围的建议，逐组关系见 JSON 的 `sourceOverlapReviews`。范围相交只证明证据重叠，不能自动合并模块。

明确保留的差异：RWC-FETCH 的既有拟议 main 路径与 renderer 来源分类需要复核；项目领域和 chunk 传输跨多个运行环境，应区分共享合同与各进程适配器；host-provided RPC 的最新条件化 main 来源关系已引用，实际实例仍未知。

第三方处理沿用包导入、原生运行时适配器和未知 helper 的边界。未把依赖注入对象一律判为第三方；未宣称版本锁定、原生兼容或完整可重建。App-host 旧间接输入 pin 漂移仍保留为限制。

下一项工作是处理清单内的来源重叠，并将职责关联到现有恢复任务。当前只关闭“这些既有建议缺少统一字段视图”这一子项；原计划九项完成条件不变，整体分析未完成。
