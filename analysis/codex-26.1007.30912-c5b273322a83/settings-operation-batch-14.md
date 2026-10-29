# 受信联系人、时间管理与云端偏好分析

本批交付10项有限操作目标、9项支撑机制与30条待执行产品规格，接入[恢复覆盖表v12](restoration-coverage-v12.json)的T43至T45。[功能台账v21](feature-scope-v21.json)现有340项定义、344项用户操作、103项支撑及1117条未执行规格。[现有实施计划](implementation-plan-v8.md)保留为排程基线，本批任务由最新覆盖表扩展，没有另写计划版本。

| 页面 | 本批目标 | 模块恢复决定 |
| --- | --- | --- |
| Trusted contact | 5 | Recover identity-scoped contact queries, consent/epoch dialogs and selected-ID mutations; keep recipient delivery outside UI success. |
| Safety | 3 | Recover shared recurring editor and legacy adapter with separate quiet/study policies; preserve identity/readback/unsaved navigation. |
| Cloud settings | 2 | Recover cloud preference hooks/cache writer and pattern validator as first-party modules; separate cloud consumers from local settings. |

Trusted contact先查资格再查列表，当前页只展示首个联系人。邀请需姓名、有效邮箱和同意；关闭或重开表单会隔离旧响应的对话框更新，但不等于取消网络请求。

重发与移除分别调用选中联系人ID；个人说明动作只打开邮件编辑器，邀请成功反馈不证明邮件送达或对方已接受。

Safety区分静默、学习、父级管理及不支持格式；保存时重新核对身份和权限，监听切换并取消，刷新确认后才关闭。旧版常开学习通过独立适配器转成时段。

云端偏好分别读取用户值和账户/用户配置，以服务响应更新捕获的查询缓存。分支草稿绑定服务器基线；格式校验覆盖占位符、长度和字符，不等于完整Git引用规则。

已恢复的查询/写入、旧版适配和格式校验归第一方模块；React等第三方实现不生成维护副本。真实服务、调度算法及模式使用方保留明确验收要求。

27项精确源码helper/回调隔离用例通过；仅以合成身份、联系人、时段、配置和内存查询/服务替身执行冻结源码；没有发送邀请、邮件、修改真实账户或调用模型服务。111个已选择源码单元的冻结文件与字节范围核验通过。

保留访问家族与产品模式的区别；云端偏好与本机差异视图分别归属，未凭名称排除整页。 模块路径是恢复归属提案，客户端源码尚未生成。

45个设置容器中42个已有局部合同，3个待展开。联系请求完成与邀请送达、时段已保存与实际执行、格式检查通过与Git服务接受分别验收。 局部缺口不作为其他静态盘点的全局前置条件，完整分析尚未完成。
