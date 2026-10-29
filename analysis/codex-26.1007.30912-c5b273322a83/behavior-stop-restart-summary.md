# 执行中停止／重启的实际结果

本组2次授权已用2次、余0。第二条按原精确提示提交一次；首条取消仍未测到。[结构化结果](behavior-stop-restart.json)及[来源索引](behavior-stop-restart-provenance.json)保存各次检查。

停止前，同一thread/turn的UI明确为inProgress、cwd匹配；重新核实自有主PID后发送一次SIGTERM，主进程及当时记录的3个CLI子进程退出。之后以同一冻结应用、profile、CODEX_HOME和策略启动新PID，CLI身份复核通过。

重启后首次当前页样本未显示原提示。专用项目内实际侧栏行已从临时client-new-thread标识变为local:加后端UUID；先从该行自身entry.conversationId/cwd确认身份，再定位实际已观察行点击一次。原thread/turn重新出现，状态为interrupted，记录的items只有userMessage。没有新提示、重发、resume RPC或继续按钮操作，没有观察到继续执行。这验证本次中断状态可重新打开，不证明后台自动恢复执行或耐久写入机制。

此前用户明确允许对同一合成目录重新登记，得到新项目ID。登记仅调用一次：初版观察器因额外dialog计数而停下，稍后同一原调用已fulfilled，根目录与实际UI均核实；未点击信任、未重试登记。早先“项目控件缺失／剩余1次”是中间快照，当前预算以本批为准。

README仍匹配原71字节／SHA256；该会话没有独立文件读取审计。完成观察后，自有应用及已记录CLI子进程清理退出已核实。第一条的completed UI与本条interrupted UI分别保存；取消、其他故障恢复、PTY、审批和完整功能仍待分析。
