# 存储、安全与家庭设置：清理重查、共享认证及角色边界

本批交付26项有限操作目标、13项支撑机制与78条待执行产品规格，接入[恢复覆盖表v11](restoration-coverage-v11.json)的T40至T42。[功能台账v20](feature-scope-v20.json)现有330项定义、334项用户操作、94项支撑及1087条未执行规格。[现有实施计划](implementation-plan-v8.md)保留为排程基线，本批任务由最新覆盖表扩展，没有另写计划版本。

| 页面 | 本批目标 | 模块恢复决定 |
| --- | --- | --- |
| Storage | 3 | Separate local measurement, complete descendant inventory and reviewed cleanup; reuse archive/worktree owners with host context. |
| Security | 19 | Separate credentials, protection, sessions/trust, grants and PIN state machines. Retain device-code policy as an explicit Codex/shared consumer. |
| Parental controls | 4 | Separate role/identity orchestration, delegated invitations/member management and notice-only dismissal; reuse account notifications. |

Storage仅本机展示扫描服务；清理按父会话及所有子代理过滤和计量，先审阅再确认，重查变化/执行中/不完整条目并跳过。验证与删除不是已证明的原子事务。

Security区分密码/MFA/通行密钥、账户高级保护、Lockdown、会话注销、设备信任和第三方授权；真实认证、历史、硬件密钥订购等继续由独立接口或委托模块负责。

设备码登录开关的源码明确列出Codex和Office用途；CSP是另一个有独立flag的账户偏好。访问家族不能替代产品模式处置。

PIN有身份/代次和重置挑战保护；所选build的两处返回effects为空，不据此声称重置返回路径已接通。

Parental controls保留角色与成员身份检查、邀请委托与不存在家庭的404续查；解除关联通知的Close仅提交捕获notice_ids，不能当作解绑或年龄验证。

34项精确源码helper/回调隔离用例通过；仅执行冻结源码函数/回调与合成库存、身份、查询、服务替身；未扫描真实磁盘、删除会话、修改认证或家庭资料、调用模型服务。303个已选择源码单元的冻结文件与字节范围核验通过。

Security中的设备码许可明确供Codex与Office共用；不按ChatGPT标签删除整页。Storage复用归档/工作树，家庭安全通知复用FSC-0103。 模块路径是恢复归属提案，客户端源码尚未生成。

45个设置容器中39个已有局部合同，6个待展开。本地清理、账户会话注销、设备信任撤销及家庭通知关闭具有不同对象；委托模块与空PIN返回effects保留缺口。 局部缺口不作为其他静态盘点的全局前置条件，完整分析尚未完成。
