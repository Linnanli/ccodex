# 20项命令消费者缺口：动态工具表连接

本批确认8个工具ID连接到已有参数化注册调用，直接消费者缺口由20降至12。具体编辑器命令提供方、用户目标归属、产品模式及真实效果尚未证明。20项命令的用户目标关联仍全部保留，不能将8条连接算作8项功能完成。

## 已确认的连接

`MG:id=jG.*.id`与renderer的`yP`包含同样8组常量。`yP`经静态导出`Lmn`进入header的导入`O`，初始化为`Y=Object.values(O)`。`W`枚举Y，取传入的`controls.commands[tool]`；值为truthy时生成G，G调用从`IBn/Pw`导入的注册钩子。这里细化的是历史[消费者记录](command-consumer-contracts.json)中已有的`E(n,o,l)`动态调用。

| 命令ID | controls.commands键 |
| --- | --- |
| `artifacts.selectTool` | `select` |
| `artifacts.handTool` | `hand` |
| `artifacts.rectangleTool` | `rect` |
| `artifacts.circleTool` | `ellipse` |
| `artifacts.noteTool` | `note` |
| `artifacts.arrowTool` | `arrow` |
| `artifacts.lineTool` | `line` |
| `artifacts.textTool` | `text` |

`G`的活动条件要求编辑器可见，并按originPanel或编辑器/tabpanel焦点判断。键盘路径还拒绝关闭键盘、已处理、重复、组合输入、编辑器外目标及具名辅助谓词F命中的事件。`W`的快捷键匹配条件使用`!=null`，生成G使用truthy，两者不能混同。

`Pw`在effect中注册并清理；普通业务回调返回值不会被返回或await。`Pqt`允许同ID多个项，派发按优先级及逆序活动项进行。注册存在、菜单派发成功与实际工具效果分别需要证据。

## 仍保留的12项直接消费者缺口

`openControlWindow`、`canvas.prompt`、`implementTodo`、`openSidebar`、`newCodexPanel`、`addToThread`、`addFileToThread`、`showLspMcpCliArgs`、`dumpNuxState`、`resetNuxState`、`toggleNotch`、`notchVoice`。

- `openControlWindow`有命令菜单可见性条件，缺实际业务接收器。
- `canvas.prompt`有菜单聚焦与通用派发路径，缺具体编辑器处理器。
- 8项`vscode-only`有元数据及快捷键可配置性过滤，缺实际扩展注册或桌面转发连接。名称和enablement字符串不能决定产品模式。
- `toggleNotch`与`notchVoice`在选定快捷键列表中被过滤，缺命令ID到系统快捷键/窗口处理器的连接；过滤不支持全局缺失结论。

## 校验与边界

复用完整Program作用域提取：15次解析、10个不同文件；本批回查1143个范围出现、472个不同范围，并核对ESM导入导出、8组常量和注册参数。文字预筛覆盖15067个JS路径，73个候选中9个解析、64个locale类候选只校验字节与哈希；预筛不能证明动态消费者不存在。header为额外导入消费者，不计入这9个文字候选。

来源账本仅更新8条消费者状态；其余960条不变。706条未关联记录、181项明确机制、525项待用途决定、509项功能及503unknown/6shared模式均不变。产品场景执行、模型请求、客户端启动、构建与实现新增均为0。原39条要求、9项分析标准和M1–M7验收保持不变；v7审查的20项是历史快照，本补充只更新消费者缺口维度。

下一步只查header导出W的具体调用方及controls生产者，核实工具所属用户目标；到已命名的编辑器包接口即保留边界，不重复展开已明注册器或原生提供方。

结构化结论见[合同](command-consumer-gaps-v1.json)，范围与解析检查见[核验记录](raw/command-consumer-gaps-v1/verification.json)。
