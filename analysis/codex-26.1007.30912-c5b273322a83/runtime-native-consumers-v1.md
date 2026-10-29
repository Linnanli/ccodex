# Task Manager、通知授权与字体消费者合同 v1

已交付 RAM-05/08/11 的选定 JS 边界与消费者合同。原生 provider、实际行为和完整运行时采用资格仍未验证；原九项完成标准、实施计划 v10 与功能分母不变。

Task Manager 的 bootstrap guard 和 Help 菜单已有完整来源，本次复用，不再解析或回放同一入口。已保存运行时清单含一个零参数调用和一个 guard 读取；JS 没有该调用的数据或动作协议。进程字段、刷新、关闭等问题须由 native 来源或受控实际观察补齐，该源码调查至此结案。

通知服务仅在 macOS/Windows 注入。macOS Prod 且未打包时状态不可查询；native granted/denied/not-determined 映射 enabled/disabled/not-determined，其余 null。getter 的 native 错误传播；打开设置方法却会记录并吞掉内部错误。**FSC-0102 的 renderer toast 仅覆盖实际传播到 mutation/RPC 的错误，不能保证提示 OS 设置打开失败。**

Windows 直接打开通知设置；macOS 对 null/not-determined 发起授权请求而不等待其 Promise，等待 2000ms 后打开带 bundle id 的系统设置。设置、composer 和 onboarding 的 query 各有刷新条件；onboarding 只在等待时间戳后的 60 秒窗口中每秒轮询。beacon 返回 true 表示动作已处理，不证明已授权。

字体原生 getter 直接透传；UI 要求 family 与非空 faces，以及 PostScript/full/style name 和 isMonospaced 字段，单纯字符串列表不足。代码字体要求所有 face 等宽。缺少目录时保留自定义 CSS 输入；读取错误不会由 queryFn 自动转为空目录。样式选择与 FontFace loading 是独立责任：按 FontFaceSet 缓存 alias、合并并发，失败返回 false 并允许重试。这里记录的是消费者要求，没有观察实际 OS 枚举结果。

本批核对 40 个源码范围（含 3 个已发布范围复用）、10 条连接，47 项隔离源码用例通过。仅使用合成 native/shell/clock/scope/FontFace 替身；首次样例的 undefined 默认参数问题已修复并留档。没有启动客户端、真实服务或模型，不计产品或 native 验收。第三方实现不生成到客户端。

[完整合同](runtime-native-consumers-v1.json) · [证据](runtime-native-consumers-v1-evidence.jsonl) · [回放](raw/runtime-native-consumers-v1/replay-results.json)
