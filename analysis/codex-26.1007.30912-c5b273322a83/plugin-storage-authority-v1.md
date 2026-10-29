# 插件存储权威边界 v1

本次关闭 SD-05 的选定插件子问题：插件状态涉及多个独立写入方，不能恢复成一个客户端本地 store。冻结源码中既有后台协议和账户 HTTP，也有桌面主进程直接文件操作。此处是静态合同；没有运行客户端、服务或模型，没有读个人配置，没有完成真实安装或恢复验收。

| 状态/资源 | 选定写入方或来源 | 恢复时保留的边界 |
| --- | --- | --- |
| 列表、乐观启停和错误快照 | renderer query cache | 仅客户端缓存；还原缓存不等于回滚磁盘 |
| 本地主机启停 | config/read → config/batchWrite | 层返回的 filePath/version、upsert、expectedVersion、reloadUserConfig |
| 账户插件及 remote-source 启停 | HTTP enable/disable；账户卸载 HTTP | account 身份检查、remotePluginId、非账户 remote-source 后续刷新 |
| 列表、安装、非账户卸载、升级 | host RPC / app-server | plugin/list、plugin/install、plugin/uninstall、marketplace/upgrade |
| 桌面内置市场 | 主进程文件操作 | desktop codexHome/.tmp/bundled-marketplaces；staging、原生停止、替换、清理顺序 |
| 执行端插件 cache | app-server 安装与主进程调和 | execution codexHome/plugins/cache；version/latest、平台路径语义 |
| SSH 端内置市场 | app-server 文件接口 | 执行端 home；删除、写载荷、最后写 marker，与桌面 staging 路径不同 |
| 旧导入市场 | 主进程文件操作 | cache/claude-cowork；名字不证明模式或完整用户功能身份 |
| 扩展同步的管理标记 | 注入的 globalState | electron-chrome-extension-sync-managed-plugin-ids；底层 flush 未证明 |

Ine 在 staging 中写清单、复制插件后，停止原生宿主、删除原目标并 rename；finally 清理 staging。选定函数没有旧目标恢复分支。Nne 对远端目标先删除再写入，以 marker 最后写入作为后续复用条件，选定函数没有 staging rename。两者都不能据此称为完整原子事务。cie 的监视 cache 使用 executionCodexHome，市场清单使用桌面 codexHome，两个根必须分别注入。

W05 保留 HTTP、app-server 和原生接口的独立 provider；W06 分开管理缓存、配置、桌面文件、执行端文件和标记状态；T17 只编排用户操作及这些接口。durable、remote-source 和旧市场名称不作为删除 ChatGPT 功能的依据。以上是工程设计推断，具体源码事实、字节范围和来源哈希见[机器记录](plugin-storage-authority-v1.json)及[证据](plugin-storage-authority-v1-evidence.jsonl)。

仍需后续解决的是实际配置层/路径/flush、服务端安装实现、HTTP 服务、完整交互安装入口、实际双 home 值、复制与原生 provider、globalState 持久化及产品恢复行为。它们各自限制对应集成验收，不能让本次边界调查无限延伸。该子步骤已交付；SD-05 全域与完整分析仍未宣称完成。[实施计划 v10](implementation-plan-v10.md)继续有效，本轮不新增计划版本或功能分母。
