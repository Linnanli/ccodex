# 提交链路的恢复职责与行为场景

固定基线 `codex-26.1007.30912-c5b273322a83`。以下维护模块由[条件连接目录](submission-host-instance.json)提出；模块名称是新设计，源码范围与契约 IDs 见[结构化建议](submission-recovery-guidance.json)。它们不代表原作者的文件划分，也不是新增功能数量。

| 拟恢复职责 | 已见源码责任 | 实施前需补足 |
| --- | --- | --- |
| renderer provider 生命周期 | OMc 的安装／清理；Bfn 的 registry 分支 | 实际 scope、mount／effect 与产品条件 |
| host RPC 选择与缓存 | KI 的 primary、client、cache、延迟能力与退役 | 真实分支、错误／duplicate／dispose 的 RPC 语义 |
| 域 manager 注册与替换 | X3、loi、Sii、N3 的创建、发布与清理 | ordinary host 入口、其他 manager 写入与启动顺序 |
| 内部 manager RPC 应用封装 | yMc／vMc 捕获对象，X2t／W2t 转发原参数 | nIt／eIt 来源、版本、许可和实际 port delivery |
| host registry RPC 适配 | SMc 的 ready、watch、lease、replacement 清理 | 外部 endpoint 实现、对象身份和运行条件 |

应用自己的封装与 RPC 库分开维护。当前没有确认 nIt／eIt 的包来源，也没有决定独立运行时或完整后端；不得复制库实现或将未知协议直接换成通用 JSON RPC。队列／admission、通知与持久化沿既有目录继续独立建模，adapter 的同步返回不算任务完成。

| 场景 | 触发与需要的观察 | 当前证据 |
| --- | --- | --- |
| 普通提交的实际实例 | 同一 scope／host、provider、N3 manager、KI 分支与同 turn 完成对应 | 唯一样例已完成并可重新打开；实例链没有记录 |
| unavailable 与注册状态 | provider 存在；分别观察已登记／未登记 host 的 primary 条件与 fallback | 静态条件已更正，实际状态未触发 |
| primary 异常 | forHost 抛错后分别有 client、有 cache、两者均无 | 异常后选择顺序有源码，能力的实际行为未验证 |
| manager 替换与重连 | 仅使用自有 host，观察旧 client 清理、新状态及 stale callback | 仅静态生命周期契约 |
| host registry ready／断开 | 真实 registry 的 ready、replacement、lease／watch 清理 | endpoint 和触发条件未确定 |
| 执行中普通取消 | 额外合成任务获授权后使用产品取消；请求、接受和终态分别观察 | 未执行，唯一样例授权不覆盖额外任务 |
| 执行中断与重启 | 额外自有任务获授权后中断归属确认的进程，再关联原 turn 与新连接 | 已完成任务重新打开不覆盖此场景 |

这 7 行是有触发条件的验证场景，尚未新增运行。受控 fixture 可用于后续实现回归，但不能代替原客户端的实际行为记录。场景通过后仍需继续完整功能清单、失败／审批／持久化、模式边界、独立构建与升级验证。
