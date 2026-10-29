# 本地审查暂存、取消暂存与撤销

本批关闭选定调用链的源码分析：3类用户目标、5个操作、22条未执行规格归入既有T06。补入确认状态、revision检查、补丁组装、两个worker方法及Git参数；未执行任何Git写入、模型任务或客户端启动。

控件门控明确排除chatgpt-thread/remote-thread，并要求有效仓库、staged/unstaged来源及local/worktree上下文。文件/区块还受unmerged、canApplyPatchActions和busy约束。整组操作另走apply-review-section-changes；staged来源无Revert all按钮，后台支持不等于存在UI。

确认弹窗只保存参数及revision/文件列表。确认时读取当前来源、仓库和宿主，文件/区块先核对revision，条件refetch后再核对；section由后台重读binary patch和summary并比较全部revision。不再询问偏好先于Git结果写入；关闭弹窗只清pending。

stage写索引；unstage反向写索引。staged文件/区块revert先反向索引、再反向工作区，第二步失败可部分成功；每次atomic不提供跨请求回滚。刷新或临时文件清理失败也可能在Git已成功后形成错误，不能仅凭UI错误推断磁盘未改。section的transport异常与文件/区块catch边界不同。

重建职责分为确认/状态控制器、补丁组装、Git worker适配器。拟议路径与imports/exports、状态、副作用、第三方依赖边界见[契约](review-git-actions-v1.json)的maintenanceProposals；不复制第三方实现，也不把这些提议当作原始目录。

证据：20项源码事实、63个维护见证；6个不同完整程序，7次最终解析，6个ESM身份连接及9项源码断言通过。134个选定单元独立解析，UTF8范围和文件哈希回读通过。这些检查只证明选定源码对应关系。

实际写盘、冲突/二进制/重命名、并发、执行中取消、关窗/重启和偏好耐久性仍未验证。3项目标的完整产品模式保持unknown。当前有限清单518功能、596个不同用户操作、1891条未执行规格；客户端实现及新增运行通过仍为0。

下一批继续具体审查搜索/视图偏好或保留的任务工作流消费者；复用本批、来源选择和完整文件读取契约，止于已确认接口。
