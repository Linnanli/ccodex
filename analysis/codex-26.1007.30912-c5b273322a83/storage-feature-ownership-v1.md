# 存储与功能职责整合 v1

本批将项目/远程状态、下载、自动化及平台更新的源码所有者接入既有11域，并新增5类限定存储边界。21条静态事实、8个维护职责提议与17项功能的条件关联已记录。它不代表全客户端存储分母、完整调用链或实际持久化验收。

## 会影响恢复工程的结论

| 家族 | 数据与所有者 | 恢复时必须区分 |
| --- | --- | --- |
| 项目/远程 | 项目对象、外观和 managed SSH/autoConnect 复用 globalState；共享列表/registry 是内存视图 | set/刷新/连接/flush 各自完成；迁移不是跨文件事务 |
| 下载 | Xwe 控制活动对象；Kb/AppHost 转发；session 管历史；DownloadItem 写用户文件 | 清历史、停止下载、删除实际文件、清提醒四种后果分开 |
| 自动化 | 旧 TOML + memory/salt、共享 SQLite、当前账户/安装实例服务副本、enrollment/globalState | 本地文件不是一律可丢的缓存；SQL事务不覆盖文件或服务 |
| Windows 更新 | userData 下的状态文件 + native cache 下的更新包 | 两个根与 native stage/activate 单独配置/验收 |
| macOS/Linux 更新 | Sparkle addon / 已安装包元数据与系统包管理器 | 未知 native 缓存根显式留空；Linux 检查不等同于下载安装 |

## 写入、删除与恢复的具体边界

- **SFO-FACT-01** x4 是注入 globalState 的本地项目适配器；create/update/appearance 写 LOCAL_PROJECTS/PROJECT_APPEARANCES。NHe 在所选装配处收到 scopedState 与 new x4(scopedState)。这不是远程项目数据库的证明。 项目对象与外观通过 globalState.set 写入；删除分支委托 ni。写入完成沿用 SDMD-02 的队列/flush 合同。
  待验证：所有项目用户入口到本适配器的完整连接、远程项目 provider、实际有效 home 与磁盘完成仍分别待验。
- **SFO-FACT-02** noe 把旧工作区根整理成本地项目与 selected project；Eoe 只迁移满足旧 self-mapping 条件的远程项目，按 host/path 去重并重写顺序、选择和旧映射；goe 的自动化 cwd 迁移可创建项目并 await flushOrThrow。 多个 globalState.set 是分步改写；goe 对新建项目显式排空。不得推断全部旧键均删除或跨自动化/项目事务。
  待验证：迁移触发时序与崩溃恢复、实际旧数据形状；不读取个人项目记录。
- **SFO-FACT-03** SSH 保存和 autoConnect 偏好通过 fKe.appState 写入；保存列表会保留未参与当前目录的旧项并清理被移除项的偏好。两个命名请求 handler 分别委托 saveCodexManagedRemoteSshConnections 和 setRemoteConnectionAutoConnect。 偏好先写再 await 刷新/连接或断开；网络失败不等于偏好回滚。loadSavedRemoteConnections 兼容旧 alias 字段，继承 RCS-E018。
  待验证：继承已选 hXe→fKe 注入合同；实际文件排空/连接后效不由 UI mutation 成功或内存替身证明。
- **SFO-FACT-04** uqe.add 可从 ~/.ssh/config 解析指定 alias 元数据，再登记 managed connection 与 autoConnect；remove 先过滤 globalState 列表和偏好再刷新。它与 sharedObjectRepository 的连接列表、registry 实时状态属于不同职责。 SSH 配置路径是所选元数据读取输入；这两个登记方法没有把 appState 写入等同于修改 ~/.ssh/config。共享列表与错误/进度是内存发布。
  待验证：SSH 解析 helper 的 Include/路径语义沿原边界保留；没有实际读取 .ssh/config。
- **SFO-FACT-05** MMe 构造 kje 时传入下载目录与提示偏好 getter，目录回退 app.getPath(downloads)；kje 使用同一 options 构造 Xwe。AppHost createAppHost 从浏览器 manager 的 downloadStore 字段创建 downloads: new Kb(...)，Kb 逐项转发。 偏好读取来源是 settingsStore.getEffective；设置写入继续继承 SDMD-03，下载目录选择对话框只返回路径。
  待验证：运行时 session 的实际 partition、有效目录/权限、renderer bridge 实例运行值仍未观察。
- **SFO-FACT-06** Xwe 的持久下载历史交给 browserSession.getDownloadHistory/searchDownloadHistory/removeDownloadFromHistory/clearData；clearHistory 捕获非 progressing GUID，清理 downloads 类型，再读回并对残留抛错。 记录删除拒绝 live/progressing 条目；clearHistory 的 JS 后验只检查非 progressing 历史。所选 Xwe 没有 rm/unlink 下载文件的调用。
  待验证：运行时 API 如何写磁盘、clearData 的完整原生副作用和重启恢复留在 SDMD-08 provider 边界。
- **SFO-FACT-07** Xwe 将 liveDownloads、activeSavePaths、unacknowledgedDownloadIds 和生命周期序号放在主进程对象内；暂停、取消和恢复委托 DownloadItem。完成或失败加入未确认集合，取消不走同一提醒分支。 finish 移除 live 对象和活动路径；存在下载时产生 download.active 重启阻塞项。没有选定证据证明这些 Set/Map 跨重启保存。
  待验证：DownloadItem 写入/取消后的文件后效、进程崩溃时内存与原生历史的协调仍须运行观察。
- **SFO-FACT-08** Xwe.reserveSavePath 使用所选下载目录和 basename，规避已存在/活动路径并分配后缀；用户下载可走保存对话框或 session 目录，非用户下载调用 setSavePath。update 可采纳实际 getSavePath。 文件 payload 路径由系统/偏好/用户对话框产生，不固定在 Codex profile；existsSync 仅作存在检查。
  待验证：实际文件写入由运行时承担；JS 的候选路径保留不构成跨进程原子占位。
- **SFO-FACT-09** 本地自动化目录由 mF=join(o.ot(),automations) 与 gF/_F 得到 <home>/automations/<id>/automation.toml；MF 校验 ID 并读 TOML，FF 在已有行无 accountId 时写文件。 PF 在同目录写唯一临时文件后 rename；rename 失败时先 rm 目标再 rename，不能承诺任意平台的原子替换或 fsync。
  待验证：o.ot 的 home 选择继承已有 SDMD-01/02 源码合同；实际有效根、路径隔离、写失败残留与耐久性未观察。
- **SFO-FACT-10** 自动化行/运行记录使用共享 SQLite provider q；$i 选择 <home>/sqlite/<databaseFileName|Qi()>，Qi 依据 BUILD_FLAVOR/NODE_ENV 选择 codex.db 或 codex-dev.db。na 通过 require(better-sqlite3) 加载外部实现。 ea 创建目录并打开数据库，尝试 WAL：返回 wal 则 synchronous=NORMAL，否则 FULL，再调用迁移 callback；失败关闭。q 只在 Electron 下返回缓存连接。
  待验证：这是共享数据库内所选表的 owner，不是所有 SQLite 表的完整恢复；退出 close/崩溃/迁移兼容性和 native ABI 分别待验。
- **SFO-FACT-11** 本地 rI/iI 在默认 persist 分支先 FF 写自动化文件，再 dF INSERT OR REPLACE 数据库；dF 捕获 SQL 异常并返回 false，而这两个调用点没有把该返回值作为成功前提。QF 的读取规范化也可能更新调度行。 文件和 SQL 是顺序副作用；读取列表不保证无写入。persist:false 用于先准备对象、后走服务保存和本地缓存。
  待验证：文件成功/SQL 失败的恢复策略没有由所选调用建立事务保证；不执行真实自动化。
- **SFO-FACT-12** 本地 aI 删除先 DELETE automations 行，再递归 rm 自动化目录，分别返回 store_unavailable/invalid_id/not_found/state_cleanup_failed/remove_failed/deleted。z_e 仅在 deleted/not_found 后另尝试 Br/ha 删除 automation_runs，异常被捕获。 SQL 行、文件目录与 runs 清理不在一个事务内；已有行也计入存在判断。外层 success 包含 not_found，不能推出所有残留文件已成功删除。
  待验证：删除后的恢复/运行中自动化协调与实际权限错误留待独立数据行为验证。
- **SFO-FACT-13** SF/TF/xF 根据 accountId/userId/installationId 和 migration 状态区分旧本地文件与当前账户 SQL 缓存。IF 仅首次尝试在没有自动化文件、没有 owner 时从旧无账户行重建文件。 迁移期间可合并旧文件与当前 owner 缓存，完成后仅当前 owner；owner 切换和列表可见性不等价于物理删除另一账户数据。
  待验证：账户切换、旧文件读取失败和重启时的实际条件未验证；不读取账户数据。
- **SFO-FACT-14** zF 接纳已验证的服务副本时校验旧文件 hash；可先复制 memory.md，然后 BEGIN，写 owner 行/移动 runs/删除旧行并再次核对 hash，COMMIT 后再 unlink 旧 TOML。BF/goe 的旧 cwd→project 迁移另分步改写项目与自动化。 SQL 部分有 BEGIN/COMMIT/ROLLBACK；memory 复制与 TOML 删除在事务之外。文件删除失败可在数据库已提交后返回 null。
  待验证：跨文件、数据库与服务的中断恢复没有全局事务证明；各失败阶段需后续合成行为测试。
- **SFO-FACT-15** ppe.saveAndVerify 先 POST /automations/save，再 GET /automation/<id> 独立核对安装 ID、legacy ID 与内容；hosted create/update 之后经 Tn/LF 缓存 SQL，delete 先请求服务 remove 再本地删除。 每次请求前后检查当前 principal/install；15s timeout。服务保存成功后本地缓存仍可能失败，不能报告为跨端原子事务。
  待验证：服务的实际持久化、幂等、认证和离线协调属于外部 API；没有调用任何服务。
- **SFO-FACT-16** ppe 的 enrollment 与迁移状态分别来自服务接口和 globalState。persistStatus 写 account:user[:installation] 键后 flushOrThrow；失败恢复先前内存值。安装 ID 新建也显式排空。 syncOwner 先处理 DELETED heartbeat 再分页拉取（limit=100，限制重复/过多 cursor），缓存返回项并修剪当前 owner 行；内存 owner/queue/enrollment 不作为磁盘仓库。
  待验证：恢复内存不证明此前磁盘或远端副作用已撤销；退出排空与实际重新登录同步仍待验证。
- **SFO-FACT-17** 自动化 jitter salt 保存于 <home>/automations/.run-jitter-salt；ZF 先读非空值，否则生成 UUID，尝试写入，失败仍返回并缓存生成值。 磁盘写入失败时本进程仍使用内存 salt；不能假定跨重启调度 jitter 必然稳定。
  待验证：并发进程、失败权限与重启后的调度行为未观察。
- **SFO-FACT-18** Windows wn 的状态根是 realpath(userData/windows-msix-updater/<currentPackageFamily>)；staged-msix.json 保存 buildVersion/packagePath/length/sha256。有效包路径必须等于 native cache/windows-updates/prepared.msix，且文件可访问。 readStageState 对无效/缺失状态移除状态文件；reconcile 对不新于当前 build 的版本 discard。读取路径检查不是重新 hash 或完整 native stage 验证。
  待验证：native 返回的有效缓存根、Windows 权限/包身份和激活提交行为未在当前 macOS 上观察。
- **SFO-FACT-19** Windows _n 仅接受 HTTPS URL/最终响应，在 native cache/windows-updates/prepared.download 流式写入并计算 SHA-256；按可用 manifest 长度/hash核对，rename 到 prepared.msix 后调用 native.readPackageMetadata 核对应用身份、publisher 和 arch。 finally 清理 .download；包 metadata 核对在 rename 后。wn 再 stagePackage，之后 temp-write/rename staged-msix.json；策略变化会 discard，激活交给 native。
  待验证：校验信息可选性、文件与元数据提交、native stage/activate、断电恢复均不由静态成功路径替代验收。
- **SFO-FACT-20** wn 初始化会删除状态根内 .msix/.download 普通文件和 installing 目录，再 reconcile；discard 分别移除 staged-msix.json 与 native cache 的 prepared.msix。Windows Store 路线由 Mn/Nn 与 native provider 管理。 桌面状态根与包缓存根是不同输入；清理动作不能推广到 profile 的所有文件。Store 检查/安装队列状态主要为实例字段与 native 回调。
  待验证：MSIX/Store provider 的内部数据库、系统账户命名空间和实际清理结果留在平台边界。
- **SFO-FACT-21** Kn 的 macOS 路线加载 resources/native/sparkle.node 并登记回调，下载/安装由 addon 承担；Linux Ze 读取 executable 同目录 resources/linux-package-metadata.json，仅比较已安装版本并在需要时 relaunch。 macOS 的 ready/progress/下载时间与重启提示是 JS 实例状态；没有选定 JS 缓存路径。Linux 路线没有在此实现远程包下载或安装。
  待验证：Sparkle/native/system package manager 的实际数据目录、命名空间、签名及恢复仍需对应 provider 证据；不能猜写 profile/cache。

## 拟议工程职责

| 维护单元 | 拟议路径 |
| --- | --- |
| 本地项目目录、外观及旧工作区迁移 | `apps/desktop/src/main/projects/local-project-state.ts` |
| 连接配置与 autoConnect 偏好、共享连接镜像的协调 | `apps/desktop/src/main/connections/connection-state.ts` |
| 下载控制、历史 gateway、活动对象与实际保存路径 | `apps/desktop/src/main/browser/downloads.ts` |
| 自动化 TOML、目录及本地 salt 文件 | `apps/desktop/src/main/automations/local-files.ts` |
| 共享 SQL 自动化 repository、owner 过滤与迁移协调 | `apps/desktop/src/main/automations/repository.ts` |
| 自动化账户保存、独立验证、enrollment 与本地协调 | `apps/desktop/src/main/automations/account-sync.ts` |
| Windows MSIX 状态、下载文件及 native stage/activate 协调 | `apps/desktop/src/main/updates/windows-msix.ts` |
| 平台更新 gateway 与原生/包管理器边界 | `apps/desktop/src/main/updates/platform-updater.ts` |

这些是第一方职责提议。better-sqlite3 的冻结包元数据为12.11.1；声明依赖并沿用既有原生 ABI/来源审计，不生成其实现副本。Sparkle、Windows updater 与浏览器私有历史接口的独立来源/构建资格仍保留。

## 功能关联及覆盖限制

17项关联中11项补充本批源码边界，6项复用插件/认证已有合同。CSV用于浏览，JSON保留各功能原操作合同及未闭合边界。其余409项当前有限功能的存储/provider缺口不变；没有将相似名字或共同源码范围当作状态归属。

自动化 create/update/delete handler 已登记为 SQ-02 的待盘点入口候选，包含 cron/heartbeat；本批不新增功能定义或改写426项分母。项目目录的源码 owner 登记也不等于每个项目入口已连接。

新增10条未执行存储恢复场景单列在本 JSON，不混入既有1407条产品规格或报告为通过。没有新增客户端启动、模型提交、服务调用或客户端实现。

## 本批关闭条件与下一步

本批命名家族中可见的存储职责已登记；native/backend内部、有效根、隔离和耐久性保持精确外部边界。整个SQ-04仍为部分完成，不将该固定批次关闭扩大为全域映射完成。下一步转SQ-02剩余菜单/命令/路由来源，优先对照已发现自动化 handler；只有新增消费者或矛盾证据才重开本批源码调查。

来源：[结构化合同](storage-feature-ownership-v1.json)、[功能关联表](storage-feature-ownership-v1.csv)、[证据](storage-feature-ownership-v1-evidence.jsonl)。全部源范围对应冻结基线，源码验证只证明所述静态结构，不能证明实际产品/native/build通过。
