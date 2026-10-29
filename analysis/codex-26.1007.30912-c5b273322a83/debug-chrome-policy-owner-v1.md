# 调试页策略：启动、写入与导航边界

调试页开关要求值严格等于 true，且构建类型允许调试菜单。允许的构建是 dev、agent、nightly、internal-alpha；public-beta 和 prod 不允许。主进程解析顺序为有效 BUILD_FLAVOR、包元数据、NODE_ENV 默认值。损坏的候选 JSON 会抛错。

启动从 bootstrap 缓存上下文取得构建类型，在 app readiness、store 加载及选定迁移之后读取有效设置，再调用原生接口并更新本地 flag。设置写入则重新解析构建类型。冻结 renderer 导入的策略在该设置行固定检查 prod，因此控件条件为 false；这不是 ChatGPT 模式排除依据。

| 写入入口 | 顺序 | 原生调用抛错后的选定源码结果 |
| --- | --- | --- |
| setGlobalStateValue | native → flag → globalState.set → 窗口广播 | flag/store/广播均未执行 |
| setConfigurationValue | globalState.set → native → flag | set 已发生，flag 未更新，无本地回滚 |
| settings adapter | store.set → store.get → afterWrite → native → flag | 写入调用拒绝，set 已发生，flag 未更新 |

store 实际落盘与调用端错误处理不由这张表证明。三处 native 调用均无本地方法存在性检查或 try；启动异常另交给 bootstrap 外层处理。native 请求、本地 flag、stored 与 effective 设置应分别建模，不能自动加上回滚或把它们合并。

本地 flag 的两个选定消费者控制 downloads/history 到应用设置的映射及请求条件；其它 rewrite、权限和受限导航策略仍独立存在。这里不能证明 version/histograms 的 native 允许列表。帮助文案宣称可信诊断页可开放、chrome-untrusted 仍阻止，只作为产品意图记录。

建议将构建策略、main 启动/路由策略、设置副作用及 renderer 控件分别维护；原生执行经 runtime-adapter 的 chrome-page-policy 合同引入。第三方实现仍作为依赖。63 个源码选择含重叠生命周期上下文，不代表 63 个恢复模块。

17 条源码事实、4 条静态关联和 15 个隔离场景已交付。场景使用合成环境、包元数据、store、native 方法和 JSX；没有启动客户端、提交模型任务或执行真实原生调用，不计产品通过。首次脚本漏写广播替身的失败已修正，并增加成功/失败时广播检查。

选定 JS owner 与条件问题在此收口；真实特权页、profile/guest 隔离、native 返回/失败、设置送达与重启列为实施验证；独立 Owl 来源或经等价验证的 provider 列为构建前提。RAM-02/04/06 的选定内部源码项均已有结论，15 组运行时能力的完整采用资格仍未成立。下一项为 SD-03 已保存的 11 个协议变体差异及采用决定。

[结构化结论](debug-chrome-policy-owner-v1.json)、[源码事实](debug-chrome-policy-owner-v1-evidence.jsonl)、[隔离检查](debug-chrome-policy-owner-v1-replay.json)。
