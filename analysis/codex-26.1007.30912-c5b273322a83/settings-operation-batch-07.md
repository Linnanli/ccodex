# 年龄、密码与云电脑：操作归属和恢复边界

本批交付13项有限操作目标、5项支撑机制与39条待执行产品规格，接入[恢复覆盖表v5](restoration-coverage-v5.json)的T23至T25。[功能台账v14](feature-scope-v14.json)现有211项定义、215项用户操作、46项支撑及730条未执行规格。原实施计划v7保留，没有另写计划版本。

| 页面 | 本批目标 | 模块恢复决定 |
| --- | --- | --- |
| Age | 2 | Separate age presentation from settings-scoped verification lifecycle and provider/authoritative-readback adapters; preserve phase distinction and identity disposal. |
| Passwords | 5 | Separate masked saved-credential metadata/delete reconciliation from 1Password enrollment/status/revocation. Preserve expectedIdentity and nonretry mutations; do not add plaintext password storage or reveal. |
| Cloud computer | 6 | Separate config/site permission policy, cookie views and passkey metadata from adapters; retain distinct Work and Orbit target/identity rules rather than merging endpoints. |

年龄验证区分发起、进行中、等待权威结果、刷新失败；身份或资格变化时销毁控制器并复位，刷新失败不能当作验证成功或直接重新发起。

密码页只读取credential_id、网站、掩码账户、创建时间和游标；未出现明文密码读取/显示。删除响应不确定时刷新对账，不自动重试删除，也不声称网站已退出。

1Password绑定账户/用户并阻断回调工作区不匹配；连接目的地只接受三个精确HTTPS origin及/oauth/authorize。导航或关闭浏览器均不等于连接成功。

云电脑三种默认审批映射到两个字段，站点权限单独patch。Work与dot Cookie保持不同身份/target/surface约束；dot先取消查询、重查身份，再按捕获target删除。Passkey只分析元数据和确认删除。

23项精确源码helper/回调隔离用例通过；核对身份/游标/非重试策略、OAuth目的地与合成tab、Cookie账户与target约束、删除分发、模式输入规范化，以及年龄控制器资格/复用/身份变化销毁。所有接收器为合成替身，未运行原应用模块，未读取真实凭据、访问验证/OAuth供应商或新增模型提交。114个已选择源码单元的冻结文件与字节范围核验通过。

三个入口虽属chatGpt访问族，但账户/年龄/凭据/浏览器共享消费者未完成模式闭合，确认排除仍为0。第三方React、query、UI、schema、domain和provider实现不生成，沿既有清单或服务适配引入；第一方保留身份、生命周期、对账、目标与缓存策略。模块路径是恢复归属提案，客户端源码尚未生成。

45个设置容器中22个已有局部合同，23个待展开。导入的年龄/provider、OAuth、pattern/domain、target、HTTP身份和存储边界保留在合同及覆盖表，实际运行、权限、模式、持久化与委托内部实现仍待验收。局部缺口不作为其他静态盘点的全局前置条件，完整分析尚未完成。
