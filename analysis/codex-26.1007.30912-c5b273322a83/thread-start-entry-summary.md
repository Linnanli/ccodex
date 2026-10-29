# 普通新任务、首条消息与 MCP 辅助会话

旧 `TTC-V-01 thread/start` 是账户绑定的临时只读 MCP extension 会话。普通新任务从 composer 的新建分支进入 `HGi/startConversation`，再分别创建线程和提交首 turn。二者有不同目标、payload、身份和清理规则。

| 层次 | 源码结论 | 恢复时保留 |
| --- | --- | --- |
| rpt / _9e / TJe | 新建目标调用 CE/HGi，管理 client ID、导航、runtime 与异步 settlement；已有线程提交另走原分支 | 新建与追加消息分开；onSettled 可晚于首次返回 |
| HGi / GGi | 规范化输入、权限、roots、mode/source、附件与配置，包装身份和环境回调，调用 KI-selected RPC | 区分 UI、创建输入、运行时准备和传输 |
| Dfn / zln | 创建线程后，可返回 not-requested、not-started、rejected、accepted 或首turn outcome-unknown | 线程ID、首turn ID、消息ID、request ID与结果独立保存 |
| efn / Xdn | 可消费 prewarm，否则发送 start/startAeon；映射与 initialization 分阶段 | 不把所有创建动作都假定为新的 thread/start 请求 |
| MCP UC.queryFn | ephemeral/read-only/mcp_extension_host；host/account/user query key；30秒源码超时 | 属支撑生命周期，模式和实际消费者继续核对 |
| MCP retire / unsubscribe | 按 pending requests 立即或延后退订，异步失败只记 debug | 本地释放不等于后台清理成功 |

4组导入导出绑定和先前保存的 Dfn constructor 连接已核对。**实际 UI 的 KI provider 是否选中相应 Dfn 仍未证明**；manager/creation 部分继续作为条件接口合同。

## 创建、发送与未知结果

zln 的创建成功不等于首条消息已发送。初始化或部分设置失败可返回 created/not-started；空输入且无其他首turn内容可返回 not-requested；首turn RPC 拒绝为 rejected，普通本地错误为 not-started。它们都可能保留新线程ID。

`outcome-unknown` 有顶层创建和首turn两种身份。Promise.race 可先返回未知，原链稍后仍进入 onSettled；该结果不能当作已取消或已失败，也不能盲目再次发送。iK 的提示错误携带原 result，保留后续核对所需的线程、消息与请求身份。

ID 保留有明确范围：efn 的 identity callback 等 initialization 错误可返回 ID；但映射/setConversation 位于该 catch 之外，后台返回后这里抛错仍会向上传播而没有结果 ID。恢复时须把后台可能接受与调用方取得 ID 分开记录。

## MCP 边界

旧 TTC-V-01 与保存的 queryFn 范围/哈希一致，不能再用它代表普通新建任务。账户检查在请求前和响应后各一次；signal.aborted 在响应后检查，故不能据此证明没有发送 start。retire 按请求排空条件立即或延后 unsubscribe；退订错误被吞掉不证明服务端清理，ephemeral 的实际留存也未验证。kle 经 shared KUt→az=3e4，源码请求 timeoutMs 为30000；本次没有等待真实超时。

## 验证和交付

[17条源码事实](thread-start-entry-contracts.json)来自3个冻结文件的5次完整 Program 解析，并复用先前 manager constructor 来源。[25个隔离场景](thread-start-isolated-observations.json)通过：两条本机 Node22 命令执行6个选定单位，覆盖正常/部分失败、两个层次的未知送达及稍后 settlement、lease 释放、MCP 账户/信号/退订和响应后映射失败。

全部服务、UI、provider、Git/存储和运行时能力均为显式内存替身。没有客户端运行、模型提交、实际线程或首turn创建、MCP session、IPC、项目变更或持久化写入。25个隔离场景不计真实功能验收；此前一次实际任务完成和一次重启后 interrupted 仍仅证明对应合成样例。

[v7有限功能视图](feature-scope-v7.json)将旧 MCP start 候选归为支撑，另登记普通新建用户目标：48项定义、52用户操作、22支撑、1项旧resume关联待审；新增4条规格后共212条未执行。原71根保留，连同归档和普通新建两个新增入口为73根/75行为条目；12项关联待办保留。967旧入口未映射、48项模式unknown、确认排除0、完整产品分母未知。

本批关闭“普通新任务与 MCP start 是否同一操作”的问题，不重复调查已定位的创建/分支/归档菜单。实际receiver、prewarm、服务、完整MCP消费者、模式、存储和行为仍在[计划v6](implementation-plan-v6.md)中保留。下一步按已有旧入口台账批量对齐 owner、运行环境和模式条件，减少逐个回调登记造成的范围扩展。[发布来源与回执](thread-start-entry-provenance.json)保存各次解析及两组观察；既有REA结果继续作为输入，本批未新增REA运行。
