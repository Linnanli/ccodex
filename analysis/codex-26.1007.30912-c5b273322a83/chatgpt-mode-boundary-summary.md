# ChatGPT 候选模块边界定向分析

固定基线：`codex-26.1007.30912-c5b273322a83`。范围是 `features.json` 中 `chatgpt-conversation`、`chatgpt-project` 两个原先 inferred 组的 **9 个 publishedEntrypoints**，共 **704,298 字节**。这是候选模块分母，不是功能分母或全部消费者分母。

**9 个整模块的产品模式仍为 unknown；确认可排除模块数为 0。** 两个完整函数可以确认在源码内复用 Chat/Work 分支，但不能据此认定 Codex 归属或运行可达性。没有操作客户端、账户历史、凭据或模型，也没有执行目标代码。

| 完整模块（webview/assets 下） | 字节 | 完整函数 | call/new | import 声明 | export 绑定 | 边界调用形式候选 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| chatgpt-conversation-page-23bea3bc76ac.js | 150925 | 475 | 2400 | 57 | 15 | 2 |
| chatgpt-conversation-page-387f07c72a6d.js | 369 | 0 | 1 | 6 | 2 | 0 |
| chatgpt-conversation-runtime-184f29f1b276.js | 10556 | 77 | 329 | 6 | 2 | 2 |
| chatgpt-conversation-share-dialog-5d0caac55bcd.js | 45446 | 52 | 339 | 10 | 5 | 1 |
| chatgpt-conversation-share-dialog-f9af515a7eaf.js | 172 | 0 | 1 | 2 | 1 | 0 |
| chatgpt-conversation-turn-content-fb0cd9e95f87.js | 455292 | 1164 | 6091 | 74 | 22 | 17 |
| chatgpt-project-fetch-652f0ab6af18.js | 98 | 0 | 1 | 1 | 1 | 0 |
| chatgpt-project-settings-dialog-8af3e5dc9374.js | 38918 | 69 | 404 | 9 | 1 | 2 |
| chatgpt-project-sources-35a06ad8e3bc.js | 2522 | 4 | 26 | 2 | 4 | 0 |
| 合计 | 704298 | 1841 | 9592 | 167 | 53 | 24 |

解析包括 219,770 个 AST 节点、21 个动态 import 表达式，9 个完整模块没有解析错误。24 个边界调用形式记录只是限定审查入口，不能把 `fetch` 等方法拼写当作网络调用证明。每条保留实际词法绑定、完整调用范围、参数和适用的外部 export 别名；最终 receiver 实现、传输和模式未确认时保持 unknown。其余通用 UI 调用没有展开所有外层条件，空 conditions 不表示无 guard。

## 已审查的来源关系

- `MODE-R01`：两个页面 wrapper（完整 `f_`、`p_`）的 JSX 实参都绑定到同一个本地 `m_` 函数；小 wrapper 的实际 import/export 链可解析。复用冻结 Route 合同得到 2 个 lazy component consumer，分别关联 `ROUTE-0042`、`ROUTE-0045` 和 `ROUTE-0051`。这是源码注册/构造关系，不是运行可达证明。
- `MODE-R02`：完整 `m_` 用 conversation origin `tpp/flora` 生成 `X`，通过 `X` 选择 `productExperience: work/chat`，并对同一实际 imported mode-transition symbol（本地 `Jo` ← `app-initial.jqn`）传递 `work` 或 `X ? work : chat`。可确认此函数的源码 Chat/Work 复用。外层 transition 实现、挂载条件及 Codex 归属未知。
- `MODE-R03`：完整 `PM` 从 prop `isWorkConversation` 的词法绑定得到归一化变量 `U`，同一绑定用于分支和下游 turn/action 参数。可确认源码中的布尔分支复用；无法确认全部调用方如何赋值。
- `MODE-R04`：完整 `tS/sS/cS` 记录实际 Work handoff 请求、结果身份检查、刷新和 durable `tpp/continue_in_work` 验证，以及 imported continuation 调用（本地 `So` ← `app-initial.DRt`，saved export alias 为 `Xwi`）。已确认本地直接业务链；外部 request facade、continuation 实现与 Codex 可达条件未知。
- `CGP-R01..05`：冻结的三模块项目审查记录实际 `iOn` save、`oOn` upload hook、`sOn` delete hook、`fkn` 本地文件夹资格、`gkn` edit 绑定。`q`、`dt` 的 initializer 到 receiver 调用为本地词法数据流；返回对象方法实现仍在外部。设置组件有实际 `s && L && je(i)` 本地文件夹分支，复用的 `pss/Dos/jos/sFs` caller/guard 证据要求保留共享情形。

运行时模块直接调用 `/conversation/{conversation_id}/stream_status`、`.../genui/refresh_widget`；share dialog 直接调用 `/wham/accounts/check`；turn 模块包含 handoff、反馈、browser、connector 等实际 facade member 调用。上述路径用于保留实际参数来源，不用于按 URL 推断产品模式或合并功能。

项目 fetch 小模块只完成 import、initializer 调用及 re-export，没有自身 request 实现。`$wt→BY` 等 saved 大 bundle export alias 是符号事实。当前九模块没有建立到既有 `RWC-*` request-wrapper 业务合同的直接匹配（0），不能把已有 `TFt/AW` 或 `fN/e6` 合同套到 `$wt/iOn/oOn/sOn` 上。页面内实际 `Nvn` 根的 `dispatchHostMessage` 也只确认调用和 export alias；这不证明该调用进入 IPC。

## 模式结论与缺口

4 个主 range review、5 个项目 review 和 6 个复用 guard note 独立于完整 AST 分母。`oZ(allowWork)` 的 ChatGPT 能力/seat/Work Cloud 条件，conversation 的来源类型，sidebar `chat/work/codex` 产品模式，是不同维度。shared settings caller 和专用 project route guard 不能互相替代，也不能据命名删除整模块。

下一次仅需沿已登记的真实外部绑定补足实现和消费者：`$wt/BY` request facade、页面 mode-transition symbol、`So` continuation、项目 `iOn/oOn/sOn/fkn/gkn/akn` 的上游实现，以及这些组件的实际产品模式/flag/数据条件。只有具有完整适用范围的调用方和 guard 证据，才能给整模块或具体功能作可排除结论。未做新的大 bundle 完整 AST 扫描。

## 产物与校验

- `chatgpt-candidate-module-contracts.json`：9 个模块的完整 AST 合同、actual import/export 链、24 个边界记录、4 个主 range review、5 个项目 review 引用、2 个 Route consumer 和 6 个 guard note。
- `evidence.jsonl`：23,011 条 fresh 字节证据，其中 20,915 条 MODE-AST，2,096 条冻结 CGP 证据。原始相对路径、source hash、UTF-8 半开范围和 span hash 可核对。项目 journal 合入时保留原字段并增加统一 `id`；原 project 文件未修改。
- `project-review.json`、`project-evidence.jsonl`：被冻结子范围；其 counts 是上述9模块分母的子集，不能相加作为新模块/函数数量。
- `validation.json`：独立验证直接输入 hash、JSON pointer、引用 ID、源 hash/UTF-8 范围与 span hash。复用的历史间接输入单独列验证层级；既有 RWC 过去 pin 的 published global evidence index 随后累加，身份漂移会如实报告，不改原合同或声称该历史 pin 已通过。
- `frozen-manifest.json`：本轮输出和脚本 SHA256。

独立完整性核验的核心层有 **0 个错误**：48/48 个直接 artifact pin（含重复引用）、23,011 条 fresh span、1,841 个函数范围、9,592 个调用范围、5,216 个 JSON pointer 和 52,934 次证据引用均通过；实际引用的 131 个外部证据 ID 的源字节范围也全部通过。这里验证的是已保存证据与固定源码的身份和范围，没有重跑 AST 或执行目标代码。没有显式 producer pin 的 journal 只记录实际 hash，未引用的历史 journal 行不计为已核验。

历史间接输入层检查 12 个 pin，其中 **1 个身份漂移**，所以 `allLayersPassed=false`。既有 `.analysis-local/review-work/request-wrapper-contracts.json` 的 `/inputs/10` 引用 `analysis/codex-26.1007.30912-c5b273322a83/evidence.jsonl`：expected SHA256 为 `3be3357474d190e6ebf32b0943d9354f6a2ae0e6f3f5e2d0a25e8bbadf9d596b`，observed SHA256 为 `e0c0965293ac7733fcce7cc2d1a99c7a3a4eff7ae7f13e6674fedb43a92625a0`。这是旧合同的间接输入 pin；本轮 9 个直接源码输入与 fresh 证据均通过。保留旧合同和历史漂移记录，不声称全历史链通过。

独立验证重放命令：

```sh
python3 scripts/analysis/verify_chatgpt_candidate_modules.py
```

解析器：`@babel/parser 8.0.4`，implementation SHA256 `43d95824b43928626ccf99136e95ab90260c18406f22f8acf57f239483127f66`。重放命令：

```sh
/Users/nallylin/.nvm/versions/node/v22.23.2/bin/node scripts/analysis/chatgpt_candidate_module_contracts.mjs --parser-path /private/tmp/ccodex-rea-tooling/install/node_modules/@babel/parser
```

输出记录结构事实、范围和审查结论；没有生成第三方实现代码。模块内混合依赖的所有权不能由函数 inventory 自动确认。

[模式切换来源补充](mode-transition-origin-summary.md)将两处Jo调用接到jqn/gS及初始化、lPt。gS无值域校验，lPt有两处原样返回persistedMode；chat/work实参和codex字面缺失不能限定全局域。e导入身份用新增保存metadata有限关闭，工厂／存储、真实运行与Codex归属继续未知，原9模块及排除0不改。
