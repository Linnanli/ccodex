# 显式模式切换：参数与状态契约

本批关闭 FSC-0481 中 `a1s`、`kti`、`gS` 的参数与直接状态变化，并纠正“这三个函数组成单一路径”的理解。

| 命令 | 请求值 | 先写主页模式 | 若到达 kti 的目标 |
| --- | --- | --- | --- |
| switchToMode1 | chat | gS(chat) | work |
| switchToMode2 | work | gS(work) | work |
| switchToMode3 | codex | 无 | codex |

注册资格分别检查 ChatGPT capability/workOnly、工作访问、Codex 访问错误，均使用 fallback 优先级。主页 `chat/work` 与 `ij` 的 `work/codex` 是不同状态轴。`kti` 不调用 `gS`，它通过 detail-level setter 选择 `STEPS_PROSE` 或 `STEPS_COMMANDS`，并处理访问引导及导航/项目恢复。

`/codex-access` 有提前返回分支；当前为 work 时，非 codex 请求走 `iPt → wH → gS`，不进入 kti。kti 的访问拒绝、同模式、openHome、restoreNavigation 和七种恢复条件分别记录，避免用一个“切换成功”概括不同后果。

detail-level setter 先更新内存对象，再提交异步请求；失败只在对象仍是该次写入时回滚。kti 没有 await 该 Promise。导航继续不代表服务已接受，也不证明草稿、项目或持久值恢复正确。

Codex 保留路径需要访问引导、detail-level 和导航恢复职责；不能整体删除带 chat 名称的协调器。Chat 请求入口是剥离候选；Ezt composer 变体仍需逐入口对照。此处未把整个功能或模块判为 ChatGPT 专属。

核对了冻结源码范围、四条精确导入导出和十四个有界函数体。既有 gS 内存替身观察与同一源码哈希相符，只支持局部 guard/写入顺序；没有新增执行目标代码或真实客户端转换。八条子场景均未执行，不加入产品通过数。

[结构化合同与定位](mode-explicit-switch-v1.json)保存完整分支、参数、源码和限制。功能账本、实施计划及全部全局计数保持。下一步只补同一功能已具名的 Ezt 变体，形成逐入口保留/剥离决定；不重新调查本批提供方。
