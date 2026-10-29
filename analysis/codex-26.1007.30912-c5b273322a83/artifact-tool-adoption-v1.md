# 工作簿与演示工具：功能归属及工程增补

7个命令已取得具名消费者、编辑器提供方及有限用户目标的源码关联：工作簿目标FSC-0512包含select/hand/text/rect/ellipse/arrow/line；演示目标FSC-0513包含除hand外的6项。每个编辑器是一项带工具参数的操作，不把13个参数出现算成13项功能。`noteTool`仍缺具体提供方。

页面编辑器惰性选择PageArtifactEditor，再按文档类型选择SheetsEditor或PresentationEditor。写权限、文档canEdit、readOnly、viewOnly，以及内层CRDT就绪等条件分别保留。版本预览明确isEditing:false；上传handoff的模块预加载不算编辑器挂载。**这两个目标的产品模式仍是unknown，不能据此声称已证明Codex采用，也不能认定ChatGPT专属并剥离。**

工作簿的几何命令直接委托insertShape，演示的几何命令只设置待插入状态。文本的单向激活与切换、hand差异、select的commit:false清理，以及键盘/focus/卸载守卫均进入操作和回归规格。与已有列表样式、浏览器批注模式及发送产物批注的目标分别对照，未将这些不同操作强行合并。

工程仍采用实施计划v12及其M1–M7验收。本增补把两个目标加入既有T51，提供共享注册、工作簿适配、演示适配3项维护职责和8条未执行规格；两张60节点依赖图无新增节点或边。编辑器/controller/worker/CRDT实现保留具名外部边界，第三方代码通过明确依赖方式引入，不复制实现。

当前有限清单511项功能、584项不同用户操作、1852条未执行规格；模式505 unknown/6 shared。命令源码用途待关联从20降至13：12项直接消费者缺口，加noteTool的具体提供方/用途缺口。968来源身份不变；699项未关联，含181项明确机制和518项待用途决定。7条关联仅关闭源码用途问题，未证明完整运行调用链。

本批核对7个完整程序，独立复核35,721个AST节点及446个不同源码范围。没有新增模型请求、客户端启动、服务访问、构建或运行通过；原39条要求、9项分析标准和完整复刻目标不变。上层模式准入、实际controller注入、形状最终提交/撤销/同步/重启结果仍待验证。

见[结构化合同](artifact-tool-adoption-v1.json)、[当前功能清单](feature-scope-v53.csv)、[实现覆盖](restoration-coverage-v44.json)、[模块归属](feature-module-ownership-v19.csv)及[当前来源处置](legacy-entry-dispositions-v37.json)。下一批处理已有12项直接消费者缺口和noteTool；没有矛盾证据时，不重开本批编辑器内部实现。
