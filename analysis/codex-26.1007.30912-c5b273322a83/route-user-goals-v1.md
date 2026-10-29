# ZIs路由的页面与操作消费者 v1

固定135条path-route已逐条连接实际组件、具名行为边界或无直接操作的路由槽，归为59组页面/操作提议。59不是新功能数量；既有488功能、534操作、1650未执行规格及721来源待处置记录均未改写。完整分析未完成。

最终查询解析84个完整Program，保留111个组件绑定、84条导出记录和12条显式导出/导入别名连接；旧layout拓扑复用。不存在按同名minified变量跨文件连接。

本批对维护结构有直接影响的结论：

- /local入口的zKa调用能力查询后直接返回children，未以能力结果阻断渲染。不能凭capability字段生成不存在的拦截。
- 四个账户会话入口明确allowWork:true；MCP全局视图显式区分codex/chatgpt productContext。名称包含ChatGpt不能作为整文件剥离证据。
- 首次工作区选择会调用createOrSelectLocalProjects，包含选择/全选/添加目录/跳过以及带位置校验的导航；它是需恢复的实际流程候选。
- 云会话同一组件覆盖main/hotkey，区分404不可访问和无缓存的其他失败，并保留重试；这只是静态错误合同，没有新增真实失败样例。
- /diff的选定输入函数直接接收state.unifiedDiff，不因错误文案写base64就发明解码步骤；/plan-summary只显示既有计划内容，不执行计划。
- 旧插件、远程连接和/o入口已有明确兼容导航；扩展新任务页的hooks副作用单列，未把重定向误报为整个函数无操作。

各组的保留边界可用于下一轮功能归并。relatedExistingFeatureIds仅表示相关入口或功能家族，不认定目标等价，不据此减少旧功能来源待处置数。实际模式、账户/平台开关、服务成功、取消及恢复后效仍需各自证据。

| 组 | 路由 | 页面/用户目标 | 已确认处理与剩余边界 |
| --- | --- | --- | --- |
| ZRG-01 | ROUTE-0002 | 打开计算机交接目标 | BrowserHandoffPage解析目标；账户/用户/目标缺失显示不可用状态，否则按connectionThreadId/threadId/tabId渲染目标；提供Return home。 **边界：**目标解析器与交接组件的会话绑定、权限及实际焦点效果未运行验证。 |
| ZRG-02 | ROUTE-0003 | 由深链进入云环境创建选择器 | 拒绝非空search/hash；按账户、用户与environmentConfigs可用性选择加载、不可用对话框或创建选择器；关闭时核对来源账户并后退或回首页。 **边界：**选择器创建/保存后效复用既有云环境合同；本批不运行服务。 |
| ZRG-03 | ROUTE-0004 | 认领推荐链接 | ReferralShareLinkPage校验linkId与ChatGPT token认证条件；enabled时safePost /referrals/link/{link_id}/claim，成功回首页，失败显示错误。 **边界：**明确是chatgpt_referral_consumer_free服务流程；不据此推断其余共享账户代码可删除。 |
| ZRG-04 | ROUTE-0005 | 进入归档记录管理 | rFs渲染bFs；既有归档合同明确该界面包含本地、云端及账户会话分支。 **边界：**本批复用archive-mode-ownership及既有FSC-0280至0284合同，未把整归档页面标成ChatGPT专属。 |
| ZRG-05 | ROUTE-0007, ROUTE-0009 | 打开Dot首页或其会话 | OrbitPage分支渲染首页容器；OrbitConversationRoute是children透传包装，加载器另预取MessagingRoomView与LocalConversationPage。 **边界：**未运行FeatureNavigationRoute的状态/功能可用性；预取不证明MessagingRoomView必被渲染。 |
| ZRG-06 | ROUTE-0008, ROUTE-0015, ROUTE-0016 | 进入首页、新任务或项目选择上下文 | dFs识别/projects及search中项目上下文；项目入口按si和chatgpt能力选择等待、重定向、fIs项目选择或OJa(routeProjectId)。/与/projects无直接element，继承该父组件。 **边界：**OJa/fIs内部操作仍以其既有合同或具名组件为边界，不能按/dots/new名字把dFs全体划为ChatGPT。 |
| ZRG-07 | ROUTE-0012, ROUTE-0036, ROUTE-0163 | 进入客户端引导 | OnboardingRoute在authMethod非chatgpt或debugOverride时返回fallback，否则按账户类型选personal/k12/health/workspace步骤；FirstRunPage按认证及引导版本选步骤，onAccept写NUX状态并导航首页；OnboardingPage挂载FullscreenOnboarding作用域。 **边界：**authMethod=chatgpt不是产品ChatGPT模式的等价判定；引导决策、账户条件与真实写入/启动状态未执行。不同入口不是单一等价功能。 |
| ZRG-08 | ROUTE-0013 | 保留无直接页面的工作区路由槽 | 该Route只有path，无element及本地操作消费者；匹配经过AuthedRoute和外层XXa/VZa。 **边界：**不能从workspace/deactivated文本虚构停用对话框；实际祖先渲染与外部工作区状态保留未知。 |
| ZRG-09 | ROUTE-0017 | 从浏览器入口切换至Work上下文 | jZ(browser:true)限制平台；fFs在Dc allowed时按wp选择gS(work)或sPt(work)，在microtask后渲染dFs。 **边界：**平台判定和状态值未求值；已存在MODE publisher合同，不重开其存储provider。 |
| ZRG-10 | ROUTE-0018 | 打开账户或本地映射项目 | sFs从pathname解析projectId并查本地项目/开关；未匹配时带chatGptProjectId state回首页，否则oZ包裹OJa(routeProjectId)。 **边界：**项目映射、账户能力和运行实例未执行；分支包含模式相关行为，整条不排除。 |
| ZRG-11 | ROUTE-0019 | 打开商户设置 | xJa按Mm和nWa加载状态选择ei等待或wJa。 **边界：**实际设置动作终点为wJa；本批未把可用性状态当作业务模式。 |
| ZRG-12 | ROUTE-0020, ROUTE-0021 | 完成年龄或监护人验证 | 账户/用户具备后挂载独立验证状态机；本地视图提供retry/Check again、错误状态、返回/settings/account；监护人路由另受oZ包装。 **边界：**Persona会话、服务验证结果及其刷新/关闭后效仍未运行验证。 |
| ZRG-13 | ROUTE-0023 | 查看地图或指定实体 | MapsPage无entityId且能力未知时等待、不可用时回首页；有实体时渲染entityId面板并onClose回首页。 **边界：**地图实体内容与服务权限以子组件为边界，不能从路由名称建立完整地理功能清单。 |
| ZRG-14 | ROUTE-0024 | 打开分享的商品实体 | SharedProductPage将entityShareId传给分享面板，并按账户/用户/实体重建key；同时渲染默认会话背景。 **边界：**分享实体权限和具体交互属于下层面板；受oZ能力包装，未证明整文件模式专属。 |
| ZRG-15 | ROUTE-0025 | 进入购物界面 | aFs在1008193688待定时返回null，开启时渲染DFs，否则首页；外层oZ另行判断能力。 **边界：**DFs商品操作与实际开关值未执行；该条件不能推广为ChatGPT模式判定。 |
| ZRG-16 | ROUTE-0026 | 进入CME界面 | xWa查询chatgpt.cme能力：加载时显示CME加载态、可用才渲染ZFs/CmePage，否则回首页。 **边界：**能力名称与实际能力来源未闭合；CmePage下层操作保留具名边界。 |
| ZRG-17 | ROUTE-0027 | 进入图像页面及错误恢复 | qPs处理lang/slug、路由激活key和ImagesRoute错误边界；slug缺失选wFs，否则TFs(locale)，外层仍经oZ。 **边界：**图片生成、编辑或历史的操作明细未由该路由证明；不能自动新增所有图片功能。 |
| ZRG-18 | ROUTE-0028, ROUTE-0029, ROUTE-0030, ROUTE-0031 | 浏览、使用或创建GPT | 分别接MyGptsPage、GptDiscoveryPage、GptChatPage和GptBuilderPage；存在账户检查、刷新/重试和创建资格不可用状态，路由受oZ。 **边界：**这些是已确认的页面家族，未证明传递依赖闭包或实际可访问性，不作整模块删除。 |
| ZRG-19 | ROUTE-0032 | 处理Codex访问资格结果 | nFs按ep.status：loading返回null，allowed/error回首页，denied渲染VFs。 **边界：**VFs拒绝界面与实际账户资格未运行；这是Codex客户端所需候选边界。 |
| ZRG-20 | ROUTE-0033 | 显示听写状态及恢复粘贴失败文本 | GlobalDictationPage监听paste-failed/start；失败可复制恢复文本、打开Accessibility设置或dismiss并派发global-dictation-close；正常页面派发renderer-ready。 **边界：**复制、权限窗口、录音和粘贴副作用未执行；FSC-0489控制入口不能覆盖全部恢复动作。 |
| ZRG-21 | ROUTE-0034 | 打开独立调试窗口 | 既有KIs路由条件外，DebugWindowPage再次allowDebugMenu检查；订阅origin-conversation和analytics-history消息并传给detached调试面板。 **边界：**实际消息来源与Debug UI全操作不由本批证明。 |
| ZRG-22 | ROUTE-0035 | 处理扩展的新任务兼容入口 | NewThreadPanelPage调用l()/n(h)/s(_)后无条件返回Navigate(/,replace:true)。 **边界：**hooks的副作用未展开，因此只确认当前渲染重定向，不称整个函数no-op。 |
| ZRG-23 | ROUTE-0038, ROUTE-0039 | 按插件深链打开应用或设置入口 | PluginMcpAppDeepLinkPage解析codex://plugins/...，读取启用的插件库存及host模式；app-server走se；其余匹配入口路径并区分loading、found、not-found、ambiguous。 **边界：**插件库存、unique-name fallback、实际工具页面及服务后效未执行；两条路径同一组件，不新增两份业务实现。 |
| ZRG-24 | ROUTE-0040 | 打开MCP应用全局视图 | ChatGptMcpExtensionGlobalViewPage通过ke路径匹配计算productContext=codex或chatgpt，传给hostedView；父布局允许browser/electron并经tFs。 **边界：**组件名字包含ChatGpt不证明只服务ChatGPT；实际ke实例与hosted view协议仍需既有合同约束。 |
| ZRG-25 | ROUTE-0041 | 打开本地会话页面 | zKa查询codex.browser.execution后直接返回children；LocalConversationPage经显式ESM别名到Ac，组合jc与Mc(showComposer默认true)。 **边界：**查询结果未构成该包装器的渲染阻断；jc/Mc会话状态、任务执行与持久化继续采用既有合同。 |
| ZRG-26 | ROUTE-0042, ROUTE-0045 | 打开账户会话及临时或归档预览 | oZ明确allowWork:true，WKa拒绝WEB:ID并准备会话；f_区分archivedConversationPreview、temporary参数、激活key，渲染m_与会话作用域。 **边界：**可用于Work的入口不等于整页面已证明shared；发送、模型和恢复语义不在路由级闭合。 |
| ZRG-27 | ROUTE-0043 | 从指定消息进入会话分支流程 | BranchConversationPage校验conversationId/messageId；账户未就绪等待，否则传三项ID给W；路由allowWork:true。 **边界：**W分支创建/复制和模型后效未执行；不能与普通fork或预测fork自动等同。 |
| ZRG-28 | ROUTE-0044 | 打开共享项目会话 | SharedProjectConversationPage读取owner_user_id、等待账户/用户；属于当前owner时转自有会话，否则创建含accountId/accountUserId/conversationId/ownerUserId/projectId/visitKey的访问上下文；allowWork:true。 **边界：**实际共享许可及访问服务未执行，不自动归为ChatGPT专属。 |
| ZRG-29 | ROUTE-0046, ROUTE-0047, ROUTE-0048, ROUTE-0049, ROUTE-0050 | 打开Agent列表、详情或编辑入口 | uFs/lFs要求kZ及chatgpt能力，缺失则回首页；cFs始终可把useLegacyRoute=!kZ\|\|!capable传给KFs；编辑子路由nm提供Outlet。 **边界：**详情的legacy分支使整个Agent家族不能凭两个受限入口排除；qFs/KFs/JFs实际页面行为为具名后续边界。 |
| ZRG-30 | ROUTE-0053, ROUTE-0054, ROUTE-0055, ROUTE-0056, ROUTE-0057, ROUTE-0058, ROUTE-0059, ROUTE-0060, ROUTE-0061, ROUTE-0062, ROUTE-0063 | 浏览Space集合、页面或邀请 | 六个集合入口共用SpacesLandingRoute；personal按view选择collection目标；SpacePage处理account_id切换/清理、invitation_id及多种页面布局；SpaceDetailRoute按spaceId与状态选择视图；ZPs另检查browser.in-app。 **边界：**外层oZ和实际集合/页面权限仍未知；搜索、编辑、上传等细粒度操作不能从路由数量推导。 |
| ZRG-31 | ROUTE-0064, ROUTE-0066, ROUTE-0068, ROUTE-0069, ROUTE-0070, ROUTE-0071, ROUTE-0072, ROUTE-0073, ROUTE-0074 | 浏览企业资料及其子视图 | 浏览器和oZ包装后，BusinessProfilesPage按profileId选择St列表或qe详情；列表实际具有查询、分页、错误重试及products/section查询分支。其子路径自身没有element，交给父页面。 **边界：**qe下的具体dashboard/chats/insights等消费者尚未在本批展开；保留精确qe组件边界，不能把8个子路径各算成功能。 |
| ZRG-32 | ROUTE-0075, ROUTE-0083 | 打开健康界面或处理其OAuth回调 | pJa按资格/加载状态选择等待、gJa或首页；HealthOAuthCallbackPage在账户就绪后传currentAccountId给w；两路经browser/electron和oZ。 **边界：**健康权限和OAuth的w处理器/服务后效未运行，不能由callback路径名称认定模式剥离范围。 |
| ZRG-33 | ROUTE-0076, ROUTE-0078, ROUTE-0079, ROUTE-0080, ROUTE-0081 | 浏览财务页面及连接回调 | PersonalFinancePage按accountId挂载ba；ba从路径选accounts/chats/transactions或dashboard，按finances资格加载账户/连接/内容；PlaidCallbackPage独立处理回调。子路径不另挂新组件。 **边界：**财务服务、Plaid交换和账户许可保持外部边界；平台wrapper及oZ不等于全文件ChatGPT专属证据。 |
| ZRG-34 | ROUTE-0082 | 恢复应用连接OAuth流程 | AppConnectOAuthCallbackPage是独立导出，承担连接回调与恢复上下文；组件内状态区分匹配账户、回调失败和连接结果。 **边界：**本批固定在Je及其直接局部组件，不执行token交换或恢复任务；既有连接/automation OAuth合同只是相关入口。 |
| ZRG-35 | ROUTE-0085, ROUTE-0086, ROUTE-0087 | 浏览文件库、分享入口或单个文件 | hFs会按file_id/review_access_requests选择分享处理，按Mr/jD等转Space或Sites；LibraryFileRoute解析libraryFileId并onClose回/library；分享页处理account_id及邀请/访问审核上下文。 **边界：**LibraryPage的Ba内容与文件操作API未全展开；迁移重定向必须保留，不能复制成三个独立文件系统。 |
| ZRG-36 | ROUTE-0088, ROUTE-0091, ROUTE-0092 | 打开快捷窗口并创建或查看本地任务 | hotkey-window是Outlet容器；NewThread页配置mainWindowPath并挂载composer；Thread页维护主窗口路径、父会话返回和hotkeyWindowHotkeys.open，conversationId缺失时重定向。 **边界：**/hotkey-window根的index aIs决定初始导航；实际原生热键和窗口归属未运行。 |
| ZRG-37 | ROUTE-0093, ROUTE-0125 | 在主窗口或快捷窗口打开云会话 | 同一RemoteConversationPage使用main/hotkey variant；缺taskId重定向，404产生不可访问处理，其他失败且无缓存显示可重试错误；保留已有数据。 **边界：**task接口、host和账号实际实例及成功服务语义未运行；错误处理不是已执行失败样例。 |
| ZRG-38 | ROUTE-0096 | 打开内部演示工具 | oFs查询demo-tools能力，loading为空、不可用首页、可用渲染DIs。 **边界：**具体演示工具由DIs边界承载；当前账户可用性未知，不默认为产品必有操作。 |
| ZRG-39 | ROUTE-0098 | 浏览安全扫描、发现与仓库界面 | SecurityRoute按gate、插件库存、远程host状态得ready；不ready显示状态并可切本机；ready时按/security/new、scans、findings、repositories等路径选列表/详情。 **边界：**创建扫描、结果服务和具体发现动作仍在子组件；该源码确认新页面家族，未加入488个既有完整定义。 |
| ZRG-40 | ROUTE-0100, ROUTE-0101, ROUTE-0102 | 打开套餐、结账或工作区管理Web入口 | PricingPlanPage等待当前account并渲染Wo；CheckoutWebviewPage检验URL条件后渲染pe；WorkspaceSettingsWebviewPage有效解析时返回null，否则回首页。 **边界：**后两个入口的URL helper可能执行宿主操作；本批不宣称null等于无副作用，不执行支付或账户写入。 |
| ZRG-41 | ROUTE-0104, ROUTE-0107, ROUTE-0110 | 进入技能或插件列表容器 | 路径本身没有element；其index子路由分别挂j2r、kIs、j2r，父tFs先检查si。 **边界：**列表的实际操作复用已有Skills/Plugins合同；index构造不证明任意子路径运行时均挂该列表。 |
| ZRG-42 | ROUTE-0106, ROUTE-0109 | 兼容旧插件详情路径 | KPs把/skills/plugins前缀改为BHe；ManagePluginDetailPage把/skills/manage/plugins改/plugins并设breadcrumb=settings；两者保留search/hash/state且replace。 **边界：**BHe实际常量及新路径实例仍保留原范围依据；不是两套独立插件详情。 |
| ZRG-43 | ROUTE-0112 | 打开插件详情及安装/连接上下文 | PluginDetailPage显式ESM别名到ra；ra解析pluginId、host、marketplace、安装上下文，包含连接回调、启用开关与onTryInChat预填任务等操作。 **边界：**ra较大，不把其全部742缓存槽当独立功能；插件操作继续以既有合同为准，未运行安装或连接。 |
| ZRG-44 | ROUTE-0114, ROUTE-0115 | 打开拉取请求列表或指定请求 | PullRequestsRoute解析githubHost/owner/repository/number，非法指定请求转列表；合并记忆账户/route state/默认host，传initialPullRequest和githubHostname给qt。 **边界：**qt拉取、审查、评论及合并等操作不能由该入口推出；未提交外部请求。 |
| ZRG-45 | ROUTE-0116, ROUTE-0117, ROUTE-0118, ROUTE-0119, ROUTE-0120, ROUTE-0121, ROUTE-0122, ROUTE-0123, ROUTE-0124 | 浏览或管理Sites项目 | AppgenPage具有搜索、owned/shared/pinned视图、分页重试、创建/编辑入口；子页面按projectId进入设置/analytics overview/events/plugins/automations/database；wKa可整体转Space对应路径，analytics/events有独立flag。 **边界：**各项目写操作及服务仍需各自合同；将路由家族视作候选功能组，不把9个路径等同9个完整功能。 |
| ZRG-46 | ROUTE-0126 | 进入移动端远程控制设置 | CodexMobilePage读取MFA setup required结果、remoteControlStatus和debug override，传给M设置组件。 **边界：**M的实际设备添加、MFA验证与权限后效未执行；不能把该页简化为二维码。 |
| ZRG-47 | ROUTE-0127 | 兼容旧远程连接页面 | RemoteConnectionsPage按a()平台判定跳首页或/settings/connections，当前导出不渲染独立连接管理页。 **边界：**保留平台谓词实际值未知；具体管理操作引用Connections现有合同。 |
| ZRG-48 | ROUTE-0129, ROUTE-0130 | 打开自己或指定用户名的资料页面 | ProfilePage构造visit/profileVisitKey，读取preview=true，onUsernameChanged以replace更新/profile或/u/:username；qZa处理资料可见性及v1/v2开关回退。 **边界：**公开username资料与旧/settings/profile不自动等同；服务、保存和可见性未运行。 |
| ZRG-49 | ROUTE-0133, ROUTE-0137, ROUTE-0138, ROUTE-0139, ROUTE-0140, ROUTE-0141, ROUTE-0142, ROUTE-0143, ROUTE-0144, ROUTE-0145, ROUTE-0146, ROUTE-0147, ROUTE-0148, ROUTE-0149, ROUTE-0150, ROUTE-0151 | 按设置slug和参数打开对应设置页 | M6先处理work-settings/部分MNs slug重定向，否则读取lQa[slug]并包SettingsSection错误边界；eFs先校验browserFamily，非法则转/computer-use；其余路径传固定slug。 **边界：**沿用现有设置页合同；具体账户/平台分支及真实效果仍未证明。动态gWa.map模板不在这135条内，未机械展开新增功能。 |
| ZRG-50 | ROUTE-0136 | 打开MCP扩展设置视图 | electron-only父wrapper及tFs之后，McpExtensionSettingsViewPage经别名到it：选定hostId、读取views、传settings:true、selection/embedded/lifetime给K。 **边界：**实际视图生命周期、嵌入内容和host通信沿用现有preload/MCP合同，未执行。 |
| ZRG-51 | ROUTE-0153 | 查看开源许可文本 | OpenSourceLicensesPage显示加载态、许可text或No third-party notices were found，并提供携带state的返回导航；设置页入口既有FSC-0027关联。 **边界：**展示归档notice不证明每个依赖安装版本或可重建来源；依赖清单保持原有未知。 |
| ZRG-52 | ROUTE-0156, ROUTE-0157, ROUTE-0158 | 打开受信联系人邀请、拒绝或移除链接 | TrustedContactLinkPage从search读取token/entry_point并区分mode，传给ge；外层TrustedContactLinkLayout按authMethod选择布局。 **边界：**ge的具体确认、校验与服务结果未执行；与设置中的邀请/移除功能只有相关关联。 |
| ZRG-53 | ROUTE-0159 | 在Spotlight中搜索并打开任务或命令 | SpotlightPage处理焦点开关、搜索session、dot/chatgpt/local/remote结果导航、owner-window路径和threadSelection；命令执行/导航失败显示alert。 **边界：**实际原生owner window和命令成效未执行；需按结果类型保留共享UI与可剥离分支。 |
| ZRG-54 | ROUTE-0160 | 显示原生头像悬浮层 | 路由按jZ在electron渲染FFs，browser/extension转首页；AvatarOverlayNativePage无selectedAvatar返回null并派发pointer interaction false，有头像则渲染mv。 **边界：**头像选择来源、动画和原生窗口输入未执行；不能因Avatar名称推为ChatGPT模式独占。 |
| ZRG-55 | ROUTE-0162 | 打开登录及工作区恢复流程 | LoginRoute读取workspaceRecovery=true交给Gn；AuthedRoute在无认证且requiresAuth时带返回路径跳/login，XXa另选择引导及gatewayOAuth登录状态。 **边界：**认证实现、token持久化与服务协议保留具名Gn/gateway边界；本批不读用户凭据、不登录。 |
| ZRG-56 | ROUTE-0164 | 首次选择、添加或跳过工作区 | SelectWorkspacePage合并已有roots、推断roots和手工选择；可单选/全选、打开文件夹或skip；continue调用createOrSelectLocalProjects并检查返回及当前位置后导航与聚焦composer。 **边界：**实际目录存在性、项目创建与skip宿主处理未执行；它不是单纯展示文件夹的静态页面。 |
| ZRG-57 | ROUTE-0165 | 查看传入的代码差异 | EditorDiffPage的M只从route state读取unifiedDiff/conversationId，缺失显示No diff available；j解析差异/统计、unified/split/auto布局、rich preview及评论上下文。 **边界：**错误文案含base64不证明存在base64解码：选定M直接传unifiedDiff；解析及文件/评论服务另保留边界。 |
| ZRG-58 | ROUTE-0166 | 查看本地任务计划摘要 | PlanSummaryPage要求state.planContent/conversationId/hostId，缺失显示占位；_构造local-thread route及completed assistant-message交给消息渲染器，含错误边界。 **边界：**该页显示现有计划内容，不证明创建新任务、执行计划或恢复执行。 |
| ZRG-59 | ROUTE-0167, ROUTE-0168 | 兼容旧Orbit路径 | GPs将/o映射og；/o/claim-email或/approve映射SXe；其余去掉/o后接SXe，保留search/hash/state并replace。 **边界：**不从别名路径创建新的Orbit业务目标；目标常量与最终页面仍由既有来源确定。 |

完整路由、导出、源码范围和明确边界见[JSON](route-user-goals-v1.json)、[135条CSV](route-user-goals-v1.csv)、[九字段证据](route-user-goals-v1-evidence.jsonl)与[核对记录](raw/zis-route-goals-v1/verification.json)。

下一步把工作区选择、差异查看和计划摘要三组实际操作接入原功能清单；逐动作核对输入、触发、状态写入及错误/取消/恢复边界。禁止再重复135条路由角色分类，或递归展开无关provider。
