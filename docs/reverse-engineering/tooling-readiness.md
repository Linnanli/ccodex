# REA 工具接口与准备状态

日期：2026 年 10 月 13 日。状态：固定版本工具已安装，微型样例和首次正式应用分析均已结束；正式结果的结构图为 partial，语义图为 partial 且 truncated。以下是工具接口及环境核实，客户端分析结论另见基线目录。

## 固定版本与来源

| 项目 | 核实结果 |
| --- | --- |
| npm 包 | `rea-agents@6.4.0` |
| npm 发布源码提交 | `a56f7bb668ab23fec8d33f7af353ac7ed2fe1895` |
| Node.js 要求 | `^22.19.0 || ^24.11.0 || >=26.0.0` |
| 本机 Node.js | `v22.23.2` |
| 本地 CLI | `/private/tmp/ccodex-rea-tooling/install/node_modules/rea-agents/scripts/rea.mjs` |
| 版本实测 | `node .../rea.mjs --version` 输出 `6.4.0` |
| 安装方式 | 临时目录局部安装；未执行 `setup`、全局安装或包安装脚本 |
| 辅助依赖 | `playwright-core@1.58.2` 已安装在该临时工具目录 |

npm integrity 为 `sha512-Vj1zWfSlna5bphGoaoI/TcVBuYvze9u+OyPC3Shz8YkBqaCTqB4COnnRoX7XDwMpwI24ZlFEel2yEj0k8LTWEQ==`。注册表元数据、实际安装包版本、CLI 帮助、锁文件和证据哈希保存在 [本地工具清单](../../.analysis-local/tooling/tooling-manifest.json)。临时安装目录可能被系统清理；需要重建时按照清单中的固定版本和锁文件安装。

本机 npm 默认镜像出现证书验证失败。准备过程通过命令级 `--registry https://registry.npmjs.org` 获取官方元数据并安装，没有修改全局 npm 配置或关闭证书验证。

## 发布版本可用的静态分析命令

输入支持绝对路径的 ASAR 或提取后的应用目录。正式执行应使用冻结副本，并将 unpacked 伴随目录一并提供。

```bash
node --max-old-space-size=8192 \
  /private/tmp/ccodex-rea-tooling/install/node_modules/rea-agents/scripts/rea.mjs \
  analyze-javascript-application "/绝对路径/冻结副本/app.asar" \
  --max-heap-mb 4096 \
  --analysis-timeout-ms 600000 \
  --artifact-format asar \
  --integrity-policy fail \
  --format json \
  > "/绝对路径/分析结果/rea-application.json" \
  2> "/绝对路径/分析结果/rea-progress.jsonl"
```

上述命令和参数通过 6.4.0 的实际 CLI 帮助核实。它是严格校验的命令模板；实际执行记录保存于基线目录的 run.json 文件。`--max-old-space-size` 控制主 CLI 的 V8 堆，`--max-heap-mb` 仅控制独立源码分析器；数值需结合机器内存调整。`--analysis-timeout-ms` 是每个源码的启动、分析及传输期限，超时可能返回部分证据并终止剩余分析。

6.4.0 的专用 CLI 选项为 `--max-heap-mb`、`--analysis-timeout-ms`、`--artifact-format` 和 `--integrity-policy`。输出使用 `--format json` 或 `--format jsonl`，进度写 stderr。不得用展示用的 `--filter-output`、`--token-limit`、`--token-offset` 代替原始完整结果保存。

## 需要记录的范围和限制

- 6.4.0 使用静态文本及 AST 分析，不执行目标 JavaScript、HTML 或原生模块。
- 根归档哈希、inventory manifest、结构图、语义图、统计、limitations 和 coverage 是结果的独立部分。需要检查它们各自的完整性，不能只看命令是否退出成功。
- 发布包中语义节点上限固定为整个应用 `100000`、每个源码 `20000`；增加内存不会解除它们。被省略的调用和数据流关系保持未知。
- 源码分析器默认 V8 old-space 为 `1024 MiB`，每个源码默认期限 `300000 ms`。允许设置 heap `128–16384 MiB` 和期限 `1–2147483647 ms`；这些是工具参数边界，不是机器资源保证。
- 静态目录读取不跟随符号链接；unpacked 文件缺失、完整性不一致、无效 UTF-8、解析失败及资源不足必须保留为缺口。
- 原生 `.node` 的语法调用线索不证明实际原生导出；source map 路径或哈希也不证明原始工程已恢复。
- JSON/JSONL 输出可流式保存；MCP 完整响应仍受传输预算影响。大结果宜保存 CLI 原始 JSON，后续再按 graph 及 Evidence 查询。

6.4.0 未提供 `--source-path`、`--max-semantic-nodes` 或 `--max-semantic-nodes-per-file`。调查时 GitHub `main` 文档包含这些选项，但它们不能作为该 npm 版本的可执行接口依据。正式分析应引用 [发布提交对应的文档](https://github.com/morluto/rea/blob/a56f7bb668ab23fec8d33f7af353ac7ed2fe1895/docs/javascript-artifact-reconstruction.md) 及本地实际帮助。

对于大型应用，先完整保存原包分析，再逐项检查覆盖缺口。分目录或按原始文件生成额外调查输入能够减少总容量压力，但会改变输入根哈希，不能直接声称这些补充图与原始应用图同一身份；每个补充输入需有原始路径、文件哈希和范围映射。单个大 bundle 超过每文件上限时，6.4.0 无法仅通过 CLI 参数保证完整语义分析，需要有来源映射的 AST 定向分析、后续发布版本或其他明确记录的补充方法。完整文件盘点、静态关系覆盖和实际行为验证必须分别统计。

## 功能追踪与实际行为观察接口

`trace-application-feature`、`trace-javascript-semantics` 和版本比较消费既有应用 Evidence，不会执行目标。独立 CLI 进程之间没有保留会话引用，需要在 JSON 请求文件里提供完整 Evidence。

已用四个冻结原文件组成独立补充输入，实际执行架构分析与两次 feature trace，记录见 [补充报告](../../analysis/codex-26.1007.30912-c5b273322a83/supplemental/rea-bootstrap-bridges-v1/report.md)。字面通道 `get-shared-object-snapshot` 匹配成功；通过常量别名使用的 `message-from-view` 未匹配，不能据此判定功能缺失。

源码核实表明 8 MiB 是 JSON 解析方式切换阈值，并非输入文件大小上限。635 MB 原始 Evidence 可用 [包装工具](../../scripts/analysis/wrap_rea_trace_input.py) 逐字节嵌入请求，但 REA 后续仍需在内存中构建、校验完整对象；本轮没有运行该大文件 trace。补充输入的图与完整应用图保持不同身份。

Electron 的 `file://` 页面使用以下 attach 工作流：

```bash
node /private/tmp/ccodex-rea-tooling/install/node_modules/rea-agents/scripts/rea.mjs \
  list-electron-targets http://127.0.0.1:9444 --format json

node /private/tmp/ccodex-rea-tooling/install/node_modules/rea-agents/scripts/rea.mjs \
  inspect-electron-page http://127.0.0.1:9444 "实际返回的目标ID" \
  --observation-ms 1000 --format json
```

该观察接口接受 literal loopback HTTP endpoint 和真实 ASAR 内页面，记录 DOM、frame、资源和脚本元数据；`--include-script-sources` 可显式取得脚本文本。它不点击、不导航、不调用 Electron IPC。HTTP(S) 页面另用 browser 系列接口。脚本存在与运行行为、因果关系是不同证据。

`capture-electron-scenario` 是主动运行接口，会拥有应用生命周期并安装观察 hook，且会阻断部分 shell、updater 和系统集成效果。若要对照未经这些 hook 改变的基线行为，应使用独立样例配置运行应用，并通过被动观察配合实际操作验证。[Electron 观察说明](https://github.com/morluto/rea/blob/a56f7bb668ab23fec8d33f7af353ac7ed2fe1895/docs/electron-observation.md)

## 本机预检结果

独立五文件样例最初两次在 sandbox 中均于 `main.js` 的 JavaScript worker 启动前失败。失败返回包含 inventory、部分 HTML 观察和 `details.partial_observation`，这些仅属于工具样例。

REA 在 macOS 上通过 `xcrun swiftc` 编译内部进程归属 helper，失败日志包括默认 `~/.cache/clang/ModuleCache` 写入被当前 sandbox 拒绝，以及随后出现的 Swift compiler/SDK 诊断。检查安装代码确认它会删除 `CLANG_MODULE_CACHE_PATH`；命令级 `XDG_CACHE_HOME` / `SWIFT_MODULECACHE_PATH` 预检仍然失败。第三次在获准的正常本机环境中成功完成五文件分析，并产生最终 Evidence `ev_7f370f0984a81616c116e246309c3fd35436c44ab4386391f3d30b0f915db86d`。因此前述 SDK 诊断不能单独证明工具链不兼容。没有修改全局环境或工具源码，没有关闭进程归属检查。

保留的结果为：

- [默认环境预检](../../.analysis-local/tooling/fixture-analysis.json)
- [局部缓存环境预检](../../.analysis-local/tooling/fixture-analysis-scoped-cache.json)
- [真实 CLI 帮助](../../.analysis-local/tooling/analyze-javascript-application.help.txt)
- [正常本机环境预检结果](../../.analysis-local/tooling/fixture-analysis-unsandboxed.json)

正式运行需要允许工具编译自身 helper 及检查其分析 worker。成功的 fixture 证明环境预检通过，仍不能计为客户端分析完成。

实际目标使用 `app://-/index.html`。REA 6.4.0 的 `list-electron-targets` 已成功连接测试端口，但将三个 page target 全部归入 `unsupported_url`，可分析目标为零；其被动 Electron 接口当前仅接受受支持的本地 file 页面。客户端 UI 行为通过独立 CDP/Playwright 观察补充，必须在证据中标明方法，不能伪称 REA 已完成页面观察。
