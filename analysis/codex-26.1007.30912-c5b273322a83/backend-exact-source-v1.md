# 桌面对应后台源码与预测 fork 接收契约

桌面声明的提交`740e5af33c71225640e0c1c1555c514c2c93ab74`中，预测fork的参数和接收分支可以公开取得。当前是精确版本后台候选，尚未完成源码构建或实际预测验证。

## 已取得的证据

- 原定4地址中的Cargo.toml/Cargo.lock返回200；两个旧源码路径返回404。沿同提交目录定位到拆分的`protocol/v2/thread.rs`、`mod.rs`，以及`message_processor.rs` → `ThreadRequestProcessor` → `thread_processor.rs`链路。Git tree API限流403另存，未使用凭据或其他版本。
- Workspace版本为`0.162.0-alpha.17.2`。锁文件1473条包记录：1294条registry均有checksum，18条Git记录对应8个source，161条无source。选定5个后台包锁版本仍为`0.0.0`，原锁能否直接参与发布构建尚未执行核对。
- 三个crates-io补丁依赖锁到精确OpenAI fork修订。客户端工程应通过独立后台依赖及包管理保留这些约束；本批没有生成恢复客户端源码或第三方实现副本。
- Rust的ThreadForkParams共21字段，与冻结experimental声明字段集合完全对应；公开0.162.0候选少`experimentalPredictionMode`。源码明确声明此bool的默认值与序列化属性。

## 接收行为及维护决定

后台在初始化/experimental检查后分派ThreadFork。预测模式拒绝配置覆盖、非ephemeral以及path/turn cutoff，调用`fork_options_from_parent`取得父状态；找不到已加载父线程会返回对应错误。它设置ephemeral、启用ReasoningEffortOverride，沿prepared或history创建路径建立线程，再恢复继承设置。

Handler先发送fork响应，按条件重放usage，再发送ThreadStarted。这是源码调用顺序，尚未验证连接投递顺序。创建后的设置恢复等操作仍可报错，不能把流程计为已证明原子回滚、取消清理或重启恢复。

另一个`thread/prediction/request`方法返回“尚未实现”，它与带experimentalPredictionMode的thread/fork分支分别记录。

选型从“匹配后台接收实现未取得”推进为“精确提交的类型与接收源码可取得”。公开0.162.0候选仍不能靠删flag或普通fork满足预测语义。后续只展开`ThreadManager::fork_options_from_parent`和`CodexThread::restore_thread_settings`两个被调用核心边界；有效工具/环境/history继承、cache reuse、成功预测和完整构建继续保留为待证实项。

## 资格与范围

15次脚本HTTP请求：12个200、2个404、1个403；保留全部正文、收据和哈希。已取得7份源码/清单及5份目录页面。静态字段和调用检查通过；没有完整checkout、源码构建、目标执行、客户端启动或模型提交。8份核心台账、功能/模式/来源/场景数量及行为授权保持不变，完整分析尚未完成。

[结构化结论](backend-exact-source-v1.json) · [逐项证据](backend-exact-source-v1-evidence.jsonl) · [版本清单](https://raw.githubusercontent.com/openai/codex/740e5af33c71225640e0c1c1555c514c2c93ab74/codex-rs/Cargo.toml) · [协议类型](https://raw.githubusercontent.com/openai/codex/740e5af33c71225640e0c1c1555c514c2c93ab74/codex-rs/app-server-protocol/src/protocol/v2/thread.rs) · [处理器](https://raw.githubusercontent.com/openai/codex/740e5af33c71225640e0c1c1555c514c2c93ab74/codex-rs/app-server/src/request_processors/thread_processor.rs)
