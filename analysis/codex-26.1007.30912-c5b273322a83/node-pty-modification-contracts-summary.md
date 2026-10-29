# node-pty 修改与客户端调用边界

固定 node-pty 1.1.0 的两个 Windows JS 有9处差异。所选静态范围形成18条记录（15确认、1推断、2未决）和11个未执行场景，见[合同](node-pty-modification-contracts.json)。

修改增加进程枚举 callback，并改变部分终止分支的顺序和返回值：Promise rejection 可回退，同步调用错误不由该 catch 处理；pre-ready kill 只排队。普通同版本上游包不足以证明接口等价。应评估独立补丁依赖、受维护 fork 或等价适配器；第三方实现留在本地分析副本，未复制到正式合同或维护源码。

[独立审查](node-pty-modification-contracts-peer-review.json)仅覆盖四个小型 package JS、9差异范围，100项检查。作者的[524项坐标及元数据验证](node-pty-modification-contracts-validation.json)另行统计；client main 的连续1383B声明窗口仅经作者静态分析，没有独立语义审查。原作者合同的 pending-peer 字段保留原字节，其后完成的有限 package peer 在[交付来源](node-pty-modification-contracts-provenance.json)单列。

原生来源/ABI、完整包等价、Windows实际运行、模式归属及 renderer services.terminal 到 main adapter 的实例连接仍未知。11个作者场景与15个peer fixture均未执行，不能合并为已验证行为。
