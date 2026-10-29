# 环境页面添加项目的委托决定

FSC-0105/T14 的本地 Ke 确认为 initial 的 j$t/z0r：记录本地创建 flow 后发送 `electron-add-new-workspace-root-option`。匹配的 main handler 经构造器注入的 Mje 文件夹选择器调用 `createOrSelectLocalProjects`。消息实际送达、有效实例与服务效果未实测。

这条选择／登记项目路径与既有 `projects.createLocal` 弹窗合同分开维护。前者选择根目录、允许选中已有项目，并发送取消或成功及导航消息；后者解析名称、来源、外观、Git 初始化和激活参数，可以创建默认根目录，返回项目 ID 与根路径。不能因名称都含“添加项目”合并合同。

维护决定：沿用项目领域 owner，并增加拟议文件 `apps/desktop/src/main/projects/project-folder-picker.ts`；该路径是恢复设计，尚未生成客户端实现。现有功能 ID 和 T14 保持不变，原 createLocal 合同仍需自己的消费者依据。

远程 qe/k$t 单独发送打开远程项目弹窗的消息。initial 的 dialog 文件名命中仅为资源索引，已排除为“打开弹窗”的证据。没有把 WSL 远程创建关联当成本地等价证明。

本批审查两个完整 Program，公布六项有限事实与精确来源片段。373 项功能、48 组任务和未执行场景规格不变；未调用模型、启动客户端或验证真实持久化。完整分析仍未完成。

数据及来源：[决定与来源](project-local-delegation-v1.json)、[证据](project-local-delegation-v1-evidence.jsonl)。
