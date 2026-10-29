# 绘图工具：两个具体编辑器提供方

已把共享动态工具注册组件接到两个具体controls生产者：工作簿提供7种工具，演示编辑器提供6种，并集覆盖8个共享ID中的7个。`hand`仅工作簿提供，`note`在两张选定表都未提供。这里的“有”表示带条件的源码回调，实际挂载、交互效果和产品模式仍未验证。

| 命令ID | 工作簿 | 演示 |
| --- | --- | --- |
| `artifacts.selectTool` | 有 | 有 |
| `artifacts.handTool` | 有 | 未提供 |
| `artifacts.rectangleTool` | 有 | 有 |
| `artifacts.circleTool` | 有 | 有 |
| `artifacts.arrowTool` | 有 | 有 |
| `artifacts.lineTool` | 有 | 有 |
| `artifacts.textTool` | 有 | 有 |
| `artifacts.noteTool` | 未提供 | 未提供 |

## 条件与行为差异

两个wrapper用`!viewOnly`控制共享注册组件；辅助函数只计算编辑/导出/协作/产品导航权限，没有产品模式判定。两个容器还把“host允许编辑且CRDT发布就绪”传入内层。工作簿命令表额外要求manualEditUiEnabled，键盘又有grid、输入焦点和当前工具状态条件。演示的选定controls不提供工作簿那种自定义键盘匹配器。

- 工作簿select重置文本与hand；hand清除浮动形状文本并启用导航状态。text取消单元格编辑后激活文本工具。
- 工作簿形状回调直接调用`runWorksheetEdit('insertShape', ...)`，arrow映射line+true，且要求选中新形状。此处没有等待或本地捕获方法结果。
- 演示select清除多个临时状态，以commit:false结束元素交互和选择框；text反转文本工具状态。
- 演示形状回调清理其他工具后设置待插入geometry/arrow；此时不能认定形状已经提交或写入。

## 来源连接与维护边界

工作簿走`D → t/cx → Nv → Av → cv → sv`；Av是会增加插件的函数适配器。演示走`re → side-panel E → lazy n/bb.PresentationPanel → xb → v_ → lm`；panel的r/Pc是另一初始化器，实际组件由命名空间getter确定。两者最终把controls传给已核实的共享W/G注册钩子。

两个控制器hook别名ri/ai都导入artifact-source-bootstrap的Xt。本批记录传入参数、返回接口和回调效果，到该hook、构造器与controller方法停止；未证明实际是同一个运行实例，也没有凭chunk名判定编辑器实现属于某个公开依赖。恢复时需要分别维护共享注册适配和两种编辑器工具适配，保留不同状态及提交时机。

## 核验与剩余项

保存8次完整Program解析、6个不同文件；回查416个范围出现/216个不同范围，并对导出命名空间、两张完整命令表及条件做AST检查。原共享工具消费者连接继续有效；本补充只细化两个具体提供方。`note`的其他调用方、7项工具的Codex采用路径/用户目标和运行行为仍待确认，不能从局部未提供得出全局缺失。

968来源、706未关联、181明确机制、525待用途决定均保持；直接命令消费者缺口仍12，命令用户目标关联待确认仍20。保留两个源代码目标候选，不新增已采纳功能、模块记录或产品场景。503unknown/6shared模式、原39条要求/9项标准及M1–M7验收不变；没有新模型请求、客户端启动、构建或产品场景执行。

下一步只查两种wrapper的直接调用/懒加载位置及其路由、访问和模式条件，比较现有功能后再决定目标归属。

见[结构化合同](artifact-tool-providers-v1.json)、[核验记录](raw/artifact-tool-providers-v1/verification.json)和[此前8条消费者连接](command-consumer-gaps-v1.md)。
