# 原生菜单的恢复边界

本批对原有 189 条菜单记录逐条核对冻结源码和已保存的完整 Program 身份，不增加功能定义。

| 来源角色 | 数量 | 恢复决定 |
| --- | ---: | --- |
| 自定义回调 schema | 88 | 保留应用条件及回调，委托领域/窗口服务 |
| 标准 runtime role schema | 29 | 保留 role 声明，runtime 行为另验 |
| role 与显式 submenu 并存 | 4 | 两者同时保留，不能丢弃应用子菜单 |
| 纯子菜单容器 | 8 | 保留层级和条件，不另算业务功能 |
| 动态描述适配 schema | 1 | 保留字段、label 转义及动态 click 委托 |
| 生成器选项 | 26 | 保留参数和回调，不当作最终菜单实例数 |
| 构造/安装 API、工厂及消费者 | 33 | 保留装配、注入、刷新和生命周期 |

其中 20 条属于 `R$e` 候选第三方生成器。已从官方 `electron-context-menu` 的 `v4.1.2` 标签取得源码、manifest 和 MIT license，三个文件的 Git blob 身份均核对一致；19 组默认动作的键、属性集合、ID、标签及回调参数个数与冻结生成器吻合。结合包声明，这支持选定函数的第三方归属，不能证明实际打包版本、无修改或语义等价。[上游源码](https://github.com/sindresorhus/electron-context-menu/blob/v4.1.2/index.js)、[上游 manifest](https://github.com/sindresorhus/electron-context-menu/blob/v4.1.2/package.json)。

恢复决定是通过包引入该生成器，恢复第一方配置和回调适配；不生成库的实现副本。目前不能把 `4.1.2` 当作已确认的实际版本或可直接替换的锁定版本。依赖 root-023 的四项调查仅取得部分进展，修改、实际版本及第一方启用关系仍保留。

八组拟维护职责已分开：应用菜单、dock、MCP App context、浏览器 context、动态菜单适配、tray、trace 入口及外部库。它们是维护建议，未宣称还原原作者模块或完成全部消费者映射。源码中的 Chat 命名不作为剥离依据。

原生 Open Folder 回调已明确到注入的 `getElectronMessageHandlerForWindow(window)` 及 `createOrSelectProject(window.webContents)`。它与既有 T14 picker 合同存在候选关系，但实际注入身份未证明，故不合并功能、不新增功能关联。

当前旧入口中 394 条尚待源码角色处置；完整功能解决数仍为 0。保留 [v27 功能定义](feature-scope-v27.json)、[v18 恢复任务](restoration-coverage-v18.json) 和 1216 条未执行规格，当前菜单与旧入口计数由本批 overlay 更新，避免复制无变化的大台账。

明细：[角色及维护决定](native-menu-roles-v1.json)、[旧入口 v3](legacy-entry-dispositions-v3.json)、[九字段证据](native-menu-roles-v1-evidence.jsonl)。后续处理现有 backend/IPC 候选的协议归属和实际接收边界；不重扫菜单。没有启动客户端、提交模型任务或执行目标代码。
