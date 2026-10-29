# 独立命令场景后端比较

冻结随包 CLI 与公开 npm `0.162.0` 分别使用新建专用 HOME/CODEX_HOME；两者五项检查均通过。

| 场景 | 保存结果是否相同 |
| --- | --- |
| initialize | 是 |
| command-completion | 是 |
| command-nonzero-exit | 是 |
| command-input-validation | 是 |
| command-stream-and-terminate | 是 |

比较完成输出、非零退出、参数错误码、流式样例输出和取消结果；initialize 仅比较返回字段名。

这组场景使用 readOnly/no-network 策略，未提交模型任务。结果不证明桌面、PTY、审批或整个后端兼容。

公开 npm 包与固定 Rust 提交的源码关系仍为 unknown。冻结 CLI 哈希是入口 shell wrapper，公开 CLI 哈希是 native executable，不能直接用两者哈希判断二进制差异。

来源：[完整比较](command-backend-comparison.json)、[冻结运行](command-protocol-frozen-home-normal-host.json)、[公开运行](command-protocol-public-npm-manifest-snapshot.json)。
