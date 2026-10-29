# 设置入口参数、主机解析与隔离观察

两个设置入口传给可见性hook的第二参数，均来自所选主机解析后的kind===local，不能直接当作Codex／ChatGPT模式边界。见[24条限定合同](settings-entry-callers-contracts.json)、[证据行](settings-entry-callers-evidence.jsonl)、[17项隔离观察](settings-entry-callers-observations.json)、[8条待执行UI规格](settings-entry-callers-scenarios.json)及[完整归档索引](settings-entry-callers-provenance.json)。这是固定基线的分析增量，没有生成客户端工程。

| 入口 | hook参数 | 本地条件来源 |
| --- | --- | --- |
| SettingsPage / ri | 当前slug（time-management归为safety）、b、f | ne(f).kind===local；ne经shared.N$t连接pzt |
| 设置命令项 / U | null、isSelectedHostLocal、selectedHostId | Fa先计算ce(selectedHostId).kind===local，再经lazy组件props传入；ce也连接pzt |

两处selectedHostId都来自同一initial模块的Q6导入，但真实provider、配置发布者和运行实例尚未证明。页面还从usage的tab query得到候选slug；该解析器本批未执行。hook第二参数为false时使用上一批保存的12项精简列表，仍叠加各页访问与能力条件。它不等于home composer的chat/work偏好，也不构成删除ChatGPT页面的依据。

命令菜单还受shared.OAt→XAn访问条件、搜索／Configure组条件控制；lazy loader按字面模块路径选择VisibleSettingsCommandMenuSectionItems→U。U先过滤disabled，内部列表为空时整组返回null；之后才构造按认证来源和gate控制的外部账户／安全项。K区分appRoute、host路由消息和onNavigate callback；回调正常返回后由外层负责关闭，helper返回false则提前退出。profile事件及外部浏览器调用的先后顺序、同步异常与未await的Promise分别保留，真实导航与bridge receiver仍未知。

pzt优先返回ID匹配的host_config对象，否则解析远程列表；列表顺序为SSH、WSL、remote-control，重复ID取首项。未匹配ID回退默认Local。environment-git:hosted:前缀在没有匹配配置覆盖时返回“Cloud executor”，kind仍为local。前缀后缀经过decodeURIComponent，畸形编码可抛错。因此kind:local描述此解析器的返回值，不能代替物理主机、网络可达性或访问授权判断。

一次Node22 VM命令加载15个保存单位共1941字节，包含10个函数及5个常量赋值，17项合成场景全部通过：默认与未知ID回退、列表缺失与等待、云执行器、畸形编码、SSH alias／参数、WSL、remote-control、重复ID、配置优先级、null／undefined及memo复用。FI记录与React编译器memo cache均为明确替身，每项新建VM；没有读取真实主机配置，没有运行返回的SSH／WSL命令，也没有启动原客户端、执行UI、修改设置或提交模型。它们支持所选函数在这些输入下的行为，不能升级原功能验收。

REA固定版本6.4.0重新分析package.json与四个设置／菜单JS的字节相同副本：应用图140节点／953边，限于这五文件子集的coverage为complete；语义图27173节点／29013关系，coverage为unknown，8815个未知项，所有语义关系族均partial。大部分导入有意未纳入子集。两处hook调用按模块hash与UTF-16范围各匹配一个REA call-site，但没有直接关联该site的语义关系；callee与参数连接来自另存的完整Program词法分析，不能称REA已经闭合整条调用链。

完整REA成功输出以[无损gzip](raw/settings-entry-callers/rea/rea-03-output.json.gz)保存，解压后53911108字节及SHA均已核对；[紧凑投影](raw/settings-entry-callers/rea/rea-projection.json)保留两处原JSON pointer、节点、覆盖情况与hash。不会将大图节点数当成功能数量。此前两次REA因macOS Swift辅助程序的模块缓存写权限失败；尝试调整缓存后仍失败，获自动审批的正常执行完成，工具所有权检查未被移除。工具安装的离线缓存失败及投影脚本首次把families误当字典的失败均保留；修正投影未重跑REA，也未重跑17个VM场景。

本批22条源码事实／2条推断，67个规范AST单位（长度合计37735字节，含重叠）、270处词法引用、6项跨模块连接。三条作者解析命令共解析9个完整Program，涉及5个不同文件；REA另解析其子集的4个JS文件，不重复合并计数。字面文件名扫描覆盖14770个JS共381823019字节，仅5文件命中，不能替代计算路径和运行时加载调查。作者核对6个含范围文件的426个唯一范围、968处坐标、五份REA输入及全部14770文件hash；没有增加独立语义审查。

恢复源码可按职责组织host descriptor resolver、account/workspace access、settings catalog/visibility、command navigation adapter，并用包管理器引入React、状态与路由依赖。这里的目录建议是维护设计推断；并未找回原作者目录，也未完成这些库的全量版本与补丁鉴定。应保留host_config优先级、未知ID回退、列表顺序、加载与异常合同，再用真实UI／provider证据决定兼容策略。

当前37项有限功能、40用户操作／5机制／26队列、160条功能待执行规格、967未映射旧入口与337 deferred均保持。新增8条UI规格独立列出，全部未执行。没有新模式归属或确认ChatGPT-only排除，完整分母与分析目标仍未闭合；下一步应追Q6/provider与真实host配置发布者，核对共享消费者后再收窄重建范围。此前获批模型样例组2／2已用、剩余0，本批没有新增模型提交。
