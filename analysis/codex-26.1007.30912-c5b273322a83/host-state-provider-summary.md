# 主机选择、共享快照与状态更新

Q6已连接到主机选择hook p8a；共享配置的NI订阅、preload缓存和首次快照IPC channel也已分别定位。见[28条限定合同](host-state-provider-contracts.json)、[证据行](host-state-provider-evidence.jsonl)、[26项隔离观察](host-state-provider-observations.json)、[8条待执行UI规格](host-state-provider-scenarios.json)和[完整归档索引](host-state-provider-provenance.json)。本批补充固定基线的完整Program作用域分析，没有新的REA执行；上一批REA语义unknown与8815未知项保持。

| 状态层 | 已确认的源码行为 | 仍未知 |
| --- | --- | --- |
| 所选主机p8a | 插件host、settings query、h8a依次取候选；按访问资格及连接状态选择ID | 实际React provider、连接查询Zs/a8a及dNn合并规则 |
| 共享对象NI | 从快照取初值，按键订阅更新；setter先登记历史，再发送，最后写本地值 | 真实store实例、消息送达及跨窗口一致性 |
| preload快照A | 同步IPC取初值；shared-object-set先更新A再invoke | 真实IPC成功／失败与上层恢复策略 |
| main共享仓库wee | 内存对象、浅快照、同步订阅通知；所选构造初始化Local配置 | MMe与hXe的仓库注入是否同实例、上游持久化 |

p8a的插件详情hostId优先且未在此trim；只有settings路径才读取并trim query hostId，空字符串经||回退h8a。访问条件Ge来自shared.AAt→ejn，沿用此前pq本地访问资格；它不是home composer的chat/work偏好。连接数据或状态尚未得到时s8a返回undefined，u8a会保留未知候选；得到列表后，候选不在connected列表且不是local才回退local。这与后续pzt描述符的未知ID回退是两个状态层。

h8a由fd(q,as)创建，fd经shared.don连接Uk signal工厂，此调用没有传持久化key；不能据此认定它已经落盘，实际scope/store和存储策略仍未知。setter先store.set(h8a,id)，再更新路由：插件详情跳回/settings/plugins-settings并replace；普通settings仅在query已有hostId时修改，不额外创建该参数。后续同步导航异常不会在所选函数内回滚已经完成的状态写入。

NI的初始化器通过可选bridge getter读取快照。onMount先登记shared-object-updated listener，再发送subscribe；清理先退listener再发unsubscribe。izt先调用历史管理替身对应的tRt，随后dispatch shared-object-set，最后e.set；Object.is相等只跳过历史项，仍发送和更新。Hf/Vf/ire继续连接可选electronBridge及window事件；bridge返回Promise的catch处理不能证明main已经收到或保存。

preload的A由sendSync(codex_desktop:get-shared-object-snapshot)??{}初始化；getter直接读A[key]。发送shared-object-set时先更新A，再await ipcRenderer.invoke；所选函数没有失败回滚。接收非chunked的shared-object-updated也先更新A，再派发window MessageEvent。这里确认的是源代码顺序，没有新增真实Electron或IPC观察。

首次快照注册者为main.$Xe，使用g.kt；g require bootstrap，而bootstrap实际exports.kt=Pt，Pt才是快照channel字面值。callback先调用isTrustedIpcEvent，拒绝时返回{}，否则调用getContextForWebContents(sender)?.getSharedObjectSnapshot()??{}。hXe的同名方法委托其仓库getSnapshot。实际$Xe调用参数、context resolver实例及与MMe仓库的注入连接仍需核对，不能以同名字段代替同实例证明。

wee小类本身没有持久化I/O：undefined删除，其他值赋入，随后同步通知；listener抛错会在值已改变后中断后续listener。所选hXe构造new wee，并以startup.m初始化host_config；该导出getter连接$r={id:local,display_name:Local,kind:local}。另保存SSH／WSL／remote-control的set调用位置及SSH空数组初始化，但只覆盖完整调用范围，没有推断整套发现、保存或远程连接机制。MMe的subscribe按sender/key引用计数并立即发送当前值，unsubscribe减计数，destroyed清理；实际外层接收器验证与实例仍未观察。

一次Node22 VM命令加载9个保存单位共2243字节，含7函数、1类及1工厂赋值；26项合成场景全部通过。覆盖候选优先级、trim、连接缺失／断开、状态先写后导航及异常、快照初值、订阅／清理顺序、函数更新、相等值仍发送、仓库删除／浅拷贝和listener异常。router/access/store/status/memo/bridge/history均为明确替身，原t8a查询、Uk、Vf、preload及真实IPC未执行；没有客户端启动、设置修改或模型提交。这些结果不升级真实功能验收。

六条分析命令共完成14次完整Program解析，涉及6个不同源码文件。形成26条源码事实／2条设计推断，75个去重规范AST单位（长度合计12450字节，含重叠）、328处词法位置及9项跨模块连接。作者字节核对检查8源码文件、5153个唯一范围和13008次坐标出现，原始79个保存选段与规范75单位均一致；这不是新增独立语义审查。

source-05曾按未限定名称误选7144字节QXe，已从规范合同剔除；bootstrap的defineProperty导出搜索为空，也未作为不存在channel的证据。source-06改按真实getSharedObjectSnapshot callee和exports.kt=Pt赋值定位。两项派生候选错误、原文件和完整执行记录均保留；没有重跑26项VM观察来改写历史结果。

重建工程可按主机选择与路由、连接状态过滤、共享订阅桥和主进程内存仓库划分职责。合同中的features/hosts、platform/shared-objects、services/shared-objects只是维护设计建议，并非找回原作者目录。React、路由、状态和Electron实现通过依赖引入；上游持久化应另立明确合同，不能把内存仓库替换成任意文件存储后宣称等价。

原37项有限功能、40用户操作／5机制／26队列、160条未执行功能规格、967未映射旧入口及337 deferred保持。新增8条UI规格全部未执行且单独计数，模式归属与确认排除仍未增加。获批模型样例组2/2已使用、剩余0；停止／重启的既有interrupted观察保留。本批收窄provider与配置来源缺口，下一步应继续核对仓库构造注入和连接状态查询，再决定哪些行为能够独立重建；完整功能分母和总体分析目标仍未闭合。
