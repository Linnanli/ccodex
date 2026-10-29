# Git命令的来源、功能与维护边界

本批核对7个ID、12处注册，归并为6个用户目标、7个操作与24条未执行规格。提交、正式/草稿PR、分支命令先选择本地流程状态；两处合并命令先打开合并UI。不能把这些命令视为已经执行Git或合并成功。

| 功能 | 源码结论 | 维护职责 |
| --- | --- | --- |
| FSC-0441 发起本地Git提交流程 | deferQueries选择Ut/Ht；guard及是否经过工作树分支设置不同 | GCG-M01 |
| FSC-0442 发起正式或草稿PR创建流程 | 两种操作共享创建目标，保留defaultToDraft与Un分流 | GCG-M01 |
| FSC-0443 进入工作树分支设置流程 | 先清空排队动作，再进入branch setup；不证明分支已创建 | GCG-M01 |
| FSC-0444 打开关联PR链接 | URL非空时可用；board分析事件与实际外链打开分开 | GCG-M02 |
| FSC-0445 打开并确认PR合并流程 | 线程与detail注册guard不同；开菜单、确认mutation与实际合并是不同阶段 | GCG-M02 |
| FSC-0446 切换活动行Git归属提示 | 固定gate控制，翻转keyed state；未证明查询/渲染/落盘 | GCG-M03 |

重要恢复约束：LocalGitActionsScope按hostId/cwd取key，不自行加入conversationId。线程合并guard只排除draft/merged；detail命令guard要求open等条件。detail菜单可打开与实际按钮mergeDisabled分开判断；仓库禁用merge commit时提示后续使用squash，不自动重试。Blame命令的所选options没有额外焦点guard。

全部目标mode仍unknown。第三方只采用包、运行时或适配边界，不生成其实现。三个十字段维护提议接入现有T06；当前444项有限功能、476用户操作、118支撑、1482条未执行规格、51任务与两套60节点图。原438项定义不改。

968条来源身份保留，7条新增有条件功能关联；无功能关联来源从804降至797，含8个明确菜单机制。其他103条命令目标缺口完整保留，来源功能完全解决数仍0。原九项分析完成标准未提升。

[结构化合同](git-command-goals-v1.json)、[证据](git-command-goals-v1-evidence.jsonl)、[功能账本v38](feature-scope-v38.json)、[职责映射v4](feature-module-ownership-v4.json)、[来源v17](legacy-entry-dispositions-v17.json)。新9次完整AST解析覆盖7个冻结文件，只用于源码分析；没有客户端、模型、服务、Git动作或产品/构建通过。
