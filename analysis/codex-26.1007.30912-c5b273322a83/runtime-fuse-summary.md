# 定制运行时 fuse 字节只读核对

基线 `codex-26.1007.30912-c5b273322a83`。主可执行文件与 Codex Framework 两份完整二进制共 296,579,104 字节，运行副本哈希与冻结清单一致。主可执行文件未匹配 sentinel；Framework 匹配一处 v1/长度9 的标准格式数据，wire 为 `010011001`。这是两个选定二进制的分母。

| 序号 | 外部 v1 schema 名称 | 原字节 | schema 解读 |
| --- | --- | --- | --- |
| 0 | run_as_node | 0 | disabled |
| 1 | cookie_encryption | 1 | enabled |
| 2 | node_options | 0 | disabled |
| 3 | node_cli_inspect | 0 | disabled |
| 4 | embedded_asar_integrity_validation | 1 | enabled |
| 5 | only_load_app_from_asar | 1 | enabled |
| 6 | load_browser_process_specific_v8_snapshot | 0 | disabled |
| 7 | grant_file_protocol_extra_privileges | 0 | disabled |
| 8 | wasm_trap_handlers | 1 | enabled |

解码依据为 [Electron 官方 fuse 格式与说明](https://www.electronjs.org/docs/latest/tutorial/fuses)及 [v44.7.0 schema](https://github.com/electron/electron/blob/v44.7.0/build/fuses/fuses.json5)。外部 schema 仅用于序号和字节含义，不能将该版本当作 Owl 实际版本；Owl 的原生消费者与执行效果未验证。

RunAsNode、NODE_OPTIONS、NodeCliInspect 对应字节均为0，因此未据此尝试运行环境诊断。未改 fuse、签名或安装包，未启动客户端或提交模型任务。实际 Node/Electron 兼容版本和原生模块 ABI 仍unknown；完整 wire 与逐字节10条来源证据保留原始范围和 span digest。

embedded ASAR integrity 的启用值不解释此前7条 unpacked 声明矛盾，也不证明它们的运行校验通过。
