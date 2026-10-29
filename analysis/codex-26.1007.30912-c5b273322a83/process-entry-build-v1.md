# 进程、worker 与资源入口构建边界 v1

本批把已核对的发布入口接到维护路径、输出位置和独立资源要求。它补充[工程方案 v12](implementation-plan-v12.md)，没有生成客户端实现，也没有证明独立构建。完整进程行为、动态资源生产者和模式归属仍有具名缺口。

基线为 `codex-26.1007.30912-c5b273322a83`。原九项分析完成标准保持。冻结源码、已有文件/原生资源目录与既有 preload、运行时合同是本批依据，没有运行目标程序、启动客户端、提交模型任务或请求服务。

## 已确认的范围

| 范围 | 结果与限定 |
| --- | --- |
| JS/MJS/CJS 筛查 | `.vite/build` 与 `webview` 中 14,816 个发布文件；词法候选筛查不能证明全局动态调用闭包 |
| 完整 AST | 92 个不同候选程序、17,243,312 个语法节点，0 解析错误；另对 main/worker 做 2 次完整绑定核对，共 1,593,900 个节点 |
| 启动语法位置 | 44 处：30 个浏览器或未限定 Worker 构造、1 个 SharedWorker、2 个 audioWorklet 候选、3 个 Node Worker、8 个 child_process 包装调用 |
| HTML | `index.html`、`detached-window.html`、orbit `frame.html` 共 3 个，逐项联接脚本、样式、modulepreload/license 资源与 CSP |
| 原生/Wasm 资源 | 沿用已保存目录的 49 个 archive、112 个 disk、8 个外部 Wasm，共 169 次产物出现；逐行联接文件大小和 hash |

44 处是语法位置，169 条是产物出现记录，都不等于进程数量、可执行入口数量、功能数量或新增依赖数量。词法筛查未覆盖无相关词元的动态别名、任意包装和所有外部包内部路径。保存有 service-worker 文件，并不证明它被注册；未找到合格注册调用也不证明全局不存在。

## 对构建方案的具体影响

桌面应用的产品 worker 使用一个物理 `worker.js`，通过 `workerData.workerId` 分派 `git`、`open-in` 和 `computer-use`。建议保留一个 `apps/desktop/src/worker/entry.ts` → `apps/desktop/dist/worker.js`，把第一方管理、消息总线及各身份职责拆为维护模块。不能从三个身份推出三个重复入口，也不能从五个同绑定构造位置推出五个实际线程实例。

绑定核对还确认 `Ut` 初始化为 `[git]`；相应循环对 git 复用已有 bus 后 `continue`，后面的 `new H9(e)` 不由这个初始字面量走到。数组后续变更和完整运行可达性尚未证明，因此该语法位置仍保留，不能计作已观察实例。

| 维护设计 | 输出/契约 | 资格 |
| --- | --- | --- |
| `src/main/early-bootstrap.ts`、`bootstrap.ts`、`index.ts` | 分阶段主进程输出，保持权限准备与后续延迟装配 | 复用 v12；不因本批而增加启动通过数 |
| 三个 preload 入口 | `dist/preload.js`、`browser-page-preload.js`、`sandbox-preload.js` | 复用既有单入口 CJS 兼容 bundle 规则；electron 由运行时提供 |
| `src/main/workers/worker-manager.ts`、`worker-bus.ts` | 创建/缓存实例、MessagePort、请求与退出；正确定位相邻输出 `worker.js` | 新拟议维护路径；不追加到已有 115 项职责分母 |
| `src/worker/entry.ts` 及身份模块 | 一个产品 worker 输出，分别装配 Git、open-in、computer-use | 保留原生/后台依赖合同；不把底层 SDK 实现复制为第一方源码 |
| renderer 入口与资源 registry | 主窗口、detached、orbit iframe；模块 worker、SharedWorker、worklet、Blob 与嵌套 worker | 按已选 bundler 和新锁重新生成 URL/资源；动态参数逐行保留未决 |
| `tools/build/` 资源清单与 runtime/backend adapter | 独立取得 runtime、helpers、native addons、Wasm、Node/plugin、CLI/voice/shell 工具 | 路径/目录分组是设计推断，尚不证明具体消费者或可重建配方 |

manager 的静态合同包含可选 main RPC 与 Sentry 端口转交、配置/认证更新、当前实例检查、待处理请求中止与幂等退出清理。仅 `id === git && g.B()` 分支发出 `worker-flush-and-exit` 并设 11 秒兜底；其余分支直接终止。这里保留 `g.B()` 的原资格，不能由这段代码宣称 flush、持久化或原生操作实际完成。

bootstrap/worker 内另有两处 data URL 诊断 worker，属于待固定 SDK/包产物资格的边界；8 处 child_process 调用是包装层出现，真实可执行参数仍需消费者/生产者联接。它们不构成 10 个独立产品 helper。第三方实现从新锁的独立包引入；分析原始片段保存于证据，不生成维护源码副本。

## 浏览器与原生资源处置

直接资源名字包括文档、regex、预编译、页面显示、共享 worker、演示控制器、HEIC、远程画面、缩略图、语音变换和 workbook 等。名字只能帮助定位，不能决定是否为 ChatGPT 专用。每个启动位置均有冻结范围、hash、来源描述、维护/构建建议及未决条件，见[44 处启动位置](process-entry-build-v1-launch-sites.csv)。

机器合同单列“启动子树中的字面量资源提及”和相对目录联接。它们不是完整 URL 构造器绑定证明，也不覆盖通过变量、配置、Blob、`locateFile` 或嵌套 loader 得到的实际目标。不能将 PDF 等包的默认 worker 文件名直接改成目录内某个 hashed 文件，或把包的所有候选 worker 都生成第一方源码。

3 个 HTML 分别保留模块入口和 CSP；orbit `frame.html` 还引用独立 frame 模块、样式和第三方 notices。HTML 的标题或某个资源名字不构成模式排除依据。实际主窗口/detached/orbit 导航消费者及 service-worker 安装生命周期属于 PEB-G02。

[169 条资源处置](process-entry-build-v1-resources.csv)保留原 catalog 行及来源资格。按路径/kind 提议 66 个 native-addon、42 个 Wasm/WebCIL、21 个 runtime/platform、23 个 backend/CLI、11 个 Node/plugin、3 个 platform helper、3 个其他工具/库资源义务。组名不宣称真实运行角色；例如 `runtime-or-helper` 的原目录标签中包括动态库，CLI 目录也含非可执行产物。

所有资源尚未在本批选择独立发行物或证明源码重建。资源清单建议键用于避免同名冲突，实际包布局必须由消费者/loader 和打包配方决定，不应机械搬移原文件。继续复用 BG-01 合同、BG-02 独立来源、BG-03 headers/架构/ABI、BG-04 打包与升级四个关口及已有 15 组运行时能力，不从每个资源重新追查同一 provider。

## 本批停止条件与剩余工作

已交付限定范围的入口/资源清单、构建决定及可回读证据；本批不再为补齐底层 provider 反复展开同一调用链。剩余项分为五个具名边界：

1. PEB-G01：变量/Blob/包装可执行参数。只在会改变资源输出、包选择、可执行选择或生命周期接口时继续追查。
2. PEB-G02：主窗口、detached、orbit 的实际导航消费者与 service-worker 注册。决定资源采用、模式保留与安装/更新行为。
3. PEB-G03：原生/工具资源消费者与独立来源配方。引用已有 provider/ABI 缺口，避免递归重开。
4. PEB-G04：产品模式与独立运行时。当前仍为 504 unknown、5 shared、整项功能排除 0、完整运行时路线资格 0。
5. PEB-G05：筛查的动态调用覆盖。出现具体遗漏包装或消费者时再开，不以词法筛查冒充全局闭包。

509 项功能、582 个不同用户操作、125 个支撑操作、1844 条未执行场景、115 项职责、202 条依赖及原任务图均保持。客户端实现、构建尝试和新增运行通过为 0。已用完的模型样例授权不阻止上述静态工作；本批不请求新增授权，也不把该限制当作全局停滞原因。

[机器合同](process-entry-build-v1.json) · [55 条证据](process-entry-build-v1-evidence.jsonl) · [原始提取与输入](raw/process-entry-build-v1/input-manifest.json) · [核对结果](raw/process-entry-build-v1/verification.json)
