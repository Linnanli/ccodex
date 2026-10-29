# 跨宿主命令描述的用途与桌面准入

8个VSCode描述项的源码用途已判定为跨宿主命令描述机制：`implementTodo`、`openSidebar`、`newCodexPanel`、`addToThread`、`addFileToThread`、`showLspMcpCliArgs`、`dumpNuxState`、`resetNuxState`。主进程AG与渲染端r6n内容相同，均经包装写入`kind: vscode-only`。

## 已确认的边界

- 命令菜单：渲染端`g6n → jmn → Gr`要求`kind === webview`；实际`wn.filter`把不满足者排除。
- 快捷键对话框和设置：`v6n → Amn → P/Ee`排除`vscode-only`；实际的`I.filter(P)`及`Oe.filter(e => Ee(e) && ...)`均使用该条件。已按声明身份区别局部同名变量。
- 键位更新：共享`WG/nK`使用相同宿主条件，`vK`在持久化前对不可配置命令抛错。

这些条件只证明选定菜单/快捷键/配置投影。通用注册器是否能登记任意ID、是否存在其他桌面调用方、扩展处理器如何实现，均未据此判定。`vscode-only`不是产品模式；enablement字符串没有执行。

## 工程与缺口处置

保留`packages/command-contracts`的ID、描述数据和平台投影约束，不为这8项生成猜测处理器或新增桌面功能。对应版本VSCode扩展实现与宿主连接仍是具名缺失材料；只有发现实际桌面注册/调用或相反源码证据时，重开具体链路。工程依据仍为实施计划v12及前次工具功能增补；本次不新增任务、目录或依赖图节点。

源码用途待决定命令13→5：剩余`openControlWindow`、`canvas.prompt`、`toggleNotch`、`notchVoice`和`noteTool`。其中前4项需要实际接收器，note需要具体提供方与已知参数化注册器的连接。

**未知处理器连接仍为12项：8项扩展侧、4项桌面候选。** 不能把用途分类完成计成消费者连接完成。968来源中699项仍无功能映射；明确机制181→189，待用途决定518→510。

有限功能清单仍为511项、584个不同用户操作、1852条未执行规格，模式505 unknown/6 shared。没有新增运行通过、模型提交、模式分类或客户端实现；整体分析尚未完成。

本次使用5份完整Program AST，共3,666,782节点；独立复核源码字节、AST范围、导入导出连接与字面量描述一致性。目标JS未执行。结构化结论见[合同](command-platform-dispositions-v1.json)，来源账本见[v38](legacy-entry-dispositions-v38.json)。
