Root settings/RPC 交付逻辑及拷贝复核通过：实际独立 checker exit 0，2,664 checks，errors[]。

四批原始 journal 共 153 条（65/24/25/39），44 份选定原始 metadata 加 20 份别名逐字节一致；再加 5 份来源说明，共 69 个只读输出。原 schema、九个最低字段、ID、source pin、locator 类型、confidence 和模式/运行状态均保留。

已只读审查 root 自有 publisher 与导入 helper 的固定配置、路径规范、symlink 检查、先验证后写入、已有输出等字节复用及新输出 0444 机制。实际 69 个输出均为固定 baseline 下的普通 0444 文件。

General 使用原 closedFiles 76 项 owner closure；外部 peer JSON/MD 由 owner confirmation.peerFiles 单独固定。Local/General confirmation 缺 baseline 字段，依据固定同 baseline owner manifest；General final-link-validation 同样依据固定 owner manifest，未给原报告补造字段。三次实际 root 交付收据均保留：前两次 exit 1 缺字段，第三次 exit 0；只核 saved source/config/stdio pins，没有重跑 producer。

不同 author/peer 计数按原 countPointer 单独保留，交付未相加。Global/runtime 新增均为 0，完整功能分母未知；RPC actualMode 24 条 unknown、General 32 操作 mode unknown，原未观测运行状态保留。

本次只复核 root 交付逻辑及 metadata 拷贝。本 reviewer 创作过 General source core，因此不声称独立重验其源码语义；独立源码审查由 runtime_distribution 完成。未读/解析原目标 JS 或大型 AST，未执行 root producer/helper/目标、UI、网络、模型或个人资料。未复核全 manifest 闭包或旧 global ledger；已保存自有真实工具源码、stdout/stderr、exit 收据与精确输入 pins。
