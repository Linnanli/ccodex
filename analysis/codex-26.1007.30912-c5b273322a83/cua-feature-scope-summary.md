# 电脑使用设置的功能归属与恢复验收

当前有限功能视图更新为[44项功能JSON](feature-scope-v2.json)、[CSV](feature-scope-v2.csv)与[192条未执行规格](feature-scope-v2-scenarios.json)。[本批分析](cua-feature-scope.json)将已有消费者证据落实为7个用户目标，把原14个CUA候选分成8个用户写操作和6个查询／搜索支撑；待审队列由26降为12。三类仍覆盖相同71个候选：48用户操作、11机制、12队列。没有新增真实运行或模型任务。

| 功能ID | 用户目标 | 不同写操作 |
| --- | --- | --- |
| FSC-0038 | 撤销电脑应用的始终允许授权 | removeAppApproval |
| FSC-0039 | 设置电脑使用操作的声音反馈 | setSoundMode |
| FSC-0040 | 设置锁屏时是否允许电脑使用 | setLockedUseEnabled |
| FSC-0041 | 设置Messages的全局读取策略 | setMessagesReadAccessPolicy |
| FSC-0042 | 管理Messages某个聊天的读取决定 | setMessagesReadDecision, removeMessagesReadDecision |
| FSC-0043 | 设置Messages是否始终允许向所有聊天发送 | setMessagesSendAllowAllChats |
| FSC-0044 | 撤销Messages某个聊天的始终允许发送授权 | removeMessagesSendApproval |

定义依据是[已接上的控件与服务合同](cua-settings-consumer-contracts.json)，不是按服务方法数新增14项功能。新增与修改聊天读取决定复用同一写方法；移除是不同操作，归于同一聊天读取管理目标。应用授权撤销与FSC-0037审批决定分别保留。声音的三个值、锁屏boolean、读取policy与逐聊天decision是各自输入，查询和Add搜索不另算用户目标。[21条作者推断记录](cua-feature-scope-evidence.jsonl)与原源码事实分列，不新增全局证据journal条目。

条件按入口分别保留。主视图要求computer-use available，锁屏行另要求macOS、locked capability与非null enabled。直接Messages子路由早于主视图guard返回，受所选插件loading／installed分支控制；列表导航availability不能自动套到该路由。页面查询选中host，14个本地设置服务没有host实参，不能据此宣称每台远程主机各有一份策略。

读取全局policy与逐聊天决定分开，allowAll只隐藏控件；发送全局allowAll也只隐藏逐聊天授权列表。读取三种mutation与全局发送先cancel query；逐聊天发送撤销没有相同onMutate。声音没有本地onError，锁屏null会更新enabled并隐藏行，移除确认的pending按钮与onOpenChange也有不同guard。恢复工程和验收应保留这些差异，不能用统一表单行为抹平。

搜索以200ms debounce、query/session、ready／权限／错误状态和串行队列支撑新增聊天选择。取消query或关闭UI不证明宿主/native操作停止，写包装没有signal。手机关闭插件的严格false和安装后锁屏的严格true规则只是共享服务上下文；本批未接全其入口，不将其验收算入设置页七个目标。

本批给8个写操作分别登记success／failure／cancel／restore，共[32条新功能规格](cua-feature-scope-scenarios.json)，全部未执行。原160条逐对象保留，原20条CUA控件规格也保留原件，作为条件和竞态细节参考，不重复加到192条中。重开规格要求核对真实query、receiver与OS／服务持久化，不能把缓存setData当作落盘。

恢复顺序按证据列为四道门槛：先声明本地typed服务与外部依赖边界，再恢复能力／路由与query策略，然后接七组交互，最后验证真实provider、receiver、系统权限和重开。每道门槛的前置与来源在分析JSON的recoveryStages中登记。React、query/cache及native第三方实现用依赖引入；它们的完整版本、补丁和ABI仍沿独立依赖调查，不据本批导入名认定身份。

新视图使用版本化文件，原[37项v1 JSON](feature-scope-current.json)、[v1 CSV](feature-scope-current.csv)、[160条v1规格](feature-scope-current-scenarios.json)保持历史字节，旧合同的哈希与pointer继续可复核。analysis-state的featureScopeCurrentView和本报告入口明确指向v2；历史报告中的37／26／160是其当时快照。

44项模式仍为unknown，ChatGPT-only确认排除仍为0，完整功能分母未知。设置分类codexOrWorkLocal是访问资格证据，不能单独完成产品模式／共享依赖判定。967旧入口未映射与337 deferred没有因本批归属增加而消解。剩余12项包括两条设置只读facet、一条WSL多动作卡、thread四种生命周期、四种通知／状态facet和项目能力父动作；仍需分别闭合。

本批只重新读取既有源码范围、metadata pointer与关联；没有新REA／Program解析，没有执行目标函数、修改系统设置或提交模型。来源校验和[发布索引](cua-feature-scope-provenance.json)支持可追溯性，不替代独立语义审查或真实UI验收；完整分析目标保持未完成。
