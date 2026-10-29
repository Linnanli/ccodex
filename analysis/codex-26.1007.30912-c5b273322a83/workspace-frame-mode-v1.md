# 工作区入口、布局状态与模式条件

已完成既有 FSC-0456（previousTab/nextTab）所用工作区 frame 的选定源码入口与条件核对。该结论补充阶段二的保留理由及阶段四的状态/组件边界；实际模式归属和行为验收仍未完成。

工作区 layout.N 与会话页 Oh 都经显式 ESM 导入使用同一个 Ac → jc 组件。两个调用点没有本地应用模式门控；各自相邻的 metadata 或侧栏门控不能移套到 Ac。jc 内部仍会按启用条件返回 null，因此源码引用不等于实际显示。

| 条件 | 冻结源码中的含义 | 恢复决定 |
| --- | --- | --- |
| zei / chrome.bt | 非 side-panel，且有 persistentWorkspace 或开关 3528415127 | 保留工作区及功能开关判断；实际值未知 |
| wS、DS、AS | 内容主表面、初始表面和焦点 | 与应用模式分别建模 |
| kS、LN、zN、G1n | full/split/chat 布局及主页标签条件 | 不按名称作为 ChatGPT 排除依据 |
| hRn、bj、OS | 默认会话可见性与显式请求 | on-request 令 hRn=false，但 OS 仍可使 bj=true |
| initial.gS / lPt / vS | 既有 home-composer-mode-v1 偏好及访问条件 | 复用已有 publisher/store 合同；不推导全局闭合枚举 |

保留 Ac/jc 及会话/内容两条状态路径。两个源码使用方支持共享组件的保留，但尚不足以把 FSC-0456 整项模式改为 shared，也不能排除整个 Oh 或 layout.N 文件。既有三个 ChatGPT 专属分支决定继续有效，本批没有新增排除项。

源码问题在明确实参边界收口：实际 RouteScope、调用方提供的 workspace/session、功能开关值、挂载状态、命令后效、焦点和持久化均列为精确后续条件；不因这些未知重新分析既有 publisher/store。

本批有 13 条证据、36 处冻结范围和 10 条显式 ESM 连接；解析两份消费者 Program（50810 节点），复用三个既有 Program 索引。无目标代码求值、客户端启动、模型/服务提交或构建。当前功能/操作/场景分母及原九项完成标准保持。

[逐项合同](workspace-frame-mode-v1.json) · [证据](workspace-frame-mode-v1-evidence.jsonl)
