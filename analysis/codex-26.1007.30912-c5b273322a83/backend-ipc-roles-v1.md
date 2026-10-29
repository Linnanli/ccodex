# 后台请求与 IPC 的恢复决定

本批将原有 91 条后台候选和 50 条 IPC 候选接到冻结源码中的完整调用或通道位置。没有增加功能定义、运行通过数或模型提交。

91 条调用对应 52 个方法：5 条在选定 mB class 内明确调用同 class 的 sendAppServerRequest 定义，其余 86 条的参数、字段或调用结果来源已记录，实际注入实例仍未知。不能将这些记录直接解释为 91 项功能或已确认送达的后台调用。

## 公开后台的采用边界

固定公开 CLI 0.162.0 与随包 CLI 的既有导出比较中，这 52 个方法的 experimental 有效 schema 均相同；43 个也在 stable 中相同。9 个非 stable 方法为 project/delete、project/list、project/move、project/read、project/update、remoteControl/enable、rollout/compress、thread/realtime/stop、thread/settings/update。

决定：公开 app-server 可作为这些请求合同的适配候选，9 个非 stable 方法须单列服务和启用条件。schema 相同不证明动态参数均合法、实际服务支持或成功后效；全协议 466 变体中的 11 组差异仍保留。

## 连接适配器必须保留的行为

- 初始化/重连等待和退出/失败条件、发送前钩子、请求 id、pending 关联、认证与 trace。
- 默认 30 秒超时及 null 关闭定时器、onSettled、传输 cancelRequest 钩子与发送失败清理。
- 条件性的 thread/start、thread/fork 超时晚到响应清理；不能统一为立即删除 pending。
- 配置成功处理、Chronicle 协调、归档/预热/观察/广播，以及内部请求、窗口/host 请求和合并等待者的分流。

传输取消不等于用户任务取消。VL/o.S 的完整错误和值变换、RL 的 tracing 选择集合及实际 transport/provider 不在本批闭合范围。

## IPC 不是用户功能清单

50 条记录分为 41 条通道常量、4 条参数化通道名生成函数、3 条 API 参数和2 条事件通道判断分支。前45条归入传输支持声明，避免按重复通道制造功能。四个完整 IPC Program 和 ICe 函数中的36处 API 使用已登记；不代表完整 main/worker 消费者覆盖。

两个浏览器策略查询已形成源级协议配对：browser preload 的 sendSync 对应 main WebContents 的 ipc-message-sync 通道判断。保留同步查询、returnValue 和平台分支；实际对象、触发和返回效果未观察。connect-app-host 继续沿用已验证来源的 MessagePort/trust/context/App-host 服务合同，httpFetch 不并入 app-server request port。

恢复源码职责据此分为 IPC 合同、preload bridge、main browser policy、app-server connection 和 App-host connection；标准 Electron 与第三方库通过依赖提供。本批没有生成客户端实现。

当前[旧入口 v4](legacy-entry-dispositions-v4.json)仍保留全部968个 ID，253条待源码角色处置；完整功能解决数仍为0。373项功能、48任务及1216条未执行规格保持原定义，由当前 overlay 更新入口与协议决定。

明细：[来源、请求合同和维护决定](backend-ipc-roles-v1.json)、[九字段证据](backend-ipc-roles-v1-evidence.jsonl)。下一步处置剩余路由/导航/快捷键入口的支持、容器与用户操作角色，并连接既有功能，避免重做后台/IPC枚举。
