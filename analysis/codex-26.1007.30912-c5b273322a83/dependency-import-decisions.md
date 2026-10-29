# 依赖引入决策表

固定基线 `codex-26.1007.30912-c5b273322a83`。下列版本是官方来源候选；实际 baseline 安装锁和完整等价性均未知。当前只形成实施提案，未安装包或生成锁。

| 入口 | 决策 | 实施边界 |
| --- | --- | --- |
| `react@19.2.7` → `react` | core 候选 | 114 export occurrence、92 参数、38 有限转发、4 root 方法形状不证明完整 factory 等价。 |
| `react-dom@19.2.7` → `react-dom` | DOM 候选 | 与 client 分开消费；不因同包名互换入口。 |
| `react-dom@19.2.7` → `react-dom/client` | `createRoot` 候选 | 保留应用 annotation wrapper；缺少选定 emitted exports 不作模式排除。 |
| `@sentry/core@10.29.0` → root | `getMainCarrier`、`getGlobalSingleton` 候选 | 平台 SDK 与完整应用初始化适配器尚未识别。 |
| `getSentryCarrier` / `@sentry/core/carrier[.js]` | 不生成导入 | root 不公开，package exports 无 carrier 子路径；先确定公共上层接口及应用调用契约。 |
| JSX/compiler/Scheduler、Sentry 平台 SDK | 暂缓定包/绑定 | 已知 Scheduler 范围 `^0.27.0`，实际锁未知；公开 JSX/compiler 入口不等于已绑定应用消费者。 |

Sentry 六组有限操作投影中的版本键编码差异不足以判定修改，27 个差异只是 JSON 叶编码。外层绑定、常量折叠、懒初始化与后续写入未闭合，修改状态和完整等价性保持 unknown；两份 map 内容相符也不补足缺失 npm gitHead 的整包构建来源。

React wrapper 的保存接口包含 `mountBrowserCommentRuntime`、`setSiteAnnotationPreview`、`dispose`、`root.render/unmount`；这些是继承的静态接口/应用适配器候选，运行效果未确认。Sentry 保留应用 SDK 选择、初始化/配置和 global/时序职责；既有 truthy version 与 singleton 语义列作未来验证要求，未声称已经识别完整 wrapper。

关闭条件分开记录：重建项目需固定精确版本、完整依赖锁与 JSX/compiler/Scheduler 消费绑定；原 baseline 安装锁需独立原始安装来源证据。完整等价需完整转换/差异及绑定和依赖闭包；兼容性需应用接口与自有合成生命周期/初始化验证，模式需明确 capability 消费证据。上述验证本批未执行。

依据：[React safe 摘要](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/react-upstream-identity-contracts-summary.md)、[React safe main](/Users/nallylin/Documents/code/ccodex/analysis/codex-26.1007.30912-c5b273322a83/react-upstream-identity-contracts.json)、[Sentry 冻结摘要](/Users/nallylin/Documents/code/ccodex/.analysis-local/sentry-upstream-identity-work/summary.md)、[Sentry safe main](/Users/nallylin/Documents/code/ccodex/.analysis-local/sentry-upstream-identity-work/sentry-upstream-identity-contracts.json)。详细选定字段及输入 pins 见同目录 `decisions.json`。不复制目标或第三方实现，不读取原 HTTP headers，不修改既有冻结成果或公共文档。

[objc-js来源与替换边界](objc-modification-contracts-summary.md)核对所选9文件与官方1.5.0一致，binary差异与ABI来源继续单列。当前没有修改这两个native源文件或维护source fork的依据；应固定官方来源，分别验证独立构建与窗口事件／通知／Apple Event adapter。原peer仅审静态单位，不能据同版本或导出名直接认定可替换。

[objc-js独立构建结果](objc-independent-build-summary.md)将原配方的ffi.h失败与SDK ffi候选的实际成功分别登记。27个native源文件未改；配方变化仅涉及ffi include/link。可维护候选是固定官方包加独立构建配方，而非生成库实现副本。Node header缓存来源、系统libffi可复现来源、实际未带-fobjc-arc的命令、Owl Node24和ARM均须继续验证；未证明可直接替换随包binary。

[source-context来源](settings-source-context-origin-summary.md)确认所选构造器namespace为node:async_hooks，属于Node运行时内置依赖。候选方案仅恢复第一方转发与生命周期adapter，由固定运行时提供AsyncLocalStorage；不生成原生实现或额外npm依赖。Node24.19官方文档只作公开API候选，actual target/runtime/current namespace/instance尚未证明。本机Node22隔离实验另批记录，采用前需核对完整client/source与运行时兼容。


[source-context候选观察](source-context-behavior-observations-summary.md)在本机Node22 builtin AsyncLocalStorage上实际执行8个局部场景。它支持该候选adapter的局部语义，不把内置API变成需恢复的第三方源码，也不证明Owl目标runtime兼容。选定builtin、第一方wrapper及真实运行时的取得／ABI仍分别登记。


[main persisted-atom接收候选](mode-persistence-receiver-summary.md)是第一方控制与适配职责；injected globalState、sender及owner/filter不等同于某个可直接安装的npm包。四选定范围没有恢复第三方实现；耐久后端及其版本来源继续调查。


[持久化记录与键策略](main-persistence-policy-summary.md)只提取第一方控制契约；n.* schema API和U.default比较器仍是独立依赖边界，本批没有确认其版本／实现或生成库代码。不要因safeParse或default调用外形就把普通包替换视为等价，也不要将cache键名称当作ChatGPT专属判据。


[globalState文件后端](global-state-storage-origin-summary.md)的Map／调度／JSON编排属于第一方，选定源码直接require node:fs、node:fs/promises、node:path、node:crypto及node:timers/promises；将它们声明为运行时依赖，不恢复第三方实现。本批重新取得的4个Babel包仅用于分析，沿用旧工具lock的固定版本，不计为客户端依赖。schema/default/archives比较器和Owl运行时的实际接口语义仍需核对。


[退出清理边界](shutdown-persistence-summary.md)把Electron生命周期／dialog、运行时Promise／timers、objc-js与平台插件、存储和backend接口留作外部依赖；所选退出协调与清理编排属于第一方。17个合成场景没有加载native或依赖实现，不增加第三方源码恢复，也不证明目标Electron/Owl ABI或平台行为。
