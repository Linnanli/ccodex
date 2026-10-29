# 设置页面、RPC 与 local host 的恢复边界

固定基线：`codex-26.1007.30912-c5b273322a83`。四批独立静态分析已完成有限复核，正式交付保留原 schema、证据 ID、哈希和定位。实际复制见[交付索引](settings-and-rpc-delivery-provenance.json)；这些记录不加入旧全局 journal，也不是完整功能分母。

| 分析范围 | 原证据记录 | 所选代码范围 | 结构化结果 |
| --- | ---: | --- | --- |
| Agent 设置页 | 65 | 29 个完整页面函数；另有 122B 共享请求边界 | [页面契约](settings-agent-page-contracts.json) |
| GeneralSettings | 39 | 61 个完整函数、70,544B；32 条操作或展示契约 | [页面契约](settings-general-page-contracts.json) |
| RPC 实现边界 | 24 | 17 个完整单位、128 个方法 | [RPC 契约](submission-rpc-dependency-contracts.json) |
| local host 注册 | 25 | 8 个完整单位、24,176B；另有 7 条旧引用 | [注册契约](local-host-registration-contracts.json) |

四批共 153 条独立证据。单位、方法、操作和旧引用各有不同分母，不能相加成为用户功能数量。没有新增运行观察、模型任务、已确认 ChatGPT 专属排除项或完整客户端实现。

Agent 页面由实际 `ConfigurationPanel→Tr` 导出绑定确定。六项配置控件共用本地写入函数，配置层和工作区选择影响 payload；project 分支存在读文件、校验、编辑和保存 callback。实验功能、推理强度，以及诊断、重置、取消、启用四项依赖操作另有源码契约。该冻结批次止于导入 provider 和共享请求转发；实际接收、磁盘状态和运行结果需要后续证据。

General 与 family 两个注册属性引用同一 `cQa` factory，实际组件为 `Bs`，132B 入口包装另调用 `Lc` 初始化器。两个注册属性不能当作两份页面实现或两项独立功能。`qs/Jo` appearance 导出不在所选 General 页面闭包内，因此没有归入其重置行为。

General 的 32 条契约涉及任务目录、语言、关闭确认、文件打开位置、Windows/WSL、界面偏好、睡眠、历史压缩、速度与提示、输入行为、Popout 热键、系统音频和只读信息。具体约束会影响复刻：WSL 探测未通过时先返回；音频只有 ready 才执行所选偏好写入；热键处理保留清空、取消、错误和缓存刷新；Full Access 控件改变选项可见性并确认，不能据此认定已激活权限。偏好写入、缓存刷新和界面 pending 状态分别记录，导入 provider 的最终持久化未在本批证明。

RPC 以远程能力引用工作。所选 `dup`、断连回调、根对象关闭 session、普通引用释放以及 transport abort 属于不同生命周期路径。恢复时需要这些契约，不能只迁移请求名称。公开 [capnweb 包导入候选](capnweb-upstream-candidate-summary.md)有独立有限对照，但基线实际安装锁、完整修改和 wire 等价性仍未证明。应用 manager/coordinator、host/scope 和订阅清理由第一方职责层处理。

local host 的 `N3` factory 明确仅在 host 等于 `local` 时查找 `loi`，有结果才调用 `uoi` 订阅。`LI` 写入默认 local，`VI` 提供当前 host 集合；这些是静态创建与选择候选。`X3` 的注册、替换、删除涉及对象身份、dispose 和 local/daybreak 状态复位，三个工具 caller 只查找现有 manager。实际 atom/factory 执行、初始化顺序、UI 接收实例及 host-provided 到 `Dfn` 的关系仍未知。

恢复结构因此至少需要保留页面 factory 与初始化、配置层和偏好适配、RPC session 与能力引用、host 注册与生命周期四类职责。此处是有来源的局部职责建议，完整目录、所有共享依赖及全部功能恢复顺序仍待分析。

各复核范围分开保存：Agent 的完整源检查、保存元数据检查和计数修复不同；General 的原 38 条核心、共享请求链接及最终 39 条增量分别检查；RPC 和 local host 各有自己的有限 peer。交付索引保留这些 counter 的原路径和含义，没有把它们相加表示覆盖率。两次交付脚本字段假设错误发生在正式写入前，真实失败记录保留；第三次交付成功。

[交付复核](settings-and-rpc-delivery-peer-review.md)的实际 checker 完成 2,664 项检查，限定于 root 交付脚本、可信 helper 和 64 份精确 metadata 拷贝／别名。复核者同时是 General 原分析作者，源码语义的独立复核仍以另一个 peer 的有限范围为准。[复核交付索引](settings-and-rpc-delivery-review-provenance.json)与[真实执行归档](raw/settings-and-rpc/delivery-execution-provenance.json)分别记录范围及真实失败历史。
