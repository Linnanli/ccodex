# 音频 measurement：生产与消费边界

已定位两条独立服务：通用 histogram RPC provider，以及实时语音麦克风发现诊断。后者在 createAppHost 创建时触发一次配置，进程 readiness 后配置具名 histogram；同步配置失败不自动重试。它同步读取 measurements，逐次累加两个布尔桶，处理 missing、unsupported、counter_discontinuity 和 unavailable。音频服务退出次数由独立的 child-process-gone 状态提供。

renderer 的选定采集方法在设备未找到错误时诊断，成功时按 1% 抽样。诊断并行读取浏览器设备聚合和 host 快照，以 2000ms 为超时，保留请求释放与取消。结果写入日志；选定装配的 onDiagnostic 为空回调，不能把它描述成已确认的诊断上传链。通用全局入口另在 clone 后释放 RPC 结果，并按对象身份清理。

[Chromium 上游实现](https://raw.githubusercontent.com/chromium/chromium/main/services/audio/public/cpp/audio_system_to_service_adapter.cc)提供设备查询正常／默认回调的布尔 histogram 线索，且输入和输出查询共用该名称。它尚未绑定冻结 Owl 版本，也不证明 Owl 的 JS 采集桥、增量或重置语义。

维护结构分为 main 的通用 provider、具名计数、音频服务生命周期，以及 renderer 的诊断聚合与通用入口。原生采集留在独立 runtime provider；第三方 RPC／释放 helper 不生成实现副本。JS 每次累加桶值，故必须在适配前核实 native 返回增量还是累计快照，以及多窗口、多读取方和重新配置的影响。不能用普通进程 metrics 或空 ready 结果代替。

本次关闭选定 JS owner、数据格式、调用和发布路径问题；保留完整消费者／模式归属及 native 实现缺口。22 个隔离源码场景通过，使用合成 app、设备、RPC、时钟数据，未启动客户端、调用原生接口或提交模型任务；不计产品场景通过。

后续问题分三类：源码结论本次交付；真实 RPC、平台、设备、计数和重启行为列为实施验证；Owl 采集桥来源／构建输入或经验证的等效 provider 列为取得或开发前提。缺少原生环境不重新打开已解决的 JS 盘点。下一内部分析项是 RAM-04 调试页策略的启动 owner 和完整条件。

[结构化合同](audio-measurement-owner-v1.json)、[源码事实](audio-measurement-owner-v1-evidence.jsonl)、[隔离回放](audio-measurement-owner-v1-replay.json)、[上游线索及限制](audio-measurement-primary-review-v1.json)。
