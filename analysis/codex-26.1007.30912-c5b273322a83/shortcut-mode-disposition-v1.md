# 快捷键功能的模式与保留边界

搜索可配置快捷键（FSC-0067）、单项编辑或恢复（FSC-0068）、批量恢复默认值（FSC-0069）按冻结源码归为 **shared**。共同设置核心与 Codex 呈现保留，ChatGPT 弹窗适配和专属呈现分支可以分别剥离；不能删除整个快捷键模块。此结论尚未实施。

设置路由实际选择动态导入的 KeyboardShortcutsSettings，重导出连接到 Vt；未传 presentation 时，Vt 读取 ij 的 work/codex 条件。另一条具体弹窗链在 work 分支载入 ChatGptKeyboardShortcutsDialog，并明确把 presentation:chatgpt 传给同一 Vt。源码调用与导入导出已核对，有效状态和真实挂载未观察。

两端共用搜索、命令行与单项更新。恢复默认值保留各自语义：Codex 确认后重置整个键位表并按条件恢复浏览器 modifier，ChatGPT 直接顺序重置选定命令。数字导航偏好（FSC-0070）在选定组件的 Codex 呈现中条件保留；缺少全局排他证明，仍为 unknown。

模式覆盖从 **505 unknown / 6 shared** 更新为 **502 unknown / 9 shared**。511 功能、584 个不同用户操作、1852 条未执行规格、来源、模块及依赖身份不变。没有新增整项功能排除、行为通过、模型调用或客户端实现。主要分析阶段仍未完成。

依据：[源码合同](shortcut-mode-disposition-v1.json) · [模式覆盖](feature-mode-dispositions-v10.csv)。接收器、系统快捷键注册、保存耐久性和独立构建另行验收。
