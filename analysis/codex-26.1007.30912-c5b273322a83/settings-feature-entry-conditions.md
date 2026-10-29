# 设置入口条件与现有功能的关联

本批关闭 SD-01 的一个有限子步骤：53 个设置分支均有处置记录；现有 48 个功能逐项有设置入口关联或不属于本批的理由。42 项关联到三个设置页面，6 项属于会话/线程入口。212 条既有场景均接上入口映射，没有增加执行通过数。

| 页面/入口 | 现有功能数 | 已明确的入口条件 |
| --- | ---: | --- |
| General | 29 | 必须进入完整主机设置目录；general-settings 的 switch 分支继承 personalization 的 visible=true。仍保留每个控件的平台和能力条件。 |
| Agent | 6 | 目录允许精简主机；分类与页面 predicate 分别组合。导航不可见不等于所有错误状态下都不能挂载。 |
| Computer use 主视图 | 3 | 外层设置页条件后，主视图要求能力 available；锁屏选项另有 macOS 和 capability 条件。 |
| Computer use / Messages | 4 | 保留外层加载/重定向规则；内部先于主视图分流，再按插件加载/候选/安装状态决定。 |
| 会话与线程入口 | 6 | 不套用设置页面条件；保留既有入口合同和待解决的旧入口身份。 |

新增完整 Program 解析确认 MNs/PNs 使用同一个 FNs 绑定，其四项只涉及 usage、analytics、consumer-view、usage-code-review。因此 General、Agent、Computer use 不会进入该 usage-tab 重定向；work-settings → agent?mode=work 是另一分支。旧台账中的这处条件疑点由本批覆盖说明，历史文件保留。

访问资格、主机 descriptor、平台、capability 与产品模式分别记录。48 项仍为 mode=unknown，确认可排除的 ChatGPT-only 项仍为零。第二个可见性参数来自 descriptor.kind===local，不能当作产品模式，也不能据此认定物理本机。

本批只把静态入口条件关联到原有定义与场景，不证明实际挂载、接收端、持久化或完整构建。其余 50 个设置分支保留待逐项处置；SD-01 整体和完整分析目标均未完成。

对应结构化数据：[入口与场景映射](settings-feature-entry-conditions.json)。现有功能和场景仍以 v7 为定义来源，本批作为关联层，不复制或改写其语义。
