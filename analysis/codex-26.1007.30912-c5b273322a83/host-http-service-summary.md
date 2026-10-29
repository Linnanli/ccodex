# host HTTP service 的有限静态合同

基线 codex-26.1007.30912-c5b273322a83。范围为 bootstrap、其直接main启动依赖与main直接require的provider三份冻结源；43 个完整有界原始 parse units，共 90332 bytes（含重叠），87 条新增证据、4 条逐字复用原记录。没有全bundle AST或目标/UI/网络/模型执行。

bootstrap 仅声明 zt 通道并以 vt 导出；main 的 g=require(bootstrap) QXe 注册 ipcMain.on(g.vt)。处理器首先 !F(event) 返回，F来自 isTrustedIpcEvent 输入；再取首个port，由注入的getContextForWebContents查context，调用可选createAppHost，再用CXe连接并注册view。真实信任实现、实际context类型和peer尚未验证。

选定hXe同一完整class内，constructor将this.fetchWrapper赋为new Ude；createAppHost内x=new i.mi(callback)，i来自src-BJv5Mk7n，其中mi getter指向Ue。Zde服务参数明示httpFetch:x。三个后续spread helpers的所选静态返回形状没有httpFetch，Zde保留service字段并提供services getter；外层helper binding/初始化/运行身份仍unknown。provider回调调用fetchHttp并附带page-checkpoint response observer，WebContents destroyed注册provider disposal。view端registerAppView等待的remote services与host Zde.services方向不同。

Ude.fetchHttp准备URL/headers/body，传递expectedIdentity、signal、upload progress和retry；允许的响应返回Response接口；普通fetch可保留上游body，progress分支先收集完整data并Buffer.concat，再构建Response，不能据此宣称端到端流式交付。HTTP失败及自身try内捕获异常转换为结构化error；URL/日志目标/计时预处理位于try外，其异常可由provider清理后重抛。performDesktopFetch源中保留网络allow检查、auth/surface/device/integrity目的地guard、认证获取/刷新、workspace路由/abort信号和受条件限制的401重试，再调用注入applicationNetwork.fetch或progress request。未读取任何实际认证/环境值。RPC/base、applicationNetwork和部分imported token/header/error/stream helper未追踪，网络结果未验证。

完整hXe/Ude class locator不代表所有其他方法已语义审查。全部来源/source span/pointer/脚本pins与原journal复用位置记录于JSON；源JS只以sourcePath定位，不复制实现到输出。模式保持unknown；标签和命名不构成模式证明。旧冻结产物、rootpublisher和历史failure/间接pin未修改。

复现：node .analysis-local/host-http-service-work/trace_host_http.cjs /path/to/@babel/parser/lib/index.js；独立验证：python3 .analysis-local/host-http-service-work/verify_host_http.py。
