# 快捷键弹窗与三类快捷键设置边界

FSC-0425「显示或关闭键盘快捷键对话框」按选定源码归为 **shared**。同一命令/本地状态控制器经具体 lazy export 进入 Ae：Codex 呈现显示当前可用快捷键标签，work 分支载入明确指定 ChatGPT 呈现的可编辑设置弹窗。保留共同控制器和 Codex 列表适配，单独剥离 ChatGPT 界面适配；不能删除整个快捷键模块。

Codex 列表保留键位、命令注册、能力和平台筛选，以及加载、空列表、文本搜索、分组。ChatGPT 弹窗复用此前已归为 shared 的搜索/编辑/恢复功能，另有焦点恢复和捕获 Escape 条件。现有三条弹窗规格已补充两端差异，不新增操作或场景身份。

| 设置 | 更新接口 | 必须保留的差异 |
| --- | --- | --- |
| 实时语音 FSC-0231 | set-codex-command-keybinding；realtimeVoice；set/clear | 已闭合接收器链复用；独立门控、取消和键位缓存 |
| 听写 FSC-0234 | global-dictation-set-hotkey / global-dictation-set-toggle-hotkey | hold/toggle、清除 null、冲突提示、两类缓存刷新 |
| Appshot FSC-0093 | 导入能力对象的 appshot.setHotkey | 平台预设选项、同值跳过、停用和响应错误 |

三个设置适配器应独立维护，可共享捕获/显示工具。其模式本批仍为 unknown，按既有 Codex 条件保留。响应后的缓存更新不能当作系统注册成功；语音核心 shared 也不能推出所有设置页 shared。

模式覆盖由 **502 unknown / 9 shared** 更新为 **501 unknown / 10 shared**。511 功能、584 个不同操作、1852 未执行规格、来源与模块/依赖身份不变。只有源码分析/设计结论，没有新增模型任务、行为通过或客户端实现。

本批复用已保存的大文件控制器和模式证据，只完整解析四个小模块；没有重新展开原生提供方。实际组件挂载、焦点效果、服务实例、系统注册、保存与重启仍待验证。整体分析尚未完成。

依据：[源码合同](shortcut-dialog-hotkey-boundaries-v1.json) · [模式清单](feature-mode-dispositions-v11.csv)。
