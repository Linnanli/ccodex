# 广告、归档与数据控制：明确操作对象及批量作用域

本批交付18项有限操作目标、9项支撑机制与54条待执行产品规格，接入[恢复覆盖表v9](restoration-coverage-v9.json)的T34至T36。[功能台账v18](feature-scope-v18.json)现有292项定义、296项用户操作、73项支撑及973条未执行规格。[现有实施计划](implementation-plan-v8.md)保留为排程基线，本批任务由最新覆盖表扩展，没有另写计划版本。

| 页面 | 本批目标 | 模块恢复决定 |
| --- | --- | --- |
| Ads controls | 5 | Separate ad preferences, entitlement and read-only history/topics from account conversations; delegate external billing entry. |
| Archived chats | 5 | Aggregate typed sources in presentation while preserving separate local host, cloud task and account conversation effect adapters; reuse existing local unarchive owner. |
| Data controls | 8 | Separate account conversation data, privacy/permission and remote Work environment services; preserve delegated managers and shared account access. |

Ads的历史行与兴趣主题为只读展示；删除接口清理广告profile。广告退出/恢复受独立资格和身份约束，升级链接仅负责外部导航。

Archived chats混合不同类型来源：本地线程调用宿主archive适配器，云任务调用recover，账户会话调用自己的取消归档/删除服务。云任务行没有所选会话删除按钮。

本地“删除全部归档”调用deleteAllArchivedConversations，作用于所选宿主；当前搜索/项目筛选不能缩小这个接口的语义。按项目删除则逐个处理明确ID。

Data controls的批量archive/delete调用账户/conversations；导出是异步邮件请求，需保留token/身份守卫。位置的服务器许可与设备权限分开；Work reset仅针对当前远端环境并声明保留Library。

共享链接、Information sharing和其他懒加载管理器保留委托边界；不能把页面导航当成这些管理器功能已完整恢复。

27项精确源码helper/回调隔离用例通过；仅执行冻结源码函数/回调及合成状态、查询和服务替身；未读取账户数据、提交真实删除/导出/重置、请求设备位置或调用模型服务。145个已选择源码单元的冻结文件与字节范围核验通过。

三页保留待具体消费者的模式核对；共享账户访问层沿用已收束合同，本地取消归档复用FSC-0046。第三方实现及服务接收方保持外置边界。 模块路径是恢复归属提案，客户端源码尚未生成。

45个设置容器中33个已有局部合同，12个待展开。“全部本地归档”是选定宿主的整体操作，不等于当前筛选结果；账户批量会话操作、广告数据清理和云端Work重置分别验收。 局部缺口不作为其他静态盘点的全局前置条件，完整分析尚未完成。
