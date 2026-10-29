# 核心功能粒度与当前有限清单

本批为已有本地提交、普通停止和MCP电脑应用审批新增FSC-0035至FSC-0037三个baseline-local功能定义。当前有限清单累计37项，关联40个用户操作、5个机制支撑，另26个候选继续排队，三类合计覆盖原71操作。完整产品功能分母仍未知。见[本批分析](core-feature-scope.json)、[当前有限清单JSON](feature-scope-current.json)、[CSV](feature-scope-current.csv)、[160条待执行规格](feature-scope-current-scenarios.json)、[36条作者推断记录](core-feature-scope-evidence.jsonl)及[来源](core-feature-scope-provenance.json)。没有新增运行、审批决定或模型提交。

| 新功能ID | 用户目标 | 关联的直接操作 | 仍待闭合 |
| --- | --- | --- | --- |
| FSC-0035 | 向已有本地对话提交消息 | renderer-existing-local-submit | 实际目标／scope／host、KI选支、送达、队列及耐久状态 |
| FSC-0036 | 停止已有本地对话的当前执行 | ordinary-local-cancel | 真实stop按钮和同turn绑定、下游结果、native及重开后的状态来源 |
| FSC-0037 | 决定MCP电脑应用使用请求 | accept-session-or-null、accept-always、decline | 实际请求生产条件／模式、receiver、响应确认、安全规则及持久化 |

这三个定义采用用户目标与有条件的入口契约。已有本地提交与新建对话、cloud、worktree保持各自范围；本批不声称后者已分析完成。提交链把draft／UI ownership、局部接纳、队列、start／steer和最终完成分开。普通stop未传expectedTurnId，不能从确认框里的turnId推断wire有该参数；goal暂停失败后可能已中断，后续异常也不等于可以重发。

三个审批动作归于一次应用使用决定，保留各自action／persist条件与响应，不称操作等价。主动作仅在支持session时发送session，否则null；always取决于对应选项；拒绝是decline。accept先写曾批准atom，所选rejection分支只按当前request key恢复ref/loading，没有回滚atom。此定义只覆盖mcpServerElicitation中经browser优先分支后选中的电脑应用卡片，不覆盖command／file审批、permissionRequest或整个审批组。ChatGPT文案和computer-use名字均未用于模式排除。

原33个非设置候选全部经过本批作者的有限粒度审阅：5个分配为直接用户操作；turn/start、turn/steer、turn/interrupt、conditional-Dfn-capability和一条源中断状态表示共5个保留为机制支撑。它们的关联不穷尽所有调用方，也不是“一种协议方法等于一种feature”。尤其notification目录中的turn/interrupt记录描述源码状态转移，不能当成已经收到某个通知。

另23个非设置候选仍排队：thread start／resume／fork／archive四项缺具体用户消费者，thread/started、turn/started、turn/completed、error四项缺状态到实际展示目标的连接，14个电脑使用query／service包装缺真实设置控件与模式条件，一个项目能力派生条件缺父动作。加上原两条设置只读facet和一条WSL多动作卡，共26队列。所有候选仍保留在产品调查范围，没有被当作“不存在”或排除。

本批新增20条未执行规格，逐操作覆盖success／failure／cancel／restore，并保留旧140条；累计160条执行数仍为0。每条包含精确条件、参数状态引用、源合同及预期限度。此前[34个中断VM场景](interrupt-control-flow-summary.md)只支持指定替身下的函数条件，[SIGTERM重启观察](behavior-stop-restart.json)只支持绑定UI中的同turn interrupted；两者都没有覆盖真实stop控制和完整功能验收。已有两条模型样例组已消耗2／2、剩余0，本批没有使用或扩充授权。

本批新读取并核对6个冻结Program文件、84个唯一范围、223个metadata pointer／JSONL line，涵盖选定composer、provider、approval及interrupt单位。没有新解析Program或运行REA，词法和语义关系仍沿用已引用的有限REA／AST补充合同；字节校验不是新的独立语义审查。首轮结果使用概念性数组pointer引用JSONL记录，第二轮改为显式line locator；两个版本的工具、元数据和完整命令捕获均保留，当前交付使用第二轮。

原FSC-0001至0034及140规格逐对象保持；当前读者以37／40／5／26／160替代旧34／35／36／140的当前有限视图，旧文件作为不可改写的历史快照继续保留。37项仍全部mode unknown，confirmed排除0；36旧大组是另一粒度，不能相加。968旧入口仍只有一个设置容器部分关联、967未映射、0完全解析；composer命令标签尚未证明与这些回调同一身份，因此本批没有虚增旧入口覆盖。337 deferred没有消解。

后续先接队列项的真实消费者和模式／依赖条件，再扩展细粒度功能及模块恢复表。source→条件→操作→用户目标→验收可作为恢复顺序的依据；本批没有生成客户端源码或第三方实现，也没有把条件机制包装成已可独立构建的功能。
