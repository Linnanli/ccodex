# 三个 preload 入口与独立构建边界 v1

三个发布入口已分别接到主进程加载位置，并与上一批运行时加载合同对照。本批形成可用于 W02/W04 的构建规则，没有生成客户端实现，也没有证明独立运行时或完整构建可用。

| 维护入口提案 | 构建输出 | 职责与加载方式 |
| --- | --- | --- |
| `apps/desktop/src/preload/app.ts` | `dist/preload.js` | 应用窗口隔离世界桥接；bootstrap 路径经 M1e/y1e 进入 BrowserWindow 的 webPreferences。复用既有 `preload/app-host-bridge.ts`。 |
| `apps/desktop/src/browser-preload/index.ts` | `dist/browser-page-preload.js` | 浏览器页面注释、输入和 webMCP 通知；admitted guest attach 注入该路径。保留既有 `browser-preload/annotation/*` 职责。 |
| `apps/desktop/src/preload/mcp-sandbox.ts` | `dist/sandbox-preload.js` | MCP guest 的校验与端口握手；will-attach 在校验后覆盖路径及 sandbox 参数。 |

上述路径是维护方案，原发布文件用于来源定位。复用现有 desktop-transport、app-host 和 annotation 归属，不把每个 controller 另建一个包，也不将大范围 witness 复制到多个模块。

## 可直接采用的构建决定

- 每个入口单独生成一个 CommonJS 兼容 bundle，内部动态代码随该入口打包；`electron` 由选定运行时提供。检查产物不能遗留受控 require 表无法加载的代码 chunk 或包名。
- 维护源码以包导入引入纯 JS 依赖；构建时从新的精确锁安装并按入口打包。第三方实现只出现在依赖和构建产物，不手工生成到维护源码。不能统一 external 全部第三方包。
- 使用新工程自己的打包绝对路径。应用窗口、浏览器 guest、MCP guest 各自加载并归因错误；SDK 的 session preload 注入另行处理。
- 编译 target、运行时 types 和 ABI 由实际选定 provider 决定。当前不能把普通 Electron 的版本声明当作定制运行时资格。

## 第一方接口与生命周期

应用 `electronBridge` 对象有22项属性，逐项名称、表达式及原始字节位置见[桥接清单](preload-build-boundaries-v1-bridge.csv)。另有 codexWindowType、条件暴露的 Sentry 命名空间，以及窗口 message/端口路径；22项不能代表全部跨世界接口。

启动先同步读取 Sentry 元数据、build flavor、共享对象快照及系统主题。首次侧栏 bootstrap 是另一次惰性同步读取；返回 undefined 会再次读取。主进程需先具备对应 handler。worker 通过每 worker 的 Set/Map 管理订阅，最后一个回调删除时移除 IPC listener；共享快照在发送 shared-object-set 前乐观更新，收到通知后同步，undefined 删除键。主题、MCP host 端口、PIP decoder/frame 和 app-host 转移分别保留生命周期。

浏览器 guest attach 的 cU 策略显式要求 sandbox/contextIsolation/webSecurity，并关闭 Node 集成；应用窗口的选定 preferences 显式 contextIsolation=true、nodeIntegration=false，未显式设置 sandbox，默认值仍需按 provider 核对。浏览器源码有3处 executeInMainWorld，annotation policy 仅在安全顶层分支读取；webMCP 有独立 policy 分支，不能混用两者条件。可选 zoom 调用不包含在普通调用计数中。

MCP guest 校验协议、host/子域、端口/凭据、skybridge 路径、origin 和 initId，再筛选12个必需、7个可选端口并转移 replyPort。一次性标志在 postMessage 前置 true，代码内未设置失败重试回退。主进程仍需执行 partition/source/view/init 的独立校验；仅有 guest 校验不证明主侧或原生交付。

## 依赖与仍未验收项

浏览器 React/ReactDOM 的19.2.7是既有合同中的源码自报版本；实际发行、修改状态和新锁仍待核实。Sentry PreloadInjection 的 helper 尝试解析 `../../preload/default.js`，在 Classic/ready/绝对路径/文件存在条件下登记 session preload；它不能充当应用 preload.js 的加载依据。本批不新增 canonical 依赖，也不把上述第三方实现恢复成业务源码。

window.open 局部 handler 确有 browserPagePreloadPath override；整个 helper 对象到该参数的中间数据流本批仍未全部证明。原生 provider、headers/ABI、main-world 实际执行、真实端口交付、原安装路径独立性和干净构建均待验收。六项[构建与集成关口](preload-build-boundaries-v1.json)明确列出预期；当前均未执行。

本批解析5个完整 Program，另对 main/bootstrap 各做一次绑定定位；三个 preload 的普通词法匹配 Electron CallExpression 为48处（30/17/1），不覆盖可选调用、构造器或任意别名。补充 AST 依照原计划4.6；没有新 REA 运行、目标 eval、客户端启动、服务/模型请求或构建。

509项功能、582个不同操作、125支撑、1844条未执行场景、51任务和504 unknown/5 shared保持。原九项分析完成标准及完整复刻范围保持；本批只关闭三个入口的构建边界调查，未宣称整个分析完成。

[结构化合同](preload-build-boundaries-v1.json) · [桥接清单](preload-build-boundaries-v1-bridge.csv) · [证据](preload-build-boundaries-v1-evidence.jsonl) · [运行时脚本合同](native-runtime-embedded-sources-v1.md)
