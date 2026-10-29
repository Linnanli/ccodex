# 路由、导航和快捷键的工程边界决定

剩余253条已保存来源记录已全部完成有限角色处置：169个路由构造、47个Navigate构造、3个路由转换，以及34个快捷键/renderer组合或订阅候选。旧入口v5保留968个原ID，待角色分类为0；完整功能身份解决仍为0，962条没有功能关联。此处关闭的是来源分类队列。

170个已保存路由中，7个直接构造Navigate，与导航清单中的同一位置配对；另有55个路由的已解析页面组件定义包含Navigate分支。这些组件仍可能有其他返回、条件和副作用，不据此判定它们总会重定向，也不按URL名称剥离ChatGPT功能。3次转换输入分别关联154、169、170个构造，是有重叠的静态图，不能相加为493个页面。

已有ROUTE-0152的367项条件关联，经精确祖先图接到ROUTE-0134、0169、0161、0170四个组合上下文。它们说明恢复时须保留的外层组合，不代表每层各实现367项功能，也不新增模式证据。

## 建议源码职责

| 拟议文件 | 职责及必须保留的边界 |
| --- | --- |
| `renderer/navigation/route-table.tsx` | 路由组合、嵌套、条件、动态map和页面加载；调用已有设置策略，不复制页面实现。 |
| `renderer/navigation/router.tsx` | 三个转换输入与router装配；框架转换代码由依赖提供。 |
| `renderer/navigation/redirects.tsx` | 可共享的导航契约；页面特有的判断、目标、replace/state仍由原页面负责。 |
| `main/shortcuts/global-shortcut-registry.ts` | 注册集合、generation、暂停、释放监视、布局更新及失败回退。 |
| `main/shortcuts/register-client-shortcuts.ts` | 十个管理器消费者的装配；录音等领域状态不并入registry。 |
| `main/windows/input-event-adapter.ts` | 六个窗口输入事件的挂接接口；具体MCP、browser和window策略保持各自所有权。 |
| `renderer/commands/registry.ts` | 已证明Pw绑定的enabled/active/priority、键盘/context、菜单元数据及effect清理。 |
| `renderer/commands/registrations.ts` | 七个组合函数保持原职责；十处xs调用仍为消息订阅候选，与Pw分开。 |

完整路径及职责、环境、来源范围、导入导出、共享状态、副作用、依赖与限制均在[结构化决定](entry-composition-roles-v1.json)中。八项是有源码支持的维护建议，不是原作者模块数，也不是完整客户端目录。底层框架、React和运行时通过依赖提供；第一方适配层需要恢复。

fI/aI/pI合同明确注册结果、所有者检查、重复键、平台/裸修饰键分支、释放监视失败回滚、暂停和布局替换失败时的状态恢复。把这些调用简单替换为globalShortcut.register会遗漏客户端行为。实际native/helper提供方仍需独立取得资格。

本批复用完整Program分析和已有合同，只复核冻结字节，没有新增解析、REA调用、客户端运行、模型任务或产品验收。373项功能、48任务、1216条未执行规格及372 unknown/1 shared保持不变。12项关联、3项重叠、模式共享闭包和实际provider/行为缺口仍需处理。

下一项以既有12项关联和3项重叠为固定队列，决定同一目标的共享消费者或不同操作，并将本批入口职责接入既有任务/逻辑模块方案；不再枚举已分类968条来源。[旧入口v5](legacy-entry-dispositions-v5.json)、[九字段证据](entry-composition-roles-v1-evidence.jsonl)保留限定范围。
