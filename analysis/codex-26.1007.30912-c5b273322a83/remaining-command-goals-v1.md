# 剩余命令的功能去向分析

固定基线中的78条未关联命令已按34组完成来源处置：48条用户操作候选、7条共享支撑机制、3条既有功能入口候选，以及20条有明确边界的消费者缺口。命令编号、处理条件和不同宿主变体分别保留；这些数量不是新增功能数量。

当前功能台账仍为463项、1569条未执行产品规格，工程依据仍为[实施计划v11](implementation-plan-v11.md)。本批未新增客户端实现、目标程序执行、模型提交、服务调用或产品验证通过，也未提升原九项完成标准。

## 来源范围

字面检索覆盖冻结 app.asar 中15047个JS文件，包含隐藏的 .vite 目录。138个命中程序完成整段AST解析，得到628处精确键命中和919份源码范围；另对4个程序作作用域或导出分析，保存233份范围。142次解析均无解析错误。628处包含声明、文字、状态键及回调，不能按命中数统计功能。

字面未命中不证明功能不存在：计算命令ID、原生宿主、VS Code扩展和归档外组件仍可能提供消费者。全部源码副本只保存为分析证据，最终客户端不纳入第三方实现副本。

## 会改变恢复方式的处理条件

- 输入框的QS导入解析为iIc，再调用Pw；iIc覆写isActive以限制当前scope。py则直接解析为Pw，不能将两种注册包装视为相同。
- 最近会话的previous/next普通回调为空，动作由keyboardHandler驱动，并在修饰键释放时提交；blur清理暂态。普通命令派发不能模拟完整键盘流程。
- qDt中的focusMainChat注册固定禁用。其他surface中的同ID注册仍需保留各自条件。
- startVoiceMode在活动会话存在时请求停止；清空输入只调用setText，不据此删除附件。
- Appshot命令先发送宿主消息，事件处理器再执行前台目标查询和捕获。无目标、能力不可用和捕获异常分别处理。
- forceReloadSkills命令不返回刷新Promise；普通skills/list与hosted listSkills的参数契约不同。
- 宠物覆盖层的renderer入口发送open消息，系统快捷键委托toggle；设置页面导航、快捷键配置和实际功能执行分别记录。

## 逐组去向

| 分组 | 命令 | 去向 | 职责与边界 |
| --- | --- | --- | --- |
| RCG-G01 控制窗口入口 | `openControlWindow` | 命令描述的消费者缺口 | 命令 registry 到控制窗口宿主消费者 |
| RCG-G02 实时语音入口与活动会话控制 | `composer.startVoiceMode`, `realtimeVoice.toggleMicrophoneMute`, `realtimeVoice.toggleOutputMute`, `realtimeVoice.endCall` | 用户操作候选 | Pd.realtimeVoiceRuntime.requestRealtimeStart 与 Pd.realtimeVoice.controlActive |
| RCG-G03 发起会议笔记 | `meetings.takeNotes` | 用户操作候选 | app-initial 的 L2 导出及会议录制宿主 |
| RCG-G04 切换浏览器批注模式 | `browser.toggleAnnotationMode` | 用户操作候选 | browser-sidebar-command 与浏览器宿主 interaction mode |
| RCG-G05 发送产物批注 | `artifact.sendAnnotations` | 用户操作候选 | 注入的 onSend；use-command-hotkey 的 accelerator 订阅和键盘监听器 |
| RCG-G06 输入框提交与清空命令 | `composer.submitInBackground`, `composer.submit`, `composer.steer`, `composer.queue`, `composer.clear` | 用户操作候选 | 注入 submit/backgroundSubmit、听写控制和 composer controller |
| RCG-G07 向输入框添加附件 | `composer.addPhotos`, `composer.captureAppshot`, `composer.addFiles` | 用户操作候选 | 文件选择器、附件 handler、appshot-shortcut 消息及 ndc 原生捕获 |
| RCG-G08 共享审批命令适配 | `approval.approve`, `approval.decline` | 共享支撑机制 | 注入的审批回调及具体请求类型 |
| RCG-G09 从本地会话发起分支 | `forkThread` | 既有功能的入口候选 | ahe 分支协调器和导航 |
| RCG-G10 宠物覆盖层入口 | `openAvatarOverlay` | 用户操作候选 | avatar-overlay-open 与 toggleAvatarOverlay |
| RCG-G11 切换需要关注的会话筛选 | `togglePriorityFilter` | 用户操作候选 | 侧边栏活动筛选状态及 fei/gei/pei |
| RCG-G12 聚焦主会话或侧聊 | `focusMainChat`, `focusSideChat` | 用户操作候选 | IP/YTc/主侧 scope 与浮动 surface focus |
| RCG-G13 画布工具命令描述 | `artifacts.selectTool`, `artifacts.handTool`, `canvas.prompt`, `artifacts.rectangleTool`, `artifacts.circleTool`, `artifacts.arrowTool`, `artifacts.lineTool`, `artifacts.textTool`, `artifacts.noteTool` | 命令描述的消费者缺口 | 产物编辑器的计算 ID 注册或外部编辑器命令桥 |
| RCG-G14 复制当前 Page 链接 | `copyPageLink` | 用户操作候选 | fn 复制协作者与页面链接状态 |
| RCG-G15 聚焦 Page 块控件 | `focusPageBlockControls` | 用户操作候选 | 块控件 onFocusControls 与 editor selection |
| RCG-G16 打开 Orbit | `openOrbit` | 用户操作候选 | og 路由和 Orbit 页面 |
| RCG-G17 跳到下一条需要关注的会话 | `nextThreadNeedingAttention` | 用户操作候选 | 侧边栏会话状态、Ykr 排序和 DF 导航 |
| RCG-G18 在最近会话中切换 | `previousRecentThread`, `nextRecentThread` | 用户操作候选 | fLs/pLs/mLs 的选择状态和 lbc 导航 |
| RCG-G19 按序号打开最近会话 | `recentThread1`, `recentThread2`, `recentThread3`, `recentThread4`, `recentThread5`, `recentThread6` | 用户操作候选 | WQa 有序列表和 DF 导航 |
| RCG-G20 显式模式切换分支 | `switchToMode1`, `switchToMode2`, `switchToMode3` | 用户操作候选 | 模式协调器、路由及 composer onModeChange |
| RCG-G21 设置与技能页面导航适配 | `codexMicroSettings`, `mcpSettings`, `personalitySettings`, `keyboardShortcuts`, `openSkills` | 共享支撑机制 | navigate-to-route 接收器及五个页面容器 |
| RCG-G22 从命令入口检测外部 Agent 数据 | `importExternalAgent` | 既有功能的入口候选 | eva 检测服务与 z6s 导入选择控制器 |
| RCG-G23 从命令入口强制刷新技能 | `forceReloadSkills` | 既有功能的入口候选 | skills/list 或 Pd.hostedThreadFiles.listSkills 与查询缓存 |
| RCG-G24 切换线程审查标签 | `toggleReviewTab` | 用户操作候选 | Kr 标签切换与审查面板状态 |
| RCG-G25 切换侧面板全宽 | `toggleMaximizeSidePanel` | 用户操作候选 | CS、活动标签、yii 与布局包装器 |
| RCG-G26 文件位置与定义导航 | `file.goToDefinition`, `file.navigateBack`, `file.navigateForward`, `goToLine` | 用户操作候选 | 定义 provider、onOpenLocation、文件历史状态与行号 surface adapter |
| RCG-G27 VS Code 扩展宿主命令 | `implementTodo`, `openSidebar`, `newCodexPanel`, `addToThread`, `addFileToThread`, `showLspMcpCliArgs`, `dumpNuxState`, `resetNuxState` | 扩展宿主消费者缺口 | VS Code 扩展的命令注册和宿主上下文 |
| RCG-G28 切换 Spotlight 搜索窗口 | `spotlightSearch` | 用户操作候选 | XQe 与 createWindow(/spotlight) |
| RCG-G29 旧 Notch 描述与刷新分支 | `toggleNotch`, `notchVoice` | 旧命令消费者缺口 | 旧命令的迁移规则或实际派发消费者 |
| RCG-G30 区域截图的接收会话 | `screenshotToCurrentChat`, `screenshotToNewChat` | 用户操作候选 | 主窗口消息及区域截图 renderer/native 捕获器 |
| RCG-G31 切换快捷弹出窗口 | `hotkeyWindow` | 用户操作候选 | Pd.hotkeyWindowCommands 与 UQe/window controller |
| RCG-G32 按住与单次切换听写 | `globalDictationHold`, `globalDictationSingleTap` | 用户操作候选 | DQe 会话、窗口、原生热键与转写/粘贴协作者 |
| RCG-G33 全局实时语音快捷键 | `realtimeVoice` | 用户操作候选 | requestRealtimeToggle 与 subscribeRealtimeVoiceSessionReservation |
| RCG-G34 开始或停止性能跟踪 | `toggleTraceRecording` | 用户操作候选 | contentTracing、文件输出、对话框和可选 trace 上传 |

每条命令的行为、条件、来源范围、候选功能关系及还缺的输入见[结构化结论](remaining-command-goals-v1.json)；[逐项表格](remaining-command-goals-v1.csv)便于筛选，[证据记录](remaining-command-goals-v1-evidence.jsonl)保留固定源码位置。

## 纳入功能台账的下一步

对34组作一次有限的纳入决定：将证据支持的入口接入既有操作，必要时新增有限目标，为共享机制保留具体调用方，并把20条消费者缺口接到相应宿主边界。分支、技能刷新和外部导入的3条入口目前只是既有功能候选，尚未宣布操作等价。

不因原生或服务尚未验收而重开本批已交付的JS合同。只有出现矛盾源码、新消费者或具体未解调用目标才定向补查。模式归属、主要行为对照、私有运行时和独立构建仍按原分析计划继续验收。
