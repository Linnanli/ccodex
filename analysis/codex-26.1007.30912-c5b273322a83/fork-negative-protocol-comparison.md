# thread/fork 负例契约核对

两端各使用两个独立空 HOME/CODEX_HOME，以 experimentalApi=true/false 测试固定不存在 UUID。4 个 CLI 会话均正常退出，32 个 fork 请求均返回错误，未创建线程、未调用模型。app-server 及子进程运行在禁止网络、限制写入自有目录的 sandbox-exec profile 下。

冻结版本的实验 schema 声明 experimentalPredictionMode:boolean；实际错误字符串被布尔解码拒绝，true 值在 experimentalApi=false 时被能力检查拒绝。公开 npm 的稳定和实验 schema 均未声明此字段；true、false、错误字符串均返回与无字段及未知字段对照相同的缺失 rollout 错误。这个路径表现为未识别/忽略字段，不能解释为预测功能兼容。

| experimentalApi | 用例 | 冻结版本 | 公开 npm | 错误契约相同 |
|---|---|---|---|---|
| True | without-prediction-field | absent-thread-or-rollout-lookup-rejection | absent-thread-or-rollout-lookup-rejection | True |
| True | prediction-false | absent-thread-or-rollout-lookup-rejection | absent-thread-or-rollout-lookup-rejection | True |
| True | prediction-true | absent-thread-or-rollout-lookup-rejection | absent-thread-or-rollout-lookup-rejection | True |
| True | prediction-invalid-string | parameter-decoding-rejection | absent-thread-or-rollout-lookup-rejection | False |
| True | unknown-field-control | absent-thread-or-rollout-lookup-rejection | absent-thread-or-rollout-lookup-rejection | True |
| True | known-ephemeral-invalid-string | parameter-decoding-rejection | parameter-decoding-rejection | True |
| True | known-experimental-before-turn-id | absent-thread-or-rollout-lookup-rejection | absent-thread-or-rollout-lookup-rejection | True |
| True | known-experimental-before-turn-invalid-bool | parameter-decoding-rejection | parameter-decoding-rejection | True |
| False | without-prediction-field | absent-thread-or-rollout-lookup-rejection | absent-thread-or-rollout-lookup-rejection | True |
| False | prediction-false | absent-thread-or-rollout-lookup-rejection | absent-thread-or-rollout-lookup-rejection | True |
| False | prediction-true | experimental-capability-rejection | absent-thread-or-rollout-lookup-rejection | False |
| False | prediction-invalid-string | parameter-decoding-rejection | absent-thread-or-rollout-lookup-rejection | False |
| False | unknown-field-control | absent-thread-or-rollout-lookup-rejection | absent-thread-or-rollout-lookup-rejection | True |
| False | known-ephemeral-invalid-string | parameter-decoding-rejection | parameter-decoding-rejection | True |
| False | known-experimental-before-turn-id | experimental-capability-rejection | experimental-capability-rejection | True |
| False | known-experimental-before-turn-invalid-bool | parameter-decoding-rejection | parameter-decoding-rejection | True |

13/16 个配对负例的错误契约相同，3/16 不同。已知 ephemeral 错误类型、beforeTurnId 实验门控及错误类型均作为两端对照成立。所有错误 code 都是 -32600；依据完整 message 区分解码、能力门控和 lookup。

默认运行环境的嵌套 sandbox_apply 失败和公开清单路径前缀预检失败均单独保留。成功运行的输入清单、runner 快照、schema、raw response、sandbox profile 及既有保护输出均已复核 SHA256。

结果仍不证明任何预测运行成功、完整后端兼容、桌面实际动态接收方或 npm 发布物与源码 commit 的绑定。

机器可读结果：[fork-negative-protocol-comparison.json](fork-negative-protocol-comparison.json)。
