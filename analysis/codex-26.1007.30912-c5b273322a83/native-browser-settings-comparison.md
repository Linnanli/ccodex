# 原生浏览器设置页：独立运行时差异

固定公共 Electron 42.3.0 darwin-x64 的 guest webview 无法直接加载本次八个 Chromium 设置 URL，均返回 `ERR_INVALID_URL (-300)`。同一次探针的自建 host 与 guest 控制页均成功，进程退出码0；归档及运行时Framework与已校验归档一致。这是公共候选运行时的能力差异，不是原客户端功能验收。

| 原设置类别 | 本次直接加载结果 |
| --- | --- |
| 联系资料 | addresses、contactInfo 均拒绝 |
| 密码管理器 | passwords、根路径均拒绝 |
| 扩展 | extensions 拒绝 |
| 站点权限 | content、handlers、cookies 均拒绝 |

恢复任务T26／FSC-0221必须接入独立的原生浏览器设置能力。renderer保留类别/host/capability门控、路由和展示；`packages/runtime-adapter/src/browser-settings`负责特权页面、底层浏览器服务与分区，合同放在`packages/contracts/src/browser-settings`。以上为模块归属，尚未生成客户端实现。

运行时若保留这些页面，需要可独立取得并固定的运行时或fork；若独立重建设置界面，还须有等价的底层浏览器服务与行为证据。仅修改JS import、复制页面外观或隐藏不可用入口不能满足完整目标。第三方Chromium、UI等实现仍作为外部依赖，不生成进业务源码。两条候选路线均未证明可独立构建或行为等价。

原调用合同还要求特定partition、配对mountId/theme生命周期、back/forward/URL同步、销毁和迟到响应保护；详见[源码操作合同](settings-operation-batch-08.json)。原生页面内部操作及底层数据尚未完整盘点，仍归属于这项运行时任务，不能算已完成。入口的codexOrWorkLocal是权限分类，当前没有ChatGPT专属排除结论。

共五次公共运行时尝试：前四次含SIGABRT、SIGSEGV和超时，均作为不完整探针保留；第三次仅获得控制页与一个ERR_FAILED，崩溃原因未证明。最终一次改为单窗口、真实guest webview，完整测得上述结果。探针未读取真实浏览记录/密码、调用模型或运行原客户端，进程检查无本次残留。

[结构化结果及逐次原始记录](native-browser-settings-comparison.json)保存完整结果、边界、模块归属与验收条件。本结论只排除本次固定运行时中的直接嵌入路线，不宣称所有Electron版本或自定义实现都缺少该能力。原9项分析标准的状态、237项有限定义和808条待执行产品规格保持不变，目标继续。
