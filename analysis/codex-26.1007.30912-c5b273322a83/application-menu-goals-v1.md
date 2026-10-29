# 应用菜单用户目标与模块去向 v1

固定基线：`codex-26.1007.30912-c5b273322a83`。SQ-01 的 12 条菜单 schema 已逐条处置，形成 11 项新增有限用户目标；两条全屏入口合并为一个目标。已有 373 项定义逐项读取并按行为/目标比较，原定义保留。

| 功能 | 菜单入口数 | 去重与模块 |
| --- | ---: | --- |
| FSC-0374 从应用菜单发起新建项目 | 1 | MENU-UNIT-application-menu, AMG-M01 |
| FSC-0375 重载应用窗口 | 1 | MENU-UNIT-application-menu |
| FSC-0376 检查桌面客户端更新 | 1 | MENU-UNIT-application-menu |
| FSC-0377 切换当前窗口全屏 | 2 | MENU-UNIT-application-menu |
| FSC-0378 打开 Codex 应用文档 | 1 | MENU-UNIT-application-menu |
| FSC-0379 查看 Codex 更新说明 | 1 | MENU-UNIT-application-menu |
| FSC-0380 打开 Codex 故障排查指南 | 1 | MENU-UNIT-application-menu |
| FSC-0381 查看服务运行状态 | 1 | MENU-UNIT-application-menu |
| FSC-0382 打开并提交应用反馈 | 1 | MENU-UNIT-application-menu, AMG-M02 |
| FSC-0383 打开桌面任务管理器 | 1 | MENU-UNIT-application-menu |
| FSC-0384 重启并记录启动性能 | 1 | MENU-UNIT-application-menu, AMG-M03 |

新建项目仅 z0r 分支复用 FSC-0105 的添加目录流程；整个命令还会按模式、访问资格和宿主分流到 gji 或 L0r，因此不合并整个目标。反馈菜单、Pw 命令及 /feedback 是同一目标的不同入口。四个帮助链接按文档、更新说明、故障排查、服务状态的不同信息目标保留，执行器共用 external-links adapter。

重载窗口受 buildFlavor != Prod 限制；全屏仅操作有效焦点窗口，没有创建主窗口的回退。检查更新只证明委托 checkForUpdates 和不可用提示，不证明下载或安装成功。Task Manager 复用此前已交付入口合同，内部原生窗口和操作仍缺独立运行时证据。

启动性能录制新增了明确的本地状态/存储链：确认默认取消 → 写 record-next-startup（0600）→ 重启 provider/quit → 下次启动消费标记 → 创建 startup-performance（0700）并录制。1 秒 Promise.race 只限制启动等待；120 秒 unref timer 才控制停止。标记在录制前消费，录制失败不会自动补回。所选链无上传调用，实际 native/退出/重启及数据隔离尚未观察。

复用已有 MENU-UNIT-application-menu 提议，另给项目命令、反馈命令、启动录制三个十字段职责提议。它们尚未并入原 37 职责的统一视图；后续 SQ-03 必须处理跨功能状态/范围归属。第三方和运行时实现均保持依赖边界，不生成实现副本。

当前台账 [v28](feature-scope-v28.json) 为 **384 项有限定义、388 项用户操作、117 项支撑、1252 条未执行规格**；[覆盖表 v19](restoration-coverage-v19.json) 为 49 个任务。新增 T49 作为 [v10](implementation-plan-v10.md) 的增补；原计划 373/48/1216 是历史快照。当前两套 [排序图 v2](restoration-current-ordering-v2.json) 各 58 节点。

12 条旧来源记录获得部分目标关联；[来源视图 v6](legacy-entry-dispositions-v6.json) 仍为 968 条、角色待审 0、无功能关联 950、完整功能解决 0。这些分母不能互换。全部新增目标模式 unknown；未新增 ChatGPT 排除。

核验重新读取 4 份冻结文件、36 个新选择和 3 个复用菜单函数，检查 40 条限定连接与 2 处调用位置。连接核验只证明所选源码字节、语法和未遮蔽调用；外部 callee 原 Program 声明身份采用固定查询记录。新增 36 条产品规格均未执行；新增模型提交、客户端运行、服务调用、客户端实现均为 0。

下一项 SQ-02：其余固定入口逐条对应用户目标/已有功能/别名/机制。已知来源角色不再重新分类；本批 12 条和已确认共享分支不再进入重复待办。完整分析仍未完成。
