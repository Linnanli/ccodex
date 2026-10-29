# 面板、布局与浏览器菜单目标批次 v1

SQ-02-menu-panels-03固定10条schema已有逐条去向，形成10个新增有限目标。

| 功能 | 关键边界 |
| --- | --- |
| FSC-0399 查看应用版本与构建信息 | Actual OWL BrowserWindow compatibility, HTML/readiness/icon helpers and accessibility/close behavior. |
| FSC-0400 显示或隐藏应用侧边栏 | Effective mount/scope, ZRt transition/state writes, focus and persistence. |
| FSC-0401 显示或隐藏底部面板 | Actual terminal/fallback creation, visibility atoms, native transport and restart restoration. |
| FSC-0402 切换当前线程摘要的显示或固定状态 | Full command mount/priority, source state atoms and persistence, Chat-only branch separation. |
| FSC-0403 显示或选择当前线程终端 | yPa.open implementation/provider, PTY process lifecycle, actual focus and command/native path equivalence. |
| FSC-0404 切换当前上下文的文件树或资源浏览器 | Actual winning consumer, Zma/TJ filesystem provider, mode-specific page explorer eligibility and persistence. |
| FSC-0405 切换工作区布局或浏览器面板 | D layout state machine, creation/selection delegates, actual focus/persistence and full-mode integration. |
| FSC-0406 在当前上下文打开内嵌浏览器标签 | Rt/native page lifecycle, successful empty-tab creation, storage isolation, transfer/adoption and errors. |
| FSC-0407 聚焦当前浏览器地址栏 | Effective winning registration, ai/source edit guards, actual DOM focus/select and IME/cancel behavior. |
| FSC-0408 刷新当前可见浏览器页面 | OWL manager implementation, actual navigation/load errors, pending request cancellation and selection timing. |

原生终端消息调用UNa/yPa.open，命令回调走$Na条件分支，未声称两条路径等价。底部面板是容器显示/隐藏动作，保留独立目标。

文件树命令有本地线程、页面资源浏览器及标题菜单消费者，按上下文处理；不能仅按命令名将它们合并为同一文件打开实现。摘要命令存在本地线程消费者，整个命令继续保留，不新增ChatGPT专属排除。

Cycle workspace layout与Toggle browser panel为同一个隐藏入口的标签变体。普通浏览器页面刷新与应用窗口刷新分开，强制刷新留在后续来源。

当前[功能台账v31](feature-scope-v31.json)为408项有限定义、414项用户操作、117项支撑；[规格v28](feature-scope-v28-scenarios.json)为1336条未执行规格（本批新增30条）。[覆盖v22](restoration-coverage-v22.json)仍49个任务，增量并入T49；[排序v5](restoration-current-ordering-v5.json)两图仍各58节点。完整产品分母未知，历史实施计划v10未改。

[来源视图v9](legacy-entry-dispositions-v9.json)仍968条：角色待审0、无功能关联919、完整功能解决0；累计43条菜单schema获得部分目标关联。角色分类完成不等于功能恢复完成。

新增关于窗口、工作区命令适配、浏览器命令适配三个十字段维护提议；与此前7项一起待SQ-03统一，既有37职责不变。第三方实现仍通过依赖引入。

静态选取覆盖16个原Program、85个保存选取及16条显式ESM连接。实际挂载/优先级、原生窗口/浏览器/PTY、后台与持久化未由这些检查证明。本批客户端运行、模型提交、服务调用、实现和产品测试通过新增均0。

停点：本批固定10条各有目标和委托边界；不再递归展开深层未知。SQ-02整体、SQ-03/SQ-04及实际行为缺口仍未完成。
