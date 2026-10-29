# Codex 独立客户端恢复实施计划草案 版本 11

恢复固定基线的 Codex 界面、交互、状态、持久化和桌面集成，剥离已证明只供 ChatGPT 使用的分支，第三方实现通过依赖管理接入。工程应能维护、升级，并从干净环境构建打包，运行时独立于原客户端安装路径。当前仍处于分析和设计阶段，客户端实现尚未开始。

当前范围是 463 项有限功能、500 项用户操作、118 项支撑、51 个业务任务及 1569 条未执行产品规格。完整产品分母未知。[机器计划](implementation-milestones-v11.json)逐 ID 连接[功能 v42](feature-scope-v42.json)、[规格 v39](feature-scope-v39-scenarios.json)、[任务 v33](restoration-coverage-v33.json)和[职责 v8](feature-module-ownership-v8.json)。历史 v10 的 373 项范围不再作为当前实施入口。

## 工程边界与依赖方向

发布 chunk 用来定位来源；维护模块按进程、职责、状态权威及副作用划分。拟工程主干如下，具体路径以职责合同为准，保留 app-server-client、storage-contracts、main/persistence 等既有提案，不机械改名或按每个 controller 新建包。

```text
apps/desktop/src/main/               启动、窗口、宿主、系统及退出的组合根
apps/desktop/src/preload/            隔离世界、IPC、端口和受控注入
apps/desktop/src/renderer/app/       初始化、路由、多窗口和模式
apps/desktop/src/renderer/features/  功能界面、控制器及局部状态
apps/desktop/src/workers/            有独立生命周期的工作任务
apps/desktop/resources/              可追踪来源的资源
packages/                           按合同隔离的协议、后台、运行时及存储适配
tools/recovery/                     来源映射及可审查转换
tools/build/                        独立生成、构建和打包
tests/fixtures/                     合成样例及回归输入
```

renderer 调用按服务区分的合同；main/preload 的组合根注入传输、后台、存储和运行时 provider。业务控制器不直接绑定某个原安装路径或私有运行时单例。app-server、桌面 HTTP、app-host、resolver、扩展连接及 socket 分别保留接收方身份、错误、断连、取消和释放语义，不能共享一套含糊的消息总线。

| 设计决定 | 实施规则 |
| --- | --- |
| ARCH-01 | 按进程和权威划分组合根；每条 IPC/RPC 边界使用按服务区分的合同，renderer 不持有原生 provider。 |
| ARCH-02 | 现有 84 条职责和 48 个粗 facade 用于目录内职责划分，不为每个 controller 建一个 npm 包。具体拟路径优先于粗工程树；不自动改名 worker/workers 或现有客户端包。 |
| ARCH-03 | 共享来源 witness 只作为来源证据；按保存的共享/重叠规则选择实现所有者或注入接口，不能向多个目录复制同一 bundle 范围。 |
| ARCH-04 | W02 先形成 workspace 与构建配方，W03 准备能力类型；运行时和原生输入最终资格由 BG-01 至 BG-04 验收。保留既有两套依赖图，避免把全部构建输入成功误设为 W03 的源码前置。 |
| ARCH-05 | 202 条第三方记录通过依赖、单独补丁或明确 ABI 适配接入；原发布版本证据和新工程选择的精确锁分别保存，不能把未知版本填成推测版本。 |
| ARCH-06 | 只按已证明的 ChatGPT 专用分支剥离；未知模式、共享提交及账户/宿主权威保留。完整客户端验收保持 M1 至 M7，分析完成继续按原九标准。 |

## 来源到模块的转换约束

[职责映射](feature-module-ownership-v8.json)包含 84 条限定职责和 48 个粗工作流 facade；它们不等于 132 个已恢复模块。每条限定职责保留 responsibility、environment、mode、sourceRanges、imports、exports、sharedState、sideEffects、thirdPartyDependencies、proposedPath 十项字段。机器计划索引全部职责、功能及操作，不把粗 facade 的历史功能集合擅自扩充为完整权威。

1726 个来源 witness 和 27 条共享处置作为转换证据；原有 19 条逻辑重叠规则继续有效。一个来源范围可以支持多个判断，不能因此在多个目录复制同一实现。转换记录保存基线、源路径/hash/字节范围、变换方式、依赖、拟路径及回归场景。逐功能持久化权威仍有缺口；另列的 17 条限定存储关联不能充抵全部 463 项。

## 源码准备和真实集成顺序

两套[60 节点依赖图](restoration-current-ordering-v16.json)保持现有边和层次。源码准备可以在接口合同可用时推进；真实运行时、服务和持久化集成继续受外部输入及专门验收条件约束。

| 基础任务 | 源码准备上游 | 真实集成上游 | 准备输出 |
| --- | --- | --- | --- |
| W01 合同与来源映射 | 无 | 无 | 84 条限定职责、48 个粗工作流 facade 与 463 项功能的来源映射；1726 个来源 witness 及 27 条共享处置；逐转换保留十项模块字段 |
| W02 独立构建与依赖输入 | 无 | 无 | 独立 workspace、分进程编译及打包配方；202 条依赖的引入与精确锁任务、30 条构建输入补齐决定 |
| W03 运行时与平台能力 | W01, W02 | W01, W02 | 15 组能力接口及生命周期；已闭合 JS 策略与独立 provider 边界、四个构建验收关口 |
| W04 桌面传输与宿主 | W01 | W01, W03 | 按服务区分的 preload、app-host、HTTP、resolver、socket 传输与编解码；身份、信任、订阅、断连、取消及释放合同 |
| W05 后台适配 | W01, W02 | W01, W02 | app-server 请求通知适配与两个协议差异采用决定；预测 fork 和其他服务独立能力接口与不支持状态 |
| W06 状态与持久化 | W01 | W01, W03 | 11 个存储域与后续选定边界的 driver、根路径及权威注入；读取、写入、revision、flush、退出、迁移与恢复职责 |
| W07 应用壳与模式 | W01, W04, W06 | W04, W06 | 应用初始化、路由、多窗口与共享 composer/controller；产品模式、认证家族、执行位置、会话类别及资格的分离状态 |
| W08 其余功能与完整范围 | W04, W05, W06, W07 | W04, W05, W06, W07 | 51 个业务任务、463 项有限功能及各自界面/控制器/宿主消费者；500 项操作、118 项支撑和 1569 条规格的实现与验收对应 |
| W09 剥离升级与最终验收 | W08, T01, T02, T03, T04, T05, T06, T07, T08, T09, T10, T11, T12, T13, T14, T15, T16, T17, T18, T19, T20, T21, T22, T23, T24, T25, T26, T27, T28, T29, T30, T31, T32, T33, T34, T35, T36, T37, T38, T39, T40, T41, T42, T43, T44, T45, T46, T47, T48, T49, T50, T51 | W08 和全部 51 个业务任务 | 全范围验收、ChatGPT 专用分支剥离及第三方审计；干净构建安装、新基线差分、依赖升级与数据迁移备份回退 |

W02 先交付 workspace、依赖引入和构建配方；W03 再准备运行时能力及类型。BUILD-001 等运行时相关输入的最终成功留给 BG-01 至 BG-04，不把‘所有构建输入已成功’设成 W03 的源码前置，也不因此修改既有依赖图。源码准备出口要求调用与失败语义可实现；真实集成出口要求真实接收方、效果及平台行为通过。

## 业务任务及完整范围

| 任务 | 有限功能数 | 拟主模块 |
| --- | --- | --- |
| T01 General | 28 | `apps/desktop/src/renderer/features/settings/general` |
| T02 Agent | 6 | `apps/desktop/src/renderer/features/settings/agent` |
| T03 任务生命周期、输入框配置与侧聊状态 | 13 | `apps/desktop/src/renderer/features/tasks` |
| T04 电脑使用 | 8 | `apps/desktop/src/renderer/features/computer-use` |
| T05 项目与远程入口 | 3 | `apps/desktop/src/renderer/features/projects` |
| T06 Git设置、本地动作与PR命令 | 16 | `apps/desktop/src/renderer/features/git` |
| T07 工作树 | 9 | `apps/desktop/src/renderer/features/worktrees` |
| T08 快捷键 | 5 | `apps/desktop/src/renderer/features/shortcuts` |
| T09 文件查看器 | 2 | `apps/desktop/src/renderer/features/file-viewers` |
| T10 外观 | 19 | `apps/desktop/src/renderer/features/appearance` |
| T11 Appshot | 4 | `apps/desktop/src/renderer/features/appshots` |
| T12 桌面通知 | 6 | `apps/desktop/src/renderer/features/notifications/desktop` |
| T13 账户通知 | 1 | `apps/desktop/src/renderer/features/notifications/account` |
| T14 本地环境配置与当前线程动作 | 5 | `apps/desktop/src/renderer/features/local-environments` |
| T15 Hooks | 7 | `apps/desktop/src/renderer/features/hooks` |
| T16 MCP | 6 | `apps/desktop/src/renderer/features/mcp` |
| T17 Plugins | 16 | `apps/desktop/src/renderer/features/extensions` |
| T18 Skills | 9 | `apps/desktop/src/renderer/features/skills` |
| T19 Connections | 19 | `apps/desktop/src/renderer/features/connections` |
| T20 Usage | 10 | `apps/desktop/src/renderer/features/usage` |
| T21 Billing | 11 | `apps/desktop/src/renderer/features/billing` |
| T22 Teams | 13 | `apps/desktop/src/renderer/features/teams` |
| T23 Age | 2 | `apps/desktop/src/renderer/features/account/age` |
| T24 Passwords | 5 | `apps/desktop/src/renderer/features/credentials` |
| T25 Cloud computer | 6 | `apps/desktop/src/renderer/features/cloud-computer` |
| T26 Browser use | 10 | `apps/desktop/src/renderer/features/browser/settings` |
| T27 Chronicle | 6 | `apps/desktop/src/renderer/features/chronicle` |
| T28 Voice | 10 | `apps/desktop/src/renderer/features/voice/settings` |
| T29 Code review | 15 | `apps/desktop/src/renderer/features/review/settings` |
| T30 Codex Cloud | 8 | `apps/desktop/src/renderer/features/cloud-environments/settings` |
| T31 Debug | 2 | `apps/desktop/src/renderer/features/diagnostics/settings` |
| T32 Pets | 7 | `apps/desktop/src/renderer/features/pets/settings` |
| T33 Import | 5 | `apps/desktop/src/renderer/features/imports/settings` |
| T34 Ads controls | 5 | `apps/desktop/src/renderer/features/ads/settings` |
| T35 归档记录与账户会话删除 | 5 | `apps/desktop/src/renderer/features/archives/settings` |
| T36 Data controls | 8 | `apps/desktop/src/renderer/features/privacy/settings` |
| T37 Agreements | 2 | `apps/desktop/src/renderer/features/agreements/settings` |
| T38 Account | 5 | `apps/desktop/src/renderer/features/account/settings` |
| T39 Extension | 5 | `apps/desktop/src/renderer/features/browser-extension/settings` |
| T40 Storage | 3 | `apps/desktop/src/renderer/features/storage/settings` |
| T41 Security | 19 | `apps/desktop/src/renderer/features/account-security/settings` |
| T42 Parental controls | 4 | `apps/desktop/src/renderer/features/family/settings` |
| T43 Trusted contact | 5 | `apps/desktop/src/renderer/features/trusted-contact/settings` |
| T44 Safety | 3 | `apps/desktop/src/renderer/features/time-management/settings` |
| T45 Cloud settings | 2 | `apps/desktop/src/renderer/features/cloud-preferences/settings` |
| T46 Cloud environments | 7 | `apps/desktop/src/renderer/features/cloud-environments/legacy-settings` |
| T47 Personalization | 15 | `apps/desktop/src/renderer/features/personalization/settings` |
| T48 Codex Micro | 11 | `apps/desktop/src/renderer/features/codex-micro/settings` |
| T49 应用菜单、历史撤销与桌面面板动作 | 62 | `apps/desktop/src/main/menus/application-menu.ts` |
| T50 计划任务页面、草稿、历史与运行协调 | 9 | `apps/desktop/src/renderer/automations/automation-page.tsx` |
| T51 页面编辑器命令与列表格式 | 1 | `apps/desktop/src/renderer/features/pages/list-format-commands.tsx` |

机器计划逐项保存 463 个 featureId、500 个操作 ID、118 个支撑 ID、1569 个 scenarioId 与任务的联系。设置、自动化、文件/变更/Git、终端/PTY、远程/云端、浏览器、系统及页面编辑器等已发现能力均保留；共享消费者不重复计数，Pages 等名称本身也不是 ChatGPT 专用的证据。

## 运行时与原生能力

[运行时矩阵](runtime-adoption-matrix-v1.json)采用第一方能力合同与独立 provider 的边界，完整合格路线仍为 0。固定 stock Electron 42.3.0 直接替换整个 Owl 的路线已被保存的接口和特权页对照否定；公共原语须按各组能力单独验收。独立发行或自有 provider 需要来源/版本/完整性、构建输入、ABI、目标平台和升级资格。

| 能力组 | 适配路径 | 关键未取得条件 |
| --- | --- | --- |
| RAM-01 原生菜单 tracking | `packages/runtime-adapter/src/native-menu-tracking` | 菜单开启、关闭和销毁的原生时序及 tracking 副作用；取得对应实现源码或运行时扩展。 |
| RAM-02 音频 measurement | `packages/runtime-adapter/src/measurement` | 真实 histogram 生产、delta/reset/configured-set、多 reader/平台语义及独立 bridge 来源。 |
| RAM-03 运行时特性与 Windows policy | `packages/runtime-adapter/src/runtime-feature-policy` | 两键的原生效果、默认值与可逆性；supported-feature registry；Windows policy fallback 的实际清理效果。 |
| RAM-04 Chrome 调试页策略 | `packages/runtime-adapter/src/chrome-page-policy` | 真实特权页/策略作用范围、profile/guest 边界及可构建 provider。 |
| RAM-05 Task Manager | `packages/runtime-adapter/src/diagnostics/task-manager` | 选定 Task Manager JS 委托已定位；原生 payload、动作、刷新与关闭仍待验证。 |
| RAM-06 窗口平台能力 | `packages/runtime-adapter/src/window-capabilities` | 原生能力、setInputShape/hit-testing、坐标/DPI 及真实 RPC/平台效果。 |
| RAM-07 历史滑动导航 | `packages/runtime-adapter/src/history-swipe` | 原生手势、overlay 与导航状态同步的独立 provider 及目标 SDK/headers。 |
| RAM-08 通知授权状态 | `packages/runtime-adapter/src/notifications/authorization` | 选定状态查询、设置打开及生命周期已定位；真实授权状态、系统设置与原生失败语义待验证。 |
| RAM-09 屏幕光标能力 | `packages/runtime-adapter/src/cursor-capabilities` | 平台能力条件与独立探测 provider；当前 getter 读数不构成跨平台证明。 |
| RAM-10 浏览器权限 prompt | `packages/runtime-adapter/src/browser-permissions` | 选定 JS 请求/响应及释放已定位；原生提示注入、实际权限裁决及 profile 隔离待验证。 |
| RAM-11 系统字体枚举 | `packages/runtime-adapter/src/fonts` | 选定字体数据形状、加载和消费者已定位；真实字体枚举、平台差异及底层来源待验证。 |
| RAM-12 浏览器 ownership、adoption 和 clone | `packages/runtime-adapter/src/browser-ownership` | 可独立构建的 clone/adoption 实现；原 live clone 的实际历史/页面状态语义；同一 view 移动不能证明复制能力。 |
| RAM-13 受限 Node 网络与 scoped IPC | `packages/runtime-adapter/src/process-policy` | 能拒绝通用网络和越界 IPC、允许声明端点的执行机制、平台策略与可构建实现；不是 permission.has 的返回值。 |
| RAM-14 普通更新与 managed relaunch | `packages/runtime-adapter/src/updates` | 选定更新策略及启动/写入消费者已定位；独立更新来源、签名、安装/重启与回退待验证。 |
| RAM-15 四类特权浏览器设置 | `packages/runtime-adapter/src/browser-settings` | 四类页面的底层数据/服务行为、独立 provider 与构建来源；固定 stock guest 已拒绝八个目标 URL。 |

RAM-02/04/06 的音频、调试策略和 input-shape JS 边界已交付；后续 Task Manager、授权设置、字体、浏览器权限提示及更新策略的选定 JS 合同也已交付。只因原生效果尚未验证，不重开相同入口追踪。node-pty 修改、objc-js 与 Sparkle 分别保留补丁/源码/二进制来源和目标 ABI 验收；本地 Node 构建或导出加载不能替代目标运行时行为。

| 构建关口 | 涉及输入 | 验收决定 |
| --- | --- | --- |
| BG-01 | BUILD-001, BUILD-003, BUILD-013, BUILD-015 | types 必须从选定 provider 的合同产生；声明一个不存在的方法不构成兼容。 |
| BG-02 | BUILD-005, BUILD-006, BUILD-011, BUILD-021 | runtime-driver 只指向独立依赖/源码构建产物；记录 commit、平台、校验和与 SDK/headers。现未取得完整 Owl 输入。 |
| BG-03 | BUILD-026 | 按目标 runtime headers、NODE_MODULE_VERSION/Node-API 要求、架构与 SDK 重建 native packages。Node 版本、Node-API 10 或本地 Node22 objc load 均不证明 Owl/候选 Electron ABI。 |
| BG-04 | BUILD-012, BUILD-017, BUILD-022, BUILD-025, BUILD-027, BUILD-028, BUILD-029, BUILD-030 | 锁定独立 artifact/构建配方、preload/resources/helpers、应用标识/数据根和签名更新配置；新版本重建并验证能力差异，不读取原安装路径。 |

## 后台协议与持久化

[协议采用](protocol-delta-adoption-v1.json)保留 466 个变体比较中的 455 相同与 11 不同：10 个通知变体的可选 nullable model/reasoningEffort 需要容忍和传递，另一个预测 fork 需要匹配语义的后台。预测 fork 不静默降为普通 fork 或新会话；实际 decoder、receiver、通知后效和发行到源码绑定继续验证。

[11 个存储域](storage-domain-map-v1.json)与[后续存储关联](storage-feature-ownership-v1.json)分别保留权威、路径、写入、revision、flush、退出及迁移恢复责任。desktop home、execution home、runtime profile、浏览器 partition、native credential 与远端账户状态分别注入。后续插件和认证权威合同已经提供选定源码边界；完整 store 分母、实际有效根、逐功能权威和全域隔离仍待闭合。

## 第三方依赖与构建输入

[202 条依赖记录](dependency-investigation-actions-v1.json)逐条有调查动作，包含 78 项根声明；有动作不等于精确版本或修改状态均已确定。原发布版本证据与新工程选定版本及精确锁分开保存。React/UI、schema/query、遥测、native/Wasm 和运行时通过依赖引入，第一方封装和策略恢复为维护源码，第三方 bundle 实现不生成进第一方目录。

[30 条构建输入处置](build-input-dispositions-v1.json)涉及 21 个唯一原路径，均有替代方式、依赖任务和验收要求，替代实现仍为 0。TypeScript/Vite/Forge 是构建职责候选；完整工具链锁、资源、运行时及原生输入、签名和更新配置仍须由独立工程实际验证。

## 模式剥离与升级

当前模式为 462 项 unknown、1 项 shared，整功能确认排除为 0。已有[3 组 ChatGPT 专用分支决定](chat-branch-decisions.json)供后续剥离；共享 composer/controller、Codex 提交、账户访问和宿主能力保留。产品模式、认证家族、执行位置、会话类别及后台资格分别建模，不按名称删功能。

每次升级建立新基线，记录来源、版本、hash 和工具参数；对功能入口/条件、协议通知、状态 schema、依赖修改、运行时能力、资源及平台行为做差分。差异回到拟维护模块、影响场景及迁移/备份/回退配方，历史证据不覆盖。

## 实施验收与当前分析出口

M1 至 M7 完整沿用历史验收条件，当前均未实施。源码合同、隔离回放、mock 或占位不能作为真实功能通过。

| 里程碑 | 上游 | 退出条件 |
| --- | --- | --- |
| M1 独立工程与运行时 | 无 | 干净构建、安装、启动均不读取原应用路径；所有存储位置和认证来源明确 |
| M2 传输与后台适配 | M1 | 请求/响应/通知/超时/异常/断连/销毁/能力释放逐项通过；公开后台差异逐项适配且不静默删除字段 |
| M3 状态与基础界面 | M2 | 初始化、并发写、错误和重开符合基线；迁移失败可恢复备份 |
| M4 任务生命周期 | M2, M3 | 后台接受、终态与界面分别证明；取消和重启恢复不靠本地改状态或重发冒充 |
| M5 其余 Codex 能力 | M2, M3, M4 | 核对真实 worker/Git/PTY/remote/权限；全部实际发现功能均在完整表中 |
| M6 剥离与升级 | M3, M4, M5 | 无误删共享能力且维护源码无第三方实现副本；新基线差分定位模块和回归场景 |
| M7 完整验收 | M1, M2, M3, M4, M5, M6 | 每个保留功能有实际结果；mock/占位/未决服务/未通过项不算完成 |

分析出口按[原九标准与 39 项要求的当前复核](analysis-stage-decisions-v5.md)及[资格说明](analysis-stage-decisions-v5-qualification.json)判断，本次不提升完成状态。1569 条产品规格属于后续产品验收；主要行为对照和会改变工程结构的未知仍是分析义务。78 条命令关联和 772 条来源关联缺口保留，后者不等于 772 个已证明缺失的功能。

已有只读样例完成且可重开；取消样例提前完成，因此执行中取消未测；停止后重启为 interrupted，自动续跑未证明。审批、失败和 PTY 等主要路径仍缺行为对照。最初 1 次及后续 2 次模型授权均已用完，新增模型测试须另有授权；冻结源码与设计工作可继续。

当前计划整合到此交付；后续来源分析限定为现有 78 条命令关联的一次固定范围处置，区分已有功能入口、支撑、有限新目标和确切缺失消费者。已交付 JS 合同只在出现矛盾来源、新保留消费者或具体未解调用目标时重访；外部 provider 缺失进入具名集成关口，不能成为无界递归调查的理由。
