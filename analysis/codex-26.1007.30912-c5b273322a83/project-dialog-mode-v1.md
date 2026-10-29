# 项目对话框消费者与模式边界 v1

本批交付 SD-01/AO-A12 选定源码问题：本地文件夹 capability 的旧/新版对话框消费者、上层项目来源与 Codex 保留用途。完整分析与客户端实现仍未完成。

## 影响重建的结论

- **Codex 模式仍使用 linked/backing 项目。** `aAr` 在 `sidebarMode=codex` 时保留来源 `codex`，映射非空仍启用相关项目来源。`oAr` 把关联项目和 cached placeholder 表达为 `source=chatgpt`，并附带本地线程。因此 source 标签不能充当产品模式排除依据。最终显示仍有布局/能力条件。
- **项目行有实际分流。** `nSs → TSs → OSs` 对普通 Codex 项目走 `Ibs`；关联项目走 `pss → Dos → Pt`。另有 `ProjectsIndexPage → xi → Lr → Dos`，及项目首页 `bo → Vos → K → q`。旧 pss 的无 chat 专用 guard 结论复用已有证据。
- **两版对话框共享本地文件夹条件。** capability、严格写权限与 CRUD allowed、普通私有 g-p- 项目以及 open-default memory 同时成立才呈现。旧 Pt 的 L 是局部权限变量。缺失 memory_scope 与显式 null 的行为不同；保存状态禁用组件并参与保存计数，不单独隐藏它。
- **新版有两层账户复核。** `Vos` 在等待后要求原账户非空且未切换，`K` 再作当前账户相等检查。K 单独 null/null 也相等，且 q 有直接导出；保护范围不能泛化。账户切换会抑制 mount，但 import/补取已在复核前发生。
- **本地任务用途有源码实据。** projects index 的 `jzt → FSi` 选择 `projectKind=local`，支持已有根路径、新项目占位、并发去重和异步结果条件性重定位。真实创建与持久化仍由 ISi/provider 决定。

## 维护决定与剩余边界

保留项目域的 backing 关联、本地文件夹与本地任务支撑，将第一方条件和时序接入既有 W06/W07/T01；框架/query/state 实现仍通过依赖引入。AO-A12 的直接呈现父链已有来源，不再写成“尚未找到消费者”。本 predicate 仍是支撑能力，不新增用户功能。

项目设置的 sources/connectors/memory/sharing 需分别取得模式证据；本批不作整功能或整文件排除。实际 gate、账户/权限值、DUe 匹配、ISi 后效和真实界面仍未验证。3 组既有 Chat 专用分支决定与 0 项整功能排除不变。

## 验证范围

完整解析 5 个不同 Program，共 11 次自适应解析；发布 39 个去重源码范围（含 2 个既有范围）、10 个命名 import/export 连接及 11 条九字段证据。54 项隔离源码用例通过，覆盖资格/权限、Codex 映射输入、来源分流、文件夹条件、账户切换和本地项目选择；依赖均为合成注入，未启动客户端、服务或模型。

详见[结构化合同](project-dialog-mode-v1.json)、[证据](project-dialog-mode-v1-evidence.jsonl)及[回放记录](raw/project-dialog-mode-v1/replay.json)。373 项功能、1216 条未执行产品规格、48 个任务、37 个职责及实施计划 v10 保持不变；源码回放不计产品通过。
