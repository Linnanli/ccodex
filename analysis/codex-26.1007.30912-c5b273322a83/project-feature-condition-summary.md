# 项目 localFolders 剩余状态条件的静态补充

基线 codex-26.1007.30912-c5b273322a83。沿旧冻结 settings 条件 s=c(rt) 的必要导入与导出追踪，读取/哈希 settings、shared 与小型 local-folders 模块三个源。新解析小模块 5983 bytes（13顶层语句、1981 AST nodes），以及 13 个完整 shared 函数、2个完整候选赋值、8个 export specifiers、4个 settings 原始单位；不新解析大型 shared/settings 全模块。28 parse units，15022 原始 bytes（含重叠），51 条新证据，15条旧 journal 原字节子集。

保存的完整 settings 绑定给出 c←shared.Ban、rt←local-folders.i。小模块导出 i 的是 Program var L，R initializer 将其构造为派生状态；V 内另有同名 let L，不混用。callback 按 && 顺序要求：e(E) 为 truthy；remote services 的 projectChatGptProvisioning 非null；projects 非null；e(O) identity 非null；k(e,c.LOCAL_PROJECTS).data 非null。这是源码合同，未观察实际值或渲染分支。

shared aliases 使 E/O/k/c 分别对应 C7r/T7r/nK/Nj。选定 C7r 读取 keyed gate 2880010779，$U 的候选定义调用 client.getFeatureGate 并含 false 默认/server fallback；T7r 候选先检查 C7r 再要求 OG/kG 非null，返回accountId/userId；两个完整候选赋值只表明来源 TG 的字段读取。没有读取真实账号、token、用户targeting或运行状态，不能将这些条件归为 ChatGPT-only。

nK 返回 getter 对 iK/key 的读取；aK 中候选 query 请求名为 get-global-state，data 经过 ODn/kDn/Qpt。LOCAL_PROJECTS enum 是 local-projects；选定默认registry没有显式 LOCAL_PROJECTS 项。实际query结果、fallback语义与host能力均未运行验证。capability receiver e6 的旧 HTTP-origin 仅提供远端 services 初始化候选，不证明实际host注册。

c 的 shared facade lA 使用 uA 的 use/useLayoutEffect/useMemo/useSyncExternalStore API，uA 候选由 o()初始化。J 只保留 return bct(e,t,void 0,n) 的构造边界；不恢复React/客户端feature SDK/derived-store/query库完整实现。工具Babel/host Node只固定metadata，package.json原字节小snapshot另存。

当前范围只关闭一个旧localFolders条件的静态来源候选。原shared外层词法绑定、全部赋值/consumer、初始化、gate/身份/capability/query实际值、mounting、端口请求成功和产品模式仍unknown；静态false/default分支不能证明功能可删除，确认排除数为0。旧历史间接pin漂移未改写或升级。

producer：node .analysis-local/project-feature-condition-work/trace_project_feature_condition.mjs。独立verifier对最终main/journal/summary/reused journal计算validation.finalProducts pins后冻结；本producer自检查不替代独立或实际行为验证。
