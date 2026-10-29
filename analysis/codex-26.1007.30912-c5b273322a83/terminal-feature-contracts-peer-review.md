# 终端合同独立有界审查

最终状态为 `passed-with-static-scope-limits`。独立核对 35 条作者记录、43 个保存完整单位（逐单位原字节总和 48074，包含 manager/member 重叠）、6 条导入导出路径、38 条保存绑定记录及 6 条继承原行。最终完整核对 815 项、限定修订核对 601 项均无错误；两种范围有重叠，不合计为新覆盖。最终 7 产品精确 pins 在同目录 JSON 的 `reviewedProducts`。

七项语义差异已修正：宿主 create 排除本地消费的 workspaceRoot 并保留 conversationTitle；restart 直接返回异步重启结果，只有内部 close 结果在 finally 中传给 tR；renderer 选项没有 cols/rows，两个状态方法归 manager；TerminalTab 保留 durable/ordinary 条件；Reload 只证明 onRetry 转发；sessionId 的 nullish 创建选择与 truthy 清理守卫分别保留。队列 attached/listener/headless 条件、环境 error/exit 分支、同 id 重启及渲染器释放/宿主关闭差异均逐所选源码核对。

qli → returned terminal service → yGt → EGt 为静态条件绑定。实际 UI、宿主服务/PTY/native 实现、端口送达、模式、持久化与依赖版本仍 unknown。31 条原源码合同、4 条 artifact/unknown/proposal、6 条继承记录和既有 36 功能组分母保持独立；新增全局记录 0。

仅读保存文本及来源限定 metadata，未读或重 hash 原 bundle、未重新 parse、未运行作者或目标。来源窗外引用继承已有 metadata；183 个绑定子窗和 43 个单位只核对保存文本，完整节点类型继承旧 AST。真实 checker 失误、七项原 finding、修订前快照与每次 source/stdout/stderr/exit 收据均保留；第一次 final 检查因缺 snapshot 接受门禁已明确作废，最终接受 snapshot-final-02/check-final-02。

正式仅允许复制本 JSON/MD；实现文本、AST、输入快照、脚本和详细收据留在本地。
