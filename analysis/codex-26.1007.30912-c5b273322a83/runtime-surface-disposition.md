# 固定公开运行时的接口差异与第一方职责

对原有10文件范围的229条已解析API路径、1242个调用位置核对固定Electron 42.3.0的[官方发布描述](https://github.com/electron/electron/releases/expanded_assets/v42.3.0)：189条同时有API JSON和类型声明，23条仅有类型声明，17条在两者中均未声明。三条`.bind`路径对应6处JavaScript绑定调用，按底层函数核对。该比较不证明参数、事件、平台或行为兼容。

自有公开运行时探针读到17条均为`undefined`，6条公开正例均为函数；没有调用缺失方法。隐藏窗口已销毁，但app.quit未在期限内完成，监督器最终终止了自有进程组，进程检查无残留。读数作为有限证据保留，完整成功运行数为0；不重试掩盖退出问题。

| 固定描述中缺少的路径 | 第一方能力边界 | 已保存调用数 |
| --- | --- | ---: |
| `app.beginNativeMenuTracking` | native-menu | 1 |
| `app.collectMeasurements` | measurements | 2 |
| `app.configureMeasurementCollection` | measurements | 2 |
| `app.endNativeMenuTracking` | native-menu | 2 |
| `app.isRuntimeFeatureEnabled` | runtime-feature-policy | 1 |
| `app.setDebugChromePagesEnabled` | runtime-feature-policy | 3 |
| `app.setLegacyChromePolicyFallbackEnabled` | runtime-feature-policy | 2 |
| `app.setRuntimeFeatures` | runtime-feature-policy | 2 |
| `app.showTaskManager` | diagnostics | 1 |
| `BrowserWindow.isAlwaysOnTopSupported` | window-capabilities | 2 |
| `BrowserWindow.isInputShapeSupported` | window-capabilities | 1 |
| `BrowserWindow.isSystemBackdropSupported` | window-capabilities | 1 |
| `BrowserWindow#instance.setHistorySwipeNavigationState` | window-capabilities | 1 |
| `Notification.getPermissionStatus` | notification-authorization | 1 |
| `screen.isCursorScreenPointSupported` | cursor-capability | 1 |
| `Session#instance.setPermissionPromptHandler` | browser-permissions | 1 |
| `systemPreferences.getFontFamilies` | font-enumeration | 1 |

[逐项调用约束和证据](runtime-surface-disposition.json)覆盖24个精确第一方源码单元、25个上述调用。测量不是进程metrics，字体getter没有局部缺失回退；不支持Owl feature的特定异常可返回false，但缺失方法的TypeError不自动进入该分支。浏览器prompt handler还与默认拒绝、通知、下载和导航策略共同配置，不能仅替换方法名。

当前处理决定：第一方源码维护九组能力接口及业务状态，运行时或有来源的独立实现提供底层能力。普通Electron直接替换路线仍被排除；带第一方适配的路线继续保留候选资格。Owl独立分发/源码尚未取得资格，完整运行时路线未选定。

旧决策中的浏览器接收方未知已由[所有权合同](browser-ownership-contracts.json)BA-04至BA-08部分关闭：重复接收、路由、generation和清理顺序已有静态定位；实际native lease消费及转移/clone仍未知。既有[公开历史对照](public-history-duplicate-comparison.md)继续使用，不重复验证。

17条不是全部私有能力清单。4293个名称候选、34个解析预算触顶表达式仍在未解析范围；原生更新provider、Node网络/IPC、adoption/clone和特权浏览器设置另有已登记边界。公开描述及类型文件只在分析临时目录保存，发布物不包含第三方实现。

下一项定向分析限定为runtime feature允许键、reset和unsupported条件、legacy-policy能力predicate及保留消费者，定位`At`、`e$`和`n$`，再确定需要哪些native provider。功能仍为373项、48任务组、1216条未执行规格；本批新增模型提交、原客户端运行和产品验收通过均为0，完整分析尚未完成。
