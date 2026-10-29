# General 访问摘要：具体消费者与业务支撑

AO-A02 的选定源码问题已交付：该行展示 Daybreak/cyber 访问资格，没有启用能力或写入偏好的动作。它有 Codex 的保留路径，完整功能模式仍为 unknown。

General 先通过已有 Codex 访问选择器选择 Vs，再要求 Codex/Work Local 访问允许和 feature gate。Co 按本地主机认证、偏好支持、gate 与版本能力，选择两条资格来源：

| 来源 | 资格判定 | 保留的边界 |
| --- | --- | --- |
| 模型列表 | 经 JRi/QRi 查询 model/list 并转换；仅可见模型参与，daybreakRed 优先于 daybreakBlue | 实际后端列表、过滤输入、host 与版本 |
| 账户资格 | 当前身份与账户严格匹配；personal 仅采用 individual grants；active cyber 的 tac3/government 为 Red，tac1/tac2 为 Blue | verified_access、accounts provider 与实际认证状态 |

账户查询 key 包含 account/user，且 v3 只为非加载的 chatgpt 认证构造身份。认证家族不等于产品模式。复用已有 SHs→yTn→TG 发布合同，本次只接通消费者，没有重复追 publisher。

Eo 显示的资格与模型菜单中的实际启用状态分开。此摘要不与归档 FSC-0280 或 Security 外部计划入口 FSC-0312 合并，也不新增功能 ID、owner 或模式排除。

41 项隔离源码用例通过，覆盖隐藏模型、Red 优先级、individual 过滤、账户不匹配、来源选择及查询身份。React、状态、版本判断和 HTTP 由自有 fixture 注入；没有真实 UI、服务、模型或原生执行，不能计作产品验收。

源码、导入导出、维护决定与未验证条件见 [JSON](access-summary-consumer-v1.json) 和 [证据](access-summary-consumer-v1-evidence.jsonl)。
