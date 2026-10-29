# 认证存储的客户端与后台边界 v1

选定 JS 链路已明确：桌面客户端管理预登录策略、传输选择和内存令牌缓存，登录及凭据读取委托给 app-server；原生 credential store 的实际选择、namespace 与迁移仍未知。本轮不读取凭据、个人配置或历史，不运行客户端、模型或真实服务。

最影响独立客户端设计的新结论是：**非空配置 overrides 会禁止选定标准连接类复用本地 daemon，改用 stdio 子进程。** secret-auth-storage 的正向预登录结果是这种 override 的一种来源。空列表只允许继续检查 daemon 条件，不保证复用；其他主机和传输有独立分支。

| 层 | 已核实的静态责任 | 尚不能证明 |
| --- | --- | --- |
| 预登录策略 | darwin/linux、Network 成功且 Recognized/true 时产生 features.secret_auth_storage=true | 原生最终选择了哪种存储；空列表不是显式关闭 keyring |
| 稳定 ID | userData/statsig-state.json 的 STATSIG_STABLE_ID，写入失败处理与 flush | 该文件保存用户凭据；全部身份已被隔离 |
| 标准本地连接 | getConfigOverrides → -c 参数；非空 overrides 禁止 daemon 分支 | 实际启动的进程、home 或平台 namespace |
| 认证 API | account/login/start、cancel、logout 与 getAuthStatus | 后台 auth.json/keyring/secret 的写入、删除和迁移 |
| bearer cache | generation 防旧响应、并发 Promise、身份变更失效 | 清内存等价于删磁盘凭据 |
| workspace auth | 等待账户变更完成、路由匹配与 abort signal | 新增了一个持久化凭据仓库 |

W03/W05/W06 应将这些接口分开注入，并分别记录 host、transport、executable、home、overrides 与 credential provider/namespace。协议中的 chatgpt/chatgptAuthTokens 是认证家族，Codex 路由也消费其 bearer，不能凭名称删除。实际原生来源与运行验收继续保留，不伪造已实现 provider。

26 项精确源码隔离用例通过，包括策略失败和 shutdown 异常、daemon/stdio 选择、旧 generation 响应、认证参数与后端错误。用例只使用合成 Statsig、transport 和 backend，无真实网络、socket、进程启动或凭据。它们不计产品功能通过。见[回放记录](auth-storage-authority-v1-replay.json)、[源码与工程决定](auth-storage-authority-v1.json)、[证据](auth-storage-authority-v1-evidence.jsonl)。

另纠正一次重复调度：[37 个逻辑职责的十项字段视图](logical-module-contracts-v1.md)已存在，19 条重叠规则及 251 个来源范围继续复用，本轮没有再生成同一模块清单。实施计划 v10 与原九项标准不变。
