# 由已审查契约提出的维护模块边界

基线：`codex-26.1007.30912-c5b273322a83`。11 条局部建议；不表示原作者目录已恢复，也不覆盖全部模块。未生成客户端源码。

| 契约 | 拟维护位置 | 依据与边界 |
| --- | --- | --- |
| RWC-MANAGER | `packages/app-server-client/src/request-manager.ts` | Request scheduling and transport facade；来源范围与未解决项见结构化记录 |
| RWC-SELECTOR | `packages/app-host-client/src/host-selector.ts` | Host-specific service selection；来源范围与未解决项见结构化记录 |
| RWC-FETCH | `apps/desktop/src/main/network/desktop-fetch.ts` | Desktop HTTP transport adapter；来源范围与未解决项见结构化记录 |
| RWC-RESOLVER | `packages/app-host-client/src/request-resolver.ts` | Injected request resolver；来源范围与未解决项见结构化记录 |
| RWC-HOSTED-FILES | `packages/app-server-client/src/extensions/hosted-files.ts` | Hosted-file extension connection；来源范围与未解决项见结构化记录 |
| RWC-HOST-TRANSPORT | `packages/app-server-client/src/host-connection.ts` | Host connection adapter；来源范围与未解决项见结构化记录 |
| RWC-COORDINATION | `apps/desktop/src/main/coordination/socket-client.ts` | Cross-client coordination adapter；来源范围与未解决项见结构化记录 |
| RWC-PROJECTS | `packages/projects/src/project-service.ts` | Project domain and state contracts；来源范围与未解决项见结构化记录 |
| chunk-transport.json | `packages/desktop-transport/src/chunked-messages.ts` | Host-to-view framing, acknowledgement and assembly；来源范围与未解决项见结构化记录 |
| browser-annotation-lifecycle | `apps/desktop/src/browser-preload/annotation/browser-annotation-lifecycle.tsx` | Browser annotation application adapter；来源范围与未解决项见结构化记录 |
| browser-annotation-root | `apps/desktop/src/browser-preload/annotation/browser-annotation-root.tsx` | Browser annotation application adapter；来源范围与未解决项见结构化记录 |

路径由职责和运行边界提出。源范围只作为溯源，不可逐段复制进拟议文件：同一契约可能包含 renderer、main 和共享接口，应在实现阶段按运行环境拆开。mode 均保留 unknown，不能据路径把整个浏览器或网络模块排除。

第三方实现通过依赖导入；第一方封装按契约恢复。项目服务、请求选择器、HTTP、app-server 扩展和协调 socket 分别保留边界，避免把同名 sendRequest 混为一种协议。

Owl、私有后端能力、库版本来源、共享闭包和全功能覆盖仍影响最终项目结构；这些决定未完成前，目录仅作维护建议。原输入哈希、证据 ID、来源范围和每项未知见 module-boundary-proposals.json。升级需重建新基线并比较接口、模式条件、依赖和行为场景。
