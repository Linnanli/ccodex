# 连接状态选择器、启动请求与迟到返回

本批接上上一轮远程状态生产端的renderer使用路径。结论见[20条限定合同](remote-status-consumer-contracts.json)、[证据行](remote-status-consumer-evidence.jsonl)、[24项隔离观察](remote-status-consumer-observations.json)、[8条待执行场景](remote-status-consumer-scenarios.json)与[来源索引](remote-status-consumer-provenance.json)。

**a8a是状态聚合选择器，启动effect才发送状态请求。** t8a将描述符映射为hostId，经i8a.default后传给Zs(a8a,n)。a8a回调逐host读取Vs；11条按模块/导出/词法绑定连接确认Vs→SF→xF.state$。s8a只保留connected项，p8a随后选择主机。列表未知和已知空列表的回退不同。外部normalizer的准确包/版本与完整语义仍未知，本批没有将其猜成uniq，也没有执行其实现。

xF初始state为disconnected、error为null；progress由默认null的独立Loi保存。Zs的React/scope读取、订阅与retain适配，和Ih的60000ms默认autoDispose均有源码；真实provider及生命周期没有执行。不能由selector读到值就证明后端已连接或真实订阅已送达。

ERs effect先登记合格host并安装manager watch，再保存state/error/progress快照，调用yo(app-server-connection-state,{params:{hostId}})。host-backed缺key时跳过。yo/$G→yDn把host参数编码为JSON并向vscode://codex/app-server-connection-state发送；source/signal/priority与可选select保持各自位置。实际AW bridge实例和接收投递仍待验证。

main对象属性位于$L，async arrow将hostId原样交给remoteConnectionsHandler。hXe创建$L时第6实参是自身remoteConnectionsHandler，$L第6形参o直接保存；结合上一批hXe→fKe连接，所选静态服务身份已接上。fKe端点读取registry state/progress/error，缺失返回disconnected/null/null。真实hXe/$L构造与IPC没有在本批运行。

| 返回条件 | 所选代码行为 |
| --- | --- |
| effect和manager有效，三项快照均严格相同 | 先写progress，再写state/error |
| state/error/progress任一项改变 | 忽略迟到返回；error对象比较身份 |
| manager替换、host删除或effect清理 | 忽略旧返回 |
| 初始manager为null | 接纳第一次观察到的非空身份，之后的替换使请求失效 |
| active请求失败 | 调用Fn并warning；保留已有state/error/progress |
| stale请求失败 | warning，不调用Fn |

Fn接到xoi，只把默认false的CF标志设为true；它没有清空连接状态，CF的完整产品含义仍待其余消费者核对。boi在state不是connecting时清progress，因此connected返回先写入的progress会再次清空；connecting返回保留它。若progress已写而后续query/telemetry/状态helper同步失败，catch仍可写CF，不能按原子提交恢复。

cleanup关闭存活标志、注销watch并dispose所选历史请求；本次yo没有传signal，cleanup也没有直接取消该请求。忽略迟到返回与真实transport取消是不同验收项。自动连接/历史刷新另受live、f、autoConnect、授权、候选集合和PRs条件限制，不能用它们概括前面的全部状态请求。

一次Node22 VM命令加载21个保存单位4671字节，24场景通过，涵盖聚合/筛选、快照身份、manager变化、cleanup、失败保留、progress顺序、URI编码和main endpoint。React/compiler、scope工厂、normalizer、manager/watch、transport以及query/telemetry副作用均为明确替身；没有真实窗口、React hooks、IPC、网络、账户或模型任务。8条真实集成规格未执行。

本批5次完整Program解析覆盖initial/shared/main三个固定文件，保存70个完整AST单位（1继承）、958个去重词法位置及11条合格导入导出关系。没有新REA命令；原REA partial/unknown边界保持，AST连接不等于REA完整语义覆盖。

拟维护职责为renderer状态族、bootstrap生命周期、URI请求适配和main薄端点，路径与来源见合同。当前关闭的是所选状态聚合、启动seed方法/参数和服务端点的静态缺口；接下来需补后续连接事件写入者、真实provider/bridge及normalizer依赖来源。原37功能/40用户操作/5机制/26队列/160未执行功能规格、967未映射旧入口和337 deferred保持，mode unknown与确认排除0不变，完整功能分母未知。本组模型样例2/2已用、余0，本批新增0，整体分析未完成。
