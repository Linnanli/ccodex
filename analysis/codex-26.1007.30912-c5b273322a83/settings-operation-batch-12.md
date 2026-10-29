# 协议、账户与扩展：区分法律操作、账户身份及浏览器权限策略

本批交付12项有限操作目标、8项支撑机制与36条待执行产品规格，接入[恢复覆盖表v10](restoration-coverage-v10.json)的T37至T39。[功能台账v19](feature-scope-v19.json)现有304项定义、308项用户操作、81项支撑及1009条未执行规格。[现有实施计划](implementation-plan-v8.md)保留为排程基线，本批任务由最新覆盖表扩展，没有另写计划版本。

| 页面 | 本批目标 | 模块恢复决定 |
| --- | --- | --- |
| Agreements | 2 | Separate legal document reading from explicit workspace signing and scoped metadata state. |
| Account | 5 | Separate current-user/profile, delegated identity editors and personal-account deletion; preserve external email route and shared age ownership. |
| Extension | 5 | Recover browser permission policy editing with revision/identity and enterprise guards; do not invent installation or connection controls. |

Agreements将服务协议/BAA文档导航与签署分开；签署只在未签署HIPAA工作区展示，提交后合并时间戳并刷新该工作区元数据。

Account保存姓名时保留请求期间的新草稿；用户名打开委托编辑器，builder profile所选行只读，年龄复用已有功能。

当前邮件根组件把auth0ClientId固定为null：可见Add/Change打开外部账户设置，本地reauth查询及邮件/OTP弹窗没有被该路径启用。

个人账户删除保留身份、近期登录、确认文字/联系方式、提交时重查、刷新取消及错误区分；风险头获取有回退，失败可能返回空头，并非强制终止请求。

Extension管理审批默认、站点规则、历史、网站工具和全局CDP；保存带身份和expected_revision，冲突不自动重试。站点回调跳过fullCdp，拒绝显式ask，校验器不做URL规范化。

29项精确源码helper/回调隔离用例通过；仅执行冻结源码函数、回调和根组件，使用合成身份、查询、UI与服务替身；未接受真实协议、删除账户、更改权限或调用模型服务。135个已选择源码单元的冻结文件与字节范围核验通过。

沿用共享账户访问边界；账户年龄入口复用FSC-0199/FSC-0200。用户名与CME管理器保留委托，邮件本地流程不可由当前按钮触达。 模块路径是恢复归属提案，客户端源码尚未生成。

45个设置容器中36个已有局部合同，9个待展开。协议链接与签署、账户删除与本地数据清理、全局CDP与站点规则分别验收；扩展页没有安装或连接操作。 局部缺口不作为其他静态盘点的全局前置条件，完整分析尚未完成。
