# 云任务头部：回调合同与功能归属

已核对 Fa、ka、ya 及其具体回调和值来源，并在同一批次接入功能、规格、任务和职责清单。

ya 实际是 Create/Open PR 按钮，不是轮次选择器。它从轮次关系中选择 PR 操作对象，没有切换轮次的界面。创建 POST 完成后仍依赖逐 turn 查询获得 URL；2 秒周期 refetch 停止不等于 observer disabled。服务拒绝、查询 failed 和创建后晚到 URL 是不同状态；没有显式总超时或取消按钮。

云任务 Archive 的可见条件是时间戳 truthiness，不是归档状态或权限。服务成功后更新缓存、导航与 toast；这些回调异常仍可能进入失败提示，因此错误不等于远端未归档。Undo 复用云端 recover；View 复用归档浏览。复制入口只传 taskId，保留默认 host/access 与本地入口的差异。

菜单还按条件提供按任务取消宠物通知静音和移动到左右窗格。已核对 chat 描述符的生产者，排除这个入口的 content 新窗口与底部移动分支；Close 的接收方是显示状态事务，不能仅凭菜单 id 推断删标签或关窗口。

新增 FSC-0500 云任务归档、FSC-0501 任务通知取消静音、FSC-0502 指定窗格移动。8 项已有功能只追加入口、规格和明确的新接收方操作，保留旧 ID 与原行为；PR 创建和 Close 新增不同接收方操作，置顶、复制、打开 PR、恢复与归档浏览复用已有操作。4 项维护职责是提议，尚未实现。

30 条场景全部未执行。当前500项有限功能、566个不同操作、1761条未执行规格、51任务；715条未关联来源身份不变。没有模型提交、目标运行、服务调用、剪贴板写入或 Git 修改。

本批两组控件的选定源码与功能归属已闭环。THV-GAP-HEADER 中 ai/oi review tabs 和 panel wrapper 仍待定向分析；没有宣告整个线程页面或原九项完成标准已完成。实际运行值、模式归属、服务/native/存储/布局后效与独立构建仍须验证。

[完整合同](remote-header-actions-v1.json) · [功能清单](feature-scope-v47.json) · [未执行规格](feature-scope-v44-scenarios.json) · [任务覆盖](restoration-coverage-v38.json) · [职责映射](feature-module-ownership-v13.json)
