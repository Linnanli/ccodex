# General 更新策略：provider 与消费者

AO-A01 的选定源码链路已交付：它支撑应用内更新策略，General 只呈现只读状态，没有新增更新操作。完整分析和实际更新器验证仍未完成。

`experimentalFeature/list` → shared 的按 host 查询 → `w_c` 查找 `in_app_updates`，随后分别发布页面布尔值与主进程三态输入；两者须保留为不同接口。

- 页面仅在 `enabled === false` 时显示 Managed。未显示该行不能证明更新已经允许。
- 主进程输入还合并配置开关、认证/查询就绪状态，可为 `true`、`false` 或 `null`。bridge 忽略 null/undefined，其他值取反后传给更新控制器。
- 已接通 main 的 `appUpdates:b` 与 bootstrap 创建的 `Kn`。控制器从 pending 开始，首次有效结果将本次启动锁定为 allowed/denied；后续结果用于报告策略变化。
- 启用更新器的构建中，源码设置 300000ms 等待计时器，超时委托允许初始化；denied 不被该允许方法改写。这里只核对源码，未运行真实计时器。
- 检查和安装入口等待策略 resolution 并检查 denied；平台初始化仍是外部适配边界。

维护时保留三层职责：General 只读呈现、renderer 策略查询/发布、main 启动策略与 updater 适配。保持第三方框架/状态/查询库为依赖，不生成它们的实现。暂不新增功能 ID、owner 或模式分类。

明确保留的缺口是后台组织策略生成、实际 host/account/gate 值、构建是否启用更新器、平台 native updater 和策略变化提示界面。这些缺口不再使同一 General 行进入重复盘点。

本次只核对冻结源码范围、命名导入导出与 provider 身份；没有客户端、服务、模型或真实产品测试。详细范围和证据见 [JSON](managed-update-policy-v1.json) 与 [证据](managed-update-policy-v1-evidence.jsonl)。
