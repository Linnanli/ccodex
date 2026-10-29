# preload 的 connect-app-host 转发静态证据

基线 codex-26.1007.30912-c5b273322a83。仅完整解析固定 preload.js（6909 bytes，SHA a3e622f8d80a83e58fb3cfcc640fa7e14e6461cccdae9ef7d7b0c821dde256b7），核实 22 个顶层语句、1813 个 AST nodes；未解析其他大型 bundle，未执行目标源码、UI、模型或网络。新增 32 条独立 source/span 证据，21 个完整选定范围保留原始文字；累计 1559 bytes（含重叠），去重 783 bytes。

源码在 `typeof window<`u`` 条件后注册 window 的 message callback。callback 使用 `t.source!==window||t.data?.type!==`connect-app-host`` 条件提前 return，然后从 `t.data` 解构 `port:n`，调用 `e.ipcRenderer.postMessage(_,void 0,[n])`。Program 的 `e` 由 `require("electron")` 初始化；`_` 由 `codex_desktop:connect-app-host` 字面量初始化。具体 &&、完整 callback/guard/declaration/call/transfer ranges 的原文与 SHA 均保留，不能只按字符串同名连线。

完整小 Program 的可见词法声明与作用域扫描确认 callback 内 e/_ 对应上述 Program binding；t 对应 callback 参数，n 对应 callback block 内 let 解构。另有 25 个独立同名 e binding，已记录其声明范围和对应参考数量。20 个赋值/update/循环 AST 候选中，6 个直接标识符赋值目标均不指向这4个选定 binding；未发现 direct eval/with 源码形式。这只说明可见源码中的重绑定语法，不能证明外部对象属性、运行时或跨进程行为。

Electron 是 require 边界，此补充不生成它的实现；Babel/host Node 仅作为固定分析工具输入。实际 Electron 返回对象、ipcRenderer 属性、window sender、callback dispatch、端口传送、main receiver、运行成功和产品模式仍 unknown。通用 channel 名称不能证明 ChatGPT-only，确认排除数为0。第三方 Sentry 等无关 preload 代码的完整 AST 计数并不代表逐功能语义审查，完整源码未复制进产物。

复现 producer：`node .analysis-local/preload-app-host-work/trace_preload_app_host.mjs`。独立 verifier 会对最终 main/journal/summary 直接计算 validation.finalProducts pins；此处 producer 检查不能替代独立核验或运行行为证据。
