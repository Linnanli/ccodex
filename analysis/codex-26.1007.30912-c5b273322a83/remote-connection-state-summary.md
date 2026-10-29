# 远程连接目录、刷新并发与连接状态

本批关闭所选远程状态**生产端**的静态连接和替身时序缺口；renderer状态query及真实实例仍待验证。见[23条限定合同](remote-connection-state-contracts.json)、[证据行](remote-connection-state-evidence.jsonl)、[35项隔离观察](remote-connection-state-observations.json)、[10条待执行场景](remote-connection-state-scenarios.json)和[来源索引](remote-connection-state-provenance.json)。

| 来源 | 过期成功 | 过期失败 | 失败或空值处理 |
| --- | --- | --- | --- |
| SSH | 转向最新刷新Promise | 仍拒绝旧调用方 | 当前错误传播；相等结果直接reconcile |
| WSL | wrapper继续等最新一轮 | run抑制旧错误，wrapper等最新一轮 | null保留旧列表并至多安排一次30000ms重试；成功空数组可清空 |
| remote-control | 返回当时仓库缓存，不等最新一轮 | loader返回空且不写状态 | I3/R3/L3和未知错误有不同标志与clientId清理，未知错误重抛 |

这些规则来自完整固定main Program的词法绑定及保存的代码范围，不能统一改为一个“取最新值”刷新器。调用方失败、目录发布、授权状态和实际连接完成也分别保留。

hXe把自身appState、共享仓库和registry传入fKe；构造器直接保存。hXe对三类目录键的subscriber会调用reconcile，另一subscriber触发manager后台刷新。fKe与hXe的列表getter都按SSH、WSL、remote-control顺序展开，缺失列表为空，不在这一层去重。appServerConnectionState直接查询registry并为缺失连接返回disconnected/null/null，因此“已保存主机”与“已连接主机”是两个分母。

SSH先保存generation和最新Promise，成功后才检查是否过期。当前结果的catalog对账集合来自保存配置；U.default比较相等时直接reconcile，否则set仓库。set调用真实wee时先改内存再同步通知subscriber，subscriber异常可使刷新失败而新内存值已存在。U.default本批只定位到包装器，没有恢复其第三方实现或认定其包身份。

WSL的null发现失败与authoritative空数组不同。null保留旧列表，只在尚未尝试重试时安排30000ms计时器；回调检查enabled和generation。有效发现重置重试标志，authoritative才对账catalog，随后set并调用auto-connect helper。该连接调用没有await，目录刷新返回不代表连接结束。dispose在本类中失效WSL generation并清重试，但不会在这里清掉已发布旧数组。

remote-control关闭时写空列表及四个false状态，未在这一分支清clientId。重复enable先返回已缓存列表，其次复用在途刷新；finally只清仍属于本次的pending引用。当前刷新过滤本机env/install，附加autoConnect后发布；授权为true才对账catalog并开始auto-connect，丢失授权时await旧列表的disconnect。loader的三种Error子类与未知异常保留各自available/accessRequired/authRequired/clientAuthorized组合，R3分支不会像I3/L3那样清clientId。

reconcile按Map保留同hostId最后一项并排除owningHost；autoConnect=false处置已有连接。hKe的复用比较包括外部相等比较、false→true规范化以及r.Ri谓词下的hostId/envId条件。创建错误被记录，配置仍进入新Map；处置错误可在Map替换之前抛出。因此重建时不能把整次刷新视为原子事务。

建议分别维护目录刷新、连接reconcile、平台/服务发现适配和共享数据契约四类职责，具体拟议路径与来源ID见合同。这是新维护设计，不是恢复原作者目录。r/c模块、SSH解析、enrollment和API均保留依赖边界；没有把第三方实现复制到客户端源码。

一次Node22 VM命令执行保存的完整fKe、wee及七个helper/常量/Error类，共9单位24785字节，35场景通过。运行了这两个类的实际构造器和选定方法；appState、registry、服务、r.Ri、U.default比较与计时器均为明确替身。比较器使用JSON规范化后的Node比较，仅支持这些fixture，不证明真实U.default语义。没有执行hXe构造器或其真实subscriber，也没有真实窗口、IPC、SSH配置读取、远程发现、网络、设置变更或模型任务。10条集成场景均未执行。

本批仅新增一次完整main Program解析，没有新REA命令；既有REA partial/unknown限制保持。45个保存单位含1个继承wee单位，原始绑定记录617处、按引用位置去重后616处；字节长度合计含重叠，不是新增代码体积。

后续出口明确为三项：先接renderer状态query的真实方法与host参数，再对齐真实subscriber/registry/provider时序，最后核对appState耐久保存和平台行为。本批没有以生产端证据代替这三项。原37项有限功能、40用户操作/5机制/26队列、160条未执行功能规格、967未映射旧入口、337 deferred、mode unknown及确认排除0均保持；完整功能分母未知，整个分析仍未完成。已有模型样例组2/2已用、余0，本批新增0。
