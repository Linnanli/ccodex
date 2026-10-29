# 大消息 codec 与 assembler 验证

基线：`codex-26.1007.30912-c5b273322a83`。从冻结源码提取完整表达式，在无外部能力的 Node VM 中执行 11 组场景、40 条断言，全部通过。结果仅证明提取的纯代码行为；桌面 IPC 投递、sender 排队与任务功能仍待验证。

复现脚本是 `scripts/analysis/chunk_transport_fixture.cjs`。通过 `--parser-path` 指定已固定的 Babel parser，读取当前冻结基线；每次执行核对源文件与 15 个来源范围的 SHA-256。输入映射、结果和环境分别保存在 `chunk-fixture-input-map.json`、`chunk-fixture-results.jsonl`、`chunk-fixture-summary.json`。没有将目标实现文本写入这些产物。

| 场景 | 实际行为 |
| --- | --- |
| 普通对象、数组、undefined 与 Unicode | 深层值及 UTF-16 code unit 保留，包括拆开的 surrogate 和未成对 surrogate |
| 特殊分块数组 | 按输入顺序展开；重复对象保留值形状，但不保留共享身份 |
| 已符合帧形状校验的 chunk 序号乱序或重复 | 删除该 transfer 且不返回 ack；之后正确帧不能续传；start 序号分支未由这些场景验证 |
| chunk 缺少 start | 不返回 ack；不凭此假设完整 sender 会自动重试 |
| 不满足帧校验的形状 | 原值 passthrough，没有按 chunk transfer 接收 |
| 新 start | 清除旧 transfer 状态 |
| 不完整 token 流与逻辑错误 | chunk 抛错后可残留 transfer；end 抛错前会删除 transfer |
| 不支持的值 | cycle、BigInt、function、symbol 被拒绝 |
| 特殊对象 | Date 按 enumerable 属性产生空对象，Uint8Array 产生属性对象；`__proto__` 为 own property |

输入全部为测试用合成对象。VM 未注入 require、process、文件、网络、IPC 或 timer，禁用字符串和 Wasm 动态代码生成，初始化和每组场景各限时 1000 ms。

下一步验证双端真实发送与确认、lost ack、窗口加载重试、critical 优先级、preload 缓存和 origin gate。上述测试不覆盖完整应用初始化、UI 可达性或各模式归属。
