# shared HTTP service 来源的有限静态候选链

基线 codex-26.1007.30912-c5b273322a83。只读取并哈希 shared 源 607ad0866dd25ed3764711b4467a9b60708353a599485b5249ff4cbe0e870245；沿已有 kxn→e6.httpFetch，只新解析 qli/Uli/Hli/t6/hFt/yF 六个完整函数；原 kxn 与保存的 shared export clause 只重核已有完整范围/原 journal hash，不新增 AST。6 个选定 parse units，共 47285 bytes（含重叠），新增 46 条 source/span 证据。未重跑全 bundle AST、目标/UI/网络/模型，未读取账号、历史或凭据。

候选连接：qli 内 `$3=Uli(Vli),e6=await $3.services`；Uli 创建 MessageChannel，向 window.location.origin 发 connect-app-host 并转交 port2，随后用 port1 与 local target 调用 nIt。选定 yF initializer 有 `nIt=hFt`；hFt 返回 `new BFt(new VFt(port),localTarget,options).getRemoteMain()`。BFt/VFt/oF/Bli 的完整来源范围及方法单独定位；aF/zFt 只语义审查 constructor/getMainImport 必要成员，其余成员的完整 class locator 不表示逐成员审查。BFt 经 zFt.getMainImport 获取 imports[0]，aF constructor 创建 SFt Proxy；实际 await 解码、RPC delivery 和 peer service 未验证。

Vli 是 Hli 构造的 Bli local callback target；Bli.services 返回自己的构造参数对象。它有6个直接 callback 字段和2个未展开 registry spread，和 qli 等待 connection remote-main 的 services 不是同一个语法接收者。不能把本地 callback 对象当成 host httpFetch 注册表。

原 shared 中 e6=、Vli=、nIt= 各只有1个字面候选，httpFetch 只有 kxn 的1个访问；这些只是固定 source 的文字选择分母，不是全部 RPC service 注册、运行可达、全模块外层 binding 或函数覆盖证明。保存 export index 给出 e6→fN、qli→mN、Uli→hN、kxn→OFt；来源/pointer/hash 与同模块定义范围保留，不能按跨模块同名接线。

本轮只收窄为 source-qualified app-host/RPC 连接候选，httpFetch 的实际 host 注册/实现、接收 port 的 peer、原全模块外层词法 binding/后续赋值、初始化次序、请求成功和产品模式仍 unknown。MessagePort、frontend/window/header 标签不能单独判定模式，也不允许据此移除功能。旧 facade、root 发布文件与历史失败/间接 pin 未修改或升级。

复现 producer：`node .analysis-local/http-service-origin-work/trace_http_origin.cjs /path/to/@babel/parser/lib/index.js`；独立数据验证：`python3 .analysis-local/http-service-origin-work/verify_http_origin.py`。源 JS 仅以 sourcePath/bytes/hash 保留，不复制实现进输出；引用的旧 journal 原记录字节另存 referenced-existing-evidence.jsonl。
