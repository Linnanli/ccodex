# 中断函数的条件与隔离观察

本批核对普通本地停止链中的函数行为：在固定shared Program中重新定位Ien、zen、Len、Pen、Ren、IN及两个Dfn方法，保存8条源码事实、12个范围和17处Program绑定。9个保存单位5259字节在本机Node22的VM中完成34个场景。没有启动桌面应用、点击停止或提交模型任务；真实UI接收实例和Node24／Owl行为仍未知。见[源码契约](interrupt-control-flow.json)、[场景结果](interrupt-control-flow-observations.json)、[限定解释与维护边界](interrupt-control-flow-findings.json)、[证据](interrupt-control-flow-evidence.jsonl)及[来源索引](interrupt-control-flow-provenance.json)。

普通composer的既有源码链没有传expectedTurnId。Ien先取最后一个有turnId的快照；显式expected ID不匹配或该项不是inProgress时直接返回null。没有expected ID且快照非活动时只尝试清理后台终端。新Program分析关闭所选Ien／helper的词法绑定，不关闭[KI/provider的实际实例](submission-host-instance-summary.md)。yda范围沿用旧完整定位并重核字节，没有重新解析整个initial Program。

| 条件或结果 | 本批观察到的函数行为 | 范围 |
| --- | --- | --- |
| 普通成功 | 中断请求履行后本地标记原turn；返回ID与notification完成分别表达 | C04、C05 |
| 服务端报告另一活动ID | 无expected ID可补发一次；补发成功返回报告ID，但该成功分支只标记原turn；补发报精确no-active-turn时另标记报告turn | C09–C12 |
| no-active-turn文本错误 | 无expected ID时本地标记并返回原ID；有expected ID时返回null | C13 |
| 清理前后台 | 无expected ID先发起node_repl清理，显式ID在finally发起；backgroundCleanup不等待清理Promise | C04–C07 |
| 暂停goal失败 | system在中断前退出；user-stop继续中断后抛附带interruptedTurnId的错误，renderer仍可先记录该ID再重抛 | M05、M06 |
| follower不可用 | 只有follower角色加三类指定文本原因才回退本地并标记needsResume | M01–M03 |
| descendant清理 | finally中的被等待清理错误可替换self错误；user-stop调用单独后台方法 | W01–W03 |
| renderer包装 | 显式client避开host选择；user结果更新有精确条件，yda成功返回undefined | R01–R03 |

Pen仅识别两种固定基线文本格式，Ren要求完全相同的`no active turn to interrupt`。不能把任意错误当作可补发。zen的10000ms只在显式假scheduler中推进，goal请求的500ms只验证传入选项；没有观察真实超时强制、native进程终止、bridge送达或后端落盘。等待期间已completed的原turn在本场景不被Len覆盖，也不代表真实通知排序已验证。

所有模型／RPC、follower、logger、events、runtime、scheduler、descendant清理和renderer store均为受控替身。Ben.default用标准Array.findLast边界替代，mz／ah仅处理合成turns数组，canonical历史未执行。IN的generic utility来源未独立归类；Ben依赖只定位到Program声明与使用，不能据此认定包名。原第三方实现没有复制进交付文件，保存源码片段只留在本地分析区；这些替身不能直接作为恢复项目中的兼容实现。

实际启动了两次VM观察命令。首轮在M06的跨VM原型deepStrictEqual断言失败，已有部分函数调用执行但没有完整结果文件；第二轮改为逐字段比较后完成34个场景。失败的精确脚本、stdout、stderr、receipt与首轮source选择均保留。34是成功套件的场景定义数，个别场景含多个变体；不是总调用数、产品功能数或独立运行次数。作者校验另核2个源文件、31个唯一范围与58个metadata pointer，没有新增独立语义审查。

[已有桌面结果](behavior-stop-restart.json)保持原结论：取消样例没有找到可精确绑定的控制项，取消点击0；另一个样例通过SIGTERM停止并重启后，在绑定的UI中看到同一turn为interrupted。后者不证明停止按钮、yda/Ien或哪一条持久化路径执行，也未观察到继续运行。该两条模型样例组已使用2／2、剩余0；本批不消耗或扩充授权。

维护职责可暂分为取消UI控制、turn中断编排、基线错误适配及runtime清理四个候选边界，具体建议保存在findings JSON。异常需要携带“可能已中断”的结果，避免把goal或descendant后续失败直接视为可以重发的失败。此处是恢复职责提案，没有生成客户端实现。FSC-0001至0034、35已关联操作、36队列和968入口覆盖状态均保持，未从协议方法数增加feature；模式仍unknown，ChatGPT排除0、完整功能分母与整项目构建继续待闭合。
