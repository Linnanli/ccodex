# Renderer 命令与快捷键窄范围分析

冻结基线：`codex-26.1007.30912-c5b273322a83`。仅解析选定完整函数、相邻 Program 片段和 55KB 命令菜单模块；未执行目标代码。

`Nw` 创建默认 `uJt` 与动态 `dJt`。`Pw → Pqt` 随 React effect 注册和清理；`Lqt` 先按 normal/fallback 优先级从后向前尝试动态处理器，再使用默认 Map。命令菜单、键盘和 host run-command 最终会进入同一分发层。

选定 6 个初始 hook：`iMi/les/Dcc/q9s/iEs/gcc`。其中有 6 次直接 `Pw` 调用、10 次字面量 `xs` 订阅；这是此范围内的分母，完整 initial 的注册数量未知。完整 `o6n` 数组有 145 条直接 schema，本分析提取 13 条关注项。菜单 `Oa` 另有 1 次使用动态 commandId 的 `Pw` alias 调用。

`dispatchHostMessage` 候选实现为 renderer 内投递；`dispatchMessage` 候选实现经 preload 进入 Electron IPC。设置页默认入口使用本地导航事件；本地打开文件夹使用 IPC 消息。不能按方法名称推断进程边界。

`newProject` 包含本地与 Work/ChatGPT 项目分支；`newTask` 使用当前模式与项目上下文。因此需要逐条保留条件，不能据名称直接剔除共享功能。`openThreadInNewWindow` 此范围只确认 schema，实际动态 handler 仍未知。

现有线程导航：菜单内部 `Fa → ro → bo → ho → yo` 在完整菜单 Program 中验证。跨文件候选链保存了 `local:` key 解码、identity ID adapter、hostId/state、`/local` 前缀及 orbit/prewarm 分支。initial/shared 原始外层作用域尚未验证，不能把候选链当成完整运行导航证明。

JSON 保留每条完整函数/调用的源路径、source SHA256、UTF-8 零基 end-exclusive 范围及 span SHA256。相邻 Program 只证明选定片段内的绑定；消费者中的 free outer binding 保留 unknown，供父任务统一作用域 AST 核对。所有产品 mode 仍为 unknown。

桥接与现有线程导航的独立证据见 `renderer-command-bridge-helper.json`；其最终 47 条证据已冻结。

语义 notes 为人工 review。`renderer-command-extract.mjs` 可重新生成局部 AST 原始清单；`renderer-command-ranges.json` 独立保留 171 条范围，`renderer-command-evidence-replay.py` 可复验或通过 `--emit` 从冻结源码重建 evidence。脚本均不执行目标代码。
