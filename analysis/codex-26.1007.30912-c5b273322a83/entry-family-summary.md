# 旧入口分组与源码所有者映射

基线 `codex-26.1007.30912-c5b273322a83`。本次将原台账的968条记录全部定位到9个完整原始Program，分成10类机制、165个词法所有者组。[机器清单](entry-family-map.json)、[CSV](entry-family-map.csv)和[来源记录](entry-family-evidence.jsonl)保留全部原入口ID。没有新增模型请求或操作原客户端。

## 会改变后续分析的结论

原“settings-section-lexical-candidate”的53条全部是 `ua` 表的属性。完整Program中只有一个顶层 `ua` 声明、一处赋值和一处读取；`la(e,t)`按key返回 `component`、`commandAsset`、`navigation`资源描述，并对cloud-environments及Windows appshots作特例。53条都不是设置panel注册证明，不能作为设置功能分母。对应源范围和导出保存于[表分析](raw/entry-families/settings-table.json)。后续设置盘点应以真实panel及可见性消费者为入口。

182条命令元数据的源码所有者为 `MG`、`kG`、`AG`。原完整注册合同将其分为153条webview、21条electron-only、8条vscode-only；后两者通过 `NG`附加kind并展开到MG。平台kind不等于产品模式，元数据不是handler注册。它们的命令ID、requiredAccess、shortcutScope和原合同指针逐条保留，下一项按真实注册消费者批量连接。

170个路由构造仍归 `ZIs` 初始化函数，三个转换消费者、47个导航目标分别登记。父子关系、构造条件和原guard note关联保留；layout、redirect、资源或协议分支不能逐条当成用户功能。143个宿主消息case归同一个 `MMe.handleMessage`，实际状态/接收实例仍须沿具体功能合同证明。

## 分组

| 机制 | 原记录 | 词法所有者组 |
| --- | ---: | ---: |
| 路由构造 | 170 | 1 |
| 导航和重定向 | 47 | 31 |
| 路由表转换 | 3 | 1 |
| 命令元数据 | 182 | 3 |
| 原生菜单装配 | 189 | 14 |
| 宿主消息分发 | 143 | 1 |
| 后台调用候选 | 91 | 42 |
| IPC 通道候选 | 50 | 49 |
| 设置图标和导航资源描述 | 53 | 1 |
| 快捷键及 renderer 注册 | 40 | 22 |

词法所有者表示源码内包含该范围的外层绑定，不能代替业务状态所有者或运行实例。清单的环境与拟议包路径是维护设计建议；`productMode`保持unknown。

## 核验与后续

9个不同源码文件进行了9次完整Program解析，设置小文件补充解析1次；共5,617,835个AST节点。824条原范围恰好对应完整节点，余144条是原词法范围：91条位于完整调用中，53条位于资源ObjectProperty中。没有把这些词法片段改称完整节点。1712个不同源码范围的哈希经冻结文件核对。

本次关闭“旧入口缺少统一源码所有者分组”和“53个设置词法候选究竟是什么”两项限定问题。用户功能定义仍为48项，212条功能验收规格仍未执行；旧台账的功能关联、模式、337条deferred及实际行为缺口没有因分组而减少。完整功能分母继续未知，分析未完成。

下一步按[清单中的nextActions](entry-family-map.json)连接命令注册消费者及访问条件，同时推进A2的运行时/依赖决定。设置改从panel消费者盘点。这些组用作有限工作批次；不重复调查已定位的归档、resume、fork和start入口。[实施计划v6](implementation-plan-v6.md)和[原分析计划](../../docs/reverse-engineering/analysis-plan.md)继续有效。
