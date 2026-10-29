已比较公开发布 CLI 与冻结客户端 CLI 的 9 个实验候选方法；下表记录三类 schema 闭包的精确结构比较。

比较二进制来自官方 npm `@openai/codex@0.162.0-darwin-x64`，SRI 校验通过。

Rust 映射参考：`rust-v0.162.0` / `c1382380de69521303b416720a52f42d51af6248`。npm 元数据未提供 gitHead，比较二进制与此源码提交的关系为 unknown；npm SRI 也不等同于 GitHub release asset 摘要。

冻结 CLI SHA-256：`50ab38ba21d0d9f8346f32f41848382f15b556190f3c7a07e885a4fb73e379c8`。

公开 CLI SHA-256：`fd4bb93679bfcc546765a3363a0df9a855f364b61ea6681009b28ba4c2e5b60d`。

| 方法 | Request | Params | Response |
|---|---|---|---|
| project/delete | equal | equal | equal |
| project/list | equal | equal | equal |
| project/move | equal | equal | equal |
| project/read | equal | equal | equal |
| project/update | equal | equal | equal |
| remoteControl/enable | equal | equal | equal |
| rollout/compress | equal | equal | equal |
| thread/realtime/stop | equal | equal | equal |
| thread/settings/update | equal | equal | equal |

比较阶段仅处理 schema；未执行公开 app-server 运行时。去除字段仅限 `description`、`title`、`$schema`、`$comment`；默认值、约束、其他 annotation 与数组顺序保留。

固定 Rust 源码仅用于 method → response 类型映射，不能据此认定公开生成协议支持这些方法。

证据：[公开生成记录](</Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/public-protocol-generation-npm.json>)，[冻结生成记录](</Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/protocol-generation.json>)，[完整比较数据](</Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/public-experimental-compatibility.json>)。

复跑：`python3 scripts/analysis/compare_public_experimental.py --generation-record /Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/public-protocol-generation-npm.json`。
