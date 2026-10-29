# 选定原生 Node 版本静态结构

固定 Framework 中 `_napi_get_node_version` 的完整有界函数直接引用静态结构，其 `major/minor/patch` 为 **24.19.0**，`release` 为 **node**。这是所选原生接口所引用的静态发行版本结构；未执行查询。

- 基线：`codex-26.1007.30912-c5b273322a83`；Framework `296,533,696` 字节，SHA256 `34598d1cd28252b97c5010bd5d82e2ffc6ca71f2661c85cf89eeddfbb1706398`。
- 实际符号 VM/file `0x4b42f60`；完整主体 81 字节、19 条指令、3 条内部控制流边；15 字节 NOP 后下一实际符号位于 `0x4b42fc0`。函数在 RDI/RSI 非空路径把结构指针写到 RSI。
- RIP-relative LEA 直接指向结构 VM/file `0x111d3720`，24 字节：3 个 uint32、4 字节对齐、8 字节 release 字段。
- release 字段原始 `78f9690f00001000` 是 chained rebase 编码，不是裸指针。实际 `LC_DYLD_CHAINED_FIXUPS` 声明 format 2；只沿选定页的 229 个指针到该字段，确认 bind/reserved/high8 为 0、target VM/file `0xf69f978`，读取 `node\0`。
- 新增 24 条原始字节证据，符号、映射、函数、结构、选定链和字符串均记录完整 span/hash；原始有限 LLVM 输出、命令、退出码、工具身份均保留。

结构含义采用父级已核对的[官方 Node-API 文档](https://nodejs.org/api/n-api.html#napi_get_node_version)；该外部网页自报 v26.11.1，不是目标版本；[官方固定 tag 结构头](https://raw.githubusercontent.com/nodejs/node/v24.19.0/src/node_api_types.h)也已由父级核对字段顺序/类型，目标值独立来自二进制。指针格式依据本机 Apple 官方 SDK `fixup-chains.h` 原字节快照；主机 SDK 版本也不作为目标 SDK 结论。

目标、探针、app、网络、凭证与模型均未执行或读取；旧冻结产物保持原字节。实际执行后的 Node 版本、Electron 兼容发行版、`NODE_MODULE_VERSION`、传统原生 ABI、完整调用点闭包与启动执行效果仍未知。不从 Node-API=10、Chromium、开发依赖或路径版本推算传统 ABI；不解释既有 archive/unpacked 声明矛盾。
