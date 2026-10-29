# 公共 Electron 运行时对照结果

固定的 Electron 42.3.0 darwin-x64 **不能直接替换现有 Owl**。官方归档通过 SHA-256 核验；实际进程测得 Node 24.15.0、Chromium 148.0.7778.180、传统 modules ABI 146、N-API 10。这些数值不能代替原 Owl 的实际运行版本或 ABI。

| 能力 | 实测结果 | 工程决定 |
| --- | --- | --- |
| 任务管理器 | showTaskManager 缺失；getAppMetrics 返回 CPU/内存字段 | 公开数据接口可作为候选，仍需第一方诊断界面及行为验收 |
| managed update policy | Owl linked binding 缺失 | 策略 provider 与普通更新 transport 分开；沿用已确认的 nullable 分支边界 |
| 浏览器 clone/所有权 | clone、adoption lease、setAgentActive 缺失；公开 history restore 保留编辑后的表单，但没有保留编辑后的 JS 堆值 | 历史恢复只证明一个可用原语；live clone 与 lease 生命周期仍有差距 |
| Node 网络/IPC | --allow-ipc 被拒绝；启用 --permission 后 has(net/ipc) 为 false，但自有 TCP/Unix socket 均可往返 | 不能把 false 当成网络隔离，不能只删除不支持的参数；仍需实际权限实现 |

[结构化结果](public-runtime-comparison.json)区分四次公共运行时启动：首次主探针在能力检查前因参数错误失败，修正后的主探针成功，另有一次预期的非法参数退出和一次成功的本地传输探针。进程检查无残留，自建 socket 已清理。首次下载的 DNS 失败也保留，未计作成功取证。

16 份固定版本官方源码/文档、下载记录、探针、终态和哈希见[来源索引](public-runtime-comparison-provenance.json)。Node 24.19.0 的源码对照与实际 Node 24.15.0 探针分列。公开 [history 接口](https://github.com/electron/electron/blob/v42.3.0/docs/api/navigation-history.md)和 [WebContentsView](https://github.com/electron/electron/blob/v42.3.0/docs/api/web-contents-view.md)可用于评估适配路线，尚未证明 Owl 行为等价。

本批没有运行原客户端、调用模型、生成客户端依赖实现或增加产品功能验收。完整功能分母、模式归属和 212 条未执行验收规格保持原状态。独立 Owl 来源、其他私有 API、原生 ABI 及全客户端行为仍是缺口。

下一项先复用现有证据完成阶段收束：按原计划九项标准列出已满足项、内部待补项和缺失的外部输入，把后续调查限定到会改变功能、依赖或独立构建决定的问题；不继续重复已闭合的源码定位。
