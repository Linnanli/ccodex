# Chat专用分支的排除决定与Codex保留依据

本次确定3组具体源码分支在重建客户端中排除：临时Chat页脚、Chat专用输入提示配置、切换到Chat的快捷键注册。每组均在[决定清单](chat-branch-decisions.json)记录条件、精确源码范围、必须保留的共享依赖和升级检查；这不是整模块或完整功能的排除证明，尚未修改客户端实现。

| 决定 | 排除位置 | 必须保留 |
| --- | --- | --- |
| CBX-01 | `jRt` 中严格chat且临时会话的页脚分支 | 共享布局、状态provider和NRt |
| CBX-02 | `wzt/Ezt` 的Chat专用trigger、inline hints和variant选择 | Codex的Q9配置、controller生命周期及Work草稿恢复 |
| CBX-03 | `Ezt` 中目标为chat的switchToMode1注册 | Work切换、newTask、共享切换处理及命令框架 |

已有“创建新会话并提交首条消息”（FSC-0048）新增明确保留依据：Codex专用Tzt把isCodexHome传给共享M9，经已有jRt／NRt目的地选择进入已登记的本地提交链。其处理由“待模式审查”推进为“已有正向Codex消费者，保留并等待集成验证”。完整独占／共享归属仍为unknown；无需先证明所有其他消费者不存在，才能保留这个已确认被Codex使用的操作。

25项隔离用例通过，覆盖页脚条件、共享提示配置、Chat快捷键目标和Codex入口。其内4项在VM内仅移除页脚条件式，比较合成Codex／Work渲染树保持一致；不作为完整客户端剥离验收。首轮8项因fixture缺少导入谓词Wg失败，修正测试替身后全部通过，两个版本均保留。

复用了已保存完整Program的词法身份，只解析5个已选择函数和12处局部范围；没有重新扫描大bundle、增加模型提交或启动原客户端。主composer、远端Work候选和账户归档适配器仍按已有共享消费者证据保留。

[功能台账v25](feature-scope-v25.json)和[覆盖表v16](restoration-coverage-v16.json)接入上述决定；仍为373项功能、48个任务组、1216条未执行产品规格。模式总数仍是shared 1／unknown 372，整项功能排除仍为0；另有3组源码分支排除决定，二者分别统计。原九项完成标准未改为通过，完整分析尚未完成。
