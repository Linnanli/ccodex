# Git 设置页面分析

已把冻结 Git 页面中的全部实际控件收束为10项用户偏好和1项支撑操作，并接入[功能台账 v8](feature-scope-v8.json)。有限台账从48项增至58项；新增48条产品验收规格，累计260条，均未执行。完整客户端功能分母仍未建立。

| 功能 | 设置键 | 默认值 |
| --- | --- | --- |
| 设置新建分支前缀 | git-branch-prefix | "codex/" |
| 设置始终强制推送 | git-always-force-push | false |
| 设置默认创建草稿 PR | git-create-pull-request-as-draft | true |
| 设置 PR 合并方式 | git-pull-request-merge-method | "merge" |
| 设置提交指令 | git-commit-instructions | "" |
| 设置 PR 描述指令 | git-pr-instructions | "" |
| 设置禁用 Git 差异面板 | git-review-mode | "full" |
| 设置代码审查展示位置 | reviewDelivery | "inline" |
| 设置监听 PR 自动合并偏好 | git-pr-watch-auto-merge | false |
| 设置监听 PR 的自定义指令 | git-pr-watch-instructions | "" |

页面工厂、静态路由和控件已有条件关联；实际挂载、入口条件值和产品模式未观测。Git分支不在缩减host列表内，codexLocal是访问分类，不能直接当作产品模式排除证据。禁用Git差异控件还受单独selector控制。

分支前缀在失焦或启用的保存快捷键时提交，pending时禁止编辑；合并方式还会跳过相同值。三个指令文本框停止输入3秒后自动提交，也支持保存按钮、快捷键和卸载时提交。失败快照不会自动重复提交，显式保存或新编辑才能重试；旧请求成功不会清掉较新的草稿。其他控件的pending和相等值守卫各不相同，已逐项记录。

保存偏好与更新已有PR watcher分成两个结果。后者只筛选ACTIVE heartbeat及两行标记都匹配的记录，保留标记前提示和身份、模型、日程等字段，重建后续文本；提示相同则跳过。多个更新并发，一项失败可能留下部分成功；所选路径没有补偿已保存偏好或已更新的其他watcher。分析未读取或修改真实automation。

共享写入默认乐观更新缓存，写入失败时恢复旧快照，随后刷新并通知。底层选择宿主settings服务或set-setting；所选main路径校验值再调用AL.write。AL.write执行store.set和afterWrite，这层没有显式等待flush；writeForAgent则会检查agentAccess并等待flush。因此UI可写的read-only代理设置不应被误禁用，而保存成功不能证明重启耐久性。真实store和磁盘调度保留为独立问题。

6份完整Program解析结果覆盖5个不同源码文件。最新隔离回放的21个不同用例全部通过，涵盖缓存回滚、宿主/通用请求选支、自动保存、watcher筛选/更新和UI/代理写入差异；早先18个用例与之重叠，不相加。React、query/mutation调度、真实store和服务均由替身代替，所以这些结果不计作产品场景通过。

第三方实现没有生成到独立客户端代码中。本批只保存分析所需原始片段和引用；应用职责建议分为Git控件、偏好描述/传输、自动保存状态和watcher更新适配，外部React及其他provider保留依赖边界，完整包身份/版本闭包仍沿用依赖分析的限定结论。

[逐项合同与源码引用](settings-git-page-contracts.json)保留守卫、参数、错误、无显式取消、持久化和消费者缺口。[验收场景](feature-scope-v8-scenarios.json)保持未执行状态；模型授权余0、模式排除0，本批没有新增模型提交或原客户端运行。

本页面的控件→处理函数→共享保存/支撑操作→验收规格映射已交付。下一步用同一批已定位页面组件完成剩余设置用户操作台账；Git真实磁盘耐久性和运行消费者进入专门验证队列，不作为继续盘点其他页面的前置阻断。
