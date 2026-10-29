# 标签页状态、持久化与恢复边界

本批关闭既有6个命令、4项功能的限定源码问题；不新增功能台账、场景或实施计划版本。源码状态归属有交付，实际落盘、启动送达和完整恢复仍待验证。

| 入口 | 状态与边界 |
| --- | --- |
| undoAppAction / redoAppAction（FSC-0453） | 按scope选择的内存动作历史；动作callback的业务后效另行委托。 |
| reopenClosedTab（FSC-0454） | Ezn保存最近25条关闭描述，Yji尝试恢复；描述可序列化不证明关闭列表已落盘。 |
| closeOtherTabs（FSC-0455） | XRn检查并逐个关闭，写活跃标签状态；Geo可将可序列化投影写入YP。不是整体持久化事务。 |
| nextTab / previousTab（FSC-0456） | 面板分支改活动ID/MRU/选择历史，投影可进入YP；workspace分支仍委托其selectAdjacentTab。 |

源码明确区分三层：XRn的标签实例与焦点状态；n5a/t5a的version1路由及布局投影；共享IJ/_I/yI/hI镜像与publisher委托。已有接收合同在主进程写globalState；实际桥接实例仍未观察。`storedTabs$`不是文件存储API。Geo仅在未抑制、未断开且投影变化等条件下写入YP。主进程对`thread-browser-tabs-v1:`和`thread-tab-routes-v1:`检查primary persistence owner；窗口所有权不等于Codex/ChatGPT模式归属。

恢复入口Leo读、解析及允许时迁移YP后调用zeo；Beo按面板拓扑恢复描述，选择版本和断开状态约束Heo应用布局。Veo可显示“Tab unavailable”。重开关闭标签、恢复历史记录和继续模型执行不能互相代替。

保留4组明确边界：实际实例及启动hydration；物理写入与重启时序；具体descriptor/workspace委托；窗口所有权、模式与真实关闭/恢复效果。既有globalState/shutdown合同复用，不因缺少运行观察而重复追查已证明的JS来源。

三个冻结Program完整AST解析及范围/哈希核对通过，保存15条事实、44个来源范围和6条显式ESM连接。没有目标代码求值、客户端启动、模型/服务请求或构建；488项功能、534个不同用户操作、125项支撑、1650条未执行规格、51项任务及原九项标准状态保持。

[逐项合同](tab-state-persistence-v1.json) · [证据](tab-state-persistence-v1-evidence.jsonl)
