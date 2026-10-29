# Computer-use settings 静态边界

固定基线 codex-26.1007.30912-c5b273322a83，只做静态 AST 分析。

- 9 个操作、5 个 query 已通过明确 import/export、e6 服务获取、MessageChannel/preload IPC 和 main service 发布链，接到 Ghe 的 14 个同名方法；这不等于运行时已触发。
- c 是 shared 的 JL：abort/ finally 调用 awaitable 的可选 Symbol.dispose，并在 await 前后检查 signal。五个 query 把 signal 交给 JL；串行 Messages 搜索只在队列前后检查 signal，调用 JL 时没有传 signal。主进程所选文件写入、defaults、installer 和 worker 请求没有显式 signal 参数。
- 应用授权在 win32 使用 config.toml；其他平台使用 homedir 下 CUAService group container JSON。消息读/发设置仅 darwin。独立 Electron userData 目录不足以证明这些设置隔离。
- sound 接 /usr/bin/defaults；locked-use 接 Codex Computer Use Installer。只记录调用构造，未执行。
- 模式归属仍未知，0 个已证实 ChatGPT-only 排除。实际 UI/IPC/native 行为、worker handler、Windows 迁移、原生分发与并发写入语义仍待验证。

产物：[目录](computer-use-settings-boundary.json)、[完整所选 AST 节点](computer-use-settings-boundary-units.json)、[独立证据](computer-use-settings-boundary-evidence.jsonl)。这些证据没有加入全局 journal。
