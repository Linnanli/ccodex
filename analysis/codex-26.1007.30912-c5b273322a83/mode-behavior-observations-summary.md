# 模式函数的隔离行为观察

固定基线 `codex-26.1007.30912-c5b273322a83`。一条实际Node22命令执行20个独立VM场景，gS 6项、lPt 8项、FJ 6项，预期检查均通过。仅运行保存的3个小函数共901字节，依赖由VM内内存替身提供；每次evaluation限制50ms，未提供process、require或真实外部资源。

gS首setter同步抛错会阻止后续setter，而返回rejected Promise仍继续；lPt两处persisted分支保留对象身份，能力表达式同步抛错可先于extension结果；FJ publisher同步抛错阻止atom写，返回rejected Promise仍继续。rejection由观察器立即挂catch后另列settlement。这些结果支持所选函数在明确替身条件下的控制流，不验证真实hI／ARt或完整错误传播链。

FJ的coerce和delay仅用于通用工厂场景，实际MODE两参数调用未据此启用选项。内存publisher故意不修改持久Map，结果不证明实际provider、UI、文件持久化、native、传输或Codex归属。旧MODE26／Storage46及其未执行场景保持原范围。

[读者](mode-behavior-observations.json)接到[逐场景输入、预期与实际结果](raw/mode-behavior-observations/author/mode-behavior-observations.json)和[实际命令收据](raw/mode-behavior-observations/author/observe-receipt.json)。20个场景共享一条实际命令，不宣称20个subprocess；源码、runner与计划全文仅保留local-only。本次交付metadata，不再次运行场景；原客户端、真实存储及模型任务新增均为0。
