# 审查来源、仓库、基准分支与提交选择

从实际ReviewThreadSidePanelTab的工具栏及其状态回调补入四类独立用户目标、7个操作、17条未执行回归规格。它们归既有T06，不把选择参数展开成独立功能，也不并入“打开Changes标签”。

| 功能 | 必须保留的差异 |
| --- | --- |
| FSC-0514 选择变更来源 | 两版菜单；Git禁用时仍可用Last turn；cloud只显示标签；ChatGPT路由只提供branch/uncommitted。commit走提交子菜单。 |
| FSC-0515 切换仓库 | 多仓库才显示；Last turn显示All repos。覆盖根变化清提交及基准覆盖；从Last turn切仓库转Uncommitted。 |
| FSC-0516 搜索和选择基准分支 | 本地大小写无关搜索、精确ref、加载/错误/Retry；写独立基准覆盖，读取时覆盖优先于默认。没有在该回调中执行checkout。 |
| FSC-0517 选择已有提交 | 查询加载/失败/空列表分开；选sha先写VY再切commit；与创建Git提交分开。 |

提出两个维护模块：`review-source-controller.ts`管理独立状态与query输入；`review-source-controls.tsx`保留呈现、局部搜索及回调。React/UI/状态依赖通过包或既有第一方适配引入，不生成第三方实现副本。已有完整文件读取后台合同继续复用，不因本次消费者分析重开Git提供方。

**限制：四项目标的完整产品模式仍为unknown。** 具体ChatGPT来源集合已确认，但它不足以替代实际Codex准入/挂载证明。tMa虽声明无效提交等回退规则，在选定app-initial中只有静态导出；安装方和实际生命周期未验证。Fu/Ch/Af的有效存储、query后台结果、晚到数据及重启均未动态观察。

本批核对3个完整程序、3,278,010个AST节点、14组导入身份连接，独立重解析139个选定源码单元并核对原始字节。没有执行目标JS、启动客户端或提交模型任务。静态检查不计作行为通过。

当前有限清单515项功能、591项不同用户操作（592次出现）、1869条未执行规格；模式505 unknown/10 shared。原511项定义、1852条规格和51个任务身份保留；来源身份968及699项未关联计数不变。模块职责增至120项，具体源码见证以模块清单计数为准。两张60节点依赖图不变，原39条要求、9项分析标准与M1–M7验收不变，客户端实现仍未开始。

[源码契约](review-source-selection-v1.json) · [功能清单](feature-scope-v54.csv) · [模式处置](feature-mode-dispositions-v12.csv) · [模块归属](feature-module-ownership-v20.csv) · [实现覆盖](restoration-coverage-v45.json) · [工程增补](implementation-plan-v12-review-source-addendum-v1.json)

本批停止在已确认的选择器/state/query接口。后续沿具体文件操作、搜索和视图偏好消费者补齐审查工作流；实际验证按独立fixture和授权条件安排，不重开本批已确认的内部实现。
