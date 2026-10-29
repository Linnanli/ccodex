# 导航入口与资源采用 v1

本批关闭主窗口、detached 和 orbit 的具名源码映射问题，落实为 5 项资源构建决定。它补充[工程方案 v12](implementation-plan-v12.md)及[入口/资源清单](process-entry-build-v1.md)，未证明真实导航、完整产品模式边界或独立运行时。

固定基线为 `codex-26.1007.30912-c5b273322a83`。11 个不同程序完成 AST 与作用域核对，最终一次提取 4,338,831 个语法节点、73 个选定源码单元，27 条九字段事实、6 条 namespace/export 连接与 2 条 ESM 别名连接均有冻结字节定位。首次引用位置集合包含属性键和声明名，已保留为被替代尝试；修正后重新解析同一组程序，两个 pass 共 22 次解析、8,677,662 节点。另对两个已有小程序复核 selector 初始值及 import 调用，共 26,828 节点；合计 24 次解析、8,704,490 节点，没有解析失败或目标代码执行。

## 应用窗口与 detached

`main` 精确 require 的协议模块提供 root、HTML selector 和 URL builder。selector 仅在 `initialRoute === /detached-window` 时选择 `detached-window.html`；其他值选择 `index.html`。URL builder 保留 `initialRoute` 和显式 MCP sandbox 开发标志。

主窗口 factory 将 `moduleDir: __dirname` 交给 manager，primary factory 再委托 `createPrimaryWindow`，把 `/` 初始路由归一为空。启动源码以 `t.d(t.s(__dirname), applicationNetwork)` 注册协议；冻结 root 为 `join(moduleDir, .., .., webview)`。新工程若采用 `dist/renderer`，须注入自己的资源根，不能照搬这个相对路径。

`createWindow` 的 dev 分支构造 renderer URL；packaged 分支检查选定 HTML 后 await `loadURL`。资源缺失或捕获到加载失败后转到生成的 data HTML。返回了 BrowserWindow、出现了错误页或 Dev URL 可达，都不能算目标 renderer 已成功挂载。

选定的 detached prewarm/open 方法明确传入 `appearance: detached` 与导出的 `/detached-window` 初始路由。open 分支也可能复用 prewarmed window；source lost、receiver prepared/ready、move 和释放各有条件。这里未证明注入对象的实际实例身份或运行搬移结果。

detached HTML 的入口动态导入 `initializeDetachedWindow`，成功后在 pagehide 释放返回资源，初始化失败时关闭窗口。初始化函数从 `detachedWindows` 服务取得内容类型、request 和 root，校验一致性，再装配标题栏和内容。选定 registry 为 `N={browser:m}`，不能从“独立窗口”一词推导这是本地任务线程的新窗口 renderer，也不能把 registry 初始字面量当成全局不可修改证明。

## orbit iframe 与运行时

`Bfo` 返回冻结 orbit frame URL。它的 `I1` export 经 editor-lazy 的 `s` import 进入预加载器；`Hfo` 的 `F1` export 经 `o` import 接入另一预热协调器。前者加 `preload` 参数并等待 `orbit-character-preloaded`，后者等待 loaded 后发送 inactive/reduced-motion 状态；两者均有来源/同源检查与超时/pagehide 清理，不能合并成一个成功信号。

iframe factory 设置 `allow-scripts allow-same-origin` sandbox 和 `cross-origin-isolated` permission。主进程的匹配器只接受固定 app origin、无用户名密码、锚定 hashed orbit frame 路径；子帧导航还检查同 app origin 与直接 parent main frame，非主帧 app redirect 被阻止。

匹配响应添加 `Document-Isolation-Policy: isolate-and-require-corp` 和 `frame-ancestors 'self'` CSP header。HTML meta CSP 是另外的约束；不能把这个 header 描述为删除了 meta CSP。实际运行时是否支持及如何执行这些策略尚未验证。

因此，新的 frame URL、资源 manifest、直接子帧白名单和响应头匹配器必须一并生成。采用新目录或新应用 origin 时，保留旧 hashed-path regex 会使合法新 frame 无法匹配；简单复制 HTML 不足以恢复这条路径。

frame 源码仅在 `crossOriginIsolated && SharedArrayBuffer` 时选 threaded，否则选 single-thread。两支分别动态导入 engine 模块，并通过 `locateFile` 及 module URL 定位 `.mjs/.wasm/.data`；预载资源 load 或 error 都会结束等待，因此等待结束不等于资源成功。清理还包括 presentation、owner lease 和事件处理。

这里的 avatar/editor presentation、conversationId、preload 参数及 threaded/single-thread 均不是 Codex/ChatGPT 产品模式。保留未知消费者与两条资源路径，engine/第三方实现通过固定独立包或运行时引入，第一方只维护桥接、生命周期及策略；不生成 vendor 源码副本。

## service-worker 的限定结论

选定 logout consumer 检查相关浏览器能力，然后查询 `/service-worker/events.js` 的已有 registration/subscription，必要时请求退订后 unsubscribe。这是清理路径，不能作为注册调用的证据。

保存的 worker 实现 push、notificationclick 和 HTTPS target hostname 条件，默认目标为 ChatGPT 域。它的文件内容不证明桌面已经注册，也不足以排除整个通知功能。注册生产者、权限、安装/更新、保留消费者和实际通知仍有明确缺口；本批不声称全局不存在 register 路径。

## 构建采用与行为对照

| 资源 | 采用决定 |
| --- | --- |
| 主应用 HTML | 保留共同壳与 Codex 路由；资源根、entry manifest、app 协议策略显式注入 |
| detached HTML | 保留服务/receiver/registry/lifecycle 边界；与线程新窗口目标分别维护 |
| orbit frame | URL、origin、导航白名单、响应头、sandbox、消息身份和清理同步配置 |
| orbit engine | 固定独立资源来源，保留两条能力路径及 loader 相对布局；源码构建与 ABI 未证明 |
| web push | 清理与注册分开；保留通知 receiver、目标 URL 和模式消费者的未决义务 |

历史[行为记录](behavior-checks.md)中，独立测试应用曾显示 Codex 控件、composer 和本地位置。这与共同应用壳需要保留一致，但没有辨明本批具体 HTML URL、detached receiver、orbit header 或 service-worker 注册。本批只回读已有观察，没有新运行，也不增加产品通过数。该旧文档的早期规格总数不作为当前全局计数。

本批停止继续展开 PEB-G02 的这些源码生产者；实际导航与完整模式仍未完成。接下来只解析已具名的 D6r/vYo 两个 audioWorklet URL 生产者，以确定资源输出。既有 provider/headers/ABI 缺口引用 BG-01 至 BG-04 和 15 组能力合同，不逐消费者重新深挖。

509 功能、582 个不同操作、125 支撑、1844 未执行规格、115 职责、202 依赖、504 unknown/5 shared 均未改变。原九项分析标准与七项实施验收保持；实现、构建和新增实际导航/模型/服务调用为 0，完整分析仍未完成。

[机器合同](navigation-entry-adoption-v1.json) · [5 项资源 CSV](navigation-entry-adoption-v1.csv) · [27 条事实](navigation-entry-adoption-v1-evidence.jsonl) · [原始提取](raw/navigation-entry-adoption-v1/extraction.json.gz) · [核对](raw/navigation-entry-adoption-v1/verification.json)
