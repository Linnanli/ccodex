固定基线 `codex-26.1007.30912-c5b273322a83` 的普通 composer 静态入口已形成 39 条局部契约、33 个完整 source unit 和 5 条来源限定 import/export 路由。原 36 功能组、旧 8 单位/19 调用及旧 catalog 的 UI-to-operation=0 不变；新静态分母单独计数，运行时 UI→操作关联仍为 0。

提交路径是 X7e 发出的 handleSubmit callback 或 rut 的受条件保护的键盘 callback → Qft.Xl → Mc=Zut.submitComposer → Put/Cdt.local.submit → rpt 提供的 _9e.handleSubmitLocal → source-qualified initial.Tta → shared.KI 所选 RPC 的 getTurnCoordinator/sendMessage。rpt 的 local rZ lazy wrapper 原函数确实返回 Qft；UI 显示、lazy load 成功和事件实际触发仍未知。

KI 会选择 registry.forHost、client.rpc、缓存或 deferred proxy。当前没有把该选择的实际实例接到 Dfn 的 registry population 证据。Dfn 能力链则静态可见：构造 turnCoordinator=dfn(this,...)，cfn.sendMessage → ifn → submissionHost.start/steer → Dfn.startTurn/steerTurn → 既有 Uun/Qun/tdn 契约。ifn 的 resume、pending/active turn、queue/when-idle、steer 失败回 start 与请求线程一致性检查决定分支；steer 意图还可能通过 admissionStart 或 toolOutput 发送 turn/start。这是条件能力链，不是实测 receiver。

取消经过 X7e.stop → xQe 清确认 → Qft.onStop → rpt 去重/isStopping 与错误 toast → source-qualified initial.yda → KI/注入 client.interruptConversation。条件 Dfn 路径区分 follower owner 回退、expected turn、goal pause 时序、turn/interrupt callback 和 descendant cleanup；ordinary composer 未被误接到另一条 stopThread/thread/stop 路径。

状态所有权按来源分开：renderer 管 draft/history/issSubmitting/确认与取消去重；coordinator 管 accepted/queued scheduling；manager 管 conversation、optimistic/unconfirmed turn；通知 reducer 与持久化是独立边界。locallyAccepted/requestDispatched、清空编辑框或返回排队 ID 均未升级为 turn/completed。

证据见 [main.json](main.json)、多来源 [evidence.jsonl](evidence.jsonl) 与校验 [validation.json](validation.json)。全部源文件与定位范围 pin/hash；旧 evidence IDs 只从冻结本地快照选取。实际失败 attempts 保留 source/stdout/stderr/exit，探查诊断中的短 Sentry/通用 disposable helper 片段排除在第一方契约外。未执行目标代码、CLI、UI、目标网络/模型，也未读取个人 profile、凭据或历史。

下一条最有决定性的静态证据是 KI registry/client.rpc 的填充与具体 host/mode 实例绑定；随后才是 callback 对应的具体 DOM/command subscriber，以及与通知/持久化的实例关系。该批不改完整 Codex 目标，也不作独立构建、兼容或升级通过判定。
