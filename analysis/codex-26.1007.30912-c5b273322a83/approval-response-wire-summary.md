# 审批响应封装、宿主接收与后台适配

本批把上轮未明确的 `Pvn` 响应封装接到主进程路由、连接和传输接口，交付6条源码契约、stable/experimental两项协议对照和1项后台适配决定。20项隔离探针通过，包含一次合成串联。

响应先形成 `mcp-response` 的桌面包装：hostId、threadId、response；有跟踪对象时再附 requestMethod/trace。主进程先尝试动态工具响应路由；未命中时按 hostId 查连接并调用 `handleClientResponse(response, threadId)`。保存的构造器、参数和导出关系把此条件路径接到 `mB` 连接和 `MR` delivery，真实实例与原生桥注册尚未观察。

`handleClientResponse` 在等待就绪前清理交互跟踪。就绪失败会广播错误并正常返回，未发送响应；成功后向 delivery 传递响应和独立的 threadId。delivery 对普通主机把变换后的响应序列化为 JSON，再调用传输的 send；durable 走自己的编码与 shared-thread 字段。两个发送层都没有等待下层返回的 Promise。因此，主进程调用完成仍不能作为后台审批确认。

后台适配应回复已有服务端请求 ID，保留 result 的 action/content/_meta；桌面的路由包装与后台结果体分开维护。固定的公开 CLI 0.162.0 与冻结 CLI 的响应 schema 在 stable/experimental 下逐字节相同，服务端请求的有效 schema 也与旧比较一致。这支持复用结果体形状，真实授权、执行绑定、通知和 durable 路径仍需验证，不能据此宣布全部后台兼容。

恢复决定与逐条来源、异常和验收条件见[合同](approval-response-wire-contracts.json)。职责仍接到现有 T03/T04 的审批消费者，没有新增完整功能定义，没有生成客户端或第三方实现。当前120项定义、457条待执行产品规格和覆盖表保持原样；本批产品实测、模型提交和原客户端运行均为0。

本子步骤的源码封装与接收问题已有处理决定。真实传输、实例、后台确认、界面和耐久性继续留在所属模块验收中。下一批回到功能分母：复用保存的工厂与页面绑定，展开 plugins-settings、skills-settings、connections 三个尚未完成操作归属的容器；不再重复追踪本批已经明确的返回语义。
