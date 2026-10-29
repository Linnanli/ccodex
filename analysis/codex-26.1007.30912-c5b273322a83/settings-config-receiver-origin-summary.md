# 项目配置保存的主进程接收链

固定基线 `codex-26.1007.30912-c5b273322a83`。本批补上同一原 Program 中的静态注入：同一个构造函数创建 $L，将其传给 Ude，再将 this.fetchWrapper 作为第八实参传给 MMe。MMe 保存该接收对象，Ude 将 VS Code 桥请求转给 $L。这闭合的是源绑定和注入关系，实际实例与后续重写仍未知。

$L.handlers 登记 read-file 和 local-environment-config-save，使用 path/configPath、hostId 与 raw；保存 handler 先 await mkdir，再 await writeFile，随后构造 success。调用 namespace i.di，其 i 来自 require(./src-BJv5Mk7n.js)。此批没有证明 di 的实现或真实client，不能从方法名宣称已落盘。该路径适用于所选项目配置桥；非项目 pMn 的 config/value/write 经 KI/rpc，仍属另一条链。

[来源读者](settings-config-receiver-origin.json)连接[冻结作者合同](raw/settings-config-receiver-origin/author/settings-config-receiver-origin.json)与[独立审查](raw/settings-config-receiver-origin/independent-review/independent-review.md)。25记录为23 confirmed、1 inferred、1 unresolved；20新选源、2旧case、2保存renderer绑定、1缺口分列。原main新解析1次，958314 AST节点、3879顶层语句，仅导出选定绑定与坐标；13成员与构造／声明范围重叠，不能当完整main语义覆盖。作者665项、独立913项分别通过；peer重核26/29保存坐标，另3依赖作者metadata，未重读或重解析原main。

独立审查修正了3处措辞：桥方法构造／分发 envelope，不保证直接返回它；$L dispatch 在 source 为 nullish 时直接调用 callback，否则交给尚未展开的 i.U；Ude catch 仅捕获 dispatch 实际抛出或返回的 rejection，不能假定 i.U 透明转发 handler 错误。[修前合同](raw/settings-config-receiver-origin/history/pre-peer-wording-01/settings-config-receiver-origin.json)与[修前journal](raw/settings-config-receiver-origin/history/pre-peer-wording-01/evidence.jsonl)保留原字节，不把历史版本累加为新记录。

取消分支触发 controller.abort，但所选文件 handler 不消费 signal，未证明 I/O 被取消。消息送达、响应完成、client/source输入、文件持久化、完整模式和实现归属仍待验证；后续di来源调查另批保存，不追溯升级本快照。旧settings-config-dispatch 40记录、全局journal及模式排除0未改，没有新目标或模型执行。
