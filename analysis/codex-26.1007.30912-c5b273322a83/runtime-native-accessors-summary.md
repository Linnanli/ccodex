# 选定原生 accessor 与 fuse wire 的静态绑定

基线 `codex-26.1007.30912-c5b273322a83`。仅只读一份完整 Framework 的哈希及 Mach-O 元数据，再核对9个 fuse accessor（各17字节）和一个77字节 `_napi_get_version` 函数；共230字节完整函数主体。有限 llvm-objdump 原始输出、命令与哈希另存，未启动目标、改 fuse、联网或提交模型任务。

9个 accessor 均通过 `movb RIP+disp,%al` 读取同一冻结 wire 的对应字节，再 `cmpb $0x31,%al; sete %al; ret`。LC_SEGMENT_64 的 VM→文件映射与位移独立解析，不使用反汇编输出中的邻近装饰符号推断数据身份。当前固定 wire 为 `010011001`，此为静态代码与字节绑定，未验证调用点闭包或启动执行效果。

| ordinal | 已记录 fuse 名称 | accessor unslid VM | 读取 unslid VM | 读取 file offset | 固定字节 |
| --- | --- | --- | --- | --- | --- |
| 0 | run_as_node | `0x4a279e0` | `0xead17b2` | 246224818 | `0` |
| 1 | cookie_encryption | `0x4a27a00` | `0xead17b3` | 246224819 | `1` |
| 2 | node_options | `0x4a27a20` | `0xead17b4` | 246224820 | `0` |
| 3 | node_cli_inspect | `0x4a27a40` | `0xead17b5` | 246224821 | `0` |
| 4 | embedded_asar_integrity_validation | `0x4a27a60` | `0xead17b6` | 246224822 | `1` |
| 5 | only_load_app_from_asar | `0x4a27a80` | `0xead17b7` | 246224823 | `1` |
| 6 | load_browser_process_specific_v8_snapshot | `0x4a27aa0` | `0xead17b8` | 246224824 | `0` |
| 7 | grant_file_protocol_extra_privileges | `0x4a27ac0` | `0xead17b9` | 246224825 | `0` |
| 8 | wasm_trap_handlers | `0x4a27ae0` | `0xead17ba` | 246224826 | `1` |

`_napi_get_version` 主体范围 `[0x4b2aa60,0x4b2aaad)`，条件分支和末尾跳转均在函数内；唯一 `ret` 位于 `0x4b2aa8e`，尾错误分支跳回共同收尾处。随后3字节 padding，再在 `0x4b2aab0` 开始 `_napi_create_promise`。当前 Mach-O 无 LC_FUNCTION_STARTS；范围依据上述机器码控制流、padding和符号边界，未声称来自函数起点表。非零 RDI、非零 RSI 路径的 `0x4b2aa73` 静态编码 `movl $10,(%rsi)`；这是命名 Node-API accessor 的版本常量10，实际调用未执行。

[Node 官方文档](https://nodejs.org/api/n-api.html#napi_get_version)说明此输出代表支持的最高 Node-API 版本；本文只确认静态常量10，未验证实际调用或全部API兼容。该外部文档页自报 `v26.11.1` 不是目标 Node 版本，Node-API 稳定性也不等于 Node C++ API、外部库或传统模块 ABI 的兼容证明。

实际 Node 版本、Electron兼容版本、传统 `NODE_MODULE_VERSION` 和原生模块 ABI 均为 unknown。Framework 路径版本 `155.0.8059.40` 与外部 fuse schema tag 均不是上述版本证明；此补充也不解释7条既有归档声明矛盾。旧 fuse 材料与原脚本逐哈希保持原字节。
