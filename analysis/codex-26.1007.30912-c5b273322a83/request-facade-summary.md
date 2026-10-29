# Shared BY 请求 facade 的有限完整范围追踪

基线：codex-26.1007.30912-c5b273322a83；archive SHA256 c5b273322a833ce5165429d468021cc6289a11cc68d075b80ae773bd7fb6731f。使用现有 request-wrapper AST/index 与冻结 9-file 模式合同选择原始范围；未重新解析整个 bundle，未运行目标、UI、模型或请求网络，未访问账号、history 或凭据。

真实链是 9-file consumer 的 `./app-shared-8bd9d0399038.js:$wt` → shared local `BY` → `VY` initializer 中 `BY=new Gxn({getAdditionalHeaders:Nzn})` → 完整 `Gxn` facade → 已保存 lexical binding 的 `AW.getInstance()` → 普通路径的 `fetchJson/fetch/kxn/e6.httpFetch`。具体 httpFetch provider、最终 endpoint/base URL 与运行初始化仍未知。

同名风险：app-initial 的 exported `BY` 实际是 local `vko` initializer，和 shared exported `$wt` 的 local `BY` 不是同一个服务。两个实际 export specifier、完整 export declaration 与 definition 均独立定位；不能按跨模块同名合并。来源/index pointer/hash 均在 JSON；独立验证只检查本次直接输入与引用的原 journal bytes，先前间接 pin 的历史 mismatch 未由本轮解决。

完整范围确认的请求层：路径替换调用参数 toString；query arrays 重复追加，非数组 null/undefined 跳过；默认 header provider 在前、caller additionalHeaders 在后，surface 处理有大小写无关查找；string body 保留，其余 requestBody JSON.stringify，FormData 走额外 bytes/contentType helper；retry/keepalive/verb 路径各自保留。safe 方法名不表示吞错：makeRequest 对部分 abort/expected/transcribe 情况抑制 warning 后仍重抛原值。

AW.sendRequest 的普通路径与特定 `vscode://codex/` / dictation connect-info dispatchMessage 路径明确分开。OW/Dxn 错误对象、HTTP non-ok/JSON parse、abort/cancel/dispose、response/body/callback 和完整 stream 方法均保留定位；动态服务、流依赖及实际事件排序不在本轮验证范围。

Nzn 固定 frontend/form/window header 标签，再合并条件 route/device 分支与 computed/dynamic helper 输出。Pzn 只表达 bridge appVersion/device-support 的源码条件；computed key symbols 和实际 header 值未读取/未解析。标签及浏览器头分支不能证明实际模式，也不能据此将这些 modules 认定 ChatGPT-only 或直接移除。

分母：原 9-file candidate corpus 内找到 3 条 source-qualified import bindings、18 条直接 BY member 调用，来自 3 个文件；方法计数 {"safeGet":4,"safePost":13,"safePatch":1}。本轮读取并哈希 2 个冻结源文件，解析 20 个完整选定 units（含重叠 221347 bytes），产生 54 条新 source/span 证据。不是全应用 HTTP、模式或功能覆盖。

复现：`node .analysis-local/mode-facade-work/trace-facade.cjs /path/to/@babel/parser/lib/index.js`。全部 54 新 byte spans、6 输入哈希、27 次 JSON pointer 和 159 个唯一证据引用验证通过，0 errors。另用 validate_facade.py 独立核验静态输入、span、JSON pointer、来源 journal 精确记录字节及分母；保留原引用记录到 referenced-existing-evidence.jsonl。原产物与 root 发布文件未修改，动态实现/运行/模式继续 unknown。
