# 音频 Worklet 入口与构建边界 v1

本批关闭三个音频资源的 URL、注册名、消息与输出选择，并更正旧入口筛选的两处遗漏。它补充[工程方案 v12](implementation-plan-v12.md)，交付的是分析合同，尚未生成客户端代码或验证实际音频。

## 对原清单的更正

旧筛选器使用 `Worker`、`worker_threads`、`child_process`、`utilityProcess` 和 worker 文件名，未覆盖 `Worklet`。同一批14,816个冻结 JS/MJS/CJS 已全部回读大小/hash；新增字面量筛查得到3个消费者程序，均做完整 AST 核对。原清单两处 audioWorklet 加载之外，补入 `mark-session-create` 和 `voice-dsp` 各一处。原44处保留为历史，累计已知为46处，其中 audioWorklet 加载4处；这仍不是全局动态调用闭包。

最终提取9个不同完整程序、3,369,112个语法节点、54个选定源码单元；9条显式ESM别名联接，3条URL到实际资源联接。离线验证核对278次保存片段出现，并重新解析3个小型processor文件与选定语句。一次导出片段因不带原声明而失败，已保留工具草稿，修正片段解析选项后通过；9个原始完整程序没有解析失败。

## 构建采用决定

| 维护职责候选 | processor 注册名 | 必须保留的接口 |
| --- | --- | --- |
| `renderer/audio/worklets/dictation-audio.ts` | `dictation-audio` | 2048样本块、首块提前flush、Float32Array转移、boundary前flush/回显、stop/stopped与停止处理 |
| `renderer/audio/worklets/realtime-buffered-audio.ts` | `codex-realtime-buffered-audio` | release/mute请求，phase-changed/mute-applied/capture-started响应；缓冲/回放/live及静音清空 |
| `renderer/audio/worklets/vad-audio-frame.ts` | `voice-vad-frame-processor` | 默认10ms分帧、sampleRate与Float32样本packet、转移buffer和尾部不足一帧保留；detectorFactory另属边界 |

输出建议为 `apps/desktop/dist/renderer/assets/*-[hash].js` 三个独立模块，由新构建图生成URL，URL与注册名须一起接到消费者。不要沿用旧hash文件名，也不能只将处理器并入renderer初始化脚本。一个资源可以有多个配置：实时麦克风采用默认30秒缓冲，`mark-session-create` 使用同一处理器并设置20秒、`replayRate:2`；不能复制为两个不同实现，也不能丢掉调用方配置。是否缓冲还受 `bufferInputWhileConnecting` 控制。

维护路径是第一方职责提议，未由文件名证明完整归属；目前没有确认这些资源各自对应独立第三方包。第一方适配与协议需恢复成源码，已确认第三方通过新锁引入；bundler生成的初始化helper由选定构建工具产生。分析片段不进入最终维护源码作为vendor副本，202条依赖分母不变。

## 初始化、失败与释放

听写先初始化URL，再按需准备/缓存AudioContext与processor。`sinkId:none` 构造失败有默认构造回退。静态链路区分音频首块、boundary、stop-and-flush确认、转写finish和cancel/close；flush超时及启动取消有明确路径。disposeAudioCapture关闭当前捕获后还调用prepareAudio预热下一份缓存，不能将close理解为所有AudioContext均已释放。全局听写通过显式导入使用同一类，与MediaRecorder及其取消/错误清理相邻；这不能证明转写服务成功。

实时麦克风等待worklet、设备偏好、输入流和原生静音条件，再建立单声道MediaStreamDestination。静音应先禁用输出，再按当前requestId确认恢复条件；设备刷新串行，stop处理输入/输出tracks和context。WebRTC连接后的release和stop不同，holdInputUntilReady有单独条件。session track消费者另有abort、processorerror、port关闭和连接监听清理。

VAD worklet只分帧；声学判定仍由注入detector执行。controller保留track存活、generation和sample sequence检查、零gain输出连接以及stop/reset/destroy。不能用worklet成功加载推定检测器、真实麦克风、媒体权限、转写或WebRTC后效均可用。

## 原九项完成标准的本轮影响

以下逐项核对原计划定位并继承v6审查资格，结合当前v12/范围/模式及本批来源说明影响，**不是对所有历史证据重新做全量验收**。原九项要求、两张任务图和七项实施验收不变。

| 标准 | 当前资格 | 本轮影响与边界 |
| --- | --- | --- |
| AC-01 | 继承已有记录/方案依据 | 继承冻结基线记录；本批9个源码程序及14,816个筛查输入的字节/hash均核对。不是重审全部历史基线。 |
| AC-02 | 仍有实质分析缺口 | 仍partial。补入2个真实加载位置，旧44变为累计已知46；仅覆盖字面量worklet候选，不宣称动态闭包或完整功能分母。 |
| AC-03 | 仍有实质分析缺口 | 仍partial。504 unknown/5 shared，整功能排除0；本批不由音频/头像/会话名称或enum推定模式。 |
| AC-04 | 仍有实质分析缺口 | 仍partial。补足3个音频资源与4个消费者的初始化/消息/释放接口；不代表509功能关键边界全闭合。 |
| AC-05 | 继承已有记录/方案依据 | 继承202条依赖与调查动作记录；本批不添加包版本/来源/许可确认，不生成第三方维护代码。 |
| AC-06 | 继承已有记录/方案依据 | 继承原生/Wasm/helper/运行时/服务独立记录与15组能力条件；合格完整运行时路线仍0。 |
| AC-07 | 继承已有记录/方案依据 | 继承已有记录义务；本批更正候选选择遗漏并保留筛查/AST/动态限制。 |
| AC-08 | 仍有实质分析缺口 | 仍partial。仅复用历史正常完成/重开/中断样例与差异记录；没有新增音频或取消/失败观察。1844场景不要求在分析阶段全部执行。 |
| AC-09 | 继承已有记录/方案依据 | 继承v12工程方案及两张任务图；3个资源输出/接口选择作为补充，不提升为源码实现或干净构建已完成。 |

实现1844条场景全部执行、原生ABI/平台集成和干净打包属于相应后续验收，不能把它们统一设置为所有静态分析的前置关口。主要行为对照、真正改变架构的未知项仍未完成，不能据此宣布分析结束。

## 停止条件与下一步

三个资源的具名URL/processor/消息/输出选择在本批关闭。只在新消费者、矛盾源码或影响输出/协议的新输入出现时重开；已命名provider/ABI缺口直接引用既有合同。没有新增目标代码执行、客户端启动、麦克风/模型/服务请求、构建或产品通过。

以FSC-0466实时语音为有限集合，核对avatar overlay实际start调用所在控制器及productExperience条件，区分Codex正向用途、共享、专属分支或明确unknown；复用本批音频合同，不再追查既明URL或同一原生provider。

509项功能、582个不同操作、125个支撑、1844条未执行规格、115项职责、202条依赖、504 unknown/5 shared均保持，整功能排除0。完整分析仍未完成。

[机器合同](audio-worklet-build-boundaries-v1.json) · [26条源码证据](audio-worklet-build-boundaries-v1-evidence.jsonl) · [输入与工具](raw/audio-worklet-build-boundaries-v1/input-manifest.json) · [离线核对](raw/audio-worklet-build-boundaries-v1/verification.json)
