# source-context 的维护模块建议

建议路径 `apps/desktop/src/main/context/source-context.ts`，用于维护已知主进程配置接收链所用的第一方上下文转发。该路径由职责提出，原作者目录与其他消费者尚未知；模式归属保持 unknown。

[结构化映射](source-context-module-proposal.json)把 lX、rX 和 k 的三个原始范围接到[新来源合同](settings-source-context-origin-summary.md)，每项保留完整文件 hash、byte/UTF-16范围和小单位 hash。原 frozen 6 个来源模块建议保持不变。

依赖采用所选运行时内置 `node:async_hooks` 的 AsyncLocalStorage。维护 adapter 保留同步转发、原返回值和异常边界；不复制 Node 原生实现，也不为内置API生成 npm 包。接口类型、实际source值、实例生命周期与其他消费者须继续调查。

升级时分别检查新基线绑定/范围变化、运行时API、上下文隔离、return/throw/Promise identity与异步继承。候选本机实验和真实主进程/client行为分别验收，完整fetch、I/O取消及持久化仍未验证。
