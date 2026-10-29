# 本地环境 Hooks 与 MCP 的恢复边界

本批为三个页面和选定 provider 增加 17 条静态合同、41 项隔离源码回放及 16 对协议 schema 比较。未新增正式功能定义，当前仍为 103 项有限定义、406 条待执行产品规格；35 个设置容器的完整操作归属继续保留。

本地环境保存与激活分开，revision 冲突触发重新读取；保存后激活失败保留 selection-failed。Hooks 保留来源分组、受管理/待信任状态、带 JSON 引号的状态键、okOverridden 错误与回滚。MCP 将保存/删除、启停、OAuth 和后台重启分开，保留 stdio/HTTP 字段和项目来源只读条件。

冻结与公开候选的八类 schema 在 stable/experimental 中共 16 对合同形状相同，详见[结构化合同](environment-extension-contracts.json)。Hooks 列表的页面规则比 schema 更严格：无项目根时不查询。实际服务身份、宿主保存、OAuth、通知和耐久性尚待核对。41 个回放使用合成替身，没有真实配置写入、模型任务、hook 执行或原客户端运行。第一次回放的错误预期已修正，失败与成功记录均保留。

[统一实施草案](implementation-plan-v7.md)将这些边界安排为环境、Hooks、MCP 三组恢复任务，并连接当前全部有限功能与构建缺口。后续先完成三页面的操作归属及真实 provider 链，再回到任务生命周期的主要接收链核对；不以设置页局部调查代替完整目标。
