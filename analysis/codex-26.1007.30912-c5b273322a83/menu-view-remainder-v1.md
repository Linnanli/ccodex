# View菜单剩余来源 v1

SQ-02-menu-view-remainder-07已为records97..121中剩余16条来源确定去向；跳过9条已交付来源。

| 去向 | 结论 |
| --- | --- |
| FSC-0400 显示或隐藏应用侧边栏 | additional-source-alias；1条来源 |
| FSC-0405 切换工作区布局或浏览器面板 | additional-operation；1条来源 |
| FSC-0422 请求复制当前浏览器页面地址 | new-goal；1条来源 |
| FSC-0423 请求切换原生开发者工具 | new-goal；1条来源 |
| FSC-0424 调整当前页面或应用窗口的缩放 | new-goal；7条来源 |
| FSC-0425 显示或关闭键盘快捷键对话框 | new-goal；1条来源 |
| FSC-0426 请求粘贴并匹配目标样式 | new-goal；1条来源 |

Browser、Developer、Help三容器登记为机制，不增加功能或支撑操作。侧栏额外键复用FSC-0400；Full view作为FSC-0405新操作，保留workspace/browser-origin判定与E(scope,full)断点。

缩放不能丢失分支：普通键先尝试页面Ve，未处理时才await M并发送窗口缩放；numadd/numsub/num0隐藏键只尝试页面。非Mac Ctrl+=使用普通分支。选定cVs接收窗口step/reset消息并调用注入provider，展示提示、管理计时器与portal；实际缩放步长、上下限、持久化和native行为未证明。

键盘快捷键命令在q9s切换local open，惰性导入KeyboardShortcutsDialog，传入onOpenChange并要求propagateLoadError；内容、mount和实际错误UI未验证。DevTools和Paste and Match Style委托原生role，后者仅在Mac Edit中找到既有role时替换并绑定Command+Shift+V。

新增5项目标、8项操作、20条未执行规格。当前[台账v35](feature-scope-v35.json)为426项有限定义、443项用户操作、117支撑；[规格v32](feature-scope-v32-scenarios.json)共1407条。[覆盖v26](restoration-coverage-v26.json)仍49任务，[排序v9](restoration-current-ordering-v9.json)仍两套58节点图。

[来源v13](legacy-entry-dispositions-v13.json)累计81条目标部分关联（71schema/10生成选项），另7条机制。881条无功能关联包含这7条无需独立功能的机制；角色待审0、完整功能解决0。37统一职责与16项菜单增补提议待SQ-03统一，九项标准/39项要求状态保持。

本批新解析1个原Program并保存4个完整声明，复用CZe、workspace、sidebar、Pw与Fsc合同。客户端/模型/服务/实现/产品通过新增均0；第三方实现副本0。停在页面管理器、native role、注入zoom provider、workspace E和惰性dialog边界；完整SQ-02与分析尚未完成。
