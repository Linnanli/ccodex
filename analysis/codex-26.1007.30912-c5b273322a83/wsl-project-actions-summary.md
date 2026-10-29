# WSL 项目入口与创建合同

General 的 WSL 卡片包含不同动作：已连接时调用打开远程项目弹窗的 helper，未连接时链接到 `/settings/connections/wsl`，没有主机时显示安装说明。卡片本身不创建项目。[结构化合同](wsl-project-actions-contracts.json)记录所选源码范围、导入关系、静态事实和待验证项。

General 调用 `Kr({hostId})`；`Kr` 导入对应 initial 的 `B0r`，后者发送 `open-create-remote-project-modal` 消息。此入口没有传 `setActive`。已定位的 `Wuc` 注册消息处理器，要求当前没有请求、`Ofr()` 为真且 `LW()` 为假；中央 renderer switch 对同类型消息直接跳过，不是创建项目的接收端。消息总线的真实投递和运行实例仍需核对。

`Wuc` 使用的延迟组件经 `Yuc` 加载 `CreateRemoteProjectModal`，小模块再将请求传入 `CreateProjectDialog`。后者对该类型请求直接保存 `o.setActive`。远程创建后的主动项目切换要求没有外部完成回调、处于 setup 模式且 `setActive === true`。因此，在请求按该链路保持原值的条件下，General 入口不触发该主动切换分支；不能根据其他入口传 true 的行为补上默认值。

弹窗从导入的候选主机列表中匹配请求 host，匹配不到时按当前 host、已选远程 host、首个候选回退。提交受到 busy、主机可用性、路径检查和外观加载条件限制。主机筛选、路径合法性及路径比较 helper 的实现尚未在本批展开，不将其名称当作语义证明。

目录验证请求 `remote-workspace-directory-entries`，返回目录经比较 helper 后必须匹配选定路径；异常返回 false。setup 模式还调用重复项目检查。目录未验证、允许创建且尚未确认时先显示确认；确认 token 的 host、path 和 comparablePath 必须仍匹配当前状态，创建目录后再次验证。`pick` 模式只发送目录选择结果，不创建项目。

创建优先使用注入的 `projects.createRemote`；该接口不存在时才按旧状态路径写项目、可选外观和排序。随后还有公共 bookkeeping 和条件性的选中状态更新。代码中没有包围这些步骤的事务回滚，后续步骤失败可能已产生部分写入；真实 provider、持久化和重复检查规则仍需验证。busy 时页面关闭与编辑受到限制，关闭 UI 不能证明后台操作取消。

本批交付 12 条静态事实和 8 条未执行的合同场景，不新增功能定义，不修改当前 44 项功能、12 项队列或 192 条功能规格。`GENERAL-OP-032` 保留为待拆分复合候选；下一步结合连接页面归属与实际创建行为决定如何分配用户目标和导航支撑。模式仍为 unknown，没有新增 ChatGPT 专属排除。

原始五次完整 Program 分析均成功；另外解析两个小模块及一个有边界的初始化片段，以连接延迟加载。解析只把冻结 JS 当作数据，没有导入或执行目标模块，没有运行客户端、创建目录、提交模型任务或修改系统设置。这些静态合同指导后续恢复，真实 UI 和接收方仍按里程碑验收。
