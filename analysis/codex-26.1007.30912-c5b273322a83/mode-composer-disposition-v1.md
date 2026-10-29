# Composer 变体与模式取舍

FSC-0481 已完成本批逐入口分析。它是包含 Codex 入口和 ChatGPT 产品选择的共享跨模式功能；静态分类从 unknown 改为 shared。当前有效模式视图为 **502 unknown、2 shared**，504 个功能和全部操作/规格标识保持。

| 范围 | 决定 |
| --- | --- |
| Codex 请求、访问引导、detail-level 与导航恢复 | 保留职责 |
| 请求 chat 的控件及 chat 专属 composer 展示 | 从 Codex-only 产品入口中省略；保留共享写入器与控制器 |
| work 请求、升级/pending、task suggestions | 按调用条件取舍；整段 work handler 不能直接删除 |
| shared-home、项目、文本、controller 适配 | 保留 Codex 条件需要的职责，完整依赖仍须验证 |
| newTask 的切模式 keyboardHandler | 与默认创建任务回调分别处理 |

直接调用方 `wzt` 已找到，传给 `Ezt` 的模式、许可、pending 和回调均有定位。父回调中 picker 来源调用 `iPt`，其他来源调用 `gS`；二者最终使用同一写入器。`Ezt` 的 `LRt` 只刷新建议缓存，不能与其他文件的同名函数合并。

切换可以先取消 pending submit，再因升级或许可返回；pending 显示 work 不等于已写入模式。正常路径还涉及项目、查询参数、路由、mention 和文本迁移。`newTask` 在特定空输入条件下会切换模式并消费按键，不能一概当作创建任务。

模式分类来自已追踪的功能职责，运行验收单独保留。没有把整个 Ezt 或 RCGA-M05 判为可删除，也未确认全部 shared-home 条件在真实 Codex 实例中的值。gg、账户、服务、原生和存储提供方不在本批继续展开。

[模式覆盖层](feature-mode-dispositions-v1.json)明确覆盖基础 v48 中 FSC-0481 的单个 mode 字段；[有效模式 CSV](feature-mode-dispositions-v1.csv)含全部504个既有标识。基础功能账本和实施计划保持原字节，其旧模式数字是基础快照。其他数量、全局运行通过数和完整完成标准不变。

[结构化合同](mode-composer-disposition-v1.json)保存13条事实、6条未执行子规格、六条精确导入导出及源码位置。没有新增模型任务、目标代码执行或真实模式切换。下一批转向已具名的本地线程功能模式分类，复用已有入口/后台证据。
