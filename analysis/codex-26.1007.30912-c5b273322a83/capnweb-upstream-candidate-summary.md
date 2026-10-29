# capnweb 官方候选与 RPC 包导入边界

固定应用基线：`codex-26.1007.30912-c5b273322a83`。这是第三方依赖候选调查，已完成有限独立元数据复核；没有执行目标或上游包，也没有提交额外模型任务。

官方 npm `capnweb@0.11.1` 归档通过其声明的 SHA-512 SRI 与 SHA-1 校验；包声明 MIT、Cloudflare 仓库和 root 导出。npm 元数据的 `gitHead` 为 `20fe0fb488d9238ac69b05776287999b24e4e3e8`，尚未独立检查该提交树。根依赖范围 `^0.11.1` 与许可声明中的 `0.8.0`／`0.11.1` 仍不能证明基线实际安装版本。

| 所选目标单位 | 官方默认 ESM 候选 | 有限对应 |
| --- | --- | --- |
| `aF` | `RpcStub` | constructor、dup、onRpcBroken、map、toString，共 5 个所选成员 |
| `oF` | `RpcPromise` | constructor、then、catch、finally、toString，共 5 个所选成员 |
| `BFt` | `RpcSession` | constructor、getRemoteMain、getStats、drain，共 4 个所选成员 |
| `VFt` | 内部 `MessagePortTransport` | constructor、send、receive、abort，共 4 个所选成员 |
| `hFt` | `newMessagePortRpcSession` | transport 构造参数数 1、session 构造参数数 3、getRemoteMain 参数数 0 |

前四组的 18 个成员仅确认名称和声明参数个数相符；默认参数、返回值、异常、能力引用、wire 编码和生命周期等价性没有因此得到证明。所选目标来源为当时消费并保存的 metadata 快照，后续作者修订需要单独核对差异。稳定 ID、原 source span 与候选位置见[结构化记录](capnweb-upstream-candidate.json)和[14 条证据](capnweb-upstream-candidate-evidence.jsonl)。

包只声明 root 导出，默认 ESM／CJS、workerd 和 bun 使用不同入口。所选默认 ESM 公开 `RpcTarget`、`RpcStub`、`RpcPromise`、`RpcSession`、`newMessagePortRpcSession` 等 16 个名称；`MessagePortTransport` 不在公开导出中。正常导入候选应使用公开 root API，应用自身的 manager／coordinator façade、host 与 scope 选择、watch、lease、断连和销毁职责继续由第一方适配器负责。

默认 ESM 的 `RpcTarget` 初始化还有运行环境条件：存在 `workersModule` 时使用它提供的类型，否则使用本地空类。普通包导入须保留这类条件及包的副作用；不能把目标中的一个空类直接当作全部运行环境行为。基线实际锁、完整修改状态、多个版本是否并存、原生 MessagePort 送达与能力释放兼容仍待验证。

官方默认模块 99,112 B，只做了 1 次完整 Program 解析；初稿停在 5 个公开变量的 identifier alias。后续只解析完整 alias 声明窗口及所选表达式，保留首个错误假设的失败记录，并补齐 6 个所选单位。官方 source map 的 10 份 `sourcesContent` 属于上游候选，不能计入应用 source map 覆盖。

独立复核实际通过 334 项检查，覆盖 14 条记录、10 份精确元数据副本及上述有限形状对应；归档 SRI 属于已保存的作者观察，peer 没有重新读取或验算归档。两次检查器假设错误的失败记录保留。结构化原稿中的 `independent-review-pending` 按原字节保留，后续结果单独见[复核报告](capnweb-upstream-candidate-peer-review.md)及[复核交付索引](capnweb-upstream-candidate-review-provenance.json)。

第三方源码、source-map 内容与 tarball 均仅保存在本地分析副本。正式目录只包含包元数据、接口位置、有限对应与执行记录。该调查没有改写全局 journal、既有依赖 CSV 的实际版本或完整功能分母。

公开来源：[npm 0.11.1 元数据](https://registry.npmjs.org/capnweb/0.11.1)、[Cloudflare 仓库](https://github.com/cloudflare/capnweb)、[官方 MessagePort 文档](https://capnweb.com/transports/message-port/)。官方在线文档仅提供接口背景，固定版本的判断使用已保存发行物。
