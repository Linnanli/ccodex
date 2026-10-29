# 浏览器权限 prompt 合同 v1

已交付 SD-02 / RAM-10 的选定 JS 请求、响应、生命周期与 app partition 来源；原生 provider 尚未取得独立构建资格。原九项完成标准、实施计划 v10 和功能分母不变。

- `ewe` 配置 `persist:codex-browser-app`，注册定制 prompt handler；普通 request/check 默认拒绝。同名固定分区本身不证明客户端数据隔离。
- `kje` → `xje` 管理待处理提示，`jb` 透传 RPC origin；renderer 订阅快照并按 id/tab/conversation/mountGeneration 响应。
- controller 核对当前 owner、页面/线程引用、挂载与 host 代次、renderer 实例及导航版本，拒绝过期响应。跨窗口移动更换快照 ID；mount 同步只更新对应代次。
- 响应同时受 strict schema 与 native 动作/精度集合约束。JS respond 不自行删除 pending；原生 closed 事件驱动清理。过期或隐藏也不等于已经原生 dismiss。
- 订阅 dispose、owner destroyed、RPC broken 和异步 callback rejection 清理副本。同步 callback throw 不在该 Promise catch 的保护内。
- UI 提交按返回值/异常显示失败，非 dismiss 操作受 500ms 阈值限制；dismiss 绕过该阈值。组件与订阅清理已接到具体源码。

维护职责继续采用 RAM-10 的 `packages/contracts/src/runtime/browser-permissions` 与 `packages/runtime-adapter/src/browser-permissions` 建议路径。第三方 Zod 作为依赖，不生成其实现。原生 prompt 构造、closed/响应语义、OS 设置、实际授权与持久化仍需 provider；公开 request/check handler 不能充抵同一协议。

本批核对 27 个源码范围、8 条选定连接，50 项隔离源码用例通过。回放使用自有 EventEmitter、页面/窗口/线程、RPC、时钟及 session 替身，并直接复用冻结 Zod。没有启动客户端、模型或真实服务；不计产品或原生验收。

[完整合同](browser-permission-prompt-v1.json) · [证据记录](browser-permission-prompt-v1-evidence.jsonl) · [回放结果](raw/browser-permission-prompt-v1/replay-results.json)
