# 预测 fork 的父状态继承与设置恢复

固定提交`740e5af33c71225640e0c1c1555c514c2c93ab74`的两条命名核心边界已追踪到直接Session实现。静态契约已取得，尚未执行源码测试、后台或成功预测。

| 内容 | 源码路径与限制 |
| --- | --- |
| 父线程资格 | live registry查找排除internal线程；持久化历史存在不代表符合此入口 |
| 配置与环境 | state锁内捕获configuration、live环境snapshot和reasoning pin；锁外物化配置。环境requests和live bindings分别传递 |
| 插件及扩展 | history mode、disabled plugins、client MCP extensions、turn extension数据显式传入启动参数 |
| 推理强度 | 父override feature关闭时可能按配置/模型默认重新计算pin，child后续启用feature |
| 动态工具 | 默认空spec列表由启动代码从历史元数据读取；不据此宣称所有实时工具/provider状态被克隆 |
| instructions | 后续启动查找前捕获已应用快照；源任务绑定provider不成为新root回调 |
| 创建后恢复 | 明确恢复collaboration mode及Windows sandbox；直接Session更新与排队settings操作是不同入口 |

Session设置更新先校验候选，再在同一state锁内发布配置；config contributor通知、权限代理刷新和MCP预热在其后发生。直接restore没有调用独立的persistence permit或ThreadSettingsApplied发送路径，返回Ok不能单独证明持久化或投递。

新线程先登记，再进行调用方的设置恢复。恢复约束失败可转为RPC错误，所选handler没有在该分支显式撤销登记；实际残留、全局清理与取消行为仍需观察。不能把它改写成未经基线证实的原子事务。

已有测试源码描述instructions在源卸载期间仍保留，以及普通冷恢复/历史fork不从旧rollout恢复环境。这些测试未运行，也不替代预测fork的live环境继承验证。另记录9项后续观察条件，全部为未执行，未增加产品场景通过数。

本批只读10个同提交响应，包含8份Rust源码和2份目录页面。12条结论及来源范围已保存；核心台账、功能/模式/来源/产品场景数量和授权不变。配置物化器及外部provider后效作为明确边界保留，不继续递归展开。本阶段完整分析仍未完成。

下一批只核对同提交的发布构建输入：工具链、目标/feature及workspace alpha版本与锁中0.0.0的处理方式，最多6份已由目录确认的构建文件。

[结构化结论](backend-inheritance-v1.json) · [逐项证据](backend-inheritance-v1-evidence.jsonl) · [父状态入口](https://raw.githubusercontent.com/openai/codex/740e5af33c71225640e0c1c1555c514c2c93ab74/codex-rs/core/src/thread_manager.rs) · [会话实现](https://raw.githubusercontent.com/openai/codex/740e5af33c71225640e0c1c1555c514c2c93ab74/codex-rs/core/src/session/mod.rs)
