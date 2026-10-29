# 内嵌依赖定向契约调查

基线：codex-26.1007.30912-c5b273322a83。本次只读静态分析 4 个固定源文件，211 条证据，9 条依赖契约、2 条应用适配器候选。未执行目标代码，未复制第三方实现到维护源码。

现有 bundled-version-hint 分母 17；本次绑定其中 6 条，其余 11 条未在该子任务覆盖。另增加 router 与 ProseMirror 候选定位。

| 契约 | 文件范围 | 有代码绑定的版本自报 | 未解决项 |
| --- | --- | --- | --- |
| react-core-renderer | app.asar/webview/assets/app-shared-8bd9d0399038.js | 19.2.7 | 上游分发身份/修改状态、完整依赖闭包、运行与模式归属 |
| react-dom-renderer | app.asar/webview/assets/app-shared-8bd9d0399038.js | 19.2.7 | 上游分发身份/修改状态、完整依赖闭包、运行与模式归属 |
| react-router-renderer | app.asar/webview/assets/app-shared-8bd9d0399038.js | 7.18.1 | 上游分发身份/修改状态、完整依赖闭包、运行与模式归属 |
| statsig-metadata-renderer | app.asar/webview/assets/app-shared-8bd9d0399038.js | 3.34.0 | 上游分发身份/修改状态、完整依赖闭包、运行与模式归属 |
| prosemirror-model-renderer | app.asar/webview/assets/app-shared-8bd9d0399038.js | unknown | 上游分发身份/修改状态、完整依赖闭包、运行与模式归属 |
| prosemirror-view-renderer | app.asar/webview/assets/app-shared-8bd9d0399038.js | unknown | 上游分发身份/修改状态、完整依赖闭包、运行与模式归属 |
| react-core-browser-preload | app.asar/.vite/build/browser-page-preload.js | 19.2.7 | 上游分发身份/修改状态、完整依赖闭包、运行与模式归属 |
| react-dom-browser-preload | app.asar/.vite/build/browser-page-preload.js | 19.2.7 | 上游分发身份/修改状态、完整依赖闭包、运行与模式归属 |
| zod-v4-core-main | app.asar/.vite/build/zod-ClKgiFhi.js | 4.4.3 | 上游分发身份/修改状态、完整依赖闭包、运行与模式归属 |

React 的版本赋值被绑定到工厂的 export 参数，ReactDOM 同时有库名为 react-dom 的 devtools 身份对象；因此这些不是仅按字符串邻近得到的线索。仍未证明本地 bundle 与普通上游包完全等价。

Router 的 7.18.1 来自浏览器初始化函数中的 window.__reactRouterVersion 赋值；9 KB 初始化函数不是完整 router 依赖闭包。第一方路由注册必须保留，并按既有 route-contracts 验证。

Zod 4.4.3 对象被 $ZodType._zod.version 使用；此版本只覆盖该内部 core 绑定，不能覆盖所有 Zod 或 legacy 接口。

Statsig 仅确认 SDK 元数据 3.34.0。通知表中的相同版本是 @oai-statsig 系列；不能直接视为普通公开 Statsig 子包或推断未修改。

ProseMirror model/view 有库特有诊断与 Fragment、EditorView 实现候选边界，版本保持 unknown。通知里的 1.25.11 / 1.42.1 只是候选，尚不构成锁版本。

browser-page-preload 的 jx 与 Mx 保留为第一方应用适配器候选：jx 对接浏览器 host bridge、annotation 状态并管理 createRoot/render/unmount；Mx 持有评论相关 React 状态。其模式归属及真实可达行为仍需单独验证。

所有边界都是固定 bundle 中完整 AST 节点范围，不等同于原作者源码模块边界。没有检测到库版权/许可证注释；实际 AST 注释均为 sourceMappingURL。源码匹配、完整模块归属和依赖替换行为不计为完成。
