# 代码审查与云环境：用户操作和服务边界

本批交付23项有限操作目标、6项支撑机制与69条待执行产品规格，接入[恢复覆盖表v7](restoration-coverage-v7.json)的T29至T30。[功能台账v16](feature-scope-v16.json)现有260项定义、264项用户操作、58项支撑及877条未执行规格。原实施计划v7保留，没有另写计划版本。

| 页面 | 本批目标 | 模块恢复决定 |
| --- | --- | --- |
| Code review | 15 | Separate desktop review tool/provider preferences from cloud repository policy and personal user preferences. Keep first-party policy, concurrency/funding/permission guards; externalize third-party UI/query packages and connect REST/host adapters. |
| Codex Cloud | 8 | Keep cloud catalog/editor policy in renderer, assign request/createDraft/delete to environmentConfigs, reuse existing environment creation/task/vault adapters, and preserve identity/credential/uncertain-result rules before implementation. |

代码审查拆为桌面嵌入工具/托管实例、仓库代码与安全策略、个人偏好三组。仓库 PATCH 与用户偏好 PATCH 不共用持久化语义；额度偏好与显式 authorize_funding 也独立。

仓库查询区分 GitLab 空搜索、直接仓库查找和搜索分页；仅400/403/404触发查找回退，GitHub排除归档并最多125页。连接加载在返回前核对账户/用户并支持取消。

安全合并保护还受提供商、功能开关、admin权限及严重程度顺序约束；实际GitHub必需检查设置仍由提供商承担。路径覆盖规则保留继承null和成功后关闭编辑器。

云环境编辑草稿的未知响应会禁用重复Edit以免重复任务；删除成功在取消查询后再次核对身份。秘密值映射为空白，变量/密钥草稿带accountId/userId所有者。创建流程、共享编辑器和个人密钥库继续按已有边界恢复。

23项精确源码helper/回调隔离用例通过；仅执行冻结源码的仓库规范化、查询/变更回调、账户守卫、草稿创建错误与密钥元数据映射，接收器和记录均为合成替身；未调用真实审查、云环境、密钥库或模型服务。196个已选择源码单元的冻结文件与字节范围核验通过。

保留审查 app/cloud 访问、认证方式、账户与功能开关的独立含义，确认整模块排除仍为0；第三方实现作为依赖引入，第一方门控、策略、错误与缓存协调保留。 模块路径是恢复归属提案，客户端源码尚未生成。

45个设置容器中27个已有局部合同，18个待展开。两个页面的操作已接到审查 REST/偏好、environmentConfigs、共享环境编辑器、任务和密钥库边界；委托内部实现与实际服务/模式/持久化属于各自局部验收，不能计为产品通过。 局部缺口不作为其他静态盘点的全局前置条件，完整分析尚未完成。
