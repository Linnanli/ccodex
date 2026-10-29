# applicationNetwork 有限静态合同

固定基线 codex-26.1007.30912-c5b273322a83。原始源文件5份（4个JS与package metadata）；36个完整有界parse units、53549 bytes（含重叠）、24个tr类成员、70条新增证据、6条逐字复用host证据。没有全bundle AST、目标执行、UI、网络或模型任务。

实际 adapter 候选位于 bootstrap.tr：fetch进行policy检查并调用required electron f.net.fetch；request进行policy检查并返回f.net.request。application-network-startup名称不证明实例：该chunk的tt getter映射Br设置zr，默认zr调用未解析的fetch标识符（global仅为候选，原始outer binding unknown），Vr仅转发。bootstrap.oE创建本地r=new tr并以r.fetch闭包注册o.tt，返回aE.applicationNetwork:r。main.u0e取g.I()的applicationNetwork:a，传入vXe的t，再传入hXe选项；冻结hXe constructor选定new Ude表达式传e.applicationNetwork。该链为有坐标的静态实例候选，原始outer binding/reassignment、startup顺序和真实运行实例均unknown。

tr保留loading/ready/failed、generation、连接/account通知刷新、readiness、session.webRequest限制与dispose等状态。requirements.oa验证application.network并形成restricted/unrestricted policy；sa对local protocols放行，restricted仅https/wss精确allowedDomains匹配（去尾点），loading的null policy对其他网络目的地拒绝。devRendererOrigin旁路值unknown。preauth Statsig另有独立partition/header限制与完整nr URL/method helper（POST到https://ab.chatgpt.com/v1/initialize且无userinfo/hash）。

普通fetch与上传progress使用同一adapter候选的两种runtime API。冻结Ude的progress consumer调用getUploadProgress、事件、end(body)/abort，响应data先Buffer.concat再构建Response；native ClientRequest实际语义与网络结果未验证。网络startup.Xc临时transport按initialize→configRequirements/read→config/read（条件logout）读policy，finally关闭；Us/eo/Lr及解析helper尚未追踪。startup-requirements.da/ta/na包含Node permission/relaunch/IPС allowance与Owl错误文本；package仅声明electron42.3.0及owl-shell scripts。不能由declared electron spec推断stock Electron兼容或native源码已恢复。

第一方适配器归属为inferred；required electron/API及opaque库调用边界为source-confirmed。没有生成第三方实现。mode仍unknown，无ChatGPT-only排除证明。旧freeze/rootpublisher/公开文档未改。详尽ranges/hash/import/export/reused journal坐标、依赖分类与限制见application-network.json。

复现：node .analysis-local/application-network-work/trace_application_network.cjs /private/tmp/ccodex-rea-tooling/install/node_modules/@babel/parser/lib/index.js；独立验证：python3 .analysis-local/application-network-work/verify_application_network.py。
