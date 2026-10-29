# 设置分类、访问资格与产品模式边界

本批把设置分类接到实际访问状态定义，确认它们不能直接作为删除ChatGPT功能的清单。见[逐项来源合同](settings-mode-boundary-contracts.json)、[25条限定证据](settings-mode-boundary-evidence.jsonl)、[12条待执行规格](settings-mode-boundary-scenarios.json)及[来源与执行记录](settings-mode-boundary-provenance.json)。本批没有运行目标函数、启动客户端、修改设置或提交模型任务。

| 分类标签 | 分类项数 | 所选源码中的访问条件 |
| --- | ---: | --- |
| chatGpt | 14 | DG.status为allowed；DG取调试覆盖或TTn，TTn检查surface、认证来源、账户匹配和plan |
| chatGptOrCodex | 4 | chatGpt或codex选择器为true |
| codex | 7 | _q.status为allowed；组合local与Work云端／本地状态 |
| codexOrWorkLocal | 9 | JAn.status为allowed；组合local与Work本地状态 |
| codexLocal | 6 | pq.status为allowed；调试覆盖或fq.local |

Ta共40个分类项；Tt有53个命名可见性分支，另13分支无Ta分类。53项与旧settings registry逐范围关联，并保留git-settings等fall-through到实际return分支的关系。它们是设置条件的有限清单，不能替代完整功能分母；每项仍为mode unknown、排除false、featureId未分配。

local、voice、workCloud、workLocal由不同规则生成。GK先处理surface和认证加载；非chatgpt/chatgptAuthTokens认证的所选路径返回allowed/accountId:null，ChatGPT认证继续检查账户、plan与workspace开关。FAn再对Work云端、本地copilot与voice施加不同unsupported-auth规则。源码返回allowed不证明真实客户端或后台服务已经授权。认证来源、访问资格、主机能力和home composer的chat/work偏好须分开记录。

LAn按首个allowed、loading、第一项error、第二项error、第一实参的次序合并，不能用简单mode标签替代。pq、mq、hq、DG还受调试覆盖和gate影响，实际provider、输入订阅及gate值未观察。设置hook的第二参数默认true；false时仅Ca的12个slug继续处理，本批未把该参数的全部调用点接上，不能猜测它是产品模式。

分类条件与逐页predicate相交；无分类时只跳过这一层分类过滤，仍执行逐页条件。pending与error有各自处理，error没有简单乘上分类条件。可见列表、导航列表、选中项fallback与route内容渲染分别受控，不应在恢复时合并成一个菜单开关。

computer-use归入codexOrWorkLocal，再叠加主机能力及加载状态。本批只闭合设置列表的访问条件；页面内部、Messages直接子路由、手机setup、安装后步骤和本地服务仍按[CUA消费者合同](cua-settings-consumer-summary.md)分别判断。14个chatGpt分类也不等于14个可删除功能；后续还需核对实际调用方及共享依赖。

拟恢复源码的职责边界是：账户与workspace访问状态、host capability、设置目录／可见性、home composer偏好及各页面application facade。状态保留loading/error/denied原因和组合顺序；第三方state/query实现用依赖引入。本批提出职责分离，未还原原作者目录，未生成客户端工程，也未确定这些导入的完整第三方身份。

本批包含23条源码事实和2条作者推断，80个规范代码单位、140个词法位置和5个按模块身份连接的导入导出。7条数据解析命令共解析8个完整Program，涉及2个唯一文件；其中source-05虽命令成功退出，但漏读TemplateLiteral值，其派生表被拒绝，source-07修正后纳入规范结果。另一个初选Trt实际是图标，vr来自initial的U_t，已从分类证据排除；原候选保留供审计。作者第二稿为53项补旧证据ID及fall-through关系，未改变25条事实。所有版本、解析器元数据、工具、stdout/stderr和receipt保留；没有新增REA或独立语义审查。

作者核对2份冻结源码的367个唯一范围、731处坐标，含UTF-16与UTF-8位置，并核对已保存输入和导入模块身份；这些检查支持来源可追踪，不替代真实行为观察。12条规格未执行，也未并入原160条feature规格。当前37功能、40用户操作／5机制／26队列、967未映射旧入口及337 deferred保持；没有新模式分类或确认排除，完整分析仍未完成。

下一步追设置hook的实际调用参数、访问输入发布者和各候选页面的共享依赖，再决定保留范围；不能仅靠分类名删除页面。停止／重启的既有观察仍为interrupted，未证明续跑；已批准模型样例组已用2／2、剩余0。本批不增加模型或系统设置操作授权。
