# 模块职责归属与任务关联 v1

38 条既有建议已关联到现有基础恢复工作 W03–W07，并整理为 37 组暂定职责：两份 KI host 选择器建议统一为一个实现责任。这里统计的是维护职责，不是已恢复源码模块数。

19 组来源重叠均已有有限设计处置：3 组共享 helper 委托、1 组合并同一 KI 合同、1 组 resolver/调用适配器分工、11 组组装或 import 证据分离、3 组运行时 policy/provider/renderer 分工。完整源码分区与运行效果仍未证明。

具体工程决定：renderer 的 AW/TFt HTTP facade 改放 `packages/desktop-http-client/src/desktop-fetch.ts`；main 的 Ude HTTP 编排保持独立。项目领域按 shared contract、renderer client、main service 分成三个拟议文件。App-host 旧 `src/` 建议统一到 `apps/desktop/src/`。所有路径均为新维护设计。

KI 及相关 provider/manager 职责已条件关联 T03 的已知用户链路。其余职责已明确基础工作归属，并逐项记录所缺的功能消费者证据；没有按名称或同文件批量指定功能。

项目关联核对发现：FSC-0105/T14 已记录“从环境页面添加项目”，本地分支 Ke 的导入绑定到 initial 的 j$t，但到既有 createLocal dialog/service 的目标身份尚待核对。FSC-0045/T05 是 WSL 远程创建；本轮没有新增或合并功能。

| 职责 owner | 基础工作 | 拟议文件 |
| --- | --- | --- |
| LM-BOUNDARY-STRUCT-RWC-MANAGER | W05 | `packages/app-server-client/src/request-manager.ts` |
| LM-BOUNDARY-STRUCT-RWC-FETCH | W04 | `packages/desktop-http-client/src/desktop-fetch.ts` |
| LM-BOUNDARY-STRUCT-RWC-RESOLVER | W04 | `packages/app-host-client/src/request-resolver.ts` |
| LM-BOUNDARY-STRUCT-RWC-HOSTED-FILES | W05 | `packages/app-server-client/src/extensions/hosted-files.ts` |
| LM-BOUNDARY-STRUCT-RWC-HOST-TRANSPORT | W05 | `packages/app-server-client/src/host-connection.ts` |
| LM-BOUNDARY-STRUCT-RWC-COORDINATION | W04 | `apps/desktop/src/main/coordination/socket-client.ts` |
| LM-BOUNDARY-STRUCT-RWC-PROJECTS | W06 | `packages/projects/src/contracts.ts`<br>`apps/desktop/src/renderer/projects/project-client.ts`<br>`apps/desktop/src/main/projects/project-service.ts` |
| LM-BOUNDARY-STRUCT-CHUNK | W04 | `packages/desktop-transport/src/chunked-messages.ts` |
| LM-BOUNDARY-STRUCT-browser-annotation-lifecycle | W07 | `apps/desktop/src/browser-preload/annotation/browser-annotation-lifecycle.tsx` |
| LM-BOUNDARY-STRUCT-browser-annotation-root | W07 | `apps/desktop/src/browser-preload/annotation/browser-annotation-root.tsx` |
| LM-APPHOST-AH-M01 | W04 | `apps/desktop/src/preload/app-host-bridge.ts` |
| LM-APPHOST-AH-M02 | W04 | `apps/desktop/src/main/app-host/connection-handler.ts` |
| LM-APPHOST-AH-M03 | W04 | `apps/desktop/src/main/window-services/context-registry.ts` |
| LM-APPHOST-AH-M04 | W04 | `apps/desktop/src/main/app-host/service-assembly.ts` |
| LM-APPHOST-AH-M05 | W04 | `apps/desktop/src/main/http/http-provider.ts` |
| LM-APPHOST-AH-M06 | W04 | `apps/desktop/src/main/http/desktop-fetch.ts` |
| LM-APPHOST-AH-M07 | W03 | `apps/desktop/src/main/network/application-network.ts` |
| LM-APPHOST-AH-M08 | W03 | `apps/desktop/src/main/network/runtime-startup.ts` |
| LM-SOURCE-MODE-TRANSITION | W07 | `apps/desktop/src/renderer/mode/transition.ts` |
| LM-SOURCE-MODE-RESOLVER | W07 | `apps/desktop/src/renderer/mode/resolver.ts` |
| LM-SOURCE-MODE-STATE | W07 | `apps/desktop/src/renderer/mode/state.ts` |
| LM-SOURCE-NATIVE-WINDOW-EVENTS | W03 | `apps/desktop/src/main/native/window-events.ts` |
| LM-SOURCE-NATIVE-NOTIFICATIONS | W03 | `apps/desktop/src/main/native/notifications.ts` |
| LM-SOURCE-NATIVE-APPLE-EVENTS | W03 | `apps/desktop/src/worker/native/apple-events.ts` |
| LM-PROVIDER-provider-lifecycle | W04 | `apps/desktop/src/renderer/app-host/provider-lifecycle.ts` |
| LM-PROVIDER-host-rpc-selector | W04 | `packages/app-host-client/src/host-rpc-selector.ts` |
| LM-PROVIDER-domain-host-registry | W04 | `packages/app-server-client/src/domain-host-registry.ts` |
| LM-PROVIDER-internal-manager-rpc-adapter | W04 | `apps/desktop/src/renderer/app-host/internal-manager-rpc.ts` |
| LM-PROVIDER-host-provided-rpc-adapter | W04 | `apps/desktop/src/renderer/app-host/host-provided-rpc.ts` |
| LM-CONTEXT-HOST-SOURCE-CONTEXT-MODULE-PROPOSAL-001 | W05 | `apps/desktop/src/main/context/source-context.ts` |
| LM-RUNTIME-RF-1 | W03 | `runtime/runtime-feature-policy.ts` |
| LM-RUNTIME-RF-2 | W04 | `runtime/runtime-feature-provider.ts` |
| LM-RUNTIME-RF-3 | W07 | `renderer/runtime-feature-gates.ts` |
| LM-SETTINGS-0 | W07 | `settings/asset-registry.ts` |
| LM-SETTINGS-1 | W07 | `settings/page-factory-registry.ts` |
| LM-SETTINGS-2 | W07 | `settings/sections-and-visibility.ts` |
| LM-SETTINGS-3 | W07 | `settings/route-policy-and-renderer.tsx` |

373 项功能、48 组功能任务、1216 条未执行场景规格及原九项完成标准保持原状态。未运行原客户端、调用模型或生成客户端/第三方实现。下一项是补齐 FSC-0105 本地委托与 createLocal 的准确来源关系。
