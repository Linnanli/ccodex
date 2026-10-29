# Sentry 来源候选与依赖导入决定

固定基线 `codex-26.1007.30912-c5b273322a83`。原 17 个内嵌提示中的 001、005、008 对应本次限定分析；9 个完整 carrier helper、3 个邻接单位与 5 个保存官方模块分别作为分析范围。官方 `@sentry/core@10.29.0` 候选归档的 SHA512 SRI 与 SHA1 已核验，两个 source map 内容与固定 Git 提交相符；npm 响应没有 gitHead，基线实际安装锁及整包构建来源仍未知。来源与定位见[契约目录](sentry-upstream-identity-contracts.json)的 `officialPackage`、`officialRelease` 与 `contracts`。

会影响重建的接口限制是：官方 root 入口公开 `getMainCarrier`、`getGlobalSingleton`，没有公开 `getSentryCarrier`，package exports 也没有 carrier 深层路径。依赖方案可以保留两个公开导入作为候选；其余调用需要先确定公共上层接口及应用封装契约。当前没有识别完整 Node、browser 或 Electron SDK 选择与应用初始化层，不能生成内部函数的包导入。

9 组参数形状中，3 组操作投影相符，另 6 组保留 literal 与 SDK_VERSION 读法的差异。27 个 JSON 叶差异不等于 27 处行为修改，也不足以证明库被修改或未修改。已有 truthy version、全局 singleton、外层绑定与懒初始化时序需要纳入后续兼容验证，完整等价和模式归属仍未知。

本批 31 条独立记录包含 9 条来源坐标和 22 条 artifact／提案；复用 17 个旧引用，全局 journal 没有新增记录。[独立审查](sentry-upstream-identity-contracts-peer-review.json)的当前错误为 0；其 1,344 项接受检查与历史累计计数存在重叠，不能当作运行验证次数。失败历史与已更正的元数据问题仍在本地保存。

本次只交付白名单内的选定元数据、原 journal 与小型审查报告；目标函数全文、第三方实现、原 HTTP 响应和失败诊断 stdout 留在本地。原摘要见 [raw 目录](raw/recovery-decisions/sentry-upstream-identity-contracts/summary.md)，实际复制范围见[交付记录](sentry-upstream-identity-contracts-delivery-provenance.json)。交付没有安装包、生成锁文件、执行目标或扩大功能与行为确认范围。
