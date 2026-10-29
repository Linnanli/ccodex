# 依赖静态调查阶段结果

基线：`codex-26.1007.30912-c5b273322a83`。范围为冻结副本；未执行客户端代码，未读取用户会话数据，未生成第三方实现代码。此成果是分析阶段的依赖子任务结果，需要后续与 REA 的模块关系、功能调用方和行为记录合并。当前不能据此宣称逆向分析完成。

## 覆盖与版本依据

- 根声明：46 个 runtime、32 个 dev，共 78 个。6 个存在根路径实际解析的安装元数据；1 个只有嵌套安装元数据（`@worklouder/wl-device-kit`）；71 个没有 ASAR 安装 manifest，需要定位内嵌代码或构建依赖。
- ASAR 的 `node_modules`：51 个 package.json 全部解析；49 个具名且有版本、34 个唯一名称；2 个仅是模块格式描述；0 个解析错误。
- 归档外：59 个 package.json 全部解析；58 个具名且有版本、31 个唯一名称；1 个没有版本的 default_app 描述；0 个解析错误。
- 第三方声明通知：1466 条 name/version、1283 个唯一名称。通知明确写 “may be included”，因此版本只能作为候选。通知同时包含 React/React DOM 19.2.7、19.2.8，Zod 3.25.76、4.4.3，Vite 8.1.5、8.2.0，不能把整个通知表当成客户端运行锁文件。
- 对 14816 个 `.vite`/`webview` JS 文件做了词法扫描，得到 620 个 bare import 候选（161 个名称），17 个嵌入版本自报线索。语法高亮语法和字符串中的示例可能产生候选，尚须 AST/REA 确认；动态计算的加载不在该覆盖内。
- 已核实行为：0。与上游逐文件比对的包：0。所有修改状态都明确记为 unknown。

## 根路径可解析的安装版本

| 名称 | 根声明 | 根路径安装元数据 | 元数据许可证 | 证据 |
| --- | --- | --- | --- | --- |
| @worklouder/device-kit-oai | file:../vendor/oai-js-registry/worklouder/device-kit-oai/0.2.1/package | 0.2.1 | UNLICENSED | dep-e-00042 |
| better-sqlite3 | ^12.11.1 | 12.11.1 | MIT | dep-e-00043 |
| node-pty | ^1.1.0 | 1.1.0 | MIT | dep-e-00047 |
| objc-js | 1.5.0 | 1.5.0 | metadata未声明；见许可证文件 | dep-e-00049 |
| tslib | ^2.8.1 | 2.8.1 | 0BSD | dep-e-00051 |
| node-addon-api | ^8.9.0 | 8.9.0 | MIT | dep-e-00046 |

`@worklouder/wl-device-kit` 0.2.2 的 manifest 位于 device-kit-oai 的嵌套 node_modules；它说明嵌套包存在，不证明根路径 `require('@worklouder/wl-device-kit')` 可解析。`node-addon-api` 的 7.0.0、8.9.0 共存，根路径版本是 8.9.0。

`objc-js` 元数据未声明 license，但其 `LICENSE` 首行是 MIT License；文件来源与 SHA-256 在 installed-dependencies.csv 中，不以缺失 metadata 字段推断不存在许可证。

嵌入自报线索：Sentry SDK family 10.29.0; react 19.2.7; react-dom 19.2.7; Statsig SDK family 3.34.0; zod 4.4.3。这些线索记录了字节位置和 hash，尚未建立完整的上游代码范围映射。SDK family 线索不能直接确定具体子包。

## 第一方私有与第三方私有边界

根声明中的第一方私有候选（13 个）：@oai/integrity-state, app-server-manager, app-server-types, browser-api, browser-backend-common, browser-common, commands, external-agent-migration, git-worker, protocol, shared-node, @openai/codex-app-tools-plugin, browser-client。

归档外还存在 `@oai/cua` 0.2.6、`@oai/cua-repl` 0.1.0、`@oai/sky` 0.7.6、`@oai/browser-desktop` 0.1.1；明确记录为第一方私有候选，保留源码与接口调查项。

`@worklouder/device-kit-oai` 0.2.1、`@worklouder/wl-device-kit` 0.2.2 自报 UNLICENSED，未声明公共 repository；属于第三方私有供应组件候选。需要来源/取得方式/接口评估，不能默认能通过公共 npm 包替换。其子依赖和原生/Wasm 均被保留，模式归属仍需调用方追踪。

## 原生、Wasm 与运行时

- ASAR 原生 `.node` 15 个，归档外 `.node` 51 个，共 66 个发布原生工件；包含其他平台预编译件，数量不代表当前机器会加载全部。
- ASAR Wasm/Webcil 34 个，归档外 Wasm/压缩 Wasm 8 个。含 .NET/OpenXML/Protobuf、Walnut、Worklouder LVGL、orbit characters、浏览器可访问性/ZXing 等；源码所有权和 Codex 模式需求仍待逐项确认。
- 归档外 Mach-O/ELF/PE 工件 112 个（包含上述 51 个 `.node`）；已保存 `file` 平台识别结果与 hash。
- 发布 `owl-electron-app.json` 明确自报 `runtimeName: owl` 和运行时归档 hash。根 devDependency `electron: 42.3.0` 是构建声明，不足以证明运行时为该版本。
- `com.openai.codex.framework` 在 plist 自报版本 `155.0.8059.40`（dep-e-02520）。
- `org.sparkle-project.Sparkle` 在 plist 自报版本 `2.9.1`（dep-e-02521）。
- `codex-package.json` 自报 CLI 0.162.0-alpha.17.2，target x86_64-apple-darwin，含 CLI、code-mode-host、voice-host、zsh/rg 与系统插件等边界。
- voice sources.json 保存了 11 个 source name/version/url/hash 声明及 1 个 GVDB revision；声明可用于后续取得源码，尚未下载与核实构建。不能根据 voice 名称就删除为 ChatGPT 专属功能。
- 盘点到 756 个第三方源码/头文件/原生构建输入；文件存在不证明输入完整或能重新构建。尤其 permissions.node/LVGL、Walnut、orbit、定制运行时需要来源或替代方案。

## 构建输入与差异

30 个构建输入出现项均未随发布包提供，其中 21 个为根 scripts 引用，9 个为锁文件/工程配置候选。缺失项见 build-inputs.json；记录的是相对该发布包缺失，不推断原工程没有这些文件。

- 原根脚本依赖上级 cli、app-server-types、scripts 以及缺失的 owl-shell/prepare/package 脚本。原构建流程不能直接从发布输入重跑。
- 未提供 pnpm/yarn/npm 锁文件、pnpm-workspace、tsconfig、Forge/Vite 根配置。
- @serialport/bindings-cpp 声明 node-gyp-build 4.6.0，而就近安装 manifest 是 4.8.4；不能根据 root 声明或单独包声明锁定最终依赖树。
- node-pty 声明 node-addon-api ^7.1.0，就近可解析版本为 8.9.0；需要确认 overrides/构建处理。
- better-sqlite3 声明的 prebuild-install 未随包提供。已有 better_sqlite3.node，缺失安装工具不能直接推断运行加载失败，但重新构建/安装过程需要补齐。
- 外部 cua_node 的 playwright/playwright-core 自报 1.57.0，与根 devDependency ^1.61.1 不同；工具运行时应独立锁定，避免合并成一个版本。

## 未解决项与下一步

1. 结合 REA/AST 为每个保留功能确认第三方调用方、Codex/ChatGPT/shared 归属及传递依赖；所有现有 mode 均是 unknown，不做无证据删除。
2. 对缺失 manifest 的 bundle 依赖定位版本和原始模块范围，先使用通知候选及版本自报，再对照准确上游包。
3. 取得锁定包后核对源码文件与原生构建 patch；目前没有任何“未修改上游”的证明。
4. 识别私有包、定制 Owl 运行时、原生扩展、Wasm 的接口/源码及来源条件；将不可取得源码的部分独立写入实施缺口。
5. 为实现工程选择准确依赖版本和生成新锁文件；必要 wrapper 属于待恢复的第一方代码，第三方实现由依赖管理引入。

## 产物

- `dependencies.json`：根声明、ASAR/外部安装包、嵌入版本线索、就近依赖边、词法 import 候选。
- `root-dependencies.csv`、`installed-dependencies.csv`、`external-dependencies.csv`：可合并的清单。
- `attribution.json`：完整通知 name/version/license 文本线索及字节范围。
- `native-runtime.json`：原生/Wasm 工件、运行时与 plist 元数据、voice sources 声明、存在的源文件/构建输入。
- `build-inputs.json`、`summary.json`：缺口与覆盖分母。
- `evidence.jsonl`：sourcePath/sourceHash/locator/method/confidence；只静态确认存在，不代表行为已验证。
- 复现脚本：`scripts/analysis/dependencies.py`。所有大体积原包和第三方实现仍只存在于独立本地分析副本。

## 公开精确版本归档核对

已静态比较五个根包，官方 npm 的 dist.integrity 全部通过，详见 [逐文件报告](upstream-comparison.md)。node-pty 的两个 Windows JS 文件与上游不同；objc-js 原生文件也不同。better-sqlite3/node-pty/objc-js 的原生来源、ABI 和独立构建尚未验证；发布文件缺失与源码修改分别统计。CSV 中仅对应根声明及根安装 occurrence 更新修改状态，同版嵌套安装不继承该结论。先前静态盘点中的“尚未比较”描述是历史范围，现以上游比较记录补充，依赖运行验证仍为 0。

## 内嵌版本声明与逐项调查动作

17/17 既有 bundle hint 已绑定源码声明，详见 [内嵌依赖续查](embedded-dependency-continuation-summary.md) 与 [逐项调查动作](embedded-dependency-investigation-actions.json)。CSV 的 source、recommendedIntegration、unresolved 和 investigationActions 已逐条补齐。sourceSelfReportedVersion 单独记录源码自报，version 保留为空，因为实际上游分发版本仍未确认；Sentry 注册表默认值和索引不等于活跃版本，私有 Statsig 不等于普通公开包。第一方适配器保留，完整第三方闭包、修改状态、模式与运行均继续调查。原 CSV 字节和哈希由 raw/dependency-publication 的 before 快照保存。

## 基线目录发布清单

本说明已发布到固定基线目录；此前列出的 dependencies.json 与各独立 CSV 保留于 `.analysis-local/dependency-work/`。公开合并清单为 `dependencies.csv`，使用 occurrenceType 区分 root-declaration、asar-installed-package、external-installed-package、bundled-version-hint，共 202 条。证据位于 `dependency-evidence.jsonl`；统计和本地完整索引的路径与 SHA-256 位于 `dependency-summary.json`。构建输入和原生/Wasm 清单分别为 `build-inputs.json`、`native-runtime.json`。source map 全范围扫描单独记录在 `source-maps.json` 和 `source-map-evidence.jsonl`。

## Source map 全范围核实

读取并对照基线哈希的文件为 17848/17848 个，包含全部 ASAR 与归档外 JS/MJS/CJS/CSS/JSON；独立 `.map` 文件按完整文件清单检查。ASAR-unpacked 的磁盘重复件与 symlink 排除计数、逐文件路径/hash 都保存在 source-maps.json。

共 11325 个 sourceMappingURL 文本出现点，涉及 11318 个 JS 文件；全部由 Babel 完整解析并确认注释位置。实际 directive 注释 11316 个，均引用冻结输入中缺失的相对 `.map` 文件。9 个文本误报出现在外部 Playwright 的 babelBundleImpl.js/utilsBundleImpl.js 字符串、代码或正则中，未计为可用 source map。解析未解决 marker 为 0，读取/哈希错误为 0，JSON 解析错误为 0。

独立 map 文件 0；内联解码 map 0；JSON source map 对象 0；可取得的 sourcesContent 条目 0。这证明冻结发布输入没有可利用的 source map 源码覆盖；原构建环境、远端调试服务或其他未随发布输入提供的 map 是否存在仍未知。包内已有的未打包源码文件另行记录，不能由 map 缺失推断所有源码文件都不存在。

source-map-evidence.jsonl 的 11325 条证据已核对 sourceHash、字节定位边界和引用，marker 总数等于真实注释+误报+未解决数；验证结果见 source-map-validation.json。
