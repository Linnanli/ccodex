# 数据存储职责与隔离边界

本轮形成11个有边界的数据域映射，并新增15条冻结源码事实。它说明路径输入、写入与恢复责任；尚未建立完整产品存储分母，也未读取运行中的个人目录或凭据。

桌面Codex home、后台执行home和Electron userData必须作为三个输入。前两者虽有共同回退表达式，执行home还可能经WSL分流；userData覆盖则会trim并resolve。环境、平台及运行返回值仍未观察。

settingsStore启动读取config.toml的desktop部分，初始化后由config/batchWrite后台接口写入。迁移清理既可由服务配置已存在触发，也可在迁移写入确认后触发。不能替换为简单本地TOML写入器。

thread assignments本地副本使用globalState，队列/后台写入另有职责；其flush只等待队列，不等于globalState文件flush。启动另会清理指定history-snapshot数据库及三个sidecar，不能扩大为会话数据库统一清理。

|数据域|路径/权威来源|维护决定|
|---|---|---|
|SDMD-01 Electron profile|oD(env override or appData/build flavor/agent run ID); app.setPath(userData,...)|独立应用标识、显式profile根和runtime配置分别管理；不依靠改目录名称证明全部隔离。|
|SDMD-02 主进程globalState|desktopCodexHome/.codex-global-state.json; .bak and same-directory temp|状态接口、调度队列和JSON后端分离；广播、内存完成和文件完成使用不同合同。|
|SDMD-03 桌面设置与旧键迁移|startup reads desktopCodexHome/config.toml desktop section; effective backend configuration layer/path unresolved|保留本地启动读取器、设置状态/迁移协调器和后台配置gateway三个边界；不生成直接覆盖TOML的替代写入器。|
|SDMD-04 thread memberships与projectless路径提示|globalState key families; backend callback may own additional state, whose effective storage is unresolved|维护membership队列/后台桥和本地状态适配两个职责；不为flush名称凭空新增数据库，也不省略全局状态文件排空。|
|SDMD-05 history-snapshot启动清理|desktopCodexHome/sqlite/codex-history-snapshots[[-flavor]].db and three SQLite sidecars|将启动清理作为显式迁移/维护步骤，保留精确文件族；禁止把它扩大到所有SQLite或会话记录。|
|SDMD-06 app-server任务与执行状态|executionCodexHome is separately resolved; inherited env, WSL, remote websocket or daemon can select another effective authority|backend运行配置必须携带host/transport/executable/home身份；本地桌面home和后端有效home分别验收。|
|SDMD-07 认证与secret storage|auth.json/keyring and keychain access group are frozen capability/metadata clues; active provider and namespace unresolved|认证仓库、平台密钥命名空间和后台身份作为独立依赖合同；不得将文件目录覆盖当作凭据隔离开关。|
|SDMD-08 浏览器持久partition|persist:codex-browser- + encoded name; persist:codex-browser-app-route: + encoded two-input NUL tuple|独立runtime profile和partition身份一起管理；保留app/route身份及permission处理，不复制原浏览器profile。|
|SDMD-09 renderer persisted atoms与窗口标签页|electron-persisted-atom-state with thread-browser-tabs-v1:/thread-tab-routes-v1: subkeys; not automatically renderer localStorage|renderer镜像、IPC策略和main状态后端分开；保留primary owner、删除编码和窗口过滤。|
|SDMD-10 共享host对象镜像|selected main in-memory object and shallow snapshots; no disk path established|将此域保留为内存发布仓库；持久化由各真实owner另行承担，不重复保存整个镜像。|
|SDMD-11 退出、日志与tracing排空|globalState, settingsStore, membership queue, tracing and logger each retain own authority; log paths unresolved here|退出协调器按provider记录等待/超时/失败，区分正常退出、强停和断电；不以一个flush标签代表全部域。|

## 行为证据及限制

沿用已有9个隔离文件场景、17个退出替身场景及已授权停止/重启的真实记录；这些各有范围，不能合计为全域隔离或持久化通过。真实重启恢复interrupted任务不证明自动续跑，也不证明内部数据库位置。

认证、secret/keyring、远程服务和浏览器session各有独立权威来源。CODEX_HOME/userData不同不足以证明凭据隔离；逻辑partition名不等于磁盘根。

本图仍缺完整plugin/cache/download/update-resume/automation/workspace及远端账户服务的逐store盘点；WSL helper、设置schema/迁移、实际provider和有效根等具体缺口见每域。SD-05整体保持开放。

下一内部项为SD-06：将已有37个逻辑owner规范成计划要求的模块字段。功能373、任务48、未执行规格1216不变；本轮无客户端启动、模型调用或新的行为通过项。

[结构化映射](storage-domain-map-v1.json)、[源码事实](storage-domain-map-v1-evidence.jsonl)。拟议维护路径不是原目录或已生成客户端代码。
