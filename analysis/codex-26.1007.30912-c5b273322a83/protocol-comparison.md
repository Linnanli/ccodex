# 公开 app-server 协议比较

状态：静态契约比较完成一轮；公开后端运行及实验契约尚未验证。桌面基线为 `codex-26.1007.30912-c5b273322a83`，随包 CLI 为 `0.162.0-alpha.17.2`。

比较候选固定为 OpenAI [rust-v0.162.0](https://github.com/openai/codex/releases/tag/rust-v0.162.0)，提交 [c1382380de69521303b416720a52f42d51af6248](https://github.com/openai/codex/commit/c1382380de69521303b416720a52f42d51af6248)。该公开提交晚于桌面基线，不视为桌面 CLI 的精确源码。下载清单、文件长度及 SHA-256 在 `public-protocol-source.json`，随包 CLI 的 schema 生成命令及结果在 `protocol-generation.json`。

`compare_protocol.py` 校验了 780 份已登记输入的长度和哈希，包括公开下载及随包稳定/实验 schema。比较递归收集 `$ref`，只忽略 description、title、$schema、$comment；保留默认值、required、约束和枚举顺序。字段差异、JSON pointer 与契约哈希在 `protocol-compatibility.json`。

| 范围 | 结果 | 适用限制 |
| --- | --- | --- |
| 稳定 ClientRequest | 105/105 请求契约结构相同 | 不验证客户端实际传参或返回结果处理 |
| 稳定 ServerRequest | 10/10 契约结构相同 | 不验证审批 UI 和执行效果 |
| ClientNotification | 1/1 契约结构相同 | 不验证通知投递 |
| ServerNotification | 84 个方法；79 契约相同，5 有差异 | 同名方法仍可能携带新字段 |
| 桌面直接调用候选 | 52 个；43 个公开稳定请求契约相同；9 个位于实验接口 | 仍需确认调用方模式与可达性 |
| 选取的完整 schema 文件 | 9 份中 7 份结构相同 | 通知文件和 v2 响应集合存在差异 |

公开仓库的已提交 JSON 由默认稳定导出生成，实验接口被过滤。9 个直接调用候选均能在固定 `common.rs` 中找到 variant 及实验标记：`project/delete`、`project/list`、`project/move`、`project/read`、`project/update`、`remoteControl/enable`、`rollout/compress`、`thread/realtime/stop`、`thread/settings/update`。缺少稳定 JSON 条目不能解释为公开源码没有该能力。公开实验参数、返回契约和 handler 尚未生成或运行。

公开 `ThreadItem.subAgentActivity` 增加可选 `model` 与 `reasoningEffort` 字段，影响 `item/completed`、`item/started`、`thread/started`、`turn/completed`、`turn/started` 的递归通知契约。两项不在 required 中；仍需核对桌面解码、显示和未知字段处理。

v2 schema 集合还把 `SkillMetadata.path` 与 `SkillSummary.path` 的引用从 `AbsolutePathBuf` 改为 `LegacyAppPathString`。两者在 JSON schema 中都仅约束为 string，但 Rust 类型和路径处理含义不能仅由 JSON 约束等价推断；处理相对路径的行为尚待核对。

此次比较支持将公开 app-server 继续作为集成候选。采用决定还需要实验契约、52 个直接调用的参数与返回处理，以及 108 个 `sendRequest` wrapper 方法的绑定身份。独立命令测试使用随包 CLI，不能据此宣称公开 CLI 或桌面任务兼容。
