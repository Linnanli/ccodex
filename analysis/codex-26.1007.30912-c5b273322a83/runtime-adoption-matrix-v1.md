# 独立运行时能力与构建取舍

本次决定维护边界与逐组实施前提，尚未取得通过完整资格验证的运行时。固定17个缺席接口全部接入15组职责，另外合并既有clone/adoption、进程权限、更新及特权设置合同。15组是维护分组，不是完整私有接口或产品功能分母。

采用第一方能力合同/adapter与独立runtime/native provider分离的结构；普通Electron 42.3.0直接替换整个Owl的路线不成立。独立Owl来源尚未建立；平台bridge/引擎fork或等价服务实现仍按下表验证。

|组|职责|具体剩余前提|
|---|---|---|
|RAM-01 原生菜单 tracking|保留 menu-open/begin 与 menu-close/destroy/end 的成对生命周期。|菜单开启、关闭和销毁的原生时序及 tracking 副作用；取得对应实现源码或运行时扩展。|
|RAM-02 音频 measurement|保留具名 histogram 配置、ready/unsupported/unavailable 和计数不连续分支。|具名 histogram 的真实生产者、数据格式及调用消费者闭包；底层采集实现尚未取得。|
|RAM-03 运行时特性与 Windows policy|沿用已分析的两键 allowlist、boolean 合并、成功后缓存、reset、认证 owner/generation 和特定 unsupported 错误映射。|两键的原生效果、默认值与可逆性；supported-feature registry；Windows policy fallback 的实际清理效果。|
|RAM-04 Chrome 调试页策略|保留设置写入、副作用、启动路径与 allowDebugMenu 组合条件；不按名称排除。|启动 owner 的完整条件及底层开关作用范围；选定运行时的等效页面/策略 provider。|
|RAM-05 Task Manager|由第一方承担菜单、能力声明、错误传播和独立诊断 UI 的集成；保留顶层 bootstrap 前提。|基线实际字段、动作、刷新/关闭语义和独立 UI 实现；不以空函数满足 guard。|
|RAM-06 窗口平台能力|保留 always-on-top 的 false/null 发布及 Windows GPU/backdrop 判定；input-shape 先补 owner。|input-shape 实际功能消费者与平台条件仍需内部源码追踪；三项原生支持条件和实现 provider 未验证。|
|RAM-07 历史滑动导航|保留 primary 窗口注册、darwin 限制、overlayBounds/Color 空值转换及状态保存。|原生手势、overlay 与导航状态同步的独立 provider 及目标 SDK/headers。|
|RAM-08 通知授权状态|保留 authorization 不可用返回 null，granted/denied/not-determined 的精确映射和错误传播。|目标平台授权 API、bridge 源码与实际状态映射；不从能显示通知推导授权结果。|
|RAM-09 屏幕光标能力|保留能力为 true 才建立 controller 的工厂条件。|平台能力条件与独立探测 provider；当前 getter 读数不构成跨平台证明。|
|RAM-10 浏览器权限 prompt|保留 app partition、browser permission handling、prompt 委托、request/check 默认拒绝和相关导航/下载策略。|prompt 参数、响应及生命周期和浏览器服务后效；公开 request handler 不构成同协议实现。|
|RAM-11 系统字体枚举|第一方承担直接查询和结果传递；不凭空填充字体列表或静默兜底。|返回值格式、字体集合/本地化行为及对应 OS provider 源码和目标 SDK。|
|RAM-12 浏览器 ownership、adoption 和 clone|主进程 owner manager 管理 route admission、generation、session/preload、pending 与销毁；可保留同一 live view 的移动方案。|可独立构建的 clone/adoption 实现；原 live clone 的实际历史/页面状态语义；同一 view 移动不能证明复制能力。|
|RAM-13 受限 Node 网络与 scoped IPC|保留端点构造、restricted/unrestricted 分流、relaunch 参数/环境和 open-event 重放；设计独立 broker/权限执行接口。|能拒绝通用网络和越界 IPC、允许声明端点的执行机制、平台策略与可构建实现；不是 permission.has 的返回值。|
|RAM-14 普通更新与 managed relaunch|普通 transport 与 nullable managed-policy 分离；保留 schema、策略监听、notice/deadline/重试与初始化失败语义。|独立签名/更新 feed/安装配置、平台 updater 以及 managed-policy 事件/注销；Sparkle 来源不覆盖 Owl binding。|
|RAM-15 四类特权浏览器设置|保留 contactInfo/passwordManager/extensions/siteSettings，kind/host/capability、partition、mountId、theme、导航和过期响应清理。|四类页面的底层数据/服务行为、独立 provider 与构建来源；固定 stock guest 已拒绝八个目标 URL。|

## 构建与升级决定

四组构建门槛已经接到既有BUILD输入和W02/W03：运行时types、独立获取/启动、native ABI/SDK、打包安装升级。拟议目录是维护建议，没有生成客户端实现或第三方实现。

固定Electron候选的完整源码提交为`e0127e99aeaa66bb580538fc7409831b5248cccb`；该提交DEPS记录Node 24.15.0，冻结framework静态结构为24.19.0。这一差异要求按选定目标重建与验证native依赖，不能据此单独断言ABI兼容或不兼容。[官方提交](https://github.com/electron/electron/commit/e0127e99aeaa66bb580538fc7409831b5248cccb)

Node 24.19.0的固定权限文档没有给出所需scoped IPC/网络策略，CLI文档查不到两个flag；结合已有本地传输探针，不接受仅传普通Node permission参数作为已实现的隔离。[权限文档](https://nodejs.org/download/release/v24.19.0/docs/api/permissions.html)、[CLI文档](https://nodejs.org/download/release/v24.19.0/docs/api/cli.html)

Sparkle 2.9.1的Swift包使用binaryTarget，属于预编译依赖路线；source build和Owl managed-policy binding仍分别待验收。[Package.swift](https://raw.githubusercontent.com/sparkle-project/Sparkle/2.9.1/Package.swift)

node-pty保留已确认的修改边界；objc-js保留已有Node22.23.2/x64独立构建及export-only load证据，目标运行时集成仍未通过。两者均已接到依赖清单，未生成第三方实现副本。

## 分析出口与后续工作

本轮关闭的是逐组维护/构建处置：每组都有来源、责任、拟议路径、具体缺口和验收。SD-02整体仍开放：完整独立运行时、部分内部消费者/owner及真实native行为未闭合。没有把接口声明、公开原语或局部探针计为完整复刻。

下一项内部工作为SD-05数据域职责映射；继续使用保存证据。只有取得新源码、发行物或具体provider时，才重访相应运行时取舍；不重复已完成的接口存在性枚举。373项功能、48任务组和1216条未执行规格保持。

[结构化矩阵](runtime-adoption-matrix-v1.json)、[证据](runtime-adoption-matrix-v1-evidence.jsonl)、[公开来源审阅记录](runtime-adoption-primary-review-v1.json)。公开来源记录的哈希只标识本地审阅记录，未冒充上游文件/二进制哈希。
