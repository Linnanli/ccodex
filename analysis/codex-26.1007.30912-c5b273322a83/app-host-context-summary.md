# App-host context/trust 实际调用来源的有限静态合同

基线 codex-26.1007.30912-c5b273322a83。只读取冻结main一份源；新解析u0e/M1e/vXe三个完整函数共40897 bytes，再整合独立有限trust调查的10个成员/helper units；合计13 units、41880 bytes（含重叠）、32条新证据与5条原host-HTTP记录。未解析整bundle或巨大window-manager class，未执行目标/UI/网络/模型或读真实认证/环境/历史。

u0e实际调用链：H=M1e(options)；Oe(event)调用H.isTrustedIpcSender(event.sender,event.senderFrame??null)；QXe的无spread options明示getContextForWebContents:H.getContextForWebContents、isTrustedIpcEvent:Oe。旧QXe内部参数alias是u/F，不能把callee局部名直接当caller对象。选定startup内无H/Oe assignment/update；原Program外层binding/property mutation仍unknown。

M1e本地R初始null，z=new y1e；返回setWindowContext(input)赋R=input，context getter在z.hasRegisteredWebContents(input)为true时返回R，否则null；trust函数绑定z。u0e传windowServices:H给vXe，vXe参数alias m构造de=new hXe(options)，调用m.setWindowContext(de)，返回getWindowContext闭包。该同作用域construction/slot/条件getter关系支持静态候选hXe→旧HTTP createAppHost合同，不证明实时注册、成功初始化、实例值或后续生命周期。

独立trust有限合同/具体完整source/hash/span和声明/参数/caller差异保存在主JSON与journal；不追全部window registration closure，不把membership/URL/frame代码当成实时认可证据。动态registry、原完整class/外层binding、实际sender/frame/port、RPC/network/模式继续unknown。旧host HTTP/preload历史状态没有改写。

复现：node .analysis-local/app-host-context-work/trace_app_host_context.cjs /path/to/@babel/parser/lib/index.js；独立pin/span/reference验证：python3 .analysis-local/app-host-context-work/verify_app_host_context.py。

选定trust代码：isTrustedIpcSender在sender.id非null且不在registeredWebContentsIds时返回false；否则调用x1e。x1e拒绝显式非mainFrame，再将(senderFrame??sender.mainFrame).url传P9。P9包含about:blank、app: host为-或空、符合HTTP(S)检查的同origin，以及file入口URL startsWith前缀分支。这个file判断不是精确pathname相等。M9源码用process.env.ELECTRON_RENDERER_URL或e1e；本轮没有读实际环境值或fallback initializer。hasRegisteredWebContents只查询集合中的input.id；没有追集合populate/unregister全闭包或验证任何真实sender。

失败历史保存在failures.json并作为独立input pin保留：首次producer自身局部变量遮蔽产生ReferenceError，修正后重跑。它没有执行目标代码，也没有新增运行/模式证据。
