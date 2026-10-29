# React 官方候选与限定接口调查

基线 `codex-26.1007.30912-c5b273322a83`；仅调查 bundle-hint-002/003/009/010，四项占旧候选 17 项中的四项。原 65571 条全局证据与 36 组功能分母保持不变；本批不新增全局记录。

取得官方 npm `react@19.2.7` / `react-dom@19.2.7` 原始 metadata 与 tarball，两包归档的 SHA-512 SRI 与 SHA-1 均核对。保存的 GitHub `v19.2.7` tag commit 与两包 npm gitHead 相同，均为 `6117d7cca4906492c51fe6a03381e35adfd86e7d`。MIT LICENSE 保存为分析资料；签名与 attestation 只记录存在，未做密码学验证。官方 [React 19.2.7 release](https://github.com/react/react/releases/tag/v19.2.7) 与 [React metadata](https://registry.npmjs.org/react/19.2.7)、[ReactDOM metadata](https://registry.npmjs.org/react-dom/19.2.7) 可定位公开候选。

解析 6 份已存证完整工厂、3 份官方 production 模块，共 190654 AST nodes。React 两份工厂各 42 个保留导出，ReactDOM 两份各 14 个，官方成员均有对应直接导出。两份 client 工厂各保留 `createRoot`；官方还导出 `hydrateRoot` 与 `version`，未证明该差异由完整 bundler 归一化解释。

114 次保留导出对照中，92 次直接解析的 callable 参数数量/类型一致；React 两份合计 38 个极限定单 return internals 转发形状一致（仅映射 formal 参数标识符与唯一直接导出 internals 对象标识符）。两份 `createRoot` 的返回末项 `new` 与唯一选中构造器、其 `render(1)` / `unmount(0)` prototype assignments 已静态关联，4 次方法参数形状对应官方成员。没有把这些形状升级为函数体或整个包等价。

建议（inferred/proposal）：重建项目可将准确版本 `react: 19.2.7` 和 `react-dom: 19.2.7` 作为有来源与接口证据支持的依赖候选；`createRoot` 从 `react-dom/client` 引入，保留应用 annotation/state/mount/host 生命周期适配。归档与保存的第三方源码仅属于本分析目录，不进入恢复源码。Scheduler 官方声明为 `^0.27.0`，并不是目标或重建项目的精确安装锁。

本批 33 条新 journal：16 条限定 source 对照，17 条官方 artifact/边界/建议记录；另引用 152 个旧证据 ID，未把引用计为新 source。完整官方归档成员 inventory 为 70 项，仅 10 项源码/metadata/LICENSE 内容保存于 analysis JSON。

未决：目标实际安装锁、完整代码/修改状态、全依赖闭包、JSX/compiler/Scheduler 具体绑定、应用消费者模式、实际 mount/update/unmount 兼容性。目标源码未执行，目标/UI/模型任务为 0。公开包 metadata/SRI/git tag 成功不会改变这些 unknown。

原始响应及执行收据见 [upstream/fetch-receipts.json](upstream/fetch-receipts.json) 与 `attempts/`；精确接口/源坐标见 [comparison.json](comparison.json)、[evidence.jsonl](evidence.jsonl) 和 [react-upstream-identity-contracts.json](react-upstream-identity-contracts.json)。第一次网络 fetch 因 sandbox DNS 失败，其真实 exit/stderr 保存；获准 public HTTPS 后成功，不涉及 npm install、目标执行或个人数据。
