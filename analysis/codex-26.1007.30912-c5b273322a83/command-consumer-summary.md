# 命令注册消费者批次结案

24个静态import候选已全部通过完整Program核对，均导入`app-initial`的`IBn → Pw`绑定；共56个直接注册调用，其中51处静态ID、40个不同静态ID、5处动态ID。[合同清单](command-consumer-contracts.json)保存逐文件import、参数绑定、最近函数和结构条件。

加上此前`app-initial`的49处，限定25个Program共105处直接调用、98处静态ID、80个不同静态ID及7处动态ID。80个ID均可按字面key连接到182条元数据中的记录；这只建立key关联，不证明功能等价、访问权限或模式。多个handler可共用ID，动态ID仍单列，默认handler表亦不在本次分母内。

本批关闭“24个import是否真实连接同一hook、有哪些直接调用和局部传递引用”这一有限问题。当前选定结果没有其他引用或本地重导出。它不覆盖namespace、动态import及全应用的其他注册API，也没有验证实际组件挂载或dispatch。既有48项有限功能、212条未执行验收规格、模式unknown和完整功能分母未知均保持。

初次primary分析把`yM as py`的导出标签`py`误计为import引用。已修正规则并仅重跑primary，当前otherReferences为0，5个直接调用完全相同。原结果和修正结果均保留；共25次完整解析、24个不同文件。[来源记录](command-consumer-provenance.json)包含每次命令、终态和输出哈希。

没有新增模型提交、原客户端运行或REA重跑。本批结束后不继续扩张注册细节，下一项转入[运行时方案](runtime-adapter-options.md)的A2能力/依赖决定：先核对task-manager启动guard与caller条件。默认命令表、实际dispatch、requiredAccess和挂载条件保留为后续明确缺口，不算已关闭。完整分析仍在进行。
