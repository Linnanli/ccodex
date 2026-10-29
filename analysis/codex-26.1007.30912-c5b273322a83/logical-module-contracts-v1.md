# 逻辑模块合同与维护边界

现有38条提案已统一为37个职责单元；每个单元明确职责、环境、模式、来源、导入、导出、共享状态、副作用、第三方依赖及拟议路径。它们是维护设计，不是恢复出的原作者模块，也不是完整客户端模块分母。

沿用19项源码重叠决定：KI selector只维护一份；Vfn/Sii/loi由domain registry承担；X2t与RPC连接生命周期分开；hXe装配范围不复制给每个provider；runtime policy、service与renderer gate分别维护。

本次将7条runtime/settings建议路径按main/renderer职责放入统一目录。此前已纠正的renderer fetch与main fetch、project跨进程三文件边界继续有效。项目本地delegate的旧待查状态由已保存的来源结论替代，完整集成仍未验证。

|职责单元|拟议维护路径|基础任务|
|---|---|---|
|LM-BOUNDARY-STRUCT-RWC-MANAGER|packages/app-server-client/src/request-manager.ts|W05|
|LM-BOUNDARY-STRUCT-RWC-FETCH|packages/desktop-http-client/src/desktop-fetch.ts|W04|
|LM-BOUNDARY-STRUCT-RWC-RESOLVER|packages/app-host-client/src/request-resolver.ts|W04|
|LM-BOUNDARY-STRUCT-RWC-HOSTED-FILES|packages/app-server-client/src/extensions/hosted-files.ts|W05|
|LM-BOUNDARY-STRUCT-RWC-HOST-TRANSPORT|packages/app-server-client/src/host-connection.ts|W05|
|LM-BOUNDARY-STRUCT-RWC-COORDINATION|apps/desktop/src/main/coordination/socket-client.ts|W04|
|LM-BOUNDARY-STRUCT-RWC-PROJECTS|packages/projects/src/contracts.ts<br>apps/desktop/src/renderer/projects/project-client.ts<br>apps/desktop/src/main/projects/project-service.ts|W06|
|LM-BOUNDARY-STRUCT-CHUNK|packages/desktop-transport/src/chunked-messages.ts|W04|
|LM-BOUNDARY-STRUCT-browser-annotation-lifecycle|apps/desktop/src/browser-preload/annotation/browser-annotation-lifecycle.tsx|W07|
|LM-BOUNDARY-STRUCT-browser-annotation-root|apps/desktop/src/browser-preload/annotation/browser-annotation-root.tsx|W07|
|LM-APPHOST-AH-M01|apps/desktop/src/preload/app-host-bridge.ts|W04|
|LM-APPHOST-AH-M02|apps/desktop/src/main/app-host/connection-handler.ts|W04|
|LM-APPHOST-AH-M03|apps/desktop/src/main/window-services/context-registry.ts|W04|
|LM-APPHOST-AH-M04|apps/desktop/src/main/app-host/service-assembly.ts|W04|
|LM-APPHOST-AH-M05|apps/desktop/src/main/http/http-provider.ts|W04|
|LM-APPHOST-AH-M06|apps/desktop/src/main/http/desktop-fetch.ts|W04|
|LM-APPHOST-AH-M07|apps/desktop/src/main/network/application-network.ts|W03|
|LM-APPHOST-AH-M08|apps/desktop/src/main/network/runtime-startup.ts|W03|
|LM-SOURCE-MODE-TRANSITION|apps/desktop/src/renderer/mode/transition.ts|W07|
|LM-SOURCE-MODE-RESOLVER|apps/desktop/src/renderer/mode/resolver.ts|W07|
|LM-SOURCE-MODE-STATE|apps/desktop/src/renderer/mode/state.ts|W07|
|LM-SOURCE-NATIVE-WINDOW-EVENTS|apps/desktop/src/main/native/window-events.ts|W03|
|LM-SOURCE-NATIVE-NOTIFICATIONS|apps/desktop/src/main/native/notifications.ts|W03|
|LM-SOURCE-NATIVE-APPLE-EVENTS|apps/desktop/src/worker/native/apple-events.ts|W03|
|LM-PROVIDER-provider-lifecycle|apps/desktop/src/renderer/app-host/provider-lifecycle.ts|W04|
|LM-PROVIDER-host-rpc-selector|packages/app-host-client/src/host-rpc-selector.ts|W04|
|LM-PROVIDER-domain-host-registry|packages/app-server-client/src/domain-host-registry.ts|W04|
|LM-PROVIDER-internal-manager-rpc-adapter|apps/desktop/src/renderer/app-host/internal-manager-rpc.ts|W04|
|LM-PROVIDER-host-provided-rpc-adapter|apps/desktop/src/renderer/app-host/host-provided-rpc.ts|W04|
|LM-CONTEXT-HOST-SOURCE-CONTEXT-MODULE-PROPOSAL-001|apps/desktop/src/main/context/source-context.ts|W05|
|LM-RUNTIME-RF-1|apps/desktop/src/main/runtime/runtime-feature-policy.ts|W03|
|LM-RUNTIME-RF-2|apps/desktop/src/main/runtime/runtime-feature-provider.ts|W04|
|LM-RUNTIME-RF-3|apps/desktop/src/renderer/runtime/runtime-feature-gates.ts|W07|
|LM-SETTINGS-0|apps/desktop/src/renderer/settings/asset-registry.ts|W07|
|LM-SETTINGS-1|apps/desktop/src/renderer/settings/page-factory-registry.ts|W07|
|LM-SETTINGS-2|apps/desktop/src/renderer/settings/sections-and-visibility.ts|W07|
|LM-SETTINGS-3|apps/desktop/src/renderer/settings/route-policy-and-renderer.tsx|W07|

## 第三方与接口

仅已有明确边界的objc-js、browser annotation React/DOM和Statsig家族接入对应依赖调查记录。含包候选的bundle不代表每个逻辑模块都直接消费该包；实际锁定版本、修改状态和RPC等opaque helper来源仍需核实。node:async_hooks作为runtime builtin，不新增npm替代实现。

导入字段记录合同输入和共享职责规则；导出字段保留已观察的接口。完整ESM导入导出、所有consumer及运行实例没有被字段齐全所证明；最终类型和新源码命名留给实施阶段依据合同确定。

## 证据格式与分析出口

38条旧unmatched journal补齐verificationStatus，将复合confidence保守规范为inferred；12条main receiver记录补齐基线、来源哈希别名、method和验证状态。原文件、结论及来源坐标保留，规范视图共50条，未增加源码或行为通过项。

本轮关闭37单元字段整合和这50条格式缺口；不能据此关闭整个SD-06或原计划九项标准。后续定向调查转向SD-02的input-shape owner/consumer：已有运行时取舍明确保留这一内部源码缺口，应先追消费者再选平台provider。无需新增客户端或模型调用。

[结构化合同](logical-module-contracts-v1.json)、[职责推断](logical-module-contracts-v1-evidence.jsonl)、[证据规范映射](selected-evidence-schema-normalization-v1.json)。
