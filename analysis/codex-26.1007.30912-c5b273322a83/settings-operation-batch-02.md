# 设置操作第二批：Worktrees、键盘快捷键、文件类型处理器

本批交付15项用户目标、2项支撑机制和56条待执行验收规格。当前[有限功能台账v9](feature-scope-v9.json)包含73项定义、316条未执行产品规格；全客户端功能分母、跨入口去重和产品模式分类仍未闭合。

| 页面 | 用户目标 |
| --- | --- |
| Worktrees | 浏览并刷新工作树及关联会话 |
| Worktrees | 设置工作树根目录 |
| Worktrees | 设置创建工作树前刷新上游 |
| Worktrees | 设置自动清理旧工作树 |
| Worktrees | 设置自动清理保留工作树数量 |
| Worktrees | 打开工作树关联的会话 |
| Worktrees | 在已有工作树开始新会话 |
| Worktrees | 删除指定工作树及归档其本地会话 |
| Keyboard shortcuts | 搜索可配置的键盘快捷键 |
| Keyboard shortcuts | 编辑或恢复单项命令快捷键 |
| Keyboard shortcuts | 批量恢复快捷键默认值 |
| Keyboard shortcuts | 设置数字快捷键切换聊天或标签页 |
| Keyboard shortcuts | 设置点击链接时使用系统浏览器的修饰键 |
| File type handlers | 查看并重试文件类型处理器发现 |
| File type handlers | 选择文件类型的首选查看器 |

Worktrees的根目录、自动清理开关和保留数量采用host专用写入：local走共享设置，其他host通过config/batchWrite更新desktop键，并分别处理缓存回滚和失效。刷新上游偏好仍走共享设置。根目录先trim并检查绝对路径，路径风格由host codexHome选择；保留数量采用parseInt并钳制到至少1，不能用HTML输入属性替代这段逻辑。关闭自动清理需要确认，取消不写入。

工作树列表聚合正常线程、pinned线程及条件下的附件owner，去重并过滤未pinned的子代理；并不保证列出所有owner。删除前重新读取pins，先等待所有传入native会话归档，再删除指定工作树并刷新列表；异常最终释放pending。归档部分成功或删除成功后刷新失败都没有补偿，错误反馈不等于所有副作用均未发生。新建和打开会话分别保留TU/导航边界，没有把回调送达当作创建任务或发送首条消息。environments标签委托到独立本地环境内容，保留为另一个页面的分析任务。

键盘页按展示模式、平台、能力和开关筛选命令，文本搜索与按键序列搜索分开。行编辑器记录set/append/replace/remove/reset/clear、序列前缀冲突、annotation限制及取消行为。Codex展示的批量重置先确认，再并发重置keymap及可用的链接修饰键；另一展示分支顺序重置符合条件的自定义命令，若有匹配焦点则只处理该项，搜索结果不会自动缩小这个集合。部分失败保留已完成效果。General中的弹窗快捷键与参数化命令编辑可能有重叠，已列专门去重项，未宣称73项是全局唯一功能分母。

文件类型处理器按host和最长匹配扩展名选择查看器。每行用请求序号抑制旧请求的错误/清理反馈；共享map写入另按queryClient排队、执行时读取最新map并合并，前项失败不会卡住后续项。两个不同queryClient之间的竞争不由这段代码解决，实际跨窗口和持久化仍需验证。Retry只重试主query和已启用的辅助query。

8份完整Program解析和29项隔离源码回放通过；所用hooks、缓存、RPC、线程、pins、删除、viewer resolver及按键解析均有明确替身边界，没有实际读取或修改个人项目、会话、偏好、快捷键或工作树，没有新增模型请求，也没有运行原客户端。隔离回放不计作产品场景实测。

[逐项合同、事实和源码引用](settings-operation-batch-02.json)区分控件、委托组件和真实服务后效。第三方实现没有生成到客户端源码；React/compiler、query/mutation、OS与服务依赖保持外部边界，包版本仍按既有依赖调查处理。

已定位的45个设置页面容器中，七个页面有功能合同关联，剩余38个继续按页面批次处理。这是控件分析覆盖，不代表这些页面的运行行为已全部验证。下一批优先Notifications、Appearance与Appshots，并与既有General/Agent合同做去重；公共运行和存储缺口继续独立验证。
