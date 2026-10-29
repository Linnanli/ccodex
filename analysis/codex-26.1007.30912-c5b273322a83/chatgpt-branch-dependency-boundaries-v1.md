# ChatGPT 三个既有分支的拆分边界

三个既有分支组的直接依赖已核对，并作为实施计划的有效补充。新增一项明确取舍：移除 Chat 配置选择后，可省略 primary 私有的 kzt 纯字面量绑定；共享配置和处理器继续保留。没有新增整功能或整模块排除。

| 原决定 | 可拆边界 | 必须保留与具体限制 |
| --- | --- | --- |
| CBX-01 临时 Chat 页脚挂载 | 实际挂载的是临时 Chat 入门弹窗宿主，可省略这处条件调用 | 懒加载小文件转导出回 primary 的 A4→Xwt；主包、jRt/NRt、VIt 和共享公告/存储机制不能整体删除 |
| CBX-02 Chat 输入提示配置 | 移除 Chat 选择后，省略只有一处值读取且无本地导出的私有 kzt 配置 | Q9 还含 $→skill-mention，须保留 /、@、$ 及处理器；同一 effect 的 work 草稿恢复和控制器生命周期保留 |
| CBX-03 切换到 Chat 快捷键 | 省略 switchToMode1 这处注册 | newTask 的默认回调和切模式 keyboardHandler 分开；后者也可请求 Chat，不能原样保留后便宣称所有 Chat 入口已切断 |

CFt 的真实链路是“primary 懒加载 → temporary-chat 小文件 → 从 primary 导入 kr → A4 → Xwt”。Xwt 涉及公告资格、弹窗候选、本地已读标记及关闭动作；仅按文件名或 chunk 拆模块会误判边界。门控、公告、账户和持久化提供方均停在明确接口，没有继续递归调查。

对四个符号做了整 Program 的引用角色核对。CFt as bt、VIt as _u、kzt as JT 是外部导入端名，不是本地同名绑定的值读取。私有 kzt 的唯一值读取位于 Ezt 的 Chat 配置选择；其字面量只有 / 与 @，中性 Q9 另有 $ 技能提及。新增省略决定只针对这个私有配置值，不允许按名字删除其他导入或 suggestion 模块。

[结构化补充](chatgpt-branch-dependency-boundaries-v1.json)保存三项策略、六条事实、源码位置和升级约束，并覆盖原决定的相关说明。原三组决定数保持；功能、操作、模式覆盖层、规格和任务计数均未改变，当前仍为501 unknown、3 shared。源码与保存证据核对不等于实际 UI/服务/持久化通过，本轮没有目标求值、客户端启动、模型或服务调用。

下一步只闭合 primary Qx→initial VXt 的默认 newTask 接收器。selectChat:true 仅是已知输入，不能据此断言函数永远进入 Chat；该目的地与单模式键盘回退仍需源码判断。完整剥离及原分析计划尚未完成。
