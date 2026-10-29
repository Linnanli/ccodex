# 七项本地线程功能的归属与保留边界

七项既有功能已完成本批静态判断。**FSC-0402 摘要面板由 unknown 改为 shared**；其余六项保留 unknown 的全局模式归属，并明确保留已追踪的本地线程职责。有效分类为 **501 unknown、3 shared**，仍是504项功能；操作、规格、任务和职责标识未增加。

| 功能 | 模式结论 | 实施依据 |
| --- | --- | --- |
| FSC-0397 改名 | unknown | 保留 pending worktree/已有线程分流、主机确认与历史适配；注入 override 和全部跨产品调用方未闭合 |
| FSC-0402 摘要显示/固定 | shared | 保留本地摘要状态与命令；从被剥离的 ChatGPT 路由省略其 mh/vh 展示适配；共享状态与整个 chunk 不删除 |
| FSC-0403 终端展示/选择 | unknown | 保留 native open、command toggle、terminalId 标签选择；三者分别验收，PTY 提供方另列 |
| FSC-0503 分享静态快照 | unknown | 保留脱敏、上传准备、发布和复制；准备阶段即可上传，离线导出不能代替完整分享 |
| FSC-0504 子代理内容/总览 | unknown | 保留两种入口、父子/主机校验和异步过期结果处理；这些前端条件不证明服务授权 |
| FSC-0505 PR详情 | unknown | 保留 canonical/board 分流；T06拥有详情，T03消费入口；不混入创建或合并 |
| FSC-0506 停止后台终端 | unknown | conversationId 清理全部后台终端；所点 terminalId 只控制 pending 展示，不能改成停止单个终端 |

摘要共享结论有直接调用方证据：m_ 从 conversation_origin 派生 tpp/flora 与普通 chat 条件，允许 rn 或 pr 条件进入摘要挂载，将数据、conversationId 和受控回调传给 mh。mh 注册 togglePinnedSummary，与本地 fc/Ne 是同一个用户目标的具体消费适配。此结论来自数据、条件与回调链，未以文件名、翻译字符串或产品标签单独分类。

[结构化决定](local-thread-mode-classification-v1.json)逐项保存保留职责、模块边界、精确未知边界、来源位置与置信度。[累计模式覆盖层](feature-mode-dispositions-v2.json)保留此前 FSC-0481 的共享结论，并只追加 FSC-0402；[有效 CSV](feature-mode-dispositions-v2.csv)覆盖全部504个既有标识。基础功能账本 v48 与七套既有清单保持原字节。

本批只解析冻结的 ChatGPT 会话页来找 mh 的直接调用方，并复用已有源码合同；没有目标代码求值、客户端启动、模型提交或服务请求。源码哈希/范围检查用于确认出处，不能证明真实 UI、持久化、PTY、账户许可、分享服务或完整构建通过。原计划九项标准与完整复刻范围不变。

下一步转向原计划6.3中已发布的三个 ChatGPT 专属分支决定组，核对可拆边界和共享依赖保留理由，不重新递归调查模式基础设施。
