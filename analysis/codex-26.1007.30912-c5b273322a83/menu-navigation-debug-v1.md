# 线程导航、调试工具与应用历史菜单批次 v1

SQ-02-menu-navigation-debug-05固定records76..85的10条schema已有逐条去向。后一线程作为既有FSC-0411的方向操作，名称明确为相邻线程导航；另新增7项目标。

| 目标 | 边界 |
| --- | --- |
| FSC-0411 在当前列表中切换相邻线程 | Injected targets/onSelect and command winner, real route selection, tab interception and shortcut preference durability. |
| FSC-0412 显示或隐藏应用调试面板 | I3a/Ym/yd/K3a modal ownership, actual vbc lifecycle, focus/close and IPC delivery. |
| FSC-0413 从剪贴板打开应用深链接 | Effective deep-link queue/parser/receiver, accepted URL forms, native clipboard/dialog results and final route. |
| FSC-0414 复制当前认证用户标识 | Effective auth/user-id provider, ownership/privacy context and actual clipboard/failure handling. |
| FSC-0415 显示或隐藏侧栏 RAM 使用指示器 | BNo initializer/lifetime, INo measurement/rendering, native processMemory sampling and resource cleanup. |
| FSC-0416 显示或隐藏查询状态调试工具 | e_ environment identity, NNc library origin/version and independent package import, actual query client, portal/resize accessibility and cleanup. |
| FSC-0417 请求切换 React Scan 调试工具 | Actual React Scan subscriber/load path, package/version provenance, state/lifecycle and measured runtime behavior. |
| FSC-0418 在应用路由历史中后退或前进 | gm feature/environment identity, tracked settings-change ownership, router history/provider and actual navigation/focus across platforms. |

调试门控不能合并：调试面板/剪贴板链接/用户ID/RAM菜单使用注入allowDebugMenu；React Scan还需allowDevtools与dev/agent/nightly构建；Query工具使用isDev或internal策略。构建类型不能用来判定ChatGPT专属。

RAM显示还需processMemory存在。Query工具消息可以切换isOpen，但环境/构建门控可能继续隐藏UI；NNc依赖来源未确认。React Scan请求的独立接收方仍未知，Fsc的no-op标签不证明全程序没有实现。

应用历史后退有设置未保存确认及两个特殊路径回首页，普通后退/前进调用router(-1/+1)。网页历史与相邻线程列表导航分别保留。

本批新增7项定义、9项操作、25条未执行规格。[台账v33](feature-scope-v33.json)现418项定义、429项用户操作、117项支撑；[规格v30](feature-scope-v30-scenarios.json)共1376条。[覆盖v24](restoration-coverage-v24.json)仍49任务，[排序v7](restoration-current-ordering-v7.json)仍两套58节点图。完整产品分母未知。

[来源v11](legacy-entry-dispositions-v11.json)仍968条，角色待审0、无功能关联900、完整功能解决0；累计62条菜单来源部分关联（60schema、2生成选项）。37职责及14项菜单增补提议待SQ-03统一。

选取来自6个不同原Program，共37个保存范围，6条显式ESM连接复用或定位实际导出身份。剪贴板、菜单、客户端、模型与服务均未执行；未新增产品/构建通过。第三方实现通过依赖引入，身份不明的调试UI单列缺口。

停点：固定10条有目标、操作/别名及必要回调边界；不继续递归恢复modal、剪贴板认证、React Scan、measurement或router provider。剩余SQ-02、SQ-03/SQ-04及实际行为条件保留。
