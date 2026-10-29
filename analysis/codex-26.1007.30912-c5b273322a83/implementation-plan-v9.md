# Codex 独立客户端恢复实施计划草案 版本 9

目标是完整恢复固定基线的 Codex 行为，剥离有证据证明仅供 ChatGPT 使用的分支，并通过独立依赖引入第三方组件。项目须能维护、升级及从干净环境构建打包，运行时无需读取原客户端安装目录。本阶段交付分析与实施依据；客户端实现尚未开始。

本版采用[功能台账 v23](feature-scope-v23.json)、[场景台账](feature-scope-v21-scenarios.json)和[恢复覆盖表 v14](restoration-coverage-v14.json)：340项有限定义、344项用户操作、103项支撑、1117条未执行产品规格，分别归属45个恢复任务。完整产品分母仍未知。本版统一v8计划之后已发布的范围；未开始客户端实现，也未增加分析或行为通过项。

## 源码恢复与集成前置条件

源码准备和真实集成分别排程。合同、纯状态转换、请求编码、界面控制器及构建配置设计可依据已有契约进行；运行时选择影响原生驱动、宿主接入、真实持久化、安装和打包。源码准备完成后，所属里程碑仍须通过真实集成验收。

| 工作 | 源码准备的前置条件 | 真实集成的前置条件 |
| --- | --- | --- |
| W01 合同与来源映射 | 固定来源和既有请求、事件及生命周期契约 | 对应真实provider、错误与释放行为 |
| W02 独立构建输入 | 已登记依赖、30项构建输入及来源政策 | 完整精确锁、运行时集成、干净构建和打包 |
| W03 运行时与平台 | W01、W02；逐能力接口及候选路线 | 独立来源、版本、ABI和全部所需能力实测 |
| W04 桌面传输与宿主 | W01；可先恢复编码和生命周期状态机 | W01、W03；真实IPC、身份、信任与端口释放 |
| W05 后台适配 | W01、W02；按已比较的schema与差异设计 | 实际后台版本、provider、服务及通知语义 |
| W06 状态与持久化 | W01；可先恢复schema、revision和保存状态机 | W01、W03；实际文件驱动、原子替换、退出与迁移 |
| W07 应用壳与模式 | W01、W04、W06的接口和状态合同 | W04、W06的真实集成和窗口生命周期 |
| T01至T45 功能恢复 | 对应有来源的界面、状态、后台和存储接口 | 下表所列原有依赖、具体账户条件和逐功能后效 |
| W09 最终剥离与验收 | W08及全部45个任务的设计结果 | 全部任务、完整范围处置、独立构建及实际产品结果 |

[机器可读里程碑](implementation-milestones-v9.json)保存两套依赖图。M1至M7的原有整体验收条件继续有效；源码准备不会把M1标为完成，也不会替代真实IPC、权限、服务或落盘结果。后续实施可以先恢复证据充分的源码，完整发布必须通过全部集成条件。

## 工程结构与共享边界

按进程、状态所有权及生命周期组织第一方源码；发布chunk仅作来源定位。每个转换记录原文件hash、字节范围、导入导出、副作用、第三方边界、目标模块与验收场景。建议目录为：

```text
apps/desktop/src/main/                 启动、窗口、宿主、系统与退出
apps/desktop/src/preload/              世界隔离、IPC、端口与浏览器注入
apps/desktop/src/renderer/app/         路由、初始化与窗口状态
apps/desktop/src/renderer/features/    功能界面、控制器和状态
apps/desktop/src/workers/              独立生命周期后台工作
apps/desktop/resources/               有来源记录的资源
packages/contracts/src/               DTO、事件、错误和能力合同
packages/desktop-transport/src/        传输、宿主选择、信任和释放
packages/backend-adapter/src/          app-server及其他服务适配
packages/runtime-adapter/src/          独立运行时和原生能力接口
packages/state-storage/src/            schema、revision、保存与迁移
tools/recovery/                        来源映射和可审查转换
tools/build/                           自有构建、生成和打包工具
tests/fixtures/                        合成目录与回归样例
```

[首页分流证据](product-flow-ownership.md)要求保留同一套共享composer和controller。Codex入口策略放入`home-surface-policy`，共享渲染放入`home-composer`，本地任务提交放入`local-submission`。产品模式、认证家族、执行位置、会话类别和后台资格分别建模；不能按`chatgpt`字符串删除本地任务或共享组件。已定位的chat专属渲染分支可先隔离，删除前仍检查全部消费者和依赖。

app-server、桌面HTTP、注入resolver、扩展连接和协调socket各自维护协议及接收方。renderer通过合同调用宿主；不会直接导入main或原生实现。设置保存与实际消费者效果分开验收。

## 运行时路线与发布条件

固定公开Electron 42.3.0的[实测对照](public-runtime-comparison.md)不支持直接替换Owl：任务管理器、更新策略、WebContents clone与lease、Node网络及IPC权限均有差异。公开API或同view移动只支持对应原语，不能据此宣称完整运行时兼容。

[浏览器设置对照](native-browser-settings-comparison.md)又确认：当前guest嵌入拒绝八个特权URL，而自建host和guest正例通过。联系人、密码管理、扩展和站点设置四类能力归W03的运行时及服务接口所有，T26消费这些接口。直接嵌入stock Electron内部URL的路线已被该实测否定；可独立取得的适用运行时、以及具有等价数据服务的第一方设置界面仍是待验证候选。

运行时资格须同时覆盖功能、来源、版本、ABI、构建、升级和第三方边界。空页面、改URL、复制原安装中的Owl或删启动guard均不能满足资格。live-history clone的必要可观察行为须从调用合同与实际证据界定；公开探针未保留JS堆值这一事实，不能单独证明原clone承诺保留JS堆。

运行时未取得资格时，相关集成与发布保持未通过；其他已有契约的源码准备保留独立排程。未选择最终运行时，不宣称完整独立构建已经可行。

## 功能恢复任务

下表列出全部当前所有者。具体操作、支撑、来源、条件、场景及十项共享消费者关系保留在[恢复覆盖表](restoration-coverage-v14.json)；同一功能不会因多个入口而重复恢复。

| 任务 | 定义数 | 第一方主模块 | 真实集成依赖 |
| --- | --- | --- | --- |
| T01 General | 28 | `apps/desktop/src/renderer/features/settings/general` | W04, W06, W07 |
| T02 Agent | 6 | `apps/desktop/src/renderer/features/settings/agent` | W05, W06, W07 |
| T03 任务生命周期 | 5 | `apps/desktop/src/renderer/features/tasks` | W04, W05, W06, W07 |
| T04 电脑使用 | 8 | `apps/desktop/src/renderer/features/computer-use` | W04, W05, W06, W07 |
| T05 项目与远程入口 | 1 | `apps/desktop/src/renderer/features/projects` | W04, W05, W06, W07 |
| T06 Git | 10 | `apps/desktop/src/renderer/features/git` | W05, W06, W07 |
| T07 工作树 | 8 | `apps/desktop/src/renderer/features/worktrees` | W04, W05, W06, W07 |
| T08 快捷键 | 5 | `apps/desktop/src/renderer/features/shortcuts` | W03, W06, W07 |
| T09 文件查看器 | 2 | `apps/desktop/src/renderer/features/file-viewers` | W04, W06, W07 |
| T10 外观 | 19 | `apps/desktop/src/renderer/features/appearance` | W03, W06, W07 |
| T11 Appshot | 4 | `apps/desktop/src/renderer/features/appshots` | W03, W04, W06, W07 |
| T12 桌面通知 | 6 | `apps/desktop/src/renderer/features/notifications/desktop` | W03, W04, W06, W07 |
| T13 账户通知 | 1 | `apps/desktop/src/renderer/features/notifications/account` | W05, W06, W07 |
| T14 本地环境 | 4 | `apps/desktop/src/renderer/features/local-environments` | W04, W05, W06, W07 |
| T15 Hooks | 7 | `apps/desktop/src/renderer/features/hooks` | W05, W07 |
| T16 MCP | 6 | `apps/desktop/src/renderer/features/mcp` | W03, W05, W07 |
| T17 Plugins | 16 | `apps/desktop/src/renderer/features/extensions` | W03, W05, W07 |
| T18 Skills | 9 | `apps/desktop/src/renderer/features/skills` | W03, W05, W07 |
| T19 Connections | 19 | `apps/desktop/src/renderer/features/connections` | W03, W05, W07 |
| T20 Usage | 10 | `apps/desktop/src/renderer/features/usage` | W03, W05, W07 |
| T21 Billing | 11 | `apps/desktop/src/renderer/features/billing` | W03, W05, W07 |
| T22 Teams | 13 | `apps/desktop/src/renderer/features/teams` | W03, W05, W07 |
| T23 Age | 2 | `apps/desktop/src/renderer/features/account/age` | W03, W05, W07 |
| T24 Passwords | 5 | `apps/desktop/src/renderer/features/credentials` | W03, W05, W07 |
| T25 Cloud computer | 6 | `apps/desktop/src/renderer/features/cloud-computer` | W03, W05, W07 |
| T26 Browser use | 10 | `apps/desktop/src/renderer/features/browser/settings` | W03, W05, W07 |
| T27 Chronicle | 6 | `apps/desktop/src/renderer/features/chronicle` | W03, W05, W07 |
| T28 Voice | 10 | `apps/desktop/src/renderer/features/voice/settings` | W03, W05, W07 |
| T29 Code review | 15 | `apps/desktop/src/renderer/features/review/settings` | W03, W05, W07 |
| T30 Codex Cloud | 8 | `apps/desktop/src/renderer/features/cloud-environments/settings` | W03, W05, W07 |
| T31 Debug | 2 | `apps/desktop/src/renderer/features/diagnostics/settings` | W03, W05, W07 |
| T32 Pets | 7 | `apps/desktop/src/renderer/features/pets/settings` | W03, W05, W07 |
| T33 Import | 5 | `apps/desktop/src/renderer/features/imports/settings` | W03, W05, W07 |
| T34 Ads controls | 5 | `apps/desktop/src/renderer/features/ads/settings` | W03, W05, W07 |
| T35 Archived chats | 5 | `apps/desktop/src/renderer/features/archives/settings` | W03, W05, W07 |
| T36 Data controls | 8 | `apps/desktop/src/renderer/features/privacy/settings` | W03, W05, W07 |
| T37 Agreements | 2 | `apps/desktop/src/renderer/features/agreements/settings` | W03, W05, W07 |
| T38 Account | 5 | `apps/desktop/src/renderer/features/account/settings` | W03, W05, W07 |
| T39 Extension | 5 | `apps/desktop/src/renderer/features/browser-extension/settings` | W03, W05, W07 |
| T40 Storage | 3 | `apps/desktop/src/renderer/features/storage/settings` | W03, W05, W07 |
| T41 Security | 19 | `apps/desktop/src/renderer/features/account-security/settings` | W03, W05, W07 |
| T42 Parental controls | 4 | `apps/desktop/src/renderer/features/family/settings` | W03, W05, W07 |
| T43 Trusted contact | 5 | `apps/desktop/src/renderer/features/trusted-contact/settings` | W03, W05, W07 |
| T44 Safety | 3 | `apps/desktop/src/renderer/features/time-management/settings` | W03, W05, W07 |
| T45 Cloud settings | 2 | `apps/desktop/src/renderer/features/cloud-preferences/settings` | W03, W05, W07 |

General与Agent偏好须接上实际配置消费者；任务生命周期分别检查后台接受、流式事件、审批、取消、终态、导航和持久化。本地环境保存成功后激活失败仍保留独立结果；Hooks保留来源、管理层和信任；MCP、插件、技能与连接保留共享管理器和OAuth生命周期。导入检测、同步、历史和后置设置分别调用自己的服务。终端、文件与变更、浏览器所有权、云端和系统能力的既有合同继续属于完整恢复范围。

## 第三方依赖与构建输入

[依赖清单](dependencies.csv)的202项记录、78项根声明及其版本依据继续保留。原发布包仅6项根路径安装版本已确认；新工程生成自己的精确锁，并分别记录原版本证据、新选版本及兼容结果。未确认的内嵌实现不会作为第一方源码导出。React及UI、query/schema、遥测、capnweb、native和Wasm按明确接口引入；上游修改用受维护依赖、补丁或第一方适配分别处理。

[30项构建输入](build-input-dispositions-v1.json)已有处置但替代实现为0。TypeScript、Vite和Forge作为来源支持的构建职责候选，自行建立工作区、分进程构建和打包配置；具体版本与最终运行时集成在新工程锁中确定。原monorepo脚本不必逐字恢复，其类型生成、资源、诊断、原生构建和打包职责必须由独立工具承担。普通包锁、native ABI和私有运行时输入分别验收，不能互相代替。

## 未完成范围与分析出口

45个已发现设置容器中42个有局部操作合同；cloud-environments、personalization、codex-micro的源码选择已保存，尚待归并为操作与恢复规格。本版未把选择源码计为完成页面分析。保留12项关联待办、3项交叉重叠及全部其他所需能力，完整产品分母未知。

340项定义中shared 1、unknown 339，确认ChatGPT整项排除0。未知归属合法保留；拟删除分支仍须核对模式条件、消费者及共享依赖。不能以认证家族、文件名或设置页名称替代产品模式判定。[归档共享消费者证据](archive-mode-ownership.json)与[账户访问边界](desktop-access-publication.md)分别约束模式和访问条件。

968条旧入口原ID全部保留：235条资源／命令声明为已确认非用户操作来源，6条注册调用已确认callee，1条保留部分功能容器关联，726条角色待定；967条仍无功能映射。来源角色、功能映射和完整行为链是不同计数，不能互相充抵。详见[逐ID处置](legacy-entry-dispositions.md)。

先交付上述三个已选设置合同，再依[六组未决问题及关闭条件](analysis-stage-decisions-v3.json)核对会改变架构的未知：独立运行时和native来源、后台provider／receiver、数据与认证边界及主要行为差异。浏览器clone需求已经有[合同与候选路线](browser-clone-route-qualification.md)和[公共历史复制对照](public-history-duplicate-comparison.md)，复用这些结果，只调查仍缺的后效与实现来源。

新增选择必须指出影响哪个范围或架构决定，以及停止调查的证据条件。未知分类数量无需机械归零；独立客户端构建、打包和全部产品回归在实施阶段完成。会改变完整范围或架构的未知仍不得宣称关闭。

## 行为验收与升级

既有只读样例已完成并可重新打开；执行中停止再重启得到interrupted，尚无自动续跑证明；取消前任务提前完成，执行中取消仍待验证。原授权的1加2次模型样例全部用完。本版新增模型提交、原客户端运行和真实服务调用均为0。1117条产品规格仍为未执行；隔离源码测试只证明所选逻辑。

最终验收覆盖每个保留功能的正常、失败、取消、恢复和具体条件，核对真实状态、服务后效与持久化；mock或占位不计完成。干净构建、安装、打包、独立标识及存储路径不得读取原安装。升级建立新基线，比较功能、入口条件、协议、schema、依赖修改、资源和平台行为；每项差异映射到模块、回归场景及迁移回退。

原九项分析标准保持四项资料或范围义务已有交付、五项部分完成。本版只消除已发布功能台账与实施排程的脱节。AC-09中的范围排程子步骤已同步；目录与边界决定、运行时可行性、主要行为及其他原标准仍按当前证据逐项审计，未提升完成状态。
